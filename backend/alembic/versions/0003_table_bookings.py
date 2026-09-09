"""add table_bookings (reservations)

Revision ID: 0003_table_bookings
Revises: 0002_order_lifecycle
Create Date: 2026-09-09
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0003_table_bookings'
down_revision = '0002_order_lifecycle'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'table_bookings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('table_id', sa.Integer(), sa.ForeignKey('tables.id'), nullable=False),
        sa.Column('customer_name', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('guests', sa.Integer(), nullable=True),
        sa.Column('starts_at', sa.DateTime(), nullable=False),
        sa.Column('ends_at', sa.DateTime(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table('table_bookings')