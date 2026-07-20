"""Module entry service for persisting pm-skills outputs."""

from typing import Any, Optional

from open_webui.models.pm import PMEntries, PMEntryForm


class ModuleEntryService:
    """Service for persisting pm-skills outputs to ModuleEntry."""

    def __init__(self):
        pass

    async def create_entry(
        self,
        user_id: str,
        project_id: str,
        module_type: str,
        title: str,
        content: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Create a new module entry from pm-skills output.

        Args:
            user_id: User ID
            project_id: Project ID
            module_type: Module type (e.g., "prd", "requirement", "strategy")
            title: Entry title
            content: Entry content
            data: Additional data

        Returns:
            Created entry
        """
        form_data = PMEntryForm(
            project_id=project_id,
            module_type=module_type,
            title=title,
            content=content,
            data=data,
        )
        entry = await PMEntries.insert_new_entry(user_id, form_data)
        return entry.model_dump() if entry else {}

    async def update_entry(
        self,
        entry_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Update an existing module entry.

        Args:
            entry_id: Entry ID
            title: New title
            content: New content
            data: New data

        Returns:
            Updated entry
        """
        from open_webui.models.pm import PMEntryUpdateForm

        form_data = PMEntryUpdateForm(
            title=title,
            content=content,
            data=data,
        )
        entry = await PMEntries.update_entry_by_id(entry_id, form_data)
        return entry.model_dump() if entry else {}

    async def get_entry(self, entry_id: str) -> Optional[dict[str, Any]]:
        """Get a module entry by ID.

        Args:
            entry_id: Entry ID

        Returns:
            Entry dict or None
        """
        entry = await PMEntries.get_entry_by_id(entry_id)
        return entry.model_dump() if entry else None


# Singleton instance
module_entry_service = ModuleEntryService()
