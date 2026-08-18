# Resumen de mejoras del pipeline Sentinel-2

**Fecha:** 17 de agosto de 2026
**Branch:** `feature/parcel-cloud-coverage`

## Resumen ejecutivo

Se corrigió el tratamiento de la nubosidad para que la calidad de una adquisición no dependa únicamente del porcentaje global informado para toda la escena Sentinel-2. Ahora el sistema calcula las nubes, sombras y píxeles útiles dentro de la geometría exacta de cada parcela mediante la capa SCL de Sentinel-2 L2A.

Además, el cálculo de NDVI utiliza la misma máscara espacial y de calidad, y los objetivos OE3 y OE4 solo pueden procesar adquisiciones aptas y con máscara de nubes aplicada. Esto evita que una fecha aparentemente despejada a nivel de escena genere resultados agrícolas contaminados por nubes sobre la parcela.

## Problema identificado

El sistema mostraba resultados contradictorios en parcelas cercanas y en una misma fecha porque utilizaba `eo:cloud_cover`, un indicador calculado para la escena satelital completa. Ese valor no permite saber cuánta nube se encuentra realmente encima de una parcela específica.

Por ejemplo, una escena puede tener poca nubosidad global y, al mismo tiempo, una nube puede cubrir gran parte de una parcela pequeña. Por este motivo se separaron explícitamente los siguientes conceptos:

- **Nubosidad de escena:** metadato general provisto por el catálogo satelital.
- **Nubosidad de parcela:** porcentaje calculado únicamente dentro del polígono de la parcela.
- **Sombras de parcela:** porcentaje de píxeles clasificados como sombra de nube.
- **Píxeles válidos de origen:** proporción con información satelital disponible.
- **Píxeles utilizables:** proporción restante después de excluir nubes, sombras y datos inválidos.

## Cambios realizados

### 1. Cálculo de nubosidad real sobre la parcela

- Se integró la clasificación SCL de Sentinel-2 L2A junto con `dataMask`.
- Se aplica la geometría exacta de la parcela, por lo que los píxeles exteriores no afectan los porcentajes.
- Se consideran nubes las clases SCL 8, 9 y 10.
- Se considera sombra de nube la clase SCL 3.
- Se consideran datos inválidos la clase SCL 0 y los píxeles con `dataMask = 0`.
- La solicitud SCL conserva una resolución cercana a sus 20 metros nativos y corrige el ancho según la latitud.
- Las descargas usan consistentemente `mosaickingOrder: leastCC` para evitar diferencias entre productos obtenidos para una misma adquisición.

### 2. Persistencia y trazabilidad

Se añadieron campos para conservar la procedencia y calidad de cada adquisición:

- `scene_id`
- `parcel_cloud_cover`
- `parcel_shadow_cover`
- `valid_pixel_percentage`
- `usable_pixel_percentage`
- `quality_status`
- `cloud_method`
- `scl_data`
- `analysis_valid_pixel_percentage`
- `cloud_mask_applied`

Las migraciones correspondientes son:

- `backend/migrations/add_parcel_cloud_coverage.sql`
- `backend/migrations/add_scl_quality_and_masked_ndvi.sql`

### 3. Política de calidad

| Estado | Condiciones principales | Uso permitido |
|---|---|---|
| `suitable` | Nubes de parcela ≤ 20 %, datos válidos de origen ≥ 80 % y píxeles utilizables ≥ 80 % | NDVI, OE3 y OE4 |
| `caution` | Nubes ≤ 20 % y datos válidos ≥ 80 %, pero píxeles utilizables < 80 % por sombras u otras exclusiones | Revisión; no se usa automáticamente en OE3/OE4 |
| `unsuitable` | Nubes > 20 % o datos válidos de origen < 80 % | Se conserva para trazabilidad, pero se bloquea en OE3/OE4 |

### 4. NDVI con máscara coherente

- La capa SCL se reproyecta de su cuadrícula aproximada de 20 m a la cuadrícula de las bandas B04/B08 mediante vecino más cercano.
- La máscara combinada excluye el exterior de la parcela, nodata, valores no finitos, denominadores iguales a cero, datos inválidos, sombras y nubes.
- Los valores excluidos se escriben como `NaN` y no participan en las estadísticas.
- Media, mínimo, máximo, desviación estándar, mediana, percentil 10 y percentil 90 usan exactamente la misma máscara válida.
- Los NDVI históricos se recalcularon y se invalidaron los resultados derivados que ya no eran confiables.

### 5. Protección de los objetivos OE3 y OE4

- OE3 y OE4 rechazan adquisiciones que no tengan `cloud_mask_applied = true`.
- También rechazan fechas cuyo estado no sea `suitable`.
- La validación de propiedad de la parcela se ejecuta antes de devolver resultados idempotentes existentes.
- La máscara binaria de OE3 utiliza el contrato: 0 = no cultivado, 1 = cultivado y 255 = sin datos.
- Al regenerar resultados se eliminan en cascada los derivados anteriores, evitando descriptores de textura huérfanos.
- OE4 genera los descriptores de bordes, homogeneidad y contraste solamente sobre segmentaciones válidas.

### 6. Cambios en el frontend

- Se distingue visualmente la nubosidad de **escena** de la nubosidad de **parcela**.
- Se muestran nubes, sombras, datos válidos de origen y píxeles utilizables.
- Las fechas se identifican como **Apta**, **Precaución** o **No apta** mediante etiquetas y colores.
- Las fechas no aptas siguen visibles en el módulo Sentinel para auditoría, pero no pueden seleccionarse para OE3 u OE4.

### 7. Automatización operativa

Se incorporaron scripts para actualizar datos históricos y regenerar los productos:

- `backend/scripts/backfill_scl_quality.py`: obtiene SCL y recalcula la calidad local.
- `backend/scripts/calculate_missing_suitable_ndvi.py`: calcula NDVI faltantes únicamente para adquisiciones aptas.
- `backend/scripts/regenerate_oe3_oe4.py`: regenera segmentaciones OE3 y texturas OE4 válidas.

## Resultados obtenidos con los datos locales

| Fecha | Nubes de escena | Nubes de parcela | Píxeles utilizables | Estado | NDVI medio | OE3/OE4 |
|---|---:|---:|---:|---|---:|---|
| 2026-05-10 | 5,80 % | 0,00 % | 100,00 % | Apta | 0,4256 | Segmentación 63,04 %; 3 texturas |
| 2026-07-27 | 1,72 % | 0,00 % | 100,00 % | Apta | 0,7868 | Segmentación 99,80 %; 3 texturas |
| 2026-08-11 | 6,45 % | 42,88 % | 57,12 % | No apta | 0,4084 con máscara | Sin OE3/OE4 |

El resultado del 11 de agosto es la evidencia más importante de la corrección: aunque la escena reportaba solamente 6,45 % de nubes, la parcela estaba cubierta en 42,88 %. Con el criterio anterior esa fecha podía aceptarse; con el nuevo cálculo queda correctamente bloqueada para OE3 y OE4.

### Descriptores OE4 regenerados

| Fecha | Bordes (normalizado) | Homogeneidad | Contraste |
|---|---:|---:|---:|
| 2026-05-10 | 0,0808 | 0,1050 | 0,1682 |
| 2026-07-27 | 0,0533 | 0,0519 | 0,1132 |

## Validaciones ejecutadas

- Ocho pruebas específicas del pipeline de nubes, NDVI y calidad finalizaron correctamente.
- La compilación de los módulos Python finalizó sin errores.
- La generación del esquema OpenAPI se completó correctamente.
- El build de producción del frontend y la validación de TypeScript finalizaron correctamente.
- Se comprobó la respuesta HTTP del frontend y el estado saludable del backend.
- Se verificó que no quedaran texturas huérfanas después de la regeneración.
- Las migraciones fueron aplicadas sobre la base local después de generar respaldos.

## Alcance y limitaciones

- SCL es una clasificación oficial derivada de Sentinel-2 L2A y constituye una estimación mucho más representativa para cada parcela, pero no es una medición física perfecta de cada nube.
- Su resolución nativa aproximada es de 20 m; por eso los bordes de nubes y parcelas pueden presentar incertidumbre espacial.
- Una adquisición no apta puede conservar un NDVI enmascarado para auditoría, pero no puede alimentar automáticamente OE3 ni OE4.
- Estas mejoras resuelven la calidad del procesamiento satelital. No sustituyen la falta de una fuente nacional completa de geometrías de parcelas; los datos de Brasil siguen siendo evidencia parcial para los objetivos que dependen de esa disponibilidad.

## Conclusión

La mejora principal fue pasar de una decisión basada en la nubosidad general de una escena a una evaluación local, reproducible y trazable dentro de cada parcela. El NDVI y los productos OE3/OE4 ahora comparten una política de calidad coherente, por lo que se reduce considerablemente el riesgo de generar conclusiones agrícolas a partir de píxeles nublados, sombreados o inválidos.
