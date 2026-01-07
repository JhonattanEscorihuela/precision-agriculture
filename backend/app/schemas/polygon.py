from pydantic import BaseModel
from typing import List

# Esquema para crear polígonos (entrada)
class PolygonCreate(BaseModel):
    name: str
    coordinates: List[List[float]]

# Esquema para actualizar polígonos (entrada)
class PolygonUpdate(BaseModel):
    name: str

# Esquema de respuesta (salida)
class PolygonResponse(BaseModel):
    id: int
    name: str
    coordinates: List[List[float]]