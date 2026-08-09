/** OE3 - Presentación del resultado real de segmentación espacial. */

import type { ResourceState, SegmentationResult } from '@/lib/analysisTypes';
import NDVIOverlayPreview from '@/app/components/molecules/NDVIOverlayPreview';

interface SegmentationPanelProps {
  acquisitionId?: number | null;
  state: ResourceState<SegmentationResult>;
  onRetry: () => void;
}

const formatCalculationDate = (date: string) =>
  new Intl.DateTimeFormat('es-ES', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(date));

export default function SegmentationPanel({
  acquisitionId,
  state,
  onRetry,
}: SegmentationPanelProps) {
  const result = state.data;
  const cultivatedPercentage = result
    ? Math.min(100, Math.max(0, result.cultivated_percentage))
    : 0;
  const uncultivatedPercentage = 100 - cultivatedPercentage;

  return (
    <section className="rounded-xl border border-emerald-200 bg-gradient-to-br from-emerald-50 to-green-50 p-6 shadow-lg">
      <div className="mb-5 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-100 text-emerald-700">
          <svg aria-hidden="true" className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              d="M4 6a2 2 0 012-2h4v6H4V6zm10-2h4a2 2 0 012 2v4h-6V4zM4 14h6v6H6a2 2 0 01-2-2v-4zm10 0h6v4a2 2 0 01-2 2h-4v-6z"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
            />
          </svg>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">OE3</p>
          <h3 className="text-lg font-bold text-gray-900">Segmentación de la parcela</h3>
        </div>
      </div>

      {state.status === 'loading' && (
        <div className="flex min-h-64 items-center justify-center rounded-xl border border-emerald-100 bg-white/70" role="status">
          <div className="text-center">
            <div className="mx-auto mb-3 h-8 w-8 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-600" />
            <p className="text-sm font-medium text-emerald-800">Calculando segmentación...</p>
          </div>
        </div>
      )}

      {state.status === 'empty' && (
        <div className="min-h-64 rounded-xl border border-dashed border-emerald-300 bg-white/70 p-6 text-center">
          <p className="mt-12 font-semibold text-gray-800">Todavía no hay una segmentación disponible</p>
          <p className="mt-2 text-sm text-gray-600">
            {state.error ?? 'Primero se necesita un análisis NDVI de la parcela.'}
          </p>
          <button className="mt-5 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700" onClick={onRetry} type="button">
            Reintentar
          </button>
        </div>
      )}

      {state.status === 'error' && (
        <div className="min-h-64 rounded-xl border border-red-200 bg-red-50 p-6 text-center" role="alert">
          <p className="mt-12 font-semibold text-red-900">No se pudo cargar la segmentación</p>
          <p className="mt-2 text-sm text-red-700">{state.error}</p>
          <button className="mt-5 rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700" onClick={onRetry} type="button">
            Reintentar
          </button>
        </div>
      )}

      {state.status === 'success' && result && (
        <div>
          <div className="rounded-xl border border-emerald-100 bg-white p-5 text-center shadow-sm">
            <p className="text-sm font-medium text-gray-600">Área cultivada</p>
            <div className="my-2 inline-flex items-baseline rounded-full bg-emerald-100 px-5 py-2 text-emerald-800">
              <span className="text-4xl font-bold tracking-tight">{cultivatedPercentage.toFixed(1)}</span>
              <span className="ml-1 text-xl font-semibold">%</span>
            </div>
            <p className="text-xs text-gray-500">
              {result.cultivated_pixels.toLocaleString('es-ES')} de {result.total_pixels.toLocaleString('es-ES')} píxeles
            </p>
          </div>

          <progress
            aria-label="Porcentaje de área cultivada"
            className="mt-5 h-3 w-full overflow-hidden rounded-full accent-emerald-600"
            max={100}
            value={cultivatedPercentage}
          />

          <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-sm">
            <div className="flex items-center gap-2 text-gray-700">
              <span className="h-3 w-3 rounded-sm bg-emerald-600" />
              <span>Cultivado ({cultivatedPercentage.toFixed(1)}%)</span>
            </div>
            <div className="flex items-center gap-2 text-gray-700">
              <span className="h-3 w-3 rounded-sm bg-gray-300" />
              <span>Sin vegetación ({uncultivatedPercentage.toFixed(1)}%)</span>
            </div>
          </div>

          <dl className="mt-5 grid gap-3 border-t border-emerald-200 pt-4 sm:grid-cols-2">
            <div>
              <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Fecha de cálculo</dt>
              <dd className="mt-1 text-sm font-semibold text-gray-800">{formatCalculationDate(result.calculation_date)}</dd>
            </div>
            <div>
              <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Umbral NDVI</dt>
              <dd className="mt-1 text-sm font-semibold text-gray-800">{result.threshold_used.toFixed(2)}</dd>
            </div>
          </dl>

          <div className="mt-5 border-t border-emerald-200 pt-5">
            <NDVIOverlayPreview acquisitionId={acquisitionId} />
          </div>
        </div>
      )}
    </section>
  );
}
