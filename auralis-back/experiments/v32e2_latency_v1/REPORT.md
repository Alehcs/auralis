# FASE V3.2-E.2 — Latencias y costo de la mitigación

## Resultado

Se completaron las cuatro rondas registradas: 16 procesos nuevos, 216 tiempos por recorrido y brazo, **6.912 mediciones** en total. Cada proceso mantiene un PyTorch y una sesión ONNX. Todos los tiempos se conservan, sin descartar atípicos, reemplazar rondas ni ampliar el presupuesto.

| Comparación | Forward | Preparación + forward |
|---|---|---|
| Efecto del modelo: C1_s2026 mitigado / V3.1 mitigado | cumple | cumple |
| Efecto del runtime en V3.1: mitigado / original | cumple | cumple |
| Efecto del runtime en C1_s2026: mitigado / original | cumple | cumple |
| Cambio completo: C1_s2026 mitigado / V3.1 original | cumple | cumple |

Cada dictamen aplica el límite de +5 % a p50 y p95 en todas las rondas. No se usa una media favorable para borrar incumplimientos. Completar esta fase no aprueba al candidato ni autoriza cambiar el servicio.

## Protocolo y trazabilidad

Se revisaron los protocolos B/E/E.1, sus resultados y scripts reales. En E.1, s2026 mitigado dio p95 de forward +8,69 % / −0,57 % y preparación +8,42 % / −2,15 % frente a V3.1 mitigado: conflicto entre sus dos rondas. No se cambió la semilla ni el checkpoint seleccionado (s2026, época 55; V3.1, época 40).

Configuración reutilizada directamente de `E.1/intervention.py`: `SessionOptions.add_session_config_entry("mlas.disable_kleidiai", "1")`. El brazo original no añade esa entrada. CPUExecutionProvider, FP32, batch 1, cuatro hilos intra-op y uno inter-op, ORT_SEQUENTIAL, ORT_ENABLE_ALL, arena y memory-pattern por defecto. No se inventó otra opción ni se cambió el runtime instalado.

Entorno comprobado: Apple M5, 24 GiB, macOS-26.6.2-arm64-arm-64bit; Python 3.12.7, ORT 1.25.1, PyTorch 2.11.0, NumPy 1.26.4. El binario ORT coincide por SHA-256 con E.1; commit de build 8a77e45942. protocol.json conserva versiones, hardware, fuentes, artefactos y hashes de las 18 entradas antes de medir.

| Brazo | Modelo | Runtime |
|---|---|---|
| A | V3.1 | default |
| B | V3.1 | kleidiai_off |
| C | C1_s2026 | default |
| D | C1_s2026 | kleidiai_off |

| Ronda | Orden |
|---|---|
| 1 | A → B → D → C |
| 2 | B → C → A → D |
| 3 | C → D → B → A |
| 4 | D → A → C → B |

Diseño equilibrado: cada brazo ocupa cada posición una vez y las 12 transiciones dirigidas entre brazos aparecen una vez dentro de las rondas. Procesos nuevos y secuenciales; sin entrenamiento u otro banco detectado. No se cerraron aplicaciones del usuario.

Las 18 observaciones son las mismas de E/E.1. Diez calentamientos por recorrido (índices 0–9); después 12 ciclos completos de 18 = 216 mediciones por recorrido. Orden de los dos recorridos intercalado con RNG NumPy seed 42, idéntico para todos. Ventanas `perf_counter_ns`: incluyen preparación únicamente en su recorrido y conversión de salida escalar, como B. Excluyen hashes, comparaciones, profiling, serialización, carga de archivos/modelos, HTTP y ruido.

Se importó la API y se mantuvo su composición PyTorch/XAI, sin ejecutar Grad-CAM ni modificar su tratamiento de gradientes. Estas son mediciones aisladas de un solo forward; no se eliminó el diagnóstico del producto ni se le atribuye ahorro por omitir sus veinte pasadas. La latencia del handler con ruido y la latencia HTTP completa no se vuelven a medir aquí.

## Cuatro rondas: tiempos en milisegundos

Cada celda contiene **p50 / p95**, con 216 mediciones. Los 6.912 tiempos individuales, identidad de brazo/muestra, salida y timestamps monotónicos están en `timings.csv` y `runs/round*/<brazo>/timings.csv`. No se redondearon los datos usados para decidir.

| Ronda | Posición | Brazo | Forward p50 / p95 | Preparación + forward p50 / p95 |
|---|---|---|---|---|
| 1 | 1 | A | 24.9418 / 25.4461 | 25.0291 / 25.6291 |
| 1 | 2 | B | 20.5125 / 21.8232 | 20.7926 / 22.2455 |
| 1 | 3 | D | 21.0927 / 22.4046 | 21.4247 / 22.9310 |
| 1 | 4 | C | 24.8955 / 25.4336 | 25.0787 / 25.5841 |
| 2 | 1 | B | 21.2305 / 22.6047 | 21.6285 / 22.9926 |
| 2 | 2 | C | 24.9943 / 30.6223 | 25.0862 / 28.7835 |
| 2 | 3 | A | 24.8997 / 25.6750 | 25.0357 / 25.7454 |
| 2 | 4 | D | 21.5991 / 23.1583 | 21.9533 / 23.3425 |
| 3 | 1 | C | 24.9139 / 25.7385 | 25.0933 / 26.2736 |
| 3 | 2 | D | 21.3994 / 22.8228 | 21.6811 / 23.1941 |
| 3 | 3 | B | 21.2119 / 22.5820 | 21.5416 / 22.9401 |
| 3 | 4 | A | 24.9263 / 25.4984 | 25.0691 / 25.7938 |
| 4 | 1 | D | 21.1204 / 22.5402 | 21.5259 / 23.0503 |
| 4 | 2 | A | 24.8617 / 25.3577 | 25.0703 / 25.5487 |
| 4 | 3 | C | 24.9421 / 25.4565 | 25.0404 / 25.6280 |
| 4 | 4 | B | 20.9944 / 22.4301 | 21.3389 / 22.7204 |

## Comparaciones separadas

Cambio porcentual = 100 × (numerador / denominador − 1); un valor negativo indica menor latencia. Se conserva cada ronda.

### Efecto del modelo: C1_s2026 mitigado / V3.1 mitigado

| Ronda | Recorrido | Δ p50 % | Δ p95 % | Ambos ≤ +5 % |
|---|---|---|---|---|
| 1 | forward | +2.829 | +2.664 | sí |
| 2 | forward | +1.736 | +2.449 | sí |
| 3 | forward | +0.884 | +1.066 | sí |
| 4 | forward | +0.600 | +0.491 | sí |
| 1 | prepare_forward | +3.040 | +3.082 | sí |
| 2 | prepare_forward | +1.502 | +1.522 | sí |
| 3 | prepare_forward | +0.648 | +1.107 | sí |
| 4 | prepare_forward | +0.877 | +1.452 | sí |

| Recorrido | p50 | p95 | Dictamen |
|---|---|---|---|
| forward | cumple | cumple | cumple |
| prepare_forward | cumple | cumple | cumple |

### Efecto del runtime en V3.1: mitigado / original

| Ronda | Recorrido | Δ p50 % | Δ p95 % | Ambos ≤ +5 % |
|---|---|---|---|---|
| 1 | forward | -17.759 | -14.238 | sí |
| 2 | forward | -14.736 | -11.958 | sí |
| 3 | forward | -14.902 | -11.437 | sí |
| 4 | forward | -15.555 | -11.545 | sí |
| 1 | prepare_forward | -16.926 | -13.202 | sí |
| 2 | prepare_forward | -13.609 | -10.692 | sí |
| 3 | prepare_forward | -14.071 | -11.063 | sí |
| 4 | prepare_forward | -14.884 | -11.070 | sí |

| Recorrido | p50 | p95 | Dictamen |
|---|---|---|---|
| forward | cumple | cumple | cumple |
| prepare_forward | cumple | cumple | cumple |

### Efecto del runtime en C1_s2026: mitigado / original

| Ronda | Recorrido | Δ p50 % | Δ p95 % | Ambos ≤ +5 % |
|---|---|---|---|---|
| 1 | forward | -15.275 | -11.909 | sí |
| 2 | forward | -13.584 | -24.374 | sí |
| 3 | forward | -14.106 | -11.328 | sí |
| 4 | forward | -15.322 | -11.456 | sí |
| 1 | prepare_forward | -14.570 | -10.370 | sí |
| 2 | prepare_forward | -12.489 | -18.903 | sí |
| 3 | prepare_forward | -13.598 | -11.721 | sí |
| 4 | prepare_forward | -14.035 | -10.058 | sí |

| Recorrido | p50 | p95 | Dictamen |
|---|---|---|---|
| forward | cumple | cumple | cumple |
| prepare_forward | cumple | cumple | cumple |

### Cambio completo: C1_s2026 mitigado / V3.1 original

| Ronda | Recorrido | Δ p50 % | Δ p95 % | Ambos ≤ +5 % |
|---|---|---|---|---|
| 1 | forward | -15.432 | -11.953 | sí |
| 2 | forward | -13.256 | -9.802 | sí |
| 3 | forward | -14.149 | -10.493 | sí |
| 4 | forward | -15.048 | -11.111 | sí |
| 1 | prepare_forward | -14.401 | -10.527 | sí |
| 2 | prepare_forward | -12.312 | -9.333 | sí |
| 3 | prepare_forward | -13.515 | -10.079 | sí |
| 4 | prepare_forward | -14.138 | -9.779 | sí |

| Recorrido | p50 | p95 | Dictamen |
|---|---|---|---|
| forward | cumple | cumple | cumple |
| prepare_forward | cumple | cumple | cumple |

### Contexto: C1_s2026 original / V3.1 original

| Ronda | Recorrido | Δ p50 % | Δ p95 % | Ambos ≤ +5 % |
|---|---|---|---|---|
| 1 | forward | -0.186 | -0.049 | sí |
| 2 | forward | +0.380 | +19.269 | no |
| 3 | forward | -0.050 | +0.942 | sí |
| 4 | forward | +0.323 | +0.389 | sí |
| 1 | prepare_forward | +0.198 | -0.175 | sí |
| 2 | prepare_forward | +0.202 | +11.801 | no |
| 3 | prepare_forward | +0.096 | +1.860 | sí |
| 4 | prepare_forward | -0.119 | +0.311 | sí |

| Recorrido | p50 | p95 | Dictamen |
|---|---|---|---|
| forward | cumple | inconcluso | inconcluso |
| prepare_forward | cumple | inconcluso | inconcluso |

Por percentil: cuatro rondas dentro del límite = cumple; cuatro fuera = incumple; mezcla = inconcluso. Por recorrido: un percentil que falla las cuatro implica incumplimiento; ambos que pasan las cuatro implican cumplimiento; los demás casos son inconclusos. La comparación C/A es contexto, no sustituye D/B, B/A, D/C ni D/A.

La mitigación se evalúa dentro de cada modelo y el cambio completo se evalúa contra V3.1 original bajo los mismos hilos del banco. No se considera aceptable una ralentización compartida por el solo ahorro de RAM. No se extrapola D/A a la duración de una petición HTTP activa, cuyo diagnóstico y otros costes permanecen.

## Reutilización de evidencia y comprobaciones

Se verificaron antes de medir los 154 entregables hasheados de E y los 387 de E.1, además de fuentes, pesos, ONNX y binario ORT. Hardware, versiones, Python, contrato de entrada y opciones coinciden. Por ello se reutilizan la paridad completa de 263 observaciones y la memoria del servicio con ruido de E.1. No se repitieron los bancos de s42/s137, la evaluación completa, las 704 pruebas HTTP ni XAI.

Después de las ventanas medidas, cada proceso realizó seis forwards de comprobación: muestras fijas 0, 6 y 12, en ambos recorridos. Se verificó igualdad exacta entre recorridos y tolerancia original contra los valores completos de E.1 (`atol=rtol=1e-5`). También se comprobaron los escalares ya producidos por las 432 mediciones, sin inferencias adicionales. Pesos y BatchNorm permanecen intactos; 206.875 parámetros y ningún gradiente acumulado.

La evidencia E.1 mantiene el cumplimiento RSS de los tres C1 mitigados y el fallo del runtime original para s137/s2026. Su memoria se midió con diagnóstico de ruido y composición equivalente. El RSS de los procesos nuevos se registra solo como contexto; no reemplaza aquella guarda ni representa consumo de un servicio sin diagnóstico. Tamaño y parámetros permanecen iguales por hashes.

## Actividad del equipo e incidentes

| Ronda | Brazo | CPU máx. % | Disponible mín. GiB | Swap-in / out bytes | Alertas |
|---|---|---|---|---|---|
| 1 | A | 49.2 | 9.38 | 49152 / 147456 | swap activity during measurement |
| 1 | B | 49.0 | 9.52 | 114688 / 0 | swap activity during measurement |
| 1 | D | 49.0 | 9.51 | 0 / 0 | ninguna |
| 1 | C | 48.6 | 9.37 | 311296 / 622592 | swap activity during measurement |
| 2 | B | 49.2 | 9.51 | 0 / 0 | ninguna |
| 2 | C | 65.2 | 9.29 | 1867776 / 212992 | swap activity during measurement |
| 2 | A | 51.4 | 9.37 | 147456 / 0 | swap activity during measurement |
| 2 | D | 50.9 | 9.56 | 1458176 / 0 | swap activity during measurement |
| 3 | C | 52.3 | 9.38 | 32768 / 0 | swap activity during measurement |
| 3 | D | 47.8 | 9.61 | 0 / 0 | ninguna |
| 3 | B | 47.8 | 9.61 | 32768 / 0 | swap activity during measurement |
| 3 | A | 51.4 | 9.43 | 16384 / 0 | swap activity during measurement |
| 4 | D | 49.5 | 9.42 | 0 / 0 | ninguna |
| 4 | A | 48.3 | 9.41 | 0 / 0 | ninguna |
| 4 | C | 48.7 | 9.42 | 32768 / 0 | swap activity during measurement |
| 4 | B | 47.2 | 9.61 | 32768 / 0 | swap activity during measurement |

El muestreo externo de E.1 se reutiliza: RSS cada 5 ms y sistema cada segundo, desde lanzamiento. Las alertas de swap son del sistema completo, no atribución al modelo ni prueba de interferencia. Se conservaron todos los datos. No se observó suspensión, interrupción de procesos ni entrenamiento concurrente identificado; no hay fundamento para atribuir diferencias de latencia a una aplicación concreta. La actividad normal de escritorio limita el aislamiento del equipo.

Incidente previo a medición: un chequeo del adaptador usaba `has_session_config_entry`, ausente en esta versión instalada. Se detectó en preflight sin ejecutar ningún brazo y se cambió por `get_session_config_entry` con su excepción de entrada ausente. `worker.py` y el protocolo originales permanecen; `worker_v2.py` y `revision1.json` registran el cambio antes del primer proceso. No cambia la opción de mitigación ni se reemplaza una medición. `execution_incidents.json` conserva el registro de ejecución.

Verificación final: 181 comprobaciones; 4772 archivos protegidos sin cambios. Se comprobaron presupuesto, orden equilibrado, 16 PID distintos y cerrados, secuencia idéntica, opciones equivalentes, predicciones y hashes. No se iniciaron servidores nuevos.

## Recomendación

Las cuatro rondas cumplen las guardas en los dos recorridos para el efecto del modelo, el efecto del runtime en ambos modelos y el cambio completo. El pendiente de latencia de s2026 queda resuelto para este protocolo acotado; no hace falta aceptar una ralentización fuera de las guardas. Recomiendo continuar hacia una evaluación de integración autorizada, manteniendo los tres C1 como candidatos y sin seleccionar uno para producción.

E.1 y sus resultados originales permanecen visibles, incluidas sus rondas desfavorables. E.2 usa el presupuesto y los dos recorridos aislados solicitados; no demuestra estabilidad de un servicio HTTP prolongado ni de otro hardware.

Persisten las limitaciones de validation usada para selección, el deterioro tolerado en baja actividad y las dudas XAI de borde/fondo. No son resultados sobre un test independiente ni evidencia de rendimiento móvil. Resolver latencia no resuelve esas limitaciones.

## Archivos y reproducción

`protocol.json`, `PROTOCOL.md`, `revision1.json`: registros previos. `lib.py` reutiliza carga y factory de E.1; `revision1.py` reutiliza su monitor externo; `worker_v2.py` mide los dos recorridos. `runs/` conserva logs, sistemas, warmups y tiempos. `latency_summary.csv`, `comparisons.csv`, `verdicts.csv`, `small_prediction_checks.csv`, `system_conditions.csv` y `analysis.json` permiten regenerar tablas. `verification.json`, `protected_before.json` y `artifact_hashes.json` preservan trazabilidad. Comandos en `REPRODUCE.md`.

**V3.1 sigue activa; todos los C1 continúan como candidatos. El producto aprobado permanece intacto.** Sin entrenamiento, reexportación, cuantización, cambios de dependencias, commits, push o publicación. La mitigación no se aplicó a producción y no se seleccionó una semilla. No se comenzó otra fase.

**FASE V3.2-E.2: CUMPLIDA** — se completó la medición y su interpretación; esto no implica aprobar al candidato.
