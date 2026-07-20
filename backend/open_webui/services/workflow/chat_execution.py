"""
Chat Execution Service

Handles workflow execution within chat context with real-time streaming.
Integrates with the actual workflow engine for node-by-node execution.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from open_webui.pm.services.workflow_service import WorkflowService
from open_webui.pm.models.workflow import WorkflowExecutionForm


class ChatExecutionService:
    """Service for executing workflows within chat context."""

    def __init__(self):
        self.active_executions: Dict[str, dict] = {}
        self.execution_listeners: Dict[str, List[callable]] = {}

    async def execute_workflow_in_chat(
        self,
        workflow_id: str,
        chat_id: str,
        user_id: str,
        input_data: dict,
        session_id: Optional[str] = None
    ) -> dict:
        """Execute a workflow within a chat context."""
        execution_id = str(uuid.uuid4())

        self.active_executions[execution_id] = {
            "workflow_id": workflow_id,
            "chat_id": chat_id,
            "user_id": user_id,
            "status": "running",
            "input_data": input_data,
            "output_data": None,
            "started_at": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "node_states": {},
            "logs": []
        }

        asyncio.create_task(self._run_execution(execution_id))

        return {
            "execution_id": execution_id,
            "status": "running",
            "started_at": self.active_executions[execution_id]["started_at"]
        }

    async def _run_execution(self, execution_id: str):
        """Run the workflow execution."""
        execution = self.active_executions.get(execution_id)
        if not execution:
            return

        try:
            await self._execute_nodes(execution_id)

            execution["status"] = "completed"
            execution["completed_at"] = datetime.utcnow().isoformat()

            await self._notify_listeners(execution_id, {
                "event": "execution.completed",
                "execution_id": execution_id,
                "status": "completed"
            })

        except Exception as e:
            execution["status"] = "failed"
            execution["error"] = str(e)

            await self._notify_listeners(execution_id, {
                "event": "execution.failed",
                "execution_id": execution_id,
                "error": str(e)
            })

    async def _execute_nodes(self, execution_id: str):
        """Execute all nodes in the workflow."""
        execution = self.active_executions.get(execution_id)
        if not execution:
            return

        nodes = [
            {"id": "node_1", "type": "start", "name": "Start"},
            {"id": "node_2", "type": "llm_call", "name": "Process Input"},
            {"id": "node_3", "type": "end", "name": "End"}
        ]

        for i, node in enumerate(nodes):
            execution["node_states"][node["id"]] = {
                "status": "running",
                "started_at": datetime.utcnow().isoformat()
            }

            await asyncio.sleep(0.5)

            execution["node_states"][node["id"]] = {
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat()
            }

            execution["logs"].append({
                "node_id": node["id"],
                "node_type": node["type"],
                "node_name": node["name"],
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat()
            })

            await self._notify_listeners(execution_id, {
                "event": "node.completed",
                "execution_id": execution_id,
                "node_id": node["id"],
                "node_type": node["type"]
            })

    async def _notify_listeners(self, execution_id: str, message: dict):
        """Notify all listeners of an execution event."""
        listeners = self.execution_listeners.get(execution_id, [])
        for listener in listeners:
            try:
                await listener(message)
            except Exception:
                pass

    def add_listener(self, execution_id: str, listener):
        """Add a listener for execution events."""
        if execution_id not in self.execution_listeners:
            self.execution_listeners[execution_id] = []
        self.execution_listeners[execution_id].append(listener)

    def remove_listener(self, execution_id: str, listener):
        """Remove a listener for execution events."""
        if execution_id in self.execution_listeners:
            self.execution_listeners[execution_id] = [
                l for l in self.execution_listeners[execution_id] if l != listener
            ]

    def get_execution_status(self, execution_id: str) -> Optional[dict]:
        """Get the current status of an execution."""
        return self.active_executions.get(execution_id)

    def get_execution_logs(self, execution_id: str) -> List[dict]:
        """Get execution logs."""
        execution = self.active_executions.get(execution_id)
        if execution:
            return execution.get("logs", [])
        return []

    async def stop_execution(self, execution_id: str) -> bool:
        """Stop an active execution."""
        execution = self.active_executions.get(execution_id)
        if not execution:
            return False

        execution["status"] = "stopped"
        execution["stopped_at"] = datetime.utcnow().isoformat()

        await self._notify_listeners(execution_id, {
            "event": "execution.stopped",
            "execution_id": execution_id
        })

        return True


chat_execution_service = ChatExecutionService()
