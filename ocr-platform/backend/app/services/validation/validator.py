"""Validation engine for normalized extracted values."""
from __future__ import annotations

import re
from typing import Any

from app.schemas.configuration import ValidationRules


class ValueValidator:
    """Validates an extracted value against configured validation rules."""

    @staticmethod
    def validate(value: str | None, rules: ValidationRules | dict[str, Any] | None) -> tuple[bool, str | None]:
        """Validate value. Returns (passed: bool, error_message: str | None)."""
        if rules is None:
            return True, None

        if isinstance(rules, dict):
            req = rules.get("required", False)
            regex_pat = rules.get("regex")
            min_len = rules.get("min_length")
            max_len = rules.get("max_length")
            min_val = rules.get("min_value")
            max_val = rules.get("max_value")
            allowed = rules.get("allowed_values", [])
        else:
            req = rules.required
            regex_pat = rules.regex
            min_len = rules.min_length
            max_len = rules.max_length
            min_val = rules.min_value
            max_val = rules.max_value
            allowed = rules.allowed_values

        if req and (value is None or not str(value).strip()):
            return False, "Value is required but was empty or missing"

        if value is None:
            return True, None

        val_str = str(value)

        # Regex check
        if regex_pat:
            try:
                if not re.search(regex_pat, val_str):
                    return False, f"Value '{val_str}' does not match expected pattern: {regex_pat}"
            except re.error as e:
                return False, f"Invalid regex pattern in configuration: {e}"

        # Length check
        if min_len is not None and len(val_str) < min_len:
            return False, f"Value length {len(val_str)} is less than minimum {min_len}"

        if max_len is not None and len(val_str) > max_len:
            return False, f"Value length {len(val_str)} exceeds maximum {max_len}"

        # Allowed values
        if allowed and val_str not in allowed:
            return False, f"Value '{val_str}' is not in allowed set: {allowed}"

        # Numeric bounds
        if min_val is not None or max_val is not None:
            try:
                num = float(re.sub(r"[^\d.-]", "", val_str))
                if min_val is not None and num < min_val:
                    return False, f"Numeric value {num} is less than minimum {min_val}"
                if max_val is not None and num > max_val:
                    return False, f"Numeric value {num} exceeds maximum {max_val}"
            except (ValueError, TypeError):
                return False, f"Value '{val_str}' cannot be parsed as a number for bounds checking"

        return True, None
