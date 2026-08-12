-- Agregar columna satellite_png a la tabla ndvi_results
-- Para cachear imagen satelital RGB true color

-- Ejecutar después de levantar el contenedor de BD:
-- docker exec -i precision-agriculture-db psql -U postgres -d precision < backend/migrations/add_satellite_png_column.sql

ALTER TABLE ndvi_results
ADD COLUMN IF NOT EXISTS satellite_png BYTEA;

-- Verificar que se creó correctamente
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'ndvi_results'
AND column_name = 'satellite_png';

-- Comentario en la columna para documentación
COMMENT ON COLUMN ndvi_results.satellite_png IS 'PNG RGB true color de la imagen satelital para visualización (caché)';
