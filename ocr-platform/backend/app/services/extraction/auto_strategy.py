"""Automatic extraction strategy generator.

Analyzes user intent (field name, human pattern, examples, description)
and available OCR tokens/text to generate an optimal ExtractionRule automatically.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.services.intelligence.suggestions import FIELD_CATALOGUE
from app.services.pattern.human_parser import (
    compile_human_pattern,
    infer_from_description,
    infer_from_examples,
)
from app.services.pattern.type_inferrer import infer_output_type

COMMON_ANCHORS_BY_FIELD: dict[str, list[str]] = {
    "serial_number": ["Serial Number", "Serial No", "Serial #", "S/N", "SN", "Serial:"],
    "product_id": ["Product ID", "Product Code", "Item #", "SKU", "Model"],
    "warranty_code": ["Warranty Code", "Warranty #", "Warranty", "Coverage Code"],
    "purchase_date": ["Purchase Date", "Date of Purchase", "Order Date", "Date"],
    "order_number": ["Order Number", "Order #", "Order ID", "PO Number"],
    "account_number": ["Account Number", "Account #", "Acct No", "Account:"],
}


@dataclass
class CandidateMatch:
    value: str
    context_before: str
    context_after: str
    anchor_found: str | None = None
    confidence: float = 0.85
    page: int = 1
    bounding_box: dict[str, int] | None = None


@dataclass
class AutoStrategyResult:
    field_id: str
    display_name: str
    human_pattern: str
    compiled_regex: str
    output_type: str
    strategy: str  # anchored_pattern | direct_pattern
    anchor: str | None
    rule_dict: dict[str, Any]
    confidence: float
    ambiguous: bool
    candidates: list[CandidateMatch] = field(default_factory=list)
    explanation: list[str] = field(default_factory=list)


def _slugify(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower())
    cleaned = re.sub(r"^_+|_+$", "", cleaned)
    if not cleaned or not cleaned[0].isalpha():
        cleaned = "field_" + cleaned
    return cleaned


def _find_known_anchors_for_field(field_key: str, display_name: str) -> list[str]:
    """Retrieve known candidate label anchors for a field."""
    anchors: list[str] = []

    # Check hardcoded common anchors
    if field_key in COMMON_ANCHORS_BY_FIELD:
        anchors.extend(COMMON_ANCHORS_BY_FIELD[field_key])

    # Check intelligence catalogue
    for entry in FIELD_CATALOGUE:
        if entry["field_name"] == field_key:
            anchors.extend([a.title() for a in entry.get("aliases", [])])

    # Default anchor: field display name itself
    if display_name not in anchors:
        anchors.insert(0, display_name)

    return list(dict.fromkeys(anchors))


def generate_auto_strategy(
    display_name: str,
    human_pattern: str | None = None,
    examples: list[str] | None = None,
    description: str | None = None,
    ocr_text: str | None = None,
    ocr_tolerant: bool = True,
) -> AutoStrategyResult:
    """Generate an ExtractionRule automatically based on intent and optional OCR text."""
    field_id = _slugify(display_name)
    ex_list = [e.strip() for e in (examples or []) if e and e.strip()]

    # 1. Determine pattern & regex
    final_human_pattern = human_pattern
    if not final_human_pattern:
        if ex_list:
            infer_res = infer_from_examples(ex_list)
            final_human_pattern = infer_res.inferred_human_pattern
        elif description:
            desc_res = infer_from_description(description)
            final_human_pattern = desc_res.inferred_human_pattern
        else:
            final_human_pattern = "{ANY}"

    comp = compile_human_pattern(final_human_pattern, ocr_tolerant=ocr_tolerant)
    compiled_regex = comp.ocr_tolerant_regex if ocr_tolerant else comp.regex

    # 2. Determine Output Type
    type_res = infer_output_type(final_human_pattern, ex_list, display_name)

    explanation: list[str] = [
        f"Parsed pattern '{final_human_pattern}' into regex '{compiled_regex}'",
        f"Inferred output type '{type_res.inferred_type}' with confidence {type_res.confidence:.0%}",
    ]

    candidate_anchors = _find_known_anchors_for_field(field_id, display_name)
    candidates: list[CandidateMatch] = []
    chosen_strategy = "direct_pattern"
    chosen_anchor: str | None = None
    is_ambiguous = False
    confidence = 0.85

    # 3. If OCR text is available, search for matches and check surrounding context
    if ocr_text:
        try:
            pattern_obj = re.compile(compiled_regex)
            matches = list(pattern_obj.finditer(ocr_text))

            if len(matches) == 0 and ocr_tolerant:
                # Try standard regex if tolerant had no matches
                pattern_obj = re.compile(comp.regex)
                matches = list(pattern_obj.finditer(ocr_text))

            for m in matches:
                val = m.group(0)
                start, end = m.start(), m.end()
                before = ocr_text[max(0, start - 40):start].strip()
                after = ocr_text[end:min(len(ocr_text), end + 40)].strip()

                matched_anchor: str | None = None
                for anc in candidate_anchors:
                    if anc.lower() in before.lower():
                        matched_anchor = anc
                        break

                cand_conf = 0.95 if matched_anchor else 0.75
                candidates.append(
                    CandidateMatch(
                        value=val,
                        context_before=before,
                        context_after=after,
                        anchor_found=matched_anchor,
                        confidence=cand_conf,
                    )
                )

            if len(candidates) == 1:
                explanation.append(f"Found exactly 1 match in document: '{candidates[0].value}'")
                if candidates[0].anchor_found:
                    chosen_strategy = "anchored_pattern"
                    chosen_anchor = candidates[0].anchor_found
                    confidence = 0.95
                    explanation.append(f"Detected label '{chosen_anchor}' near the value")
                else:
                    chosen_strategy = "direct_pattern"
                    confidence = 0.90
            elif len(candidates) > 1:
                anchored_candidates = [c for c in candidates if c.anchor_found]
                if len(anchored_candidates) == 1:
                    chosen_strategy = "anchored_pattern"
                    chosen_anchor = anchored_candidates[0].anchor_found
                    confidence = 0.92
                    explanation.append(
                        f"Found multiple candidates, but only one is near the label '{chosen_anchor}'"
                    )
                else:
                    is_ambiguous = True
                    confidence = 0.65
                    chosen_strategy = "anchored_pattern" if candidate_anchors else "direct_pattern"
                    chosen_anchor = candidate_anchors[0] if candidate_anchors else None
                    explanation.append(
                        f"Found {len(candidates)} possible matches. Ambiguity resolution recommended."
                    )
            else:
                explanation.append("No matches found in document text with provided pattern")
                confidence = 0.50
                # Fallback to anchored pattern if we have candidate labels
                if candidate_anchors:
                    chosen_strategy = "anchored_pattern"
                    chosen_anchor = candidate_anchors[0]
        except re.error:
            explanation.append("Error evaluating regex on text; falling back to default rule")
    else:
        # No document text provided: default to anchored pattern if known anchor exists
        if candidate_anchors:
            chosen_strategy = "anchored_pattern"
            chosen_anchor = candidate_anchors[0]
            explanation.append(f"Assigned default nearby label '{chosen_anchor}' for this field")
        else:
            chosen_strategy = "direct_pattern"
            explanation.append("No common label identified; using direct pattern search")

    # Build internal ExtractionRule dictionary compatible with ExtractionRuleSchema
    rule_dict: dict[str, Any] = {
        "strategy": chosen_strategy,
        "priority": 100,
        "pattern": {
            "type": "regex",
            "value": compiled_regex,
            "examples": ex_list,
        },
        "search": {
            "direction": "after",
            "scope": "same_line",
            "max_lines": 5,
        },
    }

    if chosen_strategy == "anchored_pattern" and chosen_anchor:
        rule_dict["anchor"] = {
            "value": chosen_anchor,
            "match": "fuzzy",
            "minimum_similarity": 0.85,
        }

    return AutoStrategyResult(
        field_id=field_id,
        display_name=display_name,
        human_pattern=final_human_pattern,
        compiled_regex=compiled_regex,
        output_type=type_res.inferred_type,
        strategy=chosen_strategy,
        anchor=chosen_anchor,
        rule_dict=rule_dict,
        confidence=confidence,
        ambiguous=is_ambiguous,
        candidates=candidates,
        explanation=explanation,
    )
