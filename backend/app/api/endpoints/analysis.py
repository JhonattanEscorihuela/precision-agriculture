"""
OE3+OE4 - Endpoint para análisis completo de parcelas.
Pipeline: NDVI → Segmentación → Textura sobre todas las fechas disponibles.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.user import User
from app.core.security import get_current_user
from app.schemas.analysis import (
    FullAnalysisResponse,
    AnalysisErrorResponse
)
from app.services.analysis_service import AnalysisService


router = APIRouter()


@router.post(
    "/run/{polygon_id}",
    response_model=FullAnalysisResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": AnalysisErrorResponse, "description": "Polygon not found"},
        403: {"model": AnalysisErrorResponse, "description": "Access denied"},
        400: {"model": AnalysisErrorResponse, "description": "No NDVI results found for this polygon"}
    }
)
async def run_full_analysis(
    polygon_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Ejecuta análisis completo sobre todas las fechas NDVI de una parcela.

    **Workflow:**
    1. Verifica que el polígono existe y pertenece al usuario actual
    2. Obtiene todos los NDVIResult del polígono (requiere al menos 1)
    3. Para cada fecha:
       - Calcula segmentación (threshold=0.30, sin guardar máscara)
       - Calcula textura (3 descriptores: edges, homogeneity, contrast)
       - Acumula resultados por fecha
       - Si hay error: acumula en dates_failed y continúa con siguiente fecha
    4. Agrega métricas por kernel:
       - **mean_std_normalized**: promedio de std_normalized sobre todas las fechas
       - **dates_discriminative**: cantidad de fechas donde std_normalized > 0.10
    5. Identifica kernel más discriminativo (mayor mean_std_normalized)

    **Idempotencia:** Los servicios internos (segmentación + textura) son idempotentes.
    Múltiples llamadas retornan los mismos resultados cacheados en BD.

    **Prerequisito:** El polígono debe tener al menos 1 NDVI calculado.
    Usar POST /api/ndvi/calculate para cada fecha antes de ejecutar este pipeline.

    Args:
        polygon_id: ID del polígono a analizar
        db: Sesión de base de datos
        current_user: Usuario autenticado (JWT)

    Returns:
        FullAnalysisResponse con:
        - Resumen (polygon_id, total_ndvi_results, dates_processed, dates_failed)
        - per_date_results: lista detallada por fecha (NDVI + segmentación + textura)
        - aggregated: métricas por kernel + most_discriminative_kernel

    Raises:
        HTTPException 404: Si el polígono no existe
        HTTPException 403: Si el usuario no tiene acceso al polígono
        HTTPException 400: Si el polígono no tiene NDVI results calculados
    """
    service = AnalysisService()

    result = await service.run_full_analysis(
        polygon_id=polygon_id,
        user_id=current_user.id,
        db=db
    )

    return result
