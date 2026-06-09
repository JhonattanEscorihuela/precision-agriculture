"""
OE2 - Endpoints para cálculo y consulta de NDVI.
Solo orquestación, lógica en app/services/ndvi_service.py
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import io

from app.database import get_session
from app.models.user import User
from app.core.security import get_current_user
from app.schemas.ndvi import (
    NDVICalculateRequest,
    NDVICalculateResponse,
    NDVIStatsResponse,
    NDVIErrorResponse
)
from app.services.ndvi_service import NDVIService
from app.crud import ndvi as crud_ndvi
from app.crud import polygon as crud_polygon


router = APIRouter()


# ⚠️ ORDEN CRÍTICO: Registrar rutas específicas ANTES de las genéricas
# FastAPI evalúa rutas en orden de registro
# Si /{acquisition_id} se registra antes que /polygon/{polygon_id},
# FastAPI intentará convertir "polygon" a int y fallará con 422


@router.post(
    "/calculate",
    response_model=NDVICalculateResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": NDVIErrorResponse, "description": "Acquisition not found"},
        403: {"model": NDVIErrorResponse, "description": "Access denied"},
        500: {"model": NDVIErrorResponse, "description": "Calculation error"}
    }
)
async def calculate_ndvi(
    request: NDVICalculateRequest,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Calcula el índice NDVI para una adquisición Sentinel-2.

    **Workflow:**
    1. Valida que acquisition_id existe
    2. Verifica que adquisición pertenece al usuario actual
    3. Si ya existe NDVI, lo retorna sin recalcular (idempotente)
    4. Si no existe, calcula NDVI con manejo de división por cero
    5. Guarda raster y estadísticos en BD
    6. Retorna estadísticos calculados

    **Idempotencia:** Múltiples llamadas con el mismo acquisition_id retornan el mismo resultado.

    Args:
        request: acquisition_id de la adquisición Sentinel-2
        db: Sesión de base de datos
        current_user: Usuario autenticado (JWT)

    Returns:
        NDVICalculateResponse con estadísticos y metadata

    Raises:
        HTTPException 404: Si acquisition_id no existe
        HTTPException 403: Si no tiene acceso a la adquisición
        HTTPException 500: Si hay error en el cálculo
    """
    service = NDVIService()
    result = await service.calculate_ndvi(
        acquisition_id=request.acquisition_id,
        user_id=current_user.id,
        db=db
    )

    # Formatear response con calculation_date en raíz
    return NDVICalculateResponse(
        ndvi_id=result["ndvi_id"],
        acquisition_id=result["acquisition_id"],
        polygon_id=result["polygon_id"],
        calculation_date=result["calculation_date"],
        stats=NDVIStatsResponse(
            acquisition_id=result["acquisition_id"],
            polygon_id=result["polygon_id"],
            calculation_date=result["calculation_date"],
            **result["stats"]
        ),
        message="NDVI calculado exitosamente"
    )


# Ruta específica /polygon/{polygon_id} ANTES de la genérica /{acquisition_id}
@router.get(
    "/polygon/{polygon_id}",
    response_model=List[NDVIStatsResponse],
    responses={
        403: {"model": NDVIErrorResponse, "description": "Access denied"}
    }
)
async def get_ndvi_by_polygon(
    polygon_id: int,
    start_date: str = None,
    end_date: str = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Lista todos los NDVI calculados para un polígono, opcionalmente filtrados por rango de fechas.

    Útil para el frontend dashboard: obtener NDVIs en período específico según filtro CloudWatch.
    Retorna lista ordenada por fecha de adquisición (cronológico).

    Args:
        polygon_id: ID del polígono
        start_date: Fecha inicio filtro (YYYY-MM-DD) - opcional
        end_date: Fecha fin filtro (YYYY-MM-DD) - opcional
        limit: Número máximo de resultados (default 100, suficiente para 2 años)
        db: Sesión de base de datos
        current_user: Usuario autenticado (JWT)

    Returns:
        Lista de NDVIStatsResponse en rango especificado

    Raises:
        HTTPException 403: Si no tiene acceso al polígono
    """
    # Verificar ownership del polígono
    polygon = await crud_polygon.get_polygon_by_id(db, polygon_id)
    if not polygon or polygon.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this polygon"
        )

    # Obtener NDVIs del polígono (ahora retorna tuplas con acquisition_date)
    ndvi_tuples = await crud_ndvi.get_ndvi_by_polygon(
        db,
        polygon_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )

    # Formatear respuestas
    return [
        NDVIStatsResponse(
            acquisition_id=ndvi.acquisition_id,
            polygon_id=ndvi.polygon_id,
            acquisition_date=acq_date,  # Fecha de la imagen satelital
            calculation_date=ndvi.calculation_date.isoformat(),
            ndvi_mean=ndvi.ndvi_mean,
            ndvi_min=ndvi.ndvi_min,
            ndvi_max=ndvi.ndvi_max,
            ndvi_std=ndvi.ndvi_std,
            width=ndvi.width,
            height=ndvi.height
        )
        for ndvi, acq_date in ndvi_tuples
    ]


# Ruta genérica /{acquisition_id} DESPUÉS de las específicas
@router.get(
    "/{acquisition_id}",
    response_model=NDVIStatsResponse,
    responses={
        404: {"model": NDVIErrorResponse, "description": "NDVI not calculated yet"},
        403: {"model": NDVIErrorResponse, "description": "Access denied"}
    }
)
async def get_ndvi_stats(
    acquisition_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene estadísticos NDVI si ya fueron calculados.

    Verifica ownership antes de retornar. El frontend usa este endpoint
    al montar NDVIPanel para detectar si ya existe NDVI calculado.

    Args:
        acquisition_id: ID de la adquisición
        db: Sesión de base de datos
        current_user: Usuario autenticado (JWT)

    Returns:
        NDVIStatsResponse con estadísticos

    Raises:
        HTTPException 404: Si no existe NDVI calculado
        HTTPException 403: Si no tiene acceso
    """
    service = NDVIService()
    result = await service.get_ndvi_stats(
        acquisition_id=acquisition_id,
        user_id=current_user.id,
        db=db
    )

    return NDVIStatsResponse(
        acquisition_id=result["acquisition_id"],
        polygon_id=result["polygon_id"],
        acquisition_date=result["acquisition_date"],
        calculation_date=result["calculation_date"],
        **result["stats"]
    )


@router.get(
    "/{acquisition_id}/tiff",
    responses={
        200: {
            "content": {"application/octet-stream": {}},
            "description": "TIFF file with NDVI raster (float32)"
        },
        404: {"model": NDVIErrorResponse, "description": "NDVI not calculated yet"},
        403: {"model": NDVIErrorResponse, "description": "Access denied"}
    }
)
async def download_ndvi_tiff(
    acquisition_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Descarga el raster NDVI como archivo TIFF.

    El TIFF contiene valores float32 en rango [-1, 1] con compresión LZW.
    Preserva CRS y transform del raster original. Verifica ownership antes
    de permitir descarga.

    Args:
        acquisition_id: ID de la adquisición
        db: Sesión de base de datos
        current_user: Usuario autenticado (JWT)

    Returns:
        StreamingResponse con TIFF file

    Raises:
        HTTPException 404: Si no existe NDVI calculado
        HTTPException 403: Si no tiene acceso
    """
    service = NDVIService()
    ndvi_tiff = await service.get_ndvi_tiff(
        acquisition_id=acquisition_id,
        user_id=current_user.id,
        db=db
    )

    # Crear stream desde bytes
    tiff_stream = io.BytesIO(ndvi_tiff)

    return StreamingResponse(
        tiff_stream,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename=ndvi_acquisition_{acquisition_id}.tif"
        }
    )
