# OE4 — Texture Overlay Endpoint — Evidencia de Implementación

**Fecha:** 2026-08-04  
**Commit:** `34de01a` (merge de `37135b7`)  
**Objetivo:** Endpoint para generar overlays PNG coloreados de textura para visualización en mapas Leaflet

---

## ✅ IMPLEMENTACIÓN COMPLETA

### 1. Modelo de caché

**Archivo:** `backend/app/models/analysis.py`

```python
class TextureOverlayCache(SQLModel, table=True):
    """Caché de overlays PNG coloreados de textura."""
    __tablename__ = "texture_overlay_cache"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    ndvi_result_id: int  # FK a ndvi_results
    kernel: str  # contrast, edges, homogeneity
    overlay_png: bytes  # PNG coloreado RGBA
    interpretation: str  # Texto explicativo
    created_at: Optional[datetime]
```

**Constraint UNIQUE:** `(ndvi_result_id, kernel)` — un overlay por cada combinación

**Tabla creada en PostgreSQL:**
```sql
CREATE TABLE texture_overlay_cache (
    id SERIAL PRIMARY KEY,
    ndvi_result_id INTEGER NOT NULL REFERENCES ndvi_results(id) ON DELETE CASCADE,
    kernel VARCHAR(20) NOT NULL,
    overlay_png BYTEA NOT NULL,
    interpretation TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_texture_overlay_ndvi_kernel UNIQUE(ndvi_result_id, kernel)
);
```

---

### 2. Servicio de generación

**Archivo:** `backend/app/services/texture_overlay_service.py` (170 líneas, nuevo)

**Función principal:**
```python
def generate_texture_overlay(
    ndvi_tiff_bytes: bytes,
    kernel_name: str
) -> Tuple[bytes, List[List[float]], str]
```

**Kernels implementados (según metodología OE4):**

1. **contrast** — Magnitud del gradiente (Sobel):
   ```python
   gx = convolve(ndvi, kernel_gx)  # Sobel horizontal
   gy = convolve(ndvi, kernel_gy)  # Sobel vertical
   texture = sqrt(gx² + gy²)
   ```

2. **edges** — Laplaciano (detecta bordes internos):
   ```python
   kernel_edges = [[0, 1, 0], [1, -4, 1], [0, 1, 0]]
   texture = abs(convolve(ndvi, kernel_edges))
   ```

3. **homogeneity** — Diferencia con media local:
   ```python
   mean_local = convolve(ndvi, mean_kernel)
   texture = abs(ndvi - mean_local)
   ```

**Paleta de colores (variabilidad frío/cálido):**
- 💙 **Azul** `#3b82f6` → Percentil 0-33 (Uniforme/bajo)
- 💜 **Púrpura** `#8b5cf6` → Percentil 33-66 (Moderado)
- 🧡 **Naranja** `#f97316` → Percentil 66-100 (Heterogéneo/alto)
- ⬜ **Transparente** → píxeles inválidos

**Alpha:** 180 (70% opacidad)

---

### 3. Interpretaciones dinámicas

**Función:** `_generate_interpretation(kernel_name, mean_value)`

#### Kernel: contrast

| mean_value | Interpretación |
|------------|----------------|
| < 0.05 | "Campo muy uniforme — cultivo homogéneo con buen manejo..." |
| 0.05-0.12 | "Variabilidad normal — dentro de parámetros esperados..." |
| > 0.12 | "Campo heterogéneo — se detectan zonas con diferente vigor..." |

#### Kernel: edges

| mean_value | Interpretación |
|------------|----------------|
| < 0.02 | "Sin bordes internos significativos — transiciones suaves..." |
| 0.02-0.08 | "Bordes moderados — pueden corresponder a caminos, canales..." |
| > 0.08 | "Bordes marcados — revisar problemas de drenaje o cambios de lote..." |

#### Kernel: homogeneity

| mean_value | Interpretación |
|------------|----------------|
| < 0.03 | "Alta homogeneidad — el cultivo crece de forma muy pareja..." |
| 0.03-0.08 | "Homogeneidad moderada — variación normal dentro del cultivo..." |
| > 0.08 | "Baja homogeneidad — evaluar factores como riego, fertilización..." |

---

### 4. CRUD

**Archivo:** `backend/app/crud/texture_overlay.py` (89 líneas, nuevo)

```python
async def get_cached_overlay(db, ndvi_result_id, kernel) -> Optional[TextureOverlayCache]
async def save_overlay_cache(db, ndvi_result_id, kernel, overlay_png, interpretation) -> TextureOverlayCache
```

---

### 5. Endpoint

**Archivo:** `backend/app/api/endpoints/texture.py` (+172 líneas)

**Ruta:** `GET /api/texture/overlay/{ndvi_result_id}?kernel=X`

**Query params:**
- `kernel: str` — "contrast" (default), "edges", o "homogeneity"
- `force: bool = False` — Forzar recálculo

**Response:**
```json
{
  "image_base64": "data:image/png;base64,...",
  "bounds": [[lat_south, lng_west], [lat_north, lng_east]],
  "kernel": "contrast",
  "cached": true/false,
  "interpretation": "Variabilidad normal — dentro de parámetros...",
  "metadata": {
    "date": "2026-07-27",
    "polygon_id": 1,
    "thresholds_percentiles": [33, 66]
  }
}
```

**Cache policy:**
1. Primera llamada: calcula, guarda en BD, retorna (cached=false)
2. Siguientes llamadas: sirve desde caché (cached=true)
3. `?force=true`: recalcula y actualiza caché

**Seguridad:**
- Requiere JWT (autenticación)
- Verifica ownership del polígono
- Valida kernel name

---

## 🧪 VALIDACIÓN COMPLETA

### Test 1: Kernel "contrast" (primera llamada)

**Request:**
```bash
GET /api/texture/overlay/1?kernel=contrast
Authorization: Bearer eyJhbGci...
```

**Response:**
```json
{
  "cached": false,
  "interpretation": "Variabilidad normal — dentro de parámetros esperados para cultivo de arroz. Monitorear evolución.",
  "image_base64_length": 51782,
  "bounds": [[8.8386, -67.5274], [8.8536, -67.5102]],
  "metadata": {
    "date": "2026-07-27",
    "polygon_id": 1,
    "thresholds_percentiles": [33, 66]
  }
}
```

**BD después:**
```sql
SELECT kernel, LENGTH(overlay_png) FROM texture_overlay_cache WHERE ndvi_result_id=1 AND kernel='contrast';
-- kernel='contrast', length=38819 bytes (~38KB)
```

---

### Test 2: Kernel "edges" (primera llamada)

**Request:**
```bash
GET /api/texture/overlay/1?kernel=edges
```

**Response:**
```json
{
  "cached": false,
  "interpretation": "Bordes moderados — se detectan algunas divisiones internas. Pueden corresponder a caminos, canales o diferencias de siembra.",
  "image_base64_length": 58634
}
```

**BD:**
```sql
-- kernel='edges', length=43957 bytes (~43KB)
```

---

### Test 3: Kernel "homogeneity" (primera llamada)

**Request:**
```bash
GET /api/texture/overlay/1?kernel=homogeneity
```

**Response:**
```json
{
  "cached": false,
  "interpretation": "Alta homogeneidad — el cultivo crece de forma muy pareja. Excelente uniformidad.",
  "image_base64_length": 56570
}
```

**BD:**
```sql
-- kernel='homogeneity', length=42409 bytes (~42KB)
```

---

### Test 4: Llamadas cacheadas (segunda vez)

**Requests:**
```bash
GET /api/texture/overlay/1?kernel=contrast
GET /api/texture/overlay/1?kernel=edges
GET /api/texture/overlay/1?kernel=homogeneity
```

**Results:**
```
contrast:    cached=True
edges:       cached=True
homogeneity: cached=True
```

**Logs backend:**
```
SELECT texture_overlay_cache... (solo SELECT, sin convolución)
200 OK (< 100ms cada uno)
```

---

### Test 5: Recálculo forzado

**Request:**
```bash
GET /api/texture/overlay/1?kernel=contrast&force=true
```

**Response:**
```json
{
  "cached": false,
  "interpretation": "Variabilidad normal — dentro de parámetros esperados..."
}
```

**BD:**
```sql
-- UPDATE texture_overlay_cache SET overlay_png=...
```

---

## 📊 STORAGE & PERFORMANCE

| Métrica | Valor |
|---------|-------|
| Tamaño PNG contrast | ~38KB |
| Tamaño PNG edges | ~43KB |
| Tamaño PNG homogeneity | ~42KB |
| Primera llamada (cálculo) | ~4-6s (convolución + PNG) |
| Llamadas cacheadas | <100ms (SELECT desde BD) |
| Storage por NDVI result | ~123KB (3 kernels × 41KB promedio) |

**Storage impact:** Para 33 adquisiciones (proyecto completo), storage total ≈ 4MB (aceptable en PostgreSQL).

---

## 🎯 INTEGRACIÓN FRONTEND

**Según spec** (`FRONTEND_SPEC_OVERLAYS.md`):

### Nivel 1 — Mapa General

```tsx
// Control de selección
const [overlayMode, setOverlayMode] = useState<'none' | 'ndvi' | 'texture'>('none');
const [textureKernel, setTextureKernel] = useState<'contrast' | 'edges' | 'homogeneity'>('contrast');

// Cargar overlay
if (overlayMode === 'texture') {
  const data = await fetchTextureOverlay(ndviResultId, textureKernel);
  <ImageOverlay
    url={data.image_base64}
    bounds={data.bounds}
    opacity={0.7}
  />
}
```

### Nivel 2 — TextureWidget.tsx

```tsx
<div>
  <select value={kernel} onChange={e => setKernel(e.target.value)}>
    <option value="contrast">Contraste</option>
    <option value="edges">Bordes</option>
    <option value="homogeneity">Homogeneidad</option>
  </select>

  <img 
    src={overlayData.image_base64} 
    alt={`Textura ${kernel}`}
    className="w-full aspect-square"
  />

  <p className="text-sm text-gray-600">
    💡 {overlayData.interpretation}
  </p>

  <div className="flex gap-2">
    <span className="text-blue-600">💙 Uniforme</span>
    <span className="text-purple-600">💜 Moderado</span>
    <span className="text-orange-600">🧡 Heterogéneo</span>
  </div>
</div>
```

---

## ✅ CRITERIOS DE COMPLETITUD

- [x] Modelo TextureOverlayCache con UNIQUE constraint
- [x] Tabla texture_overlay_cache creada en PostgreSQL
- [x] Servicio generate_texture_overlay() con 3 kernels
- [x] Paleta de colores percentil (azul/púrpura/naranja)
- [x] Interpretaciones dinámicas por kernel
- [x] CRUD get_cached_overlay() y save_overlay_cache()
- [x] Endpoint GET /api/texture/overlay/{ndvi_result_id}
- [x] Cache policy (primera=false, siguientes=true, force)
- [x] Ownership verification (JWT + polygon check)
- [x] Tests manuales: 3 kernels × 2 llamadas + force
- [x] BD con datos verificados (3 rows, ~40KB cada uno)
- [x] Docker-compose build exitoso
- [x] Logs sin errores
- [x] Commit y merge a main
- [x] Push a remoto
- [x] Documentación de evidencia

---

## 🚀 PRÓXIMOS PASOS

1. **Frontend:** Implementar visualización según `FRONTEND_SPEC_OVERLAYS.md`
   - Nivel 1: Radio toggle "Textura" + dropdown kernel en mapa
   - Nivel 2: TextureWidget con imagen + interpretación + dropdown

2. **Sincronización dropdown:** Si usuario cambia kernel en widget, actualizar el overlay del mapa (y viceversa)

3. **Optimización (opcional):**
   - Pre-generar overlays de textura al calcular NDVI
   - Endpoint batch para cargar múltiples kernels en paralelo

---

## 📝 LIMITACIONES CONOCIDAS

1. **Bounds recalculados:** Los bounds se extraen del TIFF en cada llamada cacheada. Se podría optimizar guardándolos en BD.

2. **Sin invalidación automática:** Si se recalcula el NDVI, los overlays de textura cacheados quedan obsoletos. Considerar CASCADE delete o invalidación manual.

3. **Interpretaciones estáticas:** Los umbrales (0.05, 0.12, etc.) son fijos. En un sistema productivo, se calibrarían según región/cultivo.

4. **Un solo NDVI por overlay:** La textura se calcula sobre el NDVI actual. Para comparar texturas temporales, se necesitarían múltiples llamadas.

---

## 🔬 METODOLOGÍA CIENTÍFICA

Los kernels implementados siguen la metodología OE4:

- **Laplaciano** (edges): Operador de segunda derivada para detectar bordes internos
- **Varianza local** (homogeneity): Cuantifica heterogeneidad espacial
- **Magnitud gradiente** (contrast): Operadores Sobel para detectar cambios direccionales

**Referencias:**
- `docs/metodologia_textura_OE4.md v2.1`
- Sección 3: Operadores convolucionales
- Sección 4: Normalización y criterio discriminativo

---

**Endpoint listo para uso en frontend. Ver `FRONTEND_SPEC_OVERLAYS.md` para especificación completa de integración.**
