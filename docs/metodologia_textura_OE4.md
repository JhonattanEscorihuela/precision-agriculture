# Metodología de Análisis de Textura mediante Filtrado Convolucional sobre NDVI
## Objetivo Específico 4 (OE4) - Evaluar descriptores de textura

**Proyecto:** Aplicación web de agricultura de precisión para análisis de salud de cultivos de arroz  
**Institución:** Universidad Simón Bolívar  
**Fecha:** Agosto 2026  
**Versión:** 3.0 (Final con resultados empíricos)  
**Estado:** Completo

---

## 1. Introducción

El índice de vegetación de diferencia normalizada (NDVI) es una métrica ampliamente utilizada para evaluar la salud de la vegetación mediante el contraste entre las bandas del espectro visible e infrarrojo cercano (Rouse et al., 1974). Sin embargo, el uso exclusivo de estadísticos globales como la media del NDVI presenta limitaciones importantes en la caracterización espacial de cultivos.

Dos parcelas pueden exhibir valores medios de NDVI idénticos pero presentar patrones espaciales radicalmente diferentes: una parcela puede mostrar vegetación uniforme y homogénea, mientras que otra puede presentar alta variabilidad espacial con zonas de estrés hídrico, plagas, o crecimiento irregular (Haralick et al., 1973). Esta variabilidad intra-parcela no es capturada por estadísticos de primer orden (media, desviación estándar), requiriendo análisis de características de segundo orden que consideren las relaciones espaciales entre píxeles vecinos.

El análisis de textura mediante filtrado convolucional permite evaluar la **organización espacial** de los valores de NDVI, identificando patrones como:

- **Homogeneidad:** Bajo contraste entre píxeles vecinos, indicativo de desarrollo uniforme del cultivo.
- **Bordes y transiciones abruptas:** Cambios bruscos en el NDVI que pueden señalar estrés localizado, deficiencias nutricionales, o variabilidad edáfica.
- **Contraste:** Magnitud de las diferencias locales, relacionada con la heterogeneidad estructural del dosel vegetal.

Este estudio propone evaluar descriptores de textura mediante tres operadores convolucionales aplicados sobre el raster NDVI de zonas previamente segmentadas como cultivadas, contribuyendo a un análisis multidimensional de la salud vegetal que complementa las métricas espectrales tradicionales.

---

## 2. Fundamento Teórico: Convolución Discreta 2D

### 2.1 Definición

La **convolución discreta bidimensional** es una operación matemática que aplica un kernel (matriz de coeficientes) sobre una imagen, produciendo una transformación local basada en el vecindario de cada píxel. Formalmente, la convolución de una imagen $I(x, y)$ con un kernel $K$ de dimensiones $(2m+1) \times (2n+1)$ se define como:

$$
(I * K)(x, y) = \sum_{i=-m}^{m} \sum_{j=-n}^{n} I(x-i, y-j) \cdot K(i, j)
$$

Donde:
- $I(x, y)$: Valor del píxel en la posición $(x, y)$ de la imagen original
- $K(i, j)$: Coeficiente del kernel en la posición $(i, j)$
- $(I * K)(x, y)$: Valor resultante en la imagen convolucionada

La convolución realiza una suma ponderada del vecindario de cada píxel, donde los pesos están definidos por el kernel. La elección del kernel determina la naturaleza de la transformación: detección de bordes, suavizado, realce de contraste, entre otras (Gonzalez & Woods, 2018).

### 2.2 Ejemplo Numérico: Operador Laplaciano

El **operador Laplaciano** es un filtro de detección de bordes que calcula la segunda derivada discreta de la imagen, resaltando regiones con cambios bruscos de intensidad. El kernel Laplaciano estándar (sin componentes diagonales) es:

$$
K_{Laplaciano} = \begin{bmatrix}
0 & 1 & 0 \\
1 & -4 & 1 \\
0 & 1 & 0
\end{bmatrix}
$$

**Caso 1: Zona homogénea (sin transición)**

Considérese una región de NDVI uniforme con valor 0.7:

$$
I = \begin{bmatrix}
0.7 & 0.7 & 0.7 \\
0.7 & 0.7 & 0.7 \\
0.7 & 0.7 & 0.7
\end{bmatrix}
$$

Aplicando la convolución en el píxel central:

$$
\begin{align}
(I * K)(x, y) &= 0 \cdot 0.7 + 1 \cdot 0.7 + 0 \cdot 0.7 \\
              &\quad + 1 \cdot 0.7 + (-4) \cdot 0.7 + 1 \cdot 0.7 \\
              &\quad + 0 \cdot 0.7 + 1 \cdot 0.7 + 0 \cdot 0.7 \\
              &= 0.7 + 0.7 - 2.8 + 0.7 + 0.7 \\
              &= \mathbf{0.0}
\end{align}
$$

**Resultado:** En zonas homogéneas, el Laplaciano retorna **cero**, indicando ausencia de variación espacial.

**Caso 2: Transición brusca (borde)**

Considérese una transición entre vegetación sana (NDVI = 0.7) y suelo desnudo o vegetación estresada (NDVI = 0.2):

$$
I = \begin{bmatrix}
0.7 & 0.7 & 0.7 \\
0.7 & 0.7 & 0.2 \\
0.7 & 0.2 & 0.2
\end{bmatrix}
$$

Aplicando la convolución en el píxel central:

$$
\begin{align}
(I * K)(x, y) &= 0 \cdot 0.7 + 1 \cdot 0.7 + 0 \cdot 0.7 \\
              &\quad + 1 \cdot 0.7 + (-4) \cdot 0.7 + 1 \cdot 0.2 \\
              &\quad + 0 \cdot 0.7 + 1 \cdot 0.2 + 0 \cdot 0.2 \\
              &= 0.7 + 0.7 - 2.8 + 0.2 + 0.2 \\
              &= \mathbf{-1.0}
\end{align}
$$

**Resultado:** En bordes o transiciones, el Laplaciano retorna un **valor no nulo** (positivo o negativo), cuya magnitud es proporcional a la intensidad del cambio espacial.

Este comportamiento permite cuantificar la presencia de estructuras locales en el NDVI, distinguiendo entre zonas uniformes (respuesta cercana a cero) y zonas con variabilidad espacial significativa (respuesta de alta magnitud).

---

## 3. Operadores Convolucionales Utilizados

Se emplean tres operadores convolucionales con propósitos complementarios, aplicados sobre el raster NDVI de zonas cultivadas previamente segmentadas (OE3):

### 3.1 Operador de Detección de Bordes: Laplaciano

**Kernel:**

$$
K_{edges} = \begin{bmatrix}
0 & 1 & 0 \\
1 & -4 & 1 \\
0 & 1 & 0
\end{bmatrix}
$$

**Función:** Detecta transiciones abruptas en el NDVI mediante el cálculo de la segunda derivada discreta. Valores elevados de la respuesta indican bordes o discontinuidades espaciales, asociadas a:
- Estrés hídrico localizado
- Variabilidad en densidad de siembra
- Presencia de malezas o áreas sin cobertura vegetal
- Heterogeneidad edáfica

**Referencia:** Marr & Hildreth (1980) formalizaron el uso del Laplaciano como operador fundamental en la teoría de detección de bordes, demostrando su optimalidad bajo criterios de localización y respuesta única.

### 3.2 Operador de Homogeneidad: Varianza Local

**Función:** Cuantifica la **heterogeneidad espacial** del NDVI mediante el cálculo de la varianza en un vecindario 3×3. Este descriptor captura la dispersión de valores dentro de cada ventana local.

**Fórmula de cálculo:**

La varianza local se calcula mediante dos convoluciones:

$$
\text{Var}_{local}(x, y) = \mathbb{E}[I^2] - (\mathbb{E}[I])^2
$$

Donde:
- $\mathbb{E}[I] = I * K_{media}$: Media local del NDVI
- $\mathbb{E}[I^2] = I^2 * K_{media}$: Media local del NDVI al cuadrado

**Kernels utilizados:**

$$
K_{media} = \frac{1}{9} \begin{bmatrix}
1 & 1 & 1 \\
1 & 1 & 1 \\
1 & 1 & 1
\end{bmatrix}
$$

**Implementación:**

```python
# Paso 1: Elevar NDVI al cuadrado
ndvi_squared = ndvi_array ** 2

# Paso 2: Calcular media local de NDVI
mean_ndvi = convolve(ndvi_array, kernel_media)

# Paso 3: Calcular media local de NDVI²
mean_ndvi_squared = convolve(ndvi_squared, kernel_media)

# Paso 4: Varianza local
variance_local = mean_ndvi_squared - (mean_ndvi ** 2)
```

**Ejemplo numérico: Patrón ajedrez vs zona lisa**

**Caso A: Zona heterogénea (patrón ajedrez)**

Considérese una región con alternancia espacial entre vegetación densa (NDVI = 0.7) y estrés hídrico (NDVI = 0.4):

$$
I_{ajedrez} = \begin{bmatrix}
0.7 & 0.4 & 0.7 \\
0.4 & 0.7 & 0.4 \\
0.7 & 0.4 & 0.7
\end{bmatrix}
$$

**Cálculo paso a paso:**

1. Media local:
$$
\mathbb{E}[I] = \frac{1}{9}(0.7 + 0.4 + 0.7 + 0.4 + 0.7 + 0.4 + 0.7 + 0.4 + 0.7) = \frac{5.1}{9} = \mathbf{0.567}
$$

2. NDVI al cuadrado:
$$
I^2 = \begin{bmatrix}
0.49 & 0.16 & 0.49 \\
0.16 & 0.49 & 0.16 \\
0.49 & 0.16 & 0.49
\end{bmatrix}
$$

3. Media de NDVI²:
$$
\mathbb{E}[I^2] = \frac{1}{9}(0.49 + 0.16 + 0.49 + 0.16 + 0.49 + 0.16 + 0.49 + 0.16 + 0.49) = \frac{3.09}{9} = \mathbf{0.343}
$$

4. Varianza local:
$$
\text{Var}_{local} = 0.343 - (0.567)^2 = 0.343 - 0.321 = \mathbf{0.022}
$$

**Caso B: Zona homogénea (lisa)**

Región con vegetación uniforme (NDVI = 0.7):

$$
I_{lisa} = \begin{bmatrix}
0.7 & 0.7 & 0.7 \\
0.7 & 0.7 & 0.7 \\
0.7 & 0.7 & 0.7
\end{bmatrix}
$$

**Cálculo:**

1. Media local: $\mathbb{E}[I] = 0.7$
2. Media de NDVI²: $\mathbb{E}[I^2] = 0.49$
3. Varianza local:
$$
\text{Var}_{local} = 0.49 - (0.7)^2 = 0.49 - 0.49 = \mathbf{0.0}
$$

**Conclusión:** La varianza local distingue correctamente:
- **Alta varianza (0.022):** Patrón heterogéneo (ajedrez)
- **Baja varianza (0.0):** Zona homogénea (lisa)

**Por qué NO usar el filtro de media directamente:**

Si se aplicara el filtro de media sobre el patrón ajedrez:

$$
\text{Media}_{ajedrez} = 0.544 \approx 0.55
$$

La imagen resultante sería **uniforme** con valor ~0.55 en toda la región, **eliminando** precisamente la heterogeneidad que queremos detectar. El filtro de media **suaviza** la imagen, haciendo que zonas heterogéneas y homogéneas se vean indistinguibles tras la convolución (ambas producen respuestas de baja desviación estándar).

En contraste, la **varianza local captura la dispersión antes del suavizado**, preservando la información de heterogeneidad espacial.

**Referencia:** Haralick et al. (1973) demuestran que descriptores de segundo orden como la varianza local son necesarios para caracterizar textura, superando las limitaciones de estadísticos globales de primer orden. Gonzalez & Woods (2018, Cap. 11) formalizan el cálculo de varianza local como métrica fundamental en análisis de textura.

### 3.3 Operador de Contraste: Magnitud del Gradiente

**Función:** Cuantifica la **magnitud del cambio espacial** del NDVI en todas las direcciones, calculando el gradiente bidimensional y su norma euclidiana. Este descriptor mide el contraste local, relacionado con:
- Variabilidad microclimática (sombreado, exposición)
- Patrones de riego irregular
- Gradientes de fertilización
- Transiciones entre zonas de diferente vigor vegetativo

**Operadores de Sobel para componentes Gx y Gy:**

$$
G_x = \begin{bmatrix}
-1 & 0 & 1 \\
-2 & 0 & 2 \\
-1 & 0 & 1
\end{bmatrix}
\qquad
G_y = \begin{bmatrix}
-1 & -2 & -1 \\
0 & 0 & 0 \\
1 & 2 & 1
\end{bmatrix}
$$

**Cálculo de la magnitud:**

1. Convolucionar imagen con $G_x$ y $G_y$ para obtener gradientes direccionales
2. Calcular magnitud del gradiente (norma euclidiana):

$$
G(x, y) = \sqrt{[I * G_x]^2 + [I * G_y]^2}
$$

**Implementación:**

```python
# Paso 1: Calcular componentes del gradiente
gradient_x = convolve(ndvi_array, kernel_gx)
gradient_y = convolve(ndvi_array, kernel_gy)

# Paso 2: Magnitud del gradiente
gradient_magnitude = np.sqrt(gradient_x**2 + gradient_y**2)
```

**Ejemplo numérico: Gradiente horizontal vs magnitud total**

Considérese una transición diagonal de NDVI (vegetación sana → estresada):

$$
I = \begin{bmatrix}
0.8 & 0.7 & 0.6 \\
0.7 & 0.6 & 0.5 \\
0.6 & 0.5 & 0.4
\end{bmatrix}
$$

**Cálculo de Gx (componente horizontal):**

$$
\begin{align}
(I * G_x)(x, y) &= -1 \cdot 0.8 + 0 \cdot 0.7 + 1 \cdot 0.6 \\
                &\quad + (-2) \cdot 0.7 + 0 \cdot 0.6 + 2 \cdot 0.5 \\
                &\quad + (-1) \cdot 0.6 + 0 \cdot 0.5 + 1 \cdot 0.4 \\
                &= -0.8 + 0.6 - 1.4 + 1.0 - 0.6 + 0.4 \\
                &= \mathbf{-0.8}
\end{align}
$$

**Cálculo de Gy (componente vertical):**

$$
\begin{align}
(I * G_y)(x, y) &= -1 \cdot 0.8 + (-2) \cdot 0.7 + (-1) \cdot 0.6 \\
                &\quad + 0 \cdot 0.7 + 0 \cdot 0.6 + 0 \cdot 0.5 \\
                &\quad + 1 \cdot 0.6 + 2 \cdot 0.5 + 1 \cdot 0.4 \\
                &= -0.8 - 1.4 - 0.6 + 0.6 + 1.0 + 0.4 \\
                &= \mathbf{-0.8}
\end{align}
$$

**Magnitud del gradiente:**

$$
G = \sqrt{(-0.8)^2 + (-0.8)^2} = \sqrt{0.64 + 0.64} = \sqrt{1.28} = \mathbf{1.13}
$$

**Por qué usar magnitud y NO solo Gx:**

**Problema de anisotropía:** El operador $G_x$ únicamente detecta cambios en dirección horizontal (Este-Oeste). Si la transición ocurre en otra orientación, la respuesta será subóptima o nula.

**Experimento: Rotación de la transición**

Transición **vertical** (Norte-Sur):

$$
I_{vertical} = \begin{bmatrix}
0.8 & 0.6 & 0.4 \\
0.8 & 0.6 & 0.4 \\
0.8 & 0.6 & 0.4
\end{bmatrix}
$$

- **Gradiente horizontal ($G_x$):** Detecta perfectamente la transición → respuesta alta
- **Si solo usáramos $G_y$:** No detecta nada (transición perpendicular) → respuesta nula

Transición **horizontal** (Este-Oeste):

$$
I_{horizontal} = \begin{bmatrix}
0.8 & 0.8 & 0.8 \\
0.6 & 0.6 & 0.6 \\
0.4 & 0.4 & 0.4
\end{bmatrix}
$$

- **Gradiente horizontal ($G_x$):** No detecta nada → respuesta nula
- **Gradiente vertical ($G_y$):** Detecta perfectamente la transición → respuesta alta

**Conclusión: La magnitud $G = \sqrt{G_x^2 + G_y^2}$ es rotationally invariant (invariante rotacional)**, detectando transiciones en **cualquier orientación** con magnitud proporcional a la intensidad del cambio, sin sesgos direccionales.

En parcelas agrícolas reales, los patrones de estrés pueden ocurrir en cualquier dirección (gradientes de suelo, sombreado, drenaje). Usar únicamente $G_x$ introduciría un sesgo metodológico indefendible, donde la detectabilidad de un patrón dependería de su orientación espacial.

**Referencia:** Sobel & Feldman (1968) propusieron el operador de gradiente **isotrópico** 3×3, enfatizando la necesidad de combinar ambas direcciones para lograr invariancia rotacional. Marr & Hildreth (1980) formalizan la isotropía como propiedad fundamental de operadores de detección de bordes robustos. Haralick et al. (1973) establecen la magnitud del gradiente como descriptor estándar de textura direccional.

---

## 4. Diseño Experimental

### 4.1 Preprocesamiento: Selección del Dominio de Aplicación

**Decisión metodológica crítica:** La convolución se aplica sobre el **raster NDVI completo**, no sobre la máscara binaria de segmentación.

**Justificación:**

1. **Preservación de información espectral:** La máscara binaria (valores 0 y 1) elimina toda la información cuantitativa del NDVI. Convolucionar la máscara solo capturaría geometría de la región cultivada, no propiedades de la vegetación.

2. **Detección de variabilidad intra-parcela:** El objetivo de OE4 es caracterizar la **heterogeneidad espacial** del NDVI dentro de la zona cultivada. Esto requiere operar sobre los valores continuos del NDVI, no sobre una representación binaria.

3. **Consistencia con literatura:** Los trabajos de referencia en análisis de textura aplicada a índices de vegetación (e.g., Haralick et al., 1973; Gonzalez & Woods, 2018) operan sobre imágenes en escala de grises o valores radiométricos continuos, no sobre máscaras binarias.

**Flujo de procesamiento:**

```
1. Raster NDVI (float32, rango [-1, 1])
2. Máscara cultivada (bool, de OE3)
3. Convolución sobre NDVI completo (preserva valores continuos)
4. Extracción de respuestas solo dentro de máscara cultivada
5. Cálculo de estadísticos (mean, std, min, max) sobre respuestas extraídas
```

### 4.2 Manejo de Bordes de Máscara

**Problema:** Al aplicar convolución cerca del borde de la zona cultivada, el kernel 3×3 puede incluir píxeles fuera de la máscara (vegetación no cultivada, suelo desnudo, cuerpos de agua). Esto introduce **bordes artificiales** que contaminan los descriptores.

**Estrategia propuesta: Erosión morfológica de la máscara**

1. **Erosión de 1 píxel:** Se aplica una operación de erosión morfológica sobre la máscara binaria cultivada, reduciendo su extensión en 1 píxel desde todos los bordes.

2. **Extracción de respuestas:** Los descriptores se calculan únicamente sobre píxeles que pertenecen a la **máscara erosionada**, garantizando que todo el vecindario 3×3 esté completamente dentro de la zona cultivada original.

**Justificación:**

- **Evita contaminación por bordes:** Elimina píxeles cuyo vecindario incluye elementos externos a la parcela.
- **Preserva representatividad:** La pérdida de 1 píxel perimetral es despreciable en parcelas agrícolas (típicamente >10,000 píxeles), manteniendo >95% del área original.
- **Consistencia con literatura:** Técnica estándar en procesamiento de imágenes para evitar efectos de borde (Gonzalez & Woods, 2018, Cap. 9).

**Implementación técnica:**

```python
from scipy.ndimage import binary_erosion

# Erosión de 1 píxel (estructura 3×3)
estructura = np.ones((3, 3), dtype=bool)
mascara_erosionada = binary_erosion(mascara_cultivada, structure=estructura)

# Extracción de respuestas solo en zona segura
respuestas_validas = respuesta_convolucion[mascara_erosionada]
```

### 4.3 Criterio de Descriptor Discriminativo con Normalización

Un descriptor de textura es considerado **discriminativo** si presenta suficiente variabilidad espacial para diferenciar entre regiones o detectar patrones. Descriptores con respuesta constante o casi constante no aportan información útil para caracterización.

**Problema: Incomparabilidad de escalas entre kernels**

Los tres operadores convolucionales producen respuestas en **rangos completamente diferentes**:

| Operador | Rango típico de respuesta | Ejemplo std real |
|----------|---------------------------|------------------|
| Laplaciano | [-4, 4] | std ≈ 0.8 |
| Varianza local | [0, 0.5] | std ≈ 0.03 |
| Gradiente (magnitud) | [0, 5.7] | std ≈ 1.2 |

**Ejemplo numérico del problema:**

Supongamos un umbral absoluto $\tau = 0.05$:

1. **Laplaciano:** std = 0.8 → $0.8 > 0.05$ → **discriminativo** ✅
2. **Varianza local:** std = 0.03 → $0.03 \not> 0.05$ → **no discriminativo** ❌
3. **Gradiente:** std = 1.2 → $1.2 > 0.05$ → **discriminativo** ✅

**Problema:** La varianza local es rechazada **no porque tenga poca variabilidad relativa a su escala**, sino porque su escala absoluta es menor. Un descriptor podría tener alta heterogeneidad en su propio rango pero ser descartado injustamente por un umbral inadecuado.

**Solución: Normalización min-max antes de calcular desviación estándar**

**Paso 1: Normalizar respuestas al rango [0, 1]**

Para cada descriptor, transformar las respuestas del kernel:

$$
R_{norm}(x, y) = \frac{R(x, y) - R_{min}}{R_{max} - R_{min}}
$$

Donde:
- $R(x, y)$: Respuesta original del kernel en píxel $(x, y)$
- $R_{min}, R_{max}$: Valores mínimo y máximo sobre toda la zona cultivada
- $R_{norm}(x, y)$: Respuesta normalizada en $[0, 1]$

**Paso 2: Calcular desviación estándar normalizada**

$$
\sigma_{norm} = \text{std}(R_{norm})
$$

**Paso 3: Aplicar umbral sobre desviación normalizada**

$$
\text{Discriminativo} \iff \sigma_{norm} > \tau_{norm}
$$

**Definición del umbral normalizado:**

Se propone $\tau_{norm} = 0.10$, justificado por:

1. **Interpretación intuitiva:** Una std de 0.10 en escala [0, 1] significa que los valores típicos se dispersan ±10% del rango total, indicando variabilidad significativa.

2. **Independencia de escala:** El criterio es ahora **justo** entre kernels: cada operador se evalúa según su propia variabilidad relativa, no su magnitud absoluta.

3. **Separación de casos triviales:** Respuestas casi constantes (e.g., zona completamente homogénea) tendrán $\sigma_{norm} \approx 0$, independientemente del kernel.

**Ejemplo comparativo:**

Supongamos las mismas respuestas anteriores, ahora normalizadas:

| Operador | Respuesta original | Min | Max | Rango | std original | std normalizada |
|----------|-------------------|-----|-----|-------|--------------|-----------------|
| Laplaciano | [-2.0, 2.0] | -2.0 | 2.0 | 4.0 | 0.8 | **0.20** |
| Varianza local | [0, 0.10] | 0 | 0.10 | 0.10 | 0.03 | **0.30** |
| Gradiente | [0, 4.0] | 0 | 4.0 | 4.0 | 1.2 | **0.30** |

Con umbral $\tau_{norm} = 0.10$:

1. **Laplaciano:** $0.20 > 0.10$ → **discriminativo** ✅
2. **Varianza local:** $0.30 > 0.10$ → **discriminativo** ✅ (corregido)
3. **Gradiente:** $0.30 > 0.10$ → **discriminativo** ✅

**Conclusión:** La normalización permite que descriptores con rangos inherentemente pequeños (como la varianza local) sean evaluados justamente según su variabilidad relativa, eliminando el sesgo de escala.

**Implementación:**

```python
# Normalizar respuestas al rango [0, 1]
r_min = responses.min()
r_max = responses.max()
responses_norm = (responses - r_min) / (r_max - r_min) if r_max > r_min else np.zeros_like(responses)

# Calcular std sobre respuestas normalizadas
std_norm = responses_norm.std()

# Criterio discriminativo
is_discriminative = std_norm > 0.10
```

**Interpretación final:**

- **std_norm > 0.10 (discriminativo):** El descriptor captura variabilidad espacial significativa **dentro de su propia escala**, útil para caracterización.
- **std_norm ≤ 0.10 (no discriminativo):** Respuesta casi constante en términos relativos, no aporta información espacial relevante (puede descartarse en análisis posterior).

**Caveat: Sensibilidad a outliers**

La normalización min-max es sensible a valores extremos (outliers): un píxel anómalo con respuesta muy alta o muy baja infla artificialmente el rango $[R_{min}, R_{max}]$, comprimiendo el resto de valores normalizados hacia un rango estrecho y reduciendo la desviación estándar normalizada. En datos con outliers severos (e.g., errores de calibración radiométrica, artefactos de procesamiento), podría considerarse normalización por percentiles (e.g., rango entre percentil 5 y 95) para mayor robustez, a costa de complejidad metodológica.

Para este estudio, se asume que el preprocesamiento de NDVI (máscara de píxeles válidos, filtrado de nodata) ha eliminado outliers significativos, justificando el uso de normalización min-max estándar.

**Referencia:** La normalización min-max es práctica estándar en análisis multivariado cuando se comparan variables con diferentes unidades o escalas (Jain & Dubes, 1988). En procesamiento de imágenes, Gonzalez & Woods (2018, Cap. 3) formalizan la necesidad de normalización para comparar respuestas de filtros heterogéneos.

---

## 5. Resultados

El análisis de textura se ejecutó sobre 3 parcelas del Sistema de Riego Río Guárico (SRRG), Calabozo, Venezuela, procesando 16 fechas de adquisición por parcela (febrero–julio 2026). Total: 48 observaciones parcela-fecha, 144 descriptores de textura calculados.

### 5.1 Resultados Agregados por Parcela

| Parcela | Polygon ID | Fechas | edges mean | edges disc | homog. mean | homog. disc | contrast mean | contrast disc | Ganador |
|---------|------------|--------|------------|------------|-------------|-------------|---------------|---------------|---------|
| 211     | 1          | 16     | 0.048      | 0/16       | 0.051       | 0/16        | **0.100**     | 7/16          | contrast |
| 217     | 2          | 16     | 0.038      | 0/16       | 0.050       | 0/16        | **0.093**     | 7/16          | contrast |
| 85      | 3          | 16     | 0.053      | 0/16       | 0.076       | 2/16        | **0.130**     | 16/16         | contrast |

**Nota:** "mean" = mean_std_normalized; "disc" = fechas donde std_normalized > τ (discriminativo); τ = 0.10.

### 5.2 Promedios Globales (N=48 observaciones)

| Descriptor   | Mean std_normalized | Fechas discriminativas | % discriminativo |
|--------------|---------------------|------------------------|------------------|
| edges        | 0.047               | 0/48                   | 0.0%             |
| homogeneity  | 0.059               | 2/48                   | 4.2%             |
| **contrast** | **0.108**           | **30/48**              | **62.5%**        |

**Ratios de discriminación:**
- Contrast vs edges: 2.3× superior (0.108 / 0.047)
- Contrast vs homogeneity: 1.8× superior (0.108 / 0.059)

### 5.3 Ranking de Descriptores

El descriptor **contrast** (magnitud de gradiente de Sobel) ocupó el primer lugar del ranking en:

- **100% de las parcelas** (3/3)
- **100% de las fechas** (48/48 observaciones)

El ranking `contrast > homogeneity > edges` se mantuvo consistente independientemente de:
- La parcela analizada
- La fecha de adquisición
- El nivel de NDVI medio del cultivo

### 5.4 Validación del Umbral Discriminativo

El umbral teórico τ = 0.10 se validó empíricamente:

| Descriptor   | Cruces de τ | Interpretación |
|--------------|-------------|----------------|
| edges        | 0/48        | Nunca discriminativo — correctamente descartado |
| homogeneity  | 2/48        | Marginalmente discriminativo (solo en parcela 85) |
| contrast     | 30/48       | Consistentemente discriminativo |

El umbral τ = 0.10 separa efectivamente los descriptores: edges y homogeneity permanecen por debajo en la gran mayoría de casos, mientras que contrast lo supera en el 62.5% de las observaciones.

### 5.5 Caracterización de Parcelas por Textura

La heterogeneidad espacial varía entre parcelas:

| Parcela | Contrast mean | Interpretación |
|---------|---------------|----------------|
| 85      | 0.130         | Alta heterogeneidad (discriminativo 16/16 fechas) |
| 211     | 0.100         | Heterogeneidad moderada |
| 217     | 0.093         | Menor heterogeneidad relativa |

La parcela 85 presenta consistentemente mayor variabilidad espacial interna, posiblemente asociada a factores edáficos o de manejo de riego diferencial.

---

## 6. Conclusión

### 6.1 Respuesta al Objetivo Específico 4

**Pregunta:** ¿Cuál descriptor de textura basado en filtrado convolucional es más discriminativo para caracterizar la heterogeneidad espacial del NDVI en cultivos de arroz?

**Respuesta empírica:** El descriptor de **contraste**, implementado mediante la magnitud del gradiente de Sobel (operador isotrópico), es consistentemente el más discriminativo.

### 6.2 Evidencia Cuantitativa

1. **Superioridad estadística:** El contrast presentó un mean_std_normalized de 0.108, superando en 2.3× a edges (0.047) y en 1.8× a homogeneity (0.059).

2. **Consistencia del ranking:** El ordenamiento `contrast > homogeneity > edges` se mantuvo en el 100% de las 48 observaciones parcela-fecha analizadas.

3. **Capacidad discriminativa:** Contrast cruzó el umbral τ=0.10 en el 62.5% de los casos, mientras edges nunca lo cruzó (0%) y homogeneity solo marginalmente (4.2%).

4. **Robustez temporal:** El resultado es independiente de la fecha de adquisición, manteniéndose consistente a lo largo de 5 meses de monitoreo.

5. **Robustez espacial:** El resultado se replica en las 3 parcelas analizadas, con características edáficas y de manejo potencialmente distintas.

### 6.3 Interpretación Agronómica

El descriptor de contraste captura transiciones graduales en el vigor vegetativo, detectando:
- Gradientes de estrés hídrico
- Variabilidad en densidad de cobertura
- Heterogeneidad microclimática (sombreado, exposición)

A diferencia del Laplaciano (edges), que solo responde a discontinuidades abruptas, la magnitud del gradiente es sensible a variaciones suaves que caracterizan la transición entre zonas sanas y estresadas del cultivo.

### 6.4 Recomendación

Para aplicaciones de monitoreo de cultivos de arroz mediante teledetección, se recomienda utilizar el **descriptor de contraste (magnitud del gradiente de Sobel)** como métrica principal de heterogeneidad textural, complementando los indicadores espectrales tradicionales (NDVI medio) con información sobre la organización espacial del dosel vegetal.

---

## 7. Referencias

Gonzalez, R. C., & Woods, R. E. (2018). *Digital image processing* (4th ed.). Pearson Education.

Haralick, R. M., Shanmugam, K., & Dinstein, I. (1973). Textural features for image classification. *IEEE Transactions on Systems, Man, and Cybernetics*, *SMC-3*(6), 610-621. https://doi.org/10.1109/TSMC.1973.4309314

Jain, A. K., & Dubes, R. C. (1988). *Algorithms for clustering data*. Prentice-Hall.

Marr, D., & Hildreth, E. (1980). Theory of edge detection. *Proceedings of the Royal Society of London. Series B. Biological Sciences*, *207*(1167), 187-217. https://doi.org/10.1098/rspb.1980.0020

Rouse, J. W., Haas, R. H., Schell, J. A., & Deering, D. W. (1974). Monitoring vegetation systems in the Great Plains with ERTS. In *Third Earth Resources Technology Satellite-1 Symposium* (Vol. 1, pp. 309-317). NASA SP-351.

Sobel, I., & Feldman, G. (1968). *A 3×3 isotropic gradient operator for image processing*. Presentado en Stanford Artificial Intelligence Project (SAIL). [Nota: Este trabajo seminal fue presentado en un contexto académico interno; se cita ampliamente pero no tiene publicación formal indexada].

---

## Notas Metodológicas Adicionales

### A.1 Validación de Implementación

La implementación del servicio `texture_service.py` fue validada mediante:

1. **Test sintético:** ✅ Imagen NDVI artificial con zona homogénea (respuesta Laplaciano ≈ 0) y zona con transición (respuesta no nula).
2. **Verificación dimensional:** ✅ Erosión reduce correctamente la máscara sin eliminarla por completo (área residual >95%).
3. **Comprobación de rango:** ✅ Respuestas del Laplaciano en rango esperado (~[-4, 4] para NDVI en [0, 1]).
4. **Ejecución sobre datos reales:** ✅ 48 observaciones parcela-fecha procesadas exitosamente.

### A.2 Limitaciones del Estudio

- **Resolución espacial:** Sentinel-2 tiene resolución de 10m/píxel (bandas B04/B08). Patrones de textura menores a 30m pueden no ser detectables.
- **Ventana de análisis:** Se utiliza kernel 3×3 (30m × 30m), apropiado para parcelas >1 hectárea. Parcelas pequeñas pueden no tener suficientes píxeles tras erosión.
- **Cobertura temporal:** Estudio limitado a 5 meses (febrero–julio 2026) en zona tropical. Generalización a otras regiones climáticas requiere validación adicional.

---

**Documento final con resultados empíricos completos.**  
**Versión:** 3.0  
**Estado:** Completo
