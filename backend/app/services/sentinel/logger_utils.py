"""
Módulo de logging detallado para requests/responses Sentinel Hub.
Responsabilidad: Logging estructurado y diagnóstico.
"""

import json
import logging
from typing import Dict, Optional
import httpx
from .geometry import calculate_bbox, is_polygon_closed

logger = logging.getLogger(__name__)


def log_request_details(
    operation: str,
    polygon_geojson: Dict,
    request_payload: Dict,
    polygon_id: Optional[int] = None
):
    """
    Logging detallado de la petición a Sentinel Hub.

    Args:
        operation: Nombre de la operación (ej: "DOWNLOAD_NDVI")
        polygon_geojson: Geometría GeoJSON del polígono
        request_payload: Payload completo que se enviará
        polygon_id: ID del polígono si aplica
    """
    logger.info("")
    logger.info("=" * 100)
    logger.info(f"🛰️  SENTINEL HUB REQUEST - {operation}")
    logger.info("=" * 100)

    if polygon_id:
        logger.info(f"📍 Polygon ID: {polygon_id}")

    logger.info("")
    logger.info("--- 1️⃣  COORDENADAS DEL POLÍGONO (como vienen de la DB) ---")
    logger.info(f"Type: {polygon_geojson.get('type')}")
    logger.info("Coordinates:")

    coords = polygon_geojson.get('coordinates', [[]])[0]
    for i, coord in enumerate(coords):
        logger.info(f"  [{i}] {coord}  (lng={coord[0]:.6f}, lat={coord[1]:.6f})")

    logger.info(f"\nTotal de puntos: {len(coords)}")

    # Verificar si está cerrado
    if len(coords) > 1:
        closed = is_polygon_closed(coords)
        logger.info(f"¿Polígono cerrado? {closed}")
        if not closed:
            logger.warning("⚠️  ADVERTENCIA: El polígono NO está cerrado!")

    logger.info("")
    logger.info("--- 2️⃣  BOUNDING BOX CALCULADO ---")
    if coords:
        bbox = calculate_bbox(coords)
        logger.info(f"Min Longitude: {bbox['min_lng']:.6f}")
        logger.info(f"Max Longitude: {bbox['max_lng']:.6f}")
        logger.info(f"Min Latitude: {bbox['min_lat']:.6f}")
        logger.info(f"Max Latitude: {bbox['max_lat']:.6f}")
        logger.info(f"Centro: ({bbox['center_lng']:.6f}, {bbox['center_lat']:.6f})")
        logger.info(f"Dimensiones: {bbox['width_degrees']:.6f}° × {bbox['height_degrees']:.6f}°")

        # Estimación de tamaño en metros
        meters_per_deg_lat = 111000
        meters_per_deg_lng = 111000 * abs(bbox['center_lat'])
        width_m = bbox['width_degrees'] * meters_per_deg_lng
        height_m = bbox['height_degrees'] * meters_per_deg_lat
        logger.info(f"Tamaño aproximado: {width_m:.0f}m × {height_m:.0f}m")

    logger.info("")
    logger.info("--- 3️⃣  REQUEST JSON COMPLETO (sin token) ---")
    logger.info(json.dumps(request_payload, indent=2, ensure_ascii=False))

    logger.info("")
    logger.info(f"🌐 URL destino: https://sh.dataspace.copernicus.eu/api/v1/process")
    logger.info("=" * 100)
    logger.info("")


def log_response_details(
    operation: str,
    response: httpx.Response,
    success: bool
):
    """
    Logging detallado de la respuesta de Sentinel Hub.

    Args:
        operation: Nombre de la operación
        response: Respuesta HTTP
        success: Si fue exitosa
    """
    logger.info("")
    logger.info("=" * 100)
    logger.info(f"📬 SENTINEL HUB RESPONSE - {operation}")
    logger.info("=" * 100)

    logger.info(f"HTTP Status: {response.status_code}")
    logger.info(f"Success: {success}")

    logger.info("")
    logger.info("--- RESPONSE HEADERS ---")
    for key, value in response.headers.items():
        logger.info(f"{key}: {value}")

    logger.info("")
    if success:
        logger.info("--- RESPONSE BODY ---")
        logger.info(f"✅ Success! Downloaded {len(response.content)} bytes")
        logger.info(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
    else:
        logger.info("--- RESPONSE BODY (ERROR) ---")
        logger.error(f"❌ HTTP {response.status_code}")

        # Intentar parsear como JSON
        try:
            error_json = response.json()
            logger.error("Error JSON:")
            logger.error(json.dumps(error_json, indent=2, ensure_ascii=False))
        except:
            # Si no es JSON, mostrar como texto
            logger.error("Error Text:")
            logger.error(response.text[:2000])  # Primeros 2000 caracteres

    logger.info("=" * 100)
    logger.info("")
