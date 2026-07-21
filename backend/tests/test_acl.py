"""
Unit tests for ACL helpers (Issues #27, #28, #29).

Covers:
- require_owner: owner OK / non-owner 403 / admin bypass / None owner 403
- require_project_access: project exists + owner 200 / project missing 404 /
  non-owner 403 / admin bypass
- require_entry_access: entry exists + owner 200 / entry missing 404 /
  IDOR prevention (non-owner accessing other's entry by id → 403) /
  admin bypass
- require_workflow_owner: workflow owner OK / non-owner 403 / admin bypass /
  NULL owner only admin can access

These tests use unittest.mock to avoid the heavy DB fixture setup. The ACL
helpers are pure functions (require_owner, require_workflow_owner) or thin
async wrappers around PMProjects/PMEntries (require_project_access,
require_entry_access) — mocking the repository layer keeps tests fast and
deterministic.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock, MagicMock, patch

from open_webui.utils.acl import (
    require_owner,
    require_project_access,
    require_entry_access,
    require_workflow_owner,
    ADMIN_ROLE,
)


# ---------------------------------------------------------------------------
# require_owner
# ---------------------------------------------------------------------------

class TestRequireOwner:
    """Tests for the require_owner ownership check."""

    def test_owner_ok(self):
        """Owner accessing their own resource → no exception."""
        require_owner(
            resource_user_id='user-a',
            actor_user_id='user-a',
            actor_role='user',
        )

    def test_non_owner_forbidden(self):
        """Non-owner accessing someone else's resource → 403."""
        with pytest.raises(HTTPException) as exc:
            require_owner(
                resource_user_id='user-a',
                actor_user_id='user-b',
                actor_role='user',
            )
        assert exc.value.status_code == 403

    def test_admin_bypass(self):
        """Admin can access any resource regardless of owner."""
        require_owner(
            resource_user_id='user-a',
            actor_user_id='admin-1',
            actor_role=ADMIN_ROLE,
        )

    def test_none_owner_user_forbidden(self):
        """NULL owner + non-admin actor → 403 (defensive: prevents accidental
        access to legacy rows not yet backfilled by migration b9c0d1e2f3a4)."""
        with pytest.raises(HTTPException) as exc:
            require_owner(
                resource_user_id=None,
                actor_user_id='user-b',
                actor_role='user',
            )
        assert exc.value.status_code == 403

    def test_none_owner_admin_bypass(self):
        """NULL owner + admin → allowed (admin must be able to triage legacy rows)."""
        require_owner(
            resource_user_id=None,
            actor_user_id='admin-1',
            actor_role=ADMIN_ROLE,
        )


# ---------------------------------------------------------------------------
# require_project_access
# ---------------------------------------------------------------------------

class TestRequireProjectAccess:
    """Tests for require_project_access (Issue #27)."""

    @pytest.mark.asyncio
    async def test_project_owner_ok(self):
        """Project owner accessing their project → returns project."""
        project = MagicMock()
        project.user_id = 'user-a'
        with patch(
            'open_webui.utils.acl.PMProjects.get_project_by_id',
            new=AsyncMock(return_value=project),
        ):
            result = await require_project_access(
                project_id='proj-1',
                actor_user_id='user-a',
                actor_role='user',
                db=MagicMock(),
            )
        assert result is project

    @pytest.mark.asyncio
    async def test_project_not_found(self):
        """Non-existent project → 404 (NOT 403 — avoid leaking existence)."""
        with patch(
            'open_webui.utils.acl.PMProjects.get_project_by_id',
            new=AsyncMock(return_value=None),
        ):
            with pytest.raises(HTTPException) as exc:
                await require_project_access(
                    project_id='missing',
                    actor_user_id='user-a',
                    actor_role='user',
                    db=MagicMock(),
                )
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_project_non_owner_forbidden(self):
        """Non-owner accessing someone else's project → 403."""
        project = MagicMock()
        project.user_id = 'user-a'
        with patch(
            'open_webui.utils.acl.PMProjects.get_project_by_id',
            new=AsyncMock(return_value=project),
        ):
            with pytest.raises(HTTPException) as exc:
                await require_project_access(
                    project_id='proj-1',
                    actor_user_id='user-b',
                    actor_role='user',
                    db=MagicMock(),
                )
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_project_admin_bypass(self):
        """Admin can access any project."""
        project = MagicMock()
        project.user_id = 'user-a'
        with patch(
            'open_webui.utils.acl.PMProjects.get_project_by_id',
            new=AsyncMock(return_value=project),
        ):
            result = await require_project_access(
                project_id='proj-1',
                actor_user_id='admin-1',
                actor_role=ADMIN_ROLE,
                db=MagicMock(),
            )
        assert result is project


# ---------------------------------------------------------------------------
# require_entry_access (IDOR prevention — Issue #28)
# ---------------------------------------------------------------------------

class TestRequireEntryAccess:
    """Tests for require_entry_access — IDOR prevention is the core goal."""

    @pytest.mark.asyncio
    async def test_entry_owner_ok(self):
        """Owner accessing their entry → returns entry."""
        entry = MagicMock()
        entry.id = 'entry-1'
        entry.project_id = 'proj-1'
        project = MagicMock()
        project.user_id = 'user-a'

        with patch(
            'open_webui.utils.acl.PMEntries.get_entry_by_id',
            new=AsyncMock(return_value=entry),
        ), patch(
            'open_webui.utils.acl.PMProjects.get_project_by_id',
            new=AsyncMock(return_value=project),
        ):
            result = await require_entry_access(
                entry_id='entry-1',
                actor_user_id='user-a',
                actor_role='user',
                db=MagicMock(),
            )
        assert result is entry

    @pytest.mark.asyncio
    async def test_entry_not_found(self):
        """Non-existent entry → 404."""
        with patch(
            'open_webui.utils.acl.PMEntries.get_entry_by_id',
            new=AsyncMock(return_value=None),
        ):
            with pytest.raises(HTTPException) as exc:
                await require_entry_access(
                    entry_id='missing',
                    actor_user_id='user-a',
                    actor_role='user',
                    db=MagicMock(),
                )
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_idor_non_owner_forbidden(self):
        """IDOR attack: attacker knows entry_id of someone else's entry → 403.

        This is the key test for Issue #28. The attacker tries to access
        entry-1 (owned by user-a via proj-1) as user-b. The check should
        resolve entry→project→owner and reject.
        """
        entry = MagicMock()
        entry.id = 'entry-1'
        entry.project_id = 'proj-1'  # project owner is user-a, not user-b
        project = MagicMock()
        project.user_id = 'user-a'

        with patch(
            'open_webui.utils.acl.PMEntries.get_entry_by_id',
            new=AsyncMock(return_value=entry),
        ), patch(
            'open_webui.utils.acl.PMProjects.get_project_by_id',
            new=AsyncMock(return_value=project),
        ):
            with pytest.raises(HTTPException) as exc:
                await require_entry_access(
                    entry_id='entry-1',
                    actor_user_id='user-b',  # attacker
                    actor_role='user',
                    db=MagicMock(),
                )
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_entry_admin_bypass(self):
        """Admin can access any entry (e.g. for support/triage)."""
        entry = MagicMock()
        entry.id = 'entry-1'
        entry.project_id = 'proj-1'
        project = MagicMock()
        project.user_id = 'user-a'

        with patch(
            'open_webui.utils.acl.PMEntries.get_entry_by_id',
            new=AsyncMock(return_value=entry),
        ), patch(
            'open_webui.utils.acl.PMProjects.get_project_by_id',
            new=AsyncMock(return_value=project),
        ):
            result = await require_entry_access(
                entry_id='entry-1',
                actor_user_id='admin-1',
                actor_role=ADMIN_ROLE,
                db=MagicMock(),
            )
        assert result is entry


# ---------------------------------------------------------------------------
# require_workflow_owner
# ---------------------------------------------------------------------------

class TestRequireWorkflowOwner:
    """Tests for require_workflow_owner (Issue #29)."""

    def test_workflow_owner_ok(self):
        require_workflow_owner(
            resource_owner_id='user-a',
            actor_user_id='user-a',
            actor_role='user',
        )

    def test_workflow_non_owner_forbidden(self):
        with pytest.raises(HTTPException) as exc:
            require_workflow_owner(
                resource_owner_id='user-a',
                actor_user_id='user-b',
                actor_role='user',
            )
        assert exc.value.status_code == 403

    def test_workflow_admin_bypass(self):
        require_workflow_owner(
            resource_owner_id='user-a',
            actor_user_id='admin-1',
            actor_role=ADMIN_ROLE,
        )

    def test_workflow_null_owner_user_forbidden(self):
        """Legacy workflow with NULL owner (pre-migration) → non-admin 403.

        After migration b9c0d1e2f3a4 backfills owner_id, this case should
        rarely happen in production. The defensive check prevents accidental
        access if backfill skipped some rows.
        """
        with pytest.raises(HTTPException) as exc:
            require_workflow_owner(
                resource_owner_id=None,
                actor_user_id='user-b',
                actor_role='user',
            )
        assert exc.value.status_code == 403

    def test_workflow_null_owner_admin_bypass(self):
        """Admin can access legacy workflows with NULL owner for triage."""
        require_workflow_owner(
            resource_owner_id=None,
            actor_user_id='admin-1',
            actor_role=ADMIN_ROLE,
        )
