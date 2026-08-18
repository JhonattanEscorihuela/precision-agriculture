# Informe final de mejoras y estado del proyecto

Fecha de validación: 17 de agosto de 2026.

## Resultado ejecutivo

El proyecto quedó operativo de extremo a extremo para identificar adquisiciones
Sentinel-2, calcular NDVI enmascarado, segmentar zonas cultivadas y evaluar tres
descriptores de textura. La corrección central fue reemplazar la nubosidad global
de escena como decisión final por una medición local dentro de cada parcela
basada en SCL y `dataMask`.

OE1 y OE2 están cubiertos técnica y funcionalmente. OE3 y OE4 también están
implementados e integrados, con evidencia exploratoria, pero conservan una
limitación científica: todavía no existe verdad terrestre suficiente para medir
exactitud agronómica ni generalización nacional.

## Cambios realizados

### Calidad de nubes y NDVI

- Nubosidad local calculada por parcela con clases SCL 8, 9 y 10.
- Sombra de nube calculada con SCL 3.
- Cobertura fuente válida y porcentaje final utilizable registrados por fecha.
- Reproyección de SCL categórico por vecino más cercano a la cuadrícula B04/B08.
- Máscara única para TIFF y todos los estadísticos NDVI; los excluidos son `NaN`.
- Estados `suitable`, `caution` y `unsuitable` visibles en frontend.
- OE3, OE4 y fenología solo consumen resultados `suitable` con
  `cloud_mask_applied=true`.

La fecha 2026-08-11 mostró por qué era necesario: la escena indicaba 6,45 % de
nubes, pero dentro de la parcela había 42,88 %. Ahora queda bloqueada para
análisis derivados.

### Seguridad y aislamiento de usuarios

- Actualización y eliminación de parcelas protegidas por JWT y propiedad.
- Descargas, disponibilidad y adquisición Sentinel protegidas contra acceso a
  parcelas de otro usuario.
- Respuesta 401 consistente cuando falta el token Bearer.
- Expiración JWT tomada de `ACCESS_TOKEN_EXPIRE_MINUTES` (480 minutos por
  defecto), en lugar de un valor fijo de 30 días.
- Pruebas específicas para parcela inexistente, usuario propietario y acceso
  ajeno.

### Integridad y migraciones de base de datos

- Alembic incorporado con baseline y revisión de adopción del esquema de calidad.
- Claves foráneas con borrado en cascada para adquisición, NDVI, segmentación,
  textura y cachés.
- Unicidad por parcela/fecha, adquisición/NDVI, NDVI/segmentación,
  segmentación/kernel y NDVI/kernel de overlay.
- Corrección del metadata de SQLModel 0.0.8: las claves foráneas se declaran
  explícitamente en los modelos `table=True`.
- El contenedor backend aplica `alembic upgrade head` antes de iniciar Uvicorn.

Antes de migrar se generó el respaldo local
`precision-agriculture-backups/pre_alembic_20260817.dump` (3.055.864 bytes),
SHA-256
`4C27E2A49D352FA3B7CB329025837C60B3DD21C80AC47D3206D5258D0D824EF8`.
La base activa quedó en `20260817_0002 (head)` sin alterar los conteos: 2
parcelas, 5 adquisiciones, 5 NDVI, 3 segmentaciones y 9 texturas.

### Frontend y experiencia de uso

- Una sola regla reutilizable determina si una adquisición puede alimentar
  análisis.
- Las fechas no aptas siguen visibles para auditoría, pero no son seleccionables
  para OE3/OE4.
- Corrección de efectos React, dependencias, estados de carga y código no usado.
- Pruebas unitarias para elegibilidad y etiquetas de calidad.
- Build standalone de Next.js, imagen de producción no-root y lockfile
  reproducible.
- Contexto Docker del frontend reducido de más de 137 MB a 778 KB mediante
  `.dockerignore`.

### Operación y producción

- Compose de desarrollo con healthchecks, montaje de código y dependencias
  explícitas entre servicios.
- Compose de producción corregido para variables `SENTINEL_CLIENT_*`, URL pública
  del API y nivel de logs SQL.
- Endpoint `/health` comprueba tanto API como conexión PostgreSQL.
- Nginx incorpora ruta de parcelas, encabezados de seguridad, CSP y límites de
  solicitudes para autenticación/API.
- Workflow de GitHub Actions con PostgreSQL, Alembic, pruebas, cobertura, lint,
  TypeScript, build Next.js y validación de imágenes Docker.

## Validaciones finales

| Validación | Resultado |
|---|---|
| Backend Pytest | 44 aprobadas, 2 integraciones externas omitidas |
| Cobertura backend | 52 % total |
| Pruebas frontend | 2/2 aprobadas |
| TypeScript | Sin errores |
| ESLint | Sin errores ni advertencias |
| Build Next.js | Correcto; 8 páginas generadas |
| Compose desarrollo/producción | Configuración válida |
| Alembic | `20260817_0002 (head)` |
| Backend local | `/health` responde `ok` |
| Frontend local | `/` y `/login` responden HTTP 200 |

## Estado de los objetivos

| Objetivo | Estado técnico | Estado científico |
|---|---|---|
| OE1 — Identificar escenas aptas | Completo | Evidencia local reproducible |
| OE2 — Aplicar NDVI | Completo | NDVI coherente con máscara local |
| OE3 — Analizar segmentación | Completo | Validación exploratoria parcial |
| OE4 — Evaluar textura | Completo | Validación exploratoria parcial |
| OE5 — Construir interfaz | Funcional e integrada | Falta reporte/exportación si se exige como alcance final |

Los CSV atribuidos a Brasil son útiles como prueba exploratoria, pero 37 de las
39 fechas del segundo archivo se solapan con el primero y no incluyen geometría,
cultivo ni etiquetas de campo. El análisis detallado y el protocolo para cerrar
la validación están en `docs/VALIDACION_CIENTIFICA_OE3_OE4.md`.

## Pendiente más crítico

La prioridad restante no es otro filtro de software: es conseguir verdad
terrestre trazable. Se necesitan parcelas con geometría, cultivo/variedad, ciclo,
fechas de observación y clases verificadas en campo, separadas por parcela entre
calibración y validación. Sin eso se puede defender el prototipo y su
reproducibilidad, pero no una exactitud agronómica nacional.

Como siguientes mejoras de ingeniería quedan elevar la cobertura de endpoints y
servicios OE3/OE4, automatizar respaldo/restore en despliegue y decidir si la
comparación temporal y exportación de informes forman parte obligatoria de OE5.
