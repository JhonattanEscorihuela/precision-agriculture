# ⚡ Quick Start - Prueba Sentinel en 2 minutos

## 1️⃣ Configurar credenciales

```bash
cd backend
cp .env.example .env
```

Edita `.env` y agrega tus credenciales de [Copernicus DataSpace](https://dataspace.copernicus.eu/):

```bash
SENTINEL_CLIENT_ID=your_client_id_here
SENTINEL_CLIENT_SECRET=your_client_secret_here
```

## 2️⃣ Instalar dependencias

```bash
pip install -r requirements.txt
```

## 3️⃣ Iniciar servidor

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 4️⃣ Probar el servicio

### Opción A: Swagger UI (Recomendado)

Abre en tu navegador: **http://localhost:8000/docs**

1. Expande `POST /sentinel/test`
2. Click en "Try it out"
3. Usa estos valores:
   ```json
   {
     "start_date": "2024-06-15",
     "end_date": "2024-06-20",
     "download_type": "ndvi"
   }
   ```
4. Click "Execute"
5. Descarga el archivo desde el botón "Download"

### Opción B: curl desde terminal

```bash
# Probar descarga de NDVI
curl -X POST http://localhost:8000/sentinel/test \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-06-15",
    "end_date": "2024-06-20",
    "download_type": "ndvi"
  }' \
  --output test_ndvi.tif

# Probar descarga de imagen RGB
curl -X POST http://localhost:8000/sentinel/test \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-06-15",
    "end_date": "2024-06-20",
    "download_type": "true-color"
  }' \
  --output test_true_color.png

# Probar descarga de bandas B04+B08
curl -X POST http://localhost:8000/sentinel/test \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-06-15",
    "end_date": "2024-06-20",
    "download_type": "bands"
  }' \
  --output test_bands.tif
```

**Resultado esperado:**
- Archivos descargados: `test_ndvi.tif`, `test_true_color.png`, `test_bands.tif`
- Logs del servidor muestran detalles de la petición (coordenadas, bbox, resolución)

---

## 🎉 ¡Listo!

Si descargaste exitosamente los archivos, tu servicio Sentinel-2 está funcionando correctamente.

### 📖 Próximos pasos:

1. **[SENTINEL_SERVICE.md](SENTINEL_SERVICE.md)** - Documentación completa de la API
2. **Swagger UI**: http://localhost:8000/docs - Documentación interactiva
3. Integrar con el frontend para usar tus propios polígonos

### 🔍 Endpoints principales:

- `POST /sentinel/test` - Prueba con coordenadas hardcodeadas (**no requiere DB**)
- `POST /sentinel/check-availability` - Verifica disponibilidad de imágenes
- `POST /sentinel/download/ndvi` - Descarga NDVI de tus polígonos
- `POST /sentinel/download/bands` - Descarga bandas específicas
- `POST /sentinel/download/true-color` - Descarga imagen RGB

### 📍 Coordenadas de prueba:

El endpoint `/sentinel/test` usa estas coordenadas (Madrid, España):

```json
[[-3.7038, 40.4168], [-3.7038, 40.4268], [-3.6938, 40.4268], [-3.6938, 40.4168], [-3.7038, 40.4168]]
```

Aproximadamente 1 km × 1 km, ideal para pruebas rápidas.

---

## 🆘 Troubleshooting

### El servidor no responde

```bash
# Verificar que el servidor está corriendo
curl http://localhost:8000/

# Ver logs del servidor (en la terminal de uvicorn)
```

### Errores de autenticación

```bash
# Verificar credenciales
cat .env | grep SENTINEL

# Asegúrate de que las variables estén definidas
echo $SENTINEL_CLIENT_ID
echo $SENTINEL_CLIENT_SECRET
```

### Error 400 (Bad Request)

- Verifica el formato de fechas: `YYYY-MM-DD`
- Asegúrate de que `download_type` sea: `"ndvi"`, `"true-color"`, o `"bands"`

### Error 500 (Internal Server Error)

- Revisa los logs del servidor para ver el error de Sentinel Hub
- Verifica que las fechas tengan imágenes disponibles
- Prueba con un rango de fechas más amplio o `max_cloud_coverage` más alto
