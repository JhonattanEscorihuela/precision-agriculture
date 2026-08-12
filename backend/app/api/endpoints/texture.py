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


@router.get(
    "/overlay/{ndvi_result_id}",
    responses={
        200: {
            "description": "PNG coloreado de textura con bounds para visualización en mapa",
            "content": {
                "application/json": {
                    "example": {
                        "image_base64": "data:image/png;base64,iVBORw0KG...",
                        "bounds": [[8.838, -67.528], [8.853, -67.515]],
                        "kernel": "contrast",
                        "cached": True,
                        "interpretation": "Campo heterogéneo — se detectan...",
                        "metadata": {
                            "date": "2026-03-22",
                            "polygon_id": 10,
                            "thresholds_percentiles": [33, 66]
                        }
                    }
                }
            }
        },
        404: {"model": TextureErrorResponse, "description": "NDVI result not found"},
        403: {"model": TextureErrorResponse, "description": "Access denied"},
        400: {"model": TextureErrorResponse, "description": "Invalid kernel name"}
    }
)
async def get_texture_overlay(
    ndvi_result_id: int,
    kernel: str = "contrast",
    force: bool = False,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Genera overlay coloreado de textura para visualización en mapa Leaflet.

    **Workflow:**
    1. Busca NDVIResult por ndvi_result_id
    2. Verifica ownership del polígono
    3. Si existe cache (texture_overlay_cache) y no force → retorna desde caché
    4. Si no existe cache o force=true:
       - Aplica kernel de textura al TIFF NDVI
       - Genera PNG coloreado RGBA con paleta percentil
       - Genera interpretación textual según kernel y valores
       - Guarda en cache (tabla texture_overlay_cache)
    5. Retorna base64 + bounds + metadata + interpretation

    **Cache policy:**
    - Primera llamada: calcula y guarda (cached=false)
    - Siguientes llamadas: sirve desde cache (cached=true)
    - Query param ?force=true: recalcula y actualiza cache

    **Kernels disponibles:**
    - **contrast**: Magnitud del gradiente (Sobel) — detecta variabilidad local
    - **edges**: Laplaciano — detecta bordes internos y transiciones
    - **homogeneity**: Diferencia con media local — cuantifica uniformidad

    **Paleta de colores (variabilidad frío/cálido):**
    - Azul (#3b82f6): Percentil 0-33 (Uniforme)
    - Púrpura (#8b5cf6): Percentil 33-66 (Moderado)
    - Naranja (#f97316): Percentil 66-100 (Heterogéneo)

    Args:
        ndvi_result_id: ID del resultado NDVI
        kernel: Nombre del kernel (contrast/edges/homogeneity)
        force: Forzar recálculo aunque exista caché (default: False)
        db: Sesión de base de datos
        current_user: Usuario autenticado (JWT)

    Returns:
        JSON con image_base64, bounds, kernel, cached, interpretation y metadata

    Raises:
        HTTPException 404: Si no existe NDVI result
        HTTPException 403: Si no tiene acceso
        HTTPException 400: Si kernel inválido
        HTTPException 500: Si hay error generando overlay
    """
    import base64
    from app.services.texture_overlay_service import generate_texture_overlay
    from app.crud import texture_overlay as crud_overlay
    from app.crud import ndvi as crud_ndvi
    from app.crud import polygon as crud_polygon
    from app.models.acquisition import SentinelAcquisition
    from sqlalchemy import select

    # Validar kernel
    valid_kernels = ["contrast", "edges", "homogeneity"]
    if kernel not in valid_kernels:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid kernel '{kernel}'. Must be one of: {', '.join(valid_kernels)}"
        )

    try:
        # 1. Buscar NDVIResult
        ndvi_result = await crud_ndvi.get_ndvi_by_id(db, ndvi_result_id)
        if not ndvi_result:
            raise HTTPException(
                status_code=404,
                detail=f"NDVI result not found with id={ndvi_result_id}"
            )

        # 2. Verificar ownership del polígono
        polygon = await crud_polygon.get_polygon_by_id(db, ndvi_result.polygon_id)
        if not polygon or polygon.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You don't have access to this NDVI result"
            )

        # 3. Obtener fecha de adquisición
        query = select(SentinelAcquisition.acquisition_date).where(
            SentinelAcquisition.id == ndvi_result.acquisition_id
        )
        result = await db.execute(query)
        acquisition_date = result.scalar_one_or_none()

        # 4. Preparar geometría del polígono para máscara
        polygon_geojson = {
            "type": "Polygon",
            "coordinates": [polygon.coordinates]  # polygon.coordinates ya es [[lng, lat], ...]
        }

        # 5. Cache check
        cached_overlay = await crud_overlay.get_cached_overlay(db, ndvi_result_id, kernel)

        if cached_overlay and not force:
            # Servir desde caché
            png_bytes = cached_overlay.overlay_png
            interpretation = cached_overlay.interpretation
            # Re-generar bounds desde el TIFF
            _, leaflet_bounds, _ = generate_texture_overlay(ndvi_result.ndvi_tiff, kernel, polygon_geojson)
            cached = True
        else:
            # 6. Generar overlay con máscara de polígono
            png_bytes, leaflet_bounds, interpretation = generate_texture_overlay(
                ndvi_result.ndvi_tiff, kernel, polygon_geojson
            )

            # 7. Guardar en cache (crea o actualiza)
            await crud_overlay.save_overlay_cache(
                db, ndvi_result_id, kernel, png_bytes, interpretation
            )
            cached = False

        # 7. Codificar a base64
        image_b64 = f"data:image/png;base64,{base64.b64encode(png_bytes).decode()}"

        # 8. Respuesta
        return {
            "image_base64": image_b64,
            "bounds": leaflet_bounds,
            "kernel": kernel,
            "cached": cached,
            "interpretation": interpretation,
            "metadata": {
                "date": str(acquisition_date) if acquisition_date else None,
                "polygon_id": ndvi_result.polygon_id,
                "thresholds_percentiles": [33, 66]
            }
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error generating texture overlay: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating texture overlay: {str(e)}"
        )
