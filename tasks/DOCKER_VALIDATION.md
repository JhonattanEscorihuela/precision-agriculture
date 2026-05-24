# Validación Docker - Guía end-to-end

> **Lección aprendida OE1:** Tests pasando NO garantiza que el sistema completo funcione.  
> SIEMPRE validar con docker-compose después de implementar features.

---

## 🚨 Por qué es crítico

**Tests unitarios detectan:**
- Lógica de negocio correcta
- Funciones individuales
- Casos edge

**Docker-compose detecta:**
- Imports faltantes que tests no usan
- Modelos sin implementar
- Variables de entorno incorrectas
- CORS mal configurado
- Networking entre contenedores
- Dependencias de requirements.txt incompletas
- Configuración de base de datos
- Conflictos de puertos

**Ejemplo real OE1:**
- ✅ pytest: todos pasando
- ❌ docker-compose: `ImportError: cannot import name 'User'`
- Causa: main.py importaba User pero user.py estaba vacío
- Tests no lo detectaron porque no importaban main.py completo

---

## ✅ Checklist de validación Docker

### Paso 1: Build y startup
```bash
docker-compose down -v  # Limpiar todo
docker-compose up --build
```

**Verificar:**
- [ ] Build completa sin errores de dependencias
- [ ] Los 3 contenedores levantan (frontend, backend, db)
- [ ] Backend muestra "Application startup complete"
- [ ] Frontend muestra "Ready in XXXms"
- [ ] Database muestra "database system is ready to accept connections"

### Paso 2: Verificar servicios
```bash
# Backend health
curl http://localhost:8000/
# Debe retornar: {"message":"Backend is running"}

# API Docs
curl -I http://localhost:8000/docs
# Debe retornar: 200 OK

# Frontend
curl -I http://localhost:3000/
# Debe retornar: 200 OK

# Database
docker-compose exec db psql -U postgres -d precision_agriculture -c "SELECT version();"
# Debe retornar: PostgreSQL version
```

### Paso 3: Verificar logs
```bash
# Ver logs completos
docker-compose logs

# Solo backend
docker-compose logs backend --tail=50

# Solo errores
docker-compose logs | grep -i error
```

**Sin errores críticos:**
- [ ] No hay tracebacks de Python
- [ ] No hay "ImportError", "ModuleNotFoundError"
- [ ] No hay "ConnectionRefusedError"
- [ ] No hay "OperationalError" de database

### Paso 4: Validar conectividad entre servicios
```bash
# Backend puede conectar a DB
docker-compose exec backend python -c "from app.database import engine; print('DB OK')"

# Frontend puede hacer request a backend
curl http://localhost:3000/api/test-backend-connection
```

### Paso 5: Prueba manual end-to-end

**OE1 Example:**
1. Abrir http://localhost:3000
2. Ver mapa cargado con Leaflet
3. Hacer click en parcela existente
4. Panel lateral aparece
5. Fechas disponibles se cargan automáticamente
6. Seleccionar fecha
7. Click "Analizar esta fecha"
8. Mensaje de éxito: "✓ Imagen lista para análisis"

**Verificar en BD:**
```bash
docker-compose exec db psql -U postgres -d precision_agriculture -c "
SELECT id, polygon_id, acquisition_date, cloud_coverage 
FROM sentinel_acquisitions 
ORDER BY id DESC LIMIT 5;
"
```

---

## 🐛 Errores comunes y soluciones

### 1. Backend muere al inicio
**Síntoma:** `precision-agriculture-backend exited with code 1`

**Causas comunes:**
- Imports faltantes en main.py
- Modelos sin implementar
- Variables de entorno incorrectas

**Debug:**
```bash
docker-compose logs backend --tail=100
# Buscar "ImportError", "ModuleNotFoundError", "AttributeError"
```

### 2. Frontend no puede conectar a backend
**Síntoma:** CORS errors en consola del navegador

**Verificar:**
```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción: specific origins
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Database connection refused
**Síntoma:** `OperationalError: could not connect to server`

**Verificar:**
```yaml
# docker-compose.yml
services:
  backend:
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/precision_agriculture
    depends_on:
      - db
```

### 4. Modelos no se crean en BD
**Síntoma:** `relation "sentinel_acquisitions" does not exist`

**Verificar:**
```python
# backend/main.py
# ¿Están todos los modelos importados?
from app.models.polygon import Polygon
from app.models.acquisition import SentinelAcquisition

@app.on_event("startup")
async def on_startup():
    await init_db()  # ¿Está llamándose?
```

---

## 📋 Template de validación para PRs

Antes de mergear cualquier feature:

```markdown
## Validación Docker ✅

- [ ] `docker-compose up --build` levanta sin errores
- [ ] Backend logs: sin tracebacks
- [ ] Frontend accesible: http://localhost:3000
- [ ] Backend accesible: http://localhost:8000
- [ ] API Docs: http://localhost:8000/docs
- [ ] Prueba manual completada: [describir flujo probado]
- [ ] Cambios en BD verificados con `psql`

**Logs relevantes:**
```
[pegar últimas 20 líneas de backend logs]
```

**Evidencia manual:**
[screenshot o descripción del flujo funcionando]
```

---

## 🔄 Workflow recomendado

### Para cada feature:

1. **Desarrollo local:**
   ```bash
   # Backend con venv
   cd backend
   source venv_39/bin/activate
   pytest tests/
   uvicorn main:app --reload
   ```

2. **Validación Docker:**
   ```bash
   docker-compose down -v
   docker-compose up --build
   # Seguir checklist arriba
   ```

3. **Si falla Docker pero tests pasan:**
   - Revisar imports en main.py
   - Verificar modelos implementados
   - Verificar requirements.txt actualizado
   - Verificar variables de entorno en docker-compose.yml

4. **Documentar:**
   - Actualizar tasks/lessons.md con errores encontrados
   - Actualizar CLAUDE.md con estado completado
   - Crear tasks/oe{N}_complete.md con evidencia

---

## 🎯 Criterio de completitud

**Un OE NO está completo hasta que:**
- ✅ Tests unitarios pasan
- ✅ Tests de integración pasan
- ✅ `docker-compose up --build` levanta sin errores
- ✅ Flujo manual probado end-to-end
- ✅ Evidencia documentada

**No confiar solo en tests.** Docker-compose es la validación real del sistema completo.
