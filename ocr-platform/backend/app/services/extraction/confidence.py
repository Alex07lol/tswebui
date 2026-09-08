"""Explainable confidence scoring for extracted values."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConfidenceBreakdown:
    """Component breakdown of the extraction confidence score."""

    ocr: float
    anchor: float
    pattern: float
    validation: float
    overall: float

    def to_dict(self) -> dict[str, float]:
        return {
            "ocr": self.ocr,
            "anchor": self.anchor,
            "pattern": self.pattern,
            "validation": self.validation,
            "overall": self.overall,
        }


class ConfidenceEngine:
    """Calculates multi-factor, explainable confidence scores for extraction candidates."""

    @staticmethod
    def calculate(
        ocr_confidence: float | None,
        anchor_confidence: float | None,
        pattern_confidence: float | None,
        validation_passed: bool | None,
    ) -> ConfidenceBreakdown:
        """Combine signals into a final score (0.0 to 1.0).

        Weights:
            - OCR confidence: 35%
            - Anchor consistency: 30%
            - Pattern match: 25%
            - Validation: 10%
        """
        ocr = float(ocr_confidence) if ocr_confidence is not None else 0.85
        anchor = float(anchor_confidence) if anchor_confidence is not None else 1.0
        pattern = float(pattern_confidence) if pattern_confidence is not None else 1.0
        val_score = 1.0 if (validation_passed is True or validation_passed is None) else 0.0

        overall = (0.35 * ocr) + (0.30 * anchor) + (0.25 * pattern) + (0.10 * val_score)
        overall_clamped = max(0.0, min(1.0, round(overall, 4)))

        return ConfidenceBreakdown(
            ocr=round(ocr, 4),
            anchor=round(anchor, 4),
            pattern=round(pattern, 4),
            validation=round(val_score, 4),
            overall=overall_clamped,
        )
