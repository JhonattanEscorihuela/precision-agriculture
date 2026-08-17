"""Pruebas de alineación y aplicación de la máscara SCL al NDVI."""

import asyncio
from io import BytesIO

import numpy as np
import rasterio
from rasterio.transform import from_origin

from app.services.ndvi_service import NDVIService


def _single_band_tiff(array: np.ndarray, pixel_size: float = 1.0) -> bytes:
    output = BytesIO()
    with rasterio.open(
        output,
        "w",
        driver="GTiff",
        width=array.shape[1],
        height=array.shape[0],
        count=1,
        dtype=str(array.dtype),
        crs="EPSG:4326",
        transform=from_origin(0, 4, pixel_size, pixel_size),
    ) as dataset:
        dataset.write(array, 1)
    return output.getvalue()


def _scl_tiff() -> bytes:
    # Cada píxel SCL de 2 grados se alinea con 2x2 píxeles de reflectancia.
    scl = np.array([[8, 3], [4, 4]], dtype=np.uint8)
    data_mask = np.ones((2, 2), dtype=np.uint8)
    output = BytesIO()
    with rasterio.open(
        output,
        "w",
        driver="GTiff",
        width=2,
        height=2,
        count=2,
        dtype="uint8",
        crs="EPSG:4326",
        transform=from_origin(0, 4, 2, 2),
    ) as dataset:
        dataset.write(scl, 1)
        dataset.write(data_mask, 2)
    return output.getvalue()


def test_ndvi_excludes_clouds_shadows_and_resamples_scl_with_nearest_neighbor():
    red = np.full((4, 4), 0.2, dtype=np.float32)
    nir = np.full((4, 4), 0.6, dtype=np.float32)
    polygon = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [4, 0], [4, 4], [0, 4], [0, 0]]],
    }

    ndvi, invalid, _, valid_percentage = asyncio.run(
        NDVIService()._read_and_calculate_ndvi(
            _single_band_tiff(red),
            _single_band_tiff(nir),
            _scl_tiff(),
            polygon,
        )
    )

    assert np.count_nonzero(invalid) == 8
    assert np.count_nonzero(np.isfinite(ndvi)) == 8
    assert np.allclose(ndvi[np.isfinite(ndvi)], 0.5)
    assert valid_percentage == 50.0


def test_ndvi_statistics_use_only_the_combined_valid_mask():
    red = np.full((4, 4), 0.2, dtype=np.float32)
    nir = np.full((4, 4), 0.6, dtype=np.float32)
    polygon = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [4, 0], [4, 4], [0, 4], [0, 0]]],
    }
    red_tiff = _single_band_tiff(red)
    nir_tiff = _single_band_tiff(nir)
    service = NDVIService()
    ndvi, invalid, _, _ = asyncio.run(
        service._read_and_calculate_ndvi(red_tiff, nir_tiff, _scl_tiff(), polygon)
    )

    stats = service._calculate_statistics(ndvi, invalid, red_tiff, nir_tiff)

    for key in ("ndvi_mean", "ndvi_min", "ndvi_max", "ndvi_median", "ndvi_p10", "ndvi_p90"):
        assert np.isclose(stats[key], 0.5)
    assert np.isclose(stats["ndvi_std"], 0.0)
