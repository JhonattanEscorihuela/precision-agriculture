export type QualityStatus = 'suitable' | 'caution' | 'unsuitable' | null;

interface AnalysisQualityInput {
  quality_status?: QualityStatus;
  cloud_mask_applied?: boolean;
}

export function isAnalysisEligible(input: AnalysisQualityInput): boolean {
  return input.quality_status === 'suitable' && input.cloud_mask_applied === true;
}

export function getQualityLabel(status: QualityStatus): string | null {
  if (status === 'suitable') return 'Apta';
  if (status === 'caution') return 'Precaución';
  if (status === 'unsuitable') return 'No apta';
  return null;
}
