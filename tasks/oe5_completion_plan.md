# Plan de Completitud OE5 — Construir Interfaz Integrada

**Fecha inicio**: 2026-08-21  
**Rama**: `feature/oe5-temporal-comparison-and-export`  
**Estado actual**: 85% completo (falta comparación temporal + exportación reportes)

---

## OBJETIVO ACADÉMICO 5

```
Desarrollar una interfaz de usuario orientada a servicios, que permita:
- ✅ Visualización de mapas de estado de salud del cultivo
- ✅ Comparación entre distintas fechas de análisis
- ⚠️ Exportación de los resultados generados
```

---

## FUNCIONALIDADES PENDIENTES

### 1. Comparación Temporal Multi-Fecha

**Frontend**:
- [ ] `components/organisms/TemporalComparisonWidget.tsx` (nuevo)
  - Selector multi-fecha (2-4 fechas simultáneas)
  - Grid 2x2 o 1x4 según cantidad seleccionada
  - Cada celda: mapa NDVI overlay + stats + imagen satelital
  - Sincronización de zoom/pan entre mapas
  - Toggle: NDVI / Segmentación / Textura
- [ ] `hooks/useTemporalComparison.ts` (nuevo)
  - Gestión estado multi-fecha
  - Fetch paralelo de análisis para fechas seleccionadas
  - Caché de resultados por fecha
- [ ] Integración en `/cultivos/[id]` (dashboard individual)
  - Nuevo tab "Comparación Temporal" o widget expandible

**Backend**: ✅ No requiere endpoints nuevos (usa GET existentes)

**Tiempo estimado**: 4-5 días

---

### 2. Exportación de Reportes

**Backend**:
- [ ] `services/report_service.py` (nuevo)
  - Función `generate_pdf_report(polygon_id, date_range)`
    - Usar librería: `reportlab` o `weasyprint`
    - Contenido: portada, metadatos parcela, mapas NDVI/segmentación/textura, estadísticos, gráfica evolución temporal
    - Formato: A4, logo UC (opcional), footer con fecha generación
  - Función `generate_csv_export(polygon_id, date_range)`
    - Columnas: date, ndvi_mean, ndvi_std, cultivated_area_ha, cloud_quality, edges_mean, homogeneity_mean, contrast_mean
    - Ordenado por fecha ascendente
- [ ] `api/endpoints/reports.py` (nuevo)
  - `GET /api/reports/pdf/{polygon_id}?start_date=X&end_date=Y`
    - Response: archivo PDF (Content-Type: application/pdf)
  - `GET /api/reports/csv/{polygon_id}?start_date=X&end_date=Y`
    - Response: archivo CSV (Content-Type: text/csv)
- [ ] Modelo `models/report.py` (opcional, solo si se cachean reportes)
  - Tabla `report_cache` con: polygon_id, start_date, end_date, format, file_path, generated_at
  - TTL: 24 horas (regenerar si hay nuevos análisis)
- [ ] Tests `tests/test_report_service.py`
  - Test generación PDF con parcela 211
  - Test generación CSV con datos de 3 fechas
  - Test validación rango fechas

**Frontend**:
- [ ] `components/molecules/ExportButtons.tsx` (nuevo)
  - Botón "Descargar PDF" → llama `/api/reports/pdf/{id}`
  - Botón "Exportar CSV" → llama `/api/reports/csv/{id}`
  - Loading state con spinner
  - Manejo de errores (sin datos, rango inválido)
- [ ] Integración en `/cultivos/[id]`
  - Colocar botones en header del dashboard o dentro de widget resumen
  - Usar rango de fechas del selector existente o permitir customización

**Dependencias nuevas**:
```bash
# Backend
pip install reportlab pillow  # Para PDF con imágenes
# o alternativamente:
pip install weasyprint  # HTML → PDF (más flexible para layouts)
```

**Tiempo estimado**: 5-6 días

---

## CRITERIOS DE COMPLETITUD

### Tests
- [ ] `pytest tests/test_report_service.py -v` pasa
- [ ] Test end-to-end: generar PDF y validar contenido (usar PyPDF2)
- [ ] Test CSV: validar columnas y formato de datos

### Docker
- [ ] `docker-compose up --build` levanta sin errores
- [ ] Endpoint `/api/reports/pdf` responde con archivo válido
- [ ] Endpoint `/api/reports/csv` responde con datos correctos

### Prueba Manual
- [ ] Abrir `/cultivos/211` en navegador
- [ ] Seleccionar 3 fechas en comparador temporal
- [ ] Verificar grid de mapas sincronizados
- [ ] Descargar PDF → abrir y validar contenido
- [ ] Exportar CSV → abrir en Excel/LibreOffice y validar datos
- [ ] Repetir en mobile (375px) y desktop (1920px)

### Documentación
- [ ] Actualizar `CLAUDE.md` líneas OE5 con checkmarks completos
- [ ] Crear `tasks/oe5_complete.md` con evidencia (screenshots, output CSV, PDF sample)
- [ ] Actualizar `tasks/lessons.md` con aprendizajes del proceso

---

## DECISIONES DE DISEÑO

### Comparación Temporal
**Opción A**: Widget separado con tab "Comparación"  
**Opción B**: Selector multi-fecha reemplaza selector single existente  
**Elegida**: **Opción A** — mantener flujo actual y agregar vista especializada

**Layout comparativo**:
- 2 fechas: grid 1x2 (horizontal)
- 3 fechas: grid 1x3 (horizontal) o 2+1 (desktop), stack vertical (mobile)
- 4 fechas: grid 2x2 (desktop), stack vertical (mobile)

**Sincronización mapas**:
- Zoom/pan sincronizado: Leaflet sync plugin o estado compartido
- Toggle análisis (NDVI/Seg/Tex) global para todas las fechas

### Exportación Reportes
**Formato PDF**:
- Librería: `reportlab` (control fino) vs `weasyprint` (HTML→PDF más fácil)
- **Elegida**: `weasyprint` — permite usar Tailwind CSS del frontend para layout consistente

**Contenido PDF**:
1. Portada: nombre parcela, coordenadas, área, rango fechas
2. Resumen: tabla con estadísticos por fecha
3. Mapas: NDVI + Segmentación + Textura (1 página por fecha)
4. Gráfica evolución temporal (exportar SVG desde Recharts)
5. Footer: "Generado por PEG UC — Sistema Agricultura Precisión"

**CSV**:
- 1 fila por fecha
- Todas las métricas numéricas (NDVI, área, textura)
- Header descriptivo en español
- Separador: coma (estándar CSV)

---

## ORDEN DE IMPLEMENTACIÓN

### Fase 1: Backend Exportación (3 días)
1. Crear `services/report_service.py` con generación CSV
2. Crear endpoint `/api/reports/csv`
3. Tests CSV
4. Agregar `weasyprint` y crear template HTML para PDF
5. Implementar `generate_pdf_report()`
6. Crear endpoint `/api/reports/pdf`
7. Tests PDF

### Fase 2: Frontend Exportación (1 día)
1. Crear `ExportButtons.tsx`
2. Integrar en dashboard `/cultivos/[id]`
3. Validar descarga en navegador

### Fase 3: Frontend Comparación Temporal (4 días)
1. Crear `hooks/useTemporalComparison.ts`
2. Crear `TemporalComparisonWidget.tsx` con grid básico
3. Integrar mapas Leaflet en cada celda
4. Implementar sincronización zoom/pan
5. Agregar toggle NDVI/Seg/Tex
6. Integrar en dashboard como nuevo tab o widget expandible
7. Validar responsive mobile/desktop

### Fase 4: Validación Final (1 día)
1. Tests completos (pytest + manual)
2. Docker validation
3. Documentar evidencia
4. Screenshots para `tasks/oe5_complete.md`
5. Actualizar CLAUDE.md
6. Merge a main y push

---

## ESTIMACIÓN TOTAL

**Tiempo**: 9-10 días  
**Complejidad**: Media (backend PDF) a Alta (sincronización mapas frontend)  
**Riesgo**: Bajo (no depende de datos externos ni ground truth)

---

## SIGUIENTE PASO

Iniciar Fase 1: Backend Exportación CSV
- Crear `backend/app/services/report_service.py`
- Función básica `generate_csv_export()` con query JOIN a todas las tablas

**Esperando confirmación para proceder.**
