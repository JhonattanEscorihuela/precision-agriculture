"""Calcula OE2 faltante solo para adquisiciones con calidad local apta."""

import asyncio
import json

from sqlalchemy import select

from app.database import async_session
from app.models.acquisition import SentinelAcquisition
from app.models.analysis import NDVIResult
from app.models.polygon import Polygon
from app.services.ndvi_service import NDVIService


async def main() -> None:
    service = NDVIService()
    report = []

    async with async_session() as listing_db:
        acquisition_ids = list((
            await listing_db.execute(
                select(SentinelAcquisition.id)
                .outerjoin(
                    NDVIResult,
                    NDVIResult.acquisition_id == SentinelAcquisition.id,
                )
                .where(
                    SentinelAcquisition.quality_status == "suitable",
                    SentinelAcquisition.scl_data.is_not(None),
                    NDVIResult.id.is_(None),
                )
                .order_by(SentinelAcquisition.id)
            )
        ).scalars().all())

    for acquisition_id in acquisition_ids:
        async with async_session() as db:
            acquisition, polygon = (
                await db.execute(
                    select(SentinelAcquisition, Polygon)
                    .join(Polygon, SentinelAcquisition.polygon_id == Polygon.id)
                    .where(SentinelAcquisition.id == acquisition_id)
                )
            ).one()
            item = {
                "acquisition_id": acquisition.id,
                "date": acquisition.acquisition_date,
                "quality_status": acquisition.quality_status,
            }
            try:
                result = await service.calculate_ndvi(
                    acquisition_id=acquisition.id,
                    user_id=polygon.user_id,
                    db=db,
                )
                item.update({
                    "status": "calculated",
                    "ndvi_result_id": result["ndvi_id"],
                    "ndvi_mean": round(result["stats"]["ndvi_mean"], 4),
                    "analysis_valid_pixel_percentage": result["stats"][
                        "analysis_valid_pixel_percentage"
                    ],
                    "cloud_mask_applied": result["stats"]["cloud_mask_applied"],
                })
            except Exception as exc:
                await db.rollback()
                item["status"] = "error"
                item["error"] = str(exc)
            report.append(item)

    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
