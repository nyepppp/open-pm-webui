"""add created_version_number to pm_entry

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-07-17 00:00:01.000000

Adds the `created_version_number` column to `pm_entry`, persisting the
version number at which the entry was originally created. Previously this
information was lost because only `current_version_number` (computed from
the latest version) was exposed.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b8c9d0e1f2a3'
down_revision: Union[str, None] = 'a7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('pm_entry')]

    if 'created_version_number' not in columns:
        op.add_column(
            'pm_entry',
            sa.Column('created_version_number', sa.Text(), nullable=True),
        )

    # Backfill existing rows with 'v1' (matches the value set by create_entry
    # for the initial entry version).
    op.execute(
        "UPDATE pm_entry SET created_version_number = 'v1' "
        "WHERE created_version_number IS NULL"
    )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('pm_entry')]
    if 'created_version_number' in columns:
        op.drop_column('pm_entry', 'created_version_number')
