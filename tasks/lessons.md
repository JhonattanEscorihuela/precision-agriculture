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

### 🚀 Siguiente: OE2

Migrar cálculo NDVI de notebook a `ndvi_service.py`:
- Leer B04 y B08 desde BD (usar `acquisition_id`)
- Calcular NDVI: `(B08 - B04) / (B08 + B04)`
- Guardar resultado en modelo `NDVIAnalysis`
- Endpoint `POST /api/ndvi/calculate`
- Frontend: Visualización NDVI con mapa de calor
- **VALIDAR:** Tests + docker-compose + prueba manual frontend responsive
