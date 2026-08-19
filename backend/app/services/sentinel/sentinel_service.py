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
from .geometry import calculate_optimal_dimensions

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
        polygon_id: Optional[int] = None,
        scene_id: Optional[str] = None
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
            scene_id: Scene ID específico para forzar escena exacta (opcional)

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
            polygon_id=polygon_id,
            scene_id=scene_id
        )

    async def download_true_color_tiff(
        self,
        polygon_geojson: Dict,
        start_date: str,
        end_date: str,
        width: int = 512,
        height: int = 512,
        max_cloud_coverage: int = 20,
        polygon_id: Optional[int] = None,
        scene_id: Optional[str] = None
    ) -> bytes:
        """
        Descarga imagen RGB true-color como TIFF georreferenciado.

        Args:
            polygon_geojson: Polígono en formato GeoJSON (geometry)
            start_date: Fecha inicio (YYYY-MM-DD)
            end_date: Fecha fin (YYYY-MM-DD)
            width: Ancho en píxeles
            height: Alto en píxeles
            max_cloud_coverage: Cobertura máxima de nubes (0-100)
            polygon_id: ID del polígono (para logging)
            scene_id: Scene ID específico para forzar escena exacta (opcional)

        Returns:
            bytes: Contenido del TIFF georreferenciado
        """
        return await self.process_client.download_true_color_tiff(
            polygon_geojson=polygon_geojson,
            start_date=start_date,
            end_date=end_date,
            width=width,
            height=height,
            max_cloud_coverage=max_cloud_coverage,
            polygon_id=polygon_id,
            scene_id=scene_id
        )

    async def download_scene_classification(
        self,
        polygon_geojson: Dict,
        start_date: str,
        end_date: str,
        width: int = 512,
        height: int = 512,
        max_cloud_coverage: int = 20,
        polygon_id: Optional[int] = None
    ) -> bytes:
        """Descarga SCL y dataMask para calcular nubosidad dentro de la parcela."""
        return await self.process_client.download_scene_classification(
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
        max_cloud_coverage: int = 20,
        scene_id: Optional[str] = None
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

                # Completar datos faltantes si es necesario
                needs_update = False

                if existing.scl_data is None or existing.parcel_cloud_cover is None:
                    logger.info("☁️  Completando métricas SCL faltantes de la adquisición existente...")
                    scl_width, scl_height = calculate_optimal_dimensions(
                        polygon_coords,
                        max_resolution_m_per_px=20.0,
                    )
                    scl_bytes = await self.download_scene_classification(
                        polygon_geojson=polygon_geojson,
                        start_date=date,
                        end_date=date,
                        width=scl_width,
                        height=scl_height,
                        max_cloud_coverage=max_cloud_coverage,
                        polygon_id=polygon_id
                    )
                    from app.services.cloud_coverage_service import calculate_parcel_cloud_coverage
                    metrics = calculate_parcel_cloud_coverage(scl_bytes, polygon_geojson)
                    existing.scl_data = scl_bytes
                    existing.parcel_cloud_cover = metrics["parcel_cloud_cover"]
                    existing.parcel_shadow_cover = metrics["parcel_shadow_cover"]
                    existing.valid_pixel_percentage = metrics["valid_pixel_percentage"]
                    existing.usable_pixel_percentage = metrics["usable_pixel_percentage"]
                    existing.quality_status = metrics["quality_status"]
                    existing.cloud_method = "SCL"
                    existing.scene_id = existing.scene_id or scene_id
                    needs_update = True

                if existing.rgb_png is None:
                    logger.info("🌈 Completando RGB PNG faltante de la adquisición existente...")
                    rgb_png_bytes = await self.download_true_color(
                        polygon_geojson=polygon_geojson,
                        start_date=date,
                        end_date=date,
                        width=width,
                        height=height,
                        max_cloud_coverage=max_cloud_coverage,
                        polygon_id=polygon_id
                    )
                    rgb_size_kb = len(rgb_png_bytes) / 1024
                    logger.info(f"✅ RGB PNG descargado: {rgb_size_kb:.2f} KB")
                    existing.rgb_png = rgb_png_bytes
                    needs_update = True

                if needs_update:
                    db_session.add(existing)
                    await db_session.commit()
                    await db_session.refresh(existing)
                return {
                    "acquisition_id": existing.id,
                    "polygon_id": existing.polygon_id,
                    "date": existing.acquisition_date,
                    "cloud_coverage": existing.cloud_coverage,
                    "scene_id": existing.scene_id,
                    "parcel_cloud_cover": existing.parcel_cloud_cover,
                    "parcel_shadow_cover": existing.parcel_shadow_cover,
                    "valid_pixel_percentage": existing.valid_pixel_percentage,
                    "usable_pixel_percentage": existing.usable_pixel_percentage,
                    "quality_status": existing.quality_status,
                    "cloud_method": existing.cloud_method,
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

        # Calcular nubosidad real dentro del polígono con SCL y dataMask.
        logger.info("☁️  Calculando nubosidad SCL dentro de la parcela...")
        scl_width, scl_height = calculate_optimal_dimensions(
            polygon_coords,
            max_resolution_m_per_px=20.0,
        )
        scl_bytes = await self.download_scene_classification(
            polygon_geojson=polygon_geojson,
            start_date=date,
            end_date=date,
            width=scl_width,
            height=scl_height,
            max_cloud_coverage=max_cloud_coverage,
            polygon_id=polygon_id
        )
        from app.services.cloud_coverage_service import calculate_parcel_cloud_coverage
        parcel_quality = calculate_parcel_cloud_coverage(scl_bytes, polygon_geojson)

        # Descargar RGB PNG en la misma adquisición (garantiza misma escena)
        logger.info("🌈 Descargando imagen RGB true-color...")
        rgb_png_bytes = await self.download_true_color(
            polygon_geojson=polygon_geojson,
            start_date=date,
            end_date=date,
            width=width,
            height=height,
            max_cloud_coverage=max_cloud_coverage,
            polygon_id=polygon_id
        )
        rgb_size_kb = len(rgb_png_bytes) / 1024
        logger.info(f"✅ RGB PNG descargado: {rgb_size_kb:.2f} KB")

        # Obtener cloud_coverage del día desde STAC
        logger.info("☁️  Obteniendo cloud_coverage desde STAC...")
        try:
            available_dates = await self.get_available_dates(
                polygon_coords=polygon_coords,
                start_date=date,
                end_date=date,
                max_cloud=100
            )
        except Exception as metadata_error:
            logger.warning(
                "No se pudo recuperar metadata STAC para %s; "
                "las bandas y métricas SCL sí son válidas: %s",
                date,
                metadata_error,
            )
            available_dates = []

        cloud_coverage = None
        if available_dates:
            selected_scene = available_dates[0]
            cloud_coverage = selected_scene["cloud_cover"]
            resolved_scene_id = selected_scene.get("scene_id")
            if scene_id and resolved_scene_id and scene_id != resolved_scene_id:
                logger.warning(
                    "La escena solicitada %s no coincide con la escena leastCC %s; "
                    "se usará la resuelta por STAC",
                    scene_id,
                    resolved_scene_id,
                )
            scene_id = resolved_scene_id or scene_id
            logger.info(f"   Cloud coverage: {cloud_coverage}%")
        else:
            logger.warning(f"⚠️  No se encontró cloud_coverage global para {date}; se guardará NULL")

        # Crear registro en BD
        if db_session:
            logger.info("💾 Guardando en base de datos...")
            acquisition_data = SentinelAcquisitionCreate(
                polygon_id=polygon_id,
                acquisition_date=date,
                cloud_coverage=cloud_coverage,
                scene_id=scene_id,
                parcel_cloud_cover=parcel_quality["parcel_cloud_cover"],
                parcel_shadow_cover=parcel_quality["parcel_shadow_cover"],
                valid_pixel_percentage=parcel_quality["valid_pixel_percentage"],
                usable_pixel_percentage=parcel_quality["usable_pixel_percentage"],
                quality_status=parcel_quality["quality_status"],
                cloud_method="SCL",
                width=width,
                height=height,
                b04_data=b04_bytes,
                b08_data=b08_bytes,
                scl_data=scl_bytes,
                rgb_png=rgb_png_bytes,
                created_at=datetime.utcnow().isoformat()
            )

            acquisition = await create_acquisition(db_session, acquisition_data)
            logger.info(f"✅ Adquisición guardada con ID: {acquisition.id}")

            return {
                "acquisition_id": acquisition.id,
                "polygon_id": acquisition.polygon_id,
                "date": acquisition.acquisition_date,
                "cloud_coverage": acquisition.cloud_coverage,
                "scene_id": acquisition.scene_id,
                "parcel_cloud_cover": acquisition.parcel_cloud_cover,
                "parcel_shadow_cover": acquisition.parcel_shadow_cover,
                "valid_pixel_percentage": acquisition.valid_pixel_percentage,
                "usable_pixel_percentage": acquisition.usable_pixel_percentage,
                "quality_status": acquisition.quality_status,
                "cloud_method": acquisition.cloud_method,
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
                "scene_id": scene_id,
                **parcel_quality,
                "cloud_method": "SCL",
                "size_b04_kb": len(b04_bytes) / 1024,
                "size_b08_kb": len(b08_bytes) / 1024
            }
