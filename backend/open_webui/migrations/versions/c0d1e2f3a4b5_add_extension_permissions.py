"""add pm_permission table for extension RBAC (#33)

Revision ID: c0d1e2f3a4b5
Revises: b9c0d1e2f3a4
Create Date: 2026-07-22 00:00:01.000000

扩展资源 (skills/tools/functions/workflows) RBAC 权限表.
支持 user 级 + role 级 grant, admin bypass 由 acl.py 在运行时判定.

兼容 SQLite / PostgreSQL (守卫式: 若已存在则跳过).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c0d1e2f3a4b5'
down_revision: Union[str, None] = 'b9c0d1e2f3a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建 pm_permission 表 + 索引 (守卫式)."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'pm_permission' not in existing_tables:
        op.create_table(
            'pm_permission',
            sa.Column('id', sa.Text(), primary_key=True, nullable=False),
            sa.Column('resource_type', sa.Text(), nullable=False),
            sa.Column('resource_id', sa.Text(), nullable=False),
            sa.Column('principal_type', sa.Text(), nullable=False),
            sa.Column('principal_id', sa.Text(), nullable=False),
            sa.Column('level', sa.Text(), nullable=False, server_default='read'),
            sa.Column('granted_by', sa.Text(), nullable=True),
            sa.Column('created_at', sa.BigInteger(), nullable=True),
        )
        op.create_index(
            'ix_pm_permission_resource',
            'pm_permission',
            ['resource_type', 'resource_id'],
        )
        op.create_index(
            'ix_pm_permission_principal',
            'pm_permission',
            ['principal_type', 'principal_id'],
        )
        # 默认 backfill: admin role 对所有 'tool' / 'function' 资源拥有 manage 权限
        # 实际现有资源 id 需要在 router 启动时由 admin 主动 grant, 这里不自动 backfill
        # 因为 backfill 需要枚举所有现有 skill/tool/function id, 留给运维或后续脚本


def downgrade() -> None:
    """删索引、删表 (守卫式)."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'pm_permission' in existing_tables:
        existing_indexes = {idx['name'] for idx in inspector.get_indexes('pm_permission')}
        if 'ix_pm_permission_principal' in existing_indexes:
            op.drop_index('ix_pm_permission_principal', table_name='pm_permission')
        if 'ix_pm_permission_resource' in existing_indexes:
            op.drop_index('ix_pm_permission_resource', table_name='pm_permission')
        op.drop_table('pm_permission')
