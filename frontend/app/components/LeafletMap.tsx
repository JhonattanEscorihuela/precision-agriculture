'use client';

import React, { useEffect } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import 'leaflet-draw';
import { usePolygons } from '../context/PolygonContext';
import { v4 as uuidv4 } from 'uuid';
import axios from '@/lib/axios';

export default function LeafletMap() {
    const { addPolygon, setAllPolygons, polygons } = usePolygons(); // Ahora con setAllPolygons para sincronizar

    const mapRef = React.useRef<L.Map | null>(null);
    const drawnItemsRef = React.useRef<L.FeatureGroup | null>(null);

    // Función para obtener polígonos desde el backend
    const fetchPolygonsFromBackend = async () => {
        try {
            const response = await axios.get('/polygons');
            setAllPolygons(response.data); // Sincronizamos el contexto con los datos del backend
        } catch (error) {
            console.error('Error al obtener los polígonos desde el backend:', error);
        }
    };

    // Función para crear un nuevo polígono en el backend
    const createPolygonInBackend = async (polygon: { name: string; coordinates: number[][] }) => {
        try {
            const response = await axios.post('/polygons', polygon);
            const newPolygon = response.data;

            // Agregar el polígono recién creado al contexto local
            addPolygon(newPolygon);
        } catch (error) {
            console.error('Error al guardar el polígono en el backend:', error);
        }
    };

    // Inicializar el mapa
    useEffect(() => {
        const map = L.map('map', {
            center: [10.441, -66.3584], // Centrado en Venezuela
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

        baseLayers['OpenStreetMap'].addTo(map);
        L.control.layers(baseLayers).addTo(map);

        const drawnItems = new L.FeatureGroup();
        map.addLayer(drawnItems);
        drawnItemsRef.current = drawnItems;

        // Habilitar controles para dibujar polígonos
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
                circlemarker: false,
                polyline: false,
                marker: false,
            },
        });
        map.addControl(drawControl);

        // Manejo del evento de creación de un nuevo polígono
        map.on(L.Draw.Event.CREATED, (event: any) => {
            const layer = event.layer;
            drawnItems.addLayer(layer);

            // Extraer coordenadas del polígono dibujado
            const coordinates = layer.getLatLngs()[0]?.map((coord: L.LatLng) => [coord.lat, coord.lng]);

            // Nuevo polígono construido
            const newPolygon = {
                id: uuidv4(), // Este ID se reemplazará con el generado en el backend
                name: `Parcela ${new Date().toLocaleString()}`,
                coordinates,
            };

            // Guardar en el backend
            createPolygonInBackend(newPolygon);
        });

        // Permitir el ajuste dinámico del tamaño del mapa
        map.invalidateSize();

        // Ejecutar la función para obtener polígonos desde el backend
        fetchPolygonsFromBackend();

        return () => {
            map.remove();
        };
    }, []); // Este useEffect se ejecuta solo al montar

    // Actualizar y redibujar polígonos en el mapa al cambiar el estado
    useEffect(() => {
        if (!mapRef.current || !drawnItemsRef.current) return;
        const drawnItems = drawnItemsRef.current!;

        // Limpiar los polígonos dibujados previamente
        drawnItems.clearLayers();

        // Redibujar todos los polígonos almacenados en el contexto
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

            // Añadir capa al mapa interactivo
            drawnItems.addLayer(polygonLayer);
        });
    }, [polygons]); // Se actualizan cada vez que `polygons` cambian

    return (
        <div className="w-full h-[80vh] relative">
            <div id="map" className="h-full"></div>
        </div>
    );
}