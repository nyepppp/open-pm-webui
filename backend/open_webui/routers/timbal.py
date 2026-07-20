"""FastAPI router for Timbal integration."""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import json
import os
import time
from functools import wraps

import sys
_backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(_backend_dir, 'lib'))

from timbal.execution_service import WorkflowExecutionService
from timbal.models import TimbalWorkflow, TimbalExecution, TimbalConfig
from timbal.client import TimbalClient


router = APIRouter(tags=["timbal"])

# Global execution service
_execution_service: Optional[WorkflowExecutionService] = None

# Rate limiting storage
_rate_limit_storage: Dict[str, list] = {}


class ExecuteWorkflowRequest(BaseModel):
    """Request model for workflow execution."""
    inputs: Dict[str, Any] = Field(default_factory=dict)
    sync: bool = False


def rate_limit(requests_per_minute: int = 60):
    """Rate limiting decorator for API endpoints."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get client IP from request
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if request:
                client_ip = request.client.host if request.client else "unknown"
                current_time = time.time()
                
                # Clean old entries
                if client_ip in _rate_limit_storage:
                    _rate_limit_storage[client_ip] = [
                        t for t in _rate_limit_storage[client_ip]
                        if current_time - t < 60
                    ]
                else:
                    _rate_limit_storage[client_ip] = []
                
                # Check rate limit
                if len(_rate_limit_storage[client_ip]) >= requests_per_minute:
                    raise HTTPException(
                        status_code=429,
                        detail=f"Rate limit exceeded. Maximum {requests_per_minute} requests per minute."
                    )
                
                _rate_limit_storage[client_ip].append(current_time)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def get_execution_service() -> WorkflowExecutionService:
    """Get or create execution service."""
    global _execution_service
    if _execution_service is None:
        config = TimbalConfig()
        client = TimbalClient(config)
        _execution_service = WorkflowExecutionService(client)
    return _execution_service


@router.get("/healthcheck")
async def healthcheck():
    """Check Timbal service health."""
    try:
        service = get_execution_service()
        result = await service.client.healthcheck()
        return {"status": "healthy", "timbal": result}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Timbal service unavailable: {str(e)}")


@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    request: ExecuteWorkflowRequest
):
    """Execute a workflow."""
    try:
        service = get_execution_service()
        workflow = TimbalWorkflow(id=workflow_id, name="", nodes=[], edges=[])
        execution = await service.execute_workflow(workflow, request.inputs, request.sync)
        return execution.dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/{workflow_id}/stream")
async def stream_workflow(workflow_id: str, inputs: Dict[str, Any]):
    """Stream workflow execution via SSE."""
    async def event_generator():
        service = get_execution_service()
        workflow = TimbalWorkflow(id=workflow_id, name="", nodes=[], edges=[])
        
        try:
            async for event in service.stream_workflow(workflow, inputs):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@router.get("/executions/{execution_id}")
async def get_execution_status(execution_id: str):
    """Get execution status."""
    service = get_execution_service()
    execution = await service.get_execution_status(execution_id)
    
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return execution.dict()


@router.post("/executions/{execution_id}/stop")
async def stop_execution(execution_id: str):
    """Stop a running execution."""
    service = get_execution_service()
    execution = await service.stop_execution(execution_id)
    
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return execution.dict()
