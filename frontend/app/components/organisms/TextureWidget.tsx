/**
 * OE4 - Widget placeholder de descriptores de textura (futuro).
 * Muestra skeleton animado mientras se implementa la funcionalidad.
 */

'use client';

export default function TextureWidget() {
  return (
    <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-6 border border-purple-200 shadow-lg">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <span className="text-2xl">🔬</span>
        <h3 className="font-bold text-gray-900">Descriptores de Textura</h3>
        <span className="ml-auto text-xs bg-purple-200 text-purple-800 px-2 py-1 rounded-full font-semibold">
          OE4 - Próximamente
        </span>
      </div>

      {/* Skeleton de matriz de textura */}
      <div className="bg-white rounded-lg p-4 mb-4 animate-pulse">
        <div className="h-4 w-56 bg-gray-200 rounded mb-3"></div>
        <div className="grid grid-cols-4 gap-2">
          {[...Array(16)].map((_, i) => (
            <div
              key={i}
              className="h-12 bg-gradient-to-br from-purple-100 to-pink-100 rounded"
              style={{
                animationDelay: `${i * 0.05}s`,
                opacity: 0.3 + (Math.random() * 0.7)
              }}
            ></div>
          ))}
        </div>
      </div>

      {/* Descriptores placeholder */}
      <div className="grid grid-cols-2 gap-2 mb-4">
        {['Contraste', 'Homogeneidad', 'Entropía', 'Energía'].map((desc, i) => (
          <div key={i} className="bg-white/70 backdrop-blur-sm rounded-lg p-2 animate-pulse">
            <p className="text-xs text-gray-600 mb-1">{desc}</p>
            <div className="h-5 w-16 bg-gray-300 rounded"></div>
          </div>
        ))}
      </div>

      {/* Info */}
      <div className="bg-purple-100 border border-purple-300 rounded-lg p-3">
        <p className="text-xs text-purple-800">
          <span className="font-semibold">🧠 Objetivo:</span> Evaluar descriptores de textura mediante filtrado
          convolucional para caracterizar patrones en el cultivo (GLCM, LBP, etc.).
        </p>
      </div>
    </div>
  );
}
