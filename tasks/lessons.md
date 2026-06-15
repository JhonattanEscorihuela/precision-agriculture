# Lecciones Aprendidas - OE1

## Completado: 2026-05-23 (FINAL)

### ✅ Patrones exitosos

1. **Arquitectura en capas funciona**
   - Modelos → CRUD → Servicios → Endpoints
   - Nunca lógica de negocio en endpoints
   - Separación clara de responsabilidades

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

### Evidencia OE1 (2026-05-23)

- 16 fechas aptas (2025, cloud < 20%, Parcela 211 SRRG)
- Mejor fecha: 2025-12-31 (9.28% nubes)
- Bandas: B04 25KB, B08 24KB guardadas en BD
- Flujo manual completo verificado: register → login → parcela → fechas → adquirir → logout

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

### OE2 Debugging (2026-06-08)

- Next.js 16 caché agresivo → siempre `down + build`, nunca `restart`
- CORS error → revisar backend logs (500 esconde CORS)
- JWT en headers → usar `useAuth()` hook

---

### Error crítico: Sesiones DB compartidas en asyncio (2026-06-08)

**Problema:** AsyncSession compartida entre tasks paralelos → ResourceClosedError  
**Solución:** Una sesión por task con `async with AsyncSession(engine) as task_db`  
**Lección:** 1 task = 1 sesión independiente. Commit explícito antes de salir del context.

### Regla TDD: Más de 3 rebuilds = tests inadecuados (2026-06-08)

Si necesitas >3 rebuilds para una feature, PAUSA y escribe tests más específicos.

### Asyncio batch pattern (2026-06-08)

Patrón: asyncio.gather() con sesión independiente por task. Docker: usar imagen ghcr.io/osgeo/gdal para evitar compilar GDAL.

---

### Loop infinito: `getStartDate()` ejecutado en dependencies (2026-06-08)

**Causa:** `new Date()` retorna objeto nuevo cada vez → React detecta cambio → loop  
**Fix:** Usar valor estable `range` del context, no ejecutar funciones en dependencies

---

### Refactorización modular sentinel/ (2026-06-09)

952 líneas → 7 módulos (auth, stac_client, process_client, geometry, request_builder, logger_utils, sentinel_service). Patrón SRP aplicado. Ver CLAUDE.md arquitectura backend.

---

### Bug crítico: Scale factor aplicado 2 veces (2026-06-12)

**Causa:** Process API retorna float32 [0-1], asumimos uint16 [0-10000] → dividimos /10000 de nuevo  
**Impacto:** Todos los NDVIs ~50% más bajos  
**Fix:** NO aplicar scale factor con Process API (ya escalado)  
**Lección:** SIEMPRE inspeccionar dtype/range antes de procesar rasters. Validar contra CSV oficial Copernicus antes de marcar OE completo.

---

### Loop infinito: Array dependencies useEffect (2026-06-12)

`polygons.map()` crea nuevo array cada render → loop. Fix: `.join(',')` o `useMemo`.


---

### Performance regression (2026-06-12)

1. **Logs duplicados:** `echo=True` + `basicConfig` → 2 handlers. Fix: `echo=False` + `getLogger().setLevel(INFO)`
2. **N+1 queries:** Loop con SELECT individual. Fix: `WHERE id IN (...)` bulk query
3. **Double request:** useEffect cascada por `setState` de dependencies. Fix: `useRef` para fetch inmediato en mount, debounce solo para edición manual

---

