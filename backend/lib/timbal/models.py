"""Timbal data models."""

import os
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class TimbalExecutionStatus(str, Enum):
    """Execution status enum."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    STOPPED = "stopped"


class TimbalConfig(BaseModel):
    """Timbal configuration."""
    endpoint_url: str = Field(default_factory=lambda: os.getenv("TIMBAL_ENDPOINT_URL", "http://localhost:3000"))
    api_key: Optional[str] = Field(default_factory=lambda: os.getenv("TIMBAL_API_KEY"))
    timeout: int = 30
    max_concurrent_executions: int = 10
    max_retries: int = 3
    retry_intervals: List[int] = [1, 2, 4]


class TimbalWorkflow(BaseModel):
    """Workflow definition."""
    id: str
    name: str
    description: Optional[str] = None
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    config: Dict[str, Any] = {}
    version: str = "1.0.0"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TimbalExecution(BaseModel):
    """Workflow execution."""
    id: str
    workflow_id: str
    status: TimbalExecutionStatus = TimbalExecutionStatus.PENDING
    inputs: Dict[str, Any] = {}
    outputs: Dict[str, Any] = {}
    logs: List[str] = []
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    stopped_by: Optional[str] = None
    timeout_at: Optional[datetime] = None


class TimbalTool(BaseModel):
    """Tool definition."""
    id: str
    name: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = {}
    return_schema: Dict[str, Any] = {}
    handler_function: Optional[str] = None
    binding_type: str = "pm_operation"


class TimbalNode(BaseModel):
    """Workflow node."""
    id: str
    type: str
    config: Dict[str, Any] = {}
    inputs: List[str] = []
    outputs: List[str] = []
    position_x: float = 0.0
    position_y: float = 0.0


class TimbalToolBinding(BaseModel):
    """Tool binding configuration."""
    tool_id: str
    node_id: str
    parameter_mappings: Dict[str, str] = {}
    auto_map: bool = True
    template_id: Optional[str] = None
