export type ResourceStatus = 'loading' | 'success' | 'empty' | 'error';

export interface ResourceState<T> {
  status: ResourceStatus;
  data: T | null;
  error: string | null;
}

export interface NDVISummary {
  ndvi_result_id: number;
  acquisition_id: number;
  polygon_id: number;
  acquisition_date: string;
  calculation_date: string;
  ndvi_mean: number;
  ndvi_min: number;
  ndvi_max: number;
  ndvi_std: number;
  ndvi_median?: number | null;
  ndvi_p10?: number | null;
  ndvi_p90?: number | null;
  width: number;
  height: number;
  analysis_valid_pixel_percentage?: number | null;
  cloud_mask_applied?: boolean;
  quality_status?: 'suitable' | 'caution' | 'unsuitable' | null;
  parcel_cloud_cover?: number | null;
  usable_pixel_percentage?: number | null;
}

export interface SegmentationResult {
  id: number;
  ndvi_result_id: number;
  acquisition_id: number;
  polygon_id: number;
  calculation_date: string;
  threshold_used: number;
  total_pixels: number;
  cultivated_pixels: number;
  cultivated_percentage: number;
  tiff_binary_mask: string | null;
  has_binary_mask: boolean;
}

export type TextureKernelType = 'edges' | 'homogeneity' | 'contrast';

export interface TextureDescriptor {
  id: number;
  segmentation_result_id: number;
  polygon_id: number;
  kernel_type: TextureKernelType;
  mean: number;
  std: number;
  min_val: number;
  max_val: number;
  std_normalized: number;
  discriminative: boolean;
  calculation_date: string;
}

export interface PhenologyCurvePoint {
  date: string;
  days_since_first_observation: number;
  ndvi_parcel: number;
  ndvi_reference: number;
}

export interface PhenologyComparison {
  polygon_id: number;
  reference_polygon_ids: number[];
  dates_compared: number;
  similarity_score: number | null;
  matches_rice_pattern: boolean | null;
  sufficient_for_classification: boolean;
  observation_span_days: number;
  minimum_observations: number;
  minimum_span_days: number;
  reference_source: string;
  alignment_method: string;
  warnings: string[];
  classification: string;
  curve_data: PhenologyCurvePoint[];
}

export interface UseParcelAnalysisResult {
  latestNDVI: ResourceState<NDVISummary>;
  segmentation: ResourceState<SegmentationResult>;
  texture: ResourceState<TextureDescriptor[]>;
  phenology: ResourceState<PhenologyComparison>;
  retry: () => Promise<void>;
}
