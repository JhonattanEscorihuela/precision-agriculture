"""
OE3 - Schemas Pydantic para endpoints de segmentación.
"""

from pydantic import BaseModel, Field
from typing import Optional


class SegmentationRequest(BaseModel):
    """Request para calcular segmentación de un NDVI."""
    ndvi_result_id: int = Field(..., description="ID del resultado NDVI")
    threshold: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Umbral NDVI para clasificación (default 0.3)"
    )
    save_mask: bool = Field(
        False,
        description="Guardar máscara binaria TIFF (consume ~500KB por resultado)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "ndvi_result_id": 1,
                "threshold": 0.3,
                "save_mask": False
            }
        }


class SegmentationResponse(BaseModel):
    """Response con métricas de segmentación."""
    id: int
    ndvi_result_id: int = Field(..., description="ID del resultado NDVI")
    acquisition_id: int = Field(
        ...,
        description="Alias compatible de ndvi_result_id; se conserva para clientes existentes"
    )
    polygon_id: int
    calculation_date: str = Field(..., description="Fecha y hora del cálculo (ISO 8601)")
    threshold_used: float = Field(..., ge=0, le=1, description="Umbral aplicado")
    total_pixels: int = Field(..., ge=0, description="Total de píxeles válidos")
    cultivated_pixels: int = Field(..., ge=0, description="Píxeles clasificados como cultivados")
    cultivated_percentage: float = Field(..., ge=0, le=100, description="Porcentaje cultivado")
    tiff_binary_mask: Optional[str] = Field(None, description="Siempre null (descarga via /mask)")
    has_binary_mask: bool = Field(..., description="True si máscara disponible para descarga")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "ndvi_result_id": 1,
                "acquisition_id": 1,
                "polygon_id": 211,
                "calculation_date": "2026-07-31T22:00:00Z",
                "threshold_used": 0.3,
                "total_pixels": 262144,
                "cultivated_pixels": 198432,
                "cultivated_percentage": 75.68,
                "tiff_binary_mask": None,
                "has_binary_mask": True
            }
        }


class SegmentationErrorResponse(BaseModel):
    """Response de error."""
    detail: str
