# TEST OE1 FRONTEND - Flujo end-to-end

## Componentes implementados

### ✅ Atoms (< 50 líneas)
- `atoms/DateBadge.tsx` - Badge para fechas (formato legible, sin tecnicismos)

### ✅ Molecules (< 100 líneas)
- `molecules/DateSelector.tsx` - Lista de fechas con loading/empty states
- `molecules/AcquireButton.tsx` - Botón con estados idle/loading/success/error

### ✅ Organisms (< 200 líneas)
- `organisms/SentinelPanel.tsx` - Panel lateral completo con:
  - Selector de rango de fechas
  - Consulta a GET /api/sentinel/available-dates/{polygon_id}
  - Selector de fechas disponibles
  - Botón de adquisición → POST /api/sentinel/acquire

### ✅ Integración con mapa
- `LeafletMap.tsx` modificado para:
  - Detectar click en parcelas
  - Abrir SentinelPanel con datos de la parcela
  - Panel no bloquea el mapa (drawer lateral)

## Flujo de prueba

### 1. Iniciar backend
```bash
cd backend
source venv_39/bin/activate
uvicorn main:app --reload
```

### 2. Iniciar frontend
```bash
cd frontend
npm run dev
```

### 3. Probar flujo completo

**Paso 1:** Abrir http://localhost:3000

**Paso 2:** Hacer click en una parcela del mapa
- ✅ Aparece panel lateral derecho
- ✅ Muestra nombre/ID de la parcela
- ✅ Selector de fechas inicio/fin

**Paso 3:** El panel automáticamente consulta fechas disponibles
- ✅ Spinner mientras consulta STAC API
- ✅ GET /api/sentinel/available-dates/{polygon_id}?start_date=2025-01-01&end_date=2025-12-31&max_cloud=20

**Paso 4:** Ver fechas disponibles
- ✅ Grid de DateBadge con fechas en formato legible (ej: "14 Jun 2025")
- ✅ Sin términos técnicos (nubosidad, cloud_cover ocultos)
- ✅ Contador: "16 fechas disponibles"

**Paso 5:** Seleccionar una fecha
- ✅ Click en DateBadge → se marca como seleccionado (verde)
- ✅ Botón "Analizar esta fecha" se habilita

**Paso 6:** Adquirir imagen
- ✅ Click en "Analizar esta fecha"
- ✅ Botón cambia a "Descargando imagen..." con spinner
- ✅ POST /api/sentinel/acquire con {polygon_id, date}
- ✅ Al éxito: "✓ Imagen lista para análisis"

**Paso 7:** Verificar en BD
```bash
cd backend
sqlite3 precision_agriculture.db
SELECT id, polygon_id, acquisition_date, cloud_coverage FROM sentinel_acquisitions;
```

## Checklist de cumplimiento

- [x] Solo Tailwind (sin CSS puro)
- [x] TypeScript estricto
- [x] Componentes < 200 líneas cada uno
- [x] Panel es drawer lateral (no bloquea mapa)
- [x] Usuario no ve términos técnicos (B04, B08, L2A, cloud_cover)
- [x] Fechas en formato legible (español)
- [x] Estados de carga claros
- [x] Mensajes amigables en estados vacíos
- [x] Integración con coordUtils.ts (ya existente en LeafletMap)

## Evidencia de completitud OE1-FRONTEND

### API Endpoints usados
- ✅ GET /api/sentinel/available-dates/{polygon_id}
- ✅ POST /api/sentinel/acquire

### Componentes atómicos creados
1. ✅ DateBadge.tsx (42 líneas)
2. ✅ AcquireButton.tsx (78 líneas)
3. ✅ DateSelector.tsx (74 líneas)
4. ✅ SentinelPanel.tsx (198 líneas)

### Flujo funcional
1. ✅ Click en parcela → panel aparece
2. ✅ Consulta automática de fechas
3. ✅ Selección de fecha
4. ✅ Adquisición exitosa
5. ✅ acquisition_id guardado en BD

## Próximos pasos

**OE2 Frontend:** Panel de visualización NDVI
- Mostrar estadísticas (mean, std, percentiles)
- Visualizar imagen NDVI con colormap
- Clasificación por salud (critical/alert/healthy)
