"""审计日志查询 router (#37).

GET /api/v1/audit-logs/ - 查询审计日志
  admin 看全部, 普通用户只看自己的 (按 actor_user_id 过滤)
  支持 resource_type / action 过滤, limit/offset 分页
"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from open_webui.utils.auth import get_verified_user
from open_webui.models.audit_logs import AuditLogs

log = logging.getLogger(__name__)

router = APIRouter(tags=["audit_logs"])


@router.get("/")
async def list_audit_logs(
    user=Depends(get_verified_user),
    limit: int = Query(100, ge=1, le=500, description="Max results (1-500)"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    resource_type: str = Query(None, description="Filter by resource type"),
    action: str = Query(None, description="Filter by action"),
):
    """查询审计日志.

    #37: admin 看全部, 普通用户只看自己的.
    """
    logs = await AuditLogs.list_logs(
        user_id=user.id,
        user_role=user.role,
        limit=limit,
        offset=offset,
        resource_type=resource_type,
        action=action,
    )
    return [
        {
            "id": l.id,
            "timestamp": l.timestamp,
            "actor_user_id": l.actor_user_id,
            "actor_role": l.actor_role,
            "action": l.action,
            "resource_type": l.resource_type,
            "resource_id": l.resource_id,
            "project_id": l.project_id,
            "detail": json.loads(l.detail) if l.detail else None,
            "ip_address": l.ip_address,
            "user_agent": l.user_agent,
        }
        for l in logs
    ]
