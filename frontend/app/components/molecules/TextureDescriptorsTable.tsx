/** OE4 - Tabla de descriptores de textura reales. */

import type { TextureDescriptor } from '@/lib/analysisTypes';

interface TextureDescriptorsTableProps {
  descriptors: TextureDescriptor[];
}

const descriptorLabels: Record<string, string> = {
  edges: 'Bordes (Laplaciano)',
  homogeneity: 'Homogeneidad',
  contrast: 'Contraste',
};

export default function TextureDescriptorsTable({ descriptors }: TextureDescriptorsTableProps) {
  return (
    <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 text-xs uppercase tracking-wide text-gray-600">
            <tr>
              <th className="px-4 py-3 font-semibold">Descriptor</th>
              <th className="px-4 py-3 text-right font-semibold">Media</th>
              <th className="px-4 py-3 text-right font-semibold">Desv. Est.</th>
              <th className="px-4 py-3 text-right font-semibold">Rango</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {descriptors.map((descriptor) => (
              <tr
                className={descriptor.discriminative
                  ? 'border-l-4 border-l-emerald-500 bg-emerald-50'
                  : 'border-l-4 border-l-transparent bg-white'}
                key={descriptor.id}
              >
                <th className="whitespace-nowrap px-4 py-3 font-medium text-gray-900">
                  {descriptorLabels[descriptor.kernel_type] ?? descriptor.kernel_type}
                </th>
                <td className="px-4 py-3 text-right tabular-nums text-gray-700">{descriptor.mean.toFixed(3)}</td>
                <td className="px-4 py-3 text-right tabular-nums text-gray-700">{descriptor.std.toFixed(3)}</td>
                <td className="px-4 py-3 text-right tabular-nums text-gray-700">
                  {(descriptor.max_val - descriptor.min_val).toFixed(3)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
