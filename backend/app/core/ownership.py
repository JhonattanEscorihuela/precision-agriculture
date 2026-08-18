"""Centralized authorization helpers for resources owned by a user."""

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.polygon import get_polygon_by_id
from app.models.polygon import Polygon


async def require_owned_polygon(
    db: AsyncSession,
    polygon_id: int,
    user_id: int,
) -> Polygon:
    """Return a polygon only when it exists and belongs to ``user_id``."""
    polygon = await get_polygon_by_id(db, polygon_id)
    if not polygon:
        raise HTTPException(status_code=404, detail="Polygon not found")

    if polygon.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to access this polygon",
        )

    return polygon
