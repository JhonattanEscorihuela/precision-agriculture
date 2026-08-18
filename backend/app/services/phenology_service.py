"""OE3 - Comparación fenológica contra una plantilla teórica de arroz."""

import logging
import math
from datetime import date
from typing import Any, Dict, List, Optional, Sequence, Tuple

from fastapi import HTTPException
from scipy.stats import pearsonr
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import ndvi as crud_ndvi
from app.crud import polygon as crud_polygon

logger = logging.getLogger(__name__)


class PhenologyService:
    """Compara la evolución NDVI de una parcela con una plantilla de arroz."""

    RICE_REFERENCE_TEMPLATE: Sequence[Tuple[int, float]] = (
        (0, 0.30),
        (35, 0.50),
        (50, 0.60),
        (65, 0.80),
        (75, 0.70),
        (95, 0.60),
        (120, 0.50),
        (150, 0.40),
    )
    REFERENCE_SOURCE = "Plantilla teórica de arroz — Rio Grande do Sul (Brasil)"
    ALIGNMENT_METHOD = "Días desde la primera observación NDVI (aproximación)"
    MINIMUM_OBSERVATIONS = 5
    MINIMUM_SPAN_DAYS = 90
    THRESHOLD_HIGH = 0.85
    THRESHOLD_MODERATE = 0.70
    VARIANCE_EPSILON = 1e-12

    async def compare_parcel(
        self,
        polygon_id: int,
        user_id: int,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """Construye una comparación alineada por días desde la primera observación."""
        logger.info("Comparando fenología de la parcela %s", polygon_id)

        polygon = await crud_polygon.get_polygon_by_id(db, polygon_id)
        if not polygon:
            raise HTTPException(status_code=404, detail="Polygon not found")

        if polygon.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to access this polygon",
            )

        ndvi_results_with_dates = await crud_ndvi.get_ndvi_by_polygon(
            db,
            polygon_id,
            quality_eligible_only=True,
        )
        if not ndvi_results_with_dates:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No NDVI data eligible for phenology. Use suitable "
                    "acquisitions recalculated with the SCL cloud mask."
                ),
            )

        warnings: List[str] = [
            "Solo se utilizaron adquisiciones aptas con máscara SCL aplicada.",
            "El día 0 corresponde a la primera observación NDVI disponible, "
            "no a la fecha real de siembra."
        ]
        observations = self._aggregate_observations(ndvi_results_with_dates, warnings)
        if not observations:
            raise HTTPException(
                status_code=400,
                detail="No valid NDVI data for this parcel. Recalculate NDVI first.",
            )

        first_date = observations[0][0]
        curve_data = []
        for observation_date, ndvi_mean in observations:
            days_since_first = (observation_date - first_date).days
            curve_data.append(
                {
                    "date": observation_date.isoformat(),
                    "days_since_first_observation": days_since_first,
                    "ndvi_parcel": ndvi_mean,
                    "ndvi_reference": self._interpolate_reference(days_since_first),
                }
            )

        observation_span_days = curve_data[-1]["days_since_first_observation"]
        parcel_values = [point["ndvi_parcel"] for point in curve_data]
        reference_values = [point["ndvi_reference"] for point in curve_data]
        sufficient, sufficiency_warnings = self._validate_for_classification(
            parcel_values,
            reference_values,
            observation_span_days,
        )
        warnings.extend(sufficiency_warnings)

        similarity_score = None
        matches_rice_pattern = None
        if sufficient:
            correlation, _ = pearsonr(parcel_values, reference_values)
            if math.isfinite(float(correlation)):
                similarity_score = float(correlation)
                matches_rice_pattern = self._matches_pattern(similarity_score)
                classification = self._classify(similarity_score)
            else:
                sufficient = False
                warnings.append("La correlación no produjo un valor finito.")
                classification = self._exploratory_classification()
        else:
            classification = self._exploratory_classification()

        return {
            "polygon_id": polygon_id,
            "reference_polygon_ids": [],
            "dates_compared": len(curve_data),
            "similarity_score": similarity_score,
            "matches_rice_pattern": matches_rice_pattern,
            "sufficient_for_classification": sufficient,
            "observation_span_days": observation_span_days,
            "minimum_observations": self.MINIMUM_OBSERVATIONS,
            "minimum_span_days": self.MINIMUM_SPAN_DAYS,
            "reference_source": self.REFERENCE_SOURCE,
            "alignment_method": self.ALIGNMENT_METHOD,
            "classification": classification,
            "warnings": warnings,
            "curve_data": curve_data,
        }

    def _aggregate_observations(
        self,
        ndvi_results_with_dates: Sequence[Tuple[Any, Any]],
        warnings: List[str],
    ) -> List[Tuple[date, float]]:
        """Promedia resultados duplicados por fecha y descarta valores inválidos."""
        values_by_date: Dict[date, List[float]] = {}
        discarded = 0

        for ndvi_result, acquisition_date in ndvi_results_with_dates:
            try:
                parsed_date = date.fromisoformat(str(acquisition_date)[:10])
                ndvi_mean = float(ndvi_result.ndvi_mean)
            except (TypeError, ValueError):
                discarded += 1
                continue

            if not math.isfinite(ndvi_mean):
                discarded += 1
                continue

            values_by_date.setdefault(parsed_date, []).append(ndvi_mean)

        if discarded:
            warnings.append(
                f"Se descartaron {discarded} observaciones con fecha o NDVI no válido."
            )

        duplicated_dates = sum(len(values) > 1 for values in values_by_date.values())
        if duplicated_dates:
            warnings.append(
                f"Se promediaron observaciones duplicadas en {duplicated_dates} "
                "fechas de adquisición."
            )

        return [
            (observation_date, sum(values) / len(values))
            for observation_date, values in sorted(values_by_date.items())
        ]

    def _interpolate_reference(self, days_since_first: int) -> float:
        """Interpola linealmente la plantilla y mantiene sus extremos constantes."""
        if days_since_first <= self.RICE_REFERENCE_TEMPLATE[0][0]:
            return self.RICE_REFERENCE_TEMPLATE[0][1]

        for (left_day, left_ndvi), (right_day, right_ndvi) in zip(
            self.RICE_REFERENCE_TEMPLATE,
            self.RICE_REFERENCE_TEMPLATE[1:],
        ):
            if days_since_first <= right_day:
                position = (days_since_first - left_day) / (right_day - left_day)
                return left_ndvi + position * (right_ndvi - left_ndvi)

        return self.RICE_REFERENCE_TEMPLATE[-1][1]

    def _validate_for_classification(
        self,
        parcel_values: Sequence[float],
        reference_values: Sequence[float],
        observation_span_days: int,
    ) -> Tuple[bool, List[str]]:
        warnings = []

        if len(parcel_values) < self.MINIMUM_OBSERVATIONS:
            warnings.append(
                f"Se requieren al menos {self.MINIMUM_OBSERVATIONS} observaciones; "
                f"hay {len(parcel_values)}."
            )
        if observation_span_days < self.MINIMUM_SPAN_DAYS:
            warnings.append(
                f"Se requieren al menos {self.MINIMUM_SPAN_DAYS} días de cobertura; "
                f"hay {observation_span_days}."
            )
        if not all(math.isfinite(value) for value in (*parcel_values, *reference_values)):
            warnings.append("Las curvas contienen valores no finitos.")
        if self._variance(parcel_values) <= self.VARIANCE_EPSILON:
            warnings.append("La curva NDVI de la parcela no tiene variación suficiente.")
        if self._variance(reference_values) <= self.VARIANCE_EPSILON:
            warnings.append("La curva de referencia no tiene variación suficiente.")

        return not warnings, warnings

    @staticmethod
    def _variance(values: Sequence[float]) -> float:
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        return sum((value - mean) ** 2 for value in values) / len(values)

    def _classify(self, correlation: float) -> str:
        if correlation >= self.THRESHOLD_HIGH:
            return "Alta similitud — patrón fenológico compatible con arroz"
        if correlation >= self.THRESHOLD_MODERATE:
            return "Similitud moderada — resultado no concluyente"
        return "Baja similitud — patrón fenológico no compatible con arroz"

    def _matches_pattern(self, correlation: float) -> Optional[bool]:
        if correlation >= self.THRESHOLD_HIGH:
            return True
        if correlation < self.THRESHOLD_MODERATE:
            return False
        return None

    def _exploratory_classification(self) -> str:
        return (
            "Comparación exploratoria — aún no hay cobertura temporal suficiente "
            "para clasificar el patrón fenológico."
        )
