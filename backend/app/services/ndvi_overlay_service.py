"""
OE2 - Servicio de generación de overlays NDVI coloreados.
Genera imágenes PNG con transparencia para visualización en mapas Leaflet.
"""

import io
import base64
import numpy as np
from PIL import Image
import rasterio
from rasterio.transform import array_bounds
from rasterio.features import geometry_mask
from typing import Tuple, List


def generate_ndvi_overlay(
    ndvi_tiff_bytes: bytes,
    polygon_geojson: dict
) -> Tuple[bytes, List[List[float]]]:
    """
    Genera PNG coloreado RGBA desde TIFF NDVI con recorte a la forma del polígono.

    Paleta de colores (semáforo de salud):
    - Verde (#16a34a): NDVI >= 0.5 (Sano)
    - Amarillo (#eab308): 0.3 <= NDVI < 0.5 (Alerta)
    - Rojo (#dc2626): NDVI < 0.3 (Crítico)
    - Transparente: píxeles inválidos/nodata/fuera del polígono

    Args:
        ndvi_tiff_bytes: Bytes del archivo TIFF NDVI
        polygon_geojson: Geometría del polígono en formato GeoJSON
                         {"type": "Polygon", "coordinates": [[[lng, lat], ...]]}

    Returns:
        Tupla (png_bytes, leaflet_bounds)
        - png_bytes: Imagen PNG RGBA en bytes (solo polígono coloreado)
        - leaflet_bounds: [[lat_south, lng_west], [lat_north, lng_east]]
    """
    # 1. Abrir TIFF y leer datos
    with rasterio.open(io.BytesIO(ndvi_tiff_bytes)) as src:
        ndvi = src.read(1).astype(np.float32)
        transform = src.transform

        # Extraer bounds georreferenciados
        # array_bounds retorna (west, south, east, north)
        bounds = array_bounds(src.height, src.width, transform)

        # Convertir a formato Leaflet: [[south, west], [north, east]]
        leaflet_bounds = [[bounds[1], bounds[0]], [bounds[3], bounds[2]]]

        # Obtener nodata value si existe
        nodata = src.nodata

        # 2. Crear máscara del polígono
        # geometry_mask retorna True donde NO hay geometría
        # invert=True → True DENTRO del polígono
        polygon_mask = geometry_mask(
            [polygon_geojson],
            out_shape=(src.height, src.width),
            transform=transform,
            invert=True  # True = dentro del polígono
        )

    # 3. Crear imagen RGBA (4 canales: R, G, B, Alpha)
    h, w = ndvi.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)

    # 4. Máscara de datos válidos: rango válido Y dentro del polígono
    valid = ~np.isnan(ndvi) & (ndvi >= -1) & (ndvi <= 1) & polygon_mask
    if nodata is not None:
        valid = valid & (ndvi != nodata)

    # 5. Aplicar colores según umbrales (solo a píxeles válidos)
    # Verde: NDVI >= 0.5 (Sano)
    green_mask = valid & (ndvi >= 0.5)
    rgba[green_mask] = [22, 163, 74, 180]  # #16a34a, alpha=180 (70% opacidad)

    # Amarillo: 0.3 <= NDVI < 0.5 (Alerta)
    yellow_mask = valid & (ndvi >= 0.3) & (ndvi < 0.5)
    rgba[yellow_mask] = [234, 179, 8, 180]  # #eab308, alpha=180

    # Rojo: NDVI < 0.3 (Crítico)
    red_mask = valid & (ndvi < 0.3)
    rgba[red_mask] = [220, 38, 38, 180]  # #dc2626, alpha=180

    # Píxeles inválidos o fuera del polígono → transparente (alpha=0, ya es default)

    # 6. Crear PNG con optimización
    img = Image.fromarray(rgba, mode='RGBA')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG', optimize=True)
    png_bytes = buffer.getvalue()

    return png_bytes, leaflet_bounds
