"""Data normalization pipeline for extracted values."""
from __future__ import annotations

import re
from typing import Any


class Normalizer:
    """Normalizes raw extracted text according to configured transformation steps."""

    @staticmethod
    def normalize(value: str | None, steps: list[str | dict[str, Any]] | None) -> str | None:
        """Apply sequential normalization steps to value."""
        if value is None:
            return None

        result = str(value)
        if not steps:
            return result.strip()

        for step in steps:
            if isinstance(step, str):
                name = step.lower()
                params: dict[str, Any] = {}
            elif isinstance(step, dict):
                name = list(step.keys())[0].lower()
                params = step.get(name, {}) or {}
            else:
                continue

            result = Normalizer._apply_step(result, name, params)
            if result is None:
                break

        return result

    @staticmethod
    def _apply_step(val: str, name: str, params: dict[str, Any]) -> str:
        if name in ("trim", "strip"):
            return val.strip()
        elif name in ("uppercase", "upper"):
            return val.upper()
        elif name in ("lowercase", "lower"):
            return val.lower()
        elif name == "remove_whitespace":
            return "".join(val.split())
        elif name == "replace":
            old = str(params.get("old", ""))
            new = str(params.get("new", ""))
            return val.replace(old, new) if old else val
        elif name == "regex_replace":
            pat = str(params.get("pattern", ""))
            rep = str(params.get("replacement", ""))
            return re.sub(pat, rep, val) if pat else val
        elif name == "clean_currency":
            # Strip currency symbols and whitespace
            return re.sub(r"[^\d.,-]", "", val).strip()
        return val
