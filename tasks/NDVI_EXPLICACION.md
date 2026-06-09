# Explicación de Estadísticos NDVI

## ¿Qué es NDVI?

NDVI (Normalized Difference Vegetation Index) mide la salud de la vegetación usando imágenes satelitales. Valores entre -1 y 1.

**Rango de valores:**
- **< 0.3**: Crítico (rojo) - Vegetación escasa, estrés severo, posible falla del cultivo
- **0.3-0.5**: Moderado (amarillo) - Vegetación moderada, revisar y monitorear
- **≥ 0.5**: Saludable (verde) - Vegetación óptima, cultivo en buen estado

---

## ¿Por qué 4 valores para una fecha?

Cuando calculas NDVI para una fecha específica, **cada píxel de la imagen satelital tiene su propio valor NDVI**.

**Ejemplo real (Parcela 2, 2026-05-18):**
- Imagen satelital: 512 × 512 píxeles = **262,144 píxeles**
- Cada píxel representa ~10m × 10m de terreno
- Cada píxel tiene su valor NDVI individual

Por eso necesitamos **estadísticos** para resumir todos esos valores:

---

## Estadísticos NDVI

### 1. **NDVI Mean (Promedio) - EL MÁS IMPORTANTE**
```
Valor promedio de NDVI de TODOS los píxeles de la parcela
```

**Qué representa:**
- Estado de salud **general** del cultivo
- Valor representativo de toda la parcela
- **Este es el que usamos para clasificar: crítico/moderado/saludable**

**Ejemplo:**
```
NDVI Mean = 0.289
→ Suma de 262,144 valores NDVI ÷ 262,144 = 0.289
→ Estado: CRÍTICO (< 0.3)
```

**Cuándo usarlo:**
- ✅ Tomar decisiones sobre toda la parcela
- ✅ Comparar diferentes fechas
- ✅ Reportar estado general del cultivo

---

### 2. **NDVI Min (Mínimo)**
```
Valor más bajo de NDVI encontrado en algún píxel de la parcela
```

**Qué representa:**
- La **zona más deteriorada** de la parcela
- Puede ser suelo desnudo, agua, área con problema

**Ejemplo:**
```
NDVI Min = 0.0
→ Hay al menos un píxel con NDVI = 0 (suelo sin vegetación)
```

**Cuándo usarlo:**
- ⚠️ Identificar zonas problemáticas específicas
- ⚠️ Detectar áreas que necesitan atención inmediata
- ⚠️ Valores cercanos a 0 o negativos → revisar en campo

**⚠️ NO usar Min para clasificar la parcela completa** (sería demasiado pesimista)

---

### 3. **NDVI Max (Máximo)**
```
Valor más alto de NDVI encontrado en algún píxel de la parcela
```

**Qué representa:**
- La **zona más saludable** de la parcela
- Potencial máximo del cultivo en condiciones óptimas

**Ejemplo:**
```
NDVI Max = 0.811
→ Hay zonas con vegetación muy saludable
```

**Cuándo usarlo:**
- ✅ Ver el potencial de la parcela
- ✅ Identificar zonas de mejor rendimiento
- ✅ Comparar con parcelas vecinas

**⚠️ NO usar Max para clasificar la parcela completa** (sería demasiado optimista)

---

### 4. **NDVI Std (Desviación Estándar)**
```
Mide qué tan diferentes son los valores NDVI entre sí
```

**Qué representa:**
- **Homogeneidad** del cultivo
- Valores bajos → parcela uniforme
- Valores altos → parcela heterogénea (zonas muy diferentes)

**Ejemplo:**
```
NDVI Std = 0.15 (bajo) → Cultivo uniforme, mismo estado en toda la parcela
NDVI Std = 0.35 (alto) → Cultivo heterogéneo, zonas muy diferentes
```

**Cuándo usarlo:**
- 🔍 Detectar variabilidad dentro de la parcela
- 🔍 Identificar necesidad de manejo diferenciado (agricultura de precisión)
- 🔍 Valores altos → investigar causas (riego desigual, plagas localizadas, suelo variable)

---

## Caso Real: Parcela 2, 18 Mayo 2026

```
NDVI Mean: 0.289  → CRÍTICO (promedio general)
NDVI Min:  0.0    → Hay zonas sin vegetación
NDVI Max:  0.811  → Pero también hay zonas saludables
NDVI Std:  0.18   → Parcela heterogénea (hay zonas muy diferentes)
```

**Interpretación:**
1. **Estado general: CRÍTICO** (mean < 0.3)
2. La parcela tiene zonas muy diferentes (std alto)
3. Hay zonas sin vegetación (min = 0) Y zonas saludables (max = 0.8)
4. **Acción recomendada:** Ir a campo, identificar qué zonas están mal y por qué

**Posibles causas de heterogeneidad:**
- Riego desigual
- Parte de la parcela tiene plaga/enfermedad
- Diferentes tipos de suelo
- Drenaje deficiente en algunas zonas

---

## Resumen: ¿Qué valor mirar?

| Pregunta | Estadístico | Razón |
|----------|-------------|-------|
| ¿Cómo está mi parcela en general? | **NDVI Mean** | Representa toda la parcela |
| ¿Tengo zonas con problema? | **NDVI Min** | Identifica peores áreas |
| ¿Cuál es mi potencial máximo? | **NDVI Max** | Muestra mejor desempeño |
| ¿Mi parcela es uniforme? | **NDVI Std** | Mide homogeneidad |

**REGLA DE ORO:**
> **Usa siempre NDVI Mean para clasificar el estado de salud general.**
> Los demás estadísticos son complementarios para entender detalles.

---

## Analogía con Examen Escolar

Imagina que la parcela es un salón de clases con 262,144 estudiantes:

- **NDVI Mean (Promedio)**: Nota promedio del salón → ¿Cómo está el grupo?
- **NDVI Min (Mínimo)**: Peor nota del salón → ¿Quién necesita más ayuda?
- **NDVI Max (Máximo)**: Mejor nota del salón → ¿Cuál es el techo del grupo?
- **NDVI Std (Desviación)**: ¿Todos tienen notas similares o hay mucha diferencia?

Si el promedio es 3.0 (crítico), pero hay alguien con 8.0 (max), significa que **el grupo en general está mal, aunque algunos estudiantes estén bien**. No clasificarías el salón como "excelente" por un solo estudiante con 8.0.

---

## Configuración Actual del Sistema

### Clasificación Unificada (Lista + Dashboard)
```
NDVI Mean < 0.3  → 🔴 CRÍTICO  (rojo)
NDVI Mean 0.3-0.5 → 🟡 MODERADO (amarillo)
NDVI Mean ≥ 0.5  → 🟢 SALUDABLE (verde)
```

### Dónde se Aplica
- ✅ Lista `/cultivos` → Badge de estado
- ✅ Dashboard `/cultivos/[id]` → "Estado Actual"
- ✅ Widget evolución temporal → Todos los puntos de la gráfica
- ✅ Clasificación de salud de parcelas

**Consistencia garantizada:** Mismo valor NDVI Mean = mismo color en toda la aplicación.
