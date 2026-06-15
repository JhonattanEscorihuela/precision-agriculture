"""
OE1 - Modelo de adquisiciones de imágenes Sentinel-2.
Almacena bandas B04 y B08 descargadas para análisis posterior.
"""

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer, ForeignKey, Index
from typing import Optional


class SentinelAcquisitionBase(SQLModel):
    """Campos base para adquisición de Sentinel-2"""
    polygon_id: int = Field(sa_column=Column(Integer, ForeignKey("polygon.id", ondelete="CASCADE")))
    acquisition_date: str = Field(description="Fecha de la escena (YYYY-MM-DD)")
    cloud_coverage: float = Field(description="Porcentaje de cobertura de nubes (0-100)")
    width: int = Field(description="Ancho de la imagen en píxeles")
    height: int = Field(description="Alto de la imagen en píxeles")


class SentinelAcquisition(SentinelAcquisitionBase, table=True):
    """
    Tabla de adquisiciones de bandas Sentinel-2.

    Almacena las bandas espectrales B04 (Red) y B08 (NIR) en formato TIFF
    para posterior cálculo de índices espectrales (NDVI en OE2).
    """
    __tablename__ = "sentinel_acquisitions"

    id: Optional[int] = Field(default=None, primary_key=True)
    b04_data: bytes = Field(description="Banda roja (Red) en formato TIFF")
    b08_data: bytes = Field(description="Banda infrarrojo cercano (NIR) en formato TIFF")
    created_at: str = Field(description="Timestamp de creación (ISO 8601)")

    # Índices para optimizar queries frecuentes
    __table_args__ = (
        Index('idx_polygon_date', 'polygon_id', 'acquisition_date'),
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
                "width": 512,
                "height": 512,
                "created_at": "2024-06-16T10:30:00Z"
            }
        }


class SentinelAcquisitionCreate(SentinelAcquisitionBase):
    """Schema para crear una nueva adquisición"""
    b04_data: bytes
    b08_data: bytes
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
