"""
Script para analizar la distribución de clases SCL en una adquisición.
Uso: python -m app.scripts.analyze_scl_distribution <acquisition_id>
"""

import sys
import io
import asyncio
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from sqlalchemy import select
from app.database import async_session
from app.models.acquisition import SentinelAcquisition
from app.models.polygon import Polygon


async def analyze_scl_distribution(acq_id: int):
    """Analiza la distribución de clases SCL dentro de una parcela."""

    async with async_session() as session:
        # Obtener adquisición
        stmt = select(SentinelAcquisition).where(SentinelAcquisition.id == acq_id)
        result = await session.execute(stmt)
        acquisition = result.scalar_one_or_none()

        if not acquisition:
            print(f"❌ Acquisition {acq_id} not found")
            return

        # Obtener polígono
        stmt = select(Polygon).where(Polygon.id == acquisition.polygon_id)
        result = await session.execute(stmt)
        polygon = result.scalar_one_or_none()

        if not polygon:
            print(f"❌ Polygon {acquisition.polygon_id} not found")
            return

        print("=" * 70)
        print(f"ANÁLISIS SCL - Acquisition ID: {acq_id}")
        print("=" * 70)
        print(f"Parcela: {polygon.name}")
        print(f"Polygon ID: {polygon.id}")
        print(f"Fecha: {acquisition.acquisition_date}")
        print(f"Scene ID: {acquisition.scene_id or 'N/A'}")
        print(f"Scene cloud: {acquisition.cloud_coverage}%")
        print(f"Parcel cloud (BD): {acquisition.parcel_cloud_cover}%")
        print(f"Quality status: {acquisition.quality_status}")
        print()

        if not acquisition.scl_data:
            print("❌ No hay datos SCL para esta adquisición")
            return

        # Cargar SCL
        with rasterio.open(io.BytesIO(acquisition.scl_data)) as src:
            scl = src.read(1)  # Banda 1 = SCL
            datamask = src.read(2)  # Banda 2 = dataMask
            transform = src.transform

            print(f"Dimensiones raster: {src.width}x{src.height} píxeles")
            print()

            # Crear máscara del polígono
            polygon_geom = {"type": "Polygon", "coordinates": [polygon.coordinates]}
            parcel_mask = geometry_mask(
                [polygon_geom],
                out_shape=scl.shape,
                transform=transform,
                invert=True
            )

            # Aplicar máscara: solo píxeles dentro del polígono
            scl_in_parcel = scl[parcel_mask]
            datamask_in_parcel = datamask[parcel_mask]

            total_pixels = len(scl_in_parcel)
            valid_pixels = np.sum(datamask_in_parcel > 0)
            invalid_pixels = np.sum(datamask_in_parcel == 0)

            print(f"Total píxeles en parcela: {total_pixels:,}")
            print(f"  - Válidos (dataMask > 0): {valid_pixels:,} ({100*valid_pixels/total_pixels:.1f}%)")
            print(f"  - Inválidos (dataMask = 0): {invalid_pixels:,} ({100*invalid_pixels/total_pixels:.1f}%)")
            print()

            # Distribución de clases SCL
            scl_classes = {
                0: "No Data",
                1: "Saturated or defective",
                2: "Dark Area Pixels",
                3: "Cloud shadows",
                4: "Vegetation",
                5: "Not vegetated",
                6: "Water",
                7: "Unclassified",
                8: "Cloud medium probability",
                9: "Cloud high probability",
                10: "Thin cirrus",
                11: "Snow/Ice"
            }

            print("DISTRIBUCIÓN DE CLASES SCL:")
            print("-" * 70)
            print(f"{'Clase':<6} {'Nombre':<30} {'Píxeles':>10} {'%Total':>8} {'%Válidos':>10}")
            print("-" * 70)

            class_counts = {}
            for class_val in range(12):
                count = np.sum(scl_in_parcel == class_val)
                if count > 0:
                    class_counts[class_val] = count
                    class_name = scl_classes.get(class_val, f"Unknown {class_val}")
                    pct_total = 100 * count / total_pixels
                    pct_valid = 100 * count / valid_pixels if valid_pixels > 0 else 0

                    # Marcar clases importantes
                    marker = ""
                    if class_val == 7:
                        marker = " ⚠️  UNCLASSIFIED"
                    elif class_val in [8, 9, 10]:
                        marker = " ☁️  NUBE"
                    elif class_val == 3:
                        marker = " 🌑 SOMBRA"

                    print(f"{class_val:<6} {class_name:<30} {count:>10,} {pct_total:>7.2f}% {pct_valid:>9.2f}%{marker}")

            print("-" * 70)

            # Análisis específico de clase 7
            print()
            print("ANÁLISIS CLASE 7 (UNCLASSIFIED):")
            print("-" * 70)

            class_7_count = class_counts.get(7, 0)
            if class_7_count > 0:
                class_7_pct = 100 * class_7_count / total_pixels
                class_7_pct_valid = 100 * class_7_count / valid_pixels if valid_pixels > 0 else 0

                print(f"Píxeles clase 7: {class_7_count:,}")
                print(f"Porcentaje del total: {class_7_pct:.2f}%")
                print(f"Porcentaje de válidos: {class_7_pct_valid:.2f}%")
                print()

                # Crear máscara de clase 7 para análisis espacial
                class_7_mask = (scl == 7) & parcel_mask

                # Obtener posiciones de píxeles clase 7
                rows, cols = np.where(class_7_mask)

                if len(rows) > 0:
                    print("Distribución espacial:")
                    print(f"  - Fila mínima: {rows.min()}")
                    print(f"  - Fila máxima: {rows.max()}")
                    print(f"  - Columna mínima: {cols.min()}")
                    print(f"  - Columna máxima: {cols.max()}")
                    print(f"  - Rango vertical: {rows.max() - rows.min() + 1} píxeles")
                    print(f"  - Rango horizontal: {cols.max() - cols.min() + 1} píxeles")

                    # Calcular dispersión
                    row_std = np.std(rows)
                    col_std = np.std(cols)
                    print(f"  - Desviación estándar (filas): {row_std:.1f}")
                    print(f"  - Desviación estándar (cols): {col_std:.1f}")

                    # Clusters aproximados
                    if row_std < 10 and col_std < 10:
                        print("  → Píxeles CONCENTRADOS (posible nube localizada)")
                    elif row_std > 50 or col_std > 50:
                        print("  → Píxeles DISPERSOS (posible ruido o neblina)")
                    else:
                        print("  → Píxeles SEMI-DISPERSOS")
            else:
                print("✅ NO hay píxeles clase 7 en esta parcela")

            print()

            # Análisis de nubes (clases 8, 9, 10)
            print("ANÁLISIS NUBES (clases 8, 9, 10):")
            print("-" * 70)

            cloud_pixels = sum(class_counts.get(c, 0) for c in [8, 9, 10])
            if cloud_pixels > 0:
                cloud_pct = 100 * cloud_pixels / valid_pixels if valid_pixels > 0 else 0
                print(f"Total píxeles nube: {cloud_pixels:,}")
                print(f"Porcentaje de válidos: {cloud_pct:.2f}%")
                print(f"⚠️  Esto NO incluye clase 7 (unclassified)")
            else:
                print("✅ NO hay píxeles clasificados como nube (8/9/10)")

            print()

            # Comparación
            print("COMPARACIÓN:")
            print("-" * 70)
            print(f"Nubosidad reportada en BD: {acquisition.parcel_cloud_cover}%")
            print(f"Nubosidad calculada (8+9+10): {cloud_pct:.2f}%")

            if class_7_count > 0:
                total_cloud_with_7 = cloud_pixels + class_7_count
                total_pct_with_7 = 100 * total_cloud_with_7 / valid_pixels if valid_pixels > 0 else 0
                print(f"Nubosidad SI incluimos clase 7: {total_pct_with_7:.2f}%")
                print()
                print(f"⚠️  DIFERENCIA: {total_pct_with_7 - cloud_pct:.2f}% puntos porcentuales")

                if total_pct_with_7 > 20:
                    print(f"⚠️  Si clase 7 se contara como nube, esta fecha sería UNSUITABLE (>{20}%)")

            print()
            print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python -m app.scripts.analyze_scl_distribution <acquisition_id>")
        sys.exit(1)

    acq_id = int(sys.argv[1])
    asyncio.run(analyze_scl_distribution(acq_id))
