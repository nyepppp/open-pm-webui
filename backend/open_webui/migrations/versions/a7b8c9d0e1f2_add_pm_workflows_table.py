"""add pm_workflows tables

Revision ID: a7b8c9d0e1f2
Revises: 63238cd619f8
Create Date: 2026-07-17 00:00:00.000000

Creates the pm_workflows, pm_workflow_nodes, pm_workflow_edges, and
pm_workflow_executions tables that back the PM workspace workflow designer.
Previously these tables were created only via Base.metadata.create_all,
which left migration-based environments (CI, fresh prod, Docker cold start
without create_all) without them.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, None] = '63238cd619f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # pm_workflows
    if 'pm_workflows' not in tables:
        op.create_table(
            'pm_workflows',
            sa.Column('id', sa.Text(), nullable=False),
            sa.Column('name', sa.Text(), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('project_id', sa.Text(), nullable=True),
            sa.Column('status', sa.Text(), nullable=True, server_default='draft'),
            sa.Column('nodes', sa.Text(), nullable=True, server_default='[]'),
            sa.Column('edges', sa.Text(), nullable=True, server_default='[]'),
            sa.Column('execution_history', sa.Text(), nullable=True, server_default='[]'),
            sa.Column('created_at', sa.BigInteger(), nullable=False),
            sa.Column('updated_at', sa.BigInteger(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )

    # pm_workflow_nodes
    if 'pm_workflow_nodes' not in tables:
        op.create_table(
            'pm_workflow_nodes',
            sa.Column('id', sa.Text(), nullable=False),
            sa.Column('workflow_id', sa.Text(), nullable=False),
            sa.Column('type', sa.Text(), nullable=False),
            sa.Column('name', sa.Text(), nullable=False),
            sa.Column('position_x', sa.Float(), nullable=True, server_default='0.0'),
            sa.Column('position_y', sa.Float(), nullable=True, server_default='0.0'),
            sa.Column('config', sa.Text(), nullable=True, server_default='{}'),
            sa.Column('input_schema', sa.Text(), nullable=True),
            sa.Column('output_schema', sa.Text(), nullable=True),
            sa.Column('script', sa.Text(), nullable=True),
            sa.Column('skill_id', sa.Text(), nullable=True),
            sa.Column('created_at', sa.BigInteger(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )

    # pm_workflow_edges
    if 'pm_workflow_edges' not in tables:
        op.create_table(
            'pm_workflow_edges',
            sa.Column('id', sa.Text(), nullable=False),
            sa.Column('workflow_id', sa.Text(), nullable=False),
            sa.Column('source_node_id', sa.Text(), nullable=False),
            sa.Column('target_node_id', sa.Text(), nullable=False),
            sa.Column('data_mapping_rules', sa.Text(), nullable=True, server_default='{}'),
            sa.Column('label', sa.Text(), nullable=True),
            sa.Column('created_at', sa.BigInteger(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )

    # pm_workflow_executions
    if 'pm_workflow_executions' not in tables:
        op.create_table(
            'pm_workflow_executions',
            sa.Column('id', sa.Text(), nullable=False),
            sa.Column('workflow_id', sa.Text(), nullable=False),
            sa.Column('status', sa.Text(), nullable=True, server_default='pending'),
            sa.Column('input_data', sa.Text(), nullable=True, server_default='{}'),
            sa.Column('output_data', sa.Text(), nullable=True, server_default='{}'),
            sa.Column('node_states', sa.Text(), nullable=True, server_default='[]'),
            sa.Column('logs', sa.Text(), nullable=True, server_default='[]'),
            sa.Column('started_at', sa.BigInteger(), nullable=False),
            sa.Column('completed_at', sa.BigInteger(), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )

    # Add indexes for common lookups
    inspector.clear_cache()
    tables = inspector.get_table_names()

    if 'pm_workflows' in tables:
        if not _index_exists(inspector, 'ix_pm_workflows_project', 'pm_workflows'):
            op.create_index('ix_pm_workflows_project', 'pm_workflows', ['project_id'], unique=False)

    if 'pm_workflow_nodes' in tables:
        if not _index_exists(inspector, 'ix_pm_workflow_nodes_workflow', 'pm_workflow_nodes'):
            op.create_index('ix_pm_workflow_nodes_workflow', 'pm_workflow_nodes', ['workflow_id'], unique=False)

    if 'pm_workflow_edges' in tables:
        if not _index_exists(inspector, 'ix_pm_workflow_edges_workflow', 'pm_workflow_edges'):
            op.create_index('ix_pm_workflow_edges_workflow', 'pm_workflow_edges', ['workflow_id'], unique=False)

    if 'pm_workflow_executions' in tables:
        if not _index_exists(inspector, 'ix_pm_workflow_executions_workflow', 'pm_workflow_executions'):
            op.create_index('ix_pm_workflow_executions_workflow', 'pm_workflow_executions', ['workflow_id'], unique=False)


def _index_exists(inspector, index_name, table_name):
    """Check if an index already exists on the given table."""
    indexes = inspector.get_indexes(table_name)
    return any(idx['name'] == index_name for idx in indexes)


def downgrade() -> None:
    # Drop indexes first, then tables in reverse dependency order
    for table in ['pm_workflow_executions', 'pm_workflow_edges', 'pm_workflow_nodes', 'pm_workflows']:
        op.drop_index(f'ix_{table}_workflow', table_name=table, if_exists=True)
        op.drop_index(f'ix_{table}_project', table_name=table, if_exists=True)
        op.drop_table(table, if_exists=True)
