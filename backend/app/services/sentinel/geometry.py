"""
Módulo de cálculos geométricos para polígonos.
Responsabilidad: Bounding box, dimensiones óptimas, validaciones.
"""

import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


def calculate_bbox(coords: List[List[float]]) -> Dict:
    """
    Calcula el bounding box de un conjunto de coordenadas.

    Args:
        coords: Lista de coordenadas [[lng, lat], ...]

    Returns:
        Dict con min/max lng/lat, centro y dimensiones
    """
    lngs = [c[0] for c in coords]
    lats = [c[1] for c in coords]

    return {
        "min_lng": min(lngs),
        "max_lng": max(lngs),
        "min_lat": min(lats),
        "max_lat": max(lats),
        "center_lng": (min(lngs) + max(lngs)) / 2,
        "center_lat": (min(lats) + max(lats)) / 2,
        "width_degrees": max(lngs) - min(lngs),
        "height_degrees": max(lats) - min(lats)
    }


def calculate_optimal_dimensions(
    coords: List[List[float]],
    max_resolution_m_per_px: float = 1000.0,
    min_dimension: int = 10
) -> Tuple[int, int]:
    """
    Calcula dimensiones óptimas (width, height) para petición a Sentinel Hub.

    Asegura que la resolución no exceda el límite de Sentinel Hub (1500 m/px).

    Args:
        coords: Lista de coordenadas [[lng, lat], ...]
        max_resolution_m_per_px: Resolución máxima deseada en metros por píxel
        min_dimension: Dimensión mínima en píxeles

    Returns:
        Tuple[int, int]: (width, height) en píxeles

    Notes:
        Sentinel Hub tiene un límite de 1500 m/px de resolución.
        Usamos un valor más conservador (1000 m/px por defecto).
    """
    bbox = calculate_bbox(coords)

    # Convertir dimensiones de grados a metros
    # Aproximación: 1 grado de latitud ≈ 111 km
    # Longitud depende de la latitud: 1 grado lng ≈ 111 km × cos(lat)
    meters_per_deg_lat = 111000
    meters_per_deg_lng = 111000 * abs(bbox['center_lat'])

    width_m = bbox['width_degrees'] * meters_per_deg_lng
    height_m = bbox['height_degrees'] * meters_per_deg_lat

    # Calcular dimensiones en píxeles para lograr la resolución deseada
    width_px = max(min_dimension, int(width_m / max_resolution_m_per_px))
    height_px = max(min_dimension, int(height_m / max_resolution_m_per_px))

    logger.info(
        f"📐 Dimensiones calculadas: {width_m:.0f}m × {height_m:.0f}m → "
        f"{width_px}px × {height_px}px "
        f"(resolución: {width_m/width_px:.1f} m/px × {height_m/height_px:.1f} m/px)"
    )

    return width_px, height_px


def is_polygon_closed(coords: List[List[float]]) -> bool:
    """
    Verifica si un polígono está cerrado (primer punto = último punto).

    Args:
        coords: Lista de coordenadas [[lng, lat], ...]

    Returns:
        bool: True si el polígono está cerrado
    """
    if len(coords) < 2:
        return False

    first = coords[0]
    last = coords[-1]
    return first[0] == last[0] and first[1] == last[1]
