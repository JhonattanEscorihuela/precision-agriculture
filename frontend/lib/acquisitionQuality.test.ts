import { describe, expect, it } from 'vitest';

import { getQualityLabel, isAnalysisEligible } from './acquisitionQuality';

describe('isAnalysisEligible', () => {
  it('accepts only suitable acquisitions with the SCL mask applied', () => {
    expect(isAnalysisEligible({ quality_status: 'suitable', cloud_mask_applied: true })).toBe(true);
    expect(isAnalysisEligible({ quality_status: 'suitable', cloud_mask_applied: false })).toBe(false);
    expect(isAnalysisEligible({ quality_status: 'caution', cloud_mask_applied: true })).toBe(false);
    expect(isAnalysisEligible({ quality_status: 'unsuitable', cloud_mask_applied: true })).toBe(false);
  });
});

describe('getQualityLabel', () => {
  it('uses the labels shown in the Sentinel interface', () => {
    expect(getQualityLabel('suitable')).toBe('Apta');
    expect(getQualityLabel('caution')).toBe('Precaución');
    expect(getQualityLabel('unsuitable')).toBe('No apta');
    expect(getQualityLabel(null)).toBeNull();
  });
});
