# V3.2-C — protocolo registrado antes de entrenar o evaluar candidatos

Tres entrenamientos secuenciales desde cero: C0 backbone 0.2, C1 0, C2 0.1;
cabeza 0.3, seed42, CoroniumV3 original (206875 parámetros), sin promoción.
Se importan arquitectura, WeightedHuberLoss, aumentaciones, preparación y split
existentes sin editar. No se carga V3.1 para entrenar.

La instrucción actual prevalece sobre la propuesta B: checkpoint por mínimo
MAE determinista; scheduler ReduceLROnPlateau y parada por Weighted Huber
DETERMINISTA. Delta1/alpha2, AdamW lr0.001/weight_decay1e-5, factor0.5,
patience3/min_lr1e-6; parada patience10/min_delta0; máximo100 épocas.
Agregación por observación. Validation siempre eval, BN congelada, sin MC,
sin aumentaciones, sin ajuste de transformaciones ni recalibración BN.

MPS float32 determinista, 4 hilos CPU/1 interop, workers0, batch8 común a los
brazos. Batch32 de Phase1.5 requería ~12.9GB de driver MPS; ahora solo ~9GB
están disponibles. Batch8 se fija antes del piloto por recursos; cambia las
actualizaciones/estadísticas BN respecto al histórico, NO entre C0/C1/C2.
Piloto desechable de 3 pasos (batch8) y 2 forwards eval antes de entrenar:
no se reutilizan sus pesos. Se estiman tiempo de época/máximo y memoria, con
límite preventivo de driver14GiB, RSS16GiB y disponibilidad512MiB; detener ante
no finitos o exceso, sin cambiar configuración a mitad del experimento.

Inicialización única seed42 copiada byte a byte a cada brazo, state_dict idéntico.
Orden por época precomputado con generador CPU privado seed42. Aumentaciones
originales, con semilla SHA256(42,augmentation,epoch,source_row) y RNG CPU
restaurado después: mismas imágenes entre brazos. Cada dropout recibe antes del
forward semilla SHA256(42,dropout,epoch,batch,module_name), incluyendo cabeza,
para que p=0 no desplace la secuencia aleatoria de las otras capas. Los masks
no pueden ser idénticos a distintas probabilidades; p=0 no consume RNG. Las
activaciones, gradientes, BN, scheduler, parada y épocas seleccionadas pueden
divergir como consecuencia del tratamiento. No se comparan curvas train con
ruido contra validation para concluir sobreajuste.

## Controles y XAI (definidos antes de resultados)

Evaluación final CPU float32 batch1 4/1 hilos de inicial, seleccionado y V3.1
histórico sobre idénticos train1051 y validation263, sin aumentaciones/eval.
Referencia constante: media del target train solamente. Se guardan identidades,
targets originales y predicciones sin redondear. Recalcular en float64 MAE,
RMSE,R2,MAPE,sesgo,p95 absoluto, dispersión/correlación, bandas y cola SI>2.
La selección durante entrenamiento MPS batch8 y el scoring CPU batch1 se
etiquetan por separado. No se reselecciona checkpoint en CPU ni mediante XAI.

Nueve muestras: en cada banda ordenar por (target,source_row) y tomar índices
0,round((n-1)/2),n-1. Se fija solo con targets/identidad, incluye SI>2.
Grad-CAM: reutilizar compute_gradcam y GradCAMHookManager de explain_model.py,
stage4 (salida del bloque 64x64), escalar SI, ReLU, bilinear512x512,
align_corners=False, minmax y umbral1e-8 originales. Eval/BN intacta. Guardar
mapas inicial/seleccionado para todas las muestras y brazos; correlación y
solapamiento top10% frente a inicial, con mapas constantes explícitos.
Figuras con todos los arrays origin=upper, sin flips/transposes; B+=max(x,0),
B-=max(-x,0); B+-B- reconstruye exactamente el NPY. Ejes son píxeles del array,
sin WCS, máscaras regionales ni etiquetas físicas inventadas.

Reutilizar el procedimiento de borrado de /api/xai/faithfulness sin importar
ni modificar API: ordenar píxeles por saliencia y poner a cero ambas polaridades,
0/10/20/30/40/50/60/70/80/90/100% área. Desempate índice ascendente estable.
Tres órdenes aleatorios seed42/137/2026 (son auditoría, NO entrenamientos),
idénticos entre candidatos; guardar todas las predicciones y cambios en SI pp,
sin dividir por un output inicial casi cero, sin llamar al cambio error de target.
Integrar random_prediction-guided_prediction en fracción0..1; positivo solo
indica mayor descenso guiado. Igual área no igual geometría/contenido magnético:
registrar |B| retirado, artefactos OOD y sensibilidad a cero/fondo. No causalidad.
No barridos MC: función original sigue disponible; C1 mantiene cabeza0.3 y
Dropout2d p0; C0/C2 mantienen los cuatro Dropout2d y cabeza0.3.

## Filtros preliminares B

Ruta precisión, sin modificar umbrales B: mejora MAE>=0.01 frente V3.1;
RMSE incremento<=0.01, MAPE<=0.5pp, |sesgo|<=+0.01; MAE bandas/cola<=+0.01,
|sesgo| bandas<=+0.02, p95<=+0.02. Comparar también C1/C2 vs C0 seed42:
mejora y no degradación>0.005. IC exploratorio pareado de diferencia MAE,
bloques27 días TAI desde2016-02-03,2000 bootstrap seed2026. No test independiente.
Una semilla NO satisface estabilidad V3.2-D. Sin ONNX ni HTTP de candidatos
por instrucción; costos/paridad ONNX y bytes totales de servicio quedan pendientes,
no se declaran satisfechos. Duración/RSS/driver entrenamiento no sustituyen
latencia/RSS de inferencia de B. Conservar todos los resultados desfavorables.
No siguiente fase, commits, push, publicaciones ni cambios de producto.
