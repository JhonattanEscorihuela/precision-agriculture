"""Cálculo de nubosidad dentro de una parcela a partir de Sentinel-2 SCL."""

from typing import Dict

import numpy as np
import rasterio
from rasterio.features import geometry_mask


CLOUD_CLASSES = (8, 9, 10)
CLOUD_SHADOW_CLASS = 3
MAX_SUITABLE_CLOUD_PERCENTAGE = 20.0
MIN_VALID_DATA_PERCENTAGE = 80.0
MIN_USABLE_PIXEL_PERCENTAGE = 80.0


def classify_observation_quality(metrics: Dict[str, float]) -> str:
    """Clasifica si una observación es apta para análisis agronómico."""
    if (
        metrics["parcel_cloud_cover"] > MAX_SUITABLE_CLOUD_PERCENTAGE
        or metrics["valid_pixel_percentage"] < MIN_VALID_DATA_PERCENTAGE
    ):
        return "unsuitable"
    if metrics["usable_pixel_percentage"] < MIN_USABLE_PIXEL_PERCENTAGE:
        return "caution"
    return "suitable"


def calculate_parcel_cloud_coverage(
    scl_tiff: bytes,
    polygon_geojson: Dict,
) -> Dict[str, float]:
    """
    Calcula nubes, sombras y datos válidos dentro del polígono.

    SCL 8/9/10 representan nube media, nube alta y cirros. SCL 3 se
    reporta separadamente como sombra. SCL 0 y dataMask=0 son datos no válidos.
    """
    with rasterio.MemoryFile(scl_tiff) as memory_file:
        with memory_file.open() as dataset:
            if dataset.count < 2:
                raise ValueError("El TIFF SCL debe contener SCL y dataMask")

            scl = dataset.read(1)
            data_mask = dataset.read(2).astype(bool)
            parcel_mask = geometry_mask(
                [polygon_geojson],
                out_shape=(dataset.height, dataset.width),
                transform=dataset.transform,
                invert=True,
            )

    parcel_pixels = int(np.count_nonzero(parcel_mask))
    if parcel_pixels == 0:
        raise ValueError("El polígono no intersecta ningún píxel del raster SCL")

    valid_mask = parcel_mask & data_mask & (scl != 0)
    valid_pixels = int(np.count_nonzero(valid_mask))
    if valid_pixels == 0:
        raise ValueError("No hay píxeles SCL válidos dentro de la parcela")

    cloud_pixels = int(np.count_nonzero(valid_mask & np.isin(scl, CLOUD_CLASSES)))
    shadow_pixels = int(np.count_nonzero(valid_mask & (scl == CLOUD_SHADOW_CLASS)))
    usable_pixels = int(np.count_nonzero(
        valid_mask
        & ~np.isin(scl, CLOUD_CLASSES)
        & (scl != CLOUD_SHADOW_CLASS)
    ))

    metrics = {
        "parcel_cloud_cover": round(100.0 * cloud_pixels / valid_pixels, 2),
        "parcel_shadow_cover": round(100.0 * shadow_pixels / valid_pixels, 2),
        "valid_pixel_percentage": round(100.0 * valid_pixels / parcel_pixels, 2),
        "usable_pixel_percentage": round(100.0 * usable_pixels / parcel_pixels, 2),
    }
    metrics["quality_status"] = classify_observation_quality(metrics)
    return metrics
