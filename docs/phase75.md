# Fase 7.5 — Plasma y corona guiados por HMI

Implementación local `phase75-v2`, en **`/phase6/`**, sobre la esfera real de
Unity → Needle. Hero: **29 marzo 2022, 00:00:53 UTC**. Las cinco fechas funcionan.
El usuario aprobó el diseño de Fase 7.5. La revisión v2 hace más visible su
movimiento; la prueba física de AR sigue pendiente. Publicada el 12 de septiembre de 2026 para probarla en iPhone;
sitio público versión 12.

## Escena y referencia

Antes de editar se verificaron los siete hashes finales de Fase 7.4. La ruta
correcta ya contenía aquellas mejoras: no había otra variante que trasladar.
La identidad también se confirmó en el navegador: `phase74-v1`, HMI29 y GLB real
`Phase5Solar.glb`, SHA-256
`6694a42dd2f0b322c7a65dc9d55d17eb1fe653ab0ec85884ee68b20cb14999b5`.
El GLB, su geometría original, el exportador, la escena Unity y los atlas no cambian.

La imagen adjunta por el usuario es la referencia estética: filamentos suaves,
regiones luminosas, fondo con estructura a varias escalas y halo irregular.
No se usa esa imagen como textura ni se trasladan sus regiones al HMI del caso.
La paleta dorada se inspira en esa presentación; no representa temperatura ni
una observación AIA de estas fechas.

## Cambios visuales

- `web/src/phase6/surface-shader.ts`: sustituye el patrón celular dominante por
  ruido suave deformado y hebras anisótropas a varias escalas, con filtrado de
  detalle según su tamaño en pantalla. El transporte local y las variaciones de
  emisión usan el reloj superficial existente; no rotan el Sol ni las guías HMI.
  Las envolventes luminosas proceden de mipmaps de los canales B+/B− del estado
  seleccionado. Los núcleos mantienen la misma atenuación anclada de Fase 7.4.
- `web/src/phase6/activity-loops.ts`: añade haces de arcos ilustrativos sobre la
  esfera original. Lee únicamente las dos imágenes de canales ya verificadas y
  decodificadas en memoria. Localiza concentraciones de signo opuesto; cada
  hebra distribuye sus apoyos dentro de píxeles con señal del signo correspondiente.
  Las curvas, alturas, selección de parejas y velocidades son decisiones gráficas,
  **no una extrapolación del campo ni conexiones magnéticas comprobadas**.
- Los mismos apoyos alimentan un tejido fino de contornos en el material de la
  superficie. Así las regiones activas tienen una transición luminosa al fondo,
  y los arcos elevados se integran mejor. El brillo viaja suavemente por las hebras;
  el pequeño movimiento transversal se anula en sus apoyos.
- `web/src/phase5/visual-materials.ts`: corona de caída corta con un halo difuso,
  rayos suaves curvados e irregularidad angular sobre el plano original de Unity.
  La corona general es decorativa. No se reconstruyen altura atmosférica, campo 3D,
  emisiones EUV, manchas confirmadas, velocidades o erupciones.
- `web/src/phase5/main.ts`: integración mínima para crear/liberar el recurso visual,
  seleccionar su geometría en el mismo commit temporal y excluirlo de Quick Look.
  Etiquetas actualizadas para distinguir HMI y recreación inspirada en SDO/AIA.
  `web/phase6/index.html` identifica la Fase 7.5.

Se inspeccionaron cuatro iteraciones con PNG nativos. La primera tenía demasiado
contraste y arcos demasiado tenues; la segunda produjo haces rígidos y altos;
la tercera suavizó el fondo, bajó los arcos y distribuyó sus apoyos; la cuarta
integró filamentos superficiales alrededor de los mismos apoyos HMI. Las capturas
y fuentes intermedias se conservan bajo `evidence/phase75/`.

No se modifican SI, ONNX, HMI, B+/B−, orden temporal, cinco atlas, contratos,
backend, modelos, métricas, frontend principal, contexto GOES/SRS ni controles
centrales. La caída real de SI entre el 29 y el 30 permanece.

## Recursos, timeline y AR

La caché temporal conserva **20 texturas** más la decoración original retenida.
No hay nuevas imágenes de producto, dependencias ni peticiones de datos. Se
precalculan cinco geometrías de arcos y se reutiliza un único material; durante
cada frame solo cambian uniforms existentes. La geometría de arcos se intercambia
junto con el atlas, las guías y los valores científicos, en el punto medio del
fundido ya existente. Regresar a una fecha con t=0 reproduce exactamente su imagen.

Los días 24/25/28/29/30 muestran respectivamente **9/8/12/12/12** grupos gráficos,
con 14 hebras por grupo. No son conteos científicos de regiones NOAA. En HMI29:
**4 draw calls y 43.394 triángulos**, frente a 3 y 24.578 en la base. Los cinco
buffers se liberan explícitamente, al igual que el material. No hay creación de
geometría, texturas o materiales por frame.

Los nuevos arcos heredan órbita, escala y colocación de la esfera Unity. WebXR y
Needle Go utilizan el mismo material, reloj y control temporal. Se probaron los
controles reales del panel AR mostrando temporalmente ese DOM en escritorio;
esto **no inicia ni simula una sesión XR** y no certifica tracking o colocación.
La instrumentación se retiró. Quick Look sigue exportando el atlas horneado
seleccionado, sin shader procedural, arcos nuevos, trazadores ni timeline.

## Evidencia y comprobaciones

Directorio: `prototypes/phase4-unity-needle/evidence/phase75/`.

- `comparison.png`, `hero-full.png`, `hero-close.png`: antes/después con los mismos
  HMI29, cámara, escala y t=0. Originales PNG **1206×855**, DPR 1.5; cámara a
  distancias 2 y 1,15. La composición solo coloca los PNG sobre el fondo real
  #090b10; no afila ni corrige su color. El alfa de los originales debe respetarse.
- `comparison-motion.mp4`: 9 segundos, 0–8 a velocidad 1× y 8–9 congelado en t=8.
  Misma cámara y estado en ambos lados. Se conservan los WebM originales y dos PNG
  congelados por versión, idénticos entre sí. Vídeo reproducido completo en el
  navegador, sin error. La cadencia de captura depende del navegador.
- `before-check.png` confirma exactamente la base al restaurarla temporalmente
  para medirla; `final-identity.png` coincide exactamente con el resultado final
  después de reponerlo. No quedó activa la base anterior.
- Cinco retornos adelante/atrás: igualdad exacta de píxeles. SI/ONNX/UTC, hashes de
  mapas, IDs del contexto y apoyos visuales corresponden al mismo estado.
- HMI/B+/B−: igualdad exacta frente a Fase 7.4 y entre capturas pausadas. Los
  shaders generados de estas capas y de Fase 5 son idénticos a la base.
- `verify.py` contrasta cada apoyo registrado con el promedio 5×5 de los píxeles
  del canal firmado correspondiente. Verifica **2.061 archivos protegidos**,
  pares de cámara/datos, retornos, pausa, controles, caché y tamaño responsive.
- Play adelante/atrás termina en los extremos; el evento X1.3 conserva HMI29;
  zoom, escala, órbita y pausa funcionan. Liberar elimina el canvas y Reintentar
  reconstruye correctamente la escena y sus recursos.
- Responsive **393×852**, ancho del documento 393: cinco fechas, Sol y tres capas
  científicas comprobadas, sin desbordamiento horizontal del documento. Esto
  sigue siendo un navegador de escritorio con viewport pequeño.
- **26 tests existentes y TypeScript/Vite pasan**. Los avisos de tamaño de chunks
  y MaterialX ya existían. No aparece instrumentación de captura/AR de prueba en
  los bundles de producción.

`final-source-hashes.json`, `product-changes.patch` y `baseline/` permiten revisar
las modificaciones exactas. `make-comparison.py`, `make-video.py` y `verify.py`
reproducen la composición y las comprobaciones sin tocar fuentes científicas.

## Rendimiento observado

Muestras de 30 s, mismo navegador de escritorio, HMI29, escala 1, cámara a
distancia 2, DPR 1.5 y movimiento superficial normal, sin compilar ni codificar
vídeo durante las medidas:

| Muestra | Callbacks/s | Mediana | p95 | Intervalos >50 ms |
| --- | ---: | ---: | ---: | ---: |
| Fase 7.4 | 59,998 | 16,7 ms | 18,6 ms | 0 |
| Fase 7.5, primera muestra | 59,830 | 16,7 ms | 18,7 ms | 2 |
| Fase 7.5, muestra adicional | 59,999 | 16,7 ms | 18,7 ms | 0 |

Los dos intervalos largos se conservan y motivaron una muestra adicional con
la versión final ya caliente, registrada por separado. Estas medidas son
**cadencia de callbacks de render**, no tiempo GPU, consumo, estabilidad de
tracking ni rendimiento físico móvil. No se afirma una mejora de rendimiento.

## Prueba física pendiente

En iPhone 15 Pro: comprobar primero la web en Brave/Chrome; para AR usar la ruta
Safari → Needle Go con una URL HTTPS que contenga esta versión. Revisar el 29,
acercarse, pausar superficie, cambiar 29→30→24, usar HMI/B+/B−, escalar y salir de
AR. Confirmar que no se desplazan las marcas HMI, no se duplican arcos y no hay
saltos de estado. Medir allí 30 s y registrar calor, fluidez y tracking.

El sitio público ya contiene **Fase 7.5 v2**. La publicación para iPhone no
transforma la validación de escritorio en validación física de AR.

## Revisión v2 — Movimiento algo más visible

A petición del usuario tras aprobar expresamente el diseño, se multiplica por
**1,65** el tiempo local que usan el flujo superficial, la emisión de los
filamentos y el pequeño movimiento de las hebras. El reloj de presentación, la
timeline, su cadencia de 2 s, las amplitudes y la geometría no cambian. La corona
y los trazadores conservan su ritmo anterior. No aumenta el brillo global ni se
modifican la paleta o los datos HMI.

En `evidence/phase75/motion-v2/` quedan la base aprobada, el parche, hashes finales,
vídeo comparativo de 9 s y PNG de comprobación. El disco y el detalle HMI29 a t=0
son idénticos píxel a píxel; lo mismo ocurre en las cinco fechas frente a los PNG
aprobados. La pausa produce dos capturas idénticas. Se conservan los 2.061 archivos
protegidos; 26 tests y TypeScript/Vite pasan. No se repite ni se atribuye a v2 la
medición de rendimiento de v1; no hay nuevos recursos ni draw calls.

El ajuste solo altera la velocidad visual, sin introducir velocidades físicas
medidas. Publicada posteriormente para que el usuario pueda abrirla en su iPhone.

## Publicación para iPhone — 12 septiembre 2026

La petición de abrir el resultado aprobado en iPhone se atendió publicando la
versión **12**, conservando el acceso público existente, sin cambiar su audiencia.
Se reutilizó el build ya validado y se guardó únicamente el repositorio del Site:
`8dabe0d3b6767d9408250ad13361f27c6352f8ac`. No se hizo commit del repositorio padre.

Enlace directo: https://auralis-phase4-needle-probe.alejandro-cornejog4.chatgpt.site/phase6/

Sites confirmó `succeeded`; la respuesta se conserva en
`evidence/phase75/publication/publication.json`. No se repitió la auditoría HTTP
anónima de fases anteriores. QR directo en `publication/iphone-qr.png`.
La versión incluye el diseño aprobado y el movimiento 1,65× de v2. La prueba
física en iPhone y en AR todavía corresponde al dispositivo del usuario.

## Comprobación pública de las cinco fechas y preparación AR

Tras la solicitud de conservar el diseño aprobado en todos los magnetogramas y
AR, se comprobó la versión pública 12, build `phase75-v2`. No fue necesario
modificar el código ni publicar otra versión: los seis hashes del código
aprobado siguen idénticos a `motion-v2/final-source-hashes.json`.

En el navegador se seleccionaron 24, 25, 28, 29 y 30 de marzo. Cada fecha usa el
mismo shader `anchored-hmi-v75-2`, con su propio atlas, guías B+/B− y geometría de
arcos: las identidades de superficie, arcos, SI y controles AR coinciden. Se
completó Play 24→30 y 30→24, con parada en ambos extremos y cero errores
registrados. Se restauró HMI29 y la animación superficial. Capturas y resultados:
`evidence/phase75/ar-readiness/public-five-states.json` y `public-playback.json`.

Los controles compartidos siguen como hijo directo de `needle-engine`, conforme
al manejo de DOM overlay del runtime 5.1.12. Conservan selección de las cinco
fechas, Play/Pause, dirección, capas, escala y pausa de superficie. La prueba
local previa de sus botones está en `evidence/phase75/ar-dom.json`; no fue una
sesión XR. Needle Go carga esta misma URL y ruta de materiales web. Referencia
del proveedor: https://engine.needle.tools/docs/how-to-guides/xr/ios-webxr-app-clip

Para iPhone: abrir `/phase6/` en Safari, pulsar **Abrir en Needle Go**, autorizar
la cámara y colocar sobre una superficie. La timeline del panel AR permite
recorrer las cinco observaciones; se puede desplazar el panel y la escala UTC.
Quick Look es una instantánea reducida y no incluye el shader, los arcos
procedurales, la animación superficial ni la timeline del diseño aprobado.
La colocación, estabilidad y rendimiento en el iPhone físico siguen pendientes.
