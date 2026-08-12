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
    rgb_png_bytes: bytes,
    ndvi_tiff_bytes: bytes,
    polygon_geojson: dict
) -> Tuple[bytes, List[List[float]]]:
    """
    Convierte PNG RGB a PNG RGBA con máscara de polígono.

    Usa la georreferencia del NDVI TIFF (que sí tiene transform correcto)
    para aplicar la máscara al RGB PNG (que no tiene georreferencia).

    Args:
        rgb_png_bytes: Bytes del PNG RGB sin georreferencia
        ndvi_tiff_bytes: Bytes del NDVI TIFF (para extraer transform)
        polygon_geojson: Geometría del polígono en formato GeoJSON
                         {"type": "Polygon", "coordinates": [[[lng, lat], ...]]}

    Returns:
        Tupla (png_bytes, leaflet_bounds)
        - png_bytes: Imagen PNG RGBA en bytes (solo polígono visible)
        - leaflet_bounds: [[lat_south, lng_west], [lat_north, lng_east]]
    """
    # 1. Extraer georreferencia del NDVI TIFF (que SÍ la tiene)
    with rasterio.open(io.BytesIO(ndvi_tiff_bytes)) as src:
        transform = src.transform
        bounds = array_bounds(src.height, src.width, transform)
        leaflet_bounds = [[bounds[1], bounds[0]], [bounds[3], bounds[2]]]

        # Crear máscara del polígono usando transform del NDVI
        polygon_mask = geometry_mask(
            [polygon_geojson],
            out_shape=(src.height, src.width),
            transform=transform,
            invert=True  # True = dentro del polígono
        )

    # 2. Abrir RGB PNG y convertir a array
    img = Image.open(io.BytesIO(rgb_png_bytes))
    rgb_arr = np.array(img)

    # Si es RGBA, tomar solo RGB
    if rgb_arr.shape[2] == 4:
        r = rgb_arr[:, :, 0]
        g = rgb_arr[:, :, 1]
        b = rgb_arr[:, :, 2]
    else:
        r = rgb_arr[:, :, 0]
        g = rgb_arr[:, :, 1]
        b = rgb_arr[:, :, 2]

    # 3. Crear imagen RGBA
    h, w = r.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)

    # Asignar RGB solo a píxeles dentro del polígono
    rgba[polygon_mask, 0] = r[polygon_mask]
    rgba[polygon_mask, 1] = g[polygon_mask]
    rgba[polygon_mask, 2] = b[polygon_mask]
    rgba[polygon_mask, 3] = 255  # Opaco dentro del polígono

    # Píxeles fuera del polígono → transparente (alpha=0, ya es default)

    # 4. Crear PNG con optimización
    result_img = Image.fromarray(rgba, mode='RGBA')
    buffer = io.BytesIO()
    result_img.save(buffer, format='PNG', optimize=True)
    png_bytes = buffer.getvalue()

    return png_bytes, leaflet_bounds
