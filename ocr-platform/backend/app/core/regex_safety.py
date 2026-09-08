"""Safe regular expression validation and execution with ReDoS protection."""
from __future__ import annotations

import re
import threading
from typing import Any

from app.core.logging import get_logger

log = get_logger(__name__)

# Max permitted regex pattern length
MAX_REGEX_LENGTH = 500
# Max characters searched in a single match evaluation
MAX_INPUT_LENGTH = 50_000

# Patterns known to induce catastrophic exponential backtracking (ReDoS)
DANGEROUS_PATTERNS = [
    re.compile(r"\([^\)]*[\+\*]\)[^\)]*[\+\*]"),  # Nested quantifiers like (a+)+ or (.*)*
    re.compile(r"\([a-zA-Z0-9_\\]+\|[\s\S]+\)[\+\*]"),  # Overlapping alternations with quantifier
]


class RegexSafetyError(ValueError):
    """Raised when a regular expression fails safety checks or execution limits."""
    pass


class SafeRegex:
    """Validates and executes user-defined regex safely."""

    @classmethod
    def validate_pattern(cls, pattern_str: str) -> None:
        """Ensure regex pattern does not exceed length limits or contain catastrophic structures."""
        if not pattern_str:
            raise RegexSafetyError("Empty regex pattern")

        if len(pattern_str) > MAX_REGEX_LENGTH:
            raise RegexSafetyError(
                f"Regex pattern exceeds maximum allowed length of {MAX_REGEX_LENGTH} characters"
            )

        for dangerous_pat in DANGEROUS_PATTERNS:
            if dangerous_pat.search(pattern_str):
                raise RegexSafetyError(
                    "Potential catastrophic backtracking construct (ReDoS) detected in pattern"
                )

        try:
            re.compile(pattern_str)
        except re.error as e:
            raise RegexSafetyError(f"Invalid regular expression: {e}")

    @classmethod
    def safe_search(
        cls,
        pattern_str: str,
        text: str,
        timeout_seconds: float = 1.0,
        timeout_sec: float | None = None,
    ) -> re.Match[str] | None:
        """Execute regex search with strict timeout and input length enforcement."""
        cls.validate_pattern(pattern_str)

        actual_timeout = timeout_sec if timeout_sec is not None else timeout_seconds
        truncated_text = text[:MAX_INPUT_LENGTH]
        compiled = re.compile(pattern_str)

        result: list[Any] = [None]
        exception: list[Any] = [None]

        def target() -> None:
            try:
                result[0] = compiled.search(truncated_text)
            except Exception as e:
                exception[0] = e

        t = threading.Thread(target=target)
        t.start()
        t.join(timeout=actual_timeout)

        if t.is_alive():
            log.warning("Regex execution exceeded safety timeout", pattern=pattern_str)
            raise RegexSafetyError(f"Regex execution timed out after {actual_timeout}s")

        if exception[0]:
            raise exception[0]

        return result[0]

    search = safe_search
