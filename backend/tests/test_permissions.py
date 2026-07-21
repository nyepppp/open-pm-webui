"""
Tests for permissions RBAC (#33).

Validates Permission model grant/check/revoke logic and admin bypass.
Uses stub for DB context to avoid real DB dependency.
"""

import os
import sys
import types
import importlib.util
from unittest.mock import patch, MagicMock, AsyncMock

import pytest


# 先 stub open_webui 包, 避免触发完整依赖链 (uvicorn 等)
# 但用真实的 SQLAlchemy declarative_base 让 Permission 类正常工作
from sqlalchemy.orm import declarative_base as _real_declarative_base

if "open_webui" not in sys.modules:
    open_webui_stub = types.ModuleType("open_webui")
    sys.modules["open_webui"] = open_webui_stub
if "open_webui.internal" not in sys.modules:
    internal_stub = types.ModuleType("open_webui.internal")
    sys.modules["open_webui.internal"] = internal_stub
if "open_webui.internal.db" not in sys.modules:
    db_stub = types.ModuleType("open_webui.internal.db")
    # 用真实 SQLAlchemy 的 declarative_base, 让 Permission 类能正确注册列
    db_stub.Base = _real_declarative_base()
    db_stub.get_async_db_context = None  # 占位, 后面会 patch
    sys.modules["open_webui.internal.db"] = db_stub
    internal_stub.db = db_stub

# 同样 stub open_webui.utils.acl 以避免循环导入
if "open_webui.utils" not in sys.modules:
    utils_stub = types.ModuleType("open_webui.utils")
    sys.modules["open_webui.utils"] = utils_stub
if "open_webui.utils.acl" not in sys.modules:
    acl_stub = types.ModuleType("open_webui.utils.acl")
    acl_stub.ADMIN_ROLE = "admin"
    sys.modules["open_webui.utils.acl"] = acl_stub
    utils_stub.acl = acl_stub

# 现在才加载 permissions 模块
_module_path = os.path.join(
    os.path.dirname(__file__), "..", "open_webui", "models", "permissions.py"
)
_spec = importlib.util.spec_from_file_location("permissions_under_test", _module_path)
permissions_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(permissions_module)


def _stub_get_async_db_context():
    """构造一个 fake get_async_db_context 函数, 返回 async context manager.

    真实 get_async_db_context 是 @asynccontextmanager 装饰的函数,
    调用 -> 返回 async context manager (支持 async with).
    """
    session = MagicMock()
    session.get = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.delete = AsyncMock()
    session.commit = AsyncMock()
    scalars_mock = MagicMock()
    scalars_mock.all = MagicMock(return_value=[])
    result_mock = MagicMock()
    result_mock.scalars = MagicMock(return_value=scalars_mock)
    session.execute = AsyncMock(return_value=result_mock)

    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def fake_ctx():
        yield session

    return fake_ctx, session


@pytest.fixture(autouse=True)
def patch_db_context():
    """每个测试自动 stub get_async_db_context, 避免真实 DB."""
    fake_ctx, session = _stub_get_async_db_context()
    with patch.object(permissions_module, "get_async_db_context", fake_ctx):
        yield session


# 注册到 sys.modules 以便 patch.object 内部查找
sys.modules["permissions_under_test"] = permissions_module

Permission = permissions_module.Permission
Permissions = permissions_module.Permissions


def _make_perm(level="read", principal_type="user", principal_id="user-A",
               resource_type="skill", resource_id="skill-X"):
    """构造一个内存中的 Permission 对象."""
    return Permission(
        id=f"{resource_type}:{resource_id}:{principal_type}:{principal_id}",
        resource_type=resource_type,
        resource_id=resource_id,
        principal_type=principal_type,
        principal_id=principal_id,
        level=level,
    )


class TestAdminBypass:
    """#33: admin 角色直接 bypass, 不查 DB."""

    @pytest.mark.asyncio
    async def test_admin_check_returns_true_without_db_call(self, patch_db_context):
        # admin 调用 check, 不应触发任何 DB 查询
        ok = await Permissions.check(
            resource_type="skill",
            resource_id="any",
            user_id="admin-1",
            user_role="admin",
            required_level="execute",
        )
        assert ok is True
        # patch_db_context 是 MagicMock session, execute 不应被调用
        assert patch_db_context.execute.call_count == 0


class TestGrantThenCheck:
    """#33: 授予权限后, check 通过."""

    @pytest.mark.asyncio
    async def test_grant_user_execute_then_check_passes(self, patch_db_context):
        # mock db.execute 返回包含一个 execute grant
        grant = _make_perm(level="execute")
        scalars_mock = MagicMock()
        scalars_mock.all = MagicMock(return_value=[grant])
        result_mock = MagicMock()
        result_mock.scalars = MagicMock(return_value=scalars_mock)
        patch_db_context.execute = AsyncMock(return_value=result_mock)

        ok = await Permissions.check(
            resource_type="skill",
            resource_id="skill-X",
            user_id="user-A",
            user_role="user",
            required_level="execute",
        )
        assert ok is True


class TestNoGrantDenied:
    """#33: 未授权用户 check 返回 False."""

    @pytest.mark.asyncio
    async def test_check_returns_false_without_grant(self, patch_db_context):
        # 默认 session 返回空列表
        ok = await Permissions.check(
            resource_type="skill",
            resource_id="skill-X",
            user_id="user-B",
            user_role="user",
            required_level="execute",
        )
        assert ok is False


class TestLevelHierarchy:
    """#33: level 层级 read < execute < manage."""

    @pytest.mark.asyncio
    async def test_read_grant_does_not_satisfy_execute(self, patch_db_context):
        grant = _make_perm(level="read")
        scalars_mock = MagicMock()
        scalars_mock.all = MagicMock(return_value=[grant])
        result_mock = MagicMock()
        result_mock.scalars = MagicMock(return_value=scalars_mock)
        patch_db_context.execute = AsyncMock(return_value=result_mock)

        ok = await Permissions.check(
            resource_type="skill",
            resource_id="skill-X",
            user_id="user-A",
            user_role="user",
            required_level="execute",
        )
        assert ok is False

    @pytest.mark.asyncio
    async def test_manage_grant_satisfies_execute(self, patch_db_context):
        grant = _make_perm(level="manage")
        scalars_mock = MagicMock()
        scalars_mock.all = MagicMock(return_value=[grant])
        result_mock = MagicMock()
        result_mock.scalars = MagicMock(return_value=scalars_mock)
        patch_db_context.execute = AsyncMock(return_value=result_mock)

        ok = await Permissions.check(
            resource_type="skill",
            resource_id="skill-X",
            user_id="user-A",
            user_role="user",
            required_level="execute",
        )
        assert ok is True


class TestRoleLevelGrant:
    """#33: role 级 grant (principal_type='role')."""

    @pytest.mark.asyncio
    async def test_role_grant_passes(self, patch_db_context):
        # 给 'editor' role 一个 execute grant
        grant = _make_perm(
            level="execute", principal_type="role", principal_id="editor"
        )
        scalars_mock = MagicMock()
        scalars_mock.all = MagicMock(return_value=[grant])
        result_mock = MagicMock()
        result_mock.scalars = MagicMock(return_value=scalars_mock)
        patch_db_context.execute = AsyncMock(return_value=result_mock)

        ok = await Permissions.check(
            resource_type="skill",
            resource_id="skill-X",
            user_id="user-A",
            user_role="editor",
            required_level="execute",
        )
        assert ok is True


class TestRevokePermission:
    """#33: 撤销 grant."""

    @pytest.mark.asyncio
    async def test_revoke_existing_permission(self, patch_db_context):
        existing = _make_perm()
        patch_db_context.get = AsyncMock(return_value=existing)

        ok = await Permissions.revoke("skill:skill-X:user:user-A")
        assert ok is True
        assert patch_db_context.delete.call_count == 1

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_returns_false(self, patch_db_context):
        patch_db_context.get = AsyncMock(return_value=None)

        ok = await Permissions.revoke("nonexistent")
        assert ok is False
        assert patch_db_context.delete.call_count == 0


class TestUpsertOnGrant:
    """#33: grant 同主键时 upsert (更新 level), 不重复插入."""

    @pytest.mark.asyncio
    async def test_grant_updates_existing_level(self, patch_db_context):
        existing = _make_perm(level="read")
        patch_db_context.get = AsyncMock(return_value=existing)

        await Permissions.grant(
            resource_type="skill",
            resource_id="skill-X",
            principal_type="user",
            principal_id="user-A",
            level="execute",
            granted_by="admin-1",
        )
        # 应更新 level 而非 add 新对象
        assert existing.level == "execute"
        assert existing.granted_by == "admin-1"
        assert patch_db_context.add.call_count == 0
        assert patch_db_context.commit.call_count == 1
