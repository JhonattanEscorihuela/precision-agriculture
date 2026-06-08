# 📋 PLAN OE2: Aplicar cálculo de índice NDVI sobre imágenes Sentinel-2

**Objetivo:** Aplicar el cálculo del índice NDVI sobre las imágenes satelitales Sentinel-2 del área de interés seleccionada por el usuario  
**OE:** OE2 - Aplicar índices espectrales (NDVI)  
**Estado:** Planificación inicial  
**Fecha:** 2026-06-08  
**Rama:** feature/oe2-ndvi-calculation

---

## 🎯 META

Usuario puede:
1. Calcular NDVI sobre una adquisición existente (acquisition_id del OE1)
2. Ver estadísticos del NDVI (mean, min, max, std)
3. Visualizar el rango de valores NDVI con escala de colores
4. Descargar el raster NDVI como archivo TIFF
5. NDVI queda disponible para análisis espacial en OE3

---

## ✅ CORRECCIONES APLICADAS (Revisiones pre-implementación)

### 🔴 Problemas críticos corregidos — Revisión 1

1. **Autenticación JWT agregada:** Todos los endpoints ahora requieren `current_user = Depends(get_current_user)`. El servicio valida ownership antes de operar.

2. **Tipo de datos de fechas:** Cambiado de `str` a `datetime` nativo de SQLModel para consistencia con OE1.

3. **Fixtures de tests:** Agregado `synthetic_acquisition` para tests unitarios rápidos + test de integración separado con datos reales (`@pytest.mark.integration`).

### 🟡 Mejoras implementadas — Revisión 1

4. **Documentación `ndvi_std`:** Agregada descripción explícita que puede ser 0.0 si imagen uniforme.

5. **Storybook eliminado:** Reemplazado por verificación visual en localhost:3000.

6. **Endpoint `/polygon/{polygon_id}` agregado:** Permite al frontend verificar si ya existe NDVI antes de mostrar botón.

7. **Estados del NDVIPanel:** Implementado state machine `idle → loading → calculated → error` con detección automática de NDVI existente al montar.

---

### 🔴 Problemas críticos corregidos — Revisión 2

8. **Conflicto de rutas FastAPI:** Documentado orden de registro crítico. `/polygon/{polygon_id}` DEBE registrarse ANTES de `/{acquisition_id}` para evitar 422 Unprocessable Entity.

9. **Fixture no persiste en BD:** Corregido `synthetic_acquisition` para usar `async`, `db.add()`, `await db.commit()`. Agregados fixtures encadenados: `test_user → test_polygon → synthetic_acquisition`.

### 🟡 Refinamientos implementados — Revisión 2

10. **Manejo de nodata:** Agregado enmascaramiento de píxeles `nodata` (típicamente 0 en Sentinel-2 L2A) en cálculo de estadísticos.

11. **calculation_date en raíz de response:** Agregado a `NDVICalculateResponse` para acceso directo del frontend sin GET adicional.

12. **Idempotencia en POST /calculate:** Servicio verifica si ya existe NDVI y lo retorna sin recalcular. Previene errores de UNIQUE constraint en doble click.

---

## 📊 CONTEXTO DE ENTRADA (del OE1)

**Ya disponible:**
- Modelo `SentinelAcquisition` con bandas B04 y B08 en formato TIFF (bytea)
- Cada registro tiene: id, polygon_id, acquisition_date, b04_data, b08_data
- Bandas normalizadas como L2A (reflectancia superficial)
- Factor de escala L2A: dividir entre 10000.0 antes del cálculo

**Fórmula NDVI:**
```
NDVI = (B08 - B04) / (B08 + B04)
```

**Validación obligatoria:**
- Convertir bandas a float32 ANTES de operar
- Manejar división por cero con np.where
- Verificar que todos los valores queden en [-1, 1]
- Preservar CRS y transform del raster original

---

## 📦 COMPONENTES A IMPLEMENTAR

### 1. Modelo de datos `backend/app/models/analysis.py`

```python
class NDVIResult(SQLModel, table=True):
    __tablename__ = "ndvi_results"
    
    id: int (PK, autoincrement)
    acquisition_id: int (FK → sentinel_acquisitions, UNIQUE)
    polygon_id: int (FK → polygons)
    calculation_date: datetime (default_factory=datetime.utcnow)
    
    # Raster NDVI completo
    ndvi_tiff: bytes  # Raster NDVI como TIFF float32
    
    # Estadísticos (calculados sobre píxeles válidos)
    ndvi_mean: float
    ndvi_min: float
    ndvi_max: float
    ndvi_std: float  # Puede ser 0.0 si imagen uniforme
    
    # Metadatos del raster
    width: int
    height: int
    
    created_at: Optional[datetime] (default_factory=datetime.utcnow)
```

**Justificación:**
- `acquisition_id` UNIQUE: solo un cálculo NDVI por adquisición
- Estadísticos pre-calculados para consultas rápidas en frontend
- Guardar raster completo para análisis espacial en OE3

**Migración:**
- Usar SQLModel.metadata.create_all (consistente con OE1)
- No requiere Alembic para este proyecto

---

### 2. CRUD `backend/app/crud/ndvi.py`

```python
async def save_ndvi_result(
    db: AsyncSession,
    acquisition_id: int,
    polygon_id: int,
    ndvi_tiff: bytes,
    stats: Dict[str, float],
    width: int,
    height: int
) -> NDVIResult

async def get_ndvi_by_acquisition(
    db: AsyncSession,
    acquisition_id: int
) -> Optional[NDVIResult]

async def get_ndvi_by_polygon(
    db: AsyncSession,
    polygon_id: int,
    limit: int = 10
) -> List[NDVIResult]

async def delete_ndvi_result(
    db: AsyncSession,
    ndvi_id: int
) -> bool
```

**Responsabilidades:**
- Solo operaciones de BD, sin lógica de cálculo
- Validar FK constraints
- Retornar objetos SQLModel

---

### 3. Servicio `backend/app/services/ndvi_service.py`

```python
class NDVIService:
    """
    Servicio para calcular índice NDVI sobre bandas Sentinel-2 L2A.
    
    Workflow:
    1. Leer bandas B04 y B08 desde BD (via CRUD)
    2. Convertir bytes TIFF a arrays numpy float32
    3. Aplicar factor de escala L2A (÷ 10000.0)
    4. Calcular NDVI con manejo de división por cero
    5. Validar rango [-1, 1]
    6. Calcular estadísticos
    7. Convertir resultado a TIFF bytes
    8. Guardar en BD (via CRUD)
    """
    
    async def calculate_ndvi(
        self,
        acquisition_id: int,
        user_id: int,
        db: AsyncSession
    ) -> NDVIResult:
        """
        Calcula NDVI para una adquisición existente.
        
        IDEMPOTENTE: Si ya existe NDVI para este acquisition_id, lo retorna
        sin recalcular. Esto previene errores de UNIQUE constraint y mejora UX.
        
        Args:
            acquisition_id: ID de la adquisición Sentinel-2
            user_id: ID del usuario (para verificar ownership)
            db: Sesión async de BD
            
        Returns:
            NDVIResult con raster y estadísticos
            
        Raises:
            ValueError: Si acquisition_id no existe
            HTTPException 403: Si adquisición no pertenece al usuario
            ValueError: Si NDVI fuera de rango [-1, 1]
            ValueError: Si bandas tienen dimensiones diferentes
        """
        # 1. Verificar si ya existe NDVI (idempotencia)
        existing = await crud_ndvi.get_ndvi_by_acquisition(db, acquisition_id)
        if existing:
            return existing
        
        # 2. Obtener adquisición
        # 3. Verificar ownership: polygon.user_id == user_id
        # 4. Calcular NDVI
        pass
    
    async def get_ndvi_stats(
        self,
        acquisition_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticos NDVI si ya fueron calculados.
        """
        pass
    
    async def get_ndvi_tiff(
        self,
        acquisition_id: int,
        db: AsyncSession
    ) -> bytes:
        """
        Obtiene el raster NDVI como TIFF bytes para descarga.
        """
        pass
```

**Detalles técnicos:**

#### 3.1 Lectura de bandas desde BD
```python
# Obtener adquisición via CRUD
acquisition = await acquisition_crud.get_acquisition_by_id(db, acquisition_id)

# Leer TIFF desde bytes con rasterio
import io
import rasterio

# Leer bandas y metadatos
with rasterio.open(io.BytesIO(acquisition.b04_data)) as src:
    b04_array = src.read(1)
    nodata_b04 = src.nodata  # típicamente 0 en Sentinel-2 L2A
    profile = src.profile
    transform = src.transform
    crs = src.crs

with rasterio.open(io.BytesIO(acquisition.b08_data)) as src:
    b08_array = src.read(1)
    nodata_b08 = src.nodata

# Crear máscara de píxeles nodata
nodata_mask = np.zeros_like(b04_array, dtype=bool)
if nodata_b04 is not None:
    nodata_mask |= (b04_array == nodata_b04)
if nodata_b08 is not None:
    nodata_mask |= (b08_array == nodata_b08)
```

#### 3.2 Cálculo NDVI
```python
import numpy as np

# Convertir a float32
b04 = b04_array.astype(np.float32)
b08 = b08_array.astype(np.float32)

# Aplicar factor de escala L2A
b04 = b04 / 10000.0
b08 = b08 / 10000.0

# Calcular NDVI con manejo de división por cero
denominator = b08 + b04
ndvi = np.where(
    denominator == 0,
    0,  # valor por defecto si suma es cero
    (b08 - b04) / denominator
)

# Validar rango
assert ndvi.min() >= -1 and ndvi.max() <= 1, \
    f"NDVI fuera de rango: [{ndvi.min():.4f}, {ndvi.max():.4f}]"
```

#### 3.3 Cálculo de estadísticos
```python
# Calcular sobre píxeles válidos (no NaN, dentro de [-1, 1], no nodata)
valid_mask = ~np.isnan(ndvi) & (ndvi >= -1) & (ndvi <= 1) & ~nodata_mask
valid_pixels = ndvi[valid_mask]

# Validar que hay píxeles válidos
if len(valid_pixels) == 0:
    raise ValueError("No hay píxeles válidos para calcular NDVI")

stats = {
    "ndvi_mean": float(np.mean(valid_pixels)),
    "ndvi_min": float(np.min(valid_pixels)),
    "ndvi_max": float(np.max(valid_pixels)),
    "ndvi_std": float(np.std(valid_pixels))
}
```

#### 3.4 Guardar raster como TIFF
```python
# Actualizar perfil para NDVI (float32, 1 banda)
profile.update(
    dtype=rasterio.float32,
    count=1,
    compress='lzw'  # comprimir para reducir tamaño
)

# Escribir a bytes
ndvi_buffer = io.BytesIO()
with rasterio.open(ndvi_buffer, 'w', **profile) as dst:
    dst.write(ndvi, 1)

ndvi_tiff = ndvi_buffer.getvalue()
```

---

### 4. Schemas `backend/app/schemas/ndvi.py`

```python
from pydantic import BaseModel, Field
from typing import Optional

class NDVICalculateRequest(BaseModel):
    acquisition_id: int = Field(..., description="ID de la adquisición Sentinel-2")

class NDVIStatsResponse(BaseModel):
    acquisition_id: int
    polygon_id: int
    calculation_date: str  # Serializado como ISO string en response
    ndvi_mean: float = Field(..., ge=-1, le=1)
    ndvi_min: float = Field(..., ge=-1, le=1)
    ndvi_max: float = Field(..., ge=-1, le=1)
    ndvi_std: float = Field(..., ge=0, description="Desviación estándar. 0 si imagen uniforme.")
    width: int
    height: int

class NDVICalculateResponse(BaseModel):
    ndvi_id: int
    acquisition_id: int
    polygon_id: int
    calculation_date: str  # En raíz para acceso directo del frontend
    stats: NDVIStatsResponse
    message: str = "NDVI calculado exitosamente"
```

---

### 5. Endpoints `backend/app/api/endpoints/ndvi.py`

```python
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.models.user import User
from app.core.security import get_current_user

router = APIRouter(prefix="/ndvi", tags=["NDVI"])

# ⚠️ ORDEN CRÍTICO: Registrar rutas específicas ANTES de las genéricas
# FastAPI evalúa rutas en orden de registro
# Si /{acquisition_id} se registra antes que /polygon/{polygon_id},
# FastAPI intentará convertir "polygon" a int y fallará con 422

@router.post("/calculate", response_model=NDVICalculateResponse)
async def calculate_ndvi(
    request: NDVICalculateRequest,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Calcula el índice NDVI para una adquisición Sentinel-2.
    
    - Valida que acquisition_id existe
    - Verifica que adquisición pertenece al usuario actual
    - Si ya existe NDVI, retorna el existente (idempotente)
    - Si no existe, calcula NDVI con manejo de división por cero
    - Guarda raster y estadísticos en BD
    - Retorna estadísticos calculados
    """
    # Llamar servicio pasando user_id para verificación de ownership
    pass

# Ruta específica /polygon/{polygon_id} ANTES de la genérica /{acquisition_id}
@router.get("/polygon/{polygon_id}", response_model=List[NDVIStatsResponse])
async def get_ndvi_by_polygon(
    polygon_id: int,
    limit: int = 10,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Lista todos los NDVI calculados para un polígono.
    Útil para el frontend: verificar si ya existe NDVI antes de mostrar botón.
    """
    pass

# Ruta genérica /{acquisition_id} DESPUÉS de las específicas
@router.get("/{acquisition_id}", response_model=NDVIStatsResponse)
async def get_ndvi_stats(
    acquisition_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene estadísticos NDVI si ya fueron calculados.
    Verifica ownership antes de retornar.
    """
    pass

@router.get("/{acquisition_id}/tiff")
async def download_ndvi_tiff(
    acquisition_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Descarga el raster NDVI como archivo TIFF.
    Verifica ownership antes de permitir descarga.
    
    Returns:
        Response: TIFF file con Content-Disposition attachment
    """
    pass
```

---

### 6. Tests `backend/tests/test_oe2_ndvi.py`

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np
import rasterio
import io

# Parcelas de referencia SRRG (Venezuela)
PARCELA_211 = [
    [-67.528058, 8.8441233],
    [-67.5153475, 8.8386166],
    [-67.5103962, 8.8478932],
    [-67.522828, 8.8534209],
    [-67.528058, 8.8441233]
]

PARCELA_217 = [
    [-67.538379, 8.8042214],
    [-67.5369724, 8.8130876],
    [-67.5351396, 8.8123084],
    [-67.5337757, 8.8125401],
    [-67.5239405, 8.8082815],
    [-67.5257482, 8.7980897],
    [-67.538379, 8.8042214]
]

PARCELA_85 = [
    [-67.586587, 8.8508969],
    [-67.5991461, 8.8654285],
    [-67.5869706, 8.8659561],
    [-67.5776965, 8.8549892],
    [-67.586587, 8.8508969]
]

@pytest.mark.asyncio
async def test_calculate_ndvi_success():
    """Debe calcular NDVI correctamente para parcela real."""
    pass

@pytest.mark.asyncio
async def test_ndvi_range_validation():
    """NDVI debe estar en rango [-1, 1]."""
    pass

@pytest.mark.asyncio
async def test_ndvi_statistics():
    """Estadísticos deben ser consistentes con el raster."""
    pass

@pytest.mark.asyncio
async def test_ndvi_tiff_format():
    """Raster NDVI debe ser TIFF float32 válido."""
    pass

@pytest.mark.asyncio
async def test_endpoint_calculate():
    """Test de integración endpoint POST /ndvi/calculate."""
    pass

@pytest.mark.asyncio
async def test_endpoint_get_stats():
    """Test de integración endpoint GET /ndvi/{acquisition_id}."""
    pass

@pytest.mark.asyncio
async def test_endpoint_download_tiff():
    """Test de integración endpoint GET /ndvi/{acquisition_id}/tiff."""
    pass

@pytest.mark.asyncio
async def test_all_parcelas_ndvi():
    """
    Test de evidencia OE2: calcular NDVI para las 3 parcelas de referencia.
    
    Usa fixtures con TIFFs sintéticos para tests unitarios rápidos.
    
    Debe generar tabla de resultados:
    | Parcela | Fecha | NDVI Mean | NDVI Min | NDVI Max | NDVI Std |
    """
    pass

@pytest.mark.integration
@pytest.mark.asyncio
async def test_all_parcelas_ndvi_real():
    """
    Test de integración con datos reales de Copernicus.
    
    Requiere credenciales OAuth2 y conexión a APIs externas.
    Se ejecuta manualmente con: pytest -m integration
    
    Workflow:
    1. Llamar OE1 acquire_bands() para las 3 parcelas
    2. Calcular NDVI para cada una
    3. Generar tabla de evidencia CSV
    """
    pass

# Fixtures encadenados para tests unitarios
@pytest.fixture
async def test_user(db: AsyncSession):
    """Crea usuario de prueba en BD."""
    from app.models.user import User
    import bcrypt
    
    user = User(
        email="test@example.com",
        hashed_password=bcrypt.hashpw("test123".encode(), bcrypt.gensalt()).decode(),
        full_name="Test User"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@pytest.fixture
async def test_polygon(db: AsyncSession, test_user):
    """Crea polígono de prueba asociado al usuario."""
    from app.models.polygon import Polygon
    
    polygon = Polygon(
        name="Test Parcela",
        coordinates=PARCELA_211,  # coordenadas SRRG Venezuela
        user_id=test_user.id
    )
    db.add(polygon)
    await db.commit()
    await db.refresh(polygon)
    return polygon

@pytest.fixture
async def synthetic_acquisition(db: AsyncSession, test_polygon):
    """
    Crea adquisición con bandas sintéticas para tests unitarios.
    
    Genera B04 y B08 con valores realistas:
    - B04: 500-2000 (reflectancia roja)
    - B08: 1000-4000 (reflectancia NIR)
    
    Persiste en BD para que el servicio pueda consultarla.
    """
    import numpy as np
    import rasterio
    import io
    from app.models.acquisition import SentinelAcquisition
    
    b04 = np.random.randint(500, 2000, (100, 100), dtype=np.uint16)
    b08 = np.random.randint(1000, 4000, (100, 100), dtype=np.uint16)
    
    def array_to_tiff(arr) -> bytes:
        buf = io.BytesIO()
        with rasterio.open(buf, 'w', driver='GTiff',
                          height=100, width=100, count=1,
                          dtype=arr.dtype,
                          crs='EPSG:4326',
                          transform=rasterio.transform.from_bounds(
                              -67.6, 8.7, -67.5, 8.9, 100, 100
                          ),
                          nodata=0) as dst:  # nodata=0 para Sentinel-2 L2A
            dst.write(arr, 1)
        return buf.getvalue()
    
    acquisition = SentinelAcquisition(
        polygon_id=test_polygon.id,
        acquisition_date=datetime(2025, 3, 15),
        cloud_coverage=15.0,
        b04_data=array_to_tiff(b04),
        b08_data=array_to_tiff(b08),
        width=100,
        height=100
    )
    db.add(acquisition)
    await db.commit()
    await db.refresh(acquisition)
    return acquisition
```

---

### 7. Frontend — Componente atoms/NDVIBadge.tsx

```typescript
// frontend/app/components/atoms/NDVIBadge.tsx
interface NDVIBadgeProps {
  value: number;  // NDVI value in [-1, 1]
  size?: 'sm' | 'md' | 'lg';
}

/**
 * Badge que muestra valor NDVI con color según rango:
 * [-1, 0)  → #8B4513 (sin vegetación)
 * [0, 0.2) → #D2B48C (vegetación escasa)
 * [0.2, 0.4) → #ADFF2F (vegetación baja)
 * [0.4, 0.6) → #32CD32 (vegetación media)
 * [0.6, 1]  → #006400 (vegetación densa)
 */
```

**Reglas:**
- < 50 líneas (atom)
- Solo Tailwind CSS
- Prop `value` validado en [-1, 1]
- Formato: "NDVI: 0.XXX"

---

### 8. Frontend — Componente molecules/NDVIStats.tsx

```typescript
// frontend/app/components/molecules/NDVIStats.tsx
interface NDVIStatsProps {
  stats: {
    ndvi_mean: number;
    ndvi_min: number;
    ndvi_max: number;
    ndvi_std: number;
  };
  onDownload?: () => void;  // opcional: descargar TIFF
}

/**
 * Tarjeta que muestra estadísticos NDVI en grid 2x2:
 * - Promedio (con badge coloreado)
 * - Mínimo
 * - Máximo
 * - Desviación estándar
 * + Botón de descarga TIFF (opcional)
 */
```

**Reglas:**
- < 100 líneas (molecule)
- Grid responsive (2x2 desktop, 1 col mobile)
- Usa NDVIBadge para el promedio
- Botón descarga con icon (download)

---

### 9. Frontend — Componente molecules/NDVIColorScale.tsx

```typescript
// frontend/app/components/molecules/NDVIColorScale.tsx
/**
 * Escala de colores NDVI horizontal con labels:
 * 
 * [-1.0]  [0.0]  [0.2]  [0.4]  [0.6]  [1.0]
 *   |      |      |      |      |      |
 * ████████████████████████████████████████
 * Sin veg | Escasa | Baja | Media | Densa
 */
```

**Reglas:**
- < 100 líneas (molecule)
- Gradient CSS con los 5 colores
- Labels en extremos y puntos de cambio
- Responsive (scroll horizontal en mobile)

---

### 10. Frontend — Componente organisms/NDVIPanel.tsx

```typescript
// frontend/app/components/organisms/NDVIPanel.tsx
interface NDVIPanelProps {
  acquisitionId: number;
  polygonId: number;
  onClose?: () => void;
}

type PanelState = 
  | 'idle'          // Sin NDVI calculado — mostrar botón
  | 'loading'       // Calculando
  | 'calculated'    // Ya existe — mostrar estadísticos
  | 'error'         // Error en cálculo

/**
 * Panel completo de visualización NDVI.
 * 
 * Flujo:
 * 1. Al montar: GET /ndvi/{acquisition_id}
 *    - Si existe (200) → estado 'calculated', mostrar stats
 *    - Si no existe (404) → estado 'idle', mostrar botón
 * 2. Usuario click "Calcular NDVI" → POST /ndvi/calculate
 *    - Estado 'loading' con spinner
 *    - Al completar → estado 'calculated'
 * 3. Usuario vuelve a abrir panel → mostrar stats sin recalcular
 * 
 * Componentes renderizados según estado:
 * - idle: Botón "Calcular NDVI"
 * - loading: Spinner + "Calculando..."
 * - calculated: NDVIStats + NDVIColorScale + Botón descarga
 * - error: Alert con mensaje de error
 * 
 * Se integra dentro del SentinelPanel existente.
 */
```

**Reglas:**
- < 200 líneas (organism)
- Responsive (panel lateral desktop, modal inferior mobile)
- Loading state durante cálculo
- Error handling con toast/alert
- Integrado al flujo: SentinelPanel → acquire → NDVIPanel

---

## 🔄 ORDEN DE IMPLEMENTACIÓN

### Fase 1: Backend — Modelo y CRUD
- [ ] 1.1 Crear modelo `NDVIResult` en `models/analysis.py`
- [ ] 1.2 Actualizar `main.py` para importar modelo
- [ ] 1.3 Crear `crud/ndvi.py` con operaciones BD
- [ ] 1.4 Test unitario de modelo y CRUD (sin cálculos)

### Fase 2: Backend — Servicio NDVI
- [ ] 2.1 Instalar dependencia: `rasterio` (si no está)
- [ ] 2.2 Implementar `NDVIService.calculate_ndvi()`
- [ ] 2.3 Test: lectura de bandas desde BD
- [ ] 2.4 Test: cálculo NDVI con manejo de división por cero
- [ ] 2.5 Test: validación rango [-1, 1]
- [ ] 2.6 Test: cálculo de estadísticos
- [ ] 2.7 Test: guardar raster como TIFF

### Fase 3: Backend — Schemas y Endpoints
- [ ] 3.1 Crear `schemas/ndvi.py`
- [ ] 3.2 Crear `api/endpoints/ndvi.py`
- [ ] 3.3 Registrar router en `main.py`
- [ ] 3.4 Test endpoint `POST /ndvi/calculate` (con JWT)
- [ ] 3.5 Test endpoint `GET /ndvi/{acquisition_id}` (con JWT)
- [ ] 3.6 Test endpoint `GET /ndvi/polygon/{polygon_id}` (con JWT)
- [ ] 3.7 Test endpoint `GET /ndvi/{acquisition_id}/tiff` (con JWT)
- [ ] 3.8 Test de ownership: verificar 403 si usuario intenta acceder NDVI de otro

### Fase 4: Backend — Evidencia medible
- [ ] 4.1 Test integración con 3 parcelas SRRG (Parcela 211, 217, 85)
- [ ] 4.2 Generar tabla de evidencia:
  ```
  | Parcela | Fecha | NDVI Mean | NDVI Min | NDVI Max | NDVI Std |
  |---------|-------|-----------|----------|----------|----------|
  | 211     | ...   | ...       | ...      | ...      | ...      |
  | 217     | ...   | ...       | ...      | ...      | ...      |
  | 85      | ...   | ...       | ...      | ...      | ...      |
  ```
- [ ] 4.3 Guardar CSV: `tasks/tabla_evidencia_oe2.csv`

### Fase 5: Frontend — Componentes atómicos
- [ ] 5.1 Crear `atoms/NDVIBadge.tsx` (< 50 líneas)
- [ ] 5.2 Verificar visual en localhost:3000 con datos hardcodeados

### Fase 6: Frontend — Componentes moleculares
- [ ] 6.1 Crear `molecules/NDVIStats.tsx` (< 100 líneas)
- [ ] 6.2 Crear `molecules/NDVIColorScale.tsx` (< 100 líneas)
- [ ] 6.3 Test visual de stats + scale

### Fase 7: Frontend — Componente organismo
- [ ] 7.1 Crear `organisms/NDVIPanel.tsx` (< 200 líneas)
- [ ] 7.2 Implementar lógica de estados: idle / loading / calculated / error
- [ ] 7.3 Al montar: GET /ndvi/{acquisition_id} para detectar si ya existe
- [ ] 7.4 Integrar con SentinelPanel existente
- [ ] 7.5 Conectar con endpoints backend (con JWT automático via axios interceptors)
- [ ] 7.6 Implementar descarga TIFF
- [ ] 7.7 Manejo de errores con toast/alert

### Fase 8: Validación completa
- [ ] 8.1 Tests backend pasando: `pytest tests/test_oe2_ndvi.py -v`
- [ ] 8.2 Validación docker-compose: `docker-compose up --build`
- [ ] 8.3 Verificar logs backend y frontend sin errores
- [ ] 8.4 Prueba manual end-to-end:
  - Login → Seleccionar parcela → Ver fechas disponibles
  - Adquirir bandas → Calcular NDVI → Ver estadísticos
  - Descargar TIFF → Verificar archivo válido
- [ ] 8.5 Verificar responsive (375px mobile, 1920px desktop)

### Fase 9: Documentación
- [ ] 9.1 Actualizar CLAUDE.md con estado OE2 completado
- [ ] 9.2 Documentar lecciones en `tasks/lessons.md`
- [ ] 9.3 Crear `tasks/oe2_complete.md` con evidencia
- [ ] 9.4 Merge a main y push: `git checkout main && git merge feature/oe2-ndvi-calculation && git push`

---

## 📊 EVIDENCIA MEDIBLE (Criterio de Completitud)

Al finalizar el OE2, debo poder demostrar:

### 1. Cálculo funcional
```bash
POST /api/ndvi/calculate
{"acquisition_id": 123}

Response:
{
  "ndvi_id": 456,
  "acquisition_id": 123,
  "polygon_id": 1,
  "stats": {
    "ndvi_mean": 0.6523,
    "ndvi_min": -0.1234,
    "ndvi_max": 0.8765,
    "ndvi_std": 0.1432
  }
}
```

### 2. Consulta de estadísticos
```bash
GET /api/ndvi/123

Response:
{
  "acquisition_id": 123,
  "polygon_id": 1,
  "calculation_date": "2026-06-08T10:30:00Z",
  "ndvi_mean": 0.6523,
  "ndvi_min": -0.1234,
  "ndvi_max": 0.8765,
  "ndvi_std": 0.1432,
  "width": 512,
  "height": 512
}
```

### 3. Descarga de raster
```bash
GET /api/ndvi/123/tiff

Response: application/octet-stream (archivo TIFF float32)
```

### 4. Datos en BD
```sql
SELECT id, acquisition_id, polygon_id, 
       ndvi_mean, ndvi_min, ndvi_max, ndvi_std,
       length(ndvi_tiff) as tiff_size
FROM ndvi_results;
```

### 5. Tabla de evidencia con parcelas reales SRRG
```csv
parcela_id,parcela_nombre,fecha_adquisicion,ndvi_mean,ndvi_min,ndvi_max,ndvi_std
1,Parcela 211,2025-03-15,0.6523,-0.1234,0.8765,0.1432
2,Parcela 217,2024-06-20,0.5891,-0.0987,0.8234,0.1567
3,Parcela 85,2026-01-10,0.7012,-0.1456,0.9123,0.1234
```

### 6. Tests pasando
```bash
pytest tests/test_oe2_ndvi.py -v
# 8 tests passed
```

### 7. Frontend funcional
- [ ] Panel NDVI visible después de adquisición
- [ ] Botón "Calcular NDVI" funciona
- [ ] Estadísticos se muestran correctamente
- [ ] Badge NDVI coloreado según rango
- [ ] Escala de colores visible
- [ ] Descarga TIFF funciona
- [ ] Responsive en mobile (375px) y desktop (1920px)

---

## ⚠️ RESTRICCIONES Y DECISIONES TÉCNICAS

| Aspecto | Decisión |
|---------|----------|
| Formato raster NDVI | TIFF float32 (no PNG, no uint8) |
| Factor de escala L2A | Dividir entre 10000.0 antes del cálculo |
| Manejo división por cero | np.where con valor por defecto 0 |
| Validación rango | Assert -1 ≤ ndvi ≤ 1 en servicio |
| Estadísticos | Solo sobre píxeles válidos (no NaN) |
| CRS y transform | Preservar del raster original (B04/B08) |
| Almacenamiento | PostgreSQL bytea (NO filesystem) |
| Compresión TIFF | LZW para reducir tamaño |
| Unicidad | 1 NDVI por acquisition_id (UNIQUE constraint) |
| Escala de colores | 5 rangos de [-1, 1] según vegetación |

---

## 🎨 ESCALA DE COLORES NDVI

| Rango NDVI | Color | Hex | Interpretación |
|------------|-------|-----|----------------|
| [-1.0, 0.0) | Marrón | #8B4513 | Sin vegetación (agua, suelo desnudo) |
| [0.0, 0.2) | Beige | #D2B48C | Vegetación escasa (estrés, suelo) |
| [0.2, 0.4) | Verde-amarillo | #ADFF2F | Vegetación baja (pastos secos) |
| [0.4, 0.6) | Verde lima | #32CD32 | Vegetación media (cultivos sanos) |
| [0.6, 1.0] | Verde oscuro | #006400 | Vegetación densa (óptima fotosíntesis) |

---

## 🚀 SIGUIENTE PASO DESPUÉS DE OE2

Una vez completado OE2:
- **OE3:** Analizar y segmentar zonas cultivadas usando NDVI
- Endpoints: `POST /api/segmentation/analyze` que consume `ndvi_id`
- Migrar filtros convolucionales de notebook a servicio
- Clasificar píxeles por umbral NDVI (cultivo vs no-cultivo)
- Calcular área cultivada por parcela

---

## 📝 NOTAS IMPORTANTES

- ✅ Factor de escala L2A (÷ 10000.0) es CRÍTICO — sin él, NDVI estará fuera de rango
- ✅ Usar np.where para división por cero — nunca asumir que B08+B04 > 0
- ✅ Validar [-1, 1] con assert — mejor fallar temprano que guardar datos incorrectos
- ✅ Preservar CRS y transform — OE3 necesitará georreferenciar los resultados
- ✅ Calcular estadísticos solo sobre píxeles válidos — excluir NaN y outliers
- ✅ Guardar raster completo — OE3 lo necesita para análisis espacial
- ✅ TIFF float32 obligatorio — no convertir a uint8 para "ahorrar espacio"
- ✅ Validación docker-compose obligatoria — tests pasando NO garantiza que funcione end-to-end

---

## ✅ CRITERIO DE COMPLETITUD (OBLIGATORIO)

**Un OE NO está completo hasta que:**
- ✅ Tests unitarios pasan (`pytest`)
- ✅ Tests de integración pasan (APIs reales)
- ✅ `docker-compose up --build` levanta sin errores
- ✅ Flujo manual probado end-to-end (frontend + backend + db)
- ✅ Evidencia documentada en `tasks/oe2_complete.md`
- ✅ Tabla CSV con datos reales de 3 parcelas SRRG
- ✅ CLAUDE.md actualizado con estado completado
- ✅ Lecciones documentadas en `tasks/lessons.md`
- ✅ Responsive validado (375px y 1920px)
- ✅ Merge a main y push realizado

---

## 🚨 ANTES DE IMPLEMENTAR — ESPERAR CONFIRMACIÓN

**Este es el plan detallado para OE2.**

Por favor confirma:
1. ¿El alcance del OE2 está claro?
2. ¿La arquitectura propuesta es correcta?
3. ¿El orden de implementación tiene sentido?
4. ¿Hay algo que deba agregarse o modificarse antes de empezar?

Una vez confirmado, procederé con la Fase 1 (Backend — Modelo y CRUD).
