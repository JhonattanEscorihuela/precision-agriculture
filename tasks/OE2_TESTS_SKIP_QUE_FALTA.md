# OE2 — Qué falta para que pasen los tests en SKIP

**Fecha:** 2026-06-15  
**Tests en SKIP:** 2 de 18 (11%)

---

## Test 1: test_ndvi_cross_validation ⏭️ SKIP

**Estado actual:** SKIP - "Adquisiciones no disponibles en test DB"

### ¿Por qué hace SKIP?

El test busca adquisiciones Sentinel-2 en la BD de tests (SQLite en memoria) para 3 fechas específicas:
- 2026-03-22 (NDVI Copernicus: 0.8535)
- 2025-11-27 (NDVI Copernicus: 0.3087)
- 2025-07-02 (NDVI Copernicus: 0.5594)

Como la BD de tests está vacía (se crea nueva en cada test), **no encuentra las adquisiciones** y hace skip.

### ¿Qué falta para que pase?

#### Opción A: Usar BD real en lugar de SQLite en memoria (RECOMENDADO)

```python
# En test_ndvi_cross_validation.py, cambiar fixture:

@pytest.fixture
async def test_db_real():
    """Usar BD PostgreSQL real en lugar de SQLite memoria"""
    from app.database import async_engine
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    async_session = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session

# Luego cambiar la firma del test:
async def test_ndvi_cross_validation(
    test_db_real: AsyncSession,  # <- usar BD real
    # ... resto igual
):
```

**Ventajas:**
- ✅ Usa datos reales ya existentes en BD (33 fechas Parcela 211)
- ✅ Validación real contra Copernicus
- ✅ No requiere crear fixtures sintéticos

**Desventajas:**
- ⚠️ Requiere docker-compose corriendo
- ⚠️ Test depende de datos externos

#### Opción B: Crear fixtures con adquisiciones sintéticas

```python
# Agregar fixture para cada fecha de validación:

@pytest.fixture
async def acquisition_2026_03_22(test_db: AsyncSession, parcela_211):
    """Crea adquisición sintética para 2026-03-22"""
    acquisition = SentinelAcquisition(
        polygon_id=parcela_211.id,
        acquisition_date="2026-03-22",
        cloud_coverage=0.0,
        b04_data=generate_synthetic_tiff_band(512, 512, "B04"),
        b08_data=generate_synthetic_tiff_band(512, 512, "B08"),
        width=512,
        height=512,
        created_at=datetime.utcnow().isoformat()
    )
    test_db.add(acquisition)
    await test_db.commit()
    await test_db.refresh(acquisition)
    return acquisition

# Repetir para 2025-11-27 y 2025-07-02
```

**Ventajas:**
- ✅ Test independiente (no requiere docker)
- ✅ Rápido (SQLite en memoria)

**Desventajas:**
- ⚠️ NDVI sintético puede no coincidir con Copernicus
- ⚠️ No valida datos reales

### Mi recomendación: **Opción A - Usar BD real**

El test está diseñado para **validación cruzada real**, no para datos sintéticos. Ya tienes 33 fechas reales en BD, úsalas.

**Pasos para hacer que pase:**

1. Agregar fixture para BD real en `conftest.py`:
```python
@pytest.fixture
async def postgres_db():
    """Conexión a BD PostgreSQL real para tests de integración"""
    from app.database import async_engine
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    async_session = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
```

2. Modificar el test para usar `postgres_db` en lugar de `test_db`

3. Ejecutar con docker-compose corriendo:
```bash
docker-compose up -d
pytest backend/tests/test_ndvi_cross_validation.py::test_ndvi_cross_validation -v
```

**Resultado esperado:** ✅ PASS - 21 fechas validadas, ~67% dentro de ±10%

---

## Test 2: test_ndvi_percentiles_calculation ⏭️ SKIP

**Estado actual:** SKIP - "Percentiles no implementados aún"

### ¿Por qué hace SKIP?

El servicio NDVI actualmente calcula solo:
- `ndvi_mean`
- `ndvi_min`
- `ndvi_max`
- `ndvi_std`

**NO calcula:**
- `ndvi_median` (percentil 50)
- `ndvi_p10` (percentil 10)
- `ndvi_p90` (percentil 90)

El modelo `NDVIResult` tiene los campos definidos pero con `Optional` y `default=None`:

```python
# backend/app/models/analysis.py
class NDVIResultBase(SQLModel):
    ndvi_median: Optional[float] = Field(default=None, ...)
    ndvi_p10: Optional[float] = Field(default=None, ...)
    ndvi_p90: Optional[float] = Field(default=None, ...)
```

El test verifica si `stats.get("ndvi_median")` es `None` y si lo es, hace skip.

### ¿Qué falta para que pase?

Agregar cálculo de percentiles en `backend/app/services/ndvi_service.py`:

#### Paso 1: Modificar función calculate_ndvi()

```python
# En ndvi_service.py, dentro de calculate_ndvi(), después de calcular mean/min/max/std:

# Calcular percentiles (median, p10, p90)
ndvi_median = float(np.median(ndvi_valid))
ndvi_p10 = float(np.percentile(ndvi_valid, 10))
ndvi_p90 = float(np.percentile(ndvi_valid, 90))

# Actualizar el diccionario stats:
stats = {
    "ndvi_mean": ndvi_mean,
    "ndvi_min": ndvi_min,
    "ndvi_max": ndvi_max,
    "ndvi_std": ndvi_std,
    "ndvi_median": ndvi_median,  # <- agregar
    "ndvi_p10": ndvi_p10,        # <- agregar
    "ndvi_p90": ndvi_p90,        # <- agregar
}

# Actualizar llamada a save_ndvi_result():
ndvi_result = await crud_ndvi.save_ndvi_result(
    db=db,
    acquisition_id=acquisition_id,
    polygon_id=polygon_id,
    ndvi_tiff=tiff_bytes,
    stats=stats,  # <- ahora incluye percentiles
    width=width,
    height=height
)
```

#### Paso 2: Modificar CRUD para guardar percentiles

```python
# En backend/app/crud/ndvi.py, función save_ndvi_result():

async def save_ndvi_result(
    db: AsyncSession,
    acquisition_id: int,
    polygon_id: int,
    ndvi_tiff: bytes,
    stats: dict,
    width: int,
    height: int
) -> NDVIResult:
    ndvi_result = NDVIResult(
        acquisition_id=acquisition_id,
        polygon_id=polygon_id,
        ndvi_tiff=ndvi_tiff,
        ndvi_mean=stats["ndvi_mean"],
        ndvi_min=stats["ndvi_min"],
        ndvi_max=stats["ndvi_max"],
        ndvi_std=stats["ndvi_std"],
        ndvi_median=stats.get("ndvi_median"),  # <- agregar
        ndvi_p10=stats.get("ndvi_p10"),        # <- agregar
        ndvi_p90=stats.get("ndvi_p90"),        # <- agregar
        width=width,
        height=height,
        calculation_date=datetime.utcnow()
    )
    # ... resto igual
```

#### Paso 3: Actualizar schemas de respuesta

```python
# En backend/app/schemas/ndvi.py:

class NDVIStatsResponse(BaseModel):
    ndvi_mean: float
    ndvi_min: float
    ndvi_max: float
    ndvi_std: float
    ndvi_median: Optional[float] = None  # <- agregar
    ndvi_p10: Optional[float] = None     # <- agregar
    ndvi_p90: Optional[float] = None     # <- agregar
    # ... resto igual
```

#### Paso 4: Ejecutar test

```bash
pytest backend/tests/test_ndvi_cross_validation.py::test_ndvi_percentiles_calculation -v
```

**Resultado esperado:** ✅ PASS

### ¿Por qué los percentiles son útiles?

1. **ndvi_median (P50)** — Más robusto que mean contra valores atípicos
2. **ndvi_p10** — Límite inferior distribución (10% píxeles tienen NDVI menor)
3. **ndvi_p90** — Límite superior distribución (10% píxeles tienen NDVI mayor)

**Ejemplo de uso:**
```python
# Clasificación de salud más precisa con percentiles:
if ndvi_median > 0.6 and ndvi_p10 > 0.4:
    return "Healthy consistente"  # Alta vegetación uniforme
elif ndvi_median > 0.6 but ndvi_p10 < 0.3:
    return "Healthy con zonas críticas"  # Alta vegetación pero áreas problemáticas
```

---

## Resumen: Qué hacer para que pasen los SKIP

| Test | Acción | Esfuerzo | Impacto |
|------|--------|----------|---------|
| **test_ndvi_cross_validation** | Usar BD real en lugar de SQLite memoria | 🟡 Medio (15 min) | 🟢 Alto - Validación real |
| **test_ndvi_percentiles_calculation** | Agregar cálculo percentiles en servicio | 🟢 Bajo (10 min) | 🟡 Medio - Estadísticos extras |

### Prioridad de implementación

**1. test_ndvi_percentiles_calculation** (recomendado primero)
- ✅ Más fácil de implementar (solo agregar np.median/percentile)
- ✅ No requiere BD real
- ✅ Mejora calidad estadísticos NDVI
- ✅ Útil para clasificación de salud más precisa

**2. test_ndvi_cross_validation** (opcional)
- ℹ️ Ya validaste manualmente con 21 fechas (tabla en OE2_DATOS_EXACTOS_SOLICITADOS.md)
- ℹ️ Resultado: 67% fechas dentro de ±10% (aceptable)
- ℹ️ Automatizar este test es útil pero no crítico (ya tienes la evidencia)

---

## Código completo para implementar percentiles

**Archivo:** `backend/app/services/ndvi_service.py`

Buscar la sección donde se calculan estadísticos y reemplazar:

```python
# ANTES:
ndvi_mean = float(np.mean(ndvi_valid))
ndvi_min = float(np.min(ndvi_valid))
ndvi_max = float(np.max(ndvi_valid))
ndvi_std = float(np.std(ndvi_valid))

stats = {
    "ndvi_mean": ndvi_mean,
    "ndvi_min": ndvi_min,
    "ndvi_max": ndvi_max,
    "ndvi_std": ndvi_std,
}

# DESPUÉS:
ndvi_mean = float(np.mean(ndvi_valid))
ndvi_min = float(np.min(ndvi_valid))
ndvi_max = float(np.max(ndvi_valid))
ndvi_std = float(np.std(ndvi_valid))
ndvi_median = float(np.median(ndvi_valid))
ndvi_p10 = float(np.percentile(ndvi_valid, 10))
ndvi_p90 = float(np.percentile(ndvi_valid, 90))

stats = {
    "ndvi_mean": ndvi_mean,
    "ndvi_min": ndvi_min,
    "ndvi_max": ndvi_max,
    "ndvi_std": ndvi_std,
    "ndvi_median": ndvi_median,
    "ndvi_p10": ndvi_p10,
    "ndvi_p90": ndvi_p90,
}
```

**Eso es todo.** Con eso el test pasará ✅

---

**¿Quieres que implemente los percentiles ahora?** Es solo agregar 3 líneas de código.
