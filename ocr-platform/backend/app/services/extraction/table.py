"""Structured table and line-item extraction subsystem."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.providers.ocr.base import BoundingBox, OCRPage, OCRWord
from app.services.extraction.anchors import get_line_number, get_word_bbox, get_word_index


@dataclass
class TableCell:
    text: str
    confidence: float
    bbox: dict[str, int]


@dataclass
class TableRow:
    row_number: int
    cells: dict[str, TableCell]
    bbox: dict[str, int]


@dataclass
class TableExtractionResult:
    headers: list[str]
    rows: list[TableRow]
    raw_data: list[dict[str, str]]
    confidence: float


class TableExtractor:
    """Detects tabular data, row bands, and column alignments on OCR pages."""

    DEFAULT_HEADERS = ["item", "description", "qty", "quantity", "unit price", "price", "amount", "total"]

    @classmethod
    def extract_table(
        cls,
        page: Any,
        expected_columns: list[str] | None = None,
        region_bbox: BoundingBox | None = None,
    ) -> TableExtractionResult:
        """Extract structured rows and columns from an OCR page."""
        words = getattr(page, "words", [])
        if not words:
            return TableExtractionResult(headers=[], rows=[], raw_data=[], confidence=0.0)

        # Filter by region if specified
        if region_bbox:
            words = [
                w
                for w in words
                if (
                    get_word_bbox(w).x >= region_bbox.x
                    and get_word_bbox(w).y >= region_bbox.y
                    and get_word_bbox(w).x + get_word_bbox(w).width <= region_bbox.x + region_bbox.width
                    and get_word_bbox(w).y + get_word_bbox(w).height <= region_bbox.y + region_bbox.height
                )
            ]

        # Group words by line
        lines_dict: dict[int, list[Any]] = {}
        for w in words:
            lines_dict.setdefault(get_line_number(w), []).append(w)

        sorted_lines = sorted(lines_dict.items(), key=lambda x: x[0])
        target_headers = [h.lower() for h in (expected_columns or cls.DEFAULT_HEADERS)]

        # 1. Detect header line: line containing highest number of matching header tokens
        best_header_line_num = -1
        best_header_words: list[Any] = []
        best_match_count = 0

        for line_num, line_words in sorted_lines:
            match_count = 0
            for w in line_words:
                clean_txt = w.text.lower().strip(" :-,")
                if any(h in clean_txt for h in target_headers):
                    match_count += 1
            if match_count > best_match_count:
                best_match_count = match_count
                best_header_line_num = line_num
                best_header_words = sorted(line_words, key=get_word_index)

        # If no explicit header found, use top line
        if best_match_count == 0 and sorted_lines:
            best_header_line_num = sorted_lines[0][0]
            best_header_words = sorted(sorted_lines[0][1], key=get_word_index)

        # 2. Compute column horizontal spans (x_min, x_max) from header words
        columns: list[dict[str, Any]] = []
        for idx, hw in enumerate(best_header_words):
            b = get_word_bbox(hw)
            col_name = hw.text.lower().strip(" :-,") or f"col_{idx + 1}"
            columns.append({"name": col_name, "x_min": b.x - 10, "x_max": b.x + b.width + 10})

        # Widen outer column bounds
        if columns:
            columns[0]["x_min"] = 0
            columns[-1]["x_max"] = 99999
            # Fill intermediate gaps between columns
            for i in range(len(columns) - 1):
                mid = (columns[i]["x_max"] + columns[i + 1]["x_min"]) // 2
                columns[i]["x_max"] = mid
                columns[i + 1]["x_min"] = mid

        # 3. Detect row bands below the header line
        table_rows: list[TableRow] = []
        raw_rows: list[dict[str, str]] = []
        row_idx = 1

        for line_num, line_words in sorted_lines:
            if line_num <= best_header_line_num:
                continue

            row_words = sorted(line_words, key=get_word_index)
            if not row_words:
                continue

            row_cells: dict[str, TableCell] = {}
            raw_cell_map: dict[str, str] = {}

            # Map words in this row to columns
            for col in columns:
                col_name = col["name"]
                c_min, c_max = col["x_min"], col["x_max"]

                matching = [
                    w for w in row_words if c_min <= (get_word_bbox(w).x + get_word_bbox(w).width // 2) <= c_max
                ]
                if matching:
                    cell_text = " ".join(w.text for w in matching)
                    avg_conf = sum(
                        float(getattr(w, "confidence", 0.9) or 0.9) for w in matching
                    ) / len(matching)
                    min_x = min(get_word_bbox(w).x for w in matching)
                    min_y = min(get_word_bbox(w).y for w in matching)
                    max_x = max(get_word_bbox(w).x + get_word_bbox(w).width for w in matching)
                    max_y = max(get_word_bbox(w).y + get_word_bbox(w).height for w in matching)

                    cell = TableCell(
                        text=cell_text,
                        confidence=round(avg_conf, 4),
                        bbox={"x": min_x, "y": min_y, "width": max_x - min_x, "height": max_y - min_y},
                    )
                    row_cells[col_name] = cell
                    raw_cell_map[col_name] = cell_text

            if raw_cell_map:
                row_min_x = min(get_word_bbox(w).x for w in row_words)
                row_min_y = min(get_word_bbox(w).y for w in row_words)
                row_max_x = max(get_word_bbox(w).x + get_word_bbox(w).width for w in row_words)
                row_max_y = max(get_word_bbox(w).y + get_word_bbox(w).height for w in row_words)

                table_rows.append(
                    TableRow(
                        row_number=row_idx,
                        cells=row_cells,
                        bbox={
                            "x": row_min_x,
                            "y": row_min_y,
                            "width": row_max_x - row_min_x,
                            "height": row_max_y - row_min_y,
                        },
                    )
                )
                raw_rows.append(raw_cell_map)
                row_idx += 1

        header_names = [c["name"] for c in columns]
        overall_conf = (
            sum(
                sum(c.confidence for c in r.cells.values()) / max(1, len(r.cells))
                for r in table_rows
            )
            / max(1, len(table_rows))
            if table_rows
            else 0.0
        )

        return TableExtractionResult(
            headers=header_names,
            rows=table_rows,
            raw_data=raw_rows,
            confidence=round(overall_conf, 4),
        )
