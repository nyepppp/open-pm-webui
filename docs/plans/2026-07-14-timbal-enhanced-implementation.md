# Workflow + Agent Engine - Timbal Enhanced Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enhance existing Timbal integration to support Dify-style visual workflow orchestration and Agent capabilities (tool use, memory, planning).

**Architecture:** Build enhancement layers on top of existing Timbal foundation. Keep Timbal as core execution engine, add DAG-based workflow orchestration, Agent runtime with ReAct pattern, and enhanced visual designer.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic, Timbal (embedded), Svelte 5, TypeScript, Tailwind CSS

**Timeline:** 3-4 weeks (vs 4-5 weeks for pure custom design)

---

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│              Frontend (Svelte 5)             │
│  ┌─────────────┐      ┌─────────────────┐  │
│  │ Enhanced    │      │ Agent Chat      │  │
│  │ Workflow    │      │ Interface       │  │
│  │ Designer v2 │      │ (New)           │  │
│  │ (Svelte 5)  │      │                 │  │
│  └──────┬──────┘      └────────┬────────┘  │
└─────────┼──────────────────────┼───────────┘
          │                      │
          ▼                      ▼
┌─────────────────────────────────────────────┐
│              API Layer (FastAPI)            │
│  ┌─────────────┐      ┌─────────────────┐ │
│  │ /api/v2/    │      │ /api/v2/agent/  │ │
│  │ workflows   │      │ sessions        │ │
│  │ /executions │      │ /runs           │ │
│  └──────┬──────┘      └────────┬────────┘ │
└─────────┼──────────────────────┼───────────┘
          │                      │
          ▼                      ▼
┌─────────────────────────────────────────────┐
│           Enhancement Layer (New)          │
│  ┌─────────────┐      ┌─────────────────┐ │
│  │ DAG Engine  │      │ Agent Runtime   │ │
│  │ (New)       │      │ (New)           │ │
│  │             │      │                 │ │
│  │ • Parse DAG │      │ • ReAct Loop    │ │
│  │ • Topo Sort │      │ • Tool Use      │ │
│  │ • State Mgmt│      │ • Memory        │ │
│  │ • Node Exec │      │ • Planning      │ │
│  └──────┬──────┘      └────────┬────────┘ │
└─────────┼──────────────────────┼───────────┘
          │                      │
          └──────────┬───────────┘
                     ▼
┌─────────────────────────────────────────────┐
│           Timbal Core (Existing)            │
│  ┌─────────┐ ┌─────────┐ ┌─────────────┐  │
│  │ Timbal  │ │ Timbal  │ │ Timbal      │  │
│  │ Client  │ │ Execution│ │ Tools      │  │
│  │ (httpx) │ │ Service  │ │ (PM Skill) │  │
│  └─────────┘ └─────────┘ └─────────────┘  │
└─────────────────────────────────────────────┘
```

---

## Phase 1: Enhance Timbal Node Types (Week 1)

### Task 1: Extend Timbal Models with New Node Types

**Files:**
- Create: `backend/open_webui/pm/models/v2_workflow.py`
- Modify: `backend/lib/timbal/models.py`

**Step 1: Add new node types to Timbal models**

```python
# backend/lib/timbal/models.py

# Add to existing file

class TimbalNodeType(str, Enum):
    """Extended node types for Timbal workflows."""
    # Control Flow
    START = "start"
    END = "end"
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"
    MERGE = "merge"
    
    # Data Processing
    VARIABLE_SET = "variable_set"
    TRANSFORM = "transform"
    FILTER = "filter"
    
    # AI/LLM
    LLM = "llm"
    PROMPT_TEMPLATE = "prompt_template"
    AGENT = "agent"
    
    # Tools
    TOOL_CALL = "tool_call"
    HTTP_REQUEST = "http_request"
    DATABASE_QUERY = "database_query"
    
    # PM Specific
    PM_CREATE_ENTRY = "pm_create_entry"
    PM_UPDATE_ENTRY = "pm_update_entry"
    PM_QUERY = "pm_query"
    
    # Integration
    WEBHOOK = "webhook"
    SCHEDULE = "schedule"
    EVENT_LISTEN = "event_listen"
    
    # Legacy (keep for compatibility)
    SKILL_CALL = "skill_call"


class TimbalNodeV2(BaseModel):
    """Enhanced workflow node with full configuration."""
    id: str
    type: TimbalNodeType
    name: str
    description: Optional[str] = None
    config: Dict[str, Any] = {}
    inputs: List[Dict[str, Any]] = []  # Full port definitions
    outputs: List[Dict[str, Any]] = []
    position_x: float = 0.0
    position_y: float = 0.0
    error_handling: Optional[Dict[str, Any]] = None


class TimbalEdgeV2(BaseModel):
    """Enhanced workflow edge with conditions."""
    id: str
    source: str
    target: str
    condition: Optional[str] = None  # JavaScript expression for condition nodes
    label: Optional[str] = None
    data_mapping: Dict[str, str] = {}  # Output -> Input mapping


class TimbalWorkflowV2(BaseModel):
    """Enhanced workflow definition."""
    id: str
    name: str
    description: Optional[str] = None
    nodes: List[TimbalNodeV2] = []
    edges: List[TimbalEdgeV2] = []
    config: Dict[str, Any] = {}
    version: str = "2.0.0"
    category: Optional[str] = None
    is_template: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

**Step 2: Create v2_workflow.py for database models**

```python
# backend/open_webui/pm/models/v2_workflow.py

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import relationship

from open_webui.pm.models import Base


class V2Workflow(Base):
    """Enhanced workflow definition."""
    
    __tablename__ = 'v2_workflows'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey('pm_project.id'))
    
    # DAG definition (JSONB for flexibility)
    nodes = Column(JSONB, nullable=False, default=list)
    edges = Column(JSONB, nullable=False, default=list)
    
    # Metadata
    version = Column(Integer, default=1)
    is_template = Column(Boolean, default=False)
    category = Column(String(50))
    
    # Status
    status = Column(String(20), default='draft')
    
    # Timestamps
    created_by = Column(PGUUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    executions = relationship("V2WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")
    agent_sessions = relationship("V2AgentSession", back_populates="workflow")


class V2WorkflowExecution(Base):
    """Workflow execution instance."""
    
    __tablename__ = 'v2_workflow_executions'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    workflow_id = Column(PGUUID(as_uuid=True), ForeignKey('v2_workflows.id', ondelete='CASCADE'))
    
    # Execution status
    status = Column(String(20))
    trigger_type = Column(String(20))
    
    # Input/Output
    input_data = Column(JSONB)
    output_data = Column(JSONB)
    
    # Execution context
    context = Column(JSONB)
    node_states = Column(JSONB)
    
    # Error handling
    error_message = Column(Text)
    error_node_id = Column(PGUUID(as_uuid=True))
    
    # Timestamps
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    workflow = relationship("V2Workflow", back_populates="executions")
    agent_runs = relationship("V2AgentRun", back_populates="workflow_execution")
```

**Step 3: Commit**

```bash
git add backend/lib/timbal/models.py
git add backend/open_webui/pm/models/v2_workflow.py
git commit -m "feat(models): extend Timbal with new node types and v2 workflow models"
```

---

### Task 2: Implement DAG Engine

**Files:**
- Create: `backend/open_webui/pm/services/workflow_engine/dag.py`
- Create: `backend/open_webui/pm/services/workflow_engine/state.py`

**Step 1: Write dag.py**

```python
"""DAG (Directed Acyclic Graph) parser and executor for Timbal workflows."""

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any


@dataclass
class DAGNode:
    """Represents a node in the DAG."""
    id: str
    type: str
    config: dict = field(default_factory=dict)
    inputs: List[dict] = field(default_factory=list)
    outputs: List[dict] = field(default_factory=list)


@dataclass
class DAGEdge:
    """Represents an edge in the DAG."""
    id: str
    source: str
    target: str
    condition: Optional[str] = None
    label: Optional[str] = None
    data_mapping: Dict[str, str] = field(default_factory=dict)


class DAG:
    """Directed Acyclic Graph for workflow execution."""
    
    def __init__(self):
        self.nodes: Dict[str, DAGNode] = {}
        self.edges: Dict[str, DAGEdge] = {}
        self._adjacency: Dict[str, List[str]] = defaultdict(list)
        self._reverse_adjacency: Dict[str, List[str]] = defaultdict(list)
        self._indegree: Dict[str, int] = defaultdict(int)
    
    def add_node(self, node: DAGNode) -> None:
        """Add a node to the DAG."""
        self.nodes[node.id] = node
        if node.id not in self._indegree:
            self._indegree[node.id] = 0
    
    def add_edge(self, edge: DAGEdge) -> None:
        """Add an edge to the DAG."""
        self.edges[edge.id] = edge
        self._adjacency[edge.source].append(edge.target)
        self._reverse_adjacency[edge.target].append(edge.source)
        self._indegree[edge.target] += 1
    
    def topological_sort(self) -> List[str]:
        """Perform topological sort."""
        in_degree = defaultdict(int)
        for node_id in self.nodes:
            in_degree[node_id] = self._indegree.get(node_id, 0)
        
        queue = deque([node_id for node_id in self.nodes if in_degree[node_id] == 0])
        result = []
        
        while queue:
            node_id = queue.popleft()
            result.append(node_id)
            
            for neighbor in self._adjacency[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(result) != len(self.nodes):
            raise ValueError("Workflow contains a cycle. DAG must be acyclic.")
        
        return result
    
    def get_predecessors(self, node_id: str) -> List[str]:
        """Get all predecessor nodes."""
        return self._reverse_adjacency.get(node_id, [])
    
    def get_successors(self, node_id: str) -> List[str]:
        """Get all successor nodes."""
        return self._adjacency.get(node_id, [])
    
    def get_node(self, node_id: str) -> Optional[DAGNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """Validate the DAG structure."""
        # Check for disconnected nodes
        connected_nodes = set()
        for edge in self.edges.values():
            connected_nodes.add(edge.source)
            connected_nodes.add(edge.target)
        
        for node_id in self.nodes:
            if node_id not in connected_nodes and len(self.nodes) > 1:
                return False, f"Node '{node_id}' is disconnected from the workflow"
        
        # Check for cycle
        try:
            self.topological_sort()
        except ValueError as e:
            return False, str(e)
        
        return True, None


def parse_dag(nodes: List[dict], edges: List[dict]) -> DAG:
    """Parse nodes and edges into a DAG."""
    dag = DAG()
    
    for node_data in nodes:
        node = DAGNode(
            id=node_data['id'],
            type=node_data['type'],
            config=node_data.get('config', {}),
            inputs=node_data.get('inputs', []),
            outputs=node_data.get('outputs', [])
        )
        dag.add_node(node)
    
    for edge_data in edges:
        edge = DAGEdge(
            id=edge_data['id'],
            source=edge_data['source'],
            target=edge_data['target'],
            condition=edge_data.get('condition'),
            label=edge_data.get('label'),
            data_mapping=edge_data.get('data_mapping', {})
        )
        dag.add_edge(edge)
    
    return dag
```

**Step 2: Write state.py**

```python
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
```

**Step 3: Commit**

```bash
git add backend/open_webui/pm/services/workflow_engine/
git commit -m "feat(engine): add DAG parser and execution state management"
```

---

### Task 3: Implement Node Executors

**Files:**
- Create: `backend/open_webui/pm/services/workflow_engine/nodes/__init__.py`
- Create: `backend/open_webui/pm/services/workflow_engine/nodes/base.py`
- Create: `backend/open_webui/pm/services/workflow_engine/nodes/control.py`
- Create: `backend/open_webui/pm/services/workflow_engine/nodes/llm.py`
- Create: `backend/open_webui/pm/services/workflow_engine/nodes/data.py`

**Step 1: Write base.py**

```python
"""Base node executor class."""

from abc import ABC, abstractmethod
from typing import Any, Dict

from ..state import ExecutionState, NodeResult


class BaseNodeExecutor(ABC):
    """Base class for all node executors."""
    
    @abstractmethod
    async def execute(self, node_config: Dict[str, Any], state: ExecutionState) -> NodeResult:
        """Execute the node."""
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate node configuration."""
        return True
    
    def get_required_inputs(self) -> list:
        """Get list of required input names."""
        return []
    
    def get_outputs(self) -> list:
        """Get list of output names."""
        return []
```

**Step 2: Write control.py**

```python
"""Control flow node executors."""

from typing import Any, Dict

from .base import BaseNodeExecutor
from ..state import ExecutionState, NodeResult, NodeStatus


class StartNodeExecutor(BaseNodeExecutor):
    """Executor for start nodes."""
    
    async def execute(self, node_config: Dict[str, Any], state: ExecutionState) -> NodeResult:
        return NodeResult(
            status=NodeStatus.COMPLETED,
            output={'started': True}
        )


class EndNodeExecutor(BaseNodeExecutor):
    """Executor for end nodes."""
    
    async def execute(self, node_config: Dict[str, Any], state: ExecutionState) -> NodeResult:
        return NodeResult(
            status=NodeStatus.COMPLETED,
            output={'completed': True, 'final_output': state.variables}
        )


class ConditionNodeExecutor(BaseNodeExecutor):
    """Executor for condition nodes."""
    
    async def execute(self, node_config: Dict[str, Any], state: ExecutionState) -> NodeResult:
        try:
            condition = node_config.get('condition', '')
            result = self._evaluate_condition(condition, state)
            
            return NodeResult(
                status=NodeStatus.COMPLETED,
                output={'condition_met': result}
            )
        except Exception as e:
            return NodeResult(
                status=NodeStatus.FAILED,
                error=str(e)
            )
    
    def _evaluate_condition(self, condition: str, state: ExecutionState) -> bool:
        """Evaluate a condition expression."""
        try:
            expr = condition
            for var_name, var_value in state.variables.items():
                placeholder = f"{{{{{var_name}}}}}"
                expr = expr.replace(placeholder, repr(var_value))
            
            return eval(expr, {"__builtins__": {}}, {})
        except:
            return False


class LoopNodeExecutor(BaseNodeExecutor):
    """Executor for loop nodes."""
    
    async def execute(self, node_config: Dict[str, Any], state: ExecutionState) -> NodeResult:
        try:
            iterations = node_config.get('iterations', 1)
            items = node_config.get('items', [])
            
            if items:
                # Iterate over items
                results = []
                for item in items:
                    state.set_variable('current_item', item)
                    results.append(item)
                
                return NodeResult(
                    status=NodeStatus.COMPLETED,
                    output={'iterations': len(items), 'results': results}
                )
            else:
                # Iterate N times
                return NodeResult(
                    status=NodeStatus.COMPLETED,
                    output={'iterations': iterations}
                )
        except Exception as e:
            return NodeResult(
                status=NodeStatus.FAILED,
                error=str(e)
            )
```

**Step 3: Write llm.py**

```python
"""LLM and AI node executors."""

import os
from typing import Any, Dict

import openai

from .base import BaseNodeExecutor
from ..state import ExecutionState, NodeResult, NodeStatus


class LLMNodeExecutor(BaseNodeExecutor):
    """Executor for LLM nodes."""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    async def execute(self, node_config: Dict[str, Any], state: ExecutionState) -> NodeResult:
        try:
            model = node_config.get('model', 'gpt-4')
            temperature = node_config.get('temperature', 0.7)
            max_tokens = node_config.get('max_tokens', 2048)
            prompt_template = node_config.get('prompt', '')
            
            # Resolve variables in prompt
            prompt = self._resolve_variables(prompt_template, state)
            
            # Call LLM
            response = await self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return NodeResult(
                status=NodeStatus.COMPLETED,
                output={
                    'text': response.choices[0].message.content,
                    'model': model,
                    'usage': {
                        'prompt_tokens': response.usage.prompt_tokens,
                        'completion_tokens': response.usage.completion_tokens,
                        'total_tokens': response.usage.total_tokens
                    }
                }
            )
        except Exception as e:
            return NodeResult(
                status=NodeStatus.FAILED,
                error=str(e)
            )
    
    def _resolve_variables(self, template: str, state: ExecutionState) -> str:
        """Resolve variables in template string."""
        result = template
        for var_name, var_value in state.variables.items():
            placeholder = f"{{{{{var_name}}}}}"
            result = result.replace(placeholder, str(var_value))
        return result


class PromptTemplateNodeExecutor(BaseNodeExecutor):
    """Executor for prompt template nodes."""
    
    async def execute(self, node_config: Dict[str, Any], state: ExecutionState) -> NodeResult:
        try:
            template = node_config.get('template', '')
            resolved = self._resolve_variables(template, state)
            
            return NodeResult(
                status=NodeStatus.COMPLETED,
                output={'prompt': resolved}
            )
        except Exception as e:
            return NodeResult(
                status=NodeStatus.FAILED,
                error=str(e)
            )
    
    def _resolve_variables(self, template: str, state: ExecutionState) -> str:
        """Resolve variables in template string."""
        result = template
        for var_name, var_value in state.variables.items():
            placeholder = f"{{{{{var_name}}}}}"
            result = result.replace(placeholder, str(var_value))
        return result
```

**Step 4: Write data.py**

```python
"""Data processing node executors."""

from typing import Any, Dict

from .base import BaseNodeExecutor
from ..state import ExecutionState, NodeResult, NodeStatus


class VariableSetNodeExecutor(BaseNodeExecutor):
    """Executor for variable set nodes."""
    
    async def execute(self, node_config: Dict[str, Any], state: ExecutionState) -> NodeResult:
        try:
            variables = node_config.get('variables', {})
            
            for var_name, var_value in variables.items():
                # Resolve variable references
                if isinstance(var_value, str) and var_value.startswith('{{') and var_value.endswith('}}'):
                    ref_name = var_value[2:-2]
                    var_value = state.get_variable(ref_name)
                
                state.set_variable(var_name, var_value)
            
            return NodeResult(
                status=NodeStatus.COMPLETED,
                output={'variables_set': list(variables.keys())}
            )
        except Exception as e:
            return NodeResult(
                status=NodeStatus.FAILED,
                error=str(e)
            )


class TransformNodeExecutor(BaseNodeExecutor):
    """Executor for data transform nodes."""
    
    async def execute(self, node_config: Dict[str, Any], state: ExecutionState) -> NodeResult:
        try:
            input_var = node_config.get('input', '')
            transform = node_config.get('transform', '')
            output_var = node_config.get('output', '')
            
            input_data = state.get_variable(input_var)
            
            # Apply transformation
            if transform == 'uppercase':
                result = str(input_data).upper()
            elif transform == 'lowercase':
                result = str(input_data).lower()
            elif transform == 'json_parse':
                import json
                result = json.loads(input_data) if isinstance(input_data, str) else input_data
            elif transform == 'json_stringify':
                import json
                result = json.dumps(input_data)
            else:
                result = input_data
            
            if output_var:
                state.set_variable(output_var, result)
            
            return NodeResult(
                status=NodeStatus.COMPLETED,
                output={'transformed': result}
            )
        except Exception as e:
            return NodeResult(
                status=NodeStatus.FAILED,
                error=str(e)
            )


class FilterNodeExecutor(BaseNodeExecutor):
    """Executor for filter nodes."""
    
    async def execute(self, node_config: Dict[str, Any], state: ExecutionState) -> NodeResult:
        try:
            input_var = node_config.get('input', '')
            condition = node_config.get('condition', '')
            output_var = node_config.get('output', '')
            
            input_data = state.get_variable(input_var)
            
            # Filter logic
            if isinstance(input_data, list):
                # Simple filter (in production, use proper expression evaluation)
                result = [item for item in input_data if item]
            else:
                result = input_data
            
            if output_var:
                state.set_variable(output_var, result)
            
            return NodeResult(
                status=NodeStatus.COMPLETED,
                output={'filtered': result}
            )
        except Exception as e:
            return NodeResult(
                status=NodeStatus.FAILED,
                error=str(e)
            )
```

**Step 5: Commit**

```bash
git add backend/open_webui/pm/services/workflow_engine/nodes/
git commit -m "feat(nodes): implement control, llm, and data node executors"
```

---

### Task 4: Implement Workflow Execution Engine

**Files:**
- Create: `backend/open_webui/pm/services/workflow_engine/engine.py`

**Step 1: Write engine.py**

```python
"""Workflow execution engine with Timbal integration."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from .dag import DAG, DAGNode, parse_dag
from .state import ExecutionState, ExecutionStatus, NodeResult, NodeStatus
from .nodes.base import BaseNodeExecutor
from .nodes.control import StartNodeExecutor, EndNodeExecutor, ConditionNodeExecutor, LoopNodeExecutor
from .nodes.llm import LLMNodeExecutor, PromptTemplateNodeExecutor
from .nodes.data import VariableSetNodeExecutor, TransformNodeExecutor, FilterNodeExecutor

# Import Timbal integration
from backend.lib.timbal.execution_service import WorkflowExecutionService
from backend.lib.timbal.models import TimbalWorkflow, TimbalExecutionStatus

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Enhanced workflow execution engine with DAG support."""
    
    def __init__(self, timbal_service: Optional[WorkflowExecutionService] = None):
        self.node_registry: Dict[str, BaseNodeExecutor] = {}
        self.timbal_service = timbal_service
        
        # Register built-in executors
        self._register_builtin_executors()
    
    def _register_builtin_executors(self):
        """Register all built-in node executors."""
        self.register_node_executor('start', StartNodeExecutor())
        self.register_node_executor('end', EndNodeExecutor())
        self.register_node_executor('condition', ConditionNodeExecutor())
        self.register_node_executor('loop', LoopNodeExecutor())
        self.register_node_executor('llm', LLMNodeExecutor())
        self.register_node_executor('prompt_template', PromptTemplateNodeExecutor())
        self.register_node_executor('variable_set', VariableSetNodeExecutor())
        self.register_node_executor('transform', TransformNodeExecutor())
        self.register_node_executor('filter', FilterNodeExecutor())
    
    def register_node_executor(self, node_type: str, executor: BaseNodeExecutor) -> None:
        """Register a node executor for a given type."""
        self.node_registry[node_type] = executor
    
    async def execute(
        self,
        workflow_id: UUID,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        input_data: Optional[Dict[str, Any]] = None
    ) -> ExecutionState:
        """Execute a workflow."""
        state = ExecutionState(
            workflow_id=workflow_id,
            status=ExecutionStatus.RUNNING
        )
        
        # Set input variables
        if input_data:
            for key, value in input_data.items():
                state.set_variable(key, value)
        
        try:
            # Parse DAG
            dag = parse_dag(nodes, edges)
            
            # Validate DAG
            is_valid, error = dag.validate()
            if not is_valid:
                state.status = ExecutionStatus.FAILED
                state.error = error
                return state
            
            # Topological sort for execution order
            execution_order = dag.topological_sort()
            
            # Execute nodes
            for node_id in execution_order:
                if state.should_abort:
                    break
                
                node = dag.get_node(node_id)
                state.current_node_id = node_id
                
                try:
                    result = await self._execute_node(node, state)
                    state.set_node_result(node_id, result)
                    
                    if result.status == NodeStatus.FAILED:
                        if self._should_abort_on_error(node):
                            state.status = ExecutionStatus.FAILED
                            state.error = result.error
                            break
                
                except Exception as e:
                    logger.exception(f"Error executing node {node_id}")
                    state.set_node_result(node_id, NodeResult(
                        status=NodeStatus.FAILED,
                        error=str(e)
                    ))
                    state.status = ExecutionStatus.FAILED
                    state.error = str(e)
                    break
            
            # Set final status
            if state.status != ExecutionStatus.FAILED:
                state.status = ExecutionStatus.COMPLETED
        
        except Exception as e:
            logger.exception("Workflow execution failed")
            state.status = ExecutionStatus.FAILED
            state.error = str(e)
        
        return state
    
    async def _execute_node(self, node: DAGNode, state: ExecutionState) -> NodeResult:
        """Execute a single node."""
        started_at = datetime.utcnow()
        
        # Get executor for node type
        executor = self.node_registry.get(node.type)
        if not executor:
            return NodeResult(
                status=NodeStatus.FAILED,
                error=f"No executor registered for node type: {node.type}",
                started_at=started_at,
                completed_at=datetime.utcnow()
            )
        
        # Execute
        try:
            result = await executor.execute(node.config, state)
            result.started_at = started_at
            result.completed_at = datetime.utcnow()
            return result
        except Exception as e:
            return NodeResult(
                status=NodeStatus.FAILED,
                error=str(e),
                started_at=started_at,
                completed_at=datetime.utcnow()
            )
    
    def _should_abort_on_error(self, node: DAGNode) -> bool:
        """Check if workflow should abort on node error."""
        error_handling = node.config.get('error_handling', {})
        strategy = error_handling.get('strategy', 'abort')
        return strategy == 'abort'
    
    async def execute_with_timbal(
        self,
        workflow_id: UUID,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        input_data: Optional[Dict[str, Any]] = None,
        sync: bool = False
    ) -> ExecutionState:
        """Execute workflow with Timbal integration for skill nodes."""
        # First execute enhanced nodes
        state = await self.execute(workflow_id, nodes, edges, input_data)
        
        # If Timbal service available, execute Timbal-specific nodes
        if self.timbal_service and state.status == ExecutionStatus.COMPLETED:
            timbal_nodes = [n for n in nodes if n.get('type') == 'skill_call']
            
            for node in timbal_nodes:
                try:
                    # Create Timbal workflow
                    timbal_workflow = TimbalWorkflow(
                        id=node['id'],
                        name=node.get('name', ''),
                        nodes=[node],
                        edges=[]
                    )
                    
                    # Execute via Timbal
                    execution = await self.timbal_service.execute_workflow(
                        workflow=timbal_workflow,
                        inputs=input_data or {},
                        sync=sync
                    )
                    
                    # Update state with Timbal results
                    if execution.status == TimbalExecutionStatus.SUCCEEDED:
                        state.set_variable(f"timbal_{node['id']}", execution.outputs)
                    
                except Exception as e:
                    logger.exception(f"Timbal execution failed for node {node['id']}")
                    state.set_node_result(node['id'], NodeResult(
                        status=NodeStatus.FAILED,
                        error=f"Timbal execution failed: {str(e)}"
                    ))
        
        return state
```

**Step 2: Commit**

```bash
git add backend/open_webui/pm/services/workflow_engine/engine.py
git commit -m "feat(engine): implement workflow execution engine with Timbal integration"
```

---

## Phase 2: Agent Runtime (Week 2)

### Task 5: Implement Agent Runtime

**Files:**
- Create: `backend/open_webui/pm/services/agent_runtime/agent.py`
- Create: `backend/open_webui/pm/services/agent_runtime/memory.py`
- Create: `backend/open_webui/pm/services/agent_runtime/tools.py`

**Step 1: Write tools.py**

```python
"""Tool registry and execution for Agent."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ToolResult:
    """Tool execution result."""
    def __init__(self, success: bool, output: Any = None, error: str = None):
        self.success = success
        self.output = output
        self.error = error


class BaseTool(ABC):
    """Base class for tools."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool."""
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for LLM."""
        return {
            'name': self.name,
            'description': self.description
        }


class ToolRegistry:
    """Registry for tools."""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools."""
        return [tool.get_schema() for tool in self._tools.values()]
    
    async def execute(self, name: str, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        tool = self.get(name)
        if not tool:
            return ToolResult(success=False, error=f"Tool not found: {name}")
        return await tool.execute(**kwargs)
```

**Step 2: Write memory.py**

```python
"""Memory management for Agent."""

from datetime import datetime
from typing import Any, Dict, List, Optional


class Memory:
    """Single memory entry."""
    
    def __init__(self, content: str, memory_type: str = 'short_term', metadata: Dict = None):
        self.content = content
        self.memory_type = memory_type
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.accessed_at = None


class MemoryStore:
    """In-memory store for agent memories."""
    
    def __init__(self, max_short_term: int = 10):
        self.max_short_term = max_short_term
        self._memories: List[Memory] = []
    
    async def store(self, content: str, memory_type: str = 'short_term', metadata: Dict = None) -> None:
        """Store a new memory."""
        memory = Memory(content=content, memory_type=memory_type, metadata=metadata)
        self._memories.append(memory)
        
        # Keep only recent short-term memories
        if memory_type == 'short_term':
            short_term = [m for m in self._memories if m.memory_type == 'short_term']
            if len(short_term) > self.max_short_term:
                self._memories = [
                    m for m in self._memories 
                    if m.memory_type != 'short_term' or m not in short_term[:-self.max_short_term]
                ]
    
    async def retrieve(self, query: str = None, limit: int = 10) -> List[Memory]:
        """Retrieve memories."""
        sorted_memories = sorted(self._memories, key=lambda m: m.created_at, reverse=True)
        return sorted_memories[:limit]
    
    async def clear(self) -> None:
        """Clear all memories."""
        self._memories = []
```

**Step 3: Write agent.py**

```python
"""Agent runtime with ReAct pattern."""

import json
import time
from typing import Any, Dict, List, Optional
from uuid import UUID

import openai

from .memory import MemoryStore
from .tools import ToolRegistry, ToolResult


class ThoughtStep:
    """Single step in ReAct loop."""
    
    def __init__(self, observation: str, reasoning: str, action: str, action_input: Dict = None):
        self.observation = observation
        self.reasoning = reasoning
        self.action = action
        self.action_input = action_input or {}


class AgentRun:
    """Agent execution run."""
    
    def __init__(self, session_id: UUID, user_message: str):
        self.session_id = session_id
        self.user_message = user_message
        self.thought_process: List[ThoughtStep] = []
        self.tool_calls: List[Dict] = []
        self.assistant_message: Optional[str] = None
        self.token_usage: Dict[str, int] = {}
        self.duration_ms: int = 0


class AgentRuntime:
    """ReAct-based agent runtime."""
    
    def __init__(self, llm_config: Dict[str, Any], tool_registry: ToolRegistry, memory_store: MemoryStore):
        self.llm_config = llm_config
        self.tool_registry = tool_registry
        self.memory_store = memory_store
        self.client = openai.AsyncOpenAI()
    
    async def run(self, session_id: UUID, user_message: str, max_steps: int = 10) -> AgentRun:
        """Run agent with user input."""
        start_time = time.time()
        run = AgentRun(session_id=session_id, user_message=user_message)
        
        # Retrieve relevant memories
        memories = await self.memory_store.retrieve(query=user_message)
        memory_context = "\n".join([f"- {m.content}" for m in memories])
        
        # Build system prompt
        system_prompt = self._build_system_prompt()
        
        # ReAct loop
        for step in range(max_steps):
            # Build prompt with history
            prompt = self._build_react_prompt(
                user_message=user_message,
                memory_context=memory_context,
                previous_steps=run.thought_process
            )
            
            # Call LLM
            response = await self.client.chat.completions.create(
                model=self.llm_config.get('model', 'gpt-4'),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.llm_config.get('temperature', 0.7)
            )
            
            content = response.choices[0].message.content
            
            # Parse thought
            thought = self._parse_thought(content)
            run.thought_process.append(thought)
            
            # Update token usage
            run.token_usage['prompt_tokens'] = run.token_usage.get('prompt_tokens', 0) + response.usage.prompt_tokens
            run.token_usage['completion_tokens'] = run.token_usage.get('completion_tokens', 0) + response.usage.completion_tokens
            
            # Execute action
            if thought.action == 'respond':
                run.assistant_message = thought.action_input.get('message', '')
                break
            elif thought.action == 'use_tool':
                tool_name = thought.action_input.get('tool')
                tool_params = thought.action_input.get('params', {})
                
                result = await self.tool_registry.execute(tool_name, **tool_params)
                run.tool_calls.append({
                    'tool': tool_name,
                    'params': tool_params,
                    'result': result.output if result.success else result.error
                })
            elif thought.action == 'plan':
                # Planning action
                pass
        
        # Store memory
        if run.assistant_message:
            await self.memory_store.store(
                content=f"User: {user_message}\nAssistant: {run.assistant_message}",
                memory_type='short_term'
            )
        
        run.duration_ms = int((time.time() - start_time) * 1000)
        return run
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for agent."""
        tools = self.tool_registry.list_tools()
        tools_desc = "\n".join([f"- {t['name']}: {t['description']}" for t in tools])
        
        return f"""You are an AI assistant that can use tools to help users.

Available tools:
{tools_desc}

You must respond in the following format:
Observation: <what you observe>
Thought: <your reasoning>
Action: <respond|use_tool|plan>
Action Input: <JSON object with action parameters>

For respond action:
Action Input: {{"message": "your response"}}

For use_tool action:
Action Input: {{"tool": "tool_name", "params": {{"param1": "value1"}}}}

For plan action:
Action Input: {{"plan": ["step1", "step2"]}}
"""
    
    def _build_react_prompt(self, user_message: str, memory_context: str, previous_steps: List[ThoughtStep]) -> str:
        """Build ReAct prompt."""
        history = ""
        for step in previous_steps:
            history += f"Observation: {step.observation}\n"
            history += f"Thought: {step.reasoning}\n"
            history += f"Action: {step.action}\n"
            history += f"Action Input: {json.dumps(step.action_input)}\n\n"
        
        return f"""Previous memories:
{memory_context}

{history}
User: {user_message}

What is your next thought and action?"""
    
    def _parse_thought(self, content: str) -> ThoughtStep:
        """Parse LLM response into thought step."""
        lines = content.split('\n')
        observation = ''
        reasoning = ''
        action = 'respond'
        action_input = {}
        
        for line in lines:
            if line.startswith('Observation:'):
                observation = line.replace('Observation:', '').strip()
            elif line.startswith('Thought:'):
                reasoning = line.replace('Thought:', '').strip()
            elif line.startswith('Action:'):
                action = line.replace('Action:', '').strip()
            elif line.startswith('Action Input:'):
                try:
                    action_input = json.loads(line.replace('Action Input:', '').strip())
                except:
                    pass
        
        return ThoughtStep(
            observation=observation,
            reasoning=reasoning,
            action=action,
            action_input=action_input
        )
```

**Step 4: Commit**

```bash
git add backend/open_webui/pm/services/agent_runtime/
git commit -m "feat(agent): implement ReAct agent runtime with memory and tools"
```

---

## Phase 3: API Routes (Week 2-3)

### Task 6: Create Enhanced Workflow API

**Files:**
- Create: `backend/open_webui/pm/api/v2/workflows.py`
- Modify: `backend/open_webui/main.py`

**Step 1: Write v2/workflows.py**

```python
"""V2 Workflow API routes with enhanced features."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from open_webui.pm.database import get_db
from open_webui.pm.models.v2_workflow import V2Workflow, V2WorkflowExecution
from open_webui.pm.schemas.v2_workflow import (
    WorkflowCreate, WorkflowResponse, WorkflowUpdate,
    WorkflowExecutionCreate, WorkflowExecutionResponse
)
from open_webui.pm.services.workflow_engine.engine import WorkflowEngine
from open_webui.pm.services.workflow_engine.state import ExecutionStatus

# Import Timbal service
from backend.lib.timbal.execution_service import WorkflowExecutionService
from backend.lib.timbal.client import TimbalClient, TimbalConfig

router = APIRouter(prefix="/workflows", tags=["workflows"])

# Initialize services
timbal_config = TimbalConfig()
timbal_client = TimbalClient(timbal_config)
timbal_service = WorkflowExecutionService(timbal_client)
workflow_engine = WorkflowEngine(timbal_service=timbal_service)


@router.post("", response_model=WorkflowResponse)
async def create_workflow(workflow: WorkflowCreate, db: AsyncSession = Depends(get_db)):
    """Create a new workflow."""
    db_workflow = V2Workflow(**workflow.model_dump())
    db.add(db_workflow)
    await db.commit()
    await db.refresh(db_workflow)
    return db_workflow


@router.get("", response_model=List[WorkflowResponse])
async def list_workflows(project_id: UUID = None, db: AsyncSession = Depends(get_db)):
    """List workflows."""
    query = db.query(V2Workflow)
    if project_id:
        query = query.filter(V2Workflow.project_id == project_id)
    workflows = await query.all()
    return workflows


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a specific workflow."""
    workflow = await db.get(V2Workflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(workflow_id: UUID, workflow_update: WorkflowUpdate, db: AsyncSession = Depends(get_db)):
    """Update a workflow."""
    workflow = await db.get(V2Workflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    update_data = workflow_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workflow, field, value)
    
    await db.commit()
    await db.refresh(workflow)
    return workflow


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a workflow."""
    workflow = await db.get(V2Workflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    await db.delete(workflow)
    await db.commit()
    return {"message": "Workflow deleted"}


@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(workflow_id: UUID, execution: WorkflowExecutionCreate, db: AsyncSession = Depends(get_db)):
    """Execute a workflow."""
    workflow = await db.get(V2Workflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Create execution record
    db_execution = V2WorkflowExecution(
        workflow_id=workflow_id,
        status=ExecutionStatus.PENDING.value,
        input_data=execution.input_data,
        trigger_type=execution.trigger_type
    )
    db.add(db_execution)
    await db.commit()
    await db.refresh(db_execution)
    
    # Execute workflow
    state = await workflow_engine.execute_with_timbal(
        workflow_id=workflow_id,
        nodes=workflow.nodes,
        edges=workflow.edges,
        input_data=execution.input_data,
        sync=execution.trigger_type == 'manual'
    )
    
    # Update execution record
    db_execution.status = state.status.value
    db_execution.output_data = state.variables
    db_execution.node_states = state.to_dict()['node_results']
    if state.error:
        db_execution.error_message = state.error
    
    await db.commit()
    await db.refresh(db_execution)
    
    return db_execution


@router.get("/{workflow_id}/executions", response_model=List[WorkflowExecutionResponse])
async def list_executions(workflow_id: UUID, db: AsyncSession = Depends(get_db)):
    """List workflow executions."""
    executions = await db.query(V2WorkflowExecution).filter(
        V2WorkflowExecution.workflow_id == workflow_id
    ).all()
    return executions
```

**Step 2: Update main.py**

```python
# backend/open_webui/main.py

from open_webui.pm.api.v2 import workflows as v2_workflows

# Add to routes
app.include_router(v2_workflows.router, prefix="/api/v2", tags=["v2"])
```

**Step 3: Commit**

```bash
git add backend/open_webui/pm/api/v2/workflows.py
git add backend/open_webui/main.py
git commit -m "feat(api): add v2 workflow endpoints with Timbal integration"
```

---

### Task 7: Create Agent API

**Files:**
- Create: `backend/open_webui/pm/api/v2/agent.py`

**Step 1: Write v2/agent.py**

```python
"""V2 Agent API routes."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from open_webui.pm.database import get_db
from open_webui.pm.models.v2_agent import V2AgentSession, V2AgentRun
from open_webui.pm.schemas.v2_agent import (
    AgentSessionCreate, AgentSessionResponse, AgentSessionUpdate,
    ChatRequest, ChatResponse
)
from open_webui.pm.services.agent_runtime.agent import AgentRuntime
from open_webui.pm.services.agent_runtime.memory import MemoryStore
from open_webui.pm.services.agent_runtime.tools import ToolRegistry

router = APIRouter(prefix="/agent", tags=["agent"])

# Initialize agent runtime
tool_registry = ToolRegistry()
memory_store = MemoryStore()


@router.post("/sessions", response_model=AgentSessionResponse)
async def create_session(session: AgentSessionCreate, db: AsyncSession = Depends(get_db)):
    """Create a new agent session."""
    db_session = V2AgentSession(**session.model_dump())
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    return db_session


@router.get("/sessions/{session_id}", response_model=AgentSessionResponse)
async def get_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get agent session."""
    session = await db.get(V2AgentSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/sessions/{session_id}/chat", response_model=ChatResponse)
async def chat(session_id: UUID, request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Chat with agent."""
    session = await db.get(V2AgentSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Initialize agent runtime
    agent = AgentRuntime(
        llm_config=session.llm_config or {},
        tool_registry=tool_registry,
        memory_store=memory_store
    )
    
    # Run agent
    run = await agent.run(
        session_id=session_id,
        user_message=request.message
    )
    
    # Save run to database
    db_run = V2AgentRun(
        session_id=session_id,
        user_message=request.message,
        assistant_message=run.assistant_message,
        thought_process=[step.__dict__ for step in run.thought_process],
        tool_calls=run.tool_calls,
        token_usage=run.token_usage,
        duration_ms=run.duration_ms
    )
    db.add(db_run)
    await db.commit()
    
    return ChatResponse(
        message=run.assistant_message or "",
        run_id=db_run.id,
        tool_calls=run.tool_calls,
        token_usage=run.token_usage
    )


@router.get("/sessions/{session_id}/runs")
async def list_runs(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """List agent runs."""
    runs = await db.query(V2AgentRun).filter(
        V2AgentRun.session_id == session_id
    ).all()
    return runs


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete agent session."""
    session = await db.get(V2AgentSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    await db.delete(session)
    await db.commit()
    return {"message": "Session deleted"}
```

**Step 2: Commit**

```bash
git add backend/open_webui/pm/api/v2/agent.py
git commit -m "feat(api): add v2 agent session and chat endpoints"
```

---

## Phase 4: Frontend Components (Week 3)

### Task 8: Create Enhanced Workflow Designer

**Files:**
- Create: `src/lib/components/workflow-v2/WorkflowDesigner.svelte`
- Create: `src/lib/components/workflow-v2/NodeSidebar.svelte`
- Create: `src/lib/components/workflow-v2/PropertyPanel.svelte`
- Create: `src/lib/components/workflow-v2/Canvas.svelte`
- Create: `src/lib/components/workflow-v2/types.ts`

**Step 1: Write types.ts**

```typescript
// src/lib/components/workflow-v2/types.ts

export interface Point {
    x: number;
    y: number;
}

export interface Port {
    id: string;
    name: string;
    type: string;
    required: boolean;
}

export interface WorkflowNode {
    id: string;
    type: string;
    name: string;
    description?: string;
    position: Point;
    config: Record<string, any>;
    inputs: Port[];
    outputs: Port[];
}

export interface WorkflowEdge {
    id: string;
    source: string;
    target: string;
    condition?: string;
    label?: string;
}

export interface Workflow {
    id?: string;
    name: string;
    description?: string;
    nodes: WorkflowNode[];
    edges: WorkflowEdge[];
}

export const NODE_TYPES = [
    { type: 'start', label: 'Start', category: 'control', color: '#4CAF50' },
    { type: 'end', label: 'End', category: 'control', color: '#F44336' },
    { type: 'llm', label: 'LLM', category: 'ai', color: '#2196F3' },
    { type: 'condition', label: 'Condition', category: 'control', color: '#FF9800' },
    { type: 'variable_set', label: 'Set Variable', category: 'data', color: '#9C27B0' },
    { type: 'tool_call', label: 'Tool Call', category: 'tools', color: '#00BCD4' },
    { type: 'agent', label: 'Agent', category: 'ai', color: '#673AB7' },
    { type: 'skill_call', label: 'Skill Call', category: 'timbal', color: '#795548' },
] as const;
```

**Step 2: Write Canvas.svelte**

```svelte
<!-- src/lib/components/workflow-v2/Canvas.svelte -->
<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    import type { WorkflowNode, WorkflowEdge, Point } from './types';
    
    export let nodes: WorkflowNode[] = [];
    export let edges: WorkflowEdge[] = [];
    export let selectedNode: WorkflowNode | null = null;
    
    const dispatch = createEventDispatcher<{
        nodeSelect: WorkflowNode;
        nodeMove: { nodeId: string; position: Point };
    }>();
    
    let draggingNode: string | null = null;
    let dragOffset = { x: 0, y: 0 };
    
    function handleMouseDown(event: MouseEvent, node: WorkflowNode) {
        event.stopPropagation();
        draggingNode = node.id;
        dragOffset = {
            x: event.clientX - node.position.x,
            y: event.clientY - node.position.y
        };
        selectedNode = node;
        dispatch('nodeSelect', node);
    }
    
    function handleMouseMove(event: MouseEvent) {
        if (draggingNode) {
            const node = nodes.find(n => n.id === draggingNode);
            if (node) {
                const newPosition = {
                    x: event.clientX - dragOffset.x,
                    y: event.clientY - dragOffset.y
                };
                dispatch('nodeMove', { nodeId: draggingNode, position: newPosition });
            }
        }
    }
    
    function handleMouseUp() {
        draggingNode = null;
    }
    
    function getEdgePath(edge: WorkflowEdge): string {
        const sourceNode = nodes.find(n => n.id === edge.source);
        const targetNode = nodes.find(n => n.id === edge.target);
        
        if (!sourceNode || !targetNode) return '';
        
        const startX = sourceNode.position.x + 100;
        const startY = sourceNode.position.y + 40;
        const endX = targetNode.position.x;
        const endY = targetNode.position.y + 40;
        
        const midX = (startX + endX) / 2;
        
        return `M ${startX} ${startY} C ${midX} ${startY}, ${midX} ${endY}, ${endX} ${endY}`;
    }
    
    function getNodeColor(type: string): string {
        const colors: Record<string, string> = {
            'start': '#4CAF50',
            'end': '#F44336',
            'llm': '#2196F3',
            'condition': '#FF9800',
            'variable_set': '#9C27B0',
            'tool_call': '#00BCD4',
            'agent': '#673AB7',
            'skill_call': '#795548'
        };
        return colors[type] || '#757575';
    }
</script>

<svg 
    class="workflow-canvas"
    on:mousemove={handleMouseMove}
    on:mouseup={handleMouseUp}
>
    <defs>
        <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
            <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#e0e0e0" stroke-width="0.5"/>
        </pattern>
    </defs>
    <rect width="100%" height="100%" fill="url(#grid)" />
    
    {#each edges as edge}
        <path 
            d={getEdgePath(edge)}
            fill="none"
            stroke="#999"
            stroke-width="2"
            marker-end="url(#arrowhead)"
        />
    {/each}
    
    {#each nodes as node}
        <g 
            transform={`translate(${node.position.x}, ${node.position.y})`}
            class="workflow-node"
            class:selected={selectedNode?.id === node.id}
            on:mousedown={(e) => handleMouseDown(e, node)}
        >
            <rect 
                width="100" 
                height="80" 
                rx="8" 
                fill={getNodeColor(node.type)}
                stroke={selectedNode?.id === node.id ? '#333' : 'none'}
                stroke-width="2"
            />
            <text x="50" y="30" text-anchor="middle" fill="white" font-size="12" font-weight="bold">
                {node.name}
            </text>
            <text x="50" y="50" text-anchor="middle" fill="white" font-size="10">
                {node.type}
            </text>
        </g>
    {/each}
    
    <defs>
        <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="#999" />
        </marker>
    </defs>
</svg>

<style>
    .workflow-canvas {
        width: 100%;
        height: 100%;
        min-height: 600px;
        cursor: grab;
    }
    
    .workflow-canvas:active {
        cursor: grabbing;
    }
    
    .workflow-node {
        cursor: pointer;
        transition: filter 0.2s;
    }
    
    .workflow-node:hover {
        filter: brightness(1.1);
    }
    
    .workflow-node.selected rect {
        stroke: #333;
        stroke-width: 3;
    }
</style>
```

**Step 3: Write WorkflowDesigner.svelte**

```svelte
<!-- src/lib/components/workflow-v2/WorkflowDesigner.svelte -->
<script lang="ts">
    import type { Workflow, WorkflowNode, WorkflowEdge, Point } from './types';
    import Canvas from './Canvas.svelte';
    import NodeSidebar from './NodeSidebar.svelte';
    import PropertyPanel from './PropertyPanel.svelte';
    
    export let workflow: Workflow = {
        name: 'New Workflow',
        nodes: [],
        edges: []
    };
    
    let selectedNode: WorkflowNode | null = null;
    let nodeIdCounter = 0;
    
    function generateNodeId(): string {
        return `node_${++nodeIdCounter}`;
    }
    
    function handleNodeSelect(node: WorkflowNode) {
        selectedNode = node;
    }
    
    function handleNodeMove(event: CustomEvent<{ nodeId: string; position: Point }>) {
        const { nodeId, position } = event.detail;
        const node = workflow.nodes.find(n => n.id === nodeId);
        if (node) {
            node.position = position;
            workflow = workflow;
        }
    }
    
    function handleDrop(event: DragEvent) {
        event.preventDefault();
        const data = event.dataTransfer?.getData('application/json');
        if (data) {
            const { type } = JSON.parse(data);
            const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
            const position = {
                x: event.clientX - rect.left,
                y: event.clientY - rect.top
            };
            
            const newNode: WorkflowNode = {
                id: generateNodeId(),
                type,
                name: type.charAt(0).toUpperCase() + type.slice(1),
                position,
                config: {},
                inputs: [],
                outputs: []
            };
            
            workflow.nodes = [...workflow.nodes, newNode];
        }
    }
    
    function handleDragOver(event: DragEvent) {
        event.preventDefault();
    }
    
    async function saveWorkflow() {
        // TODO: Implement API call
        console.log('Saving workflow:', workflow);
    }
</script>

<div class="workflow-designer">
    <div class="designer-header">
        <h2>{workflow.name}</h2>
        <button class="save-button" on:click={saveWorkflow}>Save</button>
    </div>
    
    <div class="designer-body">
        <NodeSidebar />
        
        <div 
            class="canvas-container"
            on:drop={handleDrop}
            on:dragover={handleDragOver}
        >
            <Canvas 
                {workflow}
                bind:selectedNode
                on:nodeSelect={(e) => handleNodeSelect(e.detail)}
                on:nodeMove={handleNodeMove}
            />
        </div>
        
        <PropertyPanel node={selectedNode} />
    </div>
</div>

<style>
    .workflow-designer {
        display: flex;
        flex-direction: column;
        height: 100vh;
    }
    
    .designer-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px;
        border-bottom: 1px solid #ddd;
    }
    
    .designer-header h2 {
        margin: 0;
        font-size: 20px;
    }
    
    .save-button {
        padding: 8px 16px;
        background: #2196F3;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 14px;
    }
    
    .save-button:hover {
        background: #1976D2;
    }
    
    .designer-body {
        display: flex;
        flex: 1;
        overflow: hidden;
    }
    
    .canvas-container {
        flex: 1;
        overflow: hidden;
    }
</style>
```

**Step 4: Commit**

```bash
git add src/lib/components/workflow-v2/
git commit -m "feat(ui): add enhanced workflow designer components"
```

---

## Phase 5: Integration & Testing (Week 3-4)

### Task 9: Integrate with Existing Routes

**Files:**
- Modify: `src/routes/(app)/workflows/[workflowId]/+page.svelte`

**Step 1: Update workflow designer page**

```svelte
<!-- src/routes/(app)/workflows/[workflowId]/+page.svelte -->
<script lang="ts">
    import { page } from '$app/stores';
    import WorkflowDesigner from '$lib/components/workflow-v2/WorkflowDesigner.svelte';
    import type { Workflow } from '$lib/components/workflow-v2/types';
    
    const workflowId = $page.params.workflowId;
    
    let workflow: Workflow = {
        id: workflowId,
        name: 'My Workflow',
        nodes: [],
        edges: []
    };
</script>

<div class="workflow-page">
    <WorkflowDesigner {workflow} />
</div>

<style>
    .workflow-page {
        height: 100vh;
        display: flex;
        flex-direction: column;
    }
</style>
```

**Step 2: Commit**

```bash
git add src/routes/(app)/workflows/[workflowId]/+page.svelte
git commit -m "feat(ui): integrate enhanced workflow designer into app routes"
```

---

### Task 10: Add Tests

**Files:**
- Create: `backend/tests/services/test_dag.py`
- Create: `backend/tests/services/test_workflow_engine.py`

**Step 1: Write tests**

```python
"""Tests for DAG parser and workflow engine."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from open_webui.pm.services.workflow_engine.dag import DAG, DAGNode, DAGEdge, parse_dag
from open_webui.pm.services.workflow_engine.engine import WorkflowEngine
from open_webui.pm.services.workflow_engine.state import ExecutionStatus, NodeStatus


class TestDAG:
    """Test cases for DAG operations."""
    
    def test_topological_sort_linear(self):
        """Test topological sort with linear graph."""
        dag = DAG()
        dag.add_node(DAGNode(id='A', type='start'))
        dag.add_node(DAGNode(id='B', type='process'))
        dag.add_node(DAGNode(id='C', type='end'))
        dag.add_edge(DAGEdge(id='e1', source='A', target='B'))
        dag.add_edge(DAGEdge(id='e2', source='B', target='C'))
        
        result = dag.topological_sort()
        assert result == ['A', 'B', 'C']
    
    def test_topological_sort_cycle_detection(self):
        """Test cycle detection."""
        dag = DAG()
        dag.add_node(DAGNode(id='A', type='start'))
        dag.add_node(DAGNode(id='B', type='process'))
        dag.add_node(DAGNode(id='C', type='process'))
        dag.add_edge(DAGEdge(id='e1', source='A', target='B'))
        dag.add_edge(DAGEdge(id='e2', source='B', target='C'))
        dag.add_edge(DAGEdge(id='e3', source='C', target='A'))
        
        with pytest.raises(ValueError, match="cycle"):
            dag.topological_sort()


class TestWorkflowEngine:
    """Test cases for workflow engine."""
    
    @pytest.fixture
    def engine(self):
        """Create workflow engine."""
        return WorkflowEngine()
    
    @pytest.mark.asyncio
    async def test_execute_linear_workflow(self, engine):
        """Test executing a linear workflow."""
        nodes = [
            {'id': 'start', 'type': 'start', 'config': {}},
            {'id': 'process', 'type': 'variable_set', 'config': {'variables': {'test': 'value'}}},
            {'id': 'end', 'type': 'end', 'config': {}}
        ]
        
        edges = [
            {'id': 'e1', 'source': 'start', 'target': 'process'},
            {'id': 'e2', 'source': 'process', 'target': 'end'}
        ]
        
        state = await engine.execute(
            workflow_id='test-workflow',
            nodes=nodes,
            edges=edges
        )
        
        assert state.status == ExecutionStatus.COMPLETED
        assert len(state.node_results) == 3
        assert state.get_variable('test') == 'value'
```

**Step 2: Commit**

```bash
git add backend/tests/services/test_dag.py
git add backend/tests/services/test_workflow_engine.py
git commit -m "test: add DAG and workflow engine tests"
```

---

## Summary

This enhanced Timbal-based implementation plan:

1. **Builds on existing Timbal foundation** - Keeps all existing Timbal code
2. **Adds DAG-based orchestration** - New engine with topological sort, state management
3. **Extends node types** - From skill-only to 15+ node types including control flow, LLM, data processing
4. **Adds Agent runtime** - ReAct pattern with memory and tool use
5. **Provides visual designer** - Enhanced Svelte 5 components
6. **Maintains backward compatibility** - Existing Timbal routes still work

**Timeline**: 3-4 weeks (vs 4-5 weeks for pure custom)
**Risk**: Low (based on stable Timbal foundation)
**Extensibility**: High (plugin-based node registry)

---

**Ready to execute?** Choose:
1. **Subagent-driven** - I dispatch tasks to specialized agents
2. **Sequential execution** - I implement tasks one by one in this session
