"""Active learning from human corrections.

When a user corrects an extracted field value in the UI,
record that correction and infer rule improvements.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.core.logging import get_logger

log = get_logger(__name__)


@dataclass
class Correction:
    document_id: str
    field_name: str
    original_value: str | None
    corrected_value: str
    ocr_tokens: list[str] = field(default_factory=list)
    anchor_candidates: list[str] = field(default_factory=list)


@dataclass
class CorrectionInsight:
    field_name: str
    suggested_anchor_aliases: list[str]
    suggested_pattern: str | None
    confidence_delta: float


def _extract_anchor_candidates(tokens: list[str], corrected_value: str) -> list[str]:
    """Find tokens near the corrected value that could serve as anchors."""
    candidates: list[str] = []
    value_lower = corrected_value.lower()
    for i, tok in enumerate(tokens):
        if tok.lower() == value_lower:
            for offset in range(1, 4):
                if i - offset >= 0:
                    candidates.append(tokens[i - offset])
            break
    return candidates[:3]


def _infer_pattern(values: list[str]) -> str | None:
    """Infer a regex pattern from a list of corrected values."""
    if not values:
        return None
    date_re = re.compile(r"^\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}$")
    if all(date_re.match(v) for v in values):
        return r"\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}"
    currency_re = re.compile(r"^\$?[\d,]+\.?\d{0,2}$")
    if all(currency_re.match(v) for v in values):
        return r"\$?[\d,]+\.?\d{0,2}"
    if all(v.isdigit() for v in values):
        return r"\d+"
    return None


class CorrectionEngine:
    """In-memory store for corrections; can be persisted externally."""

    def __init__(self) -> None:
        self._history: dict[str, list[str]] = {}
        self._anchors: dict[str, list[str]] = {}

    def record(self, correction: Correction) -> CorrectionInsight:
        """Record a correction and return derived insight."""
        fn = correction.field_name
        val = correction.corrected_value.strip()

        self._history.setdefault(fn, []).append(val)
        anchors = _extract_anchor_candidates(correction.ocr_tokens, val)
        for a in anchors:
            if a not in self._anchors.get(fn, []):
                self._anchors.setdefault(fn, []).append(a)

        pattern = _infer_pattern(self._history[fn])
        insight = CorrectionInsight(
            field_name=fn,
            suggested_anchor_aliases=self._anchors.get(fn, [])[:5],
            suggested_pattern=pattern,
            confidence_delta=0.05 * min(len(self._history[fn]), 10),
        )
        log.info(
            "Correction recorded",
            field=fn,
            corrected_value=val,
            insight_pattern=pattern,
        )
        return insight

    def get_insights(self, field_name: str) -> CorrectionInsight | None:
        if field_name not in self._history:
            return None
        return CorrectionInsight(
            field_name=field_name,
            suggested_anchor_aliases=self._anchors.get(field_name, [])[:5],
            suggested_pattern=_infer_pattern(self._history[field_name]),
            confidence_delta=0.05 * min(len(self._history[field_name]), 10),
        )

    def all_field_names(self) -> list[str]:
        return list(self._history.keys())

    def history_count(self, field_name: str) -> int:
        return len(self._history.get(field_name, []))


_engine = CorrectionEngine()


def get_correction_engine() -> CorrectionEngine:
    return _engine
