# 📍 Resumen: Corrección de Coordenadas Frontend

## 🎯 Problema resuelto

El frontend enviaba coordenadas en formato **`[lat, lng]`** (Leaflet) pero el backend esperaba **`[lng, lat]`** (GeoJSON estándar).

## ✅ Archivos modificados/creados

### Nuevos archivos:

1. **`frontend/app/utils/coordUtils.ts`** ⭐
   - Funciones de conversión entre formatos
   - `leafletToGeoJSON()` - `[lat, lng]` → `[lng, lat]`
   - `geoJSONToLeaflet()` - `[lng, lat]` → `[lat, lng]`
   - Validación y detección automática de formato

2. **`frontend/test_data/test_madrid.geojson`**
   - GeoJSON de prueba (Madrid, España)

3. **`frontend/test_data/test_venezuela.geojson`**
   - GeoJSON de prueba (Guárico, Venezuela)

4. **`backend/migrate_coords.sql`**
   - Script SQL para migrar datos existentes si es necesario

5. **`frontend/COORD_FIX.md`**
   - Documentación detallada del problema y solución

6. **`RESUMEN_COORD_FIX.md`**
   - Este archivo

### Archivos modificados:

7. **`frontend/app/components/LeafletMap.tsx`**
   - ✅ Importa `leafletToGeoJSON` y `geoJSONToLeaflet`
   - ✅ Al **crear** polígono: convierte `[lat, lng]` → `[lng, lat]` antes de enviar
   - ✅ Al **cargar** polígonos: convierte `[lng, lat]` → `[lat, lng]` para mostrar

8. **`frontend/app/nueva-parcela/page.tsx`**
   - ✅ **Remueve** la inversión incorrecta de coordenadas
   - ✅ GeoJSON ahora se envía tal cual al backend (ya viene en formato correcto)

## 🔄 Flujo correcto

### Dibujar en mapa → Backend:
```
Usuario dibuja → Leaflet [lat, lng] → leafletToGeoJSON()
→ Backend [lng, lat] ✅
```

### Subir GeoJSON → Backend:
```
Archivo GeoJSON [lng, lat] → NO INVERTIR
→ Backend [lng, lat] ✅
```

### Backend → Mostrar en mapa:
```
Backend [lng, lat] → geoJSONToLeaflet()
→ Leaflet [lat, lng] ✅
```

## 🧪 Cómo probar

### 1. Probar con archivo GeoJSON

```bash
cd frontend

# Iniciar dev server
npm run dev

# Ve a http://localhost:3000/nueva-parcela
# Tab "Subir Archivo"
# Sube: test_data/test_madrid.geojson o test_data/test_venezuela.geojson
# Verifica que se muestre en la ubicación correcta en el mapa
```

### 2. Dibujar polígono manualmente

```bash
# Ve a http://localhost:3000/
# Usa la herramienta de dibujo de Leaflet (icono ⬢)
# Dibuja un polígono en una ubicación conocida
# Verifica en la base de datos que las coordenadas sean [lng, lat]
```

**Verificar en PostgreSQL:**
```sql
-- Conectar a la BD
psql -U postgres -d precision

-- Ver último polígono creado
SELECT id, name, coordinates[1:2] FROM polygons ORDER BY id DESC LIMIT 1;

-- Verificar formato:
-- ✅ Correcto: [[-67.47, 8.89], [-67.47, 8.89], ...]  (lng < 10)
-- ❌ Incorrecto: [[8.89, -67.47], [8.89, -67.47], ...]  (lat primero)
```

### 3. Migrar datos existentes (si aplica)

Si ya tienes polígonos guardados con coordenadas invertidas:

```bash
cd backend

# Conectar a PostgreSQL
psql -U postgres -d precision

# Ejecutar script de migración
\i migrate_coords.sql

# Seguir las instrucciones en el script
```

## 🔍 Debugging

### Problema: Los polígonos no se muestran en el mapa

**Posibles causas:**

1. **Coordenadas fuera de rango**
   ```sql
   -- Verificar rangos
   SELECT
       id,
       (coordinates[1]->0)::numeric as lng_first,
       (coordinates[1]->1)::numeric as lat_first
   FROM polygons;

   -- lng debe estar en [-180, 180]
   -- lat debe estar en [-90, 90]
   ```

2. **Formato aún invertido**
   ```javascript
   // En LeafletMap.tsx, agregar temporalmente:
   console.log('Coords desde backend:', polygons[0]?.coordinates);
   console.log('Formato detectado:', detectCoordFormat(polygons[0]?.coordinates));
   ```

3. **Mapa no centrado en la región correcta**
   ```typescript
   // LeafletMap.tsx línea 17
   // Ajustar center según tu región:
   const map = L.map('map', {
       center: [10.441, -66.3584],  // Venezuela
       zoom: 7
   });
   ```

### Herramienta online para validar GeoJSON

https://geojson.io/

- Pega tu GeoJSON
- Verifica que se muestre en la ubicación correcta
- Si aparece en el océano o en el lugar incorrecto → coordenadas invertidas

## 📊 Formato de coordenadas por región

Para verificar que el formato es correcto:

### España (Madrid):
```json
[[-3.7038, 40.4168]]
  ↑       ↑
  lng     lat
  (-3°)   (40°)
```

### Venezuela (Guárico):
```json
[[-67.477, 8.890]]
  ↑        ↑
  lng      lat
  (-67°)   (9°)
```

### Regla rápida:
- **Longitud** (lng): Valores más grandes en magnitud (ej: -67, -180, 150)
- **Latitud** (lat): Valores más pequeños en magnitud (ej: 8, 40, -45)
- En España/Venezuela: lng es negativo, lat es positivo pequeño

## ✅ Checklist final

- [ ] `coordUtils.ts` creado con funciones de conversión
- [ ] `LeafletMap.tsx` actualizado (importa y usa utilidades)
- [ ] `nueva-parcela/page.tsx` actualizado (NO invierte GeoJSON)
- [ ] Archivos de prueba creados (`test_*.geojson`)
- [ ] Script de migración creado (`migrate_coords.sql`)
- [ ] Documentación creada (`COORD_FIX.md`)
- [ ] Probar: Dibujar polígono → guardar → mostrar correctamente
- [ ] Probar: Subir GeoJSON → guardar → mostrar correctamente
- [ ] Verificar: Coordenadas en BD tienen formato `[lng, lat]`

## 🎯 Objetivo avanzado

**OE6 (Interfaz de Usuario)** - Corrección de manejo de coordenadas geoespaciales

Este fix es fundamental para que:
- ✅ Los polígonos se guarden en el formato estándar GeoJSON
- ✅ El backend pueda usar las coordenadas correctamente con Sentinel-2
- ✅ Los mapas se muestren en las ubicaciones correctas
- ✅ Futuros cálculos geoespaciales funcionen correctamente

---

## 📝 Notas importantes

1. **GeoJSON es el estándar**: Siempre `[lng, lat]`
2. **Leaflet es la excepción**: Usa `[lat, lng]` por convención geográfica
3. **Siempre convertir explícitamente**: Nunca asumir el formato
4. **Validar en múltiples puntos**: Backend, frontend, archivos subidos
5. **Documentar el formato**: En comentarios y documentación

---

¿Necesitas ayuda con la migración de datos existentes o con las pruebas? 🚀
