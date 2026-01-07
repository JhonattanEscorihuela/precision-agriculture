from fastapi import APIRouter, HTTPException
from app.schemas.polygon import PolygonCreate, PolygonUpdate, PolygonResponse
from typing import List

router = APIRouter()

# Simulación de almacenamiento temporal
polygons_db = []

# Crear un nuevo polígono
@router.post("/", response_model=PolygonResponse, status_code=201)
def create_polygon(polygon: PolygonCreate):
    new_polygon = polygon.dict()
    new_polygon["id"] = len(polygons_db) + 1  # Simulación de ID único
    polygons_db.append(new_polygon)
    return new_polygon

# Leer todos los polígonos
@router.get("/", response_model=List[PolygonResponse], status_code=200)
def get_all_polygons():
    return polygons_db

# Actualizar polígonos
@router.put("/{polygon_id}", response_model=PolygonResponse)
def update_polygon(polygon_id: int, polygon: PolygonUpdate):
    for stored_polygon in polygons_db:
        if stored_polygon["id"] == polygon_id:
            stored_polygon.update(polygon.dict())
            return stored_polygon
    raise HTTPException(status_code=404, detail="Polygon not found")

# Eliminar polígonos
@router.delete("/{polygon_id}", status_code=204)
def delete_polygon(polygon_id: int):
    global polygons_db
    polygons_db = [p for p in polygons_db if p["id"] != polygon_id]
    return