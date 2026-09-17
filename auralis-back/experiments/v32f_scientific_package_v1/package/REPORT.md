# FASE V3.2-F — Paquete científico

**Coronium V3.2 — candidatos. V3.1 sigue activa. Ninguna semilla seleccionada ni modelo promovido.**

## Entrega y alcance

26 figuras en PNG 300 dpi, SVG y PDF; 25 tablas CSV; índice de fuentes/hashes,
comandos de regeneración, revisión visual y verificaciones. Todo se generó desde
resultados conservados. No se importó PyTorch/ONNX Runtime ni se ejecutaron
inferencias, entrenamientos, exportaciones, benchmarks o nuevos barridos XAI.

[Índice completo](INDEX.md) · [fuentes y hashes](sources.json) · [tablas](tables/metrics.csv).
El script reutiliza mediante AST las funciones puras `metrics` y `protected` de B,
`save_figure` de `plot_final_scatter.py` y las primitivas de diagramación existentes.
No ejecuta los entrypoints de Fase1.7, que incluyen mediciones/inferencia.

## Auditoría y reutilización

[Inventario inicial](tables/inventory.csv) clasifica cada archivo de B–E.2 y los
scripts/figuras de Fase1.7. Se reutilizan predicciones C/D, curvas JSONL, manifiestos,
paridad E/E1, registros individuales E/E1/E2 y 81 arrays Grad-CAM de D. Se adaptan
etiquetas/rutas y presentación mediante wrapper aislado. Las figuras antiguas
V3.1 y resultados exp005 contaminados no se mezclan con candidatos. Los snapshots,
reproducciones repetidas y renderizados preliminares quedan como evidencia
histórica/redundante; D sustituye el procedimiento preliminar de oclusión de C
para las comparaciones principales, sin borrar C. C2 sigue siendo seed42 preliminar.

No se copian ni se sobrescriben gráficos públicos. El paquete no es un release
de servicio. Faltan test temporal independiente, HTTP con mitigación, replicación
C2 en tres semillas, costos ONNX C0/C2 y rendimiento móvil físico; se señalan como
faltantes, sin generarlos en esta fase.

## Métricas y definición estadística

Float64 sobre predicciones guardadas, sin redondeo de presentación. Residuo =
predicción − SI. MAE/RMSE/sesgo/p95 se expresan en **SI percentage points**, MAPE
en porcentaje, R² sin unidades. p95: cuantil lineal del error absoluto. MAPE
excluye targets cero (no los hay aquí); R² utiliza la media del grupo evaluado.

1.051 observaciones train y 263 validation, sin solapamiento de identidades;
orden, nombres y targets comprobados. Validation se utilizó para selección de
checkpoint/early stopping: no es test independiente ni temporal. Baja n=43,
media n=96, alta n=124; cola SI>2 n=71, **subconjunto de alta**. En train:181/380/490,
cola 286. El mismo conjunto repetido entre semillas no genera789 casos independientes.

### Validation determinista CPU y referencias

| model | n | mae | rmse | r2 | mape | bias | p95_absolute_error |
|---|---|---|---|---|---|---|---|
| V3.1 | 263 | 0.204083 | 0.258233 | 0.453720 | 10.497507 | -0.186877 | 0.487845 |
| constant | 263 | 0.304404 | 0.349620 | -0.001348 | 17.887177 | 0.012828 | 0.591570 |
| strong_raw | 263 | 1.522976 | 1.532148 | -18.230629 | 88.451411 | -1.522976 | 1.822476 |
| strong_affine_train | 263 | 0.113250 | 0.136335 | 0.847733 | 6.646445 | 0.024066 | 0.251355 |
| initial_s42 | 263 | 1.726987 | 1.761651 | -24.423267 | 98.331392 | -1.726987 | 2.328941 |
| initial_s137 | 263 | 1.674809 | 1.710790 | -22.976472 | 95.229295 | -1.674809 | 2.278734 |
| initial_s2026 | 263 | 1.672777 | 1.708433 | -22.910444 | 95.129422 | -1.672777 | 2.274150 |
| C0_s42 | 263 | 0.157275 | 0.200928 | 0.669270 | 8.234291 | -0.129664 | 0.395529 |
| C0_s137 | 263 | 0.119257 | 0.142129 | 0.834515 | 7.245099 | 0.014180 | 0.263434 |
| C0_s2026 | 263 | 0.139347 | 0.174612 | 0.750229 | 7.474151 | -0.094607 | 0.343204 |
| C1_s42 | 263 | 0.048335 | 0.059056 | 0.971429 | 2.908951 | 0.013242 | 0.109745 |
| C1_s137 | 263 | 0.054007 | 0.068193 | 0.961904 | 3.164928 | -0.001931 | 0.126519 |
| C1_s2026 | 263 | 0.051862 | 0.064623 | 0.965789 | 3.087453 | 0.003185 | 0.122804 |
| C2_s42 | 263 | 0.093997 | 0.116039 | 0.889694 | 5.548944 | -0.006168 | 0.222232 |

Constante: media de train. Referencia cruda: fracción de píxeles |NPY|>0,5 tras
resize, no el target original previo al resize. Referencia afín calibrada únicamente
sobre train, sin recalibración en F. Inicializaciones son controles sin entrenar.
C2 es experimento preliminar de seed42, no estabilidad de tres semillas.

### Agregación entre semillas (métricas, sin ensemble)

| configuration | metric | mean | sample_sd | minimum | maximum |
|---|---|---|---|---|---|
| C0 | mae | 0.138626 | 0.019019 | 0.119257 | 0.157275 |
| C0 | rmse | 0.172557 | 0.029453 | 0.142129 | 0.200928 |
| C0 | r2 | 0.751338 | 0.082628 | 0.669270 | 0.834515 |
| C0 | mape | 7.651180 | 0.517813 | 7.245099 | 8.234291 |
| C0 | bias | -0.070030 | 0.075005 | -0.129664 | 0.014180 |
| C0 | p95_absolute_error | 0.334056 | 0.066521 | 0.263434 | 0.395529 |
| C1 | mae | 0.051401 | 0.002864 | 0.048335 | 0.054007 |
| C1 | rmse | 0.063958 | 0.004605 | 0.059056 | 0.068193 |
| C1 | r2 | 0.966374 | 0.004789 | 0.961904 | 0.971429 |
| C1 | mape | 3.053777 | 0.131269 | 2.908951 | 3.164928 |
| C1 | bias | 0.004832 | 0.007719 | -0.001931 | 0.013242 |
| C1 | p95_absolute_error | 0.119689 | 0.008810 | 0.109745 | 0.126519 |

Desviación muestral ddof=1. La media resume las tres métricas, no corresponde a
un cuarto modelo ni a predicciones promediadas. CSV conserva también train,
bandas y cola para cada semilla y sus agregados.

### Resultado desfavorable: baja actividad

| model | mae | r2 | bias | p95_absolute_error |
|---|---|---|---|---|
| V3.1 | 0.051748 | -0.529200 | 0.043637 | 0.116598 |
| C1_s42 | 0.058251 | -0.616571 | 0.056837 | 0.107053 |
| C1_s137 | 0.058415 | -0.683266 | 0.057385 | 0.114773 |
| C1_s2026 | 0.057438 | -0.669874 | 0.054877 | 0.113008 |

C1 mejora el error global pero empeora el MAE bajo respecto a V3.1, dentro del
margen tolerado registrado en D. Los R² bajos negativos permanecen explícitos;
no se convierten en porcentajes de acierto. La mayor equivocación de cada C1
aparece en la misma observación row161, visible con los tres mayores errores por
semilla. La tabla conserva los diez peores casos de cada modelo/control.

Train/validation deterministas están en figura08/tablas. Las curvas de figura01
usan train con aumentaciones/dropout y validation eval MPS batch8: esa distancia
no se interpreta como una comparación de generalización a igualdad de protocolo.

### V3.1 MC20: contexto separado

| model | n | mae | rmse | r2 | mape | bias | p95_absolute_error |
|---|---|---|---|---|---|---|---|
| V3.1_MC20 | 263 | 0.101558 | 0.123380 | 0.875297 | 5.987026 | 0.000968 | 0.232278 |

MPS batch32, MC Dropout T20. No se mezcla con CPU determinista ni con diagnóstico
de ruido de entrada HTTP. B conserva además un diagnóstico mecanístico sobre 18
muestras (seis por banda); no se extrapola a las 263 ni se combina con MC20 oficial.
La menor MAE al activar backbone dropout localiza una ruta, no demuestra por sí
sola qué componente BN/ECA/no linealidad causa la diferencia.

## Paridad y trazabilidad

[Artefactos C1](tables/candidate_artifacts.csv) relaciona semillas 42/137/2026 con
épocas 27/60/55, checkpoints, ONNX y SHA-256. No se cambia de época. Paridad por
observación y resumen conserva los cuatro modelos, runtime original y mitigado:
**0 excesos** de `|ONNX−PT| <= 1e-5 + 1e-5*|PT|` en 263 casos por combinación.
Un máximo absoluto >1e-5 puede cumplir la tolerancia combinada. Son valores
completos, distintos de respuestas HTTP redondeadas a cuatro decimales.
[ONNX metrics](tables/onnx_metrics.csv) conserva pequeñas diferencias de kernels;
no reemplaza silenciosamente las métricas PyTorch C/D.

## Eficiencia: cohortes y efectos separados

Apple M5, 24 GiB, CPU FP32, batch 1, 4 hilos intra/1 inter, ORT 1.25.1; PyTorch permanece
residente. RSS es del proceso (bibliotecas, modelos, entradas, temporales y cachés),
no memoria exclusiva de pesos. ONNX autocontenido 835.234 bytes; 206.875 parámetros.
Pesos de servicio V3.1 = 1.683.503 bytes; C1 = 1.681.327 bytes. Dependencias/metadatos se
necesitan aparte; logs de investigación no son pesos. Tamaño<=+10% y parámetros
<512000 cumplen. Las figuras/tablas conservan todas las rondas.

- **E original:** s137/s2026 incumplen RSS; no se declaran corregidos bajo default.
- **E.1 original y mitigado:** causa documentada en caché nativa de KleidiAI;
  única mitigación `mlas.disable_kleidiai=1`, aplicada a referencia y candidatos.
  RSS mitigado pasa en dos rondas; s42/s137 pasan latencias; s2026 p95 quedó
  inconcluso. E usa pico muestreado; E1 usa máximo conservador externo/interno/
  lifetime. Se preservan definiciones, componentes y etapas, sin sumarlas.
- **E.2:** cuatro rondas, cuatro brazos,216 mediciones por recorrido y 10 calentamientos;
  6.912 tiempos, procesos nuevos. Solo forward/preparación+forward. Modelo mitigado
  C1_s2026 vs V3.1 mitigado pasa en las cuatro rondas; el máximo incremento p95
  es 2,6642% / 3,0816%. Mitigación mejora la velocidad de ambos; cambio completo
  C1 mitigado vs V3.1 original también pasa. La comparación original de modelos
  conserva p95 inconcluso. E2 resuelve esos recorridos mitigados, no revalida HTTP.

[Latencias individuales](tables/latency_individual.csv), [p50/p95](tables/latency_summary.csv),
[guardas por ronda](tables/cost_guards_by_round.csv), [comparaciones E2](tables/e2_comparisons.csv)
y [dictámenes E2](tables/e2_verdicts.csv) mantienen contextos diferenciados. Las
alertas de actividad de sistema de E2 permanecen en `analysis.json`/
`system_conditions.csv` originales; no se eliminan rondas ni se atribuye una
causa externa sin evidencia. No hubo nuevos benchmarks en F.

**HTTP E:** dos rondas, original runtime; 20 pasadas de ruido + determinista frente
a determinista solo. Cache fría se refiere al resultado: modelo, filesystem y
conexión permanecen calientes. Cache caliente no ejecuta forwards. La predicción
sin redondear y la pública redondeada coinciden entre modos según los registros
originales; sin diagnóstico es “no calculado” (`null`), nunca cero. El ahorro al
omitir ruido es otra intervención y no compensa una guarda de costo del modelo.
No hay medida HTTP mitigada. Tiempos del Mac no certifican móviles.

## XAI y arquitectura

Arquitectura C1: misma topología residual/ECA, backbone dropout 0 y cabeza 0,3;
eval desactiva dropout y congela BN. No se sugiere una red estructuralmente nueva.

Nueve paneles XAI contienen todos los 81 mapas de D:3 configuraciones × 3 semillas ×
9 observaciones fijas. HMI[-1,1], CAM[0,1], origin upper, nearest, sin volteos,
renormalización ni cambio de muestras. La figura de oclusión usa los 2.592 registros
originales y 162 comparaciones guiada/aleatoria, con 15 controles por máscara guiada.
Se comprueba de nuevo la diferencia entre perturbación guiada y media aleatoria.

Los mapas de inicializaciones también muestran estructura; retirar más magnitud
magnética confunde la interpretación de caída de predicción. Mapas brillantes o
caídas mayores no prueban causalidad física, localización válida ni “aprendizaje
correcto”. Las dudas sobre borde/fondo permanecen abiertas.

## Guía para tesis y presentación

- **Tesis, cuerpo:** figuras 01/02/04/06/07/08/10/11/13/16; tablas de métricas,
  semillas, guardas y artefactos. Mantener 03 como contexto metodológico separado.
- **Tesis, evidencia complementaria:**05 referencias completas,09 casos adversos,
  12 banco E1,14 HTTP original,15 pesos, los nueve paneles 17 y 18 oclusiones con controles.
- **Diapositivas:**02 estabilidad,07 bandas,11 memoria,13 efectos runtime/modelo y 16 red.
  Para XAI usar el conjunto de paneles 17 y 18 o explicar explícitamente qué panel
  fijo se muestra; no elegirlo por apariencia favorable.
- Preferir SVG/PDF para texto/vector. Los mapas mantienen arrays raster originales
  incrustados; PNG 300 dpi disponible. Usar leyendas y límites del índice como pie.

## Verificaciones, discrepancias y cierre

4.943 archivos protegidos permanecen idénticos. Se verificaron 1.537 entradas de
manifiestos previos C–E2 sin discrepancias. Recalcular métricas C/D produce
máxima diferencia 0 con sus JSON; no se sobrescribió evidencia anterior. Cuantiles
recalculados desde tiempos individuales, ratios E2 comprobados, orden/targets/
identidades/splits y ddof=1 verificados. Las 26 figuras fueron inspeccionadas en
hojas de contacto: sin etiquetas cortadas ni puntos fuera del encuadre; las
escalas XAI conservan el método original. CSV sin redondeo; etiquetas sí redondean.

[Verificación](verification.json), [pruebas adicionales](additional_checks.json),
[revisión visual](visual_review.json), [discrepancias](discrepancies.json) y manifiesto
completan la trazabilidad. Fuentes previas permanecen en sus rutas, no se copian
pesos grandes al paquete. El manifiesto vincula esos archivos mediante hashes.

**Recomendación:** usar este paquete científico para tesis y revisión de una
posible integración posterior. No implica aprobar al candidato, elegir semilla,
aplicar mitigación al producto ni resolver las limitaciones científicas/XAI.

**FASE V3.2-F: CUMPLIDA.** V3.1 sigue activa y el producto aprobado permanece
intacto. No se inicia otra fase.
