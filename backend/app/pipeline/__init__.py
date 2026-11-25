"""Core humanization pipeline (P2 -> P3 -> P4 -> P5)."""

from app.pipeline.p2_extractor import ContextProfile, extract
from app.pipeline.p3_slm_engine import (
    GenerationConfig,
    SLMEngine,
    engine_status,
    get_engine,
)
from app.pipeline.p4_preservation import (
    ACCEPTANCE_THRESHOLD,
    PreservationReport,
    build_diff,
    evaluate,
)
from app.pipeline.p5_adaptive_repair import AdaptiveRepairController, RepairOutcome

__all__ = [
    "ContextProfile",
    "extract",
    "GenerationConfig",
    "SLMEngine",
    "engine_status",
    "get_engine",
    "ACCEPTANCE_THRESHOLD",
    "PreservationReport",
    "build_diff",
    "evaluate",
    "AdaptiveRepairController",
    "RepairOutcome",
]
