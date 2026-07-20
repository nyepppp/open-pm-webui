"""Session binding service for PM workspace session persistence."""

from typing import Optional

from open_webui.pm.models.session_binding import (
    SessionBindingForm,
    SessionBindings,
)


class SessionBindingService:
    """Service for session binding operations."""

    async def bind_session(self, form_data: SessionBindingForm) -> dict:
        """Bind a session to a workspace."""
        # Unbind any existing active binding for this session
        existing = await SessionBindings.get_active_binding_by_session(form_data.session_id)
        if existing:
            await SessionBindings.update_binding_status(existing.id, "false")

        binding = await SessionBindings.insert_new_binding(form_data)
        return binding.model_dump() if binding else None

    async def unbind_session(self, session_id: str) -> bool:
        """Unbind a session from its workspace."""
        binding = await SessionBindings.get_active_binding_by_session(session_id)
        if binding:
            await SessionBindings.update_binding_status(binding.id, "false")
            return True
        return False

    async def get_session_workspace(self, session_id: str) -> Optional[dict]:
        """Get the workspace bound to a session."""
        binding = await SessionBindings.get_active_binding_by_session(session_id)
        if binding:
            return {
                "workspace_id": binding.workspace_id,
                "bound_at": binding.bound_at,
            }
        return None

    async def switch_workspace(self, session_id: str, new_workspace_id: str) -> dict:
        """Switch a session to a different workspace."""
        # Unbind existing
        await self.unbind_session(session_id)
        # Bind to new workspace
        form_data = SessionBindingForm(session_id=session_id, workspace_id=new_workspace_id)
        return await self.bind_session(form_data)

    async def get_workspace_bindings(self, workspace_id: str) -> list[dict]:
        """Get all bindings for a workspace."""
        bindings = await SessionBindings.get_bindings_by_workspace(workspace_id)
        return [b.model_dump() for b in bindings]


# Singleton instance
SessionBindingService = SessionBindingService()
