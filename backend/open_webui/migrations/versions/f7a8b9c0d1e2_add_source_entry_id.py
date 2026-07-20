"""add source_entry_id column to pm_entry

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-07-18 00:00:03.000000

为 PMEntry 增加 source_entry_id 列（派生源条目 ID），并 backfill 历史数据：
- pm_entry.source_entry_id (Text, nullable, indexed)
- Backfill：遍历 pm_relation 中 relation_type='derives' 的记录，
  通过 pm_entity 反查 entry_id，把源 entity 的 entry_id 写入派生 entry 的 source_entry_id。

兼容 SQLite / PostgreSQL。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f7a8b9c0d1e2'
down_revision: Union[str, None] = 'e6f7a8b9c0d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """加列 + 索引 + backfill 历史数据。"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 1. pm_entry.source_entry_id + 索引（守卫式）
    entry_cols = {c['name'] for c in inspector.get_columns('pm_entry')}
    if 'source_entry_id' not in entry_cols:
        op.add_column(
            'pm_entry',
            sa.Column('source_entry_id', sa.Text(), nullable=True),
        )

    existing_indexes = {idx['name'] for idx in inspector.get_indexes('pm_entry')}
    if 'ix_pm_entry_source_entry_id' not in existing_indexes:
        op.create_index(
            'ix_pm_entry_source_entry_id',
            'pm_entry',
            ['source_entry_id'],
        )

    # 2. Backfill pm_entry.source_entry_id from pm_relation (relation_type='derives')
    #    逻辑：对于每条 pm_entry，若它作为派生目标（pm_entity.entry_id = pm_entry.id），
    #    且存在 pm_relation 关系 relation_type='derives'，entity_b_id = 该 entity.id，
    #    则把 source_entry_id 设为 entity_a_id 对应 entity 的 entry_id。
    #
    #    SQLite / PostgreSQL 语法一致（标准 SQL 子查询）。
    conn.execute(sa.text(
        """
        UPDATE pm_entry
        SET source_entry_id = (
            SELECT src_entity.entry_id
            FROM pm_relation r
            JOIN pm_entity dst_entity ON dst_entity.id = r.entity_b_id
            JOIN pm_entity src_entity ON src_entity.id = r.entity_a_id
            WHERE dst_entity.entry_id = pm_entry.id
              AND r.relation_type = 'derives'
              AND src_entity.entry_id IS NOT NULL
            LIMIT 1
        )
        WHERE source_entry_id IS NULL
          AND EXISTS (
            SELECT 1 FROM pm_relation r
            JOIN pm_entity dst_entity ON dst_entity.id = r.entity_b_id
            WHERE dst_entity.entry_id = pm_entry.id
              AND r.relation_type = 'derives'
          )
        """
    ))


def downgrade() -> None:
    """删索引、删列。"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    existing_indexes = {idx['name'] for idx in inspector.get_indexes('pm_entry')}
    if 'ix_pm_entry_source_entry_id' in existing_indexes:
        op.drop_index('ix_pm_entry_source_entry_id', table_name='pm_entry')

    entry_cols = {c['name'] for c in inspector.get_columns('pm_entry')}
    if 'source_entry_id' in entry_cols:
        op.drop_column('pm_entry', 'source_entry_id')
