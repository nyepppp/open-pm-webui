"""Session binding model for PM workspace session persistence."""

import time
import uuid
from typing import Optional

from open_webui.internal.db import Base, get_async_db_context
from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Boolean, Column, Text, select
from sqlalchemy.ext.asyncio import AsyncSession


class SessionBinding(Base):
    """Represents a chat session bound to a PM workspace."""

    __tablename__ = "pm_session_bindings"

    id = Column(Text, primary_key=True, unique=True)
    session_id = Column(Text, nullable=False)
    workspace_id = Column(Text, nullable=False)
    bound_at = Column(BigInteger)
    unbound_at = Column(BigInteger, nullable=True)
    is_active = Column(Text, default="true")  # "true" or "false"


class SessionBindingModel(BaseModel):
    """Pydantic model for SessionBinding."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    workspace_id: str
    bound_at: int
    unbound_at: Optional[int] = None
    is_active: str = "true"


class SessionBindingForm(BaseModel):
    """Form for creating/updating SessionBinding."""

    session_id: str
    workspace_id: str


class SessionBindings:
    """CRUD operations for SessionBinding."""

    async def insert_new_binding(
        self, form_data: SessionBindingForm, db: Optional[AsyncSession] = None
    ) -> Optional[SessionBindingModel]:
        """Create a new session binding."""
        async with get_async_db_context(db) as db:
            binding = SessionBinding(
                id=str(uuid.uuid4()),
                session_id=form_data.session_id,
                workspace_id=form_data.workspace_id,
                bound_at=int(time.time_ns()),
                unbound_at=None,
                is_active="true",
            )
            db.add(binding)
            await db.commit()
            return SessionBindingModel.model_validate(binding)

    async def get_binding_by_id(
        self, binding_id: str, db: Optional[AsyncSession] = None
    ) -> Optional[SessionBindingModel]:
        """Get binding by ID."""
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(SessionBinding).where(SessionBinding.id == binding_id)
            )
            binding = result.scalar_one_or_none()
            return SessionBindingModel.model_validate(binding) if binding else None

    async def get_active_binding_by_session(
        self, session_id: str, db: Optional[AsyncSession] = None
    ) -> Optional[SessionBindingModel]:
        """Get active binding for a session."""
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(SessionBinding)
                .where(SessionBinding.session_id == session_id)
                .where(SessionBinding.is_active == "true")
            )
            binding = result.scalar_one_or_none()
            return SessionBindingModel.model_validate(binding) if binding else None

    async def get_bindings_by_workspace(
        self, workspace_id: str, db: Optional[AsyncSession] = None
    ) -> list[SessionBindingModel]:
        """Get all bindings for a workspace."""
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(SessionBinding).where(SessionBinding.workspace_id == workspace_id)
            )
            return [
                SessionBindingModel.model_validate(b)
                for b in result.scalars().all()
            ]

    async def update_binding_status(
        self,
        binding_id: str,
        is_active: str,
        db: Optional[AsyncSession] = None,
    ) -> Optional[SessionBindingModel]:
        """Update binding status."""
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(SessionBinding).where(SessionBinding.id == binding_id)
            )
            binding = result.scalar_one_or_none()
            if not binding:
                return None
            binding.is_active = is_active
            if is_active == "false":
                binding.unbound_at = int(time.time_ns())
            await db.commit()
            return SessionBindingModel.model_validate(binding)

    async def delete_binding_by_id(
        self, binding_id: str, db: Optional[AsyncSession] = None
    ) -> bool:
        """Delete a binding."""
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(SessionBinding).where(SessionBinding.id == binding_id)
            )
            binding = result.scalar_one_or_none()
            if binding:
                await db.delete(binding)
                await db.commit()
            return True


# Singleton instance
SessionBindings = SessionBindings()
