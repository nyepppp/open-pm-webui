"""PM 操作审计日志模型 (#37).

记录 PM 关键操作 (create/update/delete/execute/grant/revoke) 的元数据,
用于安全审计、合规追溯、异常行为检测.

设计:
- admin 看全部日志, 普通用户只看自己的
- 不存储敏感数据 (如完整 request body), 仅存 detail JSON 摘要
- 写入失败不应阻塞主流程 (best-effort, log error 后继续)
"""

import json
import logging
import time
import uuid
from typing import Any, Optional

from sqlalchemy import Column, Text, BigInteger, select

from open_webui.internal.db import Base, get_async_db_context

log = logging.getLogger(__name__)


class AuditLog(Base):
    """审计日志条目."""
    __tablename__ = "pm_audit_log"

    id = Column(Text, primary_key=True)
    timestamp = Column(BigInteger, default=lambda: int(time.time() * 1000))
    actor_user_id = Column(Text, nullable=True)
    actor_role = Column(Text, nullable=True)
    action = Column(Text, nullable=False)  # 'create' | 'update' | 'delete' | 'execute' | 'grant' | 'revoke'
    resource_type = Column(Text, nullable=False)  # 'project' | 'entry' | 'workflow' | 'permission'
    resource_id = Column(Text, nullable=True)
    project_id = Column(Text, nullable=True)
    detail = Column(Text, nullable=True)  # JSON string 摘要
    ip_address = Column(Text, nullable=True)
    user_agent = Column(Text, nullable=True)


class AuditLogs:
    """审计日志 CRUD 单例."""

    @classmethod
    async def record(
        cls,
        action: str,
        resource_type: str,
        actor_user_id: Optional[str] = None,
        actor_role: Optional[str] = None,
        resource_id: Optional[str] = None,
        project_id: Optional[str] = None,
        detail: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Optional[AuditLog]:
        """写入一条审计日志 (best-effort: 失败仅 log, 不抛出).

        Args:
            action: 操作类型 ('create'/'update'/'delete'/'execute'/'grant'/'revoke')
            resource_type: 资源类型 ('project'/'entry'/'workflow'/'permission')
            actor_user_id: 操作者用户 id
            actor_role: 操作者角色
            resource_id: 资源 id
            project_id: 所属 project id (可空, 如 permission 操作)
            detail: 额外元数据 (JSON 序列化为字符串存储)
            ip_address: 请求方 IP
            user_agent: 请求方 User-Agent

        Returns:
            创建的 AuditLog 对象, 或 None (写入失败时)
        """
        try:
            async with get_async_db_context() as db:
                entry = AuditLog(
                    id=str(uuid.uuid4()),
                    timestamp=int(time.time() * 1000),
                    actor_user_id=actor_user_id,
                    actor_role=actor_role,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    project_id=project_id,
                    detail=json.dumps(detail, ensure_ascii=False) if detail else None,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
                db.add(entry)
                await db.commit()
                return entry
        except Exception as e:
            # 审计日志写入失败不应阻塞主流程
            log.error(
                "Failed to write audit log: action=%s resource=%s:%s actor=%s error=%s",
                action, resource_type, resource_id, actor_user_id, e,
                exc_info=True,
            )
            return None

    @classmethod
    async def list_logs(
        cls,
        user_id: str,
        user_role: str,
        limit: int = 100,
        offset: int = 0,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
    ) -> list[AuditLog]:
        """查询审计日志.

        admin 看全部, 普通用户只看自己的 (按 actor_user_id 过滤).

        Args:
            user_id: 查询者用户 id
            user_role: 查询者角色 (admin 看全部)
            limit: 最多返回条数 (1-500)
            offset: 分页偏移
            resource_type: 可选过滤 - 资源类型
            action: 可选过滤 - 操作类型

        Returns:
            AuditLog 列表, 按 timestamp 倒序
        """
        from open_webui.utils.acl import ADMIN_ROLE

        async with get_async_db_context() as db:
            stmt = (
                select(AuditLog)
                .order_by(AuditLog.timestamp.desc())
                .limit(limit)
                .offset(offset)
            )
            # 普通用户只能看自己的; admin 看全部
            if user_role != ADMIN_ROLE:
                stmt = stmt.where(AuditLog.actor_user_id == user_id)
            if resource_type:
                stmt = stmt.where(AuditLog.resource_type == resource_type)
            if action:
                stmt = stmt.where(AuditLog.action == action)

            result = await db.execute(stmt)
            return list(result.scalars().all())
