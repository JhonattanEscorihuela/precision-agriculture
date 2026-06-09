/**
 * Utilidades geoespaciales para cálculos de área y distancia.
 */

/**
 * Calcula el área de un polígono en hectáreas usando la fórmula de Shoelace.
 * Asume coordenadas en grados [lng, lat] WGS84.
 *
 * Para áreas pequeñas (~< 100 km²), proyección simple es suficiente.
 *
 * @param coordinates Array de coordenadas [[lng, lat], ...]
 * @returns Área en hectáreas
 */
export function calculatePolygonArea(coordinates: number[][]): number {
  if (coordinates.length < 3) return 0;

  // Convertir grados a metros aproximados (en el ecuador)
  // 1 grado lat ≈ 111,320 metros
  // 1 grado lng ≈ 111,320 * cos(lat) metros
  const lat = coordinates[0][1]; // Latitud de referencia
  const metersPerDegreeLat = 111320;
  const metersPerDegreeLng = 111320 * Math.cos((lat * Math.PI) / 180);

  // Convertir coordenadas a metros relativos
  const coordsMeters = coordinates.map(([lng, lat]) => [
    lng * metersPerDegreeLng,
    lat * metersPerDegreeLat,
  ]);

  // Fórmula de Shoelace para calcular área
  let area = 0;
  for (let i = 0; i < coordsMeters.length; i++) {
    const [x1, y1] = coordsMeters[i];
    const [x2, y2] = coordsMeters[(i + 1) % coordsMeters.length];
    area += x1 * y2 - x2 * y1;
  }
  area = Math.abs(area) / 2;

  // Convertir de m² a hectáreas (1 ha = 10,000 m²)
  return area / 10000;
}

/**
 * Formatea área en hectáreas con 2 decimales.
 */
export function formatArea(hectares: number): string {
  return `${hectares.toFixed(2)} ha`;
}
