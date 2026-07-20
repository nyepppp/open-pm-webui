"""Confirmation service for pm-skills write operations."""

from typing import Any, Optional

from open_webui.pm.models.pm_skills_mapping import PmSkillsMappings


class ConfirmationService:
    """Service for managing confirmation gates on pm-skills outputs."""

    def __init__(self):
        pass

    async def requires_confirmation(self, skill_id: str) -> bool:
        """Check if a skill requires confirmation before persisting output.

        Args:
            skill_id: Skill ID

        Returns:
            True if confirmation is required
        """
        # All write operations require confirmation per Constitution Principle III
        # Check if skill is in mapping
        # For now, all pm-skills require confirmation
        return True

    async def confirm_output(
        self,
        invocation_id: str,
        confirmed: bool,
        feedback: Optional[str] = None,
    ) -> dict[str, Any]:
        """Confirm or reject a skill output.

        Args:
            invocation_id: Unique invocation ID
            confirmed: Whether the output is confirmed
            feedback: Optional user feedback

        Returns:
            Confirmation result
        """
        return {
            "invocation_id": invocation_id,
            "status": "confirmed" if confirmed else "rejected",
            "feedback": feedback,
        }

    async def get_pending_confirmations(self) -> list[dict[str, Any]]:
        """Get list of pending confirmations.

        Returns:
            List of pending confirmations
        """
        # In production, this would query the database
        return []


# Singleton instance
confirmation_service = ConfirmationService()
