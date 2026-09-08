"""Tests for table and line-item extraction subsystem."""
from __future__ import annotations

import pytest
from app.providers.ocr.base import BoundingBox, OCRPage, OCRWord
from app.services.extraction.table import TableExtractor


def test_table_extractor_structure() -> None:
    """Test TableExtractor on synthetic OCR words organized in rows and columns."""
    # Create synthetic words representing:
    # Line 1 (Header): Item     Qty    Price    Total
    # Line 2 (Row 1):  Widget   2      10.00    20.00
    # Line 3 (Row 2):  Gadget   1      35.50    35.50
    words = [
        # Line 1: Header
        OCRWord(text="Item", confidence=0.99, bounding_box=BoundingBox(10, 10, 50, 20), word_index=0, line_number=1),
        OCRWord(text="Qty", confidence=0.98, bounding_box=BoundingBox(100, 10, 40, 20), word_index=1, line_number=1),
        OCRWord(text="Price", confidence=0.97, bounding_box=BoundingBox(200, 10, 50, 20), word_index=2, line_number=1),
        OCRWord(text="Total", confidence=0.99, bounding_box=BoundingBox(300, 10, 50, 20), word_index=3, line_number=1),
        # Line 2: Row 1
        OCRWord(text="Widget", confidence=0.95, bounding_box=BoundingBox(10, 40, 60, 20), word_index=0, line_number=2),
        OCRWord(text="2", confidence=0.96, bounding_box=BoundingBox(105, 40, 20, 20), word_index=1, line_number=2),
        OCRWord(text="10.00", confidence=0.94, bounding_box=BoundingBox(205, 40, 45, 20), word_index=2, line_number=2),
        OCRWord(text="20.00", confidence=0.95, bounding_box=BoundingBox(305, 40, 45, 20), word_index=3, line_number=2),
        # Line 3: Row 2
        OCRWord(text="Gadget", confidence=0.96, bounding_box=BoundingBox(10, 70, 60, 20), word_index=0, line_number=3),
        OCRWord(text="1", confidence=0.98, bounding_box=BoundingBox(105, 70, 20, 20), word_index=1, line_number=3),
        OCRWord(text="35.50", confidence=0.93, bounding_box=BoundingBox(205, 70, 45, 20), word_index=2, line_number=3),
        OCRWord(text="35.50", confidence=0.94, bounding_box=BoundingBox(305, 70, 45, 20), word_index=3, line_number=3),
    ]

    page = OCRPage(page_number=1, width=500, height=300, text="", words=words)
    result = TableExtractor.extract_table(page, expected_columns=["item", "qty", "price", "total"])

    assert len(result.rows) == 2
    assert "item" in result.headers
    assert "qty" in result.headers
    assert "price" in result.headers
    assert "total" in result.headers

    # Check raw data
    assert len(result.raw_data) == 2
    row1 = result.raw_data[0]
    assert row1["item"] == "Widget"
    assert row1["qty"] == "2"
    assert row1["price"] == "10.00"
    assert row1["total"] == "20.00"

    row2 = result.raw_data[1]
    assert row2["item"] == "Gadget"
    assert row2["qty"] == "1"
    assert row2["price"] == "35.50"
    assert row2["total"] == "35.50"

    assert result.confidence > 0.9
