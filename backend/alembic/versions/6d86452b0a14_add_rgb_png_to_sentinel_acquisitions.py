"""add_rgb_png_to_sentinel_acquisitions

Revision ID: 6d86452b0a14
Revises: 20260817_0002
Create Date: 2026-08-19 20:28:31.175355
"""

from alembic import op
import sqlalchemy as sa


revision = '6d86452b0a14'
down_revision = '20260817_0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('sentinel_acquisitions', sa.Column('rgb_png', sa.LargeBinary(), nullable=True))


def downgrade() -> None:
    op.drop_column('sentinel_acquisitions', 'rgb_png')
