# Corrección Docker + Lección end-to-end

**Fecha:** 2026-05-23  
**Contexto:** Backend murió en docker-compose tras OE1 completo

---

## 🐛 Problema encontrado

```
precision-agriculture-backend exited with code 1

ImportError: cannot import name 'User' from 'app.models.user'
```

**Causa:**
- `backend/main.py` línea 8 importaba `User`
- `backend/app/models/user.py` estaba vacío (solo boilerplate)
- Tests pasaban porque no importaban main.py directamente
- Docker sí ejecuta main.py completo → error al startup

---

## ✅ Solución aplicada

**Archivo:** `backend/main.py`

```python
# Antes
from app.models.user import User

# Después
# from app.models.user import User  # TODO OE5: Implementar autenticación
```

**Resultado:**
```bash
docker-compose restart backend
# Backend levantó correctamente
# INFO: Application startup complete.
# INFO: Uvicorn running on http://0.0.0.0:8000
```

---

## 📚 Lección crítica aprendida

### Tests pasando ≠ Sistema funcionando

**Lo que detectan tests:**
- Lógica de negocio
- Funciones individuales
- Casos edge

**Lo que NO detectan tests:**
- Imports en main.py no utilizados por tests
- Modelos vacíos referenciados en startup
- Variables de entorno Docker
- CORS configuration
- Networking entre contenedores
- Dependencias faltantes en requirements.txt

### Nuevo workflow OBLIGATORIO

```
1. Implementar feature
2. ✅ pytest tests/
3. ✅ docker-compose up --build    ← CRÍTICO
4. ✅ Prueba manual end-to-end
5. ✅ Documentar evidencia
```

**Regla:** Feature NO está completa hasta que docker-compose levanta sin errores.

---

## 📝 Documentación actualizada

### 1. tasks/lessons.md
- Agregado error Docker como lección #5
- Agregado patrón de validación end-to-end como lección #6
- Checklist de completitud para cada OE

### 2. tasks/DOCKER_VALIDATION.md (NUEVO)
Guía completa con:
- Checklist de validación Docker paso a paso
- Comandos para verificar servicios
- Errores comunes y soluciones
- Template para validación en PRs
- Criterio de completitud

### 3. CLAUDE.md
- Sección "WORKFLOW DE TRABAJO" actualizada con validación Docker obligatoria
- Criterio de completitud expandido (tests + docker + manual)
- Checklist pre-respuesta actualizado
- Sección "TESTING Y VALIDACIÓN" con 3 niveles

---

## ✅ Estado actual verificado

```bash
docker-compose ps
NAME                             STATUS
precision-agriculture-backend    Up
precision-agriculture-db         Up  
precision-agriculture-frontend   Up

# Servicios funcionando
http://localhost:3000    → Frontend ✅
http://localhost:8000    → Backend ✅
http://localhost:8000/docs → API Docs ✅
```

---

## 🎯 Aplicar en futuros OEs

**OE2, OE3, OE4, OE5 - SIEMPRE:**

1. Implementar feature backend
2. Tests unitarios → ✅
3. Tests integración → ✅
4. **`docker-compose up --build` → ✅**
5. Prueba manual frontend → ✅
6. Documentar en `tasks/oe{N}_complete.md`

**Si docker-compose falla pero tests pasan:**
- Revisar imports en main.py
- Verificar modelos implementados completos
- Revisar requirements.txt actualizado
- Verificar variables entorno docker-compose.yml
- Revisar CORS en FastAPI

---

## 📊 Impacto

**Antes:**
- Tests pasan → "Feature completo" ❌
- Docker falla en producción/despliegue
- Debugging post-deploy

**Ahora:**
- Tests pasan → docker-compose → manual → "Feature completo" ✅
- Issues detectados antes de mergear
- Sistema validado end-to-end

**Tiempo extra:** ~5 min por feature  
**Bugs evitados:** Críticos en producción

---

## 🚀 Próximo paso

Con sistema Docker validado, continuar con **OE2 Backend**:
- Implementar `ndvi_service.py`
- Crear modelo `NDVIAnalysis`
- CRUD para NDVI
- Endpoint `POST /api/ndvi/calculate`
- **Validar:** tests + docker + manual

Ver `tasks/oe2_plan.md` para plan completo.
