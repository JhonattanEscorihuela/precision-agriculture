import { useEffect, useState, useCallback, useRef } from 'react';
import { useOverlay } from '@/app/context/OverlayContext';

interface SatelliteImageResponse {
  image_base64: string;
  bounds: [[number, number], [number, number]];
  cached: boolean;
  metadata: {
    date: string;
    polygon_id: number;
    type: 'true_color';
  };
}

interface UseSatelliteImageResult {
  data: SatelliteImageResponse | null;
  loading: boolean;
  error: string | null;
  load: (force?: boolean) => Promise<void>;
}

export function useSatelliteImage(
  acquisitionId?: number | null
): UseSatelliteImageResult {
  const { fetchSatelliteImage, getCachedSatelliteImage, showOverlayError } = useOverlay();
  const [data, setData] = useState<SatelliteImageResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const currentAcquisitionRef = useRef<number | null>(null);

  const load = useCallback(async (force = false) => {
    if (!acquisitionId) {
      setError('No acquisition ID provided');
      return;
    }

    const cached = getCachedSatelliteImage(acquisitionId);
    if (cached && !force) {
      setData(cached);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await fetchSatelliteImage(acquisitionId, force);
      // Solo actualizar si seguimos en el mismo acquisition
      if (currentAcquisitionRef.current === acquisitionId) {
        setData(result);
      }
    } catch (err) {
      if (currentAcquisitionRef.current === acquisitionId) {
        const message = err instanceof Error ? err.message : 'Error loading satellite image';
        setError(message);
        showOverlayError(message);
      }
    } finally {
      if (currentAcquisitionRef.current === acquisitionId) {
        setLoading(false);
      }
    }
  }, [acquisitionId, fetchSatelliteImage, getCachedSatelliteImage, showOverlayError]);

  useEffect(() => {
    currentAcquisitionRef.current = acquisitionId ?? null;

    if (!acquisitionId) {
      setData(null);
      setError(null);
      setLoading(false);
      return;
    }

    const cached = getCachedSatelliteImage(acquisitionId);
    if (cached) {
      setData(cached);
      setError(null);
      setLoading(false);
    } else {
      void load(false);
    }
  }, [acquisitionId, getCachedSatelliteImage, load]);

  return { data, loading, error, load };
}
