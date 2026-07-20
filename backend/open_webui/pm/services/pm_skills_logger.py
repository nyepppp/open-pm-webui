"""Logging and observability for pm-skills execution."""

import logging
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)


class PmSkillsLogger:
    """Logger for pm-skills execution events."""

    def __init__(self):
        pass

    def log_skill_execution(
        self,
        skill_id: str,
        project_id: str,
        user_id: str,
        duration_ms: float,
        status: str,
        error: Optional[str] = None,
    ) -> None:
        """Log skill execution event.

        Args:
            skill_id: Skill ID
            project_id: Project ID
            user_id: User ID
            duration_ms: Execution duration in milliseconds
            status: Execution status (success, error)
            error: Optional error message
        """
        log_data = {
            "event": "skill_execution",
            "skill_id": skill_id,
            "project_id": project_id,
            "user_id": user_id,
            "duration_ms": duration_ms,
            "status": status,
        }
        if error:
            log_data["error"] = error

        logger.info(f"Skill execution: {log_data}")

    def log_workflow_execution(
        self,
        workflow_name: str,
        project_id: str,
        user_id: str,
        duration_ms: float,
        status: str,
        steps_completed: int = 0,
        error: Optional[str] = None,
    ) -> None:
        """Log workflow execution event.

        Args:
            workflow_name: Workflow name
            project_id: Project ID
            user_id: User ID
            duration_ms: Execution duration in milliseconds
            status: Execution status
            steps_completed: Number of steps completed
            error: Optional error message
        """
        log_data = {
            "event": "workflow_execution",
            "workflow": workflow_name,
            "project_id": project_id,
            "user_id": user_id,
            "duration_ms": duration_ms,
            "status": status,
            "steps_completed": steps_completed,
        }
        if error:
            log_data["error"] = error

        logger.info(f"Workflow execution: {log_data}")

    def log_command_invocation(
        self,
        command_id: str,
        project_id: str,
        user_id: str,
        status: str,
    ) -> None:
        """Log command invocation event.

        Args:
            command_id: Command ID
            project_id: Project ID
            user_id: User ID
            status: Invocation status
        """
        log_data = {
            "event": "command_invocation",
            "command_id": command_id,
            "project_id": project_id,
            "user_id": user_id,
            "status": status,
        }

        logger.info(f"Command invocation: {log_data}")


# Singleton instance
pm_skills_logger = PmSkillsLogger()
