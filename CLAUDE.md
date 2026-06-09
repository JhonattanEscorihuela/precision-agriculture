# CLAUDE.md
> Guía de trabajo para Claude Code en este proyecto de grado (PEG).
> Leer SIEMPRE antes de generar cualquier código.

---

## 🎯 PROYECTO

Aplicación web responsive de agricultura de precisión que analiza el estado
de salud de cultivos de arroz usando imágenes satelitales Sentinel-2.

**Stack:**
- Backend: FastAPI (async) + PostgreSQL + SQLModel
- Frontend: Next.js 16 (App Router) + TypeScript + React 19 + Leaflet
- ML: Jupyter notebooks → servicios FastAPI

---

## 📋 OBJETIVOS ESPECÍFICOS (Taxonomía de Bloom — de menor a mayor)

> ⚠️ Estos son los objetivos APROBADOS por el tutor. No usar numeración anterior.

| OE | Verbo | Nivel Bloom | Descripción |
|----|-------|-------------|-------------|
| **OE1** | Identificar | N1-N2 | Identificar escenas Sentinel-2 aptas via STAC API |
| **OE2** | Aplicar | N3 | Aplicar cálculo de índices espectrales (NDVI) |
| **OE3** | Analizar | N4 | Analizar zonas cultivadas por segmentación espacial |
| **OE4** | Evaluar | N5 | Evaluar descriptores de textura por filtrado convolucional |
| **OE5** | Construir | N6 | Construir la interfaz integrando todos los servicios |

**Nota:** La nubosidad se gestiona dentro del OE1 (filtro STAC).
La validación se distribuye como evidencia medible en cada OE.

---

## ✅ ESTADO ACTUAL

### OE1 — Identificar escenas Sentinel-2 ✅ COMPLETO

**Backend:**
- ✅ Autenticación OAuth2 Copernicus funcionando
- ✅ Modelo `SentinelAcquisition` en BD (B04 + B08)
- ✅ CRUD completo para adquisiciones (`crud/acquisition.py`)
- ✅ STAC API integrada (`get_available_dates()`)
- ✅ Process API funcionando (`acquire_bands()`)
- ✅ Endpoint `GET /sentinel/available-dates/{polygon_id}` operativo
- ✅ Endpoint `POST /sentinel/acquire` operativo
- ✅ Tests completos: `test_oe1_complete.py` pasando
- ✅ Evidencia: 16 fechas encontradas (2025, 20% nubes), bandas 25KB c/u guardadas en BD
- ✅ Coordenadas reales: Parcela 211 SRRG Calabozo, Venezuela
- ✅ Autenticación usuario (JWT + bcrypt + OAuth2)
- ✅ Parcelas asociadas a usuarios con CASCADE delete

**Frontend:**
- ✅ Componente `atoms/DateBadge.tsx` (42 líneas)
- ✅ Componente `molecules/DateSelector.tsx` (74 líneas)
- ✅ Componente `molecules/AcquireButton.tsx` (78 líneas)
- ✅ Componente `organisms/SentinelPanel.tsx` (responsive)
- ✅ Integración con `LeafletMap.tsx` (click en parcela → abre panel)
- ✅ Flujo completo: consultar fechas → seleccionar → adquirir
- ✅ UI amigable sin tecnicismos (sin cloud_cover, B04, B08, L2A)
- ✅ Panel lateral desktop / modal inferior mobile
- ✅ Fechas inteligentes (inicio: 1er día mes -6 meses, fin: hoy)
- ✅ Fechas futuras bloqueadas (max attribute)
- ✅ Responsive mobile (375px) y desktop (1920px)
- ✅ Login/Register UI implementado
- ✅ ProtectedRoute con verificación token
- ✅ Sidebar responsive con hamburger menu
- ✅ AuthContext + PolygonContext funcionando
- ✅ Axios interceptors para JWT automático

### OE2 — Aplicar índices espectrales ✅ COMPLETO

**Backend:**
- ✅ Modelo `NDVIResult` en BD con UNIQUE constraint (acquisition_id)
- ✅ CRUD completo para NDVI (`crud/ndvi.py`)
- ✅ Servicio `ndvi_service.py` con cálculo NDVI (L2A scale factor, masking nodata)
- ✅ 4 endpoints: calculate (idempotente), get stats, get by polygon, download TIFF
- ✅ Validación rango [-1, 1], estadísticos (mean, min, max, std)
- ✅ JOIN con SentinelAcquisition para obtener acquisition_date
- ✅ Tests de integración con parcelas SRRG

**Frontend:**
- ✅ Componente `atoms/NDVIBadge.tsx` - Badge coloreado por valor NDVI
- ✅ Componente `molecules/NDVIStats.tsx` - Grid estadísticos + tooltip valores negativos
- ✅ Componente `molecules/NDVIColorScale.tsx` - Escala gradiente horizontal
- ✅ Componente `organisms/NDVIPanel.tsx` - Panel cálculo + visualización (state machine)
- ✅ Componente `organisms/NDVIEvolutionWidget.tsx` - Gráfica temporal Recharts (últimas 6 fechas)
- ✅ Integración en `SentinelPanel.tsx` - Auto-mostrar después de adquisición
- ✅ Página `/cultivos` - Lista parcelas con estado de salud real (basado en NDVI)
- ✅ Página `/cultivos/[id]` - Dashboard individual con grid de widgets
- ✅ Hook `usePolygonHealth.ts` - Estado de salud por parcela (healthy/alert/critical/unknown)
- ✅ Util `geoUtils.ts` - Cálculo área parcelas (fórmula Shoelace)
- ✅ Caché local en componentes (evita re-fetch innecesarios)
- ✅ JWT auth en todas las peticiones NDVI

**Librerías:**
- ✅ `recharts@3.8.1` - Gráficas interactivas
- ✅ `numpy==1.24.3` - Cálculo NDVI
- ✅ `rasterio==1.4.3` - Lectura/escritura TIFF

### OE3 — Analizar segmentación espacial
- ✅ Prototipo filtro convolucional en notebook
- 🔧 PENDIENTE: Migrar a servicio + endpoints + widget dashboard

### OE4 — Evaluar descriptores de textura
- ✅ U-Net implementada (datos sintéticos)
- 🔧 PENDIENTE: Entrenar con datos reales + servicio + widget dashboard

### OE5 — Construir interfaz integrada
- ✅ Mapa Leaflet con dibujo de polígonos
- ✅ CRUD parcelas funcionando
- ✅ Panel lateral de adquisición Sentinel-2 (OE1 frontend)
- ✅ Panel visualización NDVI (OE2 frontend)
- ✅ Dashboard individual por parcela con widgets (patrón AWS CloudWatch)
- ✅ Estado de salud basado en datos reales
- 🔧 PENDIENTE: Comparación temporal multi-fecha, exportación reportes

---

## 📍 PARCELAS DE REFERENCIA — SRRG, Calabozo, Guárico, Venezuela

> Usar SIEMPRE estas coordenadas en tests. Nunca usar coordenadas de otras ciudades o países.

```python
# Parcela 211 — período 2024-2025
PARCELA_211 = [
    [-67.528058, 8.8441233],
    [-67.5153475, 8.8386166],
    [-67.5103962, 8.8478932],
    [-67.522828,  8.8534209],
    [-67.528058, 8.8441233]   # cierre del polígono
]

# Parcela 217 — Invierno 2024
PARCELA_217 = [
    [-67.538379,  8.8042214],
    [-67.5369724, 8.8130876],
    [-67.5351396, 8.8123084],
    [-67.5337757, 8.8125401],
    [-67.5239405, 8.8082815],
    [-67.5257482, 8.7980897],
    [-67.538379,  8.8042214]  # cierre del polígono
]

# Parcela 85 — período 2025-2026
PARCELA_85 = [
    [-67.586587,  8.8508969],
    [-67.5991461, 8.8654285],
    [-67.5869706, 8.8659561],
    [-67.5776965, 8.8549892],
    [-67.586587,  8.8508969]  # cierre del polígono
]
```

**Rangos temporales de referencia por parcela:**
| Parcela | Período | Notas |
|---------|---------|-------|
| 211 | 2024-01-01 / 2025-06-01 | Parcela principal de referencia |
| 217 | 2024-01-01 / 2024-12-31 | Invierno 2024 |
| 85  | 2025-01-01 / 2026-06-01 | Período más reciente |

**⚠️ Nubosidad en zona tropical:**
- Venezuela (Guárico) tiene mayor nubosidad que Europa
- **IMPORTANTE:** Siempre usar `max_cloud=20%` (especificación OE1)
- Período con menos nubes: diciembre-marzo (temporada seca)
- Tests verificados: fechas aptas en 2025 con 20% tolerancia
- Fecha actual de tests: 2026-05-23 (usar datos 2025-2026)

---

## 💾 ESTRATEGIA DE CACHÉ — OBLIGATORIO EN TODOS LOS OBJETIVOS

**REGLA DE ORO:** Si cuesta > 2 segundos calcularlo, debe cachearse en BD.

### 1. Idempotencia en endpoints de cálculo
```python
# POST siempre verificar si ya existe resultado
existing = await crud.get_by_acquisition_id(db, acquisition_id)
if existing:
    return existing  # ✅ Retornar sin recalcular
# Calcular solo si no existe
result = calculate_expensive_operation()
await crud.save(db, result)
return result
```

### 2. BD como caché de resultados costosos
- Guardar: NDVI, segmentaciones, descriptores de textura, máscaras ML
- GET endpoints: Solo consultan BD, **nunca recalculan**
- TTL: Infinito (datos satelitales no cambian)
- Formato: TIFF para rasters, JSON para metadatos, WKB para geometrías

### 3. Caché local en componentes React
```typescript
const [alreadyFetched, setAlreadyFetched] = useState(false);

useEffect(() => {
  if (!alreadyFetched) {
    fetchData().then(() => setAlreadyFetched(true));
  }
}, [alreadyFetched]);
```

### 4. Queries optimizados (evitar N+1)
```python
# ❌ MAL: N+1 queries
for ndvi in ndvi_list:
    acquisition = await get_acquisition(ndvi.acquisition_id)

# ✅ BIEN: JOIN en backend
query = select(NDVI, Acquisition).join(Acquisition)
```

### 5. Considerar React Query/SWR para OE3+
Solo si hay >10 peticiones redundantes por sesión.

**Aplicar en:**
- OE3: Segmentaciones (máscaras WKB en BD)
- OE4: Descriptores textura (arrays JSON en BD)
- OE5: Widgets leen datos cacheados

---

## 🏗️ ARQUITECTURA BACKEND

```
backend/app/
├── api/endpoints/     ← Solo orquestación, sin lógica
├── crud/              ← Solo operaciones de BD
├── models/            ← SQLModel (user.py, polygon.py, analysis.py)
├── schemas/           ← Pydantic request/response
├── services/          ← Toda la lógica de negocio
│   ├── sentinel/      ← OE1 (módulos: auth, stac_client, process_client, geometry, etc.)
│   │   ├── __init__.py
│   │   ├── sentinel_service.py    ← Orquestador principal
│   │   ├── auth.py                ← Autenticación OAuth2
│   │   ├── stac_client.py         ← Cliente STAC API
│   │   ├── process_client.py      ← Cliente Process API
│   │   ├── geometry.py            ← Cálculos geométricos (reutilizable OE3/OE4)
│   │   ├── request_builder.py     ← Constructor payloads
│   │   └── logger_utils.py        ← Logging detallado
│   ├── ndvi_service.py       ← OE2
│   ├── segmentation_service.py ← OE3
│   ├── texture_service.py    ← OE4
│   └── auth_logic.py
└── core/              ← Config, security
```

**Reglas irrompibles:**
- ❌ Nunca lógica en endpoints
- ❌ Nunca queries de BD fuera de crud/
- ✅ Endpoints llaman a services, services llaman a crud
- ✅ Servicios grandes (>500 líneas) → modularizar en package

---

## 🏗️ ARQUITECTURA FRONTEND

```
frontend/app/
├── components/
│   ├── atoms/         ← Botones, inputs, badges (< 50 líneas)
│   ├── molecules/     ← Combinación de atoms (< 100 líneas)
│   └── organisms/     ← Componentes completos (< 200 líneas)
├── utils/
│   └── coordUtils.ts  ← ✅ Ya resuelto: leafletToGeoJSON / geoJSONToLeaflet
└── app/               ← Páginas Next.js App Router
```

**Reglas irrompibles:**
- ❌ Nunca CSS puro — solo Tailwind
- ❌ Nunca componentes > 200 líneas — dividir
- ❌ Nunca estilos inline complejos
- ✅ Siempre TypeScript
- ✅ Siempre `ssr: false` en componentes con Leaflet
- ✅ **Siempre responsive** — Mobile-first, validar en desktop (1920px) y mobile (375px)
- ✅ Usar breakpoints Tailwind: `sm:` (640px), `md:` (768px), `lg:` (1024px), `xl:` (1280px)

---

## 🔑 COORDENADAS

```
GeoJSON / Backend / Sentinel: [lng, lat]   ← ESTÁNDAR
Leaflet frontend:              [lat, lng]   ← EXCEPCIÓN

# Usar siempre las utilidades:
import { leafletToGeoJSON, geoJSONToLeaflet } from '@/utils/coordUtils'
```

---

## 📦 OE1 — ESPECIFICACIÓN COMPLETA

### Qué debe hacer el OE1

Cuando el usuario registra una parcela y quiere analizarla:

1. Sistema consulta STAC API → lista escenas disponibles para ese polígono
2. Sistema filtra `cloud_cover ≤ 20%` internamente
3. Frontend muestra selector con solo fechas aptas (sin tecnicismos)
4. Usuario elige fecha → sistema adquiere bandas B04 y B08 via Process API
5. Bandas quedan disponibles para que OE2 calcule NDVI

### Endpoints a implementar

```
GET  /api/sentinel/available-dates/{polygon_id}?start=YYYY-MM-DD&end=YYYY-MM-DD
     → Lista fechas aptas (cloud_cover ≤ 20%) para el polígono del usuario

POST /api/sentinel/acquire
     body: { polygon_id, date }
     → Descarga B04 y B08, guarda en BD, retorna acquisition_id
```

### Estructura sentinel_service.py

```python
class SentinelService:
    async def get_available_dates(
        polygon_coords: list,
        start_date: str,
        end_date: str,
        max_cloud: int = 20
    ) -> list[dict]
    # Llama STAC API, filtra cloud_cover, retorna [{date, cloud_cover}]

    async def acquire_bands(
        polygon_coords: list,
        date: str,
        polygon_id: int
    ) -> int  # retorna acquisition_id
    # Llama Process API, descarga B04+B08 TIFF, guarda en BD
```

### STAC API (sin autenticación)

```python
POST https://stac.dataspace.copernicus.eu/v1/search
{
  "collections": ["sentinel-2-l2a"],
  "datetime": "{start}T00:00:00Z/{end}T23:59:59Z",
  "intersects": { "type": "Polygon", "coordinates": [polygon_coords] },
  "limit": 50,
  "fields": {
    "include": ["properties.datetime", "properties.eo:cloud_cover"],
    "exclude": ["assets", "links"]
  }
}
```

### Process API (requiere OAuth2)

```python
# Ya tienes CLIENT_ID y CLIENT_SECRET funcionando
# Usar credenciales existentes de backend/core/.env
# Solicitar bandas B04 y B08 en formato TIFF
```

### Evidencia medible del OE1

Al completar el OE1 debes poder mostrar:
- Tabla de fechas aptas por parcela (resultado del STAC)
- Registro en BD de las bandas adquiridas por fecha

---

## 🔄 WORKFLOW DE TRABAJO

### Git workflow (OBLIGATORIO)

**Siempre trabajar en ramas feature:**

1. **Crear rama** antes de empezar: `git checkout -b feature/nombre-descriptivo`
2. **Trabajar en la rama** (commits, tests, validación)
3. **Merge local** cuando esté completo: `git checkout main && git merge feature/nombre-descriptivo`
4. **Push** a remoto: `git push origin main`
5. **Limpiar** rama local (opcional): `git branch -d feature/nombre-descriptivo`

❌ **NUNCA** hacer commits directos a main  
✅ **SIEMPRE** usar feature branches

### Antes de implementar cualquier cosa

1. **Crear rama feature** con nombre descriptivo
2. Escribir plan en `tasks/todo.md`
3. Confirmar plan antes de empezar
4. Implementar por pasos verificables
5. **Validar con tests Y docker-compose** (ambos obligatorios)
6. Marcar completo solo con evidencia triple: tests + docker + prueba manual
7. **Merge a main y push**

### Estructura tasks/

```
tasks/
├── todo.md                  ← Plan activo con checkboxes
├── lessons.md               ← Errores corregidos y patrones aprendidos
├── DOCKER_VALIDATION.md     ← Guía de validación end-to-end
└── oe{N}_complete.md        ← Evidencia de completitud por OE
```

### Criterio de completitud (OBLIGATORIO)

**Un OE NO está completo hasta que:**
- ✅ Tests unitarios pasan (`pytest`)
- ✅ Tests de integración pasan (APIs reales)
- ✅ **`docker-compose up --build` levanta sin errores**
- ✅ **Flujo manual probado end-to-end (frontend + backend + db)**
- ✅ Evidencia documentada en `tasks/oe{N}_complete.md`
- ✅ CLAUDE.md actualizado con estado completado
- ✅ Lecciones documentadas en `tasks/lessons.md`

**⚠️ CRÍTICO:** Tests pasando NO garantiza que el sistema completo funcione.  
Docker-compose detecta: imports faltantes, modelos sin implementar, CORS, networking, etc.

Ver `tasks/DOCKER_VALIDATION.md` para guía detallada.

### Después de cualquier corrección

Actualizar `tasks/lessons.md` con el patrón del error para no repetirlo.

---

## 🚨 ANTES DE CADA RESPUESTA — CHECKLIST

- [ ] ¿Estoy trabajando en una rama feature?
- [ ] ¿Indiqué a qué OE pertenece?
- [ ] ¿Especifiqué la ruta exacta del archivo?
- [ ] ¿La lógica va en services/, no en endpoints/?
- [ ] ¿El frontend usa solo Tailwind?
- [ ] ¿El componente tiene menos de 200 líneas?
- [ ] ¿Las coordenadas usan [lng, lat]?
- [ ] ¿Validé con tests Y docker-compose?
- [ ] ¿Probé el flujo manual end-to-end?
- [ ] ¿Documenté evidencia en tasks/?
- [ ] ¿Hice merge a main y push?
- [ ] ¿Sugerí el próximo paso?

---

## 🧪 TESTING Y VALIDACIÓN

### 1. Tests unitarios e integración
```bash
# Desde backend/
pytest tests/
pytest tests/test_sentinel_service.py -v
```
Tests async con pytest-asyncio. Fixtures en `tests/conftest.py`.

### 2. Validación Docker (OBLIGATORIO)
```bash
# Limpiar y rebuild completo
docker-compose down -v
docker-compose up --build

# Verificar logs
docker-compose logs backend --tail=50
docker-compose logs frontend --tail=20

# Verificar servicios
curl http://localhost:8000/        # Backend health
curl http://localhost:8000/docs    # API docs
curl http://localhost:3000/        # Frontend
```

### 3. Prueba manual end-to-end
- Abrir frontend en navegador
- Ejecutar flujo completo según OE
- Verificar datos en BD con psql
- Documentar evidencia con screenshots/output

**Ver `tasks/DOCKER_VALIDATION.md` para checklist completo.**

---

## ⚙️ COMANDOS RÁPIDOS

- `@ESTADO` → Estado actual de los 5 OEs
- `@SIGUIENTE` → Próxima tarea prioritaria
- `@SERVICIO [nombre]` → Crear servicio backend
- `@COMPONENTE [nombre]` → Crear componente frontend
- `@PLAN` → Escribir plan en tasks/todo.md antes de implementar

---

## 📐 DECISIONES ARQUITECTÓNICAS CLAVE

| Aspecto | Decisión |
|---------|----------|
| Coordenadas | WGS84 (EPSG:4326), formato [lng, lat] |
| Formato imágenes | TIFF (no PNG) para preservar precisión float |
| Autenticación | OAuth2 Copernicus — credenciales en backend/core/.env |
| Disponibilidad escenas | STAC API (sin auth, solo metadatos) |
| Adquisición imágenes | Process API (con OAuth2) |
| Almacenamiento bandas | PostgreSQL bytea < 10MB |
| NDVI rango | [-1, 1] con factor normalización L2A |
| Clasificación salud | Critical / Alert / Healthy |

---

## 🔍 DEBUGGING FRECUENTE

```python
# Coordenadas invertidas
assert coords[0][0] < 0, "Longitud Venezuela debe ser negativa (~-67)"

# NDVI fuera de rango
assert -1 <= ndvi.mean() <= 1, "Error en normalización NDVI"

# Async session
async with AsyncSession(engine) as session:  # ✅
    result = await session.execute(query)
```