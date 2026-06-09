"""
OE2 - Operaciones CRUD para resultados NDVI.
Solo operaciones de base de datos, sin lógica de negocio.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Optional
from datetime import datetime
import logging

from app.models.analysis import NDVIResult, NDVIResultCreate

logger = logging.getLogger(__name__)


async def save_ndvi_result(
    db: AsyncSession,
    acquisition_id: int,
    polygon_id: int,
    ndvi_tiff: bytes,
    stats: dict,
    width: int,
    height: int
) -> NDVIResult:
    """
    Guarda un nuevo resultado NDVI en la base de datos.

    Args:
        db: Sesión async de base de datos
        acquisition_id: ID de la adquisición Sentinel-2
        polygon_id: ID del polígono analizado
        ndvi_tiff: Raster NDVI en formato TIFF float32 (bytes)
        stats: Diccionario con estadísticos {ndvi_mean, ndvi_min, ndvi_max, ndvi_std}
        width: Ancho del raster en píxeles
        height: Alto del raster en píxeles

    Returns:
        NDVIResult: Registro creado con ID asignado

    Raises:
        IntegrityError: Si ya existe un NDVI para este acquisition_id (UNIQUE constraint)
    """
    try:
        db_ndvi = NDVIResult(
            acquisition_id=acquisition_id,
            polygon_id=polygon_id,
            ndvi_tiff=ndvi_tiff,
            ndvi_mean=stats["ndvi_mean"],
            ndvi_min=stats["ndvi_min"],
            ndvi_max=stats["ndvi_max"],
            ndvi_std=stats["ndvi_std"],
            width=width,
            height=height,
            calculation_date=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        db.add(db_ndvi)
        await db.commit()
        await db.refresh(db_ndvi)
        return db_ndvi
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error saving NDVI result: {str(e)}")
        logging.error(f"   acquisition_id={acquisition_id}, polygon_id={polygon_id}")
        raise


async def get_ndvi_by_acquisition(
    db: AsyncSession,
    acquisition_id: int
) -> Optional[NDVIResult]:
    """
    Obtiene el resultado NDVI asociado a una adquisición.

    Args:
        db: Sesión async de base de datos
        acquisition_id: ID de la adquisición Sentinel-2

    Returns:
        NDVIResult si existe, None si no se encontró
    """
    try:
        query = select(NDVIResult).where(NDVIResult.acquisition_id == acquisition_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"❌ Error getting NDVI by acquisition: {str(e)}")
        raise


async def get_ndvi_by_polygon(
    db: AsyncSession,
    polygon_id: int,
    start_date: str = None,
    end_date: str = None,
    limit: int = 100
) -> List[tuple]:
    """
    Lista todos los resultados NDVI de un polígono con JOIN a SentinelAcquisition,
    opcionalmente filtrados por rango de fechas.

    Útil para el frontend dashboard: obtener histórico de análisis NDVI
    en período específico según filtro CloudWatch.

    Args:
        db: Sesión async de base de datos
        polygon_id: ID del polígono
        start_date: Fecha inicio filtro (YYYY-MM-DD) - opcional
        end_date: Fecha fin filtro (YYYY-MM-DD) - opcional
        limit: Número máximo de resultados (default 100, suficiente para 2 años)

    Returns:
        Lista de tuplas (NDVIResult, acquisition_date) ordenados por fecha de adquisición (cronológico)
    """
    from app.models.acquisition import SentinelAcquisition

    try:
        query = (
            select(NDVIResult, SentinelAcquisition.acquisition_date)
            .join(SentinelAcquisition, NDVIResult.acquisition_id == SentinelAcquisition.id)
            .where(NDVIResult.polygon_id == polygon_id)
        )

        # Aplicar filtros de fecha si se proporcionan
        if start_date:
            query = query.where(SentinelAcquisition.acquisition_date >= start_date)
        if end_date:
            query = query.where(SentinelAcquisition.acquisition_date <= end_date)

        query = query.order_by(SentinelAcquisition.acquisition_date.desc()).limit(limit)

        result = await db.execute(query)
        return result.all()
    except Exception as e:
        logger.error(f"❌ Error getting NDVI by polygon: {str(e)}")
        raise


async def delete_ndvi_result(
    db: AsyncSession,
    ndvi_id: int
) -> bool:
    """
    Elimina un resultado NDVI de la base de datos.

    Args:
        db: Sesión async de base de datos
        ndvi_id: ID del resultado NDVI a eliminar

    Returns:
        True si se eliminó correctamente, False si no se encontró
    """
    try:
        query = delete(NDVIResult).where(NDVIResult.id == ndvi_id)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error deleting NDVI result: {str(e)}")
        raise


async def get_ndvi_by_id(
    db: AsyncSession,
    ndvi_id: int
) -> Optional[NDVIResult]:
    """
    Obtiene un resultado NDVI por su ID.

    Args:
        db: Sesión async de base de datos
        ndvi_id: ID del resultado NDVI

    Returns:
        NDVIResult si existe, None si no se encontró
    """
    try:
        query = select(NDVIResult).where(NDVIResult.id == ndvi_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"❌ Error getting NDVI by ID: {str(e)}")
        raise
