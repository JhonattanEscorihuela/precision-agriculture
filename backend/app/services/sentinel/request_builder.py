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
    Construye evalscript para imagen RGB true-color PNG.

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


def build_true_color_tiff_evalscript() -> str:
    """
    Construye evalscript para imagen RGB true-color TIFF georreferenciado.

    Sentinel Hub requiere FLOAT32 para TIFFs georreferenciados.
    Los valores se normalizan [0, 1] y luego se convierten a UINT8 al leer.

    Returns:
        str: Evalscript RGB para TIFF
    """
    return """
//VERSION=3
function setup() {
  return {
    input: ["B02", "B03", "B04", "dataMask"],
    output: {
      bands: 4,
      sampleType: "FLOAT32"
    }
  }
}
function evaluatePixel(sample) {
  // Normalizar reflectancia [0, 0.3] a [0, 1] para FLOAT32
  const r = Math.min(1, Math.max(0, sample.B04 / 0.3));
  const g = Math.min(1, Math.max(0, sample.B03 / 0.3));
  const b = Math.min(1, Math.max(0, sample.B02 / 0.3));
  return [r, g, b, sample.dataMask];
}
"""


def build_scl_evalscript() -> str:
    """Construye un TIFF UINT8 con las bandas SCL y dataMask."""
    return """
//VERSION=3
function setup() {
  return {
    input: ["SCL", "dataMask"],
    output: {
      bands: 2,
      sampleType: "UINT8"
    }
  }
}
function evaluatePixel(sample) {
  return [sample.SCL, sample.dataMask];
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
    response_format: str = "image/tiff",
    scene_id: str = None
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
        scene_id: Scene ID específico de Sentinel-2 (opcional, para forzar escena exacta)
                 Formato: S2A_MSIL2A_20260811T145719_N0512_R039_T19PFK_20260811T182904

    Returns:
        Dict: Payload para Process API
    """
    # Construir dataFilter
    data_filter = {
        "timeRange": {
            "from": f"{start_date}T00:00:00Z",
            "to": f"{end_date}T23:59:59Z"
        },
        "maxCloudCoverage": max_cloud_coverage
    }

    # Si se especifica scene_id, extraer timestamp preciso y NO usar mosaickingOrder
    # Esto fuerza el uso de la escena exacta
    if scene_id:
        # Extraer timestamp del scene_id
        # Formato: S2B_MSIL2A_20260811T145719_N0512_R039_T19PFK_20260811T182904
        #                    ^^^^^^^^^^^^^^^^                    ^^^^^^^^^^^^^^^^
        #                    fecha + hora sensing               fecha + hora processing
        import re
        match = re.search(r'_(\d{8}T\d{6})_', scene_id)
        if match:
            sensing_time = match.group(1)  # Ej: 20260811T145719
            # Convertir a formato ISO: 2026-08-11T14:57:19Z
            sensing_iso = f"{sensing_time[:4]}-{sensing_time[4:6]}-{sensing_time[6:8]}T{sensing_time[9:11]}:{sensing_time[11:13]}:{sensing_time[13:15]}Z"
            # Usar ventana de +/- 1 minuto para asegurar que capturamos esta escena específica
            data_filter["timeRange"] = {
                "from": sensing_iso,
                "to": sensing_iso
            }
            # NO usar mosaickingOrder cuando se especifica scene exacto
        else:
            # Si no se puede parsear, usar mosaickingOrder por defecto
            data_filter["mosaickingOrder"] = "leastCC"
    else:
        # Sin scene_id, usar política de menos nubes
        data_filter["mosaickingOrder"] = "leastCC"

    payload = {
        "input": {
            "bounds": {
                "geometry": polygon_geojson,
                "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"}
            },
            "data": [{
                "type": "sentinel-2-l2a",
                "dataFilter": data_filter
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
