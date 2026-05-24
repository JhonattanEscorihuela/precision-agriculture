'use client';

import React from 'react';

interface DateBadgeProps {
  date: string;
  isSelected: boolean;
  isAcquired: boolean;
  onClick: () => void;
}

/**
 * OE1 - Atom: Badge para mostrar una fecha disponible
 * Componente mínimo clickeable con estado seleccionado y adquirido
 */
export default function DateBadge({ date, isSelected, isAcquired, onClick }: DateBadgeProps) {
  // Formatear fecha para mostrar solo día/mes
  const formatDate = (dateStr: string) => {
    const [year, month, day] = dateStr.split('-');
    return `${day}/${month}`;
  };

  return (
    <button
      onClick={onClick}
      className={`
        px-3 py-2 rounded-lg border-2 text-sm font-medium
        transition-all duration-200 relative
        ${isSelected
          ? 'bg-emerald-600 text-white border-emerald-600 shadow-md'
          : isAcquired
          ? 'bg-blue-50 text-blue-700 border-blue-300 hover:border-blue-500'
          : 'bg-white text-gray-700 border-gray-300 hover:border-emerald-500 hover:shadow-sm'
        }
      `}
    >
      {isAcquired && (
        <div className="absolute -top-1 -right-1 w-4 h-4 bg-blue-500 rounded-full flex items-center justify-center">
          <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        </div>
      )}
      <div className="text-center">
        <div className="font-semibold">{formatDate(date)}</div>
        <div className="text-xs opacity-80">{date.split('-')[0]}</div>
      </div>
    </button>
  );
}
