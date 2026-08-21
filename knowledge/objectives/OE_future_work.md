# Trabajo Futuro y Limitaciones — Objetivos Específicos

**Fecha:** 2026-08-21  
**Propósito:** Documentar funcionalidades NO implementadas, limitaciones conocidas y trabajo futuro para extender el proyecto.

---

## 1. Discrepancia Título vs Implementación — IA

### Contexto

**Título del PEG:** "DESARROLLO DE UNA INTERFAZ DE USUARIO ORIENTADA A SERVICIOS DE CÁLCULO EN LA NUBE CON **MODELOS DE INTELIGENCIA ARTIFICIAL** PARA ESTUDIOS DE AGRICULTURA DE PRECISIÓN EN CULTIVOS DE ARROZ"

**Implementación actual:** Procesamiento digital de señales + heurísticas (NO modelos entrenados)

### Estado Actual

**OE2 — Índices Espectrales:**
- ✅ Cálculo NDVI mediante fórmula: `(NIR - Red) / (NIR + Red)`
- ✅ Estadísticos sobre píxeles válidos
- ❌ NO usa Random Forest ni XGBoost para clasificación

**OE3 — Segmentación:**
- ✅ Umbralización NDVI > 0.3 (heurística fija)
- ✅ Máscara binaria cultivado/no-cultivado
- ❌ NO usa U-Net ni ResUNet-a entrenados

**OE4 — Textura:**
- ✅ Filtrado convolucional (Laplacian, LocalVariance, Sobel)
- ✅ Estadísticos sobre kernels aplicados
- ❌ NO clasifica patrones con modelos supervisados

### Razón

Según protocolo de cierre acordado con tutor:
- Enfoque en **interfaz funcional** y **pipeline de datos**
- Modelos IA requerían:
  - Ground truth etiquetado (parcelas con clase conocida)
  - Entrenamiento con datasets extensos
  - Validación cruzada con datos de campo
  - Tiempo estimado: 3-4 semanas adicionales

### Recomendación para Trabajo Futuro

**Incorporar modelos entrenados en OE2/OE3/OE4:**

1. **OE2 - Clasificación estado de salud:**
   - Entrenar Random Forest con features: NDVI, EVI, SAVI, textura
   - Clases: healthy, alert, critical, pest, disease
   - Dataset: 500+ parcelas etiquetadas
   - Métrica: F1-score ≥ 0.85

2. **OE3 - Segmentación semántica:**
   - Entrenar ResUNet-a con imágenes Sentinel-2 + máscaras ground truth
   - Arquitectura: encoder-decoder con atención
   - Dataset: 200+ parcelas anotadas píxel a píxel
   - Métrica: IoU ≥ 0.80

3. **OE4 - Clasificación de patrones:**
   - Entrenar clasificador (XGBoost) sobre descriptores de textura
   - Clases: uniform, heterogeneous, stressed, mature
   - Dataset: 300+ parcelas con etiquetas agronómicas
   - Métrica: Accuracy ≥ 0.82

**Referencia:** `docs/VALIDACION_CIENTIFICA_OE3_OE4.md` — "Alcance técnico vs científico"

---

## 2. Funcionalidades Avanzadas UI (OE5)

### 2.1 Comparación Temporal Multi-Fecha

**Descripción:** Visualizar evolución de parcela comparando 2+ fechas lado a lado.

**Funcionalidad esperada:**
- Selector multi-fecha (checkboxes)
- Grid 2x2 o 3x1 con mapas sincronizados
- Gráficas comparativas (NDVI, área cultivada, textura)
- Detección automática de cambios significativos

**Estado:** ❌ NO implementado

**Razón:** Requiere diseño UX complejo + lógica frontend avanzada (sincronización estado entre widgets).

**Estimación:** 2-3 semanas (diseño + implementación + validación).

**Prioridad:** Media (útil para análisis temporal, no crítico para demo).

### 2.2 Exportación de Reportes

**Descripción:** Generar documentos PDF o CSV con análisis de parcela.

**Funcionalidad esperada:**

**PDF:**
- Portada con datos parcela (nombre, ubicación, área)
- Mapa con overlay NDVI + segmentación + textura
- Tablas de estadísticos por fecha
- Gráficas de evolución temporal
- Recomendaciones basadas en estado de salud

**CSV:**
- Tabla con columnas: fecha, NDVI_mean, NDVI_std, área_cultivada, etc.
- Una fila por fecha analizada
- Exportable a Excel para análisis externo

**Estado:** ❌ NO implementado

**Razón:** No crítico para MVP. Requiere librerías adicionales:
- Backend: `reportlab` (PDF), `pandas` (CSV)
- Frontend: botón "Exportar" + endpoint `/api/reports/{polygon_id}`

**Estimación:** 1-2 semanas

**Prioridad:** Baja (nice-to-have para producción).

---

## 3. Validación Agronómica

### 3.1 Ground Truth de Campo

**Limitación actual:** Sin datos etiquetados de parcelas reales SRRG.

**Necesidad:**
- Visitas a campo con GPS para georreferenciar parcelas
- Registro de estado real (healthy/stressed/pest/disease)
- Muestreo durante ciclo completo (siembra → cosecha)
- Correlación con imágenes satelitales de mismas fechas

**Datos a recolectar:**
- Coordenadas GPS de parcelas representativas (min 50)
- Etiquetas de estado fenológico por fecha
- Biomasa medida (kg/ha)
- Presencia de plagas/enfermedades
- Rendimiento final (kg/ha cosechados)

**Colaboración sugerida:**
- SRRG (Sistema de Riego Río Guárico)
- INIA (Instituto Nacional de Investigaciones Agrícolas)
- Productores locales en Calabozo

**Estimación:** 3-6 meses (un ciclo agrícola completo)

**Prioridad:** Alta (fundamental para validación científica)

### 3.2 Métricas de Precisión Reales

**Actual:** Métricas técnicas (IoU, F1, RMSE) sobre datos sintéticos.

**Necesario:**
- IoU segmentación vs delimitación manual en campo
- Precisión clasificación NDVI vs estado observado
- Correlación textura vs condición agronómica real

**Depende de:** Ground truth de campo (3.1)

---

## 4. Escalabilidad y Producción

### 4.1 Optimización de Performance

**Limitaciones actuales:**
- Procesamiento síncrono (bloquea request hasta terminar cálculo)
- Sin caché distribuida (Redis)
- Queries N+1 en algunos endpoints

**Mejoras sugeridas:**
- **Celery + Redis:** Procesamiento asíncrono de tareas pesadas
  - Adquisición bandas → job en background
  - Cálculo NDVI/segmentación/textura → worker pool
  - Notificaciones WebSocket cuando termina job
- **Redis caché:** Cachear resultados de STAC API (fechas disponibles)
- **Query optimization:** Eager loading con `joinedload` en SQLAlchemy

**Estimación:** 2 semanas

**Prioridad:** Media (importante para > 100 usuarios concurrentes)

### 4.2 Monitoreo y Logging

**Actual:** Logs básicos en stdout.

**Necesario para producción:**
- **Sentry:** Error tracking con stack traces
- **Prometheus + Grafana:** Métricas de API (latencia, throughput, error rate)
- **CloudWatch Logs:** Centralización de logs (si deploy en AWS)
- **Health checks:** Endpoints `/health` con checks de BD, Copernicus API

**Estimación:** 1 semana

**Prioridad:** Alta (crítico para producción)

### 4.3 CI/CD

**Actual:** Deploy manual con Docker Compose.

**Necesario:**
- **GitHub Actions:** Pipeline de CI/CD
  - Trigger: push a `main`
  - Jobs: lint, tests, build, deploy
- **Staging environment:** Ambiente de pruebas pre-producción
- **Blue-green deployment:** Deploy sin downtime

**Estimación:** 1-2 semanas

**Prioridad:** Media (mejora calidad y velocidad de releases)

---

## 5. Funcionalidades Adicionales

### 5.1 Análisis Multi-Cultivo

**Actual:** Específico para arroz.

**Extensión:** Soportar otros cultivos (maíz, sorgo, caña de azúcar).

**Cambios necesarios:**
- Ajustar umbrales NDVI por tipo de cultivo
- Entrenar modelos específicos por cultivo
- UI: selector "Tipo de cultivo" al crear parcela

**Estimación:** 3-4 semanas

**Prioridad:** Media (útil para diversificar usuarios)

### 5.2 Alertas y Notificaciones

**Descripción:** Notificar al usuario cuando se detectan anomalías.

**Funcionalidad:**
- Email/SMS cuando NDVI cae significativamente
- Alerta si segmentación muestra pérdida de área cultivada
- Notificación cuando nueva imagen está disponible

**Tecnologías:**
- Backend: Celery Beat (tareas periódicas)
- Email: AWS SES o SendGrid
- SMS: Twilio

**Estimación:** 2 semanas

**Prioridad:** Media (mejora UX para productores)

### 5.3 Integración con Estaciones Meteorológicas

**Descripción:** Combinar datos satelitales con datos climáticos locales.

**Fuentes:**
- API INIA (temperatura, precipitación, humedad)
- Estaciones IoT en parcelas

**Correlación:**
- Relacionar caídas de NDVI con sequías
- Asociar pérdidas de área con lluvias intensas

**Estimación:** 2-3 semanas

**Prioridad:** Baja (nice-to-have, no crítico)

---

## 6. Mejoras de Código

### 6.1 Refactorización OE3/OE4

**Código duplicado:** Lógica de puerta de calidad repetida en `segmentation_service.py` y `texture_service.py`.

**Solución:** Extraer a `services/quality_gate.py`:
```python
async def validate_quality_gate(
    db: AsyncSession,
    acquisition_id: int,
    require_scl: bool = True
) -> Tuple[bool, str]:
    """
    Valida puerta de calidad de adquisición.
    Returns: (is_valid, error_message)
    """
    # Lógica centralizada
```

**Estimación:** 1 día

**Prioridad:** Baja (mejora mantenibilidad, no funcional)

### 6.2 Type Hints Completos

**Actual:** Algunos endpoints sin type hints completos.

**Mejora:** Usar `mypy --strict` y corregir todos los warnings.

**Estimación:** 2-3 días

**Prioridad:** Baja (mejora calidad código)

### 6.3 Tests de Integración con APIs Reales

**Actual:** Tests con BD SQLite en memoria y mocks.

**Mejora:** Suite de tests de integración contra:
- Copernicus STAC/Process API reales (con credenciales de test)
- PostgreSQL real (test DB separada)

**Estimación:** 1 semana

**Prioridad:** Media (mejora confianza en releases)

---

## 7. Documentación Usuario Final

### 7.1 Manual de Usuario

**Contenido:**
- Guía de registro y login
- Cómo crear una parcela
- Cómo interpretar NDVI (colores, valores)
- Qué significan los overlays de segmentación y textura
- FAQ

**Formato:** Markdown + screenshots

**Estimación:** 3-4 días

**Prioridad:** Alta (necesario para entrega a usuarios reales)

### 7.2 Video Tutorial

**Contenido:**
- Screencast de 5-7 minutos mostrando flujo completo
- Narración en español
- Publicar en YouTube

**Estimación:** 2 días (grabación + edición)

**Prioridad:** Media (útil para onboarding)

---

## 8. Resumen de Prioridades

| Categoría | Item | Prioridad | Estimación |
|-----------|------|-----------|------------|
| **IA** | Entrenar modelos supervisados OE2/OE3/OE4 | 🔴 Alta | 3-4 semanas |
| **Validación** | Ground truth de campo SRRG | 🔴 Alta | 3-6 meses |
| **Producción** | Monitoreo y logging (Sentry, Grafana) | 🔴 Alta | 1 semana |
| **Documentación** | Manual de usuario | 🔴 Alta | 3-4 días |
| **UI** | Comparación multi-fecha | 🟡 Media | 2-3 semanas |
| **UI** | Exportación PDF/CSV | 🟢 Baja | 1-2 semanas |
| **Performance** | Celery + Redis (async jobs) | 🟡 Media | 2 semanas |
| **Features** | Alertas y notificaciones | 🟡 Media | 2 semanas |
| **Features** | Multi-cultivo | 🟡 Media | 3-4 semanas |
| **Code Quality** | Refactorización quality gate | 🟢 Baja | 1 día |

**Leyenda:** 🔴 Alta | 🟡 Media | 🟢 Baja

---

## 9. Roadmap Sugerido

### Fase 3 (Corto Plazo - 1-2 meses)

1. Manual de usuario
2. Monitoreo y logging (Sentry + Grafana)
3. Ground truth piloto (10-20 parcelas, ciclo actual)

### Fase 4 (Mediano Plazo - 3-6 meses)

1. Ground truth completo (50+ parcelas, ciclo completo)
2. Entrenar modelos IA (OE2/OE3/OE4)
3. Comparación multi-fecha
4. Celery + Redis (async processing)

### Fase 5 (Largo Plazo - 6-12 meses)

1. Multi-cultivo
2. Alertas y notificaciones
3. Integración estaciones meteorológicas
4. CI/CD completo

---

## 10. Contacto y Colaboraciones

**Instituciones potenciales:**
- **SRRG (Sistema de Riego Río Guárico):** Acceso a parcelas, datos históricos
- **INIA:** Expertise agronómico, protocolos de muestreo
- **Universidad de Carabobo - Centro de Procesamiento de Imágenes:** Investigación continua
- **Productores locales (Calabozo, Guárico):** Ground truth de campo, feedback usuarios reales

**Contacto autor:**
- Email: [agregar email institucional]
- GitHub: [agregar repo público]
- LinkedIn: [agregar perfil]

---

**Última actualización:** 2026-08-21  
**Autor:** Jhonattan Escorihuela & Fabiana De La Hoz  
**Tutor:** José Rafael Pacheco  
**Institución:** Universidad de Carabobo - Escuela de Telecomunicaciones
