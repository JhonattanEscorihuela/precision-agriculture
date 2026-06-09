# Refactorización sentinel_service.py - 2026-06-09

## 🎯 Objetivo

Refactorizar `sentinel_service.py` (952 líneas) aplicando principios de separación de responsabilidades, similar a la arquitectura atoms/molecules/organisms del frontend.

---

## 📊 Antes vs Después

### Antes: Monolito de 952 líneas
```
backend/app/services/
└── sentinel_service.py  (952 líneas)
    ├── Autenticación OAuth2
    ├── Cálculos geométricos
    ├── Construcción de payloads
    ├── Logging detallado
    ├── Cliente STAC API
    ├── Cliente Process API
    └── Lógica de orquestación
```

**Problemas:**
- ❌ Difícil de testear componentes individuales
- ❌ Difícil de navegar (952 líneas)
- ❌ Múltiples responsabilidades en una clase
- ❌ Duplicación de código de logging

### Después: Arquitectura Modular (1238 líneas total, 7 módulos)

```
backend/app/services/sentinel/
├── __init__.py                    (10 líneas)  ← Export público
├── sentinel_service.py            (335 líneas) ← Orquestador principal
├── auth.py                        (72 líneas)  ← Autenticación OAuth2
├── geometry.py                    (98 líneas)  ← Cálculos geométricos
├── request_builder.py             (173 líneas) ← Construcción payloads
├── logger_utils.py                (130 líneas) ← Logging detallado
├── stac_client.py                 (126 líneas) ← Cliente STAC API
└── process_client.py              (294 líneas) ← Cliente Process API
```

**Beneficios:**
- ✅ Cada módulo < 350 líneas (testeabilidad)
- ✅ Responsabilidades claras (Single Responsibility Principle)
- ✅ Reutilización (geometry.py útil para OE3/OE4)
- ✅ Testing más fácil (mockear componentes individuales)
- ✅ **SIN alterar lógica de negocio** (misma API pública)

---

## 🏗️ Arquitectura de Módulos

### 1. `auth.py` - Autenticación (72 líneas)
**Responsabilidad:** Gestionar tokens OAuth2.

```python
class SentinelAuth:
    def authenticate() -> str
    def ensure_authenticated() -> str
    @property token -> Optional[str]
```

**Uso:**
```python
auth = SentinelAuth()
token = auth.ensure_authenticated()
```

---

### 2. `geometry.py` - Cálculos Geométricos (98 líneas)
**Responsabilidad:** Operaciones sobre coordenadas.

```python
def calculate_bbox(coords) -> Dict
def calculate_optimal_dimensions(coords) -> Tuple[int, int]
def is_polygon_closed(coords) -> bool
```

**Reutilizable en OE3/OE4:**
- OE3 (Segmentación): Calcular bbox para crops
- OE4 (Textura): Dimensiones óptimas para análisis

---

### 3. `request_builder.py` - Constructor de Payloads (173 líneas)
**Responsabilidad:** Generar evalscripts y request payloads.

```python
def build_bands_evalscript(bands) -> str
def build_ndvi_evalscript() -> str
def build_true_color_evalscript() -> str
def build_check_availability_evalscript() -> str
def build_process_request(...) -> Dict
```

**Ventaja:** Centraliza construcción de evalscripts, fácil agregar nuevos índices (EVI, SAVI).

---

### 4. `logger_utils.py` - Logging Detallado (130 líneas)
**Responsabilidad:** Logging estructurado para diagnóstico.

```python
def log_request_details(operation, polygon_geojson, request_payload, polygon_id)
def log_response_details(operation, response, success)
```

**Ventaja:** Imports de geometry (DRY), usado por process_client.

---

### 5. `stac_client.py` - Cliente STAC API (126 líneas)
**Responsabilidad:** Búsqueda de fechas disponibles (metadatos).

```python
class STACClient:
    async def get_available_dates(...) -> List[Dict]
```

**Características:**
- No requiere autenticación
- Independiente de Process API
- Fácil testear con mocks

---

### 6. `process_client.py` - Cliente Process API (294 líneas)
**Responsabilidad:** Descargas de imágenes satelitales.

```python
class ProcessClient:
    def __init__(auth: SentinelAuth)
    async def download_bands(...) -> bytes
    async def download_ndvi(...) -> bytes
    async def download_true_color(...) -> bytes
    async def check_availability(...) -> Dict
```

**Características:**
- Inyección de dependencias (auth)
- Usa request_builder y logger_utils
- Testeable con auth mock

---

### 7. `sentinel_service.py` - Orquestador (335 líneas)
**Responsabilidad:** API pública, orquesta componentes.

```python
class SentinelService:
    def __init__(self)
        self.auth = SentinelAuth()
        self.stac_client = STACClient()
        self.process_client = ProcessClient(self.auth)

    # Delegates to specialized clients
    async def get_available_dates(...) -> List[Dict]
    async def download_bands(...) -> bytes
    async def download_ndvi(...) -> bytes
    async def download_true_color(...) -> bytes
    async def check_availability(...) -> Dict
    async def acquire_bands(...) -> Dict  # OE1 business logic
```

**Ventaja:** Misma API pública, sin breaking changes.

---

## 🔧 Cambios en Código Cliente

### Actualización de Imports (2 archivos)

**Antes:**
```python
from app.services.sentinel_service import SentinelService
```

**Después:**
```python
from app.services.sentinel import SentinelService
```

**Archivos actualizados:**
- `backend/app/api/endpoints/sentinel.py`
- `backend/app/api/endpoints/ndvi_batch.py`

**✅ Sin cambios en uso:** La API de `SentinelService` se mantiene idéntica.

---

## ✅ Validación

### 1. Tests de Importación
```bash
python3 -c "from app.services.sentinel import SentinelService"
# ✅ OK dentro de Docker
```

### 2. Docker Compose
```bash
docker-compose down
docker-compose up --build -d
docker-compose ps
# ✅ All services UP
```

### 3. Logs Backend
```
app.services.sentinel.stac_client - INFO - 🔍 Consultando STAC API...
# ✅ Nuevo módulo funcionando
```

### 4. API Health
```bash
curl http://localhost:8000/
# {"message":"Backend is running"}
curl http://localhost:8000/docs
# ✅ Swagger UI accessible
```

---

## 📈 Métricas de Refactorización

| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| **Archivo más grande** | 952 líneas | 335 líneas | -65% |
| **Número de módulos** | 1 | 7 | Modularidad |
| **Responsabilidades por módulo** | 7 | 1 | SRP ✅ |
| **Testeable** | Difícil | Fácil | Mocks individuales |
| **Navegabilidad** | Difícil | Fácil | < 350 líneas/módulo |
| **Reutilización** | Baja | Alta | geometry.py en OE3/OE4 |

---

## 🧪 Testing Futuro (Facilitado)

### Antes (Difícil):
```python
# Testear solo autenticación requería instanciar todo SentinelService
service = SentinelService()  # 952 líneas cargadas
service.authenticate()
```

### Después (Fácil):
```python
# Test unitario de autenticación (solo 72 líneas)
from app.services.sentinel.auth import SentinelAuth
auth = SentinelAuth()
token = auth.authenticate()
assert token is not None

# Test con mock
from unittest.mock import Mock
auth_mock = Mock(spec=SentinelAuth)
auth_mock.ensure_authenticated.return_value = "fake_token"
process_client = ProcessClient(auth_mock)
```

---

## 🎯 Próximos OEs Beneficiados

### OE3 - Segmentación Espacial
**Reutilización:**
- `geometry.calculate_bbox()` → Para calcular bbox de segmentos
- `geometry.calculate_optimal_dimensions()` → Dimensiones de crops

### OE4 - Descriptores de Textura
**Reutilización:**
- `geometry.py` → Ventanas de análisis
- `request_builder.py` → Nuevos evalscripts para textura

### OE5 - Integración
**Ventaja:**
- Módulos pequeños más fáciles de documentar
- API clara para frontend team

---

## 📝 Lecciones Aprendidas

### ✅ Lo que funcionó bien:
1. **Arquitectura inspirada en frontend:** atoms/molecules/organisms escaló bien a backend
2. **Inyección de dependencias:** ProcessClient recibe SentinelAuth
3. **Backward compatibility:** Misma API pública, cero breaking changes
4. **Validación incremental:** Backup → Refactor → Test → Commit

### ⚠️ Consideraciones:
1. **Total líneas aumentó:** 952 → 1238 (+286 líneas)
   - **Por qué:** Imports por módulo, docstrings mejorados
   - **Vale la pena:** Mejor mantenibilidad y testabilidad
2. **Import paths cambiaron:** Requiere actualización en 2 archivos
   - **Mitigación:** Bien documentado, búsqueda automática

---

## 🏁 Estado Final

**✅ Refactorización exitosa:**
- 7 módulos cohesivos y desacoplados
- 0 breaking changes en API pública
- Docker compose validado
- Backend funcionando correctamente
- Logs muestran uso de nuevos módulos

**📦 Archivos:**
- Backup: `sentinel_service_old.py` (se puede eliminar después)
- Nuevo package: `app/services/sentinel/` (7 módulos)

**🔀 Git:**
- Branch: `feature/refactor-sentinel-service`
- Listo para merge a main después de pruebas manuales

---

## 🚀 Próximo Paso Sugerido

**Prueba manual end-to-end:**
1. Login frontend
2. Seleccionar parcela
3. Consultar fechas disponibles (STAC)
4. Adquirir bandas (Process API)
5. Calcular NDVI batch
6. Verificar logs detallados

Si todo funciona → **Merge a main** y eliminar `sentinel_service_old.py`.
