"""
Validación cruzada NDVI: Comparar nuestro cálculo vs datos oficiales Copernicus.

Para cada fecha que coincida entre STAC y CSV:
1. Descargar B04 y B08
2. Calcular NDVI
3. Comparar ndvi_mean vs CSV Copernicus

Sin guardar en BD - solo validación.
"""

import asyncio
import sys
import io
import numpy as np
import rasterio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.sentinel.sentinel_service import SentinelService
from scripts.copernicus_reference_dates import COPERNICUS_DATES


# Coordenadas Parcela 211 SRRG
PARCELA_211 = [
    [-67.528058, 8.8441233],
    [-67.5153475, 8.8386166],
    [-67.5103962, 8.8478932],
    [-67.522828, 8.8534209],
    [-67.528058, 8.8441233]
]

# Factor de escala L2A
L2A_SCALE_FACTOR = 10000.0

# Datos CSV Copernicus (extraídos manualmente)
COPERNICUS_MEAN = {
    "2025-06-05": 0.5194,
    "2025-06-17": 0.5148,
    "2025-07-02": 0.5594,
    "2025-07-05": 0.5198,
    "2025-08-13": 0.4244,
    "2025-08-23": 0.3467,
    "2025-08-29": 0.3605,
    "2025-09-02": 0.4115,
    "2025-09-10": 0.4406,
    "2025-09-12": 0.3774,
    "2025-09-15": 0.4537,
    "2025-09-22": 0.4675,
    "2025-09-23": 0.4469,
    "2025-10-05": 0.3549,
    "2025-10-22": 0.2934,
    "2025-10-25": 0.2671,
    "2025-10-28": 0.2217,
    "2025-10-30": 0.2428,
    "2025-11-02": 0.2847,
    "2025-11-04": 0.2544,
    "2025-11-09": 0.2519,
    "2025-11-11": 0.2234,
    "2025-11-21": 0.2314,
    "2025-11-22": 0.2195,
    "2025-11-27": 0.3087,
    "2025-12-02": 0.2847,
    "2025-12-04": 0.3099,
    "2025-12-07": 0.2929,
    "2025-12-09": 0.2231,
    "2025-12-12": 0.2554,
    "2025-12-17": 0.2455,
    "2025-12-19": 0.2191,
    "2025-12-22": 0.1853,
    "2025-12-24": 0.1827,
    "2025-12-27": 0.1905,
    "2026-01-01": 0.1801,
    "2026-01-06": 0.1969,
    "2026-01-08": 0.2269,
    "2026-01-16": 0.1926,
    "2026-01-21": 0.2227,
    "2026-01-23": 0.2379,
    "2026-01-28": 0.2925,
    "2026-02-05": 0.4461,
    "2026-02-10": 0.5458,
    "2026-02-12": 0.6189,
    "2026-02-17": 0.6324,
    "2026-02-22": 0.7594,
    "2026-02-25": 0.7685,
    "2026-02-27": 0.7640,
    "2026-03-09": 0.8024,
    "2026-03-21": 0.8270,
    "2026-03-22": 0.8535,
    "2026-03-27": 0.8118,
    "2026-04-01": 0.7330,
    "2026-04-10": 0.7594,
    "2026-04-11": 0.7888,
    "2026-04-13": 0.7990,
    "2026-04-28": 0.7204,
    "2026-05-01": 0.6319,
    "2026-05-06": 0.4875,
    "2026-05-08": 0.4427,
    "2026-05-10": 0.3791,
    "2026-05-11": 0.3652,
    "2026-05-18": 0.3098,
    "2026-05-26": 0.2857,
    "2026-05-28": 0.3248
}


def calculate_ndvi_from_bands(b04_bytes: bytes, b08_bytes: bytes) -> float:
    """
    Calcula NDVI mean a partir de bytes TIFF de B04 y B08.
    Misma lógica que ndvi_service.py pero sin guardar en BD.

    Returns:
        float: ndvi_mean
    """
    # Leer B04 (Red)
    with rasterio.open(io.BytesIO(b04_bytes)) as src:
        b04_array = src.read(1)
        nodata_b04 = src.nodata

    # Leer B08 (NIR)
    with rasterio.open(io.BytesIO(b08_bytes)) as src:
        b08_array = src.read(1)
        nodata_b08 = src.nodata

    # Crear máscara de píxeles nodata
    nodata_mask = np.zeros_like(b04_array, dtype=bool)
    if nodata_b04 is not None:
        nodata_mask |= (b04_array == nodata_b04)
    if nodata_b08 is not None:
        nodata_mask |= (b08_array == nodata_b08)

    # Convertir a float32
    b04 = b04_array.astype(np.float32)
    b08 = b08_array.astype(np.float32)

    # NO aplicar factor de escala: Process API ya retorna reflectancia 0.0-1.0
    # (Si se usara STAC directo con uint16, sí se aplicaría /10000)

    # Calcular NDVI con manejo de división por cero
    denominator = b08 + b04
    ndvi = np.where(
        denominator == 0,
        0.0,
        (b08 - b04) / denominator
    )

    # Aplicar máscara de nodata
    ndvi = np.where(nodata_mask, np.nan, ndvi)

    # Calcular mean como NDVI de reflectancias medias (metodología Copernicus)
    # NO como mean de array NDVI pixel-wise
    b04_mean = b04[~nodata_mask].mean()
    b08_mean = b08[~nodata_mask].mean()
    ndvi_mean = (b08_mean - b04_mean) / (b08_mean + b04_mean)

    return float(ndvi_mean)


async def validate_ndvi_cross_check():
    """Validación cruzada completa NDVI vs Copernicus."""

    sentinel_service = SentinelService()

    print("\n" + "=" * 120)
    print("VALIDACIÓN CRUZADA NDVI - COMPARACIÓN CÁLCULO vs COPERNICUS CSV")
    print("=" * 120)
    print(f"Parcela: 211 SRRG, Calabozo, Venezuela")
    print(f"Período: 2025-05-18 a 2026-05-18")
    print(f"Tolerancia: ±0.05 (5%)")
    print("=" * 120)

    # 1. Obtener fechas de STAC
    print("\n🔍 PASO 1: Obteniendo fechas disponibles en STAC...")
    stac_dates = await sentinel_service.get_available_dates(
        polygon_coords=PARCELA_211,
        start_date="2025-05-18",
        end_date="2026-05-18",
        max_cloud=20
    )

    stac_dates_set = {d['date'] for d in stac_dates}
    print(f"   ✅ {len(stac_dates_set)} fechas en STAC")

    # 2. Cargar fechas de CSV Copernicus
    copernicus_dates_set = set(COPERNICUS_DATES)
    print(f"   ✅ {len(copernicus_dates_set)} fechas en CSV Copernicus")

    # 3. Encontrar fechas coincidentes
    common_dates = sorted(stac_dates_set & copernicus_dates_set)
    print(f"\n📊 Fechas coincidentes en ambos: {len(common_dates)}")

    if len(common_dates) == 0:
        print("\n❌ No hay fechas coincidentes para validar")
        return

    # 4. Para cada fecha coincidente: descargar, calcular, comparar
    print("\n" + "=" * 120)
    print("PASO 2: Descargando bandas, calculando NDVI y comparando...")
    print("=" * 120)
    print(f"⏱️  Este proceso puede tardar varios minutos ({len(common_dates)} fechas)...")
    print()

    results = []
    errors = []

    for i, date in enumerate(common_dates, 1):
        print(f"\n[{i}/{len(common_dates)}] 📅 {date}")

        try:
            # Descargar B04
            print(f"   📥 Descargando B04...", end=" ", flush=True)
            b04_bytes = await sentinel_service.download_bands(
                polygon_geojson={
                    "type": "Polygon",
                    "coordinates": [PARCELA_211]
                },
                bands=["B04"],
                start_date=date,
                end_date=date,
                width=512,
                height=512,
                max_cloud_coverage=20
            )
            print(f"✅ {len(b04_bytes)} bytes")

            # Descargar B08
            print(f"   📥 Descargando B08...", end=" ", flush=True)
            b08_bytes = await sentinel_service.download_bands(
                polygon_geojson={
                    "type": "Polygon",
                    "coordinates": [PARCELA_211]
                },
                bands=["B08"],
                start_date=date,
                end_date=date,
                width=512,
                height=512,
                max_cloud_coverage=20
            )
            print(f"✅ {len(b08_bytes)} bytes")

            # Calcular NDVI
            print(f"   🧮 Calculando NDVI...", end=" ", flush=True)
            ndvi_ours = calculate_ndvi_from_bands(b04_bytes, b08_bytes)
            print(f"✅ {ndvi_ours:.4f}")

            # Comparar con Copernicus
            ndvi_copernicus = COPERNICUS_MEAN[date]
            difference = abs(ndvi_ours - ndvi_copernicus)
            within_tolerance = difference <= 0.05

            status = "✅ PASS" if within_tolerance else "❌ FAIL"
            print(f"   📊 NDVI Copernicus: {ndvi_copernicus:.4f}")
            print(f"   📊 Diferencia: {difference:.4f} ({difference*100:.2f}%) - {status}")

            results.append({
                "date": date,
                "ndvi_ours": ndvi_ours,
                "ndvi_copernicus": ndvi_copernicus,
                "difference": difference,
                "within_tolerance": within_tolerance
            })

        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            errors.append({
                "date": date,
                "error": str(e)
            })

    # 5. Generar tabla resumen
    print("\n" + "=" * 120)
    print("TABLA RESUMEN - COMPARACIÓN NDVI")
    print("=" * 120)
    print(f"{'Fecha':<12} | {'NDVI Nuestro':<13} | {'NDVI Copernicus':<16} | {'Diferencia':<11} | {'±0.05?':<8}")
    print("-" * 120)

    for r in results:
        status = "✅ PASS" if r['within_tolerance'] else "❌ FAIL"
        print(f"{r['date']:<12} | {r['ndvi_ours']:<13.4f} | {r['ndvi_copernicus']:<16.4f} | {r['difference']:<11.4f} | {status:<8}")

    if errors:
        print("\n⚠️  ERRORES EN DESCARGAS:")
        for e in errors:
            print(f"   - {e['date']}: {e['error'][:80]}")

    # 6. Estadísticas finales
    print("\n" + "=" * 120)
    print("ESTADÍSTICAS FINALES")
    print("=" * 120)

    total_coincident = len(common_dates)
    total_processed = len(results)
    total_pass = sum(1 for r in results if r['within_tolerance'])
    total_fail = sum(1 for r in results if not r['within_tolerance'])

    print(f"\n📊 Fechas coincidentes entre STAC y CSV: {total_coincident}")
    print(f"   ✅ Procesadas exitosamente: {total_processed}")
    print(f"   ❌ Errores en descarga: {len(errors)}")

    if results:
        print(f"\n📊 Validación NDVI (de {total_processed} procesadas):")
        print(f"   ✅ Dentro de ±0.05: {total_pass} ({100*total_pass/total_processed:.1f}%)")
        print(f"   ❌ Fuera de ±0.05: {total_fail} ({100*total_fail/total_processed:.1f}%)")

        # Diferencia promedio
        avg_diff = np.mean([r['difference'] for r in results])
        max_diff = max([r['difference'] for r in results])
        min_diff = min([r['difference'] for r in results])

        print(f"\n📊 Análisis de diferencias:")
        print(f"   Media: {avg_diff:.4f} ({avg_diff*100:.2f}%)")
        print(f"   Mínima: {min_diff:.4f} ({min_diff*100:.2f}%)")
        print(f"   Máxima: {max_diff:.4f} ({max_diff*100:.2f}%)")

        # Casos extremos
        if total_fail > 0:
            print(f"\n⚠️  FECHAS FUERA DE TOLERANCIA:")
            failed = [r for r in results if not r['within_tolerance']]
            for r in sorted(failed, key=lambda x: x['difference'], reverse=True)[:5]:
                print(f"   - {r['date']}: diferencia {r['difference']:.4f} (nuestro: {r['ndvi_ours']:.4f}, Copernicus: {r['ndvi_copernicus']:.4f})")

    print("\n" + "=" * 120)
    print("CONCLUSIÓN")
    print("=" * 120)

    if results:
        pass_rate = 100 * total_pass / total_processed
        avg_diff_pct = avg_diff * 100

        if pass_rate >= 80 and avg_diff_pct < 3:
            print("✅ VALIDACIÓN EXITOSA:")
            print(f"   - {pass_rate:.1f}% de fechas dentro de tolerancia ±0.05")
            print(f"   - Diferencia promedio: {avg_diff_pct:.2f}%")
            print("   - Nuestro cálculo NDVI es CORRECTO y coincide con Copernicus")
        elif pass_rate >= 60:
            print("⚠️  VALIDACIÓN ACEPTABLE:")
            print(f"   - {pass_rate:.1f}% de fechas dentro de tolerancia")
            print(f"   - Diferencia promedio: {avg_diff_pct:.2f}%")
            print("   - Revisar fechas con mayor discrepancia")
        else:
            print("❌ VALIDACIÓN FALLIDA:")
            print(f"   - Solo {pass_rate:.1f}% de fechas dentro de tolerancia")
            print(f"   - Diferencia promedio: {avg_diff_pct:.2f}%")
            print("   - Revisar implementación NDVI o factor de escala L2A")

    print("=" * 120)


if __name__ == "__main__":
    asyncio.run(validate_ndvi_cross_check())
