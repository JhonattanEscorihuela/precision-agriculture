"""
OE3 - Endpoint de comparación fenológica para clasificación de cultivos.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.user import User
from app.core.security import get_current_user
from app.schemas.phenology import (
    PhenologyComparisonResponse,
    PhenologyErrorResponse
)
from app.services.phenology_service import PhenologyService


router = APIRouter()


@router.get(
    "/compare/{polygon_id}",
    response_model=PhenologyComparisonResponse,
    responses={
        400: {"model": PhenologyErrorResponse, "description": "Invalid request"},
        403: {"model": PhenologyErrorResponse, "description": "Access denied"},
        404: {"model": PhenologyErrorResponse, "description": "Polygon not found"}
    }
)
async def compare_phenology(
    polygon_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Compara la curva NDVI de una parcela contra la referencia de arroz.

    Utiliza correlación de Pearson para determinar si la parcela
    tiene un comportamiento fenológico similar al arroz. Las parcelas
    de referencia (IDs 1, 2, 3) corresponden a arroz confirmado.

    **Clasificación:**
    - r ≥ 0.85: Alta similitud — probablemente arroz
    - 0.70 ≤ r < 0.85: Similitud moderada — requiere revisión
    - r < 0.70: Baja similitud — probablemente NO es arroz

    Args:
        polygon_id: ID de la parcela a clasificar

    Returns:
        Comparación con similarity_score y curve_data para gráficos
    """
    service = PhenologyService()
    return await service.compare_parcel(
        polygon_id=polygon_id,
        user_id=current_user.id,
        db=db
    )
