"""
OE1 - Operaciones CRUD para adquisiciones Sentinel-2.
Solo operaciones de base de datos, sin lógica de negocio.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Optional
from datetime import datetime
import logging

from app.models.acquisition import SentinelAcquisition, SentinelAcquisitionCreate

logger = logging.getLogger(__name__)


async def create_acquisition(
    db: AsyncSession,
    acquisition_data: SentinelAcquisitionCreate
) -> SentinelAcquisition:
    """
    Crea un nuevo registro de adquisición en la base de datos.

    Args:
        db: Sesión async de base de datos
        acquisition_data: Datos de la adquisición a crear

    Returns:
        SentinelAcquisition: Registro creado con ID asignado
    """
    try:
        db_acquisition = SentinelAcquisition(**acquisition_data.dict())
        db.add(db_acquisition)
        await db.commit()
        await db.refresh(db_acquisition)
        return db_acquisition
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error creating acquisition: {str(e)}")
        logging.error(f"   Data: {acquisition_data.dict()}")
        raise


async def get_acquisition_by_id(
    db: AsyncSession,
    acquisition_id: int
) -> Optional[SentinelAcquisition]:
    """
    Obtiene una adquisición por su ID.

    Args:
        db: Sesión async de base de datos
        acquisition_id: ID de la adquisición

    Returns:
        SentinelAcquisition o None si no existe
    """
    statement = select(SentinelAcquisition).where(SentinelAcquisition.id == acquisition_id)
    result = await db.execute(statement)
    return result.scalar_one_or_none()


async def get_acquisitions_by_polygon(
    db: AsyncSession,
    polygon_id: int,
    limit: int = 100
) -> List[SentinelAcquisition]:
    """
    Obtiene todas las adquisiciones de un polígono específico.

    Args:
        db: Sesión async de base de datos
        polygon_id: ID del polígono
        limit: Máximo número de resultados (default: 100)

    Returns:
        Lista de adquisiciones ordenadas por fecha descendente
    """
    statement = (
        select(SentinelAcquisition)
        .where(SentinelAcquisition.polygon_id == polygon_id)
        .order_by(SentinelAcquisition.acquisition_date.desc())
        .limit(limit)
    )
    result = await db.execute(statement)
    return list(result.scalars().all())


async def get_acquisition_by_polygon_and_date(
    db: AsyncSession,
    polygon_id: int,
    acquisition_date: str
) -> Optional[SentinelAcquisition]:
    """
    Obtiene una adquisición específica por polígono y fecha.
    Útil para evitar duplicados antes de crear.

    Args:
        db: Sesión async de base de datos
        polygon_id: ID del polígono
        acquisition_date: Fecha en formato YYYY-MM-DD

    Returns:
        SentinelAcquisition o None si no existe
    """
    statement = select(SentinelAcquisition).where(
        SentinelAcquisition.polygon_id == polygon_id,
        SentinelAcquisition.acquisition_date == acquisition_date
    )
    result = await db.execute(statement)
    return result.scalar_one_or_none()


async def delete_acquisition(
    db: AsyncSession,
    acquisition_id: int
) -> bool:
    """
    Elimina una adquisición por su ID.

    Args:
        db: Sesión async de base de datos
        acquisition_id: ID de la adquisición a eliminar

    Returns:
        bool: True si se eliminó, False si no existía
    """
    statement = delete(SentinelAcquisition).where(SentinelAcquisition.id == acquisition_id)
    result = await db.execute(statement)
    await db.commit()
    return result.rowcount > 0


async def get_all_acquisitions(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100
) -> List[SentinelAcquisition]:
    """
    Obtiene todas las adquisiciones (con paginación).

    Args:
        db: Sesión async de base de datos
        skip: Número de registros a saltar
        limit: Máximo número de resultados

    Returns:
        Lista de adquisiciones ordenadas por fecha descendente
    """
    statement = (
        select(SentinelAcquisition)
        .order_by(SentinelAcquisition.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(statement)
    return list(result.scalars().all())
