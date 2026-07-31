"""
OE3 - Endpoints para segmentación espacial de zonas cultivadas.
Solo orquestación, lógica en app/services/segmentation_service.py
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io

from app.database import get_session
from app.models.user import User
from app.core.security import get_current_user
from app.schemas.segmentation import (
    SegmentationRequest,
    SegmentationResponse,
    SegmentationErrorResponse
)
from app.services.segmentation_service import SegmentationService


router = APIRouter()


@router.post(
    "/analyze",
    response_model=SegmentationResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": SegmentationErrorResponse, "description": "NDVI result not found"},
        403: {"model": SegmentationErrorResponse, "description": "Access denied"},
        400: {"model": SegmentationErrorResponse, "description": "Invalid threshold"},
        500: {"model": SegmentationErrorResponse, "description": "Segmentation error"}
    }
)
async def analyze_segmentation(
    request: SegmentationRequest,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Calcula segmentación de zonas cultivadas sobre un resultado NDVI.

    **Workflow:**
    1. Valida que ndvi_result_id existe
    2. Verifica que NDVI pertenece al usuario actual
    3. Si ya existe segmentación, la retorna sin recalcular (idempotente)
    4. Si no existe, aplica umbralización sobre raster NDVI
    5. Calcula métricas: total_pixels, cultivated_pixels, percentage
    6. Opcionalmente guarda máscara binaria TIFF (save_mask=True)
    7. Guarda métricas en BD
    8. Retorna métricas calculadas

    **Idempotencia:** Múltiples llamadas con el mismo ndvi_result_id retornan el mismo resultado.

    **Threshold:**
    - Default: 0.3 (vegetación moderada, cultivos tropicales)
    - Rango: [0.0, 1.0]
    - Píxeles con NDVI > threshold se clasifican como cultivados

    **save_mask:**
    - False (default): Solo guarda métricas (~200 bytes)
    - True: Guarda máscara binaria TIFF uint8 (~500KB)
    - Máscara disponible para descarga via GET /{segmentation_id}/mask

    Args:
        request: ndvi_result_id, threshold opcional, save_mask
        db: Sesión de base de datos
        current_user: Usuario autenticado (JWT)

    Returns:
        SegmentationResponse con métricas

    Raises:
        HTTPException 404: Si ndvi_result_id no existe
        HTTPException 403: Si no tiene acceso al NDVI
        HTTPException 400: Si threshold fuera de rango [0, 1]
        HTTPException 500: Si hay error en el cálculo
    """
    service = SegmentationService()

    try:
        result = await service.calculate_segmentation(
            ndvi_result_id=request.ndvi_result_id,
            user_id=current_user.id,
            db=db,
            threshold=request.threshold,
            save_mask=request.save_mask
        )
    except ValueError as e:
        # Threshold fuera de rango [0, 1]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return SegmentationResponse(**result)


@router.get(
    "/by-ndvi/{ndvi_result_id}",
    response_model=SegmentationResponse,
    responses={
        404: {"model": SegmentationErrorResponse, "description": "Segmentation not calculated yet"},
        403: {"model": SegmentationErrorResponse, "description": "Access denied"}
    }
)
async def get_segmentation_by_ndvi(
    ndvi_result_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene segmentación ya calculada para un resultado NDVI.

    Verifica ownership antes de retornar. El frontend usa este endpoint
    para detectar si ya existe segmentación calculada.

    Args:
        ndvi_result_id: ID del resultado NDVI
        db: Sesión de base de datos
        current_user: Usuario autenticado (JWT)

    Returns:
        SegmentationResponse con métricas

    Raises:
        HTTPException 404: Si no existe segmentación calculada
        HTTPException 403: Si no tiene acceso
    """
    service = SegmentationService()
    result = await service.get_segmentation_by_ndvi(
        ndvi_result_id=ndvi_result_id,
        user_id=current_user.id,
        db=db
    )

    return SegmentationResponse(**result)


@router.get(
    "/{segmentation_id}/mask",
    responses={
        200: {
            "content": {"application/octet-stream": {}},
            "description": "TIFF file with binary mask (uint8: 0=no cultivado, 1=cultivado)"
        },
        404: {"model": SegmentationErrorResponse, "description": "Mask not saved or segmentation not found"},
        403: {"model": SegmentationErrorResponse, "description": "Access denied"}
    }
)
async def download_segmentation_mask(
    segmentation_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Descarga la máscara binaria de segmentación como archivo TIFF.

    El TIFF contiene valores uint8: 0 (no cultivado) o 1 (cultivado) con compresión LZW.
    Preserva CRS y transform del raster original. Verifica ownership antes de permitir descarga.

    **Disponibilidad:**
    La máscara solo está disponible si se calculó con save_mask=True.
    Si la máscara no fue guardada, retorna 404 con mensaje explicativo.

    Args:
        segmentation_id: ID del resultado de segmentación
        db: Sesión de base de datos
        current_user: Usuario autenticado (JWT)

    Returns:
        StreamingResponse con TIFF file

    Raises:
        HTTPException 404: Si no existe segmentación o máscara no guardada
        HTTPException 403: Si no tiene acceso
    """
    service = SegmentationService()
    mask_tiff = await service.get_segmentation_mask(
        segmentation_id=segmentation_id,
        user_id=current_user.id,
        db=db
    )

    # Crear stream desde bytes
    tiff_stream = io.BytesIO(mask_tiff)

    return StreamingResponse(
        tiff_stream,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename=segmentation_mask_{segmentation_id}.tif"
        }
    )
