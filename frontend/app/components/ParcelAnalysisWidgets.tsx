'use client';

import { useParcelAnalysis } from '@/app/hooks/useParcelAnalysis';
import NDVIEvolutionWidget from '@/app/components/organisms/NDVIEvolutionWidget';
import SegmentationPanel from '@/app/components/organisms/SegmentationPanel';
import FenologicalComparisonWidget from '@/app/components/organisms/FenologicalComparisonWidget';
import TextureWidget from '@/app/components/organisms/TextureWidget';

interface ParcelAnalysisWidgetsProps {
  polygonId: number;
  polygonName: string;
  polygonCoordinates: number[][];
}

export default function ParcelAnalysisWidgets({
  polygonId,
  polygonName,
  polygonCoordinates,
}: ParcelAnalysisWidgetsProps) {
  const { latestNDVI, segmentation, texture, phenology, retry } = useParcelAnalysis(polygonId);

  return (
    <>
      <NDVIEvolutionWidget
        polygonId={polygonId}
        polygonName={polygonName}
        polygonCoordinates={polygonCoordinates}
        onAnalysisUpdated={retry}
      />
      <SegmentationPanel
        acquisitionId={latestNDVI.data?.acquisition_id}
        state={segmentation}
        onRetry={retry}
      />
      <TextureWidget
        ndviResultId={latestNDVI.data?.ndvi_result_id}
        state={texture}
        onRetry={retry}
      />
      <FenologicalComparisonWidget state={phenology} onRetry={retry} />
    </>
  );
}
