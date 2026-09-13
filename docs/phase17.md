# FASE 1.7 — Auditoría y ampliación científica de Coronium V3.1

**Estado: FASE 1.7: CUMPLIDA.** Sin reentrenamiento, promoción de artefactos ni inicio de fases posteriores.

[Inventario y clasificación](phase17_inventory.md) · [Galería de 13 figuras](../auralis-back/reports/phase17_coronium_v3_1/analysis_v2/report.md) · [Métricas JSON](../auralis-back/reports/phase17_coronium_v3_1/analysis_v2/metrics.json) · [Verificación](../auralis-back/reports/phase17_coronium_v3_1/verification.json).

## Alcance y fuentes

Checkpoint V3.1 `best_coronium_v3_1.pth`, SHA256 `1e4c834451375a7c4a1f47bd60404bf9aec3bc20c18056c9fc1b517b168e8e51`, copia de la mejor época 40 de `experiments/phase15_runs/20260905T132456995672Z/`. Entrenamiento finalizó en época 50.

Se reutilizan los CSV reales de Phase 1.6: MC Dropout T=20 en MPS, batch 32, seed 42; y una pasada determinista PyTorch/ONNX CPU, batch 1. **No se vuelven a generar las predicciones MC de precisión en esta fase**: se verifican sus hashes, identidad, targets y coincidencia con los resultados oficiales. Las dos evaluaciones MC originales ya habían producido predicciones idénticas. No se confunden las salidas del ensayo de latencia CPU MC con las métricas oficiales MPS.

Se verificaron las 1.314 entradas procesadas contra la evidencia de Phase 1, las fuentes de promoción y la partición de 1.051 train / 263 validación, con cero observaciones compartidas. Los 263 casos son validación usada para seleccionar checkpoint y early stopping: **no constituyen test independiente ni validación temporal**. El split aleatorio no descarta dependencia temporal entre observaciones cercanas.

SI = `100 × count(abs(B_LOS) > 200 G) / original_pixel_count`, porcentaje de píxeles originales. Inputs: `clip(resize(B_LOS), -400, 400) / 400`, separados en B+/B−. No hay log ni Z-score. Los errores están en **puntos porcentuales de SI (SI pp)**, R² es adimensional y MAPE es porcentaje relativo. Residuo = predicción − target. MAPE omite targets exactamente cero; aquí los 263 son distintos de cero.

## Qué se reutilizó, corrigió y agregó

Se reutilizaron checkpoint/ONNX, registro y manifiestos, CSV de ambos protocolos, `compute_metrics`, preparación compartida de inputs, separación por observación, historial real, implementación del baseline de media y scripts de scatter, residuos, arquitectura y Grad-CAM.

Se corrigieron etiquetas log-SI/SSN/hold-out, tamaños incompletos, supuestas comparaciones controladas de benchmarks históricos, mezcla visual de parámetros normalizados con errores SI, afirmaciones fijas de significancia/fidelidad de Grad-CAM y estados de entrenamiento inventados. El Streamlit auxiliar queda identificado como legacy. El resumen del dataset deriva sus años del catálogo TAI; no presenta la serie instrumental m_45s como cadencia efectiva local. Los estados sin medición aparecen como no verificados.

Se agregaron un generador integrado (`run_phase17.py`), un verificador (`verify_phase17.py`), 12 tests dirigidos, CSV por observación/banda/año/casos extremos, métricas adicionales, timings individuales, manifiestos, snapshots de fuentes y exportaciones PNG de 300 dpi más PDF/SVG vectoriales. El entrenador permanece intacto para mantener su hash de promoción; su historial alimenta los nuevos paneles de publicación con rótulos correctos.

No se eliminó ningún archivo preexistente: **178 artefactos congelados y 26 archivos protegidos** conservan sus hashes. Se trabajó sobre `main`, respetando cambios previos del usuario. Unity, WebAR, timeline, simulación y gemelo digital no se modificaron.

## Métricas finales

Recalculadas en float64 sobre valores archivados. La reducción MC original fue float32: diferencias de últimos decimales son numéricas, no resultados nuevos. Las métricas oficiales de promoción no se reescriben.

| Modelo/protocolo | N | MAE (SI pp) | RMSE (SI pp) | R² | MAPE (%) |
|---|---:|---:|---:|---:|---:|
| V3.1 MC Dropout T=20, MPS | 263 | 0.10155762 | 0.12337954 | 0.87529664 | 5.98702568 |
| V3.1 determinista ONNX CPU | 263 | 0.20408340 | 0.25823317 | 0.45371922 | 10.49751499 |
| V3.1 determinista PyTorch CPU | 263 | 0.20408324 | 0.25823297 | 0.45372009 | 10.49750713 |
| Media del entrenamiento, split limpio | 263 | 0.30440373 | 0.34962027 | −0.00134808 | 17.88717670 |

El baseline reutiliza la clase histórica `NaivePersistence`: en realidad predice la **media de train = 1.76832124 SI %**, estimada exclusivamente con las 1.051 observaciones de entrenamiento. No es persistencia temporal y no se ajusta sobre validación.

También se entregan **sesgo, mediana, percentiles 90/95 y máximo del error absoluto, N y N no cero para MAPE**, tanto globalmente como por bandas; por año se exportan las mismas métricas descriptivas.

| Protocolo | Sesgo (SI pp) | Mediana |error| | P90 |error| | P95 |error| | Máximo |error| |
|---|---:|---:|---:|---:|---:|
| MC T=20 | +0.00096797 | 0.09472632 | 0.19497356 | 0.23227816 | 0.33932805 |
| ONNX determinista | −0.18687747 | 0.18103099 | 0.41996114 | 0.48784542 | 0.69843316 |

Todos los errores y percentiles de esta tabla están en SI pp. No se presentan como intervalos predictivos.

## Bandas y casos de mayor error

Bandas fijas basadas en el **target**, no en la predicción: baja SI <1.41; media 1.41≤SI<1.75; alta SI≥1.75. Son bandas internas de demo, sin calibración V3.1 ni equivalencia GOES.

| Banda | N | MAE MC | MAE determinista | Sesgo MC | Sesgo determinista |
|---|---:|---:|---:|---:|---:|
| Baja | 43 | 0.11345225 | 0.05174790 | +0.10696742 | +0.04363687 |
| Media | 96 | 0.09571258 | 0.10290537 | +0.00035581 | −0.09849272 |
| Alta | 124 | 0.10195806 | 0.33524079 | −0.03531596 | −0.33524079 |

Unidades: SI pp. **Todos los 124 casos de actividad alta son subestimados por el protocolo determinista** en esta validación. MC tiene menor error absoluto en 176 observaciones; determinista en 87; no hay empates. La diferencia global MAE determinista − MC es 0.10252578 SI pp. La ventaja MC no es uniforme: en actividad baja, determinista tiene menor MAE.

El R² por bandas también se entrega, pero puede ser negativo por la estrecha dispersión de los targets de cada banda. No se interpreta como evidencia automática de cambio de distribución ni se compara directamente con el R² global.

`worst_cases.csv` contiene los diez peores casos **por separado para cada protocolo**, índice original, filename, target, ambas predicciones, residuos, errores, banda y tiempo TAI/UTC. La fecha CSV original se conserva con escala desconocida.

| Protocolo / caso | Fecha del registro TAI | Target SI % | Predicción SI % | Residuo SI pp |
|---|---|---:|---:|---:|
| MC, fila 1200 | 2024-02-23 | 2.105504 | 1.766176 | −0.339328 |
| MC, fila 387 | 2018-03-17 | 1.614064 | 1.308858 | −0.305206 |
| MC, fila 1196 | 2024-02-20 | 2.072656 | 1.774680 | −0.297976 |
| Determinista, fila 1312 | 2024-08-09 | 2.949613 | 2.251180 | −0.698433 |
| Determinista, fila 1447 | 2025-02-06 | 2.441353 | 1.818943 | −0.622410 |
| Determinista, fila 1221 | 2024-03-26 | 2.428782 | 1.840243 | −0.588539 |

Los mayores errores deterministas están asociados aquí a targets altos; el peor MC no coincide con el peor determinista. La figura de seis magnetogramas permite revisar morfología y calidad visual sin atribuir causalidad a simple vista. Grad-CAM del caso determinista más extremo resalta estructuras localizadas, pero no explica por sí solo el sesgo ni demuestra causalidad física. Ese script usa `stage4`, mientras la eliminación interactiva del API usa `stage4.conv`; están rotulados y no se tratan como una misma medición.

## Por qué MC y determinista pueden diferir

PyTorch desactiva Dropout en `eval()` (identidad); con Dropout activo aplica máscaras y reescala las activaciones retenidas. [Documentación oficial de Dropout](https://docs.pytorch.org/docs/stable/generated/torch.nn.Dropout.html).

Coronium incluye Dropout2d en varios bloques antes de operaciones posteriores no lineales (ReLU, pooling, atención ECA). Aunque el reescalado conserva la esperanza local de una activación, **el promedio de la red completa con máscaras no tiene por qué igualar la red sin máscaras**. BatchNorm mantiene estadísticas congeladas en MC; no se usa `model.train()` para toda la red. La selección del checkpoint y el early stopping se hicieron con MC T=20, de modo que la selección favorece el criterio de ese protocolo. Esto es una explicación compatible con la arquitectura y el procedimiento, no una ablación causal concluida. La interpretación de MC Dropout como aproximación predictiva se fundamenta en [Gal y Ghahramani, ICML 2016](https://proceedings.mlr.press/v48/gal16.html).

El máximo desacuerdo PyTorch CPU/ONNX es **1.1920929e−6**, muy inferior a la diferencia entre protocolos; no hay evidencia de que el export ONNX explique la brecha observada. Pese a ello, este análisis no aísla por ablación cada posible contribución de máscaras, estadísticas BatchNorm, dispositivo o selección del checkpoint. Tampoco prueba que T=20 haya convergido ni generaliza a otros seeds, splits o modelos.

El mejor MAE de validación **durante entrenamiento** fue 0.09670745 en época 40; la reevaluación MC oficial da 0.10155762. Usa otra secuencia de RNG/máscaras, por lo que no se confunden ambas cifras. Train también usa aumento, dropout, estadísticas BatchNorm de entrenamiento y pesos cambiantes dentro de la época. Sus curvas no miden exactamente el mismo procedimiento que validación.

## Baselines e histórico V3

Los resultados existentes ResNet18/VGG11 proceden de validación de 352 filas, frente a 353 del V3 histórico y 263 de V3.1. No hay artefactos verificables para una reevaluación CNN emparejada sobre el split limpio, y no se reentrenan baselines en esta fase. Se preservan como contexto histórico; se rechazan rankings de precisión y reducciones porcentuales como evidencia controlada. El API mantiene sus campos aritméticos antiguos por compatibilidad, pero declara expresamente que no son evidencia de mejora V3.1.

| Referencia | Validación | Solapamiento conocido | MAE | RMSE | R² | MAPE |
|---|---:|---:|---:|---:|---:|---:|
| V3 histórico, MC T=20 | 353 filas | 145 observaciones | 0.1048 | 0.1272 | 0.8634 | 6.07% |
| V3.1, MC T=20 | 263 observaciones | 0 | 0.10155762 | 0.12337954 | 0.87529664 | 5.98702568% |
| V3.1, ONNX determinista | 263 observaciones | 0 | 0.20408340 | 0.25823317 | 0.45371922 | 10.49751499% |

Comparación **descriptiva entre protocolos y particiones distintos**. No se calcula una “mejora V3→V3.1” atribuible al modelo. CSV: `historical_protocol_comparison.csv`. No se crea un gráfico de ranking que sugiera equivalencia metodológica.

## Parámetros, tamaño y latencia

- Parámetros totales/entrenables: **206.875**, contados desde la arquitectura con el checkpoint cargado.
- Checkpoint: **848.269 bytes**, 0.80897236 MiB.
- ONNX: **835.234 bytes**, 0.79654121 MiB; self-contained, sin datos externos. No equivale al consumo RAM del proceso.
- Hardware: **Apple M5, 24 GiB, 10 CPU físicas/lógicas**, macOS 26.6.2 arm64; Python 3.12.7, PyTorch 2.11.0, ONNX Runtime 1.25.1. El suplemento `hardware.json` registra la lectura `sysctl`, bloqueada por sandbox durante el ensayo original; se preservan los campos null originales.
- CPU, float32 `(1,2,512,512)`, batch 1; cuatro hilos intra-op y uno inter-op. ONNX CPUExecutionProvider, ORT_SEQUENTIAL, optimización por defecto.
- Nueve observaciones tomadas por posiciones equiespaciadas en el orden de targets; diez calentamientos por protocolo, sesenta rondas, orden de protocolos intercalado con seed 42.
- Temporización síncrona `perf_counter_ns`, forward + extracción escalar, datos reales residentes. Excluye I/O, preparación, inicialización, HTTP, caché y diagnóstico de ruido del API.

| Carga de trabajo | Media (ms) | Mediana (ms) | P95 (ms) | N |
|---|---:|---:|---:|---:|
| ONNX determinista CPU | 24.5386 | 24.4372 | 25.4794 | 60 |
| PyTorch determinista CPU | 30.8439 | 30.8993 | 31.6730 | 60 |
| PyTorch MC T=20 CPU | 640.2160 | 639.9151 | 645.3786 | 60 |

El timing CPU MC no mide la ejecución MPS batch 32 de las métricas oficiales. Son latencias locales, con variabilidad por carga, temperatura y entorno; repetir el procedimiento no promete milisegundos idénticos. Los antiguos 25.11 ms se mantienen exclusivamente como dato histórico V3. La corrección de sincronización CUDA/MPS en el script de baselines solo aplica a futuras mediciones; no corrige retrospectivamente números antiguos.

## Gráficos finales

Todos en `analysis_v2/figures/`, con PNG 300 dpi, PDF y SVG. La galería enlaza cada formato.

1. `01_target_prediction`: target SI vs predicción, MC y determinista.
2. `02_residuals`: residuos vs predicción y vs target, ambos protocolos.
3. `03_residual_distribution`: histogramas con bins comunes y sesgo.
4. `04_absolute_error_distribution`: histogramas de error absoluto con bins comunes.
5. `05_activity_band_errors`: MAE y sesgo por banda del target, con tamaños de muestra.
6. `06_training_validation`: pérdida Huber ponderada, MAE y learning rate, 50 épocas y checkpoint 40. Ejes logarítmicos, targets sin transformación log.
7. `07_protocol_difference`: predicciones pareadas y diferencia de errores individuales.
8. `08_clean_baseline`: cuatro métricas de ambos protocolos y media de entrenamiento en el mismo split.
9. `09_largest_error_cases`: tres peores magnetogramas por protocolo, valores y fechas TAI.
10. `10_error_by_record_year`: MAE descriptivo por año TAI, N visible; no test temporal.
11. `11_latency`: distribución de las 60 mediciones por carga de trabajo; eje log ms.
12. `12_architecture`: diagrama existente corregido con tamaños y conteos reales.
13. `13_gradcam_largest_deterministic_error`: explicación cualitativa del peor caso determinista, capa y protocolo explícitos.

No se generan figuras decorativas ni intervalos de confianza inventados. R²/MAPE y comparaciones históricas adicionales están también en CSV/JSON/tablas, sin duplicar paneles innecesarios.

## Reproducción

Desde `auralis-back/`, usando el entorno de dependencias de investigación:

```sh
python scripts/run_phase17.py --output-dir reports/phase17_coronium_v3_1/<nuevo-run>
```

En esta máquina se usó `/Users/alejandro/.pyenv/versions/3.12.7/bin/python3`; el shim `python3` dentro de `auralis-back` resuelve otro entorno sin matplotlib. Las dependencias y versiones se registran en `environment.json`. Se requieren los artefactos Phase 1/1.5/1.6 y los datos locales completos.

Para regenerar cifras/figuras usando los tiempos ya medidos, sin afirmar una nueva medición:

```sh
python scripts/run_phase17.py --output-dir reports/phase17_coronium_v3_1/<repeticion> --latency-from reports/phase17_coronium_v3_1/analysis_v2/latency.json
python scripts/verify_phase17.py --report-dir reports/phase17_coronium_v3_1/analysis_v2 --repeat-dir reports/phase17_coronium_v3_1/<repeticion> --output <nueva-carpeta>/verification.json
```

La carpeta de salida del verificador debe existir; también escribe `inventory.json` allí. Los generadores rechazan sobrescrituras. Los scripts de scatter/residuos siguen disponibles individualmente con `--report-dir` y `--output-dir` nuevo. Manifiestos incluyen comandos, fuentes y hashes de salida; no se mutan los resultados de promoción.

## Verificaciones ejecutadas

- **30 tests pasan**, incluyendo 12 nuevos sobre métricas independientes con scikit-learn, límites de bandas, N=0/targets cero, alineación, baseline train-only, ponderación por banda, ranking de extremos, selector API, rechazo de CSV corrupto, separación histórica, hashes y latencia cruda.
- Suite: `python -m unittest discover -s tests -v`. Se usaron `MPLCONFIGDIR=/tmp/auralis-phase17-matplotlib` y `SUNPY_CONFIGDIR=/tmp/auralis-phase17-sunpy`. Primer intento tuvo un error de permiso de caché SunPy; el entorno corregido pasó completo.
- `verify_phase16.py` reutilizado: paridad HTTP de 11 muestras, alias/upload/caché, stats/scatter/benchmark y preservación. Desacuerdo máximo PyTorch–HTTP 4.6682358e−5 por redondeo a cuatro decimales.
- Repetición en otro proceso: **10 archivos de datos/JSON/CSV y los 13 PNG idénticos byte a byte**. El timing se reutilizó explícitamente; no es una segunda medición. PDF/SVG se generan y hashean, pero no se exige identidad binaria de sus IDs internos.
- `npm run build`: correcto. Persiste advertencia de chunks >500 kB, ajena a la validez científica; no se refactorizó la aplicación para suprimirla.
- Revisión visual de figuras y del dashboard local: unidades, separación de protocolos, leyendas y selector.
- Sin eliminación de archivos previos, sin cambios en artefactos V3/V3.1 o áreas protegidas.

Evidencia en `reports/phase17_coronium_v3_1/`: `verification.json`, `http_parity.json`, `tests-final.txt`, `build-final.txt`, `browser-verification.json` y `hardware.json`.

## Limitaciones y pendientes científicos

No existen test temporal/independiente, validación cruzada real, análisis multiseed de precisión MC, calibración de incertidumbre o estudio de convergencia de T en este conjunto. El baseline CNN limpio queda pendiente por falta de pesos/proveniencia válidos; entrenarlo sería trabajo adicional. No se reporta superioridad general MC ni mejora controlada frente a V3 histórico.

La validación utilizada para seleccionar pesos conserva sesgo de selección; las bandas son históricas y sus N desiguales. Los errores por año y casos extremos son descriptivos del mismo conjunto. Grad-CAM/deletion es diagnóstico local, dependiente de la capa, máscara y referencia; falta una evaluación agregada con controles para hablar de fidelidad global. La pérdida de información por resize/clip puede ser relevante, pero no se demuestra como causa del error sin un estudio específico.

Los nombres legacy `sunspot_index`, `Real_SSN` y `Predicted_SSN` se retienen en contratos antiguos para compatibilidad; las etiquetas científicas vigentes usan SI. El dossier y las imágenes antiguas permanecen accesibles y señalados como históricos. No se transformaron sus conclusiones antiguas en resultados nuevos.

**FASE 1.7: CUMPLIDA.** El conjunto solicitado está disponible y reproducido; las limitaciones de evidencia se declaran sin iniciar fases posteriores.
