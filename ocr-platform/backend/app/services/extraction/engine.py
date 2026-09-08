"""Configurable extraction engine supporting anchors, patterns, regions, and scopes."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.core.logging import get_logger
from app.providers.ocr.base import BoundingBox
from app.schemas.configuration import (
    ConfigurationSchema,
    ExtractionFieldSchema,
)
from app.services.extraction.anchors import (
    AnchorMatch,
    AnchorMatcher,
    get_line_number,
    get_word_bbox,
    get_word_index,
)
from app.services.extraction.confidence import ConfidenceBreakdown, ConfidenceEngine
from app.services.extraction.patterns import PatternCompiler
from app.services.normalization.normalizer import Normalizer
from app.services.validation.validator import ValueValidator

log = get_logger(__name__)


@dataclass
class ExtractedFieldResult:
    """Complete result for a single field extraction with full evidence."""

    field_id: str
    output_variable: str
    raw_value: str | None
    normalized_value: str | None
    final_confidence: float
    confidence_breakdown: dict[str, float]
    validation_passed: bool
    validation_message: str | None
    evidence: dict[str, Any]


class ExtractionEngine:
    """Executes declarative extraction configurations against OCR results."""

    @classmethod
    def extract_document(
        cls, ocr_result: Any, config: ConfigurationSchema | dict[str, Any]
    ) -> dict[str, ExtractedFieldResult]:
        """Execute all configured field rules against the document OCR result."""
        if isinstance(config, dict):
            fields_data = config.get("fields", [])
        else:
            fields_data = config.fields

        extracted_results: dict[str, ExtractedFieldResult] = {}

        def get_priority(f: Any) -> int:
            return f.priority if hasattr(f, "priority") else f.get("priority", 100)

        sorted_fields = sorted(fields_data, key=get_priority, reverse=True)

        for fld in sorted_fields:
            res = cls.extract_field(ocr_result, fld)
            extracted_results[res.output_variable] = res

        return extracted_results

    @classmethod
    def extract_field(
        cls, ocr_result: Any, field_cfg: ExtractionFieldSchema | dict[str, Any]
    ) -> ExtractedFieldResult:
        """Extract a single field by evaluating its extraction rule."""
        if isinstance(field_cfg, dict):
            field_id = field_cfg.get("id", "field")
            out_var = field_cfg.get("output", {}).get("variable", field_id)
            rule = field_cfg.get("extraction", {})
            norm_steps = field_cfg.get("normalization", [])
            val_rules = field_cfg.get("validation", {})
        else:
            field_id = field_cfg.id
            out_var = field_cfg.output.get("variable", field_id) if field_cfg.output else field_id
            rule = field_cfg.extraction
            norm_steps = field_cfg.normalization
            val_rules = field_cfg.validation

        strategy = rule.strategy if hasattr(rule, "strategy") else rule.get("strategy")
        if hasattr(strategy, "value"):
            strategy = strategy.value

        candidate = cls._execute_strategy(ocr_result, rule, strategy)

        raw_val = candidate.get("raw_value")
        norm_val = Normalizer.normalize(raw_val, norm_steps) if raw_val is not None else None
        val_passed, val_msg = ValueValidator.validate(norm_val, val_rules)

        conf = ConfidenceEngine.calculate(
            ocr_confidence=candidate.get("ocr_confidence"),
            anchor_confidence=candidate.get("anchor_confidence"),
            pattern_confidence=candidate.get("pattern_confidence"),
            validation_passed=val_passed,
        )

        return ExtractedFieldResult(
            field_id=field_id,
            output_variable=out_var,
            raw_value=raw_val,
            normalized_value=norm_val,
            final_confidence=conf.overall,
            confidence_breakdown=conf.to_dict(),
            validation_passed=val_passed,
            validation_message=val_msg,
            evidence={
                "rule_strategy": strategy,
                "anchor_text": candidate.get("anchor_text"),
                "source_line": candidate.get("source_line"),
                "ocr_confidence": candidate.get("ocr_confidence"),
                "bounding_box": candidate.get("bbox"),
                "page_number": candidate.get("page_number", 1),
            },
        )

    @classmethod
    def _execute_strategy(
        cls, ocr_result: Any, rule: Any, strategy: str
    ) -> dict[str, Any]:
        """Route to appropriate extraction strategy implementation."""
        if strategy in ("anchored_pattern", "same_line", "next_line", "multi_line"):
            return cls._extract_anchored(ocr_result, rule, strategy)
        elif strategy == "direct_pattern":
            return cls._extract_direct_pattern(ocr_result, rule)
        elif strategy == "region":
            return cls._extract_region(ocr_result, rule)
        return {}

    @classmethod
    def _extract_anchored(
        cls, ocr_result: Any, rule: Any, strategy: str
    ) -> dict[str, Any]:
        """Finds anchor and extracts value nearby."""
        anchor_cfg = rule.anchor if hasattr(rule, "anchor") else rule.get("anchor")
        if not anchor_cfg:
            return {}

        pat_cfg = rule.pattern if hasattr(rule, "pattern") else rule.get("pattern")
        regex_str = PatternCompiler.get_regex_for_pattern(pat_cfg)
        pattern = re.compile(regex_str) if regex_str else None

        pages = getattr(ocr_result, "pages", [])
        for page in pages:
            anchors = AnchorMatcher.find_anchors(page, anchor_cfg)
            if not anchors:
                continue

            best_anchor = anchors[0]
            words = getattr(page, "words", [])
            words_by_line: dict[int, list[Any]] = {}
            for w in words:
                ln = get_line_number(w)
                words_by_line.setdefault(ln, []).append(w)

            # Strategy 1: Same line after anchor
            if strategy in ("same_line", "anchored_pattern"):
                line_words = sorted(
                    words_by_line.get(best_anchor.line_number, []), key=get_word_index
                )
                after_words = [
                    w for w in line_words if get_word_bbox(w).x >= best_anchor.bounding_box.x + best_anchor.bounding_box.width - 5
                ]
                text_after = " ".join(w.text for w in after_words).lstrip(" :-=")

                if pattern:
                    m = pattern.search(text_after)
                    if m:
                        val = m.group(0)
                        matched_words = [w for w in after_words if w.text in val]
                        return cls._build_candidate(
                            val, matched_words, best_anchor, " ".join(w.text for w in line_words)
                        )
                elif text_after:
                    return cls._build_candidate(
                        text_after, after_words, best_anchor, " ".join(w.text for w in line_words)
                    )

            # Strategy 2: Next line
            if strategy in ("next_line", "anchored_pattern"):
                next_line_num = best_anchor.line_number + 1
                next_words = sorted(
                    words_by_line.get(next_line_num, []), key=get_word_index
                )
                text_next = " ".join(w.text for w in next_words).strip()
                if text_next:
                    if pattern:
                        m = pattern.search(text_next)
                        if m:
                            val = m.group(0)
                            return cls._build_candidate(val, next_words, best_anchor, text_next)
                    else:
                        return cls._build_candidate(text_next, next_words, best_anchor, text_next)

            # Strategy 3: Multi line
            if strategy == "multi_line":
                collected_lines: list[str] = []
                collected_words: list[Any] = []
                for l_num in range(best_anchor.line_number + 1, best_anchor.line_number + 6):
                    l_words = words_by_line.get(l_num, [])
                    if not l_words:
                        break
                    l_str = " ".join(w.text for w in l_words).strip()
                    collected_lines.append(l_str)
                    collected_words.extend(l_words)
                if collected_lines:
                    return cls._build_candidate(
                        "\n".join(collected_lines),
                        collected_words,
                        best_anchor,
                        collected_lines[0],
                    )

        return {}

    @classmethod
    def _extract_direct_pattern(cls, ocr_result: Any, rule: Any) -> dict[str, Any]:
        """Search entire document text for a regex pattern."""
        pat_cfg = rule.pattern if hasattr(rule, "pattern") else rule.get("pattern")
        regex_str = PatternCompiler.get_regex_for_pattern(pat_cfg)
        if not regex_str:
            return {}

        pattern = re.compile(regex_str)
        pages = getattr(ocr_result, "pages", [])
        for page in pages:
            page_text = getattr(page, "text", "") or ""
            m = pattern.search(page_text)
            if m:
                val = m.group(0)
                words = getattr(page, "words", [])
                matched_words = [w for w in words if w.text in val]
                avg_conf = (
                    sum(float(getattr(w, "confidence", 0.9) or 0.9) for w in matched_words)
                    / len(matched_words)
                    if matched_words
                    else 0.9
                )
                bbox = cls._compute_bbox(matched_words)
                return {
                    "raw_value": val,
                    "ocr_confidence": avg_conf,
                    "pattern_confidence": 1.0,
                    "anchor_confidence": 1.0,
                    "bbox": bbox,
                    "source_line": val,
                    "page_number": getattr(page, "page_number", 1),
                }
        return {}

    @classmethod
    def _extract_region(cls, ocr_result: Any, rule: Any) -> dict[str, Any]:
        """Extract words within relative fractional coordinates (0.0 to 1.0)."""
        reg_cfg = rule.region if hasattr(rule, "region") else rule.get("region")
        if not reg_cfg:
            return {}

        rx = reg_cfg.x if hasattr(reg_cfg, "x") else reg_cfg.get("x", 0.0)
        ry = reg_cfg.y if hasattr(reg_cfg, "y") else reg_cfg.get("y", 0.0)
        rw = reg_cfg.width if hasattr(reg_cfg, "width") else reg_cfg.get("width", 1.0)
        rh = reg_cfg.height if hasattr(reg_cfg, "height") else reg_cfg.get("height", 1.0)
        target_page = reg_cfg.page if hasattr(reg_cfg, "page") else reg_cfg.get("page", 1)

        pages = getattr(ocr_result, "pages", [])
        for page in pages:
            p_num = getattr(page, "page_number", 1)
            if p_num != target_page:
                continue
            pw = max(1, getattr(page, "width", 1000) or 1000)
            ph = max(1, getattr(page, "height", 1000) or 1000)

            px_min = rx * pw
            py_min = ry * ph
            px_max = (rx + rw) * pw
            py_max = (ry + rh) * ph

            words = getattr(page, "words", [])
            inside_words = []
            for w in words:
                b = get_word_bbox(w)
                if (
                    b.x >= px_min
                    and b.y >= py_min
                    and b.x + b.width <= px_max + 10
                    and b.y + b.height <= py_max + 10
                ):
                    inside_words.append(w)

            if inside_words:
                sorted_w = sorted(
                    inside_words, key=lambda w: (get_line_number(w), get_word_index(w))
                )
                text = " ".join(w.text for w in sorted_w)
                avg_conf = sum(
                    float(getattr(w, "confidence", 0.9) or 0.9) for w in inside_words
                ) / len(inside_words)
                return {
                    "raw_value": text,
                    "ocr_confidence": avg_conf,
                    "pattern_confidence": 1.0,
                    "anchor_confidence": 1.0,
                    "bbox": cls._compute_bbox(inside_words),
                    "source_line": text,
                    "page_number": p_num,
                }
        return {}

    @classmethod
    def _build_candidate(
        cls,
        val: str,
        words: list[Any],
        anchor: AnchorMatch,
        source_line: str,
    ) -> dict[str, Any]:
        avg_conf = (
            sum(float(getattr(w, "confidence", 0.85) or 0.85) for w in words) / len(words)
            if words
            else 0.85
        )
        return {
            "raw_value": val,
            "ocr_confidence": avg_conf,
            "anchor_confidence": anchor.similarity,
            "anchor_text": anchor.matched_text,
            "pattern_confidence": 1.0,
            "source_line": source_line,
            "bbox": cls._compute_bbox(words) if words else anchor.bounding_box.__dict__,
            "page_number": anchor.page_number,
        }

    @staticmethod
    def _compute_bbox(words: list[Any]) -> dict[str, int]:
        if not words:
            return {"x": 0, "y": 0, "width": 0, "height": 0}
        bboxes = [get_word_bbox(w) for w in words]
        min_x = min(b.x for b in bboxes)
        min_y = min(b.y for b in bboxes)
        max_x = max(b.x + b.width for b in bboxes)
        max_y = max(b.y + b.height for b in bboxes)
        return {
            "x": min_x,
            "y": min_y,
            "width": max_x - min_x,
            "height": max_y - min_y,
        }
