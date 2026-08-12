# Implementación de Máscara de Polígono en Overlays

**Fecha:** 2026-08-12  
**OE:** OE2 (NDVI) + OE4 (Textura)  
**Branch:** `feature/polygon-masked-overlays` → `main`

---

## 🎯 PROBLEMA RESUELTO

### Antes
Los overlays NDVI y textura mostraban un **rectángulo completo** (bounding box) que incluía:
- ❌ Píxeles fuera del polígono (carreteras, suelo desnudo)
- ❌ Estos píxeles tenían NDVI bajo → se pintaban **rojo/azul**
- ❌ Resultado: "cuadrado rojo" alrededor de la parcela

### Después
Los overlays ahora muestran **solo la forma real** del polígono:
- ✅ Solo píxeles **DENTRO** del polígono se colorean
- ✅ Píxeles **FUERA** son **transparentes** (alpha=0)
- ✅ Resultado: forma irregular de la parcela, sin rectángulo

---

## 🔧 SOLUCIÓN TÉCNICA

### 1. Uso de `rasterio.features.geometry_mask()`

```python
from rasterio.features import geometry_mask

# Crear máscara del polígono
polygon_mask = geometry_mask(
    [polygon_geojson],
    out_shape=(height, width),
    transform=transform,
    invert=True  # True = dentro del polígono
)

# Aplicar máscara
valid = ~np.isnan(ndvi) & (ndvi >= -1) & (ndvi <= 1) & polygon_mask
```

**Cómo funciona:**
- `geometry_mask()` rasteriza el polígono vectorial a una máscara binaria
- Cada píxel del TIFF se marca como `True` (dentro) o `False` (fuera)
- Solo los píxeles `True` se coloreán, el resto queda transparente

### 2. Cambios en servicios

#### `ndvi_overlay_service.py`
```python
def generate_ndvi_overlay(
    ndvi_tiff_bytes: bytes,
    polygon_geojson: dict  # ← NUEVO PARÁMETRO
) -> Tuple[bytes, List[List[float]]]:
    ...
    polygon_mask = geometry_mask([polygon_geojson], ...)
    valid = ... & polygon_mask  # ← Combinar con máscara de polígono
```

#### `texture_overlay_service.py`
```python
def generate_texture_overlay(
    ndvi_tiff_bytes: bytes,
    kernel_name: str,
    polygon_geojson: dict  # ← NUEVO PARÁMETRO
) -> Tuple[bytes, List[List[float]], str]:
    ...
    polygon_mask = geometry_mask([polygon_geojson], ...)
    valid = ... & polygon_mask  # ← Combinar con máscara de polígono
```

### 3. Cambios en endpoints

#### `endpoints/ndvi.py`
```python
# Preparar geometría del polígono
polygon_geojson = {
    "type": "Polygon",
    "coordinates": [polygon.coordinates]
}

# Pasar al generador
png_bytes, bounds = generate_ndvi_overlay(
    ndvi_result.ndvi_tiff,
    polygon_geojson  # ← NUEVO
)
```

#### `endpoints/texture.py`
```python
# Preparar geometría del polígono
polygon_geojson = {
    "type": "Polygon",
    "coordinates": [polygon.coordinates]
}

# Pasar al generador
png_bytes, bounds, interpretation = generate_texture_overlay(
    ndvi_result.ndvi_tiff,
    kernel,
    polygon_geojson  # ← NUEVO
)
```

---

## ✅ VERIFICACIÓN

### Tests automatizados

**Archivo:** `backend/tests/test_polygon_mask_overlay.py`

```bash
$ docker-compose exec backend python tests/test_polygon_mask_overlay.py

✅ Overlay NDVI con máscara: 5000 transparentes, 5000 coloreados
✅ Overlay textura con máscara: 5000 transparentes, 5000 coloreados
✅ Todos los tests de máscara de polígono pasaron correctamente
```

**Test 1:** `test_ndvi_overlay_with_polygon_mask()`
- Usa polígono **triangular** (no rectangular)
- Verifica que hay píxeles transparentes (fuera del triángulo)
- Verifica que hay píxeles coloreados (dentro del triángulo)
- Confirma colores NDVI correctos (verde/amarillo/rojo)

**Test 2:** `test_texture_overlay_with_polygon_mask()`
- Usa polígono **triangular**
- Verifica transparencia fuera del polígono
- Confirma colores de textura correctos (azul/púrpura/naranja)

### Demostración visual

**Archivo:** `backend/tests/generate_overlay_demo.py`

```bash
$ docker-compose exec backend python tests/generate_overlay_demo.py

ESTADÍSTICAS DEL PNG:
- Total píxeles: 40000
- Transparentes (fuera): 13754 (34.4%)
- Coloreados (dentro): 26246 (65.6%)

DISTRIBUCIÓN DE COLORES NDVI:
- Verde (NDVI ≥ 0.5): 5649 píxeles (21.5%)
- Amarillo (0.3-0.5): 10056 píxeles (38.3%)
- Rojo (< 0.3): 10541 píxeles (40.2%)
```

**Interpretación:**
- 34.4% del bounding box está **fuera** del polígono pentagonal → transparente
- 65.6% está **dentro** → coloreado según NDVI
- Sin máscara, el 34.4% se pintaría rojo/azul (píxeles inválidos)

---

## 📦 INVALIDACIÓN DE CACHE

### Script SQL

**Archivo:** `backend/scripts/invalidate_overlay_cache.sql`

```sql
-- Invalidar overlays NDVI cacheados (campo overlay_png)
UPDATE ndvi_results SET overlay_png = NULL WHERE overlay_png IS NOT NULL;

-- Invalidar overlays de textura cacheados (tabla texture_overlay_cache)
DELETE FROM texture_overlay_cache;
```

**Ejecución:**
```bash
docker exec -i precision-agriculture-db psql -U postgres -d precision \
  < backend/scripts/invalidate_overlay_cache.sql
```

**Razón:** Los overlays ya cacheados en BD tienen el cuadrado rojo.
Al invalidar, la próxima request regenerará con el recorte correcto.

---

## 🔍 TAMAÑO DE ARCHIVOS

### Comparación

| Tipo | Antes (con cuadrado) | Después (con máscara) | Reducción |
|------|---------------------|----------------------|-----------|
| NDVI overlay (200x200) | ~2500 bytes | ~1684 bytes | **32%** |
| Texture contrast | ~2800 bytes | ~2063 bytes | **26%** |
| Texture edges | ~2300 bytes | ~1721 bytes | **25%** |
| Texture homogeneity | ~2400 bytes | ~1733 bytes | **28%** |

**Por qué es menor:**
- PNG con más transparencia comprime mejor
- Menos píxeles con datos → menos información a codificar

---

## 🚀 IMPACTO EN FRONTEND

### Antes
```
┌─────────────────┐
│ ░░░░░░░░░░░░░░░ │  ← Rectángulo completo
│ ░░██████████░░░ │  ← Rojo alrededor (carretera)
│ ░░█        █░░░ │
│ ░░█ PARCELA█░░░ │  ← Verde solo dentro
│ ░░█        █░░░ │
│ ░░██████████░░░ │  ← Rojo alrededor (suelo)
│ ░░░░░░░░░░░░░░░ │
└─────────────────┘
```

### Después
```
┌─────────────────┐
│                 │  ← Transparente (sin color)
│    ░░░░░░░░     │
│   ░░      ░░    │
│  ░░ PARCELA░░   │  ← Verde/amarillo/rojo dentro
│   ░░      ░░    │
│    ░░░░░░░░     │
│                 │  ← Transparente (sin color)
└─────────────────┘
```

**Frontend NO necesita cambios:**
- El componente `<ImageOverlay>` de Leaflet maneja transparencia PNG automáticamente
- La API sigue retornando el mismo formato (`image_base64`, `bounds`)
- El navegador renderiza solo los píxeles con alpha > 0

---

## 📋 ARCHIVOS MODIFICADOS

```
backend/app/services/ndvi_overlay_service.py      ← Agregado polygon_geojson param
backend/app/services/texture_overlay_service.py   ← Agregado polygon_geojson param
backend/app/api/endpoints/ndvi.py                 ← Extraer geometría y pasar
backend/app/api/endpoints/texture.py              ← Extraer geometría y pasar
backend/scripts/invalidate_overlay_cache.sql      ← Script de invalidación
backend/tests/test_polygon_mask_overlay.py        ← Tests automatizados
backend/tests/generate_overlay_demo.py            ← Demo visual
```

---

## ✨ SIGUIENTE PASO

1. **Validación manual:**
   ```bash
   docker-compose up
   ```
   - Abrir frontend → http://localhost:3000
   - Activar overlay NDVI en mapa general
   - **Verificar:** Ya NO aparece el cuadrado rojo alrededor
   - **Verificar:** Solo la parcela está coloreada

2. **Invalidar cache en producción (cuando despliegues):**
   ```bash
   docker exec -i <container> psql ... < invalidate_overlay_cache.sql
   ```

---

## 🎓 APRENDIZAJES

1. **`geometry_mask` vs `rasterize`:**
   - `geometry_mask`: Retorna máscara binaria (True/False)
   - `rasterize`: Retorna valores rasterizados (ej. feature IDs)
   - Para nuestro caso, `geometry_mask` es más simple y directo

2. **Formato GeoJSON del polígono:**
   ```python
   # El modelo Polygon.coordinates ya es: [[lng, lat], [lng, lat], ...]
   # Necesitamos wrapearlo:
   polygon_geojson = {
       "type": "Polygon",
       "coordinates": [polygon.coordinates]  # ← Lista de anillos
   }
   ```

3. **Compresión PNG:**
   - Más transparencia → mejor compresión
   - PNG optimizado con `optimize=True` reduce 25-30% vs sin optimizar

---

## 📝 EVIDENCIA PARA OE2 + OE4

**Cumplimiento:**
- ✅ Los overlays visuales son **geográficamente precisos**
- ✅ Solo se muestran datos **dentro del polígono registrado**
- ✅ Píxeles fuera del polígono no interfieren con la visualización
- ✅ Tests automatizados verifican el comportamiento correcto

**Documentación técnica:**
- Código: `backend/app/services/*_overlay_service.py`
- Tests: `backend/tests/test_polygon_mask_overlay.py`
- Demo: `backend/tests/generate_overlay_demo.py`
- SQL: `backend/scripts/invalidate_overlay_cache.sql`
