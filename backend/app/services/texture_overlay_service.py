"""
OE4 - Servicio de generación de overlays de textura coloreados.
Genera imágenes PNG con transparencia para visualización en mapas Leaflet.
"""

import io
import base64
import numpy as np
from PIL import Image
import rasterio
from rasterio.transform import array_bounds
from rasterio.features import geometry_mask
from scipy.ndimage import convolve
from typing import Tuple, List


# Kernels según la metodología OE4
KERNELS = {
    "edges": np.array([
        [0,  1,  0],
        [1, -4,  1],
        [0,  1,  0]
    ], dtype=np.float32),

    "homogeneity": np.ones((3, 3), dtype=np.float32) / 9.0,

    # Para contrast usamos Sobel (magnitud del gradiente)
    "contrast_gx": np.array([
        [-1, 0, 1],
        [-2, 0, 2],
        [-1, 0, 1]
    ], dtype=np.float32),

    "contrast_gy": np.array([
        [-1, -2, -1],
        [ 0,  0,  0],
        [ 1,  2,  1]
    ], dtype=np.float32)
}


def generate_texture_overlay(
    ndvi_tiff_bytes: bytes,
    kernel_name: str,
    polygon_geojson: dict
) -> Tuple[bytes, List[List[float]], str]:
    """
    Aplica kernel de textura al NDVI y genera PNG coloreado con recorte a la forma del polígono.

    Paleta de colores (variabilidad — frío/cálido):
    - Azul (#3b82f6): Percentil 0-33 (Uniforme)
    - Púrpura (#8b5cf6): Percentil 33-66 (Moderado)
    - Naranja (#f97316): Percentil 66-100 (Heterogéneo)
    - Transparente: píxeles inválidos/fuera del polígono

    Args:
        ndvi_tiff_bytes: Bytes del archivo TIFF NDVI
        kernel_name: "contrast", "edges", o "homogeneity"
        polygon_geojson: Geometría del polígono en formato GeoJSON
                         {"type": "Polygon", "coordinates": [[[lng, lat], ...]]}

    Returns:
        Tupla (png_bytes, leaflet_bounds, interpretation)
        - png_bytes: Imagen PNG RGBA en bytes (solo polígono coloreado)
        - leaflet_bounds: [[lat_south, lng_west], [lat_north, lng_east]]
        - interpretation: Texto explicativo según kernel y valores
    """
    # 1. Abrir TIFF y leer datos
    with rasterio.open(io.BytesIO(ndvi_tiff_bytes)) as src:
        ndvi = src.read(1).astype(np.float32)
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

    # 2. Preparar array (reemplazar NaN con 0 para convolución)
    ndvi_clean = np.nan_to_num(ndvi, nan=0.0)

    # 3. Aplicar kernel según tipo
    if kernel_name == "contrast":
        # Magnitud del gradiente (Sobel)
        gx = convolve(ndvi_clean, KERNELS["contrast_gx"], mode='reflect')
        gy = convolve(ndvi_clean, KERNELS["contrast_gy"], mode='reflect')
        texture_result = np.sqrt(gx**2 + gy**2)
    elif kernel_name == "edges":
        # Laplaciano (detecta bordes internos)
        texture_result = convolve(ndvi_clean, KERNELS["edges"], mode='reflect')
        texture_result = np.abs(texture_result)  # Valor absoluto para bordes
    elif kernel_name == "homogeneity":
        # Media local (suaviza, invierte para que alto = más variación)
        mean_local = convolve(ndvi_clean, KERNELS["homogeneity"], mode='reflect')
        # Homogeneidad = diferencia con la media local
        texture_result = np.abs(ndvi_clean - mean_local)
    else:
        raise ValueError(f"Unknown kernel: {kernel_name}")

    # 4. Máscara de datos válidos (misma que NDVI) Y dentro del polígono
    valid = ~np.isnan(ndvi) & (ndvi >= -1) & (ndvi <= 1) & polygon_mask

    # 5. Calcular percentiles sobre píxeles válidos
    valid_values = texture_result[valid]
    if len(valid_values) == 0:
        raise ValueError("No valid pixels in texture result")

    p33 = np.percentile(valid_values, 33)
    p66 = np.percentile(valid_values, 66)

    # 6. Crear imagen RGBA con paleta textura
    h, w = texture_result.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)

    # Azul: percentil 0-33 (uniforme/bajo)
    blue_mask = valid & (texture_result <= p33)
    rgba[blue_mask] = [59, 130, 246, 180]  # #3b82f6, alpha=180

    # Púrpura: percentil 33-66 (moderado)
    purple_mask = valid & (texture_result > p33) & (texture_result <= p66)
    rgba[purple_mask] = [139, 92, 246, 180]  # #8b5cf6, alpha=180

    # Naranja: percentil 66-100 (heterogéneo/alto)
    orange_mask = valid & (texture_result > p66)
    rgba[orange_mask] = [249, 115, 22, 180]  # #f97316, alpha=180

    # Píxeles inválidos → transparente (alpha=0, ya es default)

    # 7. Crear PNG con optimización
    img = Image.fromarray(rgba, mode='RGBA')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG', optimize=True)
    png_bytes = buffer.getvalue()

    # 8. Generar interpretación
    mean_texture = float(valid_values.mean())
    interpretation = _generate_interpretation(kernel_name, mean_texture)

    return png_bytes, leaflet_bounds, interpretation


def _generate_interpretation(kernel_name: str, mean_value: float) -> str:
    """
    Genera texto interpretativo basado en kernel y valor promedio.

    Args:
        kernel_name: Tipo de kernel aplicado
        mean_value: Valor promedio del descriptor de textura

    Returns:
        Texto explicativo para el frontend
    """
    if kernel_name == "contrast":
        if mean_value < 0.05:
            return "Campo muy uniforme — cultivo homogéneo con buen manejo. No se detectan zonas problemáticas."
        elif mean_value < 0.12:
            return "Variabilidad normal — dentro de parámetros esperados para cultivo de arroz. Monitorear evolución."
        else:
            return "Campo heterogéneo — se detectan zonas con diferente vigor vegetativo. Posible causa: riego desigual o variabilidad de suelo."

    elif kernel_name == "edges":
        if mean_value < 0.02:
            return "Sin bordes internos significativos — el cultivo presenta transiciones suaves entre zonas."
        elif mean_value < 0.08:
            return "Bordes moderados — se detectan algunas divisiones internas. Pueden corresponder a caminos, canales o diferencias de siembra."
        else:
            return "Bordes marcados — se observan límites claros dentro de la parcela. Revisar si corresponden a problemas de drenaje o cambios de lote."

    elif kernel_name == "homogeneity":
        if mean_value < 0.03:
            return "Alta homogeneidad — el cultivo crece de forma muy pareja. Excelente uniformidad."
        elif mean_value < 0.08:
            return "Homogeneidad moderada — variación normal dentro del cultivo. Condiciones aceptables."
        else:
            return "Baja homogeneidad — se detecta variabilidad significativa. Evaluar factores como riego, fertilización o plagas."

    return "Análisis de textura completado."
