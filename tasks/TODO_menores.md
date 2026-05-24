# TODO - Tareas Menores Pendientes

## 🔴 PRIORIDAD ALTA

### 1. Flash de contenido en rutas protegidas
**Problema:** Al escribir URLs directamente (/cultivos, /nueva-parcela), se muestra un flash del contenido por milisegundos antes de redirigir al login.

**Causa:** La verificación de autenticación es asíncrona y React renderiza el componente antes de completar la validación.

**Posibles soluciones a evaluar:**
- Middleware de Next.js para verificar token en servidor (más robusto)
- Cookie httpOnly en lugar de localStorage
- Suspense boundary en layout principal
- Guards de ruta en App Router

**Estado:** 🔧 Pendiente - Requiere investigación de mejores prácticas Next.js 16

---

## 🟡 MEJORAS UI/UX

### 2. Responsive design mobile
**Descripción:** Adaptar la aplicación para dispositivos móviles (375px - 768px)

**Componentes a ajustar:**
- [ ] Sidebar → Convertir a drawer inferior o hamburger menu
- [ ] SentinelPanel → Modal inferior en móvil (no lateral)
- [ ] Cultivos grid → Single column en mobile
- [ ] Map controls → Reposicionar para pantallas pequeñas
- [ ] Forms (Login/Register) → Stack vertical en mobile

**Breakpoints Tailwind a usar:**
- `sm:` 640px
- `md:` 768px  
- `lg:` 1024px
- `xl:` 1280px

**Estado:** 🔜 Siguiente tarea prioritaria

---

### 3. Validación de formularios mejorada
**Descripción:** Añadir feedback visual en tiempo real

**Formularios afectados:**
- Login: validar formato email, longitud password
- Register: coincidencia passwords, fortaleza clave
- Nueva Parcela: validar estructura GeoJSON antes de submit

**Estado:** 📋 Por hacer

---

### 4. Indicadores de carga y feedback
**Descripción:** Mejorar UX en operaciones asíncronas

**Casos:**
- Editar nombre de parcela → mostrar spinner en botón "Guardar"
- Eliminar parcela → confirmar con modal más elegante
- Crear parcela → toast notification con éxito/error

**Estado:** 📋 Por hacer

---

## 🟢 MEJORAS FUNCIONALES

### 5. Persistencia de selección de capa base
**Descripción:** Recordar la capa de mapa seleccionada (OpenStreetMap vs ESRI Imagery)

**Implementación:** localStorage + useEffect en LeafletMap

**Estado:** 📋 Por hacer

---

### 6. Información de salud real en Cultivos
**Descripción:** Reemplazar `getHealthStatus()` aleatorio con datos reales de NDVI

**Depende de:** OE2 - Servicio NDVI completado

**Estado:** ⏳ Bloqueado por OE2

---

### 7. Exportación de datos
**Descripción:** Permitir descargar parcelas en formatos GeoJSON/KML

**Casos de uso:**
- Botón "Exportar" en página Cultivos
- Descarga individual o bulk
- Incluir metadatos (área, fechas de adquisición)

**Estado:** 📋 Por hacer

---

## 🔵 CALIDAD DE CÓDIGO

### 8. Tests unitarios frontend
**Descripción:** Agregar tests para componentes críticos

**Prioridad:**
- AuthContext
- PolygonContext
- ProtectedRoute
- Utilities (coordUtils)

**Herramientas:** Jest + React Testing Library

**Estado:** 📋 Por hacer

---

### 9. Manejo de errores centralizado
**Descripción:** Error boundary de React para capturar errores no manejados

**Implementación:** Componente ErrorBoundary en layout principal

**Estado:** 📋 Por hacer

---

### 10. Optimización de imágenes
**Descripción:** Lazy loading de componentes pesados

**Candidatos:**
- Leaflet (ya implementado con dynamic)
- SentinelPanel (considerar lazy load)
- Imágenes del logo (next/image)

**Estado:** ✅ Parcialmente completo (Leaflet optimizado)

---

## 📝 DOCUMENTACIÓN

### 11. README para desarrolladores
**Descripción:** Guía de instalación y desarrollo local

**Incluir:**
- Requisitos previos
- Variables de entorno
- Comandos de desarrollo
- Estructura de carpetas
- Guía de contribución

**Estado:** 📋 Por hacer

---

### 12. Documentación de API endpoints
**Descripción:** Swagger/OpenAPI completo con ejemplos

**Estado:** ⏳ FastAPI auto-genera docs en /docs (revisar completitud)

---

## 🎨 DETALLES VISUALES

### 13. Animaciones de transición
**Descripción:** Transiciones suaves entre páginas/estados

**Implementación:** Framer Motion o Tailwind animations

**Estado:** 📋 Por hacer

---

### 14. Dark mode
**Descripción:** Tema oscuro para reducir fatiga visual

**Implementación:** next-themes + Tailwind dark: variants

**Estado:** 📋 Nice to have (baja prioridad)

---

## LEYENDA
- 🔴 **Prioridad Alta:** Afecta funcionalidad core
- 🟡 **Mejoras UX:** Mejora experiencia de usuario
- 🟢 **Funcionales:** Nuevas características
- 🔵 **Calidad:** Mantenibilidad y robustez
- ✅ **Completo**
- 🔧 **En progreso**
- 🔜 **Siguiente**
- 📋 **Por hacer**
- ⏳ **Bloqueado**
