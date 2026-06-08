#!/usr/bin/env python3
"""
OE1 - Script de evidencia: Generación de tabla de disponibilidad de imágenes.

Consulta el STAC API de Copernicus para las 3 parcelas de referencia del SRRG
y genera un CSV con todas las fechas aptas (cloud_cover ≤ 20%).

Evidencia para reporte académico - Actividad 3 del OE1.
"""

import asyncio
import httpx
import csv
from datetime import datetime
from typing import List, Dict


# Parcelas de referencia - SRRG, Calabozo, Guárico, Venezuela
PARCELAS = {
    "211": {
        "coords": [
            [-67.528058, 8.8441233],
            [-67.5153475, 8.8386166],
            [-67.5103962, 8.8478932],
            [-67.522828, 8.8534209],
            [-67.528058, 8.8441233]
        ],
        "periodo": {"start": "2024-01-01", "end": "2025-06-01"}
    },
    "217": {
        "coords": [
            [-67.538379, 8.8042214],
            [-67.5369724, 8.8130876],
            [-67.5351396, 8.8123084],
            [-67.5337757, 8.8125401],
            [-67.5239405, 8.8082815],
            [-67.5257482, 8.7980897],
            [-67.538379, 8.8042214]
        ],
        "periodo": {"start": "2024-01-01", "end": "2024-12-31"}
    },
    "85": {
        "coords": [
            [-67.586587, 8.8508969],
            [-67.5991461, 8.8654285],
            [-67.5869706, 8.8659561],
            [-67.5776965, 8.8549892],
            [-67.586587, 8.8508969]
        ],
        "periodo": {"start": "2025-01-01", "end": "2026-06-01"}
    }
}

STAC_URL = "https://stac.dataspace.copernicus.eu/v1/search"
MAX_CLOUD = 20


async def get_available_dates(
    polygon_coords: List[List[float]],
    start_date: str,
    end_date: str,
    max_cloud: int = 20
) -> List[Dict]:
    """
    Consulta STAC API para obtener fechas disponibles.

    Args:
        polygon_coords: Coordenadas del polígono [[lng, lat], ...]
        start_date: Fecha inicio (YYYY-MM-DD)
        end_date: Fecha fin (YYYY-MM-DD)
        max_cloud: Cobertura máxima de nubes (0-100)

    Returns:
        Lista de fechas con información de nubosidad
    """
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

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            STAC_URL,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        data = response.json()

    features = data.get("features", [])

    # Filtrar por nubosidad y agrupar por fecha (quedarse con menor nubosidad)
    dates_dict = {}

    for feature in features:
        props = feature.get("properties", {})
        cloud_cover = props.get("eo:cloud_cover", 100)

        if cloud_cover <= max_cloud:
            datetime_str = props.get("datetime", "")
            date_only = datetime_str.split("T")[0] if datetime_str else ""

            if date_only:
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

    # Convertir a lista y ordenar por fecha
    available_dates = list(dates_dict.values())
    available_dates.sort(key=lambda x: x["date"])

    return available_dates


async def main():
    """
    Función principal: consulta las 3 parcelas y genera CSV + resumen.
    """
    print("=" * 80)
    print("OE1 - GENERACIÓN DE TABLA DE DISPONIBILIDAD DE IMÁGENES SENTINEL-2")
    print("=" * 80)
    print()
    print("Configuración:")
    print(f"  Max nubosidad: {MAX_CLOUD}%")
    print(f"  Parcelas: 211, 217, 85 (SRRG, Calabozo, Guárico, Venezuela)")
    print()

    all_results = []

    for parcela_id, info in PARCELAS.items():
        coords = info["coords"]
        periodo = info["periodo"]
        start = periodo["start"]
        end = periodo["end"]

        print(f"📍 Consultando Parcela {parcela_id}...")
        print(f"   Período: {start} → {end}")

        try:
            dates = await get_available_dates(
                polygon_coords=coords,
                start_date=start,
                end_date=end,
                max_cloud=MAX_CLOUD
            )

            print(f"   ✅ {len(dates)} fechas aptas encontradas")
            print()

            # Agregar a resultados
            for date_info in dates:
                all_results.append({
                    "parcela": parcela_id,
                    "fecha": date_info["date"],
                    "cloud_cover_pct": date_info["cloud_cover"],
                    "apta": "SI"
                })

        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            print()

    # Guardar CSV
    csv_path = "tasks/tabla_disponibilidad_oe1.csv"

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["parcela", "fecha", "cloud_cover_pct", "apta"])
        writer.writeheader()
        writer.writerows(all_results)

    print("=" * 80)
    print("RESULTADOS GUARDADOS")
    print("=" * 80)
    print(f"📄 CSV generado: {csv_path}")
    print(f"📊 Total de registros: {len(all_results)}")
    print()

    # Resumen por parcela
    print("=" * 80)
    print("RESUMEN POR PARCELA")
    print("=" * 80)

    for parcela_id in ["211", "217", "85"]:
        parcela_dates = [r for r in all_results if r["parcela"] == parcela_id]
        periodo = PARCELAS[parcela_id]["periodo"]
        total_days = (
            datetime.strptime(periodo["end"], "%Y-%m-%d") -
            datetime.strptime(periodo["start"], "%Y-%m-%d")
        ).days

        print(f"Parcela {parcela_id}: {len(parcela_dates)} fechas aptas de {total_days} días consultados")

    print()
    print("=" * 80)
    print("✅ EVIDENCIA GENERADA EXITOSAMENTE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
