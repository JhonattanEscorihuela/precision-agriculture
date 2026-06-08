"""
OE2 - Schemas Pydantic para endpoints de NDVI.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class NDVICalculateRequest(BaseModel):
    """Request para calcular NDVI de una adquisición."""
    acquisition_id: int = Field(..., description="ID de la adquisición Sentinel-2")

    class Config:
        json_schema_extra = {
            "example": {
                "acquisition_id": 1
            }
        }


class NDVIStatsResponse(BaseModel):
    """Response con estadísticos NDVI (sin raster binario)."""
    acquisition_id: int
    polygon_id: int
    calculation_date: str = Field(..., description="Fecha y hora del cálculo (ISO 8601)")
    ndvi_mean: float = Field(..., ge=-1, le=1, description="Promedio NDVI")
    ndvi_min: float = Field(..., ge=-1, le=1, description="Mínimo NDVI")
    ndvi_max: float = Field(..., ge=-1, le=1, description="Máximo NDVI")
    ndvi_std: float = Field(
        ...,
        ge=0,
        description="Desviación estándar NDVI. Puede ser 0 si imagen uniforme."
    )
    width: int = Field(..., description="Ancho del raster en píxeles")
    height: int = Field(..., description="Alto del raster en píxeles")

    class Config:
        json_schema_extra = {
            "example": {
                "acquisition_id": 1,
                "polygon_id": 1,
                "calculation_date": "2026-06-08T10:30:00Z",
                "ndvi_mean": 0.6523,
                "ndvi_min": -0.1234,
                "ndvi_max": 0.8765,
                "ndvi_std": 0.1432,
                "width": 512,
                "height": 512
            }
        }


class NDVICalculateResponse(BaseModel):
    """Response de cálculo NDVI exitoso."""
    ndvi_id: int = Field(..., description="ID del resultado NDVI en BD")
    acquisition_id: int
    polygon_id: int
    calculation_date: str = Field(
        ...,
        description="Fecha y hora del cálculo (ISO 8601). En raíz para acceso directo del frontend."
    )
    stats: NDVIStatsResponse
    message: str = Field(default="NDVI calculado exitosamente")

    class Config:
        json_schema_extra = {
            "example": {
                "ndvi_id": 1,
                "acquisition_id": 1,
                "polygon_id": 1,
                "calculation_date": "2026-06-08T10:30:00Z",
                "stats": {
                    "acquisition_id": 1,
                    "polygon_id": 1,
                    "calculation_date": "2026-06-08T10:30:00Z",
                    "ndvi_mean": 0.6523,
                    "ndvi_min": -0.1234,
                    "ndvi_max": 0.8765,
                    "ndvi_std": 0.1432,
                    "width": 512,
                    "height": 512
                },
                "message": "NDVI calculado exitosamente"
            }
        }


class NDVIErrorResponse(BaseModel):
    """Response de error en operaciones NDVI."""
    detail: str = Field(..., description="Descripción del error")

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Acquisition not found"
            }
        }
