"""
OE4 - Operaciones CRUD para caché de overlays de textura.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import logging

from app.models.analysis import TextureOverlayCache

logger = logging.getLogger(__name__)


async def get_cached_overlay(
    db: AsyncSession,
    ndvi_result_id: int,
    kernel: str
) -> Optional[TextureOverlayCache]:
    """
    Obtiene un overlay cacheado por ndvi_result_id y kernel.

    Args:
        db: Sesión async de base de datos
        ndvi_result_id: ID del resultado NDVI
        kernel: Nombre del kernel (contrast/edges/homogeneity)

    Returns:
        TextureOverlayCache si existe, None si no se encontró
    """
    try:
        query = select(TextureOverlayCache).where(
            TextureOverlayCache.ndvi_result_id == ndvi_result_id,
            TextureOverlayCache.kernel == kernel
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"❌ Error getting cached overlay: {str(e)}")
        raise


async def save_overlay_cache(
    db: AsyncSession,
    ndvi_result_id: int,
    kernel: str,
    overlay_png: bytes,
    interpretation: str
) -> TextureOverlayCache:
    """
    Guarda o actualiza un overlay en caché.

    Args:
        db: Sesión async de base de datos
        ndvi_result_id: ID del resultado NDVI
        kernel: Nombre del kernel
        overlay_png: PNG en bytes
        interpretation: Texto interpretativo

    Returns:
        TextureOverlayCache: Registro creado/actualizado
    """
    try:
        # Verificar si ya existe
        existing = await get_cached_overlay(db, ndvi_result_id, kernel)

        if existing:
            # Actualizar
            existing.overlay_png = overlay_png
            existing.interpretation = interpretation
            await db.commit()
            await db.refresh(existing)
            return existing
        else:
            # Crear nuevo
            new_cache = TextureOverlayCache(
                ndvi_result_id=ndvi_result_id,
                kernel=kernel,
                overlay_png=overlay_png,
                interpretation=interpretation
            )
            db.add(new_cache)
            await db.commit()
            await db.refresh(new_cache)
            return new_cache
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error saving overlay cache: {str(e)}")
        raise
