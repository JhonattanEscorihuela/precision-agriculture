"""
OE1 - Modelo de adquisiciones de imágenes Sentinel-2.
Almacena bandas B04 y B08 descargadas para análisis posterior.
"""

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer, ForeignKey, Index, UniqueConstraint
from typing import Optional


class SentinelAcquisitionBase(SQLModel):
    """Campos base para adquisición de Sentinel-2"""
    polygon_id: int = Field(sa_column=Column(Integer, ForeignKey("polygon.id", ondelete="CASCADE")))
    acquisition_date: str = Field(description="Fecha de la escena (YYYY-MM-DD)")
    cloud_coverage: Optional[float] = Field(
        default=None,
        description="Porcentaje global de nubes de la escena (0-100); null si es desconocido"
    )
    scene_id: Optional[str] = Field(default=None, description="ID del producto Sentinel seleccionado")
    parcel_cloud_cover: Optional[float] = Field(
        default=None,
        description="Porcentaje de píxeles SCL 8/9/10 dentro de la parcela"
    )
    parcel_shadow_cover: Optional[float] = Field(
        default=None,
        description="Porcentaje de sombra de nube SCL 3 dentro de la parcela"
    )
    valid_pixel_percentage: Optional[float] = Field(
        default=None,
        description="Porcentaje de píxeles SCL válidos dentro de la parcela"
    )
    usable_pixel_percentage: Optional[float] = Field(
        default=None,
        description="Porcentaje de píxeles utilizables tras excluir nubes y sombras"
    )
    quality_status: Optional[str] = Field(
        default=None,
        description="Aptitud de la observación: suitable, caution o unsuitable"
    )
    cloud_method: Optional[str] = Field(
        default=None,
        description="Método usado para la nubosidad local, por ejemplo SCL"
    )
    width: int = Field(description="Ancho de la imagen en píxeles")
    height: int = Field(description="Alto de la imagen en píxeles")


class SentinelAcquisition(SentinelAcquisitionBase, table=True):
    """
    Tabla de adquisiciones de bandas Sentinel-2.

    Almacena las bandas espectrales B04 (Red) y B08 (NIR) en formato TIFF
    para posterior cálculo de índices espectrales (NDVI en OE2).
    """
    __tablename__ = "sentinel_acquisitions"

    # SQLModel 0.0.8 no propaga ForeignKey desde la clase base al metadata.
    polygon_id: int = Field(
        sa_column=Column(Integer, ForeignKey("polygon.id", ondelete="CASCADE"))
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    b04_data: bytes = Field(description="Banda roja (Red) en formato TIFF")
    b08_data: bytes = Field(description="Banda infrarrojo cercano (NIR) en formato TIFF")
    scl_data: Optional[bytes] = Field(
        default=None,
        description="SCL y dataMask originales usados para control de calidad y enmascarado"
    )
    created_at: str = Field(description="Timestamp de creación (ISO 8601)")

    # Índices para optimizar queries frecuentes
    __table_args__ = (
        Index('idx_polygon_date', 'polygon_id', 'acquisition_date'),
        UniqueConstraint(
            'polygon_id',
            'acquisition_date',
            name='uq_sentinel_polygon_date',
        ),
        # Índice compuesto para búsquedas por polígono y fecha (get_acquisitions_by_polygon)
        # Mejora performance en queries del dashboard y NDVIPanel
    )

    class Config:
        """Configuración del modelo"""
        json_schema_extra = {
            "example": {
                "polygon_id": 1,
                "acquisition_date": "2024-06-15",
                "cloud_coverage": 12.5,
                "parcel_cloud_cover": 3.25,
                "parcel_shadow_cover": 1.1,
                "valid_pixel_percentage": 99.8,
                "usable_pixel_percentage": 95.45,
                "quality_status": "suitable",
                "cloud_method": "SCL",
                "width": 512,
                "height": 512,
                "created_at": "2024-06-16T10:30:00Z"
            }
        }


class SentinelAcquisitionCreate(SentinelAcquisitionBase):
    """Schema para crear una nueva adquisición"""
    b04_data: bytes
    b08_data: bytes
    scl_data: Optional[bytes] = None
    created_at: str


class SentinelAcquisitionPublic(SentinelAcquisitionBase):
    """
    Schema público para respuestas de API (sin datos binarios).
    Usado en endpoints para no transferir las bandas completas.
    """
    id: int
    created_at: str
    size_b04_kb: float = Field(description="Tamaño de B04 en KB")
    size_b08_kb: float = Field(description="Tamaño de B08 en KB")
