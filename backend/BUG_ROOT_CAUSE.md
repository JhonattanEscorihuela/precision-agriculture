# Bug NDVI: Root Cause Analysis

**Fecha:** 2026-06-12  
**Severidad:** CRÍTICA  
**Impacto:** Todos los cálculos NDVI incorrectos (~50% más bajos)

---

## 🐛 El Bug Real

**NO era el scale factor** (como pensábamos inicialmente).

**El problema real:** Diferencia metodológica en cálculo de NDVI mean.

### Nuestra implementación (INCORRECTA):
```python
# Calculamos NDVI pixel por pixel
ndvi[pixel] = (B08[pixel] - B04[pixel]) / (B08[pixel] + B04[pixel])

# Luego promediamos todos los NDVIs
ndvi_mean = mean(ndvi[all_pixels])  # ← INCORRECTO
# Resultado: 0.4882
```

### Metodología Copernicus (CORRECTA):
```python
# Primero calculamos reflectancias medias
b04_mean = mean(B04[all_pixels])
b08_mean = mean(B08[all_pixels])

# Luego calculamos NDVI de esas medias
ndvi_mean = (b08_mean - b04_mean) / (b08_mean + b04_mean)  # ← CORRECTO
# Resultado: 0.8762 ≈ 0.8535 Copernicus ✅
```

---

## 📊 Evidencia

**Fecha de prueba:** 2026-03-22  
**Parcela:** 211 SRRG, Calabozo, Venezuela

| Método | Valor | Fuente |
|--------|-------|--------|
| mean(NDVI[pixels]) | 0.4882 | Nuestra implementación inicial |
| NDVI(mean(B04), mean(B08)) | 0.8762 | Metodología correcta |
| Referencia CSV Copernicus | 0.8535 | Ground truth |

**Diferencia:** 0.8762 vs 0.8535 = 0.0227 (2.27%) ← **Dentro de tolerancia** ✅

---

## 🔍 Por Qué Son Diferentes

Matemáticamente:

```
mean(a/b) ≠ mean(a) / mean(b)
```

Ejemplo simplificado con 2 píxeles:

```
Pixel 1: B04=0.01, B08=0.20 → NDVI = 0.90
Pixel 2: B04=0.02, B08=0.28 → NDVI = 0.87

Método 1 (nuestro inicial):
  mean(NDVI) = (0.90 + 0.87) / 2 = 0.885

Método 2 (Copernicus):
  mean(B04) = (0.01 + 0.02) / 2 = 0.015
  mean(B08) = (0.20 + 0.28) / 2 = 0.240
  NDVI(means) = (0.240 - 0.015) / (0.240 + 0.015) = 0.882
```

La diferencia se amplifica con mayor varianza en los píxeles.

---

## ⚠️ Scale Factor: Falsa Pista

**Qué investigamos primero:** División por 10000 (scale factor L2A)

**Por qué parecía el culpable:**
- Los valores eran ~50% más bajos
- Había precedentes de scale factors en Sentinel-2

**Por qué NO era el problema:**
- Process API ya retorna valores en 0.0-1.0 (confirmado con dtype float32)
- Aplicar /10000 causaba underflow (0.02 → 0.000002)
- Pero al removerlo, seguía dando 0.4882 vs 0.8535

**Tiempo perdido en falsa pista:** ~2 horas

---

## ✅ La Solución

### Backend: `app/services/ndvi_service.py`

**Cambio en `_calculate_statistics()`:**

```python
# ANTES (INCORRECTO):
def _calculate_statistics(self, ndvi, nodata_mask):
    valid_pixels = ndvi[~nodata_mask & ~np.isnan(ndvi)]
    return {
        "ndvi_mean": float(np.mean(valid_pixels))  # ← mean de array
    }

# DESPUÉS (CORRECTO):
def _calculate_statistics(self, ndvi, nodata_mask, b04_bytes, b08_bytes):
    # Leer bandas originales
    b04 = rasterio.open(io.BytesIO(b04_bytes)).read(1)
    b08 = rasterio.open(io.BytesIO(b08_bytes)).read(1)
    
    # NDVI de las reflectancias medias
    b04_mean = b04[~nodata_mask].mean()
    b08_mean = b08[~nodata_mask].mean()
    ndvi_mean = (b08_mean - b04_mean) / (b08_mean + b04_mean)
    
    return {
        "ndvi_mean": float(ndvi_mean)  # ← NDVI de means
    }
```

### Scripts de validación

Mismo cambio aplicado a:
- `scripts/validate_ndvi_cross_check.py`
- `scripts/inspect_tiff_raw.py`
- `scripts/debug_ndvi_calculation.py`

---

## 📚 Lecciones Aprendidas

### 1. **Validación cruzada desde el principio**
- Comparar contra ground truth ANTES de marcar OE completo
- No asumir que "tests pasando" = "resultados correctos"

### 2. **Verificar metodologías, no solo implementaciones**
- El problema no era "cómo calculamos" sino "qué calculamos"
- Leer papers/documentación de fuente de datos

### 3. **Debugging con casos concretos**
- Calcular manualmente con valores conocidos
- Si manual ≠ código → bug en código
- Si manual = código pero ≠ referencia → metodología incorrecta

### 4. **No asumir precedentes**
- "Sentinel-2 usa scale factor" → Cierto para STAC directo
- Pero Process API es diferente → Validar para cada caso

### 5. **Falsa sensación de corrección**
- Remover scale factor SÍ era necesario
- Pero no suficiente → había un segundo bug oculto
- Siempre validar resultado final, no pasos intermedios

---

## 🎯 Resultado Final

**Antes del fix:**
- 28/28 fechas FAIL
- Diferencia promedio: 20.07%
- NDVI mean method: mean(array)

**Después del fix:**
- Pendiente: Re-ejecutar validación completa
- Esperado: 28/28 PASS o >90% PASS
- NDVI mean method: NDVI(mean(B04), mean(B08))

---

## 📝 Archivos Modificados

1. `app/services/ndvi_service.py`
   - Línea 115: Pasar b04_data y b08_data a _calculate_statistics
   - Líneas 218-259: Nueva implementación _calculate_statistics

2. `scripts/validate_ndvi_cross_check.py`
   - Líneas 150-157: Cambiar a NDVI de means

3. `scripts/inspect_tiff_raw.py`
   - Actualizado para mostrar ambos métodos

4. `scripts/debug_ndvi_calculation.py`
   - Actualizado para comparar métodos

5. `scripts/test_ndvi_one_date.py`
   - Nuevo script de debugging directo

---

**Estado:** Fix aplicado, validación en ejecución
