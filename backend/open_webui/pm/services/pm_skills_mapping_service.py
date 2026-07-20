"""PmSkillsMapping service for CRUD operations."""

from typing import Optional

from open_webui.pm.models.pm_skills_mapping import (
    PmSkillsMappingForm,
    PmSkillsMappingModel,
    PmSkillsMappings,
)


class PmSkillsMappingService:
    """Service for managing pm-skills to SkillContract mappings."""

    async def create_mapping(
        self, form_data: PmSkillsMappingForm
    ) -> Optional[PmSkillsMappingModel]:
        """Create a new mapping."""
        return await PmSkillsMappings.insert_new_mapping(form_data)

    async def get_mapping(self, mapping_id: str) -> Optional[PmSkillsMappingModel]:
        """Get mapping by ID."""
        return await PmSkillsMappings.get_mapping_by_id(mapping_id)

    async def get_mapping_by_command(
        self, command_id: str
    ) -> Optional[PmSkillsMappingModel]:
        """Get mapping by command_id."""
        return await PmSkillsMappings.get_mapping_by_command_id(command_id)

    async def list_mappings(self) -> list[PmSkillsMappingModel]:
        """List all mappings."""
        return await PmSkillsMappings.get_all_mappings()

    async def list_enabled_mappings(self) -> list[PmSkillsMappingModel]:
        """List enabled mappings."""
        return await PmSkillsMappings.get_enabled_mappings()

    async def update_mapping(
        self, mapping_id: str, form_data: PmSkillsMappingForm
    ) -> Optional[PmSkillsMappingModel]:
        """Update a mapping."""
        return await PmSkillsMappings.update_mapping_by_id(mapping_id, form_data)

    async def delete_mapping(self, mapping_id: str) -> bool:
        """Delete a mapping."""
        return await PmSkillsMappings.delete_mapping_by_id(mapping_id)

    async def resolve_skill_contract_id(
        self, command_id: str
    ) -> Optional[str]:
        """Resolve command_id to skill_contract_id."""
        mapping = await self.get_mapping_by_command(command_id)
        return mapping.skill_contract_id if mapping else None


# Singleton instance
pm_skills_mapping_service = PmSkillsMappingService()
