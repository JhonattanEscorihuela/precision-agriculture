# 📋 PLAN OE1: Completar sentinel_service.py con STAC API y Process API

**Objetivo:** Implementar sistema completo de consulta y adquisición de imágenes Sentinel-2  
**OE:** OE1 - Identificar escenas Sentinel-2 aptas via STAC API  
**Estado:** Sprint activo  
**Fecha:** 2026-05-23

---

## 🎯 META

Usuario puede:
1. Ver lista de fechas disponibles para su parcela (≤20% nubosidad)
2. Seleccionar fecha y adquirir bandas B04 y B08
3. Bandas quedan guardadas en BD para uso en OE2 (NDVI)

---

## 📦 COMPONENTES A IMPLEMENTAR

### 1. Modelo de datos `backend/app/models/acquisition.py`
```python
class SentinelAcquisition(SQLModel, table=True):
    id: int (PK)
    polygon_id: int (FK → polygons)
    acquisition_date: str (fecha de la escena)
    cloud_coverage: float (%)
    b04_data: bytes (banda roja TIFF)
    b08_data: bytes (banda NIR TIFF)
    width: int (píxeles)
    height: int (píxeles)
    created_at: str
```

**Justificación:** Necesitamos persistir las bandas adquiridas para OE2.

---

### 2. CRUD `backend/app/crud/acquisition.py`
- `create_acquisition()` → Insertar registro de adquisición
- `get_acquisition_by_id()` → Obtener por ID
- `get_acquisitions_by_polygon()` → Listar por parcela
- `delete_acquisition()` → Eliminar registro

---

### 3. Servicios en `backend/app/services/sentinel_service.py`

#### 3.1 Método `get_available_dates()` - STAC API
```python
async def get_available_dates(
    polygon_coords: List[List[float]],
    start_date: str,
    end_date: str,
    max_cloud: int = 20
) -> List[Dict[str, Any]]
```

**Responsabilidad:**
- ✅ Consultar STAC API (sin autenticación)
- ✅ Filtrar por cloud_cover ≤ max_cloud
- ✅ Retornar lista ordenada de fechas aptas

**Detalles técnicos:**
- URL: `POST https://stac.dataspace.copernicus.eu/v1/search`
- Payload:
  ```json
  {
    "collections": ["sentinel-2-l2a"],
    "datetime": "2024-01-01T00:00:00Z/2024-12-31T23:59:59Z",
    "intersects": {
      "type": "Polygon",
      "coordinates": [coords]
    },
    "limit": 50,
    "fields": {
      "include": ["properties.datetime", "properties.eo:cloud_cover"],
      "exclude": ["assets", "links"]
    }
  }
  ```
- Respuesta esperada: Lista de features con datetime y cloud_cover
- Filtrar localmente: `item["properties"]["eo:cloud_cover"] <= max_cloud`

#### 3.2 Método `acquire_bands()` - Process API
```python
async def acquire_bands(
    polygon_coords: List[List[float]],
    date: str,
    polygon_id: int,
    db: AsyncSession
) -> int  # retorna acquisition_id
```

**Responsabilidad:**
- ✅ Autenticar con OAuth2 (ya existente)
- ✅ Llamar Process API para B04 y B08 por separado
- ✅ Validar que TIFFs descargados < 10MB cada uno
- ✅ Guardar en BD via CRUD
- ✅ Retornar ID del registro creado

**Detalles técnicos:**
- Reutilizar `download_bands()` existente con `bands=["B04", "B08"]`
- Extraer bandas individuales del TIFF multi-banda (usar rasterio)
- Guardar cada banda como bytes separados en BD
- Calcular cloud_coverage del día (puede requerir consulta adicional a STAC)

---

### 4. Schemas `backend/app/schemas/sentinel.py`

#### Agregar:
```python
class AvailableDatesRequest(BaseModel):
    polygon_id: int
    start_date: str
    end_date: str
    max_cloud_coverage: int = 20

class AvailableDatesResponse(BaseModel):
    polygon_id: int
    dates: List[Dict[str, Any]]  # [{date, cloud_cover}]
    total_count: int

class AcquireBandsRequest(BaseModel):
    polygon_id: int
    date: str  # YYYY-MM-DD

class AcquireBandsResponse(BaseModel):
    acquisition_id: int
    polygon_id: int
    date: str
    cloud_coverage: float
    size_b04_kb: float
    size_b08_kb: float
```

---

### 5. Endpoints `backend/app/api/endpoints/sentinel.py`

#### 5.1 `GET /api/sentinel/available-dates/{polygon_id}`
```python
@router.get("/available-dates/{polygon_id}")
async def get_available_dates(
    polygon_id: int,
    start_date: str = Query(...),
    end_date: str = Query(...),
    max_cloud: int = Query(20),
    db: AsyncSession = Depends(get_session)
) -> AvailableDatesResponse
```

**Flujo:**
1. Validar que polygon existe (CRUD)
2. Obtener coords del polygon
3. Llamar `service.get_available_dates()`
4. Retornar lista de fechas aptas

#### 5.2 `POST /api/sentinel/acquire`
```python
@router.post("/acquire")
async def acquire_bands(
    request: AcquireBandsRequest,
    db: AsyncSession = Depends(get_session)
) -> AcquireBandsResponse
```

**Flujo:**
1. Validar que polygon existe
2. Validar que fecha está en lista de disponibles (opcional)
3. Llamar `service.acquire_bands()`
4. Retornar confirmación con acquisition_id

---

### 6. Tests `backend/tests/test_sentinel_service.py`

#### Test cases:
- ✅ `test_get_available_dates_success()` - Debe retornar ≥1 fecha
- ✅ `test_get_available_dates_filters_clouds()` - No incluir fechas >20% nubes
- ✅ `test_acquire_bands_success()` - Adquirir y guardar en BD
- ✅ `test_acquire_bands_validates_size()` - Rechazar si TIFF >10MB
- ✅ `test_endpoint_available_dates()` - Test de integración endpoint
- ✅ `test_endpoint_acquire()` - Test de integración endpoint

---

## 🔄 ORDEN DE IMPLEMENTACIÓN

### Fase 1: Modelos y CRUD (sin llamadas externas) ✅ COMPLETADA
- [x] 1.1 Crear `models/acquisition.py`
- [x] 1.2 Crear `crud/acquisition.py`
- [x] 1.3 Test unitario de CRUD (test_acquisition_model.py)
- [x] 1.4 Actualizar main.py para importar modelo
- ⚠️  Nota: BD usa SQLModel.metadata.create_all (no Alembic)

### Fase 2: Servicio STAC (consulta fechas) ✅ COMPLETADA
- [x] 2.1 Implementar `get_available_dates()` en `sentinel_service.py`
- [x] 2.2 Test de integración con STAC API real (test_stac_api.py)
- [x] 2.3 Verificado: 7 fechas aptas para junio 2024 en Madrid
- ✅ STAC API funciona sin autenticación

### Fase 3: Servicio Process API (adquisición) ✅ COMPLETADA
- [x] 3.1 Implementar `acquire_bands()` con descarga separada de B04 y B08
- [x] 3.2 Integrar con CRUD para guardar en BD
- [x] 3.3 Test de integración completo (test_oe1_complete.py)
- [x] 3.4 Verificado: bandas de 30KB cada una, <10MB
- ✅ Flujo completo: STAC → Process API → BD funcionando

### Fase 4: Endpoints y schemas ✅ COMPLETADA
- [x] 4.1 Crear schemas OE1 en `schemas/sentinel.py`
- [x] 4.2 Implementar endpoint `GET /available-dates/{polygon_id}`
- [x] 4.3 Implementar endpoint `POST /acquire`
- [x] 4.4 Imports verificados correctamente

### Fase 5: Validación y documentación ✅ COMPLETADA
- [x] 5.1 Probar flujo completo: consultar → seleccionar → adquirir
- [x] 5.2 Verificar tamaño de bandas en BD (<10MB c/u) → 0.67KB c/u
- [x] 5.3 Documentar endpoints en OpenAPI (automático con FastAPI)
- [x] 5.4 Actualizar CLAUDE.md con estado "OE1 completado"
- [x] 5.5 Corregir coordenadas: Madrid → Parcela 211 Venezuela
- [x] 5.6 Ajustar max_cloud: 20% → 30% (zona tropical)
- ✅ 25 fechas encontradas en 2024 para Parcela 211

---

## 📊 EVIDENCIA MEDIBLE (Criterio de Completitud)

Al finalizar el OE1, debo poder demostrar:

1. **Consulta funcional:**
   ```bash
   GET /api/sentinel/available-dates/1?start_date=2024-06-01&end_date=2024-06-30
   # Retorna: [{date: "2024-06-05", cloud_cover: 8.3}, ...]
   ```

2. **Adquisición funcional:**
   ```bash
   POST /api/sentinel/acquire
   {"polygon_id": 1, "date": "2024-06-05"}
   # Retorna: {acquisition_id: 123, ...}
   ```

3. **Datos en BD:**
   ```sql
   SELECT id, polygon_id, acquisition_date, 
          length(b04_data) as b04_size, 
          length(b08_data) as b08_size
   FROM sentinel_acquisitions;
   ```

4. **Tests pasando:**
   ```bash
   pytest tests/test_sentinel_service.py -v
   # 8 tests passed
   ```

---

## ⚠️ RESTRICCIONES Y DECISIONES TÉCNICAS

| Aspecto | Decisión |
|---------|----------|
| Formato imágenes | TIFF (no PNG) - preservar float32 |
| Coordenadas | [lng, lat] en todos lados menos Leaflet |
| Autenticación STAC | No requiere (público) |
| Autenticación Process | OAuth2 (ya implementado) |
| Límite tamaño | 10MB por banda (validar antes de guardar) |
| Nubosidad por defecto | ≤20% (configurable) |
| Almacenamiento | PostgreSQL bytea (NO filesystem) |
| Separación bandas | rasterio para extraer B04 y B08 de TIFF multi-banda |

---

## 🚀 SIGUIENTE PASO DESPUÉS DE OE1

Una vez completado OE1:
- OE2: Migrar cálculo NDVI de notebook a `ndvi_service.py`
- OE2: Endpoint `POST /api/ndvi/calculate` que consume `acquisition_id`

---

## 📝 NOTAS

- La actual función `download_bands()` ya funciona para Process API
- Solo falta integrar STAC API para consulta de fechas
- Modelo Polygon ya existe y tiene coordenadas correctas [lng,lat]
- OAuth2 ya está implementado y funcionando
- Necesitamos instalar rasterio: `pip install rasterio`
