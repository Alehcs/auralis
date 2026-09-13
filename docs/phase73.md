# Fase 7.3 — Hero solar para exposición

Versión local `phase73-v1` en `/phase6/`. El hero conserva **29 marzo 2022,
00:00:53 UTC**, `hmi-2022-03-29`. Sin commit, push ni publicación. La versión
pública sigue en 11; la aceptación estética final corresponde al usuario.

## Problema y dirección

La Fase 7.2 corrigió la fecha y redujo la apariencia de lava, pero comprimió el
contraste y dejó una superficie beige, mate y uniforme. Esta revisión mantiene
la estructura fina y las regiones ancladas, recuperando luminosidad, color solar
y profundidad para exposición.

Se inspeccionaron las referencias guardadas de Hinode y SDO y se volvieron a
consultar las páginas oficiales de [granulación Hinode](https://svs.gsfc.nasa.gov/3412)
y [SDO/AIA 171 Å](https://svs.gsfc.nasa.gov/4761). La primera informa el contraste
y detalle granular; la segunda sirve como referencia estética de brillo localizado.
Son observables distintos: no se copian regiones ni se presentan sus colores o
movimientos como datos físicos del magnetograma de 2022.

## Pulido acotado

- `web/src/phase6/surface-shader.ts`: paleta naranja/ámbar con centros granulares
  dorados, intersticios más profundos y variación intermedia moderada. Granulación
  más fina, distinta intensidad por célula, detalle adicional filtrado por
  derivadas y una pequeña señal de relieve aparente sobre el detalle decorativo.
  La textura original de Unity aporta variación acotada, sin grandes venas.
- Se conserva **exactamente la fórmula de atenuación HMI de Fase 7.2**, con el
  mismo atlas fijo, guías, semilla y UV. Un matiz cálido discreto en los bordes
  integra las concentraciones sin cambiar sus posiciones. No se modifica el
  mapa de actividad, el sombreado de las capas científicas ni sus datos.
- `web/src/phase5/visual-materials.ts`: solo en la ruta temporal, caída de brillo
  hacia el borde más marcada y resplandor corto. El plano de corona exportado
  por Unity combina una aureola cercana con una caída difusa y conserva una
  pequeña contribución de su textura original; no se añade geometría ni texturas.
  El halo participa del mismo fundido temporal y deja la superficie visible.
- `web/src/phase5/main.ts` e `web/phase6/index.html`: identificadores Fase 7.3.
  La selección del hero y el controlador temporal de Fase 7.2 no cambian.

El movimiento local suave, las pausas independientes, los 96 trazadores y el
reloj de superficie siguen existentes. No se añaden erupciones, bucles físicos,
pulsos globales o respuestas a GOES/SI. La apariencia de calor, el relieve y el
halo son ilustrativos: no son temperaturas medidas, observación directa 3D,
velocidades, topografía ni reconstrucción magnética. Los coeficientes son de
presentación y la transferencia es la misma para las cinco fechas.

## Evidencia y validación

Directorio `prototypes/phase4-unity-needle/evidence/phase73/`:

- `baseline-identity.json` y `baseline/`: hashes comprobados contra la entrega
  final de Fase 7.2 antes de editar; seis archivos originales preservados.
- `comparison.png`: antes Fase 7.2 / después Fase 7.3, siempre HMI29, cámara frontal,
  escala 1, superficie congelada en t=0. Disco completo a distancia 2 y detalle
  a 1.15. Capturas nativas 1119×660, DPR 1.5, misma iluminación de escena.
- `comparison-motion.mp4`: cámara cercana fija, 9 s, 8 s animados a velocidad de
  presentación normal y último segundo pausado. PNG, WebM y diagnósticos nativos
  conservados. Composición sobre el mismo fondo, sin coloración, afilado posterior
  ni aceleración. El alfa se decodifica con libvpx-vp9.
- `make-comparison.py`, `make-video.py` y `verify.py` reproducen la composición y
  verifican ciencia, cámaras, integridad y retornos. El instrumento DEV existente
  `web/dev/phase72-capture.mjs` se reutiliza sin cambios; está excluido del build.
- `tests.log` / `build.log`: 26 pruebas y TypeScript/Vite correctos. Persisten los
  avisos anteriores de chunks grandes y externalización MaterialX.
- `protected.json`: 2.061 archivos sin cambios, incluidos backend, datos, frontend
  principal, recursos públicos, Unity, contexto científico, controlador temporal,
  trazadores y páginas anteriores. Sin dependencias, PNG públicos ni GLB nuevos.

La muestra pareada de 30 s (mismo navegador, HMI29, cámara 1.15, lienzo y DPR)
registró 59.9970 → 60.0319 callbacks/s, mediana 16.7 ms y p95 17.5 ms en ambas;
cero intervalos mayores a 50 ms. Sin build ni codificación simultánea durante
las muestras. Los shaders generados de Fase 5 y de las tres capas científicas
son exactamente iguales a los del snapshot de Fase 7.2 (`unchanged-shaders.json`).

Los retornos de fechas, capas congeladas, navegación,
liberación/recarga y ancho responsive se documentan en `verification.json` y
`controls.json`. La caché continúa con 20 texturas temporales más la decoración
original; tres draw calls. La cadencia de render no es tiempo de GPU, consumo
energético ni una certificación de rendimiento móvil.

## Pendiente

Revisión del usuario del balance final entre brillo, detalle y halo. Prueba
física en iPhone 15 Pro y AR para comprobar legibilidad, estabilidad y calor.
WebXR/Needle Go comparten el material por código; Quick Look sigue mostrando el
atlas horneado seleccionado, sin el nuevo shader, movimiento ni timeline.

No se ha iniciado ninguna fase posterior. Publicación únicamente con autorización.
