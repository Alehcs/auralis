# Fase 1 — Contrato científico y trazabilidad de Coronium V3

Fecha: 2026-09-04 (America/Santiago). Repositorio auditado desde `c2a91e56`,
en `main`, sin entrenamiento prolongado, cambio de dependencias ni promoción
de nuevos pesos. Este documento corrige las afirmaciones incompatibles del
dossier y de documentación anterior; no modifica los resultados históricos.

**FASE 1: CUMPLIDA respecto de sus criterios de base, separación y trazabilidad.**
**No se ha obtenido todavía un modelo reentrenado ni una validación independiente.**

## Evidencia y conclusión sobre input / target

La auditoría reproducible está en
[`evidence.json`](../auralis-back/reports/phase1_v1/evidence.json).

| Comprobación local | Resultado |
| --- | --- |
| CSV | 1.763 filas, 1.314 identidades de archivo |
| Archivos `.npy` | 1.314 contenidos SHA-256 distintos; todos `(512,512)`, `float32`, valores en `[-1,1]` |
| Duplicados | Coinciden todos los campos, incluidos fecha y target |
| Estadísticas CSV/arrays | Media de cada archivo coincide con su fila; ninguna discrepancia |
| Cobertura local real | 2016-02-03 a 2026-04-12, según nombres/CSV; no 2011–2025 |
| Target | Mín. 1,2203633785; máx. 2,9787540436; media 1,7731646347 |
| Conteo original | Para cada target, `SI × 4096² / 100` es entero, con error máximo `5,83e-11` |
| Reporte preservado | Sus 353 `Real_SSN` coinciden con el target del split antiguo, diferencia máxima `6,16e-7` por redondeo/float32 |
| Métricas recalculadas desde ese reporte | MAE 0,1048064; RMSE 0,1272248; R² 0,8634007 |

`src/ingestion/massive_ingest_pipeline.py::process_magnetogram` contiene la
fórmula que explica la representación local: NaN→0, resize con antialias,
recorte ±400 y división por 400. Su esquema CSV es el observado, incluyendo
`min_value`, `max_value` y `mean_value`. El productor log/Z-score tenía otro
esquema, canales distintos y `sunspot_index_raw`, ausente del CSV local.

`SolarDataset.__getitem__` consume `sunspot_index` directamente y descompone
el array de un canal sin logaritmo. Esto también está presente en el commit
histórico `e1810a77`, que incorpora V3 PRO/ExtremeAugmentation. La salida de
la red es una regresión escalar lineal; no incluye exp, log o inversa Z-score.

El checkpoint contiene únicamente un `state_dict`, sin manifiesto de su
entrenamiento. Por ello no existe una prueba criptográfica retrospectiva del
CSV exacto usado al entrenar. Sin embargo, la concordancia entre productor,
CSV, código histórico, reporte y pesos aporta evidencia convergente suficiente
para establecer **SI crudo**, sin aplicar una transformación nueva a los targets.

El [diagnóstico del checkpoint](../auralis-back/reports/phase1_v1/checkpoint_diagnostic.json)
registra 16 filas equiespaciadas, inferencia CPU determinista sin dropout:
MAE contra SI crudo **0,13579**, contra `ln(SI)` **1,07013**, contra `log1p(SI)`
**0,60676**, contra Z-score con el scaler preservado **1,71000**. Es evidencia
auxiliar de escala, **no una nueva métrica de validación**. El scaler tiene
media 1,7657536713 y desviación 0,3462355473, distintas de las del CSV actual;
no tiene vínculo de procedencia suficiente con estos pesos y **no se aplica**.

## Pipeline establecido

1. FITS HMI LOS: matriz original `B`, expresada en G según el productor;
   sustituir NaN por cero según el código histórico.
2. Target, **antes de resize**:
   `SI = 100 × count(|B| > 200 G) / B.size`.
   Es porcentaje de píxeles de la imagen original completa (4096² aquí),
   incluidos los píxeles fuera del disco puestos a cero en el denominador.
   No es SSN internacional, conteo de manchas, clase GOES, fracción corregida
   del área solar ni predicción de actividad futura.
3. Entrada: resize a 512² con `mode='reflect'`, `anti_aliasing=True`,
   `preserve_range=True`; NaN→0; `x = clip(B_resized,-400,400)/400`.
   El `.npy` actual guarda `x`, un canal adimensional, no G ni log(B).
4. Función común `prepare_model_input`: `[max(x,0), max(-x,0)]`,
   tensor `float32` contiguo `(2,512,512)`. B+ representa la polaridad positiva;
   B− la **magnitud positiva** de la polaridad negativa. No son HMI y AIA.
5. Entrenamiento: aumentaciones históricas solamente en train; validación/API
   no las aplican. La red aprende directamente SI en porcentaje de píxeles.
6. PyTorch/ONNX: escalar en la misma escala de SI. MAE y RMSE se expresan en
   **puntos porcentuales de SI**, no log-SI. No se aplica log ni Z-score al target.

Los arrays ya descompuestos son compatibles únicamente si usan esa escala
clip400. Se rechazan formas incorrectas, NaN/infinito, amplitudes fuera de
rango y canales de polaridades inválidos. El rango por sí solo no demuestra
la procedencia de un upload: quien lo suministra debe cumplir este contrato.
Los tensores log del builder Kaggle son otra representación experimental;
no se ejecutó ni se promovió ese pipeline.

`/api/predict`, `/api/predict-dual` y `/api/predict-upload` conservan su protocolo
de compatibilidad: media de 20 pasadas ONNX con ruido gaussiano artificial
σ=0,005 y seed=42, en unidades de entrada clip400. El número `sunspot_index`
es esa media en escala de SI; `uncertainty` es su desviación, un diagnóstico
de sensibilidad. No es MC Dropout ni incertidumbre calibrada del instrumento.
La API ahora explicita contratos, unidades y condición histórica de los pesos.

## Split corregido y conservación

[`split_indices_phase1_v1.json`](../auralis-back/models/split_indices_phase1_v1.json):
**1.051 train / 263 validation, intersección de observaciones = 0**, seed 42.

Agrupar duplicados preservando todas las filas habría eliminado la fuga,
pero habría dado más peso a observaciones repetidas tanto al optimizar como
al evaluar. Al coincidir todos sus metadatos, conservar una fila por archivo
es más justificable para este dataset. Se escoge la primera fila de cada
observación y se separan sus índices originales 80/20 con `random_state=42`.
No se deduplican ni se reescriben físicamente CSV o `.npy`.

El manifiesto conserva todos los índices originales por identidad y hashes
del CSV/split antiguo. Rechaza metadatos duplicados contradictorios, índices
inválidos, solapamiento o cambios del CSV. La auditoría también verifica que
no haya dos nombres distintos con el mismo contenido binario.

El split antiguo permanece **sin cambios**: 145 archivos compartidos y
157 de 353 filas de validación filtradas desde train. Sus métricas son
históricas y contaminadas. **226 de las 263 observaciones de la validación
nueva ya estaban en el train antiguo**: evaluar los pesos promovidos con el
split nuevo no elimina esa contaminación.

El entrenamiento por defecto usa el split corregido, comprueba los hashes
de los arrays y reserva una carpeta nueva en `experiments/phase1_runs/` para
pesos, curva, historial y manifiesto. La evaluación de un run nuevo exige
que coincidan hashes de checkpoint/split y contratos. La reproducción vieja
requiere `--legacy-reproduction`. Ambas escriben en directorios nuevos;
no reemplazan el reporte que consume actualmente el dashboard. Los baselines
futuros usan el mismo split corregido y una carpeta separada.

## Fechas y elementos demostrativos

Los nombres codifican un tiempo de registro **TAI**. La API conserva
`date_original`, `date_scale='TAI'` y `date_source='filename_record_time'`;
`date`/`date_utc` contienen la conversión UTC explícita mediante
`Time(..., scale='tai').utc`, con soporte de segundos intercalares de
[Astropy](https://docs.astropy.org/en/stable/time/index.html).
Por ejemplo, `2024-01-01T00:01:30 TAI` pasa a `00:00:53 UTC`.
No se descarga información temporal durante la conversión. En el runtime
ligero sin Astropy, UTC queda `null` y se conserva TAI, sin añadir una dependencia.
Las fechas de calendario de la serie de polaridad quedan identificadas como TAI.

La columna `date` histórica se guardó como `solar_map.date.iso`, sin escala ni
headers. No coincide con el tiempo del nombre: por ejemplo, la primera fila
contiene `2016-02-03 00:00:24.200`, mientras el tiempo TAI del nombre convertido
es `2016-02-03 00:00:54.000Z`. Se preservan por separado en
[`observation_times.json`](../auralis-back/reports/phase1_v1/observation_times.json).
No se interpreta el CSV como UTC ni TAI. La generación nueva preserva la escala
del objeto SunPy y la conversión UTC en columnas explícitas.

- K-fold: tabla conservada, rotulada como ejemplo fijo sin validación ejecutada.
- AIA: fallback rotulado en el panel **y dentro del PNG**, con procedencia en
  el catálogo y header HTTP. Un archivo local AIA se identifica como procedencia
  no verificada; la mera existencia del archivo no demuestra una observación.
- C/M/X: bandas internas, sin equivalencia validada con clases GOES.
- Confianza y ruido: heurísticas explícitas en UI/respuesta API.
- `activation_pct`: se conserva por compatibilidad; describe el máximo del
  Grad-CAM normalizado, truncado a 99. No mide área, probabilidad o validación.
- Landing/dashboard: métricas históricas con advertencia de fuga y reentrenamiento.

## Cambios por archivo

Rutas relativas a la raíz del repositorio:

| Archivos | Motivo |
| --- | --- |
| `auralis-back/src/processing/model_input.py` (nuevo) | Transformación compartida y validación del input clip400 |
| `auralis-back/src/processing/scientific_split.py` (nuevo) | Deduplicación, separación, validación de identidades y hashes |
| `auralis-back/src/processing/observation_time.py` (nuevo) | Separar tiempo original TAI y conversión UTC |
| `auralis-back/src/models/train_model.py` | Input común, split corregido y resultados futuros separados con manifiesto |
| `auralis-back/src/processing/prepare_dataset.py` | Generación nueva clip400/SI crudo, escala temporal y protección de archivos existentes |
| `auralis-back/src/api/main.py` | Preprocesamiento común, fechas correctas, etiquetas de procedencia/unidades y estado histórico |
| `auralis-back/scripts/evaluate_final.py` | Evaluación ligada a su split/checkpoint; reproducción antigua explícita, sin sobrescribir reportes |
| `auralis-back/scripts/predict.py` | CLI FITS compatible con pesos promovidos, dos canales y UTC explícito |
| `auralis-back/scripts/explain_model.py`, `scripts/plot_gradcam_overlay.py` | Mismo input en explicabilidad |
| `auralis-back/scripts/test_inference.py` | Input común y split histórico persistido; diagnóstico rotulado |
| `auralis-back/src/experiments/run_external_baselines.py` | Evitar split por filas y mezcla futura con resultados históricos |
| `auralis-back/scripts/audit_phase1.py`, `tests/test_phase1.py` (nuevos) | Auditoría reproducible, manifiestos y pruebas dirigidas |
| `auralis-back/models/split_indices_phase1_v1.json`, `reports/phase1_v1/*` (nuevos) | Evidencia y trazabilidad, sin reemplazar artefactos |
| `auralis-front/src/features/dashboard/dashboard-page.tsx` | Aviso científico en las pestañas afectadas |
| `auralis-front/src/features/dashboard/components/kfold-results.tsx` | Etiqueta de ejemplo ilustrativo |
| `auralis-front/src/features/dashboard/magnetogram-panel.tsx` | Procedencia AIA, bandas internas y fecha sin falso UTC |
| `auralis-front/src/features/dashboard/prediction-chart.tsx` | Contar por fecha original cuando la conversión UTC no está disponible |
| `auralis-front/src/features/landing/{landing-hero,project-description,architecture-diagram}.tsx` | Calificar métricas históricas y corregir SI; sin rediseño |
| `auralis-front/src/lib/{api,types}.ts`, `lib/i18n/translations.ts` | Campos de procedencia y etiquetas científicas |
| `AGENTS.md`, `README.md`, `RESEARCH_DOSSIER_MASTER.md`, `docs/backend.md`, este archivo | Contrato y precedencia de las correcciones, sin reescribir el dossier |

Los cambios previos del usuario en `scientific-header.tsx`,
`simulation/SimulationControls.tsx` y `simulation/SolarSimulationPage.tsx`
no fueron editados por esta fase. Tampoco se modificó Agent Lab, arquitectura,
rutas, dependencias, checkpoints, CSV fuente, scaler ni experimentos históricos.

## Validación y reproducción

Python utilizado: **3.12.7**; NumPy 1.26.4, pandas 3.0.2, PyTorch 2.11.0,
torchvision 0.26.0, ONNX Runtime 1.25.1, Astropy 7.2.0, scikit-learn 1.8.0.
Estas son versiones ya instaladas, no las versiones declaradas por exp_005.
Dentro de `auralis-back/`, el shim `python3` selecciona otro intérprete sin
NumPy; para repetir las comprobaciones locales hay que usar el ejecutable explícito.

```sh
# Desde auralis-back; en otro equipo, usar un entorno que satisfaga los requisitos.
PYTHON=/Users/alejandro/.pyenv/versions/3.12.7/bin/python3
MPLCONFIGDIR=/tmp/auralis-mpl "$PYTHON" scripts/audit_phase1.py --checkpoint-diagnostic
SUNPY_CONFIGDIR=/tmp/auralis-sunpy MPLCONFIGDIR=/tmp/auralis-mpl "$PYTHON" -m unittest discover -s tests -p test_phase1.py -v
MPLCONFIGDIR=/tmp/auralis-mpl "$PYTHON" scripts/test_inference.py
"$PYTHON" -m compileall -q src scripts tests
# Desde auralis-front:
npm run build
```

Resultados: 13 pruebas dirigidas aprobadas; equivalencia exacta de los 1.314
inputs por dataset/evaluación/API, paridad PyTorch/ONNX en tres observaciones
con tolerancia `1e-5`, predict/alias/upload coincidentes, split reproducible sin
overlap, rechazo de datos/splits inválidos, SI previo a resize y temporalidad
TAI/UTC (incluido segundo intercalar y ausencia de Astropy), etiquetas y hashes. También se comprobó el ciclo HTTP real de FastAPI,
sus respuestas, Grad-CAM y el rechazo de validación nueva con pesos antiguos.
El test existente ejecutó 101 casos extremos del split histórico; falta el
checkpoint original no aumentado, por lo que no permite comparar dos modelos.
Su MAE determinista de 0,3236 es diagnóstico histórico, no reemplaza exp_005.

La compilación Vite termina correctamente; avisa de bundles >500 KB. No se
reestructuraron bundles. No hay `tsc` instalado, así que no se afirma un chequeo
TypeScript independiente de Vite. No se ejecutó entrenamiento completo ni
una regeneración FITS real. El fixture FITS prueba la lógica con un mapa
sintético controlado; no sustituye los FITS originales ausentes.

## Estado científico y pendientes

El checkpoint actual sirve para reproducción histórica, inspección exploratoria
y demostración. **No permite sostener métricas de generalización independientes.**
Se necesita reentrenar desde cero, sin cargar estos pesos, sobre el split nuevo,
y guardar/evaluar el experimento por separado. El entorno accesible sólo expone
CPU (CUDA/MPS no disponibles); se evitó iniciar una corrida prolongada de hasta
100 épocas × validación MC de 20 pasadas. No hay métricas nuevas que promover.

Pendientes delimitados:

1. Recuperar FITS/headers originales y la versión del productor para resolver
   el significado y escala exactos de `CSV.date`, verificar `T_REC`/tiempo de
   observación, unidades/calibración y regenerar desde la fuente bit a bit.
   `data/raw/` no contiene FITS. No se inventó esta información.
2. Recuperar el manifiesto original de entrenamiento, si existe, para vincular
   inequívocamente pesos, CSV, versiones y configuración histórica. El contrato
   actual está sólidamente respaldado por evidencia cruzada, no por ese registro ausente.
3. Reentrenar y evaluar el nuevo experimento antes de citar rendimiento. El
   split por observaciones todavía puede contener correlación entre días próximos;
   **no valida extrapolación temporal**. No se implementó una fase temporal.
4. No interpretar confianza, dispersión por ruido, bandas o Grad-CAM como
   magnitudes calibradas o evidencia de predicción de eventos solares.

Ninguna fase posterior fue iniciada.
