'use client';

import React, { useState, useEffect } from 'react';
import DateSelector from '../molecules/DateSelector';
import AcquireButton from '../molecules/AcquireButton';
import NDVIPanel from './NDVIPanel';

interface DateInfo {
  date: string;
  cloud_cover: number;
  acquired: boolean;
  ndvi_calculated: boolean;
}

interface SentinelPanelProps {
  polygonId: number;
  polygonName: string;
  isOpen: boolean;
  onClose: () => void;
}

/**
 * OE1 - Organism: Panel lateral de adquisición Sentinel-2
 * Permite consultar fechas y solicitar adquisición de bandas
 */
export default function SentinelPanel({
  polygonId,
  polygonName,
  isOpen,
  onClose
}: SentinelPanelProps) {
  // Calcular fechas inteligentes
  const getSmartDates = () => {
    const today = new Date();
    const endDateStr = today.toISOString().split('T')[0]; // Hoy

    // Fecha inicio: primer día del mes hace 6 meses
    const sixMonthsAgo = new Date(today);
    sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);
    sixMonthsAgo.setDate(1); // Primer día del mes
    const startDateStr = sixMonthsAgo.toISOString().split('T')[0];

    return { startDateStr, endDateStr, maxDateStr: endDateStr };
  };

  const { startDateStr, endDateStr, maxDateStr } = getSmartDates();

  const [startDate, setStartDate] = useState(startDateStr);
  const [endDate, setEndDate] = useState(endDateStr);
  const [dates, setDates] = useState<DateInfo[]>([]);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [isLoadingDates, setIsLoadingDates] = useState(false);
  const [isAcquiring, setIsAcquiring] = useState(false);
  const [acquisitionSuccess, setAcquisitionSuccess] = useState(false);
  const [acquisitionError, setAcquisitionError] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [lastAcquisitionId, setLastAcquisitionId] = useState<number | null>(null);

  // Resetear completamente cuando cambia la parcela
  useEffect(() => {
    if (polygonId) {
      const { startDateStr, endDateStr } = getSmartDates();
      setStartDate(startDateStr);
      setEndDate(endDateStr);
      setSelectedDate(null);
      setDates([]);
      setIsLoadingDates(false);
      setIsAcquiring(false);
      setAcquisitionSuccess(false);
      setAcquisitionError(false);
      setErrorMessage('');
    }
  }, [polygonId]);

  // Cargar fechas cuando se abre el panel
  useEffect(() => {
    if (isOpen && polygonId && startDate && endDate) {
      fetchAvailableDates();
    }
  }, [isOpen]);

  // Consultar fechas disponibles cuando cambian las fechas (después de abrir)
  useEffect(() => {
    if (isOpen && polygonId && startDate && endDate && dates.length === 0 && !isLoadingDates) {
      // Solo recargar si cambian las fechas manualmente (no en el mount inicial)
      const { startDateStr, endDateStr } = getSmartDates();
      if (startDate !== startDateStr || endDate !== endDateStr) {
        fetchAvailableDates();
      }
    }
  }, [startDate, endDate]);

  const fetchAvailableDates = async (resetAcquisitionState = true) => {
    setIsLoadingDates(true);
    setSelectedDate(null);

    // Solo resetear estado de adquisición si se solicita explícitamente
    if (resetAcquisitionState) {
      setAcquisitionSuccess(false);
      setAcquisitionError(false);
    }

    try {
      const response = await fetch(
        `http://localhost:8000/api/sentinel/available-dates/${polygonId}?start_date=${startDate}&end_date=${endDate}&max_cloud=20`
      );

      if (!response.ok) {
        throw new Error('Error al consultar fechas');
      }

      const data = await response.json();
      setDates(data.dates || []);
    } catch (error) {
      console.error('Error fetching dates:', error);
      setDates([]);
      setErrorMessage('Error al consultar fechas disponibles');
    } finally {
      setIsLoadingDates(false);
    }
  };

  const handleAcquire = async () => {
    if (!selectedDate) return;

    setIsAcquiring(true);
    setAcquisitionSuccess(false);
    setAcquisitionError(false);
    setErrorMessage('');

    try {
      const response = await fetch('http://localhost:8000/api/sentinel/acquire', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          polygon_id: polygonId,
          date: selectedDate,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al adquirir imagen');
      }

      const data = await response.json();

      setAcquisitionSuccess(true);

      if (data.acquisition_id) {
        setLastAcquisitionId(data.acquisition_id);
      }

      // Si ya existía, mostrar mensaje diferente
      if (data.already_existed) {
        setErrorMessage('Esta fecha ya había sido adquirida anteriormente');
      }

      // Refrescar fechas para actualizar badges (sin resetear estado de adquisición)
      fetchAvailableDates(false);
    } catch (error) {
      console.error('Error acquiring bands:', error);
      setAcquisitionError(true);
      setErrorMessage(error instanceof Error ? error.message : 'Error desconocido');
    } finally {
      setIsAcquiring(false);
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay para mobile */}
      <div
        className="lg:hidden fixed inset-0 bg-black/50 z-[999]"
        onClick={onClose}
      />

      {/* Panel lateral (desktop) / Modal inferior (mobile) */}
      <div className="
        fixed bg-white shadow-2xl flex flex-col

        /* Mobile: modal inferior */
        bottom-0 left-0 right-0 max-h-[85vh] rounded-t-3xl

        /* Desktop: panel lateral */
        lg:right-0 lg:left-auto lg:top-0 lg:bottom-auto lg:h-full lg:w-96 lg:rounded-none lg:max-h-none
      " style={{ zIndex: 1000 }}>
        {/* Handle para arrastrar en mobile */}
        <div className="lg:hidden flex justify-center py-3 border-b border-gray-200">
          <div className="w-12 h-1.5 bg-gray-300 rounded-full" />
        </div>

        {/* Header con info de la parcela */}
        <div className="bg-emerald-600 text-white p-4 lg:p-6">
          <div className="flex justify-between items-start gap-3">
            <div className="flex-1 min-w-0">
              <h2 className="text-lg lg:text-xl font-bold truncate">Adquisición Sentinel-2</h2>
              <p className="text-emerald-100 text-sm mt-1 truncate">{polygonName}</p>
              <p className="text-emerald-200 text-xs mt-2 hidden sm:block">
                Selecciona una fecha para descargar imágenes satelitales
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-emerald-100 transition-colors flex-shrink-0"
              aria-label="Cerrar panel"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 lg:p-6 space-y-4 lg:space-y-6">
          {/* Selector de rango de fechas */}
          <div className="space-y-4">
            <h3 className="font-semibold text-gray-800">Rango de fechas</h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-600 mb-1">Inicio</label>
                <input
                  type="date"
                  value={startDate}
                  max={maxDateStr}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Fin</label>
                <input
                  type="date"
                  value={endDate}
                  max={maxDateStr}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          {/* Selector de fechas disponibles */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-gray-800">Fechas disponibles</h3>
              {/* Leyenda de badges */}
              <div className="flex gap-1 text-xs">
                <span className="flex items-center gap-1">
                  <div className="w-3 h-3 bg-green-600 rounded-full"></div>
                  <span className="text-gray-600 hidden sm:inline">NDVI</span>
                </span>
                <span className="flex items-center gap-1 ml-2">
                  <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                  <span className="text-gray-600 hidden sm:inline">Adq.</span>
                </span>
              </div>
            </div>
            <DateSelector
              dates={dates}
              selectedDate={selectedDate}
              isLoading={isLoadingDates}
              onSelectDate={setSelectedDate}
            />
          </div>

          {/* Mensajes de error */}
          {errorMessage && !acquisitionError && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <p className="text-yellow-800 text-sm">{errorMessage}</p>
            </div>
          )}

          {acquisitionError && errorMessage && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-red-800 text-sm">{errorMessage}</p>
            </div>
          )}

          {/* Panel NDVI - Mostrar después de adquisición exitosa */}
          {acquisitionSuccess && lastAcquisitionId && (
            <div className="mt-6">
              <NDVIPanel
                acquisitionId={lastAcquisitionId}
                polygonId={polygonId}
              />
            </div>
          )}
        </div>

        {/* Footer con botón de adquisición */}
        <div className="border-t border-gray-200 p-4 lg:p-6 bg-white">
          <AcquireButton
            isLoading={isAcquiring}
            isSuccess={acquisitionSuccess}
            isError={acquisitionError}
            disabled={!selectedDate}
            onClick={handleAcquire}
          />
        </div>
      </div>
    </>
  );
}
