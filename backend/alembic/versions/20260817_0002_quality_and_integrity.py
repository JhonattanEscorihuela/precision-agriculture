"""Bring legacy databases to the cloud-quality schema and enforce integrity.

Revision ID: 20260817_0002
Revises: 20260817_0001
"""

from alembic import op
import sqlalchemy as sa


revision = "20260817_0002"
down_revision = "20260817_0001"
branch_labels = None
depends_on = None


def _column_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def _add_column_if_missing(
    table_name: str,
    column: sa.Column,
) -> None:
    if column.name not in _column_names(table_name):
        op.add_column(table_name, column)


def _has_foreign_key(table_name: str, local_column: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(
        local_column in foreign_key.get("constrained_columns", [])
        for foreign_key in inspector.get_foreign_keys(table_name)
    )


def _add_foreign_key_if_missing(
    name: str,
    source_table: str,
    target_table: str,
    local_column: str,
    remote_column: str = "id",
) -> None:
    if not _has_foreign_key(source_table, local_column):
        op.create_foreign_key(
            name,
            source_table,
            target_table,
            [local_column],
            [remote_column],
            ondelete="CASCADE",
        )


def _has_unique(table_name: str, columns: set[str]) -> bool:
    inspector = sa.inspect(op.get_bind())
    constraints = inspector.get_unique_constraints(table_name)
    return any(set(item.get("column_names") or []) == columns for item in constraints)


def upgrade() -> None:
    _add_column_if_missing(
        "sentinel_acquisitions",
        sa.Column("scene_id", sa.String(), nullable=True),
    )
    _add_column_if_missing(
        "sentinel_acquisitions",
        sa.Column("parcel_cloud_cover", sa.Float(), nullable=True),
    )
    _add_column_if_missing(
        "sentinel_acquisitions",
        sa.Column("parcel_shadow_cover", sa.Float(), nullable=True),
    )
    _add_column_if_missing(
        "sentinel_acquisitions",
        sa.Column("valid_pixel_percentage", sa.Float(), nullable=True),
    )
    _add_column_if_missing(
        "sentinel_acquisitions",
        sa.Column("usable_pixel_percentage", sa.Float(), nullable=True),
    )
    _add_column_if_missing(
        "sentinel_acquisitions",
        sa.Column("quality_status", sa.String(), nullable=True),
    )
    _add_column_if_missing(
        "sentinel_acquisitions",
        sa.Column("cloud_method", sa.String(), nullable=True),
    )
    _add_column_if_missing(
        "sentinel_acquisitions",
        sa.Column("scl_data", sa.LargeBinary(), nullable=True),
    )

    for column_name in ("ndvi_median", "ndvi_p10", "ndvi_p90"):
        _add_column_if_missing(
            "ndvi_results",
            sa.Column(column_name, sa.Float(), nullable=True),
        )
    for column_name in ("overlay_png", "satellite_png"):
        _add_column_if_missing(
            "ndvi_results",
            sa.Column(column_name, sa.LargeBinary(), nullable=True),
        )
    _add_column_if_missing(
        "ndvi_results",
        sa.Column("analysis_valid_pixel_percentage", sa.Float(), nullable=True),
    )
    _add_column_if_missing(
        "ndvi_results",
        sa.Column(
            "cloud_mask_applied",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    _add_foreign_key_if_missing(
        "fk_sentinel_acquisitions_polygon",
        "sentinel_acquisitions",
        "polygon",
        "polygon_id",
    )
    _add_foreign_key_if_missing(
        "fk_ndvi_results_acquisition",
        "ndvi_results",
        "sentinel_acquisitions",
        "acquisition_id",
    )
    _add_foreign_key_if_missing(
        "fk_ndvi_results_polygon",
        "ndvi_results",
        "polygon",
        "polygon_id",
    )
    _add_foreign_key_if_missing(
        "fk_segmentation_results_ndvi",
        "segmentation_results",
        "ndvi_results",
        "ndvi_result_id",
    )
    _add_foreign_key_if_missing(
        "fk_segmentation_results_polygon",
        "segmentation_results",
        "polygon",
        "polygon_id",
    )
    _add_foreign_key_if_missing(
        "fk_texture_descriptors_segmentation",
        "texture_descriptors",
        "segmentation_results",
        "segmentation_result_id",
    )
    _add_foreign_key_if_missing(
        "fk_texture_descriptors_polygon",
        "texture_descriptors",
        "polygon",
        "polygon_id",
    )
    _add_foreign_key_if_missing(
        "fk_texture_overlay_cache_ndvi",
        "texture_overlay_cache",
        "ndvi_results",
        "ndvi_result_id",
    )

    if not _has_unique(
        "sentinel_acquisitions",
        {"polygon_id", "acquisition_date"},
    ):
        op.create_unique_constraint(
            "uq_sentinel_polygon_date",
            "sentinel_acquisitions",
            ["polygon_id", "acquisition_date"],
        )

    if not _has_unique(
        "texture_overlay_cache",
        {"ndvi_result_id", "kernel"},
    ):
        op.create_unique_constraint(
            "uq_texture_overlay_ndvi_kernel",
            "texture_overlay_cache",
            ["ndvi_result_id", "kernel"],
        )


def downgrade() -> None:
    """Keep the adoption migration non-destructive.

    On a fresh database the baseline already creates these columns and
    constraints, while a legacy installation may have equivalent constraints
    under database-generated names. Removing them on downgrade would therefore
    destroy baseline integrity or fail unpredictably.
    """
    pass
