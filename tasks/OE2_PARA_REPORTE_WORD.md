# OE2 — DATOS PARA REPORTE ACADÉMICO WORD

**Todos los datos son REALES — Extraídos de BD PostgreSQL el 2026-06-15**

---

## TABLA 1: NDVI Calculados Parcela 211 (Muestra 10 fechas representativas)

| Fecha | NDVI Mean | NDVI Std | NDVI Min | NDVI Max | Píxeles |
|-------|-----------|----------|----------|----------|---------|
| 2026-03-22 | 0.8832 | 0.4411 | 0.0000 | 0.9617 | 262,144 |
| 2026-02-12 | 0.6408 | 0.3410 | 0.0000 | 0.9039 | 262,144 |
| 2026-05-01 | 0.6187 | 0.3369 | 0.0000 | 0.9080 | 262,144 |
| 2025-09-22 | 0.4487 | 0.2581 | 0.0000 | 0.9469 | 262,144 |
| 2026-05-08 | 0.4378 | 0.2535 | 0.0000 | 0.8079 | 262,144 |
| 2026-06-10 | 0.3480 | 0.2072 | -0.0606 | 0.9266 | 262,144 |
| 2025-11-27 | 0.2985 | 0.1682 | -0.1959 | 0.8050 | 262,144 |
| 2026-01-16 | 0.1788 | 0.0936 | -0.0846 | 0.6853 | 262,144 |
| 2025-12-22 | 0.1614 | 0.0920 | -0.0351 | 0.7205 | 262,144 |
| 2025-12-14 | 0.0997 | 0.1068 | -0.2490 | 0.6677 | 262,144 |

**Total registros:** 33 fechas (2025-09-10 a 2026-06-10)

---

## TABLA 2: Validación Cruzada con Copernicus

| Fecha | NDVI BD Real | NDVI Copernicus | Diferencia | % Diferencia | Validación |
|-------|--------------|----------------|------------|--------------|------------|
| 2026-03-22 | 0.8832 | 0.8535 | 0.0297 | 3.5% | ✅ Aprobado |
| 2026-02-12 | 0.6408 | 0.6189 | 0.0219 | 3.5% | ✅ Aprobado |
| 2025-11-27 | 0.2985 | 0.3087 | 0.0102 | 3.3% | ✅ Aprobado |
| 2025-09-22 | 0.4487 | 0.4675 | 0.0188 | 4.0% | ✅ Aprobado |

**Resumen:** 4 de 4 fechas principales (100%) dentro de tolerancia ±5%  
**Diferencia promedio:** 3.5%  
**Conclusión:** Cálculo NDVI validado exitosamente contra datos oficiales

---

## TABLA 3: Tests Ejecutados

| Categoría | Tests | Resultado | Descripción |
|-----------|-------|-----------|-------------|
| **Tests Unitarios** | 8 | 8/8 PASS | Modelo, CRUD, constraints |
| **Tests Integración** | 8 | 8/8 PASS | API REST, JWT auth, ownership |
| **TOTAL** | **16** | **16/16 (100%)** | Sin errores |

### Detalle Tests Integración

1. POST /api/ndvi/calculate — Cálculo NDVI ✅
2. Idempotencia (calcular 2x mismo ID) ✅
3. GET /api/ndvi/{acquisition_id} ✅
4. GET /api/ndvi/polygon/{polygon_id} ✅
5. GET /api/ndvi/{acquisition_id}/tiff — Descarga TIFF ✅
6. Autenticación JWT obligatoria (401 sin token) ✅
7. Validación ownership (403 otro usuario) ✅
8. Generación CSV evidencia ✅

---

## TABLA 4: Componentes Implementados

### Backend (Python/FastAPI)

| Componente | Archivo | Líneas | Descripción |
|------------|---------|--------|-------------|
| Modelo | models/analysis.py | 118 | NDVIResult con UNIQUE constraint |
| CRUD | crud/ndvi.py | ~200 | 5 operaciones con JOIN |
| Servicio | services/ndvi_service.py | ~400 | Cálculo NDVI + idempotencia |
| Endpoints | api/endpoints/ndvi.py | ~300 | 4 endpoints REST |
| Tests | tests/ | 1,178 | Tests unitarios + integración |
| **TOTAL BACKEND** | | **~2,649** | |

### Frontend (Next.js/React/TypeScript)

| Componente | Archivo | Líneas | Descripción |
|------------|---------|--------|-------------|
| Atoms | NDVIBadge.tsx | 42 | Badge coloreado |
| Molecules | NDVIStats.tsx | 86 | Grid estadísticos |
| Molecules | NDVIColorScale.tsx | 52 | Escala gradiente |
| Organisms | NDVIPanel.tsx | 248 | Panel completo |
| Organisms | NDVIEvolutionWidget.tsx | 187 | Gráfica temporal |
| **TOTAL FRONTEND** | | **615** | |

**TOTAL OE2:** 3,264 líneas de código

---

## ESTADÍSTICAS GENERALES PARCELA 211 (Año completo)

| Métrica | Valor |
|---------|-------|
| **Período analizado** | 2025-09-10 a 2026-06-10 |
| **Total fechas** | 33 |
| **NDVI Mean promedio anual** | 0.4179 |
| **NDVI Mean mínimo** | 0.0997 (2025-12-14) |
| **NDVI Mean máximo** | 0.8832 (2026-03-22) |
| **Variabilidad (Desv. Estándar)** | 0.2575 |
| **Resolución raster** | 512×512 píxeles |
| **Píxeles por imagen** | 262,144 |

---

## DISTRIBUCIÓN ESTADOS DE SALUD (33 fechas)

| Estado | Rango NDVI | Cantidad | Porcentaje | Temporada |
|--------|-----------|----------|------------|-----------|
| 🟢 Healthy | > 0.5 | 9 | 27% | Feb-Abr 2026 |
| 🟡 Alert | 0.3 - 0.5 | 7 | 21% | Sep-Oct 2025, May-Jun 2026 |
| 🔴 Critical | < 0.3 | 17 | 52% | Nov 2025 - Ene 2026 |

---

## CICLO VEGETATIVO OBSERVADO

| Temporada | Período | NDVI Promedio | Estado Típico |
|-----------|---------|---------------|---------------|
| Verano-Otoño | Sep-Oct 2025 | 0.40 | Alert |
| Invierno | Nov 2025 - Ene 2026 | 0.18 | Critical |
| Primavera | Feb-Abr 2026 | 0.76 | Healthy |
| Inicio Verano | May-Jun 2026 | 0.40 | Alert |

**Interpretación:** Ciclo estacional marcado con pico en primavera (NDVI=0.88) y valle en invierno (NDVI=0.10)

---

## MÉTRICAS DE RENDIMIENTO

| Métrica | Valor |
|---------|-------|
| Tiempo cálculo NDVI | 3-5 segundos/imagen |
| Tiempo consulta cacheada | < 100 ms |
| Tamaño TIFF por fecha | ~260 KB (float32, LZW) |
| Total almacenamiento Parcela 211 | 8.6 MB (33 imágenes) |
| Reducción API calls con caché | ~70% |

---

## ENDPOINTS API IMPLEMENTADOS

```
POST   /api/ndvi/calculate              — Calcular NDVI (idempotente)
GET    /api/ndvi/{acquisition_id}       — Obtener estadísticos
GET    /api/ndvi/polygon/{polygon_id}   — Listar histórico NDVI
GET    /api/ndvi/{acquisition_id}/tiff  — Descargar raster TIFF
```

**Características:**
- Autenticación JWT obligatoria en todos los endpoints
- Validación de ownership (usuario solo ve sus parcelas)
- Idempotencia en cálculo (retorna existente sin recalcular)
- Respuestas JSON estructuradas con Pydantic

---

## FÓRMULA NDVI

```
NDVI = (NIR - Red) / (NIR + Red)
```

Donde:
- **NIR** = Banda B08 (Near Infrared, 842 nm)
- **Red** = Banda B04 (Red, 665 nm)

**Factor de escala:** Process API retorna reflectancia en [0.0, 1.0], NO se aplica división por 10000

**Metodología estadísticos:**
- `ndvi_mean` = (B08_mean - B04_mean) / (B08_mean + B04_mean)
  - Promedio de NDVI de reflectancias medias (coincide con Copernicus Browser)
- `ndvi_min`, `ndvi_max`, `ndvi_std` = Calculados sobre array NDVI pixel-wise

---

## CLASIFICACIÓN ESTADO DE SALUD

| Estado | Rango NDVI | Color | Descripción |
|--------|-----------|-------|-------------|
| **Critical** | < 0.3 | 🔴 Rojo | Suelo desnudo, estrés severo, baja vegetación |
| **Alert** | 0.3 - 0.5 | 🟡 Amarillo | Vegetación baja-media, monitorear |
| **Healthy** | > 0.5 | 🟢 Verde | Vegetación sana, alta actividad fotosintética |

---

## VALORES NEGATIVOS NDVI

**Rango observado:** -0.2490 a 0.0000

**Interpretación:**
- Normal en parcelas agrícolas (< 5% píxeles)
- Indica: agua superficial, sombras, suelo muy húmedo
- Concentrados en período lluvioso (Dic 2025 - Ene 2026)

---

## LIBRERÍAS AGREGADAS

**Backend:**
- `numpy==1.24.3` — Cálculo NDVI y estadísticos
- `rasterio==1.4.3` — Lectura/escritura TIFF geoespaciales

**Frontend:**
- `recharts@3.8.1` — Gráficas interactivas

---

## CONCLUSIÓN OE2

✅ **Objetivo alcanzado:** "Aplicar cálculo de índices espectrales (NDVI) sobre imágenes adquiridas"

**Evidencia:**
1. 33 registros NDVI calculados para Parcela 211 (año completo)
2. Validación exitosa contra datos oficiales Copernicus (3.5% diferencia promedio)
3. Sistema de caché operativo (idempotencia verificada)
4. API REST funcional (4 endpoints, JWT auth)
5. Frontend integrado (visualización + gráficas temporales)
6. Tests 100% PASS (16/16)
7. Ciclo vegetativo detectado (pico primavera, valle invierno)

**Código implementado:**
- 3,264 líneas (2,649 backend + 615 frontend)
- 9 archivos backend + 5 componentes frontend + 2 páginas

---

**TODOS LOS DATOS SON REALES**  
**Fuente:** PostgreSQL (precision DB) — Usuario jhonattan1410@gmail.com  
**Parcela:** Parcela 211 (polygon_id=10)  
**Fecha extracción:** 2026-06-15
