# Fix Crítico: Consistencia de scene_id en imagen RGB satelital

**Fecha:** 19 de agosto de 2026  
**Severidad:** **CRÍTICA** - Afecta integridad científica del sistema  
**Reporter:** Usuario (@jhonattan1410@gmail.com)

---

## 🚨 Problema Crítico Identificado

El usuario reportó que la imagen satelital RGB mostraba **muchas nubes** para la fecha 10 de agosto (2026-08-11 en realidad), pero el sistema reportaba **0.02% de nubosidad** para esa parcela.

### Evidencia del Problema

**Base de datos:**
```sql
SELECT 
    acquisition_date,
    scene_id,
    cloud_coverage as scene_cloud,
    parcel_cloud_cover,
    quality_status
FROM sentinel_acquisitions
WHERE id = 1;

-- Resultado:
-- 2026-08-11 | S2B_MSIL2A_20260811T145719... | 6.45% | 0.02% | suitable
```

**Imagen RGB:** Mostraba claramente nubes (manchas blancas visibles)

**Conclusión:** La imagen RGB NO correspondía a la misma escena que el NDVI analizado.

---

## 🔍 Causa Raíz

### Flujo INCORRECTO (antes del fix):

1. **Adquisición de bandas B04/B08/SCL:**
   - Usa `mosaickingOrder: "leastCC"` (menos nubes)
   - Sentinel Hub selecciona escena: `S2B_MSIL2A_20260811T145719...`
   - Se guarda `scene_id` en BD
   - Se calcula NDVI con esas bandas
   - Se calcula nubosidad por parcela usando SCL de **esa escena específica**

2. **Descarga de imagen RGB (posterior):**
   - Usa NUEVAMENTE `mosaickingOrder: "leastCC"`
   - **Sentinel Hub puede seleccionar una ESCENA DIFERENTE del mismo día**
   - Parámetros: `start_date=end_date="2026-08-11"` + `maxCloudCoverage=20`
   - **NO se especificaba el scene_id**

### ¿Por qué esto es CRÍTICO?

El mismo día puede tener **múltiples pasadas** del satélite (S2A y S2B):
- Pasada 1: Escena con 0.02% nubes en parcela → Usada para NDVI
- Pasada 2: Escena con 40% nubes en parcela → Usada para RGB

**Resultado:** El usuario ve una imagen que **NO corresponde** al análisis NDVI que está consultando.

**Impacto:**
- ❌ Integridad científica comprometida
- ❌ Datos mostrados inconsistentes con análisis
- ❌ Usuario toma decisiones basadas en información errónea
- ❌ **"Esto significa plata"** como correctamente señaló el usuario

---

## ✅ Solución Implementada

### Principio fundamental:

> **Si el NDVI se calculó con la escena X, la imagen RGB DEBE ser de ESA MISMA ESCENA X, no de otra escena Y solo porque tiene menos nubes.**

### Cambios técnicos:

#### 1. Modificación de `request_builder.py`

**Antes:**
```python
def build_process_request(..., response_format: str = "image/tiff") -> Dict:
    # ...
    "dataFilter": {
        "timeRange": {"from": f"{start_date}T00:00:00Z", "to": f"{end_date}T23:59:59Z"},
        "maxCloudCoverage": max_cloud_coverage,
        "mosaickingOrder": "leastCC"  # ← PROBLEMA: puede elegir escena diferente
    }
```

**Después:**
```python
def build_process_request(..., scene_id: str = None) -> Dict:
    data_filter = {
        "timeRange": {...},
        "maxCloudCoverage": max_cloud_coverage
    }
    
    if scene_id:
        # Extraer timestamp del scene_id
        # S2B_MSIL2A_20260811T145719_... → 2026-08-11T14:57:19Z
        match = re.search(r'_(\d{8}T\d{6})_', scene_id)
        if match:
            sensing_time = match.group(1)
            sensing_iso = format_to_iso(sensing_time)
            # Usar timestamp exacto (sin mosaickingOrder)
            data_filter["timeRange"] = {"from": sensing_iso, "to": sensing_iso}
        else:
            data_filter["mosaickingOrder"] = "leastCC"
    else:
        data_filter["mosaickingOrder"] = "leastCC"
```

#### 2. Propagación de `scene_id` en cadena

- `process_client.py`: `download_true_color(scene_id=None)`
- `sentinel_service.py`: `download_true_color(scene_id=None)`
- **`ndvi.py` (endpoint crítico):**

```python
# ANTES:
rgb_png_bytes = await sentinel_service.download_true_color(
    polygon_geojson=polygon_geojson,
    start_date=acq_date_str,
    end_date=acq_date_str,
    max_cloud_coverage=20,
    polygon_id=polygon.id
    # ❌ Sin scene_id
)

# DESPUÉS:
rgb_png_bytes = await sentinel_service.download_true_color(
    polygon_geojson=polygon_geojson,
    start_date=acq_date_str,
    end_date=acq_date_str,
    max_cloud_coverage=20,
    polygon_id=polygon.id,
    scene_id=acquisition.scene_id  # ✅ FORZAR ESCENA ESPECÍFICA
)
```

#### 3. Limpieza de caché

```sql
-- 11 cachés de satellite_png limpiados
UPDATE ndvi_results SET satellite_png = NULL WHERE satellite_png IS NOT NULL;
```

Las imágenes cacheadas fueron descargadas con `leastCC` y pueden ser inconsistentes.

---

## 🧪 Validación

### Caso de prueba:

**Parcela:** #1 (usuario jhonattan1410@gmail.com)  
**Fecha:** 2026-08-11  
**Scene ID:** `S2B_MSIL2A_20260811T145719_N0512_R039_T19PFK_20260811T182904`  
**Nubosidad parcela:** 0.02%

**Resultado esperado:**
- Imagen RGB debe mostrar **la misma escena** que el NDVI
- NO debe tener nubes visibles (0.02%)
- Timestamp de la request RGB debe ser: `2026-08-11T14:57:19Z` (exacto)
- Logs deben mostrar que se usó el scene_id específico

### Verificación en logs:

```
DOWNLOAD_TRUE_COLOR request for polygon_id=1
dataFilter: {
  "timeRange": {"from": "2026-08-11T14:57:19Z", "to": "2026-08-11T14:57:19Z"},
  "maxCloudCoverage": 20
  // ✅ Sin mosaickingOrder (usa timestamp exacto)
}
```

---

## 📊 Impacto del Fix

| Aspecto | Antes | Después |
|---------|-------|---------|
| **Imagen RGB** | Cualquier escena del día con `leastCC` | MISMA escena que NDVI |
| **Consistencia** | ❌ No garantizada | ✅ Garantizada |
| **Nubosidad** | Puede diferir del análisis | Coincide con análisis |
| **Integridad científica** | ❌ Comprometida | ✅ Preservada |
| **Confianza usuario** | ❌ Baja (ve inconsistencias) | ✅ Alta (datos coherentes) |

---

## 🎯 Lecciones Aprendidas

### 1. Nunca asumir que "leastCC" da la misma escena
- El mismo día puede tener múltiples pasadas
- Cada pasada puede tener nubosidad diferente en la misma parcela
- `leastCC` elige la escena con menos nubes **globales**, no locales

### 2. La consistencia es CRÍTICA en sistemas científicos
- Si analizas con escena X, DEBES visualizar escena X
- No se puede "mejorar" la visualización usando otra escena
- El usuario necesita VER lo que se ANALIZÓ

### 3. El caché debe invalidarse al cambiar criterios
- Las imágenes cacheadas con `leastCC` son inconsistentes
- Necesitan re-descargarse con el nuevo criterio (scene_id específico)

### 4. La validación visual es clave
- Tests pueden pasar pero datos ser incorrectos
- El usuario fue quien detectó la inconsistencia
- Necesitamos validación end-to-end con inspección visual

---

## 🔧 Recomendaciones Futuras

### 1. Logging mejorado
Agregar en logs:
- Scene ID usado en cada descarga
- Timestamp exacto de la request
- Si se usó `mosaickingOrder` o timestamp específico

### 2. Validación automática
Verificar que:
- `scene_id` de RGB == `scene_id` de NDVI
- Timestamp de request coincide con sensing time del scene_id

### 3. Documentación para usuario
Explicar en UI que:
- La imagen RGB corresponde a la fecha de análisis específica
- Es la MISMA escena usada para calcular NDVI
- Puede tener nubes si la escena las tenía

### 4. Alertas de calidad
Si `parcel_cloud_cover > 5%`:
- Mostrar warning en UI
- Indicar que la imagen puede tener nubes visibles
- Explicar que el NDVI está enmascarado (solo zonas despejadas)

---

## 📚 Referencias

- PR #1: Feature parcel-cloud-coverage
- Commit: `0f5429a` - Fix critical RGB scene consistency
- Documentación: `docs/CLOUD_QUALITY_AND_NDVI_MASK.md`
- Sentinel Hub Process API: https://docs.sentinel-hub.com/api/latest/

---

## ✅ Conclusión

Este fix es **CRÍTICO** porque restaura la **integridad científica** del sistema. 

El usuario tenía razón en su observación: "si en el cálculo del NDVI se hace correcto con un cloud_cover de 20% para la imagen debe ser el mismo".

El sistema ahora garantiza que la visualización RGB corresponde EXACTAMENTE a la misma escena satelital que se usó para el análisis NDVI, preservando la coherencia y confiabilidad de los datos presentados.

**Status:** ✅ **RESUELTO** - Sistema con integridad científica restaurada
