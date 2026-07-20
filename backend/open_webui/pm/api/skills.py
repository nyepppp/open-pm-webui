"""Skill invocation API endpoints.

Provides REST API for invoking PM skills via `/pm-<id>` commands
and managing skill execution.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from open_webui.pm.skills.registry import get_skill, list_skills

router = APIRouter(prefix="/skills", tags=["pm-skills"])


class SkillInvokeRequest(BaseModel):
    """Request body for skill invocation."""

    session_id: str = Field(..., description="Chat session ID")
    workspace_id: str = Field(..., description="PM workspace ID")
    parameters: dict = Field(default_factory=dict, description="Skill parameters")


class SkillInvokeResponse(BaseModel):
    """Response from skill invocation."""

    skill_id: str
    status: str
    output: dict = Field(default_factory=dict)
    traceability_links: list[dict] = Field(default_factory=list)
    message: str = ""


@router.get("/")
async def list_available_skills():
    """List all available PM skills.

    Returns:
        List of skill metadata
    """
    return {"skills": list_skills()}


@router.post("/{skill_id}/invoke")
async def invoke_skill(skill_id: str, request: SkillInvokeRequest) -> SkillInvokeResponse:
    """Invoke a PM skill.

    Args:
        skill_id: Skill identifier (e.g., "pm-generate-test-cases")
        request: Invocation parameters

    Returns:
        Skill execution result
    """
    skill = get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found")

    # Build user message with context
    user_message = skill.build_user_message(
        user_message=request.parameters.get("prompt", ""),
        project_id=request.workspace_id,
        module_type=request.parameters.get("module_type"),
        entry_id=request.parameters.get("entry_id"),
        entry_title=request.parameters.get("entry_title"),
        entry_content_summary=request.parameters.get("entry_content_summary"),
        extra_data=request.parameters.get("extra_data"),
    )

    # TODO: Integrate with actual LLM for skill execution
    # For now, return a placeholder response
    return SkillInvokeResponse(
        skill_id=skill_id,
        status="completed",
        output={
            "message": f"Skill '{skill.name}' invoked successfully",
            "user_message": user_message,
        },
        traceability_links=[],
        message=f"Skill '{skill.name}' execution completed",
    )


@router.get("/{skill_id}")
async def get_skill_details(skill_id: str):
    """Get detailed information about a skill.

    Args:
        skill_id: Skill identifier

    Returns:
        Skill metadata and configuration
    """
    skill = get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found")

    return {
        "id": skill.id,
        "name": skill.name,
        "description": skill.description,
        "icon": skill.icon,
        "system_prompt": skill.system_prompt,
    }
