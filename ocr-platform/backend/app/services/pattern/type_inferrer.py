"""Output type inference service for beginner-friendly field definitions."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class TypeInferResult:
    inferred_type: str  # text | date | currency | number | boolean
    confidence: float
    display_format: str | None = None


def infer_output_type(
    human_pattern: str | None = None,
    examples: list[str] | None = None,
    field_name: str | None = None,
) -> TypeInferResult:
    """Infer the appropriate data output type based on pattern, samples, and name."""
    name_lower = (field_name or "").lower()

    # 1. Check boolean hints
    if any(name_lower.startswith(prefix) for prefix in ["is_", "has_", "can_"]) or name_lower in ["active", "enabled", "verified", "status"]:
        return TypeInferResult(inferred_type="boolean", confidence=0.85, display_format="True/False")

    # 2. Check pattern tokens & literals
    pat = human_pattern or ""
    if pat:
        tokens = re.findall(r"\{[A-Za-z0-9]+\}", pat)
        literals = re.sub(r"\{[A-Za-z0-9]+\}", "", pat)
        has_alpha_prefix = bool(re.search(r"[A-Za-z]", literals))

        if "{MONEY}" in tokens:
            return TypeInferResult(inferred_type="currency", confidence=0.98, display_format="$#,##0.00")

        # Pure date: only date tokens and punctuation delimiters (no alphabet prefixes like SN- or INV-)
        date_tokens = {"{YYYY}", "{YY}", "{MM}", "{DD}"}
        if tokens and all(t in date_tokens for t in tokens) and not has_alpha_prefix:
            fmt = "YYYY-MM-DD" if "-" in pat else "DD/MM/YYYY"
            return TypeInferResult(inferred_type="date", confidence=0.98, display_format=fmt)

        # Pure number: only number tokens and punctuation/empty (no alphabet prefixes)
        num_tokens = {"{N}", "{NN}", "{NNN}", "{NNNN}", "{NNNNN}", "{NNNNNN}"}
        if tokens and all(t in num_tokens for t in tokens) and not has_alpha_prefix:
            return TypeInferResult(inferred_type="number", confidence=0.95, display_format="123456")

        # If it has alpha prefix or mixed tokens, it's text
        if has_alpha_prefix:
            return TypeInferResult(inferred_type="text", confidence=0.95, display_format="Text")

    # 3. Check examples
    if examples:
        non_empty = [e.strip() for e in examples if e and e.strip()]
        if non_empty:
            sample = non_empty[0]
            if re.match(r"^[\$£€₹]\s?[\d,]+(?:\.\d{2})?$", sample):
                return TypeInferResult(inferred_type="currency", confidence=0.95, display_format="$#,##0.00")
            if re.match(r"^\d{4}[-/]\d{2}[-/]\d{2}$|^\d{2}[-/]\d{2}[-/]\d{4}$", sample):
                return TypeInferResult(inferred_type="date", confidence=0.95, display_format="Date")
            if re.match(r"^\d+(?:\.\d+)?$", sample):
                return TypeInferResult(inferred_type="number", confidence=0.90, display_format="Number")

    # 4. Check field name hints
    if "date" in name_lower or "due" in name_lower or "dob" in name_lower:
        return TypeInferResult(inferred_type="date", confidence=0.75, display_format="Date")
    if "amount" in name_lower or "total" in name_lower or "price" in name_lower or "fee" in name_lower or "tax" in name_lower or "subtotal" in name_lower:
        return TypeInferResult(inferred_type="currency", confidence=0.80, display_format="$#,##0.00")
    if "qty" in name_lower or "quantity" in name_lower or "count" in name_lower:
        return TypeInferResult(inferred_type="number", confidence=0.80, display_format="Integer")

    return TypeInferResult(inferred_type="text", confidence=0.70, display_format="Text")
