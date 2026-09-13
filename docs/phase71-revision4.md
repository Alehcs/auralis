# Fase 7.1 — Revisión 4: continuidad del detalle solar

Implementación local en `/phase6/`, build `phase71-v4`. No publicación, commit,
push ni fase posterior. La aceptación visual corresponde al usuario; las pruebas
técnicas no demuestran realismo. El sitio público continúa en la versión 11.

## Referencias observadas y criterio visual

Se reprodujeron en navegador el [vídeo de granulación Hinode](https://svs.gsfc.nasa.gov/3412),
el [vídeo SDO/AIA 171 Å](https://svs.gsfc.nasa.gov/4761) y el
[GIF Small Prominences de NASA/GSFC/SDO](https://science.nasa.gov/photojournal/small-prominences/).
También se inspeccionó la imagen ampliada de Hinode. Capturas y enlaces concretos
quedan en `evidence/phase71/revision4/references/` bajo el prototipo Needle.

Hinode muestra pequeñas células con bordes irregulares que conservan identidad
mientras se deforman. La referencia AIA muestra filamentos atmosféricos,
estructuras persistentes y brillo localizado. Son escalas y observables distintos;
la apariencia dorada del visor es una recreación, no color visible calibrado.
Los montajes solares comprimen tiempo observacional y no determinan velocidades
medidas para Auralis. No se incorporan imágenes NASA como nuevos mapas HMI.

El usuario prefirió la revisión 2: sus puntos permitían seguir recorridos y
percibir continuidad. La revisión 3 había eliminado esas pistas y modulado brillo
sobre una textura casi inmóvil. Esta revisión parte de la 2 y traslada el movimiento
principal al detalle decorativo del material. Una primera prueba de desplazamiento
más amplio producía estiramiento viscoso al acercarse; se redujo a la mitad tras
inspeccionar la comparación. Esa prueba se conserva como `trial-wide-flow/` y no
corresponde al resultado final.

## Cambio localizado

- El material retiene la textura ilustrativa original del GLB Unity, sin HMI.
  Un campo local continuo de ruido mueve suavemente su detalle, con ritmos
  distintos según la posición. El desplazamiento está acotado; no acumula giro
  global, desplazamiento uniforme de UV ni una órbita común a toda la esfera.
- La textura seleccionada de actividad y las guías HMI se muestrean siempre en sus
  UV originales. Una razón de color entre decoración desplazada y original aporta
  el detalle móvil, atenuado en concentraciones magnéticas. Los vértices no cambian.
- Dos escalas finas de modulación completan la variación local; las derivadas del
  shader atenúan el detalle no resoluble en el borde o con zoom lejano. No se
  agrandan las células al variar la cámara. El atlas original limita el detalle
  disponible con mucho aumento; no se afirma alcanzar resolución telescópica.
- Puntos ilustrativos: 256 → 96; muestras de estela: 5 → 3. Tamaño máximo 8 → 3,5
  píxeles, menor opacidad y color cálido; ciclos de aparición/desaparición de 4–9
  segundos de presentación, con fases y velocidades diferentes. Siguen siendo
  ilustrativos, sin erupciones o nuevas regiones científicas.
- Halo web con opacidad reducida al 65% y luces menos saturadas. No se modifica
  iluminación, exposición de cámara, geometría, GLB, PNG o materiales Unity guardados.
- Se reutilizan reloj y controladores de la revisión 2, incluidos pausa de
  superficie, congelado en t=0, timeline independiente, fundido atómico y AR DOM.

Archivos del producto: `web/src/phase6/surface-shader.ts`,
`web/src/phase6/surface-particles.ts`, `web/src/phase5/visual-materials.ts` y
`web/src/phase5/main.ts`. El cambio del controlador se limita a conservar/liberar
la textura decorativa y actualizar el identificador de revisión.

No nuevas dependencias, endpoints ni archivos de textura descargados. Se conservan
los 20 recursos temporales y una textura decorativa ya incluida en Unity; se libera
explícitamente al cerrar. En la vista solar: tres draw calls, 24.578 triángulos y
cinco texturas GPU observadas, frente a cuatro en la revisión 2. La textura extra
es un coste real de memoria; la cadencia de escritorio no demuestra igualdad de
coste GPU o rendimiento móvil.

## Evidencia reproducible

Directorio: `prototypes/phase4-unity-needle/evidence/phase71/revision4/`.

- `comparison-18s.mp4`: revisión 2 frente a 4; 9 s de disco completo, 9 s cerca.
  HMI del 24-03-2022 00:00:53 UTC, misma cámara, escala 1, iluminación y velocidad
  de presentación. Distancias 2 y 1,15. Cada sección: 8 s animados desde t=0 y
  1 s pausado. Capturas nativas de canvas 1206×855, DPR 1,5; composición 1712×962
  a 30 fps. Los WebM nativos tienen cadencia variable de 29,75–30 fps; el MP4
  regulariza la cadencia sin cambiar la duración ni la velocidad del movimiento. El recorte y fondo son idénticos para ambas mitades; no se altera
  velocidad, exposición ni color de la grabación.
- WebM originales, PNG sin pérdida, diagnósticos de cada captura y script
  `make-comparison.py`. El alfa se decodifica con libvpx-vp9 antes de componer;
  ignorarlo daría un halo erróneo. `verify.py` rechaza imágenes vacías y comprueba
  ciencia/cámara iguales, duración y congelación exacta de píxeles.
- `tests.log`, `build.log`, `protected.json` y `verification.json`: pruebas del
  contrato, recursos y controles; build TypeScript/Vite; 1.590 hashes protegidos.
  El aviso de chunks grandes y la externalización MaterialX son preexistentes.
- Imágenes de retorno por las cinco fechas, mapas científicos, pausa y reanudación,
  reproducción histórica en ambos sentidos, liberación y recarga del visor.
- `performance-before.json` y `performance-after.json`: muestras de 30 s en la
  misma sesión de navegador, fecha, cámara y resolución. Son callbacks de render,
  no tiempos de GPU. Resultado: 59,9966 → 59,9980 callbacks/s; mediana 16,7 ms en ambos,
  p95 18,5 → 18,6 ms, cero intervalos mayores de 50 ms. Sin compilación, codificación
  o vídeos simultáneos durante la muestra final. La cadencia no prueba igual coste GPU.
  Los datos completos están en `verification.json`.

No se tocaron HMI, B+/B−, SI, ONNX, fechas, modelos, backend, contrato temporal ni
simulación principal Three.js. La posición de las regiones sigue procediendo del
magnetograma elegido. No hay velocidades medidas, interpolación física entre
observaciones o efectos condicionados a GOES/SI. La aclaración permanece visible.

## Navegador y AR

Verificación de escritorio: escena Unity real, materiales compilados en WebGL,
capas, zoom, navegación y reproducción reversible, pausa/reanudación independiente,
retorno reproducible y liberación/recarga. La prueba no certifica teléfonos.

WebXR/Needle Go comparten este material y reloj por código; requieren una nueva
prueba física en iPhone/Android para resolución, fluidez, temperatura, colocación,
seguimiento y controles AR. No se ha realizado esa prueba. Quick Look conserva
solo el atlas horneado del estado seleccionado y materiales originales; no conserva
el nuevo flujo, los puntos, el ajuste del halo, la timeline ni los controles web.
