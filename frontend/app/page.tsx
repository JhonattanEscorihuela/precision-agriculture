'use client';

import Map from '@/app/components/Map';
import ProtectedRoute from '@/app/components/ProtectedRoute';

export default function Home() {
  return (
    <ProtectedRoute>
      <div className="animate-fade-in">
        {/* Header */}
        <div className="mb-4 lg:mb-6 p-4 lg:p-6 bg-white rounded-xl lg:rounded-2xl shadow-sm relative overflow-hidden">
          {/* Top accent line */}
          <div className="absolute top-0 left-0 right-0 h-1  " />

          <div className="flex flex-col gap-3 lg:gap-4">
            <div className="flex-1">
              <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-slate-800 mb-2 flex items-center gap-2 lg:gap-3">
                <span className="text-2xl sm:text-3xl lg:text-4xl drop-shadow-[0_2px_8px_rgba(14,165,233,0.3)]">🛰️</span>
                <span className="truncate">Mapa de Análisis Satelital</span>
              </h1>
              <p className="text-xs sm:text-sm lg:text-base text-slate-600">
                Dibuja polígonos sobre el mapa para definir las zonas de cultivo
              </p>
            </div>

            <div className="flex gap-2 sm:gap-4 flex-wrap">
              <div className="flex items-center gap-2 lg:gap-3 px-3 lg:px-4 py-2 lg:py-3 bg-satellite-blue/5 border border-satellite-blue/20 rounded-lg lg:rounded-xl transition-all hover:bg-satellite-blue/10 hover:border-satellite-blue/40">
                <span className="text-xl lg:text-2xl">📡</span>
                <div className="flex flex-col">
                  <span className="text-[10px] lg:text-xs text-slate-500 uppercase tracking-wider font-semibold">Fuente</span>
                  <span className="text-xs lg:text-sm font-bold text-satellite-deep">Sentinel-2</span>
                </div>
              </div>

              <div className="flex items-center gap-2 lg:gap-3 px-3 lg:px-4 py-2 lg:py-3 bg-satellite-blue/5 border border-satellite-blue/20 rounded-lg lg:rounded-xl transition-all hover:bg-satellite-blue/10 hover:border-satellite-blue/40">
                <span className="text-xl lg:text-2xl">🌍</span>
                <div className="flex flex-col">
                  <span className="text-[10px] lg:text-xs text-slate-500 uppercase tracking-wider font-semibold">Región</span>
                  <span className="text-xs lg:text-sm font-bold text-satellite-deep">Venezuela</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Mapa */}
        <div className="relative bg-white rounded-xl lg:rounded-2xl shadow-md overflow-hidden border-2 border-satellite-blue/10">
          <Map />

          {/* Hints flotantes - ocultos en mobile pequeño */}
          {/* <div className="hidden sm:flex absolute bottom-4 lg:bottom-6 left-4 lg:left-6 right-4 lg:right-6 gap-2 lg:gap-4 flex-wrap pointer-events-none z-[1000]">
            <div className="flex items-center gap-2 px-3 lg:px-4 py-2 lg:py-3 bg-white/95 backdrop-blur-xl border border-satellite-blue/20 rounded-lg lg:rounded-xl shadow-lg text-xs lg:text-sm text-slate-800 font-medium pointer-events-auto">
              <span className="text-lg lg:text-xl">✏️</span>
              <span className="hidden md:inline">Usa la herramienta de dibujo para crear polígonos</span>
              <span className="md:hidden">Dibuja polígonos</span>
            </div>
            <div className="hidden md:flex items-center gap-2 px-3 lg:px-4 py-2 lg:py-3 bg-white/95 backdrop-blur-xl border border-satellite-blue/20 rounded-lg lg:rounded-xl shadow-lg text-xs lg:text-sm text-slate-800 font-medium pointer-events-auto">
              <span className="text-lg lg:text-xl">🗺️</span>
              <span>Alterna entre capas de mapa</span>
            </div>
          </div> */}
        </div>
      </div>
    </ProtectedRoute>
  );
}
