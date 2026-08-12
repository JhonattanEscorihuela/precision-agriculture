-- Invalidar caches de overlays existentes
-- Ejecutar después de actualizar el código de generación de overlays
-- para forzar regeneración con máscaras de polígono

-- 1. Invalidar cache de overlays NDVI (campo overlay_png en tabla ndvi_results)
UPDATE ndvi_results SET overlay_png = NULL WHERE overlay_png IS NOT NULL;

-- 2. Invalidar cache de overlays de textura (tabla texture_overlay_cache)
DELETE FROM texture_overlay_cache;

-- Verificar invalidación
SELECT
    'NDVI overlays' AS tipo,
    COUNT(*) AS total_registros,
    COUNT(overlay_png) AS con_cache
FROM ndvi_results
UNION ALL
SELECT
    'Texture overlays' AS tipo,
    COUNT(*) AS total_registros,
    COUNT(overlay_png) AS con_cache
FROM texture_overlay_cache;
