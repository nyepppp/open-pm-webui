"""add pm_audit_log table (#37)

Revision ID: d1e2f3a4b5c6
Revises: c0d1e2f3a4b5
Create Date: 2026-07-23 00:00:01.000000

PM 操作审计日志表. 记录 create/update/delete/execute/grant/revoke 等关键操作.
兼容 SQLite / PostgreSQL (守卫式: 若已存在则跳过).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'c0d1e2f3a4b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建 pm_audit_log 表 + 3 索引 (守卫式)."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'pm_audit_log' not in existing_tables:
        op.create_table(
            'pm_audit_log',
            sa.Column('id', sa.Text(), primary_key=True, nullable=False),
            sa.Column('timestamp', sa.BigInteger(), nullable=True),
            sa.Column('actor_user_id', sa.Text(), nullable=True),
            sa.Column('actor_role', sa.Text(), nullable=True),
            sa.Column('action', sa.Text(), nullable=False),
            sa.Column('resource_type', sa.Text(), nullable=False),
            sa.Column('resource_id', sa.Text(), nullable=True),
            sa.Column('project_id', sa.Text(), nullable=True),
            sa.Column('detail', sa.Text(), nullable=True),
            sa.Column('ip_address', sa.Text(), nullable=True),
            sa.Column('user_agent', sa.Text(), nullable=True),
        )
        op.create_index(
            'ix_pm_audit_log_timestamp',
            'pm_audit_log',
            ['timestamp'],
        )
        op.create_index(
            'ix_pm_audit_log_actor',
            'pm_audit_log',
            ['actor_user_id'],
        )
        op.create_index(
            'ix_pm_audit_log_resource',
            'pm_audit_log',
            ['resource_type', 'resource_id'],
        )


def downgrade() -> None:
    """删索引、删表 (守卫式)."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'pm_audit_log' in existing_tables:
        existing_indexes = {idx['name'] for idx in inspector.get_indexes('pm_audit_log')}
        for idx_name in [
            'ix_pm_audit_log_resource',
            'ix_pm_audit_log_actor',
            'ix_pm_audit_log_timestamp',
        ]:
            if idx_name in existing_indexes:
                op.drop_index(idx_name, table_name='pm_audit_log')
        op.drop_table('pm_audit_log')
