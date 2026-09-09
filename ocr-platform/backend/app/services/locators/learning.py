"""Multi-example locator learning: builds generalized locators from multiple annotations."""
from __future__ import annotations

import json
from collections import Counter
from typing import Any

from app.services.pattern.human_parser import infer_from_examples
from app.services.pattern.type_inferrer import infer_output_type


def learn_generalized_locator(examples: list[dict[str, Any]]) -> dict[str, Any]:
    """Derive a robust, generalized locator configuration from multiple document examples.

    Args:
        examples: List of dicts, each containing:
            - selected_text: str
            - bbox_x, bbox_y, bbox_width, bbox_height: int
            - page_width, page_height: int
            - nearby_labels: list[str] (optional)

    Returns:
        Generalized locator configuration dictionary.
    """
    if not examples:
        return {}

    rel_boxes: list[tuple[float, float, float, float]] = []
    text_samples: list[str] = []
    all_anchors: list[str] = []

    for ex in examples:
        pw = max(1, ex.get("page_width", 1000))
        ph = max(1, ex.get("page_height", 1400))
        rx = ex.get("bbox_x", 0) / pw
        ry = ex.get("bbox_y", 0) / ph
        rw = ex.get("bbox_width", 100) / pw
        rh = ex.get("bbox_height", 25) / ph
        rel_boxes.append((rx, ry, rw, rh))

        t = ex.get("selected_text", "").strip()
        if t:
            text_samples.append(t)

        labels = ex.get("nearby_labels", [])
        if isinstance(labels, str):
            try:
                labels = json.loads(labels)
            except Exception:
                labels = [labels]
        all_anchors.extend(labels)

    # 1. Spatial aggregation
    avg_x = sum(b[0] for b in rel_boxes) / len(rel_boxes)
    avg_y = sum(b[1] for b in rel_boxes) / len(rel_boxes)
    avg_w = sum(b[2] for b in rel_boxes) / len(rel_boxes)
    avg_h = sum(b[3] for b in rel_boxes) / len(rel_boxes)

    max_dx = max(abs(b[0] - avg_x) for b in rel_boxes)
    max_dy = max(abs(b[1] - avg_y) for b in rel_boxes)

    tolerance_x = max(0.06, round(max_dx * 1.5, 3))
    tolerance_y = max(0.04, round(max_dy * 1.5, 3))

    # 2. Common anchors (anchors present in multiple examples)
    anchor_counts = Counter(all_anchors)
    sorted_anchors = [anchor for anchor, count in anchor_counts.most_common(5) if count >= 1]

    # 3. Pattern & Type inference
    pattern_res = infer_from_examples(text_samples) if text_samples else None
    type_res = infer_output_type(examples=text_samples) if text_samples else None

    structure_config = {
        "example_count": len(examples),
        "spatial_stability": "high" if max_dx < 0.05 and max_dy < 0.05 else "medium",
        "expected_type": type_res.inferred_type if type_res else "text",
        "same_line": bool(sorted_anchors),
    }

    return {
        "rel_x": round(avg_x, 4),
        "rel_y": round(avg_y, 4),
        "rel_width": round(avg_w, 4),
        "rel_height": round(avg_h, 4),
        "tolerance_x": tolerance_x,
        "tolerance_y": tolerance_y,
        "anchor_candidates": sorted_anchors,
        "pattern_value": pattern_res.regex if pattern_res else None,
        "human_pattern": pattern_res.inferred_human_pattern if pattern_res else None,
        "structure_config": structure_config,
    }
