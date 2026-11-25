"""
P3 - SLM Transformation Engine.

Owns the Qwen2.5-0.5B-Instruct base weights plus the project's LoRA adapter and
produces tone-conditioned candidate rewrites. The adapter is merged into the
base weights at load time: the adapter is small (r=8, ~1.08M parameters), and
merging removes the per-layer LoRA matmuls from the hot path.

Model weights are loaded lazily and shared across requests as a process-wide
singleton. Generation runs under `torch.inference_mode()`.
"""

from __future__ import annotations

import os
import re
import threading
from dataclasses import dataclass

from app.pipeline.prompts import (
    build_alpaca_prompt,
    build_user_prompt,
    resolve_tone,
    sanitize_user_text,
)

BASE_MODEL_ID = os.environ.get("HW_BASE_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")

# The LoRA adapter can live in kaggle_output/output_qwen_0_5b/final_adapter,
# in a custom path defined via HW_ADAPTER_DIR, or fallback to the repository root.
_REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
_KAGGLE_QWEN_DIR = os.path.join(
    _REPO_ROOT, "kaggle_output", "output_qwen_0_5b", "final_adapter"
)

_configured_adapter = os.environ.get("HW_ADAPTER_DIR")
if _configured_adapter:
    ADAPTER_DIR = (
        _configured_adapter
        if os.path.isabs(_configured_adapter)
        else os.path.abspath(os.path.join(_REPO_ROOT, _configured_adapter))
    )
else:
    ADAPTER_DIR = _KAGGLE_QWEN_DIR if os.path.isdir(_KAGGLE_QWEN_DIR) else _REPO_ROOT

# Words per inference chunk. Long passages are split so a single forward pass
# stays inside the latency budget and memory ceiling.
CHUNK_WORDS = int(os.environ.get("HW_CHUNK_WORDS", "180"))
MAX_NEW_TOKENS_PER_WORD = 3
MIN_NEW_TOKENS = 48
MAX_NEW_TOKENS_CEILING = 512

_lock = threading.Lock()
_engine = None


@dataclass
class GenerationConfig:
    """Decoding parameters for a single candidate generation."""

    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    repetition_penalty: float = 1.08
    max_new_tokens: int | None = None
    seed: int | None = None


class SLMEngine:
    """Loads the base model + LoRA adapter and generates humanized rewrites."""

    def __init__(self, adapter_dir: str = ADAPTER_DIR, base_model_id: str = BASE_MODEL_ID):
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self._torch = torch
        self.device = torch.device("cpu")

        # The tokenizer is taken from the base model: the adapter directory ships
        # a tokenizer_config.json without added_tokens_decoder, so loading it
        # directly can silently drop the <|im_start|>/<|im_end|> control tokens.
        self.tokenizer = AutoTokenizer.from_pretrained(base_model_id)
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        base = AutoModelForCausalLM.from_pretrained(
            base_model_id, torch_dtype=torch.float32, low_cpu_mem_usage=True
        )

        print(f"[P3] loading LoRA adapter from {adapter_dir}")
        self.model = PeftModel.from_pretrained(base, adapter_dir, torch_dtype=torch.float32)
        self.model = self.model.merge_and_unload()
        self.model.to(self.device)
        self.model.eval()
        print("[P3] adapter merged, engine ready")

    # ── public API ──────────────────────────────────────────────────────────

    def warmup(self) -> None:
        """Run a tiny generation so the first real request is not the slow one."""
        try:
            self.generate("Hello world.", tone="general", locked_keywords=[], config=GenerationConfig(max_new_tokens=8))
        except Exception as exc:  # pragma: no cover - diagnostic path
            print(f"[P3] warmup failed: {exc}")

    def generate(
        self,
        text: str,
        tone: str = "general",
        locked_keywords: list[str] | None = None,
        critique: str | None = None,
        config: GenerationConfig | None = None,
        tool: str = "humanize",
    ) -> str:
        """Generate a tone-conditioned rewrite of `text`."""
        config = config or GenerationConfig()
        clean = sanitize_user_text(text)
        if not clean:
            return text

        chunks = _chunk_text(clean, CHUNK_WORDS)
        outputs: list[str] = []
        for chunk in chunks:
            rendered = self._render(chunk, tone, locked_keywords or [], critique, tool=tool)
            outputs.append(self._run(rendered, config))

        return "\n\n".join(o for o in outputs if o).strip() or clean

    # ── internals ───────────────────────────────────────────────────────────

    def _render(
        self,
        text: str,
        tone: str,
        locked_keywords: list[str],
        critique: str | None,
        tool: str = "humanize",
    ) -> str:
        # If critique is present (e.g. from an explicit repair), incorporate it;
        # otherwise use the exact prompt format the LoRA adapter was fine-tuned on.
        return build_alpaca_prompt(
            text=text,
            tone=tone,
            locked_keywords=locked_keywords,
            tool=tool,
        )

    def _run(self, prompt: str, config: GenerationConfig) -> str:
        torch = self._torch
        inputs = self.tokenizer(
            prompt, return_tensors="pt", truncation=True, max_length=2048
        ).to(self.device)

        if config.seed is not None:
            torch.manual_seed(config.seed)

        max_new = config.max_new_tokens or _scaled_max_new_tokens(
            inputs["input_ids"].shape[1]
        )
        max_new = max(MIN_NEW_TOKENS, min(max_new, MAX_NEW_TOKENS_CEILING))

        do_sample = config.temperature > 0.0
        with torch.inference_mode():
            output = self.model.generate(
                **inputs,
                max_new_tokens=max_new,
                do_sample=do_sample,
                temperature=config.temperature if do_sample else None,
                top_p=config.top_p if do_sample else None,
                top_k=config.top_k if do_sample else None,
                repetition_penalty=config.repetition_penalty,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        generated = output[0][inputs["input_ids"].shape[1]:]
        decoded = self.tokenizer.decode(generated, skip_special_tokens=True).strip()
        if "### Output:\n" in decoded:
            decoded = decoded.split("### Output:\n")[-1].strip()
        return decoded


# ── helpers ────────────────────────────────────────────────────────────────


def _scaled_max_new_tokens(input_len: int) -> int:
    """Scale the generation budget to the input length."""
    approx_words = max(1, input_len // 1.4)
    return int(min(MAX_NEW_TOKENS_CEILING, max(MIN_NEW_TOKENS, approx_words * MAX_NEW_TOKENS_PER_WORD)))


def _chunk_text(text: str, max_words: int) -> list[str]:
    """Split text into word-bounded chunks on sentence boundaries."""
    if len(text.split()) <= max_words:
        return [text]

    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current: list[str] = []
    for sentence in sentences:
        candidate = " ".join(current + [sentence])
        if current and len(candidate.split()) > max_words:
            chunks.append(" ".join(current))
            current = [sentence]
        else:
            current.append(sentence)
    if current:
        chunks.append(" ".join(current))
    return chunks


def get_engine() -> SLMEngine:
    """Return the process-wide engine singleton, loading it on first use."""
    global _engine
    if _engine is None:
        with _lock:
            if _engine is None:
                _engine = SLMEngine()
    return _engine


def engine_status() -> dict:
    """Lightweight status payload for the health endpoint."""
    return {
        "loaded": _engine is not None,
        "base_model": BASE_MODEL_ID,
        "adapter_dir": ADAPTER_DIR,
    }
