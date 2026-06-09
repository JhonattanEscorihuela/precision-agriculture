'use client';

import React from 'react';

interface DateBadgeProps {
  date: string;
  isSelected: boolean;
  isAcquired: boolean;
  ndviCalculated?: boolean;
  onClick: () => void;
}

/**
 * OE1 - Atom: Badge para mostrar una fecha disponible.
 *
 * Estados:
 * - Verde: NDVI calculado (ndviCalculated=true)
 * - Azul: Bandas adquiridas (isAcquired=true, sin NDVI)
 * - Gris: Solo disponible (necesita adquirir primero)
 */
export default function DateBadge({ date, isSelected, isAcquired, ndviCalculated, onClick }: DateBadgeProps) {
  // Formatear fecha para mostrar solo día/mes
  const formatDate = (dateStr: string) => {
    const [year, month, day] = dateStr.split('-');
    return `${day}/${month}`;
  };

  // Determinar color y badge según estado
  const getBadgeStyle = () => {
    if (isSelected) {
      return 'bg-emerald-600 text-white border-emerald-600 shadow-md';
    }
    if (ndviCalculated) {
      // Verde: NDVI calculado
      return 'bg-green-50 text-green-700 border-green-400 hover:border-green-600';
    }
    if (isAcquired) {
      // Azul: Solo bandas adquiridas
      return 'bg-blue-50 text-blue-700 border-blue-300 hover:border-blue-500';
    }
    // Gris: Solo disponible
    return 'bg-white text-gray-700 border-gray-300 hover:border-emerald-500 hover:shadow-sm';
  };

  const getBadgeIcon = () => {
    if (ndviCalculated) {
      // Badge verde con checkmark doble
      return (
        <div className="absolute -top-1 -right-1 w-5 h-5 bg-green-600 rounded-full flex items-center justify-center shadow-sm">
          <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        </div>
      );
    }
    if (isAcquired) {
      // Badge azul con checkmark simple
      return (
        <div className="absolute -top-1 -right-1 w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center shadow-sm">
          <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        </div>
      );
    }
    return null;
  };

  return (
    <button
      onClick={onClick}
      className={`
        px-3 py-2 rounded-lg border-2 text-sm font-medium
        transition-all duration-200 relative
        ${getBadgeStyle()}
      `}
      title={
        ndviCalculated
          ? '✓ NDVI calculado'
          : isAcquired
          ? '✓ Bandas adquiridas'
          : 'Disponible para adquirir'
      }
    >
      {getBadgeIcon()}
      <div className="text-center">
        <div className="font-semibold">{formatDate(date)}</div>
        <div className="text-xs opacity-80">{date.split('-')[0]}</div>
      </div>
    </button>
  );
}
