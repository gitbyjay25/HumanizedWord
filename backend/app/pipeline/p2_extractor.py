"""
P2 - Context Feature Extractor.

Builds the *Original Context Profile* for an input passage: named entities,
numeric literals, user-locked keywords and a dense semantic embedding used as
the baseline vector `v_in` for the P4 preservation engine.

All heavy models are loaded lazily and shared as process-wide singletons so a
FastAPI worker never re-reads weights per request.
"""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass, field

_EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_SPACY_MODEL_NAME = "en_core_web_sm"

# Numbers that look like entities but carry no semantic weight.
_NUM_RE = re.compile(r"(?<!\w)\d[\d,.]*(?:%|\b)")

_lock = threading.Lock()
_nlp = None
_encoder = None


def _get_spacy():
    """Load the spaCy NER/POS pipeline once per process."""
    global _nlp
    if _nlp is None:
        with _lock:
            if _nlp is None:
                import spacy

                nlp = spacy.load(_SPACY_MODEL_NAME, disable=["lemmatizer"])
                _nlp = nlp
    return _nlp


def _get_encoder():
    """Load the Sentence-Transformers bi-encoder once per process."""
    global _encoder
    if _encoder is None:
        with _lock:
            if _encoder is None:
                from sentence_transformers import SentenceTransformer

                _encoder = SentenceTransformer(_EMBED_MODEL_NAME, device="cpu")
    return _encoder


@dataclass
class ContextProfile:
    """The baseline context profile of an input passage."""

    entities: list[str] = field(default_factory=list)
    numbers: list[str] = field(default_factory=list)
    locked_keywords: list[str] = field(default_factory=list)
    sentences: list[str] = field(default_factory=list)
    modality: list[str] = field(default_factory=list)
    embedding: object | None = None  # torch.Tensor, 384-d, L2-normalised
    raw_text: str = ""


def extract(text: str, locked_keywords: list[str] | None = None) -> ContextProfile:
    """Extract the context profile for `text`."""
    locked = [k.strip() for k in (locked_keywords or []) if k and k.strip()]

    nlp = _get_spacy()
    doc = nlp(text)

    entities: list[str] = []
    for ent in doc.ents:
        label = ent.label_
        # Keep entity strings that carry factual content; skip bare ordinals.
        if label in {"CARDINAL", "ORDINAL"} and len(ent.text) <= 2:
            continue
        if ent.text.strip() and ent.text.strip() not in entities:
            entities.append(ent.text.strip())

    numbers = [m.group(0) for m in _NUM_RE.finditer(text)]

    sentences = [s.text.strip() for s in doc.sents if s.text.strip()]
    modality = [s.root.lemma_.lower() for s in doc.sents if s.root.pos_ in {"VERB", "AUX"}]
    modality = [_modality_of(s) for s in doc.sents if s.text.strip()]

    encoder = _get_encoder()
    embedding = encoder.encode(
        [text],
        convert_to_tensor=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )[0]

    return ContextProfile(
        entities=entities,
        numbers=numbers,
        locked_keywords=locked,
        sentences=sentences,
        modality=modality,
        embedding=embedding,
        raw_text=text,
    )


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
