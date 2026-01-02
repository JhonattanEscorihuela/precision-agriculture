'use client';

import React, { useEffect } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import 'leaflet-draw';
import { usePolygons } from '../context/PolygonContext';
import { v4 as uuidv4 } from 'uuid';

export default function LeafletMap() {
    const { addPolygon, polygons } = usePolygons();

    const mapRef = React.useRef<L.Map | null>(null);
    const drawnItemsRef = React.useRef<L.FeatureGroup | null>(null);

    useEffect(() => {
/*         if (mapRef.current) return; // Evitar reinicialización */

        const map = L.map('map', {
            center: [10.441, -66.3584], // Venezuela
            zoom: 7,
        });

        mapRef.current = map;

        // Capas base
        const baseLayers = {
            OpenStreetMap: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; OpenStreetMap contributors',
            }),
            'ESRI World Imagery': L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                attribution: 'Tiles &copy; Esri',
            }),
        };

        baseLayers["OpenStreetMap"].addTo(map);
        L.control.layers(baseLayers).addTo(map);

        const drawnItems = new L.FeatureGroup();
        map.addLayer(drawnItems);
        drawnItemsRef.current = drawnItems;

        const drawControl = new L.Control.Draw({
            edit: {
                featureGroup: drawnItems,
            },
            draw: {
                polygon: {
                    allowIntersection: false,
                    showArea: true,
                    shapeOptions: {
                        color: '#3388ff',
                    },
                },
                rectangle: false,
                circle: false,
                polyline: false,
                marker: false,
            },
        });
        map.addControl(drawControl);

        map.on(L.Draw.Event.CREATED, function (event: any) {
            const layer = event.layer;
            drawnItems.addLayer(layer);

            // Guardar coordenadas
            const coordinates = layer.getLatLngs()[0]?.map((coord: L.LatLng) => [coord.lat, coord.lng]);

            const newPolygon = {
                id: uuidv4(),
                name: `Parcela ${new Date().toLocaleString()}`,
                coordinates,
            };

            addPolygon(newPolygon);
        });

        map.invalidateSize();

        return () => {
            map.remove();
        };
    }, []);

    // Redibujar polígonos guardados en `PolygonContext`:
    useEffect(() => {
        if (!mapRef.current || !drawnItemsRef.current) return;
        const drawnItems = drawnItemsRef.current!;

        // Limpiar polígonos antiguos
        drawnItems.clearLayers();

        polygons.forEach((polygon) => {
            const polygonLayer = L.polygon(
                polygon.coordinates.map((coords) => L.latLng(coords[0], coords[1])),
                {
                    color: '#3388ff',
                    weight: 2,
                    fillColor: '#3388ff',
                    fillOpacity: 0.4,
                }
            );
            drawnItems.addLayer(polygonLayer);
        });
    }, [polygons]); // Renderizar cuando cambian los polígonos

    return (
        <div className="w-full h-[80vh] relative">
            <div id="map" className="h-full"></div>
        </div>
    );
}