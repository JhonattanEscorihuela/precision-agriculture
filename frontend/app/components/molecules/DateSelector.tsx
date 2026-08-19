'use client';

import React from 'react';
import DateBadge from '../atoms/DateBadge';
import DateBadgeSkeleton from '../atoms/DateBadgeSkeleton';

interface DateInfo {
  date: string;
  cloud_cover: number;
  scene_id: string;
  acquired: boolean;
  ndvi_calculated: boolean;
  parcel_cloud_cover: number | null;
  parcel_shadow_cover: number | null;
  valid_pixel_percentage: number | null;
  usable_pixel_percentage: number | null;
  quality_status: 'suitable' | 'caution' | 'unsuitable' | null;
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
      <div className="min-h-48">
        <div className="grid grid-cols-2 gap-2">
          {Array.from({ length: 8 }).map((_, idx) => (
            <DateBadgeSkeleton key={idx} />
          ))}
        </div>
      </div>
    );
  }

  if (!dates || dates.length === 0) {
    return (
      <div className="min-h-48 flex items-center justify-center">
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-center">
          <p className="text-amber-800 text-sm">
            No encontramos imágenes disponibles en este período.
          </p>
          <p className="text-amber-600 text-xs mt-1">
            Intenta ampliar el rango de fechas.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-48 space-y-2">
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
            sceneCloudCover={dateInfo.cloud_cover}
            parcelCloudCover={dateInfo.parcel_cloud_cover}
            parcelShadowCover={dateInfo.parcel_shadow_cover}
            validPixelPercentage={dateInfo.valid_pixel_percentage}
            usablePixelPercentage={dateInfo.usable_pixel_percentage}
            qualityStatus={dateInfo.quality_status}
            onClick={() => onSelectDate(dateInfo.date)}
          />
        ))}
      </div>
    </div>
  );
}
