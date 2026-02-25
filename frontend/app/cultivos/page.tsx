'use client';

import React from 'react';
import { usePolygons } from '../context/PolygonContext';

export default function CultivosPage() {
    const {
        polygons,
        deletePolygon,        // DELETE → backend & state
        updatePolygon,        // PUT   → backend & state
    } = usePolygons();

    return (
        <div>
            <h1 className="text-2xl text-gray-950 mb-6">Mis Cultivos Guardados</h1>

            <ul className="space-y-4">
                {polygons.length > 0 ? (
                    polygons.map((polygon) => (
                        <li
                            key={polygon.id}
                            className="w-full p-4 bg-gray-100 rounded shadow-lg flex justify-between items-center"
                        >
                            {/* Nombre y estadísticas */}
                            <div>
                                <h2 className="text-xl text-gray-950 font-semibold">{polygon.name}</h2>
                                <p className="text-sm text-gray-500">
                                    <strong>Coordenadas:</strong> {polygon.coordinates.length} puntos seleccionados
                                </p>
                                <p className="text-sm text-gray-500">
                                    <strong>Área:</strong> {polygon.area?.toFixed(2)} unidades²
                                </p>
                            </div>

                            {/* Botones de acción */}
                            <div className="flex space-x-4">
                                {/* Editar */}
                                <button
                                    onClick={() => {
                                        const nuevoNombre = prompt('Renombra la parcela:', polygon.name);
                                        if (nuevoNombre && nuevoNombre !== polygon.name) {
                                            updatePolygon(polygon.id, { name: nuevoNombre });
                                        }
                                    }}
                                    className="text-yellow-600 hover:underline"
                                >
                                    ✏️
                                </button>

                                {/* Eliminar */}
                                <button
                                    onClick={() => {
                                        if (confirm('¿Eliminar esta parcela?')) {
                                            deletePolygon(polygon.id);
                                        }
                                    }}
                                    className="text-red-600 hover:underline"
                                >
                                    🗑️
                                </button>
                            </div>
                        </li>
                    ))
                ) : (
                    <p className="text-gray-500">No hay cultivos guardados aún.</p>
                )}
            </ul>
        </div>
    );
}