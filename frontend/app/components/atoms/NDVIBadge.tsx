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
 * Badge que muestra valor NDVI con color según rango de vegetación.
 *
 * Escala de colores:
 * [-1.0, 0.0)  → Marrón #8B4513 (sin vegetación: agua, suelo)
 * [0.0,  0.2)  → Beige #D2B48C (vegetación escasa: estrés)
 * [0.2,  0.4)  → Verde-amarillo #ADFF2F (vegetación baja: pastos secos)
 * [0.4,  0.6)  → Verde lima #32CD32 (vegetación media: cultivos sanos)
 * [0.6,  1.0]  → Verde oscuro #006400 (vegetación densa: óptima)
 */
export default function NDVIBadge({ value, size = 'md', showLabel = true }: NDVIBadgeProps) {
  // Determinar color según rango NDVI
  const getColor = (ndvi: number): string => {
    if (ndvi < 0) return 'bg-[#8B4513] text-white'; // Marrón (sin vegetación)
    if (ndvi < 0.2) return 'bg-[#D2B48C] text-gray-800'; // Beige (escasa)
    if (ndvi < 0.4) return 'bg-[#ADFF2F] text-gray-900'; // Verde-amarillo (baja)
    if (ndvi < 0.6) return 'bg-[#32CD32] text-white'; // Verde lima (media)
    return 'bg-[#006400] text-white'; // Verde oscuro (densa)
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
