"""
P5 - Adaptive Repair Controller.

Closed-loop quality gate around P3/P4. When a candidate fails the preservation
threshold, the controller diagnoses which sub-metric broke, injects a targeted
critique into the next prompt, anneals the sampling temperature towards more
conservative output, and retries - up to `MAX_ITERATIONS` attempts or a hard
wall-clock timeout, whichever comes first.
"""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field

from app.pipeline.p2_extractor import ContextProfile
from app.pipeline.p3_slm_engine import GenerationConfig
from app.pipeline.p4_preservation import PreservationReport, evaluate
from app.pipeline.prompts import build_critique

MAX_ITERATIONS = int(os.environ.get("HW_MAX_ITERATIONS", "1"))
HARD_TIMEOUT_SECONDS = float(os.environ.get("HW_REPAIR_TIMEOUT", "60.0"))
BASE_TEMPERATURE = 0.70
TEMPERATURE_FLOOR = 0.30
TEMPERATURE_STEP = 0.15

# A rewrite must keep at least this fraction of the input's words. Shorter
# outputs indicate truncation or collapse rather than a faithful rewrite.
# The fine-tuned adapter is naturally concise, so this threshold is loose; the
# P4 preservation score is the real gate.
MIN_LENGTH_RETENTION = 0.25

# Openers that indicate the model produced commentary instead of a rewrite.
_PREAMBLE_MARKERS = (
    "sure, here",
    "sure! here",
    "here is the rewritten",
    "here's the rewritten",
    "here is a rewritten",
    "rewritten text:",
    "rewritten version:",
    "here is the humanized",
    "humanized text:",
    "certainly! here",
    "of course! here",
)


class DegenerateCandidate(Exception):
    """Raised internally when a generation is unusable."""


def looks_valid(candidate: str, original: str, enforce_length: bool = True) -> bool:
    """Reject generations that are empty, truncated or wrapped in commentary.

    `enforce_length` is disabled for the shortening tools, where a shorter
    output is the intent rather than a failure.
    """
    if not candidate or not candidate.strip():
        return False

    stripped = candidate.strip().lower()
    if any(stripped.startswith(marker) for marker in _PREAMBLE_MARKERS):
        return False

    if enforce_length:
        original_words = len(original.split())
        candidate_words = len(candidate.split())
        if original_words >= 20 and candidate_words < original_words * MIN_LENGTH_RETENTION:
            return False

    return True


@dataclass
class RepairOutcome:
    """Result of a full repair loop."""

    text: str
    report: PreservationReport
    iterations: int = 0
    converged: bool = False
    timed_out: bool = False
    latency_ms: int = 0
    history: list[dict] = field(default_factory=list)


class AdaptiveRepairController:
    """Runs the candidate -> evaluate -> critique -> regenerate loop."""

    def __init__(
        self,
        threshold: float = 0.85,
        max_iterations: int = MAX_ITERATIONS,
        timeout_seconds: float = HARD_TIMEOUT_SECONDS,
        enforce_length: bool = True,
    ):
        self.threshold = threshold
        self.max_iterations = max_iterations
        self.timeout_seconds = timeout_seconds
        # Disabled for the shortening tools, where a shorter output is intended.
        self.enforce_length = enforce_length

    async def run(
        self,
        engine,
        text: str,
        tone: str,
        locked_keywords: list[str],
        profile: ContextProfile,
    ) -> RepairOutcome:
        """Execute the closed-loop humanization."""
        started = time.perf_counter()
        temperature = BASE_TEMPERATURE
        best_text = ""
        best_report: PreservationReport | None = None
        history: list[dict] = []
        iterations = 0
        timed_out = False
        critique: str | None = None

        for attempt in range(1, self.max_iterations + 1):
            iterations = attempt
            remaining = self.timeout_seconds - (time.perf_counter() - started)
            if remaining <= 0:
                timed_out = True
                break

            try:
                candidate = await asyncio.wait_for(
                    asyncio.to_thread(
                        engine.generate,
                        text,
                        tone,
                        locked_keywords,
                        critique,
                        GenerationConfig(temperature=temperature),
                    ),
                    timeout=remaining,
                )
            except asyncio.TimeoutError:
                timed_out = True
                break

            report = evaluate(text, candidate, profile, locked_keywords)

            if candidate and candidate.strip():
                if not best_text or best_report is None or report.total > best_report.total:
                    best_report = report
                    best_text = candidate

            if not looks_valid(candidate, text, enforce_length=self.enforce_length):
                report.total = 0.0
                history.append(
                    {
                        "attempt": attempt,
                        "temperature": round(temperature, 3),
                        "score": 0.0,
                        "missing_entities": report.missing_entities,
                        "missing_keywords": report.missing_keywords,
                        "degenerate": True,
                    }
                )
                critique = (
                    "[CRITIQUE]: The previous attempt produced an unusable answer "
                    "(it was truncated, too short, or added commentary). Rewrite "
                    "the whole passage, keeping its length roughly the same, and "
                    "output only the rewritten passage."
                )
                temperature = max(TEMPERATURE_FLOOR, temperature - TEMPERATURE_STEP)
                continue

            history.append(
                {
                    "attempt": attempt,
                    "temperature": round(temperature, 3),
                    "score": round(report.total, 4),
                    "missing_entities": report.missing_entities,
                    "missing_keywords": report.missing_keywords,
                }
            )

            if report.total >= self.threshold:
                return RepairOutcome(
                    text=candidate,
                    report=report,
                    iterations=attempt,
                    converged=True,
                    latency_ms=int((time.perf_counter() - started) * 1000),
                    history=history,
                )

            # Build the critique for the next attempt and anneal the temperature.
            critique = build_critique(
                report.missing_entities,
                report.missing_keywords,
                report.semantic,
                attempt,
            )
            temperature = max(TEMPERATURE_FLOOR, temperature - TEMPERATURE_STEP)

        # Return the best candidate generated
        if not best_text:
            best_report = evaluate(text, text, profile, locked_keywords)
            best_text = text
        elif best_report is None:
            best_report = evaluate(text, best_text, profile, locked_keywords)
        return RepairOutcome(
            text=best_text,
            report=best_report,
            iterations=iterations,
            converged=False,
            timed_out=timed_out,
            latency_ms=int((time.perf_counter() - started) * 1000),
            history=history,
        )
