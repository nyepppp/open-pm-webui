"""add pm tables

Revision ID: f2e3d4c5b6a7
Revises: 461111b60977
Create Date: 2026-07-03 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f2e3d4c5b6a7'
down_revision: Union[str, None] = '461111b60977'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # pm_project
    if 'pm_project' not in tables:
        op.create_table(
            'pm_project',
            sa.Column('id', sa.Text(), nullable=False),
            sa.Column('user_id', sa.Text(), nullable=False),
            sa.Column('name', sa.Text(), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('status', sa.Text(), nullable=False, server_default='active'),
            sa.Column('meta', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.BigInteger(), nullable=False),
            sa.Column('updated_at', sa.BigInteger(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )

    # pm_version
    if 'pm_version' not in tables:
        op.create_table(
            'pm_version',
            sa.Column('id', sa.Text(), nullable=False),
            sa.Column('project_id', sa.Text(), nullable=False),
            sa.Column('version_number', sa.Text(), nullable=False),
            sa.Column('label', sa.Text(), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('created_by', sa.Text(), nullable=True),
            sa.Column('created_at', sa.BigInteger(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )

    # pm_entry
    if 'pm_entry' not in tables:
        op.create_table(
            'pm_entry',
            sa.Column('id', sa.Text(), nullable=False),
            sa.Column('user_id', sa.Text(), nullable=False),
            sa.Column('project_id', sa.Text(), nullable=False),
            sa.Column('module_type', sa.Text(), nullable=False),
            sa.Column('title', sa.Text(), nullable=False),
            sa.Column('content', sa.Text(), nullable=True),
            sa.Column('data', sa.JSON(), nullable=True),
            sa.Column('status', sa.Text(), nullable=False, server_default='draft'),
            sa.Column('priority', sa.Text(), nullable=True),
            sa.Column('version', sa.BigInteger(), nullable=False, server_default='1'),
            sa.Column('created_at', sa.BigInteger(), nullable=False),
            sa.Column('updated_at', sa.BigInteger(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )

    # pm_entry_version
    if 'pm_entry_version' not in tables:
        op.create_table(
            'pm_entry_version',
            sa.Column('id', sa.Text(), nullable=False),
            sa.Column('entry_id', sa.Text(), nullable=False),
            sa.Column('project_id', sa.Text(), nullable=False),
            sa.Column('module_type', sa.Text(), nullable=False),
            sa.Column('version_number', sa.Text(), nullable=False),
            sa.Column('content', sa.Text(), nullable=True),
            sa.Column('entry_metadata', sa.JSON(), nullable=True),
            sa.Column('parent_id', sa.Text(), nullable=True),
            sa.Column('branch_name', sa.Text(), nullable=False, server_default='main'),
            sa.Column('change_summary', sa.Text(), nullable=True),
            sa.Column('created_by', sa.Text(), nullable=True),
            sa.Column('created_at', sa.BigInteger(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )

    # pm_entry_branch
    if 'pm_entry_branch' not in tables:
        op.create_table(
            'pm_entry_branch',
            sa.Column('id', sa.Text(), nullable=False),
            sa.Column('project_id', sa.Text(), nullable=False),
            sa.Column('entry_id', sa.Text(), nullable=False),
            sa.Column('name', sa.Text(), nullable=False),
            sa.Column('source_version_id', sa.Text(), nullable=True),
            sa.Column('status', sa.Text(), nullable=False, server_default='active'),
            sa.Column('merged_to_version_id', sa.Text(), nullable=True),
            sa.Column('created_at', sa.BigInteger(), nullable=False),
            sa.Column('updated_at', sa.BigInteger(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )

    # pm_entry_merge
    if 'pm_entry_merge' not in tables:
        op.create_table(
            'pm_entry_merge',
            sa.Column('id', sa.Text(), nullable=False),
            sa.Column('entry_id', sa.Text(), nullable=False),
            sa.Column('branch_id', sa.Text(), nullable=False),
            sa.Column('source_version_id', sa.Text(), nullable=True),
            sa.Column('target_version_id', sa.Text(), nullable=True),
            sa.Column('conflicts', sa.JSON(), nullable=True),
            sa.Column('status', sa.Text(), nullable=False, server_default='pending'),
            sa.Column('resolved_by', sa.Text(), nullable=True),
            sa.Column('merged_at', sa.BigInteger(), nullable=True),
            sa.Column('created_at', sa.BigInteger(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )

    # pm_entity
    if 'pm_entity' not in tables:
        op.create_table(
            'pm_entity',
            sa.Column('id', sa.Text(), nullable=False),
            sa.Column('project_id', sa.Text(), nullable=False),
            sa.Column('type', sa.Text(), nullable=False),
            sa.Column('name', sa.Text(), nullable=False),
            sa.Column('module_id', sa.Text(), nullable=True),
            sa.Column('feature_id', sa.Text(), nullable=True),
            sa.Column('entry_id', sa.Text(), nullable=True),
            sa.Column('entity_metadata', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.BigInteger(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )

    # pm_relation
    if 'pm_relation' not in tables:
        op.create_table(
            'pm_relation',
            sa.Column('id', sa.Text(), nullable=False),
            sa.Column('project_id', sa.Text(), nullable=False),
            sa.Column('entity_a_id', sa.Text(), nullable=False),
            sa.Column('entity_b_id', sa.Text(), nullable=False),
            sa.Column('relation_type', sa.Text(), nullable=False),
            sa.Column('confidence', sa.BigInteger(), nullable=True),
            sa.Column('confirmed', sa.BigInteger(), nullable=False, server_default='0'),
            sa.Column('created_by', sa.Text(), nullable=True),
            sa.Column('version_id', sa.Text(), nullable=True),
            sa.Column('created_at', sa.BigInteger(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )

    # Create indexes
    inspector.clear_cache()
    tables = inspector.get_table_names()

    if 'pm_entry' in tables:
        if not _index_exists(inspector, 'ix_pm_entry_project_module', 'pm_entry'):
            op.create_index('ix_pm_entry_project_module', 'pm_entry', ['project_id', 'module_type'], unique=False)
        if not _index_exists(inspector, 'ix_pm_entry_project', 'pm_entry'):
            op.create_index('ix_pm_entry_project', 'pm_entry', ['project_id'], unique=False)

    if 'pm_entry_version' in tables:
        if not _index_exists(inspector, 'ix_pm_entry_version_entry', 'pm_entry_version'):
            op.create_index('ix_pm_entry_version_entry', 'pm_entry_version', ['entry_id'], unique=False)

    if 'pm_entity' in tables:
        if not _index_exists(inspector, 'ix_pm_entity_project', 'pm_entity'):
            op.create_index('ix_pm_entity_project', 'pm_entity', ['project_id'], unique=False)

    if 'pm_relation' in tables:
        if not _index_exists(inspector, 'ix_pm_relation_project', 'pm_relation'):
            op.create_index('ix_pm_relation_project', 'pm_relation', ['project_id'], unique=False)
        if not _index_exists(inspector, 'ix_pm_relation_entities', 'pm_relation'):
            op.create_index('ix_pm_relation_entities', 'pm_relation', ['entity_a_id', 'entity_b_id'], unique=False)


def _index_exists(inspector, index_name, table_name):
    """Check if an index already exists on the given table."""
    indexes = inspector.get_indexes(table_name)
    return any(idx['name'] == index_name for idx in indexes)


def downgrade() -> None:
    # Drop indexes first
    tables_to_drop = [
        'pm_relation',
        'pm_entity',
        'pm_entry_merge',
        'pm_entry_branch',
        'pm_entry_version',
        'pm_entry',
        'pm_version',
        'pm_project',
    ]
    for table in tables_to_drop:
        op.drop_index(f'ix_{table}_project', table_name=table, if_exists=True)
        op.drop_index(f'ix_{table}_entry', table_name=table, if_exists=True)
        op.drop_index(f'ix_{table}_project_module', table_name=table, if_exists=True)
        op.drop_index(f'ix_{table}_entities', table_name=table, if_exists=True)
        op.drop_table(table, if_exists=True)