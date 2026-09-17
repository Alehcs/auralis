# V3.2-E — registro previo, ruta precisión de B

Solo candidatos no promovidos. V3.1 activa y todo producto protegido. Reusar C1
seleccionados s42 época27, s137 época60, s2026 época55, verificados contra
manifiestos/completion/config de C/D. Sin entrenamiento, recalibración BN,
cambio de arquitectura, datos, split, target o preprocesamiento. Sin ensemble.

Exportar mediante la función existente export_to_onnx.export_onnx, sin editarla:
eval CPU FP32, backbone p0/cabeza .3 inactivos, BN congelada, opset18,
dynamo=False, external_data=False, constant folding y batch dinámico. Checker
obligatorio, entrada (N,2,512,512) clip400/B+/B− y salida SI original. Hash del
estado en memoria antes/después y del archivo. Cada artefacto experimental único.

Paridad principal: 263 filas en orden y targets exactos de D, CPU FP32 batch1,
4 intra-op/1 inter-op; ORT_SEQUENTIAL/ORT_ENABLE_ALL/CPUExecutionProvider.
Criterio B: |ONNX−PT| <= 1e-5 + 1e-5*|PT|, antes de redondeo. No relajar.
Repetición PyTorch debe reproducir CSV D dentro de idéntica tolerancia; informar
además coincidencia exacta. Métricas float64 desde outputs completos para ambos,
D y ONNX: MAE/RMSE/R²/MAPE/sesgo/p95 absoluto, global/bandas/cola SI>2.
Chequeo suplementario batch2 con primeras dos filas, tolerancias idénticas.
También volver a evaluar V3.1 para referencia actual y comparación histórica.

Costo: reutilizar cost() de B, mismas 18 observaciones y orden fijado por B;
10 calentamientos/60 repeticiones forward, prepare+forward y load+prepare+forward
(filesystem caliente). Handler original: 3/30; orden intercalado seed42. Guardar
cada tiempo sin eliminar atípicos. Dos rondas independientes, proceso nuevo por
modelo/banco; ronda1 V3.1/s42/s137/s2026, ronda2 orden inverso. No bancos paralelos
ni entrenamientos concurrentes; registrar procesos y carga antes/después.
Mismo proceso importa API/dependencias/XAI y retiene un PyTorch y un ORT por
modelo, incluso V3.1. B cost original solo importaba PyTorch sin residente:
esa diferencia queda corregida de manera simétrica en E; comparar candidatos
contra V3.1 REMEDIDA E, no contra aquel RSS. Forward excluye preparación/carga.
Carga significa NPY, no startup; arranque/carga de modelos separado.

RSS a5ms de B, etapas imports/PyTorch/ORT/inputs, pico muestreado controlado
primario y ru_maxrss vitalicio separados. No restar bibliotecas para inventar
memoria exclusiva de modelo. Cachés/temporales incluidos; muestreo puede perder
picos breves. Peso requerido por servicio equivalente = checkpoint XAI + ONNX
completo, metadatos/contrato por separado; logs/CSV de investigación no son pesos.

HTTP loopback real: subprocess por modelo/ronda, puerto efímero reservado,
1worker/1cliente persistente sin concurrencia. Handler original para A=20 ruidos
Gaussian sigma.005 seed42 + determinista. B clona AST del handler eliminando
solo cálculo de ruido, uncertainty=null y método='no calculado'; mismo parsing,
preparación, clasificación, heurística de confidence y caché separada.
No modifica src/api/main.py. Cache fría significa solo caché de resultados
limpiada fuera del reloj, modelos/filesystem/conexión calientes. B mismo banco
3 calentamientos/30 frías por modo y60 calientes por modo, orden intercalado
seed42. Verificar21/1/0 forwards y valor crudo EXACTAMENTE igual entre A/B,
contra ONNX offline y redondeo4 decimales. Diagnóstico no es MC Dropout ni
incertidumbre calibrada; confidence sigue heurística.

Fixtures: reusar11 ejemplos de reports/phase17_coronium_v3_1/http_parity.json
(9 cuantiles + extremos temporales), sin selección posterior. Predicción, alias
con caché vacía y upload NPY512² y dual2x512² preparados por helper existente,
en ambos modos. Comparar hash de input y valor crudo capturado en última pasada;
respuesta pública exacta al ONNX redondeado. Fuera de latencia; reiniciar trazas
por petición y almacenar solo última salida/contador, sin retener arrays.

Guardas B precisión sin modificación: mejora MAE>=.01 vsV3.1; media mejora C0 y
ninguna semilla deteriora>.005; IC emparejado bloques27 días/2000 seed2026<0.
RMSE+.01, MAPE+.5pp, |sesgo|+.01, p95 absoluto+.02; MAE bandas/cola+.01 y
|sesgo|+.02. R²/p95 bandas informativos. Agregado media métricas y media |sesgo|,
NO predicción ensemble. Costos: p50/p95 forward y prepare+forward<=1.05 V3.1,
pico RSS controlado<=1.10, bytes pesos requeridos<=1.10, parámetros<512000.
Examinar cada ronda y semilla; conflicto entre rondas = inconcluso para esa
guarda, nunca elegir la favorable. Agregado no borra un fallo individual.
No ruta costo ni compensar costos del modelo con retirar ruido. HTTP efectos
modelo manteniendo modo y efectos ruido manteniendo modelo se reportan separados.

Límites: validation de selección, deterioro bajo tolerado y dudas borde/fondo
persisten. Solo Mac disponible; no extrapolar equipos modestos, móviles o GPU.
No promoción, integración de producto, cuantización, barridos XAI, commit/push/
publicación o siguiente fase. Registros originales nunca sobrescritos. Si un
fallo requiere corregir implementación, guardar fuente/incidente antes de reintentar.
