"""权限管理 router - admin 管理扩展资源 grant (#33).

所有写操作 (grant / revoke) 仅 admin. 读操作 (list) 任何认证用户可查
(返回结果不含敏感字段, 仅 principal_type/principal_id/level).

#37: 所有 grant/revoke 操作写入 pm_audit_log 审计表.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from open_webui.utils.auth import get_verified_user
from open_webui.utils.acl import ADMIN_ROLE
from open_webui.models.permissions import Permissions
from open_webui.models.audit_logs import AuditLogs

log = logging.getLogger(__name__)

router = APIRouter(tags=["permissions"])


class PermissionGrantForm(BaseModel):
    """权限授予表单."""

    resource_type: str = Field(..., description="'skill' | 'tool' | 'function' | 'workflow'")
    resource_id: str = Field(..., description="Resource ID")
    principal_type: str = Field(..., description="'user' | 'role'")
    principal_id: str = Field(..., description="user_id 或 role name (e.g. 'admin')")
    level: str = Field("read", description="'read' | 'execute' | 'manage'")


@router.post("/")
async def grant_permission(
    form: PermissionGrantForm,
    request: Request,
    user=Depends(get_verified_user),
):
    """授予某 principal 对某资源的权限 (仅 admin).

    #33: 仅 admin 可调用. 同主键 upsert (更新 level).
    #37: 写入审计日志.
    """
    if user.role != ADMIN_ROLE:
        raise HTTPException(status_code=403, detail="Only admin can grant permissions")

    # 参数校验
    if form.resource_type not in ("skill", "tool", "function", "workflow"):
        raise HTTPException(status_code=400, detail=f"Invalid resource_type: {form.resource_type}")
    if form.principal_type not in ("user", "role"):
        raise HTTPException(status_code=400, detail=f"Invalid principal_type: {form.principal_type}")
    if form.level not in ("read", "execute", "manage"):
        raise HTTPException(status_code=400, detail=f"Invalid level: {form.level}")

    perm = await Permissions.grant(
        resource_type=form.resource_type,
        resource_id=form.resource_id,
        principal_type=form.principal_type,
        principal_id=form.principal_id,
        level=form.level,
        granted_by=user.id,
    )

    # #37 审计: 记录授权操作
    await AuditLogs.record(
        action="grant",
        resource_type="permission",
        actor_user_id=user.id,
        actor_role=user.role,
        resource_id=perm.id,
        detail={
            "target_resource_type": form.resource_type,
            "target_resource_id": form.resource_id,
            "principal_type": form.principal_type,
            "principal_id": form.principal_id,
            "level": form.level,
        },
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return {"id": perm.id, "level": perm.level}


@router.get("/{resource_type}/{resource_id}")
async def list_permissions(
    resource_type: str,
    resource_id: str,
    user=Depends(get_verified_user),
):
    """列出某资源的所有 grant (任何认证用户可查, 不含敏感字段).

    #33: 不限制 admin, 因为列表不含 granted_by / created_at 等元数据,
    仅返回 principal_type / principal_id / level.
    """
    perms = await Permissions.list_for_resource(resource_type, resource_id)
    return [
        {
            "id": p.id,
            "principal_type": p.principal_type,
            "principal_id": p.principal_id,
            "level": p.level,
        }
        for p in perms
    ]


@router.delete("/{permission_id}")
async def revoke_permission(
    permission_id: str,
    request: Request,
    user=Depends(get_verified_user),
):
    """撤销 grant (仅 admin).

    #33: 仅 admin 可调用.
    #37: 写入审计日志.
    """
    if user.role != ADMIN_ROLE:
        raise HTTPException(status_code=403, detail="Only admin can revoke permissions")

    ok = await Permissions.revoke(permission_id)

    # #37 审计: 无论成功失败都记录尝试 (失败表示 id 不存在)
    await AuditLogs.record(
        action="revoke",
        resource_type="permission",
        actor_user_id=user.id,
        actor_role=user.role,
        resource_id=permission_id,
        detail={"success": ok},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    if not ok:
        raise HTTPException(status_code=404, detail="Permission not found")
    return {"deleted": permission_id}
