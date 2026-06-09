/**
 * OE2 - Badge NDVI con color según rango de vegetación.
 * Atom component (< 50 líneas)
 */

interface NDVIBadgeProps {
  value: number; // NDVI value in [-1, 1]
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

/**
 * Badge que muestra valor NDVI con color según estado de salud del cultivo.
 *
 * Clasificación unificada (igual que usePolygonHealth):
 * < 0.3  → Rojo crítico (vegetación escasa/estrés severo)
 * 0.3-0.5 → Amarillo alert (vegetación moderada/revisar)
 * ≥ 0.5  → Verde saludable (vegetación óptima)
 */
export default function NDVIBadge({ value, size = 'md', showLabel = true }: NDVIBadgeProps) {
  // Determinar color según estado de salud (UNIFICADO con usePolygonHealth)
  const getColor = (ndvi: number): string => {
    if (ndvi < 0.3) return 'bg-vegetation-critical text-white'; // Rojo crítico
    if (ndvi < 0.5) return 'bg-vegetation-alert text-white'; // Amarillo alert
    return 'bg-vegetation-healthy text-white'; // Verde saludable
  };

  // Tamaños
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-1.5 text-base'
  };

  return (
    <span
      className={`
        ${getColor(value)}
        ${sizeClasses[size]}
        rounded-full font-semibold
        inline-flex items-center gap-1
        shadow-sm
      `}
      title={`NDVI: ${value.toFixed(3)}`}
    >
      {showLabel && <span className="opacity-75">NDVI</span>}
      {value.toFixed(3)}
    </span>
  );
}
