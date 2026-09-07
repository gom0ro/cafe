"""initial migration

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-09
"""
from alembic import op
import sqlalchemy as sa
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from app import models

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    models.Base.metadata.create_all(bind=bind)


def downgrade():
    bind = op.get_bind()
    models.Base.metadata.drop_all(bind=bind)
