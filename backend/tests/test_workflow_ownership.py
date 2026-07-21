"""
Tests for workflow ownership (Issue #29).

Covers:
- Workflows.insert_new_workflow: writes owner_id correctly when provided;
  leaves owner_id NULL when not provided (legacy callers).
- Workflows.get_workflows_for_user: admins see all; non-admins see only their own.
- WorkflowService.get_workflow_with_access_check: returns workflow dict for
  owner/admin; raises 403 for non-owner; returns None when workflow missing.
- WorkflowService.create_workflow: passes owner_id through to repository.

These tests use unittest.mock to avoid the heavy DB fixture setup — the
repository layer (Workflows, WorkflowExecutions) is mocked at the boundary
so tests stay fast and don't require a real SQLite/Postgres instance.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock, MagicMock, patch

from open_webui.pm.models.workflow import (
    WorkflowForm,
    WorkflowModel,
    Workflows,
)
from open_webui.pm.services.workflow_service import WorkflowService
from open_webui.utils.acl import ADMIN_ROLE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_workflow_model(
    workflow_id: str = 'wf-1',
    name: str = 'Test Workflow',
    owner_id: str | None = 'user-a',
    project_id: str | None = 'proj-1',
) -> WorkflowModel:
    """Build a WorkflowModel instance for testing."""
    return WorkflowModel(
        id=workflow_id,
        name=name,
        description=None,
        project_id=project_id,
        status='draft',
        nodes='[]',
        edges='[]',
        execution_history='[]',
        owner_id=owner_id,
        acl='{"read": [], "write": []}',
        created_at=1700000000,
        updated_at=1700000000,
    )


def _make_workflow_form(name: str = 'Test Workflow') -> WorkflowForm:
    return WorkflowForm(
        name=name,
        description=None,
        project_id='proj-1',
        status='draft',
        nodes='[]',
        edges='[]',
    )


# ---------------------------------------------------------------------------
# Workflows.insert_new_workflow
# ---------------------------------------------------------------------------

class TestInsertNewWorkflow:
    """Tests for Workflows.insert_new_workflow owner_id handling."""

    @pytest.mark.asyncio
    async def test_insert_with_owner_id(self):
        """When owner_id is provided, it is written to the row."""
        captured_workflow = {}

        async def fake_context(_db):
            class FakeCtx:
                def __init__(self):
                    self.committed = False
                    self.rolled_back = False

                async def __aenter__(self):
                    self.db = MagicMock()
                    self.db.add = MagicMock()
                    return self.db

                async def __aexit__(self, *args):
                    return False

            return FakeCtx()

        form = _make_workflow_form()
        with patch(
            'open_webui.pm.models.workflow.get_async_db_context',
            new=fake_context,
        ):
            result = await Workflows().insert_new_workflow(form, owner_id='user-a')

        assert result is not None
        assert result.owner_id == 'user-a'
        assert result.acl == '{"read": [], "write": []}'

    @pytest.mark.asyncio
    async def test_insert_without_owner_id_legacy(self):
        """Legacy callers without owner_id → row has NULL owner_id (backfilled later)."""
        def fake_context(_db):
            class FakeCtx:
                def __init__(self):
                    self.db = MagicMock()

                async def __aenter__(self):
                    return self.db

                async def __aexit__(self, *args):
                    return False

            return FakeCtx()

        form = _make_workflow_form()
        with patch(
            'open_webui.pm.models.workflow.get_async_db_context',
            new=fake_context,
        ):
            result = await Workflows().insert_new_workflow(form, owner_id=None)

        assert result is not None
        assert result.owner_id is None


# ---------------------------------------------------------------------------
# Workflows.get_workflows_for_user
# ---------------------------------------------------------------------------

class TestGetWorkflowsForUser:
    """Tests for Workflows.get_workflows_for_user ACL filtering."""

    @pytest.mark.asyncio
    async def test_admin_sees_all(self):
        """Admin role → returns all workflows regardless of owner."""
        all_workflows = [
            _make_workflow_model('wf-1', owner_id='user-a'),
            _make_workflow_model('wf-2', owner_id='user-b'),
            _make_workflow_model('wf-3', owner_id=None),  # legacy
        ]

        async def fake_execute(stmt):
            result = MagicMock()
            result.scalars.return_value.all.return_value = all_workflows
            return result

        def fake_context(_db):
            class FakeCtx:
                async def __aenter__(self):
                    db = MagicMock()
                    db.execute = AsyncMock(side_effect=fake_execute)
                    return db

                async def __aexit__(self, *args):
                    return False

            return FakeCtx()

        with patch(
            'open_webui.pm.models.workflow.get_async_db_context',
            new=fake_context,
        ):
            result = await Workflows().get_workflows_for_user(
                'admin-1', ADMIN_ROLE
            )

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_non_admin_sees_only_own(self):
        """Non-admin → returns only workflows where owner_id matches."""
        own_workflow = _make_workflow_model('wf-1', owner_id='user-a')
        own_workflows = [own_workflow]

        async def fake_execute(stmt):
            result = MagicMock()
            result.scalars.return_value.all.return_value = own_workflows
            return result

        def fake_context(_db):
            class FakeCtx:
                async def __aenter__(self):
                    db = MagicMock()
                    db.execute = AsyncMock(side_effect=fake_execute)
                    return db

                async def __aexit__(self, *args):
                    return False

            return FakeCtx()

        with patch(
            'open_webui.pm.models.workflow.get_async_db_context',
            new=fake_context,
        ):
            result = await Workflows().get_workflows_for_user('user-a', 'user')

        assert len(result) == 1
        assert result[0].owner_id == 'user-a'


# ---------------------------------------------------------------------------
# WorkflowService.get_workflow_with_access_check
# ---------------------------------------------------------------------------

class TestGetWorkflowWithAccessCheck:
    """Tests for WorkflowService.get_workflow_with_access_check."""

    @pytest.mark.asyncio
    async def test_owner_ok(self):
        """Owner → returns workflow dict."""
        workflow_model = _make_workflow_model('wf-1', owner_id='user-a')
        with patch(
            'open_webui.pm.services.workflow_service.Workflows.get_workflow_by_id',
            new=AsyncMock(return_value=workflow_model),
        ):
            result = await WorkflowService().get_workflow_with_access_check(
                'wf-1', 'user-a', 'user'
            )
        assert result is not None
        assert result['id'] == 'wf-1'
        assert result['owner_id'] == 'user-a'

    @pytest.mark.asyncio
    async def test_admin_bypass(self):
        """Admin → can access any workflow."""
        workflow_model = _make_workflow_model('wf-1', owner_id='user-a')
        with patch(
            'open_webui.pm.services.workflow_service.Workflows.get_workflow_by_id',
            new=AsyncMock(return_value=workflow_model),
        ):
            result = await WorkflowService().get_workflow_with_access_check(
                'wf-1', 'admin-1', ADMIN_ROLE
            )
        assert result is not None

    @pytest.mark.asyncio
    async def test_non_owner_forbidden(self):
        """Non-owner → 403."""
        workflow_model = _make_workflow_model('wf-1', owner_id='user-a')
        with patch(
            'open_webui.pm.services.workflow_service.Workflows.get_workflow_by_id',
            new=AsyncMock(return_value=workflow_model),
        ):
            with pytest.raises(HTTPException) as exc:
                await WorkflowService().get_workflow_with_access_check(
                    'wf-1', 'user-b', 'user'
                )
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_workflow_not_found(self):
        """Non-existent workflow → returns None (router converts to 404)."""
        with patch(
            'open_webui.pm.services.workflow_service.Workflows.get_workflow_by_id',
            new=AsyncMock(return_value=None),
        ):
            result = await WorkflowService().get_workflow_with_access_check(
                'missing', 'user-a', 'user'
            )
        assert result is None

    @pytest.mark.asyncio
    async def test_null_owner_admin_ok(self):
        """NULL owner (legacy row) → admin can access, non-admin cannot."""
        workflow_model = _make_workflow_model('wf-1', owner_id=None)
        with patch(
            'open_webui.pm.services.workflow_service.Workflows.get_workflow_by_id',
            new=AsyncMock(return_value=workflow_model),
        ):
            # Admin OK
            result = await WorkflowService().get_workflow_with_access_check(
                'wf-1', 'admin-1', ADMIN_ROLE
            )
            assert result is not None

    @pytest.mark.asyncio
    async def test_null_owner_user_forbidden(self):
        """NULL owner + non-admin → 403 (defensive against un-backfilled rows)."""
        workflow_model = _make_workflow_model('wf-1', owner_id=None)
        with patch(
            'open_webui.pm.services.workflow_service.Workflows.get_workflow_by_id',
            new=AsyncMock(return_value=workflow_model),
        ):
            with pytest.raises(HTTPException) as exc:
                await WorkflowService().get_workflow_with_access_check(
                    'wf-1', 'user-a', 'user'
                )
        assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# WorkflowService.create_workflow — owner_id pass-through
# ---------------------------------------------------------------------------

class TestCreateWorkflowOwnerId:
    """Tests that WorkflowService.create_workflow passes owner_id through."""

    @pytest.mark.asyncio
    async def test_create_passes_owner_id(self):
        """owner_id is forwarded to Workflows.insert_new_workflow."""
        workflow_model = _make_workflow_model('wf-1', owner_id='user-a')
        with patch(
            'open_webui.pm.services.workflow_service.Workflows.insert_new_workflow',
            new=AsyncMock(return_value=workflow_model),
        ) as mock_insert:
            result = await WorkflowService().create_workflow(
                _make_workflow_form(), owner_id='user-a'
            )
        assert result is not None
        # Verify owner_id was forwarded
        _, kwargs = mock_insert.call_args
        assert kwargs.get('owner_id') == 'user-a'

    @pytest.mark.asyncio
    async def test_create_without_owner_id(self):
        """Legacy caller without owner_id → passes None through (backfilled later)."""
        workflow_model = _make_workflow_model('wf-1', owner_id=None)
        with patch(
            'open_webui.pm.services.workflow_service.Workflows.insert_new_workflow',
            new=AsyncMock(return_value=workflow_model),
        ) as mock_insert:
            result = await WorkflowService().create_workflow(
                _make_workflow_form()
            )
        assert result is not None
        _, kwargs = mock_insert.call_args
        # owner_id default is None
        assert kwargs.get('owner_id') is None
