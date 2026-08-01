"""
OE3 - Schemas Pydantic para endpoints de comparación fenológica.
"""

from pydantic import BaseModel, Field
from typing import List


class CurveDataPoint(BaseModel):
    """Punto de datos para visualización de curvas."""
    date: str = Field(..., description="Fecha ISO (YYYY-MM-DD)")
    ndvi_parcel: float = Field(..., description="NDVI de la parcela analizada")
    ndvi_reference: float = Field(..., description="NDVI promedio de referencia")


class PhenologyComparisonResponse(BaseModel):
    """Respuesta de comparación fenológica."""
    polygon_id: int
    reference_polygon_ids: List[int] = Field(
        ..., description="IDs de parcelas usadas como referencia"
    )
    dates_compared: int = Field(..., ge=5, description="Fechas con datos en ambas curvas")
    similarity_score: float = Field(
        ..., ge=-1, le=1, description="Correlación de Pearson [-1, 1]"
    )
    classification: str = Field(..., description="Clasificación interpretativa")
    curve_data: List[CurveDataPoint]

    class Config:
        json_schema_extra = {
            "example": {
                "polygon_id": 4,
                "reference_polygon_ids": [1, 2, 3],
                "dates_compared": 16,
                "similarity_score": 0.87,
                "classification": "Alta similitud — probablemente arroz",
                "curve_data": [
                    {"date": "2026-02-12", "ndvi_parcel": 0.52, "ndvi_reference": 0.55}
                ]
            }
        }


class PhenologyErrorResponse(BaseModel):
    """Respuesta de error."""
    detail: str
