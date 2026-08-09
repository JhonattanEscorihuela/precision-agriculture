import type { TextureKernelType } from '@/lib/analysisTypes';

export type { TextureKernelType };

export type LeafletBounds = [
  [southLatitude: number, westLongitude: number],
  [northLatitude: number, eastLongitude: number],
];

interface OverlayMetadata {
  date: string | null;
  polygon_id: number;
}

export interface NDVIOverlayResponse {
  image_base64: string;
  bounds: LeafletBounds;
  cached: boolean;
  metadata: OverlayMetadata & {
    thresholds: {
      critical: number;
      alert: number;
    };
  };
}

export interface TextureOverlayResponse {
  image_base64: string;
  bounds: LeafletBounds;
  kernel: TextureKernelType;
  cached: boolean;
  interpretation: string;
  metadata: OverlayMetadata & {
    thresholds_percentiles: [number, number];
  };
}

export type OverlayMode = 'none' | 'ndvi' | 'texture';
