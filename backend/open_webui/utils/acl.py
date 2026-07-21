"""Access control utilities for resource ownership checks.

This module provides helpers for verifying that an actor (the authenticated user)
has access to a specific PM resource (project, entry, workflow). It complements
`open_webui.utils.access_control` (which handles group-based feature permissions)
by enforcing resource-level ownership boundaries.

Typical usage in a router:

    from open_webui.utils.acl import require_project_access, require_entry_access

    @router.get('/projects/{project_id}')
    async def get_project(
        project_id: str,
        user=Depends(get_verified_user),
        db: AsyncSession = Depends(get_async_session),
    ):
        return await require_project_access(project_id, user.id, user.role, db)

Design decisions:
- Admin role bypasses all ownership checks (consistent with existing Open WebUI pattern).
- Repository-layer method signatures are NOT modified; checks happen at the router layer
  to minimize blast radius and avoid breaking existing callers (e.g. workflow engine,
  import/export tools, AI generators).
- `require_entry_access` resolves ownership via the entry's `project_id` to prevent
  Insecure Direct Object Reference (IDOR) — directly accessing an entry by ID without
  verifying the project owner is a known P0 vector (Issue #28).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from open_webui.models.pm import PMEntries, PMProjects

if TYPE_CHECKING:
    from open_webui.models.pm import PMEntryModel, PMProjectModel

log = logging.getLogger(__name__)

ADMIN_ROLE = 'admin'


def require_owner(resource_user_id: str, actor_user_id: str, actor_role: str) -> None:
    """Raise 403 if the actor is neither the resource owner nor an admin.

    Args:
        resource_user_id: The `user_id`/`owner_id` recorded on the resource row.
        actor_user_id: The authenticated user's id.
        actor_role: The authenticated user's role (`'admin'` bypasses).

    Raises:
        HTTPException(403): If actor is not owner and not admin.
    """
    if actor_role == ADMIN_ROLE:
        return
    if resource_user_id != actor_user_id:
        log.warning(
            '[ACL] access denied: actor=%s role=%s resource_owner=%s',
            actor_user_id,
            actor_role,
            resource_user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Access denied: resource is not owned by the current user.',
        )


async def require_project_access(
    project_id: str,
    actor_user_id: str,
    actor_role: str,
    db: AsyncSession,
    min_level: str = 'read',
) -> 'PMProjectModel':
    """Load a project and verify the actor has at least `min_level` access.

    Args:
        project_id: The project to load.
        actor_user_id: The authenticated user's id.
        actor_role: The authenticated user's role.
        db: Async DB session.
        min_level: Reserved for future RBAC levels. Currently only owner/admin
            distinction is enforced; the argument is accepted for API stability.

    Returns:
        The loaded `PMProjectModel`.

    Raises:
        HTTPException(404): If the project does not exist.
        HTTPException(403): If the actor is neither owner nor admin.
    """
    project = await PMProjects.get_project_by_id(project_id, db=db)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Project not found.',
        )
    require_owner(project.user_id, actor_user_id, actor_role)
    return project


async def require_entry_access(
    entry_id: str,
    actor_user_id: str,
    actor_role: str,
    db: AsyncSession,
) -> 'PMEntryModel':
    """Load an entry and verify the actor owns the entry's project.

    This prevents IDOR: an attacker who knows an `entry_id` cannot read or mutate
    another user's entry because we resolve the project owner through the entry's
    `project_id` and enforce ownership at the project level.

    Args:
        entry_id: The entry to load.
        actor_user_id: The authenticated user's id.
        actor_role: The authenticated user's role.
        db: Async DB session.

    Returns:
        The loaded `PMEntryModel`.

    Raises:
        HTTPException(404): If the entry does not exist.
        HTTPException(403): If the actor is neither owner nor admin of the entry's project.
    """
    entry = await PMEntries.get_entry_by_id(entry_id, db=db)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Entry not found.',
        )
    # Resolve ownership via the entry's project. We do NOT trust `entry.user_id`
    # as the source of truth because entries may be created by AI/workflow
    # services on behalf of the project owner; the project owner is the
    # canonical access principal.
    await require_project_access(entry.project_id, actor_user_id, actor_role, db)
    return entry


def require_workflow_owner(resource_owner_id: str, actor_user_id: str, actor_role: str) -> None:
    """Ownership check specialized for workflow resources.

    Semantically identical to `require_owner` but kept as a separate symbol so
    audit logs and future RBAC extensions can distinguish workflow access from
    project/entry access without inspecting call sites.
    """
    require_owner(resource_owner_id, actor_user_id, actor_role)


async def require_extension_access(
    resource_type: str,
    resource_id: str,
    actor_user_id: str,
    actor_role: str,
    required_level: str = 'execute',
) -> None:
    """Verify the actor has `required_level` permission on an extension resource.

    #33 Security governance: RBAC for skills/tools/functions.

    - Admin role bypasses.
    - Otherwise queries `pm_permission` table for user-level or role-level grants.
    - Raises 403 if no matching grant.

    Args:
        resource_type: 'skill' | 'tool' | 'function' | 'workflow'.
        resource_id: The resource's id.
        actor_user_id: The authenticated user's id.
        actor_role: The authenticated user's role.
        required_level: 'read' | 'execute' | 'manage'. Default 'execute' since
            most extension calls are invocations, not reads.

    Raises:
        HTTPException(403): If actor lacks required_level on the resource.
    """
    # Lazy import to avoid circular dependency (acl.py <-> permissions.py)
    from open_webui.models.permissions import Permissions

    ok = await Permissions.check(
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=actor_user_id,
        user_role=actor_role,
        required_level=required_level,
    )
    if not ok:
        log.warning(
            '[ACL] extension access denied: actor=%s role=%s resource=%s:%s required=%s',
            actor_user_id,
            actor_role,
            resource_type,
            resource_id,
            required_level,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'Access denied: no {required_level!r} permission on {resource_type}:{resource_id}.',
        )
