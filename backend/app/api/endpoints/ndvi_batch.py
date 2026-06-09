"""
OE2 - Endpoint para cálculo batch de NDVIs.
Adquiere bandas y calcula NDVI para múltiples fechas automáticamente.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database import get_session, engine
from app.models.user import User
from app.core.security import get_current_user
from app.crud import polygon as crud_polygon
from app.crud import acquisition as crud_acquisition
from app.crud import ndvi as crud_ndvi
from app.services.sentinel_service import SentinelService
from app.services.ndvi_service import NDVIService
from pydantic import BaseModel
from typing import List
import logging
import asyncio

router = APIRouter()
logger = logging.getLogger(__name__)


class BatchCalculateRequest(BaseModel):
    polygon_id: int
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    max_cloud: int = 20


class BatchCalculateResponse(BaseModel):
    total_dates: int
    already_calculated: int
    newly_calculated: int
    failed: int
    results: List[dict]


@router.post("/calculate-batch", response_model=BatchCalculateResponse)
async def calculate_ndvi_batch(
    request: BatchCalculateRequest,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Calcula NDVIs en batch para todas las fechas disponibles en un rango.

    Workflow:
    1. Consulta fechas disponibles en Sentinel (STAC API)
    2. Filtra fechas que ya tienen NDVI calculado
    3. Para cada fecha sin NDVI:
       a. Adquiere bandas B04 y B08 (si no existen)
       b. Calcula NDVI
    4. Retorna resumen de resultados
    """

    # Verificar ownership de la parcela
    polygon = await crud_polygon.get_polygon_by_id(db, request.polygon_id)
    if not polygon:
        raise HTTPException(status_code=404, detail="Polygon not found")

    if polygon.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this polygon")

    logger.info(f"Starting batch NDVI calculation for polygon {request.polygon_id} ({request.start_date} to {request.end_date})")

    # Instanciar servicios
    sentinel_svc = SentinelService()
    ndvi_svc = NDVIService()

    # 1. Obtener fechas disponibles desde Sentinel
    try:
        available_dates = await sentinel_svc.get_available_dates(
            polygon_coords=polygon.coordinates,
            start_date=request.start_date,
            end_date=request.end_date,
            max_cloud=request.max_cloud
        )
    except Exception as e:
        logger.error(f"Error fetching available dates: {e}")
        raise HTTPException(status_code=500, detail="Error consulting Sentinel dates")

    logger.info(f"Found {len(available_dates)} dates with cloud < {request.max_cloud}%")

    # 2. Obtener adquisiciones existentes
    existing_acquisitions = await crud_acquisition.get_acquisitions_by_polygon(db, request.polygon_id)
    existing_dates = {acq.acquisition_date for acq in existing_acquisitions}

    # 3. Obtener NDVIs ya calculados
    existing_ndvis = await crud_ndvi.get_ndvi_by_polygon(
        db, request.polygon_id,
        start_date=request.start_date,
        end_date=request.end_date,
        limit=1000
    )
    calculated_dates = {result.acquisition_date for result in existing_ndvis}

    logger.info(f"Already calculated: {len(calculated_dates)} dates")

    # 4. Filtrar fechas que necesitan procesamiento
    dates_to_process = [
        date_info for date_info in available_dates
        if date_info["date"] not in calculated_dates
    ]

    logger.info(f"Dates to process: {len(dates_to_process)}")

    # 5. Función para procesar una fecha individual (con su propia sesión DB)
    async def process_single_date(date_info: dict):
        date_str = date_info["date"]

        # Crear sesión DB independiente para este task
        async with AsyncSession(engine) as task_db:
            try:
                # Adquirir bandas (idempotente)
                if date_str not in existing_dates:
                    logger.info(f"📥 Acquiring bands for {date_str}...")
                    acquisition_result = await sentinel_svc.acquire_bands(
                        polygon_coords=polygon.coordinates,
                        date=date_str,
                        polygon_id=request.polygon_id,
                        db_session=task_db
                    )
                    acquisition_id = acquisition_result["acquisition_id"]
                else:
                    # Buscar acquisition_id existente
                    acquisition = next((acq for acq in existing_acquisitions if acq.acquisition_date == date_str), None)
                    acquisition_id = acquisition.id if acquisition else None

                if not acquisition_id:
                    raise Exception("Failed to get acquisition_id")

                # Calcular NDVI (idempotente)
                logger.info(f"🧮 Calculating NDVI for {date_str}...")
                ndvi_result = await ndvi_svc.calculate_ndvi(
                    acquisition_id=acquisition_id,
                    user_id=current_user.id,
                    db=task_db
                )

                # CRÍTICO: Commit explícito para persistir cambios antes de salir del contexto
                await task_db.commit()

                logger.info(f"✅ {date_str}: NDVI mean = {ndvi_result['stats']['ndvi_mean']:.3f}")
                return {
                    "date": date_str,
                    "status": "success",
                    "ndvi_mean": ndvi_result["stats"]["ndvi_mean"]
                }

            except Exception as e:
                await task_db.rollback()
                logger.error(f"❌ {date_str}: {str(e)}", exc_info=True)
                return {
                    "date": date_str,
                    "status": "failed",
                    "error": str(e)
                }

    # 6. Procesar fechas en PARALELO con límite de concurrencia
    logger.info(f"🚀 Starting parallel processing of {len(dates_to_process)} dates...")

    # Limitar a 5 tareas simultáneas para evitar sobrecarga de Sentinel API
    async def process_with_semaphore(date_info, semaphore):
        async with semaphore:
            return await process_single_date(date_info)

    if dates_to_process:
        semaphore = asyncio.Semaphore(5)  # Máximo 5 tareas simultáneas
        process_results = await asyncio.gather(
            *[process_with_semaphore(date_info, semaphore) for date_info in dates_to_process],
            return_exceptions=False
        )
    else:
        process_results = []

    # 7. Consolidar resultados
    results = []
    newly_calculated = 0
    failed = 0

    # Agregar fechas ya calculadas
    for date_info in available_dates:
        if date_info["date"] in calculated_dates:
            results.append({
                "date": date_info["date"],
                "status": "already_calculated",
                "ndvi_mean": None
            })

    # Agregar resultados del procesamiento
    for result in process_results:
        results.append(result)
        if result["status"] == "success":
            newly_calculated += 1
        elif result["status"] == "failed":
            failed += 1

    logger.info(f"🏁 Batch complete: {newly_calculated} new, {len(calculated_dates)} existing, {failed} failed")

    return BatchCalculateResponse(
        total_dates=len(available_dates),
        already_calculated=len(calculated_dates),
        newly_calculated=newly_calculated,
        failed=failed,
        results=results
    )
