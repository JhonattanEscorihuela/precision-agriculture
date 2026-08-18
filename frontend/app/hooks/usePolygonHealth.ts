/**
 * Hook para obtener el estado de salud de parcelas basado en NDVI.
 */

import { useState, useEffect } from 'react';
import { useAuth } from '@/app/context/AuthContext';
import apiClient from '@/lib/axios';

interface PolygonHealth {
  [polygonId: number]: {
    status: 'healthy' | 'alert' | 'critical' | 'unknown';
    ndvi: number | null;
    lastUpdate: string | null;
  };
}

/**
 * Obtiene el estado de salud de todas las parcelas basado en último NDVI calculado.
 *
 * Clasificación:
 * - healthy: NDVI >= 0.5 (vegetación saludable)
 * - alert: NDVI >= 0.3 (vegetación moderada, revisar)
 * - critical: NDVI < 0.3 (vegetación escasa o sin vegetación)
 * - unknown: No hay NDVI calculado
 */
export function usePolygonHealth(polygonIds: number[]) {
  const { token } = useAuth();
  const [health, setHealth] = useState<PolygonHealth>({});
  const [isLoading, setIsLoading] = useState(true);
  const polygonIdsKey = polygonIds.join(',');

  useEffect(() => {
    const fetchHealth = async () => {
      const requestedPolygonIds = polygonIdsKey
        .split(',')
        .filter(Boolean)
        .map(Number);

      if (!token || requestedPolygonIds.length === 0) {
        setIsLoading(false);
        return;
      }


      const healthData: PolygonHealth = {};

      // Consultar último NDVI de cada parcela
      for (const polygonId of requestedPolygonIds) {
        try {
          const response = await apiClient.get(
            `/api/ndvi/polygon/${polygonId}?limit=1`
          );

          if (response.data && response.data.length > 0) {
            const latestNDVI = response.data[0];
            const ndviMean = latestNDVI.ndvi_mean;

            // Clasificar según valor NDVI
            let status: 'healthy' | 'alert' | 'critical' = 'healthy';
            if (ndviMean < 0.3) {
              status = 'critical';
            } else if (ndviMean < 0.5) {
              status = 'alert';
            }

            healthData[polygonId] = {
              status,
              ndvi: ndviMean,
              lastUpdate: latestNDVI.acquisition_date
            };
          } else {
            // No hay NDVI calculado
            healthData[polygonId] = {
              status: 'unknown',
              ndvi: null,
              lastUpdate: null
            };
          }
        } catch {
          healthData[polygonId] = {
            status: 'unknown',
            ndvi: null,
            lastUpdate: null
          };
        }
      }

      setHealth(healthData);
      setIsLoading(false);
    };

    fetchHealth();
  }, [polygonIdsKey, token]);

  return { health, isLoading };
}
