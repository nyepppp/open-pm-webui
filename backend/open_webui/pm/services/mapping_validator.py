"""Mapping validation service for admin configuration."""

from typing import Any, Optional

from open_webui.pm.skills.pm_skills_loader import load_skill


class MappingValidator:
    """Validate pm-skills mapping configurations."""

    def __init__(self):
        pass

    async def validate_command_id(self, command_id: str) -> bool:
        """Validate that a command_id exists in pm-skills.

        Args:
            command_id: Command ID to validate

        Returns:
            True if valid
        """
        # Check if command_id maps to a valid skill
        from open_webui.pm.services.command_resolver import command_resolver

        skill = await command_resolver.resolve(command_id)
        return skill is not None

    async def validate_skill_contract_id(self, skill_contract_id: str) -> bool:
        """Validate that a skill_contract_id exists.

        Args:
            skill_contract_id: Skill contract ID to validate

        Returns:
            True if valid
        """
        # Check if skill_contract_id corresponds to a valid skill
        skill = load_skill(skill_contract_id)
        return skill is not None

    async def validate_mapping(
        self, command_id: str, skill_contract_id: str
    ) -> dict[str, Any]:
        """Validate a complete mapping configuration.

        Args:
            command_id: Command ID
            skill_contract_id: Skill contract ID

        Returns:
            Validation result
        """
        errors = []

        # Validate command_id
        if not await self.validate_command_id(command_id):
            errors.append(f"Invalid command_id: {command_id}")

        # Validate skill_contract_id
        if not await self.validate_skill_contract_id(skill_contract_id):
            errors.append(f"Invalid skill_contract_id: {skill_contract_id}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }


# Singleton instance
mapping_validator = MappingValidator()
