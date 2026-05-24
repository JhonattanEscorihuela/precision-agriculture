# 📋 PLAN OE2: Aplicar cálculo de índices espectrales (NDVI)

**Objetivo:** Calcular NDVI a partir de bandas B04 y B08 almacenadas en BD  
**OE:** OE2 - Aplicar índices espectrales (Nivel Bloom N3)  
**Estado:** Planificación  
**Fecha:** 2026-05-23

---

## 🎯 META

Usuario puede:
1. Seleccionar una adquisición existente (resultado de OE1)
2. Calcular NDVI automáticamente desde bandas B04/B08
3. Visualizar resultado NDVI como imagen y estadísticas
4. NDVI queda guardado en BD para OE3 (segmentación)

---

## 📐 FUNDAMENTO TÉCNICO

### Fórmula NDVI
```
NDVI = (NIR - Red) / (NIR + Red)
NDVI = (B08 - B04) / (B08 + B04)
```

**Rango:** [-1, 1]
- NDVI < 0.2: Suelo desnudo, agua, urbano
- NDVI 0.2-0.5: Vegetación escasa o estresada
- NDVI > 0.5: Vegetación saludable

### Procesamiento
1. Leer B04 y B08 como arrays numpy desde TIFF (bytes → rasterio)
2. Aplicar fórmula pixel por pixel
3. Manejar división por cero: `np.where(B08 + B04 == 0, 0, ndvi)`
4. Guardar resultado como TIFF float32
5. Calcular estadísticas: mean, std, min, max, percentiles

---

## 📦 COMPONENTES A IMPLEMENTAR

### 1. Modelo de datos `backend/app/models/ndvi_analysis.py`
```python
class NDVIAnalysis(SQLModel, table=True):
    __tablename__ = "ndvi_analyses"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    acquisition_id: int = Field(foreign_key="sentinel_acquisitions.id")
    ndvi_data: bytes = Field(description="NDVI TIFF float32")
    
    # Estadísticas
    mean_ndvi: float
    std_ndvi: float
    min_ndvi: float
    max_ndvi: float
    p25_ndvi: float  # Percentil 25
    p50_ndvi: float  # Mediana
    p75_ndvi: float  # Percentil 75
    
    # Clasificación por área
    area_critical_pct: float  # % área con NDVI < 0.3 (crítico)
    area_alert_pct: float     # % área con NDVI 0.3-0.5 (alerta)
    area_healthy_pct: float   # % área con NDVI > 0.5 (saludable)
    
    # Metadatos
    width: int
    height: int
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
```

**Justificación:** Persistir tanto la imagen NDVI como estadísticas agregadas para análisis rápido.

---

### 2. CRUD `backend/app/crud/ndvi.py`
- `create_ndvi_analysis()` → Insertar resultado NDVI
- `get_ndvi_by_id()` → Obtener por ID
- `get_ndvi_by_acquisition()` → Obtener NDVI de una adquisición específica
- `get_ndvi_history_by_polygon()` → Listar todos los NDVI de una parcela (para OE5)
- `delete_ndvi()` → Eliminar análisis

---

### 3. Servicio `backend/app/services/ndvi_service.py`

#### 3.1 Método `calculate_ndvi()`
```python
async def calculate_ndvi(
    acquisition_id: int,
    db_session: AsyncSession
) -> Dict[str, Any]
```

**Responsabilidad:**
1. Obtener registro `SentinelAcquisition` desde BD
2. Convertir `b04_data` (bytes) → numpy array con rasterio
3. Convertir `b08_data` (bytes) → numpy array con rasterio
4. Calcular NDVI: `(B08 - B04) / (B08 + B04 + 1e-10)` (evitar división por cero)
5. Calcular estadísticas con numpy
6. Clasificar píxeles por salud (critical/alert/healthy)
7. Convertir NDVI array → TIFF bytes
8. Guardar en BD via CRUD
9. Retornar ID del análisis y estadísticas

**Detalles técnicos:**
- Usar `rasterio.MemoryFile()` para leer/escribir TIFF desde bytes
- Preservar geotransform y CRS del TIFF original
- NDVI como float32 (no normalizar a uint8)
- Manejar NoData con máscaras

#### 3.2 Método `get_ndvi_image()`
```python
async def get_ndvi_image(
    ndvi_id: int,
    db_session: AsyncSession,
    format: str = "png"  # o "tiff"
) -> bytes
```

**Responsabilidad:**
- Obtener `ndvi_data` desde BD
- Si format="png": convertir a PNG con colormap (viridis o RdYlGn)
- Si format="tiff": retornar TIFF original
- Útil para visualización frontend

---

### 4. Schemas `backend/app/schemas/ndvi.py`

```python
class CalculateNDVIRequest(BaseModel):
    acquisition_id: int

class NDVIStatistics(BaseModel):
    mean: float
    std: float
    min: float
    max: float
    p25: float
    p50: float
    p75: float
    area_critical_pct: float
    area_alert_pct: float
    area_healthy_pct: float

class CalculateNDVIResponse(BaseModel):
    ndvi_id: int
    acquisition_id: int
    statistics: NDVIStatistics
    created_at: str

class GetNDVIImageRequest(BaseModel):
    ndvi_id: int
    format: str = "png"  # o "tiff"
```

---

### 5. Endpoints `backend/app/api/endpoints/ndvi.py`

#### 5.1 `POST /api/ndvi/calculate`
```python
@router.post("/calculate")
async def calculate_ndvi(
    request: CalculateNDVIRequest,
    db: AsyncSession = Depends(get_session)
) -> CalculateNDVIResponse
```

**Flujo:**
1. Validar que `acquisition_id` existe en BD
2. Verificar que no exista ya un NDVI para esa adquisición (opcional)
3. Llamar `ndvi_service.calculate_ndvi()`
4. Retornar estadísticas y `ndvi_id`

#### 5.2 `GET /api/ndvi/image/{ndvi_id}`
```python
@router.get("/image/{ndvi_id}")
async def get_ndvi_image(
    ndvi_id: int,
    format: str = Query("png", regex="^(png|tiff)$"),
    db: AsyncSession = Depends(get_session)
) -> Response
```

**Flujo:**
1. Validar que `ndvi_id` existe
2. Llamar `ndvi_service.get_ndvi_image()`
3. Retornar imagen con Content-Type apropiado

#### 5.3 `GET /api/ndvi/history/{polygon_id}`
```python
@router.get("/history/{polygon_id}")
async def get_ndvi_history(
    polygon_id: int,
    db: AsyncSession = Depends(get_session)
) -> List[CalculateNDVIResponse]
```

**Flujo:**
1. Obtener todos los NDVI asociados a una parcela
2. Útil para gráficos temporales (OE5)

---

### 6. Tests `backend/tests/test_ndvi_service.py`

#### Test cases:
- `test_calculate_ndvi_success()` - Calcular NDVI de adquisición OE1
- `test_ndvi_range_valid()` - Verificar NDVI ∈ [-1, 1]
- `test_ndvi_statistics()` - Validar mean, std, percentiles
- `test_ndvi_classification()` - Verificar % áreas suman 100%
- `test_get_ndvi_image_png()` - Exportar como PNG
- `test_get_ndvi_image_tiff()` - Exportar como TIFF
- `test_endpoint_calculate()` - Test integración endpoint
- `test_endpoint_get_image()` - Test integración endpoint

---

## 🔄 ORDEN DE IMPLEMENTACIÓN

### Fase 1: Modelos y CRUD
- [ ] 1.1 Crear `models/ndvi_analysis.py`
- [ ] 1.2 Crear `crud/ndvi.py`
- [ ] 1.3 Test unitario de CRUD
- [ ] 1.4 Actualizar main.py para importar modelo

### Fase 2: Servicio NDVI (cálculo)
- [ ] 2.1 Implementar `calculate_ndvi()` en `ndvi_service.py`
- [ ] 2.2 Test con datos reales de OE1 (usar acquisition_id del test_oe1_complete)
- [ ] 2.3 Validar rango NDVI [-1, 1]
- [ ] 2.4 Validar estadísticas (mean, std, percentiles)

### Fase 3: Servicio NDVI (visualización)
- [ ] 3.1 Implementar `get_ndvi_image()` con formato PNG
- [ ] 3.2 Implementar `get_ndvi_image()` con formato TIFF
- [ ] 3.3 Test de exportación

### Fase 4: Endpoints y schemas
- [ ] 4.1 Crear schemas en `schemas/ndvi.py`
- [ ] 4.2 Crear `endpoints/ndvi.py`
- [ ] 4.3 Implementar POST /calculate
- [ ] 4.4 Implementar GET /image/{ndvi_id}
- [ ] 4.5 Implementar GET /history/{polygon_id}

### Fase 5: Validación y documentación
- [ ] 5.1 Test de integración completo: OE1 → OE2
- [ ] 5.2 Verificar clasificación por salud (critical/alert/healthy)
- [ ] 5.3 Actualizar CLAUDE.md con estado "OE2 completado"
- [ ] 5.4 Documentar en tasks/lessons.md

---

## 📊 EVIDENCIA MEDIBLE (Criterio de Completitud)

Al finalizar el OE2, debo poder demostrar:

1. **Cálculo funcional:**
   ```bash
   POST /api/ndvi/calculate
   {"acquisition_id": 1}
   # Retorna: {
   #   "ndvi_id": 1,
   #   "statistics": {
   #     "mean": 0.65,
   #     "std": 0.12,
   #     "area_healthy_pct": 78.5,
   #     ...
   #   }
   # }
   ```

2. **Visualización funcional:**
   ```bash
   GET /api/ndvi/image/1?format=png
   # Retorna: imagen PNG con colormap
   ```

3. **Datos en BD:**
   ```sql
   SELECT id, acquisition_id, mean_ndvi, 
          area_healthy_pct, length(ndvi_data) as ndvi_size
   FROM ndvi_analyses;
   ```

4. **NDVI en rango válido:**
   ```python
   assert -1 <= ndvi_analysis.mean_ndvi <= 1
   assert -1 <= ndvi_analysis.min_ndvi <= 1
   assert -1 <= ndvi_analysis.max_ndvi <= 1
   ```

5. **Tests pasando:**
   ```bash
   pytest tests/test_ndvi_service.py -v
   # 8 tests passed
   ```

---

## ⚠️ RESTRICCIONES Y DECISIONES TÉCNICAS

| Aspecto | Decisión |
|---------|----------|
| Formato NDVI | TIFF float32 (preservar precisión) |
| Rango NDVI | [-1, 1] sin normalización |
| División por cero | Usar epsilon: `B08 + B04 + 1e-10` |
| Estadísticas | numpy: mean, std, percentile |
| Clasificación salud | Critical <0.3, Alert 0.3-0.5, Healthy >0.5 |
| Visualización | PNG con colormap RdYlGn (Red-Yellow-Green) |
| Almacenamiento | PostgreSQL bytea < 10MB |
| Dependencias | rasterio, numpy, matplotlib (para PNG) |

---

## 🚀 SIGUIENTE PASO DESPUÉS DE OE2

Una vez completado OE2:
- OE3: Analizar zonas cultivadas por segmentación espacial
- OE3: Usar NDVI como input para filtros convolucionales

---

## 🔍 REFERENCIAS

- NDVI original: Rouse et al. 1974
- Sentinel-2 L2A: Surface reflectance (ya corregida atmosféricamente)
- Umbrales salud: adaptados de FAO Guidelines for Crop Monitoring
- Colormap: matplotlib RdYlGn_r (reversed para que verde = alto NDVI)

---

## 📝 NOTAS

- Las bandas B04 y B08 ya están en BD (resultado OE1)
- Usar el mismo `acquisition_id` del test OE1 para validación
- NDVI será input para segmentación (OE3) y textura (OE4)
- Frontend mostrará imagen NDVI + estadísticas en dashboard
