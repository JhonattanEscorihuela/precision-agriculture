'use client';

import React, { createContext, useContext, useState, useSyncExternalStore } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/axios';

interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, fullName: string, password: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface StoredAuth {
  user: User | null;
  token: string | null;
}

const EMPTY_AUTH: StoredAuth = { user: null, token: null };

function readStoredAuth(): StoredAuth {
  if (typeof window === 'undefined') return EMPTY_AUTH;

  const storedToken = localStorage.getItem('token');
  const storedUser = localStorage.getItem('user');
  if (!storedToken || !storedUser) return EMPTY_AUTH;

  try {
    return { token: storedToken, user: JSON.parse(storedUser) as User };
  } catch {
    return EMPTY_AUTH;
  }
}

const subscribeToHydration = () => () => undefined;
const getClientHydrationSnapshot = () => true;
const getServerHydrationSnapshot = () => false;

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [storedAuth, setStoredAuth] = useState<StoredAuth>(readStoredAuth);
  const isHydrated = useSyncExternalStore(
    subscribeToHydration,
    getClientHydrationSnapshot,
    getServerHydrationSnapshot
  );
  const router = useRouter();
  const user = isHydrated ? storedAuth.user : null;
  const token = isHydrated ? storedAuth.token : null;
  const isLoading = !isHydrated;

  const login = async (email: string, password: string) => {
    try {
      const response = await apiClient.post('/auth/login', { email, password });
      const data = response.data;

      setStoredAuth({ token: data.access_token, user: data.user });

      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));

      router.push('/');
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Error al iniciar sesión');
    }
  };

  const register = async (email: string, fullName: string, password: string) => {
    try {
      await apiClient.post('/auth/register', {
        email,
        full_name: fullName,
        password
      });

      // Auto-login después del registro
      await login(email, password);
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Error al registrarse');
    }
  };

  const logout = () => {
    setStoredAuth(EMPTY_AUTH);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    router.push('/login');
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth debe usarse dentro de AuthProvider');
  }
  return context;
}
