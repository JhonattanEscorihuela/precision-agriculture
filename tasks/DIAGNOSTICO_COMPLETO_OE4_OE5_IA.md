# DIAGNÓSTICO COMPLETO — OE4, OE5 E INTELIGENCIA ARTIFICIAL

**Fecha**: 2026-08-21  
**Rama**: `feature/oe5-temporal-comparison-and-export`  
**Auditoría solicitada por**: Usuario (revisión exhaustiva antes de continuar implementación)

---

## FASE 1: AUDITORÍA OE4 — EVALUAR DESCRIPTORES DE TEXTURA POR FILTRADO CONVOLUCIONAL

### 1.1 ESTADO DECLARADO EN CLAUDE.MD

```
### OE4 — Evaluar descriptores de textura ✅ IMPLEMENTACIÓN COMPLETA
- ✅ Bordes, homogeneidad y contraste mediante filtrado convolucional
- ✅ Estadísticos, normalización, persistencia, overlays y widget de dashboard
- ✅ Trazabilidad completa y puerta de calidad heredada de OE3/NDVI
- ⚠️ Validación agronómica parcial: falta asociar respuestas con clases de campo
```

### 1.2 VERIFICACIÓN EN CÓDIGO — BACKEND

#### ✅ Modelo de datos (persistencia)
**Archivo**: `backend/app/models/texture.py` (121 líneas)

- **Tabla**: `texture_descriptors`
- **Campos principales**:
  - `segmentation_result_id` (FK → segmentation_results)
  - `polygon_id` (FK → polygon)
  - `kernel_type`: `'edges'`, `'homogeneity'`, `'contrast'`
  - Estadísticos: `mean`, `std`, `min_val`, `max_val`
  - Normalización: `std_normalized`, `discriminative` (bool)
  - Timestamps: `calculation_date`, `created_at`
- **Constraint UNIQUE**: `(segmentation_result_id, kernel_type)` — permite 3 descriptores por segmentación
- **Cascade**: DELETE ON CASCADE (trazabilidad limpia)

**Veredicto**: ✅ **Modelo completo y bien diseñado**

---

#### ✅ Servicio de cálculo
**Archivo**: `backend/app/services/texture_service.py` (471 líneas)

**Clase principal**: `TextureService`

**Kernels convolucionales implementados**:

1. **Laplaciano (edges)**:
   ```python
   KERNEL_EDGES = [[0, 1, 0],
                   [1, -4, 1],
                   [0, 1, 0]]
   ```
   Detecta transiciones abruptas (bordes internos).

2. **Varianza local (homogeneity)**:
   ```python
   variance_local = E[I²] - (E[I])²
   ```
   Cuantifica heterogeneidad espacial.

3. **Magnitud del gradiente (contrast)**:
   ```python
   Gx = convolve(NDVI, KERNEL_GX)  # Sobel horizontal
   Gy = convolve(NDVI, KERNEL_GY)  # Sobel vertical
   magnitude = sqrt(Gx² + Gy²)
   ```
   Mide cambios direccionales.

**Metodología científica**:
- ✅ Convolución sobre NDVI completo (no sobre máscara binaria)
- ✅ Erosión morfológica de 1 píxel (evita contaminación de bordes)
- ✅ Reemplazo de NaN con 0.0 (evita propagación)
- ✅ Normalización min-max a [0, 1]
- ✅ Criterio discriminativo: `std_normalized > 0.10` (τ_norm)

**Flujo completo** (`calculate_texture()`):
1. Idempotencia: verifica si ya existen 3 descriptores
2. Obtiene SegmentationResult y verifica ownership
3. Valida puerta de calidad (acquisition.quality_status == "suitable")
4. Valida máscara SCL aplicada (cloud_mask_applied == True)
5. Lee NDVI TIFF desde BD
6. Regenera máscara cultivada (threshold de segmentación)
7. Aplica erosión morfológica
8. Calcula 3 operadores convolucionales
9. Guarda 3 descriptores en BD (transacción atómica)

**Veredicto**: ✅ **Implementación científicamente rigurosa** (según `docs/metodologia_textura_OE4.md v2.1`)

---

#### ✅ CRUD
**Archivo**: `backend/app/crud/texture.py`

```python
async def create(db, segmentation_result_id, polygon_id, kernel_type, ...)
async def get_by_segmentation_result_id(db, segmentation_result_id) -> list
async def get_by_id(db, descriptor_id)
async def get_by_polygon(db, polygon_id) -> list
```

**Veredicto**: ✅ **CRUD completo**

---

#### ✅ Endpoints API
**Archivo**: `backend/app/api/endpoints/texture.py` (312 líneas)

**Rutas implementadas**:

1. **POST `/api/texture/analyze`** (líneas 24-92)
   - Body: `{ segmentation_result_id }`
   - Calcula 3 descriptores si no existen (idempotente)
   - Requiere JWT + ownership
   - Response: Lista de 3 `TextureDescriptorResponse`

2. **GET `/api/texture/by-segmentation/{segmentation_result_id}`** (líneas 95-134)
   - Consulta descriptores ya calculados
   - Verifica ownership
   - Response: Lista de 3 descriptores o 404

3. **GET `/api/texture/overlay/{ndvi_result_id}?kernel=X`** (líneas 136-312)
   - Genera PNG coloreado de textura para visualización en mapa
   - Query params: `kernel` (contrast/edges/homogeneity), `force` (bool)
   - Cache policy: primera llamada calcula y guarda, siguientes sirven desde caché
   - Paleta de colores: Azul (uniforme) → Púrpura (moderado) → Naranja (heterogéneo)
   - Interpretaciones dinámicas por kernel
   - Response: `{ image_base64, bounds, kernel, cached, interpretation, metadata }`

**Veredicto**: ✅ **Endpoints completos con autenticación, caché e interpretaciones**

---

#### ✅ Servicio de overlays
**Archivo**: `backend/app/services/texture_overlay_service.py` (170 líneas según `docs/OE4_OVERLAY_EVIDENCE.md`)

- Genera PNG coloreados con paleta percentil
- 3 kernels disponibles
- Interpretaciones dinámicas basadas en valor medio
- Retorna base64 + bounds Leaflet

**Modelo de caché**: `TextureOverlayCache` (tabla `texture_overlay_cache`)
- UNIQUE constraint `(ndvi_result_id, kernel)`
- Almacena PNG como bytea (~40KB por kernel)

**Veredicto**: ✅ **Sistema de overlays completo y cacheado**

---

### 1.3 VERIFICACIÓN EN CÓDIGO — FRONTEND

#### ✅ Widget de textura
**Archivo**: `frontend/app/components/organisms/TextureWidget.tsx` (157 líneas)

**Funcionalidad implementada**:
- Estados: loading, empty, error, success
- Tabla de descriptores (`TextureDescriptorsTable`)
- Preview de overlays (`TextureOverlayPreview`)
- Toggle "Imagen satélite" + "Solo imagen"
- Selector de fecha (si hay múltiples análisis)
- Timestamp de cálculo

**Integración**:
```tsx
<TextureWidget
  ndviResultId={selectedDate?.ndvi_result_id}
  acquisitionId={selectedDate?.acquisition_id}
  availableDates={availableDates}
  onDateChange={handleDateChange}
  state={texture}
  onRetry={...}
/>
```

**Veredicto**: ✅ **Widget completo e integrado en dashboard**

---

#### ✅ Componente tabla de descriptores
**Archivo**: `frontend/app/components/molecules/TextureDescriptorsTable.tsx`

- Muestra 3 filas (edges, homogeneity, contrast)
- Columnas: Descriptor, Promedio, Desv. Estándar, Mín, Máx, Discriminativo
- Indicador visual si descriptor es discriminativo

**Veredicto**: ✅ **Tabla funcional**

---

#### ✅ Componente preview de overlays
**Archivo**: `frontend/app/components/molecules/TextureOverlayPreview.tsx`

- Tabs para seleccionar kernel (Contraste, Bordes, Homogeneidad)
- Muestra overlay coloreado sobre imagen satelital (si activado)
- Interpretación textual del kernel
- Leyenda de colores

**Veredicto**: ✅ **Visualización completa**

---

### 1.4 INTEGRACIÓN EN DASHBOARD

**Archivo**: `frontend/app/components/ParcelAnalysisWidgets.tsx` (192 líneas)

**Flujo de carga de textura**:
1. Carga fechas disponibles filtradas por calidad (solo `suitable`)
2. Para fecha seleccionada:
   - Obtiene o crea segmentación (`getOrCreateSegmentation()`)
   - Obtiene o crea descriptores de textura (`getOrCreateTexture()`)
3. Maneja estados: loading, success, error
4. Recarga al cambiar de fecha (selector sincronizado)

**Veredicto**: ✅ **Integración completa y funcional**

---

### 1.5 TESTS Y VALIDACIÓN

**Tests encontrados**:
- `backend/tests/test_polygon_mask_overlay.py` (menciona textura)
- `backend/tests/generate_overlay_demo.py` (demo de generación)

**Documentación de evidencia**:
- `docs/OE4_OVERLAY_EVIDENCE.md` (2026-08-04, commit `34de01a`)
  - Tests manuales de 3 kernels
  - Verificación de cache policy
  - Storage & performance metrics
  - Integración frontend documentada

- `docs/metodologia_textura_OE4.md` (29.969 bytes, referencia científica)

- `docs/VALIDACION_CIENTIFICA_OE3_OE4.md`
  - **Cobertura técnica**: completa ✅
  - **Validación agronómica**: parcial ⚠️
  - Falta: ground truth de campo, métricas IoU/F1, parcelas independientes

**Veredicto**: ⚠️ **Tests manuales documentados, falta test automatizado end-to-end**

---

### 1.6 PUERTA DE CALIDAD

**Verificación en código** (`texture_service.py` líneas 115-129):

```python
# OE4 solo acepta la cadena trazable: calidad apta + NDVI SCL.
acquisition = await crud_acquisition.get_acquisition_by_id(
    db, ndvi_result.acquisition_id
)
if not ndvi_result.cloud_mask_applied:
    raise HTTPException(
        status_code=409,
        detail="NDVI must be recalculated with the SCL cloud mask before OE4."
    )
if not acquisition or acquisition.quality_status != "suitable":
    quality = acquisition.quality_status if acquisition else "unknown"
    raise HTTPException(
        status_code=409,
        detail=f"Observation quality is {quality}; OE4 requires suitable quality."
    )
```

**Veredicto**: ✅ **Puerta de calidad implementada correctamente**

---

### 1.7 RESUMEN OE4

| Aspecto | Estado | Evidencia |
|---------|--------|-----------|
| **Modelo BD** | ✅ Completo | `texture_descriptors` con 3 kernels por segmentación |
| **Servicio cálculo** | ✅ Completo | 3 operadores convolucionales + erosión + normalización |
| **CRUD** | ✅ Completo | Create, Read by segmentation/polygon/id |
| **Endpoints API** | ✅ Completo | POST analyze, GET by-segmentation, GET overlay |
| **Overlays PNG** | ✅ Completo | Caché de imágenes coloreadas con interpretaciones |
| **Frontend widget** | ✅ Completo | TextureWidget con tabla + preview + selector fecha |
| **Integración dashboard** | ✅ Completo | Carga automática en `/cultivos/[id]` |
| **Puerta calidad** | ✅ Completo | Solo adquisiciones suitable + NDVI con SCL |
| **Tests automatizados** | ⚠️ Parcial | Tests manuales documentados, falta pytest end-to-end |
| **Validación agronómica** | ⚠️ Parcial | Sin ground truth de campo |

**VEREDICTO FINAL OE4**: ✅ **FUNCIONALMENTE COMPLETO**  
**Implementación técnica**: 100%  
**Validación científica**: Exploratoria (limitada por ausencia de ground truth)

---

## QUÉ FALTA PARA OE4 ACADEMICAMENTE DEFENDIBLE

### Tests automatizados
- [ ] `backend/tests/test_oe4_texture_complete.py`
  - Test calcular 3 descriptores sobre parcela real (211)
  - Test idempotencia (segunda llamada retorna mismos resultados)
  - Test puerta de calidad (rechaza adquisiciones unsuitable)
  - Test ownership (rechaza usuario sin acceso)
  - Test overlay caché (primera llamada cached=false, segunda cached=true)

### Documentación de evidencia actualizada
- [x] `docs/OE4_OVERLAY_EVIDENCE.md` existe (2026-08-04)
- [ ] Actualizar con screenshots del widget funcionando
- [ ] Agregar ejemplo de datos reales de parcela 211

### Docker validation
- [ ] `docker-compose up --build` → verificar endpoints OE4 responden
- [ ] Probar flujo manual: calcular textura → ver widget → descargar overlay

---

## FASE 2: AUDITORÍA OE5 — CONSTRUIR LA INTERFAZ INTEGRANDO TODOS LOS SERVICIOS

### 2.1 ESTADO DECLARADO EN CLAUDE.MD

```
### OE5 — Construir interfaz integrada
- ✅ Mapa Leaflet con dibujo de polígonos
- ✅ CRUD parcelas funcionando
- ✅ Panel lateral de adquisición Sentinel-2 (OE1 frontend)
- ✅ Panel visualización NDVI (OE2 frontend)
- ✅ Dashboard individual por parcela con widgets (patrón AWS CloudWatch)
- ✅ Estado de salud basado en datos reales
- ✅ Imagen satelital RGB como capa de fondo en widgets
- ✅ Selector de fecha con recarga sincronizada de análisis
- ✅ Overlays en mapa con filtro de calidad (solo adquisiciones aptas)
- 🔧 PENDIENTE: Comparación temporal multi-fecha, exportación reportes
```

### 2.2 VERIFICACIÓN EN CÓDIGO — PÁGINAS PRINCIPALES

#### ✅ Página home (mapa general)
**Archivo**: `frontend/app/page.tsx`

**Funcionalidad implementada**:
- Mapa Leaflet con todas las parcelas del usuario
- Click en parcela → abre panel lateral con análisis
- Estados: loading, empty, authenticated
- Responsive (sidebar hamburger en mobile)

**Veredicto**: ✅ **Página home completa**

---

#### ✅ Página listado de cultivos
**Archivo**: `frontend/app/cultivos/page.tsx`

**Funcionalidad implementada**:
- Lista de todas las parcelas con:
  - Nombre, área (hectáreas), coordenadas
  - **Estado de salud** (healthy/alert/critical/unknown) basado en último NDVI
  - Badge coloreado por estado
  - Botón "Ver Dashboard" → `/cultivos/[id]`
- Grid responsive (1 col mobile, 2-3 cols desktop)
- Filtro por estado de salud (pendiente según estado declarado)

**Veredicto**: ✅ **Listado completo con estado de salud real**

---

#### ✅ Página dashboard individual
**Archivo**: `frontend/app/cultivos/[id]/page.tsx` (100+ líneas)

**Funcionalidad implementada**:
- Header con:
  - Nombre parcela
  - Área (hectáreas)
  - Coordenadas
  - Botón "← Volver a Cultivos"
- Componente `DateRangeFilter` (filtro temporal)
- Componente `ParcelAnalysisWidgets` (widgets de análisis)
- Loading state
- Error 404 si parcela no existe
- Responsive

**Veredicto**: ✅ **Dashboard completo e integrado**

---

### 2.3 VERIFICACIÓN EN CÓDIGO — WIDGETS DE ANÁLISIS

**Archivo**: `frontend/app/components/ParcelAnalysisWidgets.tsx` (192 líneas)

**Widgets implementados**:

1. **NDVIEvolutionWidget** (OE2)
   - Gráfica temporal de NDVI (últimas 6 fechas)
   - Estadísticos por fecha
   - Imagen satelital de fondo
   - Selector de fecha

2. **SegmentationPanel** (OE3)
   - Overlay de segmentación coloreado
   - Estadísticos de área cultivada
   - Imagen satelital de fondo
   - Selector de fecha sincronizado

3. **TextureWidget** (OE4)
   - Preview de overlays (3 kernels)
   - Tabla de descriptores
   - Imagen satelital de fondo
   - Selector de fecha sincronizado

4. **FenologicalComparisonWidget** (extra)
   - Comparación de estados fenológicos
   - Estado: phenology (cargado desde hook)

**Veredicto**: ✅ **4 widgets implementados e integrados**

---

### 2.4 VERIFICACIÓN EN CÓDIGO — MAPA LEAFLET

**Archivo**: `frontend/app/components/LeafletMap.tsx` (181 líneas según CLAUDE.md)

**Funcionalidad implementada**:
- Dibuja polígonos de parcelas
- Click en parcela → callback con datos
- Overlays de análisis:
  - NDVI coloreado
  - Segmentación
  - Textura (3 kernels)
- **Filtro de calidad**: Solo muestra overlays de adquisiciones aptas (fix 2026-08-19)
- Control de capas (toggle overlays)
- Responsive (ajusta zoom en mobile)

**Veredicto**: ✅ **Mapa completo con overlays filtrados**

---

### 2.5 VERIFICACIÓN EN CÓDIGO — INTEGRACIÓN CON OEs

#### OE1: Adquisición Sentinel-2
**Archivo**: `frontend/app/components/organisms/SentinelPanel.tsx` (288 líneas según CLAUDE.md)

- Consulta fechas disponibles (STAC API)
- Selector de rango temporal
- Botón "Adquirir bandas" (POST /api/sentinel/acquire)
- Estados: loading, success, error
- Integrado en panel lateral del mapa

**Veredicto**: ✅ **OE1 frontend completo**

---

#### OE2: NDVI
**Archivo**: `frontend/app/components/organisms/NDVIPanel.tsx` (282 líneas según CLAUDE.md)

- Cálculo NDVI (POST /api/ndvi/calculate)
- Estadísticos (mean, std, min, max)
- Badge coloreado por valor NDVI
- Descarga TIFF
- Integrado en panel lateral

**Archivo**: `frontend/app/components/organisms/NDVIEvolutionWidget.tsx` (464 líneas según CLAUDE.md)

- Gráfica temporal con Recharts
- Selector de fecha
- Overlay NDVI en mapa
- Imagen satelital de fondo

**Veredicto**: ✅ **OE2 frontend completo**

---

#### OE3: Segmentación
**Archivo**: `frontend/app/components/organisms/SegmentationPanel.tsx` (233 líneas según CLAUDE.md)

- Cálculo segmentación (POST /api/segmentation/analyze)
- Estadísticos de área cultivada
- Overlay coloreado
- Imagen satelital de fondo
- Selector de fecha

**Veredicto**: ✅ **OE3 frontend completo**

---

#### OE4: Textura
**Archivo**: `frontend/app/components/organisms/TextureWidget.tsx` (157 líneas)

- Ya auditado en sección OE4
- Integrado en dashboard individual

**Veredicto**: ✅ **OE4 frontend completo**

---

### 2.6 VERIFICACIÓN EN CÓDIGO — ESTADO DE SALUD

**Archivo**: `frontend/app/hooks/usePolygonHealth.ts` (97 líneas)

**Clasificación implementada**:
```typescript
// Clasificar según valor NDVI
let status: 'healthy' | 'alert' | 'critical' = 'healthy';
if (ndviMean < 0.3) {
  status = 'critical';
} else if (ndviMean < 0.5) {
  status = 'alert';
}
```

**Método**: ❌ **REGLAS HEURÍSTICAS** (umbrales fijos de NDVI)  
**NO es**: Modelo de Machine Learning o Deep Learning entrenado

**Veredicto**: ⚠️ **Estado de salud funcional pero NO basado en IA**

---

### 2.7 VERIFICACIÓN EN CÓDIGO — AUTENTICACIÓN Y SEGURIDAD

**Implementación**:
- ✅ JWT en todas las peticiones (axios interceptors)
- ✅ Login/Register UI
- ✅ ProtectedRoute para rutas privadas
- ✅ AuthContext con token persistido
- ✅ Ownership check en backend (todos los CRUD)
- ✅ Cascade delete de parcelas

**Veredicto**: ✅ **Autenticación completa**

---

### 2.8 VERIFICACIÓN EN CÓDIGO — RESPONSIVE

**Componentes verificados**:
- ✅ Sidebar con hamburger menu (mobile)
- ✅ Dashboard grid adapta columnas (mobile: 1 col, desktop: 2-3 cols)
- ✅ Widgets ajustan tamaño (padding, font-size)
- ✅ Mapa ajusta altura (mobile: vh reducido)
- ✅ Paneles laterales → modales inferiores (mobile)

**Breakpoints Tailwind usados**: `sm:`, `md:`, `lg:`, `xl:`

**Veredicto**: ✅ **Responsive implementado**

---

### 2.9 RESUMEN OE5

| Aspecto | Estado | Evidencia |
|---------|--------|-----------|
| **Mapa Leaflet** | ✅ Completo | Dibuja parcelas, overlays, filtro de calidad |
| **CRUD parcelas** | ✅ Completo | Crear, editar, eliminar, listar |
| **Panel OE1 (Sentinel)** | ✅ Completo | Consulta fechas, adquiere bandas |
| **Panel OE2 (NDVI)** | ✅ Completo | Calcula NDVI, estadísticos, gráfica temporal |
| **Panel OE3 (Segmentación)** | ✅ Completo | Overlay coloreado, área cultivada |
| **Panel OE4 (Textura)** | ✅ Completo | 3 kernels, tabla, preview |
| **Dashboard individual** | ✅ Completo | 4 widgets integrados |
| **Estado de salud** | ✅ Funcional | Basado en NDVI (healthy/alert/critical) |
| **Imagen satelital RGB** | ✅ Completo | Overlay en widgets, toggle "Solo imagen" |
| **Selector de fecha** | ✅ Completo | Sincronizado entre widgets |
| **Overlays filtrados** | ✅ Completo | Solo adquisiciones aptas (fix 2026-08-19) |
| **Autenticación JWT** | ✅ Completo | Login, register, protected routes |
| **Responsive** | ✅ Completo | Mobile-first, breakpoints Tailwind |
| **Comparación multi-fecha** | ❌ Falta | Widget comparativo no implementado |
| **Exportación PDF** | ❌ Falta | Endpoint y botón no implementados |
| **Exportación CSV** | ❌ Falta | Endpoint y botón no implementados |
| **Tests E2E** | ❌ Falta | No hay tests de flujo completo |

**VEREDICTO FINAL OE5**: ⚠️ **85% COMPLETO**  
**Implementación funcional base**: 100%  
**Funcionalidades avanzadas pendientes**: Comparación multi-fecha + Exportación reportes

---

## QUÉ FALTA PARA OE5 ACADEMICAMENTE DEFENDIBLE

### 1. Completar funcionalidades básicas faltantes (NO comparación avanzada ni exportación)

#### a) Tests automatizados E2E
- [ ] Test: Login → Crear parcela → Adquirir bandas → Calcular NDVI → Ver dashboard
- [ ] Test: Cambiar fecha en selector → Verificar recarga de análisis
- [ ] Test: Toggle overlays en mapa → Verificar visibilidad

#### b) Documentación de evidencia
- [ ] Screenshots del dashboard completo (`tasks/oe5_complete.md`)
- [ ] Video/GIF del flujo: mapa → click parcela → panel lateral → dashboard → widgets

#### c) Docker validation
- [ ] `docker-compose up --build` → verificar frontend accesible
- [ ] Flujo manual completo: registrar → login → crear parcela → adquirir → analizar → dashboard

#### d) Manejo de errores mejorado
- [ ] Mensajes de error claros en español
- [ ] Loading states consistentes en todos los widgets
- [ ] Empty states cuando no hay datos

---

### 2. Funcionalidades avanzadas (POSTERGAR según instrucciones)

**NO implementar ahora**:
- ❌ Comparación temporal multi-fecha avanzada (grid 2x2 de mapas sincronizados)
- ❌ Exportación PDF con mapas
- ❌ Exportación CSV con datos tabulares

**Quedarán documentadas como**:
- **Trabajo futuro** en `knowledge/objectives/OE_future_work.md`
- **Out of scope** para entrega inicial de PEG
- **Extensiones propuestas** para desarrollo post-graduación

---

## FASE 3: INVESTIGACIÓN DISCREPANCIA INTELIGENCIA ARTIFICIAL

### 3.1 REFERENCIAS A IA EN DOCUMENTACIÓN ACADÉMICA

#### En el Título del PEG
**Archivo**: `knowledge/references/template/Principal.tex` (línea 50)

```latex
\titulo{DESARROLLO DE UNA INTERFAZ DE USUARIO ORIENTADA A SERVICIOS DE 
CÁLCULO EN LA NUBE CON MODELOS DE INTELIGENCIA ARTIFICIAL PARA ESTUDIOS 
DE AGRICULTURA DE PRECISIÓN EN CULTIVOS DE ARROZ}
```

**Veredicto**: El título **promete** "MODELOS DE INTELIGENCIA ARTIFICIAL"

---

#### En Planteamiento del Problema
**Archivo**: `knowledge/references/template/Capitulos/Capitulo1.tex`

- **Línea 17**: "la inteligencia artificial (IA) de forma que los datos como insumo de entrenamiento de modelos sean directamente la información recolectada en el sitio"

- **Línea 21**: "si los modelos de inteligencia artificial como los de aprendizaje de máquina o aprendizaje profundo pueden ser alimentados con datos que se producen 'in situ'"

**Veredicto**: El planteamiento **asume** uso de modelos ML/DL entrenados

---

#### En Objetivo General
**Archivo**: `knowledge/references/template/Capitulos/Capitulo1.tex` (líneas 44-52)

**Versión aprobada**:
```
Desarrollar una interfaz gráfica de usuario, orientada a servicios de cálculo 
en la nube con modelos de inteligencia artificial para estudios de agricultura 
de precisión en cultivos de arroz.
```

**Veredicto**: El objetivo general **requiere** modelos de IA

---

#### En Objetivos Específicos (Académico 5)
**Archivo**: `knowledge/references/template/Capitulos/Capitulo1.tex` (líneas 87-107, versión Jhonattan)

```
Desarrollar un modelo de inteligencia artificial para la clasificación del 
estado de salud del cultivo de arroz, utilizando como variables de entrada 
el índice NDVI y características de textura espacial obtenidas mediante 
filtrado convolucional
```

**Veredicto**: El objetivo académico 5 **exige explícitamente** un modelo de IA para clasificación

---

#### En Alcance
**Archivo**: `knowledge/references/template/Capitulos/Capitulo1.tex` (líneas 110-112)

```
En cuanto a los modelos que se desarrollarán por razones de complejidad se 
limitarán sólo a clasificación y regresión, bien sea a través de machine 
learning o deep learning, y se espera que al menos existan dos modelos en 
cada modalidad.
```

**Veredicto**: El alcance **especifica**:
- **Mínimo 2 modelos de clasificación** (ML o DL)
- **Mínimo 2 modelos de regresión** (ML o DL)
- **Total**: 4 modelos entrenados

---

#### En Metodología
**Archivo**: `knowledge/references/template/Capitulos/Capitulo3.tex` (líneas 111-152)

**Fase 1: Segmentación General de Zonas Agrícolas**
```
Diseño del modelo base: Implementación de una red neuronal convolucional 
básica U-Net para segmentar áreas agrícolas.
```

**Fase 2: Clasificación Específica de Zonas de Arroz**
```
Rediseño del modelo utilizando la arquitectura ResUNet-a.
Inclusión de bloques residuales y mecanismos de atención.
```

**Veredicto**: La metodología académica **describe arquitecturas concretas** de DL (U-Net, ResUNet-a)

---

#### En Antecedentes
**Archivo**: `knowledge/references/template/Capitulos/Capitulo2.tex` (líneas 13-23)

Cita trabajos con IA:
- **Singh 2025**: Random Forest, SVM, XGBoost, ensambles
- **Onojeghuo 2023**: ResU-Net + Random Forest
- **Panicle-Cloud 2023**: CNN (Panicle-AI) + CatBoost

**Veredicto**: Los antecedentes **establecen precedente** de uso de modelos ML/DL entrenados

---

### 3.2 QUÉ ESTÁ REALMENTE IMPLEMENTADO EN EL SOFTWARE

#### Búsqueda en backend de librerías ML/DL

**Archivo**: `backend/requirements.txt`

```bash
# Búsqueda realizada:
grep -E "sklearn|tensorflow|torch|xgboost|keras" requirements.txt
# Resultado: (vacío)
```

**Librerías instaladas**:
- `numpy==1.24.3` (cálculo numérico)
- `rasterio==1.4.3` (lectura/escritura TIFF)
- `scipy` (convolución, erosión morfológica)

**Librerías NO instaladas**:
- ❌ scikit-learn (Random Forest, SVM, XGBoost)
- ❌ tensorflow / keras (CNN, ResU-Net, U-Net)
- ❌ pytorch (CNN, ResNet)
- ❌ xgboost (regresión/clasificación)

**Veredicto**: ❌ **NO hay librerías de ML/DL instaladas**

---

#### Búsqueda en código de modelos entrenados

**Búsqueda realizada**:
```bash
grep -r "Random Forest\|XGBoost\|CNN\|ResU-Net\|U-Net\|modelo.*entrenad" backend --include="*.py"
# Resultado: Solo menciones en comentarios o nombres de librerías del venv
```

**Archivos buscados**:
- ❌ No existen archivos `.pkl` (modelos scikit-learn)
- ❌ No existen archivos `.h5` / `.keras` (modelos TensorFlow)
- ❌ No existen archivos `.pt` / `.pth` (modelos PyTorch)
- ❌ No existen scripts `train_model.py` o similar
- ❌ No existen carpetas `models/trained/` o similar

**Veredicto**: ❌ **NO existen modelos ML/DL entrenados**

---

#### Análisis del estado de salud (healthy/alert/critical)

**Archivo**: `frontend/app/hooks/usePolygonHealth.ts` (líneas 58-64)

```typescript
// Clasificar según valor NDVI
let status: 'healthy' | 'alert' | 'critical' = 'healthy';
if (ndviMean < 0.3) {
  status = 'critical';
} else if (ndviMean < 0.5) {
  status = 'alert';
}
```

**Método utilizado**: Reglas heurísticas con umbrales fijos
- NDVI < 0.3 → `critical`
- 0.3 ≤ NDVI < 0.5 → `alert`
- NDVI ≥ 0.5 → `healthy`

**NO es**:
- ❌ Modelo Random Forest entrenado con datos etiquetados
- ❌ Red neuronal CNN clasificadora
- ❌ Modelo XGBoost
- ❌ Cualquier modelo que haya pasado por entrenamiento/validación/test

**ES**:
- ✅ Regla if-else con umbrales arbitrarios
- ✅ Sin aprendizaje de datos
- ✅ Sin capacidad de generalización

**Veredicto**: ❌ **NO hay modelo de IA para clasificación de salud**

---

### 3.3 RESUMEN DE LA DISCREPANCIA

| Aspecto | Documentación Académica | Software Implementado | Gap |
|---------|-------------------------|----------------------|-----|
| **Título PEG** | "MODELOS DE INTELIGENCIA ARTIFICIAL" | Reglas heurísticas | ❌ **GAP CRÍTICO** |
| **Objetivo General** | "modelos de inteligencia artificial" | Procesamiento de señales | ❌ **GAP CRÍTICO** |
| **Objetivo Académico 5** | "Desarrollar modelo de IA para clasificación" | Umbrales NDVI fijos | ❌ **GAP CRÍTICO** |
| **Alcance** | "mínimo 2 modelos por modalidad (4 total)" | 0 modelos entrenados | ❌ **4 modelos faltantes** |
| **Metodología Fase 1** | "U-Net para segmentar áreas agrícolas" | Threshold NDVI > 0.3 | ❌ Heurística vs DL |
| **Metodología Fase 2** | "ResUNet-a para clasificación específica" | No aplica (parcelas pre-identificadas) | ⚠️ Alcance diferente |
| **Variables de entrada IA** | NDVI + textura espacial | ✅ Ambas implementadas | ✅ **Features listas** |
| **Librerías ML/DL** | scikit-learn, TensorFlow, PyTorch | Ninguna instalada | ❌ **Infraestructura faltante** |
| **Modelos guardados** | .pkl, .h5, .pt | No existen | ❌ **Sin artefactos de modelos** |
| **Scripts entrenamiento** | train_model.py, train/val/test split | No existen | ❌ **Sin pipeline ML** |
| **Validación académica** | IoU, Dice, F1, Precision, Recall | Estadísticos NDVI, área cultivada | ⚠️ **Métricas parciales** |
| **Ground truth** | Requerido para entrenar y validar | No disponible | ⚠️ **Limitación conocida** |

---

### 3.4 CONTRADICCIÓN FUNDAMENTAL

**El PEG promete en su título y objetivos**:
> "Desarrollo de una interfaz orientada a servicios con **MODELOS DE INTELIGENCIA ARTIFICIAL**"

**Lo que el software realmente hace**:
> Desarrollo de una interfaz orientada a servicios con **PROCESAMIENTO DE SEÑALES Y REGLAS HEURÍSTICAS**

**Gravedad de la contradicción**:
- ❌ El título del PEG NO describe el software actual
- ❌ El Objetivo General NO se cumple literalmente
- ❌ El Objetivo Académico 5 NO está implementado
- ❌ El Alcance (4 modelos) NO está implementado

---

### 3.5 QUÉ FUNCIONA Y QUÉ NO

#### ✅ LO QUE SÍ ESTÁ FUNCIONANDO (Procesamiento de Señales)

1. **OE2: Cálculo de índices espectrales**
   - Fórmula matemática: `NDVI = (NIR - Red) / (NIR + Red)`
   - NO es IA, es procesamiento de señales

2. **OE3: Segmentación por umbral**
   - Regla heurística: `NDVI > 0.3 = cultivado`
   - NO es U-Net entrenado, es threshold

3. **OE4: Filtros convolucionales**
   - Operadores: Laplaciano, Sobel, Varianza local
   - NO es CNN entrenado, es convolución directa

4. **Estado de salud**
   - Reglas: `NDVI < 0.3 = critical`, `0.3-0.5 = alert`, `>0.5 = healthy`
   - NO es Random Forest/CNN, es if-else

#### ❌ LO QUE FALTA (Inteligencia Artificial)

1. **Modelo de clasificación de salud**
   - Requerido por Académico 5
   - Entrada: NDVI + descriptores textura
   - Salida: healthy/alert/critical
   - **Modelo sugerido**: Random Forest (rápido, interpretable)

2. **Modelo de regresión (rendimiento o cobertura)**
   - Requerido por Alcance (mínimo 2 modelos regresión)
   - Entrada: NDVI temporal + textura + área
   - Salida: toneladas/hectárea o % cobertura
   - **Modelo sugerido**: XGBoost (robusto, preciso)

3. **Modelo de segmentación U-Net (opcional)**
   - Mencionado en Metodología Fase 1
   - Entrada: Imagen RGB + NIR
   - Salida: Máscara cultivado/no-cultivado
   - **Nota**: Actual threshold funciona, esto sería mejora

4. **Modelo ResUNet-a (opcional)**
   - Mencionado en Metodología Fase 2
   - Para clasificación específica de arroz vs otros cultivos
   - **Nota**: Actual scope es solo arroz, no necesario

---

### 3.6 DÓNDE PERTENECE EL REQUISITO DE IA

**Análisis de los Objetivos Específicos aprobados** (CLAUDE.md líneas 13-27):

```
| OE | Verbo | Nivel Bloom | Descripción |
|----|-------|-------------|-------------|
| OE1 | Identificar | N1-N2 | Identificar escenas Sentinel-2 aptas via STAC API |
| OE2 | Aplicar | N3 | Aplicar cálculo de índices espectrales (NDVI) |
| OE3 | Analizar | N4 | Analizar zonas cultivadas por segmentación espacial |
| OE4 | Evaluar | N5 | Evaluar descriptores de textura por filtrado convolucional |
| OE5 | Construir | N6 | Construir la interfaz integrando todos los servicios |
```

**OBSERVACIÓN CRÍTICA**:
Los 5 OEs aprobados por el tutor **NO mencionan explícitamente IA ni modelos ML/DL**.

**PERO**:
- El **Objetivo Académico 5** (versión Jhonattan en `Capitulo1.tex`) SÍ menciona "Desarrollar modelo de IA"
- El **Alcance** (línea 111) SÍ menciona "2 modelos por modalidad"
- La **Metodología** (Fase 2) SÍ menciona "ResUNet-a"

**CONCLUSIÓN**:
Existe una **desconexión entre**:
- **Objetivos Específicos aprobados** (OE1-OE5, sin IA explícita)
- **Objetivos Académicos del template** (incluyen modelo de IA)

**HIPÓTESIS**:
Los OE1-OE5 fueron redefinidos **enfocándose en la infraestructura de servicios** (taxonomía Bloom), postergando la IA como componente opcional o futuro.

---

### 3.7 PRECEDENTE DE TESIS PREVIAS (CPI)

**Según `docs/VALIDACION_CIENTIFICA_OE3_OE4.md`**:

- **Mikovic (2025)**: Usó MLP (modelo IA entrenado)
- **Roche-Vargas (2026)**: Usó ResNet18 (modelo DL entrenado)

**Ambos trabajos previos del CPI SÍ implementaron modelos de IA**.

**Diferencia con este PEG**:
- Ellos: Enfoque en **desarrollo de modelos**
- Nosotros: Enfoque en **plataforma de servicios** que integraría modelos

**Contribución diferencial propuesta**:
> "Mientras Mikovic y Roche-Vargas exploraron modelos de IA aislados, este PEG propone la **arquitectura de microservicios** que permite integrar, desplegar y escalar dichos modelos en producción"

---

### 3.8 RECOMENDACIÓN SOBRE CÓMO DOCUMENTARLO ACADÉMICAMENTE

#### Opción A: Documentar como "Trabajo Futuro" (RECOMENDADA)

**Justificación**:
- Los OE1-OE5 aprobados NO exigen IA explícitamente
- El software entrega **valor funcional** (plataforma completa de análisis)
- La **infraestructura está lista** para incorporar modelos cuando exista ground truth
- Precedente: Validación no presencial es aceptada en CPI

**Acciones**:
1. Crear `knowledge/objectives/OE_future_work.md`:
   ```markdown
   ## Objetivo Académico 5 — Modelo de IA (Trabajo Futuro)
   
   ### Estado actual
   - Variables de entrada implementadas: NDVI + descriptores textura ✅
   - Clasificación funcional mediante reglas heurísticas ✅
   - Infraestructura de servicios lista para integrar modelo ✅
   
   ### Pendiente
   - Obtener ground truth de campo (etiquetas salud real)
   - Entrenar Random Forest / XGBoost para clasificación
   - Validar con k-fold cross-validation
   - Integrar como servicio /api/ml/classify
   
   ### Justificación de postergación
   - Sin ground truth, el modelo sería indemostrable
   - Alcance del PEG: arquitectura de servicios (cumplido)
   - Modelo IA: extensión natural post-validación de campo
   ```

2. En informe final, sección "Alcances y Limitaciones":
   ```
   El presente trabajo se enfocó en la arquitectura de microservicios y 
   procesamiento de señales satelitales. Si bien el Objetivo Académico 5 
   propone un modelo de IA para clasificación de salud, su implementación 
   requiere ground truth de campo no disponible en el alcance temporal del 
   PEG. Las variables predictoras (NDVI, textura) están implementadas y la 
   plataforma está preparada para incorporar modelos entrenados en trabajos 
   futuros.
   ```

3. Modificar título del PEG a:
   ```
   DESARROLLO DE UNA INTERFAZ DE USUARIO ORIENTADA A SERVICIOS DE CÁLCULO 
   EN LA NUBE PARA ESTUDIOS DE AGRICULTURA DE PRECISIÓN EN CULTIVOS DE ARROZ 
   MEDIANTE PROCESAMIENTO DE IMÁGENES SATELITALES
   ```
   **Nota**: Requiere aprobación del tutor

---

#### Opción B: Implementar Modelo IA Demo (NO RECOMENDADA SIN GROUND TRUTH)

**Justificación**:
- Cumple literalmente con Objetivo Académico 5
- Permite demostrar pipeline ML completo
- Cierra gap entre documentación y software

**Problema**:
- Sin ground truth, el modelo será **circular**:
  - Etiquetas generadas desde umbrales NDVI actuales
  - Modelo "aprende" a reproducir las mismas reglas
  - No demuestra capacidad de generalización
- **Riesgo académico**: Modelo indemostrable es peor que no tener modelo

**Acciones (solo si el tutor lo exige)**:
1. Generar dataset sintético:
   ```python
   # Etiquetar con reglas actuales
   df['health'] = df['ndvi_mean'].apply(lambda x: 
       'critical' if x < 0.3 else 'alert' if x < 0.5 else 'healthy'
   )
   ```

2. Entrenar Random Forest demo:
   ```python
   from sklearn.ensemble import RandomForestClassifier
   features = ['ndvi_mean', 'edges_mean', 'contrast_mean', 'homogeneity_mean']
   X = df[features]
   y = df['health']
   
   model = RandomForestClassifier(n_estimators=100, random_state=42)
   model.fit(X_train, y_train)
   ```

3. Guardar modelo:
   ```python
   import joblib
   joblib.dump(model, 'backend/app/models/ml/health_classifier.pkl')
   ```

4. Endpoint de inferencia:
   ```python
   @router.post("/api/ml/classify-health")
   async def classify_health(features: HealthFeatures):
       model = joblib.load('backend/app/models/ml/health_classifier.pkl')
       prediction = model.predict([features.to_array()])
       return {"health_status": prediction[0]}
   ```

**Tiempo estimado**: 3-4 días  
**Valor científico**: Bajo (modelo circular)  
**Valor académico**: Cumple requisito formal del Objetivo 5

---

#### Opción C: Transfer Learning con Modelo Pre-entrenado (EXPLORATORIA)

**Justificación**:
- Usa modelo público pre-entrenado en croplands
- Fine-tuning en parcelas SRRG (sin etiquetas, clustering no supervisado)
- Demuestra capacidad de integración con modelos externos

**Problema**:
- Modelos públicos (ej: Radiant Earth) no están calibrados para arroz venezolano
- Clustering no supervisado: difícil interpretar clases encontradas
- Requiere librerías pesadas (TensorFlow/PyTorch)

**Solo si**: El tutor acepta enfoque exploratorio y se dispone de 2-3 semanas

---

### 3.9 VEREDICTO FINAL SOBRE IA

**ESTADO ACTUAL**:
❌ **NO hay modelos de Inteligencia Artificial entrenados en el software**  
✅ **SÍ hay procesamiento de señales y reglas heurísticas funcionando**  
✅ **SÍ hay infraestructura lista para integrar modelos futuros**

**GRAVEDAD DEL GAP**:
🔴 **CRÍTICO** — El título del PEG promete "MODELOS DE IA" y no los entrega

**RECOMENDACIÓN**:
📋 **Documentar como "Trabajo Futuro"** con justificación sólida:
- Enfoque del PEG: Arquitectura de servicios (cumplido)
- Modelo IA: Requiere ground truth no disponible
- Precedente: Validación no presencial aceptada en CPI
- Contribución diferencial: Plataforma vs modelos aislados

**ALTERNATIVA (solo si tutor exige)**:
🤖 Implementar modelo Random Forest demo (circular, 3-4 días)

---

## CONSOLIDACIÓN FINAL — DIAGNÓSTICO COMPLETO

### ESTADO REAL DE LOS OBJETIVOS ESPECÍFICOS

| OE | Estado | Implementación Técnica | Validación Científica | Gap Principal |
|----|--------|------------------------|----------------------|---------------|
| **OE1** | ✅ COMPLETO | 100% | Fechas reales verificadas | Ninguno |
| **OE2** | ✅ COMPLETO | 100% | Valores NDVI coherentes | Ninguno |
| **OE3** | ✅ COMPLETO | 100% | Sin ground truth | Validación agronómica |
| **OE4** | ✅ FUNCIONAL | 100% | Sin ground truth | Tests E2E + validación agronómica |
| **OE5** | ⚠️ 85% | Base completa | N/A | Comparación multi-fecha + exportación + tests |

### ESTADO REAL DEL REQUISITO DE IA

| Aspecto | Requerido por Documentación | Implementado en Software | Gap |
|---------|----------------------------|-------------------------|-----|
| **Modelo clasificación salud** | Objetivo Académico 5 | Reglas heurísticas | ❌ **Modelo entrenado faltante** |
| **Modelos regresión** | Alcance (mínimo 2) | Ninguno | ❌ **2 modelos faltantes** |
| **U-Net segmentación** | Metodología Fase 1 | Threshold NDVI | ⚠️ **Heurística funcional** |
| **ResUNet-a** | Metodología Fase 2 | No aplica | ⚠️ **Out of scope** |
| **Variables entrada IA** | NDVI + textura | ✅ Ambas implementadas | ✅ **Listas para modelo** |
| **Infraestructura ML** | Implícito | Servicios REST | ✅ **Preparada** |

### PRÓXIMOS PASOS RECOMENDADOS

#### PRIORIDAD 1: Completar OE4 y OE5 (MUST)
1. **OE4**:
   - [ ] Test automatizado end-to-end (`test_oe4_texture_complete.py`)
   - [ ] Screenshots evidencia widget funcionando
   - [ ] Docker validation completa

2. **OE5**:
   - [ ] Tests E2E (flujo completo: login → dashboard → análisis)
   - [ ] Manejo de errores mejorado (mensajes claros español)
   - [ ] Screenshots/video del dashboard completo
   - [ ] Docker validation completa

#### PRIORIDAD 2: Resolver Discrepancia IA (CRÍTICO)
- [ ] Crear `knowledge/objectives/OE_future_work.md` con justificación
- [ ] Documentar en informe PEG sección "Alcances y Limitaciones"
- [ ] **Consultar con tutor**: ¿Aceptable documentar como trabajo futuro?
- [ ] **Si tutor exige**: Implementar Random Forest demo (3-4 días)

#### PRIORIDAD 3: Documentación Final (MUST)
- [ ] Poblar carpeta `knowledge/` según consolidación
- [ ] Actualizar CLAUDE.md con referencias a knowledge/
- [ ] Preparar evidencia de completitud (screenshots, tests, documentación)

#### PRIORIDAD 4: Funcionalidades Avanzadas OE5 (NICE TO HAVE)
- [ ] Comparación temporal multi-fecha (postergar)
- [ ] Exportación PDF/CSV (postergar)
- [ ] Estos quedan como "Extensiones Propuestas" en documentación

---

## ANEXO: ARCHIVOS CLAVE AUDITADOS

### Backend
- `backend/app/models/texture.py` — Modelo BD descriptores ✅
- `backend/app/services/texture_service.py` — Cálculo convoluciones ✅
- `backend/app/services/texture_overlay_service.py` — Generación PNG ✅
- `backend/app/crud/texture.py` — CRUD descriptores ✅
- `backend/app/crud/texture_overlay.py` — CRUD cache overlays ✅
- `backend/app/api/endpoints/texture.py` — Endpoints API ✅
- `backend/requirements.txt` — Sin librerías ML/DL ❌

### Frontend
- `frontend/app/components/organisms/TextureWidget.tsx` — Widget textura ✅
- `frontend/app/components/molecules/TextureDescriptorsTable.tsx` — Tabla ✅
- `frontend/app/components/molecules/TextureOverlayPreview.tsx` — Preview ✅
- `frontend/app/components/ParcelAnalysisWidgets.tsx` — Integración ✅
- `frontend/app/cultivos/[id]/page.tsx` — Dashboard individual ✅
- `frontend/app/hooks/usePolygonHealth.ts` — Estado salud (heurística) ⚠️

### Documentación
- `docs/OE4_OVERLAY_EVIDENCE.md` — Evidencia overlays (2026-08-04) ✅
- `docs/metodologia_textura_OE4.md` — Metodología científica ✅
- `docs/VALIDACION_CIENTIFICA_OE3_OE4.md` — Limitaciones validación ✅
- `knowledge/references/template/Capitulos/Capitulo1.tex` — Objetivos PEG
- `knowledge/references/template/Capitulos/Capitulo3.tex` — Metodología PEG

---

**FIN DEL DIAGNÓSTICO**

**ESPERANDO APROBACIÓN DEL USUARIO PARA PROCEDER CON**:
1. Completar OE4 (tests + evidencia)
2. Completar OE5 (tests + evidencia)
3. Resolver discrepancia IA (consultar tutor)
