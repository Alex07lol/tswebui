"""Visual Locator matcher: ranks and extracts candidate values from an OCR page."""
from __future__ import annotations

import difflib
import json
import math
import re
from dataclasses import dataclass
from typing import Any

from app.models.locator import ExtractionLocator


@dataclass
class MatchCandidate:
    text: str
    confidence: float
    bbox: tuple[int, int, int, int]  # x, y, width, height
    page_number: int
    score_details: dict[str, float]


def match_locator_against_page(
    locator: ExtractionLocator,
    page_words: list[dict[str, Any]],
    page_width: int,
    page_height: int,
    page_number: int = 1,
) -> MatchCandidate | None:
    """Find the best matching text on an OCR page for an ExtractionLocator.

    Args:
        locator: The locator definition.
        page_words: List of dicts with text, bbox_x, bbox_y, bbox_width, bbox_height, confidence.
        page_width: Page pixel width.
        page_height: Page pixel height.
        page_number: Current page number.

    Returns:
        Best MatchCandidate or None if no acceptable match.
    """
    if not page_words or page_width <= 0 or page_height <= 0:
        return None

    # Check page mode
    if locator.page_mode == "first" and page_number != 1:
        return None
    if locator.page_mode == "specific" and locator.specific_page and locator.specific_page != page_number:
        return None

    anchors: list[str] = []
    if locator.anchor_candidates_json:
        try:
            anchors = json.loads(locator.anchor_candidates_json)
        except Exception:
            pass

    structure: dict[str, Any] = {}
    if locator.structure_config_json:
        try:
            structure = json.loads(locator.structure_config_json)
        except Exception:
            pass

    # Group words by line (words with similar y)
    lines: dict[int, list[dict[str, Any]]] = {}
    for w in page_words:
        wy = w.get("bbox_y", 0)
        # Cluster within 16 pixels
        line_key = wy // 16
        lines.setdefault(line_key, []).append(w)

    candidates: list[MatchCandidate] = []

    # Strategy 1: Anchor-guided candidate search
    if anchors:
        for line_key, words in lines.items():
            words.sort(key=lambda x: x.get("bbox_x", 0))
            line_text = " ".join(w.get("text", "") for w in words)

            for anchor in anchors:
                ratio = difflib.SequenceMatcher(None, anchor.lower(), line_text.lower()[:len(anchor) + 10]).ratio()
                if ratio >= 0.70:
                    # Found anchor! Look for candidate after the anchor
                    after_words = []
                    anchor_found = False
                    for w in words:
                        if anchor.lower() in w.get("text", "").lower():
                            anchor_found = True
                            continue
                        if anchor_found:
                            after_words.append(w)

                    if after_words:
                        cand_text = " ".join(w.get("text", "") for w in after_words).strip()
                        bx = after_words[0].get("bbox_x", 0)
                        by = after_words[0].get("bbox_y", 0)
                        bw = (after_words[-1].get("bbox_x", 0) + after_words[-1].get("bbox_width", 0)) - bx
                        bh = max(w.get("bbox_height", 20) for w in after_words)
                        avg_conf = sum(w.get("confidence", 0.9) for w in after_words) / len(after_words)

                        score_details = _calculate_score(
                            cand_text=cand_text,
                            rel_x=bx / page_width,
                            rel_y=by / page_height,
                            target_x=locator.rel_x or 0.5,
                            target_y=locator.rel_y or 0.5,
                            anchor_sim=ratio,
                            ocr_conf=avg_conf,
                            pattern=locator.pattern_value,
                            expected_type=structure.get("expected_type"),
                        )
                        candidates.append(MatchCandidate(
                            text=cand_text,
                            confidence=score_details["composite"],
                            bbox=(bx, by, bw, bh),
                            page_number=page_number,
                            score_details=score_details,
                        ))

    # Strategy 2: Region-guided search (if target rel_x and rel_y are specified)
    if locator.rel_x is not None and locator.rel_y is not None:
        target_px_x = locator.rel_x * page_width
        target_px_y = locator.rel_y * page_height
        target_px_w = (locator.rel_width or 0.3) * page_width
        target_px_h = (locator.rel_height or 0.05) * page_height

        tol_x = locator.tolerance_x * page_width
        tol_y = locator.tolerance_y * page_height

        # Gather words inside or very close to target region
        region_words = [
            w for w in page_words
            if abs(w.get("bbox_x", 0) - target_px_x) <= (target_px_w + tol_x)
            and abs(w.get("bbox_y", 0) - target_px_y) <= (target_px_h + tol_y)
        ]

        if region_words:
            region_words.sort(key=lambda x: (x.get("bbox_y", 0) // 16, x.get("bbox_x", 0)))
            cand_text = " ".join(w.get("text", "") for w in region_words).strip()
            if cand_text:
                bx = min(w.get("bbox_x", 0) for w in region_words)
                by = min(w.get("bbox_y", 0) for w in region_words)
                max_x = max(w.get("bbox_x", 0) + w.get("bbox_width", 0) for w in region_words)
                max_y = max(w.get("bbox_y", 0) + w.get("bbox_height", 0) for w in region_words)
                bw = max_x - bx
                bh = max_y - by
                avg_conf = sum(w.get("confidence", 0.9) for w in region_words) / len(region_words)

                score_details = _calculate_score(
                    cand_text=cand_text,
                    rel_x=bx / page_width,
                    rel_y=by / page_height,
                    target_x=locator.rel_x,
                    target_y=locator.rel_y,
                    anchor_sim=0.5 if not anchors else 0.2,
                    ocr_conf=avg_conf,
                    pattern=locator.pattern_value,
                    expected_type=structure.get("expected_type"),
                )
                candidates.append(MatchCandidate(
                    text=cand_text,
                    confidence=score_details["composite"],
                    bbox=(bx, by, bw, bh),
                    page_number=page_number,
                    score_details=score_details,
                ))

    if not candidates:
        return None

    # Pick candidate with highest composite score
    candidates.sort(key=lambda c: c.confidence, reverse=True)
    return candidates[0]


def _calculate_score(
    cand_text: str,
    rel_x: float,
    rel_y: float,
    target_x: float,
    target_y: float,
    anchor_sim: float,
    ocr_conf: float,
    pattern: str | None = None,
    expected_type: str | None = None,
) -> dict[str, float]:
    """Calculate multi-signal composite score for candidate value."""
    # Spatial proximity
    dist = math.sqrt((rel_x - target_x) ** 2 + (rel_y - target_y) ** 2)
    s_region = max(0.0, 1.0 - (dist / 0.5))

    # Pattern match
    s_pattern = 1.0
    if pattern:
        try:
            s_pattern = 1.0 if re.search(pattern, cand_text) else 0.0
        except Exception:
            s_pattern = 0.5

    # Type check heuristic
    s_type = 1.0
    if expected_type == "currency" and not re.search(r"[\$€£\d]", cand_text):
        s_type = 0.3
    elif expected_type == "date" and not re.search(r"\d{2,4}", cand_text):
        s_type = 0.3

    composite = (
        0.35 * anchor_sim
        + 0.25 * s_region
        + 0.15 * s_pattern
        + 0.15 * s_type
        + 0.10 * min(1.0, ocr_conf)
    )

    return {
        "composite": round(composite, 4),
        "anchor_sim": round(anchor_sim, 4),
        "region_score": round(s_region, 4),
        "pattern_score": round(s_pattern, 4),
        "type_score": round(s_type, 4),
        "ocr_conf": round(ocr_conf, 4),
    }
