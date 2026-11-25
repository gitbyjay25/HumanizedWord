"""Shared response assembly for the humanization endpoints."""

from __future__ import annotations

from app.schemas.humanize import (
    DiffOperation,
    HumanizeMetadata,
    HumanizeResponse,
    PreservationScores,
)
from app.services.humanize_service import HumanizeResult


def build_humanize_response(
    result: HumanizeResult,
    tool: str,
    tone: str,
    locked_keywords: list[str],
    elapsed: float,
) -> HumanizeResponse:
    """Assemble the API payload from a HumanizeResult."""
    preservation = result.preservation or {}
    scores = preservation.get("scores")
    metadata = HumanizeMetadata(
        tone_applied=tone,
        word_count=len(result.text.split()),
        char_count=len(result.text),
        keywords_preserved=locked_keywords,
        tool=tool,
        preservation_score=preservation.get("composite_score"),
        scores=PreservationScores(**scores) if scores else None,
        missing_entities=preservation.get("missing_entities"),
        missing_keywords=preservation.get("missing_keywords"),
        diff=[DiffOperation(**op) for op in preservation.get("diff", [])],
        repair_iterations=result.iterations,
        converged=result.converged,
        warning=result.warning,
    )
    return HumanizeResponse(
        result=result.text,
        processing_time=elapsed,
        metadata=metadata,
    )
