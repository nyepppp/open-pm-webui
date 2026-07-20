"""add partial unique constraint on pm_project (user_id, name) for active rows

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-07-17 00:00:02.000000

Adds a partial unique index on `pm_project(user_id, name)` excluding rows
whose `status = 'archived'`. This prevents duplicate active project names
per user while still allowing a user to:
  - Create a new project with the same name as a previously archived one
  - Archive a project and create a new one with the same name

Both SQLite and PostgreSQL support partial indexes via `CREATE UNIQUE INDEX
... WHERE`. The SQL syntax used here is intentionally compatible with both.
"""

from typing import Sequence, Union

from alembic import op


revision: str = 'c9d0e1f2a3b4'
down_revision: Union[str, None] = 'b8c9d0e1f2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


INDEX_NAME = 'uq_pm_project_user_name_active'


def upgrade() -> None:
    """Create the partial unique index if it does not exist.

    先归档重复的 active 行（每个 user_id+name 组合保留 updated_at 最新的一行，
    其余设为 'archived'），再创建部分唯一索引。这样既不删除数据，又能满足
    WHERE status != 'archived' 的唯一约束。兼容 SQLite 与 PostgreSQL。
    """
    # 归档重复行：使用窗口函数找出每组（user_id, name）中除最新一行外的 active 行
    op.execute(
        """
        UPDATE pm_project
        SET status = 'archived'
        WHERE id IN (
            SELECT id FROM (
                SELECT id,
                       ROW_NUMBER() OVER (
                           PARTITION BY user_id, name
                           ORDER BY updated_at DESC, id DESC
                       ) AS rn
                FROM pm_project
                WHERE status != 'archived'
            )
            WHERE rn > 1
        )
        """
    )

    # 创建部分唯一索引（排除已归档行）
    op.execute(
        f"CREATE UNIQUE INDEX IF NOT EXISTS {INDEX_NAME} "
        "ON pm_project (user_id, name) "
        "WHERE status != 'archived'"
    )


def downgrade() -> None:
    """Drop the partial unique index."""
    op.execute(f"DROP INDEX IF EXISTS {INDEX_NAME}")
