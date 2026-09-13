# Fase 7.4 — Refinamiento de la referencia del 29 de marzo

Propuesta local `phase74-v1`, ruta `/phase6/`, sobre la esfera real Unity →
Needle. Hero **29 marzo 2022, 00:00:53 UTC**, `hmi-2022-03-29`. Pendiente de
aceptación visual del usuario y prueba física. Sin commit, push ni publicación;
el sitio público continúa en versión 11 / Fase 7. No se inicia otra fase.

## Identidad y diagnóstico antes de editar

Los seis hashes de `evidence/phase73/final-source-hashes.json` coincidieron con
los archivos de trabajo. La fecha, el build `phase73-v1` y el shader
`anchored-hmi-v73` se confirmaron también en el visor. Copias reversibles en
`prototypes/phase4-unity-needle/evidence/phase74/baseline/`, con manifiesto
`baseline-identity.json`. `restore-phase73.py` muestra una restauración en seco;
solo `--apply` la aplica y rechaza sobreescribir cambios posteriores a esta entrega. Se guardaron PNG originales de disco completo y detalle,
vídeo y rendimiento antes de modificar los materiales.

El grano ya estaba presente en PNG lossless: no lo originaba la compresión del
vídeo. El shader combinaba una retícula de frecuencia 94, deformación a frecuencias
149–157, identidad de brillo que saltaba al cambiar de célula más cercana,
intersticios contrastados y relieve mediante derivadas de píxel. El filtrado
suavizaba el ruido antes de aplicar una paleta no lineal; esa paleta recuperaba
contraste en detalle apenas resuelto. La esfera usa un material ilustrativo con
sombreado añadido; la iluminación direccional de escena no explica ese grano.

## Una propuesta de refinamiento

- `web/src/phase6/surface-shader.ts`: conserva exactamente los tres colores de
  la paleta 7.3. Radios de células variables, deformación espacial de escala más
  amplia, brillo continuo y transiciones menos duras. La frecuencia principal
  pasa de 94 a 88; se mantienen escalas intermedia y fina con menor amplitud.
  El peso de detalle depende de derivadas de pantalla y se aplica también
  **después de la paleta**, mezclando hacia un promedio de color cálido cuando
  la estructura queda subpíxel. No se desenfoca la imagen completa.
- Se elimina el relieve calculado a partir de la pendiente entre píxeles. La
  gradación continua hacia el borde da volumen sin una cara nocturna ni cráteres.
  El movimiento celular tiene menor amplitud y velocidad, conservando variación
  local suave. Los 96 trazadores existentes y sus tres muestras no cambian.
- La decoración reduce su contraste sobre núcleos y transiciones ya presentes.
  Se conserva **exactamente** la atenuación HMI, el atlas, sus UV y las guías B+/B−.
  No se desplazan, pintan, agregan ni eliminan regiones. Son concentraciones
  magnéticas recreadas, no manchas observadas o confirmadas.
- `web/src/phase5/visual-materials.ts`: halo más fino, caída más corta y variación
  angular amplia y discreta, usando el mismo plano y textura exportados de Unity.
  El borde permanece visible. Estos cambios están limitados a la ruta temporal.
- `web/src/phase5/main.ts` y `web/phase6/index.html`: identificadores 7.4. Un pequeño
  listener de captura, exclusivo de Vite DEV + `?capture`, permite comparar el
  mismo reloj de presentación. El build elimina ese listener. El instrumento
  existente `web/dev/phase72-capture.mjs` utiliza ese reloj solo para evidencia.
  El PNG de 7.3 antes/después de instrumentar es idéntico byte a byte.

DPR sigue limitado a 1.5; no se aumenta brillo global, resolución, partículas,
texturas, geometría ni dependencias. Las reglas se comparten entre las cinco
fechas. HMI sigue siendo una observación 2D de 512², no una observación 3D: el
nuevo detalle no aumenta su resolución. El dorso es ilustrativo. No se infieren
temperaturas, velocidades, erupciones, alturas o campo magnético tridimensional.

## Evidencia reproducible

Directorio `prototypes/phase4-unity-needle/evidence/phase74/`:

- `before-full.png` / `after-full.png`, `before-close.png` / `after-close.png`:
  PNG originales **1206×855**, DPR 1.5, escala 1, misma fecha y reloj t=0. Cámaras
  frontales a distancia 2 y 1.15, respectivamente; misma escena y encuadre.
- `comparison.png`: composición de esos originales sobre el fondo real #090b10,
  sin afilado ni corrección de color. Los PNG conservan alfa; un visor que ignore
  la transparencia puede mostrar mal el halo.
- `before-motion.webm` / `after-motion.webm` y `comparison-motion.mp4`: 9 segundos,
  cámara de disco fija, mismo recorrido de reloj t=0→8 a 1×, seguido de un segundo
  en t=8. El inicio y la pausa tienen tiempos exactos; la cadencia de cuadros
  durante el movimiento depende del navegador. Los dos PNG lossless de la pausa
  coinciden píxel a píxel en cada versión. Los diagnósticos DOM se actualizan
  cada 500 ms y pueden retrasarse respecto al primer fotograma pausado.
- El vídeo es una compresión de presentación; los PNG nativos son la referencia
  para detalle fino. `make-comparison.py` y `make-video.py` reproducen las
  composiciones. Se comprobó la reproducción completa de sus 9 s.
- `verify.py` verifica las parejas de cámara/fecha/escala/resolución/reloj,
  igualdad exacta al volver a cada fecha, las tres capas científicas frente a
  7.3, datos de las cinco entradas del contrato, caché, controles y pausa.
- `check-shaders.mjs` confirma que los shaders generados de Fase 5 y de HMI/B+/B−
  son idénticos a 7.3. `protected.json`: **2.061 archivos sin cambios**, incluyendo
  backend, Coronium, dataset, métricas, contrato, frontend principal, Unity,
  recursos públicos, controlador temporal, contexto y trazadores.
- `tests.log` / `build.log`: 26 tests y TypeScript/Vite correctos. Los avisos de
  tamaño de chunks y MaterialX son anteriores. La instrumentación DEV no aparece
  en los bundles de producción.

Los controles normales de animar/pausar, zoom, escala, reproducción en ambos
sentidos, evento externo sin cambio de HMI, liberación y recarga se probaron
por separado del reloj de captura. Vista responsive de escritorio 393×852,
sin desbordamiento horizontal. No equivale a iPhone ni AR físicos.

## Rendimiento de escritorio

Pares de 30 s, mismo navegador y ventana 1280×720, canvas 1206×855, DPR 1.5,
HMI29, cámara a distancia 2, escala 1 y movimiento normal. Tres draw calls,
24.578 triángulos, 20 texturas temporales más la decoración original.

La primera pareja registró 59.996 → 59.896 callbacks/s, p95 17.6 → 17.4 ms,
con 0 → 2 intervalos mayores a 50 ms. Se conserva completa; motivó repetir la
pareja sin compilación ni codificación concurrentes. La repetición limpia registró **60.029 → 59.996 callbacks/s**, mediana 16.7 ms
en ambas, p95 **18.6 → 18.5 ms** y **0 → 0** intervalos mayores a 50 ms.
Se volvió temporalmente a los materiales guardados de 7.3 para esa medida y luego
se restauró 7.4. En ambos casos, los PNG de identidad coinciden byte a byte con
sus respectivas capturas iniciales. Ambas parejas se conservan en los JSON de
rendimiento; esta muestra no demuestra una mejora de velocidad GPU.

La medición es cadencia de callbacks de render; no es tiempo GPU, energía,
estabilidad de tracking ni garantía de rendimiento móvil.

## Pendiente

La propuesta reduce la dureza del grano y permite leer las regiones con menos
competencia de la decoración. El detalle celular sigue siendo ilustrativo y
puede seguir requiriendo ajuste tras la revisión del usuario, especialmente
muy cerca del borde o con la resolución física del teléfono. Los tests no
sustituyen esa aceptación estética.

Prueba mínima en `evidence/phase74/PRUEBA-IPHONE.md`. WebXR/Needle Go comparten
el material por código; falta comprobarlos físicamente. Quick Look conserva
el atlas horneado seleccionado, sin este shader, movimiento ni timeline.
