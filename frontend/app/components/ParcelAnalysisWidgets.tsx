'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParcelAnalysis } from '@/app/hooks/useParcelAnalysis';
import { useDateRange } from '@/app/context/DateRangeContext';
import NDVIEvolutionWidget from '@/app/components/organisms/NDVIEvolutionWidget';
import SegmentationPanel from '@/app/components/organisms/SegmentationPanel';
import FenologicalComparisonWidget from '@/app/components/organisms/FenologicalComparisonWidget';
import TextureWidget from '@/app/components/organisms/TextureWidget';
import apiClient from '@/lib/axios';
import type { NDVISummary, ResourceState, SegmentationResult, TextureDescriptor } from '@/lib/analysisTypes';
import { isAxiosError } from 'axios';

interface ParcelAnalysisWidgetsProps {
  polygonId: number;
  polygonName: string;
  polygonCoordinates: number[][];
}

function formatApiDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

const loadingState = <T,>(): ResourceState<T> => ({
  status: 'loading',
  data: null,
  error: null,
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

async function getOrCreateSegmentation(ndviResultId: number): Promise<SegmentationResult> {
  try {
    const response = await apiClient.get<SegmentationResult>(
      `/api/segmentation/by-ndvi/${ndviResultId}`
    );
    return response.data;
  } catch (error: unknown) {
    if (isAxiosError(error) && error.response?.status === 404) {
      const response = await apiClient.post<SegmentationResult>('/api/segmentation/analyze', {
        ndvi_result_id: ndviResultId,
        threshold: 0.3,
        save_mask: false,
      });
      return response.data;
    }
    throw error;
  }
}

async function getOrCreateTexture(segmentationId: number): Promise<TextureDescriptor[]> {
  try {
    const response = await apiClient.get<TextureDescriptor[]>(
      `/api/texture/by-segmentation/${segmentationId}`
    );
    return response.data;
  } catch (error: unknown) {
    if (isAxiosError(error) && error.response?.status === 404) {
      const response = await apiClient.post<TextureDescriptor[]>('/api/texture/analyze', {
        segmentation_result_id: segmentationId,
      });
      return response.data;
    }
    throw error;
  }
}

export default function ParcelAnalysisWidgets({
  polygonId,
  polygonName,
  polygonCoordinates,
}: ParcelAnalysisWidgetsProps) {
  const { latestNDVI, phenology, retry: retryAll } = useParcelAnalysis(polygonId);
  const { getStartDate, getEndDate } = useDateRange();

  const [availableDates, setAvailableDates] = useState<NDVISummary[]>([]);
  const [selectedDate, setSelectedDate] = useState<NDVISummary | null>(null);
  const [segmentation, setSegmentation] = useState<ResourceState<SegmentationResult>>(loadingState());
  const [texture, setTexture] = useState<ResourceState<TextureDescriptor[]>>(loadingState());

  // Cargar fechas disponibles
  useEffect(() => {
    const loadAvailableDates = async () => {
      try {
        const startDate = formatApiDate(getStartDate());
        const endDate = formatApiDate(getEndDate());
        const response = await apiClient.get<NDVISummary[]>(`/api/ndvi/polygon/${polygonId}`, {
          params: { start_date: startDate, end_date: endDate },
        });
        setAvailableDates(response.data);

        if (response.data.length > 0 && !selectedDate) {
          setSelectedDate(response.data[0]);
        }
      } catch (error) {
        setAvailableDates([]);
      }
    };

    void loadAvailableDates();
  }, [polygonId, getStartDate, getEndDate]);

  // Sincronizar con latestNDVI cuando cambia
  useEffect(() => {
    if (latestNDVI.data && !selectedDate) {
      setSelectedDate(latestNDVI.data);
    }
  }, [latestNDVI.data, selectedDate]);

  // Cargar análisis de la fecha seleccionada
  const loadSelectedDateAnalysis = useCallback(async (ndviSummary: NDVISummary) => {
    setSegmentation(loadingState());
    setTexture(loadingState());

    try {
      const segResult = await getOrCreateSegmentation(ndviSummary.ndvi_result_id);
      setSegmentation(successState(segResult));

      try {
        const textureResult = await getOrCreateTexture(segResult.id);
        setTexture(successState(textureResult));
      } catch (err) {
        setTexture(errorState('No se pudo cargar la textura'));
      }
    } catch (err) {
      setSegmentation(errorState('No se pudo cargar la segmentación'));
      setTexture(errorState('Requiere segmentación'));
    }
  }, []);

  // Recargar cuando cambia la fecha seleccionada
  useEffect(() => {
    if (selectedDate) {
      void loadSelectedDateAnalysis(selectedDate);
    }
  }, [selectedDate, loadSelectedDateAnalysis]);

  const handleDateChange = (acquisitionId: number) => {
    const newDate = availableDates.find(d => d.acquisition_id === acquisitionId);
    if (newDate) {
      setSelectedDate(newDate);
    }
  };

  return (
    <>
      <NDVIEvolutionWidget
        polygonId={polygonId}
        polygonName={polygonName}
        polygonCoordinates={polygonCoordinates}
        onAnalysisUpdated={retryAll}
      />
      <SegmentationPanel
        acquisitionId={selectedDate?.acquisition_id}
        availableDates={availableDates}
        onDateChange={handleDateChange}
        state={segmentation}
        onRetry={() => selectedDate && loadSelectedDateAnalysis(selectedDate)}
      />
      <TextureWidget
        ndviResultId={selectedDate?.ndvi_result_id}
        acquisitionId={selectedDate?.acquisition_id}
        availableDates={availableDates}
        onDateChange={handleDateChange}
        state={texture}
        onRetry={() => selectedDate && loadSelectedDateAnalysis(selectedDate)}
      />
      <FenologicalComparisonWidget state={phenology} onRetry={retryAll} />
    </>
  );
}
