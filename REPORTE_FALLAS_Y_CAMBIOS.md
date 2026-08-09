# Reporte de fallas encontradas y cambios realizados

Fecha de revisión: 9 de agosto de 2026

Rama objetivo: `main`

Alcance: frontend, backend, overlays OE3/OE4 y comparación fenológica.

## Resumen ejecutivo

La integración frontend de los overlays NDVI y textura quedó conectada con los endpoints reales del backend. También se corrigió la comparación fenológica, que rechazaba parcelas válidas por utilizar IDs autoincrementales como referencias fijas.

La parcela local verificada dispone actualmente de tres observaciones NDVI distribuidas en 70 días. Por esa razón el sistema muestra la curva como una comparación exploratoria, pero no afirma todavía que el patrón sea o no arroz. La clasificación solo se habilita con un mínimo de cinco observaciones, 90 días de cobertura, valores finitos y variación suficiente.

## Fallas corregidas

### 1. Referencias fenológicas asociadas a IDs de parcelas

El backend asumía que los polígonos `1`, `2` y `3` siempre eran parcelas de referencia. Estos son IDs autoincrementales, por lo que una parcela normal creada por un usuario podía coincidir con uno de ellos y recibir incorrectamente el error de autorreferencia.

Corrección:

- Se eliminaron `REFERENCE_POLYGON_IDS` y la dependencia de parcelas pertenecientes a usuarios.
- Se incorporó una plantilla teórica de arroz documentada para Rio Grande do Sul, Brasil.
- La respuesta ya no informa IDs de referencia inexistentes.

### 2. Comparación por fechas calendario exactas

El algoritmo anterior exigía al menos cinco fechas exactamente iguales entre la parcela y las referencias. Este criterio falla cuando los ciclos agrícolas comienzan en fechas o años diferentes.

Corrección:

- Los puntos se alinean por días transcurridos desde la primera observación NDVI disponible.
- La plantilla se interpola linealmente en cada día observado.
- Se incluye una advertencia permanente indicando que la primera observación no equivale necesariamente a la fecha real de siembra.

### 3. Clasificación con información insuficiente

La interfaz podía terminar sin gráfica o presentar mensajes que sugerían una falla cuando había pocos datos.

Corrección:

- Con una o más observaciones válidas se devuelve y muestra la curva.
- Cuando la cobertura es insuficiente, `similarity_score` y `matches_rice_pattern` son `null`.
- Con cobertura suficiente, una similitud moderada conserva `matches_rice_pattern=null` y se presenta como resultado no concluyente, no como un rechazo.
- El frontend muestra el badge `Comparación exploratoria`, el número de observaciones, los días de cobertura y las advertencias.
- Solo se calcula Pearson después de validar cantidad de observaciones, cobertura, finitud y varianza.
- Las fechas duplicadas se promedian y los datos inválidos se descartan con advertencias explícitas.

### 4. Overlays reales no integrados en el mapa

El backend ya exponía imágenes PNG en base64, pero el mapa y los paneles todavía no consumían completamente ese contrato.

Corrección:

- Se agregaron los modos exclusivos `Ninguno`, `NDVI` y `Textura` al mapa Leaflet.
- Se agregó el selector de descriptor de textura: contraste, bordes y homogeneidad.
- El mapa solicita el último resultado NDVI de cada parcela visible y crea la capa con `L.imageOverlay` y los `bounds` recibidos.
- Un error `404` conserva solamente el borde de la parcela.
- Se agregaron indicadores de carga por parcela y notificaciones de error accesibles.
- Los paneles de segmentación y textura muestran la imagen real, su leyenda y un botón de recálculo con `force=true`.

### 5. Caché y respuestas obsoletas en el frontend

Cambiar rápidamente de parcela, modo o descriptor podía permitir que una respuesta anterior reemplazara el estado más reciente.

Corrección:

- Caché local NDVI por `acquisition_id`.
- Caché local de textura por `ndvi_result_id:kernel`.
- Deduplificación de solicitudes simultáneas.
- Versionado de escrituras para impedir que respuestas antiguas sobrescriban resultados nuevos.
- Limpieza del caché cuando cambia el usuario autenticado.
- El recálculo conserva la imagen anterior mientras llega la nueva respuesta.

### 6. Sincronización después de calcular NDVI

El dashboard no se actualizaba inmediatamente después de finalizar un cálculo NDVI desde el panel Sentinel.

Corrección:

- `NDVIPanel` notifica la finalización del cálculo.
- `SentinelPanel` propaga el evento.
- Los widgets vuelven a consultar NDVI, segmentación, textura y fenología.

### 7. Errores de TypeScript con Axios

Algunos componentes utilizaban comprobaciones de errores Axios que no eran compatibles con la versión instalada.

Corrección:

- Se usa el import nombrado `isAxiosError`.
- Se eliminaron capturas con `any` en el contexto de autenticación.

### 8. Exposición de secretos en archivos y logs

Se encontraron un `SECRET_KEY` histórico escrito literalmente en un script de validación y un log que mostraba los primeros caracteres del token OAuth de Sentinel.

Corrección:

- El script `tasks/validation_checks.sh` ahora lee `SECRET_KEY` desde el entorno y no conserva el valor literal.
- La autenticación Sentinel confirma el éxito sin registrar ninguna parte del access token.
- Si la clave histórica llegó a utilizarse fuera del entorno local, debe rotarse; eliminarla del archivo actual no la elimina del historial Git.

## Cambios principales por área

### Backend

- Nuevo servicio fenológico basado en una plantilla independiente de los IDs de usuario.
- Nuevo contrato con suficiencia de datos, cobertura, fuente, método de alineación, advertencias y resultado nullable.
- Documentación del endpoint `/api/phenology/compare/{polygon_id}` actualizada.
- Nueve casos de prueba para regresión del ID 1, cobertura suficiente, fechas duplicadas, series constantes, ausencia de NDVI, autorización y los tres estados de clasificación.

### Frontend

- Contexto global y tipos para overlays.
- Hooks para vistas previas y capas Leaflet.
- Controles del mapa, previews NDVI/textura y toast de errores.
- Integración de previews en segmentación y textura.
- Widget fenológico adaptado al contrato real y al estado exploratorio.
- Exposición del último `acquisition_id` y `ndvi_result_id` desde `useParcelAnalysis`.
- Actualización automática del dashboard después de calcular NDVI.

### Cambios previos verificados en la interfaz

- El mensaje `Próximamente` ya no aparece en el panel Sentinel.
- El panel incluye el enlace `Ver dashboard de análisis` hacia `/cultivos/{polygonId}`.
- Estos dos cambios ya estaban presentes en la base de `origin/main` revisada y no constituyen diferencias nuevas de este commit.

## Fallas y limitaciones pendientes

### Prioridad alta

1. **La referencia fenológica aún es teórica.** Existen dos series CSV en `data/`, pero el servicio no las consume y no cuentan con metadatos verificables suficientes de parcela, variedad, fecha de siembra, ciclo y ground truth para calibrar la plantilla. La clasificación debe considerarse experimental hasta integrar y validar una referencia observada.
2. **El día cero es aproximado.** Se utiliza la primera observación NDVI, no la siembra real. Una futura versión debe guardar la fecha de siembra o estimar el desfase fenológico de forma explícita.
3. **Falta autorización por propiedad en endpoints críticos.** `PUT /polygons/{id}` y `DELETE /polygons/{id}` no exigen correctamente el usuario propietario. Los endpoints Sentinel requieren JWT a nivel de router, pero consultan `polygon_id` sin verificar que pertenezca al usuario autenticado. Esto permite riesgos IDOR y debe corregirse antes de una exposición pública.
4. **Hay respuestas cacheadas antes de validar ownership.** Los servicios NDVI, segmentación y textura pueden devolver un resultado existente por ID antes de comprobar que el recurso pertenece al usuario. Un usuario autenticado que adivine IDs podría obtener datos ajenos. La validación debe ejecutarse antes de cualquier retorno idempotente o la consulta debe filtrar por recurso y propietario.
5. **No existe un sistema de migraciones.** El backend utiliza `create_all`, que crea tablas nuevas pero no actualiza tablas existentes. Debe incorporarse Alembic y versionarse las columnas, restricciones e índices.
6. **La ruta cacheada del backend sigue realizando trabajo costoso.** El overlay NDVI vuelve a procesar el TIFF para recuperar `bounds`, y el overlay de textura vuelve a ejecutar el procesamiento necesario para reconstruir datos auxiliares. Los `bounds`, metadatos e interpretación deberían persistirse junto al PNG.
7. **La configuración de producción no está alineada.** Docker Compose entrega variables `COPERNICUS_CLIENT_*`, mientras el código espera `SENTINEL_CLIENT_*`; el argumento `NEXT_PUBLIC_API_URL` no se pasa durante el build; Nginx no enruta `/polygons`; y `Dockerfile.prod` utiliza Node 18 aunque Next.js 16 requiere una versión compatible de Node 20.

### Prioridad media

1. **Los endpoints de overlay no declaran un `response_model`.** La documentación OpenAPI no describe correctamente el JSON de éxito. Deben agregarse schemas Pydantic para NDVI y textura.
2. **La caché de textura necesita una restricción única real.** Debe garantizarse en base de datos la unicidad de `ndvi_result_id + kernel_type` para evitar duplicados por concurrencia.
3. **Tratamiento de `nodata` en textura.** Convertir `NaN` a cero antes de la convolución puede contaminar los bordes de la parcela. Debe usarse una máscara válida durante el filtrado.
4. **Percentiles calculados por imagen.** Los colores de textura son relativos a cada parcela y no son directamente comparables entre parcelas. Para comparaciones globales se requieren umbrales calibrados y versionados.
5. **Opacidad duplicada.** El PNG contiene canal alfa y Leaflet aplica además opacidad `0.7`, lo que puede atenuar demasiado el resultado.
6. **Caché frontend sin límite.** Las imágenes base64 se conservan en memoria durante la sesión. Debe agregarse una política LRU o límite por cantidad/tamaño.
7. **Reintento global del dashboard.** El botón de reintento fenológico vuelve a solicitar también segmentación y textura. Conviene exponer reintentos independientes por recurso.
8. **El filtro temporal no afecta la fenología.** El dashboard comunica que el rango se aplica a todos los widgets, pero el endpoint fenológico no recibe `start_date/end_date` y utiliza todo el histórico disponible, hasta el límite del CRUD.
9. **Pearson no mide diferencia absoluta.** Dos curvas con forma semejante pero niveles o amplitudes diferentes pueden obtener una correlación alta. Antes de validar una clasificación deben combinarse correlación, error/amplitud y ground truth agronómico.
10. **La tabla y el overlay OE4 no usan la misma población.** Los descriptores tabulares se calculan sobre la máscara cultivada erosionada, mientras el overlay de textura colorea todos los píxeles NDVI válidos sin aplicar la segmentación. La imagen y la interpretación pueden no representar el mismo conjunto de píxeles.
11. **Parseo de fechas sensible a zona horaria.** Hay fechas `YYYY-MM-DD` convertidas con `new Date(string)` en el contexto temporal y la evolución NDVI. En Venezuela pueden interpretarse como UTC y mostrarse o consultarse un día antes. Debe utilizarse un parser de fecha local consistente.
12. **La segmentación no identifica arroz.** El umbral `NDVI > 0.3` separa principalmente vegetación de suelo o baja cobertura; no demuestra por sí solo que el área corresponda a arroz cultivado.
13. **Las solicitudes de overlays no se cancelan físicamente.** El versionado evita escrituras obsoletas, pero no aborta la transferencia ni limita la concurrencia al mover el mapa. Conviene incorporar `AbortController` y un límite de solicitudes simultáneas.

### Prioridad baja y mantenimiento

1. El frontend no posee pruebas automatizadas de componentes, hooks o interacción Leaflet; actualmente solo se valida con TypeScript, ESLint y comprobación manual.
2. `pytest` y `pytest-asyncio` no están declarados en un archivo de dependencias de desarrollo, por lo que las pruebas backend no son reproducibles en una imagen recién construida sin instalarlos temporalmente.
3. El repositorio contiene archivos `.pyc` históricos ya versionados. Aunque `.gitignore` evita archivos nuevos, conviene retirarlos del índice en un commit de mantenimiento separado.
4. Los errores del frontend todavía dependen parcialmente del texto `detail` enviado por el backend. Es preferible utilizar códigos de error estables.
5. El token de sesión se conserva en `localStorage`; una política de cookies `HttpOnly`, CSP y protección frente a XSS ofrecería mayor seguridad para producción.
6. `NDVIEvolutionWidget.tsx`, `NDVIPanel.tsx` y `SentinelPanel.tsx` superan el límite acordado de 200 líneas para organisms; `DateRangeFilter.tsx` y `NDVIStats.tsx` superan 100 líneas para molecules. Deben dividirse en molecules/hooks más pequeños.
7. Persisten estilos inline anteriores en el listado de cultivos, `NDVIEvolutionWidget` y `NDVIColorScale`; deben migrarse a Tailwind. El estilo inline de `SentinelPanel` sí se sustituyó por Tailwind en esta entrega.
8. Persisten llamadas `console.error` en runtime y `console.log` en una prueba de coordenadas; deben sustituirse por manejo de errores o retirarse al cerrar la depuración.
9. ESLint aún informa dependencias incompletas en dos efectos de `SentinelPanel`; la variable no utilizada detectada durante la revisión sí fue eliminada.
10. Algunos skeletons usan `Math.random()` durante el render, lo cual puede ocasionar diferencias de hidratación. Deben usar valores deterministas.
11. No hay CI, cobertura, pre-commit ni auditoría automática de dependencias; varias pruebas placeholder están vacías y algunos scripts manuales pueden ser recolectados accidentalmente por pytest.

## Validaciones ejecutadas

- `9 passed` en las pruebas unitarias de fenología.
- TypeScript: `tsc --noEmit --incremental false` sin errores.
- ESLint sobre los componentes, hooks y tipos modificados: sin errores.
- Construcción y reinicio de los servicios con Docker Compose: correctos.
- Los archivos Compose de desarrollo y producción son sintácticamente válidos; producción advierte que las variables sensibles y `NEXT_PUBLIC_API_URL` no están definidas en el entorno de validación.
- Endpoint real de la parcela local ID `1`: HTTP `200`, tres puntos, 70 días y estado exploratorio.
- Se confirmó que `.env`, cachés de pytest y artefactos de ejecución no forman parte del conjunto a publicar.

## Criterio para habilitar una clasificación fenológica

La implementación actual requiere simultáneamente:

- al menos cinco observaciones NDVI únicas;
- al menos 90 días entre la primera y la última observación;
- valores finitos en ambas curvas;
- variación suficiente en la parcela y en la plantilla.

Cumplir estos mínimos permite calcular la correlación, pero no sustituye la validación agronómica pendiente con datos reales de referencia.
