# 🔍 Auditoría de Archivos .md y Logs

**Fecha:** 2026-06-15  
**Objetivo:** Identificar archivos esenciales vs eliminables para limpiar el repositorio

---

## 📋 CLASIFICACIÓN DE ARCHIVOS

### ✅ **ESENCIALES - MANTENER** (Espina vertebral del proyecto)

#### Nivel Raíz (3 archivos)
| Archivo | Tamaño | Razón |
|---------|--------|-------|
| `CLAUDE.md` | 515 líneas | ⭐ **CRÍTICO** - Instrucciones principales para Claude Code |
| `README.md` | - | ⭐ **CRÍTICO** - Documentación principal del proyecto |
| `INSTRUCCIONES_CLAUDE.md` | 316 líneas | ⭐ **CRÍTICO** - NUNCA ELIMINAR - Instrucciones del usuario |

#### Tasks/ (4 archivos esenciales)
| Archivo | Tamaño | Razón |
|---------|--------|-------|
| `tasks/lessons.md` | 14K | ⭐ **CRÍTICO** - Historial de errores y soluciones (15 lecciones) |
| `tasks/todo.md` | 29K | ⭐ **CRÍTICO** - Plan de trabajo activo OE2-OE5 |
| `tasks/validation_report.md` | 17K | ⭐ **IMPORTANTE** - Reporte de validación reciente (2026-06-15) |
| `tasks/correcciones_completadas.md` | 9.2K | ⭐ **IMPORTANTE** - Evidencia de correcciones de seguridad |

#### Backend/ (2 archivos)
| Archivo | Tamaño | Razón |
|---------|--------|-------|
| `backend/SENTINEL_SERVICE.md` | - | ✅ Documentación técnica del servicio Sentinel |
| `backend/QUICK_START.md` | - | ✅ Guía rápida para pruebas (útil para nuevos devs) |

#### Frontend/ (1 archivo)
| Archivo | Tamaño | Razón |
|---------|--------|-------|
| `frontend/DESIGN_SYSTEM.md` | - | ✅ Sistema de diseño (referencia para UI) |

---

### 🗑️ **ELIMINABLES - DEBUG/TEMPORAL** (Candidatos a borrar)

#### 1. Archivos de FIXES específicos (ya aplicados y documentados)
```
❌ RESUMEN_COORD_FIX.md                    # Fix ya aplicado, documentado en lessons.md
❌ backend/BUG_ROOT_CAUSE.md               # Bug NDVI ya corregido
❌ frontend/COORD_FIX.md                   # Duplicado de RESUMEN_COORD_FIX.md
❌ frontend/POLYGON_CLOSING_FIX.md         # Fix ya aplicado
```

**Razón:** Estos documentos fueron útiles durante el debugging pero ahora están obsoletos.  
El contenido importante ya está en `lessons.md`.

---

#### 2. Archivos de sesiones específicas (2026-06-09)
```
❌ tasks/CHANGELOG_2026-06-09.md           (4.3K)  # Changelog de una sesión específica
❌ tasks/LIMPIEZA_CODIGO_2026-06-09.md     (3.6K)  # Limpieza ya completada
❌ tasks/SESSION_2026-06-09_RESUMEN.md     (10K)   # Resumen de sesión antigua
❌ tasks/REFACTOR_SENTINEL_SERVICE.md      (8.9K)  # Refactor ya aplicado
```

**Razón:** Documentación histórica de sesiones pasadas. El resultado ya está en el código.

---

#### 3. Múltiples documentos OE2 con datos redundantes
```
⚠️ tasks/OE2_DATOS_BD_REAL.md              (8.5K)
⚠️ tasks/OE2_DATOS_EXACTOS_SOLICITADOS.md  (12K)
⚠️ tasks/OE2_DATOS_FINALES_PARCELA_211.md  (12K)
⚠️ tasks/OE2_PARA_REPORTE_WORD.md          (7.6K)
⚠️ tasks/OE2_datos_reales_reporte.md       (15K)
⚠️ tasks/OE2_resumen_ejecutivo.md          (9.3K)
```

**Análisis:**
- Total: **~74KB** en 6 archivos sobre datos OE2
- Contenido: Estadísticas NDVI extraídas de BD para reportes
- **PROBLEMA:** Mucha redundancia entre estos archivos

**Propuesta:**
1. **MANTENER:** `OE2_PARA_REPORTE_WORD.md` (datos finales para el reporte académico)
2. **ELIMINAR:** Los otros 5 archivos (datos intermedios/duplicados)

---

#### 4. Resúmenes finales de OEs (posiblemente redundantes)
```
⚠️ tasks/OE1_RESUMEN_FINAL.md              (8.7K)
⚠️ tasks/OE2_RESUMEN_FINAL.md              (6.6K)
```

**Análisis:**
- Resúmenes finales de OE1 y OE2
- Parte del contenido ya está en CLAUDE.md (sección "ESTADO ACTUAL")

**Propuesta:**
- **MANTENER** si contienen evidencia académica específica (para el reporte de grado)
- **ELIMINAR** si solo duplican lo que está en CLAUDE.md

---

#### 5. Archivos de testing/documentación técnica
```
✅ MANTENER: tasks/DOCKER_VALIDATION.md    (5.8K)  # Guía de validación importante
✅ MANTENER: tasks/NDVI_EXPLICACION.md     (5.7K)  # Explicación teórica NDVI
❌ frontend/TEST_OE1_FRONTEND.md            # Tests ya pasados, evidencia en commits
❌ frontend/CHANGELOG_DESIGN.md             # Changelog viejo (Marzo 2026)
```

---

#### 6. Archivos menores
```
❌ tasks/TODO_menores.md                    (4.6K)  # TODOs viejos probablemente resueltos
```

---

### 📊 **LOGS - ELIMINAR**

```
❌ frontend/.next/dev/logs/                (4.0K)  # Logs de desarrollo Next.js
```

**Razón:** Logs de desarrollo autogenerados, no deben estar en el repo.  
Ya están en `.gitignore` pero existen localmente.

---

## 🎯 RESUMEN DE RECOMENDACIONES

### Mantener (14 archivos - ~80KB):
- ✅ `CLAUDE.md` ⭐ (NUNCA ELIMINAR)
- ✅ `INSTRUCCIONES_CLAUDE.md` ⭐ (NUNCA ELIMINAR)
- ✅ `README.md` ⭐
- ✅ `tasks/lessons.md` ⭐
- ✅ `tasks/todo.md` ⭐
- ✅ `tasks/validation_report.md`
- ✅ `tasks/correcciones_completadas.md`
- ✅ `tasks/DOCKER_VALIDATION.md`
- ✅ `tasks/NDVI_EXPLICACION.md`
- ✅ `tasks/OE2_PARA_REPORTE_WORD.md` (datos finales reporte)
- ✅ `tasks/AUDITORIA_ARCHIVOS.md` (este documento)
- ✅ `backend/SENTINEL_SERVICE.md`
- ✅ `backend/QUICK_START.md`
- ✅ `frontend/DESIGN_SYSTEM.md`

### Revisar antes de eliminar (2 archivos):
- ⚠️ `tasks/OE1_RESUMEN_FINAL.md` — ¿Contiene evidencia académica única?
- ⚠️ `tasks/OE2_RESUMEN_FINAL.md` — ¿Contiene evidencia académica única?

### Eliminar (18 archivos - ~135KB):
```bash
# Fixes específicos ya aplicados (4 archivos)
rm RESUMEN_COORD_FIX.md
rm backend/BUG_ROOT_CAUSE.md
rm frontend/COORD_FIX.md
rm frontend/POLYGON_CLOSING_FIX.md

# Sesiones antiguas 2026-06-09 (4 archivos)
rm tasks/CHANGELOG_2026-06-09.md
rm tasks/LIMPIEZA_CODIGO_2026-06-09.md
rm tasks/SESSION_2026-06-09_RESUMEN.md
rm tasks/REFACTOR_SENTINEL_SERVICE.md

# Datos OE2 redundantes (5 archivos - mantener solo el del reporte)
rm tasks/OE2_DATOS_BD_REAL.md
rm tasks/OE2_DATOS_EXACTOS_SOLICITADOS.md
rm tasks/OE2_DATOS_FINALES_PARCELA_211.md
rm tasks/OE2_datos_reales_reporte.md
rm tasks/OE2_resumen_ejecutivo.md

# Tests/changelogs antiguos (3 archivos)
rm frontend/TEST_OE1_FRONTEND.md
rm frontend/CHANGELOG_DESIGN.md
rm tasks/TODO_menores.md

# Logs (2 directorios/archivos)
rm -rf frontend/.next/dev/logs/
rm -rf backend/.pytest_cache/  # Si está commiteado
```

---

## 📉 IMPACTO DE LA LIMPIEZA

| Categoría | Archivos actuales | Archivos finales | Reducción |
|-----------|-------------------|------------------|-----------|
| **Archivos .md** | 34 archivos | ~16 archivos | **-53%** |
| **Tamaño total** | ~210KB | ~75KB | **-64%** |
| **Logs** | 4KB | 0KB | **-100%** |

---

## ✅ CRITERIOS DE DECISIÓN

**MANTENER si:**
- ⭐ Es parte de la documentación principal (CLAUDE.md, README.md)
- ⭐ Contiene lecciones/patrones reutilizables (lessons.md)
- ⭐ Es plan de trabajo activo (todo.md)
- ⭐ Documenta arquitectura/diseño (DESIGN_SYSTEM.md, SENTINEL_SERVICE.md)
- ⭐ Evidencia académica para el reporte de grado

**ELIMINAR si:**
- ❌ Documenta un fix específico ya aplicado
- ❌ Es resumen de una sesión pasada
- ❌ Datos redundantes (múltiples versiones del mismo contenido)
- ❌ Logs de desarrollo autogenerados
- ❌ TODOs obsoletos

---

## 🚀 DECISIÓN DEL USUARIO

### ✅ **CONFIRMADO:**
- ⭐ `INSTRUCCIONES_CLAUDE.md` **NUNCA se elimina** (instrucción del usuario)
- ⭐ Ambos archivos (`CLAUDE.md` e `INSTRUCCIONES_CLAUDE.md`) son diferentes y ambos críticos

### ⚠️ **PENDIENTE DE DECISIÓN:**
1. **Revisar manualmente** `OE1_RESUMEN_FINAL.md` y `OE2_RESUMEN_FINAL.md`
   - ¿Contienen evidencia académica única para el reporte de grado?
   - Si sí → Mantener
   - Si no → Eliminar

2. **Confirmar eliminación** de los 18 archivos listados arriba

---

## 🚀 PRÓXIMOS PASOS

1. ✅ Usuario confirma qué hacer con `OE1_RESUMEN_FINAL.md` y `OE2_RESUMEN_FINAL.md`
2. ✅ Usuario autoriza eliminación de archivos obsoletos
3. 🔧 Ejecutar script de limpieza
4. 📝 Commit: "chore: clean up obsolete documentation and logs"
5. 🚀 Push al repositorio

---

**Esperando confirmación del usuario para proceder...** ⏸️
