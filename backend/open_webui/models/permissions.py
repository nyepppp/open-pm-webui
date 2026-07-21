"""扩展资源权限模型 - RBAC for skills/tools/functions (#33).

设计:
- resource_type: 'skill' | 'tool' | 'function' | 'workflow'
- principal_type: 'user' | 'role'  (group-based 留待后续)
- level: 'read' < 'execute' < 'manage'
- admin 角色 bypass (acl.py ADMIN_ROLE)
"""

import time
import logging
from typing import Optional

from sqlalchemy import Column, Text, BigInteger, select, or_

from open_webui.internal.db import Base, get_async_db_context

log = logging.getLogger(__name__)


class Permission(Base):
    """扩展资源权限 grant 记录."""
    __tablename__ = "pm_permission"

    id = Column(Text, primary_key=True)
    resource_type = Column(Text, nullable=False)  # 'skill' | 'tool' | 'function' | 'workflow'
    resource_id = Column(Text, nullable=False)
    principal_type = Column(Text, nullable=False)  # 'user' | 'role'
    principal_id = Column(Text, nullable=False)  # user_id 或 role name (e.g. 'admin')
    level = Column(Text, nullable=False, default="read")  # 'read' | 'execute' | 'manage'
    granted_by = Column(Text, nullable=True)
    created_at = Column(BigInteger, default=lambda: int(time.time()))


_LEVEL_ORDER = {"read": 1, "execute": 2, "manage": 3}


def _level_satisfies(granted: str, required: str) -> bool:
    """检查 granted level 是否满足 required level 要求."""
    return _LEVEL_ORDER.get(granted, 0) >= _LEVEL_ORDER.get(required, 0)


class Permissions:
    """Permission CRUD 单例."""

    @classmethod
    async def grant(
        cls,
        resource_type: str,
        resource_id: str,
        principal_type: str,
        principal_id: str,
        level: str = "read",
        granted_by: Optional[str] = None,
    ) -> Optional[Permission]:
        """授予权限. id 由四元组拼接, 同主键 upsert."""
        perm_id = f"{resource_type}:{resource_id}:{principal_type}:{principal_id}"
        async with get_async_db_context() as db:
            # 查现有
            existing = await db.get(Permission, perm_id)
            if existing:
                existing.level = level
                existing.granted_by = granted_by
            else:
                perm = Permission(
                    id=perm_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    principal_type=principal_type,
                    principal_id=principal_id,
                    level=level,
                    granted_by=granted_by,
                )
                db.add(perm)
            await db.commit()
            return await db.get(Permission, perm_id)

    @classmethod
    async def check(
        cls,
        resource_type: str,
        resource_id: str,
        user_id: str,
        user_role: str,
        required_level: str = "read",
    ) -> bool:
        """检查用户对资源是否有 required_level 权限.

        Admin 直接通过 (与 acl.py ADMIN_ROLE 一致).
        否则查 user 级 + role 级 grant, 任一满足即通过.
        """
        from open_webui.utils.acl import ADMIN_ROLE

        if user_role == ADMIN_ROLE:
            return True

        async with get_async_db_context() as db:
            stmt = select(Permission).where(
                Permission.resource_type == resource_type,
                Permission.resource_id == resource_id,
                or_(
                    (Permission.principal_type == "user")
                    & (Permission.principal_id == user_id),
                    (Permission.principal_type == "role")
                    & (Permission.principal_id == user_role),
                ),
            )
            result = await db.execute(stmt)
            for p in result.scalars().all():
                if _level_satisfies(p.level, required_level):
                    return True
            return False

    @classmethod
    async def list_for_resource(
        cls, resource_type: str, resource_id: str
    ) -> list[Permission]:
        """列出某资源的所有 grant."""
        async with get_async_db_context() as db:
            stmt = select(Permission).where(
                Permission.resource_type == resource_type,
                Permission.resource_id == resource_id,
            )
            result = await db.execute(stmt)
            return list(result.scalars().all())

    @classmethod
    async def revoke(cls, permission_id: str) -> bool:
        """按 id 撤销 grant."""
        async with get_async_db_context() as db:
            existing = await db.get(Permission, permission_id)
            if not existing:
                return False
            await db.delete(existing)
            await db.commit()
            return True
