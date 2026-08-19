# Datos exploratorios de Brasil

Este directorio conserva dos exportaciones CSV de estadísticas temporales NDVI
compartidas para apoyar los objetivos OE3 y OE4. Los archivos se mantienen sin
transformaciones para preservar su trazabilidad.

## Integridad

| Archivo | SHA-256 |
|---|---|
| `Sentinel-2 L2A-3_NDVI-2025-05-18T00_00_00.000Z-2026-05-18T23_59_59.999Z.csv` | `B19189C7E59F4D2C77008BA0B7B8EB59ED7E262E534E6C691ED7275F36874EF8` |
| `Sentinel-2 L2A-3_NDVI-2025-12-07T00_00_00.000Z-2026-06-07T23_59_59.999Z.csv` | `C1257DD284169571870FDE3AD9CCA55736B6C4CE0CCA2B483796D4CCBDA173AF` |

## Uso permitido en el proyecto

- análisis exploratorio de tendencias y variabilidad NDVI;
- demostración del procesamiento temporal;
- apoyo parcial a OE3/OE4, siempre declarando sus limitaciones.

No deben presentarse como verdad terrestre, dos parcelas independientes ni una
muestra representativa nacional: 37 de las 39 fechas del segundo archivo están
también en el primero y los CSV no incluyen geometría, cultivo, manejo o
etiquetas observadas en campo.

El dictamen, los campos faltantes y el protocolo de cierre están documentados
en `docs/VALIDACION_CIENTIFICA_OE3_OE4.md`.
