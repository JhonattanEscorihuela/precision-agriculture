"""
OE2 - Tests unitarios para modelo NDVIResult y CRUD.
Tests sin dependencias externas, usando fixtures sintéticos.
"""

import pytest
import numpy as np
import rasterio
import io
import bcrypt
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.models.user import User
from app.models.polygon import Polygon
from app.models.acquisition import SentinelAcquisition
from app.models.analysis import NDVIResult
from app.crud import ndvi as crud_ndvi


# Coordenadas SRRG Venezuela (Parcela 211)
PARCELA_211 = [
    [-67.528058, 8.8441233],
    [-67.5153475, 8.8386166],
    [-67.5103962, 8.8478932],
    [-67.522828, 8.8534209],
    [-67.528058, 8.8441233]
]


@pytest.fixture(scope="function")
async def test_db():
    """
    Base de datos SQLite en memoria para tests unitarios.
    Se crea y destruye en cada test.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def test_user(test_db: AsyncSession):
    """Crea usuario de prueba en BD."""
    user = User(
        email="test@example.com",
        hashed_password=bcrypt.hashpw("test123".encode(), bcrypt.gensalt()).decode(),
        full_name="Test User"
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def test_polygon(test_db: AsyncSession, test_user):
    """Crea polígono de prueba asociado al usuario."""
    polygon = Polygon(
        name="Test Parcela 211",
        coordinates=PARCELA_211,
        user_id=test_user.id
    )
    test_db.add(polygon)
    await test_db.commit()
    await test_db.refresh(polygon)
    return polygon


def generate_synthetic_tiff_band(width: int = 100, height: int = 100, band_type: str = "B04") -> bytes:
    """
    Genera una banda sintética en formato TIFF.

    Args:
        width: Ancho en píxeles
        height: Alto en píxeles
        band_type: "B04" (red) o "B08" (NIR)

    Returns:
        bytes: TIFF con valores realistas para la banda
    """
    if band_type == "B04":
        # Reflectancia roja: 500-2000 (valores L2A típicos)
        band_data = np.random.randint(500, 2000, (height, width), dtype=np.uint16)
    else:  # B08
        # Reflectancia NIR: 1000-4000 (valores L2A típicos)
        band_data = np.random.randint(1000, 4000, (height, width), dtype=np.uint16)

    buf = io.BytesIO()
    with rasterio.open(
        buf, 'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=band_data.dtype,
        crs='EPSG:4326',
        transform=rasterio.transform.from_bounds(
            -67.6, 8.7, -67.5, 8.9, width, height
        ),
        nodata=0  # Sentinel-2 L2A usa 0 como nodata
    ) as dst:
        dst.write(band_data, 1)

    return buf.getvalue()


@pytest.fixture
async def synthetic_acquisition(test_db: AsyncSession, test_polygon):
    """
    Crea adquisición con bandas sintéticas para tests unitarios.

    Genera B04 y B08 con valores realistas y los persiste en BD.
    """
    acquisition = SentinelAcquisition(
        polygon_id=test_polygon.id,
        acquisition_date="2025-03-15",
        cloud_coverage=15.0,
        b04_data=generate_synthetic_tiff_band(100, 100, "B04"),
        b08_data=generate_synthetic_tiff_band(100, 100, "B08"),
        width=100,
        height=100,
        created_at=datetime.utcnow().isoformat()
    )
    test_db.add(acquisition)
    await test_db.commit()
    await test_db.refresh(acquisition)
    return acquisition


def generate_synthetic_ndvi_tiff(width: int = 100, height: int = 100) -> bytes:
    """
    Genera un raster NDVI sintético en formato TIFF float32.

    Returns:
        bytes: TIFF con valores NDVI en rango [-1, 1]
    """
    # Generar NDVI realista: mayoría en [0.2, 0.8] (vegetación sana)
    ndvi_data = np.random.uniform(0.2, 0.8, (height, width)).astype(np.float32)

    # Agregar algunas áreas sin vegetación (valores bajos)
    ndvi_data[0:10, 0:10] = np.random.uniform(-0.1, 0.1, (10, 10))

    buf = io.BytesIO()
    with rasterio.open(
        buf, 'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=rasterio.float32,
        crs='EPSG:4326',
        transform=rasterio.transform.from_bounds(
            -67.6, 8.7, -67.5, 8.9, width, height
        ),
        compress='lzw'
    ) as dst:
        dst.write(ndvi_data, 1)

    return buf.getvalue()


# ==================== TESTS DEL MODELO ====================

@pytest.mark.asyncio
async def test_ndvi_model_creation(test_db: AsyncSession, synthetic_acquisition):
    """Test: Crear un registro NDVIResult en BD."""
    ndvi_tiff = generate_synthetic_ndvi_tiff()

    ndvi_result = NDVIResult(
        acquisition_id=synthetic_acquisition.id,
        polygon_id=synthetic_acquisition.polygon_id,
        ndvi_tiff=ndvi_tiff,
        ndvi_mean=0.6523,
        ndvi_min=-0.1234,
        ndvi_max=0.8765,
        ndvi_std=0.1432,
        width=100,
        height=100,
        calculation_date=datetime.utcnow(),
        created_at=datetime.utcnow()
    )

    test_db.add(ndvi_result)
    await test_db.commit()
    await test_db.refresh(ndvi_result)

    # Verificar
    assert ndvi_result.id is not None
    assert ndvi_result.acquisition_id == synthetic_acquisition.id
    assert ndvi_result.ndvi_mean == 0.6523
    assert len(ndvi_result.ndvi_tiff) > 0


@pytest.mark.asyncio
async def test_ndvi_unique_constraint(test_db: AsyncSession, synthetic_acquisition):
    """Test: UNIQUE constraint en acquisition_id (solo 1 NDVI por adquisición)."""
    ndvi_tiff = generate_synthetic_ndvi_tiff()

    # Crear primer NDVI
    ndvi_1 = NDVIResult(
        acquisition_id=synthetic_acquisition.id,
        polygon_id=synthetic_acquisition.polygon_id,
        ndvi_tiff=ndvi_tiff,
        ndvi_mean=0.65,
        ndvi_min=-0.1,
        ndvi_max=0.9,
        ndvi_std=0.14,
        width=100,
        height=100
    )
    test_db.add(ndvi_1)
    await test_db.commit()

    # Intentar crear segundo NDVI con mismo acquisition_id
    ndvi_2 = NDVIResult(
        acquisition_id=synthetic_acquisition.id,  # mismo acquisition_id
        polygon_id=synthetic_acquisition.polygon_id,
        ndvi_tiff=ndvi_tiff,
        ndvi_mean=0.70,
        ndvi_min=-0.05,
        ndvi_max=0.95,
        ndvi_std=0.12,
        width=100,
        height=100
    )
    test_db.add(ndvi_2)

    # Debe fallar por UNIQUE constraint
    with pytest.raises(Exception):  # IntegrityError
        await test_db.commit()


# ==================== TESTS DEL CRUD ====================

@pytest.mark.asyncio
async def test_save_ndvi_result(test_db: AsyncSession, synthetic_acquisition):
    """Test: Guardar resultado NDVI via CRUD."""
    ndvi_tiff = generate_synthetic_ndvi_tiff()
    stats = {
        "ndvi_mean": 0.6523,
        "ndvi_min": -0.1234,
        "ndvi_max": 0.8765,
        "ndvi_std": 0.1432
    }

    ndvi_result = await crud_ndvi.save_ndvi_result(
        db=test_db,
        acquisition_id=synthetic_acquisition.id,
        polygon_id=synthetic_acquisition.polygon_id,
        ndvi_tiff=ndvi_tiff,
        stats=stats,
        width=100,
        height=100
    )

    # Verificar
    assert ndvi_result.id is not None
    assert ndvi_result.ndvi_mean == 0.6523
    assert ndvi_result.ndvi_min == -0.1234
    assert ndvi_result.ndvi_max == 0.8765
    assert ndvi_result.ndvi_std == 0.1432


@pytest.mark.asyncio
async def test_get_ndvi_by_acquisition(test_db: AsyncSession, synthetic_acquisition):
    """Test: Obtener NDVI por acquisition_id."""
    # Crear NDVI
    ndvi_tiff = generate_synthetic_ndvi_tiff()
    stats = {"ndvi_mean": 0.65, "ndvi_min": -0.1, "ndvi_max": 0.9, "ndvi_std": 0.14}

    await crud_ndvi.save_ndvi_result(
        db=test_db,
        acquisition_id=synthetic_acquisition.id,
        polygon_id=synthetic_acquisition.polygon_id,
        ndvi_tiff=ndvi_tiff,
        stats=stats,
        width=100,
        height=100
    )

    # Obtener NDVI
    ndvi_result = await crud_ndvi.get_ndvi_by_acquisition(
        db=test_db,
        acquisition_id=synthetic_acquisition.id
    )

    # Verificar
    assert ndvi_result is not None
    assert ndvi_result.acquisition_id == synthetic_acquisition.id
    assert ndvi_result.ndvi_mean == 0.65


@pytest.mark.asyncio
async def test_get_ndvi_by_acquisition_not_found(test_db: AsyncSession):
    """Test: Obtener NDVI inexistente retorna None."""
    ndvi_result = await crud_ndvi.get_ndvi_by_acquisition(
        db=test_db,
        acquisition_id=9999  # no existe
    )

    assert ndvi_result is None


@pytest.mark.asyncio
async def test_get_ndvi_by_polygon(test_db: AsyncSession, test_polygon, synthetic_acquisition):
    """Test: Listar NDVI por polygon_id."""
    # Crear 2 NDVIs para el mismo polígono
    ndvi_tiff = generate_synthetic_ndvi_tiff()

    await crud_ndvi.save_ndvi_result(
        db=test_db,
        acquisition_id=synthetic_acquisition.id,
        polygon_id=test_polygon.id,
        ndvi_tiff=ndvi_tiff,
        stats={"ndvi_mean": 0.65, "ndvi_min": -0.1, "ndvi_max": 0.9, "ndvi_std": 0.14},
        width=100,
        height=100
    )

    # Listar NDVIs
    ndvi_list = await crud_ndvi.get_ndvi_by_polygon(
        db=test_db,
        polygon_id=test_polygon.id,
        limit=10
    )

    # Verificar
    assert len(ndvi_list) == 1
    assert ndvi_list[0].polygon_id == test_polygon.id


@pytest.mark.asyncio
async def test_delete_ndvi_result(test_db: AsyncSession, synthetic_acquisition):
    """Test: Eliminar resultado NDVI."""
    # Crear NDVI
    ndvi_tiff = generate_synthetic_ndvi_tiff()
    stats = {"ndvi_mean": 0.65, "ndvi_min": -0.1, "ndvi_max": 0.9, "ndvi_std": 0.14}

    ndvi_result = await crud_ndvi.save_ndvi_result(
        db=test_db,
        acquisition_id=synthetic_acquisition.id,
        polygon_id=synthetic_acquisition.polygon_id,
        ndvi_tiff=ndvi_tiff,
        stats=stats,
        width=100,
        height=100
    )

    # Eliminar
    deleted = await crud_ndvi.delete_ndvi_result(
        db=test_db,
        ndvi_id=ndvi_result.id
    )

    assert deleted is True

    # Verificar que ya no existe
    ndvi_check = await crud_ndvi.get_ndvi_by_id(
        db=test_db,
        ndvi_id=ndvi_result.id
    )

    assert ndvi_check is None


@pytest.mark.asyncio
async def test_cascade_delete_polygon(test_db: AsyncSession, test_user, test_polygon, synthetic_acquisition):
    """Test: Cascade delete - eliminar polígono elimina NDVIs asociados."""
    # Crear NDVI
    ndvi_tiff = generate_synthetic_ndvi_tiff()
    stats = {"ndvi_mean": 0.65, "ndvi_min": -0.1, "ndvi_max": 0.9, "ndvi_std": 0.14}

    ndvi_result = await crud_ndvi.save_ndvi_result(
        db=test_db,
        acquisition_id=synthetic_acquisition.id,
        polygon_id=test_polygon.id,
        ndvi_tiff=ndvi_tiff,
        stats=stats,
        width=100,
        height=100
    )

    # Eliminar polígono (debe eliminar NDVI por CASCADE)
    await test_db.delete(test_polygon)
    await test_db.commit()

    # Verificar que NDVI ya no existe
    ndvi_check = await crud_ndvi.get_ndvi_by_id(
        db=test_db,
        ndvi_id=ndvi_result.id
    )

    assert ndvi_check is None
