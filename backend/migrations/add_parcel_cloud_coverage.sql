-- Distingue la nubosidad global de escena de la estimada dentro de la parcela.
ALTER TABLE sentinel_acquisitions
    ADD COLUMN IF NOT EXISTS scene_id VARCHAR,
    ADD COLUMN IF NOT EXISTS parcel_cloud_cover DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS parcel_shadow_cover DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS valid_pixel_percentage DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS cloud_method VARCHAR;

ALTER TABLE sentinel_acquisitions
    ALTER COLUMN cloud_coverage DROP NOT NULL;

COMMENT ON COLUMN sentinel_acquisitions.cloud_coverage IS
    'Nubosidad global de la escena/producto Sentinel (eo:cloud_cover)';
COMMENT ON COLUMN sentinel_acquisitions.parcel_cloud_cover IS
    'Porcentaje de clases SCL 8, 9 y 10 dentro del polígono';
COMMENT ON COLUMN sentinel_acquisitions.parcel_shadow_cover IS
    'Porcentaje de clase SCL 3 dentro del polígono';
