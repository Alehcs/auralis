# FASE V3.2-G — Integración controlada

**V3.1 continúa activa por defecto. Los tres C1 siguen siendo candidatos no promovidos.**

## Resultado

Integración optativa del servicio real, reversible por proceso. Diez procesos,
dos rondas invertidas,900 tiempos HTTP y 440 comprobaciones de fixture preservados.
Un proceso adicional sin variables experimentales confirma V3.1/configuración
original y los cuatro formatos. No se escogió semilla ni se cambió registro activo.

## Archivos y mecanismo

- `src/models/serving_selection.py` (nuevo): delega en active_model sin selección;
  selección finita por AURALIS_TEST_MODEL/runtime, catálogo hasheado, configuración
  C1 y rechazo de artefactos inválidos. La mitigación se limita a pruebas explícitas.
- `src/api/main.py`: carga/configuración optativas, identidad/model_status/protocolo,
  cachés por versión/runtime/archivo, métricas y comparaciones propias del candidato.
  Sin configuración experimental conserva datos/defaults V3.1. Veinte pasadas de
  ruido y una determinista permanecen; no se cambió ningún cuerpo de inferencia,
  preprocesamiento, Grad-CAM o MC salvo identificación/caché y selección de recursos.
- `experiments/v32g_service_integration_v1/`: catálogo, protocolo, pruebas, banco,
  trazas, logs, informe y comandos. Sin cambios de frontend ni del Sol/gemelo.

El registro persistente `active_model.py` permanece idéntico. No hay selector
público ni recarga en caliente; cada proceso mantiene exactamente un PyTorch
con el checkpoint propio para XAI y una sesión ONNX. C1 usa backbone dropout 0,
cabeza 0,3; eval desactiva dropout y conserva BatchNorm. Manifiesto, configuración,
época, checkpoint y ONNX se verifican contra hashes anclados; no hay fallback.

[Comandos y recuperación](RUNBOOK.md) · [matriz de consumidores](CONSUMERS.md).
La configuración directa habitual sin AURALIS_TEST_* sigue usando V3.1 original.
No se escribió .env ni configuración persistente. La mitigación es exactamente
`mlas.disable_kleidiai=1`, solo en pruebas; se validan ORT 1.25.1, hash del binario
nativo utilizado en E1/E2 y read-back de la opción. La causalidad nativa demostrada
en E1 se reutiliza; no se deduce aceptación de una cadena de configuración sola.

## Protocolo y comparabilidad

Mismas 18 entradas de E, CPU FP32, batch 1, 4 hilos intra/1 inter, ORT_SEQUENTIAL,
ORT_ENABLE_ALL, CPUExecutionProvider; mismo entorno instalado. Tres calentamientos,
30 solicitudes frías, primado 18 y 60 calientes. Conexión loopback persistente; caché
fría significa resultados vacíos, manteniendo modelo, filesystem y conexión calientes.
Todos los procesos se ejecutaron secuencialmente, con orden inverso en ronda 2.

Se usa el app/lifespan/handlers reales. `server.py` añade solo rutas privadas de
observación/reset en el banco y un contador escalar alrededor de la sesión real;
no reemplaza lifespan, respuestas ni funciones mediante AST. Tensor hashing se
activa solo fuera del timing. `launch.py` no añade ninguna ruta de observación.
El monitor externo de RSS comienza al spawn y muestrea cada 5 ms. Los logs y
serialización del banco quedan fuera de las ventanas HTTP; todo pico del servidor
se conserva. Los registros de actividad externa/swap permanecen disponibles.

## HTTP real: todas las rondas

| round | arm | cache | n | p50_ms | p95_ms | startup_ms |
|---|---|---|---|---|---|---|
| 1 | V31_original | cold_result_cache | 30 | 570.9157 | 582.7430 | 1399.5070 |
| 1 | V31_original | hot_result_cache | 60 | 0.4340 | 0.5450 | 1399.5070 |
| 1 | V31_mitigated | cold_result_cache | 30 | 498.0297 | 517.0051 | 1303.9459 |
| 1 | V31_mitigated | hot_result_cache | 60 | 0.4258 | 0.5286 | 1303.9459 |
| 1 | C1_s42 | cold_result_cache | 30 | 478.5424 | 489.6833 | 1288.4595 |
| 1 | C1_s42 | hot_result_cache | 60 | 0.4047 | 0.5621 | 1288.4595 |
| 1 | C1_s137 | cold_result_cache | 30 | 481.8355 | 544.4839 | 1284.5877 |
| 1 | C1_s137 | hot_result_cache | 60 | 0.4141 | 0.5332 | 1284.5877 |
| 1 | C1_s2026 | cold_result_cache | 30 | 474.0466 | 494.1272 | 1308.6126 |
| 1 | C1_s2026 | hot_result_cache | 60 | 0.4260 | 0.5343 | 1308.6126 |
| 2 | C1_s2026 | cold_result_cache | 30 | 476.0020 | 508.3039 | 1295.8972 |
| 2 | C1_s2026 | hot_result_cache | 60 | 0.4205 | 0.5104 | 1295.8972 |
| 2 | C1_s137 | cold_result_cache | 30 | 475.3019 | 488.8977 | 1314.9197 |
| 2 | C1_s137 | hot_result_cache | 60 | 0.4199 | 0.5256 | 1314.9197 |
| 2 | C1_s42 | cold_result_cache | 30 | 475.8206 | 485.5167 | 1283.1514 |
| 2 | C1_s42 | hot_result_cache | 60 | 0.4357 | 0.5650 | 1283.1514 |
| 2 | V31_mitigated | cold_result_cache | 30 | 477.1011 | 487.1181 | 1293.6660 |
| 2 | V31_mitigated | hot_result_cache | 60 | 0.4113 | 0.4979 | 1293.6660 |
| 2 | V31_original | cold_result_cache | 30 | 565.8708 | 590.4054 | 1290.2328 |
| 2 | V31_original | hot_result_cache | 60 | 0.4223 | 0.5590 | 1290.2328 |

[900 tiempos individuales](timings.csv) · [comparaciones por ronda](comparisons.csv).
HTTP incluye 21 forwards en caché fría y 0 en caliente. No confundir una respuesta
cacheada submilisegundo con inferencia. Predict/alias/upload2D/uploaddual coinciden
exactamente con ONNX offline guardado E/E1 en valor completo y redondeo 4 decimales;
la identidad byte a byte de los tensores preparados también coincide. No se
repite la evaluación de 263 casos: las 8 comparaciones mitigadas modelo/ronda reutilizan
esa paridad previa al coincidir artefactos, binario, configuración y contrato.

### Efectos separados (caché fría)

| round | effect | arm | reference | p50_change_percent | p95_change_percent |
|---|---|---|---|---|---|
| 1 | model_mitigated | C1_s42 | V31_mitigated | -3.9129 | -5.2846 |
| 1 | model_mitigated | C1_s137 | V31_mitigated | -3.2516 | 5.3150 |
| 1 | model_mitigated | C1_s2026 | V31_mitigated | -4.8156 | -4.4251 |
| 1 | complete_change | C1_s42 | V31_original | -16.1799 | -15.9692 |
| 1 | complete_change | C1_s137 | V31_original | -15.6030 | -6.5653 |
| 1 | complete_change | C1_s2026 | V31_original | -16.9673 | -15.2067 |
| 1 | runtime_V31 | V31_mitigated | V31_original | -12.7665 | -11.2808 |
| 2 | model_mitigated | C1_s42 | V31_mitigated | -0.2684 | -0.3288 |
| 2 | model_mitigated | C1_s137 | V31_mitigated | -0.3771 | 0.3653 |
| 2 | model_mitigated | C1_s2026 | V31_mitigated | -0.2304 | 4.3492 |
| 2 | complete_change | C1_s42 | V31_original | -15.9136 | -17.7656 |
| 2 | complete_change | C1_s137 | V31_original | -16.0052 | -17.1929 |
| 2 | complete_change | C1_s2026 | V31_original | -15.8815 | -13.9060 |
| 2 | runtime_V31 | V31_mitigated | V31_original | -15.6873 | -17.4943 |

`model_mitigated`: C1 frente a V3.1, ambos mitigados. `runtime_V31`: mismo modelo,
mitigado/original. `complete_change`: C1 mitigado frente a V3.1 original. El ahorro
de mitigación no se atribuye enteramente a C1. No se omitió el diagnóstico.

## Memoria de proceso

MiB=bytes/2^20. HTTP peak conservador=max(muestreo externo desde spawn hasta antes
de XAI, highwater del hijo al terminar HTTP/fixtures/errores/recursos). Columna final
incluye Grad-CAM cuando corresponde; no se usa esa carga desigual para comparar
con el control original sin XAI. No se descarga el modelo ni se reinicia el máximo.

| round | arm | loaded_MiB | http_peak_MiB | full_peak_MiB | GradCAM |
|---|---|---|---|---|---|
| 1 | V31_original | 389.1094 | 2246.3438 | 2246.3438 | False |
| 1 | V31_mitigated | 422.0625 | 566.7344 | 1077.2031 | True |
| 1 | C1_s42 | 421.8906 | 566.4062 | 1077.0000 | True |
| 1 | C1_s137 | 421.7969 | 566.4844 | 1076.9531 | True |
| 1 | C1_s2026 | 422.0469 | 564.6094 | 1079.0781 | True |
| 2 | C1_s2026 | 422.0625 | 564.8281 | 1075.3438 | True |
| 2 | C1_s137 | 422.1094 | 564.6719 | 1075.2188 | True |
| 2 | C1_s42 | 422.0625 | 566.5000 | 1077.0156 | True |
| 2 | V31_mitigated | 422.1719 | 566.3281 | 1076.7188 | True |
| 2 | V31_original | 388.0312 | 2224.0625 | 2224.0625 | False |

Resultados HTTP desfavorables (p95 frío frente a V3.1 mitigada, sin nuevo umbral): ronda 1 C1_s137 +5.3150%; ronda 2 C1_s137 +0.3653%; ronda 2 C1_s2026 +4.3492%. Se conservan todos.


RSS no es tamaño del modelo ni memoria exclusiva de tensores: incluye bibliotecas,
PyTorch/ORT residentes, entradas, temporales y cachés. Trazas completas por etapa en
cada `runs/round*/<arm>/rss_trace.csv`. No se extrapola a móviles ni equipos modestos.

## Guardas y dictamen

- Tamaño y parámetros: mismos artefactos de E1/E2;206875 < 512000, ONNX 835234 bytes,
  pesos de servicio C1=1681327 frente a V3.1=1683503 bytes. Cumplen límites B.
- Guardas formales de forward/preparación (+5%) y banco RSS (+10%): evidencia E1/E2
  reutilizable con hashes/configuración coincidentes. E1 s42/s137 mitigados cumplen;
  E2 resuelve los dos recorridos mitigados pendientes de s2026 con cuatro rondas.
  No se convierte HTTP en forward ni se repiten esos bancos.
- HTTP p50/p95: medición adicional; B/E no fijó guarda formal de promoción HTTP
  para este nuevo recorrido G. Se conservan los cambios porcentuales individuales,
  incluso desfavorables, sin inventar un umbral después de medir.
- RSS HTTP G: comparación suplementaria simétrica antes de XAI, con referencia
  mitigada; tabla de ratio y evaluación descriptiva respecto al 10% a continuación.
  No sustituye la guarda formal E1: orden/fixtures/primado HTTP son otra carga.

| round | effect | arm | reference | memory_ratio | within_10_percent |
|---|---|---|---|---|---|
| 1 | model_mitigated | C1_s42 | V31_mitigated | 0.9994 | True |
| 1 | model_mitigated | C1_s137 | V31_mitigated | 0.9996 | True |
| 1 | model_mitigated | C1_s2026 | V31_mitigated | 0.9963 | True |
| 1 | complete_change | C1_s42 | V31_original | 0.2521 | True |
| 1 | complete_change | C1_s137 | V31_original | 0.2522 | True |
| 1 | complete_change | C1_s2026 | V31_original | 0.2513 | True |
| 1 | runtime_V31 | V31_mitigated | V31_original | 0.2523 | True |
| 2 | model_mitigated | C1_s42 | V31_mitigated | 1.0003 | True |
| 2 | model_mitigated | C1_s137 | V31_mitigated | 0.9971 | True |
| 2 | model_mitigated | C1_s2026 | V31_mitigated | 0.9974 | True |
| 2 | complete_change | C1_s42 | V31_original | 0.2547 | True |
| 2 | complete_change | C1_s137 | V31_original | 0.2539 | True |
| 2 | complete_change | C1_s2026 | V31_original | 0.2540 | True |
| 2 | runtime_V31 | V31_mitigated | V31_original | 0.2546 | True |

Pico de toda la vida del proceso, **incluido Grad-CAM**, comparación simétrica entre instancias mitigadas:

| round | arm | reference | memory_ratio | within_10_percent |
|---|---|---|---|---|
| 1 | C1_s42 | V31_mitigated | 0.9998 | True |
| 1 | C1_s137 | V31_mitigated | 0.9998 | True |
| 1 | C1_s2026 | V31_mitigated | 1.0017 | True |
| 2 | C1_s42 | V31_mitigated | 1.0003 | True |
| 2 | C1_s137 | V31_mitigated | 0.9986 | True |
| 2 | C1_s2026 | V31_mitigated | 0.9987 | True |

Los fallos originales de E y E1/default siguen vigentes en su configuración;
la opción mitigada no los resuelve universalmente ni modifica el producto.
No se compensa un incumplimiento con ahorro de retirar ruido. Una ronda favorable
no borra otra desfavorable ni se presenta su promedio como criterio de aprobación.



Actividad del equipo: memoria disponible mínima 9.16 GiB. Hubo actividad de swap durante las ejecuciones; se conservan todos los deltas y snapshots, sin atribuirle automáticamente las diferencias HTTP ni descartar rondas.

La dirección del cambio de p95 HTTP de s2026 es **inconclusa entre rondas**: −4,4250% en la primera y +4,3492% en la segunda frente a V3.1 mitigada. Esto no revoca ni reemplaza la evidencia de forward E2, que mide otro recorrido.

## Errores, XAI y recuperación

Las pruebas de selección rechazan opciones inválidas, artefactos ausentes/corruptos
y catálogo alterado. En HTTP, imagen inexistente devuelve 404, NPY ilegible 400 y una
solicitud válida posterior recupera 21 forwards correctos. Recursos MC candidato y
Agent Lab sin evidencia compatible devuelven 503 explícito; benchmark histórico
permanece marcado histórico y no se atribuye al candidato.

Grad-CAM real en un caso fijo por instancia mitigada/ronda: 8 controles acotados,
PNG válido, hash de todos los pesos/buffers idéntico y predicción determinista
posterior exactamente igual. Se preservan gradientes necesarios para backward.
El servicio usa hook stage4.conv y visualización origin lower existentes; no se
confunde con el procedimiento D sobre stage4 completo/origin upper. No se
reescalaron los mapas F ni se declara resuelta la duda de borde/fondo.

Incidente conservado en `attempt0_startup/`: el observador inicial consultaba
`has_session_config_entry`, ausente en ORT instalado. Falló antes del primer
warmup/timing; cerró correctamente. `revision1.json` registra la corrección al
getter instalado. No se eliminó ninguna medición desfavorable ni se cambiaron
repeticiones. La prueba inicial también detectó diferencia de claves `global`
(E) / `all` (E1) en métricas; corregida antes del banco y log preservado.

Cada proceso terminó su lifespan, se comprobó salida y puerto cerrado. El
control inicial fallido también cerró. No se interrumpió ningún servicio del
usuario. Para recuperar, detener únicamente la instancia de prueba y arrancar
sin AURALIS_TEST_*; no hay pesos/registro persistente que restaurar.

## Consumidores y promoción pendiente

La API candidata entrega identidad y métricas correctas. El dashboard tiene
etiquetas V3.1/MC fijadas y **no queda certificado para conectarse a C1** sin
adaptación posterior. Agent Lab usa rutas históricas, CLI mantiene su constructor
y etiqueta V3.1, y el gemelo conserva las cinco predicciones V3.1 congeladas.
La matriz documenta los cambios futuros; no se aplican ni se regeneran esos datos.

Sigue pendiente cualquier decisión de promoción, selección de semilla, release,
adaptación pública y validación científica independiente. Validation es de
selección, baja actividad mantiene deterioro tolerado/R² negativos, XAI conserva
las dudas de borde/fondo. La integración funcional no soluciona esos límites.

## Figuras F: ubicación única, sin cambios

`auralis-back/experiments/v32f_scientific_package_v1/package/figures/`

Índice: `auralis-back/experiments/v32f_scientific_package_v1/package/INDEX.md`.
26 figuras con nombres reconocibles y mismo nombre base PNG/SVG/PDF; no movidas,
regeneradas ni copiadas. Hashes F verificados; referencias públicas intactas.

## Cierre

Recomendación: la integración local permite revisar cada candidato con runtime
mitigado; no autoriza conectar el dashboard aprobado ni promover un modelo.
Conservar los resultados desfavorables y resolver los pendientes mediante una
decisión posterior explícita. No se comienza otra fase.

Pruebas: 8 de selección/errores y 7 regresiones existentes de V3.1 pasaron.
`verification.json` identifica 5.171 archivos protegidos idénticos y únicamente
`src/api/main.py` como edición existente autorizada. Código y catálogo nuevos
quedan registrados aparte. Hashes, diff, cleanup y logs acompañan la entrega.

**FASE V3.2-G: CUMPLIDA.** V3.1 continúa activa por defecto y conserva su comportamiento
y recursos aprobados. El único cambio de código existente es la integración
optativa documentada; diseño/producto visual, pesos, datos y registro siguen intactos.
