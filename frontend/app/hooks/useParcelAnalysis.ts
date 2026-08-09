'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { isAxiosError } from 'axios';
import { useAuth } from '@/app/context/AuthContext';
import { useDateRange } from '@/app/context/DateRangeContext';
import apiClient from '@/lib/axios';
import type {
  NDVISummary,
  PhenologyComparison,
  ResourceState,
  SegmentationResult,
  TextureDescriptor,
  UseParcelAnalysisResult,
} from '@/lib/analysisTypes';

interface ApiErrorResponse {
  detail?: string;
}

const loadingState = <T,>(): ResourceState<T> => ({
  status: 'loading',
  data: null,
  error: null,
});

const emptyState = <T,>(message: string): ResourceState<T> => ({
  status: 'empty',
  data: null,
  error: message,
});

const errorState = <T,>(message: string): ResourceState<T> => ({
  status: 'error',
  data: null,
  error: message,
});

const successState = <T,>(data: T): ResourceState<T> => ({
  status: 'success',
  data,
  error: null,
});

function getStatusCode(error: unknown): number | undefined {
  return isAxiosError<ApiErrorResponse>(error) ? error.response?.status : undefined;
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (isAxiosError<ApiErrorResponse>(error)) {
    return error.response?.data?.detail || fallback;
  }

  return error instanceof Error ? error.message : fallback;
}

function getPhenologyEmptyMessage(error: unknown): string {
  const detail = isAxiosError<ApiErrorResponse>(error)
    ? error.response?.data?.detail
    : undefined;

  if (detail?.includes('No NDVI data')) {
    return 'No hay resultados NDVI suficientes para comparar esta parcela.';
  }

  return detail || 'No hay datos suficientes para realizar la comparación fenológica.';
}

function formatApiDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

async function getOrCreateSegmentation(ndviResultId: number): Promise<SegmentationResult> {
  try {
    const response = await apiClient.get<SegmentationResult>(
      `/api/segmentation/by-ndvi/${ndviResultId}`
    );
    return response.data;
  } catch (error: unknown) {
    if (getStatusCode(error) !== 404) throw error;
  }

  const response = await apiClient.post<SegmentationResult>('/api/segmentation/analyze', {
    ndvi_result_id: ndviResultId,
    threshold: 0.3,
    save_mask: false,
  });
  return response.data;
}

async function getOrCreateTexture(segmentationId: number): Promise<TextureDescriptor[]> {
  try {
    const response = await apiClient.get<TextureDescriptor[]>(
      `/api/texture/by-segmentation/${segmentationId}`
    );
    return response.data;
  } catch (error: unknown) {
    if (getStatusCode(error) !== 404) throw error;
  }

  const response = await apiClient.post<TextureDescriptor[]>('/api/texture/analyze', {
    segmentation_result_id: segmentationId,
  });
  return response.data;
}

export function useParcelAnalysis(polygonId: number): UseParcelAnalysisResult {
  const { token, isLoading: isAuthLoading } = useAuth();
  const { getStartDate, getEndDate } = useDateRange();
  const startDate = formatApiDate(getStartDate());
  const endDate = formatApiDate(getEndDate());
  const requestVersion = useRef(0);

  const [latestNDVI, setLatestNDVI] = useState<ResourceState<NDVISummary>>(loadingState);
  const [segmentation, setSegmentation] = useState<ResourceState<SegmentationResult>>(
    loadingState
  );
  const [texture, setTexture] = useState<ResourceState<TextureDescriptor[]>>(loadingState);
  const [phenology, setPhenology] = useState<ResourceState<PhenologyComparison>>(loadingState);

  const loadSpatialAnalysis = useCallback(async (version: number): Promise<void> => {
    let latestNDVI: NDVISummary | undefined;

    try {
      const response = await apiClient.get<NDVISummary[]>(`/api/ndvi/polygon/${polygonId}`, {
        params: { start_date: startDate, end_date: endDate, limit: 1 },
      });
      [latestNDVI] = response.data;
    } catch (error: unknown) {
      if (requestVersion.current !== version) return;
      const message = getErrorMessage(error, 'No se pudo consultar el NDVI de la parcela.');
      setLatestNDVI(errorState(message));
      setSegmentation(errorState(message));
      setTexture(errorState(message));
      return;
    }

    if (!latestNDVI) {
      if (requestVersion.current !== version) return;
      const message = 'No hay resultados NDVI en el periodo seleccionado.';
      setLatestNDVI(emptyState(message));
      setSegmentation(emptyState(message));
      setTexture(emptyState(message));
      return;
    }

    if (requestVersion.current !== version) return;
    setLatestNDVI(successState(latestNDVI));

    let segmentationResult: SegmentationResult;

    try {
      segmentationResult = await getOrCreateSegmentation(latestNDVI.ndvi_result_id);
    } catch (error: unknown) {
      if (requestVersion.current !== version) return;
      setSegmentation(errorState(
        getErrorMessage(error, 'No se pudo calcular la segmentación de la parcela.')
      ));
      setTexture(emptyState('La textura requiere una segmentación disponible.'));
      return;
    }

    if (requestVersion.current !== version) return;
    setSegmentation(successState(segmentationResult));

    try {
      const descriptors = await getOrCreateTexture(segmentationResult.id);
      if (requestVersion.current !== version) return;
      setTexture(descriptors.length > 0
        ? successState(descriptors)
        : emptyState('No hay descriptores de textura disponibles.'));
    } catch (error: unknown) {
      if (requestVersion.current !== version) return;
      setTexture(errorState(
        getErrorMessage(error, 'No se pudieron calcular los descriptores de textura.')
      ));
    }
  }, [endDate, polygonId, startDate]);

  const loadPhenology = useCallback(async (version: number): Promise<void> => {
    try {
      const response = await apiClient.get<PhenologyComparison>(
        `/api/phenology/compare/${polygonId}`
      );
      if (requestVersion.current !== version) return;
      setPhenology(response.data.curve_data.length > 0
        ? successState(response.data)
        : emptyState('No hay puntos suficientes para mostrar la comparación fenológica.'));
    } catch (error: unknown) {
      if (requestVersion.current !== version) return;
      const isEmpty = getStatusCode(error) === 400;
      const message = isEmpty
        ? getPhenologyEmptyMessage(error)
        : getErrorMessage(error, 'No se pudo cargar la comparación fenológica.');
      setPhenology(isEmpty ? emptyState(message) : errorState(message));
    }
  }, [polygonId]);

  const retry = useCallback(async (): Promise<void> => {
    const version = requestVersion.current + 1;
    requestVersion.current = version;

    setSegmentation(loadingState());
    setTexture(loadingState());
    setPhenology(loadingState());
    setLatestNDVI(loadingState());

    if (!token) {
      const message = 'Debes iniciar sesión para consultar los análisis.';
      setLatestNDVI(errorState(message));
      setSegmentation(errorState(message));
      setTexture(errorState(message));
      setPhenology(errorState(message));
      return;
    }

    await Promise.all([
      loadSpatialAnalysis(version),
      loadPhenology(version),
    ]);
  }, [loadPhenology, loadSpatialAnalysis, token]);

  useEffect(() => {
    if (isAuthLoading) return;

    let isActive = true;
    const startLoading = async () => {
      await Promise.resolve();
      if (isActive) await retry();
    };

    void startLoading();
    return () => {
      isActive = false;
      requestVersion.current += 1;
    };
  }, [isAuthLoading, retry]);

  return { latestNDVI, segmentation, texture, phenology, retry };
}
