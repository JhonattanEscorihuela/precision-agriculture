"""
OE4 - Endpoints para análisis de textura mediante filtrado convolucional.
Solo orquestación, lógica en app/services/texture_service.py
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_session
from app.models.user import User
from app.core.security import get_current_user
from app.schemas.texture import (
    TextureRequest,
    TextureDescriptorResponse,
    TextureErrorResponse
)
from app.services.texture_service import TextureService


router = APIRouter()


@router.post(
    "/analyze",
    response_model=List[TextureDescriptorResponse],
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": TextureErrorResponse, "description": "Segmentation or NDVI not found"},
        403: {"model": TextureErrorResponse, "description": "Access denied"},
        400: {"model": TextureErrorResponse, "description": "Cultivated area too small after erosion"},
        500: {"model": TextureErrorResponse, "description": "Texture calculation error"}
    }
)
async def analyze_texture(
    request: TextureRequest,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Calcula los 3 descriptores de textura sobre una segmentación.

    **Workflow:**
    1. Valida que segmentation_result_id existe
    2. Verifica que segmentación pertenece al usuario actual
    3. Si ya existen 3 descriptores, los retorna sin recalcular (idempotente)
    4. Si no existen, lee NDVI TIFF
    5. Regenera máscara cultivada (reusa threshold de segmentación)
    6. Aplica erosión morfológica de 1 píxel
    7. Aplica 3 operadores convolucionales:
       - **edges** (Laplaciano): detecta bordes y transiciones abruptas
       - **homogeneity** (varianza local): cuantifica heterogeneidad espacial
       - **contrast** (magnitud gradiente): mide magnitud de cambios locales
    8. Calcula estadísticos (mean, std, min, max)
    9. Normaliza respuestas a [0,1] y evalúa criterio discriminativo (std_normalized > 0.10)
    10. Guarda 3 descriptores en BD (transacción atómica)
    11. Retorna lista de 3 descriptores

    **Idempotencia:** Múltiples llamadas con el mismo segmentation_result_id retornan los mismos 3 resultados.

    **Metodología científica:** Implementación estricta de `docs/metodologia_textura_OE4.md v2.1`

    Args:
        request: segmentation_result_id
        db: Sesión de base de datos
        current_user: Usuario autenticado (JWT)

    Returns:
        Lista de 3 TextureDescriptorResponse (edges, homogeneity, contrast)

    Raises:
        HTTPException 404: Si segmentation_result_id no existe
        HTTPException 403: Si no tiene acceso a la segmentación
        HTTPException 400: Si área cultivada muy pequeña tras erosión (<10 píxeles)
        HTTPException 500: Si hay error en cálculo de convolución
    """
    service = TextureService()

    try:
        descriptors = await service.calculate_texture(
            segmentation_result_id=request.segmentation_result_id,
            user_id=current_user.id,
            db=db
        )
    except ValueError as e:
        # Zona cultivada muy pequeña tras erosión
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return descriptors


@router.get(
    "/by-segmentation/{segmentation_result_id}",
    response_model=List[TextureDescriptorResponse],
    responses={
        404: {"model": TextureErrorResponse, "description": "Texture descriptors not calculated yet"},
        403: {"model": TextureErrorResponse, "description": "Access denied"}
    }
)
async def get_texture_by_segmentation(
    segmentation_result_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene descriptores de textura ya calculados para una segmentación.

    Verifica ownership antes de retornar. El frontend usa este endpoint
    para detectar si ya existen descriptores calculados.

    Args:
        segmentation_result_id: ID del resultado de segmentación
        db: Sesión de base de datos
        current_user: Usuario autenticado (JWT)

    Returns:
        Lista de 3 TextureDescriptorResponse (edges, homogeneity, contrast)

    Raises:
        HTTPException 404: Si no existen descriptores calculados
        HTTPException 403: Si no tiene acceso
    """
    service = TextureService()
    descriptors = await service.get_descriptors_by_segmentation(
        segmentation_result_id=segmentation_result_id,
        user_id=current_user.id,
        db=db
    )

    return descriptors
