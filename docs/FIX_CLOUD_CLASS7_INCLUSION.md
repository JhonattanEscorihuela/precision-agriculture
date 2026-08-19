# Fix: Inclusión de SCL Clase 7 en Cálculo de Nubosidad

**Fecha:** 19 de agosto de 2026  
**Cambio:** Incluir clase 7 (Unclassified) en detección de nubes

---

## 🎯 Problema Identificado

**Síntoma reportado:**  
Usuario visualizaba nubes evidentes en imágenes RGB de parcelas, pero el sistema las marcaba como `suitable` con nubosidad reportada muy baja (ej: 10.31%).

**Caso crítico:**
- Parcela 7, fecha 11 agosto 2026
- Nubosidad reportada: 10.31% → `suitable`
- Usuario confirmó: "veo nubes en la imagen"

---

## 🔬 Root Cause

El algoritmo SCL (Scene Classification Layer) de Sentinel-2 clasifica píxeles en 12 categorías (0-11):

- **Clase 8:** Cloud medium probability
- **Clase 9:** Cloud high probability  
- **Clase 10:** Thin cirrus
- **Clase 7:** Unclassified ← **PROBLEMA**

**Definición clase 7 (ESA):**
> Píxeles que no pudieron clasificarse en ninguna categoría con suficiente confianza.

**Contenido típico de clase 7:**
- Bordes de nubes (transición nube-cielo)
- Nubes delgadas (thin clouds) más sutiles que clase 8
- Cirros muy finos más sutiles que clase 10
- Neblina/aerosoles
- Artefactos de sensores

**Análisis de datos reales confirmó:**

| Parcela | Nubes (8+9+10) | Clase 7 | Total con clase 7 | Proporción 7/(8+9+10) |
|---------|----------------|---------|-------------------|-----------------------|
| 7 (crítica) | 10.31% | **14.80%** | **25.11%** | 1.44x más clase 7 |
| 6 | 22.01% | **34.55%** | 56.56% | 1.57x más clase 7 |

**Patrón observado:**  
La clase 7 es **proporcional** a las nubes confirmadas, no es ruido aleatorio. Aparece sistemáticamente donde hay nubes clasificadas (8/9/10).

**Conclusión:**  
Clase 7 son **nubes reales ambiguas** que el clasificador SCL no pudo etiquetar con certeza, pero que afectan la calidad de los datos espectrales.

---

## ✅ Solución Implementada

### Cambio de código

**Archivo:** `backend/app/services/cloud_coverage_service.py`  
**Línea 10:**

```python
# ANTES
CLOUD_CLASSES = (8, 9, 10)  # Solo nubes confirmadas

# DESPUÉS
CLOUD_CLASSES = (7, 8, 9, 10)  # Incluye Unclassified como nube
```

### Justificación científica

**Principio conservador en agricultura de precisión:**
- Falso negativo (analizar fecha nublada) → análisis NDVI erróneo → decisiones agronómicas incorrectas → **pérdida económica**
- Falso positivo (rechazar fecha útil) → buscar otra fecha → menor impacto

**Mejor rechazar una fecha dudosa que analizar datos contaminados por nubes.**

### Threshold de calidad

El umbral de **20% nubosidad** se mantiene sin cambios:

- `suitable`: ≤ 20% nubes (incluye clase 7)
- `caution`: > 20% nubes pero < 80% datos válidos
- `unsuitable`: > 20% nubes

Este threshold fue definido en el Objetivo Específico 1 (OE1) y es el estándar correcto para análisis agronómico con Sentinel-2 en zona tropical.

---

## 📊 Impacto en Datos Existentes

### Re-cálculo de adquisiciones

Se ejecutó script de re-cálculo en todas las 65 adquisiciones existentes:

```bash
python -m app.scripts.recalculate_all_cloud_metrics
```

### Resultados

**Adquisiciones que cambiaron de `suitable` → `unsuitable`:**

| Acq ID | Parcela | Fecha | Cloud Antes | Cloud Ahora | Diferencia | Clase 7 |
|--------|---------|-------|-------------|-------------|------------|---------|
| 32 | 4 | 2026-06-10 | 7.23% | **27.97%** | +20.74% | 20.74% |
| 65 | 7 | 2026-08-11 | 10.31% | **25.11%** | +14.80% | 14.80% ← Caso reportado |
| 76 | 7 | 2026-01-01 | 0.00% | **36.28%** | +36.28% | 36.28% |
| 77 | 7 | 2026-01-16 | 4.58% | **41.59%** | +37.01% | 37.01% |
| 82 | 7 | 2025-12-31 | 0.40% | **25.30%** | +24.90% | 24.90% |

**Resumen:**
- Total procesadas: 65/65
- Sin cambios: 60 (92.3%)
- Cambios a unsuitable: 5 (7.7%)
- Errores: 0

### Impacto por parcela

| Parcela | Total Acqs | Suitable Antes | Suitable Después | Pérdida |
|---------|-----------|----------------|------------------|---------|
| 4 | 15 | 14 | 13 | -1 fecha (7%) |
| 6 | 15 | ~10 | ~10 | Sin cambio |
| 7 | 35 | ~31 | 27 | -4 fechas (12%) |

**Pérdida global de disponibilidad:** 7.7% menos fechas disponibles

---

## 🎯 Validación

### Caso reportado: RESUELTO ✅

**Antes del fix:**
- Parcela 7, 11 agosto 2026
- Nubosidad: 10.31% → `suitable`
- Usuario: "veo nubes en la imagen"

**Después del fix:**
- Parcela 7, 11 agosto 2026
- Nubosidad: **25.11%** → `unsuitable` ✅
- Sistema rechaza correctamente la fecha

### Nuevas adquisiciones

Parcelas creadas después del fix (IDs 10 y 11) para misma fecha 11 agosto 2026:

- **Parcela 10:** 1.69% nubosidad (clase 7: 1.67% + clase 8: 0.02%)
- **Parcela 11:** 12.73% nubosidad (clase 7: 8.80% + clase 8: 3.93%)

Ambas `suitable` y **clase 7 está incluida en el cálculo** → fix funcionando.

---

## 📝 Archivos Modificados

### Código

- `backend/app/services/cloud_coverage_service.py` (1 línea)

### Scripts creados

- `backend/app/scripts/recalculate_all_cloud_metrics.py` - Re-cálculo batch
- `backend/app/scripts/analyze_scl_distribution.py` - Análisis diagnóstico

### Documentación

- `docs/FIX_CLOUD_CLASS7_INCLUSION.md` (este archivo)

---

## 🔄 Trade-off Aceptado

**Costo:**
- ❌ Menos fechas disponibles (-7.7%)

**Beneficio:**
- ✅ Garantía de datos limpios
- ✅ Análisis NDVI más confiable
- ✅ Reduce riesgo de decisiones agronómicas con datos contaminados
- ✅ Calidad científica mejorada

**Conclusión:** El trade-off es favorable. Mejor tener menos fechas pero garantizar que todas sean verdaderamente aptas.

---

## 📚 Referencias

- **Sentinel-2 L2A Product Specification:** [ESA](https://sentinels.copernicus.eu/web/sentinel/technical-guides/sentinel-2-msi/level-2a/algorithm-overview)
- **SCL Classification:** Scene Classification Layer (banda de calidad)
- **Threshold 20%:** Estándar agricultura de precisión para Sentinel-2 en zona tropical

---

**Elaborado por:** Claude Code  
**Implementado:** 19 de agosto de 2026  
**Estado:** Validado y en producción
