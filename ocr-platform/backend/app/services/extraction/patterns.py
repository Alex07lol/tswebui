"""Pattern compilation and matching for human templates, typed patterns, and regex."""
from __future__ import annotations

import re
from typing import Any

from app.schemas.configuration import PatternConfig


class PatternCompiler:
    """Compiles human-friendly templates, typed patterns, or raw regex into compiled regex."""

    TYPED_PATTERNS: dict[str, str] = {
        "date": r"\b(?:\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})\b",
        "currency": r"(?:[\$€£₹]|Rs\.?|USD|EUR|INR|GBP)?\s*[\d,]+(?:\.\d{2})?",
        "integer": r"\b\d+\b",
        "decimal": r"\b\d+\.\d+\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone": r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "uuid": r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
    }

    @staticmethod
    def compile_template_to_regex(template: str) -> str:
        """Translate user-friendly template placeholders into regular expressions."""
        tokens = re.split(r"(\{[A-Za-z0-9_]+\})", template)
        compiled_parts: list[str] = []

        for t in tokens:
            if t == "{YYYY}":
                compiled_parts.append(r"\d{4}")
            elif t == "{YY}":
                compiled_parts.append(r"\d{2}")
            elif t == "{MM}":
                compiled_parts.append(r"\d{2}")
            elif t == "{DD}":
                compiled_parts.append(r"\d{2}")
            elif re.match(r"^\{N{2,}\}$", t):
                count = len(t) - 2
                compiled_parts.append(rf"\d{{{count}}}")
            elif t == "{N}":
                compiled_parts.append(r"\d+")
            elif re.match(r"^\{A{2,}\}$", t):
                count = len(t) - 2
                compiled_parts.append(rf"[A-Za-z]{{{count}}}")
            elif t == "{A}":
                compiled_parts.append(r"[A-Za-z]+")
            elif t == "{ANY}":
                compiled_parts.append(r"[^\s]+")
            else:
                escaped = re.sub(r"([.*+?^$()|[\]\\])", r"\\\1", t)
                compiled_parts.append(escaped)

        return "".join(compiled_parts)

    @classmethod
    def get_regex_for_pattern(cls, config: PatternConfig | dict[str, Any] | None) -> str | None:
        """Return a compiled regex string based on the pattern config."""
        if not config:
            return None

        if isinstance(config, dict):
            ptype = config.get("type", "regex")
            val = config.get("value")
            named = config.get("named_type")
        else:
            ptype = config.type.value if hasattr(config.type, "value") else str(config.type)
            val = config.value
            named = config.named_type

        if ptype == "regex" and val:
            return val
        elif ptype == "template" and val:
            return cls.compile_template_to_regex(val)
        elif ptype == "typed":
            key = (named or val or "").lower()
            return cls.TYPED_PATTERNS.get(key)
        elif ptype == "example":
            return val
        return val
