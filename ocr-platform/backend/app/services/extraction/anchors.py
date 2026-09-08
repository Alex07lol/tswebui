"""Anchor detection and matching with fuzzy and regex support."""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from typing import Any

from app.providers.ocr.base import BoundingBox, OCRPage, OCRWord
from app.schemas.configuration import AnchorConfig


def get_word_bbox(w: Any) -> BoundingBox:
    """Extract BoundingBox from either dataclass or ORM OCRWord."""
    if hasattr(w, "bounding_box"):
        return w.bounding_box
    return BoundingBox(
        x=int(getattr(w, "bbox_x", 0) or 0),
        y=int(getattr(w, "bbox_y", 0) or 0),
        width=int(getattr(w, "bbox_width", 0) or 0),
        height=int(getattr(w, "bbox_height", 0) or 0),
    )


def get_word_index(w: Any) -> int:
    return int(getattr(w, "word_index", 0) or 0)


def get_line_number(w: Any) -> int:
    return int(getattr(w, "line_number", 0) or 0)


@dataclass
class AnchorMatch:
    """Represents a located anchor within an OCR page."""

    matched_text: str
    similarity: float
    page_number: int
    line_number: int
    matched_words: list[Any]
    bounding_box: BoundingBox


class AnchorMatcher:
    """Finds anchors in OCR pages using exact, fuzzy, or regex strategies."""

    @classmethod
    def find_anchors(
        cls, page: Any, config: AnchorConfig | dict[str, Any]
    ) -> list[AnchorMatch]:
        """Search an OCR page for occurrences of the specified anchor."""
        if isinstance(config, dict):
            target_val = str(config.get("value", ""))
            mode = config.get("match", "fuzzy")
            min_sim = float(config.get("minimum_similarity", 0.85))
        else:
            target_val = config.value
            mode = config.match.value if hasattr(config.match, "value") else str(config.match)
            min_sim = config.minimum_similarity

        words = getattr(page, "words", [])
        if not target_val or not words:
            return []

        # Group words by line_number
        lines: dict[int, list[Any]] = {}
        for w in words:
            ln = get_line_number(w)
            lines.setdefault(ln, []).append(w)

        target_clean = " ".join(target_val.lower().split())
        target_token_count = len(target_clean.split())
        matches: list[AnchorMatch] = []

        for line_num, line_words in lines.items():
            words_sorted = sorted(line_words, key=get_word_index)

            # Slide over word windows matching target token count
            for i in range(len(words_sorted)):
                for window_size in range(max(1, target_token_count - 1), target_token_count + 2):
                    if i + window_size > len(words_sorted):
                        continue
                    window_words = words_sorted[i : i + window_size]
                    candidate_str = " ".join(w.text for w in window_words)
                    candidate_clean = " ".join(candidate_str.lower().split())

                    sim = 0.0
                    matched = False

                    if mode == "exact":
                        if candidate_clean == target_clean:
                            sim = 1.0
                            matched = True
                    elif mode == "regex":
                        try:
                            if re.search(target_val, candidate_str, re.IGNORECASE):
                                sim = 1.0
                                matched = True
                        except re.error:
                            pass
                    else:  # fuzzy
                        sim = difflib.SequenceMatcher(None, target_clean, candidate_clean).ratio()
                        if sim >= min_sim:
                            matched = True

                    if matched:
                        bboxes = [get_word_bbox(w) for w in window_words]
                        min_x = min(b.x for b in bboxes)
                        min_y = min(b.y for b in bboxes)
                        max_x = max(b.x + b.width for b in bboxes)
                        max_y = max(b.y + b.height for b in bboxes)

                        matches.append(
                            AnchorMatch(
                                matched_text=candidate_str,
                                similarity=round(sim, 4),
                                page_number=getattr(page, "page_number", 1),
                                line_number=line_num,
                                matched_words=window_words,
                                bounding_box=BoundingBox(
                                    x=min_x,
                                    y=min_y,
                                    width=max_x - min_x,
                                    height=max_y - min_y,
                                ),
                            )
                        )

        # Deduplicate overlapping matches and sort by similarity
        matches.sort(key=lambda m: m.similarity, reverse=True)
        unique_matches: list[AnchorMatch] = []
        seen_lines: set[int] = set()

        for m in matches:
            if m.line_number not in seen_lines:
                seen_lines.add(m.line_number)
                unique_matches.append(m)

        return unique_matches
