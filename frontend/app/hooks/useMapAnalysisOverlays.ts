'use client';

import { useCallback, useEffect, useRef, type RefObject } from 'react';
import { isAxiosError } from 'axios';
import L from 'leaflet';
import { useOverlay } from '@/app/context/OverlayContext';
import type { Polygon } from '@/app/context/PolygonContext';
import apiClient from '@/lib/axios';
import type { NDVISummary } from '@/lib/analysisTypes';
import type { OverlayMode, TextureKernelType } from '@/lib/overlayTypes';

interface MapAnalysisOverlaysOptions {
  mapRef: RefObject<L.Map | null>;
  polygons: Polygon[];
  polygonLayersRef: RefObject<Map<number, L.Polygon>>;
  mode: OverlayMode;
  textureKernel: TextureKernelType;
  refreshVersion: number;
}

const isNotFound = (error: unknown) =>
  isAxiosError(error) && error.response?.status === 404;

const errorMessage = (error: unknown) => {
  if (isAxiosError<{ detail?: string }>(error)) {
    return error.response?.data?.detail ?? 'No se pudo cargar la capa de análisis.';
  }
  return error instanceof Error ? error.message : 'No se pudo cargar la capa de análisis.';
};

export default function useMapAnalysisOverlays({
  mapRef,
  polygons,
  polygonLayersRef,
  mode,
  textureKernel,
  refreshVersion,
}: MapAnalysisOverlaysOptions) {
  const {
    getCachedNDVIOverlay,
    getCachedTextureOverlay,
    fetchNDVIOverlay,
    fetchTextureOverlay,
    showOverlayError,
  } = useOverlay();
  const layerGroupRef = useRef<L.LayerGroup | null>(null);
  const latestRef = useRef(new Map<number, NDVISummary | null>());
  const latestRequestsRef = useRef(new Map<number, Promise<NDVISummary | null>>());
  const requestVersionRef = useRef(0);
  const previousRefreshRef = useRef(refreshVersion);

  const clearLayers = useCallback(() => {
    layerGroupRef.current?.clearLayers();
    polygonLayersRef.current?.forEach((layer) => layer.bringToFront());
  }, [polygonLayersRef]);

  const getLatest = useCallback(async (polygonId: number) => {
    if (latestRef.current.has(polygonId)) return latestRef.current.get(polygonId) ?? null;
    const pending = latestRequestsRef.current.get(polygonId);
    if (pending) return pending;
    const request = apiClient
      .get<NDVISummary[]>(`/api/ndvi/polygon/${polygonId}`, { params: { limit: 1 } })
      .then(({ data }) => data[0] ?? null);
    latestRequestsRef.current.set(polygonId, request);
    try {
      const latest = await request;
      latestRef.current.set(polygonId, latest);
      return latest;
    } finally {
      latestRequestsRef.current.delete(polygonId);
    }
  }, []);

  const loadVisible = useCallback(async (version: number) => {
    const map = mapRef.current;
    if (!map || mode === 'none' || !layerGroupRef.current) return;
    let errorShown = false;
    const visible = polygons.filter(({ id }) => {
      const polygonLayer = polygonLayersRef.current?.get(id);
      return polygonLayer ? map.getBounds().intersects(polygonLayer.getBounds()) : false;
    });

    await Promise.all(visible.map(async ({ id }) => {
      const polygonLayer = polygonLayersRef.current?.get(id);
      const group = layerGroupRef.current;
      if (!polygonLayer || !group) return;
      const known = latestRef.current.get(id);
      const cached = known && mode === 'ndvi'
        ? getCachedNDVIOverlay(known.acquisition_id)
        : known && mode === 'texture'
          ? getCachedTextureOverlay(known.ndvi_result_id, textureKernel)
          : null;
      let spinner: L.Marker | null = null;
      if (!cached && !(latestRef.current.has(id) && known === null)) {
        spinner = L.marker(polygonLayer.getBounds().getCenter(), {
          interactive: false,
          icon: L.divIcon({
            className: '',
            html: '<span class="block h-7 w-7 animate-spin rounded-full border-4 border-white border-t-emerald-600 shadow"></span>',
            iconSize: [28, 28],
            iconAnchor: [14, 14],
          }),
        }).addTo(group);
      }
      try {
        const latest = known ?? await getLatest(id);
        if (!latest || version !== requestVersionRef.current) return;
        const data = mode === 'ndvi'
          ? getCachedNDVIOverlay(latest.acquisition_id)
            ?? await fetchNDVIOverlay(latest.acquisition_id)
          : getCachedTextureOverlay(latest.ndvi_result_id, textureKernel)
            ?? await fetchTextureOverlay(latest.ndvi_result_id, textureKernel);
        if (version !== requestVersionRef.current || !layerGroupRef.current) return;
        L.imageOverlay(data.image_base64, data.bounds, { opacity: 0.7, interactive: false })
          .addTo(layerGroupRef.current);
      } catch (error: unknown) {
        if (!isNotFound(error) && !errorShown && version === requestVersionRef.current) {
          errorShown = true;
          showOverlayError(errorMessage(error));
        }
      } finally {
        spinner?.remove();
        polygonLayer.bringToFront();
      }
    }));
  }, [
    fetchNDVIOverlay,
    fetchTextureOverlay,
    getCachedNDVIOverlay,
    getCachedTextureOverlay,
    getLatest,
    mapRef,
    mode,
    polygonLayersRef,
    polygons,
    showOverlayError,
    textureKernel,
  ]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const group = L.layerGroup().addTo(map);
    layerGroupRef.current = group;
    return () => {
      requestVersionRef.current += 1;
      group.remove();
      if (layerGroupRef.current === group) layerGroupRef.current = null;
    };
  }, [mapRef]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (previousRefreshRef.current !== refreshVersion) {
      latestRef.current.clear();
      previousRefreshRef.current = refreshVersion;
    }
    const reload = () => {
      const version = ++requestVersionRef.current;
      clearLayers();
      if (mode !== 'none') void loadVisible(version);
    };
    reload();
    let timer: ReturnType<typeof setTimeout> | undefined;
    const onMoveEnd = () => {
      if (timer) clearTimeout(timer);
      timer = setTimeout(reload, 250);
    };
    map.on('moveend', onMoveEnd);
    return () => {
      if (timer) clearTimeout(timer);
      map.off('moveend', onMoveEnd);
      requestVersionRef.current += 1;
      clearLayers();
    };
  }, [clearLayers, loadVisible, mapRef, mode, refreshVersion, textureKernel]);
}
