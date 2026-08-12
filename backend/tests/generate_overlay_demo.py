"""
Script de demostración: genera overlays NDVI y textura con máscara de polígono
y los guarda como archivos PNG para inspección visual.
"""

import sys
sys.path.insert(0, '/app')

import numpy as np
import io
from PIL import Image
import rasterio
from rasterio.transform import from_bounds
import base64

from app.services.ndvi_overlay_service import generate_ndvi_overlay
from app.services.texture_overlay_service import generate_texture_overlay


def create_demo_ndvi_tiff(polygon_coords: list) -> bytes:
    """
    Crea un TIFF NDVI con patrón de prueba.
    Patrón: gradiente radial desde el centro del polígono.
    """
    lngs = [coord[0] for coord in polygon_coords]
    lats = [coord[1] for coord in polygon_coords]

    west, east = min(lngs), max(lngs)
    south, north = min(lats), max(lats)

    height, width = 200, 200
    transform = from_bounds(west, south, east, north, width, height)

    # Crear gradiente radial
    y, x = np.ogrid[:height, :width]
    center_y, center_x = height // 2, width // 2
    distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
    max_distance = np.sqrt(center_x**2 + center_y**2)

    # Normalizar a rango NDVI [-1, 1]
    ndvi = 0.8 - (distance / max_distance) * 1.0  # Va de 0.8 (centro) a -0.2 (bordes)

    # Escribir TIFF
    buffer = io.BytesIO()
    with rasterio.open(
        buffer,
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=np.float32,
        crs='EPSG:4326',
        transform=transform
    ) as dst:
        dst.write(ndvi, 1)

    return buffer.getvalue()


# Polígono de prueba (pentágono irregular)
polygon_coords = [
    [-67.53, 8.84],
    [-67.51, 8.84],
    [-67.50, 8.85],
    [-67.52, 8.86],
    [-67.54, 8.855],
    [-67.53, 8.84]  # Cierre
]

polygon_geojson = {
    "type": "Polygon",
    "coordinates": [polygon_coords]
}

print("Generando TIFF NDVI de demostración...")
ndvi_tiff_bytes = create_demo_ndvi_tiff(polygon_coords)
print(f"✓ TIFF NDVI creado: {len(ndvi_tiff_bytes)} bytes")

print("\nGenerando overlay NDVI con máscara de polígono...")
png_ndvi, bounds_ndvi = generate_ndvi_overlay(ndvi_tiff_bytes, polygon_geojson)
print(f"✓ Overlay NDVI: {len(png_ndvi)} bytes")
print(f"  Bounds: {bounds_ndvi}")

print("\nGenerando overlays de textura con máscara...")
for kernel in ["contrast", "edges", "homogeneity"]:
    png_texture, bounds_texture, interpretation = generate_texture_overlay(
        ndvi_tiff_bytes, kernel, polygon_geojson
    )
    print(f"✓ Overlay textura ({kernel}): {len(png_texture)} bytes")
    print(f"  Interpretación: {interpretation[:60]}...")

# Guardar NDVI overlay para inspección
with open("/tmp/overlay_ndvi_demo.png", "wb") as f:
    f.write(png_ndvi)

print("\n✅ Overlays generados exitosamente")
print("\nCARACTERÍSTICAS:")
print("- Solo los píxeles DENTRO del polígono están coloreados")
print("- Los píxeles FUERA del polígono son transparentes (alpha=0)")
print("- El PNG resultante tiene forma irregular (no rectangular)")
print(f"- Archivo guardado: /tmp/overlay_ndvi_demo.png")

# Análisis de transparencia
img = Image.open(io.BytesIO(png_ndvi))
rgba = np.array(img)
alpha = rgba[:, :, 3]
transparent = np.sum(alpha == 0)
opaque = np.sum(alpha > 0)
total = alpha.size

print(f"\nESTADÍSTICAS DEL PNG:")
print(f"- Total píxeles: {total}")
print(f"- Transparentes (fuera): {transparent} ({100*transparent/total:.1f}%)")
print(f"- Coloreados (dentro): {opaque} ({100*opaque/total:.1f}%)")
print(f"- Dimensiones: {img.size[0]}x{img.size[1]}")

# Verificar colores NDVI
green = np.sum((rgba[:, :, 0] == 22) & (rgba[:, :, 1] == 163) & (rgba[:, :, 2] == 74))
yellow = np.sum((rgba[:, :, 0] == 234) & (rgba[:, :, 1] == 179) & (rgba[:, :, 2] == 8))
red = np.sum((rgba[:, :, 0] == 220) & (rgba[:, :, 1] == 38) & (rgba[:, :, 2] == 38))

print(f"\nDISTRIBUCIÓN DE COLORES NDVI:")
print(f"- Verde (NDVI ≥ 0.5): {green} píxeles ({100*green/opaque:.1f}% del área cultivada)")
print(f"- Amarillo (0.3-0.5): {yellow} píxeles ({100*yellow/opaque:.1f}%)")
print(f"- Rojo (< 0.3): {red} píxeles ({100*red/opaque:.1f}%)")
