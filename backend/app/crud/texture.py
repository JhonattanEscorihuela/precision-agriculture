"""
OE4 - Operaciones CRUD para descriptores de textura.
Solo operaciones de base de datos, sin lógica de negocio.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
import logging

from app.models.texture import TextureDescriptor

logger = logging.getLogger(__name__)


async def create(
    db: AsyncSession,
    segmentation_result_id: int,
    polygon_id: int,
    kernel_type: str,
    mean: float,
    std: float,
    min_val: float,
    max_val: float,
    std_normalized: float,
    discriminative: bool,
    auto_commit: bool = False
) -> TextureDescriptor:
    """
    Guarda un nuevo descriptor de textura en la base de datos.

    Args:
        db: Sesión async de base de datos
        segmentation_result_id: ID del resultado de segmentación
        polygon_id: ID del polígono analizado
        kernel_type: Tipo de kernel ("edges", "homogeneity", "contrast")
        mean: Promedio de la respuesta del filtro
        std: Desviación estándar de la respuesta
        min_val: Valor mínimo de la respuesta
        max_val: Valor máximo de la respuesta
        std_normalized: Desviación estándar sobre respuestas normalizadas [0,1]
        discriminative: True si el descriptor es discriminativo
        auto_commit: Si True, hace commit inmediatamente. Si False (default),
                     el servicio debe hacer commit manualmente (para atomicidad multi-descriptor)

    Returns:
        TextureDescriptor: Registro creado con ID asignado (si auto_commit=True)
                          o pendiente de commit (si auto_commit=False)

    Raises:
        IntegrityError: Si ya existe descriptor para (segmentation_result_id, kernel_type) (UNIQUE constraint)
    """
    try:
        db_descriptor = TextureDescriptor(
            segmentation_result_id=segmentation_result_id,
            polygon_id=polygon_id,
            kernel_type=kernel_type,
            mean=mean,
            std=std,
            min_val=min_val,
            max_val=max_val,
            std_normalized=std_normalized,
            discriminative=discriminative,
            calculation_date=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        db.add(db_descriptor)

        if auto_commit:
            await db.commit()
            await db.refresh(db_descriptor)

        return db_descriptor
    except Exception as e:
        if auto_commit:
            await db.rollback()
        logger.error(f"❌ Error saving texture descriptor: {str(e)}")
        logger.error(f"   segmentation_result_id={segmentation_result_id}, kernel_type={kernel_type}")
        raise


async def get_by_segmentation_result_id(
    db: AsyncSession,
    segmentation_result_id: int
) -> List[TextureDescriptor]:
    """
    Obtiene todos los descriptores de textura de una segmentación.

    Args:
        db: Sesión async de base de datos
        segmentation_result_id: ID del resultado de segmentación

    Returns:
        Lista de TextureDescriptor ordenados por kernel_type
    """
    try:
        query = (
            select(TextureDescriptor)
            .where(TextureDescriptor.segmentation_result_id == segmentation_result_id)
            .order_by(TextureDescriptor.kernel_type)
        )
        result = await db.execute(query)
        return result.scalars().all()
    except Exception as e:
        logger.error(f"❌ Error getting texture descriptors by segmentation: {str(e)}")
        raise


async def get_by_segmentation_and_kernel(
    db: AsyncSession,
    segmentation_result_id: int,
    kernel_type: str
) -> Optional[TextureDescriptor]:
    """
    Obtiene un descriptor específico por segmentación y tipo de kernel.

    Función de idempotencia: permite verificar si ya existe descriptor
    antes de recalcular (evita duplicados).

    Args:
        db: Sesión async de base de datos
        segmentation_result_id: ID del resultado de segmentación
        kernel_type: Tipo de kernel ("edges", "homogeneity", "contrast")

    Returns:
        TextureDescriptor si existe, None si no se encontró
    """
    try:
        query = select(TextureDescriptor).where(
            TextureDescriptor.segmentation_result_id == segmentation_result_id,
            TextureDescriptor.kernel_type == kernel_type
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"❌ Error getting texture descriptor by segmentation and kernel: {str(e)}")
        raise


async def get_by_polygon_id(
    db: AsyncSession,
    polygon_id: int,
    kernel_type: Optional[str] = None,
    limit: int = 100
) -> List[TextureDescriptor]:
    """
    Lista todos los descriptores de textura de un polígono.

    Útil para el frontend dashboard: obtener histórico de descriptores,
    opcionalmente filtrados por tipo de kernel.

    Args:
        db: Sesión async de base de datos
        polygon_id: ID del polígono
        kernel_type: Filtrar por tipo de kernel (opcional)
        limit: Número máximo de resultados (default 100)

    Returns:
        Lista de TextureDescriptor ordenados por fecha de cálculo (desc)
    """
    try:
        query = (
            select(TextureDescriptor)
            .where(TextureDescriptor.polygon_id == polygon_id)
        )

        # Aplicar filtro de kernel_type si se proporciona
        if kernel_type:
            query = query.where(TextureDescriptor.kernel_type == kernel_type)

        query = query.order_by(TextureDescriptor.calculation_date.desc()).limit(limit)

        result = await db.execute(query)
        return result.scalars().all()
    except Exception as e:
        logger.error(f"❌ Error getting texture descriptors by polygon: {str(e)}")
        raise
