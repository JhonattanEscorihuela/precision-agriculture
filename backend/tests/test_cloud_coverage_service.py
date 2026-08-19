"""Pruebas unitarias del cálculo de nubosidad SCL dentro de una parcela."""

from io import BytesIO

import numpy as np
import rasterio
from rasterio.transform import from_origin

from app.services.cloud_coverage_service import (
    calculate_parcel_cloud_coverage,
    classify_observation_quality,
)
from app.services.sentinel.request_builder import (
    build_process_request,
    build_scl_evalscript,
)
from app.services.sentinel.geometry import calculate_optimal_dimensions


def _build_scl_tiff() -> bytes:
    scl = np.array([
        [8, 9, 10, 3],
        [4, 4, 4, 4],
        [0, 4, 4, 4],
        [4, 4, 4, 4],
    ], dtype=np.uint8)
    data_mask = np.ones((4, 4), dtype=np.uint8)
    data_mask[3, 3] = 0

    output = BytesIO()
    with rasterio.open(
        output,
        "w",
        driver="GTiff",
        width=4,
        height=4,
        count=2,
        dtype="uint8",
        crs="EPSG:4326",
        transform=from_origin(0, 4, 1, 1),
    ) as dataset:
        dataset.write(scl, 1)
        dataset.write(data_mask, 2)
    return output.getvalue()


def test_calculates_cloud_shadow_and_valid_pixels_inside_polygon():
    polygon = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [4, 0], [4, 4], [0, 4], [0, 0]]],
    }

    result = calculate_parcel_cloud_coverage(_build_scl_tiff(), polygon)

    assert result == {
        "parcel_cloud_cover": 21.43,
        "parcel_shadow_cover": 7.14,
        "valid_pixel_percentage": 87.5,
        "usable_pixel_percentage": 62.5,
        "quality_status": "unsuitable",
    }


def test_uses_only_pixels_inside_the_parcel_geometry():
    left_half = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [2, 0], [2, 4], [0, 4], [0, 0]]],
    }

    result = calculate_parcel_cloud_coverage(_build_scl_tiff(), left_half)

    assert result == {
        "parcel_cloud_cover": 28.57,
        "parcel_shadow_cover": 0.0,
        "valid_pixel_percentage": 87.5,
        "usable_pixel_percentage": 62.5,
        "quality_status": "unsuitable",
    }


def test_quality_policy_distinguishes_suitable_caution_and_unsuitable():
    assert classify_observation_quality({
        "parcel_cloud_cover": 5.0,
        "valid_pixel_percentage": 100.0,
        "usable_pixel_percentage": 92.0,
    }) == "suitable"
    assert classify_observation_quality({
        "parcel_cloud_cover": 10.0,
        "valid_pixel_percentage": 100.0,
        "usable_pixel_percentage": 75.0,
    }) == "caution"
    assert classify_observation_quality({
        "parcel_cloud_cover": 21.0,
        "valid_pixel_percentage": 100.0,
        "usable_pixel_percentage": 79.0,
    }) == "unsuitable"


def test_scl_request_uses_least_cloudy_mosaic():
    request = build_process_request(
        polygon_geojson={"type": "Polygon", "coordinates": []},
        start_date="2025-12-07",
        end_date="2025-12-07",
        evalscript=build_scl_evalscript(),
        width=512,
        height=512,
        max_cloud_coverage=20,
    )

    data_filter = request["input"]["data"][0]["dataFilter"]
    assert data_filter["mosaickingOrder"] == "leastCC"
    assert 'input: ["SCL", "dataMask"]' in request["evalscript"]


def test_native_scl_dimensions_use_longitude_cosine_correction():
    coords = [[-67.528, 8.844], [-67.510, 8.844], [-67.510, 8.854], [-67.528, 8.844]]

    width, height = calculate_optimal_dimensions(
        coords,
        max_resolution_m_per_px=20.0,
    )

    assert 95 <= width <= 105
    assert 55 <= height <= 56
