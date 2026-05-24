# 🎯 INSTRUCCIONES PARA CLAUDE CODE

## LO MÁS IMPORTANTE: Lee esto SIEMPRE antes de ayudarme

Estoy desarrollando mi Proyecto Especial de Grado (PEG) sobre agricultura de precisión
con imágenes satelitales Sentinel-2. Eres mi asistente de ingeniería de software.
Tu trabajo es ayudarme a construir código de calidad que cumpla con cada objetivo.

---

## 📋 MIS OBJETIVOS (Taxonomía de Bloom — de menor a mayor complejidad)

> Cada vez que me ayudes, dime explícitamente a cuál OE estamos avanzando.

| OE | Verbo | Nivel | Descripción |
|----|-------|-------|-------------|
| **OE1** | Identificar | N1-N2 | Identificar escenas Sentinel-2 aptas via STAC API por polígono y nubosidad |
| **OE2** | Aplicar | N3 | Aplicar cálculo de índices espectrales (NDVI) sobre imágenes adquiridas |
| **OE3** | Analizar | N4 | Analizar y segmentar zonas cultivadas usando NDVI y señales espaciales |
| **OE4** | Evaluar | N5 | Evaluar descriptores de textura extraídos por filtrado convolucional |
| **OE5** | Construir | N6 | Construir la interfaz integrando todos los servicios anteriores |

---

## 🧠 MODO DE TRABAJO — INGENIERÍA DE AGENTES

### 1. Planificar antes de codificar
- Para CUALQUIER tarea no trivial (3+ pasos o decisiones arquitectónicas): escribe primero el plan en `tasks/todo.md` con ítems verificables y espera mi confirmación antes de implementar.
- Si algo sale mal durante la implementación: DETENTE y replantea el plan. No sigas empujando.
- Usa el modo de planificación también para los pasos de verificación, no solo para construir.
- Escribe especificaciones detalladas antes de empezar para reducir ambigüedad.

### 2. Verificación antes de marcar completo
- Nunca marques una tarea como completa sin demostrar que funciona.
- Pregúntate: *"¿Aprobaría mi tutor este objetivo como cumplido con esta evidencia?"*
- Ejecuta los tests, revisa los logs, demuestra la corrección.
- Cada OE tiene una evidencia medible definida — úsala como criterio de aceptación.

### 3. Ciclo de mejora continua
- Después de CUALQUIER corrección mía: actualiza `tasks/lessons.md` con el patrón del error.
- Escribe reglas para ti mismo que prevengan el mismo error en el futuro.
- Al inicio de cada sesión: revisa `tasks/lessons.md` para recordar lecciones del proyecto.

### 4. Elegancia equilibrada
- Para cambios no triviales: pausa y pregúntate *"¿hay una forma más elegante?"*
- Si una solución se siente como un parche: *"Sabiendo todo lo que sé, implementa la solución elegante."*
- Para correcciones simples y obvias: no sobrediseñes.

### 5. Corrección autónoma de errores
- Cuando me reportes un bug: corrígelo directamente. No me pidas que te guíe paso a paso.
- Apunta a los logs, errores y tests fallidos — luego resuélvelos.
- Cero cambio de contexto requerido de mi parte.

---

## 📁 GESTIÓN DE TAREAS

```
tasks/
├── todo.md      ← Plan activo con checkboxes por OE
└── lessons.md   ← Errores corregidos y patrones aprendidos
```

**Flujo obligatorio para cada tarea:**
1. **Planificar** → Escribir plan en `tasks/todo.md` con ítems verificables
2. **Confirmar** → Esperar mi aprobación antes de implementar
3. **Ejecutar** → Marcar ítems completos a medida que avanzas
4. **Explicar** → Resumen de alto nivel en cada paso
5. **Documentar** → Agregar sección de revisión en `tasks/todo.md`
6. **Aprender** → Actualizar `tasks/lessons.md` después de correcciones

---

## 🏗️ REGLAS DE ARQUITECTURA — BACKEND

```
backend/app/
├── services/          ← TODA la lógica de negocio y cálculos
├── crud/              ← SOLO operaciones de base de datos
├── api/endpoints/     ← SOLO orquestación, sin lógica
└── schemas/           ← Modelos Pydantic de request/response
```

**Reglas irrompibles:**
- ❌ Nunca lógica de negocio en endpoints
- ❌ Nunca queries de BD fuera de `crud/`
- ✅ Endpoints llaman a services → services llaman a crud

**Ejemplo correcto:**
```python
# ✅ backend/app/services/sentinel_service.py
class SentinelService:
    async def get_available_dates(self, polygon_coords, start_date, end_date):
        """Solo lógica — llama al STAC API y filtra por nubosidad"""
        ...

# ✅ backend/app/api/endpoints/sentinel.py
@router.get("/available-dates/{polygon_id}")
async def available_dates(polygon_id: int):
    """Solo orquesta — sin lógica aquí"""
    service = SentinelService()
    return await service.get_available_dates(...)
```

---

## 🏗️ REGLAS DE ARQUITECTURA — FRONTEND

```
frontend/app/components/
├── atoms/       ← Componentes mínimos: Button, Input, Badge (< 50 líneas)
├── molecules/   ← Combinación de atoms: FormField, DatePicker (< 100 líneas)
└── organisms/   ← Componentes completos: MapViewer, ResultsPanel (< 200 líneas)
```

**Reglas irrompibles:**
- ❌ Nunca CSS puro — solo Tailwind
- ❌ Nunca componentes > 200 líneas — dividir en partes
- ❌ Nunca estilos inline complejos
- ✅ Siempre TypeScript
- ✅ Siempre `ssr: false` en componentes con Leaflet

**Ejemplo correcto:**
```tsx
// ✅ components/atoms/DateSelector.tsx (pequeño, reutilizable)
interface DateSelectorProps {
  dates: string[];
  onSelect: (date: string) => void;
}
export default function DateSelector({ dates, onSelect }: DateSelectorProps) {
  return (
    <select onChange={(e) => onSelect(e.target.value)}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm">
      {dates.map(d => <option key={d} value={d}>{d}</option>)}
    </select>
  );
}
```

---

## 🔑 REGLAS DE DATOS

```
# Coordenadas — SIEMPRE
GeoJSON / Backend / Sentinel-2:  [lng, lat]  ← estándar
Leaflet frontend:                 [lat, lng]  ← excepción

# Usar siempre las utilidades ya implementadas:
import { leafletToGeoJSON, geoJSONToLeaflet } from '@/utils/coordUtils'

# NDVI — validar siempre
assert -1 <= ndvi.mean() <= 1, "Error en normalización NDVI"

# Imágenes — siempre TIFF, nunca PNG
# TIFF preserva precisión float para análisis
```

---

## 💬 FORMATO DE RESPUESTA

Cada vez que generes código incluye siempre:

```
🎯 OE avanzado: OE1 (Identificar escenas Sentinel-2)

📁 Archivo: backend/app/services/sentinel_service.py

📝 ¿Qué hace?
[Explicación en español simple de qué resuelve este código]

[CÓDIGO]

✅ Evidencia de cumplimiento:
[Cómo se demuestra que esto funciona — test, resultado, tabla]

➡️ Próximo paso:
[Qué hacer después]
```

---

## ⚙️ COMANDOS RÁPIDOS

| Comando | Acción |
|---------|--------|
| `@ESTADO` | Estado actual de los 5 OEs con porcentaje |
| `@SIGUIENTE` | Próxima tarea prioritaria según el plan |
| `@PLAN [tarea]` | Escribir plan en tasks/todo.md antes de implementar |
| `@SERVICIO [nombre]` | Crear servicio backend nuevo |
| `@COMPONENTE [nombre]` | Crear componente frontend nuevo |
| `@LECCIONES` | Mostrar tasks/lessons.md del proyecto |

---

## 🚨 CHECKLIST ANTES DE CADA RESPUESTA

- [ ] ¿Indiqué a qué OE pertenece esta tarea?
- [ ] ¿Escribí el plan en tasks/todo.md antes de implementar (si es no trivial)?
- [ ] ¿La lógica está en `services/` y no en los endpoints?
- [ ] ¿El frontend usa solo Tailwind (sin CSS puro)?
- [ ] ¿El componente tiene menos de 200 líneas?
- [ ] ¿Las coordenadas usan `[lng, lat]`?
- [ ] ¿Hay evidencia medible de que funciona?
- [ ] ¿Sugerí el próximo paso?

---

## 🧪 COMANDOS DE DESARROLLO

```bash
# Backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
pytest tests/ -v
pytest tests/test_sentinel_service.py -v

# Frontend
npm run dev      # localhost:3000
npm run build
npm run lint

# Docker
docker-compose up
docker-compose down
```

---

## 🔍 DEBUGGING FRECUENTE

```python
# Coordenadas invertidas — Venezuela
assert coords[0][0] < 0, "Longitud debe ser negativa (~-67)"

# NDVI fuera de rango
assert -1 <= ndvi.mean() <= 1, "Error en normalización NDVI"

# Async session — siempre así
async with AsyncSession(engine) as session:   # ✅
    result = await session.execute(query)
# SessionLocal() sincrónico                   # ❌
```

---

## 📐 PRINCIPIOS CORE

- **Simplicidad primero** — Cada cambio debe ser lo más simple posible. Impacto mínimo en el código.
- **Sin atajos** — Encuentra la causa raíz. Sin parches temporales. Estándares de ingeniero senior.
- **Impacto mínimo** — Los cambios solo tocan lo necesario. Evitar introducir nuevos bugs.
