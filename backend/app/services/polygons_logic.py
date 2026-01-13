import math
from typing import List

def calculate_polygon_area(coordinates: List[List[float]]) -> float:
    """Calcula el área de un polígono utilizando el algoritmo de Shoelace."""
    n = len(coordinates)
    if n < 3:  # No se puede calcular área con menos de 3 puntos
        return 0.0

    # Implementación del algoritmo de Shoelace
    area = 0.0
    for i in range(n):
        x1, y1 = coordinates[i]
        x2, y2 = coordinates[(i + 1) % n]  # Puntos consecutivos
        area += x1 * y2 - x2 * y1

    return abs(area) / 2.0