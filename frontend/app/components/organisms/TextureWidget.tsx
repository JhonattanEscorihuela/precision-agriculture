/** OE4 - Contenedor del estado y la tabla de descriptores reales. */

import type { ResourceState, TextureDescriptor } from '@/lib/analysisTypes';
import TextureDescriptorsTable from '../molecules/TextureDescriptorsTable';

interface TextureWidgetProps {
  state: ResourceState<TextureDescriptor[]>;
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

export default function TextureWidget({ state, onRetry }: TextureWidgetProps) {
  const descriptors = state.data;

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
        <div>
          <TextureDescriptorsTable descriptors={descriptors} />
          {descriptors[0] && (
            <p className="mt-3 text-xs text-gray-500">Calculado el {formatCalculationDate(descriptors[0].calculation_date)}</p>
          )}
        </div>
      )}
    </section>
  );
}
