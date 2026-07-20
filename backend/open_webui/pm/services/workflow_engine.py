"""Async workflow execution engine for PM workspace workflow designer."""

import asyncio
import json
import time
from typing import Any, Optional

from open_webui.pm.models.workflow import (
    WorkflowExecutionForm,
    WorkflowExecutions,
    WorkflowNodes,
    Workflows,
)


class WorkflowExecutionEngine:
    """Async execution engine for workflows."""

    def __init__(self):
        self._running_executions = {}

    async def execute(self, workflow_id: str, input_data: dict) -> str:
        """Execute a workflow and return execution ID."""
        # Create execution record
        form_data = WorkflowExecutionForm(
            workflow_id=workflow_id,
            status="running",
            input_data=json.dumps(input_data),
        )
        execution = await WorkflowExecutions.insert_new_execution(form_data)
        execution_id = execution.id

        # Start execution in background
        asyncio.create_task(self._run_execution(execution_id, workflow_id, input_data))
        return execution_id

    async def _run_execution(self, execution_id: str, workflow_id: str, input_data: dict):
        """Run the workflow execution."""
        try:
            # Get workflow
            workflow = await Workflows.get_workflow_by_id(workflow_id)
            if not workflow:
                await WorkflowExecutions.update_execution_status(
                    execution_id, "failed", error_message="Workflow not found"
                )
                return

            # Parse nodes and edges
            nodes = json.loads(workflow.nodes) if workflow.nodes else []
            edges = json.loads(workflow.edges) if workflow.edges else []

            # Build adjacency list
            adjacency = {}
            for edge in edges:
                source = edge.get("source_node_id")
                target = edge.get("target_node_id")
                if source not in adjacency:
                    adjacency[source] = []
                adjacency[source].append(target)

            # Find start node
            start_nodes = [n for n in nodes if n.get("type") == "start"]
            if not start_nodes:
                await WorkflowExecutions.update_execution_status(
                    execution_id, "failed", error_message="No start node found"
                )
                return

            # Execute nodes in order (simple sequential execution)
            current_node = start_nodes[0]
            node_states = []
            current_data = input_data

            while current_node:
                node_id = current_node.get("id")
                node_type = current_node.get("type")

                # Execute node based on type
                result = await self._execute_node(current_node, current_data)
                node_states.append({
                    "node_id": node_id,
                    "status": "completed",
                    "output": result,
                })

                # Update current data for next node
                current_data = result

                # Find next node
                next_node_ids = adjacency.get(node_id, [])
                if not next_node_ids:
                    break

                # For simplicity, take the first next node
                next_node_id = next_node_ids[0]
                next_nodes = [n for n in nodes if n.get("id") == next_node_id]
                if not next_nodes:
                    break
                current_node = next_nodes[0]

            # Update execution status
            await WorkflowExecutions.update_execution_status(
                execution_id,
                "completed",
                output_data=json.dumps(current_data),
            )

            # Update node states
            execution = await WorkflowExecutions.get_execution_by_id(execution_id)
            if execution:
                execution.node_states = json.dumps(node_states)

        except Exception as e:
            await WorkflowExecutions.update_execution_status(
                execution_id, "failed", error_message=str(e)
            )

    async def _execute_node(self, node: dict, input_data: dict) -> dict:
        """Execute a single node."""
        node_type = node.get("type")
        config = json.loads(node.get("config", "{}"))

        if node_type == "start":
            return input_data

        elif node_type == "end":
            return input_data

        elif node_type == "agent_call":
            # Simulate agent call (placeholder)
            return {
                "result": f"Agent call executed with config: {config}",
                "input": input_data,
            }

        elif node_type == "data_transform":
            # Apply data transformation rules
            return {
                "result": f"Data transformed with config: {config}",
                "input": input_data,
            }

        elif node_type == "condition":
            # Evaluate condition
            return {
                "result": f"Condition evaluated with config: {config}",
                "input": input_data,
            }

        elif node_type == "loop":
            # Loop execution
            return {
                "result": f"Loop executed with config: {config}",
                "input": input_data,
            }

        elif node_type == "parallel_merge":
            # Merge parallel results
            return {
                "result": f"Parallel merge executed with config: {config}",
                "input": input_data,
            }

        elif node_type == "custom":
            # Execute custom script (placeholder)
            return {
                "result": f"Custom node executed with config: {config}",
                "input": input_data,
            }

        else:
            return {"result": "Unknown node type", "input": input_data}

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution."""
        await WorkflowExecutions.update_execution_status(
            execution_id, "cancelled"
        )
        return True

    async def get_execution_status(self, execution_id: str) -> Optional[dict]:
        """Get execution status."""
        execution = await WorkflowExecutions.get_execution_by_id(execution_id)
        if not execution:
            return None

        return {
            "id": execution.id,
            "workflow_id": execution.workflow_id,
            "status": execution.status,
            "input_data": execution.input_data,
            "output_data": execution.output_data,
            "node_states": execution.node_states,
            "logs": execution.logs,
            "started_at": execution.started_at,
            "completed_at": execution.completed_at,
            "error_message": execution.error_message,
        }


# Singleton instance
WorkflowExecutionEngine = WorkflowExecutionEngine()
