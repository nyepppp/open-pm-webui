"""add workflow ownership and execution context columns

Revision ID: b9c0d1e2f3a4
Revises: g8b9c0d1e2f3
Create Date: 2026-07-21 00:00:00.000000

为 pm_workflows 表添加 owner_id / acl 列，为 pm_workflow_executions 表添加
user_id / project_id 列，支持 Issue #29 的 workflow ownership 与执行上下文
追踪。

回填策略 (D4):
- pm_workflows.owner_id: 优先取关联 pm_project.user_id；无关联 project 的
  回退到第一个 admin 用户 id，避免数据孤儿。
- pm_workflows.acl: 默认 '{"read": [], "write": []}'，留待未来 RBAC 扩展。
- pm_workflow_executions.project_id: 通过 workflow_id 关联 pm_workflows.project_id 推导。
- pm_workflow_executions.user_id: 通过 workflow_id 关联 pm_workflows.owner_id 推导。

兼容 SQLite 3.33+ / PostgreSQL（UPDATE ... FROM 子查询语法）。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b9c0d1e2f3a4'
down_revision: Union[str, None] = 'g8b9c0d1e2f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加 workflow ownership + execution context 列并回填。"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 1. pm_workflows 表 — 守卫式 add_column
    if 'pm_workflows' in inspector.get_table_names():
        existing_wf_cols = {c['name'] for c in inspector.get_columns('pm_workflows')}
        if 'owner_id' not in existing_wf_cols:
            op.add_column('pm_workflows', sa.Column('owner_id', sa.Text(), nullable=True))
        if 'acl' not in existing_wf_cols:
            op.add_column('pm_workflows', sa.Column('acl', sa.Text(), nullable=True))

    # 2. pm_workflow_executions 表 — 守卫式 add_column
    if 'pm_workflow_executions' in inspector.get_table_names():
        existing_exec_cols = {c['name'] for c in inspector.get_columns('pm_workflow_executions')}
        if 'user_id' not in existing_exec_cols:
            op.add_column('pm_workflow_executions', sa.Column('user_id', sa.Text(), nullable=True))
        if 'project_id' not in existing_exec_cols:
            op.add_column('pm_workflow_executions', sa.Column('project_id', sa.Text(), nullable=True))

    # 3. 回填 pm_workflows.owner_id
    # 优先用关联 pm_project.user_id；无 project 的回退到第一个 admin。
    # COALESCE + 标量子查询在 SQLite 3.33+ 与 PostgreSQL 均支持。
    op.execute("""
        UPDATE pm_workflows
        SET owner_id = COALESCE(
            (SELECT p.user_id FROM pm_project p WHERE p.id = pm_workflows.project_id),
            (SELECT u.id FROM users u WHERE u.role = 'admin' ORDER BY u.created_at LIMIT 1)
        )
        WHERE owner_id IS NULL
    """)

    # 4. 回填 pm_workflows.acl 默认值
    op.execute("""
        UPDATE pm_workflows
        SET acl = '{"read": [], "write": []}'
        WHERE acl IS NULL
    """)

    # 5. 回填 pm_workflow_executions.project_id（通过 workflow_id → pm_workflows.project_id）
    op.execute("""
        UPDATE pm_workflow_executions
        SET project_id = (
            SELECT w.project_id FROM pm_workflows w
            WHERE w.id = pm_workflow_executions.workflow_id
        )
        WHERE project_id IS NULL
    """)

    # 6. 回填 pm_workflow_executions.user_id（通过 workflow_id → pm_workflows.owner_id）
    op.execute("""
        UPDATE pm_workflow_executions
        SET user_id = (
            SELECT w.owner_id FROM pm_workflows w
            WHERE w.id = pm_workflow_executions.workflow_id
        )
        WHERE user_id IS NULL
    """)


def downgrade() -> None:
    """回滚 workflow ownership + execution context 列。"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'pm_workflow_executions' in inspector.get_table_names():
        existing_exec_cols = {c['name'] for c in inspector.get_columns('pm_workflow_executions')}
        if 'user_id' in existing_exec_cols:
            op.drop_column('pm_workflow_executions', 'user_id')
        if 'project_id' in existing_exec_cols:
            op.drop_column('pm_workflow_executions', 'project_id')

    if 'pm_workflows' in inspector.get_table_names():
        existing_wf_cols = {c['name'] for c in inspector.get_columns('pm_workflows')}
        if 'acl' in existing_wf_cols:
            op.drop_column('pm_workflows', 'acl')
        if 'owner_id' in existing_wf_cols:
            op.drop_column('pm_workflows', 'owner_id')
