"""add pm_annotation table

Revision ID: a1b2c3d4e5f6
Revises: f2e3d4c5b6a7
Create Date: 2026-07-05 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f2e3d4c5b6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # pm_annotation
    if 'pm_annotation' not in tables:
        op.create_table(
            'pm_annotation',
            sa.Column('id', sa.Text(), nullable=False),
            sa.Column('entry_id', sa.Text(), nullable=False),
            sa.Column('project_id', sa.Text(), nullable=False),
            sa.Column('annotation_type', sa.Text(), nullable=False),
            sa.Column('content', sa.Text(), nullable=True),
            sa.Column('source_data', sa.JSON(), nullable=True),
            sa.Column('format_template', sa.Text(), nullable=True),
            sa.Column('created_by', sa.Text(), nullable=True),
            sa.Column('created_at', sa.BigInteger(), nullable=False),
            sa.Column('updated_at', sa.BigInteger(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )
        # Create indexes
        op.create_index('ix_pm_annotation_entry', 'pm_annotation', ['entry_id'], unique=False)
        op.create_index('ix_pm_annotation_project', 'pm_annotation', ['project_id'], unique=False)
        op.create_index('ix_pm_annotation_type', 'pm_annotation', ['annotation_type'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_pm_annotation_type', table_name='pm_annotation', if_exists=True)
    op.drop_index('ix_pm_annotation_project', table_name='pm_annotation', if_exists=True)
    op.drop_index('ix_pm_annotation_entry', table_name='pm_annotation', if_exists=True)
    op.drop_table('pm_annotation', if_exists=True)