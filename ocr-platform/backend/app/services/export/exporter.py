"""Extraction results export service (JSON, CSV, tabular)."""
from __future__ import annotations

import csv
import io
import json
from typing import Any

from app.models.extraction import ExtractionResult


class ResultExporter:
    """Formats extraction results into standardized machine-readable formats."""

    @staticmethod
    def to_dict(result: ExtractionResult) -> dict[str, Any]:
        """Convert an ExtractionResult ORM instance to a structured dictionary."""
        fields_dict: dict[str, Any] = {}
        provenance_dict: dict[str, Any] = {}

        for val in getattr(result, "values", []):
            extracted = val.normalized_value if val.normalized_value is not None else val.raw_value
            # If the extracted value is a serialized JSON table, parse it
            if isinstance(extracted, str) and extracted.startswith("[{") and extracted.endswith("}]"):
                try:
                    extracted = json.loads(extracted)
                except Exception:
                    pass

            fields_dict[val.output_variable] = extracted
            provenance_dict[val.output_variable] = {
                "field_id": val.field_id,
                "raw_value": val.raw_value,
                "normalized_value": val.normalized_value,
                "confidence": val.final_confidence,
                "validation_passed": val.validation_passed,
                "validation_message": val.validation_message,
                "evidence": [
                    {
                        "rule_id": e.rule_id,
                        "anchor_text": e.anchor_text,
                        "source_line": e.source_line,
                        "ocr_confidence": e.ocr_confidence,
                        "bbox": {
                            "x": e.bbox_x,
                            "y": e.bbox_y,
                            "width": e.bbox_width,
                            "height": e.bbox_height,
                        },
                        "page_number": e.page_number,
                    }
                    for e in getattr(val, "evidence", [])
                ],
            }

        return {
            "result_id": result.id,
            "document_id": result.document_id,
            "config_version_id": result.config_version_id,
            "overall_confidence": result.overall_confidence,
            "extracted_data": fields_dict,
            "provenance": provenance_dict,
            "created_at": result.created_at.isoformat() if hasattr(result.created_at, "isoformat") else str(result.created_at),
        }

    @classmethod
    def to_json(cls, results: list[ExtractionResult] | ExtractionResult, indent: int = 2) -> str:
        """Export single or multiple results as a JSON formatted string."""
        if isinstance(results, list):
            data = [cls.to_dict(r) for r in results]
        else:
            data = cls.to_dict(results)
        return json.dumps(data, indent=indent, default=str)

    @classmethod
    def to_csv(cls, results: list[ExtractionResult]) -> str:
        """Export a list of results as a flattened CSV string."""
        if not results:
            return ""

        dicts = [cls.to_dict(r) for r in results]

        # Gather all unique column names across all results
        field_keys: set[str] = set()
        for d in dicts:
            for k in d.get("extracted_data", {}).keys():
                field_keys.add(k)

        sorted_fields = sorted(field_keys)
        headers = ["result_id", "document_id", "overall_confidence"] + sorted_fields

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()

        for d in dicts:
            row: dict[str, Any] = {
                "result_id": d["result_id"],
                "document_id": d["document_id"],
                "overall_confidence": d["overall_confidence"],
            }
            extracted_data = d.get("extracted_data", {})
            for k in sorted_fields:
                val = extracted_data.get(k, "")
                if isinstance(val, (dict, list)):
                    val = json.dumps(val)
                row[k] = val
            writer.writerow(row)

        return output.getvalue()
