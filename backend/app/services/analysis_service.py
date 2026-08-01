"""
Servicio orquestador para análisis completo por parcela.
Ejecuta NDVI → Segmentación → Textura sobre todas las fechas disponibles.
"""

import logging
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.crud import ndvi as crud_ndvi
from app.crud import polygon as crud_polygon
from app.services.segmentation_service import SegmentationService
from app.services.texture_service import TextureService

logger = logging.getLogger(__name__)


class AnalysisService:
    """
    Servicio orquestador para análisis completo de parcelas.

    Orquesta el pipeline NDVI → Segmentación → Textura sobre todas las fechas
    disponibles de una parcela, agregando resultados por kernel.

    Composición: instancia SegmentationService y TextureService (no herencia).
    """

    # Threshold FIJO para segmentación (0.3 = vegetación moderada)
    DEFAULT_THRESHOLD = 0.30

    def __init__(self):
        """Inicializa servicios por composición."""
        self.segmentation_service = SegmentationService()
        self.texture_service = TextureService()

    async def run_full_analysis(
        self,
        polygon_id: int,
        user_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Ejecuta análisis completo (segmentación + textura) sobre todas las fechas NDVI de una parcela.

        Workflow:
        1. Verificar polygon existe y pertenece al usuario
        2. Obtener todos los NDVIResult del polygon
        3. Para cada fecha:
           - Calcular segmentación (threshold=0.30)
           - Calcular textura (3 descriptores)
           - Acumular resultados por fecha
           - Si error: acumular en dates_failed y continuar
        4. Agregar por kernel (edges, homogeneity, contrast):
           - mean_std_normalized: promedio de std_normalized
           - dates_discriminative: count de discriminative=True
        5. Identificar kernel más discriminativo

        Args:
            polygon_id: ID del polígono a analizar
            user_id: ID del usuario (ownership)
            db: Sesión async BD

        Returns:
            Dict con:
            - polygon_id, total_ndvi_results, dates_processed, dates_failed
            - per_date_results: lista de resultados por fecha
            - aggregated: métricas agregadas por kernel + most_discriminative_kernel

        Raises:
            HTTPException 404: Si polygon no existe
            HTTPException 403: Si usuario no tiene acceso
            HTTPException 400: Si no hay NDVIResults calculados
        """
        logger.info(f"🚀 Iniciando análisis completo para polygon_id={polygon_id}")

        # 1. Verificar polygon existe y pertenece al usuario
        polygon = await crud_polygon.get_polygon_by_id(db, polygon_id)
        if not polygon:
            logger.error(f"❌ Polygon {polygon_id} no encontrado")
            raise HTTPException(status_code=404, detail="Polygon not found")

        if polygon.user_id != user_id:
            logger.error(f"❌ Usuario {user_id} no tiene acceso a polygon {polygon_id}")
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to access this polygon"
            )

        # 2. Obtener TODOS los NDVIResult del polygon
        ndvi_results_with_dates = await crud_ndvi.get_ndvi_by_polygon(db, polygon_id)

        if not ndvi_results_with_dates:
            logger.error(f"❌ No hay NDVIResults para polygon {polygon_id}")
            raise HTTPException(
                status_code=400,
                detail="No NDVI results found for this polygon. Calculate NDVI first."
            )

        total_ndvi_results = len(ndvi_results_with_dates)
        logger.info(f"📊 Encontrados {total_ndvi_results} NDVIResults para análisis")

        # 3. Procesar cada fecha (loop con try/except para continuar en error)
        per_date_results = []
        dates_failed = []

        # Acumuladores para agregación por kernel
        kernel_data = {
            "edges": {"std_normalized_sum": 0.0, "discriminative_count": 0, "total_count": 0},
            "homogeneity": {"std_normalized_sum": 0.0, "discriminative_count": 0, "total_count": 0},
            "contrast": {"std_normalized_sum": 0.0, "discriminative_count": 0, "total_count": 0}
        }

        for ndvi_result, acquisition_date in ndvi_results_with_dates:
            try:
                logger.info(f"📅 Procesando NDVI {ndvi_result.id} (fecha: {acquisition_date})")

                # 3a. Calcular segmentación (idempotente)
                segmentation_result = await self.segmentation_service.calculate_segmentation(
                    ndvi_result_id=ndvi_result.id,
                    user_id=user_id,
                    db=db,
                    threshold=self.DEFAULT_THRESHOLD,
                    save_mask=False  # No guardar máscara TIFF (solo métricas)
                )

                segmentation_id = segmentation_result["id"]
                logger.debug(f"   ✅ Segmentación {segmentation_id}: {segmentation_result['cultivated_percentage']:.2f}% cultivado")

                # 3b. Calcular textura (3 descriptores, idempotente)
                texture_descriptors = await self.texture_service.calculate_texture(
                    segmentation_result_id=segmentation_id,
                    user_id=user_id,
                    db=db
                )

                logger.debug(f"   ✅ Textura: {len(texture_descriptors)} descriptores calculados")

                # Organizar descriptores por kernel_type
                texture_by_kernel = {
                    "edges": None,
                    "homogeneity": None,
                    "contrast": None
                }

                for desc in texture_descriptors:
                    kernel_type = desc["kernel_type"]
                    texture_by_kernel[kernel_type] = {
                        "std_normalized": desc["std_normalized"],
                        "discriminative": desc["discriminative"]
                    }

                    # Acumular para agregación
                    kernel_data[kernel_type]["std_normalized_sum"] += desc["std_normalized"]
                    kernel_data[kernel_type]["total_count"] += 1
                    if desc["discriminative"]:
                        kernel_data[kernel_type]["discriminative_count"] += 1

                # 3c. Acumular resultado por fecha
                per_date_results.append({
                    "ndvi_result_id": ndvi_result.id,
                    "acquisition_date": acquisition_date,  # Ya es string desde BD
                    "ndvi_mean": ndvi_result.ndvi_mean,
                    "cultivated_percentage": segmentation_result["cultivated_percentage"],
                    "texture": texture_by_kernel
                })

                logger.info(f"   ✅ Fecha procesada exitosamente")

            except Exception as e:
                # Acumular error y CONTINUAR con siguiente fecha
                error_msg = str(e)
                logger.warning(f"   ⚠️  Error procesando NDVI {ndvi_result.id}: {error_msg}")
                dates_failed.append({
                    "ndvi_result_id": ndvi_result.id,
                    "error": error_msg
                })

        dates_processed = len(per_date_results)
        logger.info(f"📈 Procesamiento completado: {dates_processed}/{total_ndvi_results} exitosas, {len(dates_failed)} fallidas")

        # 4. AGREGAR por kernel
        aggregated = {}
        for kernel_type in ["edges", "homogeneity", "contrast"]:
            data = kernel_data[kernel_type]
            total = data["total_count"]

            if total > 0:
                mean_std_normalized = data["std_normalized_sum"] / total
            else:
                mean_std_normalized = 0.0

            aggregated[kernel_type] = {
                "mean_std_normalized": mean_std_normalized,
                "dates_discriminative": data["discriminative_count"]
            }

        # 5. Identificar kernel más discriminativo (mayor mean_std_normalized)
        most_discriminative_kernel = max(
            aggregated.keys(),
            key=lambda k: aggregated[k]["mean_std_normalized"]
        )

        logger.info(f"🏆 Kernel más discriminativo: {most_discriminative_kernel} "
                   f"(mean_std_norm={aggregated[most_discriminative_kernel]['mean_std_normalized']:.4f})")

        # 6. Retornar resultado completo
        return {
            "polygon_id": polygon_id,
            "total_ndvi_results": total_ndvi_results,
            "dates_processed": dates_processed,
            "dates_failed": dates_failed,
            "per_date_results": per_date_results,
            "aggregated": {
                **aggregated,
                "most_discriminative_kernel": most_discriminative_kernel
            }
        }
