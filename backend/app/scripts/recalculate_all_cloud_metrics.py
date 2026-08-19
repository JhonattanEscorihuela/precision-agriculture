"""
Script para re-calcular métricas de nubosidad de todas las adquisiciones.
Ejecutar después de cambiar CLOUD_CLASSES para incluir clase 7.

Uso: python -m app.scripts.recalculate_all_cloud_metrics
"""

import asyncio
from sqlalchemy import select
from app.database import async_session
from app.models.acquisition import SentinelAcquisition
from app.models.polygon import Polygon
from app.services.cloud_coverage_service import calculate_parcel_cloud_coverage


async def recalculate_all_cloud_metrics():
    """Re-calcula métricas SCL para todas las adquisiciones que tengan scl_data."""

    async with async_session() as session:
        # Obtener todas las adquisiciones con SCL
        stmt = select(SentinelAcquisition).where(
            SentinelAcquisition.scl_data.isnot(None)
        ).order_by(SentinelAcquisition.id)

        result = await session.execute(stmt)
        acquisitions = result.scalars().all()

        total = len(acquisitions)
        print("=" * 80)
        print(f"RE-CÁLCULO DE MÉTRICAS SCL CON CLOUD_CLASSES = (7, 8, 9, 10)")
        print("=" * 80)
        print(f"Total adquisiciones con SCL: {total}")
        print()

        if total == 0:
            print("✅ No hay adquisiciones para procesar")
            return

        # Estadísticas
        processed = 0
        errors = 0
        changed_to_unsuitable = []
        changed_to_caution = []
        stayed_same = 0

        print("Procesando adquisiciones...")
        print()

        for acq in acquisitions:
            try:
                # Obtener polígono
                stmt = select(Polygon).where(Polygon.id == acq.polygon_id)
                result = await session.execute(stmt)
                polygon = result.scalar_one_or_none()

                if not polygon:
                    print(f"⚠️  Acq {acq.id}: Polígono {acq.polygon_id} no encontrado")
                    errors += 1
                    continue

                # Guardar estado anterior
                old_status = acq.quality_status
                old_cloud = acq.parcel_cloud_cover

                # Re-calcular métricas
                polygon_geojson = {"type": "Polygon", "coordinates": [polygon.coordinates]}
                metrics = calculate_parcel_cloud_coverage(acq.scl_data, polygon_geojson)

                # Actualizar campos
                acq.parcel_cloud_cover = metrics["parcel_cloud_cover"]
                acq.parcel_shadow_cover = metrics["parcel_shadow_cover"]
                acq.valid_pixel_percentage = metrics["valid_pixel_percentage"]
                acq.usable_pixel_percentage = metrics["usable_pixel_percentage"]
                acq.quality_status = metrics["quality_status"]

                # Registrar cambios
                new_status = acq.quality_status
                new_cloud = acq.parcel_cloud_cover

                if old_status != new_status:
                    change_info = {
                        "acq_id": acq.id,
                        "polygon_id": acq.polygon_id,
                        "polygon_name": polygon.name,
                        "date": acq.acquisition_date,
                        "old_status": old_status,
                        "new_status": new_status,
                        "old_cloud": old_cloud,
                        "new_cloud": new_cloud
                    }

                    if new_status == "unsuitable" and old_status in ["suitable", "caution"]:
                        changed_to_unsuitable.append(change_info)
                        print(f"⚠️  Acq {acq.id} (Parcela {acq.polygon_id}, {acq.acquisition_date}): "
                              f"{old_status} ({old_cloud:.2f}%) → unsuitable ({new_cloud:.2f}%)")
                    elif new_status == "caution":
                        changed_to_caution.append(change_info)
                        print(f"⚠️  Acq {acq.id} (Parcela {acq.polygon_id}, {acq.acquisition_date}): "
                              f"{old_status} ({old_cloud:.2f}%) → caution ({new_cloud:.2f}%)")
                    else:
                        print(f"ℹ️  Acq {acq.id} (Parcela {acq.polygon_id}, {acq.acquisition_date}): "
                              f"{old_status} ({old_cloud:.2f}%) → {new_status} ({new_cloud:.2f}%)")
                else:
                    stayed_same += 1

                processed += 1

            except Exception as e:
                print(f"❌ Error en acq {acq.id}: {str(e)}")
                errors += 1
                continue

        # Guardar cambios
        print()
        print("Guardando cambios en base de datos...")
        await session.commit()
        print("✅ Cambios guardados")
        print()

        # Resumen
        print("=" * 80)
        print("RESUMEN")
        print("=" * 80)
        print(f"Total procesadas: {processed}/{total}")
        print(f"Errores: {errors}")
        print(f"Sin cambios: {stayed_same}")
        print(f"Cambios a unsuitable: {len(changed_to_unsuitable)}")
        print(f"Cambios a caution: {len(changed_to_caution)}")
        print()

        if changed_to_unsuitable:
            print("=" * 80)
            print("ADQUISICIONES QUE CAMBIARON A UNSUITABLE")
            print("=" * 80)
            print(f"{'Acq ID':<8} {'Parcela':<8} {'Fecha':<12} {'Cloud Antes':<12} {'Cloud Ahora':<12} {'Nombre Parcela'}")
            print("-" * 80)
            for change in changed_to_unsuitable:
                print(f"{change['acq_id']:<8} {change['polygon_id']:<8} {change['date']:<12} "
                      f"{change['old_cloud']:>10.2f}% {change['new_cloud']:>10.2f}% "
                      f"{change['polygon_name'][:30]}")
            print()

        if changed_to_caution:
            print("=" * 80)
            print("ADQUISICIONES QUE CAMBIARON A CAUTION")
            print("=" * 80)
            print(f"{'Acq ID':<8} {'Parcela':<8} {'Fecha':<12} {'Cloud Antes':<12} {'Cloud Ahora':<12}")
            print("-" * 80)
            for change in changed_to_caution:
                print(f"{change['acq_id']:<8} {change['polygon_id']:<8} {change['date']:<12} "
                      f"{change['old_cloud']:>10.2f}% {change['new_cloud']:>10.2f}%")
            print()

        # Resumen por parcela
        print("=" * 80)
        print("IMPACTO POR PARCELA")
        print("=" * 80)

        parcels_affected = {}
        for change in changed_to_unsuitable:
            pid = change['polygon_id']
            if pid not in parcels_affected:
                parcels_affected[pid] = {
                    "name": change['polygon_name'],
                    "dates": []
                }
            parcels_affected[pid]["dates"].append(change['date'])

        if parcels_affected:
            for pid, info in sorted(parcels_affected.items()):
                print(f"Parcela {pid} ({info['name'][:40]}):")
                print(f"  - Fechas ahora unsuitable: {len(info['dates'])}")
                print(f"  - Fechas: {', '.join(sorted(info['dates']))}")
                print()
        else:
            print("✅ Ninguna parcela afectada")

        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(recalculate_all_cloud_metrics())
