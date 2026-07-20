"""PmSkillsMapping model for pm-skills to SkillContract mapping."""

import time
import uuid
from typing import Optional

from open_webui.internal.db import Base, get_async_db_context
from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, Text, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession


class PmSkillsMapping(Base):
    """Mapping between pm-skills commands and SkillContract entries."""

    __tablename__ = "pm_pm_skills_mapping"

    id = Column(Text, primary_key=True, unique=True)
    command_id = Column(Text, nullable=False, unique=True)  # e.g., "write-prd"
    skill_contract_id = Column(Text, nullable=False)  # e.g., "pm-skills/write-prd"
    version = Column(Text, nullable=False)  # pm-skills version
    methodology_ref = Column(Text, nullable=False)  # path to SKILL.md
    output_contract_id = Column(Text, nullable=True)  # optional output contract
    enabled = Column(Text, default="true")  # "true" or "false"
    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)


class PmSkillsMappingModel(BaseModel):
    """Pydantic model for PmSkillsMapping."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    command_id: str
    skill_contract_id: str
    version: str
    methodology_ref: str
    output_contract_id: Optional[str] = None
    enabled: str = "true"
    created_at: int
    updated_at: int


class PmSkillsMappingForm(BaseModel):
    """Form for creating/updating PmSkillsMapping."""

    command_id: str
    skill_contract_id: str
    version: str
    methodology_ref: str
    output_contract_id: Optional[str] = None
    enabled: str = "true"


class PmSkillsMappings:
    """CRUD operations for PmSkillsMapping."""

    async def insert_new_mapping(
        self, form_data: PmSkillsMappingForm, db: Optional[AsyncSession] = None
    ) -> Optional[PmSkillsMappingModel]:
        """Create a new mapping."""
        async with get_async_db_context(db) as db:
            mapping = PmSkillsMapping(
                id=str(uuid.uuid4()),
                command_id=form_data.command_id,
                skill_contract_id=form_data.skill_contract_id,
                version=form_data.version,
                methodology_ref=form_data.methodology_ref,
                output_contract_id=form_data.output_contract_id,
                enabled=form_data.enabled,
                created_at=int(time.time_ns()),
                updated_at=int(time.time_ns()),
            )
            db.add(mapping)
            await db.commit()
            return PmSkillsMappingModel.model_validate(mapping)

    async def get_mapping_by_id(
        self, mapping_id: str, db: Optional[AsyncSession] = None
    ) -> Optional[PmSkillsMappingModel]:
        """Get mapping by ID."""
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(PmSkillsMapping).where(PmSkillsMapping.id == mapping_id)
            )
            mapping = result.scalar_one_or_none()
            return PmSkillsMappingModel.model_validate(mapping) if mapping else None

    async def get_mapping_by_command_id(
        self, command_id: str, db: Optional[AsyncSession] = None
    ) -> Optional[PmSkillsMappingModel]:
        """Get mapping by command_id."""
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(PmSkillsMapping).where(PmSkillsMapping.command_id == command_id)
            )
            mapping = result.scalar_one_or_none()
            return PmSkillsMappingModel.model_validate(mapping) if mapping else None

    async def get_all_mappings(
        self, db: Optional[AsyncSession] = None
    ) -> list[PmSkillsMappingModel]:
        """Get all mappings."""
        async with get_async_db_context(db) as db:
            result = await db.execute(select(PmSkillsMapping))
            return [
                PmSkillsMappingModel.model_validate(m)
                for m in result.scalars().all()
            ]

    async def get_enabled_mappings(
        self, db: Optional[AsyncSession] = None
    ) -> list[PmSkillsMappingModel]:
        """Get all enabled mappings."""
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(PmSkillsMapping).where(PmSkillsMapping.enabled == "true")
            )
            return [
                PmSkillsMappingModel.model_validate(m)
                for m in result.scalars().all()
            ]

    async def update_mapping_by_id(
        self,
        mapping_id: str,
        form_data: PmSkillsMappingForm,
        db: Optional[AsyncSession] = None,
    ) -> Optional[PmSkillsMappingModel]:
        """Update a mapping."""
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(PmSkillsMapping).where(PmSkillsMapping.id == mapping_id)
            )
            mapping = result.scalar_one_or_none()
            if not mapping:
                return None
            update_data = form_data.model_dump(exclude_none=True)
            if update_data:
                update_data["updated_at"] = int(time.time_ns())
                await db.execute(
                    update(PmSkillsMapping)
                    .where(PmSkillsMapping.id == mapping_id)
                    .values(**update_data)
                )
                await db.commit()
            result = await db.execute(
                select(PmSkillsMapping).where(PmSkillsMapping.id == mapping_id)
            )
            mapping = result.scalar_one_or_none()
            return PmSkillsMappingModel.model_validate(mapping) if mapping else None

    async def delete_mapping_by_id(
        self, mapping_id: str, db: Optional[AsyncSession] = None
    ) -> bool:
        """Delete a mapping."""
        async with get_async_db_context(db) as db:
            await db.execute(
                delete(PmSkillsMapping).where(PmSkillsMapping.id == mapping_id)
            )
            await db.commit()
            return True


PmSkillsMappings = PmSkillsMappings()
