/**
 * OE3 - Widget placeholder de segmentación espacial (futuro).
 * Muestra skeleton animado mientras se implementa la funcionalidad.
 */

'use client';

export default function SegmentationWidget() {
  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-200 shadow-lg">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <span className="text-2xl">🗺️</span>
        <h3 className="font-bold text-gray-900">Segmentación Espacial</h3>
        <span className="ml-auto text-xs bg-blue-200 text-blue-800 px-2 py-1 rounded-full font-semibold">
          OE3 - Próximamente
        </span>
      </div>

      {/* Skeleton de mapa segmentado */}
      <div className="bg-white rounded-lg p-4 mb-4 animate-pulse">
        <div className="h-4 w-48 bg-gray-200 rounded mb-3"></div>
        <div className="bg-gradient-to-r from-green-100 via-yellow-100 to-red-100 rounded-lg h-48 relative overflow-hidden">
          {/* Efecto de segmentos */}
          <div className="absolute inset-0 grid grid-cols-3 gap-2 p-4">
            {[...Array(9)].map((_, i) => (
              <div
                key={i}
                className="bg-white/30 backdrop-blur-sm rounded border border-white/50"
                style={{ animationDelay: `${i * 0.1}s` }}
              ></div>
            ))}
          </div>
        </div>
      </div>

      {/* Stats placeholder */}
      <div className="grid grid-cols-3 gap-2 mb-4">
        {['Zona A', 'Zona B', 'Zona C'].map((zone, i) => (
          <div key={i} className="bg-white/70 backdrop-blur-sm rounded-lg p-2 text-center animate-pulse">
            <p className="text-xs text-gray-600 mb-1">{zone}</p>
            <div className="h-5 w-12 bg-gray-300 rounded mx-auto"></div>
          </div>
        ))}
      </div>

      {/* Info */}
      <div className="bg-blue-100 border border-blue-300 rounded-lg p-3">
        <p className="text-xs text-blue-800">
          <span className="font-semibold">🔬 Objetivo:</span> Analizar zonas cultivadas mediante segmentación espacial
          para identificar áreas con diferentes características de salud.
        </p>
      </div>
    </div>
  );
}
