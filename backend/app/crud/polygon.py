from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models.polygon import Polygon

# Crear un nuevo polígono
async def create_polygon(db: AsyncSession, polygon: Polygon) -> Polygon:
    db.add(polygon)
    await db.commit()
    await db.refresh(polygon)
    return polygon

# Leer todos los polígonos
async def get_polygons(db: AsyncSession):
    result = await db.execute(select(Polygon))
    return result.scalars().all()

# Actualizar un polígono existente
async def update_polygon(db: AsyncSession, polygon_id: int, polygon_data: dict):
    query = select(Polygon).where(Polygon.id == polygon_id)
    result = await db.execute(query)
    polygon = result.scalar_one_or_none()

    if not polygon:
        return None

    # Actualizar campos
    for key, value in polygon_data.items():
        setattr(polygon, key, value)

    await db.commit()
    await db.refresh(polygon)
    return polygon

# Eliminar un polígono
async def delete_polygon(db: AsyncSession, polygon_id: int):
    query = select(Polygon).where(Polygon.id == polygon_id)
    result = await db.execute(query)
    polygon = result.scalar_one_or_none()

    if not polygon:
        return False

    await db.delete(polygon)
    await db.commit()
    return True