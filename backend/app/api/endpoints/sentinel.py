"""
Endpoints API para adquisición de imágenes Sentinel-2.
"""

from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from io import BytesIO

from app.database import get_session
from app.services.sentinel_service import SentinelService
from app.schemas.sentinel import (
    NDVIDownloadRequest,
    BandsDownloadRequest,
    AvailabilityCheckRequest,
    AvailabilityResponse,
    DownloadResponse
)
from app.schemas.sentinel_test import SentinelTestRequest
from app.crud.polygon import get_polygon_by_id


router = APIRouter()


def _build_geojson_geometry(coordinates: list) -> dict:
    """
    Convierte coordenadas de la base de datos a formato GeoJSON geometry.

    Args:
        coordinates: Lista de coordenadas [[lon, lat], ...]

    Returns:
        dict: Geometría GeoJSON
    """
    return {
        "type": "Polygon",
        "coordinates": [coordinates]
    }


@router.post("/check-availability", response_model=AvailabilityResponse)
async def check_availability(
    request: AvailabilityCheckRequest,
    db: AsyncSession = Depends(get_session)
):
    """
    Verifica si hay imágenes Sentinel-2 disponibles para un polígono y rango de fechas.

    - **polygon_id**: ID del polígono en la base de datos
    - **start_date**: Fecha de inicio (YYYY-MM-DD)
    - **end_date**: Fecha de fin (YYYY-MM-DD)
    - **max_cloud_coverage**: Cobertura máxima de nubes (0-100)
    """
    # Obtener el polígono de la base de datos
    polygon = await get_polygon_by_id(db, request.polygon_id)
    if not polygon:
        raise HTTPException(status_code=404, detail="Polygon not found")

    # Construir geometría GeoJSON
    geojson_geometry = _build_geojson_geometry(polygon.coordinates)

    # Inicializar servicio y verificar disponibilidad
    service = SentinelService()

    try:
        result = await service.check_availability(
            polygon_geojson=geojson_geometry,
            start_date=request.start_date,
            end_date=request.end_date,
            max_cloud_coverage=request.max_cloud_coverage
        )

        return AvailabilityResponse(
            available=result["available"],
            date_range=result["date_range"],
            message=result["message"],
            polygon_id=request.polygon_id
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check availability: {str(e)}"
        )


@router.post("/download/ndvi")
async def download_ndvi(
    request: NDVIDownloadRequest,
    db: AsyncSession = Depends(get_session)
):
    """
    Descarga imagen NDVI calculada para un polígono como GeoTIFF.

    El NDVI (Normalized Difference Vegetation Index) se calcula como:
    (NIR - Red) / (NIR + Red) = (B08 - B04) / (B08 + B04)

    Valores típicos:
    - Agua: < 0
    - Suelo desnudo: 0 - 0.2
    - Vegetación escasa: 0.2 - 0.5
    - Vegetación densa: 0.5 - 1.0

    - **polygon_id**: ID del polígono en la base de datos
    - **start_date**: Fecha de inicio (YYYY-MM-DD)
    - **end_date**: Fecha de fin (YYYY-MM-DD)
    - **width**: Ancho de la imagen en píxeles
    - **height**: Alto de la imagen en píxeles
    - **max_cloud_coverage**: Cobertura máxima de nubes (0-100)

    Retorna un archivo GeoTIFF con valores NDVI en formato FLOAT32.
    """
    # Obtener el polígono de la base de datos
    polygon = await get_polygon_by_id(db, request.polygon_id)
    if not polygon:
        raise HTTPException(status_code=404, detail="Polygon not found")

    # Construir geometría GeoJSON
    geojson_geometry = _build_geojson_geometry(polygon.coordinates)

    # Inicializar servicio y descargar NDVI
    service = SentinelService()

    try:
        tiff_bytes = await service.download_ndvi(
            polygon_geojson=geojson_geometry,
            start_date=request.start_date,
            end_date=request.end_date,
            width=request.width,
            height=request.height,
            max_cloud_coverage=request.max_cloud_coverage,
            polygon_id=request.polygon_id
        )

        # Retornar como archivo descargable
        return StreamingResponse(
            BytesIO(tiff_bytes),
            media_type="image/tiff",
            headers={
                "Content-Disposition": f"attachment; filename=ndvi_{request.polygon_id}_{request.start_date}.tif"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download NDVI: {str(e)}"
        )


@router.post("/download/bands")
async def download_bands(
    request: BandsDownloadRequest,
    db: AsyncSession = Depends(get_session)
):
    """
    Descarga bandas espectrales específicas de Sentinel-2 como GeoTIFF multi-banda.

    Bandas principales disponibles:
    - **B02**: Blue (490nm)
    - **B03**: Green (560nm)
    - **B04**: Red (665nm)
    - **B05**: Red Edge 1 (705nm)
    - **B06**: Red Edge 2 (740nm)
    - **B07**: Red Edge 3 (783nm)
    - **B08**: NIR (842nm)
    - **B8A**: Narrow NIR (865nm)
    - **B11**: SWIR 1 (1610nm)
    - **B12**: SWIR 2 (2190nm)

    - **polygon_id**: ID del polígono en la base de datos
    - **bands**: Lista de bandas a descargar (ej: ["B04", "B08"])
    - **start_date**: Fecha de inicio (YYYY-MM-DD)
    - **end_date**: Fecha de fin (YYYY-MM-DD)
    - **width**: Ancho de la imagen en píxeles
    - **height**: Alto de la imagen en píxeles
    - **max_cloud_coverage**: Cobertura máxima de nubes (0-100)

    Retorna un archivo GeoTIFF multi-banda con valores de reflectancia en formato FLOAT32.
    """
    # Validar que se soliciten bandas
    if not request.bands:
        raise HTTPException(status_code=400, detail="At least one band must be specified")

    # Obtener el polígono de la base de datos
    polygon = await get_polygon_by_id(db, request.polygon_id)
    if not polygon:
        raise HTTPException(status_code=404, detail="Polygon not found")

    # Construir geometría GeoJSON
    geojson_geometry = _build_geojson_geometry(polygon.coordinates)

    # Inicializar servicio y descargar bandas
    service = SentinelService()

    try:
        tiff_bytes = await service.download_bands(
            polygon_geojson=geojson_geometry,
            bands=request.bands,
            start_date=request.start_date,
            end_date=request.end_date,
            width=request.width,
            height=request.height,
            max_cloud_coverage=request.max_cloud_coverage,
            polygon_id=request.polygon_id
        )

        bands_str = "_".join(request.bands)
        filename = f"bands_{bands_str}_{request.polygon_id}_{request.start_date}.tif"

        return StreamingResponse(
            BytesIO(tiff_bytes),
            media_type="image/tiff",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download bands: {str(e)}"
        )


@router.post("/download/true-color")
async def download_true_color(
    request: NDVIDownloadRequest,
    db: AsyncSession = Depends(get_session)
):
    """
    Descarga imagen RGB true-color (B04, B03, B02) como PNG.

    Útil para visualización y verificación visual de la parcela.
    La imagen se estira automáticamente para mejor visibilidad.

    - **polygon_id**: ID del polígono en la base de datos
    - **start_date**: Fecha de inicio (YYYY-MM-DD)
    - **end_date**: Fecha de fin (YYYY-MM-DD)
    - **width**: Ancho de la imagen en píxeles
    - **height**: Alto de la imagen en píxeles
    - **max_cloud_coverage**: Cobertura máxima de nubes (0-100)

    Retorna un archivo PNG con la imagen RGB.
    """
    # Obtener el polígono de la base de datos
    polygon = await get_polygon_by_id(db, request.polygon_id)
    if not polygon:
        raise HTTPException(status_code=404, detail="Polygon not found")

    # Construir geometría GeoJSON
    geojson_geometry = _build_geojson_geometry(polygon.coordinates)

    # Inicializar servicio y descargar imagen true-color
    service = SentinelService()

    try:
        png_bytes = await service.download_true_color(
            polygon_geojson=geojson_geometry,
            start_date=request.start_date,
            end_date=request.end_date,
            width=request.width,
            height=request.height,
            max_cloud_coverage=request.max_cloud_coverage,
            polygon_id=request.polygon_id
        )

        return StreamingResponse(
            BytesIO(png_bytes),
            media_type="image/png",
            headers={
                "Content-Disposition": f"attachment; filename=true_color_{request.polygon_id}_{request.start_date}.png"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download true-color image: {str(e)}"
        )


@router.post("/test")
async def test_sentinel_download(request: SentinelTestRequest):
    """
    🧪 Endpoint de prueba para verificar que Sentinel-2 funciona correctamente.

    Usa coordenadas hardcodeadas de una parcela pequeña en España (Madrid).
    No requiere polygon_id de la base de datos.

    **Coordenadas de prueba:**
    - Ubicación: Cerca de Madrid, España
    - Polígono: ~1km² aproximadamente

    **Parámetros:**
    - **start_date**: Fecha de inicio (YYYY-MM-DD)
    - **end_date**: Fecha de fin (YYYY-MM-DD)
    - **download_type**: Tipo de descarga ("ndvi", "true-color", "bands")
    - **width**: Ancho de la imagen en píxeles (default: 256)
    - **height**: Alto de la imagen en píxeles (default: 256)
    - **max_cloud_coverage**: Cobertura máxima de nubes (default: 30)

    **Ejemplo de uso:**
    ```bash
    curl -X POST http://localhost:8000/sentinel/test \\
      -H "Content-Type: application/json" \\
      -d '{
        "start_date": "2024-06-15",
        "end_date": "2024-06-20",
        "download_type": "ndvi"
      }' --output test_ndvi.tif
    ```

    Retorna el archivo descargado (TIFF o PNG según el tipo).
    """
    # Coordenadas hardcodeadas de prueba (parcela en España, cerca de Madrid)
    TEST_COORDINATES = [
        [-3.7038, 40.4168],
        [-3.7038, 40.4268],
        [-3.6938, 40.4268],
        [-3.6938, 40.4168],
        [-3.7038, 40.4168]
    ]

    # Construir geometría GeoJSON
    geojson_geometry = {
        "type": "Polygon",
        "coordinates": [TEST_COORDINATES]
    }

    # Inicializar servicio
    service = SentinelService()

    try:
        # Descargar según el tipo solicitado
        if request.download_type == "ndvi":
            file_bytes = await service.download_ndvi(
                polygon_geojson=geojson_geometry,
                start_date=request.start_date,
                end_date=request.end_date,
                width=request.width,
                height=request.height,
                max_cloud_coverage=request.max_cloud_coverage
            )
            media_type = "image/tiff"
            filename = f"test_ndvi_{request.start_date}.tif"

        elif request.download_type == "true-color":
            file_bytes = await service.download_true_color(
                polygon_geojson=geojson_geometry,
                start_date=request.start_date,
                end_date=request.end_date,
                width=request.width,
                height=request.height,
                max_cloud_coverage=request.max_cloud_coverage
            )
            media_type = "image/png"
            filename = f"test_true_color_{request.start_date}.png"

        elif request.download_type == "bands":
            # Para prueba, descargamos B04 y B08
            file_bytes = await service.download_bands(
                polygon_geojson=geojson_geometry,
                bands=["B04", "B08"],
                start_date=request.start_date,
                end_date=request.end_date,
                width=request.width,
                height=request.height,
                max_cloud_coverage=request.max_cloud_coverage
            )
            media_type = "image/tiff"
            filename = f"test_bands_B04_B08_{request.start_date}.tif"

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid download_type: {request.download_type}"
            )

        return StreamingResponse(
            BytesIO(file_bytes),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Test-Location": "Madrid, Spain",
                "X-Coordinates": str(TEST_COORDINATES),
                "X-File-Size": str(len(file_bytes))
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Test download failed: {str(e)}"
        )
