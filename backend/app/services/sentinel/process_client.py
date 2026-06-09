"""
Módulo cliente para Process API de Copernicus DataSpace.
Responsabilidad: Descargas de imágenes satelitales.
"""

import logging
from typing import Dict, List, Optional
import httpx
from .auth import SentinelAuth
from .request_builder import (
    build_bands_evalscript,
    build_ndvi_evalscript,
    build_true_color_evalscript,
    build_check_availability_evalscript,
    build_process_request
)
from .logger_utils import log_request_details, log_response_details
from .geometry import calculate_optimal_dimensions

logger = logging.getLogger(__name__)


class ProcessClient:
    """Cliente para interactuar con Process API de Sentinel Hub."""

    PROCESS_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"

    def __init__(self, auth: SentinelAuth):
        """
        Inicializa el cliente con un gestor de autenticación.

        Args:
            auth: Instancia de SentinelAuth para obtener tokens
        """
        self.auth = auth

    async def download_bands(
        self,
        polygon_geojson: Dict,
        bands: List[str],
        start_date: str,
        end_date: str,
        width: int = 512,
        height: int = 512,
        max_cloud_coverage: int = 20,
        polygon_id: Optional[int] = None
    ) -> bytes:
        """
        Descarga bandas espectrales específicas de Sentinel-2 como GeoTIFF.

        Args:
            polygon_geojson: Polígono en formato GeoJSON (geometry)
            bands: Lista de bandas a descargar (ej: ["B04", "B08"])
            start_date: Fecha inicio (YYYY-MM-DD)
            end_date: Fecha fin (YYYY-MM-DD)
            width: Ancho de la imagen en píxeles
            height: Alto de la imagen en píxeles
            max_cloud_coverage: Cobertura máxima de nubes (0-100)
            polygon_id: ID del polígono (para logging)

        Returns:
            bytes: Contenido del GeoTIFF

        Raises:
            httpx.HTTPError: Si falla la descarga
        """
        token = self.auth.ensure_authenticated()

        evalscript = build_bands_evalscript(bands)
        request_payload = build_process_request(
            polygon_geojson=polygon_geojson,
            start_date=start_date,
            end_date=end_date,
            evalscript=evalscript,
            width=width,
            height=height,
            max_cloud_coverage=max_cloud_coverage
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        log_request_details("DOWNLOAD_BANDS", polygon_geojson, request_payload, polygon_id)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                self.PROCESS_URL,
                json=request_payload,
                headers=headers
            )

            success = (response.status_code == 200)
            log_response_details("DOWNLOAD_BANDS", response, success)

            response.raise_for_status()
            return response.content

    async def download_ndvi(
        self,
        polygon_geojson: Dict,
        start_date: str,
        end_date: str,
        width: int = 512,
        height: int = 512,
        max_cloud_coverage: int = 20,
        polygon_id: Optional[int] = None
    ) -> bytes:
        """
        Descarga NDVI calculado directamente por Sentinel Hub como GeoTIFF.

        Args:
            polygon_geojson: Polígono en formato GeoJSON (geometry)
            start_date: Fecha inicio (YYYY-MM-DD)
            end_date: Fecha fin (YYYY-MM-DD)
            width: Ancho de la imagen en píxeles
            height: Alto de la imagen en píxeles
            max_cloud_coverage: Cobertura máxima de nubes (0-100)
            polygon_id: ID del polígono (para logging)

        Returns:
            bytes: Contenido del GeoTIFF con valores NDVI [-1, 1]

        Raises:
            httpx.HTTPError: Si falla la descarga
        """
        token = self.auth.ensure_authenticated()

        evalscript = build_ndvi_evalscript()
        request_payload = build_process_request(
            polygon_geojson=polygon_geojson,
            start_date=start_date,
            end_date=end_date,
            evalscript=evalscript,
            width=width,
            height=height,
            max_cloud_coverage=max_cloud_coverage
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        log_request_details("DOWNLOAD_NDVI", polygon_geojson, request_payload, polygon_id)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                self.PROCESS_URL,
                json=request_payload,
                headers=headers
            )

            success = (response.status_code == 200)
            log_response_details("DOWNLOAD_NDVI", response, success)

            response.raise_for_status()
            return response.content

    async def download_true_color(
        self,
        polygon_geojson: Dict,
        start_date: str,
        end_date: str,
        width: int = 512,
        height: int = 512,
        max_cloud_coverage: int = 20,
        polygon_id: Optional[int] = None
    ) -> bytes:
        """
        Descarga imagen RGB true-color (B04, B03, B02) como PNG.

        Args:
            polygon_geojson: Polígono en formato GeoJSON (geometry)
            start_date: Fecha inicio (YYYY-MM-DD)
            end_date: Fecha fin (YYYY-MM-DD)
            width: Ancho de la imagen en píxeles
            height: Alto de la imagen en píxeles
            max_cloud_coverage: Cobertura máxima de nubes (0-100)
            polygon_id: ID del polígono (para logging)

        Returns:
            bytes: Contenido del PNG con imagen RGB

        Raises:
            httpx.HTTPError: Si falla la descarga
        """
        token = self.auth.ensure_authenticated()

        evalscript = build_true_color_evalscript()
        request_payload = build_process_request(
            polygon_geojson=polygon_geojson,
            start_date=start_date,
            end_date=end_date,
            evalscript=evalscript,
            width=width,
            height=height,
            max_cloud_coverage=max_cloud_coverage,
            response_format="image/png"
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        log_request_details("DOWNLOAD_TRUE_COLOR", polygon_geojson, request_payload, polygon_id)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                self.PROCESS_URL,
                json=request_payload,
                headers=headers
            )

            success = (response.status_code == 200)
            log_response_details("DOWNLOAD_TRUE_COLOR", response, success)

            response.raise_for_status()
            return response.content

    async def check_availability(
        self,
        polygon_geojson: Dict,
        start_date: str,
        end_date: str,
        max_cloud_coverage: int = 20
    ) -> Dict:
        """
        Verifica disponibilidad de imágenes Sentinel-2.

        Args:
            polygon_geojson: Polígono en formato GeoJSON (geometry)
            start_date: Fecha inicio (YYYY-MM-DD)
            end_date: Fecha fin (YYYY-MM-DD)
            max_cloud_coverage: Cobertura máxima de nubes (0-100)

        Returns:
            Dict: Información sobre disponibilidad
        """
        token = self.auth.ensure_authenticated()

        coords = polygon_geojson.get('coordinates', [[]])[0]
        width, height = calculate_optimal_dimensions(coords, max_resolution_m_per_px=1000.0)

        evalscript = build_check_availability_evalscript()
        request_payload = build_process_request(
            polygon_geojson=polygon_geojson,
            start_date=start_date,
            end_date=end_date,
            evalscript=evalscript,
            width=width,
            height=height,
            max_cloud_coverage=max_cloud_coverage,
            response_format="image/png"
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        log_request_details("CHECK_AVAILABILITY", polygon_geojson, request_payload)

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.PROCESS_URL,
                    json=request_payload,
                    headers=headers
                )

                success = (response.status_code == 200)
                log_response_details("CHECK_AVAILABILITY", response, success)

                response.raise_for_status()

                return {
                    "available": True,
                    "date_range": {"from": start_date, "to": end_date},
                    "message": "Imagery available for the specified date range"
                }

        except httpx.HTTPError as e:
            if hasattr(e, 'response') and e.response is not None:
                log_response_details("CHECK_AVAILABILITY", e.response, False)

            logger.warning(f"❌ No imagery available: {str(e)}")
            return {
                "available": False,
                "date_range": {"from": start_date, "to": end_date},
                "message": f"No imagery available or request failed: {str(e)}"
            }
