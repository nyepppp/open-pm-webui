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


class PMEntryVersion(Base):
    __tablename__ = 'pm_entry_version'

    id = Column(Text, primary_key=True, unique=True)
    entry_id = Column(Text)
    project_id = Column(Text)
    module_type = Column(Text)
    version_number = Column(Text)
    content = Column(Text, nullable=True)
    entry_metadata = Column(JSON, nullable=True)
    parent_id = Column(Text, nullable=True)
    branch_name = Column(Text, default='main')
    change_summary = Column(Text, nullable=True)
    project_version_id = Column(Text, nullable=True)  # 关联项目版本
    created_by = Column(Text, nullable=True)
    created_at = Column(BigInteger)


class PMEntryBranch(Base):
    __tablename__ = 'pm_entry_branch'

    id = Column(Text, primary_key=True, unique=True)
    project_id = Column(Text)
    entry_id = Column(Text)
    name = Column(Text)
    source_version_id = Column(Text, nullable=True)
    status = Column(Text, default='active')
    merged_to_version_id = Column(Text, nullable=True)
    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)


class PMEntryMerge(Base):
    __tablename__ = 'pm_entry_merge'

    id = Column(Text, primary_key=True, unique=True)
    entry_id = Column(Text)
    branch_id = Column(Text)
    source_version_id = Column(Text, nullable=True)
    target_version_id = Column(Text, nullable=True)
    conflicts = Column(JSON, nullable=True)
    status = Column(Text, default='pending')
    resolved_by = Column(Text, nullable=True)
    merged_at = Column(BigInteger, nullable=True)
    created_at = Column(BigInteger)


####################
# PM Traceability Schema
####################

class PMEntity(Base):
    __tablename__ = 'pm_entity'

    id = Column(Text, primary_key=True, unique=True)
    project_id = Column(Text)
    type = Column(Text)  # "requirement" | "module" | "feature" | "parameter" | "document" | "version" | "operation"
    name = Column(Text)
    module_id = Column(Text, nullable=True)
    feature_id = Column(Text, nullable=True)
    entry_id = Column(Text, nullable=True)  # 关联到 pm_entry.id
    entity_metadata = Column(JSON, nullable=True)
    created_at = Column(BigInteger)


class PMRelation(Base):
    __tablename__ = 'pm_relation'

    id = Column(Text, primary_key=True, unique=True)
    project_id = Column(Text)
    entity_a_id = Column(Text)
    entity_b_id = Column(Text)
    relation_type = Column(Text)  # "contains" | "references" | "derives" | "modifies" | "conflicts"
    confidence = Column(BigInteger, nullable=True)  # 0-100
    confirmed = Column(BigInteger, default=0)  # 0=待确认, 1=已确认
    created_by = Column(Text, nullable=True)  # "ai" | "user"
    version_id = Column(Text, nullable=True)  # 关联版本
    created_at = Column(BigInteger)


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
    project_id: Optional[str] = None
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
    current_version_number: Optional[str] = None  # computed from latest entry version
    branch_name: Optional[str] = None              # computed from latest entry version
    created_at: int
    updated_at: int


class PMEntryForm(BaseModel):
    project_id: Optional[str] = None
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


class PMEntryVersionModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    entry_id: str
    project_id: str
    module_type: str
    version_number: str
    content: Optional[str] = None
    entry_metadata: Optional[dict] = None
    parent_id: Optional[str] = None
    branch_name: str = 'main'
    change_summary: Optional[str] = None
    project_version_id: Optional[str] = None
    created_by: Optional[str] = None
    created_at: int


class PMEntryVersionForm(BaseModel):
    entry_id: Optional[str] = None
    project_id: Optional[str] = None
    module_type: Optional[str] = None
    version_number: Optional[str] = None
    content: Optional[str] = None
    entry_metadata: Optional[dict] = None
    parent_id: Optional[str] = None
    branch_name: Optional[str] = 'main'
    change_summary: Optional[str] = None
    project_version_id: Optional[str] = None


class PMEntryBranchModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    entry_id: str
    name: str
    source_version_id: Optional[str] = None
    status: str = 'active'
    merged_to_version_id: Optional[str] = None
    created_at: int
    updated_at: int


class PMEntryBranchForm(BaseModel):
    project_id: Optional[str] = None
    entry_id: Optional[str] = None
    name: str
    source_version_id: Optional[str] = None


class PMEntryMergeModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    entry_id: str
    branch_id: str
    source_version_id: Optional[str] = None
    target_version_id: Optional[str] = None
    conflicts: Optional[list] = None
    status: str = 'pending'
    resolved_by: Optional[str] = None
    merged_at: Optional[int] = None
    created_at: int


class PMEntryMergeForm(BaseModel):
    entry_id: Optional[str] = None
    branch_id: str
    target_version_id: Optional[str] = None


####################
# PM Traceability Pydantic Models
####################

class PMEntityModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    type: str
    name: str
    module_id: Optional[str] = None
    feature_id: Optional[str] = None
    entry_id: Optional[str] = None
    entity_metadata: Optional[dict] = None
    created_at: int


class PMEntityForm(BaseModel):
    project_id: Optional[str] = None
    type: str
    name: str
    module_id: Optional[str] = None
    feature_id: Optional[str] = None
    entry_id: Optional[str] = None
    entity_metadata: Optional[dict] = None


class PMRelationModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    entity_a_id: str
    entity_b_id: str
    relation_type: str
    confidence: Optional[int] = 100
    confirmed: int = 1
    created_by: Optional[str] = None
    version_id: Optional[str] = None
    created_at: int


class PMRelationForm(BaseModel):
    project_id: Optional[str] = None
    entity_a_id: str
    entity_b_id: str
    relation_type: str
    confidence: Optional[int] = 100
    confirmed: Optional[int] = 1
    created_by: Optional[str] = None
    version_id: Optional[str] = None


####################
# Table Classes
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


class PMEntryVersions:
    async def insert_new_version(
        self, user_id: str, form_data: PMEntryVersionForm, db: Optional[AsyncSession] = None
    ) -> Optional[PMEntryVersionModel]:
        async with get_async_db_context(db) as db:
            version = PMEntryVersion(
                id=str(uuid.uuid4()),
                entry_id=form_data.entry_id or '',
                project_id=form_data.project_id or '',
                module_type=form_data.module_type or '',
                version_number=form_data.version_number or f'v{int(time.time())}',
                content=form_data.content,
                entry_metadata=form_data.entry_metadata,
                parent_id=form_data.parent_id,
                branch_name=form_data.branch_name or 'main',
                change_summary=form_data.change_summary,
                project_version_id=form_data.project_version_id,
                created_by=user_id,
                created_at=int(time.time_ns()),
            )
            db.add(version)
            await db.commit()
            return PMEntryVersionModel.model_validate(version)

    async def get_versions_by_entry_id(
        self, entry_id: str, db: Optional[AsyncSession] = None
    ) -> list[PMEntryVersionModel]:
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(PMEntryVersion)
                .where(PMEntryVersion.entry_id == entry_id)
                .order_by(PMEntryVersion.created_at.desc())
            )
            return [PMEntryVersionModel.model_validate(v) for v in result.scalars().all()]

    async def get_version_by_id(
        self, version_id: str, db: Optional[AsyncSession] = None
    ) -> Optional[PMEntryVersionModel]:
        async with get_async_db_context(db) as db:
            result = await db.execute(select(PMEntryVersion).where(PMEntryVersion.id == version_id))
            version = result.scalar_one_or_none()
            return PMEntryVersionModel.model_validate(version) if version else None

    async def get_versions_by_project_version_id(
        self, project_version_id: str, db: Optional[AsyncSession] = None
    ) -> list[PMEntryVersionModel]:
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(PMEntryVersion).where(PMEntryVersion.project_version_id == project_version_id)
            )
            return [PMEntryVersionModel.model_validate(v) for v in result.scalars().all()]

    async def get_latest_version_by_entry_id(
        self, entry_id: str, db: Optional[AsyncSession] = None
    ) -> Optional[PMEntryVersionModel]:
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(PMEntryVersion)
                .where(PMEntryVersion.entry_id == entry_id)
                .order_by(PMEntryVersion.created_at.desc())
                .limit(1)
            )
            version = result.scalar_one_or_none()
            return PMEntryVersionModel.model_validate(version) if version else None


class PMEntryBranches:
    async def insert_new_branch(
        self, form_data: PMEntryBranchForm, db: Optional[AsyncSession] = None
    ) -> Optional[PMEntryBranchModel]:
        async with get_async_db_context(db) as db:
            branch = PMEntryBranch(
                id=str(uuid.uuid4()),
                project_id=form_data.project_id or '',
                entry_id=form_data.entry_id or '',
                name=form_data.name,
                source_version_id=form_data.source_version_id,
                status='active',
                created_at=int(time.time_ns()),
                updated_at=int(time.time_ns()),
            )
            db.add(branch)
            await db.commit()
            return PMEntryBranchModel.model_validate(branch)

    async def get_branches_by_entry_id(
        self, entry_id: str, db: Optional[AsyncSession] = None
    ) -> list[PMEntryBranchModel]:
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(PMEntryBranch)
                .where(PMEntryBranch.entry_id == entry_id)
                .order_by(PMEntryBranch.created_at.desc())
            )
            return [PMEntryBranchModel.model_validate(b) for b in result.scalars().all()]


class PMEntryMerges:
    async def insert_new_merge(
        self, form_data: PMEntryMergeForm, db: Optional[AsyncSession] = None
    ) -> Optional[PMEntryMergeModel]:
        async with get_async_db_context(db) as db:
            merge = PMEntryMerge(
                id=str(uuid.uuid4()),
                entry_id=form_data.entry_id or '',
                branch_id=form_data.branch_id,
                target_version_id=form_data.target_version_id,
                conflicts=[],
                status='pending',
                created_at=int(time.time_ns()),
            )
            db.add(merge)
            await db.commit()
            return PMEntryMergeModel.model_validate(merge)

    async def get_merges_by_entry_id(
        self, entry_id: str, db: Optional[AsyncSession] = None
    ) -> list[PMEntryMergeModel]:
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(PMEntryMerge)
                .where(PMEntryMerge.entry_id == entry_id)
                .order_by(PMEntryMerge.created_at.desc())
            )
            return [PMEntryMergeModel.model_validate(m) for m in result.scalars().all()]


PMEntryVersions = PMEntryVersions()
PMEntryBranches = PMEntryBranches()
PMEntryMerges = PMEntryMerges()


####################
# PM Traceability Table Classes
####################

class PMEntities:
    async def insert_new_entity(
        self, user_id: str, form_data: PMEntityForm, db: Optional[AsyncSession] = None
    ) -> Optional[PMEntityModel]:
        async with get_async_db_context(db) as db:
            entity = PMEntity(
                id=str(uuid.uuid4()),
                project_id=form_data.project_id or '',
                type=form_data.type,
                name=form_data.name,
                module_id=form_data.module_id,
                feature_id=form_data.feature_id,
                entry_id=form_data.entry_id,
                entity_metadata=form_data.entity_metadata,
                created_at=int(time.time_ns()),
            )
            db.add(entity)
            await db.commit()
            return PMEntityModel.model_validate(entity)

    async def get_entities_by_project_id(
        self, project_id: str, db: Optional[AsyncSession] = None
    ) -> list[PMEntityModel]:
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(PMEntity)
                .where(PMEntity.project_id == project_id)
                .order_by(PMEntity.created_at.desc())
            )
            return [PMEntityModel.model_validate(e) for e in result.scalars().all()]

    async def get_entity_by_id(
        self, entity_id: str, db: Optional[AsyncSession] = None
    ) -> Optional[PMEntityModel]:
        async with get_async_db_context(db) as db:
            result = await db.execute(select(PMEntity).where(PMEntity.id == entity_id))
            entity = result.scalar_one_or_none()
            return PMEntityModel.model_validate(entity) if entity else None

    async def delete_entity_by_id(
        self, entity_id: str, db: Optional[AsyncSession] = None
    ) -> bool:
        async with get_async_db_context(db) as db:
            await db.execute(delete(PMEntity).where(PMEntity.id == entity_id))
            await db.commit()
            return True


class PMRelations:
    async def insert_new_relation(
        self, user_id: str, form_data: PMRelationForm, db: Optional[AsyncSession] = None
    ) -> Optional[PMRelationModel]:
        async with get_async_db_context(db) as db:
            relation = PMRelation(
                id=str(uuid.uuid4()),
                project_id=form_data.project_id or '',
                entity_a_id=form_data.entity_a_id,
                entity_b_id=form_data.entity_b_id,
                relation_type=form_data.relation_type,
                confidence=form_data.confidence or 100,
                confirmed=form_data.confirmed or 1,
                created_by=form_data.created_by or user_id,
                version_id=form_data.version_id,
                created_at=int(time.time_ns()),
            )
            db.add(relation)
            await db.commit()
            return PMRelationModel.model_validate(relation)

    async def get_relations_by_project_id(
        self, project_id: str, db: Optional[AsyncSession] = None
    ) -> list[PMRelationModel]:
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(PMRelation)
                .where(PMRelation.project_id == project_id)
                .order_by(PMRelation.created_at.desc())
            )
            return [PMRelationModel.model_validate(r) for r in result.scalars().all()]

    async def get_relations_by_entity_id(
        self, entity_id: str, db: Optional[AsyncSession] = None
    ) -> list[PMRelationModel]:
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(PMRelation)
                .where(
                    (PMRelation.entity_a_id == entity_id) | (PMRelation.entity_b_id == entity_id)
                )
                .order_by(PMRelation.created_at.desc())
            )
            return [PMRelationModel.model_validate(r) for r in result.scalars().all()]

    async def delete_relation_by_id(
        self, relation_id: str, db: Optional[AsyncSession] = None
    ) -> bool:
        async with get_async_db_context(db) as db:
            await db.execute(delete(PMRelation).where(PMRelation.id == relation_id))
            await db.commit()
            return True


PMEntities = PMEntities()
PMRelations = PMRelations()
