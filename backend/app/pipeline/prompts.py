"""
Prompt construction for the SLM transformation engine (P3).

The fine-tuned LoRA was trained outside this repository, so the exact training
prompt template is not recorded in-tree. The templates below are the candidates
that were evaluated against the adapter; see `backend/scripts/probe_adapter.py`
and `docs/03_MODEL_INTEGRATION.md` for the benchmark that selected the default.

Tone control is expressed as natural-language instructions rather than added
special tokens: the shipped `tokenizer_config.json` contains no tone control
tokens, so `<|TONE:ACADEMIC|>` style tags would be tokenized as ordinary text
and would only confuse the adapter.
"""

from __future__ import annotations

import re

# Reserved control tokens that must never be smuggled in from user text.
# (HLD 4.2.3 - Prompt Injection & Control Token Sanitization)
_CONTROL_TOKEN_RE = re.compile(
    r"(<\|[^>|]{0,64}\|>|\[CRITIQUE\]|</?s>\[INST\]|<<SYS>>|\[/INST\]|"
    r"<\|im_start\|>|<\|im_end\|>)",
    re.IGNORECASE,
)


def sanitize_user_text(text: str) -> str:
    """Strip reserved control tokens and chat-template delimiters from raw input.

    Prevents a user passage from closing the system turn and hijacking the
    prompt, and prevents user text from forging a `[CRITIQUE]` block that the
    repair controller would mistake for its own feedback.
    """
    if not text:
        return ""
    cleaned = _CONTROL_TOKEN_RE.sub(" ", text)
    # Collapse the whitespace left behind by the substitution.
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    return cleaned.strip()


# Canonical tone -> natural language instruction.
# Supported tones: general, academic, professional, friendly, casual.
# The 4 trained LoRA tones are: academic, professional, friendly, casual.
TONE_INSTRUCTIONS: dict[str, str] = {
    "general": "in a clear, natural, neutral voice",
    "academic": "in a precise, scholarly academic tone",
    "professional": "in a polished business-professional tone",
    "friendly": "in a warm, friendly, conversational tone",
    "casual": "in a relaxed, conversational tone",
}

# Default tone used when the request omits or supplies an unknown tone.
DEFAULT_TONE = "general"

# Mapping from UI/client tones to the 4 native tones the LoRA adapter was trained on:
# (academic, professional, friendly, casual)
TONE_MAPPING: dict[str, str] = {
    "academic": "academic",
    "professional": "professional",
    "friendly": "friendly",
    "casual": "casual",
    "general": "casual",
}

# Tool-specific instruction appended to the base humanization directive.
TOOL_INSTRUCTIONS: dict[str, str] = {
    "humanize": "",
    "rewrite": (
        " Rephrase the passage so the wording changes noticeably while the meaning "
        "stays exactly the same."
    ),
    "expand": (
        " Expand the passage with a little more explanation and detail, keeping the "
        "original claims intact and adding no new facts."
    ),
    "shorten": (
        " Shorten the passage to roughly two thirds of its length while keeping every "
        "important fact, number and name."
    ),
    "summarize": (
        " Summarize the passage in a few sentences, keeping the central claims, the "
        "key numbers and the important names."
    ),
    "simplify": (
        " Rewrite the passage in plainer, simpler words so a non-expert can follow it, "
        "without changing what it says."
    ),
    "continue": (
        " Continue the passage naturally for two or three sentences, in the same voice "
        "and topic, without repeating what is already written."
    ),
    "explain": (
        " Rewrite the passage as a clear, plain explanation of what it means, keeping "
        "every technical term accurate."
    ),
    "title": (
        " Write a single short title for the passage. Output only the title and "
        "nothing else."
    ),
}

# Tools the current adapter cannot serve faithfully. `translate` has no target
# language parameter in the API contract, and the adapter was trained for
# English humanization only, so serving it would silently return a rewrite.
UNSUPPORTED_TOOLS: dict[str, str] = {
    "translate": (
        "Translation is not available yet: the current model is an English "
        "humanizer and the API has no target-language parameter."
    ),
}


def resolve_tone(tone: str | None) -> tuple[str, str]:
    """Return (canonical_tone, instruction) for a requested tone."""
    key = (tone or DEFAULT_TONE).strip().lower()
    if key not in TONE_INSTRUCTIONS:
        key = DEFAULT_TONE
    return key, TONE_INSTRUCTIONS[key]


def build_alpaca_prompt(
    text: str,
    tone: str = "general",
    locked_keywords: list[str] | None = None,
    tool: str = "humanize",
) -> str:
    """Build the exact instruction prompt matching the fine-tuning notebook.

    Template:
        ### Instruction:
        Rewrite this AI-generated text to sound naturally human. Tone: {tone}.

        ### Input:
        {text}

        ### Output:
    """
    normalized_tone = TONE_MAPPING.get((tone or "casual").strip().lower(), "casual")
    instruction = f"Rewrite this AI-generated text to sound naturally human. Tone: {normalized_tone}."

    tool_str = (tool or "humanize").strip().lower()
    tool_note = TOOL_INSTRUCTIONS.get(tool_str)
    if tool_note:
        instruction += tool_note.strip()

    if locked_keywords:
        valid_terms = [k.strip() for k in locked_keywords if k and k.strip()]
        if valid_terms:
            terms = ", ".join(f'"{k}"' for k in valid_terms)
            instruction += f" Keep these terms exactly as written: {terms}."

    clean_text = sanitize_user_text(text)
    return f"### Instruction:\n{instruction}\n\n### Input:\n{clean_text}\n\n### Output:\n"


def build_user_prompt(
    text: str,
    tone: str,
    locked_keywords: list[str] | None = None,
    critique: str | None = None,
    tool: str = "humanize",
) -> str:
    """Build the user turn for the humanization request.

    The directive is kept deliberately short. An earlier revision spelled out
    style rules ("vary sentence length, use natural transitions, drop formulaic
    AI phrasing such as ...") and Qwen2.5-0.5B responded by *restating those
    rules* instead of rewriting the passage. A single imperative produces a
    usable rewrite; an enumerated style spec produces an echo.
    """
    _, instruction = resolve_tone(tone)

    lines = [f"Rewrite this text {instruction} so it reads like a person wrote it."]

    tool_note = TOOL_INSTRUCTIONS.get((tool or "humanize").strip().lower())
    if tool_note:
        lines.append(tool_note.strip())

    # The fine-tuned adapter compresses aggressively. For length-preserving
    # tools an explicit hint measurably improves content retention.
    if (tool or "humanize").strip().lower() not in {"shorten", "summarize"}:
        lines.append("Keep roughly the same length and keep every fact, name and number.")

    if locked_keywords:
        terms = ", ".join(f'"{k}"' for k in locked_keywords)
        lines.append(f"Keep these terms exactly as written: {terms}.")

    if critique:
        lines.append(critique.strip())

    lines.append("Output only the rewritten text.")
    lines.append("")
    lines.append(text)

    return "\n".join(lines)


def build_critique(
    missing_entities: list[str],
    missing_keywords: list[str],
    semantic_score: float,
    attempt: int,
) -> str:
    """Build the structured critique injected on a failed repair attempt."""
    problems = []
    if missing_entities:
        problems.append(
            "the following named entities were dropped: "
            + ", ".join(f'"{e}"' for e in missing_entities)
        )
    if missing_keywords:
        problems.append(
            "the following required terms are missing: "
            + ", ".join(f'"{k}"' for k in missing_keywords)
        )
    if not problems:
        problems.append(
            f"the rewrite drifted from the original meaning "
            f"(semantic similarity {semantic_score:.2f})"
        )
    else:
        problems.append(f"(semantic similarity {semantic_score:.2f})")

    return (
        "[CRITIQUE]: The previous rewrite failed the context preservation check. "
        + "; ".join(problems)
        + ". Rewrite the text again, keeping every one of these items intact "
        "and preserving the original clause meaning. Do not add any new facts."
    )
