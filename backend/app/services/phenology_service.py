"""
OE3 - Servicio de comparación fenológica para clasificación de cultivos.
Compara curvas NDVI temporales contra parcelas de referencia (arroz confirmado).
"""

import logging
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from scipy.stats import pearsonr

from app.crud import ndvi as crud_ndvi
from app.crud import polygon as crud_polygon

logger = logging.getLogger(__name__)


class PhenologyService:
    """
    Servicio de comparación fenológica para clasificación de cultivos.

    Compara la evolución temporal del NDVI de una parcela contra la curva
    de referencia promedio de parcelas conocidas como arroz, utilizando
    correlación de Pearson como métrica de similitud.

    Parcelas de referencia (arroz confirmado):
    - Polygon ID 1 = Parcela 211 (SRRG, período 2024-2025)
    - Polygon ID 2 = Parcela 217 (SRRG, Invierno 2024)
    - Polygon ID 3 = Parcela 85 (SRRG, período 2025-2026)
    """

    # Parcelas de referencia con arroz confirmado
    REFERENCE_POLYGON_IDS = [1, 2, 3]

    # Umbrales de clasificación (basados en correlación de Pearson)
    THRESHOLD_HIGH = 0.85      # r >= 0.85 → Alta similitud (probablemente arroz)
    THRESHOLD_MODERATE = 0.70  # 0.70 <= r < 0.85 → Similitud moderada
    # r < 0.70 → Baja similitud (probablemente NO es arroz)

    async def build_reference_curve(self, db: AsyncSession) -> Dict[str, float]:
        """
        Construye la curva fenológica de referencia del arroz.

        Promedia los valores de NDVI de las 3 parcelas de referencia
        para cada fecha de adquisición disponible. Esto genera una
        "firma fenológica" del cultivo de arroz en la región.

        Args:
            db: Sesión async de base de datos

        Returns:
            Dict[fecha_iso, ndvi_promedio] ordenado cronológicamente.
            Ejemplo:
            {
                "2026-02-12": 0.55,
                "2026-02-17": 0.58,
                ...
            }

        Algoritmo:
            1. Obtener todos los NDVI de las 3 parcelas de referencia
            2. Agrupar por fecha de adquisición
            3. Para cada fecha: calcular promedio de ndvi_mean
            4. Retornar dict ordenado por fecha

        Raises:
            HTTPException 500: Si no hay datos suficientes en referencias
        """
        logger.info("🌾 Construyendo curva fenológica de referencia del arroz")

        # Diccionario para acumular valores por fecha
        # date_str -> lista de ndvi_mean values
        date_ndvi_map: Dict[str, List[float]] = {}

        # 1. Obtener NDVI de todas las parcelas de referencia
        for polygon_id in self.REFERENCE_POLYGON_IDS:
            try:
                ndvi_results_with_dates = await crud_ndvi.get_ndvi_by_polygon(db, polygon_id)

                if not ndvi_results_with_dates:
                    logger.warning(f"⚠️  Parcela de referencia {polygon_id} sin datos NDVI")
                    continue

                logger.debug(f"   Parcela {polygon_id}: {len(ndvi_results_with_dates)} fechas")

                # 2. Acumular valores por fecha
                for ndvi_result, acquisition_date in ndvi_results_with_dates:
                    date_str = acquisition_date  # Ya es string desde BD

                    if date_str not in date_ndvi_map:
                        date_ndvi_map[date_str] = []

                    date_ndvi_map[date_str].append(ndvi_result.ndvi_mean)

            except Exception as e:
                logger.error(f"❌ Error obteniendo NDVI de parcela {polygon_id}: {str(e)}")
                continue

        # Validar que tenemos datos
        if not date_ndvi_map:
            raise HTTPException(
                status_code=500,
                detail="No NDVI data found in reference parcels. Cannot build reference curve."
            )

        # 3. Calcular promedio por fecha
        reference_curve = {}
        for date_str, ndvi_values in date_ndvi_map.items():
            mean_ndvi = sum(ndvi_values) / len(ndvi_values)
            reference_curve[date_str] = mean_ndvi

        # 4. Ordenar por fecha
        reference_curve = dict(sorted(reference_curve.items()))

        logger.info(f"✅ Curva de referencia construida: {len(reference_curve)} fechas")
        return reference_curve

    async def compare_parcel(
        self,
        polygon_id: int,
        user_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Compara la curva NDVI de una parcela contra la curva de referencia del arroz.

        Utiliza correlación de Pearson para cuantificar la similitud entre
        la evolución temporal del NDVI de la parcela y la firma fenológica
        del arroz. Valores altos de correlación (r >= 0.85) sugieren que
        la parcela corresponde a arroz.

        Args:
            polygon_id: ID de la parcela a clasificar
            user_id: ID del usuario (ownership)
            db: Sesión async de base de datos

        Returns:
            Dict con:
            - polygon_id: ID de la parcela analizada
            - reference_polygon_ids: [1, 2, 3]
            - dates_compared: Cantidad de fechas con datos en ambas curvas
            - similarity_score: Correlación de Pearson [-1, 1]
            - classification: Texto interpretativo según umbrales
            - curve_data: Lista de puntos con ndvi_parcel y ndvi_reference por fecha

        Raises:
            HTTPException 404: Si polygon no existe
            HTTPException 403: Si usuario no tiene acceso
            HTTPException 400: Si parcela es referencia, sin NDVI, o fechas insuficientes
        """
        logger.info(f"📊 Comparando parcela {polygon_id} contra referencia de arroz")

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

        # 2. Verificar que no sea una parcela de referencia
        if polygon_id in self.REFERENCE_POLYGON_IDS:
            logger.error(f"❌ Polygon {polygon_id} es una parcela de referencia")
            raise HTTPException(
                status_code=400,
                detail="Cannot compare reference parcel against itself"
            )

        # 3. Obtener NDVI de la parcela a comparar
        ndvi_results_with_dates = await crud_ndvi.get_ndvi_by_polygon(db, polygon_id)

        if not ndvi_results_with_dates:
            logger.error(f"❌ Parcela {polygon_id} sin datos NDVI")
            raise HTTPException(
                status_code=400,
                detail="No NDVI data for this parcel. Calculate NDVI first."
            )

        logger.info(f"   Parcela tiene {len(ndvi_results_with_dates)} fechas con NDVI")

        # Construir curva de la parcela
        parcel_curve = {}
        for ndvi_result, acquisition_date in ndvi_results_with_dates:
            date_str = acquisition_date  # Ya es string
            parcel_curve[date_str] = ndvi_result.ndvi_mean

        # 5. Construir curva de referencia
        reference_curve = await self.build_reference_curve(db)

        # 6. Alinear fechas: solo usar fechas comunes
        common_dates = sorted(set(parcel_curve.keys()) & set(reference_curve.keys()))

        if len(common_dates) < 5:
            logger.error(f"❌ Fechas comunes insuficientes: {len(common_dates)}")
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient common dates for comparison (need at least 5, found {len(common_dates)})"
            )

        logger.info(f"   Fechas comunes para comparación: {len(common_dates)}")

        # 7. Preparar arrays para correlación
        parcel_values = [parcel_curve[date] for date in common_dates]
        reference_values = [reference_curve[date] for date in common_dates]

        # 8. Calcular correlación de Pearson
        r, p_value = pearsonr(parcel_values, reference_values)

        logger.info(f"   Correlación de Pearson: r={r:.3f}, p={p_value:.4f}")

        # 9. Clasificar según umbrales
        classification = self._classify(r)

        logger.info(f"   Clasificación: {classification}")

        # 10. Construir curve_data para visualización
        curve_data = [
            {
                "date": date,
                "ndvi_parcel": parcel_curve[date],
                "ndvi_reference": reference_curve[date]
            }
            for date in common_dates
        ]

        # 11. Retornar resultado completo
        return {
            "polygon_id": polygon_id,
            "reference_polygon_ids": self.REFERENCE_POLYGON_IDS,
            "dates_compared": len(common_dates),
            "similarity_score": r,
            "classification": classification,
            "curve_data": curve_data
        }

    def _classify(self, r: float) -> str:
        """
        Clasifica la similitud según correlación de Pearson.

        Args:
            r: Coeficiente de correlación de Pearson [-1, 1]

        Returns:
            Texto interpretativo de la clasificación
        """
        if r >= self.THRESHOLD_HIGH:
            return "Alta similitud — probablemente arroz"
        elif r >= self.THRESHOLD_MODERATE:
            return "Similitud moderada — requiere revisión"
        else:
            return "Baja similitud — probablemente NO es arroz"
