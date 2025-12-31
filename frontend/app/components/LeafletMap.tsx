'use client';

import React, { useEffect, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import 'leaflet-draw';
import { usePolygons } from '../context/PolygonContext';
import { v4 as uuidv4 } from 'uuid';

type PolygonData = {
    coordinates: number[][]; // Coordenadas del polígono
};

export default function LeafletMap() {
    const { addPolygon } = usePolygons();

    useEffect(() => {
        // Inicializar el mapa
        const map = L.map('map', {
            center: [10.441, -66.3584], // Coordenadas para centrar en Venezuela
            zoom: 7,
        });

        // Capas base
        const baseLayers = {
            "OpenStreetMap": L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors',
            }),
            "ESRI World Imagery": L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                attribution: 'Tiles &copy; Esri'
            }),
        };

        // Establecer OpenStreetMap como la capa base predeterminada
        baseLayers["OpenStreetMap"].addTo(map);

        // Agregar un control para intercambiar entre capas base
        L.control.layers(baseLayers).addTo(map);

        // Capas de shapes dibujados
        const drawnItems = new L.FeatureGroup();
        map.addLayer(drawnItems);

        // Controles para dibujar
        const drawControl = new L.Control.Draw({
            edit: {
                featureGroup: drawnItems,
            },
            draw: {
                polygon: {
                    // PolygonOptions instead of boolean true to satisfy types
                    allowIntersection: false,
                    showArea: true,
                    shapeOptions: {
                        color: '#3388ff'
                    }
                },
                polyline: false,
                rectangle: false,
                circle: false,
                circlemarker: false,
                marker: false,
            },
        });
        map.addControl(drawControl);

        // Manejo de eventos al dibujar polígono
        map.on(L.Draw.Event.CREATED, function (event: any) {
            const layer = event.layer;
            drawnItems.addLayer(layer);

            // Obtener las coordenadas del polígono dibujado
            const coordinates = layer.getLatLngs()[0].map((coord: L.LatLng) => [coord.lat, coord.lng]);
            console.log('Coordenadas del Polígono:', coordinates);

            // Guardar las coordenadas en el contexto
            const newPolygon = {
                id: uuidv4(), // Generar un ID único para el polígono
                name: `Parcela ${new Date().toLocaleString()}`, // Nombre dinámico con la fecha actual
                coordinates,
            };

            addPolygon(newPolygon); // Guardar polígono en el contexto global
        });

        return () => {
            map.remove();
        };
    }, []);

    return (
        <div className="w-full h-[80vh] relative">
            <div id="map" className="h-full"></div>
        </div>
    );
}