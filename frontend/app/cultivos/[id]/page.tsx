/**
 * Dashboard individual de análisis por parcela.
 * Ruta dinámica: /cultivos/[id]
 *
 * Contiene widgets de análisis:
 * - OE2: Evolución temporal NDVI
 * - OE3: (Futuro) Segmentación espacial
 * - OE4: (Futuro) Descriptores de textura
 */

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { usePolygons } from '@/app/context/PolygonContext';
import { DateRangeProvider } from '@/app/context/DateRangeContext';
import ProtectedRoute from '@/app/components/ProtectedRoute';
import NDVIEvolutionWidget from '@/app/components/organisms/NDVIEvolutionWidget';
import SegmentationWidget from '@/app/components/organisms/SegmentationWidget';
import TextureWidget from '@/app/components/organisms/TextureWidget';
import DateRangeFilter from '@/app/components/molecules/DateRangeFilter';
import { calculatePolygonArea, formatArea } from '@/app/utils/geoUtils';

interface DashboardPageProps {
  params: Promise<{
    id: string;
  }>;
}

export default function DashboardPage({ params }: DashboardPageProps) {
  const router = useRouter();
  const { polygons, fetchPolygons } = usePolygons();
  const [isLoading, setIsLoading] = useState(true);
  const [polygonId, setPolygonId] = useState<number | null>(null);

  // Unwrap params async
  useEffect(() => {
    params.then(p => setPolygonId(parseInt(p.id)));
  }, [params]);

  const polygon = polygonId ? polygons.find(p => p.id === polygonId) : null;

  useEffect(() => {
    const loadData = async () => {
      await fetchPolygons();
      setIsLoading(false);
    };
    loadData();
  }, [fetchPolygons]);

  if (isLoading || polygonId === null) {
    return (
      <ProtectedRoute>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Cargando dashboard...</p>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  if (!polygon) {
    return (
      <ProtectedRoute>
        <div className="animate-fade-in">
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
            <h2 className="text-xl font-bold text-red-900 mb-2">Parcela no encontrada</h2>
            <p className="text-red-700 mb-4">La parcela #{polygonId || 'desconocida'} no existe o fue eliminada.</p>
            <button
              onClick={() => router.push('/cultivos')}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              ← Volver a Cultivos
            </button>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  const areaHa = calculatePolygonArea(polygon.coordinates);

  return (
    <ProtectedRoute>
      <DateRangeProvider>
      <div className="animate-fade-in space-y-6">
        {/* Header del Dashboard */}
        <div className="bg-gradient-to-r from-emerald-600 to-green-600 rounded-xl lg:rounded-2xl p-6 lg:p-8 shadow-lg text-white">
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <button
                onClick={() => router.push('/cultivos')}
                className="text-emerald-100 hover:text-white text-sm mb-3 flex items-center gap-1 transition-colors"
              >
                ← Volver a Cultivos
              </button>
              <h1 className="text-2xl lg:text-4xl font-bold mb-2 flex items-center gap-3">
                <span className="text-3xl lg:text-5xl">🌱</span>
                {polygon.name}
              </h1>
              <p className="text-emerald-100 text-sm lg:text-base">
                Dashboard de Análisis · ID #{polygon.id}
              </p>
            </div>
          </div>

          {/* Stats rápidos */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 lg:gap-4">
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-3 lg:p-4">
              <p className="text-emerald-100 text-xs mb-1">Área</p>
              <p className="text-xl lg:text-2xl font-bold">{formatArea(areaHa)}</p>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-3 lg:p-4">
              <p className="text-emerald-100 text-xs mb-1">Puntos</p>
              <p className="text-xl lg:text-2xl font-bold">{polygon.coordinates.length}</p>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-3 lg:p-4">
              <p className="text-emerald-100 text-xs mb-1">Fuente</p>
              <p className="text-sm lg:text-base font-semibold">Sentinel-2</p>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-3 lg:p-4">
              <p className="text-emerald-100 text-xs mb-1">Resolución</p>
              <p className="text-sm lg:text-base font-semibold">10m/px</p>
            </div>
          </div>
        </div>

        {/* Grid de Widgets de Análisis */}
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl lg:text-2xl font-bold text-gray-900">Widgets de Análisis</h2>
              <p className="text-sm text-gray-500 mt-1">Filtra el período temporal para todos los widgets</p>
            </div>
            <DateRangeFilter />
          </div>

          {/* Grid 2 columnas en desktop, 1 en mobile */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Widget 1: Evolución Temporal NDVI (OE2) */}
            <NDVIEvolutionWidget
              polygonId={polygon.id}
              polygonName={polygon.name}
              polygonCoordinates={polygon.coordinates}
            />

            {/* Widget 2: Segmentación Espacial (OE3) */}
            <SegmentationWidget />

            {/* Widget 3: Descriptores de Textura (OE4) */}
            <TextureWidget />

            {/* Widget 4: Placeholder Comparación */}
            <div className="bg-gradient-to-br from-orange-50 to-amber-50 rounded-xl p-6 border-2 border-dashed border-orange-300">
              <div className="text-center py-8">
                <span className="text-5xl mb-4 block">📊</span>
                <h3 className="text-lg font-bold text-gray-800 mb-2">Comparación Temporal</h3>
                <p className="text-sm text-gray-600 mb-4">
                  Análisis multi-temporal · Próximamente
                </p>
                <span className="inline-block text-xs text-orange-700 bg-orange-100 px-3 py-1 rounded-full">
                  En desarrollo
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer info */}
        <div className="bg-gray-50 rounded-lg p-4 text-center text-xs text-gray-500">
          💡 Tip: Los widgets se actualizan automáticamente cuando calculas nuevos análisis en el mapa
        </div>
      </div>
      </DateRangeProvider>
    </ProtectedRoute>
  );
}
