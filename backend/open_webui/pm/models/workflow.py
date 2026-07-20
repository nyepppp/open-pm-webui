"""Workflow models for PM workspace workflow designer."""

import logging
import time
import uuid
from typing import Optional

from open_webui.internal.db import Base, get_async_db_context
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import BigInteger, Column, Float, ForeignKey, Text, select
from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger(__name__)


class Workflow(Base):
    """Represents a visual workflow definition."""

    __tablename__ = "pm_workflows"

    id = Column(Text, primary_key=True, unique=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    project_id = Column(Text, nullable=True)
    status = Column(Text, default="draft")  # draft / active / archived
    nodes = Column(Text, default="[]")  # JSON string
    edges = Column(Text, default="[]")  # JSON string
    execution_history = Column(Text, default="[]")  # JSON string
    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)


class WorkflowNode(Base):
    """Represents a single step in a workflow."""

    __tablename__ = "pm_workflow_nodes"

    id = Column(Text, primary_key=True, unique=True)
    workflow_id = Column(Text, nullable=False)
    type = Column(Text, nullable=False)  # start/end/agent_call/data_transform/condition/loop/parallel_merge/custom
    name = Column(Text, nullable=False)
    position_x = Column(Float, default=0.0)
    position_y = Column(Float, default=0.0)
    config = Column(Text, default="{}")  # JSON string
    input_schema = Column(Text, nullable=True)  # JSON string
    output_schema = Column(Text, nullable=True)  # JSON string
    script = Column(Text, nullable=True)
    skill_id = Column(Text, nullable=True)
    created_at = Column(BigInteger)


class WorkflowEdge(Base):
    """Represents data flow between nodes."""

    __tablename__ = "pm_workflow_edges"

    id = Column(Text, primary_key=True, unique=True)
    workflow_id = Column(Text, nullable=False)
    source_node_id = Column(Text, nullable=False)
    target_node_id = Column(Text, nullable=False)
    data_mapping_rules = Column(Text, default="{}")  # JSON string
    label = Column(Text, nullable=True)
    created_at = Column(BigInteger)


class WorkflowExecution(Base):
    """Represents a single workflow run."""

    __tablename__ = "pm_workflow_executions"

    id = Column(Text, primary_key=True, unique=True)
    workflow_id = Column(Text, nullable=False)
    status = Column(Text, default="pending")  # pending/running/completed/failed/cancelled
    input_data = Column(Text, default="{}")  # JSON string
    output_data = Column(Text, default="{}")  # JSON string
    node_states = Column(Text, default="[]")  # JSON string
    logs = Column(Text, default="[]")  # JSON string
    started_at = Column(BigInteger)
    completed_at = Column(BigInteger, nullable=True)
    error_message = Column(Text, nullable=True)


# Pydantic Models

class WorkflowModel(BaseModel):
    """Pydantic model for Workflow."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    project_id: Optional[str] = None
    status: str = "draft"
    nodes: str = "[]"
    edges: str = "[]"
    execution_history: str = "[]"
    created_at: Optional[int] = None
    updated_at: Optional[int] = None


class WorkflowNodeModel(BaseModel):
    """Pydantic model for WorkflowNode."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    workflow_id: str
    type: str
    name: str
    position_x: float = 0.0
    position_y: float = 0.0
    config: str = "{}"
    input_schema: Optional[str] = None
    output_schema: Optional[str] = None
    script: Optional[str] = None
    skill_id: Optional[str] = None
    created_at: int


class WorkflowEdgeModel(BaseModel):
    """Pydantic model for WorkflowEdge."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    workflow_id: str
    source_node_id: str
    target_node_id: str
    data_mapping_rules: str = "{}"
    label: Optional[str] = None
    created_at: int


class WorkflowExecutionModel(BaseModel):
    """Pydantic model for WorkflowExecution."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    workflow_id: str
    status: str = "pending"
    input_data: str = "{}"
    output_data: str = "{}"
    node_states: str = "[]"
    logs: str = "[]"
    started_at: int
    completed_at: Optional[int] = None
    error_message: Optional[str] = None


class WorkflowForm(BaseModel):
    """Form for creating/updating Workflow."""

    name: str
    description: Optional[str] = None
    project_id: Optional[str] = None
    project_ids: Optional[list[str]] = None
    status: str = "draft"
    nodes: str = "[]"
    edges: str = "[]"


class WorkflowNodeForm(BaseModel):
    """Form for creating/updating WorkflowNode."""

    workflow_id: str
    type: str
    name: str
    position_x: float = 0.0
    position_y: float = 0.0
    config: str = "{}"
    input_schema: Optional[str] = None
    output_schema: Optional[str] = None
    script: Optional[str] = None
    skill_id: Optional[str] = None


class WorkflowEdgeForm(BaseModel):
    """Form for creating/updating WorkflowEdge."""

    workflow_id: str
    source_node_id: str
    target_node_id: str
    data_mapping_rules: str = "{}"
    label: Optional[str] = None


class WorkflowExecutionForm(BaseModel):
    """Form for creating/updating WorkflowExecution."""

    workflow_id: str
    status: str = "pending"
    input_data: str = "{}"
    output_data: str = "{}"
    node_states: str = "[]"
    logs: str = "[]"
    error_message: Optional[str] = None


# CRUD Operations

class Workflows:
    """CRUD operations for Workflow."""

    async def insert_new_workflow(
        self, form_data: WorkflowForm, db: Optional[AsyncSession] = None
    ) -> Optional[WorkflowModel]:
        """Create a new workflow."""
        async with get_async_db_context(db) as db:
            # Handle project_ids -> project_id mapping
            project_id = form_data.project_id
            if not project_id and form_data.project_ids:
                project_id = form_data.project_ids[0] if form_data.project_ids else None

            workflow_id = str(uuid.uuid4())
            workflow = Workflow(
                id=workflow_id,
                name=form_data.name,
                description=form_data.description,
                project_id=project_id,
                status=form_data.status,
                nodes=form_data.nodes,
                edges=form_data.edges,
                execution_history="[]",
                created_at=int(time.time_ns()),
                updated_at=int(time.time_ns()),
            )
            try:
                db.add(workflow)
                await db.commit()
            except Exception as e:
                await db.rollback()
                log.error(
                    "insert_new_workflow failed: workflow_id=%s name=%r project_id=%s error=%s",
                    workflow_id,
                    form_data.name,
                    project_id,
                    e,
                    exc_info=True,
                )
                raise
            log.info(
                "insert_new_workflow ok: workflow_id=%s name=%r project_id=%s",
                workflow_id,
                form_data.name,
                project_id,
            )
            return WorkflowModel.model_validate(workflow)

    async def get_workflow_by_id(
        self, workflow_id: str, db: Optional[AsyncSession] = None
    ) -> Optional[WorkflowModel]:
        """Get workflow by ID."""
        async with get_async_db_context(db) as db:
            try:
                result = await db.execute(
                    select(Workflow).where(Workflow.id == workflow_id)
                )
                workflow = result.scalar_one_or_none()
            except Exception as e:
                log.error(
                    "get_workflow_by_id query failed: workflow_id=%s error=%s",
                    workflow_id,
                    e,
                    exc_info=True,
                )
                raise
            if workflow is None:
                log.warning(
                    "get_workflow_by_id returned None: workflow_id=%s (row not found "
                    "in pm_workflows — check that migration a7b8c9d0e1f2 has been applied)",
                    workflow_id,
                )
                return None
            # 防御性补全：旧数据可能时间戳为 NULL（SQLAlchemy 列默认 nullable=True）
            if workflow.created_at is None:
                workflow.created_at = int(time.time())
            if workflow.updated_at is None:
                workflow.updated_at = workflow.created_at
            return WorkflowModel.model_validate(workflow)

    async def get_workflows_by_project(
        self, project_id: str, db: Optional[AsyncSession] = None
    ) -> list[WorkflowModel]:
        """Get all workflows for a project."""
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(Workflow).where(Workflow.project_id == project_id)
            )
            return [
                WorkflowModel.model_validate(w)
                for w in result.scalars().all()
            ]

    async def get_all_workflows(
        self, db: Optional[AsyncSession] = None
    ) -> list[WorkflowModel]:
        """Get all workflows."""
        async with get_async_db_context(db) as db:
            result = await db.execute(select(Workflow))
            return [
                WorkflowModel.model_validate(w)
                for w in result.scalars().all()
            ]

    async def update_workflow_by_id(
        self,
        workflow_id: str,
        form_data: WorkflowForm,
        db: Optional[AsyncSession] = None,
    ) -> Optional[WorkflowModel]:
        """Update a workflow."""
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(Workflow).where(Workflow.id == workflow_id)
            )
            workflow = result.scalar_one_or_none()
            if not workflow:
                return None
            workflow.name = form_data.name
            workflow.description = form_data.description
            workflow.status = form_data.status
            workflow.nodes = form_data.nodes
            workflow.edges = form_data.edges
            workflow.updated_at = int(time.time_ns())
            await db.commit()
            return WorkflowModel.model_validate(workflow)

    async def delete_workflow_by_id(
        self, workflow_id: str, db: Optional[AsyncSession] = None
    ) -> bool:
        """Delete a workflow."""
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(Workflow).where(Workflow.id == workflow_id)
            )
            workflow = result.scalar_one_or_none()
            if workflow:
                await db.delete(workflow)
                await db.commit()
            return True


class WorkflowNodes:
    """CRUD operations for WorkflowNode."""

    async def insert_new_node(
        self, form_data: WorkflowNodeForm, db: Optional[AsyncSession] = None
    ) -> Optional[WorkflowNodeModel]:
        """Create a new workflow node."""
        async with get_async_db_context(db) as db:
            node = WorkflowNode(
                id=str(uuid.uuid4()),
                workflow_id=form_data.workflow_id,
                type=form_data.type,
                name=form_data.name,
                position_x=form_data.position_x,
                position_y=form_data.position_y,
                config=form_data.config,
                input_schema=form_data.input_schema,
                output_schema=form_data.output_schema,
                script=form_data.script,
                skill_id=form_data.skill_id,
                created_at=int(time.time_ns()),
            )
            db.add(node)
            await db.commit()
            return WorkflowNodeModel.model_validate(node)

    async def get_node_by_id(
        self, node_id: str, db: Optional[AsyncSession] = None
    ) -> Optional[WorkflowNodeModel]:
        """Get node by ID."""
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(WorkflowNode).where(WorkflowNode.id == node_id)
            )
            node = result.scalar_one_or_none()
            return WorkflowNodeModel.model_validate(node) if node else None

    async def get_nodes_by_workflow(
        self, workflow_id: str, db: Optional[AsyncSession] = None
    ) -> list[WorkflowNodeModel]:
        """Get all nodes for a workflow."""
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(WorkflowNode).where(WorkflowNode.workflow_id == workflow_id)
            )
            return [
                WorkflowNodeModel.model_validate(n)
                for n in result.scalars().all()
            ]

    async def delete_node_by_id(
        self, node_id: str, db: Optional[AsyncSession] = None
    ) -> bool:
        """Delete a node."""
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(WorkflowNode).where(WorkflowNode.id == node_id)
            )
            node = result.scalar_one_or_none()
            if node:
                await db.delete(node)
                await db.commit()
            return True


class WorkflowEdges:
    """CRUD operations for WorkflowEdge."""

    async def insert_new_edge(
        self, form_data: WorkflowEdgeForm, db: Optional[AsyncSession] = None
    ) -> Optional[WorkflowEdgeModel]:
        """Create a new workflow edge."""
        async with get_async_db_context(db) as db:
            edge = WorkflowEdge(
                id=str(uuid.uuid4()),
                workflow_id=form_data.workflow_id,
                source_node_id=form_data.source_node_id,
                target_node_id=form_data.target_node_id,
                data_mapping_rules=form_data.data_mapping_rules,
                label=form_data.label,
                created_at=int(time.time_ns()),
            )
            db.add(edge)
            await db.commit()
            return WorkflowEdgeModel.model_validate(edge)

    async def get_edge_by_id(
        self, edge_id: str, db: Optional[AsyncSession] = None
    ) -> Optional[WorkflowEdgeModel]:
        """Get edge by ID."""
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(WorkflowEdge).where(WorkflowEdge.id == edge_id)
            )
            edge = result.scalar_one_or_none()
            return WorkflowEdgeModel.model_validate(edge) if edge else None

    async def get_edges_by_workflow(
        self, workflow_id: str, db: Optional[AsyncSession] = None
    ) -> list[WorkflowEdgeModel]:
        """Get all edges for a workflow."""
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(WorkflowEdge).where(WorkflowEdge.workflow_id == workflow_id)
            )
            return [
                WorkflowEdgeModel.model_validate(e)
                for e in result.scalars().all()
            ]

    async def delete_edge_by_id(
        self, edge_id: str, db: Optional[AsyncSession] = None
    ) -> bool:
        """Delete an edge."""
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(WorkflowEdge).where(WorkflowEdge.id == edge_id)
            )
            edge = result.scalar_one_or_none()
            if edge:
                await db.delete(edge)
                await db.commit()
            return True


class WorkflowExecutions:
    """CRUD operations for WorkflowExecution."""

    async def insert_new_execution(
        self, form_data: WorkflowExecutionForm, db: Optional[AsyncSession] = None
    ) -> Optional[WorkflowExecutionModel]:
        """Create a new workflow execution."""
        async with get_async_db_context(db) as db:
            execution = WorkflowExecution(
                id=str(uuid.uuid4()),
                workflow_id=form_data.workflow_id,
                status=form_data.status,
                input_data=form_data.input_data,
                output_data=form_data.output_data,
                node_states=form_data.node_states,
                logs=form_data.logs,
                started_at=int(time.time_ns()),
                completed_at=None,
                error_message=form_data.error_message,
            )
            db.add(execution)
            await db.commit()
            return WorkflowExecutionModel.model_validate(execution)

    async def get_execution_by_id(
        self, execution_id: str, db: Optional[AsyncSession] = None
    ) -> Optional[WorkflowExecutionModel]:
        """Get execution by ID."""
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
            )
            execution = result.scalar_one_or_none()
            return WorkflowExecutionModel.model_validate(execution) if execution else None

    async def get_executions_by_workflow(
        self, workflow_id: str, db: Optional[AsyncSession] = None
    ) -> list[WorkflowExecutionModel]:
        """Get all executions for a workflow."""
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(WorkflowExecution).where(WorkflowExecution.workflow_id == workflow_id)
            )
            return [
                WorkflowExecutionModel.model_validate(e)
                for e in result.scalars().all()
            ]

    async def update_execution_status(
        self,
        execution_id: str,
        status: str,
        output_data: Optional[str] = None,
        error_message: Optional[str] = None,
        db: Optional[AsyncSession] = None,
    ) -> Optional[WorkflowExecutionModel]:
        """Update execution status."""
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
            )
            execution = result.scalar_one_or_none()
            if not execution:
                return None
            execution.status = status
            if output_data:
                execution.output_data = output_data
            if error_message:
                execution.error_message = error_message
            if status in ["completed", "failed", "cancelled"]:
                execution.completed_at = int(time.time_ns())
            await db.commit()
            return WorkflowExecutionModel.model_validate(execution)


# Singleton instances
Workflows = Workflows()
WorkflowNodes = WorkflowNodes()
WorkflowEdges = WorkflowEdges()
WorkflowExecutions = WorkflowExecutions()
