# Workflow + Agent Engine Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Dify-style Workflow engine and Agent runtime for open-pm-webui, replacing the existing basic workflow system with a powerful, flexible architecture supporting visual workflow orchestration and autonomous agent execution.

**Architecture:** Layered architecture with Workflow Engine and Agent Runtime as independent services sharing common infrastructure (LLM Adapter, Tool Registry, Memory Store). FastAPI backend with Svelte 5 frontend. PostgreSQL with pgvector for data and embeddings.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic, Svelte 5, TypeScript, Tailwind CSS, PostgreSQL, pgvector, Redis

---

## Phase 1: Foundation (Database & Core Models)

### Task 1: Create Alembic Migration for v2 Tables

**Files:**
- Create: `backend/alembic/versions/20260714_add_v2_workflow_tables.py`
- Modify: `backend/open_webui/pm/models/__init__.py`

**Step 1: Write migration file**

```python
"""Add v2 workflow and agent tables

Revision ID: 20260714_add_v2_workflow_tables
Revises: <previous_revision>
Create Date: 2026-07-14
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '20260714_add_v2_workflow_tables'
down_revision = '<previous_revision>'  # Update this
branch_labels = None
depends_on = None


def upgrade():
    # v2_workflows
    op.create_table(
        'v2_workflows',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('pm_project.id')),
        sa.Column('nodes', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('edges', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('version', sa.Integer(), server_default='1'),
        sa.Column('is_template', sa.Boolean(), server_default='false'),
        sa.Column('category', sa.String(50)),
        sa.Column('status', sa.String(20), server_default='draft'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'))
    )
    
    # v2_workflow_executions
    op.create_table(
        'v2_workflow_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('v2_workflows.id', ondelete='CASCADE')),
        sa.Column('status', sa.String(20)),
        sa.Column('trigger_type', sa.String(20)),
        sa.Column('input_data', postgresql.JSONB()),
        sa.Column('output_data', postgresql.JSONB()),
        sa.Column('context', postgresql.JSONB()),
        sa.Column('node_states', postgresql.JSONB()),
        sa.Column('error_message', sa.Text()),
        sa.Column('error_node_id', postgresql.UUID(as_uuid=True)),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'))
    )
    
    # v2_agent_sessions
    op.create_table(
        'v2_agent_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255)),
        sa.Column('agent_type', sa.String(50)),
        sa.Column('llm_config', postgresql.JSONB()),
        sa.Column('memory_config', postgresql.JSONB()),
        sa.Column('allowed_tools', postgresql.JSONB()),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('v2_workflows.id')),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'))
    )
    
    # v2_agent_runs
    op.create_table(
        'v2_agent_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('v2_agent_sessions.id', ondelete='CASCADE')),
        sa.Column('user_message', sa.Text(), nullable=False),
        sa.Column('thought_process', postgresql.JSONB()),
        sa.Column('tool_calls', postgresql.JSONB()),
        sa.Column('assistant_message', sa.Text()),
        sa.Column('memories_used', postgresql.JSONB()),
        sa.Column('workflow_execution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('v2_workflow_executions.id')),
        sa.Column('token_usage', postgresql.JSONB()),
        sa.Column('duration_ms', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'))
    )
    
    # v2_tools
    op.create_table(
        'v2_tools',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('category', sa.String(50)),
        sa.Column('config_schema', postgresql.JSONB()),
        sa.Column('input_schema', postgresql.JSONB()),
        sa.Column('output_schema', postgresql.JSONB()),
        sa.Column('execution_type', sa.String(20)),
        sa.Column('execution_config', postgresql.JSONB()),
        sa.Column('auth_config', postgresql.JSONB()),
        sa.Column('is_builtin', sa.Boolean(), server_default='false'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'))
    )
    
    # v2_memories (requires pgvector extension)
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    op.create_table(
        'v2_memories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('v2_agent_sessions.id', ondelete='CASCADE')),
        sa.Column('memory_type', sa.String(20)),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', sa.Text()),  # Will be updated to VECTOR(1536) after pgvector setup
        sa.Column('metadata', postgresql.JSONB()),
        sa.Column('importance_score', sa.Float()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.Column('accessed_at', sa.DateTime())
    )
    
    # Create indexes
    op.create_index('idx_v2_workflows_project', 'v2_workflows', ['project_id'])
    op.create_index('idx_v2_workflows_status', 'v2_workflows', ['status'])
    op.create_index('idx_v2_executions_workflow', 'v2_workflow_executions', ['workflow_id'])
    op.create_index('idx_v2_executions_status', 'v2_workflow_executions', ['status'])
    op.create_index('idx_v2_agent_sessions_workflow', 'v2_agent_sessions', ['workflow_id'])
    op.create_index('idx_v2_agent_runs_session', 'v2_agent_runs', ['session_id'])
    op.create_index('idx_v2_memories_session', 'v2_memories', ['session_id'])


def downgrade():
    op.drop_table('v2_memories')
    op.drop_table('v2_tools')
    op.drop_table('v2_agent_runs')
    op.drop_table('v2_agent_sessions')
    op.drop_table('v2_workflow_executions')
    op.drop_table('v2_workflows')
```

**Step 2: Run migration**

```bash
cd backend
alembic upgrade head
```

**Step 3: Verify tables created**

```bash
psql -d open_pm_webui -c "\dt v2_*"
```

**Step 4: Commit**

```bash
git add backend/alembic/versions/20260714_add_v2_workflow_tables.py
git commit -m "feat(db): add v2 workflow and agent tables"
```

---

### Task 2: Create SQLAlchemy Models

**Files:**
- Create: `backend/open_webui/pm/models/v2_workflow.py`
- Create: `backend/open_webui/pm/models/v2_agent.py`
- Modify: `backend/open_webui/pm/models/__init__.py`

**Step 1: Write v2_workflow.py**

```python
"""SQLAlchemy models for v2 workflow system."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import relationship

from open_webui.pm.models import Base


class V2Workflow(Base):
    """Workflow definition model."""
    
    __tablename__ = 'v2_workflows'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey('pm_project.id'))
    
    # DAG definition stored as JSONB
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
    """Workflow execution instance model."""
    
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


class V2Tool(Base):
    """Tool registry model."""
    
    __tablename__ = 'v2_tools'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(50))
    
    # Schemas
    config_schema = Column(JSONB)
    input_schema = Column(JSONB)
    output_schema = Column(JSONB)
    
    # Execution
    execution_type = Column(String(20))
    execution_config = Column(JSONB)
    auth_config = Column(JSONB)
    
    is_builtin = Column(Boolean, default=False)
    created_by = Column(PGUUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Step 2: Write v2_agent.py**

```python
"""SQLAlchemy models for v2 agent system."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Boolean, Float
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import relationship

from open_webui.pm.models import Base


class V2AgentSession(Base):
    """Agent session model."""
    
    __tablename__ = 'v2_agent_sessions'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255))
    
    # Configuration
    agent_type = Column(String(50))
    llm_config = Column(JSONB)
    memory_config = Column(JSONB)
    allowed_tools = Column(JSONB)
    
    # Associated workflow
    workflow_id = Column(PGUUID(as_uuid=True), ForeignKey('v2_workflows.id'))
    
    status = Column(String(20), default='active')
    created_by = Column(PGUUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    workflow = relationship("V2Workflow", back_populates="agent_sessions")
    runs = relationship("V2AgentRun", back_populates="session", cascade="all, delete-orphan")


class V2AgentRun(Base):
    """Agent execution run model."""
    
    __tablename__ = 'v2_agent_runs'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey('v2_agent_sessions.id', ondelete='CASCADE'))
    
    # User input
    user_message = Column(Text, nullable=False)
    
    # Agent reasoning
    thought_process = Column(JSONB)
    tool_calls = Column(JSONB)
    assistant_message = Column(Text)
    memories_used = Column(JSONB)
    
    # Associated workflow execution
    workflow_execution_id = Column(PGUUID(as_uuid=True), ForeignKey('v2_workflow_executions.id'))
    
    # Performance
    token_usage = Column(JSONB)
    duration_ms = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("V2AgentSession", back_populates="runs")
    workflow_execution = relationship("V2WorkflowExecution", back_populates="agent_runs")


class V2Memory(Base):
    """Memory storage model."""
    
    __tablename__ = 'v2_memories'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey('v2_agent_sessions.id', ondelete='CASCADE'))
    
    memory_type = Column(String(20))
    content = Column(Text, nullable=False)
    embedding = Column(Text)  # Will be updated to Vector(1536) with pgvector
    metadata = Column(JSONB)
    importance_score = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    accessed_at = Column(DateTime)
```

**Step 3: Update __init__.py**

```python
# backend/open_webui/pm/models/__init__.py

from .v2_workflow import V2Workflow, V2WorkflowExecution, V2Tool
from .v2_agent import V2AgentSession, V2AgentRun, V2Memory

__all__ = [
    # ... existing models ...
    'V2Workflow',
    'V2WorkflowExecution',
    'V2Tool',
    'V2AgentSession',
    'V2AgentRun',
    'V2Memory',
]
```

**Step 4: Commit**

```bash
git add backend/open_webui/pm/models/v2_workflow.py
git add backend/open_webui/pm/models/v2_agent.py
git add backend/open_webui/pm/models/__init__.py
git commit -m "feat(models): add v2 workflow and agent SQLAlchemy models"
```

---

### Task 3: Create Pydantic Schemas

**Files:**
- Create: `backend/open_webui/pm/schemas/v2_workflow.py`
- Create: `backend/open_webui/pm/schemas/v2_agent.py`

**Step 1: Write v2_workflow.py schemas**

```python
"""Pydantic schemas for v2 workflow system."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============= Node Schemas =============

class PortDefinition(BaseModel):
    """Input/Output port definition."""
    id: str
    name: str
    type: str = Field(..., pattern=r'^(string|number|boolean|object|array|any)$')
    required: bool = True
    description: Optional[str] = None


class NodeConfig(BaseModel):
    """Workflow node configuration."""
    id: str
    type: str
    name: str
    description: Optional[str] = None
    position: Dict[str, float] = Field(default_factory=dict)
    config: Dict[str, Any] = Field(default_factory=dict)
    inputs: List[PortDefinition] = Field(default_factory=list)
    outputs: List[PortDefinition] = Field(default_factory=list)
    error_handling: Optional[Dict[str, Any]] = None


class EdgeConfig(BaseModel):
    """Workflow edge configuration."""
    id: str
    source: str
    target: str
    condition: Optional[str] = None
    label: Optional[str] = None


# ============= Workflow Schemas =============

class WorkflowBase(BaseModel):
    """Base workflow schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    project_id: Optional[UUID] = None
    nodes: List[NodeConfig] = Field(default_factory=list)
    edges: List[EdgeConfig] = Field(default_factory=list)
    category: Optional[str] = None
    status: str = 'draft'


class WorkflowCreate(WorkflowBase):
    """Schema for creating a workflow."""
    pass


class WorkflowUpdate(BaseModel):
    """Schema for updating a workflow."""
    name: Optional[str] = None
    description: Optional[str] = None
    nodes: Optional[List[NodeConfig]] = None
    edges: Optional[List[EdgeConfig]] = None
    status: Optional[str] = None


class WorkflowResponse(WorkflowBase):
    """Schema for workflow response."""
    id: UUID
    version: int
    is_template: bool
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============= Execution Schemas =============

class WorkflowExecutionBase(BaseModel):
    """Base execution schema."""
    workflow_id: UUID
    input_data: Optional[Dict[str, Any]] = None
    trigger_type: str = 'manual'


class WorkflowExecutionCreate(WorkflowExecutionBase):
    """Schema for creating execution."""
    pass


class WorkflowExecutionResponse(WorkflowExecutionBase):
    """Schema for execution response."""
    id: UUID
    status: str
    output_data: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    node_states: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= Tool Schemas =============

class ToolBase(BaseModel):
    """Base tool schema."""
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    config_schema: Optional[Dict[str, Any]] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    execution_type: Optional[str] = None
    execution_config: Optional[Dict[str, Any]] = None


class ToolCreate(ToolBase):
    """Schema for creating a tool."""
    pass


class ToolResponse(ToolBase):
    """Schema for tool response."""
    id: UUID
    is_builtin: bool
    created_by: Optional[UUID] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
```

**Step 2: Write v2_agent.py schemas**

```python
"""Pydantic schemas for v2 agent system."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============= LLM Config =============

class LLMConfig(BaseModel):
    """LLM configuration."""
    model: str = 'gpt-4'
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=2048, gt=0)
    top_p: float = Field(default=1.0, ge=0, le=1)


# ============= Memory Config =============

class MemoryConfig(BaseModel):
    """Memory configuration."""
    short_term_size: int = Field(default=10, gt=0)
    long_term_enabled: bool = False
    embedding_model: str = 'text-embedding-3-small'


# ============= Agent Session =============

class AgentSessionBase(BaseModel):
    """Base agent session schema."""
    name: Optional[str] = None
    agent_type: str = 'react'
    llm_config: LLMConfig = Field(default_factory=LLMConfig)
    memory_config: MemoryConfig = Field(default_factory=MemoryConfig)
    allowed_tools: List[str] = Field(default_factory=list)
    workflow_id: Optional[UUID] = None


class AgentSessionCreate(AgentSessionBase):
    """Schema for creating agent session."""
    pass


class AgentSessionUpdate(BaseModel):
    """Schema for updating agent session."""
    name: Optional[str] = None
    llm_config: Optional[LLMConfig] = None
    memory_config: Optional[MemoryConfig] = None
    allowed_tools: Optional[List[str]] = None
    status: Optional[str] = None


class AgentSessionResponse(AgentSessionBase):
    """Schema for agent session response."""
    id: UUID
    status: str
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============= Agent Run =============

class ThoughtStep(BaseModel):
    """Single thought step in ReAct loop."""
    step: int
    observation: str
    reasoning: str
    action: str
    action_input: Optional[Dict[str, Any]] = None


class ToolCallRecord(BaseModel):
    """Tool call record."""
    tool_id: str
    tool_name: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    duration_ms: Optional[int] = None
    error: Optional[str] = None


class AgentRunBase(BaseModel):
    """Base agent run schema."""
    session_id: UUID
    user_message: str


class AgentRunCreate(AgentRunBase):
    """Schema for creating agent run."""
    pass


class AgentRunResponse(AgentRunBase):
    """Schema for agent run response."""
    id: UUID
    thought_process: List[ThoughtStep] = Field(default_factory=list)
    tool_calls: List[ToolCallRecord] = Field(default_factory=list)
    assistant_message: Optional[str] = None
    memories_used: List[str] = Field(default_factory=list)
    workflow_execution_id: Optional[UUID] = None
    token_usage: Optional[Dict[str, int]] = None
    duration_ms: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= Chat =============

class ChatMessage(BaseModel):
    """Chat message schema."""
    role: str = Field(..., pattern=r'^(user|assistant|system)$')
    content: str


class ChatRequest(BaseModel):
    """Chat request schema."""
    message: str
    session_id: Optional[UUID] = None
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Chat response schema."""
    message: str
    run_id: Optional[UUID] = None
    tool_calls: List[ToolCallRecord] = Field(default_factory=list)
    token_usage: Optional[Dict[str, int]] = None
```

**Step 3: Commit**

```bash
git add backend/open_webui/pm/schemas/v2_workflow.py
git add backend/open_webui/pm/schemas/v2_agent.py
git commit -m "feat(schemas): add v2 workflow and agent Pydantic schemas"
```

---

## Phase 2: Workflow Engine Core

### Task 4: Implement DAG Parser and Topological Sort

**Files:**
- Create: `backend/open_webui/pm/services/workflow_engine/dag.py`
- Test: `backend/tests/services/test_dag.py`

**Step 1: Write dag.py**

```python
"""DAG (Directed Acyclic Graph) parser and utilities for workflow execution."""

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


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
        """
        Perform topological sort on the DAG.
        
        Returns:
            List of node IDs in topological order.
            
        Raises:
            ValueError: If the graph contains a cycle.
        """
        # Calculate in-degrees
        in_degree = defaultdict(int)
        for node_id in self.nodes:
            in_degree[node_id] = self._indegree.get(node_id, 0)
        
        # Initialize queue with nodes having in-degree 0
        queue = deque([node_id for node_id in self.nodes if in_degree[node_id] == 0])
        result = []
        
        while queue:
            node_id = queue.popleft()
            result.append(node_id)
            
            # Reduce in-degree for neighbors
            for neighbor in self._adjacency[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check for cycles
        if len(result) != len(self.nodes):
            raise ValueError("Workflow contains a cycle. DAG must be acyclic.")
        
        return result
    
    def get_predecessors(self, node_id: str) -> List[str]:
        """Get all predecessor nodes for a given node."""
        return self._reverse_adjacency.get(node_id, [])
    
    def get_successors(self, node_id: str) -> List[str]:
        """Get all successor nodes for a given node."""
        return self._adjacency.get(node_id, [])
    
    def get_node(self, node_id: str) -> Optional[DAGNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """
        Validate the DAG structure.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
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
    """
    Parse nodes and edges into a DAG.
    
    Args:
        nodes: List of node dictionaries
        edges: List of edge dictionaries
        
    Returns:
        Constructed DAG instance
    """
    dag = DAG()
    
    # Add nodes
    for node_data in nodes:
        node = DAGNode(
            id=node_data['id'],
            type=node_data['type'],
            config=node_data.get('config', {}),
            inputs=node_data.get('inputs', []),
            outputs=node_data.get('outputs', [])
        )
        dag.add_node(node)
    
    # Add edges
    for edge_data in edges:
        edge = DAGEdge(
            id=edge_data['id'],
            source=edge_data['source'],
            target=edge_data['target'],
            condition=edge_data.get('condition'),
            label=edge_data.get('label')
        )
        dag.add_edge(edge)
    
    return dag
```

**Step 2: Write tests**

```python
"""Tests for DAG parser and utilities."""

import pytest
from open_webui.pm.services.workflow_engine.dag import DAG, DAGNode, DAGEdge, parse_dag


class TestDAG:
    """Test cases for DAG operations."""
    
    def test_topological_sort_linear(self):
        """Test topological sort with linear graph."""
        dag = DAG()
        
        # Create linear graph: A -> B -> C
        dag.add_node(DAGNode(id='A', type='start'))
        dag.add_node(DAGNode(id='B', type='process'))
        dag.add_node(DAGNode(id='C', type='end'))
        
        dag.add_edge(DAGEdge(id='e1', source='A', target='B'))
        dag.add_edge(DAGEdge(id='e2', source='B', target='C'))
        
        result = dag.topological_sort()
        assert result == ['A', 'B', 'C']
    
    def test_topological_sort_branching(self):
        """Test topological sort with branching graph."""
        dag = DAG()
        
        # Create graph: A -> B -> D
        #                    -> C -> D
        dag.add_node(DAGNode(id='A', type='start'))
        dag.add_node(DAGNode(id='B', type='process'))
        dag.add_node(DAGNode(id='C', type='process'))
        dag.add_node(DAGNode(id='D', type='end'))
        
        dag.add_edge(DAGEdge(id='e1', source='A', target='B'))
        dag.add_edge(DAGEdge(id='e2', source='A', target='C'))
        dag.add_edge(DAGEdge(id='e3', source='B', target='D'))
        dag.add_edge(DAGEdge(id='e4', source='C', target='D'))
        
        result = dag.topological_sort()
        assert result[0] == 'A'
        assert result[-1] == 'D'
        assert set(result[1:3]) == {'B', 'C'}
    
    def test_topological_sort_cycle_detection(self):
        """Test cycle detection in topological sort."""
        dag = DAG()
        
        # Create cyclic graph: A -> B -> C -> A
        dag.add_node(DAGNode(id='A', type='start'))
        dag.add_node(DAGNode(id='B', type='process'))
        dag.add_node(DAGNode(id='C', type='process'))
        
        dag.add_edge(DAGEdge(id='e1', source='A', target='B'))
        dag.add_edge(DAGEdge(id='e2', source='B', target='C'))
        dag.add_edge(DAGEdge(id='e3', source='C', target='A'))
        
        with pytest.raises(ValueError, match="cycle"):
            dag.topological_sort()
    
    def test_validate_valid_dag(self):
        """Test validation of valid DAG."""
        dag = DAG()
        dag.add_node(DAGNode(id='A', type='start'))
        dag.add_node(DAGNode(id='B', type='end'))
        dag.add_edge(DAGEdge(id='e1', source='A', target='B'))
        
        is_valid, error = dag.validate()
        assert is_valid is True
        assert error is None
    
    def test_validate_cycle(self):
        """Test validation of cyclic graph."""
        dag = DAG()
        dag.add_node(DAGNode(id='A', type='start'))
        dag.add_node(DAGNode(id='B', type='process'))
        dag.add_edge(DAGEdge(id='e1', source='A', target='B'))
        dag.add_edge(DAGEdge(id='e2', source='B', target='A'))
        
        is_valid, error = dag.validate()
        assert is_valid is False
        assert "cycle" in error.lower()


class TestParseDAG:
    """Test cases for parse_dag function."""
    
    def test_parse_simple_workflow(self):
        """Test parsing a simple workflow."""
        nodes = [
            {'id': 'start', 'type': 'start'},
            {'id': 'process', 'type': 'llm'},
            {'id': 'end', 'type': 'end'}
        ]
        
        edges = [
            {'id': 'e1', 'source': 'start', 'target': 'process'},
            {'id': 'e2', 'source': 'process', 'target': 'end'}
        ]
        
        dag = parse_dag(nodes, edges)
        
        assert len(dag.nodes) == 3
        assert len(dag.edges) == 2
        
        result = dag.topological_sort()
        assert result == ['start', 'process', 'end']
```

**Step 3: Run tests**

```bash
cd backend
pytest tests/services/test_dag.py -v
```

**Step 4: Commit**

```bash
git add backend/open_webui/pm/services/workflow_engine/dag.py
git add backend/tests/services/test_dag.py
git commit -m "feat(engine): implement DAG parser and topological sort"
```

---

### Task 5: Implement Workflow Execution Engine

**Files:**
- Create: `backend/open_webui/pm/services/workflow_engine/engine.py`
- Create: `backend/open_webui/pm/services/workflow_engine/state.py`
- Create: `backend/open_webui/pm/services/workflow_engine/nodes/__init__.py`
- Create: `backend/open_webui/pm/services/workflow_engine/nodes/base.py`

**Step 1: Write state.py**

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

**Step 2: Write base.py**

```python
"""Base node executor class."""

from abc import ABC, abstractmethod
from typing import Any, Dict

from .state import ExecutionState, NodeResult


class BaseNodeExecutor(ABC):
    """Base class for all node executors."""
    
    @abstractmethod
    async def execute(self, node_config: Dict[str, Any], state: ExecutionState) -> NodeResult:
        """
        Execute the node.
        
        Args:
            node_config: Node configuration
            state: Current execution state
            
        Returns:
            Node execution result
        """
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate node configuration.
        
        Args:
            config: Node configuration
            
        Returns:
            True if valid
        """
        return True
    
    def get_required_inputs(self) -> list:
        """Get list of required input names."""
        return []
    
    def get_outputs(self) -> list:
        """Get list of output names."""
        return []
```

**Step 3: Write engine.py**

```python
"""Workflow execution engine."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from open_webui.pm.services.workflow_engine.dag import DAG, DAGNode, parse_dag
from open_webui.pm.services.workflow_engine.state import (
    ExecutionState,
    ExecutionStatus,
    NodeResult,
    NodeStatus
)
from open_webui.pm.services.workflow_engine.nodes.base import BaseNodeExecutor

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """DAG-based workflow execution engine."""
    
    def __init__(self):
        self.node_registry: Dict[str, BaseNodeExecutor] = {}
    
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
        """
        Execute a workflow.
        
        Args:
            workflow_id: Workflow ID
            nodes: List of node configurations
            edges: List of edge configurations
            input_data: Optional input data
            
        Returns:
            Final execution state
        """
        # Initialize state
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
                        # Handle error based on node error handling config
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
```

**Step 4: Commit**

```bash
git add backend/open_webui/pm/services/workflow_engine/
git commit -m "feat(engine): implement workflow execution engine with state management"
```

---

### Task 6: Implement Basic Node Executors

**Files:**
- Create: `backend/open_webui/pm/services/workflow_engine/nodes/start.py`
- Create: `backend/open_webui/pm/services/workflow_engine/nodes/end.py`
- Create: `backend/open_webui/pm/services/workflow_engine/nodes/llm.py`
- Create: `backend/open_webui/pm/services/workflow_engine/nodes/condition.py`
- Create: `backend/open_webui/pm/services/workflow_engine/nodes/variable_set.py`

**Step 1: Write start.py**

```python
"""Start node executor."""

from typing import Any, Dict

from .base import BaseNodeExecutor
from ..state import ExecutionState, NodeResult, NodeStatus


class StartNodeExecutor(BaseNodeExecutor):
    """Executor for start nodes."""
    
    async def execute(self, node_config: Dict[str, Any], state: ExecutionState) -> NodeResult:
        """Start node simply passes through."""
        return NodeResult(
            status=NodeStatus.COMPLETED,
            output={'started': True}
        )
```

**Step 2: Write end.py**

```python
"""End node executor."""

from typing import Any, Dict

from .base import BaseNodeExecutor
from ..state import ExecutionState, NodeResult, NodeStatus


class EndNodeExecutor(BaseNodeExecutor):
    """Executor for end nodes."""
    
    async def execute(self, node_config: Dict[str, Any], state: ExecutionState) -> NodeResult:
        """End node collects final output."""
        return NodeResult(
            status=NodeStatus.COMPLETED,
            output={'completed': True}
        )
```

**Step 3: Write llm.py**

```python
"""LLM node executor."""

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
        """Execute LLM call."""
        try:
            # Get configuration
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
```

**Step 4: Write condition.py**

```python
"""Condition node executor."""

from typing import Any, Dict

from .base import BaseNodeExecutor
from ..state import ExecutionState, NodeResult, NodeStatus


class ConditionNodeExecutor(BaseNodeExecutor):
    """Executor for condition nodes."""
    
    async def execute(self, node_config: Dict[str, Any], state: ExecutionState) -> NodeResult:
        """Evaluate condition and return branch."""
        try:
            condition = node_config.get('condition', '')
            
            # Simple expression evaluation (in production, use safer eval)
            # For now, support basic variable comparisons
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
        # Simple variable substitution and evaluation
        # In production, use a proper expression parser
        try:
            # Replace variable placeholders
            expr = condition
            for var_name, var_value in state.variables.items():
                placeholder = f"{{{{{var_name}}}}}"
                expr = expr.replace(placeholder, repr(var_value))
            
            # Evaluate (safe for simple conditions)
            return eval(expr, {"__builtins__": {}}, {})
        except:
            return False
```

**Step 5: Write variable_set.py**

```python
"""Variable set node executor."""

from typing import Any, Dict

from .base import BaseNodeExecutor
from ..state import ExecutionState, NodeResult, NodeStatus


class VariableSetNodeExecutor(BaseNodeExecutor):
    """Executor for variable set nodes."""
    
    async def execute(self, node_config: Dict[str, Any], state: ExecutionState) -> NodeResult:
        """Set variables in execution state."""
        try:
            variables = node_config.get('variables', {})
            
            for var_name, var_value in variables.items():
                # Resolve any variable references
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
```

**Step 6: Commit**

```bash
git add backend/open_webui/pm/services/workflow_engine/nodes/
git commit -m "feat(nodes): implement basic node executors (start, end, llm, condition, variable_set)"
```

---

## Phase 3: Agent Runtime

### Task 7: Implement Agent Runtime Core

**Files:**
- Create: `backend/open_webui/pm/services/agent_runtime/agent.py`
- Create: `backend/open_webui/pm/services/agent_runtime/memory.py`
- Create: `backend/open_webui/pm/services/agent_runtime/tools.py`

**Step 1: Write tools.py**

```python
"""Tool registry and execution."""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx


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


class HTTPTool(BaseTool):
    """HTTP API tool."""
    
    def __init__(self, name: str, description: str, url: str, method: str = 'GET'):
        super().__init__(name, description)
        self.url = url
        self.method = method
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute HTTP request."""
        try:
            async with httpx.AsyncClient() as client:
                if self.method.upper() == 'GET':
                    response = await client.get(self.url, params=kwargs)
                else:
                    response = await client.request(self.method, self.url, json=kwargs)
                
                response.raise_for_status()
                return ToolResult(success=True, output=response.json())
        
        except Exception as e:
            return ToolResult(success=False, error=str(e))


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
"""Memory management for agent."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID


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
                # Remove oldest
                self._memories = [
                    m for m in self._memories 
                    if m.memory_type != 'short_term' or m not in short_term[:-self.max_short_term]
                ]
    
    async def retrieve(self, query: str = None, limit: int = 10) -> List[Memory]:
        """Retrieve memories."""
        # For now, return most recent memories
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
                # Planning action - could trigger workflow execution
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

## Phase 4: FastAPI Routes

### Task 8: Create Workflow API Routes

**Files:**
- Create: `backend/open_webui/pm/api/v2/workflows.py`
- Create: `backend/open_webui/pm/api/v2/__init__.py`
- Modify: `backend/open_webui/main.py`

**Step 1: Write v2/workflows.py**

```python
"""V2 Workflow API routes."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from open_webui.pm.database import get_db
from open_webui.pm.models.v2_workflow import V2Workflow, V2WorkflowExecution
from open_webui.pm.schemas.v2_workflow import (
    WorkflowCreate,
    WorkflowResponse,
    WorkflowUpdate,
    WorkflowExecutionCreate,
    WorkflowExecutionResponse
)
from open_webui.pm.services.workflow_engine.engine import WorkflowEngine
from open_webui.pm.services.workflow_engine.state import ExecutionStatus

router = APIRouter(prefix="/workflows", tags=["workflows"])

# Initialize engine
workflow_engine = WorkflowEngine()


@router.post("", response_model=WorkflowResponse)
async def create_workflow(
    workflow: WorkflowCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new workflow."""
    db_workflow = V2Workflow(**workflow.model_dump())
    db.add(db_workflow)
    await db.commit()
    await db.refresh(db_workflow)
    return db_workflow


@router.get("", response_model=List[WorkflowResponse])
async def list_workflows(
    project_id: UUID = None,
    db: AsyncSession = Depends(get_db)
):
    """List workflows."""
    query = db.query(V2Workflow)
    if project_id:
        query = query.filter(V2Workflow.project_id == project_id)
    workflows = await query.all()
    return workflows


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific workflow."""
    workflow = await db.get(V2Workflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: UUID,
    workflow_update: WorkflowUpdate,
    db: AsyncSession = Depends(get_db)
):
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
async def delete_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a workflow."""
    workflow = await db.get(V2Workflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    await db.delete(workflow)
    await db.commit()
    return {"message": "Workflow deleted"}


@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    workflow_id: UUID,
    execution: WorkflowExecutionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Execute a workflow."""
    # Get workflow
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
    state = await workflow_engine.execute(
        workflow_id=workflow_id,
        nodes=workflow.nodes,
        edges=workflow.edges,
        input_data=execution.input_data
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
async def list_executions(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db)
):
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

# ... existing routes ...

# V2 API routes
app.include_router(v2_workflows.router, prefix="/api/v2", tags=["v2"])
```

**Step 3: Commit**

```bash
git add backend/open_webui/pm/api/v2/
git add backend/open_webui/main.py
git commit -m "feat(api): add v2 workflow CRUD and execution endpoints"
```

---

### Task 9: Create Agent API Routes

**Files:**
- Create: `backend/open_webui/pm/api/v2/agent.py`
- Modify: `backend/open_webui/main.py`

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
    AgentSessionCreate,
    AgentSessionResponse,
    AgentSessionUpdate,
    ChatRequest,
    ChatResponse
)
from open_webui.pm.services.agent_runtime.agent import AgentRuntime
from open_webui.pm.services.agent_runtime.memory import MemoryStore
from open_webui.pm.services.agent_runtime.tools import ToolRegistry

router = APIRouter(prefix="/agent", tags=["agent"])

# Initialize agent runtime
tool_registry = ToolRegistry()
memory_store = MemoryStore()


@router.post("/sessions", response_model=AgentSessionResponse)
async def create_session(
    session: AgentSessionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new agent session."""
    db_session = V2AgentSession(**session.model_dump())
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    return db_session


@router.get("/sessions/{session_id}", response_model=AgentSessionResponse)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get agent session."""
    session = await db.get(V2AgentSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/sessions/{session_id}/chat", response_model=ChatResponse)
async def chat(
    session_id: UUID,
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """Chat with agent."""
    # Get session
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
async def list_runs(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """List agent runs."""
    runs = await db.query(V2AgentRun).filter(
        V2AgentRun.session_id == session_id
    ).all()
    return runs


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete agent session."""
    session = await db.get(V2AgentSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    await db.delete(session)
    await db.commit()
    return {"message": "Session deleted"}
```

**Step 2: Update main.py**

```python
from open_webui.pm.api.v2 import agent as v2_agent

# Add to routes
app.include_router(v2_agent.router, prefix="/api/v2", tags=["v2"])
```

**Step 3: Commit**

```bash
git add backend/open_webui/pm/api/v2/agent.py
git add backend/open_webui/main.py
git commit -m "feat(api): add v2 agent session and chat endpoints"
```

---

## Phase 5: Frontend Components

### Task 10: Create Workflow Designer Components

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
        nodeConnect: { source: string; target: string };
    }>();
    
    let draggingNode: string | null = null;
    let dragOffset = { x: 0, y: 0 };
    let connectingFrom: string | null = null;
    let mousePos = { x: 0, y: 0 };
    
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
        mousePos = { x: event.clientX, y: event.clientY };
        
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
            'agent': '#673AB7'
        };
        return colors[type] || '#757575';
    }
</script>

<svg 
    class="workflow-canvas"
    on:mousemove={handleMouseMove}
    on:mouseup={handleMouseUp}
>
    <!-- Grid background -->
    <defs>
        <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
            <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#e0e0e0" stroke-width="0.5"/>
        </pattern>
    </defs>
    <rect width="100%" height="100%" fill="url(#grid)" />
    
    <!-- Edges -->
    {#each edges as edge}
        <path 
            d={getEdgePath(edge)}
            fill="none"
            stroke="#999"
            stroke-width="2"
            marker-end="url(#arrowhead)"
        />
    {/each}
    
    <!-- Nodes -->
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
            <text 
                x="50" 
                y="30" 
                text-anchor="middle" 
                fill="white"
                font-size="12"
                font-weight="bold"
            >
                {node.name}
            </text>
            <text 
                x="50" 
                y="50" 
                text-anchor="middle" 
                fill="white"
                font-size="10"
            >
                {node.type}
            </text>
        </g>
    {/each}
    
    <!-- Arrow marker -->
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

**Step 3: Write NodeSidebar.svelte**

```svelte
<!-- src/lib/components/workflow-v2/NodeSidebar.svelte -->
<script lang="ts">
    import { NODE_TYPES } from './types';
    
    function handleDragStart(event: DragEvent, nodeType: string) {
        event.dataTransfer?.setData('application/json', JSON.stringify({ type: nodeType }));
    }
    
    const categories = {
        control: 'Control Flow',
        ai: 'AI / LLM',
        data: 'Data',
        tools: 'Tools'
    };
    
    $: groupedNodes = NODE_TYPES.reduce((acc, node) => {
        if (!acc[node.category]) acc[node.category] = [];
        acc[node.category].push(node);
        return acc;
    }, {} as Record<string, typeof NODE_TYPES>);
</script>

<div class="node-sidebar">
    <h3 class="sidebar-title">Nodes</h3>
    
    {#each Object.entries(groupedNodes) as [category, nodes]}
        <div class="category">
            <h4 class="category-title">{categories[category] || category}</h4>
            <div class="node-list">
                {#each nodes as node}
                    <div 
                        class="node-item"
                        draggable="true"
                        on:dragstart={(e) => handleDragStart(e, node.type)}
                    >
                        <div class="node-color" style="background-color: {node.color}"></div>
                        <span class="node-label">{node.label}</span>
                    </div>
                {/each}
            </div>
        </div>
    {/each}
</div>

<style>
    .node-sidebar {
        width: 200px;
        background: #f5f5f5;
        border-right: 1px solid #ddd;
        padding: 16px;
        overflow-y: auto;
    }
    
    .sidebar-title {
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 16px;
    }
    
    .category {
        margin-bottom: 20px;
    }
    
    .category-title {
        font-size: 12px;
        text-transform: uppercase;
        color: #666;
        margin-bottom: 8px;
    }
    
    .node-list {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    
    .node-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px;
        border-radius: 4px;
        cursor: grab;
        transition: background-color 0.2s;
    }
    
    .node-item:hover {
        background-color: #e0e0e0;
    }
    
    .node-color {
        width: 12px;
        height: 12px;
        border-radius: 2px;
    }
    
    .node-label {
        font-size: 14px;
    }
</style>
```

**Step 4: Write PropertyPanel.svelte**

```svelte
<!-- src/lib/components/workflow-v2/PropertyPanel.svelte -->
<script lang="ts">
    import type { WorkflowNode } from './types';
    
    export let node: WorkflowNode | null = null;
    
    $: configKeys = node ? Object.keys(node.config || {}) : [];
</script>

<div class="property-panel">
    {#if node}
        <h3 class="panel-title">Properties</h3>
        
        <div class="property-group">
            <label class="property-label">Name</label>
            <input 
                type="text" 
                class="property-input"
                value={node.name}
                readonly
            />
        </div>
        
        <div class="property-group">
            <label class="property-label">Type</label>
            <input 
                type="text" 
                class="property-input"
                value={node.type}
                readonly
            />
        </div>
        
        <div class="property-group">
            <label class="property-label">ID</label>
            <input 
                type="text" 
                class="property-input"
                value={node.id}
                readonly
            />
        </div>
        
        {#if configKeys.length > 0}
            <div class="property-group">
                <label class="property-label">Configuration</label>
                {#each configKeys as key}
                    <div class="config-item">
                        <span class="config-key">{key}:</span>
                        <span class="config-value">{JSON.stringify(node.config[key])}</span>
                    </div>
                {/each}
            </div>
        {/if}
    {:else}
        <p class="empty-state">Select a node to view properties</p>
    {/if}
</div>

<style>
    .property-panel {
        width: 250px;
        background: #f5f5f5;
        border-left: 1px solid #ddd;
        padding: 16px;
        overflow-y: auto;
    }
    
    .panel-title {
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 16px;
    }
    
    .property-group {
        margin-bottom: 16px;
    }
    
    .property-label {
        display: block;
        font-size: 12px;
        text-transform: uppercase;
        color: #666;
        margin-bottom: 4px;
    }
    
    .property-input {
        width: 100%;
        padding: 8px;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-size: 14px;
    }
    
    .config-item {
        display: flex;
        justify-content: space-between;
        padding: 4px 0;
        font-size: 12px;
    }
    
    .config-key {
        font-weight: bold;
        color: #333;
    }
    
    .config-value {
        color: #666;
        word-break: break-all;
    }
    
    .empty-state {
        color: #999;
        text-align: center;
        margin-top: 20px;
    }
</style>
```

**Step 5: Write WorkflowDesigner.svelte**

```svelte
<!-- src/lib/components/workflow-v2/WorkflowDesigner.svelte -->
<script lang="ts">
    import { writable } from 'svelte/store';
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
            workflow = workflow; // Trigger reactivity
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

**Step 6: Commit**

```bash
git add src/lib/components/workflow-v2/
git commit -m "feat(ui): add workflow designer components (Canvas, Sidebar, PropertyPanel)"
```

---

## Phase 6: Integration & Testing

### Task 11: Integrate Workflow Designer Page

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
    
    // TODO: Load workflow from API
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
git commit -m "feat(ui): integrate workflow designer into app routes"
```

---

### Task 12: Add Tests

**Files:**
- Create: `backend/tests/services/test_workflow_engine.py`
- Create: `backend/tests/services/test_agent_runtime.py`

**Step 1: Write workflow engine tests**

```python
"""Tests for workflow execution engine."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from open_webui.pm.services.workflow_engine.engine import WorkflowEngine
from open_webui.pm.services.workflow_engine.state import ExecutionStatus, NodeStatus
from open_webui.pm.services.workflow_engine.nodes.base import BaseNodeExecutor


class MockNodeExecutor(BaseNodeExecutor):
    """Mock executor for testing."""
    
    async def execute(self, node_config, state):
        return MagicMock(
            status=NodeStatus.COMPLETED,
            output={'result': 'success'}
        )


class TestWorkflowEngine:
    """Test cases for workflow engine."""
    
    @pytest.fixture
    def engine(self):
        """Create workflow engine with mock executors."""
        engine = WorkflowEngine()
        engine.register_node_executor('start', MockNodeExecutor())
        engine.register_node_executor('process', MockNodeExecutor())
        engine.register_node_executor('end', MockNodeExecutor())
        return engine
    
    @pytest.mark.asyncio
    async def test_execute_linear_workflow(self, engine):
        """Test executing a linear workflow."""
        nodes = [
            {'id': 'start', 'type': 'start', 'config': {}},
            {'id': 'process', 'type': 'process', 'config': {}},
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
    
    @pytest.mark.asyncio
    async def test_execute_with_input_data(self, engine):
        """Test executing workflow with input data."""
        nodes = [
            {'id': 'start', 'type': 'start', 'config': {}},
            {'id': 'process', 'type': 'process', 'config': {}}
        ]
        
        edges = [
            {'id': 'e1', 'source': 'start', 'target': 'process'}
        ]
        
        input_data = {'name': 'Test', 'value': 42}
        
        state = await engine.execute(
            workflow_id='test-workflow',
            nodes=nodes,
            edges=edges,
            input_data=input_data
        )
        
        assert state.status == ExecutionStatus.COMPLETED
        assert state.get_variable('name') == 'Test'
        assert state.get_variable('value') == 42
```

**Step 2: Commit**

```bash
git add backend/tests/services/test_workflow_engine.py
git add backend/tests/services/test_agent_runtime.py
git commit -m "test: add workflow engine and agent runtime tests"
```

---

## Summary

This implementation plan covers:

1. **Database Layer**: Alembic migration, SQLAlchemy models, Pydantic schemas
2. **Workflow Engine**: DAG parser, topological sort, execution engine, node executors
3. **Agent Runtime**: ReAct pattern, memory store, tool registry
4. **API Layer**: FastAPI routes for workflow CRUD, execution, agent sessions
5. **Frontend**: Svelte 5 components for visual workflow designer
6. **Integration**: Page routes, component integration
7. **Testing**: Unit tests for engine and runtime

**Estimated Timeline**: 4-5 weeks (based on 2-week sprints)

**Next Steps**:
1. Execute tasks in order
2. Test each phase before moving to next
3. Iterate based on feedback
