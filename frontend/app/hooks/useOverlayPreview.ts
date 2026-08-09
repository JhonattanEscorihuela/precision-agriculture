'use client';

import { useCallback, useEffect, useState } from 'react';
import { isAxiosError } from 'axios';
import { useOverlay } from '@/app/context/OverlayContext';
import type {
  NDVIOverlayResponse,
  TextureKernelType,
  TextureOverlayResponse,
} from '@/lib/overlayTypes';

type PreviewStatus = 'loading' | 'success' | 'empty' | 'error';

export interface OverlayPreview<T> {
  status: PreviewStatus;
  data: T | null;
  error: string | null;
  isRefreshing: boolean;
  recalculate: () => Promise<void>;
}

interface PreviewState<T> {
  key: string;
  status: PreviewStatus;
  data: T | null;
  error: string | null;
}

interface PreviewConfig<T> {
  cacheKey: string;
  enabled: boolean;
  emptyMessage: string;
  fallbackError: string;
  getCached: () => T | null;
  fetchData: (force: boolean) => Promise<T>;
  showError: (message: string) => void;
}

const getErrorMessage = (error: unknown, fallback: string) => {
  if (isAxiosError<{ detail?: string }>(error)) return error.response?.data?.detail ?? fallback;
  return error instanceof Error ? error.message : fallback;
};

const isNotFound = (error: unknown) =>
  isAxiosError(error) && error.response?.status === 404;

function initialState<T>(config: PreviewConfig<T>): PreviewState<T> {
  if (!config.enabled) {
    return { key: config.cacheKey, status: 'empty', data: null, error: config.emptyMessage };
  }
  const cached = config.getCached();
  return cached
    ? { key: config.cacheKey, status: 'success', data: cached, error: null }
    : { key: config.cacheKey, status: 'loading', data: null, error: null };
}

function usePreview<T>(config: PreviewConfig<T>): OverlayPreview<T> {
  const {
    cacheKey,
    emptyMessage,
    enabled,
    fallbackError,
    fetchData,
    getCached,
    showError,
  } = config;
  const [state, setState] = useState<PreviewState<T>>(() => initialState(config));
  const [refreshingKey, setRefreshingKey] = useState<string | null>(null);
  const visibleState = state.key === cacheKey ? state : initialState(config);

  useEffect(() => {
    let active = true;
    const load = async () => {
      const cached = enabled ? getCached() : null;
      if (!enabled) {
        if (active) setState({ key: cacheKey, status: 'empty', data: null, error: emptyMessage });
        return;
      }
      if (cached) {
        if (active) setState({ key: cacheKey, status: 'success', data: cached, error: null });
        return;
      }
      if (active) setState({ key: cacheKey, status: 'loading', data: null, error: null });
      try {
        const data = await fetchData(false);
        if (active) setState({ key: cacheKey, status: 'success', data, error: null });
      } catch (error: unknown) {
        if (!active) return;
        const empty = isNotFound(error);
        const message = empty ? emptyMessage : getErrorMessage(error, fallbackError);
        setState({ key: cacheKey, status: empty ? 'empty' : 'error', data: null, error: message });
        if (!empty) showError(message);
      }
    };
    void Promise.resolve().then(load);
    return () => { active = false; };
  }, [cacheKey, emptyMessage, enabled, fallbackError, fetchData, getCached, showError]);

  const recalculate = useCallback(async () => {
    if (!enabled) return;
    const previous = getCached();
    setRefreshingKey(cacheKey);
    try {
      const data = await fetchData(true);
      setState({ key: cacheKey, status: 'success', data, error: null });
    } catch (error: unknown) {
      const empty = isNotFound(error);
      const message = empty ? emptyMessage : getErrorMessage(error, fallbackError);
      setState(previous
        ? { key: cacheKey, status: 'success', data: previous, error: message }
        : { key: cacheKey, status: empty ? 'empty' : 'error', data: null, error: message });
      showError(message);
    } finally {
      setRefreshingKey((key) => key === cacheKey ? null : key);
    }
  }, [cacheKey, emptyMessage, enabled, fallbackError, fetchData, getCached, showError]);

  return {
    status: visibleState.status,
    data: visibleState.data,
    error: visibleState.error,
    isRefreshing: refreshingKey === cacheKey,
    recalculate,
  };
}

export function useNDVIOverlayPreview(acquisitionId?: number | null) {
  const { fetchNDVIOverlay, getCachedNDVIOverlay, showOverlayError } = useOverlay();
  const enabled = typeof acquisitionId === 'number' && acquisitionId > 0;
  const getCached = useCallback(
    () => enabled ? getCachedNDVIOverlay(acquisitionId ?? 0) : null,
    [acquisitionId, enabled, getCachedNDVIOverlay]
  );
  const fetchData = useCallback(
    (force: boolean) => fetchNDVIOverlay(acquisitionId ?? 0, force),
    [acquisitionId, fetchNDVIOverlay]
  );
  return usePreview<NDVIOverlayResponse>({
    cacheKey: `ndvi:${acquisitionId ?? 'none'}`,
    enabled,
    emptyMessage: 'No hay datos calculados para esta fecha.',
    fallbackError: 'No se pudo cargar la visualización NDVI.',
    getCached,
    fetchData,
    showError: showOverlayError,
  });
}

export function useTextureOverlayPreview(
  ndviResultId?: number | null,
  kernelOverride?: TextureKernelType
) {
  const {
    fetchTextureOverlay,
    getCachedTextureOverlay,
    showOverlayError,
    textureKernel,
  } = useOverlay();
  const kernel = kernelOverride ?? textureKernel;
  const enabled = typeof ndviResultId === 'number' && ndviResultId > 0;
  const getCached = useCallback(
    () => enabled ? getCachedTextureOverlay(ndviResultId ?? 0, kernel) : null,
    [enabled, getCachedTextureOverlay, kernel, ndviResultId]
  );
  const fetchData = useCallback(
    (force: boolean) => fetchTextureOverlay(ndviResultId ?? 0, kernel, force),
    [fetchTextureOverlay, kernel, ndviResultId]
  );
  return usePreview<TextureOverlayResponse>({
    cacheKey: `texture:${ndviResultId ?? 'none'}:${kernel}`,
    enabled,
    emptyMessage: 'No hay datos calculados para esta fecha.',
    fallbackError: 'No se pudo cargar la visualización de textura.',
    getCached,
    fetchData,
    showError: showOverlayError,
  });
}
