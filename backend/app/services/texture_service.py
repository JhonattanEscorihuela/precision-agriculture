"""
OE4 - Servicio de análisis de textura mediante filtrado convolucional.
Implementación estricta de docs/metodologia_textura_OE4.md v2.1
"""

import io
import logging
import numpy as np
import rasterio
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from scipy.ndimage import convolve, binary_erosion

from app.crud import texture as crud_texture
from app.crud import segmentation as crud_segmentation
from app.crud import ndvi as crud_ndvi
from app.crud import polygon as crud_polygon

logger = logging.getLogger(__name__)


class TextureService:
    """
    Servicio para calcular descriptores de textura mediante filtros convolucionales.

    Implementa la metodología científica de docs/metodologia_textura_OE4.md:
    - 3 operadores: Laplaciano (edges), Varianza local (homogeneity), Magnitud gradiente (contrast)
    - Convolución sobre NDVI completo (no sobre máscara binaria)
    - Erosión morfológica de 1 píxel para evitar contaminación de bordes
    - Normalización min-max + criterio discriminativo (std_normalized > 0.10)
    """

    # Constante según Sección 4.3
    DEFAULT_DISCRIMINATIVE_THRESHOLD = 0.10  # τ_norm

    # Kernels según Secciones 3.1, 3.2, 3.3
    KERNEL_EDGES = np.array([
        [0,  1,  0],
        [1, -4,  1],
        [0,  1,  0]
    ], dtype=np.float32)

    KERNEL_MEAN = np.ones((3, 3), dtype=np.float32) / 9.0

    KERNEL_GX = np.array([
        [-1, 0, 1],
        [-2, 0, 2],
        [-1, 0, 1]
    ], dtype=np.float32)

    KERNEL_GY = np.array([
        [-1, -2, -1],
        [ 0,  0,  0],
        [ 1,  2,  1]
    ], dtype=np.float32)

    async def calculate_texture(
        self,
        segmentation_result_id: int,
        user_id: int,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Calcula los 3 descriptores de textura sobre una segmentación.

        Workflow (según metodología OE4):
        1. Idempotencia: verificar si ya existen los 3 descriptores
        2. Obtener SegmentationResult y verificar ownership
        3. Leer NDVI TIFF
        4. Regenerar máscara cultivada (reusar threshold de segmentación)
        5. Reemplazar NaN con 0.0 (evitar propagación en convolución)
        6. Erosión morfológica de 1 píxel
        7. Aplicar 3 operadores convolucionales
        8. Guardar 3 descriptores en BD (transacción atómica)

        Args:
            segmentation_result_id: ID del resultado de segmentación
            user_id: ID del usuario (ownership)
            db: Sesión async BD

        Returns:
            Lista de 3 Dict con descriptores (edges, homogeneity, contrast)

        Raises:
            HTTPException 404: Si segmentation/ndvi/polygon no existe
            HTTPException 403: Si usuario no tiene acceso
            ValueError: Si área cultivada muy pequeña tras erosión
        """
        logger.info(f"🌾 Iniciando análisis de textura para segmentation_id={segmentation_result_id}")

        # 1. IDEMPOTENCIA
        existing = await crud_texture.get_by_segmentation_result_id(db, segmentation_result_id)
        if len(existing) == 3:
            logger.info(f"✅ Descriptores ya existen (3/3), retornando sin recalcular")
            return [self._format_response(d) for d in existing]

        # 2. OBTENER SegmentationResult
        segmentation = await crud_segmentation.get_by_id(db, segmentation_result_id)
        if not segmentation:
            logger.error(f"❌ SegmentationResult {segmentation_result_id} no encontrado")
            raise HTTPException(status_code=404, detail="Segmentation not found")

        # 3. OWNERSHIP CHECK
        polygon = await crud_polygon.get_polygon_by_id(db, segmentation.polygon_id)
        if not polygon or polygon.user_id != user_id:
            logger.error(f"❌ Usuario {user_id} no tiene acceso a segmentation {segmentation_result_id}")
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to access this segmentation"
            )

        # 4. OBTENER NDVIResult
        ndvi_result = await crud_ndvi.get_ndvi_by_id(db, segmentation.ndvi_result_id)
        if not ndvi_result:
            logger.error(f"❌ NDVIResult {segmentation.ndvi_result_id} no encontrado")
            raise HTTPException(status_code=404, detail="NDVI result not found")

        logger.info(f"📊 Segmentación válida: polygon_id={segmentation.polygon_id}, threshold={segmentation.threshold_used}")

        # 5. LEER RASTER NDVI (Sección 4.1 - convolución sobre NDVI completo)
        with rasterio.open(io.BytesIO(ndvi_result.ndvi_tiff)) as src:
            ndvi_array = src.read(1)  # float32, rango [-1, 1]
            profile = src.profile.copy()

        logger.debug(f"📐 Dimensiones NDVI: {ndvi_array.shape}, dtype: {ndvi_array.dtype}")

        # 6. REGENERAR MÁSCARA CULTIVADA (reusar threshold de segmentación)
        valid_mask = ~np.isnan(ndvi_array)
        threshold = segmentation.threshold_used  # NO recalculamos
        cultivated_mask = (ndvi_array > threshold) & valid_mask

        logger.debug(f"🔢 Píxeles cultivados: {cultivated_mask.sum()}")

        # 7. MANEJO DE NaN (Sección decisión 'a')
        ndvi_clean = np.nan_to_num(ndvi_array, nan=0.0)

        # 8. EROSIÓN MORFOLÓGICA (Sección 4.2 - 1 píxel, estructura 3×3)
        structure = np.ones((3, 3), dtype=bool)
        eroded_mask = binary_erosion(cultivated_mask, structure=structure)

        if eroded_mask.sum() == 0:
            logger.error(f"❌ Área cultivada demasiado pequeña tras erosión")
            raise ValueError("Cultivated area too small after erosion (need >9 pixels)")

        logger.info(f"📈 Píxeles tras erosión: {eroded_mask.sum()} (pérdida: {cultivated_mask.sum() - eroded_mask.sum()})")

        # 9. CALCULAR 3 DESCRIPTORES
        try:
            result_edges = self._apply_edges(ndvi_clean, eroded_mask)
            result_homogeneity = self._apply_homogeneity(ndvi_clean, eroded_mask)
            result_contrast = self._apply_contrast(ndvi_clean, eroded_mask)
        except Exception as e:
            logger.error(f"❌ Error en cálculo de descriptores: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error calculating texture descriptors: {str(e)}")

        logger.info(f"📊 Descriptores calculados:")
        logger.info(f"   Edges: mean={result_edges['mean']:.4f}, std_norm={result_edges['std_normalized']:.4f}, disc={result_edges['discriminative']}")
        logger.info(f"   Homogeneity: mean={result_homogeneity['mean']:.4f}, std_norm={result_homogeneity['std_normalized']:.4f}, disc={result_homogeneity['discriminative']}")
        logger.info(f"   Contrast: mean={result_contrast['mean']:.4f}, std_norm={result_contrast['std_normalized']:.4f}, disc={result_contrast['discriminative']}")

        # 10. GUARDAR EN BD (transacción atómica - 3 descriptores en 1 commit)
        try:
            desc_edges = await crud_texture.create(
                db, segmentation_result_id, segmentation.polygon_id,
                kernel_type="edges",
                auto_commit=False,  # NO commit intermedio
                **result_edges
            )
            desc_homogeneity = await crud_texture.create(
                db, segmentation_result_id, segmentation.polygon_id,
                kernel_type="homogeneity",
                auto_commit=False,  # NO commit intermedio
                **result_homogeneity
            )
            desc_contrast = await crud_texture.create(
                db, segmentation_result_id, segmentation.polygon_id,
                kernel_type="contrast",
                auto_commit=False,  # NO commit intermedio
                **result_contrast
            )

            # COMMIT ÚNICO (atomicidad)
            await db.commit()

            # Refresh para obtener IDs asignados
            await db.refresh(desc_edges)
            await db.refresh(desc_homogeneity)
            await db.refresh(desc_contrast)

            logger.info(f"✅ Descriptores guardados: IDs={desc_edges.id}, {desc_homogeneity.id}, {desc_contrast.id}")

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Error guardando descriptores: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error saving texture descriptors: {str(e)}")

        # 11. RETORNAR lista de 3 descriptores formateados
        return [
            self._format_response(desc_edges),
            self._format_response(desc_homogeneity),
            self._format_response(desc_contrast)
        ]

    def _apply_edges(
        self,
        ndvi_array: np.ndarray,
        eroded_mask: np.ndarray
    ) -> Dict[str, Any]:
        """
        Operador Laplaciano (Sección 3.1).

        Detecta transiciones abruptas en NDVI mediante segunda derivada discreta.

        Args:
            ndvi_array: Raster NDVI (NaN reemplazados con 0)
            eroded_mask: Máscara booleana de zona válida tras erosión

        Returns:
            Dict con: mean, std, min_val, max_val, std_normalized, discriminative
        """
        # Convolución (modo reflect - Sección decisión 'b')
        response = convolve(ndvi_array, self.KERNEL_EDGES, mode='reflect')

        # Extraer respuestas válidas
        valid_responses = response[eroded_mask]

        # Calcular estadísticos
        stats = self._calculate_statistics(valid_responses)

        # Normalizar y evaluar discriminativo
        norm_result = self._normalize_and_discriminate(valid_responses)

        return {**stats, **norm_result}

    def _apply_homogeneity(
        self,
        ndvi_array: np.ndarray,
        eroded_mask: np.ndarray
    ) -> Dict[str, Any]:
        """
        Operador Varianza Local (Sección 3.2).

        Calcula varianza local: Var = E[I²] - (E[I])²

        Args:
            ndvi_array: Raster NDVI (NaN reemplazados con 0)
            eroded_mask: Máscara booleana de zona válida tras erosión

        Returns:
            Dict con: mean, std, min_val, max_val, std_normalized, discriminative
        """
        # Paso 1: Elevar NDVI al cuadrado
        ndvi_squared = ndvi_array ** 2

        # Paso 2: Media local de NDVI
        mean_ndvi = convolve(ndvi_array, self.KERNEL_MEAN, mode='reflect')

        # Paso 3: Media local de NDVI²
        mean_ndvi_squared = convolve(ndvi_squared, self.KERNEL_MEAN, mode='reflect')

        # Paso 4: Varianza local
        variance_local = mean_ndvi_squared - (mean_ndvi ** 2)

        # CLIP de varianza (ajuste #3 - evitar negativos por redondeo)
        variance_local = np.maximum(variance_local, 0.0)

        # Extraer respuestas válidas
        valid_responses = variance_local[eroded_mask]

        # Calcular estadísticos y normalizar
        stats = self._calculate_statistics(valid_responses)
        norm_result = self._normalize_and_discriminate(valid_responses)

        return {**stats, **norm_result}

    def _apply_contrast(
        self,
        ndvi_array: np.ndarray,
        eroded_mask: np.ndarray
    ) -> Dict[str, Any]:
        """
        Operador Magnitud del Gradiente (Sección 3.3).

        Calcula magnitud: G = √(Gx² + Gy²)

        Args:
            ndvi_array: Raster NDVI (NaN reemplazados con 0)
            eroded_mask: Máscara booleana de zona válida tras erosión

        Returns:
            Dict con: mean, std, min_val, max_val, std_normalized, discriminative
        """
        # Paso 1: Gradiente horizontal
        gradient_x = convolve(ndvi_array, self.KERNEL_GX, mode='reflect')

        # Paso 2: Gradiente vertical
        gradient_y = convolve(ndvi_array, self.KERNEL_GY, mode='reflect')

        # Paso 3: Magnitud del gradiente (norma euclidiana)
        gradient_magnitude = np.sqrt(gradient_x**2 + gradient_y**2)

        # Extraer respuestas válidas
        valid_responses = gradient_magnitude[eroded_mask]

        # Calcular estadísticos y normalizar
        stats = self._calculate_statistics(valid_responses)
        norm_result = self._normalize_and_discriminate(valid_responses)

        return {**stats, **norm_result}

    def _calculate_statistics(
        self,
        responses: np.ndarray
    ) -> Dict[str, float]:
        """
        Calcula estadísticos sobre respuestas originales (NO normalizadas).

        Args:
            responses: Array de respuestas del kernel

        Returns:
            Dict con: mean, std, min_val, max_val
        """
        return {
            "mean": float(responses.mean()),
            "std": float(responses.std()),
            "min_val": float(responses.min()),
            "max_val": float(responses.max())
        }

    def _normalize_and_discriminate(
        self,
        responses: np.ndarray,
        threshold: float = None
    ) -> Dict[str, Any]:
        """
        Normalización min-max + criterio discriminativo (Sección 4.3).

        Args:
            responses: Array de respuestas del kernel
            threshold: Umbral discriminativo (default: 0.10)

        Returns:
            Dict con: std_normalized, discriminative
        """
        if threshold is None:
            threshold = self.DEFAULT_DISCRIMINATIVE_THRESHOLD

        r_min = responses.min()
        r_max = responses.max()

        # Caso: respuesta constante
        if r_max == r_min:
            logger.debug(f"⚠️  Respuesta constante (rango=0) → discriminative=False")
            return {
                "std_normalized": 0.0,
                "discriminative": False
            }

        # Normalización min-max a [0, 1]
        responses_norm = (responses - r_min) / (r_max - r_min)

        # Desviación estándar sobre respuestas normalizadas
        std_norm = float(responses_norm.std())

        # Criterio discriminativo
        discriminative = (std_norm > threshold)

        logger.debug(f"🔢 Normalización: rango=[{r_min:.4f}, {r_max:.4f}], std_norm={std_norm:.4f}, disc={discriminative}")

        return {
            "std_normalized": std_norm,
            "discriminative": discriminative
        }

    def _format_response(
        self,
        descriptor: Any
    ) -> Dict[str, Any]:
        """
        Formatea descriptor para respuesta API.

        Args:
            descriptor: Objeto TextureDescriptor de la BD

        Returns:
            Dict con campos del contrato API
        """
        return {
            "id": descriptor.id,
            "segmentation_result_id": descriptor.segmentation_result_id,
            "polygon_id": descriptor.polygon_id,
            "kernel_type": descriptor.kernel_type,
            "mean": descriptor.mean,
            "std": descriptor.std,
            "min_val": descriptor.min_val,
            "max_val": descriptor.max_val,
            "std_normalized": descriptor.std_normalized,
            "discriminative": descriptor.discriminative,
            "calculation_date": descriptor.calculation_date.isoformat()
        }

    async def get_descriptors_by_segmentation(
        self,
        segmentation_result_id: int,
        user_id: int,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Obtiene descriptores ya calculados para una segmentación.

        Verifica ownership antes de retornar.

        Args:
            segmentation_result_id: ID del resultado de segmentación
            user_id: ID del usuario (ownership)
            db: Sesión async BD

        Returns:
            Lista de Dict con descriptores

        Raises:
            HTTPException 404: Si segmentación no existe o no tiene descriptores calculados
            HTTPException 403: Si no tiene acceso
        """
        # 1. Obtener SegmentationResult
        segmentation = await crud_segmentation.get_by_id(db, segmentation_result_id)
        if not segmentation:
            raise HTTPException(status_code=404, detail="Segmentation not found")

        # 2. Ownership check
        polygon = await crud_polygon.get_polygon_by_id(db, segmentation.polygon_id)
        if not polygon or polygon.user_id != user_id:
            logger.error(f"❌ Usuario {user_id} no tiene acceso a descriptores de segmentation {segmentation_result_id}")
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to access these texture descriptors"
            )

        # 3. Obtener descriptores
        descriptors = await crud_texture.get_by_segmentation_result_id(db, segmentation_result_id)

        # 4. Si lista vacía → 404
        if not descriptors:
            raise HTTPException(
                status_code=404,
                detail="Texture descriptors not calculated yet for this segmentation"
            )

        # 5. Retornar formateados
        return [self._format_response(d) for d in descriptors]
