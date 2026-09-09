"""OCR error tolerance and character confusion layer.

Provides targeted substitutions for common OCR recognition confusions:
- O <-> 0
- I <-> 1 <-> l
- S <-> 5
- B <-> 8
- G <-> 6
- Z <-> 2
"""
from __future__ import annotations

import re

# Character confusion groups for OCR
CONFUSION_MAP: dict[str, str] = {
    "O": "[O0]",
    "0": "[0O]",
    "I": "[Il1]",
    "l": "[l1I]",
    "1": "[1Il]",
    "S": "[S5]",
    "5": "[5S]",
    "B": "[B8]",
    "8": "[8B]",
    "G": "[G6]",
    "6": "[6G]",
    "Z": "[Z2]",
    "2": "[2Z]",
}


def make_ocr_tolerant(regex_pattern: str, alphanumeric_only: bool = True) -> str:
    """Convert literal alphanumeric portions of a regex pattern into OCR-tolerant character classes.

    Does not modify regex escape sequences (e.g., \\d, \\s, \\w) or pure numeric quantifier ranges (e.g. \\d{4}).
    """
    if not regex_pattern:
        return regex_pattern

    # Tokenize regex to avoid modifying escape sequences, character classes or quantifiers
    # Matches:
    # 1. Escape sequences like \d, \w, \s, \-, etc.
    # 2. Existing bracket classes like [A-Z], [0-9]
    # 3. Quantifiers like {4}, {1,2}
    # 4. Operators like (?:, ), |, +, *, ?, ^, $
    # 5. Literal characters
    token_pattern = re.compile(
        r'(\\[a-zA-Z0-9_\-\.\+]|\[[^\]]+\]|\{[^\}]+\}|\(\?:|\(|\)|\^|\$|\||\+|\*|\?|.)'
    )

    tokens = token_pattern.findall(regex_pattern)
    result: list[str] = []

    for token in tokens:
        if len(token) == 1 and token in CONFUSION_MAP:
            result.append(CONFUSION_MAP[token])
        else:
            result.append(token)

    return "".join(result)
