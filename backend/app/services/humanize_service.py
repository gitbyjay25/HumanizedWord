"""
Humanization service.

Replaces the original word-substitution stub with the real inference pipeline:

    P2 (context extraction) -> P3 (Qwen2.5-0.5B + LoRA) -> P4 (preservation
    scoring) -> P5 (adaptive repair loop)

The public `process()` contract is preserved so existing callers and routers
keep working; `humanize()` exposes the full result including the preservation
scores and the token diff.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

from app.pipeline.p2_extractor import extract
from app.pipeline.p3_slm_engine import get_engine
from app.pipeline.p4_preservation import ACCEPTANCE_THRESHOLD, evaluate
from app.pipeline.p5_adaptive_repair import AdaptiveRepairController
from app.pipeline.prompts import UNSUPPORTED_TOOLS, sanitize_user_text

# Per-tool acceptance thresholds. Summarising and shortening legitimately drop
# content, so they are gated more loosely than a faithful rewrite.
TOOL_THRESHOLDS: dict[str, float] = {
    "humanize": ACCEPTANCE_THRESHOLD,
    "rewrite": ACCEPTANCE_THRESHOLD,
    "expand": 0.75,
    "shorten": 0.70,
    "summarize": 0.60,
    "simplify": 0.72,
    "continue": 0.55,
    "explain": 0.65,
    "title": 0.50,
    "grammar": 1.0,
}

# Tools handled without the model.
DETERMINISTIC_TOOLS = {"grammar"}

# Tools whose intent is to produce a shorter output, so the length-retention
# guard in P5 must not reject a concise rewrite.
SHORTENING_TOOLS = {"shorten", "summarize"}


class UnsupportedToolError(ValueError):
    """Raised when a requested tool cannot be served by the current adapter."""


@dataclass
class HumanizeResult:
    """Full result of a humanization request."""

    text: str
    tool: str
    tone: str
    locked_keywords: list[str] = field(default_factory=list)
    preservation: dict | None = None
    iterations: int = 0
    converged: bool = True
    timed_out: bool = False
    latency_ms: int = 0
    warning: str | None = None


class HumanizeService:
    """Runs text through the humanization pipeline."""

    async def process(
        self,
        text: str,
        tone: str,
        locked_keywords: list[str],
        tool: str,
    ) -> str:
        """Backward-compatible entry point returning only the rewritten text."""
        result = await self.humanize(text, tone, locked_keywords, tool)
        return result.text

    async def humanize(
        self,
        text: str,
        tone: str = "general",
        locked_keywords: list[str] | None = None,
        tool: str = "humanize",
    ) -> HumanizeResult:
        """Humanize `text` and return the full result."""
        started = time.perf_counter()
        tool = (tool or "humanize").strip().lower()
        locked = [k.strip() for k in (locked_keywords or []) if k and k.strip()]

        if tool in UNSUPPORTED_TOOLS:
            raise UnsupportedToolError(UNSUPPORTED_TOOLS[tool])

        if tool in DETERMINISTIC_TOOLS:
            cleaned = self._grammar(text)
            return HumanizeResult(
                text=cleaned,
                tool=tool,
                tone=tone,
                locked_keywords=locked,
                latency_ms=int((time.perf_counter() - started) * 1000),
            )

        if not text or not text.strip():
            return HumanizeResult(
                text=text,
                tool=tool,
                tone=tone,
                locked_keywords=locked,
                latency_ms=int((time.perf_counter() - started) * 1000),
            )

        # ── P2: context feature extraction ──────────────────────────────────
        profile = extract(text, locked)

        # ── P3/P4/P5: generate -> evaluate -> repair ────────────────────────
        engine = get_engine()
        controller = AdaptiveRepairController(
            threshold=TOOL_THRESHOLDS.get(tool, ACCEPTANCE_THRESHOLD),
            enforce_length=tool not in SHORTENING_TOOLS,
        )
        outcome = await controller.run(engine, text, tone, locked, profile)

        warning = None
        if not outcome.converged:
            warning = (
                "Context preservation threshold was not reached; "
                "the best available candidate is returned."
            )
        if outcome.timed_out:
            warning = (warning or "") + " The repair loop hit its time budget."

        return HumanizeResult(
            text=outcome.text,
            tool=tool,
            tone=tone,
            locked_keywords=locked,
            preservation=outcome.report.to_dict(),
            iterations=outcome.iterations,
            converged=outcome.converged,
            timed_out=outcome.timed_out,
            latency_ms=outcome.latency_ms,
            warning=warning.strip() if warning else None,
        )

    async def evaluate_only(self, original: str, candidate: str) -> dict:
        """Score an existing candidate against an original passage."""
        profile = extract(original, [])
        report = evaluate(original, candidate, profile, [])
        return report.to_dict()

    # ── deterministic tool ─────────────────────────────────────────────────

    @staticmethod
    def _grammar(text: str) -> str:
        """Deterministic whitespace/punctuation cleanup."""
        result = text.strip()
        result = re.sub(r"\s+", " ", result)
        result = re.sub(r"\s+([.,!?;:])", r"\1", result)
        if result and result[0].islower():
            result = result[0].upper() + result[1:]
        if result and result[-1] not in ".!?":
            result += "."
        return result
