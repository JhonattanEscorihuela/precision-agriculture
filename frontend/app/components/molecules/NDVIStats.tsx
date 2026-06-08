/**
 * OE2 - Tarjeta con estadísticos NDVI.
 * Molecule component (< 100 líneas)
 */

'use client';

import NDVIBadge from '../atoms/NDVIBadge';

interface NDVIStatsProps {
  stats: {
    ndvi_mean: number;
    ndvi_min: number;
    ndvi_max: number;
    ndvi_std: number;
  };
  onDownload?: () => void;
}

/**
 * Tarjeta que muestra estadísticos NDVI en grid 2x2 responsive.
 * Incluye badge coloreado para el promedio y botón opcional de descarga.
 */
export default function NDVIStats({ stats, onDownload }: NDVIStatsProps) {
  const StatItem = ({ label, value, isMean = false }: { label: string; value: number; isMean?: boolean }) => (
    <div className="bg-white/50 backdrop-blur-sm rounded-lg p-4 border border-emerald-200">
      <div className="text-xs text-gray-600 font-medium mb-2">{label}</div>
      {isMean ? (
        <NDVIBadge value={value} size="lg" showLabel={false} />
      ) : (
        <div className="text-2xl font-bold text-gray-900">
          {value.toFixed(3)}
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-4">
      {/* Grid 2x2 de estadísticos */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <StatItem label="📊 Promedio NDVI" value={stats.ndvi_mean} isMean />
        <StatItem label="📉 Mínimo" value={stats.ndvi_min} />
        <StatItem label="📈 Máximo" value={stats.ndvi_max} />
        <StatItem label="📏 Desv. Estándar" value={stats.ndvi_std} />
      </div>

      {/* Interpretación rápida */}
      <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3">
        <div className="flex items-start gap-2">
          <span className="text-xl">💡</span>
          <div className="flex-1">
            <div className="text-xs font-semibold text-emerald-800 mb-1">
              Interpretación
            </div>
            <div className="text-xs text-emerald-700">
              {getInterpretation(stats.ndvi_mean)}
            </div>
          </div>
        </div>
      </div>

      {/* Botón de descarga (opcional) */}
      {onDownload && (
        <button
          onClick={onDownload}
          className="
            w-full px-4 py-3 rounded-lg
            bg-blue-600 hover:bg-blue-700
            text-white font-medium text-sm
            flex items-center justify-center gap-2
            transition-colors duration-200
            shadow-sm hover:shadow-md
          "
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Descargar Raster NDVI (TIFF)
        </button>
      )}
    </div>
  );
}

/**
 * Genera interpretación textual del valor NDVI promedio.
 */
function getInterpretation(mean: number): string {
  if (mean < 0) {
    return 'Sin vegetación detectada. Puede indicar agua, suelo desnudo o infraestructura.';
  }
  if (mean < 0.2) {
    return 'Vegetación escasa o con estrés. Considerar revisar estado del cultivo.';
  }
  if (mean < 0.4) {
    return 'Vegetación baja. Cultivo en etapa temprana o con condiciones subóptimas.';
  }
  if (mean < 0.6) {
    return 'Vegetación saludable. Cultivo en buen estado con crecimiento normal.';
  }
  return 'Vegetación densa y vigorosa. Cultivo en estado óptimo de desarrollo.';
}
