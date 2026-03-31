# Servicio Sentinel-2 - Documentación

## 📋 Descripción

Servicio productivo para adquisición de imágenes Sentinel-2 desde Copernicus DataSpace.
Migrado desde el notebook `02_pipeline_sentinel_real.ipynb` a una API REST lista para producción.

## 🔧 Configuración

### 1. Variables de entorno

Crea un archivo `.env` en el directorio `backend/` basado en `.env.example`:

```bash
SENTINEL_CLIENT_ID=your_client_id_here
SENTINEL_CLIENT_SECRET=your_client_secret_here
```

**Obtener credenciales:**
1. Regístrate en [Copernicus DataSpace](https://dataspace.copernicus.eu/)
2. Crea una aplicación OAuth2 en tu perfil
3. Copia el Client ID y Client Secret

### 2. Instalar dependencias

```bash
cd backend
pip install -r requirements.txt
```

Nuevas dependencias agregadas:
- `httpx` - Cliente HTTP asíncrono
- `oauthlib` - Manejo OAuth2
- `requests-oauthlib` - OAuth2 para requests

## 🚀 Endpoints disponibles

Base URL: `http://localhost:8000/sentinel`

### 🧪 Endpoint de Prueba (¡Empieza aquí!)

```bash
POST /sentinel/test
```

**Endpoint de prueba que NO requiere base de datos ni polygon_id.**

Usa coordenadas hardcodeadas de una parcela en Madrid, España para verificar que todo funciona.

**Request:**
```json
{
  "start_date": "2024-06-15",
  "end_date": "2024-06-20",
  "download_type": "ndvi",
  "width": 256,
  "height": 256,
  "max_cloud_coverage": 30
}
```

**Tipos de descarga disponibles:**
- `"ndvi"` - Descarga NDVI como GeoTIFF
- `"true-color"` - Descarga imagen RGB como PNG
- `"bands"` - Descarga bandas B04+B08 como GeoTIFF

**Response:** Archivo descargado (TIFF o PNG)

**Coordenadas de prueba usadas:**
```json
[[-3.7038, 40.4168], [-3.7038, 40.4268], [-3.6938, 40.4268], [-3.6938, 40.4168], [-3.7038, 40.4168]]
```

**Pruebas rápidas:**

```bash
# Opción 1: Swagger UI (Recomendado)
# Abre http://localhost:8000/docs en tu navegador
# Ve a POST /sentinel/test → "Try it out" → Execute

# Opción 2: curl desde terminal
curl -X POST http://localhost:8000/sentinel/test \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-06-15",
    "end_date": "2024-06-20",
    "download_type": "ndvi"
  }' --output test_ndvi.tif

# Probar descarga de imagen RGB
curl -X POST http://localhost:8000/sentinel/test \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2024-06-15", "end_date": "2024-06-20", "download_type": "true-color"}' \
  --output test_true_color.png

# Probar descarga de bandas
curl -X POST http://localhost:8000/sentinel/test \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2024-06-15", "end_date": "2024-06-20", "download_type": "bands"}' \
  --output test_bands.tif
```

---

### 1. Verificar disponibilidad

```bash
POST /sentinel/check-availability
```

Verifica si hay imágenes Sentinel-2 disponibles para un polígono y rango de fechas.

**Request:**
```json
{
  "polygon_id": 1,
  "start_date": "2024-01-15",
  "end_date": "2024-01-20",
  "max_cloud_coverage": 20
}
```

**Response:**
```json
{
  "available": true,
  "date_range": {
    "from": "2024-01-15",
    "to": "2024-01-20"
  },
  "message": "Imagery available for the specified date range",
  "polygon_id": 1
}
```

### 2. Descargar NDVI

```bash
POST /sentinel/download/ndvi
```

Descarga imagen NDVI calculada como GeoTIFF.

**Request:**
```json
{
  "polygon_id": 1,
  "start_date": "2024-01-15",
  "end_date": "2024-01-20",
  "width": 512,
  "height": 512,
  "max_cloud_coverage": 20
}
```

**Response:** Archivo GeoTIFF (`image/tiff`)

El NDVI se calcula como: `(B08 - B04) / (B08 + B04)`

Valores típicos:
- **< 0**: Agua
- **0 - 0.2**: Suelo desnudo
- **0.2 - 0.5**: Vegetación escasa
- **0.5 - 1.0**: Vegetación densa

### 3. Descargar bandas específicas

```bash
POST /sentinel/download/bands
```

Descarga bandas espectrales específicas como GeoTIFF multi-banda.

**Request:**
```json
{
  "polygon_id": 1,
  "bands": ["B04", "B08"],
  "start_date": "2024-01-15",
  "end_date": "2024-01-20",
  "width": 512,
  "height": 512,
  "max_cloud_coverage": 20
}
```

**Response:** Archivo GeoTIFF multi-banda

**Bandas disponibles:**
- `B02`: Blue (490nm)
- `B03`: Green (560nm)
- `B04`: Red (665nm)
- `B05-B07`: Red Edge
- `B08`: NIR (842nm)
- `B8A`: Narrow NIR (865nm)
- `B11-B12`: SWIR

### 4. Descargar imagen true-color

```bash
POST /sentinel/download/true-color
```

Descarga imagen RGB (B04, B03, B02) como PNG para visualización.

**Request:**
```json
{
  "polygon_id": 1,
  "start_date": "2024-01-15",
  "end_date": "2024-01-20",
  "width": 512,
  "height": 512,
  "max_cloud_coverage": 20
}
```

**Response:** Archivo PNG (`image/png`)

## 🧪 Testing

### Método 1: Swagger UI (Recomendado)

1. Abre http://localhost:8000/docs en tu navegador
2. Expande `POST /sentinel/test`
3. Click en "Try it out"
4. Modifica los parámetros si lo deseas
5. Click "Execute"
6. Descarga el archivo desde el botón "Download"

**Ventajas:**
- ✅ Interfaz visual interactiva
- ✅ Documentación automática de todos los endpoints
- ✅ Prueba sin necesidad de escribir código

### Método 2: curl desde terminal

```bash
# Descarga NDVI
curl -X POST http://localhost:8000/sentinel/test \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-06-15",
    "end_date": "2024-06-20",
    "download_type": "ndvi",
    "width": 256,
    "height": 256,
    "max_cloud_coverage": 30
  }' \
  --output test_ndvi.tif

# Verificar que se descargó
ls -lh test_ndvi.tif
file test_ndvi.tif  # Debe decir "TIFF image data"
```

### Método 3: Python script

```python
import requests

response = requests.post(
    "http://localhost:8000/sentinel/test",
    json={
        "start_date": "2024-06-15",
        "end_date": "2024-06-20",
        "download_type": "ndvi"
    }
)

if response.status_code == 200:
    with open("test_ndvi.tif", "wb") as f:
        f.write(response.content)
    print("✅ Archivo descargado exitosamente")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
```

### Verificar logs del servidor

Los logs incluyen información detallada de cada petición:

```
================================================================================
🛰️  SENTINEL HUB REQUEST - DOWNLOAD_NDVI
================================================================================
📍 Polygon ID: None

--- 1️⃣  COORDENADAS DEL POLÍGONO (como vienen de la DB) ---
Type: Polygon
Coordinates:
  [0] [-3.703800, 40.416800]  (lng=-3.703800, lat=40.416800)
  ...
¿Polígono cerrado? True

--- 2️⃣  BOUNDING BOX CALCULADO ---
Min Longitude: -3.703800
Max Longitude: -3.693800
...
Tamaño aproximado: 842m × 1110m

📐 Dimensiones calculadas: 842m × 1110m → 256px × 256px (resolución: 3.3 m/px × 4.3 m/px)

--- 3️⃣  REQUEST JSON COMPLETO ---
{...}
```

## 📊 Uso desde el frontend

### Ejemplo con fetch API:

```typescript
// Verificar disponibilidad
const checkAvailability = async (polygonId: number) => {
  const response = await fetch('http://localhost:8000/sentinel/check-availability', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      polygon_id: polygonId,
      start_date: '2024-01-15',
      end_date: '2024-01-20',
      max_cloud_coverage: 20
    })
  });
  return await response.json();
};

// Descargar NDVI
const downloadNDVI = async (polygonId: number) => {
  const response = await fetch('http://localhost:8000/sentinel/download/ndvi', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      polygon_id: polygonId,
      start_date: '2024-01-15',
      end_date: '2024-01-20'
    })
  });

  // Descargar el archivo
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `ndvi_${polygonId}.tif`;
  a.click();
};
```

## 🔄 Flujo de trabajo

1. **Usuario dibuja polígono** en el mapa (frontend)
2. **Backend guarda polígono** en PostgreSQL
3. **Frontend solicita disponibilidad** de imágenes (`/check-availability`)
4. **Usuario selecciona rango de fechas**
5. **Frontend solicita descarga** (`/download/ndvi` o `/download/bands`)
6. **Backend descarga desde Sentinel Hub** y retorna archivo
7. **Frontend procesa/visualiza** el archivo descargado

## 🎯 Próximos pasos (OE2)

Una vez completado OE1 (Adquisición), el siguiente paso es:

1. Crear `ndvi_service.py` para procesar los GeoTIFF descargados
2. Calcular estadísticas (media, desviación, área vegetada)
3. Crear tabla `ndvi_analysis` en PostgreSQL
4. Almacenar resultados persistentes
5. Crear endpoint `/api/ndvi/calculate` para solicitar procesamiento

## 📝 Notas técnicas

- El servicio usa **autenticación OAuth2** automática
- Las coordenadas deben estar en **WGS84 (EPSG:4326)**
- El formato es **GeoJSON**: `[longitude, latitude]`
- Timeout por defecto: **120 segundos** para descargas
- Los GeoTIFF usan **FLOAT32** para preservar precisión
- Las imágenes PNG usan **UINT8** con stretch automático

## ⚠️ Limitaciones

- Las imágenes Sentinel-2 tienen **revisita de 5 días**
- La cobertura de nubes puede limitar disponibilidad
- Las descargas pueden tardar según el tamaño del polígono
- Se recomienda **max_cloud_coverage <= 30%** para buenos resultados
