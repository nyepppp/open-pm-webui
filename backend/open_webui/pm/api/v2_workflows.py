"""Enhanced Workflow API router with v2 workflow engine integration."""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any, Optional

from open_webui.pm.services.workflow_engine.engine import WorkflowEngine
from open_webui.pm.services.workflow_engine.state import ExecutionStatus
from open_webui.utils.auth import get_verified_user

router = APIRouter()

# Initialize workflow engine
workflow_engine = WorkflowEngine()


@router.post("/{workflow_id}/execute-v2")
async def execute_workflow_v2(
    workflow_id: str,
    request: Request,
    input_data: dict,
    user=Depends(get_verified_user),
):
    """Execute a workflow using the enhanced v2 engine."""
    try:
        # Get workflow data from request or database
        # For now, use the input data as nodes and edges
        nodes = input_data.get("nodes", [])
        edges = input_data.get("edges", [])
        
        # Execute workflow using enhanced engine
        state = await workflow_engine.execute(
            workflow_id=workflow_id,
            nodes=nodes,
            edges=edges,
            input_data=input_data.get("variables", {})
        )
        
        return {
            "status": state.status.value,
            "variables": state.variables,
            "node_results": {
                node_id: {
                    "status": result.status.value,
                    "output": result.output,
                    "error": result.error
                }
                for node_id, result in state.node_results.items()
            },
            "error": state.error
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")


@router.post("/{workflow_id}/validate-v2")
async def validate_workflow_v2(
    workflow_id: str,
    request: Request,
    input_data: dict,
    user=Depends(get_verified_user),
):
    """Validate a workflow using the enhanced v2 engine."""
    try:
        from open_webui.pm.services.workflow_engine.dag import parse_dag
        
        nodes = input_data.get("nodes", [])
        edges = input_data.get("edges", [])
        
        # Parse and validate DAG
        dag = parse_dag(nodes, edges)
        is_valid, error = dag.validate()
        
        return {
            "valid": is_valid,
            "error": error,
            "node_count": len(dag.nodes),
            "edge_count": len(dag.edges)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow validation failed: {str(e)}")
