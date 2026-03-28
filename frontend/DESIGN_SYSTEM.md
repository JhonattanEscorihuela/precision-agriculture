# Sistema de Diseño - Agricultura de Precisión

## 🎨 Filosofía de Diseño

Este sistema de diseño está inspirado en:
- **Análisis satelital NDVI**: Colores que reflejan la salud de cultivos
- **Tecnología espacial**: Efectos de escaneo y líneas satelitales
- **Cartografía**: Patrones topográficos y curvas de nivel
- **Datos científicos**: Tipografía monoespaciada para precisión numérica

---

## 🌈 Paleta de Colores

### Colores Primarios

```css
/* Suelo y Tierra */
--earth-dark: #2C1810;
--earth-medium: #5D4E37;

/* Vegetación (basado en NDVI) */
--vegetation-critical: #DC2626;  /* NDVI < 0.3 - Cultivo crítico */
--vegetation-alert: #F59E0B;     /* NDVI 0.3-0.6 - Alerta */
--vegetation-healthy: #10B981;   /* NDVI > 0.6 - Sano */
--vegetation-vibrant: #34D399;   /* NDVI > 0.7 - Óptimo */

/* Tecnología Satelital */
--satellite-blue: #0EA5E9;       /* Cielo/Agua/Tech */
--satellite-deep: #1E3A8A;       /* Espacio/Profundidad */
--satellite-darker: #0C1F47;     /* Fondo oscuro */

/* Datos e IA */
--data-accent: #8B5CF6;          /* Análisis */
--data-purple: #6366F1;          /* IA/ML */
```

### Gradientes

```css
--gradient-earth: linear-gradient(135deg, #2C1810 0%, #5D4E37 100%);
--gradient-health: linear-gradient(135deg, #10B981 0%, #34D399 100%);
--gradient-sky: linear-gradient(180deg, #0EA5E9 0%, #1E3A8A 100%);
--gradient-data: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
--gradient-sidebar: linear-gradient(135deg, #1E3A8A 0%, #0C1F47 100%);
```

---

## 🔤 Tipografía

### Fuentes

- **Texto general**: `Inter` - Moderna, legible, profesional
- **Datos numéricos**: `JetBrains Mono` - Monoespaciada, ideal para coordenadas y métricas

### Uso

```tsx
// Texto normal
<p className="text-base">Texto general</p>

// Datos numéricos (coordenadas, áreas, conteos)
<span className="data-text">123.456789</span>
```

---

## 🎭 Efectos Visuales

### 1. Scan Lines Satelitales

Efecto de líneas de escaneo como imágenes satelitales:

```css
.sidebar-scanlines {
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(14, 165, 233, 0.03) 2px,
        rgba(14, 165, 233, 0.03) 4px
    );
}
```

**Uso**: Fondos del sidebar, overlays técnicos

### 2. Patrón Topográfico

Simula curvas de nivel en mapas topográficos:

```css
.topo-pattern {
    background-image: repeating-radial-gradient(
        circle at 30% 30%,
        transparent 0,
        transparent 40px,
        rgba(16, 185, 129, 0.04) 40px,
        rgba(16, 185, 129, 0.04) 41px
    );
    animation: topoShift 20s linear infinite;
}
```

**Uso**: Fondos de cards de cultivos, fondos decorativos

### 3. Glassmorphism

Efecto de vidrio esmerilado para overlays:

```css
.glass-effect {
    background: rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(12px) saturate(180%);
    border: 1px solid rgba(255, 255, 255, 0.2);
}

.glass-effect-green {
    background: rgba(16, 185, 129, 0.08);
    backdrop-filter: blur(12px) saturate(180%);
    border: 1px solid rgba(16, 185, 129, 0.2);
}
```

**Uso**: Overlays de información, tooltips, modales

### 4. Glow Effects

Resplandor para elementos importantes:

```css
box-shadow: 0 0 20px rgba(14, 165, 233, 0.3);
```

**Uso**: Botones activos, indicadores de estado, hover states

---

## 🎬 Animaciones

### Satellite Pass

Animación de paso de satélite (ideal para loading):

```css
@keyframes satellitePass {
    0% {
        transform: translateX(-100%) translateY(-100%) rotate(45deg);
        opacity: 0;
    }
    50% { opacity: 1; }
    100% {
        transform: translateX(100%) translateY(100%) rotate(45deg);
        opacity: 0;
    }
}
```

### Topographic Shift

Movimiento sutil de patrones topográficos:

```css
@keyframes topoShift {
    0% { transform: translate(0, 0) rotate(0deg); }
    100% { transform: translate(10px, 10px) rotate(360deg); }
}
```

### Pulse Glow

Pulsación suave para indicadores:

```css
@keyframes pulseGlow {
    0%, 100% {
        opacity: 1;
        transform: scale(1);
    }
    50% {
        opacity: 0.7;
        transform: scale(1.05);
    }
}
```

### Slide In Right

Entrada desde la izquierda:

```css
@keyframes slideInRight {
    from {
        transform: translateX(-20px);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}
```

---

## 🧩 Componentes

### Botones

#### Primario (Acción principal)

```tsx
<button className="btn-primary">
    <span>Texto del botón</span>
    <span className="btn-arrow">→</span>
</button>
```

**Estilos**:
- Fondo: `var(--gradient-health)`
- Hover: Elevación + glow verde
- Transición suave del icono de flecha

#### Secundario (Acción alternativa)

```tsx
<button className="btn-secondary">
    <span>Texto del botón</span>
    <span className="btn-arrow">→</span>
</button>
```

**Estilos**:
- Fondo: Semi-transparente azul
- Border: Azul satelital
- Hover: Intensificación de color

### Cards

#### Card de Cultivo

```tsx
<div className="crop-card healthy">
    <div className="topo-pattern" />
    <div className="health-indicator health-healthy">
        <div className="health-pulse" />
        <span className="health-icon">✓</span>
    </div>
    {/* Contenido */}
</div>
```

**Estados**:
- `.healthy` - Verde (NDVI alto)
- `.alert` - Amarillo (NDVI medio)
- `.critical` - Rojo (NDVI bajo)

### Indicadores de Salud

```tsx
<div className="health-indicator health-healthy">
    <div className="health-pulse" />
    <span className="health-icon">✓</span>
</div>
```

**Variantes**:
- `health-healthy` - Verde con ✓
- `health-alert` - Amarillo con ⚠
- `health-critical` - Rojo con !

---

## 📊 Sombras

```css
--shadow-sm: 0 2px 8px rgba(30, 58, 138, 0.08);
--shadow-md: 0 4px 16px rgba(30, 58, 138, 0.12);
--shadow-lg: 0 8px 32px rgba(30, 58, 138, 0.16);
--shadow-glow-green: 0 0 20px rgba(16, 185, 129, 0.3);
--shadow-glow-blue: 0 0 20px rgba(14, 165, 233, 0.3);
```

**Uso**:
- `shadow-sm`: Cards, elementos ligeros
- `shadow-md`: Botones, navegación
- `shadow-lg`: Modales, overlays importantes
- `shadow-glow-*`: Estados activos, hover

---

## 📱 Responsive

### Breakpoints

- **Mobile**: < 768px
- **Tablet**: 768px - 1024px
- **Desktop**: > 1024px

### Patrones Responsive

```css
@media (max-width: 768px) {
    .sidebar-container {
        width: 100%;
        height: auto;
    }

    .main-content {
        padding: 1rem;
    }

    .crops-grid {
        grid-template-columns: 1fr;
    }
}
```

---

## ♿ Accesibilidad

- **Contraste**: Todos los colores cumplen WCAG AA
- **Focus states**: Bordes visibles en elementos interactivos
- **Keyboard navigation**: Todos los elementos interactivos son accesibles por teclado
- **ARIA labels**: Implementar en elementos visuales importantes

---

## 🚀 Best Practices

1. **Consistencia**: Usar siempre las variables CSS en lugar de valores hardcodeados
2. **Performance**: Usar `transform` y `opacity` para animaciones (GPU accelerated)
3. **Semántica**: Nombres de clases descriptivos y basados en función
4. **Modularidad**: Componentes reutilizables con props flexibles
5. **Documentación**: Comentar efectos complejos y decisiones de diseño

---

## 🎯 Ejemplos de Uso

### Card con efecto topográfico

```tsx
<div className="crop-card">
    <div className="topo-pattern" />
    {/* Contenido */}
</div>
```

### Botón con glow en hover

```tsx
<button style={{
    background: 'var(--gradient-health)',
    transition: 'all 0.3s ease'
}} onMouseEnter={(e) => {
    e.currentTarget.style.boxShadow = 'var(--shadow-glow-green)';
}}>
    Acción
</button>
```

### Indicador de loading satelital

```tsx
import LoadingIndicator from '@/app/components/LoadingIndicator';

<LoadingIndicator text="Cargando datos..." size="lg" />
```

---

## 📚 Recursos

- [Inter Font](https://fonts.google.com/specimen/Inter)
- [JetBrains Mono](https://fonts.google.com/specimen/JetBrains+Mono)
- [Leaflet Documentation](https://leafletjs.com/)
- [Next.js Styling](https://nextjs.org/docs/app/building-your-application/styling)
