"""Skill wrapper functions for Timbal workflow integration."""

from typing import Any, Optional

from open_webui.pm.skills.pm_skills_loader import load_skill


async def wrap_skill_for_timbal(
    skill_id: str, **kwargs: Any
) -> dict[str, Any]:
    """Wrap a pm-skill for Timbal workflow execution.

    Args:
        skill_id: Skill ID in format "pm-skills/<plugin>/<skill>"
        **kwargs: Skill input parameters

    Returns:
        dict with skill execution results
    """
    skill = load_skill(skill_id)
    if not skill:
        raise ValueError(f"Skill not found: {skill_id}")

    # For now, return the skill content as output
    # In production, this would invoke the actual skill logic
    return {
        "skill_id": skill_id,
        "skill_name": skill.get("name", ""),
        "description": skill.get("description", ""),
        "content": skill.get("content", ""),
        "inputs": kwargs,
        "output": skill.get("content", ""),
    }


def create_skill_step(skill_id: str, input_bindings: Optional[dict] = None):
    """Create a Timbal workflow step for a pm-skill.

    Args:
        skill_id: Skill ID in format "pm-skills/<plugin>/<skill>"
        input_bindings: Mapping of workflow inputs to skill inputs

    Returns:
        dict with step configuration
    """
    return {
        "skill_id": skill_id,
        "input_bindings": input_bindings or {},
    }
