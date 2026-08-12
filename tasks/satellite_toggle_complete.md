# Satellite Image Toggle - Implementation Complete ✅

**Fecha:** 2026-08-12  
**OE:** OE3 y OE4 (Segmentación y Textura)  
**Feature:** Toggle para mostrar imagen satelital RGB como fondo en widgets de análisis

---

## 🎯 Objetivo

Agregar un toggle "Imagen Satélite" en SegmentationPanel y TextureWidget que muestre la foto real del campo (RGB true color) como capa de fondo debajo del overlay de análisis.

---

## ✅ Implementación Backend

### 1. Base de datos
- ✅ **Columna** `satellite_png BYTEA` agregada a tabla `ndvi_results`
- ✅ **Migración**: `backend/migrations/add_satellite_png_column.sql`
- ✅ **Modelo**: Campo `satellite_png: Optional[bytes]` en `NDVIResult`

### 2. Servicios
- ✅ **`satellite_image_service.py`**: Función `generate_satellite_png(tiff_bytes, polygon_geojson)`
  - Convierte TIFF RGB (3 bandas) a PNG RGBA
  - Aplica máscara de polígono con `rasterio.features.geometry_mask()`
  - Píxeles fuera del polígono → transparentes (alpha=0)
  - Píxeles dentro → RGB original + alpha=255
  - Retorna: `(png_bytes, leaflet_bounds)`

- ✅ **`process_client.py`**: Método `download_true_color_tiff()`
  - Descarga imagen RGB true color como TIFF georreferenciado
  - Usa evalscript con bandas B04, B03, B02
  - `response_format="image/tiff"` (no PNG)

- ✅ **`sentinel_service.py`**: Wrapper `download_true_color_tiff()`

### 3. Endpoints
- ✅ **`GET /api/ndvi/{acquisition_id}/satellite-image`**
  - Query params: `?force=false` (para invalidar cache)
  - Verifica ownership del usuario
  - Revisa cache en BD (`ndvi_result.satellite_png`)
  - Si no existe:
    1. Descarga TIFF true color desde Sentinel Hub
    2. Aplica máscara de polígono
    3. Guarda PNG en BD
  - Retorna:
    ```json
    {
      "image_base64": "iVBORw0KG...",
      "bounds": [[lat_south, lng_west], [lat_north, lng_east]],
      "cached": true,
      "metadata": {
        "date": "2025-03-15",
        "polygon_id": 1,
        "type": "true_color"
      }
    }
    ```

### 4. CRUD
- ✅ **`ndvi.py`**: Función `update_satellite_cache(db, ndvi_result_id, png_bytes)`
  - UPDATE atómico de campo `satellite_png`

---

## ✅ Implementación Frontend

### 1. Context
- ✅ **`OverlayContext.tsx`**: Cache compartido de imágenes satelitales
  - `satelliteCache: Map<number, SatelliteImageResponse>`
  - `getCachedSatelliteImage(acquisitionId)`
  - `fetchSatelliteImage(acquisitionId, force?)`
  - Request deduplication con `inFlight` map
  - Write versioning para evitar race conditions
  - Cache invalidation al cambiar usuario (`ensureOwner()`)

### 2. Hook
- ✅ **`hooks/useSatelliteImage.ts`**: Hook reutilizable
  - Retorna: `{ data, loading, error, load }`
  - Auto-load de cache si existe
  - Fetch on-demand con `load(force?)`
  - Integración con `showOverlayError` del contexto

### 3. Componentes

#### SegmentationPanel
- ✅ State local: `showSatellite` (false por default)
- ✅ Toggle checkbox: "Imagen satélite"
- ✅ Lazy loading: Solo fetch al activar toggle por primera vez
- ✅ Composición de capas:
  ```tsx
  {showSatellite && satellite.data ? (
    <div className="relative">
      <img src="..." className="absolute inset-0" />
      <div className="relative" style={{ opacity: 0.65 }}>
        <NDVIOverlayPreview />
      </div>
    </div>
  ) : (
    <NDVIOverlayPreview />
  )}
  ```

#### TextureWidget
- ✅ Misma implementación que SegmentationPanel
- ✅ Prop `acquisitionId` agregada y propagada desde `ParcelAnalysisWidgets`
- ✅ Toggle checkbox con estilo violeta (acorde al widget)

---

## 🔧 Arquitectura de Cache

### Estrategia de 3 niveles:

1. **Base de datos** (persistente):
   - `ndvi_results.satellite_png` (BYTEA)
   - TTL: infinito (datos satelitales no cambian)
   - Invalidación manual: `?force=true`

2. **Frontend Context** (sesión):
   - `OverlayContext.satelliteCache`
   - Compartido entre SegmentationPanel y TextureWidget
   - Se limpia al cambiar usuario
   - Deduplicación automática de requests

3. **Componente local** (UI):
   - State `showSatellite` (false → true → se dispara fetch)
   - Lazy loading para optimizar ancho de banda

---

## 🎨 Diseño Visual

### Cuando toggle OFF (default):
- Solo se muestra el overlay NDVI/Textura
- No transparencia, sin imagen de fondo

### Cuando toggle ON:
1. **Capa de fondo** (z-index bajo):
   - Imagen satelital RGB true color
   - Opacity: 1.0 (opaca)
   - Posición: `absolute inset-0`

2. **Capa de overlay** (z-index alto):
   - NDVI/Textura coloreado
   - Opacity: 0.65 (semi-transparente)
   - Posición: `relative`

**Resultado:** Se ve la foto real del campo con el análisis coloreado encima (como visor térmico sobre foto).

---

## 🧪 Testing

### Backend:
- ✅ Tests en `test_polygon_mask_overlay.py` verifican transparencia fuera del polígono
- ✅ Validación de respuesta del endpoint `satellite-image`

### Frontend:
- ✅ Servidor dev corriendo sin errores de compilación
- ✅ TypeScript pasa (interfaces correctas)

### Docker:
- ✅ Contenedores corriendo (backend, frontend, db)
- ✅ Columna `satellite_png` creada correctamente
- ✅ Endpoint accesible en http://localhost:8000/api/ndvi/{id}/satellite-image

---

## 📊 Evidencia

```bash
# Base de datos
$ docker exec -i precision-agriculture-db psql -U postgres -d precision \
  -c "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'ndvi_results' AND column_name = 'satellite_png';"

  column_name  | data_type 
---------------+-----------
 satellite_png | bytea
(1 row)

# Frontend dev server
$ npm run dev
✓ Ready in 973ms
▲ Next.js 16.1.1 (Turbopack)
- Local: http://localhost:3001

# Docker containers
$ docker-compose ps
NAME                             STATUS                   PORTS
precision-agriculture-backend    Up 8 minutes             0.0.0.0:8000->8000/tcp
precision-agriculture-db         Up 8 minutes (healthy)   0.0.0.0:5432->5432/tcp
precision-agriculture-frontend   Up 8 minutes             0.0.0.0:3000->3000/tcp
```

---

## 🚀 Próximos pasos sugeridos

1. **Prueba manual end-to-end**:
   - Login → seleccionar parcela con NDVI/textura calculados
   - Ir a dashboard → activar toggle "Imagen satélite"
   - Verificar que carga correctamente
   - Verificar que overlay se ve semi-transparente encima

2. **Optimizaciones opcionales**:
   - Agregar control de opacidad con slider (0.4 - 0.8)
   - Botón de descarga de imagen satelital
   - Preload de imagen satelital en segundo plano

3. **Documentación**:
   - Actualizar CLAUDE.md con estado de OE3/OE4
   - Screenshots para evidencia de PEG

---

## 📝 Archivos Modificados

### Backend (7 archivos):
- `backend/app/api/endpoints/ndvi.py` (+ endpoint satellite-image)
- `backend/app/services/satellite_image_service.py` (nuevo)
- `backend/app/services/sentinel/process_client.py` (+ download_true_color_tiff)
- `backend/app/services/sentinel/sentinel_service.py` (+ wrapper)
- `backend/app/models/analysis.py` (+ satellite_png field)
- `backend/app/crud/ndvi.py` (+ update_satellite_cache)
- `backend/migrations/add_satellite_png_column.sql` (nuevo)

### Frontend (5 archivos):
- `frontend/app/context/OverlayContext.tsx` (+ satellite cache)
- `frontend/app/hooks/useSatelliteImage.ts` (nuevo)
- `frontend/app/components/organisms/SegmentationPanel.tsx` (+ toggle)
- `frontend/app/components/organisms/TextureWidget.tsx` (+ toggle)
- `frontend/app/components/ParcelAnalysisWidgets.tsx` (+ prop acquisitionId)

---

**Estado:** ✅ COMPLETO — Backend + Frontend implementados y corriendo
