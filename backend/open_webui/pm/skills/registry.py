"""Skill registry for PM workspace capabilities.

Central registry for all PM agent skills, enabling discovery and invocation
via skill IDs.
"""

from typing import Optional

from open_webui.pm.skills.base import BaseSkill
from open_webui.pm.skills.pm_generate_test_cases import (
    PMExtractParametersSkill,
    PMGenerateTestCasesSkill,
)
from open_webui.pm.skills.prd_to_mfp import PRDToMFPSkill

# Registry of all PM skills
_SKILL_REGISTRY: dict[str, type[BaseSkill]] = {
    PMGenerateTestCasesSkill.id: PMGenerateTestCasesSkill,
    PMExtractParametersSkill.id: PMExtractParametersSkill,
    PRDToMFPSkill.id: PRDToMFPSkill,  # D44: PRD → 模块-功能-参数 原子化转换
}


def get_skill(skill_id: str) -> Optional[BaseSkill]:
    """Get a skill instance by ID.

    Args:
        skill_id: The skill identifier (e.g., "pm-generate-test-cases")

    Returns:
        Skill instance or None if not found
    """
    skill_class = _SKILL_REGISTRY.get(skill_id)
    if skill_class:
        return skill_class()
    return None


def list_skills() -> list[dict]:
    """List all available skills with metadata.

    Returns:
        List of skill metadata dictionaries
    """
    return [
        {
            "id": skill_id,
            "name": skill_class().name,
            "description": skill_class().description,
            "icon": skill_class().icon,
        }
        for skill_id, skill_class in _SKILL_REGISTRY.items()
    ]


def register_skill(skill_id: str, skill_class: type[BaseSkill]) -> None:
    """Register a new skill in the registry.

    Args:
        skill_id: Unique skill identifier
        skill_class: Skill class inheriting from BaseSkill
    """
    _SKILL_REGISTRY[skill_id] = skill_class


def unregister_skill(skill_id: str) -> bool:
    """Remove a skill from the registry.

    Args:
        skill_id: Skill identifier to remove

    Returns:
        True if removed, False if not found
    """
    if skill_id in _SKILL_REGISTRY:
        del _SKILL_REGISTRY[skill_id]
        return True
    return False
