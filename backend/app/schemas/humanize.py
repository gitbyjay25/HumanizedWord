from pydantic import BaseModel, Field
from typing import Optional


class HumanizeRequest(BaseModel):
    text: str = Field(..., min_length=10, description="Text to humanize (min 10 chars)")
    tone: str = Field(
        default="general",
        description="Tone: general, academic, professional, friendly, casual",
    )
    locked_keywords: list[str] = Field(default_factory=list, description="Keywords to preserve unchanged")
    tool: str = Field(
        default="humanize",
        description="Tool: humanize, rewrite, expand, shorten, summarize, grammar",
    )


class PreservationScores(BaseModel):
    """The five context-preservation dimensions (P4)."""

    semantic: float = Field(..., description="M_sem - SBERT cosine similarity")
    ner: float = Field(..., description="M_ner - named entity retention")
    keyword: float = Field(..., description="M_kw - locked keyword satisfaction")
    factual: float = Field(..., description="M_fact - factual/structural consistency")
    intent: float = Field(..., description="M_intent - intent and modality alignment")


class DiffOperation(BaseModel):
    op: str = Field(..., description="replace | delete | insert")
    original: str = ""
    revised: str = ""


class HumanizeMetadata(BaseModel):
    tone_applied: str
    word_count: int
    char_count: int
    keywords_preserved: list[str]
    # ── P4 / P5 additions (optional so older clients keep working) ──
    tool: Optional[str] = None
    preservation_score: Optional[float] = Field(
        default=None, description="Composite S_total in [0,1]"
    )
    scores: Optional[PreservationScores] = None
    missing_entities: Optional[list[str]] = None
    missing_keywords: Optional[list[str]] = None
    diff: Optional[list[DiffOperation]] = None
    repair_iterations: Optional[int] = None
    converged: Optional[bool] = None
    warning: Optional[str] = None


class HumanizeResponse(BaseModel):
    result: str
    processing_time: float
    metadata: HumanizeMetadata


class EvaluateRequest(BaseModel):
    original_text: str = Field(..., min_length=1)
    candidate_text: str = Field(..., min_length=1)


class EvaluateResponse(BaseModel):
    composite_score: float
    scores: PreservationScores
    missing_entities: list[str] = []
    missing_keywords: list[str] = []
    dropped_numbers: list[str] = []
    negation_flips: list[str] = []
    diff: list[DiffOperation] = []
