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
            ndvi_result_id=result["ndvi_id"],
            acquisition_id=result["acquisition_id"],
            polygon_id=result["polygon_id"],
            acquisition_date=result["acquisition_date"],
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
            ndvi_result_id=ndvi.id,
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
        ndvi_result_id=result["ndvi_id"],
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


@router.get(
    "/{acquisition_id}/overlay",
    responses={
        200: {
            "description": "PNG coloreado con bounds para visualización en mapa",
            "content": {
                "application/json": {
                    "example": {
                        "image_base64": "data:image/png;base64,iVBORw0KG...",
                        "bounds": [[8.838, -67.528], [8.853, -67.515]],
                        "cached": True,
                        "metadata": {
                            "date": "2026-03-22",
                            "polygon_id": 10,
                            "thresholds": {"critical": 0.3, "alert": 0.5}
                        }
                    }
                }
            }
        },
        404: {"model": NDVIErrorResponse, "description": "NDVI not calculated yet"},
        403: {"model": NDVIErrorResponse, "description": "Access denied"}
    }
)
async def get_ndvi_overlay(
    acquisition_id: int,
    force: bool = False,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Genera overlay coloreado del NDVI para visualización en mapa Leaflet.

    **Workflow:**
    1. Busca NDVIResult por acquisition_id
    2. Verifica ownership del polígono
    3. Si existe cache (overlay_png) y no force → retorna desde caché
    4. Si no existe cache o force=true:
       - Genera PNG coloreado RGBA desde TIFF NDVI
       - Paleta: Verde (≥0.5) / Amarillo (0.3-0.5) / Rojo (<0.3)
       - Guarda en cache (campo overlay_png)
    5. Retorna base64 + bounds + metadata

    **Cache policy:**
    - Primera llamada: calcula y guarda (cached=false)
    - Siguientes llamadas: sirve desde cache (cached=true)
    - Query param ?force=true: recalcula y actualiza cache

    Args:
        acquisition_id: ID de la adquisición
        force: Forzar recálculo aunque exista caché (default: False)
        db: Sesión de base de datos
        current_user: Usuario autenticado (JWT)

    Returns:
        JSON con image_base64, bounds, cached flag y metadata

    Raises:
        HTTPException 404: Si no existe NDVI calculado
        HTTPException 403: Si no tiene acceso
        HTTPException 500: Si hay error generando overlay
    """
    import base64
    from app.services.ndvi_overlay_service import generate_ndvi_overlay
    from app.models.acquisition import SentinelAcquisition

    try:
        # 1. Buscar NDVIResult
        ndvi_result = await crud_ndvi.get_ndvi_by_acquisition(db, acquisition_id)
        if not ndvi_result:
            raise HTTPException(
                status_code=404,
                detail=f"NDVI not calculated for acquisition_id={acquisition_id}"
            )

        # 2. Verificar ownership del polígono
        polygon = await crud_polygon.get_polygon_by_id(db, ndvi_result.polygon_id)
        if not polygon or polygon.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You don't have access to this NDVI result"
            )

        # 3. Obtener fecha de adquisición
        from sqlalchemy import select
        query = select(SentinelAcquisition.acquisition_date).where(
            SentinelAcquisition.id == acquisition_id
        )
        result = await db.execute(query)
        acquisition_date = result.scalar_one_or_none()

        # 4. Preparar geometría del polígono para máscara
        polygon_geojson = {
            "type": "Polygon",
            "coordinates": [polygon.coordinates]  # polygon.coordinates ya es [[lng, lat], ...]
        }

        # 5. Cache check
        if ndvi_result.overlay_png and not force:
            # Servir desde caché
            png_bytes = ndvi_result.overlay_png
            # Re-generar bounds desde el TIFF (no se cachean separadamente)
            _, leaflet_bounds = generate_ndvi_overlay(ndvi_result.ndvi_tiff, polygon_geojson)
            cached = True
        else:
            # 6. Generar overlay con máscara de polígono
            png_bytes, leaflet_bounds = generate_ndvi_overlay(ndvi_result.ndvi_tiff, polygon_geojson)

            # 7. Guardar en cache
            await crud_ndvi.update_overlay_cache(db, ndvi_result.id, png_bytes)
            cached = False

        # 7. Codificar a base64
        image_b64 = f"data:image/png;base64,{base64.b64encode(png_bytes).decode()}"

        # 8. Respuesta
        return {
            "image_base64": image_b64,
            "bounds": leaflet_bounds,
            "cached": cached,
            "metadata": {
                "date": str(acquisition_date) if acquisition_date else None,
                "polygon_id": ndvi_result.polygon_id,
                "thresholds": {"critical": 0.3, "alert": 0.5}
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating NDVI overlay: {str(e)}"
        )
