# FASE V3.2-B — referencia medida y protocolo propuesto

Fecha: 2026-09-14. V3.1 sigue activa. No se entrenó, exportó ni promovió ningún
modelo. Todos los archivos nuevos pertenecen a este directorio. El protocolo
primario se registró a las 2026-09-14T15:45:37.678327+00:00; su SHA-256 es
`7719a5e5feecd2e3e7fd8980fca81b435c76845d086f88f48f82772536fa8982`. Los acuerdos de promoción NO están aprobados.

## Referencia y condiciones

Apple M5, 24 GiB, 10 núcleos físicos/lógicos; macOS 26.6.2 arm64. Hardware leído
mediante sysctl con permiso; versiones completas y orden exacto en protocol.json.
Python 3.12.7, PyTorch 2.11.0, ONNX Runtime 1.25.1, NumPy 1.26.4; CPU float32,
batch1, cuatro hilos intra-op/uno inter-op, ORT_SEQUENTIAL/ORT_ENABLE_ALL.
No GPU utilizada. En procesos sandbox MPS figura no disponible; eso no cambia
la selección CPU explícita del banco HTTP ejecutado fuera de sandbox.

Los 263 nuevos resultados ONNX coinciden exactamente con los guardados (máximo
desacuerdo 0). MAE **0.20408340 SI pp**, RMSE 0.25823317, R²
0.45371922, MAPE 10.49751499%, sesgo -0.18687747 SI pp.
MC oficial guardado: MAE 0.10155762, MPS batch32 T20 seed42; no se repitió ese
ensayo ya respaldado. Son métricas de validation utilizada para selección.

| Grupo | n | MAE SI pp | Sesgo SI pp | p95 error absoluto SI pp |
|---|---:|---:|---:|---:|
| Global | 263 | 0.20408340 | -0.18687747 | 0.48784542 |
| Baja | 43 | 0.05174790 | +0.04363687 | 0.11659800 |
| Media | 96 | 0.10290537 | -0.09849272 | 0.25692502 |
| Alta | 124 | 0.33524079 | -0.33524079 | 0.56435478 |
| Cola SI>2 | 71 | 0.39714738 | -0.39714738 | 0.57509518 |

206875 parámetros. Checkpoint 848269 bytes; ONNX 835234 bytes sin datos externos;
ambos archivos requeridos por el servicio actual suman 1683503 bytes. Se
verificaron los seis hashes de artefactos y catorce referencias de promoción.
Ese tamaño no incluye dependencias y no representa memoria de ejecución.

## Diagnóstico MC acotado

18 ejemplos preseleccionados solo por target, seis cuantiles por banda; mismo
CPU, batch1 y orden, T20 en cada modo estocástico, semillas 42/137/2026.
Se conservaron todas las 3240 pasadas estocásticas; medias calculadas en float64
desde outputs float32. El rango entre semillas NO es un intervalo de confianza.
No extrapolar estas métricas a las 263 observaciones: el subconjunto cambia
la proporción de bandas y sobrerrepresenta extremos por diseño.

| Modo | MAE medio de 3 semillas, SI pp | Rango MAE | Desplazamiento medio respecto a eval, SI pp |
|---|---:|---:|---:|
| Eval determinista | 0.182100 | — | 0 |
| MC completo | 0.123436 | 0.113976–0.128314 | +0.171382 |
| Solo cabeza | 0.186823 | 0.185484–0.188078 | -0.005528 |
| Solo backbone | 0.124049 | 0.120424–0.127678 | +0.170987 |

**Hechos:** activar dropout del backbone produce el desplazamiento ascendente
en las tres semillas; cabeza sola no corrige la brecha. En MC completo, el error
absoluto esperado de una pasada estocástica es 0.166436,
frente a 0.123436 para la media T20:
el promedio aporta reducción de error, pero no explica por sí solo el cambio
sistemático de nivel. Cada modo conserva exactamente state_dict (incluye BN),
y volver a eval reproduce exactamente la predicción inicial. No se recalibró BN.

**Hipótesis:** la distribución inducida por dropout del backbone atraviesa
convoluciones/no linealidades y estadísticas BN aprendidas con dropout anterior.
Los resultados localizan el mecanismo a ese camino, pero NO aíslan cuánto
corresponde a BN, ECA, activaciones o selección por MC. Desactivar dropout al
evaluar pesos existentes tampoco demuestra qué ocurrirá al reentrenar sin él.

## Latencia real y costo del ruido

| Trabajo | n | p50 ms | p95 ms |
|---|---:|---:|---:|
| ONNX, entrada dual residente | 60 | 22.213 | 22.651 |
| Preparación NPY residente + ONNX | 60 | 22.429 | 22.773 |
| Carga NPY + preparación + ONNX; filesystem caliente | 60 | 22.751 | 25.871 |
| Handler original directo, sin caché (21 forwards) | 30 | 509.694 | 519.650 |
| HTTP original, caché de resultados fría | 30 | 509.515 | 511.581 |
| HTTP banco sin diagnóstico, caché fría | 30 | 23.338 | 23.678 |
| HTTP original, caché caliente | 60 | 0.321 | 0.343 |
| HTTP banco sin diagnóstico, caché caliente | 60 | 0.336 | 0.373 |

Desglose del handler original: veinte forwards ruidosos p50
447.887 ms / p95 456.649;
forward determinista p50 22.276 / p95
22.658; resto p50 39.614
/ p95 42.661. El resto incluye RNG, lectura,
preparación y trabajo Python; no es exclusivamente generación de ruido.
Las medianas/p95 de componentes no deben sumarse; la suma exacta se comprobó
en cada registro individual. Todas las variantes conservaron el SI determinista.

Diez warmups para forward/preparación y 60 repeticiones; tres para handler/HTTP
y 30 solicitudes frías, 60 calientes. HTTP real mediante httpx, conexión
persistente loopback, un worker, sin concurrencia. Se reutilizó el app y handler
original en un proceso privado; solo se fijaron motores CPU/hilos y rutas del
banco. Nunca se contactó el servicio activo. Caché fría significa resultados
vacíos con modelo, conexión y filesystem calientes. HTTP caliente añadió cero
forwards; no es evidencia de inferencia submilisegundo. Alias/upload se
comprobaron adicionalmente en un ejemplo, fuera del timing.

El banco sin diagnóstico devuelve uncertainty=null, marcado como no calculado;
su payload tiene una diferencia menor de tamaño/serialización. No modifica
semántica ni código del servicio real. Preparación significa polaridades desde
NPY clip400, no decodificar FITS ni rehacer resize. El arranque HTTP observado
(1237.6 ms) es una única observación fuera del
benchmark estable, no p50/p95 de arranque. No se probó red pública, TLS o navegador.

## Memoria y operadores

El suplemento memory_protocol.json se registró ANTES de sus nuevas mediciones,
porque el RSS acumulado del banco mixto no permitía atribuir memoria al ruido.
Dos procesos nuevos, mismos imports y ambos motores residentes, mismas 18
muestras cíclicas, tres warmups y treinta cargas/solicitudes sin caché cada uno.

| Proceso CPU | RSS tras cargar ambos motores, MiB | Pico RSS muestreado, MiB | ru_maxrss, MiB |
|---|---:|---:|---:|
| Una pasada, proceso nuevo | 383.33 | 805.59 | 805.59 |
| 20 ruido + 1 punto, proceso nuevo | 383.23 | 1866.25 | 1866.25 |

RSS de todo el proceso, no memoria exclusiva de pesos/tensores. Incluye librerías,
allocators, entradas y temporales. Muestreo cada 5ms, ru_maxrss de vida completa,
sin medición GPU. La diferencia observada entre brazos es local al trabajo
registrado y necesita repetición para una decisión de promoción. No demuestra
una fuga: el brazo de ruido se estabilizó en la parte final de las 33 llamadas.
La retención/caché de allocators es hipótesis; aislarla requeriría otra prueba.
El servidor HTTP mixto llegó a 1933.36 MiB;
su cliente separado terminó en 59.14 MiB.

Perfil CPU separado, tres forwards PyTorch y seis ONNX sobre la primera muestra
predeclarada. ORT atribuye aproximadamente 89.5% del tiempo acumulado
de nodos a FusedConv. PyTorch destaca convolución, MaxPool y BatchNorm. Exportar
en eval ya fusiona BN en ONNX. Los eventos de asignación/liberación del profiler
no son pico RSS, y los tiempos instrumentados no sustituyen la tabla de latencia.

Estos resultados describen este M5 de 24 GiB. No certifican rendimiento o
viabilidad en teléfonos, Raspberry Pi u otros equipos de pocos recursos.

## Protocolo de candidatos y criterios pendientes de aprobación

Se mantiene train=1051 y validation=263. Validation ya seleccionó checkpoints
y parada de V3.1; train ya ajustó pesos. Los datos fueron inspeccionados en
auditorías/demos. No existe test independiente demostrado. No se cambió el
split ni se descargaron datos. Una partición temporal de datos expuestos será
exploratoria; un test independiente requiere auditar y reservar datos no usados.

Propuesta completa en PROTOCOL.md, congelada antes de medir. Métrica primaria:
MAE determinista SI pp. Comparar mismos datos/orden/motor/hilos/batch/dtype,
misma política de diagnóstico y caché, V3.1 congelada y control por semilla.

- **Ruta precisión:** MAE al menos 0.01 SI pp menor; latencias p50/p95 no >+5%,
  memoria no >+10%, artefactos completos no >+10%.
- **Ruta costo:** reducción de al menos 15% en p50 y p95 de forward y
  prepare+forward, o 20% RSS pico, o 20% bytes. Elegir dimensión antes del ensayo;
  MAE no aumenta >0.005 SI pp. Mantener límites de costo en otras dimensiones.
- **Guardas:** RMSE +0.01 máximo; MAPE +0.5 puntos porcentuales; |sesgo global|
  +0.01; MAE por banda y cola SI>2 +0.01; |sesgo por banda| +0.02; p95 de error
  +0.02 SI pp. Siempre <512000 parámetros. Ninguna semilla empeora MAE >0.005
  frente a su control; paridad FP32 atol=rtol=1e-5 y redondeo HTTP coherente.
- Guardar todas las semillas/repeticiones, no escoger la favorable. Incertidumbre
  pareada exploratoria por bloques temporales predefinidos; no independiente.
  Dos procesos de medición de costo en C. Compresión requiere tolerancia propia
  aprobada antes, sin relajar guardas. Mejorar solo el endpoint no crea V3.2.

Son acuerdos experimentales propuestos, no hechos científicos ni autorización.
Si no se cumplen mejoras/guardas/paridad/comparabilidad, conservar como experimento
y mantener V3.1. No ajustar umbrales después para favorecer un candidato.

## Plan mínimo V3.2-C, no iniciado

Máximo nueve entrenamientos: tres configuraciones × seeds42/137/2026, máximo
100 épocas/paciencia10. Primero control con arquitectura/pérdida/dropout V3.1
y selección, scheduler y parada por MAE determinista. Después mismo control
sin Dropout2d de backbone, cabeza0.3. Tercero, si se aprueba, backbone0.1,
cabeza0.3. No mezclar cambios de loss/ECA/stride/cuantización. El diagnóstico B
justifica ese orden, no anticipa el resultado de entrenar candidatos.

## Archivos, verificación y pendientes

Reutilizados: models/active_model.py, processing/model_input.py,
models/train_model.py y api/main.py sin editar; manifests/predicciones y método
de timing de Fases1.5–1.7. Scripts nuevos: benchmark.py, http_benchmark.py,
memory_isolation.py y este analizador. protocol.json/PROTOCOL.md y suplemento
fijan condiciones; results conserva registros por llamada, todas las pasadas,
memoria y trace ORT. protected_before.json y verification.json documentan
integridad de 3350 archivos protegidos; analysis_checks.json verifica hashes,
identidades/targets, medias MC y cuantiles de latencia de forma independiente.

La primera apertura loopback fue rechazada por el sandbox; se ejecutó el MISMO
banco con permiso, sin cambiar protocolo ni servicio. El servidor se cerró
limpiamente, con estado PyTorch intacto. Font cache aislado en runtime-cache;
sin instalación o actualización de dependencias. No commits/push/publicación.

Pendientes: aprobación de criterios antes de entrenar; opcionalmente rescoring
exploratorio de trece checkpoints de mejora (no están todos los pesos de las
50 épocas); mecanismo BN/no linealidad no aislado; repetición independiente de
costos y memoria para promoción; carga concurrente, arranque repetido, disco
frío, GPU y hardware de bajos recursos distinto. Ninguno se presenta como medido.

**FASE V3.2-B: CUMPLIDA. V3.2-C no iniciada.**
