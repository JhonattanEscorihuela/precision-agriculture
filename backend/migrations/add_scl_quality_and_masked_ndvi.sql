-- Persiste la evidencia SCL y la trazabilidad del NDVI enmascarado.
ALTER TABLE sentinel_acquisitions
    ADD COLUMN IF NOT EXISTS scl_data BYTEA,
    ADD COLUMN IF NOT EXISTS usable_pixel_percentage DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS quality_status VARCHAR;

ALTER TABLE ndvi_results
    ADD COLUMN IF NOT EXISTS analysis_valid_pixel_percentage DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS cloud_mask_applied BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN sentinel_acquisitions.scl_data IS
    'GeoTIFF de dos bandas: SCL y dataMask usados en la evaluación local';
COMMENT ON COLUMN sentinel_acquisitions.usable_pixel_percentage IS
    'Porcentaje de píxeles de parcela válidos y libres de nubes/sombras';
COMMENT ON COLUMN sentinel_acquisitions.quality_status IS
    'suitable, caution o unsuitable según política de calidad local';
COMMENT ON COLUMN ndvi_results.cloud_mask_applied IS
    'TRUE cuando el NDVI fue calculado excluyendo SCL 3, 8, 9 y 10';
