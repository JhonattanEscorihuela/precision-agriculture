'use client';

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { PhenologyComparison, ResourceState } from '@/lib/analysisTypes';

interface FenologicalComparisonWidgetProps {
  state: ResourceState<PhenologyComparison>;
  onRetry: () => void;
}

export default function FenologicalComparisonWidget({
  state,
  onRetry,
}: FenologicalComparisonWidgetProps) {
  const result = state.data;
  const matchesPattern = Boolean(result && result.similarity_score >= 0.85);
  const similarityPercentage = result ? Math.round(result.similarity_score * 100) : 0;
  const chartData = result?.curve_data.map((point) => ({
    ...point,
    displayDate: new Date(`${point.date}T00:00:00`).toLocaleDateString('es-ES', {
      day: '2-digit',
      month: 'short',
    }),
  })) ?? [];

  return (
    <section className="rounded-xl border border-emerald-200 bg-gradient-to-br from-emerald-50 to-green-50 p-6 shadow-lg">
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">OE3 · Comparación fenológica</p>
          <h3 className="mt-1 text-lg font-bold text-gray-900">Parcela vs. referencia de arroz</h3>
          <p className="mt-1 text-sm text-gray-600">Similitud de la evolución temporal del NDVI</p>
        </div>
        {state.status === 'success' && result && (
          <div className="flex items-center gap-2 sm:flex-col sm:items-end">
            <span className={`rounded-full px-3 py-1 text-xs font-semibold ring-1 ${matchesPattern ? 'bg-emerald-100 text-emerald-800 ring-emerald-300' : 'bg-red-100 text-red-800 ring-red-300'}`}>
              {matchesPattern ? 'Patrón de arroz detectado' : 'Patrón de arroz no detectado'}
            </span>
            <span className="text-2xl font-bold text-gray-900">{similarityPercentage}%</span>
            <span className="text-xs text-gray-500">de correlación</span>
          </div>
        )}
      </div>

      {state.status === 'loading' && (
        <div className="flex h-72 items-center justify-center rounded-lg border border-emerald-100 bg-white/70" role="status">
          <div className="text-center">
            <div className="mx-auto mb-3 h-8 w-8 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-600" />
            <p className="text-sm font-medium text-emerald-800">Comparando curvas NDVI...</p>
          </div>
        </div>
      )}

      {state.status === 'empty' && (
        <div className="h-72 rounded-lg border border-dashed border-emerald-300 bg-white/70 p-6 text-center">
          <p className="mt-16 font-semibold text-gray-800">No hay suficientes datos para comparar</p>
          <p className="mt-2 text-sm text-gray-600">
            {state.error ?? 'Se necesitan al menos cinco fechas NDVI coincidentes.'}
          </p>
          <button className="mt-5 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700" onClick={onRetry} type="button">Reintentar</button>
        </div>
      )}

      {state.status === 'error' && (
        <div className="h-72 rounded-lg border border-red-200 bg-red-50 p-6 text-center" role="alert">
          <p className="mt-16 font-semibold text-red-900">Comparación no disponible</p>
          <p className="mt-2 text-sm text-red-700">{state.error}</p>
          <button className="mt-5 rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700" onClick={onRetry} type="button">Reintentar</button>
        </div>
      )}

      {state.status === 'success' && result && (
        <div>
          <div className="rounded-lg border border-gray-100 bg-white p-4">
            <div className="h-64 w-full">
              <ResponsiveContainer height="100%" width="100%">
                <LineChart data={chartData} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
                  <CartesianGrid stroke="#e5e7eb" strokeDasharray="3 3" />
                  <XAxis axisLine={false} dataKey="displayDate" tickLine={false} />
                  <YAxis axisLine={false} domain={[-1, 1]} tickLine={false} />
                  <Tooltip />
                  <Legend />
                  <Line activeDot={{ r: 6 }} dataKey="ndvi_parcel" dot={{ r: 4, fill: '#059669' }} name="Parcela actual" stroke="#059669" strokeWidth={3} type="monotone" />
                  <Line activeDot={{ r: 6 }} dataKey="ndvi_reference" dot={{ r: 4, fill: '#2563eb' }} name="Referencia arroz" stroke="#2563eb" strokeDasharray="6 4" strokeWidth={3} type="monotone" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
          <p className="mt-3 text-xs text-gray-600">{result.classification}</p>
          <p className="mt-1 text-xs text-gray-500">
            {result.dates_compared} fechas comparadas · Referencia construida con {result.reference_polygon_ids.length} parcelas de arroz.
          </p>
        </div>
      )}
    </section>
  );
}
