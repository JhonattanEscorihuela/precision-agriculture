'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';

// Tipo de datos para un polígono
type Polygon = {
    id: string; // ID único del polígono
    name: string; // Nombre del polígono
    coordinates: number[][]; // Coordenadas del polígono
};

// Definir el tipo del contexto
type PolygonContextType = {
    polygons: Polygon[]; // Lista de polígonos guardados
    addPolygon: (polygon: Polygon) => void; // Función para agregar un polígono
    removePolygon: (id: string) => void; // Función para eliminar un polígono por ID
};

// Crear el contexto
const PolygonContext = createContext<PolygonContextType | undefined>(undefined);

export const PolygonProvider = ({ children }: { children: React.ReactNode }) => {
    const [polygons, setPolygons] = useState<Polygon[]>([]);

    // Cargar polígonos guardados desde localStorage al iniciar la aplicación
    useEffect(() => {
        const storedPolygons = localStorage.getItem('polygons');
        if (storedPolygons) {
            setPolygons(JSON.parse(storedPolygons));
        }
    }, []);

    // Guardar automáticamente los cambios en los polígonos en localStorage
    useEffect(() => {
        localStorage.setItem('polygons', JSON.stringify(polygons));
    }, [polygons]);

    // Agregar un nuevo polígono al estado y `localStorage`
    const addPolygon = (polygon: Polygon) => {
        setPolygons((prevPolygons) => [...prevPolygons, polygon]);
    };

    // Eliminar un polígono por ID
    const removePolygon = (id: string) => {
        setPolygons((prevPolygons) => prevPolygons.filter((polygon) => polygon.id !== id));
    };

    return (
        <PolygonContext.Provider value={{ polygons, addPolygon, removePolygon }}>
            {children}
        </PolygonContext.Provider>
    );
};

// Hook para utilizar el contexto
export const usePolygons = (): PolygonContextType => {
    const context = useContext(PolygonContext);
    if (!context) {
        throw new Error('usePolygons debe usarse dentro de un PolygonProvider.');
    }
    return context;
};