from sqlmodel import SQLModel, Field
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import Column
from typing import List

class PolygonBase(SQLModel):
    name: str
    # Cambiamos la definición del campo para que sea correctamente mapeado a JSON
    coordinates: List[List[float]] = Field(sa_column=Column(JSON))

class Polygon(PolygonBase, table=True):  # Esto define una tabla en la base de datos SQL
    id: int = Field(default=None, primary_key=True)
    area: float
    created_at: str
    updated_at: str