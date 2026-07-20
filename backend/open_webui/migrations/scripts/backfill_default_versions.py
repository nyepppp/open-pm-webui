"""一次性迁移脚本：为 current_version_id IS NULL 的 PM 项目批量补建 v1 默认版本。

背景：
    D28 修复（routers/pm.py:118-158）在新项目创建时会自动建 v1 版本。
    但所有在 D28 部署前创建的项目都不会有默认版本，导致：
    - versions 页面显示「0 个版本」
    - PRD 保存时 currentVersion 为 null，链路脆弱（Bug 1 根因）

使用：
    cd backend
    python -m open_webui.migrations.scripts.backfill_default_versions
    # 或
    python open_webui/migrations/scripts/backfill_default_versions.py

幂等性：
    脚本可重复运行。已补建的项目 current_version_id 不为 NULL，会被跳过。

输出：
    扫描 N 个项目，成功补建 M 个，失败 K 个（附失败列表）
"""
import asyncio
import os
import sys
import traceback


async def backfill() -> None:
    # 让 backend/ 成为 sys.path 第一项，便于 import open_webui.*
    backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
    if backend_root not in sys.path:
        sys.path.insert(0, backend_root)

    # 初始化 secret key（防止 config.py 报错）
    secret_key_path = os.path.join(backend_root, '.webui_secret_key')
    if os.path.exists(secret_key_path) and 'WEBUI_SECRET_KEY' not in os.environ:
        with open(secret_key_path, 'r') as f:
            os.environ['WEBUI_SECRET_KEY'] = f.read().strip()

    from sqlalchemy import select, update
    from sqlalchemy.exc import SQLAlchemyError

    from open_webui.internal.db import get_async_db
    from open_webui.models.pm import (
        PMProject,
        PMVersion,
    )

    print('=' * 70)
    print('PM 默认版本回填迁移')
    print('=' * 70)

    async with get_async_db() as db:
        # 1. 扫描所有 current_version_id IS NULL 的项目
        result = await db.execute(
            select(PMProject).where(PMProject.current_version_id.is_(None))
        )
        orphan_projects = result.scalars().all()

        total = len(orphan_projects)
        print(f'\n扫描到 {total} 个 current_version_id 为 NULL 的项目')

        if total == 0:
            print('无需迁移，退出。')
            return

        succeeded = []
        failed = []

        for idx, project in enumerate(orphan_projects, start=1):
            project_id = project.id
            project_name = getattr(project, 'name', '<unknown>')
            print(f'\n[{idx}/{total}] 处理项目: {project_id} ({project_name})')

            try:
                # 2. 创建 v1 版本（直接构造 ORM 对象，避免 insert_new_version 的 session 复用复杂性）
                import time
                import uuid

                new_version = PMVersion(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    version_number='v1',
                    label=None,
                    description='初始版本（迁移补建）',
                    created_by=project.user_id,
                    created_at=int(time.time_ns()),
                )
                db.add(new_version)
                await db.flush()  # 拿到 new_version.id

                # 3. 回填 project.current_version_id
                await db.execute(
                    update(PMProject)
                    .where(PMProject.id == project_id)
                    .values(
                        current_version_id=new_version.id,
                        updated_at=int(time.time_ns()),
                    )
                )
                await db.commit()

                print(f'  ✓ 已创建版本 v1 (id={new_version.id}) 并关联到项目')
                succeeded.append({'project_id': project_id, 'project_name': project_name, 'version_id': new_version.id})

            except SQLAlchemyError as e:
                await db.rollback()
                print(f'  ✗ DB 错误: {e}')
                traceback.print_exc()
                failed.append({'project_id': project_id, 'project_name': project_name, 'error': f'SQLAlchemyError: {e}'})
            except Exception as e:
                await db.rollback()
                print(f'  ✗ 未知错误: {e}')
                traceback.print_exc()
                failed.append({'project_id': project_id, 'project_name': project_name, 'error': f'{type(e).__name__}: {e}'})

        # 4. 输出统计
        print('\n' + '=' * 70)
        print('迁移完成')
        print('=' * 70)
        print(f'扫描总数: {total}')
        print(f'成功补建: {len(succeeded)}')
        print(f'失败:     {len(failed)}')

        if failed:
            print('\n失败列表:')
            for f in failed:
                print(f"  - project_id={f['project_id']} ({f['project_name']}): {f['error']}")

        if succeeded:
            print('\n成功列表（前 10 条）:')
            for s in succeeded[:10]:
                print(f"  - project_id={s['project_id']} ({s['project_name']}): version_id={s['version_id']}")
            if len(succeeded) > 10:
                print(f'  ... 共 {len(succeeded)} 条')


def main() -> None:
    asyncio.run(backfill())


if __name__ == '__main__':
    main()
