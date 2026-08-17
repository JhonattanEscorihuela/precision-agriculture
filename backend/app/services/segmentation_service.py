"""
OE3 - Servicio de segmentación espacial de zonas cultivadas.
Aplica umbralización sobre raster NDVI para identificar áreas cultivadas.
"""

import io
import logging
import numpy as np
import rasterio
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.crud import ndvi as crud_ndvi
from app.crud import segmentation as crud_segmentation
from app.crud import polygon as crud_polygon
from app.crud import acquisition as crud_acquisition

logger = logging.getLogger(__name__)


class SegmentationService:
    """
    Servicio para segmentar zonas cultivadas mediante umbralización NDVI.

    Workflow:
    1. Lee raster NDVI desde BD (ndvi_tiff)
    2. Aplica umbral (threshold): píxeles con NDVI > threshold = cultivado
    3. Calcula métricas: total_pixels, cultivated_pixels, percentage
    4. Genera máscara binaria opcional (uint8: 0/1)
    5. Guarda resultado en BD

    Idempotente: si ya existe segmentación para el NDVI, retorna sin recalcular.
    """

    # Umbral NDVI por defecto (0.3 = vegetación moderada)
    # Ref: Valores típicos cultivos tropicales 0.3-0.8
    DEFAULT_THRESHOLD = 0.3

    async def calculate_segmentation(
        self,
        ndvi_result_id: int,
        user_id: int,
        db: AsyncSession,
        threshold: Optional[float] = None,
        save_mask: bool = False
    ) -> Dict[str, Any]:
        """
        Calcula segmentación de zonas cultivadas sobre un resultado NDVI.

        Workflow:
        1. Validar threshold en [0, 1]
        2. Verificar si ya existe segmentación (idempotencia)
        3. Obtener NDVI result y verificar ownership
        4. Leer raster NDVI desde BD
        5. Aplicar umbralización
        6. Calcular métricas de área cultivada
        7. Generar máscara binaria (si save_mask=True)
        8. Guardar en BD

        Args:
            ndvi_result_id: ID del resultado NDVI
            user_id: ID del usuario (ownership)
            db: Sesión async BD
            threshold: Umbral NDVI (default 0.3)
            save_mask: Si True, guarda máscara binaria TIFF uint8

        Returns:
            Dict con: id, ndvi_result_id, acquisition_id, polygon_id, threshold_used,
                     total_pixels, cultivated_pixels, cultivated_percentage,
                     calculation_date, tiff_binary_mask, has_binary_mask

        Raises:
            HTTPException 404: Si ndvi_result_id no existe
            HTTPException 403: Si usuario no tiene acceso
            ValueError: Si threshold fuera de rango [0, 1]
        """
        # Usar threshold por defecto si no se especifica
        if threshold is None:
            threshold = self.DEFAULT_THRESHOLD

        logger.info(f"🌾 Iniciando segmentación para ndvi_result_id={ndvi_result_id}, threshold={threshold}")

        # 1. Validar threshold en [0, 1]
        if not (0 <= threshold <= 1):
            logger.error(f"❌ Threshold fuera de rango: {threshold}")
            raise ValueError(f"Threshold must be in range [0, 1], got {threshold}")

        # 2. Obtener NDVIResult
        ndvi_result = await crud_ndvi.get_ndvi_by_id(db, ndvi_result_id)
        if not ndvi_result:
            logger.error(f"❌ NDVIResult {ndvi_result_id} no encontrado")
            raise HTTPException(status_code=404, detail="NDVI result not found")

        # 3. Verificar ownership antes de retornar resultados existentes.
        polygon = await crud_polygon.get_polygon_by_id(db, ndvi_result.polygon_id)
        if not polygon or polygon.user_id != user_id:
            logger.error(f"❌ Usuario {user_id} no tiene acceso a ndvi_result {ndvi_result_id}")
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to access this NDVI result"
            )

        # 4. Solo un NDVI SCL-enmascarado de una observación apta puede alimentar OE3.
        acquisition = await crud_acquisition.get_acquisition_by_id(
            db,
            ndvi_result.acquisition_id,
        )
        if not ndvi_result.cloud_mask_applied:
            raise HTTPException(
                status_code=409,
                detail="NDVI must be recalculated with the SCL cloud mask before OE3.",
            )
        if not acquisition or acquisition.quality_status != "suitable":
            quality = acquisition.quality_status if acquisition else "unknown"
            raise HTTPException(
                status_code=409,
                detail=f"Observation quality is {quality}; OE3 requires suitable quality.",
            )

        # 5. Verificar idempotencia después de seguridad y calidad.
        existing_segmentation = await crud_segmentation.get_by_ndvi_result_id(db, ndvi_result_id)
        if existing_segmentation:
            logger.info(f"✅ Segmentación ya existe (id={existing_segmentation.id}), retornando sin recalcular")
            return self._format_response(existing_segmentation)

        logger.info(f"📊 NDVI válido: polygon_id={ndvi_result.polygon_id}, acquisition_id={ndvi_result.acquisition_id}")

        # 6. Leer NDVI y aplicar segmentación
        try:
            ndvi_array, cultivated_mask, total_pixels, cultivated_pixels, percentage, profile = \
                self._read_and_segment_ndvi(ndvi_result.ndvi_tiff, threshold)
        except Exception as e:
            logger.error(f"❌ Error en segmentación: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error calculating segmentation: {str(e)}")

        logger.info(f"📈 Métricas: {cultivated_pixels}/{total_pixels} píxeles ({percentage:.2f}%)")

        # 6. Generar máscara TIFF si se solicita
        binary_mask_bytes = None
        if save_mask:
            try:
                binary_mask_bytes = self._mask_to_tiff(
                    cultivated_mask,
                    profile,
                    valid_mask=~np.isnan(ndvi_array),
                )
                logger.info(f"💾 Máscara TIFF generada: {len(binary_mask_bytes)} bytes")
            except Exception as e:
                logger.error(f"❌ Error generando máscara TIFF: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error generating mask: {str(e)}")

        # 7. Guardar en BD
        segmentation_result = await crud_segmentation.create(
            db=db,
            ndvi_result_id=ndvi_result_id,
            polygon_id=ndvi_result.polygon_id,
            threshold_used=threshold,
            total_pixels=total_pixels,
            cultivated_pixels=cultivated_pixels,
            cultivated_percentage=percentage,
            binary_mask=binary_mask_bytes
        )

        logger.info(f"✅ Segmentación guardada exitosamente (id={segmentation_result.id})")

        # 8. Retornar respuesta
        return self._format_response(segmentation_result)

    def _read_and_segment_ndvi(
        self,
        ndvi_tiff_bytes: bytes,
        threshold: float
    ) -> tuple[np.ndarray, np.ndarray, int, int, float, Dict]:
        """
        Lee NDVI TIFF y aplica umbralización.

        Args:
            ndvi_tiff_bytes: TIFF NDVI (bytes)
            threshold: Umbral NDVI

        Returns:
            tuple: (ndvi_array, cultivated_mask, total_pixels, cultivated_pixels, percentage, profile)

        Raises:
            ValueError: Si no hay píxeles válidos
        """
        # Leer NDVI TIFF
        with rasterio.open(io.BytesIO(ndvi_tiff_bytes)) as src:
            ndvi_array = src.read(1)  # float32
            profile = src.profile.copy()

        logger.debug(f"📐 Dimensiones NDVI: {ndvi_array.shape}, dtype: {ndvi_array.dtype}")

        # Máscara de píxeles válidos (no NaN)
        valid_mask = ~np.isnan(ndvi_array)
        total_pixels = int(valid_mask.sum())

        if total_pixels == 0:
            raise ValueError("No valid pixels found in NDVI raster")

        # Aplicar umbralización: cultivado si NDVI > threshold
        cultivated_mask = (ndvi_array > threshold) & valid_mask
        cultivated_pixels = int(cultivated_mask.sum())

        # Calcular porcentaje
        percentage = (cultivated_pixels / total_pixels * 100.0) if total_pixels > 0 else 0.0

        logger.debug(f"🔢 Umbralización: {cultivated_pixels}/{total_pixels} píxeles cultivados ({percentage:.2f}%)")

        return ndvi_array, cultivated_mask, total_pixels, cultivated_pixels, percentage, profile

    def _mask_to_tiff(
        self,
        mask: np.ndarray,
        profile: Dict,
        valid_mask: Optional[np.ndarray] = None,
    ) -> bytes:
        """
        Convierte máscara binaria (bool) a TIFF uint8.

        Args:
            mask: Array booleano (True=cultivado, False=no cultivado)
            profile: Perfil rasterio
            valid_mask: Píxeles con NDVI válido; los demás se escriben como 255

        Returns:
            bytes: TIFF uint8 LZW (0=no cultivado, 1=cultivado, 255=nodata)
        """
        # 0=no cultivado, 1=cultivado y 255=fuera de parcela/sin dato.
        if valid_mask is None:
            valid_mask = np.ones(mask.shape, dtype=bool)
        mask_uint8 = np.full(mask.shape, 255, dtype=np.uint8)
        mask_uint8[valid_mask] = mask[valid_mask].astype(np.uint8)

        # Actualizar profile para uint8
        profile.update(
            dtype=rasterio.uint8,
            count=1,
            compress='lzw',
            nodata=255,
        )

        # Escribir a bytes
        buf = io.BytesIO()
        with rasterio.open(buf, 'w', **profile) as dst:
            dst.write(mask_uint8, 1)

        return buf.getvalue()

    def _format_response(self, segmentation_result) -> Dict[str, Any]:
        """
        Formatea resultado de segmentación para respuesta API.

        El contrato expone "ndvi_result_id" y conserva "acquisition_id" como
        alias compatible para clientes existentes.

        Args:
            segmentation_result: Objeto SegmentationResult de la BD

        Returns:
            Dict con campos del contrato API
        """
        return {
            "id": segmentation_result.id,
            "ndvi_result_id": segmentation_result.ndvi_result_id,
            "acquisition_id": segmentation_result.ndvi_result_id,  # Alias compatible
            "polygon_id": segmentation_result.polygon_id,
            "calculation_date": segmentation_result.calculation_date.isoformat(),
            "threshold_used": segmentation_result.threshold_used,
            "total_pixels": segmentation_result.total_pixels,
            "cultivated_pixels": segmentation_result.cultivated_pixels,
            "cultivated_percentage": segmentation_result.cultivated_percentage,
            "tiff_binary_mask": None,  # null en respuesta regular
            "has_binary_mask": segmentation_result.binary_mask is not None  # indica si está disponible para descarga
        }

    async def get_segmentation_by_ndvi(
        self,
        ndvi_result_id: int,
        user_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Obtiene segmentación ya calculada para un NDVI.

        Args:
            ndvi_result_id: ID del resultado NDVI
            user_id: ID del usuario (ownership)
            db: Sesión async BD

        Returns:
            Dict con datos de segmentación

        Raises:
            HTTPException 404: Si no existe segmentación
            HTTPException 403: Si no tiene acceso
        """
        segmentation_result = await crud_segmentation.get_by_ndvi_result_id(db, ndvi_result_id)
        if not segmentation_result:
            raise HTTPException(status_code=404, detail="Segmentation not calculated yet")

        # Verificar ownership
        polygon = await crud_polygon.get_polygon_by_id(db, segmentation_result.polygon_id)
        if not polygon or polygon.user_id != user_id:
            logger.error(f"❌ Usuario {user_id} no tiene acceso a segmentación {segmentation_result.id}")
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to access this segmentation"
            )

        return self._format_response(segmentation_result)

    async def get_segmentation_mask(
        self,
        segmentation_id: int,
        user_id: int,
        db: AsyncSession
    ) -> bytes:
        """
        Obtiene máscara binaria TIFF para descarga.

        Args:
            segmentation_id: ID del resultado de segmentación
            user_id: ID del usuario (ownership)
            db: Sesión async BD

        Returns:
            bytes: TIFF uint8 de máscara binaria

        Raises:
            HTTPException 404: Si no existe segmentación o no tiene máscara guardada
            HTTPException 403: Si no tiene acceso
        """
        segmentation_result = await crud_segmentation.get_by_id(db, segmentation_id)
        if not segmentation_result:
            raise HTTPException(status_code=404, detail="Segmentation not found")

        # Verificar ownership
        polygon = await crud_polygon.get_polygon_by_id(db, segmentation_result.polygon_id)
        if not polygon or polygon.user_id != user_id:
            logger.error(f"❌ Usuario {user_id} no tiene acceso a segmentación {segmentation_id}")
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to access this segmentation"
            )

        # Verificar que la máscara fue guardada
        if segmentation_result.binary_mask is None:
            raise HTTPException(
                status_code=404,
                detail="Binary mask was not saved for this segmentation. Use save_mask=true when calculating."
            )

        return segmentation_result.binary_mask
