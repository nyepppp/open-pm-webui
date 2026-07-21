"""Skill invocation API endpoints.

Provides REST API for invoking PM skills via `/pm-<id>` commands
and managing skill execution.

#33 Security governance: 所有端点强制 get_verified_user 认证;
invoke_skill / get_skill_details 额外做 require_extension_access RBAC 检查.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from open_webui.pm.skills.registry import get_skill, list_skills
from open_webui.utils.auth import get_verified_user
from open_webui.utils.acl import require_extension_access

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
async def list_available_skills(user=Depends(get_verified_user)):
    """List all available PM skills.

    #33: 强制认证 (列出可用 skill 列表, 无 RBAC 限制).

    Returns:
        List of skill metadata
    """
    return {"skills": list_skills()}


@router.post("/{skill_id}/invoke")
async def invoke_skill(
    skill_id: str,
    request: SkillInvokeRequest,
    user=Depends(get_verified_user),
) -> SkillInvokeResponse:
    """Invoke a PM skill.

    #33: 强制认证 + require_extension_access('skill', skill_id, level='execute').
    Admin bypass. 普通用户需在 pm_permission 表中有 execute grant.

    Args:
        skill_id: Skill identifier (e.g., "pm-generate-test-cases")
        request: Invocation parameters

    Returns:
        Skill execution result
    """
    skill = get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found")

    # #33 RBAC: 检查 user 对该 skill 的 execute 权限
    await require_extension_access(
        resource_type="skill",
        resource_id=skill_id,
        actor_user_id=user.id,
        actor_role=user.role,
        required_level="execute",
    )

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
async def get_skill_details(
    skill_id: str,
    user=Depends(get_verified_user),
):
    """Get detailed information about a skill.

    #33: 强制认证 + require_extension_access('skill', skill_id, level='read').

    Args:
        skill_id: Skill identifier

    Returns:
        Skill metadata and configuration
    """
    skill = get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found")

    # #33 RBAC: 检查 user 对该 skill 的 read 权限
    await require_extension_access(
        resource_type="skill",
        resource_id=skill_id,
        actor_user_id=user.id,
        actor_role=user.role,
        required_level="read",
    )

    return {
        "id": skill.id,
        "name": skill.name,
        "description": skill.description,
        "icon": skill.icon,
        "system_prompt": skill.system_prompt,
    }
