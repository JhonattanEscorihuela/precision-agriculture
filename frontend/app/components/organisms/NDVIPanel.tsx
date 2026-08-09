/**
 * OE2 - Panel completo de visualización y cálculo NDVI.
 * Organism component (< 200 líneas)
 */

'use client';

import { useCallback, useEffect, useState } from 'react';
import { isAxiosError } from 'axios';
import { useAuth } from '@/app/context/AuthContext';
import apiClient from '@/lib/axios';
import NDVIStats from '../molecules/NDVIStats';
import NDVIColorScale from '../molecules/NDVIColorScale';

interface NDVIPanelProps {
  acquisitionId: number;
  polygonId: number;
  onClose?: () => void;
  onCalculated?: () => void;
}

type PanelState = 'idle' | 'loading' | 'calculated' | 'error';

interface NDVIData {
  ndvi_id: number;
  calculation_date: string;
  stats: {
    ndvi_mean: number;
    ndvi_min: number;
    ndvi_max: number;
    ndvi_std: number;
  };
}

interface ExistingNDVIResponse {
  ndvi_result_id: number;
  acquisition_id: number;
  calculation_date: string;
  ndvi_mean: number;
  ndvi_min: number;
  ndvi_max: number;
  ndvi_std: number;
}

interface ApiErrorResponse {
  detail?: string;
}

function getAxiosError(error: unknown) {
  return isAxiosError<ApiErrorResponse>(error) ? error : null;
}

/**
 * Panel completo para cálculo y visualización de NDVI.
 *
 * State machine:
 * - idle: Sin NDVI calculado, muestra botón "Calcular NDVI"
 * - loading: Calculando NDVI, muestra spinner
 * - calculated: NDVI disponible, muestra estadísticos + escala + descarga
 * - error: Error en cálculo, muestra mensaje

 * Workflow:
 * 1. Al montar: GET /api/ndvi/{acquisition_id}
 *    - Si existe (200) → estado 'calculated'
 *    - Si no existe (404) → estado 'idle'
 * 2. Usuario click "Calcular NDVI" → POST /api/ndvi/calculate
 * 3. Usuario vuelve a abrir → muestra stats sin recalcular
 */
export default function NDVIPanel({ acquisitionId, onClose, onCalculated }: NDVIPanelProps) {
  const { token } = useAuth();
  const [state, setState] = useState<PanelState>('loading');
  const [ndviData, setNdviData] = useState<NDVIData | null>(null);
  const [error, setError] = useState<string>('');
  const [alreadyFetched, setAlreadyFetched] = useState(false); // Caché local

  const checkExistingNDVI = useCallback(async (): Promise<void> => {
    async function check(retryCount: number): Promise<void> {
      if (!token) {
        if (retryCount < 3) {
          setTimeout(() => void check(retryCount + 1), 300);
          return;
        }
        setError('No autenticado');
        setState('error');
        return;
      }

      try {
        const response = await apiClient.get<ExistingNDVIResponse>(
          `/api/ndvi/${acquisitionId}`
        );
        const data = response.data;
        setNdviData({
          ndvi_id: data.ndvi_result_id,
          calculation_date: data.calculation_date,
          stats: {
            ndvi_mean: data.ndvi_mean,
            ndvi_min: data.ndvi_min,
            ndvi_max: data.ndvi_max,
            ndvi_std: data.ndvi_std
          }
        });
        setState('calculated');
        setAlreadyFetched(true);
      } catch (error: unknown) {
        const requestError = getAxiosError(error);
        if (requestError?.response?.status === 404) {
          setState('idle');
          setAlreadyFetched(true);
        } else if (requestError?.response?.status === 401) {
          if (retryCount < 2) {
            setTimeout(() => void check(retryCount + 1), 500);
            return;
          }
          setError('Sesión expirada. Por favor, inicia sesión nuevamente');
          setState('error');
        } else {
          if (retryCount < 1) {
            setTimeout(() => void check(retryCount + 1), 300);
            return;
          }
          setError('Error al verificar NDVI existente');
          setState('error');
        }
      }
    }

    await check(0);
  }, [acquisitionId, token]);

  useEffect(() => {
    if (!alreadyFetched) {
      void checkExistingNDVI();
    }
  }, [alreadyFetched, checkExistingNDVI]);

  const calculateNDVI = async () => {
    if (!token) {
      setError('No autenticado');
      setState('error');
      return;
    }

    setState('loading');
    setError('');

    try {
      const response = await apiClient.post<NDVIData>('/api/ndvi/calculate', {
        acquisition_id: acquisitionId
      });

      setNdviData({
        ndvi_id: response.data.ndvi_id,
        calculation_date: response.data.calculation_date,
        stats: response.data.stats
      });
      setState('calculated');
      onCalculated?.();
    } catch (error: unknown) {
      const requestError = getAxiosError(error);
      if (requestError?.response?.status === 401) {
        setError('Sesión expirada. Por favor, inicia sesión nuevamente');
      } else {
        setError(requestError?.response?.data?.detail || 'Error al calcular NDVI');
      }
      setState('error');
    }
  };

  const downloadTIFF = async () => {
    if (!token) {
      setError('No autenticado');
      return;
    }

    try {
      const response = await apiClient.get<Blob>(
        `/api/ndvi/${acquisitionId}/tiff`,
        {
          responseType: 'blob'
        }
      );

      // Crear link de descarga
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `ndvi_acquisition_${acquisitionId}.tif`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error: unknown) {
      const requestError = getAxiosError(error);
      if (requestError?.response?.status === 401) {
        setError('Sesión expirada');
      } else {
        setError('Error al descargar TIFF');
      }
    }
  };

  return (
    <div className="bg-gradient-to-br from-emerald-50 to-green-50 rounded-xl p-6 border border-emerald-200 shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🌿</span>
          <h3 className="text-lg font-bold text-gray-900">Análisis NDVI</h3>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Content según estado */}
      <div className="space-y-4">
        {state === 'loading' && (
          <div className="flex flex-col items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mb-4"></div>
            <p className="text-gray-600 text-sm">Calculando índice NDVI...</p>
            <p className="text-gray-500 text-xs mt-2">Esto puede tomar unos segundos</p>
          </div>
        )}

        {state === 'idle' && (
          <div className="text-center py-8">
            <div className="text-4xl mb-4">📊</div>
            <p className="text-gray-600 mb-6">
              Calcula el índice NDVI para analizar la salud de la vegetación
            </p>
            <button
              onClick={calculateNDVI}
              className="
                px-6 py-3 rounded-lg
                bg-emerald-600 hover:bg-emerald-700
                text-white font-semibold
                shadow-md hover:shadow-lg
                transition-all duration-200
                flex items-center gap-2 mx-auto
              "
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Calcular NDVI
            </button>
          </div>
        )}

        {state === 'calculated' && ndviData && (
          <>
            {/* Metadata */}
            <div className="text-xs text-gray-500 border-b border-emerald-200 pb-2">
              Calculado el {new Date(ndviData.calculation_date).toLocaleDateString('es-ES', {
                day: '2-digit',
                month: 'long',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              })}
            </div>

            {/* Escala de colores */}
            <NDVIColorScale />

            {/* Estadísticos */}
            <NDVIStats
              stats={ndviData.stats}
              onDownload={downloadTIFF}
            />

          </>
        )}

        {state === 'error' && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <svg className="w-6 h-6 text-red-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-red-900 mb-1">Error</h4>
                <p className="text-sm text-red-700">{error}</p>
                <button
                  onClick={() => void checkExistingNDVI()}
                  className="mt-3 text-sm text-red-600 hover:text-red-800 underline"
                >
                  Reintentar
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
