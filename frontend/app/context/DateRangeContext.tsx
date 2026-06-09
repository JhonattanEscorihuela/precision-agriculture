/**
 * Context para compartir rango temporal entre widgets del dashboard.
 * Similar a AWS CloudWatch - soporta rangos relativos y absolutos.
 */

'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

export type DateRangeMode = 'relative' | 'absolute';

export type RelativeRange =
  | '1w' | '2w' | '3w' | '4w'
  | '1m' | '2m' | '3m' | '6m' | '1y';

export interface DateRange {
  mode: DateRangeMode;
  // Modo relativo
  relative?: RelativeRange;
  // Modo absoluto
  startDate?: string; // YYYY-MM-DD
  endDate?: string;   // YYYY-MM-DD
}

interface DateRangeContextType {
  range: DateRange;
  setRange: (range: DateRange) => void;
  getStartDate: () => Date;
  getEndDate: () => Date;
  getFormattedRange: () => string;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
}

const DateRangeContext = createContext<DateRangeContextType | undefined>(undefined);

/**
 * Calcula fecha de inicio según rango relativo.
 */
function calculateStartDate(relative: RelativeRange): Date {
  const now = new Date();
  const start = new Date(now);

  switch (relative) {
    case '1w':
      start.setDate(now.getDate() - 7);
      break;
    case '2w':
      start.setDate(now.getDate() - 14);
      break;
    case '3w':
      start.setDate(now.getDate() - 21);
      break;
    case '4w':
      start.setDate(now.getDate() - 28);
      break;
    case '1m':
      start.setMonth(now.getMonth() - 1);
      break;
    case '2m':
      start.setMonth(now.getMonth() - 2);
      break;
    case '3m':
      start.setMonth(now.getMonth() - 3);
      break;
    case '6m':
      start.setMonth(now.getMonth() - 6);
      break;
    case '1y':
      start.setFullYear(now.getFullYear() - 1);
      break;
  }

  return start;
}

/**
 * Formatea rango relativo a texto legible.
 */
function formatRelativeRange(relative: RelativeRange): string {
  const labels: Record<RelativeRange, string> = {
    '1w': 'Última semana',
    '2w': 'Últimas 2 semanas',
    '3w': 'Últimas 3 semanas',
    '4w': 'Últimas 4 semanas',
    '1m': 'Último mes',
    '2m': 'Últimos 2 meses',
    '3m': 'Últimos 3 meses',
    '6m': 'Últimos 6 meses',
    '1y': 'Último año'
  };
  return labels[relative];
}

export function DateRangeProvider({ children }: { children: React.ReactNode }) {
  // Default: últimos 2 meses (relativo)
  const [range, setRangeState] = useState<DateRange>({
    mode: 'relative',
    relative: '2m'
  });
  const [isLoading, setIsLoading] = useState(false);

  // Cargar desde sessionStorage al montar
  useEffect(() => {
    const stored = sessionStorage.getItem('dateRange');
    if (stored) {
      try {
        setRangeState(JSON.parse(stored));
      } catch (e) {
        console.error('Error parsing stored date range:', e);
      }
    }
  }, []);

  // Guardar en sessionStorage cuando cambia
  const setRange = (newRange: DateRange) => {
    setRangeState(newRange);
    sessionStorage.setItem('dateRange', JSON.stringify(newRange));
  };

  const getStartDate = (): Date => {
    if (range.mode === 'relative' && range.relative) {
      return calculateStartDate(range.relative);
    } else if (range.mode === 'absolute' && range.startDate) {
      return new Date(range.startDate);
    }
    // Fallback: últimos 2 meses
    return calculateStartDate('2m');
  };

  const getEndDate = (): Date => {
    if (range.mode === 'absolute' && range.endDate) {
      return new Date(range.endDate);
    }
    // Modo relativo siempre hasta hoy
    return new Date();
  };

  const getFormattedRange = (): string => {
    if (range.mode === 'relative' && range.relative) {
      return formatRelativeRange(range.relative);
    } else if (range.mode === 'absolute' && range.startDate && range.endDate) {
      const start = new Date(range.startDate).toLocaleDateString('es-ES', { day: '2-digit', month: 'short' });
      const end = new Date(range.endDate).toLocaleDateString('es-ES', { day: '2-digit', month: 'short' });
      return `${start} - ${end}`;
    }
    return 'Últimos 2 meses';
  };

  return (
    <DateRangeContext.Provider value={{ range, setRange, getStartDate, getEndDate, getFormattedRange, isLoading, setIsLoading }}>
      {children}
    </DateRangeContext.Provider>
  );
}

export function useDateRange() {
  const context = useContext(DateRangeContext);
  if (context === undefined) {
    throw new Error('useDateRange must be used within a DateRangeProvider');
  }
  return context;
}
