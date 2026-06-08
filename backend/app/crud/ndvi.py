"""
OE2 - Operaciones CRUD para resultados NDVI.
Solo operaciones de base de datos, sin lógica de negocio.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Optional
from datetime import datetime

from app.models.analysis import NDVIResult, NDVIResultCreate


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
        import logging
        logging.error(f"❌ Error saving NDVI result: {str(e)}")
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
        import logging
        logging.error(f"❌ Error getting NDVI by acquisition: {str(e)}")
        raise


async def get_ndvi_by_polygon(
    db: AsyncSession,
    polygon_id: int,
    limit: int = 10
) -> List[NDVIResult]:
    """
    Lista todos los resultados NDVI de un polígono.

    Útil para el frontend: mostrar histórico de análisis NDVI de una parcela.

    Args:
        db: Sesión async de base de datos
        polygon_id: ID del polígono
        limit: Número máximo de resultados (default 10)

    Returns:
        Lista de NDVIResult ordenados por fecha de cálculo (más reciente primero)
    """
    try:
        query = (
            select(NDVIResult)
            .where(NDVIResult.polygon_id == polygon_id)
            .order_by(NDVIResult.calculation_date.desc())
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()
    except Exception as e:
        import logging
        logging.error(f"❌ Error getting NDVI by polygon: {str(e)}")
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
        import logging
        logging.error(f"❌ Error deleting NDVI result: {str(e)}")
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
        import logging
        logging.error(f"❌ Error getting NDVI by ID: {str(e)}")
        raise
