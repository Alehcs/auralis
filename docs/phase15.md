# Fase 1.5 — Reentrenamiento y validación limpia de Coronium V3

> Registro al cierre de Fase 1.5. Posteriormente, [Fase 1.6](phase16.md) promovió
> una copia exacta de `best.pth` como Coronium V3.1. Este run y sus manifests
> originales permanecen intactos; las referencias a «no promovido» describen
> el estado de esta fase, no la versión activa actual.

**FASE 1.5: CUMPLIDA.** Entrenamiento desde cero terminado en 50 épocas,
checkpoint seleccionado en la época 40 y evaluación limpia reproducida en dos
procesos con predicciones exactamente iguales. El nuevo checkpoint no está promovido.

Run: `auralis-back/experiments/phase15_runs/20260905T132456995672Z/`.
Los resultados históricos y el checkpoint servido por la API se mantienen intactos.

## Entregables

Todos los siguientes archivos están dentro del run indicado:

- `best.pth`: nuevo checkpoint seleccionado; `epochs/best_epoch_0040.pth`
  conserva los mismos tensores. SHA-256 de `best.pth`:
  `1e4c834451375a7c4a1f47bd60404bf9aec3bc20c18056c9fc1b517b168e8e51`.
- `initial.pth`, `final.pth`, `epochs/`: inicialización, estado final, métricas de
  las 50 épocas y copias de cada mejora de checkpoint.
- `evaluation_clean_v1/manifest.json`: cuatro métricas finales y procedencia.
- `evaluation_clean_v1/predictions.csv`: 263 predicciones con fila e identidad,
  target SI, predicción SI y error absoluto, sin redondeo de presentación.
- `evaluation_clean_v1/results_comparison.csv`: salida compatible del evaluador,
  separada del CSV histórico. `evaluation_clean_repeat_v1/` conserva la repetición.
- `manifest.json`, `phase15_protocol.json`, `environment.json`, `sources/`:
  configuración, split, hashes, entorno y código exacto del experimento.
- `history.json`, `learning_curve.png`, `preflight_tests.log`,
  `artifact_verification.json`, `verification.json`: evolución y comprobaciones.
- Los logs completos están junto al directorio del run, con su mismo nombre y
  sufijos `.training.log`, `.evaluation.log` y `.evaluation-repeat.log`.

## Métricas finales

| Métrica | Fase 1.5, validation limpio (263) | Histórico exp_005, contaminado (353 filas) |
| --- | ---: | ---: |
| MAE, puntos porcentuales SI | 0,10155762 | 0,1048 |
| RMSE, puntos porcentuales SI | 0,12337954 | 0,1272 |
| R² | 0,87529664 | 0,8634 |
| MAPE | 5,98702505 % | 6,07 % |

MAPE = 100 × media(|predicción − SI| / |SI|), excluyendo SI=0; las 263
observaciones tienen target distinto de cero, así que no se excluyó ninguna.
MAE/RMSE/R² se calcularon sobre las 263 observaciones, sin ponderarlas por lote.
La referencia constante ajustada sólo con el SI medio de train dio MAE 0,30440,
RMSE 0,34962 y R² −0,00135.

Las cifras históricas se muestran únicamente como referencia: cambiaron la
partición, las observaciones y el protocolo, y el split anterior contenía 145
magnetogramas compartidos. Esta tabla no demuestra una mejora causal respecto
al modelo anterior. No se combinaron las métricas ni sus archivos.

El MAE de selección en la época 40 fue 0,09670745. La evaluación final dio
0,10155762 al reiniciar la semilla de las máscaras MC Dropout; ambos valores
quedan registrados con su función distinta. No se escogió una semilla posterior
para mejorar el resultado.

## Protocolo fijado antes del entrenamiento

- Inicialización aleatoria desde cero, seed 42 en Python, NumPy, PyTorch y MPS.
- Algoritmos deterministas habilitados; 4 hilos CPU; entrenamiento en GPU Apple MPS.
- Input de Fase 1: clip400, polaridades B+/B−, float32 `(2,512,512)`.
- Target de Fase 1: porcentaje original de píxeles con |B LOS| > 200 G, sin log ni Z-score.
- Split exacto `models/split_indices_phase1_v1.json`: 1.051 train, 263 validation; overlap cero.
- Arquitectura CoroniumV3 intacta, 206.875 parámetros; dropout espacial 0,2 y dropout de cabeza 0,3.
- Aumentaciones intactas: flips y rotación ±10°; SI >2,0 usa flips/rot90.
- Batch 32, sin descartar el lote final, `num_workers=0`; sólo train se baraja.
- AdamW: LR inicial 0,001; weight decay 0,00001; betas=(0,9;0,999), eps=1e-8,
  amsgrad=False. Float32, sin precisión mixta.
- Weighted Huber: delta=1, alpha=2; medias de época ponderadas por número de muestras.
- Máximo 100 épocas. ReduceLROnPlateau sobre val WHL, modo min, factor 0,5,
  paciencia 3, min LR 1e-6, threshold=1e-4 relativo, cooldown=0, eps=1e-8.
- Parada temprana sobre val WHL, paciencia 10, min_delta=0; checkpoint elegido
  por mínimo MAE MC de validación. Terminó en época 50 con LR 0,00003125;
  la época elegida 40 usó LR 0,000125.
- MC Dropout T=20, BatchNorm congelado durante validación; evaluación final seed 42 y batch 32.
- Evaluación final repetida en otro proceso: predicciones y métricas idénticas.

Entorno fijado: Python 3.12.7, PyTorch 2.11.0, torchvision 0.26.0,
NumPy 1.26.4, pandas 3.0.2, scikit-learn 1.8.0, macOS 26.6.2 arm64.
No se actualizaron dependencias. No se cargaron pesos antiguos: 226 de las 263
observaciones limpias habían estado en el train antiguo, por lo que un ajuste
desde ese checkpoint habría invalidado esta evaluación.

El pipeline final es el mismo de Fase 1: magnetograma almacenado
`x=clip(resize(B_LOS),−400,400)/400` → función común de polaridades
`[max(x,0),max(−x,0)]` → CoroniumV3 → estimación del porcentaje SI original.
La inferencia evaluada promedia 20 pasadas MC; sus cifras no son métricas de
una pasada ONNX. SI no es log-SI, Z-score ni el número oficial de manchas solares.

## Corrección puntual necesaria

El promedio anterior de métricas de época daba igual peso a cada lote, incluido
el último de sólo 7 observaciones de validación. Caso comprobado: targets
[0,0,3], predicciones [0,0,0] y batch=2 daban MAE=1,5, cuando la media por
observación es 1. Se corrigió únicamente la agregación de train/validation.
La pérdida optimizada por lote, arquitectura, preprocesamiento y target no cambian.
Un test dirigido cubre este caso y otro exige detenerse ante valores no finitos.

## Verificaciones ejecutadas

Las 15 pruebas de Fases 1 y 1.5 aprobaron. Se volvieron a verificar los hashes
de los 1.314 arrays y los artefactos históricos, así como el split limpio.
Dos pasos de entrenamiento en MPS reiniciados con seed 42 dieron exactamente
el mismo estado de pesos. El límite de memoria MPS se fijó en el presupuesto
recomendado por PyTorch (ratio alto 1,0; ratio bajo 0,9) en el equipo de 24 GB.

Tras entrenar y antes de evaluar se comprobaron nuevamente los hashes y el
split: **1.051 train / 263 validation, intersección de observaciones = 0**.
Todos los arrays y artefactos históricos conservaron sus hashes.
`verify_phase15_results.py` verificó las identidades y targets exactos de
validation, el checkpoint seleccionado y su inicialización, la igualdad exacta
de ambas evaluaciones y las cuatro métricas recalculadas con sklearn/float64
(coinciden dentro del redondeo de float32). No hubo salidas no finitas.
La sintaxis Python y `git diff --check` pasaron. La curva generada se inspeccionó.
Su rótulo heredado «sunspot index units» corresponde a puntos porcentuales SI.

Comandos reproducibles, desde `auralis-back/`, usando rutas nuevas para evitar
sobrescribir experimentos (cada evaluación tarda aproximadamente dos minutos
en este equipo; no repetir entrenamiento sólo para consultar resultados):

```sh
export PYTHONHASHSEED=42
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=1.0
export PYTORCH_MPS_LOW_WATERMARK_RATIO=0.9
export MPLCONFIGDIR=/tmp/auralis-mpl
/Users/alejandro/.pyenv/versions/3.12.7/bin/python3 -u scripts/run_phase15.py --train-run experiments/phase15_runs/NUEVO_ID
/Users/alejandro/.pyenv/versions/3.12.7/bin/python3 -u scripts/run_phase15.py --evaluate-run experiments/phase15_runs/NUEVO_ID --output-dir experiments/phase15_runs/NUEVO_ID/evaluation_clean_v1
/Users/alejandro/.pyenv/versions/3.12.7/bin/python3 -u scripts/run_phase15.py --evaluate-run experiments/phase15_runs/NUEVO_ID --output-dir experiments/phase15_runs/NUEVO_ID/evaluation_clean_repeat_v1
/Users/alejandro/.pyenv/versions/3.12.7/bin/python3 scripts/verify_phase15_results.py --run-dir experiments/phase15_runs/NUEVO_ID --evaluation experiments/phase15_runs/NUEVO_ID/evaluation_clean_v1 --repeat experiments/phase15_runs/NUEVO_ID/evaluation_clean_repeat_v1
```

## Archivos de código/documentación de esta fase

| Archivo | Motivo |
| --- | --- |
| `auralis-back/src/models/train_model.py` | Agregación por muestra, rechazo de pérdidas no finitas, directorio nuevo y procedencia/artefactos por época. |
| `auralis-back/scripts/evaluate_final.py` | Validar hashes del run/datos, conservar identidades y predicciones completas, métricas y protocolo en manifest. |
| `auralis-back/scripts/run_phase15.py` (nuevo) | Entrada reproducible con seed, determinismo, preservación y copias del código. |
| `auralis-back/scripts/verify_phase15_results.py` (nuevo) | Contraste independiente de métricas, predicciones, split y checkpoint. |
| `auralis-back/tests/test_phase15.py` (nuevo) | Dos tests pequeños para agregación del último lote y rechazo de valores no finitos. |
| `docs/phase15.md`, `AGENTS.md` | Informe y contexto actualizado del experimento no promovido. |

Las versiones de entrenamiento/evaluación anteriores a esta fase se conservaron
también dentro del run como `phase1_train_model_before.py` y `phase1_evaluate_before.py`.
Los demás cambios ya presentes en el workspace pertenecen a Fase 1 o al usuario.
No se modificó frontend/API ni funcionalidades de Unity, WebAR, Agent Lab o
simulación en Fase 1.5; no se requirió recompilar frontend por estos cambios.

## Alcance científico

Validation se usó para seleccionar checkpoint y parada temprana. Las métricas
son válidas para esa validación sin observaciones compartidas, pero no
constituyen un test independiente de la selección ni validación temporal;
observaciones de fechas cercanas pueden seguir correlacionadas.
La reproducibilidad se comprobó en este entorno mediante pasos de entrenamiento
reiniciados y dos evaluaciones completas, sin duplicar las 50 épocas del run.
No se afirma igualdad bit a bit entre otros dispositivos o versiones.

No quedaron bloqueos para el objetivo de Fase 1.5. Se corrigió el defecto puntual
de agregación demostrado antes de entrenar. No se generaliza el resultado a
forecasting, clases GOES ni confianza calibrada. La procedencia y limitaciones
de los datos siguen siendo las documentadas en Fase 1.

El nuevo checkpoint es utilizable para investigación bajo este contrato y
protocolo. La API mantiene el checkpoint/ONNX histórico; promover o exportar el
nuevo modelo requiere una acción posterior explícita. No se inició ninguna fase posterior.
