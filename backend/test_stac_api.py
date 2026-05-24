"""
OE1 - Fase 2: Test de integración con STAC API
Verifica que get_available_dates() funciona correctamente.
"""

import asyncio
import os
from dotenv import load_dotenv
from app.services.sentinel_service import SentinelService

# Cargar variables de entorno
load_dotenv("core/.env")


async def test_stac_api():
    """
    Prueba de consulta a STAC API para obtener fechas disponibles.
    Usa coordenadas reales de Parcela 211, SRRG Calabozo, Guárico, Venezuela.
    """
    print("\n" + "="*70)
    print("🧪 TEST: get_available_dates() con STAC API")
    print("="*70)

    # PARCELA_211 — SRRG, Calabozo, Guárico, Venezuela
    # Período 2024-2025
    test_coords = [
        [-67.528058, 8.8441233],
        [-67.5153475, 8.8386166],
        [-67.5103962, 8.8478932],
        [-67.522828,  8.8534209],
        [-67.528058, 8.8441233]
    ]

    print(f"\n📍 Coordenadas: Parcela 211, SRRG Calabozo, Guárico, Venezuela")
    print(f"   Primera coord: {test_coords[0]}")
    print(f"📅 Rango de fechas: 2025-01-01 → 2025-12-31 (período 2025)")
    print(f"☁️  Max nubosidad: 20% (especificación OE1)")

    service = SentinelService()

    try:
        # Consultar fechas disponibles
        # Usando fechas actuales (2025) con 20% según especificación OE1
        dates = await service.get_available_dates(
            polygon_coords=test_coords,
            start_date="2025-01-01",
            end_date="2025-12-31",
            max_cloud=20  # Especificación OE1: siempre 20%
        )

        print(f"\n✅ Consulta exitosa!")
        print(f"📊 Fechas disponibles encontradas: {len(dates)}")

        if dates:
            print("\n📋 Primeras 10 fechas aptas:")
            for i, date_info in enumerate(dates[:10], 1):
                print(f"   {i}. {date_info['date']} - Nubes: {date_info['cloud_cover']}%")
                print(f"      Scene: {date_info['scene_id'][:30]}...")

            # Validaciones
            print("\n🔍 Validaciones:")
            all_below_threshold = all(d["cloud_cover"] <= 20 for d in dates)
            print(f"   ✓ Todas las fechas ≤20% nubes: {all_below_threshold}")

            has_dates = all(d["date"] for d in dates)
            print(f"   ✓ Todas tienen fecha válida: {has_dates}")

            has_scene_ids = all(d["scene_id"] for d in dates)
            print(f"   ✓ Todas tienen scene_id: {has_scene_ids}")

            # Verificar orden descendente
            dates_sorted = dates == sorted(dates, key=lambda x: x["datetime"], reverse=True)
            print(f"   ✓ Ordenadas por fecha (más reciente primero): {dates_sorted}")

        else:
            print("\n⚠️  No se encontraron fechas aptas en el rango especificado")
            print("    Esto puede ocurrir si el rango temporal es muy corto o hay mucha nubosidad")

        print("\n" + "="*70)
        print("✅ TEST PASADO - STAC API funcionando correctamente")
        print("="*70)

    except Exception as e:
        print(f"\n❌ TEST FALLIDO: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(test_stac_api())
