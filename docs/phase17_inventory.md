# FASE 1.7 — Inventario científico

Inventario realizado sobre el estado inicial de la sesión, sin eliminar archivos.
Los 334 hashes iniciales están en `auralis-back/reports/phase17_coronium_v3_1/audit_before.json`.
El inventario por archivo y clasificación está en `inventory.json`, junto a esa evidencia.
Las copias de fuentes y épocas se cuentan individualmente allí; aquí se agrupan para facilitar la revisión.

| Elemento existente | Clasificación inicial | Uso / corrección en Fase 1.7 |
|---|---|---|
| `scripts/evaluate_final.py` | Necesita adaptación a V3.1 | Se reutiliza `compute_metrics`. Se corrige el encabezado V3 PRO y la promesa de reproducibilidad universal por seed. Continúa exigiendo run o reproducción legacy explícita. |
| `scripts/run_phase15.py`, `verify_phase15_results.py`, manifiestos y dos evaluaciones MC | Válido y reutilizable | Fuente de MC T=20 MPS, 263 observaciones, seed 42, batch 32. Repetición preservada como evidencia útil. |
| `src/models/train_model.py`, `history.json`, 50 JSON de épocas | Datos válidos; salida gráfica necesita adaptación | Se mantienen los hashes de promoción. El gráfico congelado usa nomenclatura antigua; se reconstruyen paneles publicables desde el historial, con protocolos, unidades, escala log de los ejes y época seleccionada. No se reentrena. |
| `models/coronium_v3_1_metrics.json`, manifiesto, checkpoint, ONNX | Válido y reutilizable | Se verifican hashes y tamaño; métricas oficiales intactas. Se amplía el análisis en un reporte separado. |
| CSV de predicciones MC/deterministas y verificación Phase 1.6 | Válido y reutilizable | Emparejamiento por índice original y archivo; chequeo de targets float32 contra metadata y de ausencia de duplicados/solapamiento. |
| `plot_final_scatter.py` y `plot_r2_diagnostic.py` | Incorrecto/desactualizado; scatter parcialmente redundante | Usaban CSV V3 y rótulos log-SI/SSN/hold-out. Ahora exportan desde reportes V3.1 verificados; helpers compartidos, sin sobrescribir gráficos previos. La banda de desviación residual ya no parece un intervalo predictivo. |
| `plot_architecture_diagram.py` | Incorrecto/desactualizado | Se corrigen log input/target, dimensiones intermedias, parámetros por bloque, pérdida y tamaño ONNX. Conteos/tamaño obtenidos del modelo/artefacto real. |
| `plot_gradcam_overlay.py` | Incorrecto/desactualizado parcialmente | Ya cargaba V3.1, pero decía log-SI y hold-out. Se corrigen unidades/protocolo/normalización; se reutiliza en el peor caso determinista. |
| `explain_model.py`, `predict.py`, `test_inference.py`, `export_to_onnx.py` | Válido y reutilizable dentro del alcance documentado | Ya usan V3.1 y el contrato compartido. Se preservan. Grad-CAM es cualitativo, no una probabilidad ni causalidad física. |
| `src/experiments/run_external_baselines.py` | Necesita adaptación | Se reutiliza `NaivePersistence` como **media de entrenamiento**, no persistencia temporal. Se corrige sincronización CUDA/MPS del temporizador para futuras ejecuciones. No se ejecuta entrenamiento CNN. |
| `experiments/results_benchmarking.json` | Necesita adaptación para comparación vigente | 352 filas de validación; distinto split del V3 histórico (353) y V3.1 (263). ResNet18/VGG11 quedan como referencias históricas; no ranking controlado. Checkpoints indicados no disponibles para reevaluación limpia verificable. |
| `exp_001`–`exp_005`, V3 .pth/.onnx/.onnx.data, scaler y split antiguo | Válido como archivo histórico; no como evidencia vigente | Se preservan bytes y metadatos. `exp_004` no satisface el esquema de listado del API y ya era omitido; no se inventan métricas faltantes. Los JSON crudos siguen disponibles. |
| `reports/results_comparison.csv`, `final_coronium_scatter_tesis.png`, `r2_diagnostic.png` | Necesita adaptación / etiquetas incorrectas | Conservados como V3 histórico. Los rótulos hold-out y log-SI de las imágenes no son válidos; índice `reports/README.md` advierte su alcance. |
| `reports/figures/learning_curve*.png`, `error_scatter.png`, `mode_collapse_evidence.png` | Necesita adaptación | Curvas/diagnósticos históricos sin respaldo para V3.1. No se reutilizan como resultados actuales. |
| `parameter_count_comparison.png`, `r2_vs_parameters.png` | Necesita adaptación | Conteos estructurales pueden orientar, pero R² de splits distintos no es un ranking válido. Se señala junto a su uso en README. |
| `reports/figures/gradcam*.png`, `prediction_result.png`, `architecture_diagram.png` | Necesita adaptación | Imágenes históricas conservadas; se generan versiones V3.1 trazables de arquitectura y Grad-CAM. |
| `reports/phase1_v1/`, `reports/phase16_coronium_v3_1/`, snapshots | Válido y reutilizable | Evidencia de contrato, hashes, split, export y paridad preservada íntegramente. |
| Notebook exploratorio, `generate_sample_viz.py`, `validate_notebook.py`, `visualize_tensor.py` | Válido como exploración de datos | Campo magnético y umbral 200 G, no rendimiento del modelo. No se mezclan sus figuras con métricas de V3.1. |
| `src/visualization/app.py` (Streamlit auxiliar) | Incorrecto/desactualizado | CNN de un canal y checkpoint legacy, pero decía V3 PRO, MAE 5.52%/0.07%, 2000+ imágenes. Se rotula legacy y se retiran esas afirmaciones no sustentadas. |
| `/api/stats` y `global-metrics.tsx` | Válido, necesita ampliación de presentación | API ya separaba protocolos. Se agrega MAPE visible y tabla MC/determinista, con unidades y alcance. |
| `/api/results-comparison`, `predicted-vs-actual.tsx` | Necesita adaptación | Selector `mc`/`deterministic`, hashes de CSV, ejes derivados de datos, versión/protocolo y unidades SI. Default MC compatible. |
| `/api/benchmark`, `architecture-comparison.tsx` | Necesita etiquetado metodológico | Se indica explícitamente la invalidez de comparación controlada. Se evita graficar parámetros normalizados y errores SI como si compartieran unidad. Conteos conservados en tabla. |
| `/api/xai/faithfulness`, `xai-faithfulness.tsx` | Datos reales; interpretación incorrecta | Se elimina afirmación fija de caída “significativamente” más rápida, categorías arbitrarias de fidelidad y porcentaje de confianza. Se muestra gap AUC dimensionalmente correcto, protocolo y limitaciones. |
| `experiment-log.tsx` | Incorrecto/desactualizado | Inventaba estado running/failed por posición/nombre y aplicaba semáforos MAE con interpretación log-SI. Ahora muestra artefactos guardados, alcance y MAE sin inferir estado vivo. |
| `model-metrics.tsx` | Incorrecto/desactualizado parcialmente | Rango 2010–2024 y atribución HMI/AIA fijos corregidos al catálogo HMI TAI real. Serie HMI m_45s no implica cadencia del muestreo local. Estados no verificados se muestran como tales. |
| `kfold-results.tsx` | Válido únicamente como ilustración ya advertida | No se elimina ni se incorpora a métricas científicas. K-fold no ejecutado. |
| `prediction-chart.tsx`, `magnetogram-panel.tsx`, landing V3.1 | Válido con sus calificaciones actuales | Se mantienen advertencias sobre datos locales, bandas internas, sensibilidad al ruido y confianza heurística. Sin cambios de predicción. |
| README y dossier | Necesita adaptación / dossier desactualizado | Se enlaza el informe vigente. Dossier íntegro identificado como archivo V3; se señalan explícitamente log-SI, hold-out y tamaño completo incorrectos. |
| Errores por banda, residuos por ambos ejes, histogramas, casos extremos, diferencia pareada, latencia con muestras | Faltante | Agregados automáticamente desde resultados e inputs reales; versiones y protocolo por figura. |
| Métricas por año de registro TAI | Faltante | Diagnóstico descriptivo del mismo split aleatorio; no evaluación temporal. |
| Catálogo de publicación PNG/PDF/SVG con hashes y comandos | Faltante | 13 figuras, CSV/JSON, fuentes y manifiesto; repetición independiente del generador. |

No se tocaron Unity, WebAR, timeline, simulación ni gemelo digital. No se inició ninguna fase posterior.
