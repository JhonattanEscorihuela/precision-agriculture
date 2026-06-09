/**
 * Hook para obtener el estado de salud de parcelas basado en NDVI.
 */

import { useState, useEffect } from 'react';
import { useAuth } from '@/app/context/AuthContext';
import axios from 'axios';

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

  useEffect(() => {
    const fetchHealth = async () => {
      if (!token || polygonIds.length === 0) {
        setIsLoading(false);
        return;
      }

      const healthData: PolygonHealth = {};

      // Consultar último NDVI de cada parcela
      for (const polygonId of polygonIds) {
        try {
          const response = await axios.get(
            `http://localhost:8000/api/ndvi/polygon/${polygonId}?limit=1`,
            {
              headers: { Authorization: `Bearer ${token}` }
            }
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
        } catch (err: any) {
          if (err.response?.status === 404) {
            // No hay NDVI para esta parcela
            healthData[polygonId] = {
              status: 'unknown',
              ndvi: null,
              lastUpdate: null
            };
          } else {
            healthData[polygonId] = {
              status: 'unknown',
              ndvi: null,
              lastUpdate: null
            };
          }
        }
      }

      setHealth(healthData);
      setIsLoading(false);
    };

    fetchHealth();
  }, [polygonIds, token]);

  return { health, isLoading };
}
