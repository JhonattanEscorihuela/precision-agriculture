/**
 * Tests para funciones de conversión de coordenadas.
 *
 * Para ejecutar (si tienes Jest configurado):
 * npm test coordUtils.test.ts
 *
 * O simplemente copiar y pegar en la consola del navegador.
 */

import {
    leafletToGeoJSON,
    geoJSONToLeaflet,
    validateGeoJSONCoords,
    detectCoordFormat
} from './coordUtils';

// Test 1: leafletToGeoJSON
console.log('🧪 Test 1: leafletToGeoJSON');
const leafletCoords = [[40.4168, -3.7038], [40.4268, -3.7038], [40.4268, -3.6938]];
const geoJsonResult = leafletToGeoJSON(leafletCoords as [number, number][]);
console.log('Input (Leaflet):', leafletCoords);
console.log('Output (GeoJSON):', geoJsonResult);
console.assert(
    geoJsonResult[0][0] === -3.7038 && geoJsonResult[0][1] === 40.4168,
    '❌ leafletToGeoJSON failed'
);
console.log('✅ leafletToGeoJSON passed\n');

// Test 2: geoJSONToLeaflet
console.log('🧪 Test 2: geoJSONToLeaflet');
const geoJsonCoords = [[-3.7038, 40.4168], [-3.7038, 40.4268], [-3.6938, 40.4268]];
const leafletResult = geoJSONToLeaflet(geoJsonCoords as [number, number][]);
console.log('Input (GeoJSON):', geoJsonCoords);
console.log('Output (Leaflet):', leafletResult);
console.assert(
    leafletResult[0][0] === 40.4168 && leafletResult[0][1] === -3.7038,
    '❌ geoJSONToLeaflet failed'
);
console.log('✅ geoJSONToLeaflet passed\n');

// Test 3: Round trip (debe volver al original)
console.log('🧪 Test 3: Round trip conversion');
const original = [[40.4168, -3.7038], [40.4268, -3.7038]];
const roundTrip = geoJSONToLeaflet(
    leafletToGeoJSON(original as [number, number][])
);
console.log('Original:', original);
console.log('After round trip:', roundTrip);
console.assert(
    roundTrip[0][0] === original[0][0] && roundTrip[0][1] === original[0][1],
    '❌ Round trip failed'
);
console.log('✅ Round trip passed\n');

// Test 4: validateGeoJSONCoords - válido
console.log('🧪 Test 4: Validate valid GeoJSON coords');
const validCoords = [[-3.7038, 40.4168], [-67.477, 8.890], [150.0, -33.8]];
const isValid = validateGeoJSONCoords(validCoords as [number, number][]);
console.log('Coords:', validCoords);
console.log('Valid?', isValid);
console.assert(isValid === true, '❌ Validation failed for valid coords');
console.log('✅ Validation passed\n');

// Test 5: validateGeoJSONCoords - inválido
console.log('🧪 Test 5: Validate invalid GeoJSON coords');
const invalidCoords = [[200, 40], [-67.477, 8.890]]; // lng > 180
const isInvalid = validateGeoJSONCoords(invalidCoords as [number, number][]);
console.log('Coords:', invalidCoords);
console.log('Valid?', isInvalid);
console.assert(isInvalid === false, '❌ Should be invalid');
console.log('✅ Invalid detection passed\n');

// Test 6: detectCoordFormat - GeoJSON
console.log('🧪 Test 6: Detect GeoJSON format');
const geoJsonFormat = [[-67.477, 8.890], [-67.472, 8.891]];
const detected1 = detectCoordFormat(geoJsonFormat as [number, number][]);
console.log('Coords:', geoJsonFormat);
console.log('Detected format:', detected1);
console.assert(detected1 === 'geojson', '❌ Should detect geojson');
console.log('✅ GeoJSON format detection passed\n');

// Test 7: detectCoordFormat - Leaflet
console.log('🧪 Test 7: Detect Leaflet format');
const leafletFormat = [[40.4168, -3.7038], [40.4268, -3.7038]];
const detected2 = detectCoordFormat(leafletFormat as [number, number][]);
console.log('Coords:', leafletFormat);
console.log('Detected format:', detected2);
console.assert(detected2 === 'leaflet', '❌ Should detect leaflet');
console.log('✅ Leaflet format detection passed\n');

// Test 8: Venezuela coords (del notebook)
console.log('🧪 Test 8: Venezuela coords from notebook');
const venezuelaGeoJSON = [
    [-67.477732, 8.890243],
    [-67.472585, 8.891811],
    [-67.482623, 8.921237]
];
const venezuelaLeaflet = geoJSONToLeaflet(venezuelaGeoJSON as [number, number][]);
console.log('GeoJSON (backend format):', venezuelaGeoJSON[0]);
console.log('Leaflet (map format):', venezuelaLeaflet[0]);
console.assert(
    venezuelaLeaflet[0][0] === 8.890243 && venezuelaLeaflet[0][1] === -67.477732,
    '❌ Venezuela conversion failed'
);
console.log('✅ Venezuela coords conversion passed\n');

console.log('════════════════════════════════════════');
console.log('✅ Todos los tests pasaron correctamente!');
console.log('════════════════════════════════════════');
