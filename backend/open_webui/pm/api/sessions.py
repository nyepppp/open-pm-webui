"""Session binding API router for PM workspace session persistence."""

from fastapi import APIRouter, HTTPException

from open_webui.pm.models.session_binding import SessionBindingForm
from open_webui.pm.services.session_binding_service import SessionBindingService

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/{session_id}/bind")
async def bind_session(session_id: str, workspace_id: str):
    """Bind a session to a workspace."""
    form_data = SessionBindingForm(session_id=session_id, workspace_id=workspace_id)
    binding = await SessionBindingService.bind_session(form_data)
    if not binding:
        raise HTTPException(status_code=400, detail="Failed to bind session")
    return binding


@router.post("/{session_id}/unbind")
async def unbind_session(session_id: str):
    """Unbind a session from its workspace."""
    success = await SessionBindingService.unbind_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="No active binding found")
    return {"message": "Session unbound"}


@router.get("/{session_id}/workspace")
async def get_session_workspace(session_id: str):
    """Get the workspace bound to a session."""
    workspace = await SessionBindingService.get_session_workspace(session_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="No active binding found")
    return workspace


@router.post("/{session_id}/switch")
async def switch_workspace(session_id: str, workspace_id: str):
    """Switch a session to a different workspace."""
    binding = await SessionBindingService.switch_workspace(session_id, workspace_id)
    if not binding:
        raise HTTPException(status_code=400, detail="Failed to switch workspace")
    return binding


@router.get("/workspace/{workspace_id}/bindings")
async def get_workspace_bindings(workspace_id: str):
    """Get all bindings for a workspace."""
    return await SessionBindingService.get_workspace_bindings(workspace_id)
