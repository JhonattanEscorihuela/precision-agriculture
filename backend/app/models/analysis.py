"""
OE2 - Modelo de resultados de análisis NDVI.
Almacena raster NDVI y estadísticos calculados a partir de bandas Sentinel-2.
"""

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer, ForeignKey, DateTime
from typing import Optional
from datetime import datetime


class NDVIResultBase(SQLModel):
    """Campos base para resultado NDVI"""
    acquisition_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("sentinel_acquisitions.id", ondelete="CASCADE"),
            unique=True
        ),
        description="ID de la adquisición Sentinel-2 (UNIQUE: 1 NDVI por adquisición)"
    )
    polygon_id: int = Field(
        sa_column=Column(Integer, ForeignKey("polygon.id", ondelete="CASCADE")),
        description="ID del polígono analizado"
    )

    # Estadísticos NDVI
    ndvi_mean: float = Field(description="Promedio NDVI ([-1, 1])")
    ndvi_min: float = Field(description="Mínimo NDVI ([-1, 1])")
    ndvi_max: float = Field(description="Máximo NDVI ([-1, 1])")
    ndvi_std: float = Field(
        description="Desviación estándar NDVI ([0, +∞)). Puede ser 0 si imagen uniforme."
    )
    ndvi_median: Optional[float] = Field(
        default=None,
        description="Mediana NDVI ([-1, 1]). Robusto contra outliers."
    )
    ndvi_p10: Optional[float] = Field(
        default=None,
        description="Percentil 10 NDVI ([-1, 1]). Límite inferior distribución."
    )
    ndvi_p90: Optional[float] = Field(
        default=None,
        description="Percentil 90 NDVI ([-1, 1]). Límite superior distribución."
    )

    # Metadatos del raster
    width: int = Field(description="Ancho del raster NDVI en píxeles")
    height: int = Field(description="Alto del raster NDVI en píxeles")
    analysis_valid_pixel_percentage: Optional[float] = Field(
        default=None,
        description="Píxeles de parcela usados tras aplicar nodata, SCL y geometría"
    )
    cloud_mask_applied: bool = Field(
        default=False,
        description="Indica si el NDVI excluyó nubes y sombras mediante SCL"
    )


class NDVIResult(NDVIResultBase, table=True):
    """
    Tabla de resultados de análisis NDVI.

    Almacena el raster NDVI completo en formato TIFF float32 y los estadísticos
    calculados sobre píxeles válidos. El raster queda disponible para análisis
    espacial en OE3 (segmentación).

    Constraint UNIQUE en acquisition_id garantiza un solo NDVI por adquisición.
    """
    __tablename__ = "ndvi_results"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Raster NDVI completo en formato TIFF float32
    ndvi_tiff: bytes = Field(description="Raster NDVI en formato TIFF float32 con compresión LZW")

    # Overlay coloreado en caché (PNG base64)
    overlay_png: Optional[bytes] = Field(
        default=None,
        description="PNG coloreado RGBA del NDVI para visualización (caché)"
    )

    # Imagen satelital true color en caché
    satellite_png: Optional[bytes] = Field(
        default=None,
        description="PNG RGB true color de la imagen satelital para visualización (caché)"
    )

    # Timestamps
    calculation_date: datetime = Field(
        sa_column=Column(DateTime),
        default_factory=datetime.utcnow,
        description="Fecha y hora del cálculo NDVI"
    )
    created_at: Optional[datetime] = Field(
        sa_column=Column(DateTime),
        default_factory=datetime.utcnow,
        description="Timestamp de creación del registro"
    )

    class Config:
        """Configuración del modelo"""
        json_schema_extra = {
            "example": {
                "acquisition_id": 1,
                "polygon_id": 1,
                "ndvi_mean": 0.6523,
                "ndvi_min": -0.1234,
                "ndvi_max": 0.8765,
                "ndvi_std": 0.1432,
                "ndvi_median": 0.6789,
                "ndvi_p10": 0.4532,
                "ndvi_p90": 0.8123,
                "width": 512,
                "height": 512,
                "calculation_date": "2026-06-08T10:30:00Z",
                "created_at": "2026-06-08T10:30:00Z"
            }
        }


class NDVIResultCreate(NDVIResultBase):
    """Schema para crear un nuevo resultado NDVI"""
    ndvi_tiff: bytes
    calculation_date: datetime
    created_at: datetime


class NDVIResultPublic(NDVIResultBase):
    """
    Schema público para respuestas de API (sin datos binarios).
    Usado en endpoints para no transferir el raster completo.
    """
    id: int
    calculation_date: datetime
    created_at: datetime
    tiff_size_kb: float = Field(description="Tamaño del TIFF NDVI en KB")


class TextureOverlayCache(SQLModel, table=True):
    """
    Caché de overlays PNG coloreados de textura.
    Un registro por (ndvi_result_id, kernel).
    """
    __tablename__ = "texture_overlay_cache"

    id: Optional[int] = Field(default=None, primary_key=True)
    ndvi_result_id: int = Field(
        sa_column=Column(Integer, ForeignKey("ndvi_results.id", ondelete="CASCADE")),
        description="ID del resultado NDVI usado como base"
    )
    kernel: str = Field(
        description="Nombre del kernel aplicado (contrast/edges/homogeneity)",
        max_length=20
    )
    overlay_png: bytes = Field(
        description="PNG coloreado RGBA del resultado de textura"
    )
    interpretation: str = Field(
        description="Texto interpretativo generado según kernel y valores"
    )
    created_at: Optional[datetime] = Field(
        sa_column=Column(DateTime),
        default_factory=datetime.utcnow,
        description="Timestamp de creación del caché"
    )
