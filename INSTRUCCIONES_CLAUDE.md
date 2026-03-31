```markdown
# 🎯 INSTRUCCIONES PARA CLAUDE

## LO MÁS IMPORTANTE: Lee esto SIEMPRE antes de ayudarme

Estoy haciendo mi proyecto de grado (PEG) sobre agricultura de precisión con imágenes satelitales.

---

## 📋 MI PROYECTO TIENE 7 OBJETIVOS

**Acuerdate que cada vez que me ayudes, debes decirme a cuál de estos 7 objetivos estamos avanzando:**

1. **OE1** - Descargar imágenes del satélite Sentinel-2
2. **OE2** - Calcular el NDVI (salud de las plantas)
3. **OE3** - Analizar texturas en las imágenes
4. **OE4** - Usar inteligencia artificial para clasificar la salud de los cultivos
5. **OE5** - Detectar nubes y validar si la imagen sirve
6. **OE6** - Crear la interfaz web para que los usuarios vean resultados
7. **OE7** - Validar que todo funciona bien (tests, métricas)

---

## 🚨 REGLAS QUE NUNCA PUEDES ROMPER

### FRONTEND (Next.js)

✅ SIEMPRE usar:
- Next.js con TypeScript
- Tailwind CSS para estilos
- Componentes pequeños y reutilizables (metodología atómica/molecular)
- Nombres de carpetas: components/atoms/, components/molecules/, components/organisms/

❌ JAMÁS usar:
- CSS puro en archivos .css
- HTML plano
- Archivos con más de 200 líneas de código
- Estilos inline complejos (solo className con Tailwind)

**Ejemplo de componente CORRECTO:**

```tsx
// ✅ components/atoms/Button.tsx (PEQUEÑO, reutilizable)
interface ButtonProps {
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary';
}

export default function Button({ label, onClick, variant = 'primary' }: ButtonProps) {
  const baseStyles = "px-4 py-2 rounded-lg font-medium transition-colors";
  const variantStyles = {
    primary: "bg-blue-600 hover:bg-blue-700 text-white",
    secondary: "bg-gray-200 hover:bg-gray-300 text-gray-800"
  };

  return (
    <button 
      onClick={onClick}
      className={`${baseStyles} ${variantStyles[variant]}`}
    >
      {label}
    </button>
  );
}
```

**Ejemplo INCORRECTO:**

```tsx
// ❌ NO HACER ESTO (archivo gigante, estilos mezclados)
export default function MegaComponent() {
  return (
    <div style={{ color: 'red' }}> {/* ❌ estilos inline */}
      {/* 500 líneas de código aquí... */}
    </div>
  );
}
```

### BACKEND (Python/FastAPI)

✅ Estructura que DEBES respetar:

```
backend/app/
  ├── services/        ← Aquí va la LÓGICA (cálculos, algoritmos)
  ├── crud/            ← Aquí va TODO lo de base de datos
  ├── api/endpoints/   ← Aquí van las URLs de la API (super simples)
  └── schemas/         ← Aquí van los modelos de datos (Pydantic)
```

❌ NUNCA mezcles:
- Lógica de negocio en los endpoints
- Queries de base de datos fuera de crud/

**Ejemplo CORRECTO:**

```python
# ✅ backend/app/services/ndvi_service.py
# (Este archivo SOLO hace cálculos, no toca la base de datos)

import numpy as np

class NDVIService:
    def calculate_ndvi(self, red_band: np.ndarray, nir_band: np.ndarray) -> np.ndarray:
        """Calcula NDVI: (NIR - Red) / (NIR + Red)"""
        ndvi = (nir_band - red_band) / (nir_band + red_band + 1e-8)
        return np.clip(ndvi, -1, 1)  # Limita valores entre -1 y 1
```

```python
# ✅ backend/app/api/endpoints/ndvi.py
# (Este archivo SOLO recibe peticiones y orquesta)

from fastapi import APIRouter, Depends
from app.services.ndvi_service import NDVIService

router = APIRouter()

@router.post("/calculate")
async def calculate_ndvi(polygon_id: int):
    service = NDVIService()
    # Llama al servicio, no hace la lógica aquí
    result = service.calculate_ndvi(...)
    return {"ndvi": result}
```

---

## 🗂️ ESTRUCTURA DE COMPONENTES FRONTEND (Metodología Molecular)

```
frontend/app/components/
├── atoms/              ← Componentes MUY pequeños (botones, inputs, iconos)
│   ├── Button.tsx
│   ├── Input.tsx
│   └── Badge.tsx
│
├── molecules/          ← Combinación de 2-3 atoms (formularios simples, cards)
│   ├── FormField.tsx   (Input + Label)
│   ├── PolygonCard.tsx (Badge + Button + texto)
│   └── DateRangePicker.tsx
│
└── organisms/          ← Componentes completos (navbar, sidebar, tablas)
    ├── MapViewer.tsx
    ├── PolygonList.tsx
    └── NDVIChart.tsx
```

**Regla de oro:** Si un componente tiene más de 150 líneas, divídelo en partes más pequeñas.

---

## 💬 CÓMO AYUDARME EN CADA RESPUESTA

Cada vez que me des código, SIEMPRE incluye:

1. **A qué objetivo avanzamos:** "Esto es para OE2 (calcular NDVI)"
2. **Dónde va el archivo:** "Crear en `backend/app/services/ndvi_service.py`"
3. **Qué hace:** Explicación en español simple
4. **Próximo paso:** Qué debería hacer después

**Ejemplo de respuesta perfecta:**

```
🎯 Estamos trabajando en: OE2 (Procesamiento - Cálculo NDVI)

📁 Archivo a crear: backend/app/services/ndvi_service.py

📝 ¿Qué hace este código?
Recibe dos imágenes (banda roja y banda infrarroja) y calcula
el índice de vegetación NDVI que nos dice qué tan sana está la planta.

[CÓDIGO AQUÍ]

✅ Próximo paso:
Ahora necesitas crear el endpoint en api/endpoints/ndvi.py para
que el frontend pueda llamar a este servicio.
¿Quieres que lo genere?
```

---

## 🔍 PREGUNTAS QUE DEBES HACERME ANTES DE GENERAR CÓDIGO

Si no estoy siendo claro en mi petición, pregúntame:

1. ¿Para qué objetivo específico es esto? (OE1-OE7)
2. ¿Va en frontend o backend?
3. ¿Es un componente nuevo o modificamos uno existente?
4. ¿Necesitas que te explique algo antes de empezar?

---

## 📦 COMANDOS RÁPIDOS (Para que copies y pegues)

Cuando me escribas, usa estos atajos:

- `@ESTADO` → Muéstrame qué objetivos están completos y cuáles faltan
- `@SIGUIENTE` → Dime qué debería hacer ahora (prioridad)
- `@COMPONENTE [nombre]` → Crea un componente frontend nuevo
- `@SERVICIO [nombre]` → Crea un servicio backend nuevo
- `@EXPLICAR [tema]` → Explícame algo que no entiendo

---

## 📊 ESTADO ACTUAL DEL PROYECTO

### ✅ OE1: Servicio de Adquisición Sentinel-2
**Estado:** IMPLEMENTADO EN NOTEBOOKS
- ✓ Autenticación OAuth2 Copernicus DataSpace
- ✓ Descarga por polígono + rango temporal
- ✓ Nivel L2A (bandas B04/B08)
- 🔧 PENDIENTE: Migrar lógica a `backend/app/services/sentinel_service.py`
- 🔧 PENDIENTE: Endpoint API `/api/sentinel/download`

### 🟡 OE2: Servicio de Procesamiento (Índices + Segmentación)
**Estado:** PARCIAL
- ✓ Cálculo NDVI en notebook 02
- ✓ Máscara vegetación (NDVI > 0.3)
- 🔧 PENDIENTE: Servicio de cálculo persistente
- 🔧 PENDIENTE: Almacenar resultados en DB (nueva tabla `ndvi_analysis`)
- 🔧 PENDIENTE: API REST para solicitar procesamiento

### 🟡 OE3: Análisis Espacial (Filtrado Convolucional)
**Estado:** PARCIAL
- ✓ Prototipo de filtro en notebook 02
- 🔧 PENDIENTE: Servicio de extracción de características
- 🔧 PENDIENTE: Pipeline automatizado feature → DB

### 🟡 OE4: Modelo IA de Clasificación
**Estado:** EN DESARROLLO
- ✓ U-Net implementada (notebook 01 sintético)
- ✓ Pipeline clasificación salud (Critical/Alert/Healthy)
- 🔧 PENDIENTE: Entrenar con datos reales
- 🔧 PENDIENTE: Servicio de inferencia (`backend/app/services/ml_service.py`)
- 🔧 PENDIENTE: Guardar modelos en `backend/models/trained/`

### ❌ OE5: Evaluación Calidad (Nubosidad)
**Estado:** NO INICIADO
- 🔧 PENDIENTE: Servicio de detección de nubes
- 🔧 PENDIENTE: Score de confiabilidad
- 🔧 PENDIENTE: Selección automática fechas alternativas

### 🟢 OE6: Interfaz de Usuario
**Estado:** BASE IMPLEMENTADA
- ✓ Mapa Leaflet con dibujo de polígonos
- ✓ Gestión de parcelas (CRUD)
- ✓ Next.js + TypeScript
- 🔧 PENDIENTE: Vista de resultados NDVI
- 🔧 PENDIENTE: Comparación temporal
- 🔧 PENDIENTE: Exportación de resultados
- 🔧 PENDIENTE: Refactorizar componentes existentes a metodología molecular

### ❌ OE7: Validación
**Estado:** NO INICIADO
- 🔧 PENDIENTE: Métricas cuantitativas (IoU, Dice ya en notebook)
- 🔧 PENDIENTE: Análisis coherencia espacial
- 🔧 PENDIENTE: Evaluación consistencia temporal

---

## 🚦 PRÓXIMOS HITOS CRÍTICOS (Orden de prioridad)

### SPRINT 1: Cerrar OE1 (Adquisición)

Crear: `backend/app/services/sentinel_service.py`

```python
class SentinelService:
    async def download_imagery(polygon_id, start_date, end_date)
    async def authenticate()
    async def check_availability()
```

**Endpoint:** `POST /api/sentinel/download`
**Tests:** `tests/test_sentinel_service.py`

### SPRINT 2: Cerrar OE2 (Procesamiento)

Crear: `backend/app/services/ndvi_service.py`

```python
class NDVIService:
    async def calculate_ndvi(imagery_id)
    async def segment_vegetation(ndvi_raster)
    async def store_results(polygon_id, ndvi_data)
```

**Nueva tabla DB:**

```python
# backend/app/models/ndvi_analysis.py
class NDVIAnalysis(SQLModel, table=True):
    id: int
    polygon_id: int  # FK a Polygon
    date: datetime
    ndvi_raster: bytes  # GeoTIFF comprimido
    vegetation_mask: bytes
    avg_ndvi: float
```

### SPRINT 3: Integrar OE4 (IA)
- Entrenar U-Net con datos reales
- Crear `ml_service.py` con inferencia
- Endpoint de clasificación

### SPRINT 4: Completar OE6 (UI)
- Refactorizar componentes existentes a metodología molecular
- Componente visualización NDVI
- Timeline comparación temporal
- Exportación GeoTIFF/PNG

---

## 📐 DECISIONES ARQUITECTÓNICAS CLAVE

### Procesamiento de imágenes
- **Almacenamiento:** PostgreSQL con bytea (< 10MB) o S3 (> 10MB)
- **Formato interno:** GeoTIFF comprimido (LZW)
- **Coordenadas:** Siempre WGS84 (EPSG:4326)

### Machine Learning
- **Framework:** TensorFlow (ya en requirements)
- **Modelo productivo:** Formato SavedModel en `backend/models/trained/`
- **Versionado:** MLflow (a implementar en OE7)

### API de resultados

```typescript
// Ejemplo respuesta /api/analysis/{polygon_id}
{
  "polygon_id": 123,
  "date": "2024-01-15",
  "ndvi_stats": {
    "mean": 0.65,
    "std": 0.12,
    "vegetated_area_m2": 15000
  },
  "health_classification": {
    "critical_pct": 5,
    "alert_pct": 20,
    "healthy_pct": 75
  },
  "quality_score": 0.92,  // OE5
  "download_urls": {
    "ndvi_map": "/static/ndvi_123_2024-01-15.tif",
    "health_map": "/static/health_123_2024-01-15.png"
  }
}
```

---

## 🧪 CRITERIOS DE VALIDACIÓN (OE7)

### Métricas cuantitativas
- IoU segmentación > 0.75
- Dice coefficient > 0.80
- Accuracy clasificación > 85%

### Coherencia espacial
- No fragmentación excesiva (filtro morfológico)
- Continuidad geométrica en parcelas contiguas

### Consistencia temporal
- Variación NDVI < 0.15 entre días consecutivos (sin eventos climáticos)
- Tendencias coherentes con estacionalidad

---

## 🔍 DEBUGGING COMÚN

### Error: Coordenadas invertidas

```python
# ❌ Incorrecto
coords = [[lat, lon], ...]  

# ✅ Correcto (GeoJSON spec)
coords = [[lon, lat], ...]
```

### Error: NDVI fuera de rango

```python
# Validar siempre
assert -1 <= ndvi.mean() <= 1, "NDVI calculation error"
```

### Error: Async/Await en servicios

```python
# ✅ Correcto
async with AsyncSession(engine) as session:
    result = await session.execute(query)

# ❌ Incorrecto
session = SessionLocal()  # Sync session
```

---

## 📚 RECURSOS DE REFERENCIA

- [Sentinel-2 User Handbook](https://sentinel.esa.int/web/sentinel/user-guides/sentinel-2-msi)
- [NDVI Theory](https://custom-scripts.sentinel-hub.com/custom-scripts/sentinel-2/ndvi/)
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)
- U-Net Paper: Ronneberger et al. (2015)
- [Atomic Design Methodology](https://bradfrost.com/blog/post/atomic-web-design/)

---

## 🎓 CONTEXTO ACADÉMICO PEG

**Universidad:** [Tu Universidad]
**Tutor:** [Nombre del Tutor]
**Fecha defensa estimada:** [Fecha]

**Entregables clave:**
1. Código fuente completo (GitHub)
2. Documentación técnica
3. Manual de usuario
4. Dataset validación + resultados
5. Presentación defensa

---

## 💡 EJEMPLOS DE USO

### Ejemplo 1: Solicitar componente frontend

**Usuario escribe:**
```
Necesito un botón para descargar imágenes satelitales
```

**Claude debe responder:**
```
🎯 Objetivo: OE6 (Interfaz de usuario)

📁 Crear archivo: frontend/app/components/atoms/DownloadButton.tsx

📝 Este botón será reutilizable para cualquier descarga.
Usa Tailwind con efecto hover y un ícono.

[CÓDIGO DEL COMPONENTE]

✅ Próximo paso:
¿Quieres que cree un componente "molecule" que combine
este botón con un selector de fechas?
```

### Ejemplo 2: Solicitar lógica backend

**Usuario escribe:**
```
Necesito calcular el NDVI de una parcela
```

**Claude debe responder:**
```
🎯 Objetivo: OE2 (Procesamiento - Cálculo NDVI)

📁 Crear archivos:
1. backend/app/services/ndvi_service.py (la lógica)
2. backend/app/api/endpoints/ndvi.py (el endpoint)

📝 ¿Qué hace?
El servicio recibe las bandas Red y NIR del satélite,
calcula (NIR - Red)/(NIR + Red) y devuelve un número
entre -1 y 1 que indica salud de la planta.

[CÓDIGO SERVICIO]
[CÓDIGO ENDPOINT]

✅ Próximo paso:
Ahora deberías crear un componente en el frontend que
llame a este endpoint y muestre el resultado en un mapa.
¿Lo genero?
```

### Ejemplo 3: Comando @ESTADO

**Usuario escribe:**
```
@ESTADO
```

**Claude debe responder:**
```
📊 ESTADO DE TU PEG

✅ OE1: Adquisición Sentinel-2 → 70% (falta crear endpoint API)
✅ OE6: Interfaz → 40% (tienes mapa, falta vista de resultados)
❌ OE2: Cálculo NDVI → 0%
❌ OE3: Análisis texturas → 0%
❌ OE4: IA → 10% (solo tienes el notebook)
❌ OE5: Detección nubes → 0%
❌ OE7: Validación → 0%

💡 Recomendación: Enfócate en completar OE1 (casi listo)
   luego continúa con OE2 que es crítico para tu proyecto.
```

---

## ✅ CHECKLIST ANTES DE CADA RESPUESTA

Antes de dar cualquier respuesta, verifica:

- [ ] ¿Indiqué a qué OE pertenece esta tarea?
- [ ] ¿Especifiqué la ruta exacta del archivo?
- [ ] ¿Usé Tailwind en componentes frontend? (NO CSS)
- [ ] ¿Dividí el componente si tiene más de 150 líneas?
- [ ] ¿Separé lógica en services/ si es backend?
- [ ] ¿Expliqué en español qué hace el código?
- [ ] ¿Sugerí el próximo paso lógico?
