import time
import uuid
from typing import Optional

from open_webui.internal.db import Base, get_async_db_context
from pydantic import BaseModel, ConfigDict
from sqlalchemy import JSON, BigInteger, Column, Text, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession


####################
# PM Project DB Schema
####################


class PMProject(Base):
    __tablename__ = 'pm_project'

    id = Column(Text, primary_key=True, unique=True)
    user_id = Column(Text)
    name = Column(Text)
    description = Column(Text, nullable=True)
    status = Column(Text, default='active')
    meta = Column(JSON, nullable=True)
    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)


class PMVersion(Base):
    __tablename__ = 'pm_version'

    id = Column(Text, primary_key=True, unique=True)
    project_id = Column(Text)
    version_number = Column(Text)
    label = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    created_by = Column(Text, nullable=True)
    created_at = Column(BigInteger)


####################
# PM Entry DB Schema
####################


class PMEntry(Base):
    __tablename__ = 'pm_entry'

    id = Column(Text, primary_key=True, unique=True)
    user_id = Column(Text)
    project_id = Column(Text)
    module_type = Column(Text)
    title = Column(Text)
    content = Column(Text, nullable=True)
    data = Column(JSON, nullable=True)
    status = Column(Text, default='draft')
    priority = Column(Text, nullable=True)
    version = Column(BigInteger, default=1)
    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)


####################
# Pydantic Models
####################


class PMProjectModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    status: str = 'active'
    meta: Optional[dict] = None
    created_at: int
    updated_at: int


class PMProjectForm(BaseModel):
    name: str
    description: Optional[str] = None
    meta: Optional[dict] = None


class PMProjectUpdateForm(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    meta: Optional[dict] = None


class PMVersionModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    version_number: str
    label: Optional[str] = None
    description: Optional[str] = None
    created_by: Optional[str] = None
    created_at: int


class PMVersionForm(BaseModel):
    project_id: str
    version_number: str
    label: Optional[str] = None
    description: Optional[str] = None


class PMEntryModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    project_id: str
    module_type: str
    title: str
    content: Optional[str] = None
    data: Optional[dict] = None
    status: str = 'draft'
    priority: Optional[str] = None
    version: int = 1
    created_at: int
    updated_at: int


class PMEntryForm(BaseModel):
    project_id: str
    module_type: str
    title: str
    content: Optional[str] = None
    data: Optional[dict] = None
    status: Optional[str] = 'draft'
    priority: Optional[str] = None


class PMEntryUpdateForm(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    data: Optional[dict] = None
    status: Optional[str] = None
    priority: Optional[str] = None


####################
# Table Classes
####################


class PMProjects:
    async def insert_new_project(
        self, user_id: str, form_data: PMProjectForm, db: Optional[AsyncSession] = None
    ) -> Optional[PMProjectModel]:
        async with get_async_db_context(db) as db:
            project = PMProject(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=form_data.name,
                description=form_data.description,
                status='active',
                meta=form_data.meta,
                created_at=int(time.time_ns()),
                updated_at=int(time.time_ns()),
            )
            db.add(project)
            await db.commit()
            return PMProjectModel.model_validate(project)

    async def get_project_by_id(
        self, project_id: str, db: Optional[AsyncSession] = None
    ) -> Optional[PMProjectModel]:
        async with get_async_db_context(db) as db:
            result = await db.execute(select(PMProject).where(PMProject.id == project_id))
            project = result.scalar_one_or_none()
            return PMProjectModel.model_validate(project) if project else None

    async def get_projects_by_user_id(
        self, user_id: str, db: Optional[AsyncSession] = None
    ) -> list[PMProjectModel]:
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(PMProject)
                .where(PMProject.user_id == user_id)
                .order_by(PMProject.updated_at.desc())
            )
            return [PMProjectModel.model_validate(p) for p in result.scalars().all()]

    async def update_project_by_id(
        self, project_id: str, form_data: PMProjectUpdateForm, db: Optional[AsyncSession] = None
    ) -> Optional[PMProjectModel]:
        async with get_async_db_context(db) as db:
            result = await db.execute(select(PMProject).where(PMProject.id == project_id))
            project = result.scalar_one_or_none()
            if not project:
                return None
            update_data = form_data.model_dump(exclude_none=True)
            if update_data:
                update_data['updated_at'] = int(time.time_ns())
                await db.execute(
                    update(PMProject).where(PMProject.id == project_id).values(**update_data)
                )
                await db.commit()
            result = await db.execute(select(PMProject).where(PMProject.id == project_id))
            project = result.scalar_one_or_none()
            return PMProjectModel.model_validate(project) if project else None

    async def delete_project_by_id(
        self, project_id: str, db: Optional[AsyncSession] = None
    ) -> bool:
        async with get_async_db_context(db) as db:
            await db.execute(delete(PMProject).where(PMProject.id == project_id))
            await db.commit()
            return True


class PMVersions:
    async def insert_new_version(
        self, form_data: PMVersionForm, user_id: str, db: Optional[AsyncSession] = None
    ) -> Optional[PMVersionModel]:
        async with get_async_db_context(db) as db:
            version = PMVersion(
                id=str(uuid.uuid4()),
                project_id=form_data.project_id,
                version_number=form_data.version_number,
                label=form_data.label,
                description=form_data.description,
                created_by=user_id,
                created_at=int(time.time_ns()),
            )
            db.add(version)
            await db.commit()
            return PMVersionModel.model_validate(version)

    async def get_versions_by_project_id(
        self, project_id: str, db: Optional[AsyncSession] = None
    ) -> list[PMVersionModel]:
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(PMVersion)
                .where(PMVersion.project_id == project_id)
                .order_by(PMVersion.created_at.desc())
            )
            return [PMVersionModel.model_validate(v) for v in result.scalars().all()]


class PMEntries:
    async def insert_new_entry(
        self, user_id: str, form_data: PMEntryForm, db: Optional[AsyncSession] = None
    ) -> Optional[PMEntryModel]:
        async with get_async_db_context(db) as db:
            entry = PMEntry(
                id=str(uuid.uuid4()),
                user_id=user_id,
                project_id=form_data.project_id,
                module_type=form_data.module_type,
                title=form_data.title,
                content=form_data.content,
                data=form_data.data,
                status=form_data.status or 'draft',
                priority=form_data.priority,
                version=1,
                created_at=int(time.time_ns()),
                updated_at=int(time.time_ns()),
            )
            db.add(entry)
            await db.commit()
            return PMEntryModel.model_validate(entry)

    async def get_entry_by_id(
        self, entry_id: str, db: Optional[AsyncSession] = None
    ) -> Optional[PMEntryModel]:
        async with get_async_db_context(db) as db:
            result = await db.execute(select(PMEntry).where(PMEntry.id == entry_id))
            entry = result.scalar_one_or_none()
            return PMEntryModel.model_validate(entry) if entry else None

    async def get_entries_by_project_and_module(
        self, project_id: str, module_type: str, db: Optional[AsyncSession] = None
    ) -> list[PMEntryModel]:
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(PMEntry)
                .where(PMEntry.project_id == project_id, PMEntry.module_type == module_type)
                .order_by(PMEntry.updated_at.desc())
            )
            return [PMEntryModel.model_validate(e) for e in result.scalars().all()]

    async def get_entries_by_project_id(
        self, project_id: str, db: Optional[AsyncSession] = None
    ) -> list[PMEntryModel]:
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(PMEntry)
                .where(PMEntry.project_id == project_id)
                .order_by(PMEntry.updated_at.desc())
            )
            return [PMEntryModel.model_validate(e) for e in result.scalars().all()]

    async def update_entry_by_id(
        self, entry_id: str, form_data: PMEntryUpdateForm, db: Optional[AsyncSession] = None
    ) -> Optional[PMEntryModel]:
        async with get_async_db_context(db) as db:
            result = await db.execute(select(PMEntry).where(PMEntry.id == entry_id))
            entry = result.scalar_one_or_none()
            if not entry:
                return None
            update_data = form_data.model_dump(exclude_none=True)
            if update_data:
                update_data['updated_at'] = int(time.time_ns())
                # Optimistic lock: increment version
                update_data['version'] = entry.version + 1
                await db.execute(
                    update(PMEntry).where(PMEntry.id == entry_id).values(**update_data)
                )
                await db.commit()
            result = await db.execute(select(PMEntry).where(PMEntry.id == entry_id))
            entry = result.scalar_one_or_none()
            return PMEntryModel.model_validate(entry) if entry else None

    async def delete_entry_by_id(
        self, entry_id: str, db: Optional[AsyncSession] = None
    ) -> bool:
        async with get_async_db_context(db) as db:
            await db.execute(delete(PMEntry).where(PMEntry.id == entry_id))
            await db.commit()
            return True


PMProjects = PMProjects()
PMVersions = PMVersions()
PMEntries = PMEntries()
