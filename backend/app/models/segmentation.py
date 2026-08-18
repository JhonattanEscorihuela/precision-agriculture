"""
OE3 - Modelo de resultados de segmentación espacial.
Almacena máscara binaria de zonas cultivadas a partir de NDVI.
"""

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer, ForeignKey, DateTime, LargeBinary
from typing import Optional
from datetime import datetime


class SegmentationResultBase(SQLModel):
    """Campos base para resultado de segmentación"""
    ndvi_result_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("ndvi_results.id", ondelete="CASCADE"),
            unique=True
        ),
        description="ID del resultado NDVI (UNIQUE: 1 segmentación por NDVI)"
    )
    polygon_id: int = Field(
        sa_column=Column(Integer, ForeignKey("polygon.id", ondelete="CASCADE")),
        description="ID del polígono analizado"
    )

    # Parámetros de segmentación
    threshold_used: float = Field(
        description="Umbral NDVI usado para clasificación (e.g., 0.3)"
    )

    # Métricas de segmentación
    total_pixels: int = Field(
        description="Total de píxeles válidos en el raster NDVI"
    )
    cultivated_pixels: int = Field(
        description="Píxeles clasificados como cultivados (NDVI > threshold)"
    )
    cultivated_percentage: float = Field(
        description="Porcentaje de área cultivada (0-100)"
    )


class SegmentationResult(SegmentationResultBase, table=True):
    """
    Tabla de resultados de segmentación espacial.

    Almacena máscara binaria de zonas cultivadas generada a partir del
    raster NDVI mediante umbralización. La máscara queda disponible para
    análisis de textura en OE4.

    Constraint UNIQUE en ndvi_result_id garantiza una sola segmentación por NDVI.
    """
    __tablename__ = "segmentation_results"

    ndvi_result_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("ndvi_results.id", ondelete="CASCADE"),
            unique=True,
        )
    )
    polygon_id: int = Field(
        sa_column=Column(Integer, ForeignKey("polygon.id", ondelete="CASCADE"))
    )
    id: Optional[int] = Field(default=None, primary_key=True)

    # Máscara binaria (0=no cultivado, 1=cultivado) en formato TIFF uint8
    binary_mask: Optional[bytes] = Field(
        sa_column=Column(LargeBinary, nullable=True),
        default=None,
        description="Máscara binaria en formato TIFF uint8 con compresión LZW. Nullable para permitir cálculos sin guardar máscara."
    )

    # Timestamps
    calculation_date: datetime = Field(
        sa_column=Column(DateTime),
        default_factory=datetime.utcnow,
        description="Fecha y hora del cálculo de segmentación"
    )
    created_at: Optional[datetime] = Field(
        sa_column=Column(DateTime),
        default_factory=datetime.utcnow,
        description="Timestamp de creación del registro"
    )

    class Config:
        """Configuración del modelo"""
        json_schema_extra = {
            "example": {
                "ndvi_result_id": 1,
                "polygon_id": 1,
                "threshold_used": 0.3,
                "total_pixels": 262144,
                "cultivated_pixels": 198432,
                "cultivated_percentage": 75.68,
                "calculation_date": "2026-07-31T10:30:00Z",
                "created_at": "2026-07-31T10:30:00Z"
            }
        }


class SegmentationResultCreate(SegmentationResultBase):
    """Schema para crear un nuevo resultado de segmentación"""
    binary_mask: Optional[bytes] = None
    calculation_date: datetime
    created_at: datetime


class SegmentationResultPublic(SegmentationResultBase):
    """
    Schema público para respuestas de API (sin datos binarios).
    Usado en endpoints para no transferir la máscara completa.
    """
    id: int
    calculation_date: datetime
    created_at: datetime
    mask_size_kb: Optional[float] = Field(
        default=None,
        description="Tamaño de la máscara en KB (null si no guardada)"
    )
