"""Workflow execution state management."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID


class ExecutionStatus(str, Enum):
    """Workflow execution status."""
    PENDING = 'pending'
    RUNNING = 'running'
    PAUSED = 'paused'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class NodeStatus(str, Enum):
    """Node execution status."""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    SKIPPED = 'skipped'


@dataclass
class NodeResult:
    """Result of node execution."""
    status: NodeStatus
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class ExecutionState:
    """Tracks workflow execution state."""
    
    workflow_id: UUID
    status: ExecutionStatus = ExecutionStatus.PENDING
    variables: Dict[str, Any] = field(default_factory=dict)
    node_results: Dict[str, NodeResult] = field(default_factory=dict)
    current_node_id: Optional[str] = None
    error: Optional[str] = None
    should_abort: bool = False
    
    def set_node_result(self, node_id: str, result: NodeResult) -> None:
        """Set result for a node."""
        self.node_results[node_id] = result
    
    def get_node_result(self, node_id: str) -> Optional[NodeResult]:
        """Get result for a node."""
        return self.node_results.get(node_id)
    
    def get_variable(self, name: str) -> Any:
        """Get variable value."""
        return self.variables.get(name)
    
    def set_variable(self, name: str, value: Any) -> None:
        """Set variable value."""
        self.variables[name] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            'workflow_id': str(self.workflow_id),
            'status': self.status.value,
            'variables': self.variables,
            'node_results': {
                node_id: {
                    'status': result.status.value,
                    'output': result.output,
                    'error': result.error,
                    'started_at': result.started_at.isoformat() if result.started_at else None,
                    'completed_at': result.completed_at.isoformat() if result.completed_at else None
                }
                for node_id, result in self.node_results.items()
            },
            'current_node_id': self.current_node_id,
            'error': self.error,
            'should_abort': self.should_abort
        }
