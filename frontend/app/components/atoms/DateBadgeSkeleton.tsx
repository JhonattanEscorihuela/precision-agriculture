'use client';

/**
 * OE1 - Atom: Skeleton para DateBadge durante carga
 * Imita visualmente DateBadge con bloques animados
 */
export default function DateBadgeSkeleton() {
  return (
    <div className="
      relative px-3 py-2 rounded-lg border-2
      bg-gray-50 border-gray-200
      cursor-default animate-pulse
    ">
      <div className="flex flex-col items-center gap-1">
        {/* Bloque fecha (grande) */}
        <div className="h-5 w-14 bg-gray-300 rounded" />

        {/* Bloque año (pequeño) */}
        <div className="h-3 w-10 bg-gray-200 rounded" />
      </div>
    </div>
  );
}
