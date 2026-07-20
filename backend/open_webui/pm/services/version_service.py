"""Version service for pm-skills version management."""

from typing import Any, Optional

from open_webui.pm.models.pm_skills_version import (
    PmSkillsVersionForm,
    PmSkillsVersions,
)


class VersionService:
    """Service for managing pm-skills versions."""

    def __init__(self):
        pass

    async def get_version(self, command_id: str) -> Optional[dict[str, Any]]:
        """Get version for a command.

        Args:
            command_id: Command ID

        Returns:
            Version dict or None
        """
        version = await PmSkillsVersions.get_version_by_command_id(command_id)
        return version.model_dump() if version else None

    async def set_version(
        self, command_id: str, version: str, methodology_hash: str
    ) -> dict[str, Any]:
        """Set version for a command.

        Args:
            command_id: Command ID
            version: Version string
            methodology_hash: Hash of SKILL.md content

        Returns:
            Updated version
        """
        form_data = PmSkillsVersionForm(
            command_id=command_id,
            version=version,
            methodology_hash=methodology_hash,
        )
        result = await PmSkillsVersions.insert_new_version(form_data)
        return result.model_dump() if result else {}

    async def list_versions(self) -> list[dict[str, Any]]:
        """List all versions.

        Returns:
            List of version dicts
        """
        versions = await PmSkillsVersions.get_all_versions()
        return [v.model_dump() for v in versions]


# Singleton instance
version_service = VersionService()
