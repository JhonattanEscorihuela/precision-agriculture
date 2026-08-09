"""OE3 - Esquemas para la comparación fenológica de una parcela."""

from typing import List, Optional

from pydantic import BaseModel, Field


class CurveDataPoint(BaseModel):
    """Punto NDVI alineado con la plantilla por días desde el inicio observado."""

    date: str = Field(..., description="Fecha ISO de la observación (YYYY-MM-DD)")
    days_since_first_observation: int = Field(
        ..., ge=0, description="Días transcurridos desde la primera observación NDVI"
    )
    ndvi_parcel: float = Field(..., description="NDVI promedio de la parcela")
    ndvi_reference: float = Field(..., description="NDVI interpolado de la plantilla")


class PhenologyComparisonResponse(BaseModel):
    """Comparación y suficiencia de datos para una clasificación fenológica."""

    polygon_id: int
    reference_polygon_ids: List[int] = Field(
        default_factory=list,
        description="Lista vacía: la referencia ya no depende de polígonos de usuarios",
    )
    dates_compared: int = Field(..., ge=1, description="Observaciones NDVI únicas comparadas")
    similarity_score: Optional[float] = Field(
        default=None,
        ge=-1,
        le=1,
        description="Correlación de Pearson; null cuando los datos son insuficientes",
    )
    matches_rice_pattern: Optional[bool] = Field(
        default=None,
        description="Resultado del umbral alto; null cuando no se puede clasificar",
    )
    sufficient_for_classification: bool
    observation_span_days: int = Field(..., ge=0)
    minimum_observations: int = Field(default=5, ge=1)
    minimum_span_days: int = Field(default=90, ge=1)
    reference_source: str
    alignment_method: str
    classification: str
    warnings: List[str] = Field(default_factory=list)
    curve_data: List[CurveDataPoint] = Field(..., min_items=1)

    class Config:
        json_schema_extra = {
            "example": {
                "polygon_id": 10,
                "reference_polygon_ids": [],
                "dates_compared": 3,
                "similarity_score": None,
                "matches_rice_pattern": None,
                "sufficient_for_classification": False,
                "observation_span_days": 70,
                "minimum_observations": 5,
                "minimum_span_days": 90,
                "reference_source": "Plantilla teórica de arroz — Rio Grande do Sul (Brasil)",
                "alignment_method": "Días desde la primera observación NDVI (aproximación)",
                "classification": (
                    "Comparación exploratoria — aún no hay cobertura temporal suficiente "
                    "para clasificar el patrón fenológico."
                ),
                "warnings": [
                    "Se requieren al menos 5 observaciones; hay 3.",
                    "Se requieren al menos 90 días de cobertura; hay 70.",
                ],
                "curve_data": [
                    {
                        "date": "2026-05-18",
                        "days_since_first_observation": 0,
                        "ndvi_parcel": 0.56,
                        "ndvi_reference": 0.30,
                    }
                ],
            }
        }


class PhenologyErrorResponse(BaseModel):
    """Respuesta de error."""

    detail: str
