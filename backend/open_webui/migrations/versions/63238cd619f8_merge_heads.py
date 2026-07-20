"""merge heads

Revision ID: 63238cd619f8
Revises: 3c9b0ca343fd, f1e2d3c4b5a6
Create Date: 2026-07-12 17:10:16.759029

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db


# revision identifiers, used by Alembic.
revision: str = '63238cd619f8'
down_revision: Union[str, None] = ('3c9b0ca343fd', 'f1e2d3c4b5a6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
