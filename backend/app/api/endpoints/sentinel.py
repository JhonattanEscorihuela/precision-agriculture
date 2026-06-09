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
    DownloadResponse,
    AvailableDatesRequest,
    AvailableDatesResponse,
    DateInfo,
    AcquireBandsRequest,
    AcquireBandsResponse
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

    Usa coordenadas hardcodeadas de Parcela 211 del SRRG, Calabozo, Guárico, Venezuela.
    No requiere polygon_id de la base de datos.

    **Coordenadas de prueba:**
    - Ubicación: SRRG, Calabozo, Guárico, Venezuela
    - Polígono: Parcela 211 (período 2024-2025)

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
    # PARCELA_211 — SRRG, Calabozo, Guárico, Venezuela
    # Período 2024-2025 (parcela principal de referencia)
    TEST_COORDINATES = [
        [-67.528058, 8.8441233],
        [-67.5153475, 8.8386166],
        [-67.5103962, 8.8478932],
        [-67.522828,  8.8534209],
        [-67.528058, 8.8441233]
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
                "X-Test-Location": "Parcela 211, SRRG Calabozo, Guárico, Venezuela",
                "X-Coordinates": str(TEST_COORDINATES),
                "X-File-Size": str(len(file_bytes))
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Test download failed: {str(e)}"
        )


# ============================================================================
# OE1 - Endpoints para consulta y adquisición de bandas Sentinel-2
# ============================================================================

@router.get("/available-dates/{polygon_id}", response_model=AvailableDatesResponse)
async def get_available_dates(
    polygon_id: int,
    start_date: str,
    end_date: str,
    max_cloud: int = 20,
    db: AsyncSession = Depends(get_session)
):
    """
    OE1 - Obtiene fechas con imágenes Sentinel-2 disponibles para un polígono.

    Consulta STAC API para listar todas las escenas Sentinel-2 L2A disponibles
    en el rango de fechas especificado, filtradas por cobertura de nubes.
    Marca cuáles ya fueron adquiridas previamente.

    **Parámetros:**
    - **polygon_id**: ID del polígono en la base de datos
    - **start_date**: Fecha de inicio (YYYY-MM-DD)
    - **end_date**: Fecha de fin (YYYY-MM-DD)
    - **max_cloud**: Cobertura máxima de nubes permitida (0-100), default: 20

    **Retorna:**
    Lista de fechas disponibles ordenadas por fecha descendente (más reciente primero),
    cada una con su porcentaje de nubosidad, scene_id, y flag `acquired`.

    **Ejemplo:**
    ```
    GET /sentinel/available-dates/1?start_date=2024-06-01&end_date=2024-06-30&max_cloud=20
    ```
    """
    from app.crud.acquisition import get_acquisitions_by_polygon

    # Obtener el polígono de la base de datos
    polygon = await get_polygon_by_id(db, polygon_id)
    if not polygon:
        raise HTTPException(status_code=404, detail=f"Polygon {polygon_id} not found")

    # Construir geometría GeoJSON
    geojson_geometry = _build_geojson_geometry(polygon.coordinates)

    # Inicializar servicio y consultar fechas
    service = SentinelService()

    try:
        dates = await service.get_available_dates(
            polygon_coords=geojson_geometry["coordinates"][0],
            start_date=start_date,
            end_date=end_date,
            max_cloud=max_cloud
        )

        # Obtener fechas ya adquiridas
        acquisitions = await get_acquisitions_by_polygon(db, polygon_id)
        acquired_dates = {acq.acquisition_date for acq in acquisitions}

        # Mapear acquisition_id por fecha para consultar NDVIs
        acquisition_id_by_date = {acq.acquisition_date: acq.id for acq in acquisitions}

        # Obtener NDVIs ya calculados
        from app.crud.ndvi import get_ndvi_by_acquisition
        ndvi_calculated_dates = set()
        for acq_date, acq_id in acquisition_id_by_date.items():
            ndvi_result = await get_ndvi_by_acquisition(db, acq_id)
            if ndvi_result:
                ndvi_calculated_dates.add(acq_date)

        # Marcar fechas adquiridas y con NDVI calculado
        date_infos = []
        for d in dates:
            date_infos.append(DateInfo(
                **d,
                acquired=(d["date"] in acquired_dates),
                ndvi_calculated=(d["date"] in ndvi_calculated_dates)
            ))

        return AvailableDatesResponse(
            polygon_id=polygon_id,
            dates=date_infos,
            total_count=len(date_infos),
            date_range={"start": start_date, "end": end_date}
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get available dates: {str(e)}"
        )


@router.post("/acquire", response_model=AcquireBandsResponse)
async def acquire_bands(
    request: AcquireBandsRequest,
    db: AsyncSession = Depends(get_session)
):
    """
    OE1 - Adquiere bandas B04 (Red) y B08 (NIR) para una fecha específica.

    Descarga las bandas espectrales desde Sentinel Hub Process API y las guarda
    en la base de datos para posterior análisis (NDVI en OE2).

    **Proceso:**
    1. Autentica con Copernicus DataSpace (OAuth2)
    2. Descarga banda B04 (Red) como GeoTIFF
    3. Descarga banda B08 (NIR) como GeoTIFF
    4. Valida que cada banda sea < 10MB
    5. Obtiene cloud_coverage desde STAC API
    6. Guarda ambas bandas en la base de datos

    **Parámetros:**
    - **polygon_id**: ID del polígono en la base de datos
    - **date**: Fecha de adquisición (YYYY-MM-DD)
    - **width**: Ancho de la imagen en píxeles (default: 512)
    - **height**: Alto de la imagen en píxeles (default: 512)

    **Retorna:**
    ID de la adquisición creada, tamaños de las bandas, y cloud coverage.

    **Restricciones:**
    - Cada banda debe ser < 10MB
    - Si ya existe una adquisición para ese polígono y fecha, retorna la existente

    **Ejemplo:**
    ```
    POST /sentinel/acquire
    {
      "polygon_id": 1,
      "date": "2024-06-15",
      "width": 512,
      "height": 512
    }
    ```
    """
    # Obtener el polígono de la base de datos
    polygon = await get_polygon_by_id(db, request.polygon_id)
    if not polygon:
        raise HTTPException(
            status_code=404,
            detail=f"Polygon {request.polygon_id} not found"
        )

    # Construir geometría GeoJSON
    geojson_geometry = _build_geojson_geometry(polygon.coordinates)

    # Inicializar servicio y adquirir bandas
    service = SentinelService()

    try:
        result = await service.acquire_bands(
            polygon_coords=geojson_geometry["coordinates"][0],
            date=request.date,
            polygon_id=request.polygon_id,
            db_session=db,
            width=request.width,
            height=request.height,
            max_cloud_coverage=20
        )

        return AcquireBandsResponse(**result)

    except ValueError as e:
        # Error de validación (ej: banda > 10MB)
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to acquire bands: {str(e)}"
        )
