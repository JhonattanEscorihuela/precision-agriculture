"""
OE2/OE3/OE4 - Servicio de generación de imágenes satelitales true color.
Descarga y cachea imágenes RGB de Sentinel Hub para usar como capa de fondo
en widgets de visualización.
"""

import io
import numpy as np
from PIL import Image
import rasterio
from rasterio.transform import array_bounds
from rasterio.features import geometry_mask
from typing import Tuple, List


def generate_satellite_png(
    tiff_bytes: bytes,
    polygon_geojson: dict
) -> Tuple[bytes, List[List[float]]]:
    """
    Convierte TIFF RGB true color a PNG RGBA con máscara de polígono.

    Args:
        tiff_bytes: Bytes del archivo TIFF RGB (3 bandas UINT8)
        polygon_geojson: Geometría del polígono en formato GeoJSON
                         {"type": "Polygon", "coordinates": [[[lng, lat], ...]]}

    Returns:
        Tupla (png_bytes, leaflet_bounds)
        - png_bytes: Imagen PNG RGBA en bytes (solo polígono visible)
        - leaflet_bounds: [[lat_south, lng_west], [lat_north, lng_east]]
    """
    # 1. Abrir TIFF y leer 3 bandas RGB
    with rasterio.open(io.BytesIO(tiff_bytes)) as src:
        # Leer bandas R, G, B
        r = src.read(1)
        g = src.read(2)
        b = src.read(3)
        transform = src.transform

        # Extraer bounds georreferenciados
        bounds = array_bounds(src.height, src.width, transform)
        leaflet_bounds = [[bounds[1], bounds[0]], [bounds[3], bounds[2]]]

        # Crear máscara del polígono
        polygon_mask = geometry_mask(
            [polygon_geojson],
            out_shape=(src.height, src.width),
            transform=transform,
            invert=True  # True = dentro del polígono
        )

    # 2. Crear imagen RGBA
    h, w = r.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)

    # Asignar RGB solo a píxeles dentro del polígono
    rgba[polygon_mask, 0] = r[polygon_mask]
    rgba[polygon_mask, 1] = g[polygon_mask]
    rgba[polygon_mask, 2] = b[polygon_mask]
    rgba[polygon_mask, 3] = 255  # Opaco dentro del polígono

    # Píxeles fuera del polígono → transparente (alpha=0, ya es default)

    # 3. Crear PNG con optimización
    img = Image.fromarray(rgba, mode='RGBA')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG', optimize=True)
    png_bytes = buffer.getvalue()

    return png_bytes, leaflet_bounds
