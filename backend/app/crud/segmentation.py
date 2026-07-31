"""
OE3 - Operaciones CRUD para resultados de segmentación.
Solo operaciones de base de datos, sin lógica de negocio.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
import logging

from app.models.segmentation import SegmentationResult

logger = logging.getLogger(__name__)


async def create(
    db: AsyncSession,
    ndvi_result_id: int,
    polygon_id: int,
    threshold_used: float,
    total_pixels: int,
    cultivated_pixels: int,
    cultivated_percentage: float,
    binary_mask: Optional[bytes] = None
) -> SegmentationResult:
    """
    Guarda un nuevo resultado de segmentación en la base de datos.

    Args:
        db: Sesión async de base de datos
        ndvi_result_id: ID del resultado NDVI
        polygon_id: ID del polígono analizado
        threshold_used: Umbral NDVI usado para clasificación
        total_pixels: Total de píxeles válidos
        cultivated_pixels: Píxeles clasificados como cultivados
        cultivated_percentage: Porcentaje de área cultivada (0-100)
        binary_mask: Máscara binaria en formato TIFF uint8 (opcional)

    Returns:
        SegmentationResult: Registro creado con ID asignado

    Raises:
        IntegrityError: Si ya existe una segmentación para este ndvi_result_id (UNIQUE constraint)
    """
    try:
        db_segmentation = SegmentationResult(
            ndvi_result_id=ndvi_result_id,
            polygon_id=polygon_id,
            threshold_used=threshold_used,
            total_pixels=total_pixels,
            cultivated_pixels=cultivated_pixels,
            cultivated_percentage=cultivated_percentage,
            binary_mask=binary_mask,
            calculation_date=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        db.add(db_segmentation)
        await db.commit()
        await db.refresh(db_segmentation)
        return db_segmentation
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error saving segmentation result: {str(e)}")
        logger.error(f"   ndvi_result_id={ndvi_result_id}, polygon_id={polygon_id}")
        raise


async def get_by_id(
    db: AsyncSession,
    segmentation_id: int
) -> Optional[SegmentationResult]:
    """
    Obtiene un resultado de segmentación por su ID.

    Args:
        db: Sesión async de base de datos
        segmentation_id: ID del resultado de segmentación

    Returns:
        SegmentationResult si existe, None si no se encontró
    """
    try:
        query = select(SegmentationResult).where(SegmentationResult.id == segmentation_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"❌ Error getting segmentation by ID: {str(e)}")
        raise


async def get_by_ndvi_result_id(
    db: AsyncSession,
    ndvi_result_id: int
) -> Optional[SegmentationResult]:
    """
    Obtiene el resultado de segmentación asociado a un resultado NDVI.

    Función de idempotencia: permite verificar si ya existe segmentación
    antes de recalcular (evita duplicados).

    Args:
        db: Sesión async de base de datos
        ndvi_result_id: ID del resultado NDVI

    Returns:
        SegmentationResult si existe, None si no se encontró
    """
    try:
        query = select(SegmentationResult).where(SegmentationResult.ndvi_result_id == ndvi_result_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"❌ Error getting segmentation by NDVI result: {str(e)}")
        raise


async def get_by_polygon_id(
    db: AsyncSession,
    polygon_id: int,
    limit: int = 100
) -> List[SegmentationResult]:
    """
    Lista todos los resultados de segmentación de un polígono.

    Útil para el frontend dashboard: obtener histórico de segmentaciones.

    Args:
        db: Sesión async de base de datos
        polygon_id: ID del polígono
        limit: Número máximo de resultados (default 100)

    Returns:
        Lista de SegmentationResult ordenados por fecha de cálculo (desc)
    """
    try:
        query = (
            select(SegmentationResult)
            .where(SegmentationResult.polygon_id == polygon_id)
            .order_by(SegmentationResult.calculation_date.desc())
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()
    except Exception as e:
        logger.error(f"❌ Error getting segmentations by polygon: {str(e)}")
        raise
