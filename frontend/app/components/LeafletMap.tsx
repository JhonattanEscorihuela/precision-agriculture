'use client';

import React, { useEffect, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import 'leaflet-draw';

type PolygonData = {
    coordinates: number[][]; // Coordenadas del polígono
};

export default function LeafletMap() {
    const [polygonData, setPolygonData] = useState<PolygonData | null>(null);

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

            // Capturar las coordenadas del polígono
            const coordinates = layer.getLatLngs()[0].map((coord: L.LatLng) => [coord.lat, coord.lng]);
            console.log('Coordenadas del Polígono:', coordinates);

            // Guardar el polígono en el estado
            setPolygonData({ coordinates });
        });

        // Limpiar el mapa
        return () => {
            map.remove();
        };
    }, []);

    return (
        <div className="w-full h-[80vh] relative">
            <div id="map" className="h-full"></div>

            {/* Mostrar las coordenadas del polígono */}
{/*             {polygonData && (
                <div className="absolute top-0 left-0 bg-white bg-opacity-90 p-4 rounded shadow-md">
                    <h3 className="font-bold">Coordenadas Seleccionadas:</h3>
                    {polygonData.coordinates.map((coord, index) => (
                        <p key={index} className="text-sm text-gray-800">
                            {`Lat: ${coord[0]}, Lng: ${coord[1]}`}
                        </p>
                    ))}
                </div>
            )} */}
        </div>
    );
}