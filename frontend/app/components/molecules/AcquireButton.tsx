'use client';

import React from 'react';

interface AcquireButtonProps {
  isLoading: boolean;
  isSuccess: boolean;
  isError: boolean;
  disabled?: boolean;
  onClick: () => void;
}

/**
 * OE1 - Molecule: Botón de adquisición con estados
 * Estados: idle / loading / success / error
 */
export default function AcquireButton({
  isLoading,
  isSuccess,
  isError,
  disabled = false,
  onClick
}: AcquireButtonProps) {
  const getButtonContent = () => {
    if (isLoading) {
      return (
        <>
          <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          Descargando imagen...
        </>
      );
    }

    if (isSuccess) {
      return (
        <>
          <span className="mr-2">✓</span>
          Imagen lista para análisis
        </>
      );
    }

    if (isError) {
      return (
        <>
          <span className="mr-2">✗</span>
          Error al descargar
        </>
      );
    }

    return 'Analizar esta fecha';
  };

  const getButtonStyles = () => {
    if (isSuccess) {
      return 'bg-emerald-600 hover:bg-emerald-700 text-white';
    }

    if (isError) {
      return 'bg-red-600 hover:bg-red-700 text-white';
    }

    if (disabled || isLoading) {
      return 'bg-gray-400 text-white cursor-not-allowed';
    }

    return 'bg-emerald-600 hover:bg-emerald-700 text-white';
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled || isLoading || isSuccess}
      className={`
        w-full px-6 py-3 rounded-lg font-semibold
        transition-all duration-200 flex items-center justify-center
        ${getButtonStyles()}
      `}
    >
      {getButtonContent()}
    </button>
  );
}
