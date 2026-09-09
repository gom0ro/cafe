"""add linked_table_id to table_bookings (paired tables in one reservation)

Revision ID: 0004_bookings_linked_table
Revises: 0003_table_bookings
Create Date: 2026-09-09
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0004_bookings_linked_table'
down_revision = '0003_table_bookings'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('table_bookings') as batch_op:
        batch_op.add_column(sa.Column('linked_table_id', sa.Integer(), sa.ForeignKey('tables.id', name='fk_table_bookings_linked_table_id'), nullable=True))
    op.create_index('ix_table_bookings_linked_table_id', 'table_bookings', ['linked_table_id'])


def downgrade():
    op.drop_index('ix_table_bookings_linked_table_id', table_name='table_bookings')
    with op.batch_alter_table('table_bookings') as batch_op:
        batch_op.drop_column('linked_table_id')