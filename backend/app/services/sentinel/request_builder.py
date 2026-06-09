"""
Módulo constructor de payloads para Process API.
Responsabilidad: Generar evalscripts y request payloads.
"""

from typing import Dict, List


def build_bands_evalscript(bands: List[str]) -> str:
    """
    Construye evalscript para descarga de bandas específicas.

    Args:
        bands: Lista de bandas (ej: ["B04", "B08"])

    Returns:
        str: Evalscript de Sentinel Hub
    """
    bands_str = '", "'.join(bands)
    bands_output = ", ".join([f"sample.{band}" for band in bands])

    return f"""
//VERSION=3
function setup() {{
  return {{
    input: ["{bands_str}"],
    output: {{
      bands: {len(bands)},
      sampleType: "FLOAT32"
    }}
  }}
}}
function evaluatePixel(sample) {{
  return [{bands_output}];
}}
"""


def build_ndvi_evalscript() -> str:
    """
    Construye evalscript para cálculo NDVI.

    Returns:
        str: Evalscript NDVI
    """
    return """
//VERSION=3
function setup() {
  return {
    input: ["B04", "B08"],
    output: {
      bands: 1,
      sampleType: "FLOAT32"
    }
  }
}
function evaluatePixel(sample) {
  let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
  return [ndvi];
}
"""


def build_true_color_evalscript() -> str:
    """
    Construye evalscript para imagen RGB true-color.

    Returns:
        str: Evalscript RGB
    """
    return """
//VERSION=3
function setup() {
  return {
    input: ["B02", "B03", "B04"],
    output: {
      bands: 3,
      sampleType: "UINT8"
    }
  }
}
function evaluatePixel(sample) {
  // Stretch reflectance [0, 0.3] to [0, 255]
  const r = Math.min(255, Math.max(0, 255 * sample.B04 / 0.3));
  const g = Math.min(255, Math.max(0, 255 * sample.B03 / 0.3));
  const b = Math.min(255, Math.max(0, 255 * sample.B02 / 0.3));
  return [r, g, b];
}
"""


def build_check_availability_evalscript() -> str:
    """
    Construye evalscript simple para verificar disponibilidad.

    Returns:
        str: Evalscript minimal
    """
    return """
//VERSION=3
function setup() {
  return {
    input: ["B04"],
    output: {
      bands: 1,
      sampleType: "UINT8"
    }
  }
}
function evaluatePixel(sample) {
  return [sample.B04 * 255];
}
"""


def build_process_request(
    polygon_geojson: Dict,
    start_date: str,
    end_date: str,
    evalscript: str,
    width: int,
    height: int,
    max_cloud_coverage: int,
    response_format: str = "image/tiff"
) -> Dict:
    """
    Construye payload completo para Process API.

    Args:
        polygon_geojson: Geometría GeoJSON del polígono
        start_date: Fecha inicio (YYYY-MM-DD)
        end_date: Fecha fin (YYYY-MM-DD)
        evalscript: Evalscript de Sentinel Hub
        width: Ancho en píxeles
        height: Alto en píxeles
        max_cloud_coverage: Cobertura máxima de nubes (0-100)
        response_format: Formato de respuesta (default: "image/tiff")

    Returns:
        Dict: Payload para Process API
    """
    payload = {
        "input": {
            "bounds": {
                "geometry": polygon_geojson,
                "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"}
            },
            "data": [{
                "type": "sentinel-2-l2a",
                "dataFilter": {
                    "timeRange": {
                        "from": f"{start_date}T00:00:00Z",
                        "to": f"{end_date}T23:59:59Z"
                    },
                    "maxCloudCoverage": max_cloud_coverage
                }
            }]
        },
        "output": {
            "width": width,
            "height": height
        },
        "evalscript": evalscript
    }

    # Solo agregar responses si el formato es TIFF
    if response_format == "image/tiff":
        payload["output"]["responses"] = [{
            "identifier": "default",
            "format": {"type": response_format}
        }]

    return payload
