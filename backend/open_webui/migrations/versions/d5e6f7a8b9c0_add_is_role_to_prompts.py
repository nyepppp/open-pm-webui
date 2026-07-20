"""add is_role to prompts

Revision ID: d5e6f7a8b9c0
Revises: c9d0e1f2a3b4
Create Date: 2026-07-18 00:00:01.000000

为 prompt 表新增 is_role 列：
- is_role BOOLEAN NOT NULL DEFAULT FALSE
- True 表示该 prompt 作为"角色提示词"使用（Part B：AI 创建工作流 + 角色提示词）
- data 字段存储角色配置（system_prompt / tools / suggested_models 等结构化字段）

兼容 SQLite / PostgreSQL：两者都支持 IF NOT EXISTS 风格的列添加守卫。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd5e6f7a8b9c0'
down_revision: Union[str, None] = 'c9d0e1f2a3b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加 is_role 列到 prompt 表。"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    prompt_cols = {c['name'] for c in inspector.get_columns('prompt')}

    if 'is_role' not in prompt_cols:
        # 默认 False，已存在的普通 prompt 不会被当作角色
        op.add_column('prompt', sa.Column('is_role', sa.Boolean(), nullable=False, server_default=sa.text('false')))


def downgrade() -> None:
    """移除 is_role 列。"""
    op.drop_column('prompt', 'is_role')
