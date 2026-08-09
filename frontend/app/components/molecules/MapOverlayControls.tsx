'use client';

import type { OverlayMode, TextureKernelType } from '@/lib/overlayTypes';

interface MapOverlayControlsProps {
  mode: OverlayMode;
  textureKernel: TextureKernelType;
  onModeChange: (mode: OverlayMode) => void;
  onTextureKernelChange: (kernel: TextureKernelType) => void;
}

const overlayOptions: Array<{ value: OverlayMode; label: string }> = [
  { value: 'none', label: 'Ninguno' },
  { value: 'ndvi', label: 'NDVI' },
  { value: 'texture', label: 'Textura' },
];

const kernelOptions: Array<{ value: TextureKernelType; label: string }> = [
  { value: 'contrast', label: 'Contraste' },
  { value: 'edges', label: 'Bordes' },
  { value: 'homogeneity', label: 'Homogeneidad' },
];

export default function MapOverlayControls({
  mode,
  textureKernel,
  onModeChange,
  onTextureKernelChange,
}: MapOverlayControlsProps) {
  return (
    <fieldset className="flex flex-wrap items-center gap-3 rounded-xl border border-gray-200 bg-white/95 p-3 shadow-md">
      <legend className="sr-only">Capa de análisis del mapa</legend>
      {overlayOptions.map((option) => (
        <label
          key={option.value}
          className="flex cursor-pointer items-center gap-2 text-sm font-medium text-gray-700"
        >
          <input
            type="radio"
            name="map-overlay"
            value={option.value}
            checked={mode === option.value}
            onChange={() => onModeChange(option.value)}
            className="h-4 w-4 accent-emerald-600"
          />
          {option.label}
        </label>
      ))}

      {mode === 'texture' && (
        <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
          <span>Descriptor</span>
          <select
            value={textureKernel}
            onChange={(event) => onTextureKernelChange(event.target.value as TextureKernelType)}
            className="rounded-lg border border-gray-300 bg-white px-2 py-1.5 text-sm text-gray-800 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200"
            aria-label="Descriptor de textura"
          >
            {kernelOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      )}
    </fieldset>
  );
}
