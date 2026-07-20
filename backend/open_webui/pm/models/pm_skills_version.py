"""PmSkillsVersion model for tracking pm-skills versions."""

import time
from typing import Optional

from open_webui.internal.db import Base, get_async_db_context
from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, Text, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession


class PmSkillsVersion(Base):
    """Track pm-skills version information."""

    __tablename__ = "pm_pm_skills_version"

    command_id = Column(Text, primary_key=True, nullable=False)  # e.g., "write-prd"
    version = Column(Text, nullable=False)  # version string
    methodology_hash = Column(Text, nullable=False)  # hash of SKILL.md content
    updated_at = Column(BigInteger)


class PmSkillsVersionModel(BaseModel):
    """Pydantic model for PmSkillsVersion."""

    model_config = ConfigDict(from_attributes=True)

    command_id: str
    version: str
    methodology_hash: str
    updated_at: int


class PmSkillsVersionForm(BaseModel):
    """Form for creating/updating PmSkillsVersion."""

    command_id: str
    version: str
    methodology_hash: str


class PmSkillsVersions:
    """CRUD operations for PmSkillsVersion."""

    async def insert_new_version(
        self, form_data: PmSkillsVersionForm, db: Optional[AsyncSession] = None
    ) -> Optional[PmSkillsVersionModel]:
        """Create or update version tracking."""
        async with get_async_db_context(db) as db:
            # Check if version already exists
            result = await db.execute(
                select(PmSkillsVersion).where(
                    PmSkillsVersion.command_id == form_data.command_id
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                # Update existing
                await db.execute(
                    update(PmSkillsVersion)
                    .where(PmSkillsVersion.command_id == form_data.command_id)
                    .values(
                        version=form_data.version,
                        methodology_hash=form_data.methodology_hash,
                        updated_at=int(time.time_ns()),
                    )
                )
            else:
                # Create new
                version = PmSkillsVersion(
                    command_id=form_data.command_id,
                    version=form_data.version,
                    methodology_hash=form_data.methodology_hash,
                    updated_at=int(time.time_ns()),
                )
                db.add(version)
            await db.commit()

            result = await db.execute(
                select(PmSkillsVersion).where(
                    PmSkillsVersion.command_id == form_data.command_id
                )
            )
            version = result.scalar_one_or_none()
            return PmSkillsVersionModel.model_validate(version) if version else None

    async def get_version_by_command_id(
        self, command_id: str, db: Optional[AsyncSession] = None
    ) -> Optional[PmSkillsVersionModel]:
        """Get version by command_id."""
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(PmSkillsVersion).where(
                    PmSkillsVersion.command_id == command_id
                )
            )
            version = result.scalar_one_or_none()
            return PmSkillsVersionModel.model_validate(version) if version else None

    async def get_all_versions(
        self, db: Optional[AsyncSession] = None
    ) -> list[PmSkillsVersionModel]:
        """Get all versions."""
        async with get_async_db_context(db) as db:
            result = await db.execute(select(PmSkillsVersion))
            return [
                PmSkillsVersionModel.model_validate(v)
                for v in result.scalars().all()
            ]

    async def delete_version_by_command_id(
        self, command_id: str, db: Optional[AsyncSession] = None
    ) -> bool:
        """Delete version by command_id."""
        async with get_async_db_context(db) as db:
            await db.execute(
                delete(PmSkillsVersion).where(
                    PmSkillsVersion.command_id == command_id
                )
            )
            await db.commit()
            return True


PmSkillsVersions = PmSkillsVersions()
