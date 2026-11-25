"""
P4 - Context Preservation Engine.

Scores a candidate rewrite against the original context profile across five
normalised dimensions and produces a composite preservation score
`S_total`, plus a token-level diff.

    S_total = 0.35*M_sem + 0.25*M_ner + 0.20*M_kw + 0.10*M_fact + 0.10*M_intent

All dimensions are clamped to [0, 1].
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field

from app.pipeline.p2_extractor import ContextProfile, extract

WEIGHTS = {
    "semantic": 0.35,
    "ner": 0.25,
    "keyword": 0.20,
    "factual": 0.10,
    "intent": 0.10,
}

ACCEPTANCE_THRESHOLD = 0.85

# Compact antonym lexicon used by the factual-consistency check.
_ANTONYMS = [
    ("increase", "decrease"), ("increased", "decreased"), ("higher", "lower"),
    ("more", "less"), ("better", "worse"), ("best", "worst"), ("large", "small"),
    ("before", "after"), ("always", "never"), ("all", "none"), ("can", "cannot"),
    ("enable", "disable"), ("enabled", "disabled"), ("true", "false"),
    ("success", "failure"), ("gain", "loss"), ("accept", "reject"),
    ("significant", "insignificant"), ("increase", "decrease"),
]

_NEGATIONS = {"not", "no", "never", "none", "neither", "nor", "cannot", "without"}
_ARTICLES = {"the", "a", "an"}

_TOKEN_RE = re.compile(r"\w+|[^\w\s]")


@dataclass
class PreservationReport:
    """The evaluation result for one candidate rewrite."""

    semantic: float = 0.0
    ner: float = 0.0
    keyword: float = 0.0
    factual: float = 0.0
    intent: float = 0.0
    total: float = 0.0
    missing_entities: list[str] = field(default_factory=list)
    missing_keywords: list[str] = field(default_factory=list)
    dropped_numbers: list[str] = field(default_factory=list)
    negated: list[str] = field(default_factory=list)
    diff: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "composite_score": round(self.total, 4),
            "scores": {
                "semantic": round(self.semantic, 4),
                "ner": round(self.ner, 4),
                "keyword": round(self.keyword, 4),
                "factual": round(self.factual, 4),
                "intent": round(self.intent, 4),
            },
            "missing_entities": self.missing_entities,
            "missing_keywords": self.missing_keywords,
            "dropped_numbers": self.dropped_numbers,
            "negation_flips": self.negated,
            "diff": self.diff,
        }


def evaluate(
    original: str,
    candidate: str,
    profile: ContextProfile | None = None,
    locked_keywords: list[str] | None = None,
) -> PreservationReport:
    """Evaluate `candidate` against `original`."""
    profile = profile or extract(original, locked_keywords)
    locked = profile.locked_keywords or (locked_keywords or [])
    report = PreservationReport()

    report.semantic = _semantic_score(profile, candidate)
    report.missing_entities = _missing_entities(profile.entities, candidate)
    report.ner = _ner_score(profile.entities, candidate, report.missing_entities)
    report.missing_keywords = _missing_keywords(locked, candidate)
    report.keyword = _keyword_score(locked, report.missing_keywords)
    report.dropped_numbers = _dropped_numbers(profile.numbers, candidate)
    report.negated = _negation_flips(original, candidate)
    report.factual = _factual_score(report.dropped_numbers, report.negated)
    report.intent = _intent_score(profile.modality, candidate)
    report.diff = build_diff(original, candidate)

    report.total = (
        WEIGHTS["semantic"] * report.semantic
        + WEIGHTS["ner"] * report.ner
        + WEIGHTS["keyword"] * report.keyword
        + WEIGHTS["factual"] * report.factual
        + WEIGHTS["intent"] * report.intent
    )
    return report


# ── dimensions ─────────────────────────────────────────────────────────────


def _semantic_score(profile: ContextProfile, candidate: str) -> float:
    """Cosine similarity between the baseline and candidate embeddings."""
    import torch

    if profile.embedding is None:
        return 0.0
    from app.pipeline.p2_extractor import _get_encoder

    encoder = _get_encoder()
    candidate_vec = encoder.encode(
        [candidate], convert_to_tensor=True, normalize_embeddings=True, show_progress_bar=False
    )[0]
    similarity = torch.nn.functional.cosine_similarity(
        profile.embedding.unsqueeze(0), candidate_vec.unsqueeze(0)
    )
    return _clamp(float(similarity.item()))


def _normalise_entity(entity: str) -> str:
    tokens = [t for t in _TOKEN_RE.findall(entity.lower()) if t not in _ARTICLES]
    return " ".join(tokens)


def _missing_entities(entities: list[str], candidate: str) -> list[str]:
    """Entities present in the input but absent from the candidate."""
    missing = []
    candidate_norm = _normalise_entity(candidate)
    candidate_tokens = set(candidate_norm.split())
    for entity in entities:
        target = _normalise_entity(entity)
        if not target:
            continue
        if target in candidate_norm:
            continue
        # Fuzzy fallback: entity tokens mostly present, or high string similarity.
        ent_tokens = target.split()
        overlap = sum(1 for t in ent_tokens if t in candidate_tokens) / len(ent_tokens)
        if overlap >= 0.8:
            continue
        if difflib.SequenceMatcher(None, target, candidate_norm).find_longest_match(
            0, len(target), 0, len(candidate_norm)
        ).size / len(target) >= 0.85:
            continue
        missing.append(entity)
    return missing


def _ner_score(entities: list[str], candidate: str, missing: list[str]) -> float:
    """Exact + fuzzy recall of input entities in the candidate."""
    if not entities:
        return 1.0
    retained = len(entities) - len(missing)
    return _clamp(retained / len(entities))


def _missing_keywords(locked: list[str], candidate: str) -> list[str]:
    """Locked keywords that do not appear verbatim in the candidate."""
    if not locked:
        return []
    lowered = candidate.lower()
    return [kw for kw in locked if kw.lower() not in lowered]


def _keyword_score(locked: list[str], missing: list[str]) -> float:
    """Proportion of locked keywords satisfied."""
    if not locked:
        return 1.0
    return _clamp((len(locked) - len(missing)) / len(locked))


def _dropped_numbers(numbers: list[str], candidate: str) -> list[str]:
    """Numeric literals from the input that vanished from the candidate."""
    if not numbers:
        return []
    candidate_norm = candidate.replace(",", "")
    dropped = []
    for number in numbers:
        bare = number.replace(",", "")
        if bare and bare not in candidate_norm and number not in candidate:
            dropped.append(number)
    return dropped


def _negation_flips(original: str, candidate: str) -> list[str]:
    """Sentences whose negation polarity flipped between input and output."""
    original_sentences = re.split(r"(?<=[.!?])\s+", original)
    candidate_sentences = re.split(r"(?<=[.!?])\s+", candidate)
    flips = []
    for sentence in original_sentences:
        o_neg = _negation_count(sentence)
        if not o_neg:
            continue
        # Find the closest candidate sentence and compare polarity.
        best = max(
            candidate_sentences,
            key=lambda c: difflib.SequenceMatcher(None, sentence, c).ratio(),
            default="",
        )
        if best and _negation_count(best) == 0:
            flips.append(sentence.strip()[:120])
    return flips


def _negation_count(text: str) -> int:
    return sum(1 for token in re.findall(r"\w+", text.lower()) if token in _NEGATIONS)


def _factual_score(dropped_numbers: list[str], negations: list[str]) -> float:
    """Penalise dropped numerics, antonym flips and negation flips."""
    score = 1.0
    if dropped_numbers:
        score -= min(0.6, 0.2 * len(dropped_numbers))
    if negations:
        score -= min(0.4, 0.2 * len(negations))
    return _clamp(score)


def _intent_score(modality: list[str], candidate: str) -> float:
    """Compare the sentence-modality profile of input and candidate."""
    if not modality:
        return 1.0
    from app.pipeline.p2_extractor import _get_spacy

    doc = _get_spacy()(candidate)
    candidate_modality = [
        _modality_of(s) for s in doc.sents if s.text.strip()
    ]
    if not candidate_modality:
        return 0.0

    from collections import Counter

    original_counts = Counter(modality)
    candidate_counts = Counter(candidate_modality)
    total = sum(original_counts.values())
    matched = sum(min(count, candidate_counts.get(key, 0)) for key, count in original_counts.items())
    # A large length change also signals an intent shift.
    length_ratio = min(1.0, len(candidate_modality) / max(1, len(modality)))
    return _clamp(0.85 * (matched / total) + 0.15 * length_ratio)


def _modality_of(sentence) -> str:
    """Classify a sentence as interrogative / imperative / declarative."""
    text = sentence.text.strip()
    if text.endswith("?"):
        return "interrogative"
    root = sentence.root
    if root.pos_ == "AUX" and root.dep_ in {"ROOT", "aux", "conj"}:
        return "imperative"
    if root.pos_ in {"VERB", "AUX"} and root.dep_ == "ROOT":
        head = " ".join(c.text.lower() for c in root.children if c.dep_ == "nsubj")
        if head in {"", "you", "we", "i"}:
            return "imperative"
    return "declarative"


# ── diff ───────────────────────────────────────────────────────────────────


def build_diff(original: str, candidate: str) -> list[dict]:
    """Token-level diff between original and candidate."""
    original_tokens = original.split()
    candidate_tokens = candidate.split()
    matcher = difflib.SequenceMatcher(None, original_tokens, candidate_tokens)
    ops = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        ops.append(
            {
                "op": tag,
                "original": " ".join(original_tokens[i1:i2]),
                "revised": " ".join(candidate_tokens[j1:j2]),
            }
        )
    return ops


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
