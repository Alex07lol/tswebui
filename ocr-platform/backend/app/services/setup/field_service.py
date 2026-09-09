"""Field service adapter.

Manages fields within a Setup, converting human definitions into
internal extraction configurations and rules automatically.
"""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.configuration import Configuration, ConfigurationVersion
from app.services.extraction.auto_strategy import generate_auto_strategy


def _confidence_to_label(conf: float) -> str:
    if conf >= 0.90:
        return "Very High"
    if conf >= 0.70:
        return "High"
    if conf >= 0.45:
        return "Medium"
    return "Low"


class FieldService:
    @staticmethod
    async def add_field(
        session: AsyncSession,
        setup_id: str,
        display_name: str,
        human_pattern: str | None = None,
        examples: list[str] | None = None,
        description: str | None = None,
        ocr_text: str | None = None,
        ocr_tolerant: bool = True,
    ) -> dict[str, Any]:
        stmt = (
            select(Configuration)
            .where(Configuration.id == setup_id)
            .options(selectinload(Configuration.versions))
        )
        res = await session.execute(stmt)
        config = res.scalar_one_or_none()
        if not config or not config.versions:
            raise ValueError(f"Setup '{setup_id}' not found")

        latest_v = max(config.versions, key=lambda v: v.version_number)
        snapshot = {}
        if latest_v.config_snapshot:
            try:
                snapshot = json.loads(latest_v.config_snapshot)
            except Exception:
                snapshot = {}

        fields_list = snapshot.get("fields", [])

        # 1. Run Auto-Strategy to derive field configuration
        auto_res = generate_auto_strategy(
            display_name=display_name,
            human_pattern=human_pattern,
            examples=examples,
            description=description,
            ocr_text=ocr_text,
            ocr_tolerant=ocr_tolerant,
        )

        field_id = auto_res.field_id
        # Disambiguate field_id if already present
        existing_ids = {f.get("id") or f.get("field_id") for f in fields_list}
        if field_id in existing_ids:
            suffix = 2
            while f"{field_id}_{suffix}" in existing_ids:
                suffix += 1
            field_id = f"{field_id}_{suffix}"

        # 2. Build full ExtractionField structure
        field_payload = {
            "id": field_id,
            "name": display_name,
            "display_name": display_name,
            "output_variable": field_id,
            "output_type": auto_res.output_type,
            "human_pattern": auto_res.human_pattern,
            "examples": examples or [],
            "required": False,
            "rules": [auto_res.rule_dict],
            "confidence_score": auto_res.confidence,
            "explanation": auto_res.explanation,
        }

        fields_list.append(field_payload)
        snapshot["fields"] = fields_list
        latest_v.config_snapshot = json.dumps(snapshot)
        await session.flush()

        candidates_out = [
            {
                "value": c.value,
                "context_before": c.context_before,
                "context_after": c.context_after,
                "anchor_found": c.anchor_found,
                "confidence": c.confidence,
            }
            for c in auto_res.candidates
        ]

        return {
            "field_id": field_id,
            "display_name": display_name,
            "human_pattern": auto_res.human_pattern,
            "output_type": auto_res.output_type,
            "status": "ready",
            "confidence_label": _confidence_to_label(auto_res.confidence),
            "confidence_score": auto_res.confidence,
            "last_example_found": auto_res.candidates[0].value if auto_res.candidates else None,
            "explanation": auto_res.explanation,
            "strategy_used": auto_res.strategy,
            "ambiguous": auto_res.ambiguous,
            "candidates": candidates_out,
        }

    @staticmethod
    async def list_fields(session: AsyncSession, setup_id: str) -> list[dict[str, Any]]:
        stmt = (
            select(Configuration)
            .where(Configuration.id == setup_id)
            .options(selectinload(Configuration.versions))
        )
        res = await session.execute(stmt)
        config = res.scalar_one_or_none()
        if not config or not config.versions:
            return []

        latest_v = max(config.versions, key=lambda v: v.version_number)
        if not latest_v.config_snapshot:
            return []

        try:
            snapshot = json.loads(latest_v.config_snapshot)
        except Exception:
            return []

        result = []
        for f in snapshot.get("fields", []):
            fid = f.get("id") or f.get("field_id", "")
            dname = f.get("display_name") or f.get("name") or fid
            c_score = f.get("confidence_score", 0.90)
            result.append({
                "field_id": fid,
                "display_name": dname,
                "human_pattern": f.get("human_pattern") or "",
                "output_type": f.get("output_type") or "text",
                "status": "ready",
                "confidence_label": _confidence_to_label(c_score),
                "confidence_score": c_score,
                "explanation": f.get("explanation") or ["Default rule active"],
            })
        return result

    @staticmethod
    async def delete_field(session: AsyncSession, setup_id: str, field_id: str) -> bool:
        stmt = (
            select(Configuration)
            .where(Configuration.id == setup_id)
            .options(selectinload(Configuration.versions))
        )
        res = await session.execute(stmt)
        config = res.scalar_one_or_none()
        if not config or not config.versions:
            return False

        latest_v = max(config.versions, key=lambda v: v.version_number)
        if not latest_v.config_snapshot:
            return False

        snapshot = json.loads(latest_v.config_snapshot)
        existing_fields = snapshot.get("fields", [])
        new_fields = [f for f in existing_fields if (f.get("id") or f.get("field_id")) != field_id]

        if len(new_fields) == len(existing_fields):
            return False

        snapshot["fields"] = new_fields
        latest_v.config_snapshot = json.dumps(snapshot)
        await session.flush()
        return True

    @staticmethod
    async def get_field_advanced(
        session: AsyncSession, setup_id: str, field_id: str
    ) -> dict[str, Any] | None:
        stmt = (
            select(Configuration)
            .where(Configuration.id == setup_id)
            .options(selectinload(Configuration.versions))
        )
        res = await session.execute(stmt)
        config = res.scalar_one_or_none()
        if not config or not config.versions:
            return None

        latest_v = max(config.versions, key=lambda v: v.version_number)
        if not latest_v.config_snapshot:
            return None

        snapshot = json.loads(latest_v.config_snapshot)
        for f in snapshot.get("fields", []):
            if (f.get("id") or f.get("field_id")) == field_id:
                return f
        return None
