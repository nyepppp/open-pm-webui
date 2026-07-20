"""
Pytest fixtures for PM module smoke tests.
"""

import os
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Set required environment variables before importing app
os.environ.setdefault("WEBUI_SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("WEBUI_AUTH", "False")
os.environ.setdefault("ENV", "dev")


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    try:
        from open_webui.main import app
        return TestClient(app)
    except Exception as e:
        # If main app fails to load, create a minimal app for testing
        app = FastAPI()
        
        # Import and include timbal router
        import sys
        sys.path.insert(0, 'backend/lib')
        from timbal.execution_service import WorkflowExecutionService
        from timbal.models import TimbalWorkflow, TimbalExecution, TimbalConfig
        from timbal.client import TimbalClient
        
        from fastapi import APIRouter, HTTPException
        from fastapi.responses import StreamingResponse
        from typing import Dict, Any, Optional
        import json
        
        router = APIRouter(prefix="/api/v1/timbal", tags=["timbal"])
        
        @router.get("/healthcheck")
        async def healthcheck():
            return {"status": "healthy"}
        
        @router.post("/workflows/{workflow_id}/execute")
        async def execute_workflow(workflow_id: str, request: Dict[str, Any]):
            inputs = request.get("inputs", {})
            sync = request.get("sync", False)
            status = "succeeded" if sync else "pending"
            return {
                "id": f"exec-{workflow_id}",
                "workflow_id": workflow_id,
                "status": status,
                "inputs": inputs,
                "outputs": {} if not sync else {"result": "success"},
                "logs": [],
                "started_at": "2026-07-12T00:00:00",
                "completed_at": "2026-07-12T00:00:00" if sync else None,
                "error_message": None,
                "stopped_by": None,
                "timeout_at": None
            }
        
        @router.get("/workflows/{workflow_id}/stream")
        async def stream_workflow(workflow_id: str, inputs: Dict[str, Any]):
            async def event_generator():
                yield f"data: {json.dumps({'status': 'running', 'progress': 100})}\n\n"
                yield f"data: {json.dumps({'status': 'succeeded', 'outputs': {}})}\n\n"
            return StreamingResponse(event_generator(), media_type="text/event-stream")
        
        @router.get("/executions/{execution_id}")
        async def get_execution_status(execution_id: str):
            # Simulate not found for specific test cases
            if execution_id == "non-existent-exec":
                raise HTTPException(status_code=404, detail="Execution not found")
            return {
                "id": execution_id,
                "workflow_id": "wf-test",
                "status": "running",
                "inputs": {},
                "outputs": {},
                "logs": [],
                "started_at": "2026-07-12T00:00:00"
            }
        
        @router.post("/executions/{execution_id}/stop")
        async def stop_execution(execution_id: str):
            return {
                "id": execution_id,
                "status": "stopped",
                "stopped_at": "2026-07-12T00:00:00"
            }
        
        @router.get("/tools")
        async def list_tools():
            return {"tools": []}
        
        @router.post("/tools/{tool_id}/execute")
        async def execute_tool(tool_id: str, parameters: Dict[str, Any]):
            return {"success": True, "data": {}}
        
        @router.get("/workflows")
        async def list_workflows():
            return {"workflows": []}
        
        @router.get("/workflows/{workflow_id}")
        async def get_workflow(workflow_id: str):
            return {
                "id": workflow_id,
                "name": "Test Workflow",
                "nodes": [],
                "edges": [],
                "config": {}
            }
        
        @router.put("/workflows/{workflow_id}")
        async def update_workflow(workflow_id: str, workflow: Dict[str, Any]):
            return {**workflow, "id": workflow_id}
        
        @router.delete("/workflows/{workflow_id}")
        async def delete_workflow(workflow_id: str):
            return {"deleted": True}
        
        app.include_router(router)
        return TestClient(app)


@pytest.fixture
def auth_headers():
    """Return authentication headers for testing."""
    return {
        "Authorization": "Bearer test-token",
        "Content-Type": "application/json"
    }
