"""add project version link columns

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-07-18 00:00:02.000000

为 PMProject / PMEntry 增加项目版本挂钩列：
- pm_project.current_version_id (Text, nullable)：当前激活的项目版本 ID（pm_version.id）
- pm_entry.project_version_id (Text, nullable, indexed)：条目关联的项目版本 ID

并 backfill 历史数据：
- pm_entry.project_version_id ← pm_entry.data.versionId（JSON 内的 UUID）
- pm_project.current_version_id ← 每个 project 最新一条 pm_version（按 created_at desc）

兼容 SQLite / PostgreSQL：JSON 访问分别用 json_extract / ->> 语法。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e6f7a8b9c0d1'
down_revision: Union[str, None] = 'd5e6f7a8b9c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """加列 + 索引 + backfill 历史数据。"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    dialect = conn.dialect.name

    # 1. pm_project.current_version_id
    project_cols = {c['name'] for c in inspector.get_columns('pm_project')}
    if 'current_version_id' not in project_cols:
        op.add_column(
            'pm_project',
            sa.Column('current_version_id', sa.Text(), nullable=True),
        )

    # 2. pm_entry.project_version_id + 索引
    entry_cols = {c['name'] for c in inspector.get_columns('pm_entry')}
    if 'project_version_id' not in entry_cols:
        op.add_column(
            'pm_entry',
            sa.Column('project_version_id', sa.Text(), nullable=True),
        )

    # 创建索引（守卫：若已存在则跳过）
    existing_indexes = {idx['name'] for idx in inspector.get_indexes('pm_entry')}
    if 'ix_pm_entry_project_version_id' not in existing_indexes:
        op.create_index(
            'ix_pm_entry_project_version_id',
            'pm_entry',
            ['project_version_id'],
        )

    # 3. Backfill pm_entry.project_version_id from data.versionId
    #    SQLite: json_extract(data, '$.versionId')
    #    PostgreSQL: data ->> 'versionId'
    if dialect == 'sqlite':
        conn.execute(sa.text(
            "UPDATE pm_entry SET project_version_id = json_extract(data, '$.versionId') "
            "WHERE project_version_id IS NULL AND data IS NOT NULL "
            "AND json_extract(data, '$.versionId') IS NOT NULL"
        ))
    elif dialect == 'postgresql':
        conn.execute(sa.text(
            "UPDATE pm_entry SET project_version_id = data ->> 'versionId' "
            "WHERE project_version_id IS NULL AND data IS NOT NULL "
            "AND (data ->> 'versionId') IS NOT NULL"
        ))
    # 其他 dialect 跳过 backfill，仅保留空列（不阻断迁移）

    # 4. Backfill pm_project.current_version_id from latest pm_version per project
    #    每个 project 取 created_at 最大的一条 pm_version.id
    if dialect == 'sqlite':
        conn.execute(sa.text(
            "UPDATE pm_project SET current_version_id = ("
            "  SELECT v.id FROM pm_version v "
            "  WHERE v.project_id = pm_project.id "
            "  ORDER BY v.created_at DESC LIMIT 1"
            ") WHERE current_version_id IS NULL "
            "AND EXISTS (SELECT 1 FROM pm_version v WHERE v.project_id = pm_project.id)"
        ))
    elif dialect == 'postgresql':
        conn.execute(sa.text(
            "UPDATE pm_project SET current_version_id = sub.latest_id "
            "FROM ("
            "  SELECT project_id, id AS latest_id "
            "  FROM ("
            "    SELECT id, project_id, "
            "      ROW_NUMBER() OVER (PARTITION BY project_id ORDER BY created_at DESC) AS rn "
            "    FROM pm_version"
            "  ) ranked WHERE rn = 1"
            ") sub "
            "WHERE pm_project.id = sub.project_id "
            "AND pm_project.current_version_id IS NULL"
        ))


def downgrade() -> None:
    """删索引、删列。"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    existing_indexes = {idx['name'] for idx in inspector.get_indexes('pm_entry')}
    if 'ix_pm_entry_project_version_id' in existing_indexes:
        op.drop_index('ix_pm_entry_project_version_id', table_name='pm_entry')

    entry_cols = {c['name'] for c in inspector.get_columns('pm_entry')}
    if 'project_version_id' in entry_cols:
        op.drop_column('pm_entry', 'project_version_id')

    project_cols = {c['name'] for c in inspector.get_columns('pm_project')}
    if 'current_version_id' in project_cols:
        op.drop_column('pm_project', 'current_version_id')
