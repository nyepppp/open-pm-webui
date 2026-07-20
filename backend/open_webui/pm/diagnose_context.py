"""PM 上下文注入诊断脚本。

用法：
    cd backend
    $env:WEBUI_SECRET_KEY="test-secret-key-for-import-check-only"
    python -m open_webui.pm.diagnose_context <project_id> <user_id>

也可不传参，自动查找第一个 admin 用户和名为 'ces' 的项目：
    python -m open_webui.pm.diagnose_context
"""

import asyncio
import sys
from typing import Optional

from open_webui.models.pm import PMEntries, PMProjects
from open_webui.models.users import Users
from open_webui.pm.chat_context import build_pm_context_system_message


async def _find_admin_user():
    """查找第一个 admin 用户。"""
    from open_webui.internal.db import get_async_db_context
    from sqlalchemy import select
    from open_webui.models.users import User

    async with get_async_db_context() as db:
        result = await db.execute(select(User).where(User.role == 'admin').limit(1))
        user = result.scalar_one_or_none()
        if user:
            return await Users.get_user_by_id(user.id)
    return None


async def _find_project_by_name(name: str):
    """查找第一个匹配名称的项目。"""
    from open_webui.internal.db import get_async_db_context
    from sqlalchemy import select
    from open_webui.models.pm import PMProject

    async with get_async_db_context() as db:
        result = await db.execute(select(PMProject).where(PMProject.name == name).limit(1))
        project = result.scalar_one_or_none()
        if project:
            return await PMProjects.get_project_by_id(project.id)
    return None


async def _find_any_project():
    """查找第一个项目。"""
    from open_webui.internal.db import get_async_db_context
    from sqlalchemy import select
    from open_webui.models.pm import PMProject

    async with get_async_db_context() as db:
        result = await db.execute(select(PMProject).limit(1))
        project = result.scalar_one_or_none()
        if project:
            return await PMProjects.get_project_by_id(project.id)
    return None


async def main(project_id: Optional[str] = None, user_id: Optional[str] = None):
    print('=' * 60)
    print('PM Context Injection Diagnostics')
    print('=' * 60)

    # 1. 解析 user
    if user_id:
        user = await Users.get_user_by_id(user_id)
        if not user:
            print(f'ERROR: User {user_id} not found')
            return
    else:
        print('No user_id provided, auto-finding first admin user...')
        user = await _find_admin_user()
        if not user:
            print('ERROR: No admin user found in DB')
            return

    print(f'User: id={user.id}, email={user.email}, role={user.role}')

    # 2. 解析 project
    if project_id:
        project = await PMProjects.get_project_by_id(project_id)
        if not project:
            print(f'ERROR: Project {project_id} not found')
            return
    else:
        print('No project_id provided, auto-finding project "ces"...')
        project = await _find_project_by_name('ces')
        if not project:
            print('Project "ces" not found, finding any project...')
            project = await _find_any_project()
        if not project:
            print('ERROR: No project found in DB')
            return

    print(f'Project: id={project.id}, name={project.name}, user_id={project.user_id}')
    print(f'Access check: project.user_id == user.id -> {project.user_id == user.id}')

    # 3. 列出项目条目
    entries = await PMEntries.get_entries_by_project_id(project.id)
    print(f'Entries count: {len(entries)}')
    if entries:
        # 按 module_type 分组统计
        from collections import Counter
        module_counts = Counter(e.module_type for e in entries)
        print('Entries by module:')
        for mod, count in module_counts.most_common():
            print(f'  {mod}: {count}')

    # 4. 调用 build_pm_context_system_message
    print()
    print('-' * 60)
    print('Calling build_pm_context_system_message...')
    try:
        msg = await build_pm_context_system_message(project.id, user)
        if msg:
            print(f'SUCCESS: System message length={len(msg)}')
            print('--- First 800 chars ---')
            print(msg[:800])
            if len(msg) > 800:
                print(f'... ({len(msg) - 800} more chars)')
        else:
            print('FAILED: build_pm_context_system_message returned None')
            print('Possible causes:')
            print('  1. project.user_id != user.id (access denied)')
            print('  2. project not found in DB')
            print('  3. exception in _verify_project_access (check logs)')
    except Exception as e:
        print(f'EXCEPTION: {type(e).__name__}: {e}')
        import traceback
        traceback.print_exc()

    print()
    print('=' * 60)
    print('Diagnostics complete')


if __name__ == '__main__':
    pid = sys.argv[1] if len(sys.argv) > 1 else None
    uid = sys.argv[2] if len(sys.argv) > 2 else None
    asyncio.run(main(pid, uid))
