# SPEC: Overlays Visuales — NDVI y Textura

## Contexto

El backend va a exponer 2 endpoints nuevos que devuelven
imágenes PNG coloreadas + coordenadas de posición. Esta
spec describe cómo integrarlos en el frontend.

## Endpoints que va a proveer el backend

```
GET /api/ndvi/{acquisition_id}/overlay
Response: {
    "image_base64": "data:image/png;base64,...",
    "bounds": [[lat_south, lng_west], [lat_north, lng_east]],
    "metadata": {
        "date": "2026-03-22",
        "thresholds": {"critical": 0.3, "alert": 0.5}
    }
}

GET /api/texture/overlay/{ndvi_result_id}?kernel=contrast
Response: {
    "image_base64": "data:image/png;base64,...",
    "bounds": [[lat_south, lng_west], [lat_north, lng_east]],
    "kernel": "contrast",
    "interpretation": "Campo heterogéneo — se detectan...",
    "metadata": {
        "thresholds_percentiles": [33, 66],
        "date": "2026-03-22"
    }
}
```

## Cache policy

- Primera llamada: backend calcula y guarda en BD
- Siguientes llamadas: backend sirve desde caché (< 100ms)
- Botón "⟳ Recalcular": frontend pasa `?force=true`,
  backend recalcula y actualiza caché

Frontend TAMBIÉN debe cachear en estado local:
- Si ya se pidió overlay para acquisition_id X, no volver
  a pedir al cambiar de tab y volver
- Invalidar caché solo con "Recalcular"

## Nivel 1 — Mapa General

### Comportamiento

Agregar controles tipo Radio + Dropdown encima o al
costado del mapa principal (página cultivos/):

```
[🔘 Ninguno] [⚪ NDVI] [⚪ Textura: [Contraste ▾]]
```

- "Ninguno" (default): Solo polígonos con borde, sin relleno
- "NDVI": Para cada parcela visible, cargar overlay NDVI
  de la ÚLTIMA fecha disponible y mostrarlo como
  ImageOverlay de Leaflet
- "Textura": Igual pero con overlay de textura. Aparece
  dropdown para elegir kernel (Contraste/Bordes/Homogeneidad)

### Reglas
- Solo 1 overlay activo a la vez
- Al cambiar radio, remover overlay anterior y cargar nuevo
- Loading spinner individual por parcela mientras carga
- Si una parcela no tiene datos, mostrarla sin overlay
  (solo borde)

### Leaflet ImageOverlay
```tsx
<ImageOverlay
    url={overlayData.image_base64}
    bounds={overlayData.bounds}
    opacity={0.7}
/>
```

## Nivel 2 — SegmentationPanel.tsx

### Lo que YA existe (mantener):
- Fecha de cálculo
- Umbral usado
- Porcentaje área cultivada

### Lo que se AGREGA:
- Imagen del NDVI coloreado (misma del overlay pero
  mostrada como `<img>` dentro del widget)
- Leyenda: 🟢 Sano (>0.5) | 🟡 Alerta (0.3-0.5) | 🔴 Crítico (<0.3)
- Botón "⟳ Recalcular" (pequeño, esquina)

### Layout sugerido:

```
┌─────────────────────────────────────┐
│ 🌱 Segmentación         ⟳          │
│                                     │
│ 📅 2026-03-22 | Umbral: 0.30       │
│ Área cultivada: 72%                 │
│                                     │
│ ┌─────────────────────────────┐     │
│ │     [Imagen NDVI colores]   │     │
│ │     (aspect ratio 1:1)      │     │
│ └─────────────────────────────┘     │
│                                     │
│ 🟢 Sano  🟡 Alerta  🔴 Crítico     │
└─────────────────────────────────────┘
```

## Nivel 2 — TextureWidget.tsx

### Lo que YA existe (mantener, puede ser colapsable):
- Tabla de descriptores (3 filas × 4 columnas)

### Lo que se AGREGA:
- Texto de interpretación (dinámico, viene del backend)
- Dropdown para seleccionar kernel
- Imagen del heatmap de textura
- Leyenda: 💙 Uniforme | 💜 Moderado | 🧡 Heterogéneo

### Layout sugerido:

```
┌─────────────────────────────────────┐
│ 🔬 Textura                ⟳         │
│                                     │
│ ▸ Tabla detalle (colapsable)        │
│                                     │
│ 💡 "Campo heterogéneo — se detectan │
│    zonas con diferente vigor."      │
│                                     │
│ [Contraste ▾]                       │
│ ┌─────────────────────────────┐     │
│ │    [Imagen textura colores] │     │
│ │    (aspect ratio 1:1)       │     │
│ └─────────────────────────────┘     │
│                                     │
│ 💙 Uniforme 💜 Moderado 🧡 Heterog. │
└─────────────────────────────────────┘
```

## Paleta de colores

### NDVI (salud — semáforo):
- `#dc2626` (rojo) → NDVI < 0.3 (Crítico)
- `#eab308` (amarillo) → 0.3 ≤ NDVI < 0.5 (Alerta)
- `#16a34a` (verde) → NDVI ≥ 0.5 (Sano)
- Fondo transparente donde no hay datos

### Textura (variabilidad — frío/cálido):
- `#3b82f6` (azul) → Percentil 0-33 (Uniforme)
- `#8b5cf6` (púrpura) → Percentil 33-66 (Moderado)
- `#f97316` (naranja) → Percentil 66-100 (Heterogéneo)
- Fondo transparente donde no hay datos

## Estados de UI

- **Loading:** Skeleton/spinner en lugar de la imagen
- **Sin datos:** Texto "No hay datos calculados para
  esta fecha" + sin imagen
- **Error:** Toast con mensaje del backend
- **Cacheado:** Mostrar inmediatamente sin loading

## Notas técnicas

- Las imágenes vienen como base64 PNG con transparencia
- Los bounds permiten posicionar con ImageOverlay de Leaflet
- La opacidad del overlay debe ser ~0.7 para ver el mapa debajo
- En el widget, la imagen se muestra como `<img>` normal
  (no necesita Leaflet)
- El dropdown de kernel en TextureWidget debe sincronizar
  con el dropdown del mapa general (si ambos visibles)
