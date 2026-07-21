"""Workflow service for PM workspace workflow designer."""

import json
from typing import Optional

from open_webui.pm.models.workflow import (
    WorkflowExecutionForm,
    WorkflowForm,
    WorkflowNodeForm,
    WorkflowEdgeForm,
    Workflows,
    WorkflowNodes,
    WorkflowEdges,
    WorkflowExecutions,
)
from open_webui.utils.acl import require_workflow_owner


class WorkflowService:
    """Service for workflow operations."""

    async def create_workflow(
        self, form_data: WorkflowForm, owner_id: Optional[str] = None
    ) -> dict:
        """Create a new workflow.

        Args:
            form_data: Workflow form fields.
            owner_id: Authenticated user's id (Issue #29). Injected by the
                router, never trusted from the wire form.
        """
        workflow = await Workflows.insert_new_workflow(form_data, owner_id=owner_id)
        return workflow.model_dump() if workflow else None

    async def get_workflow(self, workflow_id: str) -> Optional[dict]:
        """Get workflow by ID."""
        workflow = await Workflows.get_workflow_by_id(workflow_id)
        return workflow.model_dump() if workflow else None

    async def get_workflows_by_project(self, project_id: str) -> list[dict]:
        """Get all workflows for a project."""
        workflows = await Workflows.get_workflows_by_project(project_id)
        return [w.model_dump() for w in workflows]

    async def get_all_workflows(self) -> list[dict]:
        """Get all workflows (admin-only — see get_workflows_for_user for the
        ACL-respecting variant)."""
        workflows = await Workflows.get_all_workflows()
        return [w.model_dump() for w in workflows]

    async def get_workflows_for_user(
        self, user_id: str, role: str
    ) -> list[dict]:
        """Get workflows accessible to the given user (Issue #29).

        Admins see all; non-admins see only their own.
        """
        workflows = await Workflows.get_workflows_for_user(user_id, role)
        return [w.model_dump() for w in workflows]

    async def get_workflow_with_access_check(
        self, workflow_id: str, user_id: str, role: str
    ) -> Optional[dict]:
        """Load a workflow and verify ownership (Issue #29).

        Raises:
            HTTPException(403): If the actor is neither owner nor admin.
        """
        workflow = await Workflows.get_workflow_by_id(workflow_id)
        if not workflow:
            return None
        require_workflow_owner(workflow.owner_id, user_id, role)
        return workflow.model_dump()

    async def update_workflow(self, workflow_id: str, form_data: WorkflowForm) -> Optional[dict]:
        """Update a workflow."""
        workflow = await Workflows.update_workflow_by_id(workflow_id, form_data)
        return workflow.model_dump() if workflow else None

    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        return await Workflows.delete_workflow_by_id(workflow_id)

    async def create_node(self, form_data: WorkflowNodeForm) -> dict:
        """Create a new workflow node."""
        node = await WorkflowNodes.insert_new_node(form_data)
        return node.model_dump() if node else None

    async def get_nodes_by_workflow(self, workflow_id: str) -> list[dict]:
        """Get all nodes for a workflow."""
        nodes = await WorkflowNodes.get_nodes_by_workflow(workflow_id)
        return [n.model_dump() for n in nodes]

    async def delete_node(self, node_id: str) -> bool:
        """Delete a node."""
        return await WorkflowNodes.delete_node_by_id(node_id)

    async def create_edge(self, form_data: WorkflowEdgeForm) -> dict:
        """Create a new workflow edge."""
        edge = await WorkflowEdges.insert_new_edge(form_data)
        return edge.model_dump() if edge else None

    async def get_edges_by_workflow(self, workflow_id: str) -> list[dict]:
        """Get all edges for a workflow."""
        edges = await WorkflowEdges.get_edges_by_workflow(workflow_id)
        return [e.model_dump() for e in edges]

    async def delete_edge(self, edge_id: str) -> bool:
        """Delete an edge."""
        return await WorkflowEdges.delete_edge_by_id(edge_id)

    async def create_execution(
        self,
        form_data: WorkflowExecutionForm,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> dict:
        """Create a new workflow execution.

        Args:
            form_data: Execution form fields.
            user_id: Authenticated user who triggered the execution (Issue #29).
            project_id: Project context, derived from the workflow's project_id.
        """
        execution = await WorkflowExecutions.insert_new_execution(
            form_data, user_id=user_id, project_id=project_id
        )
        return execution.model_dump() if execution else None

    async def get_execution(self, execution_id: str) -> Optional[dict]:
        """Get execution by ID."""
        execution = await WorkflowExecutions.get_execution_by_id(execution_id)
        return execution.model_dump() if execution else None

    async def get_executions_by_workflow(self, workflow_id: str) -> list[dict]:
        """Get all executions for a workflow."""
        executions = await WorkflowExecutions.get_executions_by_workflow(workflow_id)
        return [e.model_dump() for e in executions]

    async def update_execution_status(
        self, execution_id: str, status: str, output_data: Optional[str] = None, error_message: Optional[str] = None
    ) -> Optional[dict]:
        """Update execution status."""
        execution = await WorkflowExecutions.update_execution_status(
            execution_id, status, output_data, error_message
        )
        return execution.model_dump() if execution else None

    async def validate_workflow(self, workflow_id: str) -> dict:
        """Validate workflow structure."""
        workflow = await Workflows.get_workflow_by_id(workflow_id)
        if not workflow:
            return {"valid": False, "errors": ["Workflow not found"]}

        errors = []
        nodes = json.loads(workflow.nodes) if workflow.nodes else []
        edges = json.loads(workflow.edges) if workflow.edges else []

        # Check for exactly one start node
        start_nodes = [n for n in nodes if n.get("type") == "start"]
        if len(start_nodes) != 1:
            errors.append(f"Must have exactly one start node, found {len(start_nodes)}")

        # Check for at least one end node
        end_nodes = [n for n in nodes if n.get("type") == "end"]
        if len(end_nodes) < 1:
            errors.append("Must have at least one end node")

        # Check for circular dependencies (simple check)
        node_ids = {n.get("id") for n in nodes}
        edge_map = {}
        for edge in edges:
            source = edge.get("source_node_id")
            target = edge.get("target_node_id")
            if source not in edge_map:
                edge_map[source] = []
            edge_map[source].append(target)

        # Check for orphaned nodes
        connected_nodes = set()
        for edge in edges:
            connected_nodes.add(edge.get("source_node_id"))
            connected_nodes.add(edge.get("target_node_id"))

        for node in nodes:
            if node.get("type") not in ["start", "end"] and node.get("id") not in connected_nodes:
                errors.append(f"Node '{node.get('name')}' is orphaned (no connections)")

        return {"valid": len(errors) == 0, "errors": errors}


# Singleton instance
WorkflowService = WorkflowService()
