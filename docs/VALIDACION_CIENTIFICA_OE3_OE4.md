# Validación científica y alcance de OE3/OE4

## Dictamen

Los objetivos OE3 y OE4 están **implementados y demostrables a nivel técnico**,
pero su validación agronómica es **parcial**. Los CSV atribuidos a Brasil son
suficientes como evidencia exploratoria de una serie NDVI y permiten ejercitar
el flujo temporal. No contienen la información necesaria para probar exactitud
frente a terreno, comparar parcelas independientes ni generalizar resultados a
parcelas venezolanas o nacionales.

Esta distinción evita dos afirmaciones que la evidencia disponible no soporta:

- OE3 no demuestra todavía que cada píxel clasificado como cultivado coincida
  con la cobertura observada en campo.
- OE4 no demuestra todavía que los descriptores de textura correspondan a una
  condición agronómica específica o que sean invariantes entre regiones,
  variedades, ciclos y prácticas de manejo.

## Evidencia disponible

Los archivos originales se conservaron sin modificación en `data/`.

| Archivo | Filas | Rango UTC declarado | Media de NDVI medio | Rango de NDVI medio | Nube de escena media/máxima |
|---|---:|---|---:|---:|---:|
| `Sentinel-2 L2A-3_NDVI-2025-05-18T00_00_00.000Z-2026-05-18T23_59_59.999Z.csv` | 64 | 2025-06-05 a 2026-05-18 | 0,4247 | 0,1801–0,8535 | 3,37 % / 19,94 % |
| `Sentinel-2 L2A-3_NDVI-2025-12-07T00_00_00.000Z-2026-06-07T23_59_59.999Z.csv` | 39 | 2025-12-07 a 2026-05-28 | 0,4667 | 0,1801–0,8535 | 1,33 % / 11,42 % |

El segundo archivo comparte 37 de sus 39 fechas con el primero. Esta alta
superposición indica que no deben contarse como dos experimentos independientes.
Además, ambos archivos tienen el mismo `sampleCount` (1.794) y `noDataCount`
(726) en las filas inspeccionadas, lo que es consistente con series relacionadas.

Los CSV aportan fecha, estadísticos de NDVI, conteo de muestras y nubosidad de
escena. No aportan identificador o geometría de parcela, coordenadas, cultivo,
variedad, fecha de siembra, manejo, observaciones de campo, etiquetas de verdad
terrestre, método de muestreo, licencia ni una división independiente de
calibración/validación.

## Qué está cubierto

### OE3 — Analizar zonas cultivadas por segmentación espacial

Cobertura técnica completa:

- segmentación reproducible mediante `NDVI > 0,3` (umbral configurable);
- máscara GeoTIFF con `0 = no cultivado`, `1 = cultivado` y `255 = nodata`;
- métricas de píxeles totales, cultivados y porcentaje cultivado;
- persistencia, idempotencia, control de propiedad y descarga de máscara;
- bloqueo de adquisiciones no aptas o sin máscara SCL aplicada;
- widget integrado para generar y consultar el resultado.

Validación pendiente:

- comparar la máscara contra polígonos o puntos etiquetados en terreno;
- reportar matriz de confusión, precisión, exhaustividad, F1 e IoU;
- estimar sensibilidad al umbral por región, fase fenológica y variedad;
- validar con parcelas independientes de las usadas para calibrar.

### OE4 — Evaluar descriptores de textura por filtrado convolucional

Cobertura técnica completa:

- operadores de bordes (Laplaciano), homogeneidad/variación local y contraste
  (gradiente Sobel) aplicados dentro de la zona cultivada válida;
- erosión de borde, normalización, estadísticos e indicador discriminativo;
- persistencia atómica de tres descriptores, caché de overlays y visualización;
- trazabilidad hacia segmentación, NDVI, adquisición y parcela;
- bloqueo de entradas no aptas por nubes y control de acceso por usuario.

Validación pendiente:

- asociar cada respuesta de textura con una observación agronómica verificable;
- medir repetibilidad temporal y estabilidad ante resolución, nubosidad residual
  y tamaño de parcela;
- comparar los descriptores con una línea base y entre clases de campo;
- probar en parcelas, fechas y regiones independientes.

## Protocolo mínimo para cerrar la validación

Cada parcela debe registrar, como mínimo:

| Campo | Requisito |
|---|---|
| `parcel_id` | Identificador estable y anonimizable |
| `geometry` | Polígono GeoJSON/WKT con CRS y fuente |
| `country`, `state`, `municipality` | Ubicación administrativa |
| `crop`, `variety` | Cultivo y variedad confirmados |
| `planting_date`, `harvest_date` | Fechas y ciclo agrícola |
| `observation_date` | Fecha UTC de visita o medición |
| `ground_truth_class` | Cultivado/no cultivado y condición observada |
| `sampling_method` | Recorrido, cuadrantes, dron u otra técnica |
| `observer`, `source` | Responsable y procedencia |
| `license_or_consent` | Permiso de uso y publicación |
| `split` | `calibration`, `validation` o `test` |

Para OE3 se recomienda etiquetar puntos o polígonos dentro y fuera del cultivo,
manteniendo las parcelas de validación fuera de la calibración del umbral. Para
OE4 se requiere definir antes del análisis qué condición de campo representa
cada clase (por ejemplo uniformidad, fallas de establecimiento o estrés) y cómo
se medirá.

## Criterios de cierre sugeridos

No se fija un valor científico universal sin acuerdo del tutor y del dominio,
pero el informe final debería incluir como mínimo:

1. procedencia, licencia y trazabilidad de cada conjunto de datos;
2. partición por parcela, no por píxel ni por fecha solapada;
3. métricas OE3 con intervalos de confianza y análisis de error;
4. comparación OE4 entre clases predefinidas y una línea base;
5. análisis de sensibilidad a umbral, resolución y política de nubes;
6. limitaciones de transferencia Brasil–Venezuela explícitamente declaradas.

## Conclusión operativa

La falta de una base nacional de parcelas no impide entregar un prototipo
funcional ni demostrar los algoritmos. Sí impide afirmar validación agronómica
nacional. La formulación defendible es: **OE3 y OE4 completos en implementación,
con validación exploratoria parcial y protocolo preparado para validación de
campo**.
