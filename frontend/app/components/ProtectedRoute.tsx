'use client';

import { useAuth } from '@/app/context/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const [shouldRender, setShouldRender] = useState(false);

  useEffect(() => {
    // Verificar token en localStorage primero (sincrónico)
    const token = localStorage.getItem('token');

    if (!token) {
      // Sin token, redirigir inmediatamente sin mostrar contenido
      router.replace('/login');
      return;
    }

    // Con token, esperar validación del contexto
    if (!isLoading) {
      if (user) {
        // Usuario válido, permitir renderizado
        setShouldRender(true);
      } else {
        // Token inválido o expirado
        router.replace('/login');
      }
    }
  }, [user, isLoading, router]);

  // No renderizar nada hasta que se confirme autenticación
  if (!shouldRender) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-emerald-50 to-green-100">
        <div className="flex flex-col items-center gap-4">
          <svg className="animate-spin h-12 w-12 text-emerald-600" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <p className="text-gray-600 text-sm">Verificando sesión...</p>
        </div>
      </div>
    );
  }

  // Solo renderiza children cuando shouldRender es true
  return <>{children}</>;
}
