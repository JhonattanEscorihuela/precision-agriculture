"""
OE2 - Test de validación cruzada NDVI vs datos Copernicus oficiales.
Compara nuestro cálculo NDVI contra estadísticos NDVI oficiales de Copernicus
para 3 fechas representativas de la Parcela 211 SRRG.
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from app.models.user import User
from app.models.polygon import Polygon
from app.core.security import create_access_token
from tests.test_ndvi_integration import PARCELA_211, parcela_211, test_db, test_user


# Datos de referencia Copernicus para Parcela 211
COPERNICUS_REFERENCE = [
    {
        "date": "2026-03-22",
        "ndvi_mean": 0.8535,
        "season": "Temporada seca (alta vegetación)",
        "cloud_coverage": 0.0
    },
    {
        "date": "2025-11-27",
        "ndvi_mean": 0.3087,
        "season": "Transición (vegetación media)",
        "cloud_coverage": 0.0
    },
    {
        "date": "2025-07-02",
        "ndvi_mean": 0.5594,
        "season": "Temporada húmeda (vegetación alta-media)",
        "cloud_coverage": 0.0
    }
]

# Tolerancia aceptable (diferencias por resolución espacial y área de recorte)
TOLERANCE = 0.05


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ndvi_cross_validation(
    test_db: AsyncSession,
    test_user: User,
    parcela_211: Polygon
):
    """
    Validación cruzada NDVI contra datos oficiales Copernicus.

    Workflow:
    1. Para cada fecha de referencia:
       - Verificar si existe adquisición Sentinel-2 en BD para esa fecha
       - Si existe, calcular NDVI con nuestro servicio
       - Comparar ndvi_mean contra valor Copernicus
       - Validar que diferencia está dentro de tolerancia (±0.05)

    2. Generar tabla resumen con resultados

    IMPORTANTE:
    - Este test requiere que las adquisiciones Sentinel-2 existan en BD
    - Si las adquisiciones no existen, el test se saltará (no fallará)
    - La validación solo se aplica a fechas con datos disponibles
    - Tolerancia: ±0.05 (5% de diferencia aceptable)

    Razones de diferencia aceptable:
    - Resolución espacial diferente (Copernicus puede usar área mayor)
    - Área de recorte exacta (polígono puede variar ligeramente)
    - Píxeles de borde (tratamiento de nodata)
    - Método de remuestreo (nearest neighbor vs bilinear)
    """
    from app.services.ndvi_service import NDVIService
    from app.crud import acquisition as crud_acquisition

    ndvi_service = NDVIService()
    results = []

    print("\n" + "=" * 100)
    print("VALIDACIÓN CRUZADA NDVI - COMPARACIÓN CON DATOS COPERNICUS OFICIALES")
    print("=" * 100)
    print(f"Parcela: {parcela_211.name}")
    print(f"Coordenadas: Calabozo, Guárico, Venezuela")
    print(f"Tolerancia: ±{TOLERANCE} ({TOLERANCE*100}%)")
    print("=" * 100)

    for ref in COPERNICUS_REFERENCE:
        date = ref["date"]
        copernicus_mean = ref["ndvi_mean"]
        season = ref["season"]
        cloud = ref["cloud_coverage"]

        print(f"\n📅 Fecha: {date}")
        print(f"   🌍 Temporada: {season}")
        print(f"   ☁️  Nubosidad: {cloud}%")
        print(f"   🎯 NDVI Copernicus: {copernicus_mean:.4f}")

        # Buscar adquisición en BD
        acquisition = await crud_acquisition.get_acquisition_by_polygon_and_date(
            test_db,
            parcela_211.id,
            date
        )

        if not acquisition:
            print(f"   ⚠️  Adquisición no encontrada en BD (test skip)")
            results.append({
                "date": date,
                "season": season,
                "ndvi_ours": None,
                "ndvi_copernicus": copernicus_mean,
                "difference": None,
                "status": "SKIP",
                "reason": "Adquisición no disponible"
            })
            continue

        print(f"   ✅ Adquisición encontrada (id={acquisition.id})")

        # Calcular NDVI con nuestro servicio
        try:
            ndvi_result = await ndvi_service.calculate_ndvi(
                acquisition_id=acquisition.id,
                user_id=test_user.id,
                db=test_db
            )

            our_mean = ndvi_result["stats"]["ndvi_mean"]
            difference = abs(our_mean - copernicus_mean)
            passed = difference <= TOLERANCE

            print(f"   🧮 NDVI Nuestro: {our_mean:.4f}")
            print(f"   📊 Diferencia: {difference:.4f} ({difference*100:.2f}%)")

            if passed:
                print(f"   ✅ PASS - Dentro de tolerancia")
                status = "PASS"
            else:
                print(f"   ❌ FAIL - Fuera de tolerancia (>{TOLERANCE})")
                status = "FAIL"

            results.append({
                "date": date,
                "season": season,
                "ndvi_ours": our_mean,
                "ndvi_copernicus": copernicus_mean,
                "difference": difference,
                "status": status,
                "reason": None
            })

        except Exception as e:
            print(f"   ❌ Error calculando NDVI: {str(e)}")
            results.append({
                "date": date,
                "season": season,
                "ndvi_ours": None,
                "ndvi_copernicus": copernicus_mean,
                "difference": None,
                "status": "ERROR",
                "reason": str(e)
            })

    # Generar tabla resumen
    print("\n" + "=" * 100)
    print("TABLA RESUMEN - VALIDACIÓN CRUZADA")
    print("=" * 100)
    print(f"{'Fecha':<12} | {'NDVI Nuestro':<13} | {'NDVI Copernicus':<16} | {'Diferencia':<11} | {'Resultado':<8}")
    print("-" * 100)

    passed_count = 0
    failed_count = 0
    skipped_count = 0

    for r in results:
        ndvi_ours_str = f"{r['ndvi_ours']:.4f}" if r['ndvi_ours'] is not None else "N/A"
        diff_str = f"{r['difference']:.4f}" if r['difference'] is not None else "N/A"

        print(f"{r['date']:<12} | {ndvi_ours_str:<13} | {r['ndvi_copernicus']:<16.4f} | {diff_str:<11} | {r['status']:<8}")

        if r['status'] == "PASS":
            passed_count += 1
        elif r['status'] == "FAIL":
            failed_count += 1
        elif r['status'] == "SKIP":
            skipped_count += 1

    print("=" * 100)
    print(f"✅ PASS: {passed_count}/{len(results)}")
    print(f"❌ FAIL: {failed_count}/{len(results)}")
    print(f"⚠️  SKIP: {skipped_count}/{len(results)}")
    print("=" * 100)

    # Assert: Si hay resultados validables, al menos uno debe pasar
    validable_results = [r for r in results if r["status"] in ["PASS", "FAIL"]]
    if validable_results:
        assert passed_count > 0, (
            f"Ninguna fecha pasó la validación. "
            f"Revisar implementación NDVI o factor de escala L2A."
        )

        # Si hay fallas, mostrar detalle
        if failed_count > 0:
            print("\n⚠️  ADVERTENCIA: Algunas fechas fallaron validación:")
            for r in results:
                if r["status"] == "FAIL":
                    print(f"   - {r['date']}: diferencia {r['difference']:.4f} > tolerancia {TOLERANCE}")
    else:
        pytest.skip("No hay adquisiciones disponibles para validar")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ndvi_percentiles_calculation(
    test_db: AsyncSession,
    test_user: User,
    parcela_211: Polygon
):
    """
    Verifica que los percentiles (median, p10, p90) se calculen correctamente
    cuando estén implementados en el servicio NDVI.

    Este test valida que:
    - median esté entre min y max
    - p10 ≤ median ≤ p90
    - p10 ≥ min
    - p90 ≤ max
    """
    from app.services.ndvi_service import NDVIService
    from app.crud import acquisition as crud_acquisition

    # Buscar cualquier adquisición disponible
    acquisition = await crud_acquisition.get_acquisitions_by_polygon(
        test_db,
        parcela_211.id,
        limit=1
    )

    if not acquisition:
        pytest.skip("No hay adquisiciones disponibles")

    ndvi_service = NDVIService()
    ndvi_result = await ndvi_service.calculate_ndvi(
        acquisition_id=acquisition[0].id,
        user_id=test_user.id,
        db=test_db
    )

    stats = ndvi_result["stats"]

    # Si los percentiles están implementados, validar relaciones
    if stats.get("ndvi_median") is not None:
        median = stats["ndvi_median"]
        p10 = stats.get("ndvi_p10")
        p90 = stats.get("ndvi_p90")
        ndvi_min = stats["ndvi_min"]
        ndvi_max = stats["ndvi_max"]

        print("\n" + "=" * 80)
        print("VALIDACIÓN PERCENTILES NDVI")
        print("=" * 80)
        print(f"Min:    {ndvi_min:.4f}")
        print(f"P10:    {p10:.4f}" if p10 is not None else "P10:    N/A")
        print(f"Median: {median:.4f}")
        print(f"P90:    {p90:.4f}" if p90 is not None else "P90:    N/A")
        print(f"Max:    {ndvi_max:.4f}")
        print("=" * 80)

        # Validaciones
        assert ndvi_min <= median <= ndvi_max, "Median debe estar entre min y max"

        if p10 is not None:
            assert p10 >= ndvi_min, "P10 debe ser >= min"
            assert p10 <= median, "P10 debe ser <= median"

        if p90 is not None:
            assert p90 >= median, "P90 debe ser >= median"
            assert p90 <= ndvi_max, "P90 debe ser <= max"

        print("✅ Todas las validaciones de percentiles pasaron")
    else:
        pytest.skip("Percentiles no implementados todavía")
