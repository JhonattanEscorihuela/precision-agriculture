"""Unit tests for the phenology comparison service."""

import math
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.crud import ndvi as crud_ndvi
from app.crud import polygon as crud_polygon
from app.services.phenology_service import PhenologyService


def _ndvi(value: float) -> SimpleNamespace:
    return SimpleNamespace(ndvi_mean=value)


def _observations(*items: tuple[str, float]) -> list[tuple[SimpleNamespace, str]]:
    return [(_ndvi(value), acquisition_date) for acquisition_date, value in items]


def _patch_data(monkeypatch: pytest.MonkeyPatch, observations, *, owner_id: int = 7) -> None:
    async def get_polygon_by_id(_db, polygon_id: int):
        return SimpleNamespace(id=polygon_id, user_id=owner_id)

    async def get_ndvi_by_polygon(
        _db,
        _polygon_id: int,
        *,
        quality_eligible_only: bool = False,
    ):
        assert quality_eligible_only is True
        return observations

    monkeypatch.setattr(crud_polygon, "get_polygon_by_id", get_polygon_by_id)
    monkeypatch.setattr(crud_ndvi, "get_ndvi_by_polygon", get_ndvi_by_polygon)


@pytest.mark.parametrize(
    ("correlation", "expected"),
    [(0.90, True), (0.80, None), (0.60, False)],
)
def test_pattern_match_has_an_explicit_inconclusive_state(correlation, expected):
    assert PhenologyService()._matches_pattern(correlation) is expected


@pytest.mark.asyncio
async def test_polygon_id_one_with_three_dates_returns_exploratory_result(monkeypatch):
    observations = _observations(
        ("2026-05-18", 0.56),
        ("2026-06-10", 0.50),
        ("2026-07-27", 0.61),
    )
    _patch_data(monkeypatch, observations)

    result = await PhenologyService().compare_parcel(1, 7, object())

    assert result["polygon_id"] == 1
    assert result["reference_polygon_ids"] == []
    assert result["dates_compared"] == 3
    assert result["sufficient_for_classification"] is False
    assert result["similarity_score"] is None
    assert result["matches_rice_pattern"] is None
    assert len(result["curve_data"]) == 3
    assert result["curve_data"][0]["days_since_first_observation"] == 0
    assert result["warnings"]


@pytest.mark.asyncio
async def test_similar_long_series_is_classified_as_rice(monkeypatch):
    observations = _observations(
        ("2026-01-01", 0.30),
        ("2026-02-05", 0.50),
        ("2026-02-20", 0.60),
        ("2026-03-07", 0.80),
        ("2026-03-17", 0.70),
        ("2026-04-06", 0.60),
    )
    _patch_data(monkeypatch, observations)

    result = await PhenologyService().compare_parcel(42, 7, object())

    assert result["dates_compared"] == 6
    assert result["observation_span_days"] == 95
    assert result["sufficient_for_classification"] is True
    assert result["similarity_score"] is not None
    assert math.isfinite(result["similarity_score"])
    assert result["matches_rice_pattern"] is True
    assert result["similarity_score"] == pytest.approx(1.0)
    assert any("primera observaci" in warning.lower() for warning in result["warnings"])


@pytest.mark.asyncio
async def test_duplicate_dates_are_averaged(monkeypatch):
    observations = _observations(
        ("2026-01-01", 0.20),
        ("2026-01-01T18:30:00Z", 0.40),
        ("2026-02-01", 0.55),
    )
    _patch_data(monkeypatch, observations)

    result = await PhenologyService().compare_parcel(8, 7, object())

    assert result["dates_compared"] == 2
    assert [point["date"] for point in result["curve_data"]] == [
        "2026-01-01",
        "2026-02-01",
    ]
    assert result["curve_data"][0]["ndvi_parcel"] == pytest.approx(0.30)
    assert any("duplicad" in warning.lower() for warning in result["warnings"])


@pytest.mark.asyncio
async def test_constant_series_is_not_classified_and_returns_warning(monkeypatch):
    observations = _observations(
        ("2026-01-01", 0.50),
        ("2026-02-05", 0.50),
        ("2026-02-20", 0.50),
        ("2026-03-07", 0.50),
        ("2026-03-17", 0.50),
        ("2026-04-06", 0.50),
    )
    _patch_data(monkeypatch, observations)

    result = await PhenologyService().compare_parcel(9, 7, object())

    assert result["sufficient_for_classification"] is False
    assert result["similarity_score"] is None
    assert result["matches_rice_pattern"] is None
    assert any("variaci" in warning.lower() for warning in result["warnings"])


@pytest.mark.asyncio
async def test_no_ndvi_raises_400(monkeypatch):
    _patch_data(monkeypatch, [])

    with pytest.raises(HTTPException) as raised:
        await PhenologyService().compare_parcel(10, 7, object())

    assert raised.value.status_code == 400
    assert "No NDVI data" in raised.value.detail


@pytest.mark.asyncio
async def test_wrong_owner_raises_403_without_loading_ndvi(monkeypatch):
    ndvi_called = False

    async def get_polygon_by_id(_db, polygon_id: int):
        return SimpleNamespace(id=polygon_id, user_id=99)

    async def get_ndvi_by_polygon(
        _db,
        _polygon_id: int,
        *,
        quality_eligible_only: bool = False,
    ):
        nonlocal ndvi_called
        ndvi_called = True
        return []

    monkeypatch.setattr(crud_polygon, "get_polygon_by_id", get_polygon_by_id)
    monkeypatch.setattr(crud_ndvi, "get_ndvi_by_polygon", get_ndvi_by_polygon)

    with pytest.raises(HTTPException) as raised:
        await PhenologyService().compare_parcel(11, 7, object())

    assert raised.value.status_code == 403
    assert ndvi_called is False
