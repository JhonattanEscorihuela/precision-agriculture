'use client'; // Este archivo se ejecuta únicamente en el cliente

import React, { useEffect } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

export default function LeafletMap() {
    useEffect(() => {
        // Crear el mapa únicamente del lado del cliente
        const map = L.map('map', {
            center: [10.441, -66.858], // Coordenadas para centrar en Venezuela
            zoom: 7, // Ajusta el nivel de zoom según tus necesidades
        });

        // Agregar el tile layer de OpenStreetMap
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        }).addTo(map);

        return () => {
            // Eliminar el mapa al desmontar el componente
            map.remove();
        };
    }, []);

    return (
        <div
            id="map"
            className="h-[70vh] w-full rounded-lg shadow"
        ></div>
    );
}