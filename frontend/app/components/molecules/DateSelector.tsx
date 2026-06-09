'use client';

import React from 'react';
import DateBadge from '../atoms/DateBadge';

interface DateInfo {
  date: string;
  cloud_cover: number;
  acquired: boolean;
  ndvi_calculated: boolean;
}

interface DateSelectorProps {
  dates: DateInfo[];
  selectedDate: string | null;
  isLoading: boolean;
  onSelectDate: (date: string) => void;
}

/**
 * OE1 - Molecule: Selector de fechas disponibles
 * Muestra lista de DateBadge con estado de carga
 */
export default function DateSelector({
  dates,
  selectedDate,
  isLoading,
  onSelectDate
}: DateSelectorProps) {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-8 space-y-3">
        <svg className="animate-spin h-8 w-8 text-emerald-600" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        <p className="text-gray-600 text-sm">Consultando fechas disponibles...</p>
      </div>
    );
  }

  if (!dates || dates.length === 0) {
    return (
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-center">
        <p className="text-amber-800 text-sm">
          No encontramos imágenes disponibles en este período.
        </p>
        <p className="text-amber-600 text-xs mt-1">
          Intenta ampliar el rango de fechas.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-sm text-gray-600 font-medium mb-3">
        {dates.length} {dates.length === 1 ? 'fecha disponible' : 'fechas disponibles'}
      </p>
      <div className="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto pr-2">
        {dates.map((dateInfo) => (
          <DateBadge
            key={dateInfo.date}
            date={dateInfo.date}
            isSelected={selectedDate === dateInfo.date}
            isAcquired={dateInfo.acquired}
            ndviCalculated={dateInfo.ndvi_calculated}
            onClick={() => onSelectDate(dateInfo.date)}
          />
        ))}
      </div>
    </div>
  );
}
