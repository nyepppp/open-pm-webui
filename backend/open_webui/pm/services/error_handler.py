"""Error handling and fallback for pm-skills integration."""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class PmSkillsError(Exception):
    """Base exception for pm-skills integration."""

    def __init__(self, message: str, skill_id: Optional[str] = None):
        self.message = message
        self.skill_id = skill_id
        super().__init__(self.message)


class SkillNotFoundError(PmSkillsError):
    """Raised when a skill is not found."""

    pass


class SkillExecutionError(PmSkillsError):
    """Raised when skill execution fails."""

    pass


class WorkflowExecutionError(PmSkillsError):
    """Raised when workflow execution fails."""

    pass


def handle_skill_error(error: Exception, skill_id: Optional[str] = None) -> dict[str, Any]:
    """Handle skill execution errors.

    Args:
        error: The exception that occurred
        skill_id: Optional skill ID

    Returns:
        Error response dict
    """
    logger.error(f"Skill execution error: {error}", exc_info=True)

    if isinstance(error, SkillNotFoundError):
        return {
            "status": "error",
            "error": f"Skill not found: {skill_id}",
            "skill_id": skill_id,
        }

    if isinstance(error, SkillExecutionError):
        return {
            "status": "error",
            "error": str(error),
            "skill_id": skill_id,
        }

    # Generic error
    return {
        "status": "error",
        "error": f"Unexpected error: {str(error)}",
        "skill_id": skill_id,
    }


def handle_workflow_error(error: Exception, workflow_name: Optional[str] = None) -> dict[str, Any]:
    """Handle workflow execution errors.

    Args:
        error: The exception that occurred
        workflow_name: Optional workflow name

    Returns:
        Error response dict
    """
    logger.error(f"Workflow execution error: {error}", exc_info=True)

    if isinstance(error, WorkflowExecutionError):
        return {
            "status": "error",
            "error": str(error),
            "workflow": workflow_name,
        }

    # Generic error
    return {
        "status": "error",
        "error": f"Unexpected workflow error: {str(error)}",
        "workflow": workflow_name,
    }
