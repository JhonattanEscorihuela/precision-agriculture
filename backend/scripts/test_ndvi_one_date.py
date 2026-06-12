"""Test directo cálculo NDVI para una fecha."""
import asyncio
import io
import sys
import numpy as np
import rasterio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.sentinel.sentinel_service import SentinelService

PARCELA_211 = [
    [-67.528058, 8.8441233],
    [-67.5153475, 8.8386166],
    [-67.5103962, 8.8478932],
    [-67.522828, 8.8534209],
    [-67.528058, 8.8441233]
]

async def test():
    sentinel = SentinelService()
    date = "2026-03-22"

    print(f"\n{'='*80}")
    print(f"TEST NDVI DIRECTO - {date}")
    print(f"{'='*80}\n")

    # Download bands
    print("📥 Descargando B04...")
    b04_bytes = await sentinel.download_bands(
        polygon_geojson={"type": "Polygon", "coordinates": [PARCELA_211]},
        bands=["B04"],
        start_date=date,
        end_date=date,
        width=512,
        height=512,
        max_cloud_coverage=20
    )
    print(f"   ✅ {len(b04_bytes)} bytes")

    print("📥 Descargando B08...")
    b08_bytes = await sentinel.download_bands(
        polygon_geojson={"type": "Polygon", "coordinates": [PARCELA_211]},
        bands=["B08"],
        start_date=date,
        end_date=date,
        width=512,
        height=512,
        max_cloud_coverage=20
    )
    print(f"   ✅ {len(b08_bytes)} bytes\n")

    # Read arrays
    with rasterio.open(io.BytesIO(b04_bytes)) as src:
        b04 = src.read(1).astype(np.float32)
        nodata_b04 = src.nodata

    with rasterio.open(io.BytesIO(b08_bytes)) as src:
        b08 = src.read(1).astype(np.float32)
        nodata_b08 = src.nodata

    # Mask nodata
    nodata_mask = np.zeros_like(b04, dtype=bool)
    if nodata_b04 is not None:
        nodata_mask |= (b04 == nodata_b04)
    if nodata_b08 is not None:
        nodata_mask |= (b08 == nodata_b08)

    print("📊 VALORES CRUDOS:")
    print(f"   B04 dtype: {b04.dtype}")
    print(f"   B04 range: [{b04.min():.6f}, {b04.max():.6f}]")
    print(f"   B04 mean (all pixels): {b04.mean():.6f}")
    print(f"   B04 mean (valid): {b04[~nodata_mask].mean():.6f}")
    print()
    print(f"   B08 dtype: {b08.dtype}")
    print(f"   B08 range: [{b08.min():.6f}, {b08.max():.6f}]")
    print(f"   B08 mean (all pixels): {b08.mean():.6f}")
    print(f"   B08 mean (valid): {b08[~nodata_mask].mean():.6f}")
    print()

    # Calculate NDVI (NO SCALE)
    denominator = b08 + b04
    ndvi = np.where(denominator == 0, 0.0, (b08 - b04) / denominator)
    ndvi = np.where(nodata_mask, np.nan, ndvi)

    valid_mask = ~np.isnan(ndvi) & (ndvi >= -1) & (ndvi <= 1)
    valid_ndvi = ndvi[valid_mask]

    print("🧮 CÁLCULO NDVI (sin scale factor):")
    print(f"   Píxeles válidos: {len(valid_ndvi)} / {ndvi.size}")
    print(f"   NDVI mean: {valid_ndvi.mean():.4f}")
    print(f"   NDVI min: {valid_ndvi.min():.4f}")
    print(f"   NDVI max: {valid_ndvi.max():.4f}")
    print()

    # Manual check con means
    b04_mean = b04[~nodata_mask].mean()
    b08_mean = b08[~nodata_mask].mean()
    manual_ndvi = (b08_mean - b04_mean) / (b08_mean + b04_mean)

    print("✋ VERIFICACIÓN MANUAL (usando means):")
    print(f"   ({b08_mean:.6f} - {b04_mean:.6f}) / ({b08_mean:.6f} + {b04_mean:.6f})")
    print(f"   = {manual_ndvi:.4f}")
    print()

    print("📋 COMPARACIÓN:")
    print(f"   NDVI calculado (mean de array): {valid_ndvi.mean():.4f}")
    print(f"   NDVI manual (mean de means):    {manual_ndvi:.4f}")
    print(f"   Copernicus CSV reference:       0.8535")
    print(f"   Diferencia vs Copernicus:       {abs(valid_ndvi.mean() - 0.8535):.4f}")
    print()
    print(f"{'='*80}\n")

if __name__ == "__main__":
    asyncio.run(test())
