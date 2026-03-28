'use client';

import React from 'react';
import dynamic from 'next/dynamic';
import 'leaflet/dist/leaflet.css';
import LoadingIndicator from './LoadingIndicator';

// Cargamos `Leaflet` dinámicamente con `ssr: false` para que se cargue solo en el navegador
const LeafletMap = dynamic(() => import("@/app/components/LeafletMap"), {
    ssr: false,
    loading: () => (
        <div className="flex items-center justify-center min-h-[600px] bg-white rounded-xl">
            <LoadingIndicator text="Cargando mapa satelital..." size="lg" />
        </div>
    )
});

export default function Map() {
    return (
        <div className="relative">
            <LeafletMap />
        </div>
    );
}