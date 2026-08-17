# Calidad de observaciones Sentinel-2 y máscara NDVI

## Qué representa cada métrica

- `cloud_coverage`: nubosidad global declarada por la escena STAC. Sirve para
  preseleccionar fechas, pero no describe necesariamente la parcela.
- `parcel_cloud_cover`: porcentaje de los píxeles SCL válidos de la parcela en
  clases 8, 9 o 10 (nube media, alta y cirros).
- `parcel_shadow_cover`: porcentaje de los píxeles SCL válidos en clase 3
  (sombra de nube).
- `valid_pixel_percentage`: cobertura de datos fuente válidos dentro de la
  parcela, antes de excluir nubes y sombras.
- `usable_pixel_percentage`: proporción total de la parcela que queda utilizable
  después de excluir datos inválidos, nubes y sombras.
- `analysis_valid_pixel_percentage`: proporción de la parcela que realmente
  intervino en el NDVI, medida sobre la grilla B04/B08.

SCL se conserva en `sentinel_acquisitions.scl_data` como GeoTIFF de dos bandas
(SCL y `dataMask`). Esto permite reproducir el control de calidad y el NDVI.

## Política de aptitud

| Estado | Regla |
| --- | --- |
| `suitable` | nube local ≤ 20%, datos fuente ≥ 80% y píxeles utilizables ≥ 80% |
| `caution` | nube local ≤ 20% y datos fuente ≥ 80%, pero utilizables < 80% por sombras |
| `unsuitable` | nube local > 20% o datos fuente < 80% |

Una observación `unsuitable` puede conservarse como evidencia, pero no debe
interpretarse como una medición agronómica confiable sin advertencia.

## Máscara aplicada al NDVI

Antes de calcular el índice se alinean SCL y `dataMask` con la grilla B04/B08.
La reproyección usa vecino más próximo porque SCL es categórico. Se excluyen:

- píxeles fuera de la geometría de la parcela;
- `nodata`, valores no finitos y denominador B08+B04 igual a cero;
- `dataMask=0` y SCL 0;
- sombra SCL 3;
- nubes SCL 8, 9 y 10.

El TIFF NDVI escribe esos píxeles como `NaN`. Las medias, desviación, extremos,
mediana y percentiles usan exactamente la misma máscara. El campo
`cloud_mask_applied` confirma que el resultado ya sigue esta metodología.

Al reemplazar un NDVI legado se invalidan su overlay, segmentación, descriptores
y overlays de textura, porque todos dependen del raster anterior.

## Puerta de calidad para OE3 y OE4

La segmentación y el análisis de textura verifican antes de reutilizar o crear
resultados que:

- el NDVI tenga `cloud_mask_applied=true`;
- la adquisición tenga `quality_status=suitable`;
- el usuario sea propietario de la parcela.

Las máscaras binarias OE3 usan `0` para no cultivado, `1` para cultivado y
`255` como `nodata`. Esto evita confundir el exterior de la parcela o una nube
enmascarada con suelo no cultivado.

## Migración y backfill

Aplicar, en orden:

1. `backend/migrations/add_parcel_cloud_coverage.sql`
2. `backend/migrations/add_scl_quality_and_masked_ndvi.sql`

Para completar adquisiciones existentes:

```bash
PYTHONPATH=/app python scripts/backfill_scl_quality.py
```

Para volver a descargar B04, B08 y SCL bajo la misma selección `leastCC` y
recalcular los NDVI existentes:

```bash
PYTHONPATH=/app python scripts/backfill_scl_quality.py --refresh-bands
```

La metadata STAC es complementaria. Si STAC falla después de que Process API
entregó TIFF válidos, el backfill conserva las bandas y reporta la advertencia.
