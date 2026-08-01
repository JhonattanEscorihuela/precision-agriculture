"""
OE4 - Schemas Pydantic para endpoints de análisis de textura.
"""

from pydantic import BaseModel, Field
from typing import List


class TextureRequest(BaseModel):
    """Request para calcular descriptores de textura."""
    segmentation_result_id: int = Field(
        ...,
        description="ID del resultado de segmentación"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "segmentation_result_id": 1
            }
        }


class TextureDescriptorResponse(BaseModel):
    """Response con un descriptor de textura."""
    id: int
    segmentation_result_id: int = Field(
        ...,
        description="ID del resultado de segmentación"
    )
    polygon_id: int
    kernel_type: str = Field(
        ...,
        description="Tipo de kernel: 'edges', 'homogeneity', 'contrast'"
    )
    mean: float = Field(
        ...,
        description="Promedio de la respuesta del filtro"
    )
    std: float = Field(
        ...,
        description="Desviación estándar de la respuesta"
    )
    min_val: float = Field(
        ...,
        description="Valor mínimo de la respuesta"
    )
    max_val: float = Field(
        ...,
        description="Valor máximo de la respuesta"
    )
    std_normalized: float = Field(
        ...,
        ge=0,
        le=1,
        description="Desviación estándar sobre respuestas normalizadas [0,1]"
    )
    discriminative: bool = Field(
        ...,
        description="True si std_normalized > 0.10 (descriptor discriminativo)"
    )
    calculation_date: str = Field(
        ...,
        description="Fecha y hora del cálculo (ISO 8601)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "segmentation_result_id": 1,
                "polygon_id": 211,
                "kernel_type": "edges",
                "mean": -0.0234,
                "std": 0.4521,
                "min_val": -1.8234,
                "max_val": 1.4567,
                "std_normalized": 0.25,
                "discriminative": True,
                "calculation_date": "2026-07-31T22:00:00Z"
            }
        }


class TextureErrorResponse(BaseModel):
    """Response de error."""
    detail: str
