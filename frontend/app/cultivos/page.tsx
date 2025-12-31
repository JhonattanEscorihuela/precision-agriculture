'use client';

import React from 'react';
import { usePolygons } from '../context/PolygonContext';

export default function CultivosPage() {
    const { polygons, removePolygon } = usePolygons();

    return (
        <div>
            <h1 className="text-2xl font-bold mb-6">Mis Cultivos Guardados</h1>

            {/* Lista de cultivos */}
            <ul className="space-y-4">
                {polygons.length > 0 ? (
                    polygons.map((polygon) => (
                        <li
                            key={polygon.id}
                            className="w-full p-4 bg-gray-100 rounded shadow-lg flex justify-between items-center"
                        >
                            <div>
                                <h2 className="text-xl font-semibold">{polygon.name}</h2>
                                <p className="text-sm text-gray-500">
                                    <strong>Coordenadas:</strong> {polygon.coordinates.length} puntos seleccionados
                                </p>
                            </div>
                            <button
                                onClick={() => removePolygon(polygon.id)}
                                className="text-red-600 font-semibold hover:underline"
                            >
                                Eliminar
                            </button>
                        </li>
                    ))
                ) : (
                    <p className="text-gray-500">No hay cultivos guardados aún.</p>
                )}
            </ul>
        </div>
    );
}