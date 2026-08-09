"""OE3 - Endpoint de comparación fenológica para clasificación de cultivos."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_session
from app.models.user import User
from app.schemas.phenology import PhenologyComparisonResponse, PhenologyErrorResponse
from app.services.phenology_service import PhenologyService

router = APIRouter()


@router.get(
    "/compare/{polygon_id}",
    response_model=PhenologyComparisonResponse,
    responses={
        400: {"model": PhenologyErrorResponse, "description": "NDVI no disponible o inválido"},
        403: {"model": PhenologyErrorResponse, "description": "Acceso denegado"},
        404: {"model": PhenologyErrorResponse, "description": "Parcela no encontrada"},
    },
)
async def compare_phenology(
    polygon_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Compara la curva NDVI de la parcela con una plantilla teórica de arroz de
    Rio Grande do Sul, Brasil.

    La plantilla se interpola linealmente según los días transcurridos desde la
    primera observación NDVI de la parcela. No usa polígonos ni datos de otros
    usuarios como referencia.

    La respuesta siempre incluye la curva exploratoria cuando existe al menos
    una observación válida. La correlación y la clasificación solo se calculan
    con cinco o más observaciones, al menos 90 días de cobertura, valores
    finitos y variación suficiente en ambas curvas.

    Umbrales cuando la evidencia es suficiente:

    - r >= 0.85: alta similitud, patrón compatible con arroz.
    - 0.70 <= r < 0.85: similitud moderada, resultado no concluyente.
    - r < 0.70: baja similitud, patrón no compatible con arroz.
    """
    service = PhenologyService()
    return await service.compare_parcel(
        polygon_id=polygon_id,
        user_id=current_user.id,
        db=db,
    )
