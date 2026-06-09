'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { usePolygons } from '../context/PolygonContext';
import ProtectedRoute from '@/app/components/ProtectedRoute';
import { calculatePolygonArea, formatArea } from '@/app/utils/geoUtils';
import { usePolygonHealth } from '@/app/hooks/usePolygonHealth';

export default function CultivosPage() {
    const router = useRouter();
    const { polygons, deletePolygon, updatePolygon, fetchPolygons } = usePolygons();
    const [editingId, setEditingId] = useState<number | null>(null);
    const [editName, setEditName] = useState('');

    // Cargar polígonos al montar el componente
    useEffect(() => {
        fetchPolygons();
    }, [fetchPolygons]);

    // Obtener estado de salud real basado en NDVI
    const polygonIds = polygons.map(p => p.id);
    const { health, isLoading: isLoadingHealth } = usePolygonHealth(polygonIds);

    const handleEdit = (id: number, currentName: string) => {
        setEditingId(id);
        setEditName(currentName);
    };

    const handleSaveEdit = async (id: number) => {
        if (editName.trim()) {
            await updatePolygon(id, { name: editName });
            setEditingId(null);
        }
    };

    const handleDelete = async (id: number, name: string) => {
        if (confirm(`¿Eliminar la parcela "${name}"?`)) {
            await deletePolygon(id);
        }
    };

    const handleViewDashboard = (id: number) => {
        router.push(`/cultivos/${id}`);
    };

    // Configuración visual por estado de salud
    const healthConfig = {
        healthy: {
            borderColor: 'border-vegetation-healthy/30',
            bgColor: 'bg-gradient-to-br from-vegetation-healthy to-vegetation-vibrant',
            icon: '✓',
            label: 'Saludable',
            textColor: 'text-vegetation-healthy',
            description: 'NDVI ≥ 0.5'
        },
        alert: {
            borderColor: 'border-vegetation-alert/30',
            bgColor: 'bg-gradient-to-br from-vegetation-alert to-yellow-400',
            icon: '⚠',
            label: 'Moderado',
            textColor: 'text-vegetation-alert',
            description: 'NDVI 0.3-0.5'
        },
        critical: {
            borderColor: 'border-vegetation-critical/30',
            bgColor: 'bg-gradient-to-br from-vegetation-critical to-red-500',
            icon: '!',
            label: 'Crítico',
            textColor: 'text-vegetation-critical',
            description: 'NDVI < 0.3'
        },
        unknown: {
            borderColor: 'border-gray-300',
            bgColor: 'bg-gradient-to-br from-gray-400 to-gray-500',
            icon: '?',
            label: 'Sin datos',
            textColor: 'text-gray-600',
            description: 'Sin NDVI'
        }
    };

    return (
        <ProtectedRoute>
        <div className="animate-fade-in">
            {/* Header */}
            <div className="flex flex-col sm:flex-row justify-between items-start gap-4 lg:gap-6 mb-4 lg:mb-6 p-4 lg:p-6 bg-white rounded-xl lg:rounded-2xl shadow-sm relative overflow-hidden">
                <div className="flex-1 min-w-0">
                    <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-slate-800 mb-2 truncate">Mis Cultivos Guardados</h1>
                    <p className="text-xs sm:text-sm lg:text-base text-slate-600">
                        Gestiona y monitorea tus parcelas desde agricultura de precisión
                    </p>
                </div>

                <div className="flex gap-2 sm:gap-4 w-full sm:w-auto">
                    <div className="flex-1 sm:flex-initial flex flex-col items-center px-4 sm:px-6 py-3 sm:py-4 bg-gradient-to-br from-vegetation-healthy to-vegetation-vibrant rounded-lg lg:rounded-xl shadow-md min-w-[100px] sm:min-w-[120px]">
                        <span className="font-mono text-white text-xl sm:text-2xl font-bold">{polygons.length}</span>
                        <span className="text-white/90 text-[10px] sm:text-xs mt-1">Parcelas</span>
                    </div>
                    <div className="flex-1 sm:flex-initial flex flex-col items-center px-4 sm:px-6 py-3 sm:py-4 bg-gradient-to-br from-vegetation-healthy to-vegetation-vibrant rounded-lg lg:rounded-xl shadow-md min-w-[100px] sm:min-w-[120px]">
                        <span className="font-mono text-white text-xl sm:text-2xl font-bold">
                            {polygons.reduce((sum, p) => {
                                const areaHa = calculatePolygonArea(p.coordinates);
                                return sum + areaHa;
                            }, 0).toFixed(2)}
                        </span>
                        <span className="text-white/90 text-[10px] sm:text-xs mt-1">Área Total (ha)</span>
                    </div>
                </div>
            </div>

            {/* Grid de cultivos */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-6">
                {polygons.length > 0 ? (
                    polygons.map((polygon, index) => {
                        // Obtener estado de salud real basado en NDVI
                        const polygonHealth = health[polygon.id] || { status: 'unknown', ndvi: null, lastUpdate: null };
                        const config = healthConfig[polygonHealth.status];
                        const areaHa = calculatePolygonArea(polygon.coordinates);

                        return (
                            <div
                                key={polygon.id}
                                className={`relative bg-white rounded-xl lg:rounded-2xl p-4 lg:p-6 shadow-md transition-all duration-400 hover:-translate-y-1 hover:shadow-xl border-2 ${config.borderColor} overflow-hidden group`}
                                style={{ animationDelay: `${index * 100}ms` }}
                            >
                                {/* Patrón topográfico de fondo */}
                                <div className="absolute inset-[-50%] opacity-30 pointer-events-none animate-topo-shift topo-pattern" />

                                {/* Indicador de salud */}
                                <div className={`absolute top-3 lg:top-4 right-3 lg:right-4 w-10 h-10 lg:w-12 lg:h-12 ${config.bgColor} rounded-full flex items-center justify-center text-white text-base lg:text-lg font-bold shadow-lg z-10`}>
                                    <div className="absolute inset-[-4px] border-2 border-current rounded-full opacity-60 animate-pulse-glow" />
                                    <span className="relative z-10">{config.icon}</span>
                                </div>

                                {/* Contenido */}
                                <div className="relative z-[1] mb-4">
                                    {editingId === polygon.id ? (
                                        <div className="flex flex-col gap-3">
                                            <input
                                                type="text"
                                                value={editName}
                                                onChange={(e) => setEditName(e.target.value)}
                                                className="w-full px-3 py-2 border-2 border-satellite-blue rounded-lg text-base font-semibold bg-satellite-blue/5 text-slate-800 outline-none transition-all focus:border-satellite-deep focus:shadow-[0_0_0_3px_rgba(14,165,233,0.1)]"
                                                autoFocus
                                                onKeyDown={(e) => {
                                                    if (e.key === 'Enter') handleSaveEdit(Number(polygon.id));
                                                    if (e.key === 'Escape') setEditingId(null);
                                                }}
                                            />
                                            <div className="flex gap-2">
                                                <button
                                                    onClick={() => handleSaveEdit(polygon.id)}
                                                    className="flex-1 px-3 py-2 bg-gradient-to-r from-vegetation-healthy to-vegetation-vibrant text-white rounded-lg font-semibold text-sm transition-all hover:shadow-[0_0_20px_rgba(16,185,129,0.3)] hover:-translate-y-0.5"
                                                >
                                                    Guardar
                                                </button>
                                                <button
                                                    onClick={() => setEditingId(null)}
                                                    className="flex-1 px-3 py-2 bg-slate-100 text-slate-800 rounded-lg font-semibold text-sm transition-all hover:bg-slate-150"
                                                >
                                                    Cancelar
                                                </button>
                                            </div>
                                        </div>
                                    ) : (
                                        <>
                                            <h2 className="text-lg lg:text-xl font-bold text-slate-800 mb-3 lg:mb-4 pr-12 lg:pr-14">
                                                {polygon.name}
                                            </h2>
                                            <div className="flex flex-col gap-1.5 lg:gap-2">
                                                <div className="flex items-center gap-2 text-xs lg:text-sm text-slate-700">
                                                    <span className="text-base lg:text-lg">📍</span>
                                                    <span className="font-mono font-medium">
                                                        {polygon.coordinates.length} puntos
                                                    </span>
                                                </div>
                                                <div className="flex items-center gap-2 text-xs lg:text-sm text-slate-700">
                                                    <span className="text-base lg:text-lg">📐</span>
                                                    <span className="font-mono font-medium">
                                                        {formatArea(areaHa)}
                                                    </span>
                                                </div>
                                                <div className="flex items-center gap-2 text-xs lg:text-sm text-slate-700">
                                                    <span className="text-base lg:text-lg">🛰️</span>
                                                    <span className={`font-medium ${config.textColor}`}>
                                                        {config.label}
                                                    </span>
                                                </div>
                                                {polygonHealth.ndvi !== null && (
                                                    <div className="flex items-center gap-2 text-xs lg:text-sm text-slate-700">
                                                        <span className="text-base lg:text-lg">📊</span>
                                                        <span className="font-mono font-medium">
                                                            NDVI: {polygonHealth.ndvi.toFixed(3)}
                                                        </span>
                                                    </div>
                                                )}
                                                {polygonHealth.lastUpdate && (
                                                    <div className="flex items-center gap-2 text-xs text-slate-500">
                                                        <span className="text-sm">🕒</span>
                                                        <span>
                                                            {new Date(polygonHealth.lastUpdate).toLocaleDateString('es-ES')}
                                                        </span>
                                                    </div>
                                                )}
                                            </div>
                                        </>
                                    )}
                                </div>

                                {/* Acciones */}
                                {editingId !== polygon.id && (
                                    <div className="flex gap-2 justify-end pt-3 lg:pt-4 border-t border-satellite-blue/10">
                                        <button
                                            onClick={() => handleViewDashboard(polygon.id)}
                                            className="flex-1 px-3 py-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg font-semibold text-sm transition-all hover:shadow-lg hover:-translate-y-0.5 flex items-center justify-center gap-1"
                                            title="Ver dashboard de análisis"
                                        >
                                            <span className="text-base">📊</span>
                                            <span className="hidden sm:inline">Dashboard</span>
                                        </button>
                                        <button
                                            onClick={() => handleEdit(polygon.id, polygon.name)}
                                            className="w-9 h-9 lg:w-10 lg:h-10 rounded-lg bg-vegetation-alert/10 text-vegetation-alert flex items-center justify-center text-lg lg:text-xl transition-all hover:bg-vegetation-alert/20 hover:shadow-lg hover:-translate-y-0.5"
                                            title="Editar nombre"
                                        >
                                            ✏️
                                        </button>
                                        <button
                                            onClick={() => handleDelete(polygon.id, polygon.name)}
                                            className="w-9 h-9 lg:w-10 lg:h-10 rounded-lg bg-vegetation-critical/10 text-vegetation-critical flex items-center justify-center text-lg lg:text-xl transition-all hover:bg-vegetation-critical/20 hover:shadow-lg hover:-translate-y-0.5"
                                            title="Eliminar parcela"
                                        >
                                            🗑️
                                        </button>
                                    </div>
                                )}
                            </div>
                        );
                    })
                ) : (
                    <div className="col-span-full text-center py-12 lg:py-16 px-4 lg:px-8 bg-white rounded-xl lg:rounded-2xl shadow-sm">
                        <div className="text-4xl lg:text-6xl mb-3 lg:mb-4 opacity-50">🌾</div>
                        <h3 className="text-lg lg:text-xl font-bold text-slate-800 mb-2">
                            No hay cultivos guardados
                        </h3>
                        <p className="text-xs lg:text-base text-slate-600 max-w-md mx-auto">
                            Comienza dibujando polígonos en el mapa principal para crear tus primeras parcelas
                        </p>
                    </div>
                )}
            </div>
        </div>
        </ProtectedRoute>
    );
}
