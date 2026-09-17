# V3.2-D — protocolo previo a los cuatro entrenamientos y controles nuevos

Reutilizar C0/C1 seed42 y controles de V3.2-C verificados por SHA-256. Ejecutar
secuencialmente, en procesos nuevos, seed137 C0, seed137 C1, seed2026 C0,
seed2026 C1. No C2, no reentrenamiento42, no pesos V3.1 para inicializar.
Arquitectura CoroniumV3 206875 parámetros (<512000), ECA/BN, datos/split
1051/263, target SI original y entrada clip400 B+/B− idénticos. Solo cambia
backbone dropout C0=.2/C1=0 dentro de cada semilla; cabeza=.3 siempre.

Se reutiliza literalmente el bucle C, con seed y ubicación parametrizadas:
MPS determinista float32, CPU4/interop1, batch8/workers0, AdamW lr.001 y
weight_decay1e-5, WeightedHuber delta1/alpha2, aumentaciones originales.
Selección mínimo MAE validation determinista (primero en empate); scheduler
ReduceLROnPlateau factor.5 patience3 min_lr1e-6 y parada patience10/min_delta0
monitorizan Weighted Huber determinista; máximo100 épocas. Métricas por
observación. Eval congela BN y apaga Dropout; sin MC ni XAI para selección.
Pesos iniciales propios por seed, archivo copiado idéntico a C0/C1. Órdenes
precalculados con generador privado seed; aumentaciones SHA256(seed,
augmentation,época,fila), dropout SHA256(seed,dropout,época,lote,capa), mismos
mecanismos C. Probabilidades distintas no permiten máscaras idénticas;
activaciones, BN, parada/scheduler divergen por tratamiento. Inicializaciones
y órdenes deben diferir entre42/137/2026. No transformaciones aprendidas con val.

Estimación previa a partir de piloto y tiempos C, sin nuevo piloto ni cambio
batch: ~84s/época como orientación; máximo400 épocas ~9.3h; C0/C1 anteriores
24.4/36.6min sugieren ~2h para cuatro brazos, sin garantía de parada similar.
Registrar recursos actuales antes de lanzar. Límites C driver14GiB/RSS16GiB/
disponibilidad512MiB. Parar secuencia por fallo, no finitos, inconsistencia o
recursos. No reiniciar ni sobrescribir brazo existente sin auditar artefactos.
Duraciones observadas con escritorio y posible análisis CPU concurrente;
no son benchmarks de inferencia. No exportación ONNX/HTTP/costos ahora.

## Evaluación y comparación fijadas

CPU float32 batch1, cuatro hilos/uno interop, eval sin aumentaciones sobre
train1051/val263 en orden C. No reelegir checkpoint en CPU. Conservar inicial,
best y final por brazo. Reusar predicciones42/constante/V3.1 de C, verificar
identidades/targets/hashes; evaluar nuevos iniciales y cuatro seleccionados.
Métricas float64 recalculadas desde CSV: MAE/RMSE/R2/MAPE/sesgo/p95 absoluto,
dispersión/correlación/rango; global, bandas <1.41/[1.41,1.75)/>=1.75 y SI>2.
Media, SD muestral ddof1, mínimo/máximo entre tres semillas por métrica;
diferencias C1−C0 emparejadas por seed, sin mezclar predicciones como ensemble.
Guardar también error por observación y bootstrap C: bloques27d TAI desde
2016-02-03,2000 réplicas seed2026. Intervalos por seed y promedio de diferencias
de error emparejadas dentro de cada observación, NO error de predicción promedio;
este último intervalo refleja observaciones condicionadas a solo tres semillas.

Guardas B sin cambios: mejora MAE>=.01 vsV3.1, mejora media vsC0 y ningún
seed empeora >.005; IC exploratorio deltaMAE inferior a cero. RMSE<=+.01,
MAPE<=+.5pp, |sesgo global|<=+.01, p95 absoluto global<=+.02; MAE cada
banda/cola<=+.01 y |sesgo banda/cola|<=+.02. Reportar por seed vsV3.1 y
C1vsC0 pareado y para medias de métricas. Para agregación de sesgo usar media
de valores absolutos por seed en la guarda (evita cancelar signos), además
de media/SD/rango del sesgo firmado. Reportar fallos individuales aunque la
media pase. R2 y p95 por banda descriptivos, sin nuevas guardas. Costos/paridad
ONNX/HTTP pendientes, no aprobados. Validation de selección, no test temporal.

## XAI dirigido fijado antes de nuevas mediciones

Mismas nueve identidades de C sin reselección. Auditado código original:
GradCAMHookManager(model,'stage4') captura salida completa del bloque128x64x64;
objetivo escalar SI, gradientes promediados espacialmente, suma por canales,
ReLU, bilinear512 align_corners=False, minmax original con umbral1e-8.
No cambiar capa, normalización o mapas para obtener mejor apariencia.
Reusar todos los mapas y oclusiones originales42. Calcular mapas originales
para inicial137/2026 y C0/C1 nuevos; guardar comparación con su inicial.
No repetir el barrido de píxeles dispersos: permanece evidencia histórica C.
Complemento nuevo común para 9 modelos (3 iniciales, C0/C1 x3 semillas):
ventanas cuadradas64x64 y128x128, enteras dentro del array512, sin wrap ni recorte.
Guiada = ventana de máxima suma del CAM con todas las posiciones posibles;
empate primer índice fila/columna. Aleatorias = cinco posiciones uniformes
válidas por seed de auditoría42/137/2026, 15 por tamaño, preguardadas antes de
inferir; mismas posiciones en todas las muestras/modelos, no rechazo por campo.
Así forma/área son idénticas, ubicación/contenido no. Guardar coordenadas de
array, máscara SHA, área, suma y fracción de |NPY| retirada, fracción de ceros,
predicción antes/después, delta firmado y absoluto; nunca error contra target
perturbado. Comparar guiada con distribución de15 controles, sin inferencia
causal ni pruebas de significación basadas en ventanas pseudorreplicadas.

Repetir descriptor C de suma CAM sobre valores NPY exactamente cero, por
muestra/banda/seed. NO máscara física del disco, WCS ni región activa. Las
ventanas pueden cruzar transiciones/campos/fondo; ceros externos, resolución,
interpolación, sesgos y normalización pueden influir. La oclusión crea bordes
artificiales y entradas fuera de distribución. Contactos de las9 muestras en
orden fijo: HMI[-1,1],B±[0,1],CAM[0,1], origin upper, sin flips/transposes;
comprobar B+−B−=NPY y alineación exacta de máscaras. Separar descripción visual,
soporte sobre ceros y respuesta del predictor; no demuestran mecanismo físico.
MC original disponible (cabeza.3 todos; cuatro Dropout2d .2 C0/0 C1), sin barridos.

## Referencia sencilla preregistrada

Contrato verificado en prepare_dataset.py/model_input.py: SI original cuenta
|B_LOS|>200G antes del resize, denominador todos los píxeles originales.
NPY = clip(resize(B_LOS),−400,400)/400. Proxy sin ajustar =
100*count(abs(NPY)>0.5)/(512*512). Umbral estricto200/400=.5, incluye ambos
signos y todos los píxeles del array en denominador, incluso ceros. Es una
aproximación en datos reducidos; resize/mezcla de polaridades/anti-aliasing
pueden cambiar cruces de umbral. No es recomputación exacta de SI original.
Registrar adicionalmente, sin sustituir versión cruda, calibración afín OLS
float64 y=a+b*proxy con intercepto, np.linalg.lstsq(rcond=None), solo1051train,
sin clipping ni búsqueda de umbral. Evaluar ambas versiones fijas en train/val,
incluso si desfavorecen CNN. Esta calibración es control separado, no cambia
preprocesamiento/modelo/producto. Fuentes, coeficientes y hashes conservados.

Diseño registrado antes de resultados D; implementación de análisis posterior
se versiona con UTC/hash antes de ejecutarse. No cambios de guardas tras ver
resultados. V3.1 y producto intactos, sin commits/push/deploy/deps/otra fase.
