"""Completa SCL/calidad y recalcula NDVI legados con máscara de nubes."""

import asyncio
import argparse
import json

from sqlalchemy import select

from app.crud.ndvi import get_ndvi_by_acquisition
from app.database import async_session
from app.models.acquisition import SentinelAcquisition
from app.models.polygon import Polygon
from app.services.ndvi_service import NDVIService
from app.services.cloud_coverage_service import calculate_parcel_cloud_coverage
from app.services.sentinel.geometry import calculate_optimal_dimensions
from app.services.sentinel.sentinel_service import SentinelService


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--refresh-bands",
        action="store_true",
        help="Vuelve a descargar B04/B08 para garantizar la misma selección leastCC que SCL",
    )
    args = parser.parse_args()
    sentinel = SentinelService()
    ndvi_service = NDVIService()
    report = []

    async with async_session() as listing_db:
        acquisition_ids = list((
            await listing_db.execute(
                select(SentinelAcquisition.id)
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
                "polygon_id": acquisition.polygon_id,
                "date": acquisition.acquisition_date,
            }
            try:
                geometry = {
                    "type": "Polygon",
                    "coordinates": [polygon.coordinates],
                }
                scl_width, scl_height = calculate_optimal_dimensions(
                    polygon.coordinates,
                    max_resolution_m_per_px=20.0,
                )
                if args.refresh_bands or not acquisition.scl_data:
                    acquisition.scl_data = await sentinel.download_scene_classification(
                        polygon_geojson=geometry,
                        start_date=acquisition.acquisition_date,
                        end_date=acquisition.acquisition_date,
                        width=scl_width,
                        height=scl_height,
                        max_cloud_coverage=100,
                        polygon_id=acquisition.polygon_id,
                    )
                quality = calculate_parcel_cloud_coverage(acquisition.scl_data, geometry)
                acquisition.parcel_cloud_cover = quality["parcel_cloud_cover"]
                acquisition.parcel_shadow_cover = quality["parcel_shadow_cover"]
                acquisition.valid_pixel_percentage = quality["valid_pixel_percentage"]
                acquisition.usable_pixel_percentage = quality["usable_pixel_percentage"]
                acquisition.quality_status = quality["quality_status"]
                acquisition.cloud_method = "SCL"

                if args.refresh_bands:
                    acquisition.b04_data = await sentinel.download_bands(
                        geometry,
                        ["B04"],
                        acquisition.acquisition_date,
                        acquisition.acquisition_date,
                        acquisition.width,
                        acquisition.height,
                        100,
                        acquisition.polygon_id,
                    )
                    acquisition.b08_data = await sentinel.download_bands(
                        geometry,
                        ["B08"],
                        acquisition.acquisition_date,
                        acquisition.acquisition_date,
                        acquisition.width,
                        acquisition.height,
                        100,
                        acquisition.polygon_id,
                    )
                    try:
                        dates = await sentinel.get_available_dates(
                            polygon.coordinates,
                            acquisition.acquisition_date,
                            acquisition.acquisition_date,
                            100,
                        )
                        if dates:
                            acquisition.cloud_coverage = dates[0]["cloud_cover"]
                            acquisition.scene_id = dates[0].get("scene_id")
                    except Exception as metadata_error:
                        # La metadata STAC es complementaria: una respuesta vacía
                        # no debe descartar TIFF válidos ya descargados.
                        item["metadata_warning"] = str(metadata_error)

                db.add(acquisition)
                await db.commit()
                await db.refresh(acquisition)
                item.update({
                    "scene_id": acquisition.scene_id,
                    "parcel_cloud_cover": acquisition.parcel_cloud_cover,
                    "parcel_shadow_cover": acquisition.parcel_shadow_cover,
                    "usable_pixel_percentage": acquisition.usable_pixel_percentage,
                    "quality_status": acquisition.quality_status,
                    "bands_refreshed": args.refresh_bands,
                })

                existing_ndvi = await get_ndvi_by_acquisition(db, acquisition.id)
                if existing_ndvi:
                    if args.refresh_bands:
                        existing_ndvi.cloud_mask_applied = False
                        db.add(existing_ndvi)
                        await db.commit()
                    result = await ndvi_service.calculate_ndvi(
                        acquisition_id=acquisition.id,
                        user_id=polygon.user_id,
                        db=db,
                    )
                    item["ndvi_result_id"] = result["ndvi_id"]
                    item["ndvi_recalculated"] = result["stats"]["cloud_mask_applied"]
                    item["analysis_valid_pixel_percentage"] = result["stats"][
                        "analysis_valid_pixel_percentage"
                    ]
                else:
                    item["ndvi_recalculated"] = False
                    item["ndvi_reason"] = "not_calculated_previously"
                item["status"] = "ok"
            except Exception as exc:
                await db.rollback()
                item["status"] = "error"
                item["error"] = str(exc)
            report.append(item)

    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
