"""
Módulo cliente para STAC API de Copernicus DataSpace.
Responsabilidad: Búsqueda de fechas disponibles (metadatos).
"""

import logging
from typing import Dict, List
import httpx

logger = logging.getLogger(__name__)


class STACClient:
    """Cliente para interactuar con STAC API (sin autenticación)."""

    STAC_URL = "https://stac.dataspace.copernicus.eu/v1/search"

    async def get_available_dates(
        self,
        polygon_coords: List[List[float]],
        start_date: str,
        end_date: str,
        max_cloud: int = 20
    ) -> List[Dict]:
        """
        Consulta STAC API para obtener fechas con imágenes disponibles.

        Implementa paginación para obtener TODAS las escenas disponibles.
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

        payload = {
            "collections": ["sentinel-2-l2a"],
            "datetime": f"{start_date}T00:00:00Z/{end_date}T23:59:59Z",
            "intersects": {
                "type": "Polygon",
                "coordinates": [polygon_coords]
            },
            "limit": 100,  # Máximo eficiente por página
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
            all_features = []
            page = 1

            async with httpx.AsyncClient(timeout=60.0) as client:
                # Primera página
                response = await client.post(
                    self.STAC_URL,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                data = response.json()

                features = data.get("features", [])
                all_features.extend(features)
                logger.info(f"📄 Página {page}: {len(features)} escenas")
                print(f"📄 Página {page}: {len(features)} escenas")  # Debug print

                # Verificar si hay más páginas (buscar link con rel="next")
                links = data.get("links", [])
                next_link = None
                for link in links:
                    if link.get("rel") == "next":
                        next_link = link
                        break

                # Paginar si hay más resultados
                while next_link:
                    page += 1

                    # El link next incluye method, href y body con token
                    next_url = next_link.get("href")
                    next_method = next_link.get("method", "POST")
                    next_body = next_link.get("body", {})

                    if next_method == "POST" and next_body:
                        response = await client.post(
                            next_url,
                            json=next_body,
                            headers={"Content-Type": "application/json"}
                        )
                    else:
                        response = await client.get(
                            next_url,
                            headers={"Content-Type": "application/json"}
                        )

                    response.raise_for_status()
                    data = response.json()

                    features = data.get("features", [])
                    all_features.extend(features)
                    logger.info(f"📄 Página {page}: {len(features)} escenas")
                    print(f"📄 Página {page}: {len(features)} escenas")  # Debug print

                    # Buscar siguiente página
                    links = data.get("links", [])
                    next_link = None
                    for link in links:
                        if link.get("rel") == "next":
                            next_link = link
                            break

            logger.info(f"📦 Total escenas obtenidas (todas las páginas): {len(all_features)}")
            print(f"📦 Total escenas obtenidas (todas las páginas): {len(all_features)}")  # Debug print

            # Filtrar por cobertura de nubes y extraer información relevante
            # Agrupar por fecha y quedarnos con la escena de menor nubosidad
            dates_dict = {}

            for feature in all_features:
                props = feature.get("properties", {})
                cloud_cover = props.get("eo:cloud_cover", 100)

                if cloud_cover <= max_cloud:
                    datetime_str = props.get("datetime", "")
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
