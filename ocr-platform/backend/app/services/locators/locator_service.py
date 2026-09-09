"""Visual PDF Field Locator analysis, creation, and rule compilation."""
from __future__ import annotations

import json
import re
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.locator import ExtractionLocator, LocatorExample
from app.services.pattern.type_inferrer import infer_output_type


def analyze_pdf_selection(
    page_width: int,
    page_height: int,
    bbox_x: int,
    bbox_y: int,
    bbox_width: int,
    bbox_height: int,
    selected_text: str,
    page_words: list[dict[str, Any]],
) -> dict[str, Any]:
    """Analyze a visual selection on an OCR page to extract coordinates, anchors, and structure.

    Args:
        page_width: Page pixel width.
        page_height: Page pixel height.
        bbox_x: Left pixel offset.
        bbox_y: Top pixel offset.
        bbox_width: Selection width.
        bbox_height: Selection height.
        selected_text: Highlighted text.
        page_words: OCR word dictionaries with text, bbox_x, bbox_y, bbox_width, bbox_height.
    """
    pw = max(1, page_width)
    ph = max(1, page_height)

    rel_x = round(bbox_x / pw, 4)
    rel_y = round(bbox_y / ph, 4)
    rel_width = round(bbox_width / pw, 4)
    rel_height = round(bbox_height / ph, 4)

    line_threshold = max(15, int(bbox_height * 0.8))

    same_line_words: list[dict[str, Any]] = []
    line_above_words: list[dict[str, Any]] = []

    for w in page_words:
        wx = w.get("bbox_x", 0)
        wy = w.get("bbox_y", 0)
        wt = w.get("text", "").strip()
        if not wt:
            continue

        # Check if on same line and to the left of the selection
        if abs(wy - bbox_y) <= line_threshold and wx < bbox_x:
            same_line_words.append(w)
        # Check if on the line immediately above
        elif 0 < (bbox_y - wy) <= (line_threshold * 2.5) and abs(wx - bbox_x) <= (bbox_width + 100):
            line_above_words.append(w)

    # Sort left-to-right
    same_line_words.sort(key=lambda item: item.get("bbox_x", 0))
    line_above_words.sort(key=lambda item: item.get("bbox_x", 0))

    anchor_candidates: list[str] = []
    same_line_text = " ".join(w.get("text", "") for w in same_line_words).strip()
    line_above_text = " ".join(w.get("text", "") for w in line_above_words).strip()

    if same_line_text:
        anchor_candidates.append(same_line_text)
        # If ends with colon, clean and add that too
        cleaned = re.sub(r"[:\-_]+$", "", same_line_text).strip()
        if cleaned and cleaned not in anchor_candidates:
            anchor_candidates.append(cleaned)

    if line_above_text and line_above_text not in anchor_candidates:
        anchor_candidates.append(line_above_text)

    # Infer type
    type_res = infer_output_type(examples=[selected_text])
    inferred_type = type_res.inferred_type

    structure_config = {
        "same_line": bool(same_line_words),
        "has_line_above_anchor": bool(line_above_words),
        "expected_type": inferred_type,
        "word_count": len(selected_text.split()),
        "char_length": len(selected_text),
    }

    return {
        "selected_text": selected_text,
        "rel_x": rel_x,
        "rel_y": rel_y,
        "rel_width": rel_width,
        "rel_height": rel_height,
        "anchor_candidates": anchor_candidates,
        "structure_config": structure_config,
        "inferred_type": inferred_type,
        "same_line_context": same_line_text,
        "line_above_context": line_above_text,
    }


async def create_locator_from_selection(
    session: AsyncSession,
    field_id: str,
    selection_data: dict[str, Any],
    name: str | None = None,
    template_label: str | None = None,
    document_id: str | None = None,
    page_number: int = 1,
    pixel_bbox: tuple[int, int, int, int, int, int] | None = None,
) -> ExtractionLocator:
    """Persist a new ExtractionLocator from an analyzed PDF selection."""
    loc_id = str(uuid.uuid4())
    anchor_list = selection_data.get("anchor_candidates", [])
    structure_config = selection_data.get("structure_config", {})

    locator = ExtractionLocator(
        id=loc_id,
        field_id=field_id,
        name=name or f"Locator for {field_id}",
        template_label=template_label or "Default Layout",
        page_mode="first" if page_number == 1 else "specific",
        specific_page=page_number,
        rel_x=selection_data.get("rel_x"),
        rel_y=selection_data.get("rel_y"),
        rel_width=selection_data.get("rel_width"),
        rel_height=selection_data.get("rel_height"),
        anchor_candidates_json=json.dumps(anchor_list),
        structure_config_json=json.dumps(structure_config),
        pattern_value=selection_data.get("pattern_value"),
        tolerance_x=0.08,
        tolerance_y=0.05,
        confidence_weight=1.0,
        priority=100,
        is_enabled=True,
    )
    session.add(locator)

    # Optional initial example
    if document_id and pixel_bbox:
        bx, by, bw, bh, pw, ph = pixel_bbox
        example = LocatorExample(
            id=str(uuid.uuid4()),
            locator_id=loc_id,
            document_id=document_id,
            page_number=page_number,
            selected_text=selection_data.get("selected_text", ""),
            bbox_x=bx,
            bbox_y=by,
            bbox_width=bw,
            bbox_height=bh,
            page_width=pw,
            page_height=ph,
            nearby_labels_json=json.dumps(anchor_list),
            ocr_confidence=selection_data.get("ocr_confidence", 1.0),
        )
        session.add(example)

    await session.commit()
    await session.refresh(locator)
    return locator


def compile_locator_to_rule(locator: ExtractionLocator, output_variable: str | None = None) -> dict[str, Any]:
    """Compile an ExtractionLocator into a standard ExtractionRule dictionary."""
    anchors = []
    if locator.anchor_candidates_json:
        try:
            anchors = json.loads(locator.anchor_candidates_json)
        except Exception:
            pass

    structure = {}
    if locator.structure_config_json:
        try:
            structure = json.loads(locator.structure_config_json)
        except Exception:
            pass

    anchor_val = anchors[0] if anchors else None
    strategy = "same_line" if (anchor_val and structure.get("same_line", True)) else ("anchored_pattern" if anchor_val else "region")

    anchor_config = None
    if anchor_val:
        anchor_config = json.dumps({
            "value": anchor_val,
            "match": "fuzzy",
            "minimum_similarity": 0.85,
        })

    search_config = None
    if anchor_val:
        search_config = json.dumps({
            "direction": "after",
            "scope": "same_line" if structure.get("same_line", True) else "next_line",
            "max_lines": 2,
        })

    pattern_config = None
    if locator.pattern_value:
        pattern_config = json.dumps({
            "type": "regex",
            "value": locator.pattern_value,
        })

    region_config = None
    if locator.rel_x is not None and locator.rel_y is not None:
        region_config = json.dumps({
            "rel_x": locator.rel_x,
            "rel_y": locator.rel_y,
            "rel_width": locator.rel_width or 0.2,
            "rel_height": locator.rel_height or 0.05,
            "tolerance_x": locator.tolerance_x,
            "tolerance_y": locator.tolerance_y,
        })

    return {
        "rule_name": locator.name or f"Visual Rule ({locator.template_label or 'Default'})",
        "strategy": strategy,
        "anchor_config": anchor_config,
        "search_config": search_config,
        "pattern_config": pattern_config,
        "region_config": region_config,
        "priority": locator.priority,
        "is_enabled": locator.is_enabled,
    }
