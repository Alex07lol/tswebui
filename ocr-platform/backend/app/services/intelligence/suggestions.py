"""Heuristic AI-assisted field and rule suggestion engine.

Given raw OCR tokens, suggests standard document fields,
candidate anchor phrases, and regex patterns — no external LLM required.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.logging import get_logger

log = get_logger(__name__)

FIELD_CATALOGUE: list[dict] = [
    {
        "field_name": "invoice_number",
        "aliases": ["invoice #", "invoice no", "inv #", "inv no", "invoice number", "bill no"],
        "pattern": r"(?:INV|INVOICE|BILL)[-\s]?\d+",
        "example": "INV-2024-001",
    },
    {
        "field_name": "po_number",
        "aliases": ["po #", "p.o. number", "purchase order", "po number", "order no"],
        "pattern": r"(?:PO|P\.O\.)[-\s]?\d+",
        "example": "PO-12345",
    },
    {
        "field_name": "invoice_date",
        "aliases": ["invoice date", "date", "bill date", "issued", "date issued"],
        "pattern": r"\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}",
        "example": "01/15/2024",
    },
    {
        "field_name": "due_date",
        "aliases": ["due date", "payment due", "pay by", "net 30", "net 60"],
        "pattern": r"\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}",
        "example": "02/15/2024",
    },
    {
        "field_name": "total_amount",
        "aliases": ["total", "amount due", "grand total", "total due", "balance due", "amount payable"],
        "pattern": r"\$?[\d,]+\.\d{2}",
        "example": "$1,234.56",
    },
    {
        "field_name": "subtotal",
        "aliases": ["subtotal", "sub-total", "net amount"],
        "pattern": r"\$?[\d,]+\.\d{2}",
        "example": "$1,000.00",
    },
    {
        "field_name": "tax_amount",
        "aliases": ["tax", "vat", "gst", "hst", "sales tax", "tax amount"],
        "pattern": r"\$?[\d,]+\.\d{2}",
        "example": "$234.56",
    },
    {
        "field_name": "vendor_name",
        "aliases": ["from", "bill from", "company", "supplier", "vendor", "sold by"],
        "pattern": None,
        "example": "Acme Corp",
    },
    {
        "field_name": "customer_name",
        "aliases": ["bill to", "ship to", "customer", "client", "sold to"],
        "pattern": None,
        "example": "John Doe",
    },
    {
        "field_name": "tax_id",
        "aliases": ["tax id", "tin", "ein", "vat number", "tax number", "federal id"],
        "pattern": r"\d{2}-\d{7}|\d{3}-\d{2}-\d{4}",
        "example": "12-3456789",
    },
    {
        "field_name": "iban",
        "aliases": ["iban", "bank account", "account number"],
        "pattern": r"[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}(?:[A-Z0-9]?){0,16}",
        "example": "GB29NWBK60161331926819",
    },
    {
        "field_name": "swift_code",
        "aliases": ["swift", "bic", "swift code", "bic code"],
        "pattern": r"[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?",
        "example": "NWBKGB2L",
    },
]


@dataclass
class FieldSuggestion:
    field_name: str
    confidence: float
    matched_alias: str
    pattern: str | None
    example: str
    strategy: str


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).lower().strip()


def suggest_fields(ocr_text: str, top_k: int = 10) -> list[FieldSuggestion]:
    """Given raw OCR text, return the top-k field suggestions."""
    normalised = _normalise(ocr_text)
    suggestions: list[FieldSuggestion] = []

    for entry in FIELD_CATALOGUE:
        best_alias: str | None = None
        alias_confidence = 0.0

        for alias in entry["aliases"]:
            if _normalise(alias) in normalised:
                conf = min(1.0, 0.5 + len(alias) / 40.0)
                if conf > alias_confidence:
                    alias_confidence = conf
                    best_alias = alias

        pattern_confidence = 0.0
        if entry["pattern"]:
            try:
                if re.search(entry["pattern"], ocr_text, re.IGNORECASE):
                    pattern_confidence = 0.6
            except re.error:
                pass

        if best_alias or pattern_confidence > 0:
            confidence = max(alias_confidence, pattern_confidence)
            strategy = "alias_match" if alias_confidence >= pattern_confidence else "pattern_match"
            suggestions.append(
                FieldSuggestion(
                    field_name=entry["field_name"],
                    confidence=confidence,
                    matched_alias=best_alias or "",
                    pattern=entry["pattern"],
                    example=entry["example"],
                    strategy=strategy,
                )
            )

    suggestions.sort(key=lambda s: s.confidence, reverse=True)
    log.info("Field suggestions generated", count=len(suggestions), top_k=top_k)
    return suggestions[:top_k]
