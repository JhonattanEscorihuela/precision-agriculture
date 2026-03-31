'use client';

import React, { useEffect } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import 'leaflet-draw';
import { usePolygons } from '@/app/context/PolygonContext';
import { leafletToGeoJSON, geoJSONToLeaflet, closePolygon } from '@/app/utils/coordUtils';

export default function LeafletMap() {
    const { polygons, fetchPolygons, createPolygon } = usePolygons();
    const mapRef = React.useRef<L.Map>(null);
    const drawnItemsRef = React.useRef<L.FeatureGroup>(null);

    // Inicializa el mapa y controles
    useEffect(() => {
        const map = L.map('map', { center: [10.441, -66.3584], zoom: 7 });
        mapRef.current = map;

        // Capas base
        const baseLayers = {
            OpenStreetMap: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; OpenStreetMap contributors',
            }),
            'ESRI World Imagery': L.tileLayer(
                'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                { attribution: 'Tiles &copy; Esri' }
            ),
        };
        baseLayers.OpenStreetMap.addTo(map);
        L.control.layers(baseLayers).addTo(map);

        // FeatureGroup para polígonos
        const drawnItems = new L.FeatureGroup();
        map.addLayer(drawnItems);
        drawnItemsRef.current = drawnItems;

        // Control de dibujo de polígonos
        const drawControl = new L.Control.Draw({
            edit: { featureGroup: drawnItems },
            draw: {
                polygon: { allowIntersection: false, showArea: true, shapeOptions: { color: '#3388ff' } },
                rectangle: false,
                circle: false,
                circlemarker: false,
                polyline: false,
                marker: false,
            },
        });
        map.addControl(drawControl);

        // Al crear un polígono en el mapa → enviar al backend
        map.on(L.Draw.Event.CREATED, (ev: any) => {
            const layer = ev.layer;
            drawnItems.addLayer(layer);

            // Leaflet devuelve coordenadas como [lat, lng]
            const leafletCoords = (layer.getLatLngs()[0] as L.LatLng[]).map((pt) => [pt.lat, pt.lng]);

            // Convertir a formato GeoJSON [lng, lat] para el backend
            let geoJsonCoords = leafletToGeoJSON(leafletCoords as [number, number][]);

            // Cerrar el polígono (GeoJSON requiere que primer punto = último punto)
            geoJsonCoords = closePolygon(geoJsonCoords);

            createPolygon({
                name: `Parcela ${new Date().toLocaleString()}`,
                coordinates: geoJsonCoords
            });
        });

        // Ajustar tamaño
        map.invalidateSize();

        // Cargar polígonos desde backend
        fetchPolygons();

        return () => {
            map.off();
            map.remove();
        };
    }, [fetchPolygons, createPolygon]);

    // Redibujar al cambiar polygons
    useEffect(() => {
        if (!mapRef.current || !drawnItemsRef.current) return;
        drawnItemsRef.current.clearLayers();

        polygons.forEach((poly) => {
            // Backend devuelve coordenadas en formato GeoJSON [lng, lat]
            // Convertir a formato Leaflet [lat, lng]
            const leafletCoords = geoJSONToLeaflet(poly.coordinates as [number, number][]);

            L.polygon(leafletCoords.map((c) => L.latLng(c[0], c[1])), {
                color: '#3388ff',
                weight: 2,
                fillColor: '#3388ff',
                fillOpacity: 0.4,
            }).addTo(drawnItemsRef.current!);
        });
    }, [polygons]);

    return <div id="map" className="w-full h-[75vh] min-h-[600px] rounded-xl overflow-hidden relative" />;
}