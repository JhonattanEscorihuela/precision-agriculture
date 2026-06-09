/**
 * Filtro de rango temporal tipo AWS CloudWatch.
 * Soporta rangos relativos (1w, 2m, etc) y absolutos (desde-hasta).
 */

'use client';

import { useState } from 'react';
import { useDateRange, DateRangeMode, RelativeRange } from '@/app/context/DateRangeContext';

/**
 * Componente de filtro de rango temporal.
 * Se muestra en la esquina superior derecha del dashboard.
 */
export default function DateRangeFilter() {
  const { range, setRange, getFormattedRange, isLoading } = useDateRange();
  const [isOpen, setIsOpen] = useState(false);
  const [tempMode, setTempMode] = useState<DateRangeMode>(range.mode);
  const [tempRelative, setTempRelative] = useState<RelativeRange>(range.relative || '2m');
  const [tempStartDate, setTempStartDate] = useState(range.startDate || '');
  const [tempEndDate, setTempEndDate] = useState(range.endDate || '');

  const relativeOptions: { value: RelativeRange; label: string }[] = [
    { value: '1w', label: 'Última semana' },
    { value: '2w', label: 'Últimas 2 semanas' },
    { value: '3w', label: 'Últimas 3 semanas' },
    { value: '4w', label: 'Últimas 4 semanas' },
    { value: '1m', label: 'Último mes' },
    { value: '2m', label: 'Últimos 2 meses' },
    { value: '3m', label: 'Últimos 3 meses' },
    { value: '6m', label: 'Últimos 6 meses' },
    { value: '1y', label: 'Último año (máx)' }
  ];

  const handleApply = () => {
    if (tempMode === 'relative') {
      setRange({
        mode: 'relative',
        relative: tempRelative
      });
    } else {
      if (!tempStartDate || !tempEndDate) {
        alert('Selecciona ambas fechas');
        return;
      }
      if (new Date(tempStartDate) >= new Date(tempEndDate)) {
        alert('La fecha de inicio debe ser anterior a la fecha final');
        return;
      }
      setRange({
        mode: 'absolute',
        startDate: tempStartDate,
        endDate: tempEndDate
      });
    }
    setIsOpen(false);
  };

  const handleCancel = () => {
    // Restaurar valores actuales
    setTempMode(range.mode);
    setTempRelative(range.relative || '2m');
    setTempStartDate(range.startDate || '');
    setTempEndDate(range.endDate || '');
    setIsOpen(false);
  };

  return (
    <div className="relative">
      {/* Botón principal */}
      <button
        onClick={() => !isLoading && setIsOpen(!isOpen)}
        disabled={isLoading}
        className="
          flex items-center gap-2 px-4 py-2
          bg-white border border-gray-300 rounded-lg
          transition-all shadow-sm
          text-sm font-medium text-gray-700
          disabled:opacity-50 disabled:cursor-not-allowed
          enabled:hover:bg-gray-50 enabled:hover:border-gray-400
        "
      >
        {isLoading ? (
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        ) : (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        )}
        <span className="hidden sm:inline">{isLoading ? 'Cargando...' : getFormattedRange()}</span>
        <span className="sm:hidden">{isLoading ? '...' : 'Rango'}</span>
        {!isLoading && (
          <svg className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        )}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <>
          {/* Overlay */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* Panel */}
          <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-xl border border-gray-200 z-50">
            {/* Tabs */}
            <div className="flex border-b border-gray-200">
              <button
                onClick={() => setTempMode('relative')}
                className={`
                  flex-1 px-4 py-3 text-sm font-medium transition-colors
                  ${tempMode === 'relative'
                    ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50/50'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }
                `}
              >
                Relativo
              </button>
              <button
                onClick={() => setTempMode('absolute')}
                className={`
                  flex-1 px-4 py-3 text-sm font-medium transition-colors
                  ${tempMode === 'absolute'
                    ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50/50'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }
                `}
              >
                Absoluto
              </button>
            </div>

            {/* Content */}
            <div className="p-4">
              {tempMode === 'relative' ? (
                <div className="space-y-2">
                  {relativeOptions.map((option) => (
                    <button
                      key={option.value}
                      onClick={() => setTempRelative(option.value)}
                      className={`
                        w-full text-left px-3 py-2 rounded-md text-sm transition-colors
                        ${tempRelative === option.value
                          ? 'bg-blue-100 text-blue-900 font-medium'
                          : 'hover:bg-gray-100 text-gray-700'
                        }
                      `}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              ) : (
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Fecha inicio
                    </label>
                    <input
                      type="date"
                      value={tempStartDate}
                      onChange={(e) => setTempStartDate(e.target.value)}
                      max={new Date().toISOString().split('T')[0]}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Fecha fin
                    </label>
                    <input
                      type="date"
                      value={tempEndDate}
                      onChange={(e) => setTempEndDate(e.target.value)}
                      max={new Date().toISOString().split('T')[0]}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div className="text-xs text-gray-500 bg-yellow-50 border border-yellow-200 rounded p-2">
                    💡 Rango máximo recomendado: 1 año
                  </div>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex gap-2 p-4 border-t border-gray-200 bg-gray-50">
              <button
                onClick={handleCancel}
                className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleApply}
                className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
              >
                Aplicar
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
