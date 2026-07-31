"""
OE4 - Modelo de descriptores de textura.
Almacena métricas de textura calculadas por filtros convolucionales sobre zonas cultivadas.
"""

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, UniqueConstraint
from typing import Optional
from datetime import datetime


class TextureDescriptorBase(SQLModel):
    """Campos base para descriptor de textura"""
    segmentation_result_id: int = Field(
        sa_column=Column(Integer, ForeignKey("segmentation_results.id", ondelete="CASCADE")),
        description="ID del resultado de segmentación"
    )
    polygon_id: int = Field(
        sa_column=Column(Integer, ForeignKey("polygon.id", ondelete="CASCADE")),
        description="ID del polígono analizado"
    )

    # Tipo de kernel convolucional aplicado
    kernel_type: str = Field(
        sa_column=Column(String(50)),
        description="Tipo de kernel: 'edges', 'homogeneity', 'contrast'"
    )

    # Estadísticos del descriptor
    mean: float = Field(description="Promedio de la respuesta del filtro")
    std: float = Field(description="Desviación estándar de la respuesta")
    min_val: float = Field(description="Valor mínimo de la respuesta")
    max_val: float = Field(description="Valor máximo de la respuesta")

    # Métrica de calidad
    discriminative: bool = Field(
        description="True si std > threshold (descriptor discriminativo). Indica que la textura tiene variabilidad útil."
    )


class TextureDescriptor(TextureDescriptorBase, table=True):
    """
    Tabla de descriptores de textura.

    Almacena métricas de textura calculadas mediante filtros convolucionales
    (Sobel, GLCM, etc.) sobre las zonas cultivadas identificadas en OE3.

    Constraint UNIQUE en (segmentation_result_id, kernel_type) permite múltiples
    descriptores por segmentación (uno por cada kernel).
    """
    __tablename__ = "texture_descriptors"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Timestamps
    calculation_date: datetime = Field(
        sa_column=Column(DateTime),
        default_factory=datetime.utcnow,
        description="Fecha y hora del cálculo del descriptor"
    )
    created_at: Optional[datetime] = Field(
        sa_column=Column(DateTime),
        default_factory=datetime.utcnow,
        description="Timestamp de creación del registro"
    )

    # Constraint UNIQUE compuesto
    __table_args__ = (
        UniqueConstraint(
            'segmentation_result_id',
            'kernel_type',
            name='uq_segmentation_kernel'
        ),
    )

    class Config:
        """Configuración del modelo"""
        json_schema_extra = {
            "example": {
                "segmentation_result_id": 1,
                "polygon_id": 1,
                "kernel_type": "edges",
                "mean": 12.45,
                "std": 8.32,
                "min_val": 0.12,
                "max_val": 45.67,
                "discriminative": True,
                "calculation_date": "2026-07-31T10:30:00Z",
                "created_at": "2026-07-31T10:30:00Z"
            }
        }


class TextureDescriptorCreate(TextureDescriptorBase):
    """Schema para crear un nuevo descriptor de textura"""
    calculation_date: datetime
    created_at: datetime


class TextureDescriptorPublic(TextureDescriptorBase):
    """
    Schema público para respuestas de API.
    Incluye todos los campos (no hay binarios en este modelo).
    """
    id: int
    calculation_date: datetime
    created_at: datetime
