"""
Schemas para endpoint de prueba de Sentinel-2.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal


class SentinelTestRequest(BaseModel):
    """
    Esquema para endpoint de prueba con coordenadas hardcodeadas.
    """
    start_date: str = Field(
        "2024-01-15",
        description="Fecha de inicio en formato YYYY-MM-DD",
        example="2024-01-15"
    )
    end_date: str = Field(
        "2024-01-20",
        description="Fecha de fin en formato YYYY-MM-DD",
        example="2024-01-20"
    )
    download_type: Literal["ndvi", "true-color", "bands"] = Field(
        "ndvi",
        description="Tipo de descarga a realizar"
    )
    width: Optional[int] = Field(
        256,
        description="Ancho de la imagen en píxeles",
        ge=1,
        le=2500
    )
    height: Optional[int] = Field(
        256,
        description="Alto de la imagen en píxeles",
        ge=1,
        le=2500
    )
    max_cloud_coverage: Optional[int] = Field(
        30,
        description="Cobertura máxima de nubes permitida (0-100)",
        ge=0,
        le=100
    )


class SentinelTestResponse(BaseModel):
    """
    Respuesta del endpoint de prueba.
    """
    success: bool
    message: str
    test_location: str
    coordinates_used: list
    file_size_bytes: int
    date_range: dict
