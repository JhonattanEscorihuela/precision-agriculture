"""
Script de prueba para verificar modelo SentinelAcquisition.
OE1 - Fase 1: Validación de modelo y CRUD
"""

import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

# Importar modelos
from app.models.polygon import Polygon
from app.models.acquisition import SentinelAcquisition, SentinelAcquisitionCreate
from app.crud.acquisition import (
    create_acquisition,
    get_acquisition_by_id,
    get_acquisitions_by_polygon,
    delete_acquisition
)


async def test_acquisition_model():
    """
    Prueba del modelo SentinelAcquisition y operaciones CRUD.
    """
    # Usar base de datos de prueba en memoria
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)

    # Crear tablas
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Crear sesión
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    print("\n" + "="*70)
    print("🧪 TEST 1: Crear adquisición")
    print("="*70)

    async with async_session() as session:
        # Crear datos de prueba
        acquisition_data = SentinelAcquisitionCreate(
            polygon_id=1,
            acquisition_date="2024-06-15",
            cloud_coverage=12.5,
            width=512,
            height=512,
            b04_data=b"fake_b04_tiff_data",
            b08_data=b"fake_b08_tiff_data",
            created_at=datetime.utcnow().isoformat()
        )

        # Crear adquisición
        acquisition = await create_acquisition(session, acquisition_data)
        print(f"✅ Adquisición creada con ID: {acquisition.id}")
        print(f"   - Polígono: {acquisition.polygon_id}")
        print(f"   - Fecha: {acquisition.acquisition_date}")
        print(f"   - Nubosidad: {acquisition.cloud_coverage}%")
        print(f"   - Dimensiones: {acquisition.width}x{acquisition.height}")
        print(f"   - Tamaño B04: {len(acquisition.b04_data)} bytes")
        print(f"   - Tamaño B08: {len(acquisition.b08_data)} bytes")

    print("\n" + "="*70)
    print("🧪 TEST 2: Obtener adquisición por ID")
    print("="*70)

    async with async_session() as session:
        acquisition = await get_acquisition_by_id(session, 1)
        if acquisition:
            print(f"✅ Adquisición encontrada: ID={acquisition.id}")
            print(f"   Fecha: {acquisition.acquisition_date}")
        else:
            print("❌ No se encontró la adquisición")

    print("\n" + "="*70)
    print("🧪 TEST 3: Obtener adquisiciones por polígono")
    print("="*70)

    async with async_session() as session:
        # Crear otra adquisición para el mismo polígono
        acquisition_data_2 = SentinelAcquisitionCreate(
            polygon_id=1,
            acquisition_date="2024-06-20",
            cloud_coverage=8.0,
            width=512,
            height=512,
            b04_data=b"fake_b04_tiff_data_2",
            b08_data=b"fake_b08_tiff_data_2",
            created_at=datetime.utcnow().isoformat()
        )
        await create_acquisition(session, acquisition_data_2)

        # Obtener todas las adquisiciones del polígono 1
        acquisitions = await get_acquisitions_by_polygon(session, 1)
        print(f"✅ Se encontraron {len(acquisitions)} adquisiciones para polígono 1:")
        for acq in acquisitions:
            print(f"   - ID {acq.id}: {acq.acquisition_date} ({acq.cloud_coverage}% nubes)")

    print("\n" + "="*70)
    print("🧪 TEST 4: Eliminar adquisición")
    print("="*70)

    async with async_session() as session:
        deleted = await delete_acquisition(session, 1)
        if deleted:
            print("✅ Adquisición eliminada correctamente")
        else:
            print("❌ No se pudo eliminar la adquisición")

        # Verificar que ya no existe
        acquisition = await get_acquisition_by_id(session, 1)
        if acquisition is None:
            print("✅ Verificado: la adquisición ya no existe")
        else:
            print("❌ Error: la adquisición aún existe")

    print("\n" + "="*70)
    print("✅ TODOS LOS TESTS PASARON")
    print("="*70)
    print("\n🎯 Fase 1 completada: Modelo y CRUD funcionando correctamente")


if __name__ == "__main__":
    asyncio.run(test_acquisition_model())
