# 🗺️ Corrección de Formato de Coordenadas

## 🎯 Problema identificado

El frontend estaba enviando coordenadas en formato **incorrecto** al backend:

- **Leaflet usa internamente:** `[latitude, longitude]` = `[lat, lng]`
- **GeoJSON estándar requiere:** `[longitude, latitude]` = `[lng, lat]`
- **Backend espera:** GeoJSON estándar `[lng, lat]`

### ❌ Comportamiento anterior:

1. **LeafletMap.tsx**: Dibujaba polígono → enviaba `[lat, lng]` ❌
2. **nueva-parcela/page.tsx**: Leía GeoJSON `[lng, lat]` → **invertía** a `[lat, lng]` → enviaba ❌
3. **Backend**: Recibía `[lat, lng]` → guardaba como está ❌
4. **LeafletMap.tsx**: Leía del backend → asumía `[lat, lng]` → mostraba incorrectamente ❌

**Resultado:** Las coordenadas se guardaban y mostraban invertidas.

## ✅ Solución implementada

### 1. Utilidad de conversión creada

**Archivo:** `frontend/app/utils/coordUtils.ts`

Funciones agregadas:
- `leafletToGeoJSON()` - Convierte `[lat, lng]` → `[lng, lat]`
- `geoJSONToLeaflet()` - Convierte `[lng, lat]` → `[lat, lng]`
- `validateGeoJSONCoords()` - Valida que las coordenadas sean válidas
- `detectCoordFormat()` - Detecta automáticamente el formato

**Ejemplo de uso:**
```typescript
import { leafletToGeoJSON, geoJSONToLeaflet } from '@/app/utils/coordUtils';

// Al enviar al backend (desde Leaflet)
const leafletCoords = [[40.4168, -3.7038], [40.4268, -3.7038]];
const geoJsonCoords = leafletToGeoJSON(leafletCoords);
// Result: [[-3.7038, 40.4168], [-3.7038, 40.4268]]

// Al recibir del backend (para Leaflet)
const backendCoords = [[-3.7038, 40.4168], [-3.7038, 40.4268]];
const leafletCoords = geoJSONToLeaflet(backendCoords);
// Result: [[40.4168, -3.7038], [40.4268, -3.7038]]
```

### 2. Componentes actualizados

#### `LeafletMap.tsx`

**Cambio 1: Al crear polígono**

```typescript
// ❌ ANTES (línea 56)
const coords = (layer.getLatLngs()[0] as L.LatLng[]).map((pt) => [pt.lat, pt.lng]);
createPolygon({ name: `Parcela ...`, coordinates: coords });

// ✅ AHORA
const leafletCoords = (layer.getLatLngs()[0] as L.LatLng[]).map((pt) => [pt.lat, pt.lng]);
const geoJsonCoords = leafletToGeoJSON(leafletCoords);
createPolygon({ name: `Parcela ...`, coordinates: geoJsonCoords });
```

**Cambio 2: Al renderizar polígonos**

```typescript
// ❌ ANTES (línea 77)
L.polygon(poly.coordinates.map((c) => L.latLng(c[0], c[1])), {...})

// ✅ AHORA
const leafletCoords = geoJSONToLeaflet(poly.coordinates);
L.polygon(leafletCoords.map((c) => L.latLng(c[0], c[1])), {...})
```

#### `nueva-parcela/page.tsx`

**Cambios en líneas 26 y 46:**

```typescript
// ❌ ANTES
const coords = data.geometry.coordinates[0].map((coord: number[]) => [coord[1], coord[0]]);
await createPolygon({ name, coordinates: coords });

// ✅ AHORA
// GeoJSON ya viene en formato correcto [lng, lat]
// NO invertir - enviar directamente al backend
const coords = data.geometry.coordinates[0];
await createPolygon({ name, coordinates: coords });
```

## 📊 Flujo correcto ahora

### Desde Leaflet (dibujo manual):

```
Usuario dibuja polígono en mapa
    ↓
Leaflet devuelve [lat, lng]
    ↓
leafletToGeoJSON() → [lng, lat]
    ↓
Enviar a backend [lng, lat] ✅
    ↓
Backend guarda [lng, lat] en PostgreSQL
```

### Desde archivo GeoJSON:

```
Usuario sube archivo GeoJSON
    ↓
Leer: [lng, lat] (ya correcto)
    ↓
Enviar directo a backend [lng, lat] ✅
    ↓
Backend guarda [lng, lat] en PostgreSQL
```

### Al cargar del backend:

```
Backend devuelve [lng, lat]
    ↓
geoJSONToLeaflet() → [lat, lng]
    ↓
Leaflet muestra correctamente ✅
```

## 🧪 Cómo probar

### Opción 1: Dibujar en mapa

1. Ve al mapa principal
2. Dibuja un polígono conocido
3. Verifica en la base de datos que las coordenadas sean `[lng, lat]`

**Verificación en psql:**
```sql
SELECT id, name, coordinates FROM polygons ORDER BY id DESC LIMIT 1;
```

**Coordenadas esperadas (ejemplo Madrid):**
```json
[[-3.7038, 40.4168], [-3.7038, 40.4268], ...]
```
- Primer valor: `-3.7038` (longitud, debe ser ~ -180 a 180)
- Segundo valor: `40.4168` (latitud, debe ser ~ -90 a 90)

### Opción 2: Subir GeoJSON

1. Ve a "Nueva Parcela" → "Subir Archivo"
2. Sube un GeoJSON con coordenadas conocidas
3. Verifica que se guarde correctamente en la BD
4. Verifica que se muestre en el mapa en la ubicación correcta

**GeoJSON de prueba (Madrid):**
```json
{
  "type": "Feature",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[
      [-3.7038, 40.4168],
      [-3.7038, 40.4268],
      [-3.6938, 40.4268],
      [-3.6938, 40.4168],
      [-3.7038, 40.4168]
    ]]
  },
  "properties": {
    "name": "Test Madrid"
  }
}
```

### Opción 3: Verificar polígonos existentes

Si ya tienes polígonos guardados con coordenadas invertidas:

1. **Migrar datos existentes:**

```sql
-- Script para invertir coordenadas existentes (ejecutar UNA VEZ)
UPDATE polygons
SET coordinates = (
  SELECT json_agg(
    json_build_array(
      (coord->1)::numeric,
      (coord->0)::numeric
    )
  )
  FROM json_array_elements(coordinates::json) AS coord
)
WHERE id > 0;  -- Ajustar condición según sea necesario
```

2. **Recargar el frontend** para ver los cambios

## 🔍 Debug de coordenadas

Si los polígonos no se muestran correctamente:

### 1. Verificar en backend (PostgreSQL):

```sql
-- Ver las coordenadas crudas
SELECT id, name, coordinates[1:2] FROM polygons;

-- Si el primer valor es < 10, probablemente está mal (es latitud en vez de longitud)
-- Correcto para España: longitud ~ -10 a 5
-- Correcto para Venezuela: longitud ~ -73 a -59
```

### 2. Verificar en frontend (Console de DevTools):

```javascript
// En LeafletMap.tsx, agregar console.log temporal:
console.log('Polígono desde backend:', poly.coordinates);
console.log('Después de conversión:', geoJSONToLeaflet(poly.coordinates));
```

### 3. Usar función de detección:

```typescript
import { detectCoordFormat } from '@/app/utils/coordUtils';

const format = detectCoordFormat(coordinates);
console.log('Formato detectado:', format);
// "geojson" → [lng, lat] ✅
// "leaflet" → [lat, lng] ❌ (necesita conversión)
```

## 📝 Checklist de verificación

- [ ] Dibujar polígono en mapa → se guarda con `[lng, lat]`
- [ ] Polígono guardado se muestra correctamente en el mapa
- [ ] Subir GeoJSON → se guarda sin invertir coordenadas
- [ ] GeoJSON subido se muestra correctamente
- [ ] Polígonos existentes (si aplica) fueron migrados
- [ ] No hay errores en la consola del navegador
- [ ] Coordenadas en BD tienen formato: `[[-X.XX, Y.YY], ...]` (lng primero)

## 🔗 Referencias

- **GeoJSON Spec**: https://datatracker.ietf.org/doc/html/rfc7946#section-3.1.1
  > "A position is an array of numbers. There MUST be two or more elements. The first two elements are longitude and latitude"

- **Leaflet LatLng**: https://leafletjs.com/reference.html#latlng
  > "Represents a geographical point with a certain latitude and longitude."

- **PostGIS Geography**: https://postgis.net/docs/using_postgis_dbmanagement.html#PostGIS_Geography
  > "Geography types always use WGS84 lon/lat coordinate system"

## 🚨 IMPORTANTE

**NO mezclar formatos:** Siempre convertir explícitamente usando las funciones de utilidad.

**Regla de oro:**
- **Enviar al backend**: Siempre `[lng, lat]` (usar `leafletToGeoJSON`)
- **Leer del backend**: Siempre convertir a `[lat, lng]` (usar `geoJSONToLeaflet`)
- **Archivos GeoJSON**: Ya vienen como `[lng, lat]`, NO invertir
