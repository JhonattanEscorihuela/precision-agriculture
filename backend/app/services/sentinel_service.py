"""
Servicio de adquisición de imágenes Sentinel-2.
Maneja la autenticación OAuth2 con Copernicus DataSpace y la descarga
de bandas espectrales para análisis de cultivos.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import httpx
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session


# Configurar logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class SentinelService:
    """
    Servicio para interactuar con la API de Copernicus DataSpace
    y descargar imágenes Sentinel-2.
    """

    PROCESS_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"
    TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    STAC_URL = "https://stac.dataspace.copernicus.eu/v1/search"

    def __init__(self):
        """
        Inicializa el servicio con credenciales desde variables de entorno.
        """
        self.client_id = os.getenv("SENTINEL_CLIENT_ID")
        self.client_secret = os.getenv("SENTINEL_CLIENT_SECRET")

        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Missing credentials: Set SENTINEL_CLIENT_ID and SENTINEL_CLIENT_SECRET "
                "environment variables"
            )

        self._access_token: Optional[str] = None

    def authenticate(self) -> str:
        """
        Obtiene un token de acceso OAuth2 desde Copernicus DataSpace.

        Returns:
            str: Token de acceso válido

        Raises:
            Exception: Si falla la autenticación
        """
        logger.info("🔐 Authenticating with Copernicus DataSpace...")
        client = BackendApplicationClient(client_id=self.client_id)
        oauth = OAuth2Session(client=client)

        token_response = oauth.fetch_token(
            token_url=self.TOKEN_URL,
            client_id=self.client_id,
            client_secret=self.client_secret,
            include_client_id=True
        )

        self._access_token = token_response["access_token"]
        logger.info(f"✅ Authentication successful! Token: {self._access_token[:20]}...")
        return self._access_token

    def _ensure_authenticated(self):
        """
        Verifica que exista un token de acceso, si no, autentica.
        """
        if not self._access_token:
            self.authenticate()

    def _calculate_bbox(self, coords: List[List[float]]) -> Dict:
        """
        Calcula el bounding box de un conjunto de coordenadas.

        Args:
            coords: Lista de coordenadas [[lng, lat], ...]

        Returns:
            Dict con min/max lng/lat
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

    def _calculate_optimal_dimensions(
        self,
        coords: List[List[float]],
        max_resolution_m_per_px: float = 1000.0,
        min_dimension: int = 10
    ) -> Tuple[int, int]:
        """
        Calcula dimensiones óptimas (width, height) para una petición a Sentinel Hub
        asegurando que la resolución no exceda el límite de Sentinel Hub (1500 m/px).

        Args:
            coords: Lista de coordenadas [[lng, lat], ...]
            max_resolution_m_per_px: Resolución máxima deseada en metros por píxel
            min_dimension: Dimensión mínima en píxeles

        Returns:
            Tuple[int, int]: (width, height) en píxeles

        Notes:
            Sentinel Hub tiene un límite de 1500 m/px de resolución.
            Usamos un valor más conservador (1000 m/px por defecto) para tener margen.
        """
        bbox = self._calculate_bbox(coords)

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

    def _log_request_details(
        self,
        operation: str,
        polygon_geojson: Dict,
        request_payload: Dict,
        polygon_id: Optional[int] = None
    ):
        """
        Logging MUY detallado de la petición a Sentinel Hub.

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
            first = coords[0]
            last = coords[-1]
            is_closed = (first[0] == last[0] and first[1] == last[1])
            logger.info(f"¿Polígono cerrado? {is_closed}")
            if not is_closed:
                logger.warning("⚠️  ADVERTENCIA: El polígono NO está cerrado!")

        logger.info("")
        logger.info("--- 2️⃣  BOUNDING BOX CALCULADO ---")
        if coords:
            bbox = self._calculate_bbox(coords)
            logger.info(f"Min Longitude: {bbox['min_lng']:.6f}")
            logger.info(f"Max Longitude: {bbox['max_lng']:.6f}")
            logger.info(f"Min Latitude: {bbox['min_lat']:.6f}")
            logger.info(f"Max Latitude: {bbox['max_lat']:.6f}")
            logger.info(f"Centro: ({bbox['center_lng']:.6f}, {bbox['center_lat']:.6f})")
            logger.info(f"Dimensiones: {bbox['width_degrees']:.6f}° × {bbox['height_degrees']:.6f}°")

            # Estimación de tamaño en metros (aproximado)
            meters_per_deg_lat = 111000
            meters_per_deg_lng = 111000 * abs(bbox['center_lat'])
            width_m = bbox['width_degrees'] * meters_per_deg_lng
            height_m = bbox['height_degrees'] * meters_per_deg_lat
            logger.info(f"Tamaño aproximado: {width_m:.0f}m × {height_m:.0f}m")

        logger.info("")
        logger.info("--- 3️⃣  REQUEST JSON COMPLETO (sin token) ---")
        logger.info(json.dumps(request_payload, indent=2, ensure_ascii=False))

        logger.info("")
        logger.info(f"🌐 URL destino: {self.PROCESS_URL}")
        logger.info("=" * 100)
        logger.info("")

    def _log_response_details(
        self,
        operation: str,
        response: httpx.Response,
        success: bool
    ):
        """
        Logging MUY detallado de la respuesta de Sentinel Hub.

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
            start_date: Fecha inicio en formato ISO (YYYY-MM-DD)
            end_date: Fecha fin en formato ISO (YYYY-MM-DD)
            width: Ancho de la imagen en píxeles
            height: Alto de la imagen en píxeles
            max_cloud_coverage: Cobertura máxima de nubes permitida (0-100)

        Returns:
            bytes: Contenido del GeoTIFF con las bandas solicitadas

        Raises:
            httpx.HTTPError: Si falla la descarga
        """
        self._ensure_authenticated()

        # Construir evalscript dinámico para las bandas solicitadas
        bands_str = '", "'.join(bands)
        bands_output = ", ".join([f"sample.{band}" for band in bands])

        evalscript = f"""
//VERSION=3
function setup() {{
  return {{
    input: ["{bands_str}"],
    output: {{
      bands: {len(bands)},
      sampleType: "FLOAT32"
    }}
  }}
}}
function evaluatePixel(sample) {{
  return [{bands_output}];
}}
"""

        request_payload = {
            "input": {
                "bounds": {
                    "geometry": polygon_geojson,
                    "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"}
                },
                "data": [{
                    "type": "sentinel-2-l2a",
                    "dataFilter": {
                        "timeRange": {
                            "from": f"{start_date}T00:00:00Z",
                            "to": f"{end_date}T23:59:59Z"
                        },
                        "maxCloudCoverage": max_cloud_coverage
                    }
                }]
            },
            "output": {
                "width": width,
                "height": height,
                "responses": [{
                    "identifier": "default",
                    "format": {"type": "image/tiff"}
                }]
            },
            "evalscript": evalscript
        }

        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json"
        }

        # Logging MUY detallado del request
        self._log_request_details("DOWNLOAD_BANDS", polygon_geojson, request_payload, polygon_id)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                self.PROCESS_URL,
                json=request_payload,
                headers=headers
            )

            success = (response.status_code == 200)

            # Logging MUY detallado de la respuesta
            self._log_response_details("DOWNLOAD_BANDS", response, success)

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

        El NDVI se calcula como: (B08 - B04) / (B08 + B04)
        donde B08 es infrarrojo cercano (NIR) y B04 es rojo (Red).

        Args:
            polygon_geojson: Polígono en formato GeoJSON (geometry)
            start_date: Fecha inicio en formato ISO (YYYY-MM-DD)
            end_date: Fecha fin en formato ISO (YYYY-MM-DD)
            width: Ancho de la imagen en píxeles
            height: Alto de la imagen en píxeles
            max_cloud_coverage: Cobertura máxima de nubes permitida (0-100)

        Returns:
            bytes: Contenido del GeoTIFF con valores NDVI en rango [-1, 1]

        Raises:
            httpx.HTTPError: Si falla la descarga
        """
        self._ensure_authenticated()

        evalscript = """
//VERSION=3
function setup() {
  return {
    input: ["B04", "B08"],
    output: {
      bands: 1,
      sampleType: "FLOAT32"
    }
  }
}
function evaluatePixel(sample) {
  let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
  return [ndvi];
}
"""

        request_payload = {
            "input": {
                "bounds": {
                    "geometry": polygon_geojson,
                    "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"}
                },
                "data": [{
                    "type": "sentinel-2-l2a",
                    "dataFilter": {
                        "timeRange": {
                            "from": f"{start_date}T00:00:00Z",
                            "to": f"{end_date}T23:59:59Z"
                        },
                        "maxCloudCoverage": max_cloud_coverage
                    }
                }]
            },
            "output": {
                "width": width,
                "height": height,
                "responses": [{
                    "identifier": "default",
                    "format": {"type": "image/tiff"}
                }]
            },
            "evalscript": evalscript
        }

        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json"
        }

        # Logging MUY detallado del request
        self._log_request_details("DOWNLOAD_NDVI", polygon_geojson, request_payload, polygon_id)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                self.PROCESS_URL,
                json=request_payload,
                headers=headers
            )

            success = (response.status_code == 200)

            # Logging MUY detallado de la respuesta
            self._log_response_details("DOWNLOAD_NDVI", response, success)

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

        Útil para visualización y verificación visual de la parcela.

        Args:
            polygon_geojson: Polígono en formato GeoJSON (geometry)
            start_date: Fecha inicio en formato ISO (YYYY-MM-DD)
            end_date: Fecha fin en formato ISO (YYYY-MM-DD)
            width: Ancho de la imagen en píxeles
            height: Alto de la imagen en píxeles
            max_cloud_coverage: Cobertura máxima de nubes permitida (0-100)

        Returns:
            bytes: Contenido del PNG con imagen RGB

        Raises:
            httpx.HTTPError: Si falla la descarga
        """
        self._ensure_authenticated()

        evalscript = """
//VERSION=3
function setup() {
  return {
    input: ["B02", "B03", "B04"],
    output: {
      bands: 3,
      sampleType: "UINT8"
    }
  }
}
function evaluatePixel(sample) {
  // Stretch reflectance [0, 0.3] to [0, 255]
  const r = Math.min(255, Math.max(0, 255 * sample.B04 / 0.3));
  const g = Math.min(255, Math.max(0, 255 * sample.B03 / 0.3));
  const b = Math.min(255, Math.max(0, 255 * sample.B02 / 0.3));
  return [r, g, b];
}
"""

        request_payload = {
            "input": {
                "bounds": {
                    "geometry": polygon_geojson,
                    "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"}
                },
                "data": [{
                    "type": "sentinel-2-l2a",
                    "dataFilter": {
                        "timeRange": {
                            "from": f"{start_date}T00:00:00Z",
                            "to": f"{end_date}T23:59:59Z"
                        },
                        "maxCloudCoverage": max_cloud_coverage
                    }
                }]
            },
            "output": {
                "width": width,
                "height": height
            },
            "evalscript": evalscript
        }

        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json"
        }

        # Logging MUY detallado del request
        self._log_request_details("DOWNLOAD_TRUE_COLOR", polygon_geojson, request_payload, polygon_id)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                self.PROCESS_URL,
                json=request_payload,
                headers=headers
            )

            success = (response.status_code == 200)

            # Logging MUY detallado de la respuesta
            self._log_response_details("DOWNLOAD_TRUE_COLOR", response, success)

            response.raise_for_status()
            return response.content

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

        Llama a Process API para obtener cada banda por separado como GeoTIFF,
        valida tamaños, y persiste en BD via CRUD.

        Args:
            polygon_coords: Coordenadas del polígono [[lng, lat], ...]
            date: Fecha de adquisición (YYYY-MM-DD)
            polygon_id: ID del polígono en BD
            width: Ancho de la imagen en píxeles
            height: Alto de la imagen en píxeles
            max_cloud_coverage: Cobertura máxima de nubes (para filtro temporal)

        Returns:
            Dict con información de la adquisición:
            {
                "acquisition_id": int,
                "polygon_id": int,
                "date": str,
                "cloud_coverage": float,
                "size_b04_kb": float,
                "size_b08_kb": float
            }

        Raises:
            ValueError: Si las bandas exceden 10MB cada una
            httpx.HTTPError: Si falla la descarga
        """
        from datetime import datetime
        from app.models.acquisition import SentinelAcquisitionCreate
        from app.crud.acquisition import create_acquisition, get_acquisition_by_polygon_and_date

        logger.info(f"🛰️  Iniciando adquisición de bandas B04 y B08...")
        logger.info(f"   Polígono ID: {polygon_id}")
        logger.info(f"   Fecha: {date}")
        logger.info(f"   Dimensiones: {width}x{height}")

        # Construir geometría GeoJSON
        polygon_geojson = {
            "type": "Polygon",
            "coordinates": [polygon_coords]
        }

        # Verificar si ya existe esta adquisición (solo si se provee db_session)
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
            max_cloud=100  # Buscar el día específico sin filtro
        )

        cloud_coverage = 0.0
        if available_dates:
            cloud_coverage = available_dates[0]["cloud_cover"]
            logger.info(f"   Cloud coverage: {cloud_coverage}%")
        else:
            logger.warning(f"⚠️  No se encontró cloud_coverage para {date}, usando 0.0")

        # Crear registro en BD (solo si se provee db_session)
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
            # Si no hay sesión, retornar datos sin guardar (útil para tests)
            logger.warning("⚠️  No se proveyó db_session, retornando datos sin guardar en BD")
            return {
                "acquisition_id": -1,
                "polygon_id": polygon_id,
                "date": date,
                "cloud_coverage": cloud_coverage,
                "size_b04_kb": len(b04_bytes) / 1024,
                "size_b08_kb": len(b08_bytes) / 1024
            }

    async def get_available_dates(
        self,
        polygon_coords: List[List[float]],
        start_date: str,
        end_date: str,
        max_cloud: int = 20
    ) -> List[Dict]:
        """
        OE1 - Consulta STAC API para obtener fechas con imágenes disponibles.

        Filtra escenas Sentinel-2 L2A con cobertura de nubes ≤ max_cloud.
        STAC API no requiere autenticación.

        Args:
            polygon_coords: Coordenadas del polígono [[lng, lat], ...]
            start_date: Fecha inicio (YYYY-MM-DD)
            end_date: Fecha fin (YYYY-MM-DD)
            max_cloud: Cobertura máxima de nubes permitida (0-100)

        Returns:
            Lista de fechas disponibles ordenadas descendente:
            [
                {
                    "date": "2024-06-15",
                    "cloud_cover": 12.5,
                    "scene_id": "S2A_...",
                    "datetime": "2024-06-15T10:30:00Z"
                },
                ...
            ]

        Raises:
            httpx.HTTPError: Si falla la consulta a STAC API
        """
        logger.info(f"🔍 Consultando STAC API para fechas disponibles...")
        logger.info(f"   Rango: {start_date} → {end_date}")
        logger.info(f"   Max nubosidad: {max_cloud}%")

        # Construir payload para STAC API
        payload = {
            "collections": ["sentinel-2-l2a"],
            "datetime": f"{start_date}T00:00:00Z/{end_date}T23:59:59Z",
            "intersects": {
                "type": "Polygon",
                "coordinates": [polygon_coords]
            },
            "limit": 100,
            "fields": {
                "include": [
                    "properties.datetime",
                    "properties.eo:cloud_cover",
                    "id"
                ],
                "exclude": ["assets", "links", "geometry"]
            }
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.STAC_URL,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                data = response.json()

            features = data.get("features", [])
            logger.info(f"📦 STAC API retornó {len(features)} escenas totales")

            # Filtrar por cobertura de nubes y extraer información relevante
            # IMPORTANTE: Agrupar por fecha y quedarnos con la escena de menor nubosidad
            dates_dict = {}  # key: date, value: {date, cloud_cover, scene_id, datetime}

            for feature in features:
                props = feature.get("properties", {})
                cloud_cover = props.get("eo:cloud_cover", 100)

                if cloud_cover <= max_cloud:
                    datetime_str = props.get("datetime", "")
                    # Extraer solo la fecha (YYYY-MM-DD)
                    date_only = datetime_str.split("T")[0] if datetime_str else ""

                    # Si ya existe esta fecha, quedarnos con la de menor cloud_cover
                    if date_only in dates_dict:
                        if cloud_cover < dates_dict[date_only]["cloud_cover"]:
                            dates_dict[date_only] = {
                                "date": date_only,
                                "cloud_cover": round(cloud_cover, 2),
                                "scene_id": feature.get("id", ""),
                                "datetime": datetime_str
                            }
                    else:
                        dates_dict[date_only] = {
                            "date": date_only,
                            "cloud_cover": round(cloud_cover, 2),
                            "scene_id": feature.get("id", ""),
                            "datetime": datetime_str
                        }

            # Convertir dict a lista y ordenar por fecha descendente
            available_dates = list(dates_dict.values())
            available_dates.sort(key=lambda x: x["datetime"], reverse=True)

            logger.info(f"✅ {len(available_dates)} fechas únicas aptas (≤{max_cloud}% nubes)")

            return available_dates

        except httpx.HTTPError as e:
            logger.error(f"❌ Error consultando STAC API: {str(e)}")
            raise

    async def check_availability(
        self,
        polygon_geojson: Dict,
        start_date: str,
        end_date: str,
        max_cloud_coverage: int = 20
    ) -> Dict:
        """
        Verifica la disponibilidad de imágenes Sentinel-2 para un polígono y rango temporal.

        Args:
            polygon_geojson: Polígono en formato GeoJSON (geometry)
            start_date: Fecha inicio en formato ISO (YYYY-MM-DD)
            end_date: Fecha fin en formato ISO (YYYY-MM-DD)
            max_cloud_coverage: Cobertura máxima de nubes permitida (0-100)

        Returns:
            Dict: Información sobre disponibilidad de imágenes
                {
                    "available": bool,
                    "date_range": {"from": str, "to": str},
                    "message": str
                }
        """
        self._ensure_authenticated()

        # Calcular dimensiones óptimas basadas en el tamaño del polígono
        # para evitar exceder el límite de resolución de Sentinel Hub (1500 m/px)
        coords = polygon_geojson.get('coordinates', [[]])[0]
        width, height = self._calculate_optimal_dimensions(coords, max_resolution_m_per_px=1000.0)

        # Intentar una descarga pequeña para verificar disponibilidad
        evalscript = """
//VERSION=3
function setup() {
  return {
    input: ["B04"],
    output: {
      bands: 1,
      sampleType: "UINT8"
    }
  }
}
function evaluatePixel(sample) {
  return [sample.B04 * 255];
}
"""

        request_payload = {
            "input": {
                "bounds": {
                    "geometry": polygon_geojson,
                    "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"}
                },
                "data": [{
                    "type": "sentinel-2-l2a",
                    "dataFilter": {
                        "timeRange": {
                            "from": f"{start_date}T00:00:00Z",
                            "to": f"{end_date}T23:59:59Z"
                        },
                        "maxCloudCoverage": max_cloud_coverage
                    }
                }]
            },
            "output": {
                "width": width,
                "height": height
            },
            "evalscript": evalscript
        }

        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json"
        }

        # Logging MUY detallado del request
        self._log_request_details("CHECK_AVAILABILITY", polygon_geojson, request_payload)

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.PROCESS_URL,
                    json=request_payload,
                    headers=headers
                )

                success = (response.status_code == 200)

                # Logging MUY detallado de la respuesta
                self._log_response_details("CHECK_AVAILABILITY", response, success)

                response.raise_for_status()

                return {
                    "available": True,
                    "date_range": {"from": start_date, "to": end_date},
                    "message": "Imagery available for the specified date range"
                }

        except httpx.HTTPError as e:
            # Si hay error, también loggeamos la respuesta
            if hasattr(e, 'response') and e.response is not None:
                self._log_response_details("CHECK_AVAILABILITY", e.response, False)

            logger.warning(f"❌ No imagery available: {str(e)}")
            return {
                "available": False,
                "date_range": {"from": start_date, "to": end_date},
                "message": f"No imagery available or request failed: {str(e)}"
            }
