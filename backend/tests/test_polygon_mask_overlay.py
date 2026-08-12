"""
Test para verificar que los overlays (NDVI y textura) recortan correctamente
a la forma del polígono usando geometry_mask de rasterio.
"""

import numpy as np
import io
from PIL import Image
import rasterio
from rasterio.transform import from_bounds

from app.services.ndvi_overlay_service import generate_ndvi_overlay
from app.services.texture_overlay_service import generate_texture_overlay


def create_synthetic_ndvi_tiff(polygon_coords: list) -> bytes:
    """
    Crea un TIFF NDVI sintético para testing.

    Args:
        polygon_coords: Coordenadas del polígono [[lng, lat], ...]

    Returns:
        Bytes del TIFF NDVI
    """
    # Extraer bounds del polígono
    lngs = [coord[0] for coord in polygon_coords]
    lats = [coord[1] for coord in polygon_coords]

    west, east = min(lngs), max(lngs)
    south, north = min(lats), max(lats)

    # Crear array 100x100 con valores NDVI sintéticos
    # Mitad superior: NDVI alto (verde) = 0.7
    # Mitad inferior: NDVI bajo (rojo) = 0.2
    height, width = 100, 100
    ndvi = np.ones((height, width), dtype=np.float32)
    ndvi[:50, :] = 0.7  # Mitad superior verde
    ndvi[50:, :] = 0.2  # Mitad inferior roja

    # Crear transform georreferenciado
    transform = from_bounds(west, south, east, north, width, height)

    # Escribir a TIFF en memoria
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


def test_ndvi_overlay_with_polygon_mask():
    """
    Verifica que generate_ndvi_overlay solo colorea píxeles DENTRO del polígono.
    """
    # Polígono de test (TRIÁNGULO para que haya esquinas fuera)
    polygon_coords = [
        [-67.52, 8.84],   # Esquina inferior izquierda
        [-67.51, 8.84],   # Esquina inferior derecha
        [-67.515, 8.85],  # Punta superior (centro)
        [-67.52, 8.84]    # Cierre
    ]

    polygon_geojson = {
        "type": "Polygon",
        "coordinates": [polygon_coords]
    }

    # Crear TIFF sintético
    ndvi_tiff_bytes = create_synthetic_ndvi_tiff(polygon_coords)

    # Generar overlay CON máscara
    png_bytes, leaflet_bounds = generate_ndvi_overlay(ndvi_tiff_bytes, polygon_geojson)

    # Verificaciones básicas
    assert len(png_bytes) > 0, "PNG debe tener contenido"
    assert len(leaflet_bounds) == 2, "Bounds debe ser [[south, west], [north, east]]"

    # Abrir PNG y verificar que tiene transparencia
    img = Image.open(io.BytesIO(png_bytes))
    assert img.mode == 'RGBA', "PNG debe ser RGBA (con canal alpha)"

    # Convertir a array para análisis
    rgba = np.array(img)

    # Verificar que hay píxeles transparentes (alpha=0)
    # Si la máscara funciona, los píxeles fuera del polígono deben ser transparentes
    alpha_channel = rgba[:, :, 3]
    transparent_pixels = np.sum(alpha_channel == 0)
    opaque_pixels = np.sum(alpha_channel > 0)

    # En un polígono que NO es el bounding box completo, debe haber transparencias
    # (las esquinas del rectángulo están fuera del polígono)
    assert transparent_pixels > 0, "Debe haber píxeles transparentes fuera del polígono"
    assert opaque_pixels > 0, "Debe haber píxeles coloreados dentro del polígono"

    # Verificar que hay colores NDVI aplicados (verde/amarillo/rojo)
    # Verde = [22, 163, 74], Rojo = [220, 38, 38]
    green_pixels = np.sum((rgba[:, :, 0] == 22) & (rgba[:, :, 1] == 163) & (rgba[:, :, 2] == 74))
    red_pixels = np.sum((rgba[:, :, 0] == 220) & (rgba[:, :, 1] == 38) & (rgba[:, :, 2] == 38))

    assert green_pixels > 0, "Debe haber píxeles verdes (NDVI alto)"
    assert red_pixels > 0, "Debe haber píxeles rojos (NDVI bajo)"

    print(f"✅ Overlay NDVI con máscara: {transparent_pixels} transparentes, "
          f"{opaque_pixels} coloreados ({green_pixels} verdes, {red_pixels} rojos)")


def test_texture_overlay_with_polygon_mask():
    """
    Verifica que generate_texture_overlay solo colorea píxeles DENTRO del polígono.
    """
    # Polígono de test (TRIÁNGULO para que haya esquinas fuera)
    polygon_coords = [
        [-67.52, 8.84],   # Esquina inferior izquierda
        [-67.51, 8.84],   # Esquina inferior derecha
        [-67.515, 8.85],  # Punta superior (centro)
        [-67.52, 8.84]    # Cierre
    ]

    polygon_geojson = {
        "type": "Polygon",
        "coordinates": [polygon_coords]
    }

    # Crear TIFF sintético
    ndvi_tiff_bytes = create_synthetic_ndvi_tiff(polygon_coords)

    # Generar overlay de textura CON máscara
    png_bytes, leaflet_bounds, interpretation = generate_texture_overlay(
        ndvi_tiff_bytes, "contrast", polygon_geojson
    )

    # Verificaciones básicas
    assert len(png_bytes) > 0, "PNG debe tener contenido"
    assert len(leaflet_bounds) == 2, "Bounds debe ser [[south, west], [north, east]]"
    assert len(interpretation) > 0, "Debe retornar interpretación textual"

    # Abrir PNG y verificar transparencia
    img = Image.open(io.BytesIO(png_bytes))
    assert img.mode == 'RGBA', "PNG debe ser RGBA"

    rgba = np.array(img)
    alpha_channel = rgba[:, :, 3]
    transparent_pixels = np.sum(alpha_channel == 0)
    opaque_pixels = np.sum(alpha_channel > 0)

    assert transparent_pixels > 0, "Debe haber píxeles transparentes fuera del polígono"
    assert opaque_pixels > 0, "Debe haber píxeles coloreados dentro del polígono"

    # Verificar que hay colores de textura aplicados (azul/púrpura/naranja)
    # Azul = [59, 130, 246], Púrpura = [139, 92, 246], Naranja = [249, 115, 22]
    blue_pixels = np.sum((rgba[:, :, 0] == 59) & (rgba[:, :, 1] == 130) & (rgba[:, :, 2] == 246))
    purple_pixels = np.sum((rgba[:, :, 0] == 139) & (rgba[:, :, 1] == 92) & (rgba[:, :, 2] == 246))
    orange_pixels = np.sum((rgba[:, :, 0] == 249) & (rgba[:, :, 1] == 115) & (rgba[:, :, 2] == 22))

    colored_pixels = blue_pixels + purple_pixels + orange_pixels
    assert colored_pixels > 0, "Debe haber píxeles con colores de textura"

    print(f"✅ Overlay textura con máscara: {transparent_pixels} transparentes, "
          f"{opaque_pixels} coloreados ({colored_pixels} con colores de textura)")


if __name__ == "__main__":
    test_ndvi_overlay_with_polygon_mask()
    test_texture_overlay_with_polygon_mask()
    print("\n✅ Todos los tests de máscara de polígono pasaron correctamente")
