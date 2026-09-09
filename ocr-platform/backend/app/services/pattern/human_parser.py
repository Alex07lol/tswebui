"""Human-readable pattern parser for beginner-friendly field definitions.

Transforms declarative human tokens like SN-{YYYY}-{NNNNNN} into compiled regular expressions,
infers human patterns from examples, and parses natural-language pattern descriptions.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from app.services.pattern.ocr_tolerance import make_ocr_tolerant

HUMAN_TOKENS: dict[str, str] = {
    "{YYYY}": r"\d{4}",
    "{YY}": r"\d{2}",
    "{MM}": r"(?:0[1-9]|1[0-2])",
    "{DD}": r"(?:0[1-9]|[12]\d|3[01])",
    "{NNNNNN}": r"\d{6}",
    "{NNNNN}": r"\d{5}",
    "{NNNN}": r"\d{4}",
    "{NNN}": r"\d{3}",
    "{NN}": r"\d{2}",
    "{N}": r"\d",
    "{AAAA}": r"[A-Za-z]{4}",
    "{AAA}": r"[A-Za-z]{3}",
    "{AA}": r"[A-Za-z]{2}",
    "{A}": r"[A-Za-z]",
    "{TEXT}": r"[\w\s]+?",
    "{ANY}": r".+?",
    "{EMAIL}": r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    "{PHONE}": r"[\+]?[\d\s\-\(\)]{7,15}",
    "{MONEY}": r"[\$£€₹]?\s?[\d,]+(?:\.\d{2})?",
}

TOKEN_EXAMPLES: dict[str, str] = {
    "{YYYY}": "2026",
    "{YY}": "26",
    "{MM}": "09",
    "{DD}": "15",
    "{NNNNNN}": "001234",
    "{NNNNN}": "12345",
    "{NNNN}": "1234",
    "{NNN}": "123",
    "{NN}": "12",
    "{N}": "5",
    "{AAAA}": "WXYZ",
    "{AAA}": "ABC",
    "{AA}": "US",
    "{A}": "X",
    "{TEXT}": "Sample Text",
    "{ANY}": "ABC-123",
    "{EMAIL}": "user@example.com",
    "{PHONE}": "+1-555-0199",
    "{MONEY}": "$1,250.00",
}


@dataclass
class CompileResult:
    human_pattern: str
    regex: str
    ocr_tolerant_regex: str
    tokens: list[str] = field(default_factory=list)
    example_match: str = ""


@dataclass
class InferResult:
    inferred_human_pattern: str
    regex: str
    confidence: float
    example_match: str = ""


def compile_human_pattern(human_pattern: str, ocr_tolerant: bool = False) -> CompileResult:
    """Compile a human pattern string into an executable regular expression."""
    if not human_pattern:
        return CompileResult(
            human_pattern="",
            regex="",
            ocr_tolerant_regex="",
            tokens=[],
            example_match="",
        )

    # Sort tokens longest first to avoid prefix collisions (e.g. {NNNNNN} before {N})
    sorted_tokens = sorted(HUMAN_TOKENS.keys(), key=len, reverse=True)
    pattern_regex = re.compile("|".join(re.escape(t) for t in sorted_tokens))

    tokens_found: list[str] = []
    example_parts: list[str] = []
    regex_parts: list[str] = []

    last_end = 0
    for match in pattern_regex.finditer(human_pattern):
        # Literal segment before token
        prefix = human_pattern[last_end:match.start()]
        if prefix:
            regex_parts.append(re.escape(prefix))
            example_parts.append(prefix)

        token = match.group(0)
        tokens_found.append(token)
        regex_parts.append(HUMAN_TOKENS[token])
        example_parts.append(TOKEN_EXAMPLES.get(token, "X"))
        last_end = match.end()

    trailing = human_pattern[last_end:]
    if trailing:
        regex_parts.append(re.escape(trailing))
        example_parts.append(trailing)

    compiled_regex = "".join(regex_parts)
    example_match = "".join(example_parts)
    ocr_regex = make_ocr_tolerant(compiled_regex) if ocr_tolerant else compiled_regex

    return CompileResult(
        human_pattern=human_pattern,
        regex=compiled_regex,
        ocr_tolerant_regex=ocr_regex,
        tokens=tokens_found,
        example_match=example_match,
    )


def infer_from_examples(examples: list[str]) -> InferResult:
    """Infer a human-readable pattern from multiple sample values."""
    valid_examples = [e.strip() for e in examples if e and e.strip()]
    if not valid_examples:
        return InferResult(
            inferred_human_pattern="{ANY}",
            regex=r".+?",
            confidence=0.1,
            example_match="",
        )

    sample = valid_examples[0]

    # Check for date patterns
    if re.match(r"^(?:0[1-9]|[12]\d|3[01])/(?:0[1-9]|1[0-2])/\d{4}$", sample):
        pattern = "{DD}/{MM}/{YYYY}"
        comp = compile_human_pattern(pattern)
        return InferResult(pattern, comp.regex, 0.95, comp.example_match)

    if re.match(r"^(?:0[1-9]|1[0-2])/(?:0[1-9]|[12]\d|3[01])/\d{4}$", sample):
        pattern = "{MM}/{DD}/{YYYY}"
        comp = compile_human_pattern(pattern)
        return InferResult(pattern, comp.regex, 0.95, comp.example_match)

    if re.match(r"^\d{4}-\d{2}-\d{2}$", sample):
        pattern = "{YYYY}-{MM}-{DD}"
        comp = compile_human_pattern(pattern)
        return InferResult(pattern, comp.regex, 0.95, comp.example_match)

    # Check for currency
    if re.match(r"^[\$£€₹]\s?[\d,]+(?:\.\d{2})?$", sample):
        pattern = "{MONEY}"
        comp = compile_human_pattern(pattern)
        return InferResult(pattern, comp.regex, 0.95, comp.example_match)

    # Segment based token analysis: e.g. SN-2026-001234
    segments = re.split(r"([\-_/:\s])", sample)
    inferred_segments: list[str] = []

    for seg in segments:
        if not seg:
            continue
        if seg in ["-", "_", "/", ":", " "]:
            inferred_segments.append(seg)
        elif re.match(r"^\d{4}$", seg) and (1990 <= int(seg) <= 2050):
            inferred_segments.append("{YYYY}")
        elif re.match(r"^\d+$", seg):
            length = len(seg)
            if length == 6:
                inferred_segments.append("{NNNNNN}")
            elif length == 5:
                inferred_segments.append("{NNNNN}")
            elif length == 4:
                inferred_segments.append("{NNNN}")
            elif length == 3:
                inferred_segments.append("{NNN}")
            elif length == 2:
                inferred_segments.append("{NN}")
            elif length == 1:
                inferred_segments.append("{N}")
            else:
                inferred_segments.append("{ANY}")
        elif re.match(r"^[A-Za-z]+$", seg):
            # Check if all examples share the exact same prefix/segment
            all_match = all(e.startswith(seg) or seg in e for e in valid_examples)
            if all_match and len(valid_examples) > 1:
                inferred_segments.append(seg)
            else:
                length = len(seg)
                if length <= 4:
                    inferred_segments.append("{" + ("A" * length) + "}")
                else:
                    inferred_segments.append("{TEXT}")
        else:
            inferred_segments.append(seg)

    inferred_pattern = "".join(inferred_segments)
    comp = compile_human_pattern(inferred_pattern)
    return InferResult(
        inferred_human_pattern=inferred_pattern,
        regex=comp.regex,
        confidence=0.9,
        example_match=sample,
    )


def infer_from_description(description: str) -> InferResult:
    """Parse a plain-language description into a human pattern."""
    desc = description.strip().lower()

    pattern_parts: list[str] = []

    # Detect prefix
    starts_with_match = re.search(r"starts with\s+['\"]?([a-zA-Z0-9_\-]+)['\"]?", desc)
    if starts_with_match:
        prefix = starts_with_match.group(1).upper()
        # check if delimiter mentioned or present
        pattern_parts.append(prefix)

    # Detect separator
    sep = "-"
    if "slash" in desc:
        sep = "/"
    elif "underscore" in desc:
        sep = "_"
    elif "space" in desc:
        sep = " "

    # Check for date components
    if "day" in desc and "month" in desc and "year" in desc:
        pattern = f"{{DD}}{sep}{{MM}}{sep}{{YYYY}}"
        comp = compile_human_pattern(pattern)
        return InferResult(pattern, comp.regex, 0.85, comp.example_match)

    # Check for year
    if "year" in desc:
        if pattern_parts:
            pattern_parts.append(sep)
        pattern_parts.append("{YYYY}")

    # Check for numbers / digits count
    digit_words = {
        "six": "{NNNNNN}",
        "6": "{NNNNNN}",
        "five": "{NNNNN}",
        "5": "{NNNNN}",
        "four": "{NNNN}",
        "4": "{NNNN}",
        "three": "{NNN}",
        "3": "{NNN}",
        "two": "{NN}",
        "2": "{NN}",
        "one": "{N}",
        "1": "{N}",
    }

    for word, token in digit_words.items():
        if f"{word} numbers" in desc or f"{word} digits" in desc:
            if pattern_parts and not pattern_parts[-1].endswith(sep):
                pattern_parts.append(sep)
            pattern_parts.append(token)
            break

    # Check for letters
    for word, count in [("four", 4), ("4", 4), ("three", 3), ("3", 3), ("two", 2), ("2", 2), ("one", 1), ("1", 1)]:
        if f"{word} letters" in desc:
            if pattern_parts and not pattern_parts[-1].endswith(sep):
                pattern_parts.append(sep)
            pattern_parts.append("{" + ("A" * count) + "}")
            break

    # Email / Phone / Currency checks
    if "email" in desc:
        pattern = "{EMAIL}"
        comp = compile_human_pattern(pattern)
        return InferResult(pattern, comp.regex, 0.9, comp.example_match)
    if "phone" in desc:
        pattern = "{PHONE}"
        comp = compile_human_pattern(pattern)
        return InferResult(pattern, comp.regex, 0.9, comp.example_match)
    if "currency" in desc or "money" in desc or "amount" in desc or "price" in desc:
        pattern = "{MONEY}"
        comp = compile_human_pattern(pattern)
        return InferResult(pattern, comp.regex, 0.9, comp.example_match)

    if not pattern_parts:
        pattern_parts = ["{ANY}"]

    inferred_pattern = "".join(pattern_parts)
    comp = compile_human_pattern(inferred_pattern)
    return InferResult(
        inferred_human_pattern=inferred_pattern,
        regex=comp.regex,
        confidence=0.8,
        example_match=comp.example_match,
    )
