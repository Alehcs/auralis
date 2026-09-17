# FASE V3.2-E — ONNX, paridad y costos de despliegue

## Resultado principal

Los tres C1 conservan su desempeño tras exportar: paridad263/263 por modelo y batch2 aprobado. PyTorch reproduce exactamente D. Se completaron las dos rondas de costo y HTTP, incluidas704 verificaciones de rutas/formato.

La configuración C1 **no supera conjuntamente las guardas B de costo**:

- **C1_s42**: incremento RSS pico +4.08% / +4.91% frente a V3.1 en rondas1/2; guarda RSS: **cumple**.

- **C1_s137**: incremento RSS pico +76.79% / +75.01% frente a V3.1 en rondas1/2; guarda RSS: **incumple**.

- **C1_s2026**: incremento RSS pico +46.98% / +46.52% frente a V3.1 en rondas1/2; guarda RSS: **incumple**.

Las guardas de latencia, tamaño y parámetros pasan en las tres semillas. Los excesos RSS de137 y2026 se repiten en ambas rondas; no se consideran un conflicto inconcluso ni se compensan con retirar ruido. No se ha aislado la causa de esa memoria adicional.

Recomendación: mantener los tres candidatos como experimentales y **no aprobar todavía su integración bajo los criterios B**. No elegir s42 por ser la única que cumple costos. Paridad no resuelve validation de selección, deterioro bajo tolerado ni dudas XAI de borde/fondo.

El tamaño de pesos propios y las dependencias adicionales de auditoría del banco se separan explícitamente en [SERVING_SCOPE.md](SERVING_SCOPE.md) y serving_scope.json. No se construyó un paquete de release candidato independiente.

La fase de medición puede estar cumplida aunque la decisión de aprobación sea desfavorable.
V3.1 sigue activa. Tres C1 candidatos no promovidos; no se selecciona semilla para producción. Esta fase mide exportación y costo, sin integrar ni modificar el producto.

## Protocolo y trazabilidad

Registro previo UTC 2026-09-15T16:29:23.539719+00:00; SHA-256 `9d940de5d886847d33aa03df139d072000b987076f8cf35a43f337d2763a580d`. Hardware: Apple M5, 24 GiB, 10 núcleos; CPU FP32 batch1, 4 intra/1 inter, ORT_SEQUENTIAL/ORT_ENABLE_ALL. Entorno completo en protocol.json. Ruta precisión de B y tolerancias sin cambios. Dos rondas completas, procesos nuevos por banco/modelo, orden de modelos invertido en ronda2; sin bancos ni entrenamientos concurrentes.

Exportador existente sin modificación: opset18, dynamo=False, constant folding, eval/BN congelada, batch dinámico, sin cuantización. Entrada (N,2,512,512) y SI original. Los tres grafos son autocontenidos, FP32, válidos por onnx.checker y cargan en ORT. Checkpoints elegidos exclusivamente por manifiestos: s42 época27, s137 época60, s2026 época55.

|Modelo|Época|SHA-256 checkpoint|SHA-256 ONNX|
|---|---|---|---|
|V3.1|40|1e4c834451375a7c4a1f47bd60404bf9aec3bc20c18056c9fc1b517b168e8e51|f09b1dc470634d880eedc1fb9009c5af359152721b02c69c171b04758f0b48aa|
|C1_s42|27|0b6778ee9518af689fb800ee502c25e7c05d51f7191b5ed50ac199e1a5342179|23b4658ba8817355c91b22b617db8dedc91a249d0294b45128623a3dbfdf1b0a|
|C1_s137|60|05ec38d8158a6456f5662488d7e97dcdd466b7f8796d166f934c89bf5ce4a5b4|a0702c77f246113a1bbeb31727f05a90a63466ffcefdab340979e28ed71aa699|
|C1_s2026|55|b332fa275547da1eba80844111f80736d00fbaad66d2ddfa5942bb5137856b20|98b19825fad71a79d3a7d835c5a958f6c7cc4299d5f520222b49d23e5967dc76|

## Paridad y métricas

Las mismas 263 identidades, targets y orden de D. PyTorch reproduce exactamente los CSV de D en los cuatro modelos. Tolerancia FP32: abs(ONNX−PT)≤1e−5+1e−5·abs(PT). Un máximo absoluto ligeramente mayor que1e−5 puede pasar el criterio combinado, que no se relajó. Batch2 suplementario pasa en todos; pesos y buffers BN conservan su hash.

|Modelo|Máx |ONNX−PT||Media |ONNX−PT||Excesos/263|Batch2|
|---|---|---|---|---|
|V3.1|1.192092896e-06|2.737734254e-07|0|True|
|C1_s42|1.001358032e-05|4.257992647e-06|0|True|
|C1_s137|1.049041748e-05|5.729298175e-06|0|True|
|C1_s2026|7.390975952e-06|2.061459501e-06|0|True|

Métricas ONNX sin redondeo de presentación, recomputadas float64. MAE/RMSE/sesgo/p95 en puntos porcentuales SI; MAPE en porcentaje.

|Modelo|mae|rmse|r2|mape|bias|p95_absolute_error|
|---|---|---|---|---|---|---|
|V3.1|0.204083|0.258233|0.453719|10.497515|-0.186877|0.487845|
|C1_s42|0.048334|0.059055|0.971430|2.908887|0.013237|0.109750|
|C1_s137|0.054008|0.068195|0.961903|3.165014|-0.001927|0.126527|
|C1_s2026|0.051862|0.064623|0.965789|3.087437|0.003183|0.122808|

### Bandas y cola completas

|Modelo|Banda|n|mae|rmse|r2|mape|bias|p95_absolute_error|
|---|---|---|---|---|---|---|---|---|
|V3.1|low|43|0.051748|0.063469|-0.529200|3.982255|0.043637|0.116598|
|V3.1|medium|96|0.102905|0.132461|-0.764520|6.500951|-0.098493|0.256925|
|V3.1|high|124|0.335241|0.355604|-1.803485|15.850953|-0.335241|0.564355|
|V3.1|tail_si_gt_2|71|0.397147|0.410420|-5.023548|17.763161|-0.397147|0.575095|
|C1_s42|low|43|0.058247|0.065254|-0.616406|4.430339|0.056832|0.107048|
|C1_s42|medium|96|0.048275|0.061611|0.618258|3.156418|0.018363|0.116579|
|C1_s42|high|124|0.044943|0.054604|0.933899|2.189650|-0.005848|0.108630|
|C1_s42|tail_si_gt_2|71|0.044166|0.053966|0.895856|1.989230|-0.018076|0.107798|
|C1_s137|low|43|0.058421|0.066595|-0.683543|4.447809|0.057391|0.114779|
|C1_s137|medium|96|0.050285|0.067180|0.546137|3.271588|0.012773|0.124890|
|C1_s137|high|124|0.055361|0.069510|0.892883|2.637665|-0.033876|0.132616|
|C1_s137|tail_si_gt_2|71|0.063880|0.078372|0.780359|2.864298|-0.054870|0.142191|
|C1_s2026|low|43|0.057437|0.066323|-0.669814|4.378138|0.054876|0.113008|
|C1_s2026|medium|96|0.051711|0.066500|0.555276|3.368667|0.009897|0.121446|
|C1_s2026|high|124|0.050045|0.062518|0.913350|2.422130|-0.019940|0.123410|
|C1_s2026|tail_si_gt_2|71|0.052702|0.065657|0.845847|2.380196|-0.033361|0.131066|

Todas las métricas PyTorch/D/ONNX y deltas se conservan en analysis/metrics.csv y metrics_drift.csv. La dispersión entre semillas corresponde a métricas de modelos separados, nunca a una predicción ensemble.

|Métrica C1 global|Media|SD muestral|Mínimo|Máximo|
|---|---|---|---|---|
|mae|0.051401|0.002865|0.048334|0.054008|
|rmse|0.063958|0.004606|0.059055|0.068195|
|r2|0.966374|0.004790|0.961903|0.971430|
|mape|3.053780|0.131339|2.908887|3.165014|
|bias|0.004831|0.007715|-0.001927|0.013237|
|p95_absolute_error|0.119695|0.008811|0.109750|0.126527|
|absolute_bias|0.006116|0.006199|0.001927|0.013237|

## Costos comparables frente a V3.1 remedida

Se reutiliza literalmente cost() de B: 10 calentamientos/60 repeticiones por camino; handler con ruido 3/30. Las18 muestras y orden intercalado seed42 permanecen. Forward usa entrada preparada residente; prepare añade contrato desde NPY residente; carga añade np.load desde filesystem caliente. No incluye creación del proceso o carga del modelo. Tiempos individuales, arranque, etapas RSS y procesos/carga del sistema acompañan cada corrida.

Corrección simétrica respecto a B: ahora ambos bancos retienen un PyTorch para XAI y una sesión ORT para TODOS los modelos. B directo importaba PyTorch pero no retenía ese modelo. Sus números históricos de RSS no son la referencia de las guardas E.

|Modelo|Ronda|Forward p50/p95 ms|Prepare+forward p50/p95 ms|Carga+prepare+forward p50/p95 ms|RSS pico muestreado MiB|RSS máximo vitalicio MiB|
|---|---|---|---|---|---|---|
|V3.1|1|24.293 / 25.649|24.608 / 28.201|24.995 / 27.719|1992.468750|1992.500000|
|V3.1|2|24.109 / 24.717|24.147 / 24.998|24.563 / 25.377|1998.984375|1998.984375|
|C1_s42|1|24.343 / 26.159|24.683 / 26.217|24.966 / 26.718|2073.671875|2073.703125|
|C1_s42|2|24.038 / 24.549|24.059 / 24.711|24.559 / 25.197|2097.109375|2097.140625|
|C1_s137|1|24.296 / 24.907|24.503 / 25.197|24.637 / 26.735|3522.406250|3522.406250|
|C1_s137|2|24.170 / 25.430|24.377 / 25.438|24.635 / 25.182|3498.390625|3498.421875|
|C1_s2026|1|24.579 / 25.711|24.783 / 26.273|25.233 / 26.729|2928.625000|2928.656250|
|C1_s2026|2|24.264 / 25.086|24.565 / 25.541|24.768 / 25.702|2928.937500|2928.968750|

|Modelo|Parámetros|Checkpoint bytes|ONNX total bytes|Pesos requeridos bytes|
|---|---|---|---|---|
|V3.1|206875|848269|835234|1683503|
|C1_s42|206875|846093|835234|1681327|
|C1_s137|206875|846093|835234|1681327|
|C1_s2026|206875|846093|835234|1681327|

El servicio equivalente necesita ONNX y checkpoint para PyTorch/XAI. Manifiestos, configuración, arquitectura, preparación y dependencias compartidas se identifican en serving_inventory.json; no se cuentan logs, evaluaciones o figuras como pesos. Estos candidatos no son paquetes de release listos para activar: el registro actual continúa apuntando a V3.1.

RSS corresponde al proceso: bibliotecas, modelos residentes, cachés, entradas y temporales. Muestreo5ms puede perder picos cortos. ru_maxrss incluye importaciones e inicialización de toda la vida; no es memoria exclusiva de activaciones. No se suman etapas RSS, ni se presenta su diferencia como memoria causal del modelo. No hay medición GPU, móvil ni en equipos modestos.

### Guardas de costo por semilla, sin escoger ronda favorable

|Modelo|Guarda|Decisión entre ambas rondas|
|---|---|---|
|C1_s42|onnx_forward/p50_ms|cumple|
|C1_s42|onnx_forward/p95_ms|cumple|
|C1_s42|prepare_plus_forward_resident_raw/p50_ms|cumple|
|C1_s42|prepare_plus_forward_resident_raw/p95_ms|cumple|
|C1_s42|rss_peak|cumple|
|C1_s42|weights_bytes|cumple|
|C1_s137|onnx_forward/p50_ms|cumple|
|C1_s137|onnx_forward/p95_ms|cumple|
|C1_s137|prepare_plus_forward_resident_raw/p50_ms|cumple|
|C1_s137|prepare_plus_forward_resident_raw/p95_ms|cumple|
|C1_s137|rss_peak|incumple|
|C1_s137|weights_bytes|cumple|
|C1_s2026|onnx_forward/p50_ms|cumple|
|C1_s2026|onnx_forward/p95_ms|cumple|
|C1_s2026|prepare_plus_forward_resident_raw/p50_ms|cumple|
|C1_s2026|prepare_plus_forward_resident_raw/p95_ms|cumple|
|C1_s2026|rss_peak|incumple|
|C1_s2026|weights_bytes|cumple|

Ratios por ronda completos en cost_guard_ratios.csv; agregados descriptivos en cost_guards.json. Cualquier conflicto de aprobación entre rondas es inconcluso, aunque la media pase. Un fallo individual no queda borrado por el agregado. Límites: +5% p50/p95 forward/prepare, +10% pico RSS controlado, +10% pesos, <512000 parámetros.

## HTTP real: ruido y modelo como intervenciones separadas

Loopback127.0.0.1 con puerto efímero reservado, un worker, cliente httpx persistente sin concurrencia. A reutiliza handlers originales con20 pasadas de ruido sigma.005 seed42 y una determinista. B elimina exclusivamente ese cálculo en una copia AST experimental del mismo handler; devuelve uncertainty=null y “no calculado”. Clasificación y confidence heurística conservadas. No es MC Dropout ni incertidumbre calibrada.

Fría significa solo fallo de caché de RESULTADOS: se limpia fuera del reloj. Modelo, librerías, filesystem y conexión permanecen calientes. Caliente está cebada para18 nombres, con0 forwards. Hay3 warmups/30 mediciones frías y60 calientes POR modo y ronda. Los tiempos HTTP incluyen serialización, transporte loopback y cliente, excluyen arranque y red pública/TLS.

|Modelo|Ronda|Caché|A ruido p50/p95 ms|B sin ruido p50/p95 ms|
|---|---|---|---|---|
|V3.1|1|cold_result_cache|549.890 / 617.616|25.344 / 26.608|
|V3.1|1|hot_result_cache|0.317 / 0.367|0.338 / 0.386|
|V3.1|2|cold_result_cache|554.885 / 622.716|25.553 / 29.952|
|V3.1|2|hot_result_cache|0.313 / 0.393|0.339 / 0.410|
|C1_s42|1|cold_result_cache|556.147 / 569.966|25.481 / 26.291|
|C1_s42|1|hot_result_cache|0.318 / 0.385|0.335 / 0.391|
|C1_s42|2|cold_result_cache|548.586 / 556.551|25.344 / 28.612|
|C1_s42|2|hot_result_cache|0.315 / 0.383|0.335 / 0.397|
|C1_s137|1|cold_result_cache|561.398 / 577.083|25.323 / 25.715|
|C1_s137|1|hot_result_cache|0.314 / 0.369|0.333 / 0.406|
|C1_s137|2|cold_result_cache|555.591 / 561.006|24.981 / 25.528|
|C1_s137|2|hot_result_cache|0.315 / 0.378|0.338 / 0.383|
|C1_s2026|1|cold_result_cache|562.420 / 597.178|25.597 / 27.680|
|C1_s2026|1|hot_result_cache|0.317 / 0.362|0.339 / 0.406|
|C1_s2026|2|cold_result_cache|550.823 / 559.354|25.058 / 25.533|
|C1_s2026|2|hot_result_cache|0.322 / 0.365|0.337 / 0.404|

### Cambiar modelo conservando servicio: HTTP frío

|Candidato|Ronda|Modo|Δp50 %|Δp95 %|
|---|---|---|---|---|
|C1_s42|1|noise20|1.137792|-7.715091|
|C1_s42|1|no_noise|0.540065|-1.193480|
|C1_s42|2|noise20|-1.135205|-10.625356|
|C1_s42|2|no_noise|-0.820429|-4.471989|
|C1_s137|1|noise20|2.092767|-6.562859|
|C1_s137|1|no_noise|-0.083845|-3.355565|
|C1_s137|2|noise20|0.127211|-9.909885|
|C1_s137|2|no_noise|-2.239695|-14.769077|
|C1_s2026|1|noise20|2.278729|-3.309213|
|C1_s2026|1|no_noise|0.995624|4.028689|
|C1_s2026|2|noise20|-0.732043|-10.175180|
|C1_s2026|2|no_noise|-1.938769|-14.754575|

### Omitir diagnóstico conservando modelo: HTTP frío

|Modelo|Ronda|Δp50 %|Δp95 %|
|---|---|---|---|
|V3.1|1|-95.391032|-95.691775|
|V3.1|2|-95.394877|-95.190127|
|C1_s42|1|-95.418271|-95.387321|
|C1_s42|2|-95.380215|-94.858972|
|C1_s137|1|-95.489295|-95.543893|
|C1_s137|2|-95.503738|-95.449557|
|C1_s2026|1|-95.448852|-95.364822|
|C1_s2026|2|-95.450858|-95.435341|

La diferencia con caché caliente refleja caché/Python/HTTP, no aceleración del modelo. Todos los efectos fríos/calientes se guardan en http_interventions.csv. El ahorro al omitir ruido NO compensa ninguna guarda de costo de cambiar modelo.

### Paridad de rutas y memoria HTTP

11 fixtures fijos de Phase17,9 cuantiles y extremos temporales; predict, alias con caché vacía, upload512² y upload dual2×512², ambos modos y ambas rondas. 88 verificaciones por modelo/ronda (704 total): hashes de input iguales, valor crudo EXACTO contra ONNX offline, respuesta igual al redondeo4decimales. En cada petición fría se verifican21/1 forwards y en caliente0. Ningún upload se guarda ni se altera el dataset.

|Modelo|Ronda|Pico RSS servicio muestreado MiB|Máximo vitalicio MiB|
|---|---|---|---|
|V3.1|1|2270.578125|2270.578125|
|V3.1|2|2269.640625|2269.640625|
|C1_s42|1|2403.875000|2403.875000|
|C1_s42|2|2405.812500|2405.812500|
|C1_s137|1|4456.250000|4457.765625|
|C1_s137|2|4638.406250|4638.406250|
|C1_s2026|1|3745.468750|3745.468750|
|C1_s2026|2|3747.421875|3747.421875|

El proceso HTTP contiene ambos modos y fixtures; su pico es conjunto, no una prueba de ahorro de memoria al quitar ruido. Arranque y memoria del cliente van separados en JSON. Todos los servidores de este banco terminaron limpiamente y sus puertos se comprobaron cerrados.

## Guardas predictivas, límites y recomendación

|Candidato|ΔMAE ONNX vsV3.1|IC95 exploratorio vsC0|Guardas fallidas vsV3.1|Guardas fallidas vsC0|
|---|---|---|---|---|
|C1_s42|-0.155749|[-0.13329118054473038, -0.08433576236298915]|[]|[]|
|C1_s137|-0.150075|[-0.07771334943901809, -0.05323950799258881]|[]|[]|
|C1_s2026|-0.152222|[-0.10706628906636183, -0.06837419166214884]|[]|[]|

Los IC usan bloques27d desde2016-02-03 TAI,2000 remuestreos seed2026; son exploratorios y condicionados a selección-validation. Guardas agregadas usan media de |sesgos individuales| para evitar cancelación. No hay test independiente, generalización temporal demostrada o selección de semilla para producción.

Se conserva el deterioro de baja actividad: los tres MAE bajos superan V3.1 dentro de +0.01, con sesgo positivo y R² bajo negativo. Las dudas XAI de borde/fondo de D continúan. Paridad de exportación no resuelve exposición a validation ni demuestra mecanismo físico.

No recomiendo aprobar todavía la integración de C1 bajo las guardas B: hay costos incumplidos o inconclusos entre rondas, conservados en las tablas. La paridad y mejora predictiva se mantienen, pero no permiten ignorar esos costos. Mantener los tres candidatos como experimentales; cualquier futura decisión requiere tratar explícitamente las guardas pendientes, sin elegir la semilla o ronda favorable.

## Verificación, incidencias y reproducción

verification.json documenta tests, hashes, invariantes y cierre de servidores. artifact_hashes.json enumera los entregables. PROTOCOL.md, protocol.json, scripts y CSV/JSON quedan disponibles para regenerar gráficas de tesis en otra fase. No se renuevan referencias públicas ni gráficos del producto.

Incidencia de implementación previa a HTTP: las respuestas originales tienen defaults V3.1/promoted. Se corrigieron solo las etiquetas del runtime privado antes de cualquier medida HTTP, con source_revisions/ e implementation_revision1.json; protocolo original y criterios intactos. No se descartaron tiempos o rondas. Segundo ajuste: el primer HTTP completó las medidas y su finalizador, pero un assert exigía exit0 tras solicitar SIGTERM. Se conservó todo, verificando PID ausente, puerto cerrado y estado intacto; el retorno original no se había persistido. Los siguientes bancos aceptan0 o−15 solo con finalizador y puerto cerrado. implementation_revision2.json y resume.py documentan la reanudación sin repetir trabajos.

**FASE V3.2-E: CUMPLIDA.** Evidencia solicitada completa, incluidos resultados desfavorables/inconclusos de aprobación de costos si los hay. V3.1 sigue activa y el producto aprobado permanece intacto. Sin promoción, entrenamientos, recalibración BN, nuevas dependencias, cambios de API/frontend/Agent Lab/gemelo/Unity/Needle/WebAR/timeline/Sol, commits, push o publicación. No comienza otra fase.
