import Map from '@/app/components/Map';

export default function Home() {
  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="mb-6 p-6 bg-white rounded-2xl shadow-sm relative overflow-hidden">
        {/* Top accent line */}
        <div className="absolute top-0 left-0 right-0 h-1  " />

        <div className="flex flex-col gap-4 ">
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-slate-800 mb-2 flex items-center gap-3">
              <span className="text-4xl drop-shadow-[0_2px_8px_rgba(14,165,233,0.3)]">🛰️</span>
              Mapa de Análisis Satelital
            </h1>
            <p className="text-slate-600">
              Dibuja polígonos sobre el mapa para definir las zonas de cultivo que deseas analizar
            </p>
          </div>

          <div className="flex gap-4 flex-wrap">
            <div className="flex items-center gap-3 px-4 py-3 bg-satellite-blue/5 border border-satellite-blue/20 rounded-xl transition-all hover:bg-satellite-blue/10 hover:border-satellite-blue/40 hover:shadow-lg hover:-translate-y-0.5">
              <span className="text-2xl">📡</span>
              <div className="flex flex-col">
                <span className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Fuente</span>
                <span className="text-sm font-bold text-satellite-deep">Sentinel-2</span>
              </div>
            </div>

            <div className="flex items-center gap-3 px-4 py-3 bg-satellite-blue/5 border border-satellite-blue/20 rounded-xl transition-all hover:bg-satellite-blue/10 hover:border-satellite-blue/40 hover:shadow-lg hover:-translate-y-0.5">
              <span className="text-2xl">🌍</span>
              <div className="flex flex-col">
                <span className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Región</span>
                <span className="text-sm font-bold text-satellite-deep">Venezuela</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Mapa */}
      <div className="relative bg-white rounded-2xl shadow-md overflow-hidden border-2 border-satellite-blue/10">
        <Map />

        {/* Hints flotantes */}
        <div className="absolute bottom-6 left-6 right-6 flex gap-4 flex-wrap pointer-events-none z-[1000]">
          <div className="flex items-center gap-2 px-4 py-3 bg-white/95 backdrop-blur-xl border border-satellite-blue/20 rounded-xl shadow-lg text-sm text-slate-800 font-medium pointer-events-auto">
            <span className="text-xl">✏️</span>
            <span>Usa la herramienta de dibujo para crear polígonos</span>
          </div>
          <div className="flex items-center gap-2 px-4 py-3 bg-white/95 backdrop-blur-xl border border-satellite-blue/20 rounded-xl shadow-lg text-sm text-slate-800 font-medium pointer-events-auto">
            <span className="text-xl">🗺️</span>
            <span>Alterna entre capas de mapa en el control superior derecho</span>
          </div>
        </div>
      </div>
    </div>
  );
}