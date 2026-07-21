"""
Tests for audit_logs module (#37).

Validates AuditLogs.record / list_logs with stubbed DB.
"""

import os
import sys
import types
import importlib.util
from unittest.mock import patch, MagicMock, AsyncMock
from contextlib import asynccontextmanager

import pytest


# 先 stub open_webui 包, 避免触发完整依赖链 (uvicorn 等)
from sqlalchemy.orm import declarative_base as _real_declarative_base

if "open_webui" not in sys.modules:
    open_webui_stub = types.ModuleType("open_webui")
    sys.modules["open_webui"] = open_webui_stub
if "open_webui.internal" not in sys.modules:
    internal_stub = types.ModuleType("open_webui.internal")
    sys.modules["open_webui.internal"] = internal_stub
if "open_webui.internal.db" not in sys.modules:
    db_stub = types.ModuleType("open_webui.internal.db")
    db_stub.Base = _real_declarative_base()
    db_stub.get_async_db_context = None
    sys.modules["open_webui.internal.db"] = db_stub
    internal_stub.db = db_stub

if "open_webui.utils" not in sys.modules:
    utils_stub = types.ModuleType("open_webui.utils")
    sys.modules["open_webui.utils"] = utils_stub
if "open_webui.utils.acl" not in sys.modules:
    acl_stub = types.ModuleType("open_webui.utils.acl")
    acl_stub.ADMIN_ROLE = "admin"
    sys.modules["open_webui.utils.acl"] = acl_stub
    utils_stub.acl = acl_stub

# 加载 audit_logs 模块
_module_path = os.path.join(
    os.path.dirname(__file__), "..", "open_webui", "models", "audit_logs.py"
)
_spec = importlib.util.spec_from_file_location("audit_logs_under_test", _module_path)
audit_logs_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(audit_logs_module)
sys.modules["audit_logs_under_test"] = audit_logs_module

AuditLog = audit_logs_module.AuditLog
AuditLogs = audit_logs_module.AuditLogs


def _stub_db(captured_entries: list):
    """构造一个 fake get_async_db_context, 捕获 db.add() 写入的 AuditLog 对象."""
    session = MagicMock()
    session.add = MagicMock(side_effect=lambda obj: captured_entries.append(obj))
    session.commit = AsyncMock()
    session.delete = AsyncMock()

    scalars_mock = MagicMock()
    result_mock = MagicMock()
    result_mock.scalars = MagicMock(return_value=scalars_mock)

    async def fake_execute(stmt):
        return result_mock

    session.execute = fake_execute

    @asynccontextmanager
    async def fake_ctx():
        yield session

    return fake_ctx, session, scalars_mock, result_mock


@pytest.fixture(autouse=True)
def patch_db_context():
    """每个测试自动 stub get_async_db_context."""
    captured = []
    fake_ctx, session, scalars_mock, result_mock = _stub_db(captured)
    with patch.object(audit_logs_module, "get_async_db_context", fake_ctx):
        yield {
            "session": session,
            "captured": captured,
            "scalars_mock": scalars_mock,
            "result_mock": result_mock,
        }


class TestRecordAndList:
    """#37: 写入审计日志后能查询到."""

    @pytest.mark.asyncio
    async def test_record_writes_entry_to_db(self, patch_db_context):
        result = await AuditLogs.record(
            action="create",
            resource_type="project",
            actor_user_id="user-A",
            actor_role="user",
            resource_id="proj-1",
            project_id="proj-1",
            detail={"name": "Test Project"},
            ip_address="127.0.0.1",
            user_agent="pytest/1.0",
        )
        assert result is not None
        assert len(patch_db_context["captured"]) == 1
        entry = patch_db_context["captured"][0]
        assert entry.action == "create"
        assert entry.resource_type == "project"
        assert entry.resource_id == "proj-1"
        assert entry.actor_user_id == "user-A"
        assert entry.actor_role == "user"
        assert entry.ip_address == "127.0.0.1"
        assert '"name": "Test Project"' in entry.detail
        assert entry.timestamp > 0

    @pytest.mark.asyncio
    async def test_list_returns_logs(self, patch_db_context):
        # 准备 fake 返回
        fake_log = AuditLog(
            id="log-1",
            timestamp=1700000000000,
            actor_user_id="user-A",
            actor_role="user",
            action="create",
            resource_type="project",
            resource_id="proj-1",
        )
        patch_db_context["scalars_mock"].all = MagicMock(return_value=[fake_log])

        logs = await AuditLogs.list_logs(
            user_id="user-A",
            user_role="user",
            limit=100,
        )
        assert len(logs) == 1
        assert logs[0].action == "create"
        assert logs[0].resource_id == "proj-1"


class TestAdminSeesAll:
    """#37: admin 看全部日志."""

    @pytest.mark.asyncio
    async def test_admin_no_actor_filter(self, patch_db_context):
        # admin 查询, 不应添加 actor_user_id 过滤
        fake_log_a = AuditLog(id="1", action="create", resource_type="project",
                              actor_user_id="user-A")
        fake_log_b = AuditLog(id="2", action="create", resource_type="project",
                              actor_user_id="user-B")
        patch_db_context["scalars_mock"].all = MagicMock(
            return_value=[fake_log_a, fake_log_b]
        )

        logs = await AuditLogs.list_logs(
            user_id="admin-1",
            user_role="admin",
        )
        assert len(logs) == 2


class TestUserSeesOnlyOwn:
    """#37: 普通用户只看自己的."""

    @pytest.mark.asyncio
    async def test_user_filter_by_actor(self, patch_db_context):
        # 普通用户查询, 仅返回自己的
        own_log = AuditLog(id="1", action="create", resource_type="project",
                           actor_user_id="user-A")
        patch_db_context["scalars_mock"].all = MagicMock(return_value=[own_log])

        logs = await AuditLogs.list_logs(
            user_id="user-A",
            user_role="user",
        )
        assert len(logs) == 1
        assert logs[0].actor_user_id == "user-A"


class TestFilterByAction:
    """#37: 按 action 过滤."""

    @pytest.mark.asyncio
    async def test_filter_by_action(self, patch_db_context):
        grant_log = AuditLog(id="1", action="grant", resource_type="permission")
        revoke_log = AuditLog(id="2", action="revoke", resource_type="permission")
        patch_db_context["scalars_mock"].all = MagicMock(return_value=[grant_log])

        # 只查 grant
        logs = await AuditLogs.list_logs(
            user_id="admin-1",
            user_role="admin",
            action="grant",
        )
        assert len(logs) == 1
        assert logs[0].action == "grant"


class TestRecordFailureBestEffort:
    """#37: 审计日志写入失败不应抛出 (best-effort)."""

    @pytest.mark.asyncio
    async def test_db_failure_returns_none(self, patch_db_context):
        # 让 commit 抛异常
        patch_db_context["session"].commit = AsyncMock(side_effect=RuntimeError("DB down"))

        # 不应抛出
        result = await AuditLogs.record(
            action="create",
            resource_type="project",
            actor_user_id="user-A",
            actor_role="user",
        )
        assert result is None


class TestOptionalFields:
    """#37: 可选字段允许 None."""

    @pytest.mark.asyncio
    async def test_minimal_record(self, patch_db_context):
        # 仅必填字段
        result = await AuditLogs.record(
            action="execute",
            resource_type="workflow",
        )
        assert result is not None
        assert result.actor_user_id is None
        assert result.resource_id is None
        assert result.detail is None
        assert result.ip_address is None
