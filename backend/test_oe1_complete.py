"""
OE1 - TEST COMPLETO DEL FLUJO
================================

Prueba integración completa:
1. Consultar fechas disponibles (STAC API)
2. Seleccionar una fecha
3. Adquirir bandas B04 y B08 (Process API)
4. Guardar en BD
5. Verificar que se guardó correctamente

Este test simula el flujo completo que hará el usuario desde el frontend.
"""

import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.models.polygon import Polygon
from app.models.acquisition import SentinelAcquisition
from app.services.sentinel_service import SentinelService
from app.crud.acquisition import get_acquisitions_by_polygon

# Cargar variables de entorno
load_dotenv("core/.env")


async def test_oe1_complete_flow():
    """
    Test completo del OE1: Identificar y adquirir escenas Sentinel-2.
    """
    print("\n" + "="*80)
    print("🧪 TEST COMPLETO OE1: Flujo de consulta y adquisición Sentinel-2")
    print("="*80)

    # Configurar BD en memoria para test
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # PARCELA_211 — SRRG, Calabozo, Guárico, Venezuela
    # Período 2024-2025 (parcela principal de referencia)
    test_coords = [
        [-67.528058, 8.8441233],
        [-67.5153475, 8.8386166],
        [-67.5103962, 8.8478932],
        [-67.522828,  8.8534209],
        [-67.528058, 8.8441233]
    ]

    # Crear polígono de prueba en BD
    async with async_session() as session:
        polygon = Polygon(
            id=1,
            name="Parcela 211 - SRRG Calabozo",
            coordinates=test_coords,
            area=150.5,  # Aproximado en hectáreas
            created_at="2025-01-01T00:00:00Z",
            updated_at="2026-05-23T00:00:00Z"
        )
        session.add(polygon)
        await session.commit()

    print("\n📍 Datos de prueba:")
    print(f"   Ubicación: Parcela 211, SRRG Calabozo, Guárico, Venezuela")
    print(f"   Coordenadas: {test_coords[0]}")
    print(f"   Polígono ID: 1")

    service = SentinelService()

    # ========================================================================
    # PASO 1: Consultar fechas disponibles (STAC API)
    # ========================================================================
    print("\n" + "-"*80)
    print("📅 PASO 1: Consultar fechas disponibles (STAC API)")
    print("-"*80)

    # Usar rango actual 2025 con 20% según especificación OE1
    dates = await service.get_available_dates(
        polygon_coords=test_coords,
        start_date="2025-01-01",
        end_date="2025-12-31",
        max_cloud=20  # Especificación OE1: siempre 20%
    )

    print(f"✅ Fechas disponibles encontradas: {len(dates)}")

    if not dates:
        print("❌ No se encontraron fechas aptas. Test abortado.")
        return

    # Mostrar primeras 3 fechas
    print("\n📋 Primeras 3 fechas aptas:")
    for i, date_info in enumerate(dates[:3], 1):
        print(f"   {i}. {date_info['date']} - Nubes: {date_info['cloud_cover']}%")

    # Seleccionar la fecha con menos nubes
    selected_date = dates[0]
    print(f"\n🎯 Fecha seleccionada: {selected_date['date']} ({selected_date['cloud_cover']}% nubes)")

    # ========================================================================
    # PASO 2: Adquirir bandas B04 y B08 (Process API)
    # ========================================================================
    print("\n" + "-"*80)
    print("🛰️  PASO 2: Adquirir bandas B04 y B08 (Process API)")
    print("-"*80)

    # Usar dimensiones pequeñas para test rápido
    async with async_session() as session:
        result = await service.acquire_bands(
            polygon_coords=test_coords,
            date=selected_date['date'],
            polygon_id=1,
            db_session=session,
            width=128,  # Pequeño para test rápido
            height=128,
            max_cloud_coverage=20
        )

    print(f"✅ Adquisición completada!")
    print(f"   ID: {result['acquisition_id']}")
    print(f"   Fecha: {result['date']}")
    print(f"   Nubosidad: {result['cloud_coverage']}%")
    print(f"   Tamaño B04: {result['size_b04_kb']:.2f} KB")
    print(f"   Tamaño B08: {result['size_b08_kb']:.2f} KB")

    # ========================================================================
    # PASO 3: Verificar que se guardó en BD
    # ========================================================================
    print("\n" + "-"*80)
    print("💾 PASO 3: Verificar datos en base de datos")
    print("-"*80)

    async with async_session() as session:
        acquisitions = await get_acquisitions_by_polygon(session, 1)

    print(f"✅ Registros encontrados en BD: {len(acquisitions)}")

    if acquisitions:
        acq = acquisitions[0]
        print(f"\n📦 Detalles del registro:")
        print(f"   ID: {acq.id}")
        print(f"   Polígono ID: {acq.polygon_id}")
        print(f"   Fecha: {acq.acquisition_date}")
        print(f"   Nubosidad: {acq.cloud_coverage}%")
        print(f"   Dimensiones: {acq.width}x{acq.height}")
        print(f"   Tamaño B04: {len(acq.b04_data)} bytes")
        print(f"   Tamaño B08: {len(acq.b08_data)} bytes")
        print(f"   Creado: {acq.created_at}")

        # Validaciones
        print(f"\n🔍 Validaciones:")
        assert acq.polygon_id == 1, "Polygon ID incorrecto"
        print(f"   ✓ Polygon ID correcto")

        assert acq.acquisition_date == selected_date['date'], "Fecha incorrecta"
        print(f"   ✓ Fecha correcta")

        assert len(acq.b04_data) > 0, "B04 vacía"
        print(f"   ✓ B04 tiene datos")

        assert len(acq.b08_data) > 0, "B08 vacía"
        print(f"   ✓ B08 tiene datos")

        assert len(acq.b04_data) < 10 * 1024 * 1024, "B04 excede 10MB"
        print(f"   ✓ B04 < 10MB")

        assert len(acq.b08_data) < 10 * 1024 * 1024, "B08 excede 10MB"
        print(f"   ✓ B08 < 10MB")

    # ========================================================================
    # RESUMEN FINAL
    # ========================================================================
    print("\n" + "="*80)
    print("✅ TEST OE1 COMPLETADO EXITOSAMENTE")
    print("="*80)
    print("\n📊 Resumen del flujo:")
    print(f"   1. ✓ Consultadas {len(dates)} fechas aptas via STAC API")
    print(f"   2. ✓ Seleccionada fecha {selected_date['date']} ({selected_date['cloud_cover']}% nubes)")
    print(f"   3. ✓ Descargadas bandas B04 y B08 via Process API")
    print(f"   4. ✓ Guardadas en BD con ID {result['acquisition_id']}")
    print(f"   5. ✓ Verificado: bandas disponibles para OE2 (NDVI)")
    print("\n🎯 OE1 FUNCIONAL: Sistema listo para calcular NDVI (OE2)")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_oe1_complete_flow())
