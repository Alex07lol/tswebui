"""Consumer-facing Field API endpoints within a Setup context."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.services.setup.field_service import FieldService

router = APIRouter()


class AddFieldRequest(BaseModel):
    display_name: str
    human_pattern: str | None = None
    examples: list[str] | None = None
    description: str | None = None
    ocr_text: str | None = None
    ocr_tolerant: bool = True


@router.get("/setups/{setup_id}/fields")
async def list_setup_fields(
    setup_id: str,
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    """List fields for a setup in simple mode."""
    return await FieldService.list_fields(session, setup_id)


@router.post("/setups/{setup_id}/fields", status_code=status.HTTP_201_CREATED)
async def add_setup_field(
    setup_id: str,
    payload: AddFieldRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Add a field using human pattern/examples with auto-generated extraction strategy."""
    try:
        return await FieldService.add_field(
            session=session,
            setup_id=setup_id,
            display_name=payload.display_name,
            human_pattern=payload.human_pattern,
            examples=payload.examples,
            description=payload.description,
            ocr_text=payload.ocr_text,
            ocr_tolerant=payload.ocr_tolerant,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/setups/{setup_id}/fields/{field_id}")
async def delete_setup_field(
    setup_id: str,
    field_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Remove a field from a setup."""
    success = await FieldService.delete_field(session, setup_id, field_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Field '{field_id}' not found in setup")
    return {"message": f"Field '{field_id}' removed"}


@router.get("/setups/{setup_id}/fields/{field_id}/advanced")
async def get_field_advanced(
    setup_id: str,
    field_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Retrieve full raw technical configuration for Advanced Rule Editor."""
    field_data = await FieldService.get_field_advanced(session, setup_id, field_id)
    if not field_data:
        raise HTTPException(status_code=404, detail=f"Field '{field_id}' not found")
    return field_data
