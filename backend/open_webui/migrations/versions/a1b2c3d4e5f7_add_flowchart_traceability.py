"""add flowchart traceability table

Revision ID: a1b2c3d4e5f7
Revises: f2e3d4c5b6a7
Create Date: 2026-07-06 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f7'
down_revision: Union[str, None] = 'f2e3d4c5b6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # pm_flowchart_traceability
    if 'pm_flowchart_traceability' not in tables:
        op.create_table(
            'pm_flowchart_traceability',
            sa.Column('id', sa.Text(), nullable=False),
            sa.Column('node_id', sa.Text(), nullable=False),
            sa.Column('flowchart_id', sa.Text(), nullable=False),
            sa.Column('entity_type', sa.Text(), nullable=False),
            sa.Column('entity_id', sa.Text(), nullable=False),
            sa.Column('entity_name', sa.Text(), nullable=True),
            sa.Column('version_id', sa.Text(), nullable=True),
            sa.Column('version_number', sa.Text(), nullable=True),
            sa.Column('bound_at', sa.BigInteger(), nullable=False),
            sa.Column('bound_by', sa.Text(), nullable=True),
            sa.Column('created_at', sa.BigInteger(), nullable=False),
            sa.Column('updated_at', sa.BigInteger(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )

    # Create indexes
    inspector.clear_cache()
    tables = inspector.get_table_names()

    if 'pm_flowchart_traceability' in tables:
        if not _index_exists(inspector, 'ix_pm_traceability_flowchart', 'pm_flowchart_traceability'):
            op.create_index('ix_pm_traceability_flowchart', 'pm_flowchart_traceability', ['flowchart_id'], unique=False)
        if not _index_exists(inspector, 'ix_pm_traceability_node', 'pm_flowchart_traceability'):
            op.create_index('ix_pm_traceability_node', 'pm_flowchart_traceability', ['node_id'], unique=False)
        if not _index_exists(inspector, 'ix_pm_traceability_entity', 'pm_flowchart_traceability'):
            op.create_index('ix_pm_traceability_entity', 'pm_flowchart_traceability', ['entity_type', 'entity_id'], unique=False)


def _index_exists(inspector, index_name, table_name):
    """Check if an index already exists on the given table."""
    indexes = inspector.get_indexes(table_name)
    return any(idx['name'] == index_name for idx in indexes)


def downgrade() -> None:
    op.drop_index('ix_pm_traceability_flowchart', table_name='pm_flowchart_traceability', if_exists=True)
    op.drop_index('ix_pm_traceability_node', table_name='pm_flowchart_traceability', if_exists=True)
    op.drop_index('ix_pm_traceability_entity', table_name='pm_flowchart_traceability', if_exists=True)
    op.drop_table('pm_flowchart_traceability', if_exists=True)
