# FASE V3.2-D — estabilidad entre semillas y controles de aprendizaje


Se conservaron C0/C1 seed42 de C y se completaron exactamente cuatro entrenamientos nuevos, C0/C1 con seed137 y seed2026. Cada modelo tiene 206875 parámetros. V3.1 sigue activa; ningún candidato ha sido promovido. La evaluación final es determinista PyTorch CPU float32, batch1, cuatro hilos/uno interop, eval sin aumentaciones, con métricas float64 recalculadas desde CSV. Las 263 observaciones son validation de selección, no un test independiente ni temporal.


## Resultado e interpretación


C1 mantiene la ventaja sobre C0 en las tres semillas. Su MAE de validation es
0.048335, 0.054007 y 0.051862 para 42, 137 y 2026; C0 obtiene 0.157275,
0.119257 y 0.139347. La media ± SD muestral es **0.051401 ± 0.002864 para
C1**, frente a **0.138626 ± 0.019019 para C0**. El rango C1 es
[0.048335, 0.054007]. Las diferencias emparejadas C1−C0 son −0.108940,
−0.065250 y −0.087485 SI pp; ninguna semilla deteriora el MAE. El intervalo
exploratorio agregado es [−0.102700, −0.072473], condicionado a estas semillas
y observaciones. No se mezclaron predicciones para crear otro modelo.

Las guardas predictivas de B pasan para cada C1 frente a V3.1 determinista y
frente a su C0, y también para las métricas agregadas. **Esto no equivale a
superar todos los requisitos de B:** costos y paridad de despliegue siguen sin
medirse. C0 falla la guarda de MAE bajo en las tres semillas; además falla
sesgo bajo en 137 y 2026. Su agregado falla ambas. Esos controles se conservan.

La baja actividad sigue siendo una debilidad de C1: MAE 0.058251, 0.058415 y
0.057438, todos peores que V3.1 (0.051748). Los aumentos de 0.006503,
0.006667 y 0.005690 pasan la tolerancia de +0.01, pero no son mejoras.
Los sesgos bajos permanecen positivos (aproximadamente +0.055 a +0.057 SI pp)
y los R² dentro de esa banda son negativos (−0.617, −0.683 y −0.670).
La banda tiene un rango de targets estrecho; el buen R² global no elimina
este resultado. También permanece subestimación media en la cola SI>2:
sesgos −0.018070, −0.054869 y −0.033359 para C1.

Hay evidencia de aprendizaje útil en esta selección-validation: los tres C1
superan ampliamente la constante train (MAE 0.304404) y las inicializaciones
sin entrenar (MAE entre 1.672777 y 1.726987). La SD de sus predicciones es
0.328518, 0.315269 y 0.325703, frente a 0.349385 de los targets; conserva
aproximadamente 0.90–0.94 de esa dispersión. Las inicializaciones tienen SD
de solo 0.000390 a 0.002397. Los gráficos completos muestran que C1 no se
limita a una constante, aunque concentra y sobreestima parte del rango bajo.
Sus MAE train/validation comparables son 0.048671/0.048335,
0.054089/0.054007 y 0.051750/0.051862. No aparece una brecha global grande
en esas condiciones; esto no descarta sobreajuste de selección ni demuestra
generalización temporal. No se usaron las curvas train con ruido para esa
comparación.

La referencia sencilla aporta una advertencia útil. El conteo crudo sobre NPY
reducido, con umbral fijo estricto |NPY|>0.5 y denominador 512², obtiene MAE
1.522976 y sesgo −1.522976; no reproduce el SI previo al resize. La versión
afín ajustada únicamente en train obtiene **MAE 0.113250** y R² 0.847733,
con train MAE 0.111824. Supera globalmente a los tres C0 y a V3.1 determinista,
pero los tres C1 la mejoran entre 0.059242 y 0.064914 SI pp de MAE. La
aproximación calibrada también sobreestima baja actividad (MAE/sesgo
+0.151234). La CNN C1 aporta precisión adicional frente a este control;
ello no identifica qué propiedades de la imagen usa ni prueba física solar.
La mala escala del conteo crudo es consistente con la diferencia de resolución
y operación de umbral; no se atribuye todo el desfase a una causa aislada sin
disponer aquí de una nueva comparación contra los arrays originales.

**La duda de borde/fondo persiste.** La revisión de las nueve muestras completas
encuentra el énfasis periférico de C1 en las tres semillas, especialmente en
las tres muestras bajas. La fracción media de suma CAM sobre ceros exactos
en esa banda es 0.205565, 0.168018 y 0.199346. Es un descriptor del mapa,
no una proporción de razonamiento físico ni una máscara del disco. Los mapas
C1 de 137/2026 correlacionan con los de 42 entre 0.915 y 0.956: el patrón
se repite, sin que eso certifique su validez. C0 también muestra fondo amplio
no nulo, aunque su periferia aparece relativamente oscura. Los mapas iniciales
ya presentan estructura magnética y periférica pese a predecir casi constantes.
La correlación C1–inicial propia va de 0.333–0.661 (42), 0.424–0.837 (137)
y 0.297–0.733 (2026). Cambian con el entrenamiento, pero algunos casos,
particularmente altos de 137, conservan mucha estructura inicial.

Los controles cuadrados de igual forma y área confirman respuesta del predictor
a las perturbaciones: en las nueve muestras de cada C1, para ambos tamaños,
la caída guiada supera la media de sus 15 ventanas aleatorias. La caída extra
media es 0.088216/0.140007 (42), 0.092643/0.135189 (137) y
0.086573/0.135327 (2026), para 64²/128² respectivamente. No es una tasa de
acierto. En C0 hay contraejemplos: con 42 y 2026 solo 8/9 casos de 64² y
7/9 de 128² muestran esa dirección. Incluso los iniciales muestran dirección
guiada favorable en 9/9 casos, pero con efectos medios mucho menores
(aproximadamente 0.000088–0.000753 SI pp). La dirección por sí sola no
demuestra aprendizaje.

La magnitud retirada revela un confusor: en C1, las ventanas guiadas retiran
en promedio 0.054–0.089 de la suma |NPY| para 64² frente a 0.017 aleatoria,
y 0.124–0.141 para 128² frente a 0.076 aleatoria. No se igualó esa información
solo por igualar área. Hay casos con más caída pese a retirar menos magnitud:
por ejemplo, fila68/seed137/128² retira 0.049666 frente a 0.074503 aleatoria,
con caída extra 0.034943 SI pp. Tampoco esto prueba causalidad: ubicación,
distribución de campo, transición al fondo y bordes artificiales siguen distintos.
En seed2026 las ventanas guiadas de los tres casos bajos recaen sobre segmentos
periféricos y cambian la predicción; no puede explicarse toda esa respuesta
como un mero color de Grad-CAM. Aun así, no se separa una dependencia útil del
predictor de un atajo o de sensibilidad fuera de distribución.

La resolución nativa 64², su interpolación a 512², la normalización por muestra
y los campos receptivos impiden interpretar cada píxel CAM como dependencia
local independiente. Las tres oclusiones registradas que retiran magnitud cero
no cambian la predicción, como corresponde a entradas idénticas; ello no hace
del soporte de ceros una máscara física. No se modificaron mapas para mejorar
su aspecto, no se asignaron regiones activas ni WCS, y los cambios sobre
entradas ocluidas no se puntuaron contra el SI original.

**Recomendación:** continuar con la configuración C1 hacia una fase posterior
de exportación, paridad y medición de costos, manteniendo V3.1 activa. La
ventaja emparejada se mantiene y las guardas predictivas pasan; C0 queda como
control desfavorable. Esta recomendación no elige la semilla más favorable ni
autoriza promoción. Conservar los tres checkpoints C1 y definir el procedimiento
de despliegue antes de nuevas mediciones. Mantener explícitas las dudas de
borde/fondo, el deterioro bajo tolerado y la necesidad de evidencia independiente.
No se ha iniciado esa fase ni una nueva línea de entrenamiento.



## Modelos individuales y referencias


MAE, RMSE, sesgo y p95 se expresan en puntos porcentuales SI; MAPE en porcentaje. Se conservan las mismas identidades/targets y orden. Cada fila corresponde a un modelo individual; no se promediaron predicciones para formar un ensemble.


| Modelo | MAE val | RMSE | R² | MAPE % | Sesgo | p95 absoluto | MAE train eval |
|---|---|---|---|---|---|---|---|
| constant | 0.304404 | 0.349620 | -0.001348 | 17.887177 | 0.012828 | 0.591570 | 0.292543 |
| V3.1 | 0.204083 | 0.258233 | 0.453720 | 10.497507 | -0.186877 | 0.487845 | 0.214952 |
| strong_raw | 1.522976 | 1.532148 | -18.230629 | 88.451411 | -1.522976 | 1.822476 | 1.543478 |
| strong_affine_train | 0.113250 | 0.136335 | 0.847733 | 6.646445 | 0.024066 | 0.251355 | 0.111824 |
| initial_s42 | 1.726987 | 1.761651 | -24.423267 | 98.331392 | -1.726987 | 2.328941 | 1.739755 |
| C0_s42 | 0.157275 | 0.200928 | 0.669270 | 8.234291 | -0.129664 | 0.395529 | 0.164151 |
| C1_s42 | 0.048335 | 0.059056 | 0.971429 | 2.908951 | 0.013242 | 0.109745 | 0.048671 |
| initial_s137 | 1.674809 | 1.710790 | -22.976472 | 95.229295 | -1.674809 | 2.278734 | 1.687629 |
| C0_s137 | 0.119257 | 0.142129 | 0.834515 | 7.245099 | 0.014180 | 0.263434 | 0.120750 |
| C1_s137 | 0.054007 | 0.068193 | 0.961904 | 3.164928 | -0.001931 | 0.126519 | 0.054089 |
| initial_s2026 | 1.672777 | 1.708433 | -22.910444 | 95.129422 | -1.672777 | 2.274150 | 1.685532 |
| C0_s2026 | 0.139347 | 0.174612 | 0.750229 | 7.474151 | -0.094607 | 0.343204 | 0.147935 |
| C1_s2026 | 0.051862 | 0.064623 | 0.965789 | 3.087453 | 0.003185 | 0.122804 | 0.051750 |


V3.1 es referencia adicional seleccionada históricamente mediante MC en época40; aquí se reutiliza su evaluación CPU determinista verificada en C (ONNX congelado de B: MAE0.20408340). El MAE MC histórico0.10155762 usó MPS batch32/T20 y otro criterio de selección; no se mezcla con estas filas. La constante se ajustó a la media de1051 train. Iniciales son checkpoints conservados antes de cualquier entrenamiento.



## Estabilidad entre tres semillas


Media y desviación muestral (ddof1) de métricas de tres modelos separados. El rango incluye todos los seeds, sin seleccionar el favorable. Tres semillas aportan evidencia limitada; esta SD no es un intervalo de generalización.


| Configuración | Métrica global val | Media | SD muestral | Mínimo | Máximo |
|---|---|---|---|---|---|
| C0 | mae | 0.138626 | 0.019019 | 0.119257 | 0.157275 |
| C0 | rmse | 0.172557 | 0.029453 | 0.142129 | 0.200928 |
| C0 | r2 | 0.751338 | 0.082628 | 0.669270 | 0.834515 |
| C0 | mape | 7.651180 | 0.517813 | 7.245099 | 8.234291 |
| C0 | bias | -0.070030 | 0.075005 | -0.129664 | 0.014180 |
| C0 | p95_absolute_error | 0.334056 | 0.066521 | 0.263434 | 0.395529 |
| C0 | absolute_bias | 0.079483 | 0.059209 | 0.014180 | 0.129664 |
| C1 | mae | 0.051401 | 0.002864 | 0.048335 | 0.054007 |
| C1 | rmse | 0.063958 | 0.004605 | 0.059056 | 0.068193 |
| C1 | r2 | 0.966374 | 0.004789 | 0.961904 | 0.971429 |
| C1 | mape | 3.053777 | 0.131269 | 2.908951 | 3.164928 |
| C1 | bias | 0.004832 | 0.007719 | -0.001931 | 0.013242 |
| C1 | p95_absolute_error | 0.119689 | 0.008810 | 0.109745 | 0.126519 |
| C1 | absolute_bias | 0.006119 | 0.006200 | 0.001931 | 0.013242 |


`seed_aggregate.csv` conserva el mismo resumen para train/validation y cada banda/cola, incluida dispersión. Sesgo firmado y media de |sesgo| se muestran separados para evitar cancelación entre semillas.


| Seed | ΔMAE C1−C0 | IC95 exploratorio por bloques | No deterioro >0.005 | Guardas fallidas C1 vsC0 |
|---|---|---|---|---|
| 42 | -0.108940 | [-0.133291, -0.084335] | True | ninguna |
| 137 | -0.065250 | [-0.077715, -0.05324] | True | ninguna |
| 2026 | -0.087485 | [-0.107066, -0.068374] | True | ninguna |


ΔMAE emparejado medio C1−C0: -0.087225; SD 0.021846; rango [-0.108940, -0.065250]. IC exploratorio agregado: [-0.1027, -0.072473]. Este IC remuestrea bloques sobre la media de errores absolutos de los tres modelos por observación, NO calcula el error de una predicción promedio. Está condicionado a estas tres semillas; no modela exhaustivamente incertidumbre entre entrenamientos.


Los intervalos usan bloques27 días de registro TAI desde2016-02-03,2000 remuestreos seed2026, igual que C. No eliminan toda correlación ni la exposición a validation. `paired_errors.csv` conserva errores emparejados por observación/seed, `paired_metrics.csv` todas las diferencias por banda/métrica y `paired_metric_aggregate.csv` su media/SD/rango.



## Bandas y cola, incluidos resultados desfavorables


Bandas internas: low<1.41, medium[1.41,1.75), high≥1.75; cola SI>2. No clases GOES. `comparison_table.csv` contiene todas las métricas en train/val para cada banda, incluidos RMSE/R²/MAPE.


| Modelo | Banda | n | MAE | RMSE | MAPE % | Sesgo | p95 absoluto |
|---|---|---|---|---|---|---|---|
| C0_s42 | low | 43 | 0.068142 | 0.078906 | 5.214092 | 0.062771 | 0.138580 |
| C0_s42 | medium | 96 | 0.084208 | 0.115147 | 5.349762 | -0.067203 | 0.241167 |
| C0_s42 | high | 124 | 0.244752 | 0.270562 | 11.514803 | -0.244752 | 0.454815 |
| C0_s42 | tail_si_gt_2 | 71 | 0.298464 | 0.315933 | 13.330046 | -0.298464 | 0.472490 |
| C1_s42 | low | 43 | 0.058251 | 0.065257 | 4.430629 | 0.056837 | 0.107053 |
| C1_s42 | medium | 96 | 0.048276 | 0.061612 | 3.156459 | 0.018367 | 0.116584 |
| C1_s42 | high | 124 | 0.044943 | 0.054603 | 2.189653 | -0.005844 | 0.108629 |
| C1_s42 | tail_si_gt_2 | 71 | 0.044165 | 0.053964 | 1.989214 | -0.018070 | 0.107794 |
| C0_s137 | low | 43 | 0.195921 | 0.201213 | 14.836323 | 0.195921 | 0.269876 |
| C0_s137 | medium | 96 | 0.100489 | 0.113104 | 6.687187 | 0.064968 | 0.185959 |
| C0_s137 | high | 124 | 0.107203 | 0.137483 | 5.044590 | -0.088163 | 0.295434 |
| C0_s137 | tail_si_gt_2 | 71 | 0.127483 | 0.160614 | 5.655365 | -0.123387 | 0.310832 |
| C1_s137 | low | 43 | 0.058415 | 0.066590 | 4.447392 | 0.057385 | 0.114773 |
| C1_s137 | medium | 96 | 0.050283 | 0.067178 | 3.271485 | 0.012766 | 0.124882 |
| C1_s137 | high | 124 | 0.055362 | 0.069510 | 2.637708 | -0.033878 | 0.132614 |
| C1_s137 | tail_si_gt_2 | 71 | 0.063880 | 0.078371 | 2.864316 | -0.054869 | 0.142197 |
| C0_s2026 | low | 43 | 0.097655 | 0.107892 | 7.452934 | 0.097622 | 0.172891 |
| C0_s2026 | medium | 96 | 0.072676 | 0.098395 | 4.618956 | -0.037575 | 0.199385 |
| C0_s2026 | high | 124 | 0.205421 | 0.230510 | 9.691982 | -0.205421 | 0.416433 |
| C0_s2026 | tail_si_gt_2 | 71 | 0.244850 | 0.264252 | 10.947040 | -0.244850 | 0.426035 |
| C1_s2026 | low | 43 | 0.057438 | 0.066324 | 4.378239 | 0.054877 | 0.113008 |
| C1_s2026 | medium | 96 | 0.051711 | 0.066500 | 3.368685 | 0.009898 | 0.121445 |
| C1_s2026 | high | 124 | 0.050045 | 0.062517 | 2.422113 | -0.019938 | 0.123407 |
| C1_s2026 | tail_si_gt_2 | 71 | 0.052702 | 0.065655 | 2.380156 | -0.033359 | 0.131065 |


## Guardas B sin modificar


Ruta precisión: mejora MAE≥0.01 vsV3.1; mejora media vscontroles y ningún seed deteriora>0.005; IC exploratorio pareado inferior a0. Guardas: ΔRMSE≤0.01, ΔMAPE≤0.5pp, Δ|sesgo global|≤0.01, Δp95 absoluto global≤0.02; ΔMAE por banda/cola≤0.01 y Δ|sesgo banda/cola|≤0.02. R² y p95 por banda se informan sin añadir nuevos umbrales. Para guardas agregadas, sesgo es media de |sesgo| por seed; los otros valores son medias de métricas. Un agregado que pase no borra fallos individuales.


| Modelo | ΔMAE vsV3.1 | Mejora ≥0.01 | Guardas fallidas vsV3.1 |
|---|---|---|---|
| C0_s42 | -0.046808 | True | low_mae |
| C1_s42 | -0.155748 | True | ninguna |
| C0_s137 | -0.084826 | True | low_mae, low_bias |
| C1_s137 | -0.150076 | True | ninguna |
| C0_s2026 | -0.064736 | True | low_mae, low_bias |
| C1_s2026 | -0.152221 | True | ninguna |

| Media de configuración | Referencia | Guardas agregadas fallidas |
|---|---|---|
| C0 | V3.1 | low_mae, low_bias |
| C1 | V3.1 | ninguna |
| C1 | C0 | ninguna |


Todos los deltas/límites y los intervalos individuales vsV3.1 y vsC0 se guardan en `comparisons.json`. Latencias p50/p95, prepare+forward, RSS aislado, bytes totales del servicio y paridad ONNX/HTTP permanecen pendientes: no se exportó ni midió ningún candidato. La memoria y duración de entrenamiento no satisfacen criterios de costo de B.



## Referencia de campo fuerte sobre datos reducidos


Contrato inspeccionado: SI original=100·count(|B_LOS|>200G)/todos los píxeles originales, antes del resize. NPY=clip(resize(B_LOS),−400,400)/400. Por ello se fijó estrictamente |NPY|>200/400=0.5 y denominador512×512, incluidos ceros y ambas polaridades. Es una aproximación sobre datos reducidos; el resize/anti-aliasing puede alterar cruces de umbral y mezclar polaridades. No se interpreta como SI original exacto ni se modifica su definición.


Calibración adicional preregistrada: predicción = 1.4390222817 + 1.4645692556 · proxy. OLS float64 con intercepto, solo1051 train, sin búsqueda de umbral ni clipping. Versión cruda conservada, aunque desfavorable. `strong_field_observations.csv` guarda conteos, denominador, identidad, target y SHA de cada NPY.


| Referencia | Banda | MAE | Sesgo | p95 absoluto |
|---|---|---|---|---|
| strong_raw | global | 1.522976 | -1.522976 | 1.822476 |
| strong_raw | low | 1.301929 | -1.301929 | 1.371262 |
| strong_raw | medium | 1.447874 | -1.447874 | 1.607624 |
| strong_raw | high | 1.657774 | -1.657774 | 1.890629 |
| strong_raw | tail_si_gt_2 | 1.693271 | -1.693271 | 1.909137 |
| strong_affine_train | global | 0.113250 | 0.024066 | 0.251355 |
| strong_affine_train | low | 0.151234 | 0.151234 | 0.215241 |
| strong_affine_train | medium | 0.085961 | 0.029027 | 0.172285 |
| strong_affine_train | high | 0.121204 | -0.023873 | 0.279217 |
| strong_affine_train | tail_si_gt_2 | 0.132301 | -0.010054 | 0.305886 |


`simple_reference_comparisons.json` compara cada C1 con ambas referencias por errores pareados. La calibración pertenece solo al control; no cambia entrada, target ni modelo de producto.



## XAI dirigido: método y evidencia completa


Se auditó y reutilizó `GradCAMHookManager(model,"stage4")` y `compute_gradcam`: salida del bloque completo128×64×64, gradiente de salida escalar promediado espacialmente por canal, suma ponderada y ReLU, bilinear512×512 align_corners=False, minmax con umbral1e−8. No es la subcapa stage4.conv. Mapas numéricos42 originales se copiaron verificando bytes; mapas nuevos preservan idéntico procedimiento y no afectan selección.


Las mismas nueve muestras fijadas por targets en C (tres por banda, extremos y mediana, incluidas filas1645/1312 con SI>2) aparecen completas en las figuras. B+−B− reconstruye exactamente el NPY; canales no negativos/excluyentes y misma máscara en ambos. Figuras HMI[-1,1],CAM[0,1], origin=upper, sin flips/transposes; coordenadas son índices del array. Se conserva representación corregida de C; no se mejora visualmente cambiando normalización.


Complemento: cuadrados64² y128², máximo de suma CAM en todas las posiciones legales frente a15 cuadrados aleatorios por tamaño (cinco por semillas42/137/2026). Forma y área idénticas, sin recorte/wrap. Posiciones aleatorias guardadas antes de inferir, comunes para todos los modelos/muestras; empate guiado por primer índice. 81 mapas y2592 registros de oclusión para tres iniciales y C0/C1×tres semillas; máscaras guiadas comprimidas, coordenadas/SHA de cada máscara y magnitud eliminada conservadas. Las oclusiones antiguas con píxeles dispersos se preservan en C, sin repetir ese barrido.


| Modelo | Seed | CAM en ceros (media3 low) | Extra caída guiada64 (media9) | Casos64 >random/9 | Extra caída guiada128 (media9) | Casos128 >random/9 |
|---|---|---|---|---|---|---|
| initial | 42 | 0.03654892432264759 | 0.000312 | 9 | 0.000564 | 9 |
| initial | 137 | 0.03200702173548916 | 0.000088 | 9 | 0.000139 | 9 |
| initial | 2026 | 0.042610128263578136 | 0.000402 | 9 | 0.000753 | 9 |
| C0 | 42 | 0.29869679547424344 | 0.059114 | 8 | 0.090212 | 7 |
| C0 | 137 | 0.2851027940014091 | 0.073342 | 8 | 0.110862 | 8 |
| C0 | 2026 | 0.2794569276987909 | 0.072250 | 8 | 0.103825 | 7 |
| C1 | 42 | 0.20556504501486317 | 0.088216 | 9 | 0.140007 | 9 |
| C1 | 137 | 0.16801826578380882 | 0.092643 | 9 | 0.135189 | 9 |
| C1 | 2026 | 0.19934603013466226 | 0.086573 | 9 | 0.135327 | 9 |


Extra caída positiva=random_mean_prediction−guided_prediction, en SI pp. Estos conteos son descriptivos, NO porcentaje de aprendizaje correcto ni confianza física. El descriptor de CAM en ceros es fracción de suma del mapa normalizado; ceros exactos NO constituyen máscara física del disco ni segmentan regiones. Resolución/interpolación, normalización, sesgos y campos receptivos pueden repartir saliencia fuera del soporte magnético. No se separa por completo ese efecto del uso del borde por el predictor.


Cada máscara registra suma dimensionless de |NPY| retirada, fracción del total, ceros incluidos, predicción antes/después y cambio firmado/absoluto. Igual área no igual información retirada. Ventanas guiadas y aleatorias pueden retirar magnitudes diferentes; sus diferencias no aíslan exclusivamente la importancia espacial. Ocluir introduce bordes artificiales y datos fuera de distribución. No se compara la entrada perturbada con el target original como error ordinario ni se declara causalidad por una caída grande. No se inventan WCS, coordenadas solares o máscaras físicas.


Mapas y comparaciones completos: `xai/map_comparison.csv`, `square_effects.csv`, `aggregate.csv` y `xai/figures/`. Cada modelo conserva CSV bruto, nueve mapas y máscaras en `xai/<modelo>_s<seed>/`. Los mapas iniciales siguen siendo controles necesarios: estructura visual y respuesta a oclusión pueden existir sin entrenamiento. MC sigue disponible con cabeza Dropout0.3; C0 conserva cuatro Dropout2d0.2 y C1 los mismos módulos con p0. No hubo barridos MC ni elección de semilla visual.



## Entrenamiento y recursos observados


| Configuración | Seed | Épocas / seleccionada | Minutos | Pico RSS de vida GiB | Máximo driver MPS muestreado GiB | MAE train eval | MAE val eval |
|---|---|---|---|---|---|---|---|
| C0 | 42 | 16 / 6 | 24.429741 | 0.808899 | 3.479843 | 0.164151 | 0.157275 |
| C1 | 42 | 37 / 27 | 36.570891 | 0.801865 | 3.481674 | 0.048671 | 0.048335 |
| C0 | 137 | 28 / 18 | 38.410290 | 0.672440 | 3.388046 | 0.120750 | 0.119257 |
| C1 | 137 | 80 / 60 | 87.154749 | 0.854950 | 3.481674 | 0.054089 | 0.054007 |
| C0 | 2026 | 28 / 18 | 38.230783 | 0.825241 | 3.479843 | 0.147935 | 0.139347 |
| C1 | 2026 | 63 / 55 | 77.784811 | 0.835312 | 3.481674 | 0.051750 | 0.051862 |


C se reprodujo exactamente: batch8/workers0, MPS float32 determinista, AdamW lr0.001/weight_decay1e−5, WeightedHuber delta1/alpha2, selección mínimo MAE determinista; scheduler ReduceLROnPlateau factor0.5/patience3/min_lr1e−6 y parada patience10/min_delta0 monitorizan WeightedHuber determinista, máximo100 épocas. No se cargó V3.1 para entrenar. AST del bucle coincide con C salvo metadato seed; cambios de semilla/rutas están en `training_adaptation.diff`.


Cada seed tiene inicialización propia, copiada byte a byte a C0/C1; las tres inicializaciones difieren. Órdenes y aumentaciones por época/fila, RNG de dropout por época/lote/capa, se controlan como en C. Hashes reales coinciden en todas las épocas compartidas. Las máscaras de backbone con p diferente no pueden ser idénticas; activaciones/BN/parada/scheduler pueden divergir por el tratamiento.


Duraciones incluyen actividad de escritorio y análisis CPU concurrente documentado. RSS de vida incluye importaciones/proceso; driver MPS incluye asignadores/cachés y es muestreado. No se suman como memorias independientes, ni equivalen a activaciones exclusivas, costo de inferencia o dispositivo móvil. Las estimaciones previas usaron el piloto C; no se entrenó un quinto brazo ni se cambió batch. Las curvas train con ruido se etiquetan como condiciones distintas: solo los MAE finales train/val en eval sin aumentaciones sustentan su comparación.



## Tests, trazabilidad e incidencias


Seis tests de protocolo pasaron con137 y con2026, más seis tests dirigidos de análisis. `verify.py` reejecutó scheduler/parada, selección por mínimo, contadores BN=132 actualizaciones/época, hashes/checkpoints finitos, identidad/targets, métricas desdeCSV y2592 máscaras. 3675 archivos protegidos sin cambios; 301 artefactos finales de C verificados. Split1051/263 sin solapamiento por fila/nombre/contenido SHA,1314 NPY contra auditoría histórica. Paridad CPU/MPS del checkpoint seleccionado comprobada sin reelección; no implica ONNX.


La verificación adicional `verify_aggregation.py` comprueba independientemente media, SD muestral, rango y deltas desde los CSV; evita cancelar signos en las guardas de sesgo. `aggregation_verification.json` conserva los resultados. La corrección gráfica registrada en `scatter_rendering_registration.json` incluye todos los puntos con ejes comunes; no cambia métricas ni criterios. `bundle_manifest_revision.json` corrige únicamente la inclusión de manifiestos anidados en los hashes finales. Versiones previas preservadas.


La primera preparación se detuvo antes de crear pesos porque Matplotlib había creado una carpeta seed137 solo con caché. Se comprobó su contenido y se completó el registro sin sobrescribir ni reiniciar entrenamientos; fuente original y registro de incidente quedan en `registration_completion.json` y `complete_registration.py`. Esto no consumió un entrenamiento. Registro/protocolo y hashes fueron previos al dispatch. Implementación posterior de análisis conserva su UTC/hash antes de ejecutar controles; el diseño ya estaba fijado.


Por brazo: `initial.pth`, `best.pth`, `final.pth`, configuración, entorno, fuentes, órdenes, historial JSONL/JSON, selección MPS y curva. Por evaluación:1051 train/263 val con identidad/target/predicción y métricas. `artifact_hashes.json` cubre artefactos finales excepto cachés y el propio manifiesto; `REPRODUCE.md` explica comandos y reutilización.



## Pendientes y cierre


Pendientes para una decisión de promoción: exportación/paridad y mediciones de costos ONNX/HTTP en fase posterior autorizada; evaluación realmente independiente/temporal; mecanismo de borde/fondo y validez física de explicaciones. Esta auditoría pequeña aporta evidencia reproducible, no prueba aprendizaje de física solar ni generalización. Ninguna comprobación pendiente se presenta como superada.


**FASE V3.2-D: CUMPLIDA.** Se obtuvo la evidencia controlada solicitada, incluidos resultados desfavorables. V3.1 y el producto aprobado permanecen intactos. Sin cambios de API, frontend, Agent Lab, gemelo, Unity/Needle, WebAR, Sol, arquitectura, preprocesamiento, target, datos o split. Sin dependencias nuevas, ONNX nuevo, commits, push ni publicación. No se comenzó otra fase.
