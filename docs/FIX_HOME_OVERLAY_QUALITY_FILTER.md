# Fix: Filtro de calidad en overlays del Home

**Fecha:** 19 de agosto de 2026  
**Archivos modificados:** `frontend/app/hooks/useMapAnalysisOverlays.ts`

---

## Problema identificado

El mapa del home mostraba overlays (NDVI y textura) de adquisiciones **no aptas** (`unsuitable`), causando visualizaciones con "manchas de nubes" (píxeles enmascarados como NaN).

### Contexto

El fix de nubosidad por parcela (implementado el 17/08/2026) funcionaba correctamente en:
- ✅ Backend (todos los servicios)
- ✅ Dashboard `/cultivos/[id]` (filtraba con `isAnalysisEligible`)
- ✅ SentinelPanel (mostraba estado visual de fechas)

**Pero NO estaba aplicado en:**
- ❌ Home/Mapa (overlays NDVI/textura)

### Causa raíz

El hook `useMapAnalysisOverlays.ts` buscaba el NDVI **más reciente** sin validar `quality_status`:

```typescript
// ANTES (línea 62):
const request = apiClient
  .get<NDVISummary[]>(`/api/ndvi/polygon/${polygonId}`, { params: { limit: 1 } })
  .then(({ data }) => data[0] ?? null);  // ❌ Sin filtro de calidad
```

Esto causaba que:
1. Se mostrara el NDVI más reciente incluso si tenía `quality_status = 'unsuitable'`
2. Los píxeles nublados (correctamente enmascarados como NaN) aparecían como "huecos" en el overlay
3. El usuario veía "colores como nubes" en el mapa

---

## Solución implementada

### 1. Importar función de validación

Se agregó el import de `isAnalysisEligible` que valida:
- `quality_status === 'suitable'`
- `cloud_mask_applied === true`

```typescript
import { isAnalysisEligible } from '@/lib/acquisitionQuality';
```

### 2. Filtrar adquisiciones aptas antes de cargar overlay

Se modificó la función `getLatest` para:
- Aumentar el límite de búsqueda a 100 (suficientes candidatos)
- Filtrar solo adquisiciones aptas
- Retornar la más reciente de las aptas

```typescript
// DESPUÉS (línea 62-69):
const request = apiClient
  .get<NDVISummary[]>(`/api/ndvi/polygon/${polygonId}`, { params: { limit: 100 } })
  .then(({ data }) => {
    // Filtrar solo adquisiciones aptas (suitable + cloud_mask_applied)
    // para evitar mostrar overlays con nubes enmascaradas
    const suitable = data.filter(isAnalysisEligible);
    return suitable[0] ?? null;
  });
```

---

## Resultado

Ahora el mapa del home:
- ✅ Solo muestra overlays de adquisiciones `suitable` con máscara aplicada
- ✅ No muestra "manchas de nubes" (píxeles enmascarados)
- ✅ Es consistente con el comportamiento del dashboard `/cultivos/[id]`
- ✅ Si no hay fechas aptas, simplemente no muestra overlay (comportamiento esperado)

---

## Verificación

Para verificar el fix:

1. **Caso con fechas aptas:**
   - Seleccionar modo overlay (NDVI o Textura) en el mapa
   - El overlay debe mostrarse sin "manchas de nubes"
   - Solo se muestra si existe al menos una adquisición `suitable`

2. **Caso sin fechas aptas:**
   - Parcela con solo adquisiciones `unsuitable` o `caution`
   - No debe mostrarse overlay (spinner desaparece sin error)

3. **Consola del navegador:**
   - No debe haber errores 404 (normal si no hay NDVI aptos)
   - Request a `/api/ndvi/polygon/{id}` debe tener `limit=100`

---

## Relación con trabajo previo

Este fix **completa** la integración del pipeline de calidad de nubes implementado por Fabiana el 17/08/2026:

| Componente | Estado antes | Estado después |
|------------|--------------|----------------|
| Backend | ✅ Completo | ✅ Sin cambios |
| Dashboard `/cultivos/[id]` | ✅ Completo | ✅ Sin cambios |
| SentinelPanel | ✅ Completo | ✅ Sin cambios |
| Home - Overlays | ❌ Sin filtro | ✅ **Fix aplicado** |

---

## Notas técnicas

- **Límite aumentado a 100:** Permite encontrar fechas aptas incluso si las más recientes no lo son
- **Filtro en frontend:** Más simple que modificar el backend (endpoint ya retorna campos necesarios)
- **Sin breaking changes:** El backend ya retornaba `quality_status` y `cloud_mask_applied`
- **Performance:** Mínimo impacto (la query ya estaba optimizada, solo aumentó el límite)

---

## Referencias

- Fix nubosidad parcela: `docs/RESUMEN_MEJORAS_PIPELINE_SENTINEL.md`
- Política de calidad: `docs/CLOUD_QUALITY_AND_NDVI_MASK.md`
- Informe final: `docs/INFORME_FINAL_MEJORAS.md`
- Función de validación: `frontend/lib/acquisitionQuality.ts`
