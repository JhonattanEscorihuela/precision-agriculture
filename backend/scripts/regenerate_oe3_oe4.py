"""Regenera OE3/OE4 solo sobre NDVI enmascarados de observaciones aptas."""

import asyncio
import json

from sqlalchemy import delete, select

from app.database import async_session
from app.models.acquisition import SentinelAcquisition
from app.models.analysis import NDVIResult, TextureOverlayCache
from app.models.polygon import Polygon
from app.models.segmentation import SegmentationResult
from app.models.texture import TextureDescriptor
from app.services.segmentation_service import SegmentationService
from app.services.texture_service import TextureService


async def _delete_derived(db, ndvi_result_id: int) -> int:
    segmentation_ids = select(SegmentationResult.id).where(
        SegmentationResult.ndvi_result_id == ndvi_result_id
    )
    texture_result = await db.execute(
        delete(TextureDescriptor).where(
            TextureDescriptor.segmentation_result_id.in_(segmentation_ids)
        ).execution_options(synchronize_session=False)
    )
    await db.execute(
        delete(TextureOverlayCache).where(
            TextureOverlayCache.ndvi_result_id == ndvi_result_id
        ).execution_options(synchronize_session=False)
    )
    segmentation_result = await db.execute(
        delete(SegmentationResult).where(
            SegmentationResult.ndvi_result_id == ndvi_result_id
        ).execution_options(synchronize_session=False)
    )
    await db.commit()
    return (texture_result.rowcount or 0) + (segmentation_result.rowcount or 0)


async def main() -> None:
    segmentation_service = SegmentationService()
    texture_service = TextureService()
    report = []

    async with async_session() as listing_db:
        rows = (
            await listing_db.execute(
                select(
                    SentinelAcquisition.id,
                    SentinelAcquisition.acquisition_date,
                    SentinelAcquisition.quality_status,
                    NDVIResult.id,
                )
                .outerjoin(
                    NDVIResult,
                    NDVIResult.acquisition_id == SentinelAcquisition.id,
                )
                .order_by(SentinelAcquisition.id)
            )
        ).all()

    for acquisition_id, acquisition_date, quality_status, ndvi_result_id in rows:
        if ndvi_result_id is None:
            report.append({
                "acquisition_id": acquisition_id,
                "date": acquisition_date,
                "quality_status": quality_status,
                "status": "skipped",
                "reason": "ndvi_not_calculated",
            })
            continue
        async with async_session() as db:
            ndvi_result, acquisition, polygon = (
                await db.execute(
                    select(NDVIResult, SentinelAcquisition, Polygon)
                    .join(
                        SentinelAcquisition,
                        NDVIResult.acquisition_id == SentinelAcquisition.id,
                    )
                    .join(Polygon, NDVIResult.polygon_id == Polygon.id)
                    .where(NDVIResult.id == ndvi_result_id)
                )
            ).one()
            item = {
                "ndvi_result_id": ndvi_result.id,
                "acquisition_id": acquisition.id,
                "date": acquisition.acquisition_date,
                "quality_status": quality_status,
            }
            try:
                item["derived_rows_removed"] = await _delete_derived(
                    db,
                    ndvi_result.id,
                )
                if quality_status != "suitable" or not ndvi_result.cloud_mask_applied:
                    item["status"] = "skipped"
                    item["reason"] = (
                        "quality_not_suitable"
                        if quality_status != "suitable"
                        else "cloud_mask_not_applied"
                    )
                    report.append(item)
                    continue

                segmentation = await segmentation_service.calculate_segmentation(
                    ndvi_result_id=ndvi_result.id,
                    user_id=polygon.user_id,
                    db=db,
                    threshold=SegmentationService.DEFAULT_THRESHOLD,
                    save_mask=True,
                )
                textures = await texture_service.calculate_texture(
                    segmentation_result_id=segmentation["id"],
                    user_id=polygon.user_id,
                    db=db,
                )
                item.update({
                    "status": "regenerated",
                    "segmentation_id": segmentation["id"],
                    "threshold": segmentation["threshold_used"],
                    "valid_pixels": segmentation["total_pixels"],
                    "cultivated_pixels": segmentation["cultivated_pixels"],
                    "cultivated_percentage": round(
                        segmentation["cultivated_percentage"],
                        2,
                    ),
                    "texture_descriptors": [
                        {
                            "kernel": descriptor["kernel_type"],
                            "std_normalized": round(
                                descriptor["std_normalized"],
                                4,
                            ),
                            "discriminative": descriptor["discriminative"],
                        }
                        for descriptor in textures
                    ],
                })
            except Exception as exc:
                await db.rollback()
                item["status"] = "error"
                item["error"] = str(exc)
            report.append(item)

    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
