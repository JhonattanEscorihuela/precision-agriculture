"""Prueba del contrato 0/1/255 para la máscara binaria OE3."""

from io import BytesIO

import numpy as np
import rasterio
from rasterio.transform import from_origin

from app.services.segmentation_service import SegmentationService


def test_binary_mask_preserves_invalid_pixels_as_255():
    cultivated = np.array([[True, False], [False, True]], dtype=bool)
    valid = np.array([[True, True], [False, True]], dtype=bool)
    profile = {
        "driver": "GTiff",
        "width": 2,
        "height": 2,
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:4326",
        "transform": from_origin(0, 2, 1, 1),
        "nodata": np.nan,
    }

    result = SegmentationService()._mask_to_tiff(
        cultivated,
        profile,
        valid_mask=valid,
    )

    with rasterio.open(BytesIO(result)) as dataset:
        assert dataset.nodata == 255
        assert dataset.read(1).tolist() == [[1, 0], [255, 1]]
