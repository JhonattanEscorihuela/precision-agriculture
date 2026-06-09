"""
Schemas Pydantic para endpoints de Sentinel-2.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class AvailabilityCheckRequest(BaseModel):
    """Request para verificar disponibilidad de imágenes"""
    polygon_id: int
    start_date: str = Field(description="Fecha de inicio (YYYY-MM-DD)")
    end_date: str = Field(description="Fecha de fin (YYYY-MM-DD)")
    max_cloud_coverage: int = Field(default=20, ge=0, le=100)


class AvailabilityResponse(BaseModel):
    """Response de disponibilidad de imágenes"""
    available: bool
    date_range: Dict[str, str]
    message: str
    polygon_id: int


class NDVIDownloadRequest(BaseModel):
    """Request para descargar NDVI"""
    polygon_id: int
    start_date: str = Field(description="Fecha de inicio (YYYY-MM-DD)")
    end_date: str = Field(description="Fecha de fin (YYYY-MM-DD)")
    width: int = Field(default=512, ge=10, le=2500)
    height: int = Field(default=512, ge=10, le=2500)
    max_cloud_coverage: int = Field(default=20, ge=0, le=100)


class BandsDownloadRequest(BaseModel):
    """Request para descargar bandas espectrales"""
    polygon_id: int
    bands: List[str] = Field(description="Lista de bandas (ej: ['B04', 'B08'])")
    start_date: str = Field(description="Fecha de inicio (YYYY-MM-DD)")
    end_date: str = Field(description="Fecha de fin (YYYY-MM-DD)")
    width: int = Field(default=512, ge=10, le=2500)
    height: int = Field(default=512, ge=10, le=2500)
    max_cloud_coverage: int = Field(default=20, ge=0, le=100)


class DownloadResponse(BaseModel):
    """Response de descarga de imágenes"""
    success: bool
    message: str
    file_size_bytes: int


# ============================================================================
# OE1 - Schemas para adquisición de bandas Sentinel-2
# ============================================================================

class DateInfo(BaseModel):
    """Información de una fecha disponible"""
    date: str = Field(description="Fecha en formato YYYY-MM-DD")
    cloud_cover: float = Field(description="Porcentaje de cobertura de nubes (0-100)")
    scene_id: str = Field(default="", description="ID de la escena Sentinel")
    datetime: str = Field(default="", description="Timestamp completo ISO 8601")
    acquired: bool = Field(default=False, description="Si esta fecha ya fue adquirida (bandas descargadas)")
    ndvi_calculated: bool = Field(default=False, description="Si esta fecha ya tiene NDVI calculado")


class AvailableDatesRequest(BaseModel):
    """Request para obtener fechas disponibles (via query params)"""
    start_date: str = Field(description="Fecha de inicio (YYYY-MM-DD)")
    end_date: str = Field(description="Fecha de fin (YYYY-MM-DD)")
    max_cloud: int = Field(default=20, ge=0, le=100)


class AvailableDatesResponse(BaseModel):
    """Response con fechas disponibles"""
    polygon_id: int
    dates: List[DateInfo]
    total_count: int
    date_range: Dict[str, str]


class AcquireBandsRequest(BaseModel):
    """Request para adquirir bandas B04 y B08"""
    polygon_id: int
    date: str = Field(description="Fecha de adquisición (YYYY-MM-DD)")
    width: int = Field(default=512, ge=10, le=2500)
    height: int = Field(default=512, ge=10, le=2500)


class AcquireBandsResponse(BaseModel):
    """Response de adquisición de bandas"""
    acquisition_id: int
    polygon_id: int
    date: str
    cloud_coverage: float
    size_b04_kb: float
    size_b08_kb: float
    already_existed: bool = Field(default=False, description="Si la adquisición ya existía")
