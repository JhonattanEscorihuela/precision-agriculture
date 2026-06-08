/**
 * OE2 - Escala de colores NDVI horizontal con labels.
 * Molecule component (< 100 líneas)
 */

'use client';

/**
 * Escala de colores NDVI horizontal con labels en puntos de cambio.
 * Usa gradient CSS con los 5 colores estándar NDVI.
 * Responsive: scroll horizontal en mobile si es necesario.
 */
export default function NDVIColorScale() {
  const ranges = [
    { value: -1.0, color: '#8B4513', label: 'Sin vegetación' },
    { value: 0.0, color: '#D2B48C', label: 'Escasa' },
    { value: 0.2, color: '#ADFF2F', label: 'Baja' },
    { value: 0.4, color: '#32CD32', label: 'Media' },
    { value: 0.6, color: '#006400', label: 'Densa' },
    { value: 1.0, color: '#006400', label: '' } // Final del rango
  ];

  return (
    <div className="space-y-2 overflow-x-auto">
      {/* Título */}
      <div className="text-xs font-semibold text-gray-700 flex items-center gap-2">
        <span>🎨</span>
        <span>Escala de Vegetación NDVI</span>
      </div>

      {/* Barra de gradiente */}
      <div className="relative h-8 rounded-lg overflow-hidden shadow-sm border border-gray-200">
        <div
          className="absolute inset-0"
          style={{
            background: `linear-gradient(to right,
              #8B4513 0%,
              #D2B48C 20%,
              #ADFF2F 40%,
              #32CD32 60%,
              #006400 80%,
              #006400 100%
            )`
          }}
        />
      </div>

      {/* Labels de valores y rangos */}
      <div className="flex justify-between text-[10px] sm:text-xs text-gray-600 font-medium">
        <span>-1.0</span>
        <span className="hidden sm:inline">0.0</span>
        <span>0.2</span>
        <span className="hidden sm:inline">0.4</span>
        <span>0.6</span>
        <span>1.0</span>
      </div>

      {/* Labels descriptivos */}
      <div className="hidden sm:grid grid-cols-5 gap-1 text-[10px] text-center text-gray-500">
        <div>Sin veg.</div>
        <div>Escasa</div>
        <div>Baja</div>
        <div>Media</div>
        <div>Densa</div>
      </div>

      {/* Nota informativa */}
      <div className="text-[10px] text-gray-500 italic pt-1">
        * Valores cercanos a 1.0 indican vegetación saludable y densa
      </div>
    </div>
  );
}
