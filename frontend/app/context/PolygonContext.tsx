'use client';

import React, { createContext, useContext, useState, useCallback } from 'react';
import axios from '@/lib/axios';

export type Polygon = {
    id: string;
    name: string;
    coordinates: number[][];
    area: number;
    created_at: string;
    updated_at: string;
};

type PolygonContextType = {
    polygons: Polygon[];
    fetchPolygons: () => Promise<void>;
    createPolygon: (p: Omit<Polygon, 'id' | 'area' | 'created_at' | 'updated_at'>) => Promise<void>;
    updatePolygon: (id: string, data: Partial<Omit<Polygon, 'id' | 'created_at' | 'updated_at'>>) => Promise<void>;
    deletePolygon: (id: string) => Promise<void>;
};

const PolygonContext = createContext<PolygonContextType | undefined>(undefined);

export const PolygonProvider = ({ children }: { children: React.ReactNode }) => {
    const [polygons, setPolygons] = useState<Polygon[]>([]);

    const fetchPolygons = useCallback(async () => {
        try {
            const { data } = await axios.get<Polygon[]>('/polygons');
            setPolygons(data);
        } catch (err) {
            console.error('Error fetching polygons:', err);
        }
    }, []);

    const createPolygon = useCallback(
        async (polygon: Omit<Polygon, 'id' | 'area' | 'created_at' | 'updated_at'>) => {
            try {
                const { data } = await axios.post<Polygon>('/polygons', polygon);
                setPolygons((prev) => [...prev, data]);
            } catch (err) {
                console.error('Error creating polygon:', err);
            }
        },
        []
    );

    const updatePolygon = useCallback(
        async (id: string, update: Partial<Omit<Polygon, 'id' | 'created_at' | 'updated_at'>>) => {
            try {
                const { data } = await axios.put<Polygon>(`/polygons/${id}`, update);
                setPolygons((prev) => prev.map((p) => (p.id === id ? data : p)));
            } catch (err) {
                console.error('Error updating polygon:', err);
            }
        },
        []
    );

    const deletePolygon = useCallback(
        async (id: string) => {
            try {
                await axios.delete(`/polygons/${id}`);
                setPolygons((prev) => prev.filter((p) => p.id !== id));
            } catch (err) {
                console.error('Error deleting polygon:', err);
            }
        },
        []
    );

    return (
        <PolygonContext.Provider
            value={{ polygons, fetchPolygons, createPolygon, updatePolygon, deletePolygon }}
        >
            {children}
        </PolygonContext.Provider>
    );
};

export const usePolygons = (): PolygonContextType => {
    const ctx = useContext(PolygonContext);
    if (!ctx) {
        throw new Error('usePolygons must be used inside a PolygonProvider');
    }
    return ctx;
};