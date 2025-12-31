'use client';

import React, { createContext, useContext, useState } from 'react';

// Tipo para los datos de un polígono
type Polygon = {
    id: string; // ID único del polígono
    name: string; // Nombre del cultivo o parcela
    coordinates: number[][]; // Coordenadas del polígono
};

// Definir un tipo para el contexto
type PolygonContextType = {
    polygons: Polygon[]; // Lista de polígonos guardados
    addPolygon: (polygon: Polygon) => void; // Función para agregar un polígono
    removePolygon: (id: string) => void; // Función para eliminar un polígono
};

// Creamos el contexto
const PolygonContext = createContext<PolygonContextType | undefined>(undefined);

// Componente proveedor del contexto
export const PolygonProvider = ({ children }: { children: React.ReactNode }) => {
    const [polygons, setPolygons] = useState<Polygon[]>([]);

    // Agregar un polígono
    const addPolygon = (polygon: Polygon) => {
        setPolygons((prevPolygons) => [...prevPolygons, polygon]);
    };

    // Eliminar un polígono por su ID
    const removePolygon = (id: string) => {
        setPolygons((prevPolygons) => prevPolygons.filter((polygon) => polygon.id !== id));
    };

    return (
        <PolygonContext.Provider value={{ polygons, addPolygon, removePolygon }}>
            {children}
        </PolygonContext.Provider>
    );
};

// Hook para usar el contexto
export const usePolygons = () => {
    const context = useContext(PolygonContext);
    if (!context) {
        throw new Error('usePolygons debe ser usado dentro de un PolygonProvider');
    }
    return context;
};