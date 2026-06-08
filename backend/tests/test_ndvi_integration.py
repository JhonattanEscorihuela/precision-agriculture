"""
OE2 - Tests de integración para endpoints NDVI.
Tests con API real, JWT authentication, y generación de evidencia medible.
"""

import pytest
import numpy as np
import rasterio
import io
import csv
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.polygon import Polygon
from app.models.acquisition import SentinelAcquisition
from app.core.security import create_access_token
from tests.test_ndvi_model_crud import (
    test_db,
    test_user,
    test_polygon,
    generate_synthetic_tiff_band
)


# Coordenadas SRRG Venezuela
PARCELA_211 = [
    [-67.528058, 8.8441233],
    [-67.5153475, 8.8386166],
    [-67.5103962, 8.8478932],
    [-67.522828, 8.8534209],
    [-67.528058, 8.8441233]
]

PARCELA_217 = [
    [-67.538379, 8.8042214],
    [-67.5369724, 8.8130876],
    [-67.5351396, 8.8123084],
    [-67.5337757, 8.8125401],
    [-67.5239405, 8.8082815],
    [-67.5257482, 8.7980897],
    [-67.538379, 8.8042214]
]

PARCELA_85 = [
    [-67.586587, 8.8508969],
    [-67.5991461, 8.8654285],
    [-67.5869706, 8.8659561],
    [-67.5776965, 8.8549892],
    [-67.586587, 8.8508969]
]


@pytest.fixture
async def parcela_211(test_db: AsyncSession, test_user):
    """Crea polígono Parcela 211."""
    polygon = Polygon(
        name="Parcela 211 SRRG",
        coordinates=PARCELA_211,
        user_id=test_user.id,
        area=100.0,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat()
    )
    test_db.add(polygon)
    await test_db.commit()
    await test_db.refresh(polygon)
    return polygon


@pytest.fixture
async def parcela_217(test_db: AsyncSession, test_user):
    """Crea polígono Parcela 217."""
    polygon = Polygon(
        name="Parcela 217 SRRG",
        coordinates=PARCELA_217,
        user_id=test_user.id,
        area=120.0,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat()
    )
    test_db.add(polygon)
    await test_db.commit()
    await test_db.refresh(polygon)
    return polygon


@pytest.fixture
async def parcela_85(test_db: AsyncSession, test_user):
    """Crea polígono Parcela 85."""
    polygon = Polygon(
        name="Parcela 85 SRRG",
        coordinates=PARCELA_85,
        user_id=test_user.id,
        area=90.0,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat()
    )
    test_db.add(polygon)
    await test_db.commit()
    await test_db.refresh(polygon)
    return polygon


@pytest.fixture
async def acquisition_211(test_db: AsyncSession, parcela_211):
    """Crea adquisición sintética para Parcela 211."""
    acquisition = SentinelAcquisition(
        polygon_id=parcela_211.id,
        acquisition_date="2025-03-15",
        cloud_coverage=12.5,
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


@pytest.fixture
async def acquisition_217(test_db: AsyncSession, parcela_217):
    """Crea adquisición sintética para Parcela 217."""
    acquisition = SentinelAcquisition(
        polygon_id=parcela_217.id,
        acquisition_date="2024-08-21",
        cloud_coverage=9.5,
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


@pytest.fixture
async def acquisition_85(test_db: AsyncSession, parcela_85):
    """Crea adquisición sintética para Parcela 85."""
    acquisition = SentinelAcquisition(
        polygon_id=parcela_85.id,
        acquisition_date="2026-02-12",
        cloud_coverage=0.4,
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


@pytest.fixture
def auth_headers(test_user):
    """Genera headers con JWT token."""
    token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}


# ==================== TESTS DE ENDPOINTS ====================

@pytest.mark.asyncio
async def test_calculate_ndvi_endpoint(
    test_db: AsyncSession,
    test_user,
    acquisition_211,
    auth_headers
):
    """Test: POST /api/ndvi/calculate calcula NDVI correctamente."""
    from main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/ndvi/calculate",
            json={"acquisition_id": acquisition_211.id},
            headers=auth_headers
        )

    assert response.status_code == 200
    data = response.json()

    # Verificar estructura de respuesta
    assert "ndvi_id" in data
    assert "acquisition_id" in data
    assert "polygon_id" in data
    assert "calculation_date" in data
    assert "stats" in data

    # Verificar estadísticos
    stats = data["stats"]
    assert -1 <= stats["ndvi_mean"] <= 1
    assert -1 <= stats["ndvi_min"] <= 1
    assert -1 <= stats["ndvi_max"] <= 1
    assert stats["ndvi_std"] >= 0


@pytest.mark.asyncio
async def test_calculate_ndvi_idempotent(
    test_db: AsyncSession,
    test_user,
    acquisition_211,
    auth_headers
):
    """Test: Calcular NDVI dos veces retorna el mismo resultado (idempotente)."""
    from main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Primera llamada
        response1 = await client.post(
            "/api/ndvi/calculate",
            json={"acquisition_id": acquisition_211.id},
            headers=auth_headers
        )

        # Segunda llamada (debe retornar el mismo NDVI)
        response2 = await client.post(
            "/api/ndvi/calculate",
            json={"acquisition_id": acquisition_211.id},
            headers=auth_headers
        )

    assert response1.status_code == 200
    assert response2.status_code == 200

    data1 = response1.json()
    data2 = response2.json()

    # Mismo ndvi_id (no recalculó)
    assert data1["ndvi_id"] == data2["ndvi_id"]
    assert data1["stats"]["ndvi_mean"] == data2["stats"]["ndvi_mean"]


@pytest.mark.asyncio
async def test_get_ndvi_stats_endpoint(
    test_db: AsyncSession,
    test_user,
    acquisition_211,
    auth_headers
):
    """Test: GET /api/ndvi/{acquisition_id} retorna estadísticos."""
    from main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Primero calcular NDVI
        await client.post(
            "/api/ndvi/calculate",
            json={"acquisition_id": acquisition_211.id},
            headers=auth_headers
        )

        # Luego obtener estadísticos
        response = await client.get(
            f"/api/ndvi/{acquisition_211.id}",
            headers=auth_headers
        )

    assert response.status_code == 200
    data = response.json()

    assert data["acquisition_id"] == acquisition_211.id
    assert "ndvi_mean" in data
    assert "calculation_date" in data


@pytest.mark.asyncio
async def test_get_ndvi_by_polygon_endpoint(
    test_db: AsyncSession,
    test_user,
    parcela_211,
    acquisition_211,
    auth_headers
):
    """Test: GET /api/ndvi/polygon/{polygon_id} lista NDVIs del polígono."""
    from main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Calcular NDVI
        await client.post(
            "/api/ndvi/calculate",
            json={"acquisition_id": acquisition_211.id},
            headers=auth_headers
        )

        # Listar NDVIs del polígono
        response = await client.get(
            f"/api/ndvi/polygon/{parcela_211.id}",
            headers=auth_headers
        )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["polygon_id"] == parcela_211.id


@pytest.mark.asyncio
async def test_download_ndvi_tiff_endpoint(
    test_db: AsyncSession,
    test_user,
    acquisition_211,
    auth_headers
):
    """Test: GET /api/ndvi/{acquisition_id}/tiff descarga TIFF válido."""
    from main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Calcular NDVI
        await client.post(
            "/api/ndvi/calculate",
            json={"acquisition_id": acquisition_211.id},
            headers=auth_headers
        )

        # Descargar TIFF
        response = await client.get(
            f"/api/ndvi/{acquisition_211.id}/tiff",
            headers=auth_headers
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    assert "attachment" in response.headers["content-disposition"]

    # Verificar que es un TIFF válido
    tiff_bytes = response.content
    assert len(tiff_bytes) > 0

    with rasterio.open(io.BytesIO(tiff_bytes)) as src:
        assert src.count == 1  # 1 banda
        assert src.dtypes[0] == "float32"
        ndvi_data = src.read(1)
        assert ndvi_data.min() >= -1
        assert ndvi_data.max() <= 1


@pytest.mark.asyncio
async def test_ndvi_without_auth_fails(test_db: AsyncSession, acquisition_211):
    """Test: Endpoints NDVI requieren autenticación JWT."""
    from main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/ndvi/calculate",
            json={"acquisition_id": acquisition_211.id}
            # Sin auth_headers
        )

    assert response.status_code == 401  # Unauthorized


@pytest.mark.asyncio
async def test_ndvi_ownership_verification(
    test_db: AsyncSession,
    acquisition_211,
    auth_headers
):
    """Test: Usuario no puede calcular NDVI de adquisición de otro usuario."""
    from main import app

    # Crear segundo usuario
    from app.models.user import User
    import bcrypt

    other_user = User(
        email="other@example.com",
        hashed_password=bcrypt.hashpw("test123".encode(), bcrypt.gensalt()).decode(),
        full_name="Other User"
    )
    test_db.add(other_user)
    await test_db.commit()

    # Token del otro usuario
    other_token = create_access_token(data={"sub": other_user.email})
    other_headers = {"Authorization": f"Bearer {other_token}"}

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/ndvi/calculate",
            json={"acquisition_id": acquisition_211.id},
            headers=other_headers
        )

    assert response.status_code == 403  # Forbidden


# ==================== EVIDENCIA MEDIBLE OE2 ====================

@pytest.mark.asyncio
async def test_generate_oe2_evidence_table(
    test_db: AsyncSession,
    test_user,
    parcela_211,
    parcela_217,
    parcela_85,
    acquisition_211,
    acquisition_217,
    acquisition_85,
    auth_headers
):
    """
    Test de evidencia OE2: Genera tabla CSV con NDVI de las 3 parcelas SRRG.

    Output: tasks/tabla_evidencia_oe2.csv
    """
    from main import app

    results = []

    # Calcular NDVI para cada parcela
    async with AsyncClient(app=app, base_url="http://test") as client:
        for parcela, acquisition in [
            (parcela_211, acquisition_211),
            (parcela_217, acquisition_217),
            (parcela_85, acquisition_85)
        ]:
            response = await client.post(
                "/api/ndvi/calculate",
                json={"acquisition_id": acquisition.id},
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            results.append({
                "parcela_id": parcela.id,
                "parcela_nombre": parcela.name,
                "fecha_adquisicion": acquisition.acquisition_date,
                "cloud_coverage": acquisition.cloud_coverage,
                "ndvi_mean": round(data["stats"]["ndvi_mean"], 4),
                "ndvi_min": round(data["stats"]["ndvi_min"], 4),
                "ndvi_max": round(data["stats"]["ndvi_max"], 4),
                "ndvi_std": round(data["stats"]["ndvi_std"], 4),
                "width": data["stats"]["width"],
                "height": data["stats"]["height"]
            })

    # Generar CSV
    output_path = "../tasks/tabla_evidencia_oe2.csv"

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            "parcela_id", "parcela_nombre", "fecha_adquisicion", "cloud_coverage",
            "ndvi_mean", "ndvi_min", "ndvi_max", "ndvi_std", "width", "height"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for result in results:
            writer.writerow(result)

    print(f"\n✅ Evidencia OE2 generada: {output_path}")
    print("\nResultados:")
    for result in results:
        print(f"  {result['parcela_nombre']}: NDVI mean={result['ndvi_mean']}, "
              f"min={result['ndvi_min']}, max={result['ndvi_max']}, std={result['ndvi_std']}")

    # Verificar que se generó el archivo
    import os
    assert os.path.exists(output_path)

    # Verificar que tiene los 3 registros
    assert len(results) == 3

    # Verificar rangos válidos
    for result in results:
        assert -1 <= result["ndvi_mean"] <= 1
        assert -1 <= result["ndvi_min"] <= 1
        assert -1 <= result["ndvi_max"] <= 1
        assert result["ndvi_std"] >= 0
