"""merge_flowchart_traceability_head

Revision ID: 97e824ef8ab0
Revises: a1b2c3d4e5f7, g8b9c0d1e2f3
Create Date: 2026-07-18 22:15:11.839392

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db


# revision identifiers, used by Alembic.
revision: str = '97e824ef8ab0'
down_revision: Union[str, None] = ('a1b2c3d4e5f7', 'g8b9c0d1e2f3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
