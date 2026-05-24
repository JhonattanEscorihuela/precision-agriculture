# OE1 - Identificar escenas Sentinel-2 aptas via STAC API

## ✅ COMPLETADO: 2026-05-23

---

## 📋 Objetivo

Implementar sistema completo de consulta y adquisición de imágenes satelitales Sentinel-2 mediante STAC API (metadatos) y Process API (descarga), filtrando por cobertura de nubes ≤20% según especificación del proyecto.

---

## 🎯 Funcionalidades Implementadas

### Backend

1. **Autenticación de usuarios**
   - Registro y login con JWT (30 días expiración)
   - Passwords hasheados con bcrypt
   - Modelo `User` con campos: email, full_name, hashed_password
   - Endpoints: `/auth/register`, `/auth/login`, `/auth/me`

2. **OAuth2 Copernicus Dataspace**
   - Client ID y Secret configurados
   - Token refresh automático
   - Integración con Process API

3. **STAC API - Consulta de disponibilidad**
   - Endpoint: `GET /api/sentinel/available-dates/{polygon_id}`
   - Parámetros: `start_date`, `end_date`, `max_cloud` (default 20%)
   - Respuesta: Lista de fechas aptas con % nubosidad
   - Sin autenticación (API pública)

4. **Process API - Adquisición de bandas**
   - Endpoint: `POST /api/sentinel/acquire`
   - Body: `{ polygon_id, date }`
   - Descarga B04 (Red) y B08 (NIR) en formato TIFF
   - Guarda en BD como bytea (~25KB cada banda)
   - Requiere OAuth2

5. **Modelos de datos**
   - `User`: id, email, full_name, hashed_password, is_active, created_at
   - `Polygon`: id, name, coordinates, area, user_id (FK CASCADE), created_at, updated_at
   - `SentinelAcquisition`: id, polygon_id (FK CASCADE), acquisition_date, cloud_cover, band_b04, band_b08, created_at

6. **CRUD completo**
   - `crud/user.py`: create, get_by_email, get_by_id
   - `crud/polygon.py`: create, get_all, get_by_user, update, delete
   - `crud/acquisition.py`: create, get_by_polygon, get_by_date, check_exists

7. **Servicios de negocio**
   - `sentinel_service.py`:
     - `get_available_dates()`: Consulta STAC, filtra nubes
     - `acquire_bands()`: Descarga bandas, guarda en BD
   - `auth_logic.py`: Funciones de seguridad (en `core/security.py`)

### Frontend

1. **Sistema de autenticación**
   - `AuthContext`: Estado global de usuario + token
   - `ProtectedRoute`: Wrapper para rutas protegidas
   - Login page (`/login`): Email + password
   - Register page (`/register`): Full name + email + password + confirm
   - Axios interceptors: JWT automático en headers, 401 → logout

2. **Atomic Design Components**
   - **Atoms**:
     - `DateBadge.tsx`: Badge de fecha con indicador de adquisición
   - **Molecules**:
     - `DateSelector.tsx`: Selector de fechas con badges interactivos
     - `AcquireButton.tsx`: Botón de adquisición con estados (loading, success, error)
   - **Organisms**:
     - `SentinelPanel.tsx`: Panel completo de consulta y adquisición

3. **SentinelPanel - Panel de adquisición**
   - Inputs de rango de fechas (inicio/fin)
   - Consulta de fechas disponibles
   - Selector visual de fechas
   - Botón de adquisición
   - Mensajes de error/éxito
   - **Responsive**:
     - Desktop: Panel lateral derecho (w-96)
     - Mobile: Modal inferior (max-h-85vh, rounded-t-3xl)
     - Overlay en mobile para cerrar

4. **Fechas inteligentes**
   - Fecha inicio: Primer día del mes hace 6 meses
   - Fecha fin: Hoy
   - Fechas futuras bloqueadas (max attribute)
   - Reset automático al cambiar de parcela

5. **Integración con mapa**
   - Click en polígono → zoom + abre SentinelPanel
   - Panel no bloquea interacción con mapa
   - Cambio de parcela → reseteo completo del panel

6. **Diseño responsive**
   - Sidebar: Hamburger menu en mobile (<1024px)
   - Layout adaptativo: `p-4 sm:p-6 lg:p-8`
   - Grid cultivos: 1 col mobile → 2 tablet → 3 desktop
   - Forms: Stack vertical, inputs escalables
   - Breakpoints: sm:640px, md:768px, lg:1024px, xl:1280px

---

## 🧪 Testing

### Tests implementados

1. **test_stac_api.py**
   - Consulta STAC con Parcela 211
   - Filtro de nubosidad ≤20%
   - Validación de estructura de respuesta

2. **test_acquisition_model.py**
   - CRUD de SentinelAcquisition
   - Validación de campos
   - Foreign keys CASCADE

3. **test_oe1_complete.py**
   - Flujo end-to-end completo
   - Consulta + adquisición + verificación BD
   - Coordenadas reales Venezuela

### Validación end-to-end

✅ `pytest tests/` → todos pasando  
✅ `docker-compose up --build` → sin errores  
✅ Frontend localhost:3000  
✅ Backend localhost:8000  
✅ API Docs localhost:8000/docs  
✅ Flujo manual:
  - Register → Login
  - Dibujar parcela
  - Click parcela → consultar fechas
  - Seleccionar fecha → adquirir bandas
  - Verificar en BD: B04 + B08 guardadas
  - Logout → nuevo usuario → parcelas aisladas

---

## 📊 Evidencia de completitud

### Parcela de referencia: 211 - SRRG Calabozo, Venezuela

**Coordenadas:**
```python
[-67.528058, 8.8441233],
[-67.5153475, 8.8386166],
[-67.5103962, 8.8478932],
[-67.522828,  8.8534209],
[-67.528058, 8.8441233]  # cerrado
```

**Resultados de consulta:**
- Período: 2025-01-01 → 2025-12-31
- Filtro: max_cloud ≤ 20%
- **Fechas encontradas: 16**
- Mejor fecha: 2025-12-31 (9.28% nubes)

**Bandas adquiridas:**
- B04 (Red): 25KB TIFF, 128x128px
- B08 (NIR): 24KB TIFF, 128x128px
- Formato: bytea en PostgreSQL
- Guardado exitoso ✅

---

## 🏗️ Arquitectura implementada

```
Backend:
  api/endpoints/
    auth.py          → /auth/register, /auth/login, /auth/me
    polygons.py      → CRUD parcelas (protegido)
    sentinel.py      → /sentinel/available-dates, /sentinel/acquire
  
  models/
    user.py          → User model
    polygon.py       → Polygon model con user_id FK
    acquisition.py   → SentinelAcquisition model
  
  crud/
    user.py          → create_user, get_user_by_email
    polygon.py       → CRUD + get_by_user
    acquisition.py   → create, get_by_polygon
  
  services/
    sentinel_service.py  → get_available_dates, acquire_bands
  
  core/
    security.py      → JWT, password hashing, get_current_user

Frontend:
  context/
    AuthContext.tsx     → Estado global usuario + token
    PolygonContext.tsx  → Estado global parcelas
  
  components/
    atoms/
      DateBadge.tsx
    molecules/
      DateSelector.tsx
      AcquireButton.tsx
    organisms/
      SentinelPanel.tsx (responsive)
    ProtectedRoute.tsx
    SideBar.tsx (responsive)
  
  pages/
    login/page.tsx
    register/page.tsx
    page.tsx               → Mapa principal
    cultivos/page.tsx      → Lista parcelas
    nueva-parcela/page.tsx → Cargar parcelas
```

---

## 🔒 Seguridad

- ✅ JWT tokens (30 días expiración)
- ✅ Bcrypt para passwords
- ✅ OAuth2 password flow
- ✅ ProtectedRoute verifica token antes de renderizar
- ✅ Axios interceptors: JWT automático + 401 handling
- ✅ Foreign keys CASCADE: user → polygons → acquisitions
- ✅ CORS configurado
- ✅ Sin flash de contenido protegido

---

## 📱 Responsive Design

**Mobile-first approach:**
- iPhone SE (375px) ✅
- iPad (768px) ✅
- Desktop (1920px) ✅

**Componentes adaptados:**
- Sidebar → Hamburger menu mobile
- SentinelPanel → Modal inferior mobile
- Forms → Stack vertical mobile
- Grid cultivos → 1/2/3 columnas según breakpoint
- Padding/spacing → escalables

---

## 📈 Métricas

**Código:**
- Backend: ~1500 líneas, 8 archivos nuevos
- Frontend: ~1200 líneas, 11 componentes nuevos
- Tests: 3 archivos, todos pasando

**Funcional:**
- 16 fechas aptas encontradas (Venezuela 2025)
- Bandas 25KB cada una (optimizado)
- Autenticación completa funcionando
- Responsive 375px - 1920px

---

## 🎓 Lecciones clave

1. **SQLModel CASCADE**: Usar `sa_column=Column(Integer, ForeignKey(..., ondelete="CASCADE"))`
2. **Circular imports**: Mover funciones para evitar ciclos
3. **Bcrypt directo**: Mejor que passlib para simplicidad
4. **Tipos consistentes**: number vs string entre frontend/backend
5. **Estado aislado**: Reset completo al cambiar props (polygonId)
6. **Docker validation**: OBLIGATORIO antes de marcar completo
7. **Responsive**: Mobile-first, breakpoints Tailwind

---

## ✅ Criterios de aceptación OE1

| Criterio | Estado |
|----------|--------|
| STAC API integrada | ✅ |
| Filtro cloud_cover ≤ 20% | ✅ |
| Process API con OAuth2 | ✅ |
| Descarga B04 + B08 | ✅ |
| Guardar en BD | ✅ |
| Frontend consulta fechas | ✅ |
| Frontend adquiere bandas | ✅ |
| UI responsive | ✅ |
| Autenticación usuarios | ✅ |
| Parcelas por usuario | ✅ |
| Tests pasando | ✅ |
| Docker funciona | ✅ |
| Flujo manual completo | ✅ |

---

## 🚀 Próximo paso: OE2

**Aplicar cálculo de índices espectrales (NDVI)**

Tareas:
1. Migrar notebook NDVI a `ndvi_service.py`
2. Crear modelo `NDVIAnalysis`
3. Endpoint `POST /api/ndvi/calculate`
4. Frontend: Visualización mapa de calor NDVI
5. Tests + Docker + Responsive

**NDVI formula:** `(B08 - B04) / (B08 + B04)`

---

**OE1 STATUS: COMPLETADO ✅**
