"""
OE2 - Servicio de cálculo de índice NDVI.
Calcula NDVI a partir de bandas Sentinel-2 L2A (B04 y B08) almacenadas en BD.
"""

import io
import logging
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.features import geometry_mask
from rasterio.warp import reproject, transform_geom
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.crud import acquisition as crud_acquisition
from app.crud import ndvi as crud_ndvi
from app.crud import polygon as crud_polygon


# Configurar logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class NDVIService:
    """
    Servicio para calcular el índice NDVI sobre bandas Sentinel-2 L2A.

    NDVI (Normalized Difference Vegetation Index) mide la salud de la vegetación
    mediante la diferencia normalizada entre las bandas NIR (B08) y Red (B04).

    Fórmula: NDVI = (NIR - Red) / (NIR + Red)
    Rango válido: [-1, 1]

    El servicio es idempotente: si ya existe un NDVI para una adquisición,
    lo retorna sin recalcular.
    """

    # NOTA IMPORTANTE: Factor de escala Sentinel-2 L2A
    # Los datos de Copernicus Process API ya vienen en reflectancia (0.0-1.0).
    # NO aplicar factor de escala para datos de Process API.
    # Si se usara STAC directo con uint16, sí aplicaría /10000.
    # L2A_SCALE_FACTOR = 10000.0  # NO USAR con Process API

    async def calculate_ndvi(
        self,
        acquisition_id: int,
        user_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Calcula NDVI para una adquisición Sentinel-2 existente.

        Workflow:
        1. Verificar si ya existe NDVI (idempotencia)
        2. Obtener adquisición y verificar ownership
        3. Leer bandas B04 y B08 desde BD
        4. Calcular NDVI con manejo de división por cero y nodata
        5. Validar rango [-1, 1]
        6. Calcular estadísticos sobre píxeles válidos
        7. Guardar resultado en BD

        Args:
            acquisition_id: ID de la adquisición Sentinel-2
            user_id: ID del usuario (para verificar ownership)
            db: Sesión async de BD

        Returns:
            Dict con: ndvi_id, acquisition_id, polygon_id, calculation_date, stats

        Raises:
            HTTPException 404: Si acquisition_id no existe
            HTTPException 403: Si adquisición no pertenece al usuario
            ValueError: Si NDVI fuera de rango [-1, 1]
            ValueError: Si bandas tienen dimensiones diferentes
            ValueError: Si no hay píxeles válidos
        """
        logger.info(f"🌿 Iniciando cálculo NDVI para acquisition_id={acquisition_id}")

        # 1. Obtener adquisición primero (necesitamos acquisition_date)
        acquisition = await crud_acquisition.get_acquisition_by_id(db, acquisition_id)
        if not acquisition:
            logger.error(f"❌ Acquisition {acquisition_id} no encontrada")
            raise HTTPException(status_code=404, detail="Acquisition not found")

        # 2. Verificar ownership antes de retornar cualquier dato existente.
        polygon = await crud_polygon.get_polygon_by_id(db, acquisition.polygon_id)
        if not polygon or polygon.user_id != user_id:
            logger.error(f"❌ Usuario {user_id} no tiene acceso a acquisition {acquisition_id}")
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to access this acquisition"
            )

        # 3. Retornar solo resultados que ya tengan aplicada la máscara científica.
        existing_ndvi = await crud_ndvi.get_ndvi_by_acquisition(db, acquisition_id)
        if existing_ndvi and existing_ndvi.cloud_mask_applied:
            logger.info(f"✅ NDVI enmascarado ya existe (id={existing_ndvi.id})")
            return self._format_response(existing_ndvi, acquisition_date=acquisition.acquisition_date)

        if not acquisition.scl_data:
            raise HTTPException(
                status_code=409,
                detail="SCL mask not available. Acquire the date again before calculating NDVI."
            )

        logger.info(f"📊 Adquisición válida: polygon_id={acquisition.polygon_id}, date={acquisition.acquisition_date}")

        # 4. Leer bandas desde BD y calcular NDVI
        try:
            ndvi_array, invalid_mask, profile, analysis_valid_percentage = await self._read_and_calculate_ndvi(
                acquisition.b04_data,
                acquisition.b08_data,
                acquisition.scl_data,
                {"type": "Polygon", "coordinates": [polygon.coordinates]},
            )
        except Exception as e:
            logger.error(f"❌ Error calculando NDVI: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error calculating NDVI: {str(e)}")

        # 5. Calcular estadísticos
        stats = self._calculate_statistics(
            ndvi_array,
            invalid_mask,
            acquisition.b04_data,
            acquisition.b08_data,
        )
        logger.info(f"📈 Estadísticos NDVI: mean={stats['ndvi_mean']:.4f}, min={stats['ndvi_min']:.4f}, max={stats['ndvi_max']:.4f}")

        # 6. Convertir NDVI a TIFF bytes
        ndvi_tiff = self._ndvi_to_tiff(ndvi_array, profile)
        logger.info(f"💾 NDVI TIFF generado: {len(ndvi_tiff)} bytes")

        # 7. Guardar en BD
        if existing_ndvi:
            ndvi_result = await crud_ndvi.replace_ndvi_result_with_masked(
                db=db,
                ndvi_result=existing_ndvi,
                ndvi_tiff=ndvi_tiff,
                stats=stats,
                width=acquisition.width,
                height=acquisition.height,
                analysis_valid_pixel_percentage=analysis_valid_percentage,
            )
        else:
            ndvi_result = await crud_ndvi.save_ndvi_result(
                db=db,
                acquisition_id=acquisition_id,
                polygon_id=acquisition.polygon_id,
                ndvi_tiff=ndvi_tiff,
                stats=stats,
                width=acquisition.width,
                height=acquisition.height,
                analysis_valid_pixel_percentage=analysis_valid_percentage,
                cloud_mask_applied=True,
            )

        logger.info(f"✅ NDVI guardado exitosamente (id={ndvi_result.id})")
        return self._format_response(ndvi_result, acquisition_date=acquisition.acquisition_date)

    async def _read_and_calculate_ndvi(
        self,
        b04_bytes: bytes,
        b08_bytes: bytes,
        scl_bytes: bytes,
        polygon_geojson: Dict,
    ) -> tuple[np.ndarray, np.ndarray, Dict, float]:
        """
        Lee bandas B04 y B08 desde bytes TIFF y calcula NDVI.

        Args:
            b04_bytes: Banda Red en formato TIFF
            b08_bytes: Banda NIR en formato TIFF

        Returns:
            tuple: (ndvi_array, nodata_mask, profile)
        """
        # Leer B04 (Red)
        with rasterio.open(io.BytesIO(b04_bytes)) as src:
            b04_array = src.read(1)
            nodata_b04 = src.nodata
            profile = src.profile.copy()
            transform = src.transform
            crs = src.crs

        # Leer B08 (NIR)
        with rasterio.open(io.BytesIO(b08_bytes)) as src:
            b08_array = src.read(1)
            nodata_b08 = src.nodata

        # Verificar dimensiones
        if b04_array.shape != b08_array.shape:
            raise ValueError(
                f"Band dimensions mismatch: B04={b04_array.shape}, B08={b08_array.shape}"
            )

        logger.debug(f"📐 Dimensiones: {b04_array.shape}, dtype: {b04_array.dtype}")

        # Crear máscara base de píxeles nodata/no finitos.
        invalid_mask = ~np.isfinite(b04_array) | ~np.isfinite(b08_array)
        if nodata_b04 is not None:
            invalid_mask |= (b04_array == nodata_b04)
        if nodata_b08 is not None:
            invalid_mask |= (b08_array == nodata_b08)

        if crs is None:
            raise ValueError("B04 raster has no CRS; polygon/SCL mask cannot be aligned")

        polygon_in_raster_crs = transform_geom("EPSG:4326", crs, polygon_geojson)
        outside_polygon = geometry_mask(
            [polygon_in_raster_crs],
            out_shape=b04_array.shape,
            transform=transform,
            invert=False,
        )
        parcel_pixels = int(np.count_nonzero(~outside_polygon))
        if parcel_pixels == 0:
            raise ValueError("Polygon does not intersect the B04/B08 raster")
        invalid_mask |= outside_polygon

        # Reproyectar SCL/dataMask a la grilla de 10 m de B04/B08 usando vecino
        # más próximo: las clases categóricas nunca deben interpolarse.
        with rasterio.open(io.BytesIO(scl_bytes)) as src:
            if src.count < 2:
                raise ValueError("SCL TIFF must contain SCL and dataMask bands")
            if src.crs is None:
                raise ValueError("SCL raster has no CRS")
            scl_source = src.read(1)
            data_mask_source = src.read(2)
            scl = np.zeros_like(b04_array, dtype=np.uint8)
            data_mask = np.zeros_like(b04_array, dtype=np.uint8)
            reproject(
                source=scl_source,
                destination=scl,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=transform,
                dst_crs=crs,
                resampling=Resampling.nearest,
                src_nodata=0,
                dst_nodata=0,
            )
            reproject(
                source=data_mask_source,
                destination=data_mask,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=transform,
                dst_crs=crs,
                resampling=Resampling.nearest,
                src_nodata=0,
                dst_nodata=0,
            )

        invalid_mask |= data_mask == 0
        invalid_mask |= scl == 0
        invalid_mask |= np.isin(scl, (3, 8, 9, 10))

        # Convertir a float32
        b04 = b04_array.astype(np.float32)
        b08 = b08_array.astype(np.float32)

        # NO aplicar factor de escala: Process API ya retorna reflectancia 0.0-1.0

        logger.debug(f"🔢 Rangos reflectancia: B04=[{b04.min():.4f}, {b04.max():.4f}], B08=[{b08.min():.4f}, {b08.max():.4f}]")

        # Calcular NDVI con manejo de división por cero
        denominator = b08 + b04
        invalid_mask |= denominator == 0
        ndvi = np.full(b04.shape, np.nan, dtype=np.float32)
        np.divide(
            b08 - b04,
            denominator,
            out=ndvi,
            where=~invalid_mask,
        )

        # Validar rango [-1, 1] (excluyendo NaN)
        valid_ndvi = ndvi[~np.isnan(ndvi)]
        if len(valid_ndvi) > 0:
            if valid_ndvi.min() < -1 or valid_ndvi.max() > 1:
                raise ValueError(
                    f"NDVI out of range: [{valid_ndvi.min():.4f}, {valid_ndvi.max():.4f}]. "
                    "Expected [-1, 1]"
                )

        # Actualizar profile para NDVI (float32, 1 banda, compresión LZW)
        profile.update(
            dtype=rasterio.float32,
            count=1,
            compress='lzw',
            transform=transform,
            crs=crs,
            nodata=np.nan,
        )

        valid_inside_parcel = int(np.count_nonzero(~invalid_mask & ~outside_polygon))
        analysis_valid_percentage = round(
            100.0 * valid_inside_parcel / parcel_pixels,
            2,
        )
        return ndvi, invalid_mask, profile, analysis_valid_percentage

    def _calculate_statistics(
        self,
        ndvi: np.ndarray,
        invalid_mask: np.ndarray,
        b04_bytes: bytes,
        b08_bytes: bytes
    ) -> Dict[str, float]:
        """
        Calcula estadísticos NDVI sobre píxeles válidos.

        ndvi_mean se calcula como NDVI(mean(B04), mean(B08)):
        - Método validado contra Copernicus Browser (diff 3.5%)
        - Coincide con metodología oficial de Copernicus
        - Documentado en OE2_PARA_REPORTE_WORD.md

        ndvi_std, ndvi_min, ndvi_max se calculan sobre el
        array NDVI pixel-wise filtrado por valid_mask.

        Args:
            ndvi: Array NDVI pixel-wise (puede contener NaN)
            invalid_mask: Máscara combinada de nodata, geometría, nubes y sombras
            b04_bytes: Banda Red en formato TIFF (para calcular mean correcto)
            b08_bytes: Banda NIR en formato TIFF (para calcular mean correcto)

        Returns:
            Dict con: ndvi_mean, ndvi_min, ndvi_max, ndvi_std

        Raises:
            ValueError: Si no hay píxeles válidos
        """
        # Máscara de píxeles válidos (no NaN, dentro de [-1, 1], no nodata)
        valid_mask = ~np.isnan(ndvi) & (ndvi >= -1) & (ndvi <= 1) & ~invalid_mask
        valid_pixels = ndvi[valid_mask]

        if len(valid_pixels) == 0:
            raise ValueError("No valid pixels to calculate NDVI statistics")

        logger.debug(
            f"📊 Píxeles válidos: {len(valid_pixels)} / {ndvi.size} "
            f"({100*len(valid_pixels)/ndvi.size:.1f}%)"
        )

        # ndvi_mean: NDVI de reflectancias medias (metodología Copernicus)
        with rasterio.open(io.BytesIO(b04_bytes)) as src:
            b04_array = src.read(1).astype(np.float32)
        with rasterio.open(io.BytesIO(b08_bytes)) as src:
            b08_array = src.read(1).astype(np.float32)

        b04_mean = b04_array[valid_mask].mean()
        b08_mean = b08_array[valid_mask].mean()
        mean_denominator = b08_mean + b04_mean
        if mean_denominator == 0:
            raise ValueError("Mean reflectance denominator is zero")

        return {
            "ndvi_mean": float((b08_mean - b04_mean) / mean_denominator),
            "ndvi_min": float(np.min(valid_pixels)),
            "ndvi_max": float(np.max(valid_pixels)),
            "ndvi_std": float(np.std(valid_pixels)),
            "ndvi_median": float(np.median(valid_pixels)),
            "ndvi_p10": float(np.percentile(valid_pixels, 10)),
            "ndvi_p90": float(np.percentile(valid_pixels, 90)),
        }

    def _ndvi_to_tiff(self, ndvi: np.ndarray, profile: Dict) -> bytes:
        """
        Convierte array NDVI a TIFF bytes con compresión LZW.

        Args:
            ndvi: Array NDVI float32
            profile: Perfil rasterio con metadatos

        Returns:
            bytes: TIFF comprimido
        """
        buf = io.BytesIO()
        with rasterio.open(buf, 'w', **profile) as dst:
            dst.write(ndvi.astype(np.float32), 1)

        return buf.getvalue()

    def _format_response(self, ndvi_result, acquisition_date: str = None) -> Dict[str, Any]:
        """
        Formatea el resultado NDVI para respuesta de API.

        Args:
            ndvi_result: Objeto NDVIResult de la BD
            acquisition_date: Fecha de adquisición (YYYY-MM-DD o date object)

        Returns:
            Dict con datos formateados
        """
        # Convertir acquisition_date a string si es date object
        if acquisition_date and hasattr(acquisition_date, 'isoformat'):
            acquisition_date_str = acquisition_date.isoformat()
        elif acquisition_date:
            acquisition_date_str = str(acquisition_date)
        else:
            acquisition_date_str = "unknown"

        return {
            "ndvi_id": ndvi_result.id,
            "acquisition_id": ndvi_result.acquisition_id,
            "polygon_id": ndvi_result.polygon_id,
            "calculation_date": ndvi_result.calculation_date.isoformat(),
            "acquisition_date": acquisition_date_str,  # En raíz para el endpoint
            "stats": {
                # Solo datos estadísticos NDVI, NO IDs ni fechas
                # (el endpoint los pasa explícitamente)
                "ndvi_mean": ndvi_result.ndvi_mean,
                "ndvi_min": ndvi_result.ndvi_min,
                "ndvi_max": ndvi_result.ndvi_max,
                "ndvi_std": ndvi_result.ndvi_std,
                "ndvi_median": ndvi_result.ndvi_median,
                "ndvi_p10": ndvi_result.ndvi_p10,
                "ndvi_p90": ndvi_result.ndvi_p90,
                "width": ndvi_result.width,
                "height": ndvi_result.height,
                "analysis_valid_pixel_percentage": ndvi_result.analysis_valid_pixel_percentage,
                "cloud_mask_applied": ndvi_result.cloud_mask_applied,
            }
        }

    async def get_ndvi_stats(
        self,
        acquisition_id: int,
        user_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticos NDVI si ya fueron calculados.

        Args:
            acquisition_id: ID de la adquisición
            user_id: ID del usuario (para verificar ownership)
            db: Sesión async de BD

        Returns:
            Dict con estadísticos si existe, None si no

        Raises:
            HTTPException 403: Si no tiene acceso
            HTTPException 404: Si no existe NDVI
        """
        from app.crud.acquisition import get_acquisition_by_id

        ndvi_result = await crud_ndvi.get_ndvi_by_acquisition(db, acquisition_id)
        if not ndvi_result:
            raise HTTPException(status_code=404, detail="NDVI not calculated yet")

        # Verificar ownership
        polygon = await crud_polygon.get_polygon_by_id(db, ndvi_result.polygon_id)
        if not polygon or polygon.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Obtener acquisition_date de la adquisición
        acquisition = await get_acquisition_by_id(db, acquisition_id)
        acquisition_date = acquisition.acquisition_date if acquisition else "unknown"

        response = self._format_response(ndvi_result, acquisition_date=acquisition_date)
        response["acquisition_date"] = acquisition_date
        return response

    async def get_ndvi_tiff(
        self,
        acquisition_id: int,
        user_id: int,
        db: AsyncSession
    ) -> bytes:
        """
        Obtiene el raster NDVI como TIFF bytes para descarga.

        Args:
            acquisition_id: ID de la adquisición
            user_id: ID del usuario (para verificar ownership)
            db: Sesión async de BD

        Returns:
            bytes: TIFF NDVI

        Raises:
            HTTPException 403: Si no tiene acceso
            HTTPException 404: Si no existe NDVI
        """
        ndvi_result = await crud_ndvi.get_ndvi_by_acquisition(db, acquisition_id)
        if not ndvi_result:
            raise HTTPException(status_code=404, detail="NDVI not calculated yet")

        # Verificar ownership
        polygon = await crud_polygon.get_polygon_by_id(db, ndvi_result.polygon_id)
        if not polygon or polygon.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        return ndvi_result.ndvi_tiff
