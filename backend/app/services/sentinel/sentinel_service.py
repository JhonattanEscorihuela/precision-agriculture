"""
Servicio principal de adquisición de imágenes Sentinel-2.
Orquesta los módulos: auth, stac_client, process_client, geometry.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from .auth import SentinelAuth
from .stac_client import STACClient
from .process_client import ProcessClient

logger = logging.getLogger(__name__)


class SentinelService:
    """
    Servicio orquestador para interactuar con Copernicus DataSpace.
    Combina autenticación, búsqueda STAC y descarga Process API.
    """

    def __init__(self):
        """Inicializa componentes del servicio."""
        self.auth = SentinelAuth()
        self.stac_client = STACClient()
        self.process_client = ProcessClient(self.auth)

    def authenticate(self) -> str:
        """Autentica y retorna token de acceso."""
        return self.auth.authenticate()

    async def get_available_dates(
        self,
        polygon_coords: List[List[float]],
        start_date: str,
        end_date: str,
        max_cloud: int = 20
    ) -> List[Dict]:
        """
        OE1 - Consulta STAC API para obtener fechas con imágenes disponibles.

        Args:
            polygon_coords: Coordenadas del polígono [[lng, lat], ...]
            start_date: Fecha inicio (YYYY-MM-DD)
            end_date: Fecha fin (YYYY-MM-DD)
            max_cloud: Cobertura máxima de nubes (0-100)

        Returns:
            Lista de fechas disponibles con metadata
        """
        return await self.stac_client.get_available_dates(
            polygon_coords=polygon_coords,
            start_date=start_date,
            end_date=end_date,
            max_cloud=max_cloud
        )

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
        Descarga bandas espectrales específicas como GeoTIFF.

        Args:
            polygon_geojson: Polígono en formato GeoJSON (geometry)
            bands: Lista de bandas (ej: ["B04", "B08"])
            start_date: Fecha inicio (YYYY-MM-DD)
            end_date: Fecha fin (YYYY-MM-DD)
            width: Ancho en píxeles
            height: Alto en píxeles
            max_cloud_coverage: Cobertura máxima de nubes (0-100)
            polygon_id: ID del polígono (para logging)

        Returns:
            bytes: Contenido del GeoTIFF
        """
        return await self.process_client.download_bands(
            polygon_geojson=polygon_geojson,
            bands=bands,
            start_date=start_date,
            end_date=end_date,
            width=width,
            height=height,
            max_cloud_coverage=max_cloud_coverage,
            polygon_id=polygon_id
        )

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
        Descarga NDVI calculado por Sentinel Hub como GeoTIFF.

        Args:
            polygon_geojson: Polígono en formato GeoJSON (geometry)
            start_date: Fecha inicio (YYYY-MM-DD)
            end_date: Fecha fin (YYYY-MM-DD)
            width: Ancho en píxeles
            height: Alto en píxeles
            max_cloud_coverage: Cobertura máxima de nubes (0-100)
            polygon_id: ID del polígono (para logging)

        Returns:
            bytes: Contenido del GeoTIFF con NDVI
        """
        return await self.process_client.download_ndvi(
            polygon_geojson=polygon_geojson,
            start_date=start_date,
            end_date=end_date,
            width=width,
            height=height,
            max_cloud_coverage=max_cloud_coverage,
            polygon_id=polygon_id
        )

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
        Descarga imagen RGB true-color como PNG.

        Args:
            polygon_geojson: Polígono en formato GeoJSON (geometry)
            start_date: Fecha inicio (YYYY-MM-DD)
            end_date: Fecha fin (YYYY-MM-DD)
            width: Ancho en píxeles
            height: Alto en píxeles
            max_cloud_coverage: Cobertura máxima de nubes (0-100)
            polygon_id: ID del polígono (para logging)

        Returns:
            bytes: Contenido del PNG
        """
        return await self.process_client.download_true_color(
            polygon_geojson=polygon_geojson,
            start_date=start_date,
            end_date=end_date,
            width=width,
            height=height,
            max_cloud_coverage=max_cloud_coverage,
            polygon_id=polygon_id
        )

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
        return await self.process_client.check_availability(
            polygon_geojson=polygon_geojson,
            start_date=start_date,
            end_date=end_date,
            max_cloud_coverage=max_cloud_coverage
        )

    async def acquire_bands(
        self,
        polygon_coords: List[List[float]],
        date: str,
        polygon_id: int,
        db_session = None,
        width: int = 512,
        height: int = 512,
        max_cloud_coverage: int = 20
    ) -> Dict:
        """
        OE1 - Descarga bandas B04 y B08 y las guarda en la base de datos.

        Args:
            polygon_coords: Coordenadas del polígono [[lng, lat], ...]
            date: Fecha de adquisición (YYYY-MM-DD)
            polygon_id: ID del polígono en BD
            db_session: Sesión de base de datos (opcional)
            width: Ancho en píxeles
            height: Alto en píxeles
            max_cloud_coverage: Cobertura máxima de nubes

        Returns:
            Dict con información de la adquisición
        """
        from app.models.acquisition import SentinelAcquisitionCreate
        from app.crud.acquisition import create_acquisition, get_acquisition_by_polygon_and_date

        logger.info(f"🛰️  Iniciando adquisición de bandas B04 y B08...")
        logger.info(f"   Polígono ID: {polygon_id}")
        logger.info(f"   Fecha: {date}")
        logger.info(f"   Dimensiones: {width}x{height}")

        polygon_geojson = {
            "type": "Polygon",
            "coordinates": [polygon_coords]
        }

        # Verificar si ya existe esta adquisición
        if db_session:
            existing = await get_acquisition_by_polygon_and_date(db_session, polygon_id, date)
            if existing:
                logger.warning(f"⚠️  Ya existe adquisición para polígono {polygon_id} en {date}")
                return {
                    "acquisition_id": existing.id,
                    "polygon_id": existing.polygon_id,
                    "date": existing.acquisition_date,
                    "cloud_coverage": existing.cloud_coverage,
                    "size_b04_kb": len(existing.b04_data) / 1024,
                    "size_b08_kb": len(existing.b08_data) / 1024,
                    "already_existed": True
                }

        # Descargar B04 (Red band)
        logger.info("📥 Descargando banda B04 (Red)...")
        b04_bytes = await self.download_bands(
            polygon_geojson=polygon_geojson,
            bands=["B04"],
            start_date=date,
            end_date=date,
            width=width,
            height=height,
            max_cloud_coverage=max_cloud_coverage,
            polygon_id=polygon_id
        )

        # Validar tamaño B04
        b04_size_mb = len(b04_bytes) / (1024 * 1024)
        logger.info(f"✅ B04 descargada: {b04_size_mb:.2f} MB")
        if b04_size_mb > 10:
            raise ValueError(f"B04 excede 10MB: {b04_size_mb:.2f} MB")

        # Descargar B08 (NIR band)
        logger.info("📥 Descargando banda B08 (NIR)...")
        b08_bytes = await self.download_bands(
            polygon_geojson=polygon_geojson,
            bands=["B08"],
            start_date=date,
            end_date=date,
            width=width,
            height=height,
            max_cloud_coverage=max_cloud_coverage,
            polygon_id=polygon_id
        )

        # Validar tamaño B08
        b08_size_mb = len(b08_bytes) / (1024 * 1024)
        logger.info(f"✅ B08 descargada: {b08_size_mb:.2f} MB")
        if b08_size_mb > 10:
            raise ValueError(f"B08 excede 10MB: {b08_size_mb:.2f} MB")

        # Obtener cloud_coverage del día desde STAC
        logger.info("☁️  Obteniendo cloud_coverage desde STAC...")
        available_dates = await self.get_available_dates(
            polygon_coords=polygon_coords,
            start_date=date,
            end_date=date,
            max_cloud=100
        )

        cloud_coverage = 0.0
        if available_dates:
            cloud_coverage = available_dates[0]["cloud_cover"]
            logger.info(f"   Cloud coverage: {cloud_coverage}%")
        else:
            logger.warning(f"⚠️  No se encontró cloud_coverage para {date}, usando 0.0")

        # Crear registro en BD
        if db_session:
            logger.info("💾 Guardando en base de datos...")
            acquisition_data = SentinelAcquisitionCreate(
                polygon_id=polygon_id,
                acquisition_date=date,
                cloud_coverage=cloud_coverage,
                width=width,
                height=height,
                b04_data=b04_bytes,
                b08_data=b08_bytes,
                created_at=datetime.utcnow().isoformat()
            )

            acquisition = await create_acquisition(db_session, acquisition_data)
            logger.info(f"✅ Adquisición guardada con ID: {acquisition.id}")

            return {
                "acquisition_id": acquisition.id,
                "polygon_id": acquisition.polygon_id,
                "date": acquisition.acquisition_date,
                "cloud_coverage": acquisition.cloud_coverage,
                "size_b04_kb": len(b04_bytes) / 1024,
                "size_b08_kb": len(b08_bytes) / 1024,
                "already_existed": False
            }
        else:
            logger.warning("⚠️  No se proveyó db_session, retornando datos sin guardar en BD")
            return {
                "acquisition_id": -1,
                "polygon_id": polygon_id,
                "date": date,
                "cloud_coverage": cloud_coverage,
                "size_b04_kb": len(b04_bytes) / 1024,
                "size_b08_kb": len(b08_bytes) / 1024
            }
