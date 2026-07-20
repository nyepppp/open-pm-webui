"""add pm_module_version table and module_version_id column to pm_entry

Revision ID: g8b9c0d1e2f3
Revises: f7a8b9c0d1e2
Create Date: 2026-07-18 00:00:04.000000

新增模块版本表 pm_module_version + 给 pm_entry 增加 module_version_id 列（带索引），
支持产品架构模块的多版本管理。

兼容 SQLite / PostgreSQL。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'g8b9c0d1e2f3'
down_revision: Union[str, None] = 'f7a8b9c0d1e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建 pm_module_version 表 + 给 pm_entry 加 module_version_id 列。"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 1. 创建 pm_module_version 表（守卫式：若已存在则跳过）
    existing_tables = inspector.get_table_names()
    if 'pm_module_version' not in existing_tables:
        op.create_table(
            'pm_module_version',
            sa.Column('id', sa.Text(), primary_key=True, nullable=False),
            sa.Column('project_id', sa.Text(), nullable=False),
            sa.Column('module_entry_id', sa.Text(), nullable=False),
            sa.Column('version_number', sa.Text(), nullable=False),
            sa.Column('change_summary', sa.Text(), nullable=True),
            sa.Column('created_by', sa.Text(), nullable=True),
            sa.Column('created_at', sa.BigInteger(), nullable=True),
            sa.Column('project_version_id', sa.Text(), nullable=True),
        )
        # module_entry_id 索引（便于按模块查版本列表）
        op.create_index(
            'ix_pm_module_version_module_entry_id',
            'pm_module_version',
            ['module_entry_id'],
        )

    # 2. 给 pm_entry 加 module_version_id 列 + 索引（守卫式）
    entry_cols = {c['name'] for c in inspector.get_columns('pm_entry')}
    if 'module_version_id' not in entry_cols:
        op.add_column(
            'pm_entry',
            sa.Column('module_version_id', sa.Text(), nullable=True),
        )

    existing_indexes = {idx['name'] for idx in inspector.get_indexes('pm_entry')}
    if 'ix_pm_entry_module_version_id' not in existing_indexes:
        op.create_index(
            'ix_pm_entry_module_version_id',
            'pm_entry',
            ['module_version_id'],
        )


def downgrade() -> None:
    """删索引、删列、删表。"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    existing_indexes = {idx['name'] for idx in inspector.get_indexes('pm_entry')}
    if 'ix_pm_entry_module_version_id' in existing_indexes:
        op.drop_index('ix_pm_entry_module_version_id', table_name='pm_entry')

    entry_cols = {c['name'] for c in inspector.get_columns('pm_entry')}
    if 'module_version_id' in entry_cols:
        op.drop_column('pm_entry', 'module_version_id')

    existing_tables = inspector.get_table_names()
    if 'pm_module_version' in existing_tables:
        existing_indexes = {idx['name'] for idx in inspector.get_indexes('pm_module_version')}
        if 'ix_pm_module_version_module_entry_id' in existing_indexes:
            op.drop_index('ix_pm_module_version_module_entry_id', table_name='pm_module_version')
        op.drop_table('pm_module_version')
