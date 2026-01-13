from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.polygon import PolygonCreate, PolygonUpdate, PolygonResponse
from app.models.polygon import Polygon
from app.crud.polygon import create_polygon, get_polygons, update_polygon, delete_polygon
from app.database import get_session
from datetime import datetime
from app.services.polygons_logic import calculate_polygon_area
from typing import List

router = APIRouter()

# Crear un nuevo polígono
@router.post("/", response_model=PolygonResponse, status_code=201)
async def create_polygon_endpoint(
    polygon: PolygonCreate,
    db: AsyncSession = Depends(get_session)
):
    # Calculamos el área del polígono
    area = calculate_polygon_area(polygon.coordinates)

    new_polygon = Polygon(
        name=polygon.name,
        coordinates=polygon.coordinates,
        area=area,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )

    return await create_polygon(db, new_polygon)

# Leer todos los polígonos
@router.get("/", response_model=List[PolygonResponse])
async def get_all_polygons_endpoint(db: AsyncSession = Depends(get_session)):
    return await get_polygons(db)

# Actualizar polígonos
@router.put("/{polygon_id}", response_model=PolygonResponse)
async def update_polygon_endpoint(
    polygon_id: int,
    polygon: PolygonUpdate,
    db: AsyncSession = Depends(get_session)
):
    # Buscar el polígono en la base de datos
    updated_polygon = await update_polygon(db, polygon_id, polygon.dict(exclude_unset=True))

    if not updated_polygon:
        raise HTTPException(status_code=404, detail="Polygon not found")

    # Si se actualizan las coordenadas, recalculamos el área
    if polygon.coordinates:
        updated_polygon.coordinates = polygon.coordinates
        updated_polygon.area = calculate_polygon_area(polygon.coordinates)
        updated_polygon.updated_at = datetime.now().isoformat()

        # Guardamos los cambios actualizados
        db.add(updated_polygon)
        await db.commit()
        await db.refresh(updated_polygon)

    return updated_polygon

# Eliminar polígonos
@router.delete("/{polygon_id}", status_code=204)
async def delete_polygon_endpoint(polygon_id: int, db: AsyncSession = Depends(get_session)):
    deleted = await delete_polygon(db, polygon_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Polygon not found")
    return