"""
Schemas Pydantic para las peticiones y respuestas de la API Sentinel-2.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class SentinelDownloadRequest(BaseModel):
    """
    Esquema para solicitar descarga de imágenes Sentinel-2.
    """
    polygon_id: int = Field(..., description="ID del polígono en la base de datos")
    start_date: str = Field(
        ...,
        description="Fecha de inicio en formato YYYY-MM-DD",
        example="2024-01-15"
    )
    end_date: str = Field(
        ...,
        description="Fecha de fin en formato YYYY-MM-DD",
        example="2024-01-20"
    )
    width: Optional[int] = Field(
        512,
        description="Ancho de la imagen en píxeles",
        ge=1,
        le=2500
    )
    height: Optional[int] = Field(
        512,
        description="Alto de la imagen en píxeles",
        ge=1,
        le=2500
    )
    max_cloud_coverage: Optional[int] = Field(
        20,
        description="Cobertura máxima de nubes permitida (0-100)",
        ge=0,
        le=100
    )


class NDVIDownloadRequest(SentinelDownloadRequest):
    """
    Esquema específico para solicitar descarga de NDVI.
    Hereda todos los campos de SentinelDownloadRequest.
    """
    pass


class BandsDownloadRequest(SentinelDownloadRequest):
    """
    Esquema para solicitar descarga de bandas específicas.
    """
    bands: List[str] = Field(
        ...,
        description="Lista de bandas a descargar (ej: ['B04', 'B08'])",
        example=["B04", "B08"]
    )


class AvailabilityCheckRequest(BaseModel):
    """
    Esquema para verificar disponibilidad de imágenes.
    """
    polygon_id: int = Field(..., description="ID del polígono en la base de datos")
    start_date: str = Field(
        ...,
        description="Fecha de inicio en formato YYYY-MM-DD",
        example="2024-01-15"
    )
    end_date: str = Field(
        ...,
        description="Fecha de fin en formato YYYY-MM-DD",
        example="2024-01-20"
    )
    max_cloud_coverage: Optional[int] = Field(
        20,
        description="Cobertura máxima de nubes permitida (0-100)",
        ge=0,
        le=100
    )


class AvailabilityResponse(BaseModel):
    """
    Respuesta de verificación de disponibilidad.
    """
    available: bool = Field(..., description="Si hay imágenes disponibles")
    date_range: Dict[str, str] = Field(..., description="Rango de fechas consultado")
    message: str = Field(..., description="Mensaje descriptivo del resultado")
    polygon_id: int = Field(..., description="ID del polígono consultado")


class DownloadResponse(BaseModel):
    """
    Respuesta exitosa de descarga de imágenes.
    """
    success: bool = Field(True, description="Si la descarga fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo")
    file_size_bytes: int = Field(..., description="Tamaño del archivo descargado")
    polygon_id: int = Field(..., description="ID del polígono procesado")
    date_range: Dict[str, str] = Field(..., description="Rango de fechas descargado")
