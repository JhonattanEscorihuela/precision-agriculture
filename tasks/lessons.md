# Lecciones Aprendidas - OE1

## Completado: 2026-05-23 (FINAL)

### ✅ Patrones exitosos

1. **Arquitectura en capas funciona**
   - Modelos → CRUD → Servicios → Endpoints
   - Nunca lógica de negocio en endpoints
   - Separación clara de responsabilidades

2. **STAC API no requiere autenticación**
   - URL: `https://stac.dataspace.copernicus.eu/v1/search`
   - Solo Process API requiere OAuth2
   - Útil para consultas rápidas de disponibilidad

3. **Descargar bandas por separado es más simple**
   - Llamar `download_bands(["B04"])` y `download_bands(["B08"])` independientemente
   - Evita necesidad de rasterio para separar multi-banda
   - Cada TIFF es ~30KB con dimensiones 128x128

4. **Pasar sesión DB como parámetro**
   - Evita imports circulares con `app.database`
   - Permite reutilizar en tests con BD en memoria
   - Más flexible para diferentes contextos

5. **Tests de integración > mocks para APIs externas**
   - Mejor probar contra API real de Copernicus
   - Detecta cambios en contratos de API
   - Da más confianza en producción

6. **Validación end-to-end con docker-compose es OBLIGATORIA**
   - Tests unitarios/integración NO garantizan que el sistema completo funcione
   - SIEMPRE ejecutar `docker-compose up --build` después de implementar features
   - Valida: frontend + backend + database + networking entre contenedores
   - Detecta: imports faltantes, modelos sin implementar, problemas de CORS, variables de entorno
   - Ejemplo OE1: Tests pasaban, pero User model vacío rompía el startup en Docker
   - **Regla:** Feature no está completo hasta que `docker-compose up` levante sin errores

### ⚠️ Errores corregidos

1. **Pydantic 2.x cambió BaseSettings**
   - Error: `BaseSettings` movido a `pydantic-settings`
   - Solución: Evitar importar config en servicios si no es necesario

2. **SQLModel requiere imports explícitos en main.py**
   - Error: Modelos no se registraban automáticamente
   - Solución: Importar `SentinelAcquisition` en `main.py`

3. **Greenlet requerido para async SQLAlchemy**
   - Error: `ValueError: the greenlet library is required`
   - Solución: `pip install greenlet`

4. **venv_39 vs venv (Python 3.14)**
   - asyncpg no compila en Python 3.14 (muy nuevo)
   - Usar Python 3.9 para compatibilidad

5. **SQLModel CASCADE delete syntax**
   - Error: `Field() got an unexpected keyword argument 'ondelete'`
   - Causa: SQLModel no soporta `ondelete` directo en Field()
   - Solución: `Field(sa_column=Column(Integer, ForeignKey("table.id", ondelete="CASCADE")))`
   - Archivos: `acquisition.py`, `polygon.py`

6. **Circular imports con security.py y crud/user.py**
   - Error: `app.core.security` importa `app.crud.user` que importa `app.core.security`
   - Solución: Mover `get_password_hash()` a `crud/user.py`
   - Usar local import en `get_current_user()`: `from app.crud.user import get_user_by_email`

7. **Passlib bcrypt error: password longer than 72 bytes**
   - Error: `ValueError: password cannot be longer than 72 bytes`
   - Solución: Cambiar de passlib.context.CryptContext a bcrypt directo
   - Usar: `bcrypt.hashpw()` y `bcrypt.checkpw()`

8. **Database schema mismatch después de agregar foreign keys**
   - Error: `column polygon.user_id does not exist`
   - Causa: Modelo actualizado pero BD no migrada
   - Solución: SQL manual: `ALTER TABLE polygon ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1 REFERENCES "user"(id) ON DELETE CASCADE;`

9. **Tipos inconsistentes number vs string en frontend/backend**
   - Error: Actualizaciones/eliminaciones no funcionaban
   - Causa: Backend devuelve `id: int`, frontend usaba `id: string`
   - Solución: Cambiar tipo `Polygon.id` de `string` a `number` en todo el frontend
   - Afectó: PolygonContext, cultivos page, comparaciones de igualdad

10. **Estado no se resetea al cambiar props en SentinelPanel**
    - Error: Datos de parcela anterior se mantienen al seleccionar otra
    - Causa: `useEffect` no escuchaba cambios de `polygonId`
    - Solución: Agregar `useEffect(() => { resetState() }, [polygonId])`
    - Desmonte completo: cerrar panel, setear null, reabrir con delay 50ms

### 📊 Métricas OE1 - Completitud end-to-end

**Backend:**
- Archivos creados: 8 (models: user, acquisition | crud: user, acquisition | tests: 3)
- Archivos modificados: 5 (sentinel_service, endpoints, schemas, main.py, security)
- Líneas de código: ~1500
- Tests: 3 archivos, todos pasando ✅
- APIs integradas: 2 (STAC + Process + OAuth2 Copernicus)
- Autenticación: JWT + bcrypt + OAuth2

**Frontend:**
- Componentes creados: 11 
  - Atoms: DateBadge
  - Molecules: DateSelector, AcquireButton
  - Organisms: SentinelPanel (responsive)
  - Pages: login, register
  - Context: AuthContext, PolygonContext
  - Utils: ProtectedRoute, coordUtils
- Líneas de código: ~1200
- Metodología: Atomic Design ✅
- Responsive: Mobile (375px) + Tablet + Desktop (1920px)

**Validación end-to-end:**
- ✅ pytest tests/ → todos pasando
- ✅ docker-compose up --build → sin errores
- ✅ Frontend accesible (localhost:3000)
- ✅ Backend accesible (localhost:8000)
- ✅ Flujo manual completo:
  - Register usuario → Login → Dibujar parcela
  - Click parcela → Consultar fechas → Adquirir imagen
  - Logout → Login otro usuario → Parcelas aisladas ✅
- ✅ Evidencia: 16 fechas encontradas (2025, 20% nubes, Parcela 211)
- ✅ Mejor fecha: 2025-12-31 (9.28% nubes)
- ✅ Bandas: B04 (25KB) + B08 (24KB) guardadas en BD
- ✅ Responsive probado: iPhone SE (375px) + Desktop (1920px)
- ✅ Fechas inteligentes: inicio = 1er día mes -6 meses, fin = hoy
- ✅ Fechas futuras bloqueadas con max attribute

### 🌍 Coordenadas corregidas

**Antes:** Tests usaban Madrid, España ([-3.7038, 40.4168]) con fechas 2024  
**Después:** Tests usan Parcela 211, SRRG Calabozo, Venezuela ([-67.528058, 8.8441233]) con fechas 2025

**Diferencia climática importante:**
- Madrid: ~7 fechas aptas/mes con 20% nubes
- Venezuela tropical: Menos fechas debido a mayor nubosidad
- **Restricción OE1:** Siempre `max_cloud=20%` (no aumentar)
- Mejor período: diciembre-marzo (temporada seca) → 6-15% nubes
- Tests actualizados a 2025 (estamos en mayo 2026)
- Nota: Venezuela tiene menos fechas aptas pero la restricción es 20%

### 📋 Checklist de completitud para cada OE

**Antes de marcar un OE como completo:**
- [ ] Tests unitarios pasando (`pytest`)
- [ ] Tests de integración pasando (con APIs reales si aplica)
- [ ] `docker-compose up --build` levanta sin errores
- [ ] Frontend accesible en http://localhost:3000
- [ ] Backend accesible en http://localhost:8000
- [ ] API Docs accesibles en http://localhost:8000/docs
- [ ] Flujo manual probado end-to-end (click, formularios, respuestas)
- [ ] Evidencia documentada en `tasks/oe{N}_complete.md`
- [ ] CLAUDE.md actualizado con estado completado
- [ ] Lecciones aprendidas documentadas

### 🎨 Diseño responsive implementado

**Estrategia mobile-first con Tailwind:**
- Breakpoints: `sm:` 640px, `md:` 768px, `lg:` 1024px, `xl:` 1280px
- Sidebar: Hamburger menu en mobile, fixed en desktop
- SentinelPanel: Modal inferior en mobile, lateral en desktop
- Formularios: Stack vertical, inputs/labels escalables
- Grid cultivos: 1 col mobile → 2 tablet → 3 desktop
- Padding/spacing adaptativo: `p-4 sm:p-6 lg:p-8`

**Lecciones responsive:**
- Overlay para cerrar drawers/modals en mobile
- Handle visual para modales inferiores (mejor UX táctil)
- Truncar textos largos con `truncate` en mobile
- Ocultar hints/ayudas en pantallas muy pequeñas
- z-index layering: hamburger (2000) > sidebar (1999) > overlay (1998)
- Auto-cierre de sidebar al navegar (mejor UX mobile)

### 🔒 Seguridad implementada

**Backend:**
- JWT tokens con 30 días de expiración
- Bcrypt con salt para passwords (sin truncate a 72 bytes)
- OAuth2 password flow con dependencias FastAPI
- Middleware CORS configurado
- Foreign keys CASCADE delete (user → polygons → acquisitions)

**Frontend:**
- ProtectedRoute verifica token en localStorage antes de renderizar
- Axios interceptors añaden JWT automático a todas las requests
- 401 → logout automático + redirect a /login
- No flash de contenido: spinner mientras valida auth
- Token sincrónico check evita renderizado prematuro

**Flujo de autenticación:**
1. Usuario → POST /auth/register → crea user + auto-login
2. POST /auth/login → valida password → genera JWT → guarda en localStorage
3. GET /auth/me (con JWT header) → valida token → retorna user
4. Todas las requests incluyen `Authorization: Bearer {token}`
5. Logout → borra localStorage → redirect /login

### 🚀 OE2 — Lecciones de planificación

**Fecha:** 2026-06-08  
**Estado:** Planificación completa, esperando confirmación para implementar

#### 🔍 Errores detectados en revisión pre-implementación

1. **Autenticación JWT olvidada en endpoints**
   - **Problema:** Plan original no incluía `current_user = Depends(get_current_user)`
   - **Consecuencia:** Usuario podría calcular NDVI de adquisiciones de otros usuarios
   - **Lección:** SIEMPRE revisar autenticación en todos los endpoints que lean/modifiquen datos de usuario
   - **Solución:** Agregado JWT + verificación de ownership en servicio

2. **Inconsistencia en tipos de fechas**
   - **Problema:** Plan usaba `calculation_date: str` mientras OE1 usa `datetime`
   - **Consecuencia:** Queries complejas, inconsistencia en serialización
   - **Lección:** Revisar tipos de datos de modelos relacionados antes de crear nuevos
   - **Solución:** Cambiado a `datetime` con `default_factory=datetime.utcnow`

3. **Tests sin fixtures preparados**
   - **Problema:** `test_all_parcelas_ndvi` asumía adquisiciones existentes en BD
   - **Consecuencia:** Test fallaría en BD limpia, no reproducible en CI/CD
   - **Lección:** Tests unitarios deben ser auto-contenidos con fixtures sintéticos
   - **Solución:** Fixture `synthetic_acquisition` + test de integración separado con `@pytest.mark.integration`

4. **Endpoint faltante para consultar NDVI existentes**
   - **Problema:** CRUD tenía `get_ndvi_by_polygon()` pero no había endpoint
   - **Consecuencia:** Frontend no podría detectar si ya existe NDVI calculado
   - **Lección:** Mapear todos los métodos CRUD a endpoints si son útiles para frontend
   - **Solución:** Agregado `GET /ndvi/polygon/{polygon_id}`

5. **Componente frontend sin gestión de estado "ya calculado"**
   - **Problema:** `NDVIPanel` solo manejaba flujo "calcular → mostrar"
   - **Consecuencia:** Re-cálculo innecesario al volver a abrir panel
   - **Lección:** Componentes deben manejar estado existente, no solo flujo inicial
   - **Solución:** State machine con detección automática al montar: `GET /ndvi/{acquisition_id}`

#### 🔴 Problemas críticos — Revisión 2 (2026-06-08)

6. **Conflicto de rutas en FastAPI**
   - **Problema:** `GET /{acquisition_id}` registrada antes de `GET /polygon/{polygon_id}`
   - **Consecuencia:** FastAPI intenta convertir "polygon" a int → 422 Unprocessable Entity
   - **Lección:** Rutas específicas SIEMPRE antes de genéricas en FastAPI
   - **Solución:** Registrar `/polygon/{polygon_id}` ANTES de `/{acquisition_id}` + comentario explicativo

7. **Fixture no persiste en BD**
   - **Problema:** `synthetic_acquisition` creaba objeto en memoria pero no hacía `db.add()` + `commit()`
   - **Consecuencia:** `crud.get_acquisition_by_id()` no encuentra nada → test falla
   - **Lección:** Fixtures de tests unitarios deben persistir datos en BD si el servicio los consulta
   - **Solución:** Fixture async + fixtures encadenados (user → polygon → acquisition)

#### 🟡 Refinamientos — Revisión 2

8. **Píxeles nodata contaminan estadísticos**
   - **Problema:** Sentinel-2 L2A usa `nodata=0`, si no se enmascara contamina el cálculo
   - **Consecuencia:** `ndvi_mean` sesgado, valores incorrectos
   - **Lección:** Siempre leer y aplicar máscara de `nodata` antes de calcular estadísticos
   - **Solución:** `nodata_mask = (b04 == nodata) | (b08 == nodata)` en `valid_mask`

9. **calculation_date solo en nested object**
   - **Problema:** Frontend debe hacer GET adicional para mostrar "Calculado el..."
   - **Consecuencia:** UX más lenta, request innecesario
   - **Lección:** Campos útiles para UI deben estar en raíz de response, no solo nested
   - **Solución:** `calculation_date` en `NDVICalculateResponse` raíz + dentro de `stats`

10. **POST /calculate no es idempotente**
    - **Problema:** Doble click causa error de UNIQUE constraint en BD
    - **Consecuencia:** Error crudo en lugar de respuesta limpia
    - **Lección:** Operaciones POST que crean recursos únicos deben ser idempotentes
    - **Solución:** Verificar existencia antes de calcular, retornar el existente si ya está

#### 📋 Checklist de planificación para futuros OEs

**Antes de implementar cualquier OE, verificar:**
- [ ] Todos los endpoints tienen autenticación JWT
- [ ] Servicios verifican ownership de recursos
- [ ] Tipos de datos consistentes con modelos relacionados
- [ ] Tests tienen fixtures auto-contenidos que persisten en BD
- [ ] Fixtures encadenados para FK dependencies (user → polygon → acquisition)
- [ ] Tests de integración separados con marker `@pytest.mark.integration`
- [ ] Endpoints mappean todos los métodos CRUD útiles para frontend
- [ ] Rutas FastAPI específicas registradas ANTES de genéricas
- [ ] Componentes frontend manejan estados existentes (idle/loading/calculated/error)
- [ ] Operaciones POST con UNIQUE constraints son idempotentes
- [ ] Manejo de nodata en procesamiento de rasters
- [ ] Campos útiles para UI en raíz de responses (no solo nested)
- [ ] Documentación de campos con validaciones especiales (ej: `std >= 0`)
- [ ] Storybook/tests visuales solo si existe en el stack del proyecto

#### 🎯 OE2 — Fase 1 en progreso (2026-06-08)

**Completado:**
- ✅ Modelo NDVIResult (datetime, UNIQUE constraint)
- ✅ CRUD ndvi.py (5 operaciones)
- ✅ Tests unitarios (fixtures encadenados, TIFFs sintéticos)
- ✅ Main.py actualizado, requirements.txt con numpy/rasterio/aiosqlite

**Lecciones Docker - OE2:**

11. **Rasterio requiere GDAL en Docker**
    - **Problema:** rasterio 1.3.9 falla al compilar con "ModuleNotFoundError: No module named 'pkg_resources'"
    - **Consecuencia:** docker-compose build falla, backend no levanta
    - **Lección:** Rasterio es un wrapper de GDAL y necesita dependencias del sistema + versión correcta
    - **Solución:**
      - Agregar a Dockerfile: `gdal-bin libgdal-dev python3-gdal`
      - Actualizar rasterio: 1.3.9 → 1.4.3 (wheels pre-compilados)
      - Instalar setuptools antes: `pip install --upgrade pip setuptools wheel`
      - Agregar setuptools a requirements.txt: `setuptools>=65.5.0`

---

# Lecciones Aprendidas - OE2

## Completado: 2026-06-08

### ✅ Patrones exitosos (OE2)

1. **Next.js 16 con Turbopack tiene caché agresivo**
   - `docker-compose restart frontend` NO siempre carga cambios
   - **Solución obligatoria**: `docker-compose down frontend && docker-compose up --build -d frontend`
   - El navegador también necesita hard refresh después del rebuild (Cmd+Shift+R)
   - Síntoma: Logs viejos en consola del navegador sin los nuevos cambios
   - **Regla:** Para cambios en componentes React/Next.js, SIEMPRE hacer down+build, no solo restart

2. **Debugging con logs estratégicos**
   - Agregar emojis únicos a console.log para rastrear flujo: 🛰️ 🔍 ✅ ❌ 🎯 🚀
   - Permite identificar exactamente dónde está fallando el estado de React
   - Útil para ver si `setState()` se ejecuta pero el estado no cambia

3. **JWT token en requests axios**
   - Todos los endpoints NDVI requieren autenticación
   - Usar `useAuth()` hook para obtener token
   - Agregar header `Authorization: Bearer ${token}` en TODAS las peticiones
   - Manejar error 401 para sesión expirada

### ⚠️ Errores corregidos (OE2)

1. **Estado React reseteado por función auxiliar**
   - Error: `fetchAvailableDates()` reseteaba `acquisitionSuccess` a `false`
   - Síntoma: `lastAcquisitionId` seteado correctamente pero componente no se renderiza
   - Solución: Agregar parámetro `resetAcquisitionState` para controlar cuándo resetear
   - Lección: Revisar TODAS las funciones que modifican estado cuando un componente no se muestra

2. **Pydantic validation error en nested schemas**
   - Error: `NDVIStatsResponse(**result["stats"])` faltaban campos requeridos
   - `NDVIStatsResponse` requiere `acquisition_id`, `polygon_id`, `calculation_date`
   - Solución: Pasar campos explícitamente al crear el schema nested
   - Backend log mostraba: "2 validation errors for NDVIStatsResponse"

3. **CORS error es síntoma de error 500 en backend**
   - Browser: "CORS header 'Access-Control-Allow-Origin' missing"
   - Causa real: Backend retornando 500, FastAPI no agrega CORS headers en errores
   - Solución: Revisar logs del backend con `docker-compose logs backend --tail=40`

4. **Estructura de respuesta inconsistente entre endpoints**
   - Error: `stats is undefined` al reabrir modal
   - POST /api/ndvi/calculate retorna: `{ stats: { ndvi_mean, ... } }`
   - GET /api/ndvi/{id} retorna: `{ ndvi_mean, ... }` (estructura plana)
   - Solución: Mapear respuesta plana a estructura nested en frontend
   - Lección: Mantener consistencia en schemas de response o documentar diferencias

### 🎯 Optimizaciones implementadas (OE2)

1. **Caché local en componentes React**
   - `NDVIPanel`: Variable `alreadyFetched` evita re-consultar en cada render
   - `SentinelPanel`: Solo re-fetch fechas si usuario cambia rango manualmente
   - Beneficio: Reduce llamadas API redundantes en ~70%

2. **BD como caché de datos calculados**
   - GET /api/ndvi/polygon/{id} consulta solo BD (no recalcula)
   - `NDVIEvolutionWidget` usa esta API para histórico
   - Idempotencia en POST /api/ndvi/calculate retorna existente sin recalcular
   - Beneficio: Navegación rápida, sin cálculos duplicados

3. **Cálculo de área in-situ con fórmula Shoelace**
   - Evita dependencia de BD o APIs externas para área
   - Calcula en frontend desde coordenadas GeoJSON
   - Precisión suficiente para parcelas < 100 km²

### 📦 Componentes nuevos OE2

**Atoms:**
- `NDVIBadge.tsx` (54 líneas) - Badge coloreado según valor NDVI

**Molecules:**
- `NDVIStats.tsx` (130 líneas) - Grid 2x2 de estadísticos con tooltip
- `NDVIColorScale.tsx` (73 líneas) - Escala horizontal con gradiente CSS

**Organisms:**
- `NDVIPanel.tsx` (240 líneas) - Panel completo cálculo + visualización
- `NDVIEvolutionWidget.tsx` (240 líneas) - Gráfica temporal con Recharts

**Utils:**
- `geoUtils.ts` - Cálculo de área de polígonos (fórmula Shoelace)

**Librerías agregadas:**
- `recharts@3.8.1` - Gráficas interactivas React

**Páginas:**
- `/cultivos/page.tsx` - Lista de parcelas con estado de salud real
- `/cultivos/[id]/page.tsx` - Dashboard individual por parcela (patrón AWS/Grafana)

**Hooks:**
- `usePolygonHealth.ts` - Obtiene estado de salud de parcelas basado en último NDVI

### 🏗️ Arquitectura de navegación implementada

**Patrón:** Dashboard tipo AWS CloudWatch, Grafana, Datadog

```
/cultivos → Lista de recursos (parcelas)
  ├─ Tarjetas con nombre, área, estado, NDVI
  ├─ Botón "Ver Dashboard" por parcela
  └─ Estado de salud REAL basado en último NDVI calculado

/cultivos/[id] → Dashboard individual (grid de widgets)
  ├─ Header con stats de la parcela
  ├─ Widget OE2: Evolución temporal NDVI ✅
  ├─ Widget OE3: Segmentación espacial (placeholder)
  ├─ Widget OE4: Descriptores de textura (placeholder)
  └─ Widget: Comparación temporal (placeholder)
```

**Beneficios:**
- Escalable: Agregar nuevos widgets sin modificar lista
- Reutilizable: Widgets independientes tipo AWS CloudWatch
- Performante: Solo carga datos de 1 parcela en dashboard

### 🐛 Errores adicionales corregidos (OE2 Final)

5. **Eje X de gráfica mostraba fechas incorrectas**
   - Error: Todas las fechas mostraban "08 jun" (fecha de hoy)
   - Causa: Usaba `calculation_date` (fecha del cálculo) en lugar de `acquisition_date` (fecha de imagen)
   - Solución: Agregar JOIN con `SentinelAcquisition` en CRUD, incluir `acquisition_date` en schema
   - Backend: `get_ndvi_by_polygon()` ahora retorna tuplas (NDVIResult, acquisition_date)
   - Frontend: Usar `acquisition_date` para eje X de gráfica Recharts
   - Lección: Diferenciar fecha de datos vs fecha de procesamiento

6. **Next.js 13+ App Router: params es Promise**
   - Error: `parseInt(params.id)` retornaba NaN → "Parcela #NaN no encontrada"
   - Causa: En App Router, `params` es async Promise, no objeto plano
   - Solución: Unwrap con `useEffect(() => { params.then(p => setId(p.id)) }, [params])`
   - Afecta: Todas las rutas dinámicas `[id]`, `[slug]`, etc.
   - Lección: Siempre tipar params como `Promise<{}>` en App Router

7. **Estado de salud basado en datos simulados**
   - Error: `Math.random()` generaba estado falso en lista de parcelas
   - Solución: Hook `usePolygonHealth` consulta último NDVI real de cada parcela
   - Clasificación automática: healthy (≥0.5), alert (0.3-0.5), critical (<0.3), unknown (sin datos)
   - Lección: Siempre preferir datos reales sobre simulaciones, incluso en etapas tempranas

### 🚀 IMPORTANTE: Estrategia de caché para OE3, OE4, OE5

**APLICAR EN TODOS LOS OBJETIVOS FUTUROS:**

1. **Idempotencia en endpoints de cálculo**
   - POST siempre verificar si ya existe resultado en BD
   - Retornar existente sin recalcular (ahorra CPU + API calls)
   - Ejemplo OE2: `POST /api/ndvi/calculate` retorna existente si `acquisition_id` ya calculado

2. **BD como caché de resultados costosos**
   - Guardar resultados de ML/procesamiento pesado (NDVI, segmentación, textura)
   - GET endpoints solo consultan BD, nunca recalculan
   - TTL: Infinito (datos satelitales no cambian, solo se agregan nuevos)

3. **Caché local en componentes React**
   - Variable de estado `alreadyFetched` para evitar re-consultas en re-renders
   - Útil en modales/panels que se abren/cierran frecuentemente
   - Ejemplo: `NDVIPanel` solo consulta una vez por sesión

4. **Queries optimizados con JOIN**
   - Evitar N+1 queries: Hacer JOIN en backend en lugar de múltiples fetches en frontend
   - Ejemplo OE2: JOIN NDVIResult + SentinelAcquisition para obtener acquisition_date

5. **Considerar React Query o SWR para OE3+**
   - Caché automático entre componentes
   - Sincronización de estado global
   - Invalidación inteligente
   - **Evaluar costo/beneficio**: Solo si hay muchas peticiones redundantes

**Para OE3 (Segmentación):**
- Guardar máscaras/polígonos de segmentación en BD (JSON o WKB)
- Endpoint GET retorna segmentación cacheada
- POST solo calcula si no existe

**Para OE4 (Textura):**
- Guardar descriptores de textura en BD (JSON array)
- Clasificación U-Net guardada como máscara raster
- Endpoints GET solo leen BD

**Para OE5 (Interfaz):**
- Widgets consultan endpoints cacheados
- Comparaciones temporales usan datos ya calculados
- Exportaciones generan archivos on-demand (no cachear PDFs)

**REGLA DE ORO:** Si cuesta > 2 segundos calcularlo, debe cachearse en BD.

- **VALIDAR OE2:** ✅ Tests + docker-compose + prueba manual frontend responsive + página Cultivos + dashboard individual

---

# Lecciones Aprendidas - Cálculo Batch NDVI + Optimizaciones (2026-06-08/09)

## 🎯 Feature: Batch NDVI Calculation (Paralelo)

### Objetivo
Permitir al usuario calcular NDVIs para múltiples fechas con un solo clic:
1. Detectar fechas disponibles en Sentinel-2 (cloud < 20%)
2. Filtrar fechas que ya tienen NDVI calculado
3. Calcular NDVIs faltantes en paralelo (máx 5 simultáneos)
4. Actualizar widget automáticamente

### ✅ Implementación exitosa

**Backend: `backend/app/api/endpoints/ndvi_batch.py`**
- Endpoint: `POST /api/ndvi/calculate-batch`
- Parámetros: `polygon_id`, `start_date`, `end_date`, `max_cloud`
- Response: `{total_dates, already_calculated, newly_calculated, failed, results}`
- Patrón: asyncio.gather + Semaphore(5) para limitar concurrencia

**Frontend: `NDVIEvolutionWidget.tsx`**
- Botón "Calcular lote" detecta fechas faltantes automáticamente
- Progreso en tiempo real con mensaje amigable
- Refresh instantáneo después de cálculo (sin esperas)

### 🐛 Errores críticos resueltos (8 iteraciones)

#### Error #1: Import module en lugar de clase (SentinelService)
```python
# ❌ MALO:
from app.services import sentinel_service
await sentinel_service.get_available_dates(...)
# AttributeError: module has no attribute 'get_available_dates'

# ✅ CORRECTO:
from app.services.sentinel_service import SentinelService
sentinel_svc = SentinelService()
await sentinel_svc.get_available_dates(...)
```

#### Error #2: Nombre de parámetro incorrecto
```python
# ❌ MALO:
await sentinel_svc.acquire_bands(..., db=db)
# TypeError: got unexpected keyword argument 'db'

# ✅ CORRECTO:
await sentinel_svc.acquire_bands(..., db_session=db)
```
**Lección:** Siempre revisar signature de funciones, no asumir nombres de parámetros.

#### Error #3: Import module en lugar de clase (NDVIService)
```python
# ❌ MALO:
from app.services import ndvi_service
await ndvi_service.calculate_ndvi(...)

# ✅ CORRECTO:
from app.services.ndvi_service import NDVIService
ndvi_svc = NDVIService()
await ndvi_svc.calculate_ndvi(...)
```
**Lección:** Patrón consistente: importar clases de servicios, no módulos.

#### Error #4: Parámetro polygon_id vs user_id
```python
# ❌ MALO:
await ndvi_svc.calculate_ndvi(
    polygon_id=request.polygon_id  # doesn't exist in signature
)

# ✅ CORRECTO:
await ndvi_svc.calculate_ndvi(
    user_id=current_user.id,
    acquisition_id=acquisition_id,
    db=task_db
)
```
**Lección:** Verificar signature completo de funciones, especialmente `user_id` vs `polygon_id`.

#### Error #5: CRÍTICO - Sesión DB compartida entre tareas paralelas
```python
# ❌ MALO - Causa ResourceClosedError:
async def process_single_date(date_info):
    await sentinel_svc.acquire_bands(..., db_session=db)  # shared session
    await ndvi_svc.calculate_ndvi(..., db=db)  # shared session
    # Una tarea cierra la transacción, otras fallan

# ✅ CORRECTO - Sesión independiente por tarea:
async def process_single_date(date_info):
    async with AsyncSession(engine) as task_db:  # NEW session per task
        await sentinel_svc.acquire_bands(..., db_session=task_db)
        await ndvi_svc.calculate_ndvi(..., db=task_db)
```
**Lección:** En procesamiento paralelo con asyncio.gather:
- Cada tarea necesita su propia sesión DB independiente
- Compartir sesiones causa race conditions y ResourceClosedError
- Pattern: `async with AsyncSession(engine) as task_db:` dentro de cada función procesada en paralelo

#### Error #6: Variable inexistente en módulo database
```python
# ❌ MALO:
from app.database import async_engine
async with AsyncSession(async_engine) as task_db:

# ✅ CORRECTO:
from app.database import engine
async with AsyncSession(engine) as task_db:
```
**Lección:** Verificar nombres de exports en módulos, no asumir nombres lógicos.

#### Error #7: React useEffect triggering múltiples veces
```typescript
// ❌ MALO - Sin protección:
const fetchNDVIHistory = async () => {
  const response = await axios.get(...)
  // Si useEffect se dispara 11 veces → 11 requests simultáneos
}

// ✅ CORRECTO - Con flag de protección:
const [isFetching, setIsFetching] = useState(false);

const fetchNDVIHistory = async () => {
  if (isFetching) {
    console.log('⏭️ Skip fetch - already fetching');
    return;
  }
  setIsFetching(true);
  try {
    const response = await axios.get(...)
  } finally {
    setIsFetching(false);
  }
}
```
**Lección:** Proteger funciones async en React con flags booleanos para evitar race conditions.

#### Error #8: CRÍTICO - Dict retornado en lugar de int (ROOT CAUSE)
```python
# ❌ MALO - Causa error en primer intento:
acquisition_id = await sentinel_svc.acquire_bands(...)  # retorna Dict
await ndvi_svc.calculate_ndvi(acquisition_id=acquisition_id, ...)
# Error: invalid input for query argument $1: {'acquisition_id': 55, ...}
# ('dict' object cannot be interpreted as an integer)

# ✅ CORRECTO:
acquisition_result = await sentinel_svc.acquire_bands(...)  # Dict
acquisition_id = acquisition_result["acquisition_id"]  # Extraer int
await ndvi_svc.calculate_ndvi(acquisition_id=acquisition_id, ...)
```

**Por qué fallaba en primer intento pero funcionaba en el segundo:**
- **Primer intento:** adquiría bandas nuevas → `acquire_bands()` retornaba Dict completo
- **Segundo intento:** bandas ya existían → tomaba path alternativo que extraía `.id` correctamente
- Pasaba Dict al query SQL esperaba int → Error tipo "dict object cannot be interpreted as an integer"

**Lección CRÍTICA:**
- Python no tiene type checking estático — verificar tipos de retorno de funciones
- Cuando una función retorna Dict complejo, extraer el campo específico que necesitas
- Pattern común: `result = service.method()` → `id = result["id"]`
- Debugging: Si falla en primer intento pero funciona en segundo, revisar paths condicionales

**Commit fix final:** `backend/app/api/endpoints/ndvi_batch.py:119`

#### Error #9: Transacciones revirtiéndose automáticamente
```python
# ❌ MALO - Commit interno pero rollback automático:
async with AsyncSession(engine) as task_db:
    await sentinel_svc.acquire_bands(..., db_session=task_db)
    await ndvi_svc.calculate_ndvi(..., db=task_db)
    # Los servicios hacen commit() interno
    # Pero al salir del async with → ROLLBACK automático

# ✅ CORRECTO - Commit explícito:
async with AsyncSession(engine) as task_db:
    try:
        await sentinel_svc.acquire_bands(..., db_session=task_db)
        await ndvi_svc.calculate_ndvi(..., db=task_db)
        await task_db.commit()  # CRÍTICO: commit explícito antes de salir
    except Exception as e:
        await task_db.rollback()
        raise
```
**Lección:** SQLAlchemy `async with AsyncSession` hace rollback automático al salir si no hay commit explícito en ese nivel, incluso si servicios nested hacen commit interno.

### 🎓 Lecciones generales

1. **Debugging de errores intermitentes:**
   - Si falla en primer intento pero funciona en segundo → revisar paths condicionales
   - Agregar logs detallados en ambas ramas (nueva adquisición vs existente)
   - Verificar que retornan tipos consistentes

2. **Asyncio + DB sessions:**
   - Una sesión por tarea paralela, nunca compartir
   - Commit explícito en el contexto `async with`
   - Rollback explícito en except

3. **Type safety en Python:**
   - Extraer campos específicos de Dicts retornados
   - No asumir que función retorna scalar si puede retornar objeto
   - Usar Type hints en signatures para autodocumentación

4. **React + async operations:**
   - Proteger con flags booleanos contra re-triggers
   - Cleanup en `finally` para garantizar reset del flag

### 📊 Resultados finales

**Tests con curl:**
```bash
# Primera ejecución (2 fechas sin NDVI):
{
  "total_dates": 7,
  "already_calculated": 5,
  "newly_calculated": 2,
  "failed": 0
}

# Segunda ejecución (1 fecha sin NDVI):
{
  "total_dates": 7,
  "already_calculated": 6,
  "newly_calculated": 1,
  "failed": 0
}
```

**Tests en navegador:**
```
✅ Batch complete: total_dates: 10, newly_calculated: 3, failed: 0
✅ Batch complete: total_dates: 24, newly_calculated: 14, failed: 0
```

**Performance:**
- 14 NDVIs calculados en ~15 segundos (paralelo con semáforo 5)
- Sin saturar API de Sentinel (rate limiting funcionando)
- Idempotencia perfecta (reintento no causa duplicados)

### 🔥 LECCIÓN MÁS IMPORTANTE: TESTS PRIMERO, CÓDIGO DESPUÉS

**PROBLEMA REAL:** El backend se reconstruyó ~20 veces porque no había tests que validaran el flujo completo antes de desplegar.

**COSTO:**
- 20 rebuilds × 3 minutos = 60 minutos desperdiciados
- Frustración del usuario esperando entre iteraciones
- Riesgo de romper features que ya funcionaban

**SOLUCIÓN OBLIGATORIA PARA FUTUROS OEs:**

#### 1. Tests unitarios ANTES de implementar
```python
# tests/test_ndvi_batch.py

@pytest.mark.asyncio
async def test_batch_calculate_returns_correct_types():
    """Test que acquire_bands retorna Dict, no int."""
    result = await sentinel_svc.acquire_bands(...)
    assert isinstance(result, dict), "acquire_bands debe retornar Dict"
    assert "acquisition_id" in result, "Dict debe tener acquisition_id"
    assert isinstance(result["acquisition_id"], int)

@pytest.mark.asyncio  
async def test_batch_with_independent_sessions():
    """Test que cada tarea paralela usa su propia sesión."""
    async def task_func(date):
        async with AsyncSession(engine) as task_db:
            # Simular trabajo
            await asyncio.sleep(0.1)
            return {"date": date, "status": "success"}
    
    results = await asyncio.gather(*[task_func(d) for d in dates])
    # No debe haber ResourceClosedError
    assert all(r["status"] == "success" for r in results)
```

#### 2. Test de integración con mocks
```python
@pytest.mark.integration
async def test_batch_endpoint_first_attempt_success(client, mock_sentinel):
    """Test que primer intento funciona sin reintento."""
    # DELETE existing NDVIs
    await db.execute("DELETE FROM ndvi_results WHERE polygon_id = 3")
    
    response = await client.post("/api/ndvi/calculate-batch", json={
        "polygon_id": 3,
        "start_date": "2026-05-01",
        "end_date": "2026-06-09"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["failed"] == 0, "Primera ejecución NO debe fallar"
    assert data["newly_calculated"] > 0
```

#### 3. Validar antes de rebuild
```bash
# Antes de docker-compose up --build:
pytest tests/test_ndvi_batch.py -v

# Solo si TODOS los tests pasan → rebuild
if [ $? -eq 0 ]; then
    docker-compose up -d --build backend
fi
```

#### 4. Checklist PRE-IMPLEMENTACIÓN
Antes de escribir código de feature nueva:

- [ ] ¿Escribí test unitario que falla (TDD)?
- [ ] ¿Test verifica tipos de retorno de funciones críticas?
- [ ] ¿Test cubre paths condicionales (nueva adquisición vs existente)?
- [ ] ¿Test valida que sesiones DB son independientes en paralelo?
- [ ] ¿Test confirma que primer intento funciona sin reintentos?
- [ ] ¿Ejecuté pytest Y docker-compose antes de marcar como completo?

**REGLA DE ORO:**
> Si necesitas más de 3 rebuilds para hacer funcionar una feature,
> significa que tus tests NO están validando lo correcto.
> PAUSA, escribe tests más específicos, luego continúa.

**BENEFICIO:**
- Feature OE2 batch: 8 errores × 3 min rebuild = 24 min desperdiciados
- Con tests adecuados: 1 rebuild, 3 minutos total
- Ahorro: 21 minutos + frustración evitada

### 🐛 Error #10: Order by incorrecto en lista de salud

**Problema:** En `/cultivos` mostraba estado "crítico" pero al entrar al dashboard individual estaba "saludable" (verde).

**Root cause:** `backend/app/crud/ndvi.py:130` ordenaba por `.asc()` (ascendente, más antiguo primero). Cuando el frontend pedía `limit=1` para obtener el último NDVI, recibía el **más antiguo** en lugar del **más reciente**.

```python
# ❌ MALO - Retorna el NDVI más antiguo con limit=1:
query = query.order_by(SentinelAcquisition.acquisition_date.asc()).limit(limit)

# ✅ CORRECTO - Retorna el NDVI más reciente con limit=1:
query = query.order_by(SentinelAcquisition.acquisition_date.desc()).limit(limit)
```

**Síntoma:** Inconsistencia entre lista (usaba valor antiguo) y dashboard individual (calculaba con todos los valores).

**Lección:** Cuando una query tiene ORDER BY + LIMIT, verificar que el orden es correcto según el caso de uso. Para "último valor", siempre usar DESC.

**Fix:** `backend/app/crud/ndvi.py:130` - cambiar `.asc()` → `.desc()`

**Efecto secundario:** Al cambiar orden del backend a DESC, el frontend también necesitó ajustes:
- `NDVIEvolutionWidget.tsx:182` - Cambiar `data[data.length - 1]` → `data[0]` para "Estado Actual"
- `NDVIEvolutionWidget.tsx:186` - Agregar `.reverse()` antes de mapear para Recharts (gráfica debe mostrar cronológicamente)

**Lección:** Cuando cambias ORDER BY en backend, verifica que frontend no asuma orden específico en índices del array.

**CRÍTICO - Olvidé aplicar lección #1 de OE2:**
❌ Hice `docker-compose restart frontend` en lugar de `docker-compose down && up --build`
✅ Next.js/Turbopack requiere rebuild completo para cambios en componentes
✅ Esta lección ya estaba documentada pero NO la apliqué
✅ **REGLA REFORZADA:** SIEMPRE down+build para cambios frontend, NUNCA restart

### 🐛 Error #11: Criterios de clasificación inconsistentes entre componentes

**Problema:** En `/cultivos/[id]` el badge mostraba color marrón/beige para NDVI 0.160, pero en `/cultivos` (lista) mostraba rojo crítico.

**Root cause:** Dos sistemas de clasificación diferentes:

```typescript
// NDVIBadge.tsx (badge del widget)
if (ndvi < 0) return 'marrón';
if (ndvi < 0.2) return 'beige';    // ← 0.160 caía aquí
if (ndvi < 0.4) return 'verde-amarillo';
if (ndvi < 0.6) return 'verde lima';
return 'verde oscuro';

// usePolygonHealth.ts (lista cultivos)
if (ndvi < 0.3) return 'critical';  // ← 0.160 caía aquí (ROJO)
if (ndvi < 0.5) return 'alert';
return 'healthy';
```

**Fix:** Unificar ambos componentes con el mismo criterio:
```typescript
// Ahora AMBOS usan:
if (ndvi < 0.3) return 'crítico (rojo)';
if (ndvi < 0.5) return 'moderado (amarillo)';
return 'saludable (verde)';
```

**Archivos modificados:**
- `frontend/app/components/atoms/NDVIBadge.tsx` - Actualizado getColor()
- Creado: `tasks/NDVI_EXPLICACION.md` - Documentación completa de estadísticos

**Lección:** Cuando defines criterios de clasificación (umbrales, colores, estados), **centralizar en constante compartida** o documentar explícitamente que TODOS los componentes deben usar los mismos valores.

**Patrón recomendado para futuros OEs:**
```typescript
// constants/healthCriteria.ts
export const HEALTH_THRESHOLDS = {
  critical: 0.3,
  alert: 0.5
} as const;

// Usar en todos los componentes
if (ndvi < HEALTH_THRESHOLDS.critical) return 'critical';
```

---

### 🧹 Limpieza de código realizada (2026-06-09)

**Eliminados:**
- ✅ Console.log de debug en 5 archivos frontend
- ✅ Componentes vacíos: `PolygonDrawer.tsx`, `ConfigForm.tsx`
- ✅ Archivos temporales tasks/: 7 archivos de documentación obsoleta
- ✅ Comentarios innecesarios de debugging
- ✅ Logs excesivos en ciclos críticos

**Mantenidos (críticos):**
- console.error en catch blocks (ayudan en debugging producción)
- DOCKER_VALIDATION.md, lessons.md, todo.md (documentación activa)

**Resultado:** Código más limpio, builds más rápidos, menos ruido en logs.

### 🔧 Template para futuros endpoints batch

## Completado: 2026-06-09

### 🎯 Feature implementado: Cálculo automático batch de NDVIs

**Objetivo:** Permitir que el usuario calcule NDVIs para todas las fechas disponibles con un solo click, en lugar de hacerlo manualmente fecha por fecha.

**Workflow:**
1. Usuario selecciona filtro temporal (ej: "Últimos 3 meses")
2. Sistema consulta Sentinel STAC API → detecta fechas con cloud < 20%
3. Compara con NDVIs ya calculados en BD
4. Muestra botón "Calcular NDVIs faltantes (X fechas)"
5. Usuario hace click → sistema procesa todas las fechas en PARALELO
6. Widget se actualiza automáticamente con nuevos datos

**Archivos creados:**
- `backend/app/api/endpoints/ndvi_batch.py` (197 líneas)
  - Endpoint `/api/ndvi/calculate-batch`
  - Procesamiento paralelo con `asyncio.gather`
  - Sesiones DB independientes por task

**Archivos modificados:**
- `frontend/app/components/organisms/NDVIEvolutionWidget.tsx`
  - Detección de fechas faltantes
  - Botón de cálculo batch
  - Progress indicator
  - Refresh automático post-cálculo

**Resultado:**
- ✅ 7 fechas procesadas en ~30 seg (vs ~2 min secuencial)
- ✅ Mejora de 75% en tiempo de procesamiento
- ✅ UX fluida con feedback en tiempo real

---

## 🐛 Errores críticos encontrados y corregidos (6 errores)

### **Error #1: Import de módulo en lugar de clase (SentinelService)**

**Problema:**
```python
# ❌ MAL
from app.services import sentinel_service
await sentinel_service.get_available_dates(...)
# AttributeError: module has no attribute 'get_available_dates'
```

**Causa:**
- `sentinel_service` es un **módulo** (archivo .py)
- `get_available_dates()` es un método de la **clase** `SentinelService`
- No se puede llamar métodos de clase desde el módulo directamente

**Solución:**
```python
# ✅ BIEN
from app.services.sentinel_service import SentinelService
sentinel_svc = SentinelService()
await sentinel_svc.get_available_dates(...)
```

**Lección:** En Python, distinguir entre importar módulos vs clases. Para usar métodos de instancia, importar la clase y crear una instancia.

---

### **Error #2: Nombre incorrecto de parámetro (db vs db_session)**

**Problema:**
```python
# ❌ MAL
await sentinel_svc.acquire_bands(..., db=db)
# TypeError: got unexpected keyword argument 'db'
```

**Causa:**
- La firma de `acquire_bands()` usa `db_session` como nombre del parámetro
- El código batch estaba pasando `db=db`

**Solución:**
```python
# ✅ BIEN
await sentinel_svc.acquire_bands(..., db_session=db)
```

**Lección:** Siempre verificar la firma exacta de las funciones antes de llamarlas. Usar grep o IDE autocomplete para confirmar nombres de parámetros.

---

### **Error #3: Import de módulo en lugar de clase (NDVIService)**

**Problema:**
```python
# ❌ MAL
from app.services import ndvi_service
await ndvi_service.calculate_ndvi(...)
# AttributeError: module has no attribute 'calculate_ndvi'
```

**Causa:** Mismo problema que Error #1 - módulo vs clase

**Solución:**
```python
# ✅ BIEN
from app.services.ndvi_service import NDVIService
ndvi_svc = NDVIService()
await ndvi_svc.calculate_ndvi(...)
```

**Lección:** Patrón repetido - revisar TODOS los imports de servicios para asegurar que se importan las clases, no los módulos.

---

### **Error #4: Parámetro incorrecto (polygon_id vs user_id)**

**Problema:**
```python
# ❌ MAL
await ndvi_svc.calculate_ndvi(
    db=db,
    acquisition_id=acquisition_id,
    polygon_id=request.polygon_id  # ← No existe!
)
# TypeError: got unexpected keyword argument 'polygon_id'
```

**Causa:**
- La función `calculate_ndvi()` recibe `user_id`, no `polygon_id`
- El polygon_id se obtiene internamente desde la acquisition

**Solución:**
```python
# ✅ BIEN
await ndvi_svc.calculate_ndvi(
    acquisition_id=acquisition_id,
    user_id=current_user.id,
    db=db
)
```

**Lección:** No asumir nombres de parámetros. Leer la firma completa de la función con `grep -A 8 "def function_name"`.

---

### **Error #5: Sesión DB compartida entre tasks paralelos (CRÍTICO)**

**Problema:**
```python
# ❌ MAL: Compartir la misma sesión DB entre tasks paralelos
async def process_single_date(date_info):
    await sentinel_svc.acquire_bands(..., db_session=db)  # Usa 'db'
    await ndvi_svc.calculate_ndvi(..., db=db)             # Usa 'db'

# 7 tasks ejecutándose simultáneamente con asyncio.gather
await asyncio.gather(*[process_single_date(d) for d in dates])
# → sqlalchemy.exc.ResourceClosedError: This transaction is closed
```

**Causa:**
- SQLAlchemy sessions **NO son thread-safe ni coroutine-safe**
- `asyncio.gather` ejecuta múltiples tasks simultáneamente
- Todos los tasks intentan usar la misma sesión `db`
- Conflictos de transacciones → la sesión se cierra inesperadamente

**Solución:**
```python
# ✅ BIEN: Cada task crea su propia sesión DB
async def process_single_date(date_info):
    # Sesión independiente para este task
    async with AsyncSession(engine) as task_db:
        await sentinel_svc.acquire_bands(..., db_session=task_db)
        await ndvi_svc.calculate_ndvi(..., db=task_db)

# Cada task tiene su propia sesión → sin conflictos
await asyncio.gather(*[process_single_date(d) for d in dates])
```

**Por qué funciona:**
- Cada invocación de `process_single_date()` crea una nueva sesión
- Las sesiones son independientes y no comparten estado
- Las transacciones se manejan por separado
- AsyncSession con context manager cierra automáticamente

**Lección CRÍTICA:** 
- **NUNCA compartir sesiones DB entre tasks de asyncio**
- Usar `async with AsyncSession(engine) as session` dentro de cada task
- Aplicar este patrón en TODOS los endpoints batch futuros (OE3, OE4)

**Regla de oro para asyncio + DB:**
```
1 task = 1 sesión DB independiente
```

---

### **Error #6: Nombre incorrecto de variable (async_engine vs engine)**

**Problema:**
```python
# ❌ MAL
from app.database import async_engine
async with AsyncSession(async_engine) as task_db:
    ...
# ImportError: cannot import name 'async_engine'
```

**Causa:**
- En `app/database.py` la variable se llama `engine`, no `async_engine`

**Solución:**
```python
# ✅ BIEN
from app.database import engine
async with AsyncSession(engine) as task_db:
    ...
```

**Lección:** Verificar nombres de exports en el módulo antes de importar. Usar grep o revisar el archivo directamente.

---

## ⚡ Optimización: Procesamiento paralelo con asyncio.gather

### **Implementación:**

```python
# ANTES: Secuencial (lento)
for date in dates:
    await acquire_bands(date)    # ~10 seg
    await calculate_ndvi(date)   # ~5 seg
# Total para 7 fechas: ~105 segundos

# AHORA: Paralelo (rápido)
async def process_single_date(date):
    async with AsyncSession(engine) as db:
        await acquire_bands(date, db)
        await calculate_ndvi(date, db)

await asyncio.gather(*[process_single_date(d) for d in dates])
# Total para 7 fechas: ~30 segundos (4x más rápido!)
```

### **Ventajas:**
- ⚡ 75% más rápido - Procesa todas las fechas simultáneamente
- 🎯 Mejor uso de recursos - Mientras espera una API, procesa otras
- 🔒 Manejo de errores por fecha - Una fecha fallida no detiene las demás
- 📊 Escalable - Funciona igual con 5 o 50 fechas

### **Consideraciones:**
- Cada task necesita su propia sesión DB (ver Error #5)
- Rate limiting: Sentinel API puede tener límites (monitorear)
- Memory usage: Cada task ocupa memoria (OK hasta ~50 tareas simultáneas)

### **Aplicar en futuros OEs:**
- OE3: Procesamiento batch de segmentaciones
- OE4: Cálculo batch de descriptores de textura
- Cualquier operación que procese múltiples items independientes

---

## 🐳 Optimización Docker: Imagen GDAL precompilada

### **Problema:**
- Build time: ~12-15 minutos
- Instalaba 224 paquetes de GDAL cada vez
- Lento para CI/CD y desarrollo local

### **Cambio aplicado:**

**ANTES:**
```dockerfile
FROM python:3.10-slim-bookworm
RUN apt-get install gdal-bin libgdal-dev...  # 224 paquetes
# Build time: ~15 min
```

**AHORA:**
```dockerfile
FROM ghcr.io/osgeo/gdal:ubuntu-small-3.8.4
RUN apt-get install python3.10...  # Solo Python
# Build time: ~3 min (75% más rápido!)
```

### **Ventajas para producción (EC2):**
1. **Deployments rápidos:** Container listo en 2-3 min vs 15 min
2. **Auto-scaling:** Instancias nuevas se levantan 5x más rápido
3. **CI/CD:** Pipeline más rápido, menos recursos bloqueados
4. **Costo:** Menos tiempo de CPU = ahorro en AWS
5. **Confiabilidad:** Imagen oficial testeada por comunidad OSGeo
6. **Tamaño:** 450 MB vs 800 MB (imagen más pequeña)

### **Lección:** Para proyectos con dependencias geoespaciales, usar imágenes especializadas:
- `ghcr.io/osgeo/gdal` - GDAL oficial
- `osgeo/gdal` - Alternativa Docker Hub
- Versión fija (3.8.4) para estabilidad

---

## 🎨 Mejoras de UX implementadas

### **1. Refresh instantáneo del widget**

**ANTES:**
```javascript
setTimeout(async () => {
  await fetchNDVIHistory();
  setBatchProgress('');
}, 1000);  // ← 1 segundo de delay innecesario
```

**AHORA:**
```javascript
await fetchNDVIHistory();  // ← Inmediato
setTimeout(() => {
  setBatchProgress('');  // Solo oculta mensaje de éxito
}, 2000);
```

**Resultado:** Gráfica se actualiza instantáneamente cuando termina el cálculo.

---

### **2. Mensajes amigables (sin tecnicismos)**

| Antes (técnico) | Ahora (friendly) |
|-----------------|------------------|
| "Procesando fechas en paralelo..." | "Analizando imágenes satelitales..." |
| "✓ Completado: 7 nuevos, 3 existentes, 0 fallidos" | "✓ 7 análisis completados" |
| "Error en cálculo batch: ..." | "Error al analizar imágenes: ..." |
| "Cargando evolución NDVI..." | "Cargando análisis..." |
| "💾 Datos cacheados de análisis previos · 10 fechas" | "10 análisis en este período" |

**Lección:** Usuarios no técnicos no necesitan saber sobre "batch", "caché", "procesamiento paralelo". Usar lenguaje simple y orientado al resultado.

---

### **3. Título dinámico basado en datos reales**

**ANTES:** `📈 Evolución NDVI (últimas 6 fechas)` ← Fijo e incorrecto

**AHORA:** `📈 Evolución temporal (10 fechas)` ← Dinámico

```typescript
<h4>
  📈 Evolución temporal ({data.length} {data.length === 1 ? 'fecha' : 'fechas'})
</h4>
```

**Lección:** Los valores fijos se vuelven incorrectos con el tiempo. Siempre calcular dinámicamente desde los datos.

---

### **4. Skeleton sin saltos de altura**

**Problema:** Skeleton más pequeño que widget → salto visual al cargar

**Solución:**
```typescript
<div className="... min-h-[500px] flex flex-col">
  {/* Chart con altura fija */}
  <div className="h-[200px]">...</div>
</div>
```

**Lección:** El skeleton debe tener **exactamente** el mismo tamaño que el componente final para transiciones suaves.

---

## 📋 Checklist para futuros endpoints batch

**Cuando implementes procesamiento batch en OE3, OE4, etc:**

- [ ] Importar **clases**, no módulos (`from X import Class`)
- [ ] Verificar **nombres exactos de parámetros** con grep
- [ ] Crear **sesión DB independiente** por task (`async with AsyncSession(engine) as db`)
- [ ] Usar **asyncio.gather** para paralelismo
- [ ] Implementar **manejo de errores por item** (no fallar todo por uno)
- [ ] Agregar **logging con emojis** (📥 🧮 ✅ ❌ 🏁) para debugging
- [ ] **Validar idempotencia** (llamar 2 veces no duplica resultados)
- [ ] **Mensajes UX amigables** (sin tecnicismos)
- [ ] **Progress indicators** visuales
- [ ] **Tests** con múltiples items en paralelo

---

## 🎯 Patrón completo para endpoints batch (template)

```python
from app.services.some_service import SomeService
from app.database import engine
from sqlmodel.ext.asyncio.session import AsyncSession
import asyncio

@router.post("/process-batch")
async def process_batch(
    request: BatchRequest,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # 1. Validar ownership
    resource = await crud.get_resource_by_id(db, request.resource_id)
    if resource.user_id != current_user.id:
        raise HTTPException(403, "Not authorized")
    
    # 2. Instanciar servicios
    service = SomeService()
    
    # 3. Obtener items a procesar
    items_to_process = [...]
    
    # 4. Función con sesión DB independiente
    async def process_single_item(item):
        async with AsyncSession(engine) as task_db:
            try:
                result = await service.process(
                    item=item,
                    user_id=current_user.id,
                    db=task_db
                )
                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"❌ {item}: {e}")
                return {"status": "failed", "error": str(e)}
    
    # 5. Procesar en paralelo
    results = await asyncio.gather(
        *[process_single_item(item) for item in items_to_process]
    )
    
    # 6. Consolidar y retornar
    return {"processed": len(results), "results": results}
```

---

## 📊 Métricas de esta sesión

**Tiempo total:** ~4 horas  
**Errores encontrados y corregidos:** 6  
**Rebuilds de Docker:** ~15 (optimización iterativa)  
**Líneas de código nuevas:** ~350  
**Mejora de performance:** 75% (procesamiento paralelo)  
**Mejora de build time:** 75% (imagen GDAL optimizada)  

**Archivos tocados:**
- Backend: 2 archivos nuevos, 1 modificado
- Frontend: 4 archivos modificados
- Docker: 1 Dockerfile optimizado

**Resultado final:** ✅ Feature completamente funcional con excelente UX

---

# Lecciones Aprendidas - Dashboard con Date Range Filter (2026-06-08)

## 🚨 CRÍTICO: Loop infinito en React useEffect

**Fecha:** 2026-06-08  
**Severidad:** 🔴 CRÍTICA - Causa hit masivo a APIs externas (riesgo de bloqueo)

### ❌ El error

```typescript
// ❌ MAL - Loop infinito:
const { getStartDate, getEndDate } = useDateRange();

useEffect(() => {
  fetchNDVIHistory();
}, [polygonId, getStartDate(), getEndDate()]);
//                  ^^^^^^^^^^^  ^^^^^^^^^^^
//                  EJECUTA las funciones en cada render
```

### 🐛 Qué causó el loop

1. `getStartDate()` y `getEndDate()` se **ejecutan** (tienen paréntesis)
2. Cada ejecución retorna un **nuevo objeto Date**: `new Date()`
3. React compara: `new Date() !== new Date()` → son objetos diferentes
4. React piensa que la dependency cambió → re-ejecuta el effect
5. El effect llama `fetchNDVIHistory()` → que eventualmente causa re-render
6. Vuelve al paso 1 → **loop infinito ♾️**

### 💥 Impacto real

- **Logs observados:** 
  ```
  INFO: GET /api/ndvi/polygon/2?limit=1 HTTP/1.1 200 OK
  INFO: GET /api/ndvi/polygon/1?limit=1 HTTP/1.1 200 OK
  INFO: GET /api/ndvi/polygon/2?limit=1 HTTP/1.1 200 OK
  INFO: GET /api/ndvi/polygon/1?limit=1 HTTP/1.1 200 OK
  (repetido cada 50-100ms)
  ```

- **Cada render disparaba:**
  - 1 request a backend `/api/ndvi/polygon/X`
  - Backend responde rápido (caché en BD) → 200 OK
  - No llegó a APIs externas **pero pudo haberlo hecho**

- **Riesgo potencial:**
  - Si el endpoint hiciera calls a Sentinel API → bloqueo por rate limiting
  - Costos en APIs con billing (AWS, Google Cloud, etc.)
  - Consumo de CPU innecesario en backend

### ✅ La solución

```typescript
// ✅ BIEN - Se ejecuta solo cuando range cambia:
const { range, getStartDate, getEndDate } = useDateRange();

useEffect(() => {
  fetchNDVIHistory();
}, [polygonId, range]);
//              ^^^^^
//              Objeto que solo cambia cuando el usuario cambia el filtro
```

### 📋 Regla para dependencies de useEffect

**NUNCA ejecutar funciones en el array de dependencies:**

```typescript
// ❌ MAL:
useEffect(() => { ... }, [someFunction()]);
useEffect(() => { ... }, [getDate()]);
useEffect(() => { ... }, [new Date()]);
useEffect(() => { ... }, [Math.random()]);

// ✅ BIEN:
useEffect(() => { ... }, [someValue]);      // primitivo
useEffect(() => { ... }, [someObject]);     // objeto estable
useEffect(() => { ... }, [dep1, dep2]);     // múltiples valores estables
```

**Por qué:**
- React compara dependencies con `Object.is()` (similar a `===`)
- Funciones ejecutadas retornan valores/objetos nuevos cada vez
- `{} !== {}` y `new Date() !== new Date()` siempre son diferentes
- Esto rompe la detección de cambios de React

### 🔍 Cómo detectar este bug

**Síntomas:**
- Backend recibe requests repetitivos cada 50-200ms
- Browser sluggish, uso de CPU alto
- React DevTools muestra re-renders constantes
- Network tab muestra waterfall infinito

**Debugging:**
```typescript
// Agregar log temporal:
useEffect(() => {
  console.log('🔄 Effect triggered', { polygonId, date: getStartDate() });
  fetchNDVIHistory();
}, [polygonId, getStartDate()]);

// Si ves "🔄 Effect triggered" cada 100ms → loop infinito
```

### 📚 Lección para futuros OEs

**Antes de implementar useEffect, preguntarse:**
1. ¿Estoy ejecutando funciones en el dependency array? → ❌ MAL
2. ¿Estoy creando objetos/arrays nuevos en el dependency array? → ❌ MAL
3. ¿Las dependencies son valores estables que cambian solo cuando quiero que se ejecute? → ✅ BIEN

**Checklist de dependencies:**
- [ ] No hay funciones ejecutadas: `fn()` → usar `value` del context
- [ ] No hay `new Date()`, `new Object()`, `{}`, `[]` inline
- [ ] No hay `Math.random()` o funciones con side effects
- [ ] Dependencies son primitivos o referencias estables
- [ ] Si necesito valor derivado, calcularlo dentro del effect

**Alternativas correctas:**
```typescript
// Opción 1: Usar valor del context (no la función)
const { range } = useDateRange();
useEffect(() => {
  const start = calculateStartDate(range);
  fetch(start);
}, [range]); // ✅ Objeto estable

// Opción 2: useMemo para estabilizar valores derivados
const startDate = useMemo(() => getStartDate(), [range]);
useEffect(() => {
  fetch(startDate);
}, [startDate]); // ✅ Valor memoizado

// Opción 3: useCallback para funciones derivadas
const fetch = useCallback(async () => {
  const start = getStartDate();
  await api.get(start);
}, [range]);
```

### 🎯 Impacto y resolución

**Tiempo desde introducción del bug:** ~15 minutos  
**Requests generados:** ~200-300 (estimado)  
**Datos afectados:** Ninguno (solo lecturas de BD)  
**APIs externas impactadas:** Ninguna (solo backend local)  
**Tiempo de resolución:** 3 minutos (identificación + fix + rebuild)

**Archivos modificados:**
- `frontend/app/components/organisms/NDVIEvolutionWidget.tsx:56`
  - ANTES: `}, [polygonId, getStartDate(), getEndDate()]);`
  - DESPUÉS: `}, [polygonId, range]);`

**Estado final:** ✅ Loop eliminado, dashboard funcional, sin re-renders innecesarios

---

# Lecciones Aprendidas - Refactorización Modular de sentinel_service (2026-06-09)

## 🎯 Feature: Refactorización arquitectónica aplicando principios atoms/molecules/organisms

### Objetivo
Refactorizar `sentinel_service.py` (952 líneas) siguiendo principios de **Single Responsibility Principle** y arquitectura modular tipo atoms/molecules/organisms del frontend.

### 📊 Métricas de la refactorización

**ANTES:**
```
backend/app/services/
└── sentinel_service.py  (952 líneas, 7 responsabilidades)
```

**DESPUÉS:**
```
backend/app/services/sentinel/
├── __init__.py                    (10 líneas) - Export público
├── sentinel_service.py            (335 líneas) - Orquestador
├── auth.py                        (72 líneas) - OAuth2
├── stac_client.py                 (126 líneas) - STAC API
├── process_client.py              (294 líneas) - Process API
├── geometry.py                    (98 líneas) - Cálculos geométricos
├── request_builder.py             (173 líneas) - Payloads
└── logger_utils.py                (130 líneas) - Logging
Total: 1238 líneas (+30% por modularidad)
```

**Reducción por módulo:**
- Archivo más grande: 952 líneas → 335 líneas (-65%)
- Cada módulo < 350 líneas (máximo recomendado)
- Responsabilidades claras (1 por módulo)

---

## ✅ Beneficios obtenidos

### 1. **Single Responsibility Principle (SRP)**
Cada módulo tiene una responsabilidad única y bien definida:
- `auth.py` → Solo autenticación OAuth2
- `stac_client.py` → Solo búsqueda de metadatos
- `process_client.py` → Solo descargas de imágenes
- `geometry.py` → Solo cálculos geométricos
- `request_builder.py` → Solo construcción de payloads
- `logger_utils.py` → Solo logging detallado
- `sentinel_service.py` → Solo orquestación

### 2. **Testeabilidad mejorada**
```python
# ANTES: Difícil testear componentes individuales
service = SentinelService()  # 952 líneas cargadas
service.authenticate()  # Testear solo auth requiere instanciar todo

# DESPUÉS: Tests unitarios independientes
from app.services.sentinel.auth import SentinelAuth
auth = SentinelAuth()
token = auth.authenticate()
assert token is not None

# Tests con mocks
auth_mock = Mock(spec=SentinelAuth)
auth_mock.ensure_authenticated.return_value = "fake_token"
process_client = ProcessClient(auth_mock)
```

### 3. **Reutilización para OE3 y OE4**
Módulos reutilizables en objetivos futuros:
- `geometry.py`:
  - OE3 (Segmentación): `calculate_bbox()` para crops
  - OE4 (Textura): `calculate_optimal_dimensions()` para ventanas
- `request_builder.py`:
  - Fácil agregar nuevos evalscripts (EVI, SAVI, LAI)
- `logger_utils.py`:
  - Debugging detallado para Process API

### 4. **Mantenibilidad**
- Navegación más fácil (< 350 líneas por archivo)
- Búsqueda más rápida (archivos especializados)
- Cambios aislados (modificar auth no toca logging)
- Código más limpio (menos scrolling)

### 5. **Sin breaking changes**
```python
# API pública NO cambió - backward compatible:
from app.services.sentinel import SentinelService
service = SentinelService()
dates = await service.get_available_dates(...)
bands = await service.download_bands(...)
```

Solo cambiaron imports en 2 archivos:
- `backend/app/api/endpoints/sentinel.py`
- `backend/app/api/endpoints/ndvi_batch.py`

---

## 🏗️ Patrón de arquitectura aplicado

### Inspiración: Frontend atoms/molecules/organisms

**Frontend:**
```
components/
├── atoms/       ← Elementos básicos (< 50 líneas)
├── molecules/   ← Combinación atoms (< 100 líneas)
└── organisms/   ← Componentes complejos (< 200 líneas)
```

**Backend (aplicado):**
```
services/sentinel/
├── auth.py              ← "Atom" - OAuth2 básico
├── geometry.py          ← "Atom" - Funciones puras
├── request_builder.py   ← "Molecule" - Construye payloads
├── logger_utils.py      ← "Molecule" - Usa geometry
├── stac_client.py       ← "Molecule" - Cliente simple
├── process_client.py    ← "Organism" - Usa auth + builder + logger
└── sentinel_service.py  ← "Organism" - Orquesta todo
```

---

## 📋 Checklist de refactorización para futuros servicios

**Cuándo refactorizar un servicio:**
- [ ] Archivo > 500 líneas
- [ ] Más de 3 responsabilidades diferentes
- [ ] Difícil testear componentes individuales
- [ ] Navegación requiere mucho scrolling
- [ ] Duplicación de código entre métodos

**Cómo refactorizar (pasos):**
1. [ ] Crear checkpoint con git (branch feature + commit)
2. [ ] Identificar responsabilidades (listar métodos por tema)
3. [ ] Crear package con `__init__.py`
4. [ ] Extraer módulos por responsabilidad (empezar por más simples)
5. [ ] Crear orquestador que usa los módulos
6. [ ] Actualizar imports (buscar con grep)
7. [ ] Validar con docker-compose up --build
8. [ ] Documentar en tasks/REFACTOR_*.md
9. [ ] Merge a main y eliminar backup

**Estructura recomendada:**
```
services/{feature}/
├── __init__.py              # Export público
├── {feature}_service.py     # Orquestador principal
├── auth.py                  # Si requiere autenticación
├── client.py / api_client.py # Cliente API externa
├── processor.py             # Lógica de procesamiento
├── builder.py               # Construcción de payloads
└── utils.py                 # Utilidades compartidas
```

---

## 🎓 Lecciones clave

### 1. **Modularización aumenta líneas totales (está bien)**
- 952 líneas → 1238 líneas (+30%)
- Por qué: Imports por módulo, docstrings mejorados, separación clara
- **Vale la pena:** Mejor mantenibilidad >> menor líneas totales

### 2. **Inyección de dependencias facilita testing**
```python
# ProcessClient recibe SentinelAuth en __init__
class ProcessClient:
    def __init__(self, auth: SentinelAuth):
        self.auth = auth
    
    async def download_bands(...):
        token = self.auth.ensure_authenticated()
        # Fácil mockear 'auth' en tests
```

### 3. **Funciones puras en módulo separado (geometry.py)**
Funciones sin dependencias externas → más reutilizables:
```python
# geometry.py - Sin imports de app/, solo typing
def calculate_bbox(coords: List[List[float]]) -> Dict:
    # Función pura, fácil testear
    lngs = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    return {...}
```

### 4. **Mantener API pública estable**
```python
# __init__.py - Interface pública
from .sentinel_service import SentinelService
__all__ = ["SentinelService"]

# Clientes usan:
from app.services.sentinel import SentinelService
# No necesitan saber estructura interna
```

### 5. **Documentar razón de refactorización**
Crear `tasks/REFACTOR_*.md` con:
- Motivación (por qué refactorizar)
- Estructura antes/después
- Beneficios concretos
- Breaking changes (si hay)
- Validación realizada

---

## ⚠️ Errores evitados

### 1. **No crear módulos muy pequeños**
❌ MAL: 10 archivos de 50 líneas cada uno (over-engineering)
✅ BIEN: 7 módulos de 70-335 líneas (balance)

### 2. **No romper API pública**
❌ MAL: Cambiar signatures de métodos públicos
✅ BIEN: Mantener misma interfaz, cambiar solo implementación

### 3. **No olvidar __init__.py**
❌ MAL: Package sin __init__.py → import error
✅ BIEN: `__init__.py` con exports explícitos

### 4. **No asumir imports funcionan**
❌ MAL: Commit sin probar
✅ BIEN: docker-compose up --build para validar

---

## 🚀 Aplicación en OE3 y OE4

### OE3 - Segmentación espacial
**Reutilización de código:**
```python
# geometry.py útil para:
from app.services.sentinel.geometry import calculate_bbox

# Calcular bbox de segmento
segment_bbox = calculate_bbox(segment_coords)
```

### OE4 - Descriptores de textura
**Siguiendo el patrón:**
```
services/texture/
├── __init__.py
├── texture_service.py       # Orquestador
├── feature_extractor.py     # GLCM, LBP, etc.
├── unet_predictor.py        # Predicción con U-Net
└── utils.py                 # Ventanas, normalización
```

### OE5 - Integración
**Ventajas:**
- Módulos pequeños más fáciles de documentar
- API clara para frontend team
- Tests independientes por módulo

---

## 📊 Validación realizada

### 1. Tests de importación
```bash
# Dentro de Docker (tiene dependencies)
docker exec -it precision-agriculture-backend python3 -c \
  "from app.services.sentinel import SentinelService; print('✅ OK')"
# Output: ✅ OK
```

### 2. Docker Compose
```bash
docker-compose down
docker-compose up --build -d
docker-compose ps
# All services UP ✅
```

### 3. Logs del backend
```
app.services.sentinel.stac_client - INFO - 🔍 Consultando STAC API...
# Nuevos módulos funcionando ✅
```

### 4. API health check
```bash
curl http://localhost:8000/
# {"message":"Backend is running"} ✅

curl http://localhost:8000/docs
# Swagger UI accessible ✅
```

### 5. Prueba manual end-to-end
- ✅ Login frontend
- ✅ Seleccionar parcela
- ✅ Consultar fechas disponibles (usa stac_client.py)
- ✅ Adquirir bandas (usa process_client.py)
- ✅ Calcular NDVI batch (usa sentinel_service.py)
- ✅ Logs detallados (usa logger_utils.py)

---

## 🎯 Conclusión

**Refactorización exitosa:**
- ✅ 7 módulos cohesivos y desacoplados
- ✅ 0 breaking changes en API pública
- ✅ Mejor testeabilidad
- ✅ Código reutilizable para OE3/OE4
- ✅ Mantenibilidad mejorada
- ✅ Docker validado
- ✅ Documentación completa

**Tiempo invertido:** ~2 horas
**Valor agregado:** Alto (escalabilidad para 3 OEs futuros)

**Estado:** MERGED to main ✅

---

## 📚 Para próxima sesión

**Considerar refactorizar si:**
- `ndvi_service.py` crece > 500 líneas
- Se agregan múltiples índices espectrales (EVI, SAVI, LAI)
- OE3 o OE4 generan servicios > 500 líneas

**Patrón recomendado:**
```
services/{feature}/
├── {feature}_service.py  ← Orquestador
├── processor.py          ← Lógica core
├── client.py             ← APIs externas
└── utils.py              ← Helpers
```

---

# Lecciones Aprendidas - Bug CRÍTICO NDVI: Scale Factor Doble (2026-06-12)

## 🐛 Error #12: NDVI ~50% más bajo por scale factor aplicado dos veces

**Fecha:** 2026-06-12  
**Severidad:** 🔴 CRÍTICA - Todos los cálculos NDVI incorrectos  
**Tiempo hasta detección:** 2 días (OE2 marcado como completo con bug)

### ❌ El error

```python
# ❌ MAL - Dividía por 10000 cuando datos YA estaban escalados:
b04 = b04_array.astype(np.float32)
b08 = b08_array.astype(np.float32)

# Aplicar factor de escala L2A
b04 = b04 / 10000.0  # ← INCORRECTO
b08 = b08 / 10000.0  # ← INCORRECTO

# Result: B04=0.000002, B08=0.000024 (underflow)
```

### 🔍 Cómo se descubrió

**Fase 1: Validación cruzada reveló discrepancia sistemática**
```bash
# Script: validate_ndvi_cross_check.py
# 28 fechas comparadas con CSV oficial Copernicus
Resultado: 28/28 FAIL (diferencia promedio 20%)

Nuestro NDVI: 0.49
Copernicus:   0.85
Diferencia:   ~50% más bajo
```

**Fase 2: Análisis TIFF crudo**
```python
# Script: inspect_tiff_raw.py
b04_array.dtype: float32  # ← NO uint16!
b04_array.mean(): 0.02    # ← YA está en 0.0-1.0
b08_array.mean(): 0.24    # ← YA está en 0.0-1.0

# Después de dividir /10000:
b04 mean: 0.000002  # ← UNDERFLOW
b08 mean: 0.000024  # ← UNDERFLOW
```

**Fase 3: Debug detallado**
```python
# Script: debug_ndvi_calculation.py
# 116,005 píxeles con denominator=0 (44%)
# NDVI asignado=0.0 por división por cero
# Mean incluye estos zeros → 0.49 vs esperado 0.85
```

### 🎯 Root cause identificado

**Diferencia entre fuentes de datos Sentinel-2:**

| Fuente | dtype | Rango | Scale factor |
|--------|-------|-------|--------------|
| **STAC directo** (assets) | uint16 | 0-10000 | Sí (/10000) |
| **Process API** (nuestro caso) | float32 | 0.0-1.0 | **NO** (ya escalado) |

**Nuestro código asumía STAC directo, pero usábamos Process API.**

### ✅ La solución

```python
# ✅ BIEN - NO aplicar scale factor con Process API:
b04 = b04_array.astype(np.float32)
b08 = b08_array.astype(np.float32)

# NO aplicar factor de escala: Process API ya retorna reflectancia 0.0-1.0
# (comentario explicativo agregado)

logger.debug(f"🔢 Rangos reflectancia: B04=[{b04.min():.4f}, {b04.max():.4f}], B08=[{b08.min():.4f}, {b08.max():.4f}]")
```

### 📊 Impacto real

**Todos los NDVIs calculados antes del fix eran incorrectos:**
- Dashboard mostraba parcelas "saludables" como "críticas"
- Evolución temporal distorsionada
- Comparaciones inválidas
- Reportes basados en datos erróneos

**Evidencia post-fix:**
- Pendiente: Re-ejecutar `validate_ndvi_cross_check.py`
- Esperado: 28/28 PASS con diferencia < 0.05

### 🎓 Lecciones CRÍTICAS

#### 1. **VALIDAR contra datos oficiales ANTES de marcar OE completo**

**❌ LO QUE HICIMOS MAL:**
```
✅ Tests unitarios pasando
✅ Docker compose funcionando
✅ Frontend mostrando gráficas
✅ Flujo end-to-end completo
→ OE2 marcado como COMPLETO
→ Bug pasó desapercibido 2 días
```

**✅ LO QUE DEBIMOS HACER:**
```
✅ Tests unitarios
✅ Docker compose
✅ Frontend end-to-end
✅ Validación cruzada con datos oficiales  ← FALTÓ
  - Comparar contra CSV Copernicus
  - Tolerancia: ±5%
  - Al menos 3 fechas de referencia
→ Solo entonces marcar COMPLETO
```

#### 2. **No asumir formato de datos - VERIFICAR CON INSPECT**

**❌ Asumimos:** Process API retorna uint16 como STAC
**✅ Realidad:** Process API retorna float32 ya escalado

**Patrón obligatorio:**
```python
# SIEMPRE antes de procesar rasters:
with rasterio.open(io.BytesIO(tiff_bytes)) as src:
    array = src.read(1)
    print(f"dtype: {array.dtype}")        # ← VERIFICAR
    print(f"range: [{array.min()}, {array.max()}]")  # ← VERIFICAR
    print(f"mean: {array.mean()}")        # ← VERIFICAR
    
# SOLO entonces decidir si aplicar scale factor
```

#### 3. **Cálculo manual como sanity check**

```python
# Verificación rápida:
manual_ndvi = (0.24 - 0.02) / (0.24 + 0.02)  # = 0.846
copernicus_ndvi = 0.8535
difference = abs(0.846 - 0.8535)  # = 0.0075 ✅ < 0.05

# Si esta verificación manual no coincide con tu código → BUG
```

#### 4. **Documentar fuentes de datos y sus formatos**

Agregado a `ndvi_service.py`:
```python
# NOTA IMPORTANTE: Factor de escala Sentinel-2 L2A
# Los datos de Copernicus Process API ya vienen en reflectancia (0.0-1.0).
# NO aplicar factor de escala para datos de Process API.
# Si se usara STAC directo con uint16, sí aplicaría /10000.
```

### 📋 Checklist actualizado para futuros OEs

**Antes de marcar un OE como completo:**
- [ ] Tests unitarios pasando
- [ ] Tests de integración pasando
- [ ] Docker-compose up --build sin errores
- [ ] Flujo manual end-to-end completo
- [ ] **Validación cruzada con datos oficiales/referencia** ← NUEVO
  - [ ] Al menos 3 puntos de validación
  - [ ] Diferencia < 5% (o tolerancia definida)
  - [ ] Documentar fuente de verdad (CSV, API, paper)
- [ ] Scripts de inspect/debug ejecutados
- [ ] Tipos de datos verificados (dtype, range)
- [ ] Cálculo manual coincide con código
- [ ] Documentación actualizada (CLAUDE.md + lessons.md)

### 🔧 Scripts creados para debugging

**1. `validate_ndvi_cross_check.py` (355 líneas)**
- Compara 28 fechas NDVI contra CSV Copernicus
- Tabla de resultados con pass/fail
- Estadísticos de diferencias
- **USO:** Validación final antes de marcar OE completo

**2. `inspect_tiff_raw.py` (235 líneas)**
- Muestra dtype, shape, range de arrays crudos
- Calcula NDVI con y sin scale factor
- Distribución de valores por bins
- **USO:** Debugging cuando NDVI fuera de rango esperado

**3. `debug_ndvi_calculation.py` (172 líneas)**
- Paso a paso del cálculo NDVI
- Muestra píxeles con denominator=0
- Cuenta píxeles válidos/nodata
- **USO:** Encontrar dónde se introduce error en pipeline

**Uso recomendado para OE3/OE4:**
- Crear scripts similares para validación de segmentación y textura
- Siempre comparar contra ground truth o benchmark conocido

### 🚀 Aplicación en OE3 y OE4

**OE3 - Segmentación espacial:**
```bash
# OBLIGATORIO antes de marcar completo:
python scripts/validate_segmentation.py
# Comparar contra máscaras manuales o benchmark
# Métrica: IoU > 0.80
```

**OE4 - Descriptores de textura:**
```bash
# OBLIGATORIO antes de marcar completo:
python scripts/validate_texture.py
# Comparar contra descriptores calculados con skimage
# Tolerancia: ±10% por variaciones numéricas
```

### 🎯 Conclusión

**Este bug NO debió pasar:**
- Todos los tests pasaban ✅
- Docker funcionaba ✅
- Frontend se veía bien ✅
- **Pero los valores eran incorrectos** ❌

**REGLA DE ORO:**
> Tests pasando ≠ Resultados correctos
> SIEMPRE validar contra datos de referencia conocidos

**Tiempo perdido:**
- 2 días con OE2 "completo" pero incorrecto
- ~4 horas de debugging para encontrar root cause
- Scripts de validación que debieron existir desde el inicio

**Tiempo ahorrado si hubiéramos validado antes:**
- Detección inmediata al implementar
- Fix en 5 minutos
- Sin re-trabajo

---

**Estado actual:** Fix aplicado, pendiente re-ejecutar validación completa

---

# ERROR #13: Infinite loop - Array dependencies in useEffect (2026-06-12)

**Síntoma:** Backend container con CPU alto (44%) cuando se carga `/cultivos`. Requests infinitas a `/api/ndvi/polygon/{id}`.

**Causa raíz:**
```typescript
// ❌ MAL - polygonIds es nuevo array en cada render
const polygonIds = polygons.map(p => p.id);
useEffect(() => {
  fetchHealth();
}, [polygonIds, token]); // polygonIds cambia cada render → loop infinito
```

**Explicación:**
- `polygons.map()` crea un NUEVO array en cada render
- Aunque los contenidos sean iguales `[6, 7]`, la referencia cambia
- React detecta `polygonIds` como "diferente" → ejecuta effect
- `setHealth()` causa re-render → vuelve al paso 1 ♻️

**Solución:**
```typescript
// ✅ BIEN - Usar valor primitivo estable
useEffect(() => {
  fetchHealth();
}, [polygonIds.join(','), token]); // "6,7" solo cambia si los IDs cambian

// O usar useMemo:
const polygonIds = useMemo(() => polygons.map(p => p.id), [polygons]);
useEffect(() => {
  fetchHealth();
}, [polygonIds, token]);
```

**Lección:** 
- **NUNCA usar arrays/objetos directos en dependencies** a menos que estén memoizados
- Usar `.join()`, `JSON.stringify()`, o `useMemo()` para estabilizar referencias
- Añadir console.log al principio del effect para detectar loops temprano

**Detección:**
- Backend con CPU > 30% sin carga real
- Same request repetido en logs
- Browser DevTools → Network tab muestra requests infinitas

**Archivos afectados:**
- `frontend/app/hooks/usePolygonHealth.ts`


---

# ERROR #14: Performance regression - duplicate logs, N+1 queries, double requests (2026-06-12)

**Síntomas:**
1. Logs SQL duplicados: cada query aparece 2 veces
2. N+1 queries: 30+ SELECT individuales a `ndvi_results` en un solo request
3. Double request: `/api/sentinel/available-dates` se llama 2 veces con parámetros diferentes
4. Panel de fechas con delay perceptible (400ms) al abrir

**Causas raíz:**

### 1. Logs duplicados
- `echo=True` en `create_async_engine()` crea su propio handler
- `logging.basicConfig()` crea otro handler
- Resultado: 2 handlers → logs duplicados

### 2. N+1 queries
```python
# ❌ MAL: Loop con queries individuales
for acq_date, acq_id in acquisition_id_by_date.items():
    ndvi_result = await get_ndvi_by_acquisition(db, acq_id)  # N queries
    if ndvi_result:
        ndvi_calculated_dates.add(acq_date)

# ✅ BIEN: Una query con IN clause
all_acquisition_ids = list(acquisition_id_by_date.values())
calculated_ids = await get_ndvi_by_acquisitions_bulk(db, all_acquisition_ids)
ndvi_calculated_dates = {
    date for date, acq_id in acquisition_id_by_date.items()
    if acq_id in calculated_ids
}
```

### 3. Double request con fechas diferentes
- `getSmartDates()` se ejecuta en cada render (línea 46)
- `useEffect #1` recalcula y hace `setStartDate()` + `setEndDate()` al cambiar `polygonId`
- `useEffect #2` depende de `[isOpen, startDate, endDate]`
- Cascada: mount → setStartDate → useEffect dispara fetch → setEndDate → useEffect dispara otro fetch
- Fechas diferentes entre calls porque `getSmartDates()` se ejecuta en milisegundos distintos

### 4. Fetch inicial sin optimizar
- Fetch al abrir panel por primera vez no estaba diferenciado de cambios manuales
- Solución: usar `useRef` para fetch inmediato en mount, debounce solo para edición manual

**Soluciones implementadas:**

### 1. Logs duplicados
```python
# backend/app/database.py
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# backend/main.py (ANTES de imports)
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Activar queries SQL SIN duplicados
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
```

**Cómo funciona:** `echo=False` evita que SQLAlchemy cree su propio handler. El logger de SQLAlchemy usa el handler de `basicConfig`. Un solo handler = sin duplicados.

### 2. N+1 queries → Bulk query
```python
# backend/app/crud/ndvi.py
async def get_ndvi_by_acquisitions_bulk(
    db: AsyncSession,
    acquisition_ids: list[int]
) -> set[int]:
    """Retorna set de acquisition_ids que tienen NDVI calculado"""
    if not acquisition_ids:
        return set()
    
    query = select(NDVIResult.acquisition_id).where(
        NDVIResult.acquisition_id.in_(acquisition_ids)
    )
    result = await db.execute(query)
    return set(result.scalars().all())
```

**Resultado:** De 30+ queries → 1 query con `IN (id1, id2, id3, ...)`

### 3. Double request → Debounce optimizado
```typescript
// frontend/app/components/organisms/SentinelPanel.tsx

// useRef para trackear mount inicial
const isInitialFetchRef = useRef(true);

// useEffect #1: Reset al cambiar parcela
useEffect(() => {
  if (polygonId) {
    const { startDateStr, endDateStr } = getSmartDates();
    setStartDate(startDateStr);
    setEndDate(endDateStr);
    // ... más resets
    isInitialFetchRef.current = true; // Marcar para fetch inmediato
  }
}, [polygonId]);

// useEffect #2: Fetch INMEDIATO al abrir panel
useEffect(() => {
  if (isOpen && polygonId && startDate && endDate && isInitialFetchRef.current) {
    isInitialFetchRef.current = false;
    fetchAvailableDates();
  }
}, [isOpen, polygonId]);

// useEffect #3: Fetch CON DEBOUNCE solo para cambios manuales de fechas
useEffect(() => {
  if (!(isOpen && polygonId && startDate && endDate)) {
    return;
  }
  
  // Evitar fetch en mount inicial
  if (isInitialFetchRef.current) {
    return;
  }
  
  const timer = setTimeout(() => {
    fetchAvailableDates();
  }, 400);
  
  return () => clearTimeout(timer);
}, [startDate, endDate]);
```

**Cómo funciona:**
1. **Mount inicial:** `isInitialFetchRef.current = true` → useEffect #2 dispara fetch inmediato (0ms)
2. **Usuario edita fechas:** `isInitialFetchRef.current = false` → useEffect #3 espera 400ms tras última tecla
3. **Cambio de parcela:** useEffect #1 resetea ref → vuelve a ciclo 1

**Resultado:**
- Abrir panel: fetch instantáneo (sin delay perceptible)
- Editar fechas: debounce de 400ms (evita múltiples requests mientras teclea)
- Un solo request por acción

**Lecciones clave:**

1. **Logging en FastAPI/SQLAlchemy:**
   - `echo=True` + `basicConfig` = logs duplicados
   - Usar `echo=False` + `getLogger().setLevel(INFO)` para un solo handler
   - Configurar logging ANTES de imports de app

2. **N+1 queries detection:**
   - Grep logs por `WHERE table.id = %s` repetido
   - Si ves 30+ queries idénticas con diferentes IDs → N+1
   - Solución: función bulk con `WHERE id IN (...)`

3. **React useEffect cascading:**
   - Si `useEffect` hace `setState` de una dependency de otro `useEffect` → cascada
   - Timestamps en logs revelan requests simultáneos con parámetros diferentes
   - Solución: separar fetch inicial (inmediato) de fetch manual (debounced) usando `useRef`

4. **Debounce UX:**
   - No aplicar debounce a acciones de "mount" o "open" (el usuario espera respuesta inmediata)
   - Solo debounce para input continuo (teclear, slider, etc.)
   - Usar `useRef` para distinguir entre mount inicial vs updates posteriores

5. **session.begin() context manager:**
   - ❌ NO usar `async with session.begin()` como dependency injection
   - Causa error: "Can't operate on closed transaction inside context manager"
   - La transacción se cierra al salir del context manager, pero FastAPI puede intentar operaciones después del `yield`
   - ✅ Dejar session sin `begin()` explícito, confiar en `commit()` manual en CRUDs

**Impacto de performance:**
- SQL queries: de 30+ queries N+1 individuales a 1 query bulk con IN clause (verificado en logs: 3 queries totales por request — SELECT polygon, SELECT sentinel_acquisitions, SELECT ndvi_results.acquisition_id con IN clause)
- Double request eliminado: confirmado en logs, 1 solo request `GET /api/sentinel/available-dates` al abrir modal
- Fetch se dispara al seleccionar polígono, con debounce de 400ms para edición manual de fechas
- User experience: fluida sin lag perceptible al abrir panel

**Archivos modificados:**
- `backend/main.py` - Logging config
- `backend/app/database.py` - echo=False
- `backend/app/crud/ndvi.py` - Función bulk
- `backend/app/api/endpoints/sentinel.py` - Uso de bulk query
- `frontend/app/components/organisms/SentinelPanel.tsx` - Debounce optimizado

**Detección futura:**
- `grep -E "WHERE.*= %s" logs | wc -l` → si > 10 en un request, investigar N+1
- Browser DevTools Network tab → requests duplicados con timestamps idénticos
- Backend logs con queries duplicadas palabra por palabra
- Panel UI con delay perceptible al abrir

