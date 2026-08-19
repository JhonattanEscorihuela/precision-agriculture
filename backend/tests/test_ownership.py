"""Regression tests for polygon ownership authorization."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.core.ownership import require_owned_polygon


@pytest.mark.asyncio
async def test_require_owned_polygon_returns_owner_resource():
    db = AsyncMock()
    polygon = SimpleNamespace(id=7, user_id=3)

    with patch(
        "app.core.ownership.get_polygon_by_id",
        new=AsyncMock(return_value=polygon),
    ):
        result = await require_owned_polygon(db, polygon_id=7, user_id=3)

    assert result is polygon


@pytest.mark.asyncio
async def test_require_owned_polygon_rejects_other_user():
    db = AsyncMock()
    polygon = SimpleNamespace(id=7, user_id=9)

    with patch(
        "app.core.ownership.get_polygon_by_id",
        new=AsyncMock(return_value=polygon),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await require_owned_polygon(db, polygon_id=7, user_id=3)

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_owned_polygon_returns_404_for_missing_resource():
    db = AsyncMock()

    with patch(
        "app.core.ownership.get_polygon_by_id",
        new=AsyncMock(return_value=None),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await require_owned_polygon(db, polygon_id=404, user_id=3)

    assert exc_info.value.status_code == 404
