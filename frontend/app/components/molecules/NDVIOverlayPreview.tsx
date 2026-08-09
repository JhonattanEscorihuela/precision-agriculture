'use client';

import Image from 'next/image';
import { useNDVIOverlayPreview } from '@/app/hooks/useOverlayPreview';

interface NDVIOverlayPreviewProps {
  acquisitionId?: number | null;
}

const legend = [
  { label: 'Sano (≥ 0.5)', color: 'bg-green-600' },
  { label: 'Alerta (0.3–0.5)', color: 'bg-yellow-500' },
  { label: 'Crítico (< 0.3)', color: 'bg-red-600' },
];

export default function NDVIOverlayPreview({ acquisitionId }: NDVIOverlayPreviewProps) {
  const preview = useNDVIOverlayPreview(acquisitionId);

  if (preview.status === 'loading') {
    return (
      <div aria-label="Cargando visualización NDVI" className="aspect-square w-full animate-pulse rounded-xl bg-emerald-100" role="status" />
    );
  }

  if (preview.status === 'empty') {
    return <p className="rounded-xl border border-dashed border-emerald-300 bg-white/70 p-6 text-center text-sm text-gray-600">No hay datos calculados para esta fecha.</p>;
  }

  if (preview.status === 'error' || !preview.data) {
    return <p className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700" role="alert">{preview.error ?? 'No se pudo cargar la visualización NDVI.'}</p>;
  }

  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <button
          aria-busy={preview.isRefreshing}
          className="rounded-lg border border-emerald-300 bg-white px-3 py-1.5 text-xs font-semibold text-emerald-800 hover:bg-emerald-50 disabled:cursor-wait disabled:opacity-60"
          disabled={preview.isRefreshing}
          onClick={() => void preview.recalculate()}
          type="button"
        >
          {preview.isRefreshing && <span aria-hidden="true" className="mr-2 inline-block h-3 w-3 animate-spin rounded-full border-2 border-emerald-200 border-t-emerald-700" />}
          Recalcular visualización
        </button>
      </div>
      <div className="relative aspect-square w-full overflow-hidden rounded-xl border border-emerald-200 bg-white">
        <Image
          alt="Mapa NDVI coloreado de la parcela"
          className="object-contain"
          fill
          sizes="(min-width: 1024px) 40vw, 90vw"
          src={preview.data.image_base64}
          unoptimized
        />
        {preview.isRefreshing && <div aria-hidden="true" className="absolute inset-0 animate-pulse bg-white/20" />}
      </div>
      <div aria-label="Leyenda NDVI" className="flex flex-wrap justify-center gap-x-4 gap-y-2 text-xs text-gray-700">
        {legend.map((item) => (
          <span className="flex items-center gap-1.5" key={item.label}>
            <span aria-hidden="true" className={`h-3 w-3 rounded-sm ${item.color}`} />
            {item.label}
          </span>
        ))}
      </div>
      {preview.error && <p className="rounded-lg bg-red-50 p-3 text-xs text-red-700" role="alert">{preview.error}</p>}
    </div>
  );
}
