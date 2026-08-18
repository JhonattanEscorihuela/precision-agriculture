"""Create the current schema on a fresh database without altering legacy tables.

Revision ID: 20260817_0001
Revises: None
"""

from alembic import op
from sqlmodel import SQLModel

from app.models.acquisition import SentinelAcquisition
from app.models.analysis import NDVIResult, TextureOverlayCache
from app.models.polygon import Polygon
from app.models.segmentation import SegmentationResult
from app.models.texture import TextureDescriptor
from app.models.user import User


revision = "20260817_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create missing tables; existing installations remain untouched here."""
    SQLModel.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    """The baseline is intentionally non-destructive on downgrade."""
    pass
