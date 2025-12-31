'use client';

import React, { useEffect } from 'react';
import dynamic from 'next/dynamic';
import 'leaflet/dist/leaflet.css';

// Cargamos `Leaflet` dinámicamente con `ssr: false` para que se cargue solo en el navegador
const LeafletMap = dynamic(() => import("@/app/components/LeafletMap"), { ssr: false });

export default function Map() {
    return (
        <div className="relative">
            <LeafletMap />
        </div>
    );
}