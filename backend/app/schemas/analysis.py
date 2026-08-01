"""
OE3+OE4 - Schemas Pydantic para análisis completo por parcela.
Pipeline: NDVI → Segmentación → Textura, agregado por kernel.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class PerDateTexture(BaseModel):
    """Textura por kernel para una fecha."""
    edges: Optional[Dict[str, Any]] = Field(
        None,
        description="Descriptor de bordes (Laplaciano): {std_normalized, discriminative}"
    )
    homogeneity: Optional[Dict[str, Any]] = Field(
        None,
        description="Descriptor de homogeneidad (varianza local): {std_normalized, discriminative}"
    )
    contrast: Optional[Dict[str, Any]] = Field(
        None,
        description="Descriptor de contraste (gradiente): {std_normalized, discriminative}"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "edges": {"std_normalized": 0.25, "discriminative": True},
                "homogeneity": {"std_normalized": 0.08, "discriminative": False},
                "contrast": {"std_normalized": 0.18, "discriminative": True}
            }
        }


class PerDateResult(BaseModel):
    """Resultado de análisis completo para una fecha."""
    ndvi_result_id: int
    acquisition_date: Optional[str] = Field(
        None,
        description="Fecha de adquisición en formato ISO 8601"
    )
    ndvi_mean: float = Field(
        ...,
        description="NDVI promedio de la parcela"
    )
    cultivated_percentage: float = Field(
        ...,
        ge=0,
        le=100,
        description="Porcentaje de área cultivada (umbral 0.30)"
    )
    texture: PerDateTexture = Field(
        ...,
        description="Descriptores de textura por kernel"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "ndvi_result_id": 42,
                "acquisition_date": "2025-02-15T10:30:00Z",
                "ndvi_mean": 0.65,
                "cultivated_percentage": 78.5,
                "texture": {
                    "edges": {"std_normalized": 0.25, "discriminative": True},
                    "homogeneity": {"std_normalized": 0.08, "discriminative": False},
                    "contrast": {"std_normalized": 0.18, "discriminative": True}
                }
            }
        }


class DateFailed(BaseModel):
    """Fecha con error durante procesamiento."""
    ndvi_result_id: int
    error: str = Field(
        ...,
        description="Mensaje de error"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "ndvi_result_id": 99,
                "error": "Cultivated area too small after erosion (< 10 pixels)"
            }
        }


class KernelSummary(BaseModel):
    """Resumen agregado por kernel."""
    mean_std_normalized: float = Field(
        ...,
        ge=0,
        le=1,
        description="Promedio de std_normalized sobre todas las fechas procesadas"
    )
    dates_discriminative: int = Field(
        ...,
        ge=0,
        description="Cantidad de fechas donde el kernel fue discriminativo (std_normalized > 0.10)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "mean_std_normalized": 0.22,
                "dates_discriminative": 8
            }
        }


class AggregatedResult(BaseModel):
    """Métricas agregadas por kernel + kernel más discriminativo."""
    edges: KernelSummary
    homogeneity: KernelSummary
    contrast: KernelSummary
    most_discriminative_kernel: str = Field(
        ...,
        description="Kernel con mayor mean_std_normalized ('edges', 'homogeneity' o 'contrast')"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "edges": {"mean_std_normalized": 0.28, "dates_discriminative": 12},
                "homogeneity": {"mean_std_normalized": 0.09, "dates_discriminative": 2},
                "contrast": {"mean_std_normalized": 0.19, "dates_discriminative": 7},
                "most_discriminative_kernel": "edges"
            }
        }


class FullAnalysisResponse(BaseModel):
    """Response del análisis completo por parcela."""
    polygon_id: int
    total_ndvi_results: int = Field(
        ...,
        description="Cantidad total de NDVI results disponibles para la parcela"
    )
    dates_processed: int = Field(
        ...,
        description="Cantidad de fechas procesadas exitosamente"
    )
    dates_failed: List[DateFailed] = Field(
        default_factory=list,
        description="Lista de fechas con error (si alguna falló)"
    )
    per_date_results: List[PerDateResult] = Field(
        ...,
        description="Resultados detallados por fecha (NDVI + segmentación + textura)"
    )
    aggregated: AggregatedResult = Field(
        ...,
        description="Métricas agregadas por kernel + kernel más discriminativo"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "polygon_id": 211,
                "total_ndvi_results": 15,
                "dates_processed": 14,
                "dates_failed": [
                    {"ndvi_result_id": 99, "error": "Cultivated area too small"}
                ],
                "per_date_results": [
                    {
                        "ndvi_result_id": 42,
                        "acquisition_date": "2025-02-15T10:30:00Z",
                        "ndvi_mean": 0.65,
                        "cultivated_percentage": 78.5,
                        "texture": {
                            "edges": {"std_normalized": 0.25, "discriminative": True},
                            "homogeneity": {"std_normalized": 0.08, "discriminative": False},
                            "contrast": {"std_normalized": 0.18, "discriminative": True}
                        }
                    }
                ],
                "aggregated": {
                    "edges": {"mean_std_normalized": 0.28, "dates_discriminative": 12},
                    "homogeneity": {"mean_std_normalized": 0.09, "dates_discriminative": 2},
                    "contrast": {"mean_std_normalized": 0.19, "dates_discriminative": 7},
                    "most_discriminative_kernel": "edges"
                }
            }
        }


class AnalysisErrorResponse(BaseModel):
    """Response de error."""
    detail: str
