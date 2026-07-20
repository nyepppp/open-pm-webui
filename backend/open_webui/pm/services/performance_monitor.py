"""Performance monitoring for pm-skills."""

import time
from typing import Any, Optional

from open_webui.pm.services.pm_skills_logger import pm_skills_logger


class PerformanceMonitor:
    """Monitor performance of pm-skills execution."""

    def __init__(self):
        pass

    async def monitor_skill_execution(
        self,
        skill_id: str,
        project_id: str,
        user_id: str,
        start_time: float,
        end_time: float,
        status: str,
    ) -> dict[str, Any]:
        """Monitor skill execution performance.

        Args:
            skill_id: Skill ID
            project_id: Project ID
            user_id: User ID
            start_time: Start time (time.time())
            end_time: End time (time.time())
            status: Execution status

        Returns:
            Performance metrics
        """
        duration_ms = (end_time - start_time) * 1000

        # Log performance
        pm_skills_logger.log_skill_execution(
            skill_id=skill_id,
            project_id=project_id,
            user_id=user_id,
            duration_ms=duration_ms,
            status=status,
        )

        return {
            "skill_id": skill_id,
            "duration_ms": duration_ms,
            "status": status,
            "meets_sla": duration_ms <= 3000,  # Tool calls ≤ 3s
        }

    async def monitor_skill_loading(
        self,
        skill_id: str,
        start_time: float,
        end_time: float,
    ) -> dict[str, Any]:
        """Monitor skill loading performance.

        Args:
            skill_id: Skill ID
            start_time: Start time
            end_time: End time

        Returns:
            Performance metrics
        """
        duration_ms = (end_time - start_time) * 1000

        return {
            "skill_id": skill_id,
            "duration_ms": duration_ms,
            "meets_sla": duration_ms <= 1000,  # Skill loading ≤ 1s
        }

    async def monitor_workflow_execution(
        self,
        workflow_name: str,
        project_id: str,
        user_id: str,
        start_time: float,
        end_time: float,
        steps_completed: int,
        status: str,
    ) -> dict[str, Any]:
        """Monitor workflow execution performance.

        Args:
            workflow_name: Workflow name
            project_id: Project ID
            user_id: User ID
            start_time: Start time
            end_time: End time
            steps_completed: Number of steps completed
            status: Execution status

        Returns:
            Performance metrics
        """
        duration_ms = (end_time - start_time) * 1000

        pm_skills_logger.log_workflow_execution(
            workflow_name=workflow_name,
            project_id=project_id,
            user_id=user_id,
            duration_ms=duration_ms,
            status=status,
            steps_completed=steps_completed,
        )

        return {
            "workflow": workflow_name,
            "duration_ms": duration_ms,
            "status": status,
            "steps_completed": steps_completed,
            "meets_sla": duration_ms <= 5000,  # Workflow execution ≤ 5s
        }


# Singleton instance
performance_monitor = PerformanceMonitor()
