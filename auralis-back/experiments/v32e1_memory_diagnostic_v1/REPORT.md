# FASE V3.2-E.1 — Diagnóstico de memoria

## Resultado y decisión

**Diagnóstico cerrado: la diferencia se reproduce y se localiza en la ruta Arm KleidiAI de ONNX Runtime 1.25.1, activada en este Apple M5.** Se conserva E íntegra. Una única mitigación de runtime, aplicada simétricamente a los cuatro modelos, elimina el exceso observado en las pruebas por etapas. No se cambiaron pesos, grafos ni producto. La aprobación de candidatos depende separadamente de las guardas de las dos rondas siguientes.

La evidencia atribuye el crecimiento a la caché nativa de tablas de convolución dependiente del contenido de las entradas de capa. Las diferencias de pesos producen distintas activaciones y, por esa vía, distinta reutilización de claves. No es un tamaño extra del checkpoint, otra arquitectura o una segunda copia de modelo. El patrón de entradas del banco y del diagnóstico de ruido activa esa retención del runtime.

La ruta PyTorch aislada no reproduce la separación entre semillas. No se identificó un defecto de retención en listas, autograd o hooks del banco que explique el salto. La causa confirmada es la ruta nativa; el conteo exacto de hashes y contribución por capa dentro del binario no se instrumentó. La relación específica pesos→cardinalidad por capa se infiere del código y los controles, no se presenta como un conteo directamente observado.

## Protocolo y protección

Apple M5,24GiB,macOS26.6.2,Python3.12.7,PyTorch2.11.0,ORT1.25.1,NumPy1.26.4. CPU FP32,batch1,4hilos intra/1inter; ORT_SEQUENTIAL,ORT_ENABLE_ALL. Mismas18 muestras y orden de E;10 calentamientos/60 repeticiones simples,3/30 solicitudes de ruido20+determinista, sigma0.005,seed42. Paridad:263 observaciones en orden original,atol=rtol=1e-5, sin cambiar tolerancias.

protocol.json/PROTOCOL.md se registraron antes de la primera medición. Las pruebas adaptativas tienen registros previos separados; intervention_registration.json fija una sola opción y orden de revalidación antes de sus resultados. Todos los procesos fueron nuevos y secuenciales. Sin entrenamiento concurrente detectado; no se interrumpieron servicios. Esta fase no abrió servidores HTTP: el banco relevante de guardas B/E reutiliza el handler real, sin transporte HTTP. El HTTP de E permanece como evidencia histórica; no se presenta como revalidación HTTP de la nueva opción.

Guarda RSS≤1.10×V3.1; p50/p95 forward y prepare+forward≤1.05×V3.1; pesos≤1.10×V3.1; parámetros<512000. Cada comparación usa misma configuración, composición de servicio y ronda. Una contradicción entre rondas es inconclusa. No se compensa memoria con omitir ruido. Las20 pasadas son un diagnóstico de ruido de entrada, no MC Dropout ni incertidumbre calibrada.

## Auditoría del banco y unidades

- Una instancia PyTorch para XAI y una sesión ORT por proceso del servicio equivalente. El wrapper referencia la misma sesión. No hay una V3.1 adicional residente al medir C1. Importar la API no ejecuta su lifespan.
- 18 arrays crudos+18 preparados suman54MiB. Respuestas, predicciones y210 registros de tiempo son escalares; la lista del handler se vacía por solicitud. La caché de resultados se limpia fuera del recorrido medido.
- El costo E no hace forwards PyTorch; la paridad sí los hace con inference_mode. En el componente PyTorch las salidas carecen de grad_fn, no se acumulan gradientes y no hay hooks. Grad-CAM requiere backward y no se ha modificado.
- Los procesos de grafos, paridad, hashes globales y fixtures se separan del costo. El monitor externo empieza al crear el hijo, incluidos imports y carga.
- RSS actual=psutil bytes; pico muestreado cada5ms; ru_maxrss=highwater de toda la vida, en bytes en macOS. Control64MiB: highwater20,135,936→87,228,416 bytes, compatible con64MiB más costes menores. MiB=bytes/2^20.
- La guarda usa max(pico externo,highwater del hijo); se conservan además las medidas internas B. Nunca se reinicia el máximo después del pico. Marcadores sub5ms pueden carecer de muestra RSS: se indican como tales.

Los cuatro ONNX tienen74 nodos, iguales operadores/conectividad/formas y constantes estructurales tras normalizar nombres y excluir pesos. Hash estructural común `ba182480f18905ee13d9028b1713b2ca1edd4479f14659efc8ee4de3081ff48c`. Los logs de V3.1/s137 muestran47 nodos optimizados asignados a CPU. Igualdad estática no se usó por sí sola como prueba de consumo idéntico.

## Memoria por componente y etapa

Última muestra RSS disponible dentro de cada etapa, MiB; última columna=pico conservador del proceso completo. Las etapas son acumulativas; no se suman como asignaciones exclusivas. PyTorch solo no ejecuta diagnóstico ONNX. El inicial/arranque, duración, picos por intervalo y todos los marcadores están en memory_stages.csv y runs/*/trace.csv.

### Configuración original: onnx

| Modelo | Imports | Checkpoint | Sesión | Entradas | Primer forward | Warmup | Fijo60 | Ciclo60 | Ruido3 | Ruido30 | Post60 | Pico |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| V3.1 | 47.73 | — | 56.03 | 98.38 | 419.53 | 493.17 | 493.17 | 516.47 | 1082.16 | 1628.41 | 1628.41 | 1628.41 |
| C1_s42 | 49.38 | — | sin muestra | 105.62 | 420.39 | 492.92 | 492.92 | 517.03 | 1091.80 | 1699.23 | 1699.23 | 1699.23 |
| C1_s137 | 45.72 | — | 54.36 | 82.17 | 421.16 | 493.50 | 493.50 | 498.67 | 1242.12 | 3121.72 | 3121.72 | 3121.72 |
| C1_s2026 | 49.62 | — | sin muestra | 109.30 | 420.81 | 493.28 | 493.28 | 500.50 | 1150.89 | 2595.45 | 2595.45 | 2595.45 |

### Configuración original: pytorch

| Modelo | Imports | Checkpoint | Sesión | Entradas | Primer forward | Warmup | Fijo60 | Ciclo60 | Ruido3 | Ruido30 | Post60 | Pico |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| V3.1 | 197.81 | 352.77 | — | 399.55 | 695.44 | 699.11 | 699.12 | 699.12 | — | — | — | 709.31 |
| C1_s42 | 197.45 | 343.88 | — | 395.64 | 693.83 | 694.06 | 694.08 | 695.27 | — | — | — | 700.86 |
| C1_s137 | 197.67 | 345.86 | — | 400.70 | 678.72 | 694.05 | 694.08 | 695.78 | — | — | — | 699.12 |
| C1_s2026 | 197.30 | 345.92 | — | 365.66 | 678.83 | 694.12 | 694.14 | 694.11 | — | — | — | 697.59 |

### Configuración original: both

| Modelo | Imports | Checkpoint | Sesión | Entradas | Primer forward | Warmup | Fijo60 | Ciclo60 | Ruido3 | Ruido30 | Post60 | Pico |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| V3.1 | 371.41 | 374.16 | 381.56 | 420.02 | 744.41 | 816.08 | 816.08 | 839.42 | 1403.06 | 1954.31 | 1954.31 | 1954.42 |
| C1_s42 | 371.55 | 372.64 | 380.14 | 405.31 | 741.77 | 816.61 | 816.61 | 841.45 | 1411.84 | 2035.67 | 2035.67 | 2035.75 |
| C1_s137 | 371.44 | 373.73 | 382.20 | 422.78 | 743.16 | 814.50 | 816.45 | 822.61 | 1549.36 | 3387.69 | 3387.69 | 3387.80 |
| C1_s2026 | 371.05 | 373.47 | 378.97 | 402.05 | 742.59 | 816.22 | 816.22 | 822.38 | 1473.02 | 2919.41 | 2919.41 | 2919.55 |

### Mitigación: ambos residentes

| Modelo | Imports | Checkpoint | Sesión | Entradas | Primer forward | Warmup | Fijo60 | Ciclo60 | Ruido3 | Ruido30 | Post60 | Pico |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| V3.1 | 371.36 | 374.36 | sin muestra | 388.00 | 520.73 | 588.78 | 588.78 | 588.78 | 599.81 | 599.81 | 599.81 | 600.47 |
| C1_s42 | 372.89 | 375.84 | sin muestra | 427.31 | 521.86 | 589.91 | 589.91 | 589.91 | 599.97 | 601.95 | 601.95 | 602.14 |
| C1_s137 | 372.59 | sin muestra | 378.66 | 438.83 | 521.33 | 589.38 | 589.38 | 589.38 | 600.23 | 600.22 | 600.22 | 600.25 |
| C1_s2026 | 371.53 | 374.38 | sin muestra | 438.02 | 520.78 | 588.83 | 588.83 | 588.83 | 599.80 | 601.78 | 601.78 | 602.50 |

### Localización y mecanismo

1. Con entrada fija, el RSS se estabiliza tras calentamiento. El ciclo determinista de18 entradas añade poco.
2. Con ruido, el RSS aumenta al recorrer nuevas muestras/perturbaciones. En s137 ONNX solo, las solicitudes3–17 de la tanda medida elevan el RSS hasta~3.1GiB; al repetir las muestras0–11 (solicitudes18–29), se mantiene aproximadamente estable. El determinista posterior tampoco sigue creciendo. Es retención dependiente de contenidos nuevos, no prueba de fuga continua por cada llamada.
3. Los logs de asignador muestran BFCArena estable en268452108 bytes después de calentamiento, mientras el RSS continúa aumentando. No se probó desactivar la arena ni un barrido de optimizaciones.
4. tracemalloc alcanza~72MiB: la mayor parte del exceso no se atribuye a objetos Python. Heap/malloc_history capturados con sesión aún viva sitúan cientos de MiB en ArmKleidiAI::MlasConv. Tras3 solicitudes de ruido:614513952 bytes V3.1 y774550304 s137 en esa categoría.
5. El código oficial v1.25.1 usa un mapa thread_local para tablas LHS, con una clave que incluye un hash de16float de la entrada de capa. No hay límite de entradas; solo se elimina el grupo anterior si cambia el buffer de padding. LhsPtrFill construye esas tablas a partir de geometría y padding, sin leer intensidades; incluir el hash de datos en la clave puede conservar tablas redundantes para una geometría. Las tablas contienen punteros/offsets y pueden ser grandes. Geometría idéntica no garantiza mismas claves ante activaciones diferentes.
6. Desactivar únicamente KleidiAI elimina la separación marcada entre los cuatro modelos en la carga observada, manteniendo ruido y modelos residentes. Esto triangula trazas, pilas nativas, fuente y control de intervención.

No se declara fuga solo porque RSS no baje. La retención thread_local y la política del asignador pueden persistir tras una solicitud o sesión; no se midió un horizonte indefinido de entradas nuevas. El máximo de un servicio prolongado bajo diversidad nueva queda sin certificar.

Fuentes oficiales conservadas y hasheadas: [convolve_kleidiai.cpp v1.25.1](https://github.com/microsoft/onnxruntime/blob/v1.25.1/onnxruntime/core/mlas/lib/kleidiai/convolve_kleidiai.cpp) y [opción de sesión v1.25.1](https://github.com/microsoft/onnxruntime/blob/v1.25.1/include/onnxruntime/core/session/onnxruntime_session_options_config_keys.h). Las dos fuentes coinciden byte a byte con el commit8a77e45942 declarado por el binario instalado (audit/runtime_binary.json y audit/upstream/build_commit_verification.json). No se extrapola el resultado a otra versión, proveedor o equipo.

### Limitaciones de instrumentación conservadas

runtime_logs activó logs de sesión pero no capturó la arena global; allocator_logs añadió el logger global. Ambos se conservan. native_attribution capturó vmmap después de salir de staged, cuando las referencias locales ya se habían liberado; sirve como observación de retención posterior, jamás como RSS de servicio. native_stacks corrigió esa ubicación, pausando dentro del frame vivo. MallocStackLogging/tracemalloc afectan el proceso: sus números no entran en guardas ni latencias. Sus logs íntegros y código quedan disponibles.

## Corrección experimental y paridad

Única mitigación: `o.add_session_config_entry("mlas.disable_kleidiai", "1")` antes de construir InferenceSession. No se parcheó ORT ni se actualizó ninguna dependencia. Es una propuesta para una eventual integración, comprobada solo en la copia experimental. No se necesita corregir una falsa lectura del banco original: el exceso de proceso era real.

| Modelo | n | máx \|ΔPT\| | media \|ΔPT\| | máx \|ΔONNX E\| | Exceden | MAE |
|---|---|---|---|---|---|---|
| V3.1 | 263 | 1.07288361e-06 | 2.8465184e-07 | 2.38418579e-07 | 0 | 0.20408341 |
| C1_s42 | 263 | 1.00135803e-05 | 4.29788017e-06 | 7.15255737e-07 | 0 | 0.04833448 |
| C1_s137 | 263 | 1.09672546e-05 | 5.68578452e-06 | 9.53674316e-07 | 0 | 0.05400831 |
| C1_s2026 | 263 | 7.51018524e-06 | 2.03834287e-06 | 9.53674316e-07 | 0 | 0.05186168 |

Todos los PyTorch nuevos reproducen exactamente los CSV de E. Paridad numérica combinada: |Δ|≤1e-5+1e-5×|referencia|, no igualdad bit a bit entre kernels. Un máximo absoluto ligeramente mayor que1e-5 puede cumplir esa tolerancia combinada. Se comparan valores completos, no redondeo público. CSV/JSON de parity/ conservan263 identidades/targets/predicciones por modelo y MAE,RMSE,R²,MAPE,sesgo,p95 global y por bandas/cola; las métricas no se mezclan entre semillas.

## Revalidación del banco B/E: dos rondas

Se reutilizó B.cost sin cambiar su cuerpo:60 tiempos por recorrido simple y30 del handler original (20ruido+det), calentamientos10/3 y orden interno RNG42. Una sesión+un PyTorch residente. Ronda1:V3.1,s42,s137,s2026, cada uno default→off. Ronda2:s2026,s137,s42,V3.1, cada uno off→default.16 procesos; se conservan todos los tiempos y rondas. No hay profiler ni liberaciones forzadas.

### default

| Ronda | Modelo | Pico MiB | Forward p50/p95 ms | Prepare p50/p95 ms | Carga+prepare p50/p95 ms | Handler21 p50/p95 ms |
|---|---|---|---|---|---|---|
| 1 | V3.1 | 2012.14 | 22.30 / 23.00 | 22.50 / 22.97 | 22.77 / 23.20 | 510.92 / 514.28 |
| 1 | C1_s42 | 2086.34 | 22.27 / 22.81 | 22.50 / 22.95 | 22.74 / 23.14 | 512.11 / 525.79 |
| 1 | C1_s137 | 3539.75 | 22.23 / 22.65 | 22.49 / 22.88 | 22.73 / 25.80 | 516.65 / 526.29 |
| 1 | C1_s2026 | 2926.80 | 24.75 / 25.67 | 24.87 / 25.60 | 25.02 / 29.29 | 561.71 / 631.61 |
| 2 | V3.1 | 1979.70 | 24.85 / 25.59 | 24.97 / 25.88 | 25.06 / 25.78 | 563.36 / 569.47 |
| 2 | C1_s42 | 2035.86 | 24.92 / 25.67 | 25.03 / 26.57 | 25.06 / 27.16 | 563.10 / 569.41 |
| 2 | C1_s137 | 3444.95 | 24.76 / 25.45 | 25.03 / 25.56 | 25.14 / 25.81 | 571.06 / 604.19 |
| 2 | C1_s2026 | 2932.53 | 24.69 / 25.26 | 25.02 / 25.68 | 25.07 / 25.53 | 569.31 / 581.91 |

### kleidiai_off

| Ronda | Modelo | Pico MiB | Forward p50/p95 ms | Prepare p50/p95 ms | Carga+prepare p50/p95 ms | Handler21 p50/p95 ms |
|---|---|---|---|---|---|---|
| 1 | V3.1 | 610.61 | 20.33 / 20.60 | 20.57 / 20.84 | 20.90 / 21.18 | 472.65 / 474.95 |
| 1 | C1_s42 | 605.56 | 19.88 / 20.28 | 20.15 / 20.38 | 20.47 / 20.73 | 462.75 / 468.53 |
| 1 | C1_s137 | 607.47 | 19.51 / 20.14 | 19.77 / 20.12 | 20.05 / 20.23 | 452.76 / 454.54 |
| 1 | C1_s2026 | 613.66 | 21.23 / 22.39 | 21.48 / 22.60 | 21.90 / 23.39 | 492.40 / 583.57 |
| 2 | V3.1 | 613.53 | 21.29 / 22.85 | 21.55 / 23.50 | 21.96 / 23.71 | 491.86 / 512.00 |
| 2 | C1_s42 | 613.55 | 21.17 / 23.19 | 21.53 / 22.89 | 21.91 / 24.04 | 491.22 / 539.60 |
| 2 | C1_s137 | 609.72 | 21.05 / 22.66 | 21.49 / 22.58 | 21.81 / 22.76 | 492.53 / 508.70 |
| 2 | C1_s2026 | 613.08 | 21.09 / 22.72 | 21.77 / 22.99 | 21.86 / 22.79 | 493.59 / 518.63 |

“Carga” en esa tabla es lectura del NPY con filesystem caliente, como B/E; no creación de sesión ni arranque del proceso. Handler directo no es HTTP. RSS incluye los temporales del diagnóstico, librerías, modelo PyTorch/ORT, entradas y caches nativas; no el proceso monitor (~decenas de MiB).

### Guardas por configuración, modelo y ronda

| Configuración | Modelo | RSS ratio R1/R2 | Forward p50 ratio R1/R2 | Forward p95 ratio R1/R2 | Prepare p50 ratio R1/R2 | Prepare p95 ratio R1/R2 | Dictamen |
|---|---|---|---|---|---|---|---|
| default | C1_s42 | 1.0369 / 1.0284 | 0.9990 / 1.0027 | 0.9917 / 1.0032 | 1.0002 / 1.0024 | 0.9992 / 1.0265 | cumple |
| default | C1_s137 | 1.7592 / 1.7401 | 0.9968 / 0.9962 | 0.9844 / 0.9945 | 0.9999 / 1.0025 | 0.9961 / 0.9875 | incumple |
| default | C1_s2026 | 1.4546 / 1.4813 | 1.1098 / 0.9934 | 1.1158 / 0.9872 | 1.1055 / 1.0020 | 1.1146 / 0.9923 | inconcluso |
| kleidiai_off | C1_s42 | 0.9917 / 1.0000 | 0.9777 / 0.9943 | 0.9843 / 1.0148 | 0.9794 / 0.9993 | 0.9778 / 0.9743 | cumple |
| kleidiai_off | C1_s137 | 0.9949 / 0.9938 | 0.9594 / 0.9890 | 0.9777 / 0.9916 | 0.9611 / 0.9973 | 0.9651 / 0.9610 | cumple |
| kleidiai_off | C1_s2026 | 1.0050 / 0.9993 | 1.0439 / 0.9905 | 1.0869 / 0.9943 | 1.0438 / 1.0101 | 1.0842 / 0.9785 | inconcluso |

El dictamen detallado por guarda está en cost_guards.json. s2026 con runtime original incumple RSS en ambas rondas: la etiqueta global inconclusa refleja además conflictos de latencia y nunca permite aprobar ese incumplimiento conocido. Se comparan modelos bajo el mismo runtime; un efecto del opt-out frente a default se informa aparte, no se usa para ocultar una guarda del candidato.

### Efecto del runtime, mismo modelo

| Ronda | Modelo | RSS off/default | Forward p50/p95 off/default | Prepare p50/p95 off/default |
|---|---|---|---|---|
| 1 | V3.1 | 0.3035 | 0.9119 / 0.8955 | 0.9146 / 0.9076 |
| 1 | C1_s42 | 0.2903 | 0.8925 / 0.8888 | 0.8956 / 0.8883 |
| 1 | C1_s137 | 0.1716 | 0.8776 / 0.8894 | 0.8790 / 0.8794 |
| 1 | C1_s2026 | 0.2097 | 0.8578 / 0.8723 | 0.8635 / 0.8829 |
| 2 | V3.1 | 0.3099 | 0.8566 / 0.8930 | 0.8631 / 0.9079 |
| 2 | C1_s42 | 0.3014 | 0.8495 / 0.9034 | 0.8604 / 0.8616 |
| 2 | C1_s137 | 0.1770 | 0.8504 / 0.8904 | 0.8586 / 0.8835 |
| 2 | C1_s2026 | 0.2091 | 0.8541 / 0.8995 | 0.8700 / 0.8952 |

### Resultados originales de E, preservados

| Modelo | Pico E R1/R2 MiB | Parámetros | Checkpoint bytes | ONNX bytes | Pesos totales bytes |
|---|---|---|---|---|---|
| V3.1 | 1992.47 / 1998.98 | 206875 | 848269 | 835234 | 1683503 |
| C1_s42 | 2073.67 / 2097.11 | 206875 | 846093 | 835234 | 1681327 |
| C1_s137 | 3522.41 / 3498.39 | 206875 | 846093 | 835234 | 1681327 |
| C1_s2026 | 2928.62 / 2928.94 | 206875 | 846093 | 835234 | 1681327 |

Todos cumplen tamaño (+10%) y parámetros (<512000). Logs y cachés del experimento no son artefactos para servir. Continúa vigente SERVING_SCOPE.md de E: pesos propios por modelo incluyen checkpoint XAI+ONNX autocontenido; dependencias y metadatos son necesarios aparte. No se ha empaquetado un release candidato.

## Presión externa, incertidumbre y pendientes

Durante los16 bancos: mínimo disponible del sistema 8.81GiB; máximos/deltas de CPU, swap y RSS del monitor en system_conditions.csv; snapshots de procesos y vm_stat antes/después en cada run. No se activó ninguna interrupción de seguridad. La actividad normal de escritorio no está eliminada; dispersión o conflictos de guardas se conservan como inconclusos. No se atribuye latencia inestable automáticamente a presión externa.

El opt-out está probado en este Mac, no en móvil ni equipo de bajos recursos. No se certifica servicio de duración indefinida, transporte HTTP/fixtures con el nuevo runtime ni Grad-CAM con esta opción (no se cambió el modelo PyTorch). La paridad263 requerida sí está completa. La configuración por defecto conserva su problema; esta fase no la corrige en producto.

## Recomendación y cierre

Mantener el bloqueo de aprobación de C1: el diagnóstico de memoria y su mitigación están resueltos para la carga observada, pero las guardas de costo incluyen resultados incumplidos o inconclusos. Recomiendo una siguiente comprobación acotada de la(s) latencia(s) señalada(s), previamente registrada y con referencia/candidatos simétricos; no un barrido para elegir un resultado favorable. No se inicia aquí.

Resolver memoria no resuelve las dudas XAI sobre borde/fondo, el deterioro tolerado en baja actividad ni el uso de validation para selección de checkpoint. Las263 observaciones no se convierten en test independiente o temporal. No se entrenó, reexportó, cuantizó, recalibró BN ni eligió una semilla.

Verificación: 251 comprobaciones;4382 archivos protegidos y154 hashes de entregables E intactos. Scripts y trazas: REPRODUCE.md, artifact_hashes.json, verification.json. Fuentes y registros originales preservados; no commits,push,publicación ni cambios de dependencias. V3.1 sigue activa y el producto aprobado permanece intacto.

**FASE V3.2-E.1: CUMPLIDA** — cierre del diagnóstico y de la revalidación solicitada; no aprobación del candidato. No se comenzó otra fase.
