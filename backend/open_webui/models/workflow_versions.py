"""
Workflow Versioning and Template System

Provides workflow versioning and template management.
"""

import time
import uuid
from datetime import datetime
from typing import List, Optional

from open_webui.internal.db import Base, get_async_db_context
from pydantic import BaseModel, ConfigDict
from sqlalchemy import JSON, BigInteger, Column, Text, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession


####################
# Workflow Version DB Schema
####################

class WorkflowVersion(Base):
    __tablename__ = 'workflow_version'

    id = Column(Text, primary_key=True, unique=True)
    workflow_id = Column(Text, nullable=False)
    version_number = Column(BigInteger, nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    nodes = Column(JSON, nullable=False)
    edges = Column(JSON, nullable=False)
    created_by = Column(Text, nullable=True)
    created_at = Column(BigInteger)
    is_active = Column(BigInteger, default=0)  # 0 = inactive, 1 = active


class WorkflowVersionModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workflow_id: str
    version_number: int
    name: str
    description: Optional[str] = None
    nodes: list
    edges: list
    created_by: Optional[str] = None
    created_at: int
    is_active: int = 0


class WorkflowVersionForm(BaseModel):
    workflow_id: str
    version_number: int
    name: str
    description: Optional[str] = None
    nodes: list
    edges: list


class WorkflowVersions:
    async def create_version(
        self, user_id: str, form_data: WorkflowVersionForm, db: Optional[AsyncSession] = None
    ) -> Optional[WorkflowVersionModel]:
        async with get_async_db_context(db) as db:
            version = WorkflowVersion(
                id=str(uuid.uuid4()),
                workflow_id=form_data.workflow_id,
                version_number=form_data.version_number,
                name=form_data.name,
                description=form_data.description,
                nodes=form_data.nodes,
                edges=form_data.edges,
                created_by=user_id,
                created_at=int(time.time_ns()),
                is_active=0,
            )
            db.add(version)
            await db.commit()
            return WorkflowVersionModel.model_validate(version)

    async def get_versions_by_workflow_id(
        self, workflow_id: str, db: Optional[AsyncSession] = None
    ) -> List[WorkflowVersionModel]:
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(WorkflowVersion)
                .where(WorkflowVersion.workflow_id == workflow_id)
                .order_by(WorkflowVersion.version_number.desc())
            )
            return [WorkflowVersionModel.model_validate(v) for v in result.scalars().all()]

    async def get_version_by_id(
        self, version_id: str, db: Optional[AsyncSession] = None
    ) -> Optional[WorkflowVersionModel]:
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(WorkflowVersion).where(WorkflowVersion.id == version_id)
            )
            version = result.scalar_one_or_none()
            return WorkflowVersionModel.model_validate(version) if version else None

    async def set_active_version(
        self, version_id: str, db: Optional[AsyncSession] = None
    ) -> bool:
        async with get_async_db_context(db) as db:
            # First, deactivate all versions for this workflow
            version = await db.execute(
                select(WorkflowVersion).where(WorkflowVersion.id == version_id)
            )
            version = version.scalar_one_or_none()
            if not version:
                return False

            # Deactivate all versions for this workflow
            await db.execute(
                update(WorkflowVersion)
                .where(WorkflowVersion.workflow_id == version.workflow_id)
                .values(is_active=0)
            )

            # Activate the specified version
            await db.execute(
                update(WorkflowVersion)
                .where(WorkflowVersion.id == version_id)
                .values(is_active=1)
            )

            await db.commit()
            return True


####################
# Workflow Template DB Schema
####################

class WorkflowTemplate(Base):
    __tablename__ = 'workflow_template'

    id = Column(Text, primary_key=True, unique=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    workflow_definition = Column(JSON, nullable=False)
    category = Column(Text, nullable=False)
    usage_count = Column(BigInteger, default=0)
    rating = Column(BigInteger, default=0)
    created_by = Column(Text, nullable=True)
    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)


class WorkflowTemplateModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    workflow_definition: dict
    category: str
    usage_count: int = 0
    rating: int = 0
    created_by: Optional[str] = None
    created_at: int
    updated_at: int


class WorkflowTemplateForm(BaseModel):
    name: str
    description: Optional[str] = None
    workflow_definition: dict
    category: str


class WorkflowTemplates:
    async def create_template(
        self, user_id: str, form_data: WorkflowTemplateForm, db: Optional[AsyncSession] = None
    ) -> Optional[WorkflowTemplateModel]:
        async with get_async_db_context(db) as db:
            template = WorkflowTemplate(
                id=str(uuid.uuid4()),
                name=form_data.name,
                description=form_data.description,
                workflow_definition=form_data.workflow_definition,
                category=form_data.category,
                usage_count=0,
                rating=0,
                created_by=user_id,
                created_at=int(time.time_ns()),
                updated_at=int(time.time_ns()),
            )
            db.add(template)
            await db.commit()
            return WorkflowTemplateModel.model_validate(template)

    async def get_templates(
        self, category: Optional[str] = None, db: Optional[AsyncSession] = None
    ) -> List[WorkflowTemplateModel]:
        async with get_async_db_context(db) as db:
            query = select(WorkflowTemplate)
            if category:
                query = query.where(WorkflowTemplate.category == category)
            result = await db.execute(query.order_by(WorkflowTemplate.usage_count.desc()))
            return [WorkflowTemplateModel.model_validate(t) for t in result.scalars().all()]

    async def get_template_by_id(
        self, template_id: str, db: Optional[AsyncSession] = None
    ) -> Optional[WorkflowTemplateModel]:
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(WorkflowTemplate).where(WorkflowTemplate.id == template_id)
            )
            template = result.scalar_one_or_none()
            return WorkflowTemplateModel.model_validate(template) if template else None

    async def increment_usage_count(
        self, template_id: str, db: Optional[AsyncSession] = None
    ) -> bool:
        async with get_async_db_context(db) as db:
            template = await db.execute(
                select(WorkflowTemplate).where(WorkflowTemplate.id == template_id)
            )
            template = template.scalar_one_or_none()
            if not template:
                return False

            template.usage_count += 1
            await db.commit()
            return True

    async def update_rating(
        self, template_id: str, rating: int, db: Optional[AsyncSession] = None
    ) -> bool:
        async with get_async_db_context(db) as db:
            template = await db.execute(
                select(WorkflowTemplate).where(WorkflowTemplate.id == template_id)
            )
            template = template.scalar_one_or_none()
            if not template:
                return False

            # Simple average calculation
            current_rating = template.rating
            current_count = template.usage_count
            new_rating = ((current_rating * current_count) + rating) / (current_count + 1)

            template.rating = int(new_rating)
            await db.commit()
            return True


# Singleton instances
WorkflowVersions = WorkflowVersions()
WorkflowTemplates = WorkflowTemplates()
