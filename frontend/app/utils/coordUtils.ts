/**
 * Utilidades para conversión de coordenadas entre Leaflet y GeoJSON.
 *
 * IMPORTANTE:
 * - Leaflet usa: [latitude, longitude] (lat, lng)
 * - GeoJSON usa: [longitude, latitude] (lng, lat)
 * - Backend espera: GeoJSON estándar [lng, lat]
 */

export type LeafletCoord = [number, number]; // [lat, lng]
export type GeoJSONCoord = [number, number]; // [lng, lat]

/**
 * Convierte coordenadas de Leaflet [lat, lng] a GeoJSON [lng, lat].
 *
 * @param coords - Array de coordenadas en formato Leaflet [lat, lng]
 * @returns Array de coordenadas en formato GeoJSON [lng, lat]
 *
 * @example
 * const leafletCoords = [[40.4168, -3.7038], [40.4268, -3.7038]];
 * const geoJsonCoords = leafletToGeoJSON(leafletCoords);
 * // Result: [[-3.7038, 40.4168], [-3.7038, 40.4268]]
 */
export function leafletToGeoJSON(coords: LeafletCoord[]): GeoJSONCoord[] {
    return coords.map(([lat, lng]) => [lng, lat]);
}

/**
 * Convierte coordenadas de GeoJSON [lng, lat] a Leaflet [lat, lng].
 *
 * @param coords - Array de coordenadas en formato GeoJSON [lng, lat]
 * @returns Array de coordenadas en formato Leaflet [lat, lng]
 *
 * @example
 * const geoJsonCoords = [[-3.7038, 40.4168], [-3.7038, 40.4268]];
 * const leafletCoords = geoJSONToLeaflet(geoJsonCoords);
 * // Result: [[40.4168, -3.7038], [40.4268, -3.7038]]
 */
export function geoJSONToLeaflet(coords: GeoJSONCoord[]): LeafletCoord[] {
    return coords.map(([lng, lat]) => [lat, lng]);
}

/**
 * Valida si las coordenadas son válidas (dentro de rangos correctos).
 *
 * @param coords - Array de coordenadas en formato GeoJSON [lng, lat]
 * @returns true si todas las coordenadas son válidas
 */
export function validateGeoJSONCoords(coords: GeoJSONCoord[]): boolean {
    return coords.every(([lng, lat]) => {
        // Longitud: -180 a 180
        // Latitud: -90 a 90
        return lng >= -180 && lng <= 180 && lat >= -90 && lat <= 90;
    });
}

/**
 * Detecta si un array de coordenadas está probablemente en formato incorrecto
 * (valores de latitud fuera del rango típico sugieren orden incorrecto).
 *
 * @param coords - Array de coordenadas [a, b]
 * @returns "geojson" | "leaflet" | "unknown"
 */
export function detectCoordFormat(coords: [number, number][]): 'geojson' | 'leaflet' | 'unknown' {
    if (coords.length === 0) return 'unknown';

    // Chequear si el primer valor está en rango de latitud (-90, 90)
    // Si está, probablemente es [lat, lng] (Leaflet)
    const firstValues = coords.map(c => c[0]);
    const avgFirst = firstValues.reduce((a, b) => a + Math.abs(b), 0) / firstValues.length;

    if (avgFirst <= 90) {
        // Probablemente latitud (Leaflet)
        return 'leaflet';
    } else {
        // Probablemente longitud (GeoJSON)
        return 'geojson';
    }
}

/**
 * Verifica si un polígono está cerrado (primer punto === último punto).
 *
 * @param coords - Array de coordenadas
 * @returns true si el polígono está cerrado
 */
export function isPolygonClosed(coords: [number, number][]): boolean {
    if (coords.length < 2) return false;

    const first = coords[0];
    const last = coords[coords.length - 1];

    return first[0] === last[0] && first[1] === last[1];
}

/**
 * Cierra un polígono agregando el primer punto al final si no está cerrado.
 * GeoJSON requiere que los polígonos estén cerrados (primer punto = último punto).
 *
 * @param coords - Array de coordenadas
 * @returns Array de coordenadas con el polígono cerrado
 *
 * @example
 * const open = [[-3.7038, 40.4168], [-3.7038, 40.4268], [-3.6938, 40.4268]];
 * const closed = closePolygon(open);
 * // Result: [[-3.7038, 40.4168], [-3.7038, 40.4268], [-3.6938, 40.4268], [-3.7038, 40.4168]]
 */
export function closePolygon(coords: [number, number][]): [number, number][] {
    if (coords.length === 0) return coords;

    // Verificar si ya está cerrado
    if (isPolygonClosed(coords)) {
        return coords;
    }

    // Cerrar el polígono agregando el primer punto al final
    return [...coords, coords[0]];
}
