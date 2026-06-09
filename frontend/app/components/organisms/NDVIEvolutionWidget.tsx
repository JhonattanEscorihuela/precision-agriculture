/**
 * OE2 - Widget de evolución temporal NDVI.
 * Organism component - Muestra gráfica de tendencia NDVI en el tiempo.
 */

'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/app/context/AuthContext';
import { useDateRange } from '@/app/context/DateRangeContext';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import NDVIBadge from '../atoms/NDVIBadge';
import { calculatePolygonArea, formatArea } from '@/app/utils/geoUtils';

interface NDVIEvolutionWidgetProps {
  polygonId: number;
  polygonName: string;
  polygonCoordinates: number[][]; // Para calcular área
}

interface NDVIDataPoint {
  acquisition_id: number;
  polygon_id: number;
  acquisition_date: string;  // Fecha de la imagen satelital
  calculation_date: string;  // Fecha del cálculo NDVI
  ndvi_mean: number;
  ndvi_min: number;
  ndvi_max: number;
  ndvi_std: number;
}

/**
 * Widget que muestra evolución temporal del NDVI con:
 * - Gráfica de línea con últimas 6 fechas
 * - Badge de estado actual (valor más reciente)
 * - Área de la parcela en hectáreas
 */
export default function NDVIEvolutionWidget({
  polygonId,
  polygonName,
  polygonCoordinates
}: NDVIEvolutionWidgetProps) {
  const { token } = useAuth();
  const { range, getStartDate, getEndDate, setIsLoading: setGlobalLoading } = useDateRange();
  const [data, setData] = useState<NDVIDataPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [missingDates, setMissingDates] = useState<number>(0);
  const [isCalculatingBatch, setIsCalculatingBatch] = useState(false);
  const [batchProgress, setBatchProgress] = useState<string>('');
  const [isFetching, setIsFetching] = useState(false);

  // Calcular área de la parcela
  const areaHectares = calculatePolygonArea(polygonCoordinates);

  useEffect(() => {
    if (!isFetching) {
      fetchNDVIHistory();
    }
  }, [polygonId, range]);

  const fetchNDVIHistory = async () => {
    if (!token) {
      setError('No autenticado');
      setIsLoading(false);
      setGlobalLoading(false);
      return;
    }

    if (isFetching) return;

    setIsFetching(true);
    setIsLoading(true);
    setGlobalLoading(true);
    setError('');

    try {
      const startDate = getStartDate().toISOString().split('T')[0];
      const endDate = getEndDate().toISOString().split('T')[0];

      // Usa BD como caché - solo retorna NDVIs ya calculados en el rango
      const response = await axios.get(
        `http://localhost:8000/api/ndvi/polygon/${polygonId}?start_date=${startDate}&end_date=${endDate}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      // Ya viene ordenado por acquisition_date desde el backend
      setData(response.data);

      // Detectar fechas faltantes: consultar fechas disponibles en Sentinel
      try {
        const availableResponse = await axios.get(
          `http://localhost:8000/api/sentinel/available-dates/${polygonId}?start_date=${startDate}&end_date=${endDate}&max_cloud=20`
        );
        const availableDates = availableResponse.data.dates || [];
        const calculatedDates = new Set(response.data.map((d: NDVIDataPoint) => d.acquisition_date));
        const missing = availableDates.filter((d: any) => !d.ndvi_calculated).length;
        setMissingDates(missing);
      } catch (e) {
        setMissingDates(0);
      }

    } catch (err: any) {
      if (err.response?.status === 404 || err.response?.data?.detail?.includes('No NDVI results')) {
        // No hay datos calculados aún
        setData([]);

        // Verificar fechas disponibles
        try {
          const startDate = getStartDate().toISOString().split('T')[0];
          const endDate = getEndDate().toISOString().split('T')[0];
          const availableResponse = await axios.get(
            `http://localhost:8000/api/sentinel/available-dates/${polygonId}?start_date=${startDate}&end_date=${endDate}&max_cloud=20`
          );
          const availableDates = availableResponse.data.dates || [];
          setMissingDates(availableDates.length);
        } catch (e) {
          setMissingDates(0);
        }
      } else {
        setError('Error al cargar histórico NDVI');
      }
    } finally {
      setIsLoading(false);
      setGlobalLoading(false);
      setIsFetching(false);
    }
  };

  const calculateBatch = async () => {
    if (!token) return;

    setIsCalculatingBatch(true);
    setBatchProgress('Analizando imágenes satelitales...');
    setGlobalLoading(true);

    try {
      const startDate = getStartDate().toISOString().split('T')[0];
      const endDate = getEndDate().toISOString().split('T')[0];

      const response = await axios.post(
        'http://localhost:8000/api/ndvi/calculate-batch',
        {
          polygon_id: polygonId,
          start_date: startDate,
          end_date: endDate,
          max_cloud: 20
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      const result = response.data;

      if (result.newly_calculated > 0) {
        setBatchProgress(`✓ ${result.newly_calculated} análisis completados`);
      } else {
        setBatchProgress('✓ Análisis completo');
      }

      await fetchNDVIHistory();

      setTimeout(() => {
        setBatchProgress('');
        setIsCalculatingBatch(false);
      }, 2000);

    } catch (err: any) {
      console.error('Batch calculation error:', err);
      setError('Error al analizar imágenes: ' + (err.response?.data?.detail || err.message));
      setIsCalculatingBatch(false);
      setGlobalLoading(false);
      setBatchProgress('');
    }
  };

  // Estado actual (valor más reciente) - data[0] porque backend ordena DESC
  const latestNDVI = data.length > 0 ? data[0] : null;

  // Formatear datos para Recharts - Revertir orden para mostrar cronológicamente (izq→der: antiguo→reciente)
  // Backend retorna DESC, pero gráfica debe mostrar ASC
  const chartData = [...data].reverse().map((point) => ({
    date: new Date(point.acquisition_date).toLocaleDateString('es-ES', {
      day: '2-digit',
      month: 'short'
    }),
    ndvi: parseFloat(point.ndvi_mean.toFixed(3)),
    fullDate: new Date(point.acquisition_date).toLocaleDateString('es-ES')
  }));

  if (isLoading) {
    return (
      <div className="bg-gradient-to-br from-emerald-50 to-green-50 rounded-xl p-6 border border-emerald-200 shadow-lg animate-pulse min-h-[500px] flex flex-col">
        {/* Header skeleton */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-8 h-8 bg-emerald-200 rounded"></div>
              <div className="h-6 w-40 bg-emerald-200 rounded"></div>
            </div>
            <div className="h-4 w-24 bg-emerald-200 rounded mb-1"></div>
            <div className="h-3 w-32 bg-emerald-200 rounded"></div>
          </div>
          <div className="h-10 w-20 bg-emerald-200 rounded"></div>
        </div>

        {/* Chart skeleton - altura fija para evitar salto */}
        <div className="bg-white rounded-lg p-4 mb-4 flex-1">
          <div className="h-4 w-48 bg-gray-200 rounded mb-3"></div>
          <div className="h-[200px] bg-gray-100 rounded flex items-end justify-around gap-2 px-4">
            {[...Array(6)].map((_, i) => (
              <div
                key={i}
                className="bg-emerald-300 rounded-t animate-pulse"
                style={{
                  height: `${40 + Math.random() * 60}%`,
                  width: '12%',
                  animationDelay: `${i * 0.1}s`
                }}
              ></div>
            ))}
          </div>
          <div className="h-4 bg-gray-100 rounded mt-2"></div>
        </div>

        {/* Stats skeleton */}
        <div className="grid grid-cols-3 gap-2 mb-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="bg-white/70 backdrop-blur-sm rounded-lg p-2">
              <div className="h-3 w-16 bg-gray-200 rounded mb-1"></div>
              <div className="h-5 w-12 bg-gray-300 rounded"></div>
            </div>
          ))}
        </div>

        {/* Loading text */}
        <div className="text-center">
          <div className="inline-flex items-center gap-2 text-sm text-emerald-700 font-medium">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-emerald-700"></div>
            <span>Cargando análisis...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 rounded-xl p-4 border border-red-200">
        <p className="text-red-700 text-sm">{error}</p>
      </div>
    );
  }

  if (data.length === 0) {
    const startDateStr = getStartDate().toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' });
    const endDateStr = getEndDate().toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' });

    return (
      <div className="bg-gradient-to-br from-emerald-50 to-green-50 rounded-xl p-6 border border-emerald-200">
        <div className="flex items-center gap-3 mb-3">
          <span className="text-2xl">🌱</span>
          <h3 className="font-bold text-gray-900">{polygonName}</h3>
        </div>
        <p className="text-sm text-gray-600 mb-2">📍 Área: {formatArea(areaHectares)}</p>
        <p className="text-xs text-gray-500 mb-4">📅 Rango: {startDateStr} - {endDateStr}</p>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <p className="text-sm text-blue-700">
            📊 No hay análisis NDVI en este rango de fechas.
          </p>
        </div>

        {/* Botón de cálculo batch si hay fechas disponibles */}
        {missingDates > 0 && !isCalculatingBatch && (
          <div className="mt-4">
            <button
              onClick={calculateBatch}
              className="w-full px-4 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-semibold transition-colors flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Calcular NDVIs automáticamente ({missingDates} fechas)
            </button>
            <p className="text-xs text-gray-500 text-center mt-2">
              Adquirirá bandas y calculará NDVI para todas las fechas disponibles
            </p>
          </div>
        )}

        {/* Progress de batch */}
        {isCalculatingBatch && (
          <div className="mt-4 bg-emerald-100 border border-emerald-300 rounded-lg p-3">
            <div className="flex items-center gap-2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-emerald-600"></div>
              <p className="text-sm text-emerald-700">{batchProgress}</p>
            </div>
          </div>
        )}

        {missingDates === 0 && !isLoading && (
          <p className="text-xs text-gray-500 text-center mt-4">
            No hay fechas disponibles en Sentinel con cloud {'<'} 20% en este rango.
          </p>
        )}
      </div>
    );
  }

  const startDateStr = getStartDate().toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' });
  const endDateStr = getEndDate().toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' });

  return (
    <div className="bg-gradient-to-br from-emerald-50 to-green-50 rounded-xl shadow-md p-6 border border-emerald-200">
      {/* Header con nombre y área */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className="text-2xl">🌱</span>
            <h3 className="font-bold text-gray-900">{polygonName}</h3>
          </div>
          <p className="text-sm text-gray-600">📍 Área: {formatArea(areaHectares)}</p>
          <p className="text-xs text-gray-500">📅 {startDateStr} - {endDateStr}</p>
        </div>

        {/* Estado actual */}
        {latestNDVI && (
          <div className="text-right">
            <p className="text-xs text-gray-500 mb-1">Estado Actual</p>
            <NDVIBadge value={latestNDVI.ndvi_mean} size="md" showLabel />
          </div>
        )}
      </div>

      {/* Gráfica de evolución */}
      <div className="bg-white rounded-lg p-4 mb-4">
        <h4 className="text-sm font-semibold text-gray-700 mb-3">
          📈 Evolución temporal ({data.length} {data.length === 1 ? 'fecha' : 'fechas'})
        </h4>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11, fill: '#6b7280' }}
              stroke="#9ca3af"
            />
            <YAxis
              domain={[-0.2, 1]}
              tick={{ fontSize: 11, fill: '#6b7280' }}
              stroke="#9ca3af"
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #d1d5db',
                borderRadius: '8px',
                fontSize: '12px'
              }}
              labelStyle={{ fontWeight: 'bold', color: '#374151' }}
              formatter={(value: number) => [value.toFixed(3), 'NDVI']}
            />
            <ReferenceLine y={0.4} stroke="#f59e0b" strokeDasharray="3 3" />
            <ReferenceLine y={0.6} stroke="#10b981" strokeDasharray="3 3" />
            <Line
              type="monotone"
              dataKey="ndvi"
              stroke="#059669"
              strokeWidth={3}
              dot={{ fill: '#059669', r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
        <div className="flex justify-center gap-4 mt-2 text-xs text-gray-500">
          <span>🟡 0.4 = Vegetación moderada</span>
          <span>🟢 0.6 = Vegetación densa</span>
        </div>
      </div>

      {/* Resumen numérico */}
      <div className="grid grid-cols-3 gap-2">
        <div className="bg-white/70 backdrop-blur-sm rounded-lg p-2 text-center">
          <p className="text-xs text-gray-600">Promedio</p>
          <p className="text-lg font-bold text-gray-900">
            {(data.reduce((sum, d) => sum + d.ndvi_mean, 0) / data.length).toFixed(3)}
          </p>
        </div>
        <div className="bg-white/70 backdrop-blur-sm rounded-lg p-2 text-center">
          <p className="text-xs text-gray-600">Mínimo</p>
          <p className="text-lg font-bold text-orange-600">
            {Math.min(...data.map(d => d.ndvi_mean)).toFixed(3)}
          </p>
        </div>
        <div className="bg-white/70 backdrop-blur-sm rounded-lg p-2 text-center">
          <p className="text-xs text-gray-600">Máximo</p>
          <p className="text-lg font-bold text-green-600">
            {Math.max(...data.map(d => d.ndvi_mean)).toFixed(3)}
          </p>
        </div>
      </div>

      {/* Nota sobre análisis */}
      <div className="mt-4 text-xs text-gray-500 text-center">
        {data.length} análisis en este período
      </div>

      {/* Botón de cálculo batch si hay fechas faltantes */}
      {missingDates > 0 && !isCalculatingBatch && (
        <div className="mt-4">
          <button
            onClick={calculateBatch}
            className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition-colors flex items-center justify-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Calcular NDVIs faltantes ({missingDates} fechas)
          </button>
        </div>
      )}

      {/* Progress de batch */}
      {isCalculatingBatch && (
        <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-3">
          <div className="flex items-center gap-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
            <p className="text-sm text-blue-700">{batchProgress}</p>
          </div>
        </div>
      )}
    </div>
  );
}
