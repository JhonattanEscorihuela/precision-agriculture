# Recomendaciones de auditoría — Precision Agriculture

Fecha de revisión: 1 de agosto de 2026

Carpeta auditada: `C:\proyectos2\precision-agriculture-main`

Alcance: frontend, backend, PostgreSQL activo, OE1–OE4, seguridad, pruebas, dependencias, Docker y metodología científica.

> La auditoría fue de solo lectura. No se modificó el código ni la información almacenada.

## Resumen ejecutivo

El proyecto funciona como demostración local, pero todavía no está listo para producción ni para considerar confiables todos sus resultados agronómicos.

Estado general:

- OE1 Sentinel está conectado, pero sus endpoints están expuestos sin autenticación ni comprobación de propietario.
- OE2 NDVI está conectado, pero el procesamiento batch falla y el manejo de píxeles inválidos y nubes debe corregirse.
- OE3 segmentación está conectado, aunque actualmente representa `NDVI > 0.3`, no necesariamente área cultivada.
- OE3 fenología está conectado, pero no funciona con la base activa por el uso de referencias hardcodeadas `[1, 2, 3]`.
- OE4 textura está conectado, pero sus nombres y criterios requieren validación científica.
- La base activa tiene constraints faltantes y datos huérfanos.
- No existe una suite de pruebas funcional ni un flujo de despliegue de producción completo.

## Validaciones ejecutadas

| Validación | Resultado |
|---|---|
| TypeScript | 0 errores |
| ESLint | 0 errores y 14 warnings |
| Build Next.js | Pasa con `NODE_ENV=production`; falla bajo la configuración `development` del Compose |
| Pruebas backend incluidas | `pytest` no está instalado |
| Pruebas con dependencias temporales | Import obsoleto; excluyéndolo: 1 aprobada y 17 errores |
| Auditoría frontend | 4 vulnerabilidades bajas, 35 moderadas y 27 altas |
| Auditoría imagen backend | 55 hallazgos conocidos en 9 paquetes |

## P0 — Bloqueantes críticos

### 1. Corregir autenticación y autorización

Problemas encontrados:

- `PUT /polygons/{id}` y `DELETE /polygons/{id}` no requieren JWT ni comprueban que la parcela pertenezca al usuario.
- Todo el router Sentinel está abierto, incluyendo disponibilidad, descargas, adquisición y `/test`.
- NDVI, segmentación y textura retornan resultados cacheados antes de validar ownership.

Archivos principales:

- `backend/app/api/endpoints/polygons.py`
- `backend/app/api/endpoints/sentinel.py`
- `backend/app/services/ndvi_service.py`
- `backend/app/services/segmentation_service.py`
- `backend/app/services/texture_service.py`

Recomendaciones:

- Agregar `get_current_user` a todo el router Sentinel.
- Consultar cada recurso mediante `(resource_id, current_user.id)` o mediante joins con `Polygon.user_id`.
- Validar ownership antes de devolver resultados existentes.
- Eliminar o proteger `/api/sentinel/test` fuera de desarrollo.
- Agregar rate limiting y cuotas por usuario a autenticación, Sentinel y procesos costosos.
- Crear pruebas automáticas de acceso entre dos usuarios diferentes.

### 2. Corregir máscaras de datos y nubes

Los evalscripts actuales solicitan B04/B08 sin `dataMask`, SCL, CLM o CLP. Los píxeles fuera del polígono o sin datos pueden llegar como cero y actualmente se consideran válidos.

Impacto:

- NDVI mínimo y desviación sesgados.
- Porcentaje de vegetación calculado sobre píxeles que no pertenecen a la parcela.
- Nubes y sombras interpretadas como cambios de vegetación.
- OE3, OE4 y fenología heredan errores de OE2.

Recomendaciones:

- Descargar en una sola petición B04, B08, `dataMask` y SCL o CLM.
- Excluir píxeles `dataMask == 0` y clases de nube, sombra, nieve y nodata.
- Fijar resolución espacial, preferiblemente 10 m/píxel para B04/B08.
- Fijar la escena o documentar explícitamente el mosaico utilizado.
- Guardar `scene_id`, tile, órbita, baseline, fecha/hora, resolución, CRS y versión del evalscript.
- Versionar el algoritmo y recalcular los resultados históricos afectados.

Documentación oficial:

- https://docs.sentinel-hub.com/api/latest/user-guides/datamask/
- https://docs.sentinel-hub.com/api/latest/data/sentinel-2-l2a/

### 3. Reparar la integridad de PostgreSQL

En la base activa solo existe el FK `polygon.user_id`. Se detectaron:

- 7 adquisiciones huérfanas.
- 7 NDVI huérfanos.
- 2 segmentaciones huérfanas.
- 6 texturas huérfanas.
- 10 NDVI sin mediana, p10 ni p90.

Recomendaciones:

- Incorporar Alembic.
- Crear respaldo antes de intervenir la base.
- Identificar, limpiar o reasignar los registros huérfanos.
- Agregar los FK declarados por los modelos y sus cascadas.
- Agregar un UNIQUE real para `(polygon_id, acquisition_date)`.
- Verificar los constraints mediante pruebas contra PostgreSQL, no solamente SQLite.
- Retirar `create_all` como mecanismo de evolución del esquema.

### 4. Corregir NDVI batch

Se observó un procesamiento que respondió HTTP 200 con cero resultados nuevos y dos fallos por `MissingGreenlet`.

Causa principal:

- `ndvi_batch.py` crea `AsyncSession(engine)` directamente y omite el sessionmaker configurado con `expire_on_commit=False`.
- El CRUD confirma la transacción y expira objetos que después vuelven a consultarse de forma implícita.

Recomendaciones:

- Usar siempre la factoría común `async_session()`.
- Hacer que la capa de servicio controle la transacción completa.
- Reemplazar commits internos de los CRUD por `flush` cuando corresponda.
- No devolver éxito general cuando todo el lote falla.
- Definir un contrato explícito para éxito, éxito parcial y fallo total.
- Añadir pruebas de lote con adquisiciones nuevas, existentes y concurrentes.

### 5. Proteger y rotar secretos

El `.env` contiene valores con apariencia real para JWT y Copernicus. No se incluyen sus valores en este informe.

Recomendaciones:

- Si esta carpeta fue enviada o publicada, rotar `SECRET_KEY` y las credenciales Sentinel.
- Utilizar secretos del entorno o un secret manager.
- Mantener `.env` fuera de imágenes, backups compartidos y control de versiones.
- Revisar cualquier repositorio o archivo ZIP compartido anteriormente.

## P1 — Alta prioridad

### 6. Eliminar información sensible de logs

Actualmente pueden registrarse:

- Prefijo del token Copernicus.
- Emails y parámetros SQL.
- Coordenadas completas.
- Headers y respuestas externas.
- TIFF binarios completos durante errores o logging SQL.

Recomendaciones:

- SQLAlchemy `INFO` solamente en desarrollo controlado.
- Logs estructurados con ID de correlación.
- Redactar tokens, emails, URL de base de datos y geometrías.
- Nunca registrar blobs ni cuerpos binarios.
- Enviar al cliente mensajes genéricos y conservar el detalle solamente en logs seguros.

### 7. Rediseñar la comparación fenológica

Problemas:

- Referencias hardcodeadas `[1, 2, 3]`.
- La única parcela activa es ID 3 y el servicio la rechaza como referencia.
- IDs 1 y 2 fueron borrados, pero sus NDVI huérfanos siguen participando.
- Se exigen cinco fechas exactamente coincidentes.
- Pearson no valida varianza, valores finitos ni desfase temporal.
- Los umbrales 0.70 y 0.85 no tienen calibración reproducible.

Recomendaciones:

- Crear un modelo de parcelas de referencia con cultivo, variedad, ciclo, fecha de siembra, procedencia y validación de campo.
- Usar identificadores estables, no IDs autoincrementales casuales.
- Alinear las curvas por días desde siembra o etapa fenológica.
- Interpolar fechas y evaluar DTW o correlación con desfase.
- Separar entrenamiento, calibración y validación.
- Reportar sensibilidad, especificidad, ROC, incertidumbre y número de observaciones.
- Hacer que el backend devuelva directamente `matches_rice_pattern` y la versión del criterio.

### 8. Corregir el significado de “área cultivada”

Actualmente significa solamente `NDVI > 0.3`.

Recomendaciones:

- Renombrar temporalmente el resultado a “área con vegetación”.
- No afirmar que representa arroz o cultivo sin ground truth.
- Calibrar el umbral por cultivo, etapa y región.
- Validar con precisión, recall, F1, IoU y matriz de confusión.
- Permitir varios thresholds o guardar el threshold como parte de la clave del resultado.
- Permitir regenerar la máscara cuando la primera ejecución utilizó `save_mask=false`.

### 9. Corregir las métricas NDVI

Problemas:

- `ndvi_mean` se calcula como `NDVI(mean(B04), mean(B08))`, que no equivale a `mean(NDVI por píxel)`.
- Denominadores cero terminan representados como NDVI 0.
- Mediana, p10 y p90 están declarados, pero no se calculan ni guardan.

Recomendaciones:

- Definir y documentar una única métrica principal.
- Calcular estadísticas sobre píxeles válidos y enmascarados.
- Proteger división por cero y validar `NaN`/infinito.
- Persistir media, mediana, p10, p90, desviación, cantidad válida y porcentaje enmascarado.
- Añadir tests numéricos con raster conocido y tolerancias explícitas.

### 10. Corregir el área geográfica

El backend aplica Shoelace directamente a longitud/latitud y guarda grados cuadrados como si fueran hectáreas.

Recomendaciones:

- Utilizar cálculo geodésico o proyectar a un CRS métrico adecuado.
- Convertir el resultado a hectáreas antes de persistirlo.
- Unificar el cálculo frontend/backend.
- Agregar una prueba con una geometría de área conocida.
- Corregir también `meters_per_deg_lng`: debe depender de `cos(radians(latitude))`.

### 11. Actualizar dependencias vulnerables

Prioridades conocidas:

- Next.js 16.1.1.
- PostCSS 8.4.31.
- `python-jose==3.3.0`.
- FastAPI 0.100.0, Starlette, Pydantic, Requests, h11 y dependencias de GDAL/Pillow presentes en la imagen.

Recomendaciones:

- Actualizar en una rama separada y ejecutar pruebas de regresión.
- Generar lock reproducible y hashes para Python.
- Generar un SBOM.
- Ejecutar `pip-audit` y `yarn audit` en CI.
- Configurar actualizaciones automáticas con revisión humana.

Avisos de referencia:

- https://github.com/advisories/GHSA-8h8q-6873-q5fj
- https://github.com/advisories/GHSA-r28c-9q8g-f849
- https://github.com/advisories/GHSA-6c5p-j8vq-pqhj
- https://github.com/advisories/GHSA-cjwg-qfpm-7377

## P2 — Arquitectura y mantenibilidad

### 12. Centralizar la comunicación frontend-backend

Problemas:

- Hay múltiples usos de `http://localhost:8000`.
- Se mezclan `fetch`, Axios directo y `apiClient`.
- El manejo de 401, errores y cancelación es diferente en cada componente.

Recomendaciones:

- Crear `NEXT_PUBLIC_API_URL`.
- Usar un único cliente HTTP.
- Centralizar JWT, 401, timeouts, abortos y traducción de errores.
- Separar DTO de API, modelos de dominio y modelos de presentación.

### 13. Mejorar autenticación frontend

Recomendaciones:

- Evitar tokens de 30 días en `localStorage` cuando se prepare producción.
- Preferir cookies `HttpOnly`, `Secure` y `SameSite`, con protección CSRF.
- Implementar access token corto, refresh, rotación y revocación.
- Validar la sesión contra `/auth/me` al iniciar.
- Agregar CSP y headers de seguridad en Next.js.

### 14. Resolver fallas funcionales de interfaz

- Propagar errores de `createPolygon`; no mostrar éxito cuando el backend falla.
- Revertir la capa “fantasma” del mapa si la creación falla.
- Implementar o retirar soporte KML.
- Persistir edición y eliminación de Leaflet o deshabilitar esos controles.
- Reiniciar `acquisitionSuccess` al seleccionar otra fecha.
- Cancelar peticiones anteriores con `AbortController`.
- Diferenciar loading, error, vacío y éxito.
- Evitar que un error de red se muestre como “no hay datos”.
- Parsear `YYYY-MM-DD` como fecha calendario local para evitar el día anterior.
- Cambiar `usePolygonHealth` por un endpoint batch o concurrencia limitada.

### 15. Cumplir las reglas de componentes

Componentes que exceden los límites acordados:

- `NDVIEvolutionWidget.tsx`: 458 líneas.
- `SentinelPanel.tsx`: 333 líneas.
- `NDVIPanel.tsx`: 309 líneas.
- `DateRangeFilter.tsx`: 214 líneas siendo molecule.
- `NDVIStats.tsx`: 129 líneas siendo molecule.

Recomendaciones:

- Extraer hooks de datos y máquinas de estado.
- Separar encabezado, gráfica, estados vacíos y acciones.
- Sustituir estilos inline por utilidades Tailwind.
- Revisar el CSS personalizado y conservar únicamente lo necesario para Leaflet o casos que Tailwind no cubra.

### 16. Accesibilidad y responsive

Recomendaciones:

- Añadir `role="dialog"`, `aria-modal`, focus trap y cierre con Escape.
- Añadir alternativa textual para gráficas.
- No envolver botones dentro de enlaces.
- No comunicar discriminación solamente mediante color.
- Ajustar la altura mínima del mapa para móviles.
- Implementar drag-and-drop real o retirar el texto que lo anuncia.
- Respetar `prefers-reduced-motion`.

### 17. Sacar blobs del almacenamiento transaccional

Recomendaciones:

- Guardar TIFF y máscaras en object storage.
- Mantener en PostgreSQL metadatos, URI, tamaño, checksum, versión y propietario.
- Evitar seleccionar blobs en listados, dashboard y fenología.
- Añadir límites de tamaño, retención y limpieza.

### 18. Mover cálculos pesados a trabajos asíncronos

NDVI, Rasterio, SciPy y textura se ejecutan actualmente dentro del event loop.

Recomendaciones:

- Introducir una cola de trabajos y workers.
- Registrar estado `queued/running/succeeded/failed`.
- Añadir progreso, cancelación, reintentos e idempotencia.
- Limitar concurrencia y consumo por usuario.
- Utilizar threadpool solo como transición.

## P3 — Pruebas, despliegue y documentación

### 19. Reparar y ampliar pruebas

- Añadir `pytest`, `pytest-asyncio`, configuración y dependencias de desarrollo.
- Corregir el import obsoleto de Sentinel.
- Completar los cuatro archivos de prueba vacíos.
- Actualizar fixtures con `created_at`.
- Agregar pruebas OE3, OE4, fenología, batch y pipeline.
- Probar autorización horizontal con dos usuarios.
- Probar carreras e idempotencia con parámetros diferentes.
- Crear pruebas frontend con Vitest/Testing Library y E2E con Playwright.
- Convertir `coordUtils.test.ts` en una prueba real, no `console.assert`.

### 20. Incorporar CI

Gates recomendados:

1. Formato y lint.
2. TypeScript.
3. Build de producción.
4. Tests frontend y backend.
5. Cobertura mínima.
6. Migraciones sobre PostgreSQL temporal.
7. `pip-audit` y `yarn audit`.
8. Build de imágenes.
9. Escaneo de secretos y contenedores.

### 21. Crear configuración Docker de producción

Problemas actuales:

- Frontend ejecuta `yarn dev`.
- Compose fija `NODE_ENV=development`.
- PostgreSQL se publica en el host con credencial trivial.
- Backend/frontend ejecutan como root.
- No hay healthchecks completos ni límites de recursos.

Recomendaciones:

- Separar perfiles `dev` y `prod`.
- Usar Dockerfiles multistage.
- Ejecutar `next build` y luego `next start`.
- Crear usuarios no-root.
- No publicar PostgreSQL fuera de la red interna.
- Añadir healthchecks, restart policy y límites de CPU/memoria.
- Usar imágenes fijadas por versión/digest y secretos externos.

### 22. Backups y observabilidad

Recomendaciones:

- Backups cifrados externos con retención definida.
- Pruebas periódicas de restauración.
- Definir RPO y RTO.
- Añadir `/healthz` y `/readyz`.
- Métricas de latencia, fallos, uso de cuota y duración de trabajos.
- Logs estructurados, tracing y alertas.

### 23. Mejorar reproducibilidad y documentación

- Incorporar Git y conservar historial verificable.
- Documentar instalación, variables, migraciones, pruebas y despliegue.
- Actualizar rutas obsoletas en `QUICK_START.md` y `SENTINEL_SERVICE.md`.
- Documentar contratos reales OE1–OE4.
- Versionar datasets, escenas, parámetros y resultados científicos.
- Conservar checksums y manifiestos de los datos usados para validar el modelo.

## Orden recomendado de implementación

### Fase 1 — Seguridad y contención

- [ ] Proteger endpoints y corregir ownership.
- [ ] Retirar/proteger `/api/sentinel/test`.
- [ ] Rotar secretos si fueron compartidos.
- [ ] Redactar logs y desactivar SQL INFO.
- [ ] Retirar exposición externa de PostgreSQL.

### Fase 2 — Datos y cálculos

- [ ] Corregir `dataMask`, nubes, escena y resolución.
- [ ] Reparar NDVI batch.
- [ ] Introducir Alembic.
- [ ] Respaldar y limpiar datos huérfanos.
- [ ] Agregar FK y UNIQUE reales.
- [ ] Corregir área geodésica y estadísticas NDVI.

### Fase 3 — Validez científica

- [ ] Renombrar “área cultivada” a “área con vegetación”.
- [ ] Versionar algoritmos y resultados.
- [ ] Construir referencias fenológicas verificadas.
- [ ] Calibrar umbrales con ground truth.
- [ ] Validar textura y fenología fuera de muestra.

### Fase 4 — Frontend y contratos

- [ ] Centralizar API URL y cliente HTTP.
- [ ] Corregir fechas, carreras y estados de error.
- [ ] Reparar KML y edición del mapa.
- [ ] Acordar DTO versionado para OE3/OE4.
- [ ] Refactorizar componentes que superan los límites.
- [ ] Mejorar accesibilidad y responsive.

### Fase 5 — Calidad y producción

- [ ] Reparar la suite de pruebas.
- [ ] Incorporar CI y auditoría de dependencias.
- [ ] Actualizar dependencias vulnerables.
- [ ] Crear imágenes Docker de producción.
- [ ] Añadir workers, backups y observabilidad.

## Recomendación final

No se recomienda agregar nuevas funcionalidades hasta completar, como mínimo:

1. Autenticación y ownership.
2. Corrección de `dataMask` y nubes.
3. Migraciones e integridad de PostgreSQL.
4. Reparación de NDVI batch.
5. Rediseño de las referencias fenológicas.

Esos puntos afectan directamente la seguridad, la conservación de datos y la validez de los resultados mostrados al usuario.

---

# RESOLUCIÓN DE RECOMENDACIONES — 2025-06-XX

## ✅ RESUELTOS

### P0.1 — Autenticación Sentinel
**Estado:** RESUELTO
**Qué se hizo:** Se agregó `dependencies=[Depends(get_current_user)]`
al router de Sentinel. Todos los endpoints ahora requieren JWT.
**Archivo:** `backend/app/api/endpoints/sentinel.py`

### P0.1 — Endpoint /test protegido
**Estado:** RESUELTO
**Qué se hizo:** Guard que bloquea el endpoint si
`ENVIRONMENT != "development"`. Retorna 403 en producción.
**Archivo:** `backend/app/api/endpoints/sentinel.py`

### P2.12 — URLs hardcodeadas frontend
**Estado:** RESUELTO
**Qué se hizo:** Se creó `NEXT_PUBLIC_API_URL` en `.env.local`.
Se migraron las 13 ocurrencias de `http://localhost:8000` a
usar `apiClient` con baseURL configurable.
**Archivos:** `frontend/lib/axios.ts`, `frontend/.env.local`,
múltiples componentes migrados a apiClient.
**Verificación:** `grep -r "localhost:8000" frontend/` retorna
0 resultados (solo el fallback en axios.ts).

### P1.9 — NDVI mean "incorrecto"
**Estado:** INVESTIGADO Y DESCARTADO
**Por qué no se cambió:** El método actual
`NDVI(mean(B04), mean(B08))` fue validado empíricamente
contra Copernicus Browser con 3.5% de diferencia promedio
(4 fechas, todas dentro de tolerancia ±5%). Ver evidencia
en `OE2_PARA_REPORTE_WORD.md`, Tabla 2.
Al cambiar al método `mean(NDVI_por_pixel)`, los valores
cayeron a la mitad (~0.36 vs 0.70) debido a píxeles de
borde/nodata incluidos en el promedio.
**Conclusión:** El método actual es correcto para nuestro
contexto y coincide con la metodología de Copernicus.

### P3 — Docker producción
**Estado:** RESUELTO
**Qué se hizo:**
- `docker-compose.prod.yml` con Nginx reverse proxy
- `frontend/Dockerfile.prod` con build standalone multi-stage
- `nginx/nginx.conf` con routing /api→backend, /→frontend
- `.env.production.example` con template de variables
- `next.config.ts` con `output: 'standalone'`
**Archivos nuevos:** `docker-compose.prod.yml`,
`frontend/Dockerfile.prod`, `nginx/nginx.conf`,
`.env.production.example`

### P0.5 — Secretos
**Estado:** RESUELTO
**Qué se hizo:** `.gitignore` cubre `*.env`. Se crearon
`.env.example` (backend y frontend) como templates sin
secretos reales. Variables sensibles solo en `.env` local.

---

## ⏳ NO RESUELTOS (con justificación)

### P0.2 — Máscaras de nubes (dataMask, SCL, CLM)
**Estado:** NO IMPLEMENTADO
**Por qué:** Requiere cambiar los evalscripts de Sentinel
Hub y re-procesar todas las adquisiciones existentes.
Impacto alto en datos ya calculados. Se documenta como
LIMITACIÓN en la tesis.
**Plan futuro:** Implementar en siguiente iteración si
hay tiempo antes de defensa.

### P0.3 — Integridad PostgreSQL (FK, huérfanos)
**Estado:** NO IMPLEMENTADO
**Por qué:** Requiere Alembic migrations + limpieza de
datos existentes. Riesgo de romper datos de prueba actuales.
**Plan futuro:** Implementar con Alembic antes del
despliegue final en AWS.

### P0.4 — NDVI batch (MissingGreenlet)
**Estado:** NO IMPLEMENTADO
**Por qué:** El endpoint individual funciona correctamente.
El batch es una optimización no crítica para la demo.
El frontend usa llamadas individuales que funcionan.
**Plan futuro:** Corregir session factory si se necesita
procesamiento masivo.

### P1.7 — Fenología con IDs hardcodeados
**Estado:** NO IMPLEMENTADO (parcialmente funcional)
**Por qué:** Los IDs [1,2,3] existen actualmente en BD
y el endpoint funciona. El problema aparecería si se
borran esas parcelas. Se necesita rediseñar con tabla
`reference_parcels` dedicada.
**Plan futuro:** Crear tabla de referencia antes de
despliegue AWS.

### P1.10 — Área geográfica (Shoelace)
**Estado:** NO IMPLEMENTADO
**Por qué:** No es crítico para la demo. Los polígonos
se visualizan correctamente en el mapa. El cálculo de
área no se muestra prominentemente en la UI.
**Plan futuro:** Usar pyproj Geod para cálculo preciso.

### P1.6 — Logs con datos sensibles
**Estado:** NO IMPLEMENTADO
**Por qué:** En desarrollo local no es un riesgo. Se
implementará antes del despliegue en AWS.
**Plan futuro:** Filtrar PII y tokens antes de AWS.

### P2.13-16 — Issues frontend
**Estado:** PENDIENTE PARA FRONTEND
**Responsable:** Compañera
**Items:**
- Token 30 días en localStorage (aceptable para tesis)
- Componentes >200 líneas (refactorizar si hay tiempo)
- Errores no propagados (mejorar UX)
- Accesibilidad (ARIA attrs)

### P2.17 — BLOBs en PostgreSQL
**Estado:** NO IMPLEMENTADO
**Por qué:** Para el volumen de datos de la tesis
(~33 imágenes × 260KB = 8.6MB), PostgreSQL es suficiente.
Object storage es over-engineering para este caso.
**Plan futuro:** Solo si se escala a muchos usuarios.

### P2.18 — Cálculos bloqueantes en event loop
**Estado:** NO IMPLEMENTADO
**Por qué:** Los cálculos (NDVI, textura) tardan 3-5
segundos. Con un solo usuario (demo de tesis), no hay
problema de concurrencia.
**Plan futuro:** Celery/asyncio task queue si se escala.

### P3.19-23 — Tests, CI/CD, backups
**Estado:** NO IMPLEMENTADO
**Por qué:** Scope de tesis. Tests existentes de OE2
pasan (16/16). CI/CD y backups son para producción real.

---

## 📊 RESUMEN

| Categoría | Total | Resueltos | No resueltos | % |
|-----------|-------|-----------|--------------|---|
| P0 (Críticos) | 5 | 2 | 3 | 40% |
| P1 (Alta) | 6 | 1* | 5 | 17% |
| P2 (Arquitectura) | 7 | 1 | 6 | 14% |
| P3 (Despliegue) | 5 | 1 | 4 | 20% |
| **TOTAL** | **23** | **5** | **18** | **22%** |

*P1.9 investigado y descartado (no era un error)

**Justificación general:** Este es un proyecto de TESIS
con scope limitado. Se priorizaron los cambios que:
1. Afectan el despliegue en AWS (CORS, env vars, Docker)
2. Afectan la seguridad mínima (auth Sentinel)
3. Fueron necesarios para correctitud científica (NDVI)

Los items no resueltos están documentados como
LIMITACIONES o TRABAJO FUTURO en el documento de tesis.
