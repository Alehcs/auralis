# FASE 3 — Contrato temporal de Coronium V3.1

Fecha: 2026-09-06. **FASE 3: CUMPLIDA**. Se define y materializa el contrato de datos; no se inicia ninguna fase posterior.

## Entregables y estructura final

- Contrato: [`temporal-sequence-v1.schema.json`](../auralis-back/contracts/temporal-sequence-v1.schema.json), JSON Schema Draft 2020-12, ID `urn:auralis:temporal-sequence:1.0.0`.
- Ejemplo completo y utilizable, con los cinco estados y todos sus valores: [`noaa12975.sequence.v1.json`](../auralis-back/reports/phase3_temporal_model/noaa12975.sequence.v1.json).
- Generador y verificador offline: [`build_phase3_temporal.py`](../auralis-back/scripts/build_phase3_temporal.py).
- Resultados y hashes de salida: [`verification.json`](../auralis-back/reports/phase3_temporal_model/verification.json).
- Dependencia adicional de validación: [`requirements-phase3.txt`](../auralis-back/contracts/requirements-phase3.txt). NumPy, Astropy y ONNX Runtime proceden del entorno completo del backend.
- Contexto actualizado en [`AGENTS.md`](../AGENTS.md).

```text
sequence (schema_version, sequence_id, scope, limitations)
├── model / preprocessing               versiones y referencias a artefactos
├── states[]                            orden explícito, ID estable
│   ├── observation                     magnetograma, horas, SRS, SI y partición
│   ├── coronium_results                protocolo, predicción y Grad-CAM ausente
│   ├── derived                         B+/B−, separación y cambio de SI
│   └── visual                          vacío, sin registro ni interpolación
├── events[]                            inicio/pico/fin UTC, NOAA, fuente y relación temporal
├── optional_reserve                    1 de abril, enabled=false
└── artifacts[]                         ID, ruta relativa, SHA-256, URL/consulta si existen
```

`states → observation → coronium_results` se vincula por contención: cada resultado pertenece exclusivamente a la observación de su estado. Los eventos se almacenan una sola vez a nivel de secuencia; `temporal_relation.preceding_state_id` y `following_state_id` los relacionan con los estados. No se anidan como si fueran mediciones de un magnetograma.

Todos los campos son obligatorios, aunque algunos aceptan `null`. No se usan NaN, Infinity, objetos Date, rutas absolutas de la máquina ni matrices gigantes dentro del JSON. `null` significa información ausente, nunca cero. `visual.assets=[]` significa que esta fase no produce activos visuales. Los objetos rechazan propiedades desconocidas para detectar errores de nombres y adiciones no versionadas.

El schema reutilizable admite secuencias de longitud variable dentro de este mismo contrato científico; el **validador del caso Fase 3** exige exactamente los cinco estados autorizados, su orden y los datos reconstruidos desde Fase 2. No es un contrato universal para FITS, vectores o recortes regionales. La versión 1.0.0 mantiene WCS, máscaras, 3D y Grad-CAM ausentes; incorporar esos datos requerirá una revisión explícita del schema, procedencia y reglas de consumo. Los consumidores deben aceptar explícitamente versiones conocidas. Cambios incompatibles implican versión mayor; una extensión compatible exige igualmente schema y versión explícitos, sin sobreescribir silenciosamente este caso congelado.

## Los cinco estados

En todos: hora de registro **00:01:30 TAI / 00:00:53 UTC**, NOAA **12975**, HARP **8088**. Los decimales completos se conservan en JSON; esta tabla redondea sólo para lectura.

| ID / orden | Fecha | Ubicación SRS | SI original (%) | ONNX V3.1 (%) | Media B+ | Media magnitud B− | Partición |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| hmi-2022-03-24 / 1 | 24-mar | N13E63 | 1.679617 | 1.470520 | 0.006268135 | 0.005543777 | train |
| hmi-2022-03-25 / 2 | 25-mar | N14E55 | 1.717091 | 1.477280 | 0.006235762 | 0.005921202 | train |
| hmi-2022-03-28 / 3 | 28-mar | N12E05 | 1.947987 | 1.656259 | 0.007608641 | 0.007773591 | selection_validation |
| hmi-2022-03-29 / 4 | 29-mar | N13W12 | 2.057672 | 1.683445 | 0.008250998 | 0.008527068 | train |
| hmi-2022-03-30 / 5 | 30-mar | N13W25 | 2.050173 | 1.712676 | 0.008448414 | 0.008786901 | train |

Cada `observation.magnetogram` conserva nombre y referencia al `.npy` original, forma `[512,512]`, tipo `float32` y hash en el registro de artefactos. No se copiaron matrices. Los ID son estables para este caso; `order` comienza en 1. `source_csv_row_1based` empieza en 1 después de la cabecera; `metadata_row_indices` conserva los índices originales desde cero, incluidas repeticiones que no crean estados adicionales.

Cadencia: 86.400, 259.200, 86.400 y 86.400 segundos. El cambio final real es **−0.007498264312744141 pp**. El primer cambio y la primera separación son `null`. Ninguna regla exige SI creciente.

El 1 de abril sólo figura en `optional_reserve`, con archivo, hash, TAI/UTC y referencia a `candidates.csv`. No tiene orden activo, resultado activo ni participa en el cálculo de límites de eventos. El 3 y 5 de abril no se incorporan; los CSV históricos referenciados conservan su contenido original más amplio.

## Semántica científica y disponibilidad

| Bloque | Naturaleza y datos disponibles | Límites / datos ausentes |
| --- | --- | --- |
| Magnetograma | Observación procesada de disco completo HMI; matriz original local y SHA-256 | Sin FITS originales, WCS, orientación certificada, T_OBS, QUALITY ni máscaras |
| Tiempo | Registro TAI del nombre y conversión Astropy a UTC; CSV original separado | `exposure_utc=null`; la fecha CSV tiene escala desconocida; TAI no lleva `Z` |
| NOAA/SRS | Ubicación textual, hora de validez y emisión, línea original, tipo magnético, área de manchas y otras regiones | No hay ubicación de píxeles ni transformación a coordenadas 3D |
| HARP | 8088 y asociación de vida con 12975/12976/12977/12984, snapshot y hash | No implica segmentación por instante ni identidad exclusiva con 12975 |
| SI original | Etiqueta guardada del porcentaje de píxeles originales con abs(B_LOS)>200 G, filas y CSV de origen | No se recalcula desde la matriz reducida; no es SI regional |
| Coronium | Estimación determinista guardada y reproducida con ONNX CPU eval, batch 1, cuatro hilos, sin ruido/MC; versión 3.1 y pesos con hashes | No es predicción de llamaradas/futuro; no equivale a métricas MC ni a test independiente |
| B+/B− | Derivación observacional reproducible: medias y receta de los canales de entrada | No son Gauss originales, porcentaje de área, flujo magnético ni campo vectorial |
| Grad-CAM | Contrato de ausencia explícita: `status=not_available`, referencia nula y explicación | No se encontró un artefacto congelado con procedencia compatible para estos estados; no se generó uno nuevo |
| Eventos | Seis registros NOAA M/X seleccionados, inicio/pico/fin, satélite, región y línea de fuente | Selección no exhaustiva; ninguna llamarada se estima desde SI |
| Visual | `kind=visual_only`, assets vacíos, registro espacial no disponible, interpolación `none` | Sin Sol 3D, timeline, materiales, campos artificiales ni animación |

Las ubicaciones SRS tienen validez a **00:00:00 UTC**, 53 segundos antes del registro HMI; fueron emitidas a **00:30:00 UTC**. Se conservan ambos tiempos. El texto N13E63, por ejemplo, pertenece al catálogo regional, no certifica dónde está un píxel del `.npy` ni constituye un centro exacto a la hora de exposición.

Las medias B+/B− se calculan en float64 sobre los canales float32 producidos por `prepare_model_input`, sobre **los 512×512 píxeles**, sin máscara de disco. Ambos son magnitudes no negativas: `B+=max(x,0)`, `B−=max(-x,0)`. El consumidor Python puede reconstruir las matrices completas desde el archivo referenciado. No se duplica la matriz en JSON ni se crea un formato binario nuevo. Un gráfico futuro podría negar B− sólo como convención visual explícita. No debe confundir esta escala con `/api/polarity-series`, que multiplica medias por 100 y presenta B− negativo.

La versión del preprocesamiento es `hmi-clip400-polarity-v1`; la del target, `strong-field-pixel-percent-200G-v1`. También se guardan el hash del código de entrada y los hashes de los pesos y del manifiesto. La media B+/B− es una derivación observacional; `coronium_results` es inferencia; `visual` sólo puede describir presentación. Grad-CAM sería atribución del modelo y una superposición coloreada sería su representación visual: ninguna sería máscara regional, probabilidad o estructura magnética real.

## Eventos independientes de los estados

La relación se calcula por `peak_utc`, manteniendo también inicio y fin del evento. Los seis intervalos completos de este caso quedan dentro de los mismos límites que sus picos.

| Evento / ID | Inicio UTC | Pico UTC | Fin UTC | Relación |
| --- | --- | --- | --- | --- |
| M4.0 / 20220328_3390 | 28-mar 10:58 | 28-mar 11:29 | 28-mar 11:45 | Entre estados 3 y 4 |
| M1.1 / 20220328_3570 | 28-mar 20:49 | 28-mar 20:59 | 28-mar 21:09 | Entre estados 3 y 4 |
| M2.2 / 20220329_3630 | 29-mar 00:57 | 29-mar 01:11 | 29-mar 01:26 | Entre estados 4 y 5 |
| M1.6 / 20220329_3990 | 29-mar 21:43 | 29-mar 21:52 | 29-mar 21:57 | Entre estados 4 y 5 |
| X1.3 / 20220330_4220 | 30-mar 17:21 | 30-mar 17:37 | 30-mar 17:46 | Después del quinto estado |
| M9.6 / 20220331_4520 | 31-mar 18:17 | 31-mar 18:35 | 31-mar 18:45 | Contexto posterior a la secuencia |

Para X1.3: `placement=after_last_state`, `preceding_state_id=hmi-2022-03-30`, `following_state_id=null`, `seconds_after_preceding_state=63367`, `captured_by_state_id=null`. Son **17 h 36 min 07 s** después del registro, sin atribución al magnetograma de la madrugada. La reserva desactivada no se convierte en un sexto estado para encerrar artificialmente el evento entre muestras. M9.6 conserva el contexto posterior ya documentado en Fase 2 y tampoco añade observaciones.

## Procedencia, generación y validaciones

Se trabaja exclusivamente con artefactos locales congelados de Fase 2. No se consultó una revisión nueva de catálogos ni se descargaron datos. Cada URL externa identifica el origen del snapshot almacenado, junto con su hora de consulta y SHA-256. El snapshot HARP se obtuvo originalmente por HTTP tras fallar HTTPS; el hash comprueba integridad local, no convierte ese transporte en autenticado. Los hashes no prueban calibración instrumental.

Desde la raíz del repositorio, con el entorno completo existente:

```bash
/Users/alejandro/.pyenv/versions/3.12.7/bin/python3 auralis-back/scripts/build_phase3_temporal.py
/Users/alejandro/.pyenv/versions/3.12.7/bin/python3 auralis-back/scripts/build_phase3_temporal.py --check
```

La primera orden genera el JSON y `verification.json`; la segunda comprueba los archivos guardados sin reescribirlos. El schema es un contrato estático editado/versionado, no se infiere del ejemplo durante la validación. El generador no depende del directorio de trabajo y no hace llamadas de red.

Validaciones realizadas:

- JSON válido, sin números no finitos; JSON Schema Draft 2020-12 con validación de formatos y campos cerrados.
- Cinco estados autorizados, IDs distintos, orden y fechas exactos; reserva desactivada y excluida.
- Conversión TAI/UTC mediante el módulo compartido, comparada con Fase 2.
- **31 referencias a artefactos** resueltas y hashes locales comprobados; además, dependencias originales del manifiesto de Fase 2 y hashes de pesos contrastados con el manifiesto promovido.
- Matrices float32 de forma correcta, finitas y dentro de [-1,1]; canales calculados con el contrato compartido.
- Ubicaciones y líneas SRS contrastadas; seis eventos únicos de NOAA 12975 contrastados con sus líneas originales; intervalos inicio≤pico≤fin.
- Reproducción ONNX de los cinco estados: **diferencia absoluta máxima 0.0** respecto de Fase 2. No es una nueva evaluación científica ni una prueba HTTP.
- Comparación semántica del JSON guardado con la reconstrucción independiente desde fuentes verificadas; conserva SI, partición, cadencia, límites de eventos y falta de datos espaciales.
- Once casos negativos rechazados: UTC falsa, ID duplicado, sexto estado, hash alterado, WCS inventado, B− negativo, falsa captura de X1.3, reserva activada, versión desconocida, caída final eliminada y referencia de modelo rota. Algunos los rechaza el schema; otros la validación semántica del caso congelado.
- Hashes del JSON, schema y generador guardados en `verification.json`; el modo `--check` también los contrasta. La regeneración produce un JSON idéntico byte a byte en el entorno registrado.

## Consumo posterior del gemelo

1. Cargar el JSON y validar `schema_version` antes de interpretarlo. El backend podrá resolver `artifacts[].path` contra la raíz **auralis-back**, comprobar hashes y adaptar esas referencias a URLs autorizadas de activos. Esas rutas son identificadores de archivos, no endpoints ni URLs directamente navegables.
2. Usar `states[].id` como clave y `order`/`observation.time.record_utc` para la selección temporal. Conservar los intervalos reales; un tiempo entre observaciones no introduce una observación nueva. Cualquier interpolación posterior deberá identificarse como visual.
3. Mostrar SI observado y estimado por separado. Cargar B+/B− en Python desde el `.npy` mediante el módulo compartido; React y Needle/Unity podrán consumir las medias JSON y los activos que un adaptador posterior publique. No se supone que un navegador o Unity pueda leer `.npy` directamente.
4. Leer `events[]` en sus propios tiempos UTC y resolver los IDs de límites. Los eventos con `following_state_id=null` son contexto posterior, no un fotograma adicional ni una predicción. No relabelar clases internas de SI como clases GOES.
5. Respetar `null` y `status`: ocultar o identificar como ausentes Grad-CAM y datos espaciales. No convertir SRS en posición 3D o textura registrada sin datos y un contrato posteriores.

Ejemplo mínimo Python, ejecutado desde la raíz del proyecto:

```python
import json
from pathlib import Path
sequence = json.loads(Path('auralis-back/reports/phase3_temporal_model/noaa12975.sequence.v1.json').read_text())
assert sequence['schema_version'] == '1.0.0'
for state in sorted(sequence['states'], key=lambda s: s['order']):
    print(state['id'], state['observation']['time']['record_utc'],
          state['observation']['target_si']['value'], state['coronium_results']['prediction_si'])
```

React/Needle podrá usar `JSON.parse` y objetos/arreglos ordinarios con nombres estables. En C#/Unity, DTOs con esos campos públicos y listas/arreglos pueden deserializar la misma estructura; TAI se mantiene como cadena y sólo las cadenas UTC se interpretan como instantes UTC. El registro `artifacts` es un arreglo, sin depender de diccionarios dinámicos. Las referencias al schema son metadatos del contrato, no instrucciones para descargar recursos.

No se modificaron API, rutas, frontend, métricas, modelo ni preprocesamiento. No se implementaron Unity/Needle, WebAR, timeline visual ni un nuevo Sol 3D.
