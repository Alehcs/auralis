# Fase 1.6 — Promoción controlada de Coronium V3.1

**FASE 1.6: CUMPLIDA.** Coronium V3.1 es el modelo activo de la API y de las
utilidades mantenidas de inferencia/Grad-CAM. Se promovió una copia exacta del
`best.pth` de Fase 1.5, sin reentrenar ni cambiar arquitectura o preprocesamiento.
Coronium V3 y el run original permanecen intactos. No se inició otra fase.

Promoción registrada: 2026-09-06 03:00 UTC (2026-09-05 en Santiago).

## Artefactos y procedencia

Rutas relativas a `auralis-back/`:

| Artefacto | Función |
| --- | --- |
| `models/best_coronium_v3_1.pth` | Checkpoint oficial, copia binaria de Fase 1.5 best.pth, época 40. |
| `models/best_coronium_v3_1.onnx` | Exportación eval-mode, opset 18, batch dinámico, 835.234 bytes autocontenidos. |
| `models/coronium_v3_1_manifest.json` | Origen, contratos, entorno, hashes de fuentes/artefactos y paridad de exportación. |
| `models/coronium_v3_1_metrics.json` | Métricas oficiales MC, deterministas de servicio y V3 histórico en bloques separados. |
| `experiments/phase16_coronium_v3_1.json` | Registro visible en el historial de experimentos, con alcance científico explícito. |
| `reports/phase16_coronium_v3_1/coronium_v3_1_mc_predictions.csv` | Copia exacta de las 263 predicciones MC de Fase 1.5. |
| `reports/phase16_coronium_v3_1/coronium_v3_1_mc_results_comparison.csv` | Copia versionada del scatter MC limpio, ahora servido por la API. |
| `reports/phase16_coronium_v3_1/coronium_v3_1_deterministic_predictions.csv` | Las mismas 263 identidades/targets con predicciones PyTorch CPU y ONNX. |

Origen: `experiments/phase15_runs/20260905T132456995672Z/best.pth`.
El run original conserva sus manifests `completed_unpromoted`: describen su
estado al cierre de Fase 1.5. El nuevo manifest registra la promoción posterior.

SHA-256 del checkpoint origen y copia V3.1:
`1e4c834451375a7c4a1f47bd60404bf9aec3bc20c18056c9fc1b517b168e8e51`.

SHA-256 del nuevo ONNX:
`f09b1dc470634d880eedc1fb9009c5af359152721b02c69c171b04758f0b48aa`.

El modelo conserva 206.875 parámetros y la clase Python `CoroniumV3`: V3.1 es
una versión de pesos/contrato de servicio, no una arquitectura nueva. El grafo
incluye los pesos; no depende del `.onnx.data` histórico de V3.

## Métricas oficiales V3.1 y métricas del servicio

| Métrica | Oficial V3.1 MC Dropout | V3.1 ONNX determinista | V3 histórico, contaminado |
| --- | ---: | ---: | ---: |
| MAE, puntos porcentuales SI | 0,10155762 | 0,20408340 | 0,1048 |
| RMSE, puntos porcentuales SI | 0,12337954 | 0,25823317 | 0,1272 |
| R² | 0,87529664 | 0,45371922 | 0,8634 |
| MAPE | 5,98702505 % | 10,49751499 % | 6,07 % |

Las métricas oficiales V3.1 son las de Fase 1.5, sin recalcular con otra semilla:
MC Dropout T=20, seed 42, batch 32, MPS. Se comprobó su consistencia con las
predicciones guardadas mediante sklearn/float64; diferencias sólo de redondeo
float32, tolerancia `atol=2e-6, rtol=1e-6`.

Ambos protocolos V3.1 usan las mismas **263 observaciones** del split limpio
(1.051 train / 263 validation), sin solapamiento. Validation se usó para selección
de checkpoint y parada temprana: no es test independiente ni validación temporal.

**La pasada determinista rinde peor que MC Dropout.** La promoción no oculta
esta diferencia ni presenta el MAE MC como rendimiento de ONNX. Las métricas
ONNX se calcularon antes del redondeo HTTP. PyTorch CPU determinista obtuvo
MAE 0,20408324, RMSE 0,25823297, R² 0,45372009 y MAPE 10,49750713 %.
La equivalencia numérica descarta un desajuste de exportación en las muestras
comprobadas; no se investigó ni cambió la arquitectura para cerrar esa brecha.

V3 histórico conserva sus 353 filas de evaluación, con 145 observaciones
compartidas entre train/validation. No es referencia válida de generalización,
ni una comparación causal con V3.1.

## Cambios necesarios

- `src/models/active_model.py` identifica los artefactos activos. Antes de servir,
  la API verifica hashes de checkpoint, ONNX, métricas y scatter para rechazar
  una mezcla de versiones. No hay fallback a V3.
- `src/api/main.py` carga V3.1 para ONNX y Grad-CAM; `/health` informa modelo,
  versión y nombres de artefactos. La versión de API es 3.1.0.
- Predicción por archivo, alias dual y upload devuelven una pasada ONNX
  determinista sin ruido, redondeada a cuatro decimales. El ruido sintético de
  20 pasadas permanece únicamente como diagnóstico separado de sensibilidad.
  Confianza, dispersión y bandas C/M/X continúan explícitamente heurísticas;
  las bandas históricas no se presentan como calibradas para V3.1 o clases GOES.
- `/api/stats` expone MC oficial, protocolo determinista e histórico V3 por
  separado. `/api/results-comparison` muestra las 263 muestras MC de V3.1.
  `/api/benchmark` conserva los valores originales y etiqueta V3 como histórico.
- `scripts/predict.py`, `explain_model.py` y `plot_gradcam_overlay.py` usan
  V3.1 y nombres de figuras versionados. Se añadió el helper de selección de
  dispositivo que el CLI FITS llamaba pero no definía.
- `scripts/export_to_onnx.py` usa V3.1, exporta un grafo autocontenido y rechaza
  sobrescribir grafos o sidecars existentes. `promote_coronium_v3_1.py` reproduce
  la creación de la release y escribe su manifest al finalizar las verificaciones.
- Frontend: referencias del modelo activo, tipos de respuesta, métricas MC,
  scatter y aviso de la diferencia con API determinista. Sin cambios de rutas.
- README, notas del backend, contexto AGENTS y este informe reflejan la release.
  El informe Fase 1.5 incorpora una nota de estado posterior sin modificar el run.
- `.gitignore` permite versionar los dos nuevos binarios pequeños y los logs de
  verificación de esta fase, conservando las excepciones de V3.

El input continúa siendo `hmi-clip400-polarity-v1`: `(512,512)` float32
`clip(resize(B_LOS),−400,400)/400` → `[max(x,0),max(−x,0)]` `(2,512,512)`.
No hay log ni Z-score. Target: porcentaje original de píxeles con
`abs(B_LOS)>200 G`, contrato `strong-field-pixel-percent-200G-v1`.

## Verificaciones y evidencia

Todo el registro está en `reports/phase16_coronium_v3_1/`:

- `promotion.log`, manifest y CSV determinista: ONNX checker aprobado y paridad
  PyTorch CPU/ONNX en **263/263** observaciones; diferencia absoluta máxima
  **1,1920929×10⁻⁶**, dentro de `atol=rtol=1e-5`. Batch dinámico de tamaño 2 aprobado.
- `verification.json`: HTTP mediante TestClient con lifespan y modelos reales;
  11 muestras seleccionadas por nueve cuantiles de target más extremos temporales.
  Archivo/alias/upload/caché iguales; stats, scatter y benchmark coherentes.
- `verification-mps.json`: repetición con PyTorch residente en MPS. Diferencia
  máxima CPU/MPS **2,3841858×10⁻⁷**. Diferencia máxima PyTorch/HTTP
  **4,6682358×10⁻⁵**, explicada por redondeo HTTP a cuatro decimales.
- `live-http.json`: Uvicorn real en `127.0.0.1:8000`, `/health` confirma V3.1,
  PyTorch MPS y ONNX cargados; predicción V3.1 y experimento registrado.
- `tests-final.log`: **18 tests aprobados** de Fases 1, 1.5 y 1.6. Incluyen
  igualdad de preprocesamiento sobre los 1.314 arrays, hashes científicos,
  rechazo de inputs inválidos, Grad-CAM, guardas de release y no sobrescritura.
- `frontend-build-final.log`: `npm run build` aprobado. Advertencia de Vite por
  chunks mayores de 500 kB; no impide el build y no se inició un refactor.
- Sintaxis Python y `git diff --check` aprobados. `completion.json` registra
  el cierre y las modificaciones respecto del workspace encontrado al inicio.

El primer intento de tests necesitó reubicar SUNPY_CONFIGDIR en `/tmp` por
restricciones del sandbox; la repetición completa pasó. Uvicorn cargó los
artefactos dentro del sandbox, pero éste impidió abrir el puerto. El arranque
local autorizado fuera del sandbox y su comprobación HTTP sí pasaron. Se
conservaron ambos logs, sin borrar los intentos iniciales.

## Preservación y alcance

`preserved_before.json` y las verificaciones confirman **127 artefactos previos
sin cambios**, incluidos checkpoint/ONNX/sidecar V3, scaler, split histórico,
resultados históricos y el run completo Fase 1.5. Los tests confirman además
los hashes originales de los 1.314 `.npy`.

`workspace_before.json` permite distinguir los cambios de esta fase de los
cambios del usuario/Fases 1 y 1.5 que ya estaban sin commit. **26 archivos** de
Unity/WebAR/timeline/Agent Lab/simulación o gemelo digital identificados en el
workspace permanecieron sin cambios respecto de ese inicio. No se modificaron
sus módulos ni se hicieron refactors generales. Se trabajó en `main`.

## Reproducción y pendientes

Desde `auralis-back/`, con las dependencias ya instaladas:

```sh
export SUNPY_CONFIGDIR=/tmp/auralis-sunpy
export MPLCONFIGDIR=/tmp/auralis-mpl
/Users/alejandro/.pyenv/versions/3.12.7/bin/python3 -m unittest discover -s tests -v
/Users/alejandro/.pyenv/versions/3.12.7/bin/python3 scripts/verify_phase16.py --output reports/phase16_coronium_v3_1/verification_NUEVA.json
```

Para acceder a MPS, ejecutar fuera del sandbox. Desde `auralis-front/`:
`npm run build`. La API arranca con `uvicorn src.api.main:app --host 127.0.0.1 --port 8000`.
El promotor es una operación de creación única: rechaza una release existente;
para verificarla se usa `verify_phase16.py`, sin reexportar ni reentrenar.

No hay pendientes bloqueantes de promoción. Quedan como limitaciones registradas
la brecha MC/determinista, la falta de un test independiente/temporal y la
calibración no realizada de confianza/bandas. No se abrió una fase para
resolverlas, no se publicó fuera de localhost y no se creó commit.
