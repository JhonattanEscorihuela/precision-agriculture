'use client';

interface OverlayToastProps {
  message: string;
  onDismiss: () => void;
}

export default function OverlayToast({ message, onDismiss }: OverlayToastProps) {
  return (
    <div
      aria-atomic="true"
      aria-live="assertive"
      className="fixed right-4 top-4 z-[2000] flex max-w-sm items-start gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-900 shadow-lg"
      role="alert"
    >
      <span className="min-w-0 flex-1">{message}</span>
      <button
        aria-label="Cerrar mensaje de error"
        className="rounded px-1 font-bold text-red-700 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-500"
        onClick={onDismiss}
        type="button"
      >
        ×
      </button>
    </div>
  );
}
