-- Migración de coordenadas: [lat, lng] → [lng, lat]
--
-- IMPORTANTE: Ejecutar SOLO UNA VEZ si ya tienes polígonos guardados
-- con coordenadas invertidas.
--
-- Este script invierte las coordenadas de todos los polígonos existentes
-- para que cumplan con el estándar GeoJSON [lng, lat]

-- Verificar datos ANTES de la migración
SELECT
    id,
    name,
    coordinates[1:3] as primeras_3_coords,
    created_at
FROM polygons
ORDER BY id;

-- Si el primer valor de cada par es pequeño (< 90), probablemente está invertido
-- Ejemplo: [40.4168, -3.7038] está mal (latitud primero)
-- Correcto: [-3.7038, 40.4168] (longitud primero)

-- Crear backup antes de migrar
CREATE TABLE IF NOT EXISTS polygons_backup AS
SELECT * FROM polygons;

-- Verificar backup
SELECT COUNT(*) as total_backup FROM polygons_backup;

-- Migración: Invertir [lat, lng] → [lng, lat]
UPDATE polygons
SET coordinates = (
  SELECT json_agg(
    json_build_array(
      (coord->1)::numeric,  -- lng (era el segundo)
      (coord->0)::numeric   -- lat (era el primero)
    )
  )
  FROM json_array_elements(coordinates::json) AS coord
)
WHERE id > 0;

-- Verificar datos DESPUÉS de la migración
SELECT
    id,
    name,
    coordinates[1:3] as primeras_3_coords,
    updated_at
FROM polygons
ORDER BY id;

-- Ahora el primer valor debe ser mayor (longitud)
-- Ejemplo: [[-3.7038, 40.4168], ...] ✅

-- Si algo salió mal, restaurar desde backup:
-- DELETE FROM polygons;
-- INSERT INTO polygons SELECT * FROM polygons_backup;

-- Si todo está correcto, eliminar backup:
-- DROP TABLE polygons_backup;
