/** OE4 - Contenedor del estado y la tabla de descriptores reales. */

'use client';

import { useState } from 'react';
import type { ResourceState, TextureDescriptor, NDVISummary } from '@/lib/analysisTypes';
import TextureDescriptorsTable from '../molecules/TextureDescriptorsTable';
import TextureOverlayPreview from '../molecules/TextureOverlayPreview';
import { useSatelliteImage } from '@/app/hooks/useSatelliteImage';

interface TextureWidgetProps {
  ndviResultId?: number | null;
  state: ResourceState<TextureDescriptor[]>;
  onRetry: () => void;
}

interface TextureWidgetPropsExtended extends TextureWidgetProps {
  acquisitionId?: number | null;
  availableDates?: NDVISummary[];
  onDateChange?: (acquisitionId: number) => void;
}

const formatCalculationDate = (date: string) =>
  new Intl.DateTimeFormat('es-ES', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(date));

export default function TextureWidget({
  ndviResultId,
  acquisitionId,
  availableDates = [],
  onDateChange,
  state,
  onRetry,
}: TextureWidgetPropsExtended) {
  const descriptors = state.data;

  const [showSatellite, setShowSatellite] = useState(false);
  const [satelliteOnly, setSatelliteOnly] = useState(false);
  const satellite = useSatelliteImage(acquisitionId);

  const handleToggleSatellite = async () => {
    if (!showSatellite && !satellite.data && !satellite.loading) {
      await satellite.load();
    }
    setShowSatellite(!showSatellite);
    if (showSatellite) setSatelliteOnly(false);
  };

  return (
    <section className="rounded-xl border border-violet-200 bg-gradient-to-br from-violet-50 to-purple-50 p-6 shadow-lg">
      <div className="mb-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-violet-700">OE4</p>
        <h3 className="text-lg font-bold text-gray-900">Descriptores de textura</h3>
      </div>

      {state.status === 'loading' && (
        <div className="flex min-h-52 items-center justify-center rounded-xl border border-violet-100 bg-white/70" role="status">
          <div className="text-center">
            <div className="mx-auto mb-3 h-8 w-8 animate-spin rounded-full border-4 border-violet-200 border-t-violet-600" />
            <p className="text-sm font-medium text-violet-800">Calculando descriptores...</p>
          </div>
        </div>
      )}

      {state.status === 'empty' && (
        <div className="min-h-52 rounded-xl border border-dashed border-violet-300 bg-white/70 p-6 text-center">
          <p className="mt-10 font-semibold text-gray-800">Todavía no hay descriptores disponibles</p>
          <p className="mt-2 text-sm text-gray-600">
            {state.error ?? 'La textura se calcula después de segmentar la parcela.'}
          </p>
          <button className="mt-5 rounded-lg bg-violet-600 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-700" onClick={onRetry} type="button">Reintentar</button>
        </div>
      )}

      {state.status === 'error' && (
        <div className="min-h-52 rounded-xl border border-red-200 bg-red-50 p-6 text-center" role="alert">
          <p className="mt-10 font-semibold text-red-900">No se pudo cargar la textura</p>
          <p className="mt-2 text-sm text-red-700">{state.error}</p>
          <button className="mt-5 rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700" onClick={onRetry} type="button">Reintentar</button>
        </div>
      )}

      {state.status === 'success' && descriptors && (
        <div className="space-y-5">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <span className="text-sm font-medium text-gray-700">Visualización</span>
            <div className="flex flex-wrap items-center gap-3">
              <label className="flex cursor-pointer items-center gap-2">
                <input
                  checked={showSatellite}
                  className="h-4 w-4 rounded border-gray-300 text-violet-600 focus:ring-2 focus:ring-violet-500"
                  onChange={handleToggleSatellite}
                  type="checkbox"
                />
                <span className="text-sm text-gray-600">Imagen satélite</span>
              </label>
              {showSatellite && satellite.data && (
                <label className="flex cursor-pointer items-center gap-2">
                  <input
                    checked={satelliteOnly}
                    className="h-4 w-4 rounded border-gray-300 text-violet-600 focus:ring-2 focus:ring-violet-500"
                    onChange={(e) => setSatelliteOnly(e.target.checked)}
                    type="checkbox"
                  />
                  <span className="text-sm text-gray-600">Solo imagen</span>
                </label>
              )}
            </div>
          </div>

          {availableDates.length > 1 && onDateChange && (
            <div className="mb-4 flex items-center gap-2">
              <label className="text-xs font-semibold text-violet-900">
                Fecha de análisis:
                <select
                  className="ml-2 rounded-lg border border-violet-300 bg-white px-3 py-1.5 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-violet-500"
                  onChange={(e) => onDateChange(Number(e.target.value))}
                  value={acquisitionId ?? ''}
                >
                  {availableDates.map((date) => (
                    <option key={date.acquisition_id} value={date.acquisition_id}>
                      {new Date(date.acquisition_date).toLocaleDateString('es-ES', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                      })}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          )}

          <TextureOverlayPreview ndviResultId={ndviResultId} showSatellite={showSatellite} satelliteData={satellite.data} satelliteOnly={satelliteOnly} />

          <details className="rounded-xl border border-violet-200 bg-white/70" open>
            <summary className="cursor-pointer px-4 py-3 text-sm font-semibold text-violet-900">
              Tabla de descriptores
            </summary>
            <div className="px-3 pb-3">
              <TextureDescriptorsTable descriptors={descriptors} />
            </div>
          </details>
          {descriptors[0] && (
            <p className="text-xs text-gray-500">Calculado el {formatCalculationDate(descriptors[0].calculation_date)}</p>
          )}
        </div>
      )}
    </section>
  );
}
