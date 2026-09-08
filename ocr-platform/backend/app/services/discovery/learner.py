"""Pattern learning and rule proposal generation from document clusters."""
from __future__ import annotations

import collections
import re
from dataclasses import dataclass
from typing import Any

from app.services.extraction.anchors import get_line_number, get_word_bbox, get_word_index


@dataclass
class ProposalData:
    field_name: str
    display_name: str
    anchor: str
    strategy: str
    pattern_config: dict[str, Any]
    evidence_samples: list[str]
    confidence_anchor: float
    confidence_pattern: float
    confidence_position: float
    confidence_overall: float


class PatternLearner:
    """Analyzes clusters of OCR results to detect stable anchors and variable field values."""

    @classmethod
    def learn_proposals_for_cluster(
        cls, cluster_docs: list[Any]  # list of OCRResult objects
    ) -> list[ProposalData]:
        """Discover extraction field proposals for a cluster of documents."""
        if not cluster_docs:
            return []

        doc_count = len(cluster_docs)

        # 1. Map all lines and words per document
        # Structure: doc_idx -> list of lines (where each line is a list of words)
        doc_lines: list[list[list[Any]]] = []
        for doc in cluster_docs:
            lines: dict[int, list[Any]] = {}
            for page in getattr(doc, "pages", []):
                for w in getattr(page, "words", []):
                    lines.setdefault(get_line_number(w), []).append(w)
            sorted_lines = [
                sorted(words, key=get_word_index) for _, words in sorted(lines.items())
            ]
            doc_lines.append(sorted_lines)

        # 2. Count phrase occurrences across documents
        # Candidate phrases are 1 to 3 words at the start of a line ending with ":" or similar
        phrase_doc_presence: dict[str, set[int]] = collections.defaultdict(set)
        phrase_values: dict[str, list[str]] = collections.defaultdict(list)

        for doc_idx, lines in enumerate(doc_lines):
            for words in lines:
                if len(words) < 2:
                    continue
                # Test prefix windows of length 1, 2, 3
                for k in range(1, min(4, len(words))):
                    prefix_words = words[:k]
                    candidate_anchor = " ".join(w.text for w in prefix_words).strip(" :-=")
                    if not candidate_anchor or len(candidate_anchor) < 3 or candidate_anchor.isdigit():
                        continue

                    remainder_words = words[k:]
                    val_str = " ".join(w.text for w in remainder_words).strip(" :-=")
                    if val_str:
                        clean_anchor = candidate_anchor.title()
                        phrase_doc_presence[clean_anchor].add(doc_idx)
                        phrase_values[clean_anchor].append(val_str)

        # 3. Filter phrases that appear in majority of documents (>= 70% or at least 1 if single doc)
        threshold_docs = max(1, int(doc_count * 0.70))
        proposals: list[ProposalData] = []

        for anchor, present_docs in phrase_doc_presence.items():
            if len(present_docs) < threshold_docs:
                continue

            vals = phrase_values.get(anchor, [])
            if not vals:
                continue

            # Check if values vary or are meaningful
            field_key = re.sub(r"[^\w]", "_", anchor.lower()).strip("_")
            if not field_key:
                field_key = "field"

            inferred_pattern = cls._infer_pattern(vals)
            anchor_conf = len(present_docs) / doc_count
            pat_conf = cls._calculate_pattern_fit(vals, inferred_pattern)
            pos_conf = 0.90
            overall = (0.40 * anchor_conf) + (0.40 * pat_conf) + (0.20 * pos_conf)

            proposals.append(
                ProposalData(
                    field_name=field_key,
                    display_name=anchor,
                    anchor=anchor,
                    strategy="anchored_pattern",
                    pattern_config=inferred_pattern,
                    evidence_samples=vals[:5],
                    confidence_anchor=round(anchor_conf, 2),
                    confidence_pattern=round(pat_conf, 2),
                    confidence_position=round(pos_conf, 2),
                    confidence_overall=round(overall, 2),
                )
            )

        # Sort proposals by overall confidence
        proposals.sort(key=lambda p: p.confidence_overall, reverse=True)
        return proposals

    @classmethod
    def _infer_pattern(cls, samples: list[str]) -> dict[str, Any]:
        """Infer best pattern type and value from observed sample strings."""
        if not samples:
            return {"type": "regex", "value": r".+"}

        # Test Date
        date_matches = sum(
            1 for s in samples if re.search(r"\b\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}\b", s)
        )
        if date_matches / len(samples) >= 0.7:
            return {"type": "typed", "named_type": "date"}

        # Test Currency / Amount
        curr_matches = sum(
            1 for s in samples if re.search(r"[\$€£₹]?\s*\d+(?:\.\d{2})?", s)
        )
        if curr_matches / len(samples) >= 0.7:
            return {"type": "typed", "named_type": "currency"}

        # Test Pure Integer
        int_matches = sum(1 for s in samples if s.isdigit())
        if int_matches / len(samples) >= 0.7:
            return {"type": "typed", "named_type": "integer"}

        # Test Alphanumeric Code / Prefix (e.g. INV-2026-001)
        prefix_matches = re.match(r"^([A-Za-z]+[-_])", samples[0])
        if prefix_matches:
            pfx = prefix_matches.group(1)
            if all(s.startswith(pfx) for s in samples):
                return {"type": "regex", "value": rf"{re.escape(pfx)}[A-Za-z0-9-]+"}

        return {"type": "regex", "value": r"[A-Za-z0-9\s.-]+"}

    @classmethod
    def _calculate_pattern_fit(cls, samples: list[str], pat_cfg: dict[str, Any]) -> float:
        """Estimate percentage of samples satisfying the inferred pattern."""
        val = pat_cfg.get("value")
        named = pat_cfg.get("named_type")
        if named == "date":
            pat = r"\b\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}\b"
        elif named == "currency":
            pat = r"\d+(?:\.\d{2})?"
        elif named == "integer":
            pat = r"^\d+$"
        elif val:
            pat = val
        else:
            return 0.85

        try:
            r = re.compile(pat)
            matches = sum(1 for s in samples if r.search(s))
            return max(0.5, matches / len(samples))
        except re.error:
            return 0.75
