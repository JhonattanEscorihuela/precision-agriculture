'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react';
import { useAuth } from '@/app/context/AuthContext';
import OverlayToast from '@/app/components/atoms/OverlayToast';
import apiClient from '@/lib/axios';
import type {
  NDVIOverlayResponse,
  TextureKernelType,
  TextureOverlayResponse,
} from '@/lib/overlayTypes';

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

interface OverlayContextValue {
  textureKernel: TextureKernelType;
  setTextureKernel: (kernel: TextureKernelType) => void;
  getCachedNDVIOverlay: (acquisitionId: number) => NDVIOverlayResponse | null;
  getCachedTextureOverlay: (
    ndviResultId: number,
    kernel: TextureKernelType
  ) => TextureOverlayResponse | null;
  getCachedSatelliteImage: (acquisitionId: number) => SatelliteImageResponse | null;
  fetchNDVIOverlay: (acquisitionId: number, force?: boolean) => Promise<NDVIOverlayResponse>;
  fetchTextureOverlay: (
    ndviResultId: number,
    kernel: TextureKernelType,
    force?: boolean
  ) => Promise<TextureOverlayResponse>;
  fetchSatelliteImage: (acquisitionId: number, force?: boolean) => Promise<SatelliteImageResponse>;
  showOverlayError: (message: string) => void;
}

const OverlayContext = createContext<OverlayContextValue | undefined>(undefined);

export function OverlayProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const ownerId = user?.id ?? null;
  const ownerRef = useRef<number | null>(ownerId);
  const generationRef = useRef(0);
  const ndviCache = useRef(new Map<number, NDVIOverlayResponse>());
  const textureCache = useRef(new Map<string, TextureOverlayResponse>());
  const satelliteCache = useRef(new Map<number, SatelliteImageResponse>());
  const inFlight = useRef(new Map<string, Promise<unknown>>());
  const writeVersions = useRef(new Map<string, number>());
  const [textureKernel, setTextureKernel] = useState<TextureKernelType>('contrast');
  const [toast, setToast] = useState<{ id: number; message: string } | null>(null);

  const ensureOwner = useCallback(() => {
    if (ownerRef.current === ownerId) return;
    ownerRef.current = ownerId;
    generationRef.current += 1;
    ndviCache.current.clear();
    textureCache.current.clear();
    satelliteCache.current.clear();
    inFlight.current.clear();
    writeVersions.current.clear();
  }, [ownerId]);

  useEffect(() => ensureOwner(), [ensureOwner]);

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => setToast(null), 5000);
    return () => window.clearTimeout(timer);
  }, [toast]);

  const showOverlayError = useCallback((message: string) => {
    setToast({ id: Date.now(), message });
  }, []);

  const getCachedNDVIOverlay = useCallback((acquisitionId: number) => {
    ensureOwner();
    return ndviCache.current.get(acquisitionId) ?? null;
  }, [ensureOwner]);

  const getCachedTextureOverlay = useCallback((id: number, kernel: TextureKernelType) => {
    ensureOwner();
    return textureCache.current.get(`${id}:${kernel}`) ?? null;
  }, [ensureOwner]);

  const getCachedSatelliteImage = useCallback((acquisitionId: number) => {
    ensureOwner();
    return satelliteCache.current.get(acquisitionId) ?? null;
  }, [ensureOwner]);

  const fetchNDVIOverlay = useCallback(async (id: number, force = false) => {
    ensureOwner();
    const cached = ndviCache.current.get(id);
    if (cached && !force) return cached;
    const requestKey = `ndvi:${id}:${force ? 'force' : 'normal'}`;
    const pending = inFlight.current.get(requestKey) as Promise<NDVIOverlayResponse> | undefined;
    if (pending) return pending;
    const cacheKey = `ndvi:${id}`;
    const version = (writeVersions.current.get(cacheKey) ?? 0) + 1;
    const generation = generationRef.current;
    writeVersions.current.set(cacheKey, version);
    const request = apiClient
      .get<NDVIOverlayResponse>(`/api/ndvi/${id}/overlay`, { params: { force } })
      .then(({ data }) => {
        if (generation === generationRef.current && writeVersions.current.get(cacheKey) === version) {
          ndviCache.current.set(id, data);
        }
        return data;
      });
    inFlight.current.set(requestKey, request);
    const clearRequest = () => {
      if (inFlight.current.get(requestKey) === request) inFlight.current.delete(requestKey);
    };
    void request.then(clearRequest, clearRequest);
    return request;
  }, [ensureOwner]);

  const fetchTextureOverlay = useCallback(async (
    id: number,
    kernel: TextureKernelType,
    force = false
  ) => {
    ensureOwner();
    const cacheKey = `${id}:${kernel}`;
    const cached = textureCache.current.get(cacheKey);
    if (cached && !force) return cached;
    const requestKey = `texture:${cacheKey}:${force ? 'force' : 'normal'}`;
    const pending = inFlight.current.get(requestKey) as Promise<TextureOverlayResponse> | undefined;
    if (pending) return pending;
    const writeKey = `texture:${cacheKey}`;
    const version = (writeVersions.current.get(writeKey) ?? 0) + 1;
    const generation = generationRef.current;
    writeVersions.current.set(writeKey, version);
    const request = apiClient
      .get<TextureOverlayResponse>(`/api/texture/overlay/${id}`, {
        params: { kernel, force },
      })
      .then(({ data }) => {
        if (generation === generationRef.current && writeVersions.current.get(writeKey) === version) {
          textureCache.current.set(cacheKey, data);
        }
        return data;
      });
    inFlight.current.set(requestKey, request);
    const clearRequest = () => {
      if (inFlight.current.get(requestKey) === request) inFlight.current.delete(requestKey);
    };
    void request.then(clearRequest, clearRequest);
    return request;
  }, [ensureOwner]);

  const fetchSatelliteImage = useCallback(async (acquisitionId: number, force = false) => {
    ensureOwner();
    const cached = satelliteCache.current.get(acquisitionId);
    if (cached && !force) return cached;
    const requestKey = `satellite:${acquisitionId}:${force ? 'force' : 'normal'}`;
    const pending = inFlight.current.get(requestKey) as Promise<SatelliteImageResponse> | undefined;
    if (pending) return pending;
    const cacheKey = `satellite:${acquisitionId}`;
    const version = (writeVersions.current.get(cacheKey) ?? 0) + 1;
    const generation = generationRef.current;
    writeVersions.current.set(cacheKey, version);
    const request = apiClient
      .get<SatelliteImageResponse>(`/api/ndvi/${acquisitionId}/satellite-image`, {
        params: { force },
      })
      .then(({ data }) => {
        if (generation === generationRef.current && writeVersions.current.get(cacheKey) === version) {
          satelliteCache.current.set(acquisitionId, data);
        }
        return data;
      });
    inFlight.current.set(requestKey, request);
    const clearRequest = () => {
      if (inFlight.current.get(requestKey) === request) inFlight.current.delete(requestKey);
    };
    void request.then(clearRequest, clearRequest);
    return request;
  }, [ensureOwner]);

  return (
    <OverlayContext.Provider value={{
      textureKernel,
      setTextureKernel,
      getCachedNDVIOverlay,
      getCachedTextureOverlay,
      getCachedSatelliteImage,
      fetchNDVIOverlay,
      fetchTextureOverlay,
      fetchSatelliteImage,
      showOverlayError,
    }}>
      {children}
      {toast && <OverlayToast message={toast.message} onDismiss={() => setToast(null)} />}
    </OverlayContext.Provider>
  );
}

export function useOverlay(): OverlayContextValue {
  const context = useContext(OverlayContext);
  if (!context) throw new Error('useOverlay debe usarse dentro de OverlayProvider');
  return context;
}
