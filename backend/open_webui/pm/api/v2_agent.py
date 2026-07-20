"""Agent API router for PM workspace."""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any, List, Optional
from uuid import UUID

from open_webui.pm.services.agent_runtime.agent import AgentRuntime
from open_webui.pm.services.agent_runtime.memory import MemoryStore
from open_webui.pm.services.agent_runtime.tools import ToolRegistry
from open_webui.utils.auth import get_verified_user

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize agent runtime
tool_registry = ToolRegistry()
memory_store = MemoryStore()

# Initialize agent runtime with default config
agent_runtime = AgentRuntime(
    llm_config={
        "model": "gpt-4",
        "temperature": 0.7
    },
    tool_registry=tool_registry,
    memory_store=memory_store
)


@router.post("/sessions")
async def create_agent_session(
    request: Request,
    session_config: dict,
    user=Depends(get_verified_user),
):
    """Create a new agent session."""
    try:
        session_id = str(UUID())
        return {
            "session_id": session_id,
            "status": "created",
            "config": session_config
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.post("/{session_id}/chat")
async def chat_with_agent(
    session_id: str,
    request: Request,
    message_data: dict,
    user=Depends(get_verified_user),
):
    """Chat with the agent."""
    try:
        user_message = message_data.get("message", "")
        
        project_id = message_data.get("project_id")
        module_type = message_data.get("module_type")
        entry_id = message_data.get("entry_id")
        
        pm_context = {}
        if project_id is not None:
            pm_context["project_id"] = project_id
        if module_type is not None:
            pm_context["module_type"] = module_type
        if entry_id is not None:
            pm_context["entry_id"] = entry_id
        
        if pm_context:
            logger.info(
                "Agent chat with PM context: project_id=%s, module_type=%s, entry_id=%s",
                project_id, module_type, entry_id
            )
        else:
            logger.debug("Agent chat without PM context (backward compatible mode)")
        
        run = await agent_runtime.run(
            session_id=UUID(session_id),
            user_message=user_message,
            pm_context=pm_context if pm_context else None
        )
        
        return {
            "message": run.assistant_message,
            "session_id": session_id,
            "thought_process": [
                {
                    "observation": step.observation,
                    "reasoning": step.reasoning,
                    "action": step.action
                }
                for step in run.thought_process
            ],
            "tool_calls": run.tool_calls,
            "token_usage": run.token_usage,
            "duration_ms": run.duration_ms
        }
    except ValueError as e:
        logger.error("Invalid session ID or parameters: %s", str(e))
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")
    except Exception as e:
        logger.exception("Agent chat failed")
        raise HTTPException(status_code=500, detail=f"Agent chat failed: {str(e)}")


@router.get("/{session_id}/runs")
async def get_agent_runs(
    session_id: str,
    request: Request,
    user=Depends(get_verified_user),
):
    """Get all runs for a session."""
    try:
        # For now, return empty list
        # In production, this would fetch from database
        return {
            "session_id": session_id,
            "runs": []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get runs: {str(e)}")


@router.delete("/{session_id}")
async def delete_agent_session(
    session_id: str,
    request: Request,
    user=Depends(get_verified_user),
):
    """Delete an agent session."""
    try:
        # Clear memory for the session
        await memory_store.clear()
        
        return {
            "session_id": session_id,
            "status": "deleted"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")
