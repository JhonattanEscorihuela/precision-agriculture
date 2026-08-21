"""
OE4 - Tests de integración completos para análisis de textura mediante filtrado convolucional.

Cubre:
1. Cálculo de 3 descriptores (edges, homogeneity, contrast)
2. Idempotencia (segunda llamada reutiliza descriptores)
3. Puerta de calidad (rechaza acquisition con quality_status != "suitable")
4. Requisito máscara SCL (rechaza NDVI sin cloud_mask_applied)
5. Ownership (rechaza usuario sin acceso)
6. Overlay/cache (primera llamada no cacheada, segunda sí)
"""

import pytest
import numpy as np
import rasterio
import io
import bcrypt
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.polygon import Polygon
from app.models.acquisition import SentinelAcquisition
from app.models.analysis import NDVIResult, TextureOverlayCache
from app.models.segmentation import SegmentationResult
from app.models.texture import TextureDescriptor  # Importar para crear tablas
from app.core.security import create_access_token
from app.database import get_session
from tests.test_ndvi_model_crud import (
    test_db,
    test_user,
    test_polygon,
    generate_synthetic_tiff_band,
    generate_synthetic_scl_tiff,
    PARCELA_211,
)


@pytest.fixture(autouse=True)
def override_application_database(test_db: AsyncSession):
    """Aísla las rutas FastAPI en la misma SQLite en memoria del test."""
    from main import app

    async def override_get_session():
        yield test_db

    app.dependency_overrides[get_session] = override_get_session
    yield
    app.dependency_overrides.pop(get_session, None)


def generate_synthetic_ndvi_tiff(width: int = 100, height: int = 100) -> bytes:
    """
    Genera un TIFF NDVI sintético para testing con valores realistas.

    Args:
        width: Ancho en píxeles
        height: Alto en píxeles

    Returns:
        bytes: TIFF con valores NDVI en rango [-1, 1]
    """
    # Crear array con valores NDVI realistas para arroz
    # 70% del área cultivada (NDVI > 0.3)
    # 30% del área no cultivada (NDVI < 0.3)
    ndvi_data = np.zeros((height, width), dtype=np.float32)

    # Zona cultivada (centro): NDVI alto (0.5-0.7)
    ndvi_data[20:80, 20:80] = np.random.uniform(0.5, 0.7, (60, 60))

    # Zona con variabilidad (bordes): NDVI medio (0.3-0.5)
    ndvi_data[10:20, 10:90] = np.random.uniform(0.3, 0.5, (10, 80))
    ndvi_data[80:90, 10:90] = np.random.uniform(0.3, 0.5, (10, 80))
    ndvi_data[20:80, 10:20] = np.random.uniform(0.3, 0.5, (60, 10))
    ndvi_data[20:80, 80:90] = np.random.uniform(0.3, 0.5, (60, 10))

    # Zona no cultivada (esquinas): NDVI bajo (0.0-0.2)
    ndvi_data[:10, :] = np.random.uniform(0.0, 0.2, (10, width))
    ndvi_data[90:, :] = np.random.uniform(0.0, 0.2, (10, width))
    ndvi_data[:, :10] = np.random.uniform(0.0, 0.2, (height, 10))
    ndvi_data[:, 90:] = np.random.uniform(0.0, 0.2, (height, 10))

    buf = io.BytesIO()
    with rasterio.open(
        buf, 'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=np.float32,
        crs='EPSG:4326',
        transform=rasterio.transform.from_bounds(
            -67.6, 8.7, -67.5, 8.9, width, height
        ),
        nodata=np.nan
    ) as dst:
        dst.write(ndvi_data, 1)

    return buf.getvalue()


@pytest.fixture
async def test_acquisition_suitable(test_db: AsyncSession, test_polygon):
    """Crea adquisición con quality_status='suitable' y SCL aplicado."""
    acquisition = SentinelAcquisition(
        polygon_id=test_polygon.id,
        acquisition_date=datetime(2025, 3, 15).isoformat(),
        cloud_coverage=5.0,
        width=100,
        height=100,
        b04_data=generate_synthetic_tiff_band(100, 100, band_type="B04"),
        b08_data=generate_synthetic_tiff_band(100, 100, band_type="B08"),
        scl_data=generate_synthetic_scl_tiff(100, 100),
        quality_status="suitable",  # ✅ Calidad apta
        created_at=datetime.utcnow().isoformat(),
    )
    test_db.add(acquisition)
    await test_db.commit()
    await test_db.refresh(acquisition)
    return acquisition


@pytest.fixture
async def test_acquisition_unsuitable(test_db: AsyncSession, test_polygon):
    """Crea adquisición con quality_status='unsuitable' (alta nubosidad)."""
    acquisition = SentinelAcquisition(
        polygon_id=test_polygon.id,
        acquisition_date=datetime(2025, 4, 20).isoformat(),
        cloud_coverage=45.0,
        width=100,
        height=100,
        b04_data=generate_synthetic_tiff_band(100, 100, band_type="B04"),
        b08_data=generate_synthetic_tiff_band(100, 100, band_type="B08"),
        scl_data=generate_synthetic_scl_tiff(100, 100),
        quality_status="unsuitable",  # ❌ Calidad no apta
        created_at=datetime.utcnow().isoformat(),
    )
    test_db.add(acquisition)
    await test_db.commit()
    await test_db.refresh(acquisition)
    return acquisition


@pytest.fixture
async def test_ndvi_with_scl(test_db: AsyncSession, test_acquisition_suitable):
    """Crea NDVI con máscara SCL aplicada."""
    ndvi = NDVIResult(
        acquisition_id=test_acquisition_suitable.id,
        polygon_id=test_acquisition_suitable.polygon_id,
        ndvi_tiff=generate_synthetic_ndvi_tiff(width=100, height=100),
        ndvi_mean=0.55,
        ndvi_std=0.15,
        ndvi_min=-0.1,
        ndvi_max=0.85,
        width=100,
        height=100,
        cloud_mask_applied=True,  # ✅ SCL aplicado
        calculation_date=datetime.utcnow(),
        created_at=datetime.utcnow().isoformat(),
    )
    test_db.add(ndvi)
    await test_db.commit()
    await test_db.refresh(ndvi)
    return ndvi


@pytest.fixture
async def test_ndvi_without_scl(test_db: AsyncSession, test_acquisition_suitable):
    """Crea NDVI SIN máscara SCL aplicada (legacy)."""
    # Necesitamos crear una nueva adquisición porque acquisition_id es UNIQUE en ndvi_results
    acquisition = SentinelAcquisition(
        polygon_id=test_acquisition_suitable.polygon_id,
        acquisition_date=datetime(2025, 3, 20).isoformat(),  # Fecha diferente
        cloud_coverage=5.0,
        width=100,
        height=100,
        b04_data=generate_synthetic_tiff_band(100, 100, band_type="B04"),
        b08_data=generate_synthetic_tiff_band(100, 100, band_type="B08"),
        scl_data=generate_synthetic_scl_tiff(100, 100),
        quality_status="suitable",
        created_at=datetime.utcnow().isoformat(),
    )
    test_db.add(acquisition)
    await test_db.commit()
    await test_db.refresh(acquisition)

    ndvi = NDVIResult(
        acquisition_id=acquisition.id,
        polygon_id=acquisition.polygon_id,
        ndvi_tiff=generate_synthetic_ndvi_tiff(width=100, height=100),
        ndvi_mean=0.52,
        ndvi_std=0.18,
        ndvi_min=-0.05,
        ndvi_max=0.80,
        width=100,
        height=100,
        cloud_mask_applied=False,  # ❌ SCL NO aplicado
        calculation_date=datetime.utcnow(),
        created_at=datetime.utcnow().isoformat(),
    )
    test_db.add(ndvi)
    await test_db.commit()
    await test_db.refresh(ndvi)
    return ndvi


@pytest.fixture
async def test_ndvi_unsuitable_quality(test_db: AsyncSession, test_acquisition_unsuitable):
    """Crea NDVI asociado a adquisición con calidad no apta."""
    ndvi = NDVIResult(
        acquisition_id=test_acquisition_unsuitable.id,
        polygon_id=test_acquisition_unsuitable.polygon_id,
        ndvi_tiff=generate_synthetic_ndvi_tiff(width=100, height=100),
        ndvi_mean=0.45,
        ndvi_std=0.20,
        ndvi_min=-0.1,
        ndvi_max=0.75,
        width=100,
        height=100,
        cloud_mask_applied=True,
        calculation_date=datetime.utcnow(),
        created_at=datetime.utcnow().isoformat(),
    )
    test_db.add(ndvi)
    await test_db.commit()
    await test_db.refresh(ndvi)
    return ndvi


@pytest.fixture
async def test_segmentation(test_db: AsyncSession, test_ndvi_with_scl):
    """Crea segmentación sobre NDVI válido."""
    segmentation = SegmentationResult(
        ndvi_result_id=test_ndvi_with_scl.id,
        polygon_id=test_ndvi_with_scl.polygon_id,
        threshold_used=0.3,
        total_pixels=10000,
        cultivated_pixels=7000,
        cultivated_percentage=70.0,
        calculation_date=datetime.utcnow(),
        created_at=datetime.utcnow().isoformat(),
    )
    test_db.add(segmentation)
    await test_db.commit()
    await test_db.refresh(segmentation)
    return segmentation


@pytest.fixture
async def test_segmentation_unsuitable(test_db: AsyncSession, test_ndvi_unsuitable_quality):
    """Crea segmentación sobre NDVI con calidad no apta."""
    segmentation = SegmentationResult(
        ndvi_result_id=test_ndvi_unsuitable_quality.id,
        polygon_id=test_ndvi_unsuitable_quality.polygon_id,
        threshold_used=0.3,
        total_pixels=10000,
        cultivated_pixels=6000,
        cultivated_percentage=60.0,
        calculation_date=datetime.utcnow(),
        created_at=datetime.utcnow().isoformat(),
    )
    test_db.add(segmentation)
    await test_db.commit()
    await test_db.refresh(segmentation)
    return segmentation


@pytest.fixture
async def test_segmentation_no_scl(test_db: AsyncSession, test_ndvi_without_scl):
    """Crea segmentación sobre NDVI sin SCL."""
    segmentation = SegmentationResult(
        ndvi_result_id=test_ndvi_without_scl.id,
        polygon_id=test_ndvi_without_scl.polygon_id,
        threshold_used=0.3,
        total_pixels=10000,
        cultivated_pixels=6500,
        cultivated_percentage=65.0,
        calculation_date=datetime.utcnow(),
        created_at=datetime.utcnow().isoformat(),
    )
    test_db.add(segmentation)
    await test_db.commit()
    await test_db.refresh(segmentation)
    return segmentation


@pytest.fixture
async def other_user(test_db: AsyncSession):
    """Crea segundo usuario para tests de ownership."""
    user = User(
        email="other@example.com",
        hashed_password=bcrypt.hashpw("other123".encode(), bcrypt.gensalt()).decode(),
        full_name="Other User",
        created_at=datetime.utcnow().isoformat(),
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_calculate_texture_descriptors_success(
    test_user,
    test_segmentation,
):
    """
    Test 1: Cálculo exitoso de 3 descriptores de textura.

    Verifica:
    - Retorna lista de 3 descriptors (edges, homogeneity, contrast)
    - Cada descriptor tiene campos requeridos
    - Valores están en rangos razonables
    """
    from main import app

    token = create_access_token(data={"sub": test_user.email})

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/texture/analyze",
            json={"segmentation_result_id": test_segmentation.id},
            headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 200, f"Error: {response.text}"

    descriptors = response.json()
    assert len(descriptors) == 3, "Debe retornar 3 descriptores"

    # Verificar que los 3 kernels están presentes
    kernel_types = {d["kernel_type"] for d in descriptors}
    assert kernel_types == {"edges", "homogeneity", "contrast"}, \
        f"Kernels esperados: edges, homogeneity, contrast. Obtenidos: {kernel_types}"

    # Verificar campos de cada descriptor
    for desc in descriptors:
        assert "id" in desc
        assert "segmentation_result_id" in desc
        assert desc["segmentation_result_id"] == test_segmentation.id
        assert "polygon_id" in desc
        assert "kernel_type" in desc
        assert "mean" in desc
        assert "std" in desc
        assert "min_val" in desc
        assert "max_val" in desc
        assert "std_normalized" in desc
        assert "discriminative" in desc
        assert "calculation_date" in desc

        # Verificar rangos razonables
        assert desc["std_normalized"] >= 0.0, "std_normalized debe ser >= 0"
        assert desc["std_normalized"] <= 1.0, "std_normalized debe ser <= 1"
        assert isinstance(desc["discriminative"], bool), "discriminative debe ser boolean"


@pytest.mark.asyncio
async def test_texture_idempotence(
    test_user,
    test_segmentation,
):
    """
    Test 2: Idempotencia del cálculo de textura.

    Verifica:
    - Primera llamada calcula y guarda descriptores
    - Segunda llamada retorna mismos descriptores sin recalcular
    - IDs de descriptores son idénticos entre llamadas
    """
    from main import app

    token = create_access_token(data={"sub": test_user.email})

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Primera llamada
        response1 = await client.post(
            "/api/texture/analyze",
            json={"segmentation_result_id": test_segmentation.id},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response1.status_code == 200
        descriptors1 = response1.json()
        ids1 = {d["id"] for d in descriptors1}

        # Segunda llamada (debe retornar mismos descriptores)
        response2 = await client.post(
            "/api/texture/analyze",
            json={"segmentation_result_id": test_segmentation.id},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response2.status_code == 200
        descriptors2 = response2.json()
        ids2 = {d["id"] for d in descriptors2}

        # Verificar que son los mismos IDs (no se recalcularon)
        assert ids1 == ids2, "Segunda llamada debe retornar mismos descriptores (idempotencia)"


@pytest.mark.asyncio
async def test_texture_rejects_unsuitable_quality(
    test_user,
    test_segmentation_unsuitable,
):
    """
    Test 3: Puerta de calidad - rechaza adquisiciones no aptas.

    Verifica:
    - Rechaza análisis de textura si acquisition.quality_status != "suitable"
    - Retorna 409 Conflict con mensaje descriptivo
    """
    from main import app

    token = create_access_token(data={"sub": test_user.email})

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/texture/analyze",
            json={"segmentation_result_id": test_segmentation_unsuitable.id},
            headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 409, \
        "Debe rechazar segmentación asociada a adquisición no apta"

    error_detail = response.json()["detail"]
    assert "quality" in error_detail.lower(), \
        f"Error debe mencionar 'quality'. Mensaje: {error_detail}"


@pytest.mark.asyncio
async def test_texture_rejects_ndvi_without_scl(
    test_user,
    test_segmentation_no_scl,
):
    """
    Test 4: Requisito máscara SCL - rechaza NDVI sin cloud_mask_applied.

    Verifica:
    - Rechaza análisis de textura si NDVI no tiene máscara SCL aplicada
    - Retorna 409 Conflict con mensaje descriptivo
    """
    from main import app

    token = create_access_token(data={"sub": test_user.email})

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/texture/analyze",
            json={"segmentation_result_id": test_segmentation_no_scl.id},
            headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 409, \
        "Debe rechazar segmentación asociada a NDVI sin SCL"

    error_detail = response.json()["detail"]
    assert "scl" in error_detail.lower() or "cloud mask" in error_detail.lower(), \
        f"Error debe mencionar 'SCL' o 'cloud mask'. Mensaje: {error_detail}"


@pytest.mark.asyncio
async def test_texture_ownership_protection(
    test_user,
    other_user,
    test_segmentation,
):
    """
    Test 5: Ownership - usuario no puede acceder a textura de parcela ajena.

    Verifica:
    - Rechaza análisis de textura si usuario no es dueño de la parcela
    - Retorna 403 Forbidden
    """
    from main import app

    # Token de otro usuario (no dueño de la parcela)
    other_token = create_access_token(data={"sub": other_user.email})

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/texture/analyze",
            json={"segmentation_result_id": test_segmentation.id},
            headers={"Authorization": f"Bearer {other_token}"}
        )

    assert response.status_code == 403, \
        "Debe rechazar acceso de usuario no autorizado"


@pytest.mark.asyncio
async def test_texture_overlay_cache_behavior(
    test_user,
    test_ndvi_with_scl,
):
    """
    Test 6: Overlay cache - primera llamada genera, segunda usa caché.

    Verifica:
    - Primera llamada: cached=false
    - Segunda llamada: cached=true
    - Imagen base64 tiene contenido
    - Bounds son válidos
    - Interpretación textual existe
    """
    from main import app

    token = create_access_token(data={"sub": test_user.email})

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Primera llamada (genera overlay)
        response1 = await client.get(
            f"/api/texture/overlay/{test_ndvi_with_scl.id}?kernel=contrast",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response1.status_code == 200
        data1 = response1.json()

        assert data1["cached"] == False, "Primera llamada debe generar overlay (no cacheado)"
        assert "image_base64" in data1
        assert data1["image_base64"].startswith("data:image/png;base64,")
        assert len(data1["image_base64"]) > 100, "Imagen debe tener contenido"
        assert "bounds" in data1
        assert len(data1["bounds"]) == 2, "Bounds debe ser [[south, west], [north, east]]"
        assert "kernel" in data1
        assert data1["kernel"] == "contrast"
        assert "interpretation" in data1
        assert len(data1["interpretation"]) > 0, "Interpretación debe tener contenido"

        # Segunda llamada (usa caché)
        response2 = await client.get(
            f"/api/texture/overlay/{test_ndvi_with_scl.id}?kernel=contrast",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response2.status_code == 200
        data2 = response2.json()

        assert data2["cached"] == True, "Segunda llamada debe usar caché"
        assert data2["image_base64"] == data1["image_base64"], \
            "Imagen cacheada debe ser idéntica a la generada"


@pytest.mark.asyncio
async def test_get_descriptors_by_segmentation(
    test_user,
    test_segmentation,
):
    """
    Test 7: GET by-segmentation endpoint.

    Verifica:
    - Calcula descriptores primero
    - Luego puede consultarlos con GET
    - Retorna mismos 3 descriptores
    """
    from main import app

    token = create_access_token(data={"sub": test_user.email})

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Calcular descriptores
        response_post = await client.post(
            "/api/texture/analyze",
            json={"segmentation_result_id": test_segmentation.id},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response_post.status_code == 200
        descriptors_post = response_post.json()

        # Consultar descriptores con GET
        response_get = await client.get(
            f"/api/texture/by-segmentation/{test_segmentation.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response_get.status_code == 200
        descriptors_get = response_get.json()

        # Verificar que son los mismos
        ids_post = {d["id"] for d in descriptors_post}
        ids_get = {d["id"] for d in descriptors_get}
        assert ids_post == ids_get, "GET debe retornar mismos descriptores que POST"


@pytest.mark.asyncio
async def test_get_descriptors_not_calculated_yet(
    test_user,
    test_segmentation,
):
    """
    Test 8: GET by-segmentation antes de calcular retorna 404.

    Verifica:
    - Si no existen descriptores calculados, retorna 404
    """
    from main import app

    token = create_access_token(data={"sub": test_user.email})

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            f"/api/texture/by-segmentation/{test_segmentation.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 404, \
        "GET debe retornar 404 si descriptores no existen todavía"
