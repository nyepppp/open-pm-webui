"""Mapping API for admin configuration."""

from typing import Any, Optional

from fastapi import APIRouter, HTTPException

from open_webui.pm.models.pm_skills_mapping import PmSkillsMappingForm
from open_webui.pm.services.pm_skills_mapping_service import pm_skills_mapping_service

router = APIRouter(prefix="/api/pm/skills/mappings")


@router.get("/")
async def list_mappings() -> list[dict[str, Any]]:
    """List all mappings."""
    mappings = await pm_skills_mapping_service.list_mappings()
    return [m.model_dump() for m in mappings]


@router.get("/{mapping_id}")
async def get_mapping(mapping_id: str) -> dict[str, Any]:
    """Get a mapping by ID."""
    mapping = await pm_skills_mapping_service.get_mapping(mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return mapping.model_dump()


@router.post("/")
async def create_mapping(form_data: PmSkillsMappingForm) -> dict[str, Any]:
    """Create a new mapping."""
    mapping = await pm_skills_mapping_service.create_mapping(form_data)
    if not mapping:
        raise HTTPException(status_code=400, detail="Failed to create mapping")
    return mapping.model_dump()


@router.put("/{mapping_id}")
async def update_mapping(mapping_id: str, form_data: PmSkillsMappingForm) -> dict[str, Any]:
    """Update a mapping."""
    mapping = await pm_skills_mapping_service.update_mapping(mapping_id, form_data)
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return mapping.model_dump()


@router.delete("/{mapping_id}")
async def delete_mapping(mapping_id: str) -> dict[str, Any]:
    """Delete a mapping."""
    success = await pm_skills_mapping_service.delete_mapping(mapping_id)
    if not success:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return {"status": "success"}
