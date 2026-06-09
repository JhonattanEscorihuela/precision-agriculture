# Changelog - 2026-06-09

## 🐛 Fixes Críticos

### 1. Estado de salud incorrecto en /cultivos
**Problema:** Lista mostraba "crítico" (rojo) pero dashboard individual mostraba "saludable" (verde).

**Root cause:** Query NDVI ordenaba `.asc()` (ascendente) pero con `limit=1` debía ordenar `.desc()` para obtener el valor más reciente.

**Fix:** `backend/app/crud/ndvi.py:130`
```python
# Antes: .order_by(SentinelAcquisition.acquisition_date.asc())
# Después: .order_by(SentinelAcquisition.acquisition_date.desc())
```

**Impacto:** Ahora el estado de salud en `/cultivos` refleja correctamente el último NDVI calculado (fecha más reciente).

**Ajustes frontend necesarios por cambio de orden:**
```typescript
// NDVIEvolutionWidget.tsx:182
// Antes: data[data.length - 1] (último índice)
// Después: data[0] (primer elemento, ahora es el más reciente por DESC)

// NDVIEvolutionWidget.tsx:186
// Agregado: [...data].reverse() antes de map
// Razón: Recharts necesita orden cronológico ASC (antiguo→reciente izq→der)
```

**Lógica final:**
- `/cultivos` muestra estado basado en último NDVI disponible (hoy o más cercano)
- Dashboard muestra evolución temporal en rango filtrado
- Ambos usan `ndvi_mean` consistentemente
- "Estado Actual" siempre refleja el valor más reciente

---

## 🧹 Limpieza de Código

### Frontend
**Eliminados:**
- 15+ console.log de debugging en producción
- Componentes vacíos: `PolygonDrawer.tsx`, `ConfigForm.tsx`
- Logs redundantes en `NDVIEvolutionWidget.tsx`
- Logs de render check en `SentinelPanel.tsx`

**Mantenidos:**
- `console.error` en catch blocks (útiles para debugging producción)
- Comentarios relevantes de arquitectura

### Tasks/
**Eliminados (7 archivos temporales):**
- `RESUMEN_EJECUTIVO_OE1.txt`
- `datos_para_reporte_word.txt`
- `generate_oe1_table.py`
- `resumen_componentes_oe1.md`
- `tabla_disponibilidad_oe1.csv`
- `docker_fix_summary.md`
- `oe1_frontend_complete.md`
- `oe2_plan.md`

**Mantenidos:**
- `lessons.md` - Documentación activa de errores/patrones
- `todo.md` - Plan de trabajo activo
- `DOCKER_VALIDATION.md` - Guía de validación
- `OE1_RESUMEN_FINAL.md`, `OE2_RESUMEN_FINAL.md` - Evidencia de completitud

---

## 📊 Impacto

**Performance:**
- Logs más limpios → debugging más rápido
- Menos ruido en consola del navegador
- Build ligeramente más rápido (componentes vacíos eliminados)

**Mantenibilidad:**
- Código más limpio y profesional
- Menos distracciones para futuros desarrolladores
- Documentación consolidada en `lessons.md`

---

## ✅ Testing

**Manual:**
1. Ingresar a `/cultivos` → verificar que estado coincide con último NDVI
2. Abrir dashboard individual → verificar consistencia
3. Verificar consola del navegador → sin logs de debug
4. Verificar logs backend → solo errores críticos

**Resultado:** ✅ Todas las verificaciones pasaron

---

## 📝 Lección Aprendida

**Agregar a tests de integración:**
```python
@pytest.mark.integration
async def test_latest_ndvi_uses_desc_order():
    """Verificar que limit=1 retorna el NDVI más reciente."""
    response = await client.get("/api/ndvi/polygon/1?limit=1")
    latest = response.json()[0]
    
    # Verificar que es el más reciente
    all_response = await client.get("/api/ndvi/polygon/1?limit=100")
    all_ndvis = all_response.json()
    assert latest["acquisition_date"] == max(n["acquisition_date"] for n in all_ndvis)
```

**REGLA:** Queries con ORDER BY + LIMIT siempre verificar dirección del ordenamiento según caso de uso.

---

## ⚠️ Meta-Lección: No Seguir las Propias Lecciones

**Error cometido en este fix:**
- Hice `docker-compose restart frontend` en lugar de `down && up --build`
- Esta lección (#1 de OE2) YA estaba documentada en `lessons.md`
- No la apliqué → usuario tuvo que recordármela

**Por qué pasó:**
- Olvidé revisar lessons.md antes de hacer el fix
- Asumí que `restart` era suficiente para cambios pequeños
- Next.js/Turbopack tiene caché agresivo que restart NO limpia

**Solución para no repetir:**
- **SIEMPRE revisar `lessons.md` antes de hacer fixes similares**
- **SIEMPRE `down && up --build` para cambios frontend, sin excepciones**
- Agregar recordatorio en prompt de sistema si es posible

**Impacto de no seguir la lección:**
- Usuario ve cambios parcialmente aplicados
- Frustración por "no funciona" cuando el código está correcto
- Tiempo perdido en debugging innecesario
