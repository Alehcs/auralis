# Pulido visual solar — iteración abierta

Fecha: 9 de septiembre de 2026. Módulo: `/phase5/`, dentro de
`prototypes/phase4-unity-needle`. Se conserva la arquitectura Unity → Needle → web,
Unity 6000.3.17f1, Needle 5.1.12, dependencias, controles y recorrido AR existente.

**Publicado, versión 8:**
[Abrir el visor](https://auralis-phase4-needle-probe.alejandro-cornejog4.chatgpt.site/phase5/).
Commit del repositorio aislado del sitio: `1e1ad792ae4f347ec93d6c8ea26d0037487bc049`.
Publicación terminada a las 18:57:37 UTC. No se ha hecho commit del repositorio padre.

## Auditoría y referencias

Se revisaron la escena y el autor Unity, los materiales, el módulo web, el contrato
y la simulación independiente `auralis-front/.../simulation/SolarScene.tsx`.
Esta última ya es una ilustración Three.js independiente; permanece intacta.
El visor que mostraba el reverso gris y «sin datos» era `/phase5/`.

Los dos videos proporcionados se pudieron reproducir en el navegador:

- [Primera referencia](https://x.com/konstructivizm/status/2097602156287385966):
  disco dorado, filamentos de brillo desigual, borde radiante y atmósfera difusa.
  En el video se ve una identificación PROBA2/SWAP 174 y fecha de 2012; el texto
  del post habla de Voyager, por lo que no se usa como descripción del video.
- [Segunda referencia](https://x.com/konstructivizm/status/2097578751722999827):
  tonos anaranjados/rojizos, textura fina, áreas muy brillantes y plasma exterior
  cambiante. Son referencias visuales compartidas por @konstructivizm; no se
  certifica aquí la procedencia original de los reposts.

Se interpretan textura, contraste y atmósfera; no se copian los videos ni se
asocian sus eventos al magnetograma de 2022. Capturas de revisión locales en
`evidence/visual-polish/reference-1.png` y `reference-2.png`.

## Cambios y reutilización

- Una malla esférica Unity sustituye los dos hemisferios de materiales distintos.
  Textura ilustrativa 2048×1024, horneada a partir de coordenadas 3D, ruido en
  cuatro escalas, deformación espacial, filamentos y grano fino. Los extremos de
  longitud y los polos coinciden; el reverso tiene el mismo acabado completo.
- La corona usa una textura transparente Unity de 512², caída radial y variación
  angular. El componente exportable `LookAt` de Needle mantiene la corona hacia
  la cámara. Se corrigió el uso de `Mathf.SmoothStep`: sus argumentos son valores
  interpolados, no los umbrales de la función GLSL del mismo nombre.
- El navegador amplía los materiales exportados: oscurecimiento hacia el limbo,
  leve borde cálido y desplazamiento muy lento de textura. «Pausar plasma» detiene
  ese movimiento; se inicia detenido con la preferencia de movimiento reducido.
  La fecha, el magnetograma y los resultados de Coronium permanecen fijos.
- Se elimina el texto del reverso. «Recreación 360°» identifica toda la esfera
  como ilustración: completar su apariencia no reconstruye observaciones ocultas.
- Magnetograma/B+/B− mantienen los PNG originales dentro del GLB, byte a byte.
  Los planos miran a la cámara para permanecer legibles desde cualquier ángulo.
  Referencia 2D mayor y contraste visual 1×/4×/12× con leyenda explícita.
  En mapa firmado: `clamp((gris−0,5)×ganancia+0,5)`; en canales: `clamp(gris×ganancia)`.
  A 4× se satura visualmente en ±0,25 o magnitud 0,25. A 1× vuelve la escala original.
  Transferencia sRGB coherente entre material web y referencia HTML. No se cambian
  píxeles de origen, medias B+/B−, SI ni predicción.
- Se reutilizan carga con hashes, cámara, órbita, zoom limitado, reset, escala,
  giro opcional, QR, WebARSessionRoot, Needle Go, diagnóstico y liberación.
  El panel AR conserva referencia, capas y escala, y permite alternar el contraste.

No hay proyección de un disco HMI sobre un globo ni ubicación regional inventada.
El primer estado sigue siendo `hmi-2022-03-24`, 00:00:53 UTC. SI conservado y ONNX
determinista se leen del contrato y permanecen separados de las métricas MC.

## Archivos

Dentro del prototipo:

- `unity/Assets/Editor/Phase5Solar.cs`, `unity/Assets/Scenes/Phase5Solar.unity`,
  recursos generados en `unity/Assets/Phase5/` y sus metadatos.
- `web/src/phase5/main.ts`, `visual-materials.ts`, `style.css`, `web/phase5/index.html`.
- `web/public/phase5/Phase5Solar.glb`, `export-evidence.json`, `state.json`;
  se retira `assets/no-data-label.png`. Los tres PNG científicos se conservan.
- `scripts/build-phase5-assets.py` actualiza únicamente los metadatos visuales;
  `scripts/verify-phase5.py` comprueba esfera continua, mapas y estado conservados;
  `scripts/prepare-phase5.sh` dirige el log a esta iteración.
- `scripts/audit-phase5-public.py` admite `--output` para guardar la nueva auditoría
  sin sobrescribir la evidencia de publicación anterior.
- Evidencia nueva: `evidence/visual-polish/`. Las evidencias iniciales de Fase 5
  permanecen como registro histórico.

Fuera del prototipo: este informe, referencia al mismo en `docs/phase5.md` y
actualización contextual de `AGENTS.md`. Backend, métricas, modelos, Agent Lab,
frontend principal y cubo de Fase 4 no reciben cambios de esta iteración.

## Validación y límites

La verificación comprueba radio y cobertura de la malla completa, continuidad de
textura en longitud/polos, ausencia de la textura del rótulo en el GLB, igualdad
de píxeles/UV científicos y conservación exacta del estado observacional.
También coteja la línea base anterior de 1.959 archivos protegidos y una nueva
línea base de 1.494 archivos de esta iteración.

Resultados registrados en `evidence/visual-polish/`:

- Unity exportó realmente el GLB: 6.206.672 bytes, SHA-256
  `6694a42dd2f0b322c7a65dc9d55d17eb1fe653ab0ec85884ee68b20cb14999b5`.
  Es mayor que el anterior (2,48 MB) por la textura esférica 2048×1024 sin pérdida;
  supone más transferencia y memoria de textura. No se descargan videos de X.
- 12 tests Node y TypeScript/build Vite pasan; se mantienen las advertencias
  heredadas de tamaño de chunks y MaterialX del runtime.
- Verificador de GLB/mapas/estado y ambas líneas base: aprobado.
- Acceso anónimo: los 36 archivos del build público coinciden, permitiendo solo
  la inserción identificada de Cloudflare en el HTML. El navegador público carga
  el hash esperado sin errores.
- Órbita, reverso completo, mapas orientados hacia cámara, contraste 1/12 y leyenda,
  pausa real del tiempo ilustrativo, liberación (cero motores) y recuperación:
  comprobados. La referencia 2D permanece cargada con 512² al liberar.
- Publicación: límites de zoom 1,15/3,8 comprobados; disposición a 393×852 CSS px
  sin desbordamiento horizontal, cuatro capas activas, referencia 512² y ausencia
  de «sin datos» en la interfaz. Es una prueba de disposición en escritorio.
- Muestra de escritorio con plasma activo: 897 callbacks en 30,0018 s,
  **29,898 renders/s**, mediana 33,3 ms, p95 33,9 ms, cero intervalos >50 ms.
  Es cadencia observada del navegador integrado en ese entorno, no tiempo GPU,
  benchmark controlado contra la versión anterior ni rendimiento de un iPhone.

Se conservan `before-solar.png`, `public-front.png`, `public-rear.png`, los tres
mapas, verificaciones, logs y publicación. No se equipara el resultado del Mac al móvil.

Needle Go conserva los materiales y comportamientos web, pero esta iteración no
ha sido probada físicamente en el iPhone. Quick Look es una ruta reducida: conserva
la esfera/textura horneada y los mapas con escala original; no exporta los ajustes
de shader del navegador, su movimiento, su contraste ni el panel HTML.
No hay simulación MHD, reconstrucción EUV real, evolución temporal ni llamaradas.
Este es un pulido fuerte, todavía abierto a revisión visual en el teléfono.

## Cómo probar

En la URL habitual `/phase5/`, arrastra hasta dar una vuelta completa; comprueba
la continuidad de la superficie. Acerca/aleja y restablece. Pausa/reanuda plasma y
giro por separado. Cambia magnetograma/B+/B−, compara la referencia 2D y prueba
contraste 1×, 4× y 12× mirando la leyenda; los valores SI y fecha no deben cambiar.

En el iPhone 15 Pro, repite en Brave y Chrome. Para AR usa Safari → Needle Go,
coloca, ajusta escala y explora alrededor. Comprueba materiales, capas, contraste,
estabilidad y salida/reentrada. Registra versiones y resultado con el formulario
del visor. Quick Look se comprueba y registra por separado.

Para ejecución local: `npm run dev` desde `prototypes/phase4-unity-needle/web`,
abrir `http://localhost:5184/phase5/`. Para compilar: `npm test` y `npm run build`.
Para verificar origen/exportación: los scripts `build-phase5-assets.py --check`
y `verify-phase5.py`. Para regenerar la apariencia desde C#, ejecutar explícitamente
`Phase5Solar.RebuildAndExport` en Unity; la preparación normal reexporta la escena
guardada sin reemplazar su autoría.
