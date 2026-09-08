"""Document fingerprinting for structural similarity analysis."""
from __future__ import annotations

import collections
import re
from dataclasses import dataclass
from typing import Any

from app.models.ocr import OCRPage, OCRResult, OCRWord
from app.services.extraction.anchors import get_line_number, get_word_bbox


@dataclass
class DocumentFingerprint:
    """Structural layout fingerprint of a document."""

    token_frequencies: dict[str, int]
    line_count: int
    top_tokens: set[str]
    structural_hash: str


class DocumentFingerprinter:
    """Computes layout and text signatures to group documents into template clusters."""

    @classmethod
    def fingerprint(cls, ocr_result: Any) -> DocumentFingerprint:
        """Extract token frequencies, line count, and structural signature."""
        pages = getattr(ocr_result, "pages", [])
        all_tokens: list[str] = []
        lines_seen: set[tuple[int, int]] = set()

        for page in pages:
            p_num = getattr(page, "page_number", 1)
            words = getattr(page, "words", [])
            for w in words:
                ln = get_line_number(w)
                lines_seen.add((p_num, ln))
                clean = re.sub(r"[^\w]", "", w.text.lower())
                if clean and not clean.isdigit() and len(clean) > 1:
                    all_tokens.append(clean)

        counts = collections.Counter(all_tokens)
        top_20 = {tok for tok, _ in counts.most_common(20)}

        # Simple structural hash based on sorted top tokens
        sig = ":".join(sorted(top_20)[:10])

        return DocumentFingerprint(
            token_frequencies=dict(counts),
            line_count=len(lines_seen),
            top_tokens=top_20,
            structural_hash=sig,
        )

    @classmethod
    def similarity(cls, fp1: DocumentFingerprint, fp2: DocumentFingerprint) -> float:
        """Compute Jaccard similarity between document token signatures (0.0 to 1.0)."""
        if not fp1.top_tokens or not fp2.top_tokens:
            return 0.0
        intersection = fp1.top_tokens.intersection(fp2.top_tokens)
        union = fp1.top_tokens.union(fp2.top_tokens)
        return len(intersection) / len(union) if union else 0.0
