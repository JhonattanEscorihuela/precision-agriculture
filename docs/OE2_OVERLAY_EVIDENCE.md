# OE2 — NDVI Overlay Endpoint — Evidencia de Implementación

**Fecha:** 2026-08-04  
**Commit:** `2c4a966` (merge de `b7769ce`)  
**Objetivo:** Endpoint para generar overlay PNG coloreado del NDVI para visualización en mapas Leaflet

---

## ✅ IMPLEMENTACIÓN COMPLETA

### 1. Modelo — Campo de caché

**Archivo:** `backend/app/models/analysis.py`

```python
# Campo agregado en NDVIResult
overlay_png: Optional[bytes] = Field(
    default=None,
    description="PNG coloreado RGBA del NDVI para visualización (caché)"
)
```

**Migración BD ejecutada:**
```sql
ALTER TABLE ndvi_results ADD COLUMN overlay_png BYTEA;
```

---

### 2. Servicio de generación

**Archivo:** `backend/app/services/ndvi_overlay_service.py` (77 líneas, nuevo)

**Función principal:**
```python
def generate_ndvi_overlay(ndvi_tiff_bytes: bytes) -> Tuple[bytes, List[List[float]]]
```

**Paleta de colores (semáforo de salud):**
- 🟢 Verde `#16a34a`: NDVI ≥ 0.5 (Sano)
- 🟡 Amarillo `#eab308`: 0.3 ≤ NDVI < 0.5 (Alerta)
- 🔴 Rojo `#dc2626`: NDVI < 0.3 (Crítico)
- ⬜ Transparente: píxeles inválidos/nodata

**Alpha:** 180 (70% opacidad) para ver el mapa base debajo

**Workflow:**
1. Lee TIFF NDVI desde bytes con rasterio
2. Extrae bounds georreferenciados
3. Crea array RGBA con máscara de datos válidos
4. Aplica colores según umbrales
5. Genera PNG optimizado con Pillow
6. Retorna (png_bytes, leaflet_bounds)

---

### 3. CRUD — Actualización de caché

**Archivo:** `backend/app/crud/ndvi.py`

```python
async def update_overlay_cache(
    db: AsyncSession,
    ndvi_id: int,
    overlay_png: bytes
) -> bool
```

---

### 4. Endpoint

**Archivo:** `backend/app/api/endpoints/ndvi.py` (+130 líneas)

**Ruta:** `GET /api/ndvi/{acquisition_id}/overlay`

**Query params:**
- `force: bool = False` — Forzar recálculo aunque exista caché

**Response:**
```json
{
  "image_base64": "data:image/png;base64,...",
  "bounds": [[lat_south, lng_west], [lat_north, lng_east]],
  "cached": true/false,
  "metadata": {
    "date": "2026-07-27",
    "polygon_id": 1,
    "thresholds": {"critical": 0.3, "alert": 0.5}
  }
}
```

**Cache policy:**
1. Primera llamada: calcula y guarda en `overlay_png` (BD)
2. Siguientes llamadas: sirve desde caché
3. `?force=true`: recalcula y actualiza caché

**Seguridad:**
- Requiere JWT (autenticación)
- Verifica ownership del polígono antes de servir

---

## 🧪 VALIDACIÓN

### Test 1: Primera llamada (genera caché)

**Request:**
```bash
GET /api/ndvi/1/overlay
Authorization: Bearer eyJhbGci...
```

**Response:**
```json
{
  "image_base64": "data:image/png;base64,iVBORw0KGg...[6380 bytes]",
  "bounds": [[8.8386, -67.5274], [8.8536, -67.5102]],
  "cached": false,
  "metadata": {
    "date": "2026-07-27",
    "polygon_id": 1,
    "thresholds": {"critical": 0.3, "alert": 0.5}
  }
}
```

**Logs backend:**
```
SELECT ndvi_results...
UPDATE ndvi_results SET overlay_png=%s WHERE id = 1
200 OK
```

**BD:**
```sql
SELECT id, LENGTH(overlay_png) FROM ndvi_results WHERE id = 1;
-- id=1, overlay_png=6380 bytes
```

---

### Test 2: Segunda llamada (usa caché)

**Request:**
```bash
GET /api/ndvi/1/overlay
```

**Response:**
```json
{
  "cached": true,
  "bounds": [[8.8386, -67.5274], [8.8536, -67.5102]],
  "metadata": {...}
}
```

**Logs backend:**
```
SELECT ndvi_results...  (solo SELECT, sin UPDATE)
200 OK
```

---

### Test 3: Recálculo forzado

**Request:**
```bash
GET /api/ndvi/1/overlay?force=true
```

**Response:**
```json
{
  "cached": false,
  "bounds": [[8.8386, -67.5274], [8.8536, -67.5102]],
  "metadata": {...}
}
```

**Logs backend:**
```
SELECT ndvi_results...
UPDATE ndvi_results SET overlay_png=%s WHERE id = 1
200 OK
```

---

## 📦 DEPENDENCIAS

**Agregada a `requirements.txt`:**
```
Pillow>=10.0.0
```

**Instalada en container:**
```bash
docker-compose up -d --build backend
✅ Backend levantó sin errores
```

---

## 🔧 CAMBIOS EN BD

**Columna agregada:**
```sql
ALTER TABLE ndvi_results ADD COLUMN overlay_png BYTEA;
```

**Verificación:**
```sql
\d ndvi_results
-- overlay_png | bytea | | |
```

---

## 📊 PERFORMANCE

| Métrica | Valor |
|---------|-------|
| Tamaño PNG | ~6.3 KB (512×512 px, RGBA, optimizado) |
| Primera llamada | ~3-5s (genera + guarda) |
| Llamadas cacheadas | <100ms (SELECT desde BD) |
| Storage impact | ~6KB por adquisición (aceptable) |

**Nota:** Para parcelas con múltiples fechas (10-20 adquisiciones), el storage total es ~60-120KB, totalmente viable en PostgreSQL.

---

## 🎯 INTEGRACIÓN FRONTEND

**Según spec** (`FRONTEND_SPEC_OVERLAYS.md`):

### Nivel 1 — Mapa General
```tsx
<ImageOverlay
  url={overlayData.image_base64}
  bounds={overlayData.bounds}
  opacity={0.7}
/>
```

### Nivel 2 — SegmentationPanel.tsx
```tsx
<img 
  src={overlayData.image_base64} 
  alt="NDVI overlay"
  className="w-full aspect-square"
/>
```

**Cache local frontend:**
```typescript
const [overlayCache, setOverlayCache] = useState<Map<number, OverlayData>>(new Map());

// Solo fetch si no está en caché
if (!overlayCache.has(acquisitionId)) {
  const data = await fetchOverlay(acquisitionId);
  setOverlayCache(prev => new Map(prev).set(acquisitionId, data));
}
```

---

## ✅ CRITERIOS DE COMPLETITUD

- [x] Modelo actualizado con campo `overlay_png`
- [x] Migración BD ejecutada
- [x] Servicio de generación implementado
- [x] CRUD de actualización caché
- [x] Endpoint implementado con ownership check
- [x] Pillow agregado a requirements.txt
- [x] Docker-compose build exitoso
- [x] Tests manuales: primera llamada, caché, force
- [x] Logs sin errores
- [x] BD con datos verificados
- [x] Commit y merge a main
- [x] Push a remoto
- [x] Documentación de evidencia

---

## 🚀 PRÓXIMOS PASOS

1. **Frontend:** Implementar `FRONTEND_SPEC_OVERLAYS.md`
   - Nivel 1: Controles Radio + ImageOverlay en mapa
   - Nivel 2: Imagen en SegmentationPanel
   
2. **OE4:** Crear endpoint similar para overlays de textura
   - `GET /api/texture/overlay/{ndvi_result_id}?kernel=contrast`
   - Paleta frío/cálido (azul → púrpura → naranja)

3. **Optimización (opcional):**
   - Si > 100 overlays en BD, considerar limpieza de caché antigua
   - Endpoints batch para cargar múltiples overlays en paralelo

---

## 📝 LIMITACIONES CONOCIDAS

1. **Bounds fijos:** Los bounds se recalculan desde el TIFF en cada llamada cacheada. Se podría optimizar guardándolos en BD.

2. **Tamaño raster:** Asume rasters ~512×512. Para rasters muy grandes (>2000×2000), el PNG podría ser >100KB.

3. **Sin compresión adicional:** Se usa `optimize=True` de Pillow. Si se necesita más compresión, evaluar PNG con cuantización de colores (256 colores vs RGBA full).

4. **Sincronización caché:** Si se recalcula el NDVI, el overlay cacheado queda obsoleto. Considerar invalidar `overlay_png = NULL` al actualizar `ndvi_tiff`.

---

**Endpoint listo para uso en frontend. Ver `FRONTEND_SPEC_OVERLAYS.md` para especificación de integración.**
