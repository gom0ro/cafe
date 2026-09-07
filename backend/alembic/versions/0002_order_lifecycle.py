"""add tables, shifts, audit_logs and order lifecycle columns

Revision ID: 0002_order_lifecycle
Revises: 0001_initial
Create Date: 2026-09-03
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_order_lifecycle'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'tables',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('number', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('seats', sa.Integer(), nullable=True),
        sa.Column('zone', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
    )

    op.create_table(
        'shifts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('opening_balance', sa.Float(), nullable=True),
        sa.Column('closing_balance', sa.Float(), nullable=True),
        sa.Column('expected_cash', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
    )

    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('entity', sa.String(), nullable=True),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('detail', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

    op.add_column('orders', sa.Column('notes', sa.Text(), nullable=True))
    op.add_column('orders', sa.Column('table_id', sa.Integer(), sa.ForeignKey('tables.id'), nullable=True))
    op.add_column('orders', sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True))
    op.add_column('orders', sa.Column('shift_id', sa.Integer(), sa.ForeignKey('shifts.id'), nullable=True))
    op.add_column('orders', sa.Column('payment_method', sa.String(), nullable=True))
    op.add_column('orders', sa.Column('paid_at', sa.DateTime(), nullable=True))
    op.add_column('orders', sa.Column('closed_at', sa.DateTime(), nullable=True))


def downgrade():
    for col in ('closed_at', 'paid_at', 'payment_method', 'shift_id', 'user_id', 'table_id', 'notes'):
        op.drop_column('orders', col)
    op.drop_table('audit_logs')
    op.drop_table('shifts')
    op.drop_table('tables')
