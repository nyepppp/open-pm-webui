"""Workflow execution service."""

import asyncio
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime, timezone, timedelta

from .models import TimbalWorkflow, TimbalExecution, TimbalExecutionStatus
from .client import TimbalClient, TimbalClientWithRetry


class WorkflowExecutionService:
    """Service for executing Timbal workflows."""
    
    def __init__(self, client: TimbalClient):
        self.client = client
        self.active_executions: Dict[str, TimbalExecution] = {}
    
    async def execute_workflow(
        self,
        workflow: TimbalWorkflow,
        inputs: Dict[str, Any],
        sync: bool = False
    ) -> TimbalExecution:
        """Execute a workflow."""
        execution = TimbalExecution(
            id=f"exec_{datetime.now(timezone.utc).timestamp()}",
            workflow_id=workflow.id,
            status=TimbalExecutionStatus.PENDING,
            inputs=inputs,
            started_at=datetime.now(timezone.utc)
        )
        
        self.active_executions[execution.id] = execution
        
        try:
            execution.status = TimbalExecutionStatus.RUNNING
            result = await self.client.run_workflow(
                workflow_id=workflow.id,
                inputs=inputs,
                sync=sync
            )
            
            execution.status = result.status
            execution.outputs = result.outputs
            execution.completed_at = datetime.now(timezone.utc)
            
        except Exception as e:
            execution.status = TimbalExecutionStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now(timezone.utc)
        
        return execution
    
    async def stream_workflow(
        self,
        workflow: TimbalWorkflow,
        inputs: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute a workflow with streaming."""
        execution = TimbalExecution(
            id=f"exec_{datetime.now(timezone.utc).timestamp()}",
            workflow_id=workflow.id,
            status=TimbalExecutionStatus.RUNNING,
            inputs=inputs,
            started_at=datetime.now(timezone.utc)
        )
        
        self.active_executions[execution.id] = execution
        
        try:
            async for event in self.client.stream_workflow(
                workflow_id=workflow.id,
                inputs=inputs
            ):
                yield event
            
            execution.status = TimbalExecutionStatus.SUCCEEDED
            execution.completed_at = datetime.now(timezone.utc)
            
        except Exception as e:
            execution.status = TimbalExecutionStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now(timezone.utc)
            raise
    
    async def stop_execution(self, execution_id: str) -> Optional[TimbalExecution]:
        """Stop a running execution."""
        execution = self.active_executions.get(execution_id)
        if not execution:
            return None
        
        if execution.status == TimbalExecutionStatus.RUNNING:
            await self.client.stop_execution(execution_id)
            execution.status = TimbalExecutionStatus.STOPPED
            execution.completed_at = datetime.now(timezone.utc)
        
        return execution
    
    async def get_execution_status(self, execution_id: str) -> Optional[TimbalExecution]:
        """Get execution status."""
        return self.active_executions.get(execution_id)
    
    async def cleanup_executions(self, max_age_hours: int = 24) -> int:
        """Remove old completed executions to prevent memory leaks.
        
        Args:
            max_age_hours: Maximum age in hours before removing an execution
            
        Returns:
            Number of executions removed
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        to_remove = [
            exec_id for exec_id, exec in self.active_executions.items()
            if exec.completed_at and exec.completed_at < cutoff
        ]
        for exec_id in to_remove:
            del self.active_executions[exec_id]
        return len(to_remove)
