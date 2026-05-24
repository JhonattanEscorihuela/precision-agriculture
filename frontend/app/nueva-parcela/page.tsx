'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { usePolygons } from '../context/PolygonContext';
import FileUploader from '../components/FileUploader';
import { closePolygon } from '../utils/coordUtils';
import ProtectedRoute from '@/app/components/ProtectedRoute';

type TabType = 'upload' | 'manual' | 'map';

export default function NuevaParcelaPage() {
    const router = useRouter();
    const { createPolygon } = usePolygons();
    const [activeTab, setActiveTab] = useState<TabType>('upload');
    const [parcelName, setParcelName] = useState('');
    const [jsonInput, setJsonInput] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    const handleFileUpload = async (file: File) => {
        try {
            const text = await file.text();
            const data = JSON.parse(text);

            // Validar estructura GeoJSON
            if (data.type === 'Feature' && data.geometry?.type === 'Polygon') {
                // GeoJSON ya viene en formato correcto [lng, lat]
                // NO invertir - enviar directamente al backend
                let coords = data.geometry.coordinates[0];

                // Asegurar que el polígono esté cerrado (primer punto = último punto)
                coords = closePolygon(coords);

                const name = data.properties?.name || parcelName || file.name.replace(/\.[^/.]+$/, '');

                await createPolygon({ name, coordinates: coords });
                setSuccess(true);
                setTimeout(() => router.push('/cultivos'), 1500);
            } else {
                setError('El archivo debe ser un GeoJSON válido con geometría tipo Polygon');
            }
        } catch (err) {
            setError('Error al procesar el archivo. Verifica que sea un GeoJSON válido.');
        }
    };

    const handleManualSubmit = async () => {
        try {
            setError('');
            const data = JSON.parse(jsonInput);

            if (data.type === 'Feature' && data.geometry?.type === 'Polygon') {
                // GeoJSON ya viene en formato correcto [lng, lat]
                // NO invertir - enviar directamente al backend
                let coords = data.geometry.coordinates[0];

                // Asegurar que el polígono esté cerrado (primer punto = último punto)
                coords = closePolygon(coords);

                const name = parcelName || data.properties?.name || 'Nueva Parcela';

                await createPolygon({ name, coordinates: coords });
                setSuccess(true);
                setTimeout(() => router.push('/cultivos'), 1500);
            } else {
                setError('El GeoJSON debe tener geometría tipo Polygon');
            }
        } catch (err) {
            setError('JSON inválido. Verifica la sintaxis.');
        }
    };

    const tabs = [
        { id: 'upload' as TabType, label: 'Subir Archivo', icon: '📁' },
        { id: 'manual' as TabType, label: 'Entrada Manual', icon: '⌨️' },
        { id: 'map' as TabType, label: 'Dibujar en Mapa', icon: '🗺️' },
    ];

    return (
        <ProtectedRoute>
        <div className="animate-fade-in">
            {/* Header */}
            <div className="mb-4 lg:mb-6 p-4 lg:p-6 bg-white rounded-xl lg:rounded-2xl shadow-sm relative overflow-hidden">
                <div className="absolute top-0 left-0 right-0 h-1 " />
                <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-slate-800 mb-2 flex items-center gap-2 lg:gap-3">
                    <span className="text-2xl sm:text-3xl lg:text-4xl">➕</span>
                    <span className="truncate">Cargar Nueva Parcela</span>
                </h1>
                <p className="text-xs sm:text-sm lg:text-base text-slate-600">
                    Importa datos geoespaciales o define manualmente una nueva zona de cultivo
                </p>
            </div>

            {/* Tabs */}
            <div className="flex gap-2 lg:gap-3 mb-4 lg:mb-6 flex-wrap">
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center gap-1.5 lg:gap-2 px-3 sm:px-4 lg:px-6 py-2 lg:py-3 rounded-lg lg:rounded-xl font-semibold text-xs sm:text-sm lg:text-base transition-all ${
                            activeTab === tab.id
                                ? 'bg-gradient-to-r from-satellite-blue to-satellite-deep text-white shadow-lg'
                                : 'bg-white text-slate-700 hover:bg-slate-50 shadow-sm border-2 border-slate-200'
                        }`}
                    >
                        <span className="text-base sm:text-lg lg:text-xl">{tab.icon}</span>
                        <span className="hidden sm:inline">{tab.label}</span>
                        <span className="sm:hidden">{tab.id === 'upload' ? 'Subir' : tab.id === 'manual' ? 'Manual' : 'Mapa'}</span>
                    </button>
                ))}
            </div>

            {/* Mensajes */}
            {error && (
                <div className="mb-4 lg:mb-6 p-3 lg:p-4 bg-vegetation-critical/10 border-2 border-vegetation-critical/30 rounded-lg lg:rounded-xl flex items-center gap-2 lg:gap-3 text-vegetation-critical animate-fade-in">
                    <span className="text-xl lg:text-2xl flex-shrink-0">⚠️</span>
                    <span className="font-medium text-xs lg:text-base">{error}</span>
                </div>
            )}

            {success && (
                <div className="mb-4 lg:mb-6 p-3 lg:p-4 bg-vegetation-healthy/10 border-2 border-vegetation-healthy/30 rounded-lg lg:rounded-xl flex items-center gap-2 lg:gap-3 text-vegetation-healthy animate-fade-in">
                    <span className="text-xl lg:text-2xl flex-shrink-0">✓</span>
                    <span className="font-medium text-xs lg:text-base">¡Parcela creada exitosamente! Redirigiendo...</span>
                </div>
            )}

            {/* Contenido según tab */}
            <div className="bg-white rounded-xl lg:rounded-2xl shadow-md p-4 sm:p-6 lg:p-8">
                {activeTab === 'upload' && (
                    <div className="space-y-6">
                        <div>
                            <label className="block text-sm font-semibold text-slate-800 mb-2">
                                Nombre de la parcela (opcional)
                            </label>
                            <input
                                type="text"
                                value={parcelName}
                                onChange={(e) => setParcelName(e.target.value)}
                                placeholder="Ej: Parcela Norte"
                                className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl focus:border-satellite-blue focus:outline-none transition-colors"
                            />
                        </div>

                        <FileUploader
                            onUpload={handleFileUpload}
                            accept=".geojson,.json,.kml"
                            maxSize={5}
                        />

                        <div className="bg-satellite-blue/5 rounded-xl p-6 border-2 border-satellite-blue/20">
                            <h3 className="font-bold text-slate-800 mb-3 flex items-center gap-2">
                                <span className="text-xl">ℹ️</span>
                                Formatos aceptados
                            </h3>
                            <ul className="space-y-2 text-sm text-slate-600">
                                <li className="flex items-center gap-2">
                                    <span className="w-2 h-2 bg-satellite-blue rounded-full"></span>
                                    <strong>GeoJSON:</strong> Formato estándar para datos geoespaciales
                                </li>
                                <li className="flex items-center gap-2">
                                    <span className="w-2 h-2 bg-satellite-blue rounded-full"></span>
                                    <strong>KML:</strong> Formato de Google Earth
                                </li>
                                <li className="flex items-center gap-2">
                                    <span className="w-2 h-2 bg-satellite-blue rounded-full"></span>
                                    La geometría debe ser tipo <code className="px-2 py-1 bg-slate-200 rounded font-mono text-xs">Polygon</code>
                                </li>
                                <li className="flex items-center gap-2">
                                    <span className="w-2 h-2 bg-satellite-blue rounded-full"></span>
                                    Coordenadas en formato <code className="px-2 py-1 bg-slate-200 rounded font-mono text-xs">[longitud, latitud]</code>
                                </li>
                            </ul>
                        </div>
                    </div>
                )}

                {activeTab === 'manual' && (
                    <div className="space-y-6">
                        <div>
                            <label className="block text-sm font-semibold text-slate-800 mb-2">
                                Nombre de la parcela
                            </label>
                            <input
                                type="text"
                                value={parcelName}
                                onChange={(e) => setParcelName(e.target.value)}
                                placeholder="Ej: Parcela Sur"
                                className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl focus:border-satellite-blue focus:outline-none transition-colors"
                            />
                        </div>

                        <div>
                            <div className="flex items-center justify-between mb-2">
                                <label className="text-sm font-semibold text-slate-800">
                                    GeoJSON
                                </label>
                                <span className="text-xs text-slate-500 font-mono">application/json</span>
                            </div>
                            <textarea
                                value={jsonInput}
                                onChange={(e) => setJsonInput(e.target.value)}
                                placeholder={`{
  "type": "Feature",
  "geometry": {
    "type": "Polygon",
    "coordinates": [
      [
        [-67.477732, 8.890243],
        [-67.472585, 8.891811],
        [-67.482623, 8.921237],
        [-67.477732, 8.890243]
      ]
    ]
  },
  "properties": {
    "name": "Mi Parcela"
  }
}`}
                                rows={14}
                                className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl font-mono text-sm focus:border-satellite-blue focus:outline-none transition-colors resize-y"
                            />
                        </div>

                        <button
                            onClick={handleManualSubmit}
                            disabled={!jsonInput.trim() || !parcelName.trim()}
                            className="w-full py-4 bg-gradient-to-r from-vegetation-healthy to-vegetation-vibrant text-white font-bold rounded-xl shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        >
                            <span>Crear Parcela</span>
                            <span className="text-xl">→</span>
                        </button>
                    </div>
                )}

                {activeTab === 'map' && (
                    <div className="text-center py-12 space-y-6">
                        <div className="text-6xl mb-4">🗺️</div>
                        <h3 className="text-2xl font-bold text-slate-800">
                            Usa el Mapa Principal
                        </h3>
                        <p className="text-slate-600 max-w-md mx-auto mb-6">
                            Para dibujar una parcela directamente en el mapa, ve a la página principal y usa las herramientas de dibujo.
                        </p>
                        <div className="flex flex-col gap-3 max-w-md mx-auto bg-slate-50 rounded-xl p-6 border-2 border-slate-200">
                            <div className="flex items-start gap-3 text-left">
                                <span className="text-2xl">1️⃣</span>
                                <div>
                                    <strong className="text-slate-800">Ve al mapa principal</strong>
                                    <p className="text-sm text-slate-600">Haz clic en "Mapa Principal" en el menú</p>
                                </div>
                            </div>
                            <div className="flex items-start gap-3 text-left">
                                <span className="text-2xl">2️⃣</span>
                                <div>
                                    <strong className="text-slate-800">Selecciona la herramienta de dibujo</strong>
                                    <p className="text-sm text-slate-600">Haz clic en el ícono de polígono ⬢</p>
                                </div>
                            </div>
                            <div className="flex items-start gap-3 text-left">
                                <span className="text-2xl">3️⃣</span>
                                <div>
                                    <strong className="text-slate-800">Dibuja tu parcela</strong>
                                    <p className="text-sm text-slate-600">Haz clic en el mapa para crear los vértices</p>
                                </div>
                            </div>
                        </div>
                        <button
                            onClick={() => router.push('/')}
                            className="px-8 py-4 bg-gradient-to-r from-satellite-blue to-satellite-deep text-white font-bold rounded-xl shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-2 mx-auto"
                        >
                            <span>Ir al Mapa Principal</span>
                            <span className="text-xl">→</span>
                        </button>
                    </div>
                )}
            </div>
        </div>
        </ProtectedRoute>
    );
}
