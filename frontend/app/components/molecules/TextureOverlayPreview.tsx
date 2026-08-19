'use client';

import Image from 'next/image';
import { useOverlay } from '@/app/context/OverlayContext';
import { useTextureOverlayPreview } from '@/app/hooks/useOverlayPreview';
import type { TextureKernelType } from '@/lib/overlayTypes';

interface SatelliteData {
  image_base64: string;
  bounds: [[number, number], [number, number]];
  cached: boolean;
}

interface TextureOverlayPreviewProps {
  ndviResultId?: number | null;
  showSatellite?: boolean;
  satelliteData?: SatelliteData | null;
  satelliteOnly?: boolean;
}

const kernelOptions: Array<{ value: TextureKernelType; label: string }> = [
  { value: 'contrast', label: 'Contraste' },
  { value: 'edges', label: 'Bordes' },
  { value: 'homogeneity', label: 'Homogeneidad' },
];

const legend = [
  { label: 'Uniforme', color: 'bg-blue-500' },
  { label: 'Moderado', color: 'bg-violet-500' },
  { label: 'Heterogéneo', color: 'bg-orange-500' },
];

export default function TextureOverlayPreview({ ndviResultId, showSatellite, satelliteData, satelliteOnly }: TextureOverlayPreviewProps) {
  const { setTextureKernel, textureKernel } = useOverlay();
  const preview = useTextureOverlayPreview(ndviResultId);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <label className="text-xs font-semibold text-violet-900">
          Descriptor
          <select
            className="ml-2 rounded-lg border border-violet-300 bg-white px-3 py-1.5 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-violet-500"
            onChange={(event) => setTextureKernel(event.target.value as TextureKernelType)}
            value={textureKernel}
          >
            {kernelOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
        </label>
        <button
          aria-busy={preview.isRefreshing}
          className="rounded-lg border border-violet-300 bg-white px-3 py-1.5 text-xs font-semibold text-violet-800 hover:bg-violet-50 disabled:cursor-wait disabled:opacity-60"
          disabled={preview.isRefreshing || !ndviResultId}
          onClick={() => void preview.recalculate()}
          type="button"
        >
          {preview.isRefreshing && <span aria-hidden="true" className="mr-2 inline-block h-3 w-3 animate-spin rounded-full border-2 border-violet-200 border-t-violet-700" />}
          Recalcular visualización
        </button>
      </div>

      {preview.status === 'loading' && <div aria-label="Cargando visualización de textura" className="aspect-square w-full animate-pulse rounded-xl bg-violet-100" role="status" />}
      {preview.status === 'empty' && <p className="rounded-xl border border-dashed border-violet-300 bg-white/70 p-6 text-center text-sm text-gray-600">No hay datos calculados para esta fecha.</p>}
      {(preview.status === 'error' || (!preview.data && preview.status === 'success')) && (
        <p className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700" role="alert">{preview.error ?? 'No se pudo cargar la visualización de textura.'}</p>
      )}
      {preview.data && preview.status === 'success' && (
        <>
          <p className="rounded-lg border border-violet-200 bg-white/80 p-3 text-sm text-gray-700">{preview.data.interpretation}</p>
          <div className="relative aspect-square w-full overflow-hidden rounded-xl border border-violet-200 bg-white">
            {showSatellite && satelliteData && (
              <Image
                alt="Imagen satélite de fondo"
                className="absolute inset-0 h-full w-full object-contain"
                fill
                sizes="(min-width: 1024px) 40vw, 90vw"
                src={satelliteData.image_base64}
                unoptimized
              />
            )}
            <Image
              alt={`Mapa de textura: ${textureKernel}`}
              className="object-contain"
              fill
              sizes="(min-width: 1024px) 40vw, 90vw"
              src={preview.data.image_base64}
              style={satelliteOnly ? { opacity: 0 } : (showSatellite && satelliteData ? { opacity: 0.7 } : undefined)}
              unoptimized
            />
            {preview.isRefreshing && <div aria-hidden="true" className="absolute inset-0 animate-pulse bg-white/20" />}
          </div>
          <div aria-label="Leyenda de textura" className="flex flex-wrap justify-center gap-x-4 gap-y-2 text-xs text-gray-700">
            {legend.map((item) => <span className="flex items-center gap-1.5" key={item.label}><span aria-hidden="true" className={`h-3 w-3 rounded-sm ${item.color}`} />{item.label}</span>)}
          </div>
          {preview.error && <p className="rounded-lg bg-red-50 p-3 text-xs text-red-700" role="alert">{preview.error}</p>}
        </>
      )}
    </div>
  );
}
