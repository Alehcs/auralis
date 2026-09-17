# FASE V3.2-C — experimentos controlados y comprobaciones de aprendizaje

Cierre UTC: 2026-09-14T18:05:25.053415+00:00. V3.1 permanece activa. Tres entrenamientos seed42 desde cero, sin promoción.

**Resultado principal:** C1 (backbone0, cabeza0.3) obtiene el menor MAE y es la única configuración que supera la mejora mínima y todas las guardas predictivas preliminares de B en seed42. C0 y C2 mejoran globalmente, pero incumplen guardas en la banda baja. Costos, paridad ONNX/HTTP y estabilidad entre semillas siguen pendientes. La auditoría XAI deja dudas concretas sobre borde y fondo; no demuestra razonamiento físico.

## Resultado determinista sobre las mismas 263 observaciones

CPU float32 batch1, cuatro hilos intra-op/uno inter-op, eval, sin aumentaciones. Métricas float64 recalculadas desde CSV guardados. Unidades MAE/RMSE/sesgo/p95: puntos porcentuales SI; MAPE: porcentaje.


| Referencia/candidato | Época | MAE | RMSE | R² | MAPE % | Sesgo | p95 error absoluto |
|---|---|---|---|---|---|---|---|
| constant | train mean | 0.304404 | 0.349620 | -0.001348 | 17.887177 | 0.012828 | 0.591570 |
| initial | inicial | 1.726987 | 1.761651 | -24.423267 | 98.331392 | -1.726987 | 2.328941 |
| V3.1 | 40 (selección MC) | 0.204083 | 0.258233 | 0.453720 | 10.497507 | -0.186877 | 0.487845 |
| C0 | 6 | 0.157275 | 0.200928 | 0.669270 | 8.234291 | -0.129664 | 0.395529 |
| C1 | 27 | 0.048335 | 0.059056 | 0.971429 | 2.908951 | 0.013242 | 0.109745 |
| C2 | 14 | 0.093997 | 0.116039 | 0.889694 | 5.548944 | -0.006168 | 0.222232 |

La referencia histórica V3.1 se vuelve a evaluar en PyTorch CPU bajo estas mismas condiciones. El servicio usa ONNX; el resultado ONNX congelado de B es MAE 0.20408340. La precisión MC histórica (MAE 0.10155762; MPS batch32 T20, selección de época por MC) es contexto adicional, NO una fila comparable al protocolo determinista actual. No se repitió MC ni se usó para elegir época.

## Controles, dispersión y train/validation comparables

| Modelo | MAE train eval | MAE validation eval | SD pred val | SD target val | Ratio SD | Correlación val | Rango pred val |
|---|---|---|---|---|---|---|---|
| constant | 0.292543 | 0.304404 | 0.000000 | 0.349385 | 0.000000 | — | 1.768321–1.768321 |
| initial | 1.739755 | 1.726987 | 0.001801 | 0.349385 | 0.005156 | 0.908444 | 0.025721–0.032441 |
| V3.1 | 0.214952 | 0.204083 | 0.194623 | 0.349385 | 0.557044 | 0.942573 | 1.338290–2.251181 |
| C0 | 0.164151 | 0.157275 | 0.229620 | 0.349385 | 0.657213 | 0.942563 | 1.341593–2.378343 |
| C1 | 0.048671 | 0.048335 | 0.328518 | 0.349385 | 0.940275 | 0.987468 | 1.309080–2.865164 |
| C2 | 0.098122 | 0.093997 | 0.306441 | 0.349385 | 0.877086 | 0.945908 | 1.386204–2.862428 |

`prediction_dispersion.png` muestra todas las observaciones, incluida la inicialización casi constante. El contraste contra la constante train y el modelo inicial mide utilidad predictiva en datos expuestos. Una correlación aislada no basta: debe acompañarse de escala, sesgo y errores. Las curvas de entrenamiento con dropout/aumentaciones están etiquetadas como condiciones distintas; no se emplean para concluir sobreajuste. La tabla anterior sí usa condiciones iguales en train y validation.

## Bandas internas y cola (no clases GOES)

Low: SI<1.41; medium: 1.41≤SI<1.75; high: SI≥1.75; cola: SI>2. El SI conservado es el porcentaje original de píxeles con |B_LOS|>200G, no un pronóstico. La entrada mantiene clip400 y canales B+/B− sin transformaciones aprendidas.


| Modelo | Banda | n | MAE | Sesgo | p95 error absoluto |
|---|---|---|---|---|---|
| constant | low | 43 | 0.435954 | 0.435954 | 0.523898 |
| constant | medium | 96 | 0.238912 | 0.238912 | 0.355442 |
| constant | high | 124 | 0.309489 | -0.308934 | 0.671998 |
| constant | tail_si_gt_2 | 71 | 0.450589 | -0.450589 | 0.704443 |
| initial | low | 43 | 1.305735 | -1.305735 | 1.377965 |
| initial | medium | 96 | 1.502161 | -1.502161 | 1.686672 |
| initial | high | 124 | 2.047124 | -2.047124 | 2.408832 |
| initial | tail_si_gt_2 | 71 | 2.188322 | -2.188322 | 2.441159 |
| V3.1 | low | 43 | 0.051748 | 0.043637 | 0.116598 |
| V3.1 | medium | 96 | 0.102905 | -0.098493 | 0.256925 |
| V3.1 | high | 124 | 0.335240 | -0.335240 | 0.564355 |
| V3.1 | tail_si_gt_2 | 71 | 0.397147 | -0.397147 | 0.575095 |
| C0 | low | 43 | 0.068142 | 0.062771 | 0.138580 |
| C0 | medium | 96 | 0.084208 | -0.067203 | 0.241167 |
| C0 | high | 124 | 0.244752 | -0.244752 | 0.454815 |
| C0 | tail_si_gt_2 | 71 | 0.298464 | -0.298464 | 0.472490 |
| C1 | low | 43 | 0.058251 | 0.056837 | 0.107053 |
| C1 | medium | 96 | 0.048276 | 0.018367 | 0.116584 |
| C1 | high | 124 | 0.044943 | -0.005844 | 0.108629 |
| C1 | tail_si_gt_2 | 71 | 0.044165 | -0.018070 | 0.107794 |
| C2 | low | 43 | 0.115388 | 0.115388 | 0.192281 |
| C2 | medium | 96 | 0.081329 | 0.004184 | 0.195488 |
| C2 | high | 124 | 0.096386 | -0.056335 | 0.246000 |
| C2 | tail_si_gt_2 | 71 | 0.100948 | -0.069524 | 0.277771 |

El CSV `comparison_table.csv` conserva además RMSE, R², MAPE y dispersión para cada banda en train y validation.

## Filtros B predefinidos: evidencia preliminar

| Candidato | ΔMAE vs V3.1 | IC95 exploratorio | Mejora ≥0.01 | Guardas fallidas vs V3.1 | ΔMAE vs C0 | Guardas fallidas vs C0 |
|---|---|---|---|---|---|---|
| C0 | -0.046808 | [-0.056319, -0.03642] | Sí | low_mae | 0.000000 | ninguna |
| C1 | -0.155748 | [-0.187471, -0.122943] | Sí | ninguna | -0.108940 | ninguna |
| C2 | -0.110087 | [-0.139566, -0.078971] | Sí | low_mae, low_bias | -0.063278 | low_mae, low_bias |

Diferencia negativa favorece al candidato. IC pareado exploratorio: bloques de 27 días de registro TAI desde 2016-02-03, 2000 remuestreos seed2026; se conservan todas las muestras de cada bloque. No elimina toda correlación ni convierte validation en test. `comparisons.json` conserva cada guarda, límite y diferencia; no se cambiaron los umbrales de B.


Comparación directa C1−C2: ΔMAE -0.045661, IC95 exploratorio [-0.05718, -0.035545]. `paired_errors.csv` conserva los errores y diferencias por observación para todos los pares relevantes.

**Pendientes expresos:** estabilidad entre semillas (V3.2-D), latencias p50/p95 de forward y prepare+forward, RSS aislado en dos procesos, bytes completos requeridos por servicio, paridad ONNX y HTTP de candidatos. No se exportó ONNX por instrucción. Duración y memoria de entrenamiento no satisfacen esas guardas. Ningún candidato se declara aprobado para promoción.

## Auditoría XAI: nueve muestras fijadas antes de resultados

| Fila | Banda | SI | Archivo |
|---|---|---|---|
| 148 | low | 1.220363 | hmi.m_45s.2016.11.12_00_01_30_TAI.magnetogram_processed.npy |
| 284 | low | 1.348197 | hmi.m_45s.2017.07.06_00_01_30_TAI.magnetogram_processed.npy |
| 68 | low | 1.408035 | hmi.m_45s.2016.06.05_00_01_30_TAI.magnetogram_processed.npy |
| 719 | medium | 1.411068 | hmi.m_45s.2021.10.09_00_01_30_TAI.magnetogram_processed.npy |
| 848 | medium | 1.497126 | hmi.m_45s.2022.05.31_00_01_30_TAI.magnetogram_processed.npy |
| 230 | medium | 1.734787 | hmi.m_45s.2017.03.30_00_01_30_TAI.magnetogram_processed.npy |
| 885 | high | 1.754844 | hmi.m_45s.2022.08.10_00_01_30_TAI.magnetogram_processed.npy |
| 1645 | high | 2.053314 | hmi.m_45s.2025.11.08_00_01_30_TAI.magnetogram_processed.npy |
| 1312 | high | 2.949613 | hmi.m_45s.2024.08.09_00_01_30_TAI.magnetogram_processed.npy |

Se eligieron los extremos y la mediana por target de cada banda, sin mirar predicciones/mapas de los nuevos modelos. Incluye dos SI>2. Se reutilizaron `GradCAMHookManager` y `compute_gradcam`: salida de stage4 (64×64), objetivo escalar, gradientes medios por canal, ReLU, interpolación bilineal a 512×512 align_corners=False y normalización original. El máximo normalizado no es un porcentaje de acierto.


| Modelo | Fila | SD CAM | Correlación CAM inicial | Solapamiento top10 inicial | AUC random−guiada (SI pp) | AUCs 3 semillas |
|---|---|---|---|---|---|---|
| initial | 148 | 0.090168 | — | — | 0.002319 | 0.002295, 0.002310, 0.002352 |
| initial | 284 | 0.069335 | — | — | 0.002302 | 0.002298, 0.002318, 0.002290 |
| initial | 68 | 0.072787 | — | — | 0.003120 | 0.003115, 0.003136, 0.003109 |
| initial | 719 | 0.059685 | — | — | 0.002606 | 0.002637, 0.002629, 0.002551 |
| initial | 848 | 0.079120 | — | — | 0.003109 | 0.003144, 0.003119, 0.003064 |
| initial | 230 | 0.068734 | — | — | 0.003080 | 0.003087, 0.003110, 0.003044 |
| initial | 885 | 0.092296 | — | — | 0.003929 | 0.003946, 0.003962, 0.003877 |
| initial | 1645 | 0.102403 | — | — | 0.004669 | 0.004682, 0.004631, 0.004693 |
| initial | 1312 | 0.140375 | — | — | 0.006605 | 0.006638, 0.006586, 0.006590 |
| C0 | 148 | 0.058165 | -0.458995 | 0.080224 | 0.008036 | 0.007256, 0.006379, 0.010472 |
| C0 | 284 | 0.037083 | -0.376130 | 0.080491 | 0.008706 | 0.009341, 0.008256, 0.008522 |
| C0 | 68 | 0.052829 | 0.002156 | 0.300488 | 0.034988 | 0.034778, 0.036702, 0.033483 |
| C0 | 719 | 0.041511 | 0.364506 | 0.177615 | 0.038035 | 0.040855, 0.037142, 0.036107 |
| C0 | 848 | 0.045178 | 0.219496 | 0.305180 | 0.058130 | 0.060913, 0.058170, 0.055307 |
| C0 | 230 | 0.052382 | 0.393801 | 0.223888 | 0.059480 | 0.062083, 0.058080, 0.058276 |
| C0 | 885 | 0.070770 | 0.575440 | 0.575227 | 0.124593 | 0.125518, 0.126013, 0.122247 |
| C0 | 1645 | 0.077531 | 0.795421 | 0.682574 | 0.239387 | 0.240954, 0.238219, 0.238986 |
| C0 | 1312 | 0.132792 | 0.843317 | 0.850462 | 0.487768 | 0.487216, 0.484347, 0.491742 |
| C1 | 148 | 0.099412 | 0.420720 | 0.414778 | 0.032260 | 0.029510, 0.033714, 0.033555 |
| C1 | 284 | 0.087078 | 0.393976 | 0.420577 | 0.039171 | 0.038460, 0.038442, 0.040611 |
| C1 | 68 | 0.104302 | 0.394111 | 0.374609 | 0.053770 | 0.051968, 0.055963, 0.053380 |
| C1 | 719 | 0.072511 | 0.509743 | 0.358015 | 0.059220 | 0.064659, 0.057657, 0.055343 |
| C1 | 848 | 0.058982 | 0.333024 | 0.245937 | 0.050692 | 0.053329, 0.046720, 0.052028 |
| C1 | 230 | 0.074612 | 0.635510 | 0.583772 | 0.091836 | 0.096304, 0.088493, 0.090710 |
| C1 | 885 | 0.080488 | 0.341935 | 0.228199 | 0.084350 | 0.087784, 0.081761, 0.083506 |
| C1 | 1645 | 0.071344 | 0.661447 | 0.407073 | 0.149743 | 0.149615, 0.145912, 0.153702 |
| C1 | 1312 | 0.089647 | 0.571819 | 0.454108 | 0.225840 | 0.223754, 0.224700, 0.229066 |
| C2 | 148 | 0.046391 | -0.275429 | 0.085527 | 0.014611 | 0.013022, 0.014411, 0.016401 |
| C2 | 284 | 0.030392 | -0.224816 | 0.091478 | 0.016141 | 0.015352, 0.018277, 0.014793 |
| C2 | 68 | 0.042272 | 0.140002 | 0.305791 | 0.056784 | 0.058152, 0.057301, 0.054899 |
| C2 | 719 | 0.035095 | 0.507464 | 0.199779 | 0.047483 | 0.049660, 0.049884, 0.042906 |
| C2 | 848 | 0.037532 | 0.315246 | 0.292935 | 0.073054 | 0.075513, 0.073017, 0.070633 |
| C2 | 230 | 0.044629 | 0.524759 | 0.263905 | 0.077297 | 0.080380, 0.079065, 0.072446 |
| C2 | 885 | 0.057322 | 0.628186 | 0.567864 | 0.141638 | 0.142375, 0.146397, 0.136142 |
| C2 | 1645 | 0.072138 | 0.818553 | 0.693065 | 0.255818 | 0.259915, 0.255427, 0.252111 |
| C2 | 1312 | 0.116737 | 0.847313 | 0.847944 | 0.502065 | 0.497962, 0.503021, 0.505213 |

Cada candidato tiene nueve figuras finales de seis paneles en `xai/C*/figures_fixed_scale/`, los mapas numéricos y 396 registros de oclusión. El inicial común tiene otros 396 registros y nueve mapas; sus pesos y outputs en eval son idénticos para C0/C1/C2, por lo que se calcula una vez y se referencia sin repetir ni elegir resultados.

Los gráficos finales fijan HMI [-1,1], polaridades [0,1] y CAM [0,1]. Una corrección solo de representación eliminó escalas automáticas asimétricas que teñían el cero de un HMI; datos/mapas/predicciones no cambiaron y los renders previos siguen disponibles (`figure_rendering_v2_registration.json`). Alineación: reconstrucción exacta B+−B−=NPY, polaridades no negativas/excluyentes, mismo tamaño 512×512, sin rotaciones/transposiciones y `origin=upper` común en todas las figuras. Los ejes indican filas/columnas del array, no coordenadas solares. No existe máscara regional/WCS con la que medir acierto espacial físico.

Oclusión: misma máscara pone a cero ambos canales, 0–100% cada10%, ranking estable; tres órdenes aleatorios seed42/137/2026 con igual número de píxeles. Se conservan predicciones absolutas, cambios respecto a entrada sin ocluir y fracción de magnitud retirada. AUC positiva indica únicamente mayor descenso guiado. Igual área no garantiza igual forma/contenido; la oclusión guiada es más contigua y la aleatoria introduce perforaciones. Ceros/bordes y borrado del disco generan entradas fuera de distribución, especialmente con áreas grandes. No se usa el target original como error ordinario de la entrada alterada y una caída grande no demuestra causalidad. La magnitud AUC depende de la escala de salida: un AUC mayor que el inicial no implica por sí solo una explicación más fiel.

MC sigue disponible mediante `enable_mc_dropout`, con BN congelada: C0 tiene cuatro Dropout2d p0.2, C2 cuatro p0.1 y C1 conserva esos módulos con p0; todos conservan cabeza Dropout p0.3. No se añadieron barridos MC.

## Entrenamiento, recursos y trazabilidad

| Candidato | Backbone/head | Parámetros | Épocas / seleccionada | Minutos | Pico RSS de vida (GiB) | Máximo driver MPS muestreado (GiB) | Estado |
|---|---|---|---|---|---|---|---|
| C0 | 0.2/0.3 | 206875 | 16 / 6 | 24.43 | 0.809 | 3.480 | early_stop_whl |
| C1 | 0.0/0.3 | 206875 | 37 / 27 | 36.57 | 0.802 | 3.482 | early_stop_whl |
| C2 | 0.1/0.3 | 206875 | 24 / 14 | 26.73 | 0.812 | 3.482 | early_stop_whl |

Batch8 común fijado antes del piloto: batch32 histórico de Phase1.5 había requerido ~12.9GB MPS y había ~9GB disponibles al preparar C. El piloto descartó tres pasos, estimó ~84s/época y ~7h máximo para los tres brazos; no constituye un cuarto entrenamiento completo ni aporta pesos a los brazos. Cuatro hilos/uno interop, workers0, float32 MPS determinista. Scheduler y parada por Weighted Huber determinista, selección exclusivamente MAE determinista (instrucción actual prevalece sobre propuesta B). Arquitectura, loss delta1/alpha2, AdamW lr0.001/decay1e-5, ECA, BN, target, split e input sin cambios.

La inicialización y el archivo initial.pth son idénticos byte a byte. Los hashes reales de orden y de los tensores aumentados coinciden en todas las épocas compartidas. El RNG de aumentaciones se aísla por época/fila; dropout por época/lote/capa, preservando máscaras de cabeza al cambiar el consumo de backbone. Las máscaras de backbone no pueden ser iguales con probabilidades distintas; gradientes/BN/scheduler/parada divergen como consecuencia del tratamiento. Batch y control RNG comunes difieren del histórico, por lo que C0 mide el protocolo nuevo y no una réplica exacta de Phase1.5.

La medición final CPU batch1 no reelige épocas: `mps_cpu_check.json` registra la discrepancia con la evaluación MPS batch8 que seleccionó el checkpoint. No implica paridad ONNX. La memoria de driver incluye cachés/allocators; RSS es de proceso y ru_maxrss es máximo de toda su vida, no activaciones exclusivas ni evidencia móvil. Hubo análisis CPU de controles/candidatos simultáneo con parte de C0/C1/C2 y actividad de escritorio; duraciones son observadas, no benchmarks de costo aislados.

## Evidencia e interpretación

### Suplemento descriptivo posterior: píxeles exactamente cero


| Modelo | Media fracción CAM en ceros: 3 casos low | Mínimo: 9 casos | Máximo: 9 casos |
|---|---|---|---|
| initial | 0.036549 | 0.014393 | 0.053619 |
| C0 | 0.298697 | 0.184031 | 0.314385 |
| C1 | 0.205565 | 0.160295 | 0.219889 |
| C2 | 0.291258 | 0.155734 | 0.306151 |

Definido después de observar el fondo de C0, con UTC y fuente en `zero_pixel_audit_registration.json`. Fracción de la suma del CAM normalizado, NO porcentaje de acierto/atención física. Los ceros son valores exactos del NPY, no una máscara física de disco o región; esta prueba tampoco aísla el borde no nulo. Normalización, resolución/interpolación y sesgos de las activaciones pueden influir. Los 36 registros completos están en `xai/zero_pixel_support.csv`. No cambia la auditoría primaria, las oclusiones ni los criterios de selección.


- **C0:** MAE validation 0.157275 frente a constante 0.304404 e inicial 1.726987. Ratio SD pred/target 0.657, correlación 0.943, sesgo -0.129664; MAE train eval 0.164151. Oclusión guiada tiene AUC media positiva en 9/9 casos (conteo descriptivo, no porcentaje de aprendizaje). Se conservan las tres semillas y todas las curvas.

- **C1:** MAE validation 0.048335 frente a constante 0.304404 e inicial 1.726987. Ratio SD pred/target 0.940, correlación 0.987, sesgo +0.013242; MAE train eval 0.048671. Oclusión guiada tiene AUC media positiva en 9/9 casos (conteo descriptivo, no porcentaje de aprendizaje). Se conservan las tres semillas y todas las curvas.

- **C2:** MAE validation 0.093997 frente a constante 0.304404 e inicial 1.726987. Ratio SD pred/target 0.877, correlación 0.946, sesgo -0.006168; MAE train eval 0.098122. Oclusión guiada tiene AUC media positiva en 9/9 casos (conteo descriptivo, no porcentaje de aprendizaje). Se conservan las tres semillas y todas las curvas.

**Control desfavorable para una lectura visual fuerte:** el inicial ya tiene correlación0.908444 con el target y AUC guiada positiva en9/9, pese a MAE1.726987 y salidas casi constantes. C0 fila148 presenta una curva guiada no monótona: algunas fracciones aleatorias reducen más la predicción aunque el AUC integrado sea positivo. La ventaja global no implica superioridad en cada fracción ni prueba física. C1 tampoco mejora el MAE bajo frente a V3.1 (0.058251 frente a0.051748), aunque esa diferencia respeta la tolerancia predefinida.


**Duda XAI concreta de C1:** inspección de las nueve muestras muestra saliencia fuerte en el borde del disco, especialmente en banda baja y varios ejemplos medios. El modelo inicial también tenía señal en ese borde. Los mapas de C1 no son idénticos al inicial, pero esta auditoría NO separa información útil para el SI global de un atajo de borde/procesamiento o de un artefacto del método de atribución. Una auditoría controlada de ese mecanismo queda pendiente; no se inventó una máscara regional ni se atribuyó una causa física. C0 y C2 también muestran atribución difusa sobre fondo en ejemplos bajos.


**Configuración a repetir:** C1 obtuvo el menor MAE determinista de esta semilla (0.048335); es una recomendación para contrastar con C0 en otras semillas, condicionada a las guardas y limitaciones anteriores. No se ejecutó otra semilla ni se inició V3.2-D.

La reducción de errores frente a controles, variación entre entradas y dependencia de las perturbaciones aportan evidencia local de aprendizaje útil. Los mapas iniciales pueden ser estructurados por la arquitectura y la magnitud de entrada; similitud inicial/entrenado o respuestas aleatorias fuertes debilitan interpretaciones visuales. Persisten selección-validation, posible correlación temporal, una sola semilla, sensibilidad a intensidad global y ausencia de prueba física/causal. Esta auditoría no separa por completo el uso de estadísticas globales de patrones espaciales aprendidos. No se demuestra generalización temporal ni aprendizaje de física solar.

## Tests, archivos y cierre

6 tests de protocolo y 4 de análisis pasaron. `verify.py` reejecuta scheduler/parada desde historial, verifica selección mínima, hashes/valores finitos, contadores BN (132 actualizaciones por época de train), métricas guardadas y oclusiones. `verification.json`: 3372 archivos protegidos sin cambios. `analysis_checks.json`: identidad/target/orden, inicialización, aumentaciones y selección. Se verificó split1051/263, sin solapamiento por fila/nombre/SHA-256, y 1314 NPY contra la auditoría histórica. La comparación de aumentaciones/orden cubre16 épocas C0–C1,16 C0–C2 y24 C1–C2.

`protocol.json`/`PROTOCOL.md` y fuentes se congelaron antes de entrenar; `analysis_implementation_registration.json` distingue el diseño previo de la implementación completada cuando C0 ya había empezado. La corrección de código `analysis_correction_v2.json` eliminó una guarda extra de p95 por banda para respetar B; no cambió sus umbrales y se hizo antes del scoring final de candidatos. La comprobación posterior de soporte en píxeles cero se registra aparte, sin efecto sobre selección ni filtros. Configuración, entorno, checkpoints inicial/seleccionado/final, curvas, historial por época, CSV train/validation, XAI y hashes permanecen en esta carpeta. `artifact_hashes.json` cubre resultados finales; caches quedan fuera.

**Pendientes:** estabilidad entre semillas, evaluación temporal/test independiente, criterios de costo de B y paridad de candidatos; pruebas físicas de explicaciones más allá de esta auditoría. Ninguno se presenta como cumplido. Son límites para promoción/generalización, no entrenamientos adicionales iniciados.

**FASE V3.2-C: CUMPLIDA.** Experimentos y auditoría acotada terminados; aprobación de un nuevo modelo pendiente. V3.1, API, preprocesamiento, target, split, artefactos históricos y producto aprobado intactos. Sin frontend/Agent Lab/gemelo/Unity/Needle/WebAR/timeline/diseño solar, ONNX nuevo, dependencias, commits, push o publicación. No se inició otra fase.
