from pydantic import BaseModel
from typing import List, Optional

# Esquema para crear polígonos (entrada)
class PolygonCreate(BaseModel):
    name: str
    coordinates: List[List[float]]

# Esquema para actualizar polígonos (entrada)
class PolygonUpdate(BaseModel):
    name: Optional[str]  # El nombre no es obligatorio en la actualización
    coordinates: Optional[List[List[float]]]  # Las coordenadas también son opcionales

# Esquema de respuesta (salida)
class PolygonResponse(BaseModel):
    id: int
    name: str
    coordinates: List[List[float]]
    area: float  # Área calculada
    created_at: str  # Fecha de creación en ISO8601
    updated_at: str  # Última actualización en ISO8601