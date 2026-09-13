# Fase 7.1 — Dinámica visual del Sol en web y AR

> **Versión local actual: revisión 4 (`phase71-v4`)**. Recupera la continuidad de la revisión 2 y mueve detalle decorativo en el material sin desplazar HMI. Véase [informe y referencias NASA](phase71-revision4.md) y vídeo comparativo de 18 s en `evidence/phase71/revision4/comparison-18s.mp4`. Aceptación visual y AR físico pendientes; sin publicación, commit ni push. El texto siguiente conserva el historial de las revisiones 1–2.

**Estado al 10 de septiembre de 2026: PARCIALMENTE CUMPLIDA.** Implementación y
verificación web terminadas; publicación y validación física AR pendientes.
No se hicieron commits, push, despliegues ni trabajo de otra fase.

Prueba local en el Mac: http://localhost:5184/phase6/

Vídeo: `prototypes/phase4-unity-needle/evidence/phase71/revision2/surface-particles.mp4`.
Dura 10 s: 0–2 s congelado en t=0, 2–8 s animado, 8–10 s pausado. Cámara fija,
24 de marzo de 2022. El WebM original conserva alfa; el MP4 compone ese alfa
sobre el fondo oscuro del visor, sin modificar la superficie.

## Corrección tras revisión del usuario

La primera entrega tenía movimiento demasiado tenue y no incluía partículas.
El usuario no lo percibió en el vídeo; las diferencias entre píxeles de esa
versión no bastaban para demostrar una apariencia viva. La revisión **phase71-v2**
añade **256 partículas ilustrativas con estelas cortas** y una circulación local
más visible. El vídeo nuevo está rotulado «Pausado / Animando / Pausado».

Las partículas son un hijo `Points` de la malla Unity existente. Siguen trayectorias
tangenciales acotadas, con cinco muestras por estela (1.280 puntos en un único
buffer). Su distribución determinista es la misma para las cinco fechas; no
representan nuevas regiones magnéticas, eyecciones ni mediciones. Las guías HMI
seleccionadas atenúan su opacidad sobre los núcleos. Comparten reloj, pausa,
fundido y guías con el material superficial. No se añade movimiento de llamaradas.

## Implementación

Se conserva la escena real `Phase5Solar.glb` exportada por Unity 6000.3.17f1 /
Needle 5.1.12. SHA-256
`6694a42dd2f0b322c7a65dc9d55d17eb1fe653ab0ec85884ee68b20cb14999b5`.
No se ha creado otra esfera ni se ha reexportado Unity. Se amplía el mismo
`onBeforeCompile` del material de `IllustrativeSphere` que ya usaba el visor.
El movimiento nuevo es una extensión de ejecución web; no aparece por sí solo
en el editor Unity ni en una exportación USDZ.

- Granulación procedural con interpolación suave y circulación local acotada en
  coordenadas de la esfera. Las celdas se desplazan y evolucionan continuamente;
  no es un multiplicador periódico de brillo global. Dos escalas de detalle y
  una variación local lenta, semilla fija **71**, sin aleatoriedad por fotograma.
- El atlas solar se consulta siempre en sus UV originales. Ningún UV HMI ni
  vértice se desplaza. B+ y B− ya presentes en la caché guían la variación tenue
  de brillo y atenúan la granulación en concentraciones fuertes. Se reutilizan
  el círculo de cada estado y la orientación comprobada: derecha de array −X,
  arriba +Y, frente −Z. La guía de brillo usa las PNG cuantizadas de referencia;
  no es una nueva magnitud científica ni una reconstrucción del plasma.
- Se recupera la escala lineal de las guías desde su almacenamiento GPU sRGB.
  Una misma transferencia y amplitudes rigen las cinco fechas, sin usar SI,
  predicciones ni eventos GOES. El dorso tiene granulación ilustrativa; su guía
  HMI es cero. Los núcleos siguen siendo concentraciones recreadas, no manchas
  observadas. La corona/los filamentos horneados permanecen sin movimiento
  adicional. Las partículas usan una geometría auxiliar; no hay llamaradas ni efectos de gran escala.
- **Pausar/Animar superficie** y **Congelar en t=0** están separados de Play.
  El mismo control sirve al overlay DOM AR. Cambiar fecha conserva el tiempo
  visual; congelarlo permite comparar estados. La fecha solo cambia mediante
  los controles temporales existentes, incluida la acción explícita de HMI
  precedente ya presente en Fase 7.
- El atlas, las guías, el círculo, los mapas y los valores cambian en el mismo
  commit temporal. La transición de 260 ms ahora desvanece el estado que está
  comprometido, llegando a negro en el punto de cambio; no mezcla un atlas
  anterior con datos nuevos. No se crean estados científicos intermedios.
- La nota web y AR dice: **«Movimiento ilustrativo; estados magnéticos basados
  en observaciones HMI»**. La explicación distingue movimiento decorativo,
  medición continua y simulación física.

## Recursos y visibilidad

No se añaden dependencias, archivos de textura, materiales ni geometrías por
fotograma. La caché sigue siendo de veinte texturas: quince mapas y cinco atlas
2048×1024. El primer estado usa dos texturas GPU adicionales ya existentes en
esa caché (guías B+/B−): cuatro residentes observadas frente a dos antes.
La revisión 2 usa tres draw calls (antes dos) y conserva 24.578 triángulos.
Crea una geometría y un material de partículas una sola vez; ambos se liberan
explícitamente al cerrar el visor. No se reemplaza la geometría solar Unity.

El reloj se detiene con página oculta, visor fuera de pantalla, capa científica
y sesión XR oculta. Se sincroniza al volver para no acumular el intervalo
invisible; delta máximo 100 ms. Se respeta la preferencia inicial de movimiento
reducido. Al liberar el visor se desconectan el observador y los listeners XR,
se dispone el contexto y se vacía la caché temporal.

Se conserva el límite web de DPR 1,5. La fuente instalada de Needle Go aplica
su propio tamaño de framebuffer según DPR nativo durante AR; **el límite web
no certifica la resolución ni el coste en iPhone AR**. No se alteró el motor.

## Verificación

Evidencia: `prototypes/phase4-unity-needle/evidence/phase71/`.

- **26/26 tests Node** correctos, incluidos reloj visible/oculto, pausa,
  reanudación, t=0, límites de delta, material sobre malla existente y ausencia
  de transferencia/UV móviles en planos científicos. Pasan los tests de fases
  anteriores de contrato, secuencia, texturas, navegación y contexto GOES.
- **TypeScript y Vite build correctos.** Persisten los avisos anteriores de
  tamaño de bundles y externalización de `node:module` en MaterialX.
  La herramienta de grabación es solo Vite DEV + `?capture`, y no aparece
  en el bundle de producción.
- `scripts/verify-phase71.py`: **1.590 archivos protegidos intactos**, incluyendo
  la línea base científica anterior, assets públicos, Unity y código principal
  backend/frontend. Cinco estados exactos; descenso final de SI conservado.
- Vídeo inicial (conservado como evidencia histórica, insuficiente visualmente
  según revisión del usuario): veinte muestras durante 10 s mantienen idénticos fecha, SI,
  predicción, hashes de mapas/atlas, guías y cámara. En el disco del vídeo,
  diferencia RGB media entre 2,5 y 7,5 s: **4,56/255**; entre 8,5 y 9,5 s
  pausados: **0**. La compresión produce 0,16/255 entre dos fotogramas de la
  pausa inicial. Estos son indicadores visuales, no métricas solares.
- Navegación adelante/atrás y capturas de las **cinco fechas** en t=0:
  diferencia RGB máxima **0** en la región del Sol al volver a la misma fecha
  (mismo navegador/GPU). No se promete igualdad binaria entre GPUs distintas.
- Play alcanza el día 30 y se detiene; sentido inverso alcanza el 24 y se
  detiene, manteniendo t=0 superficial. En el magnetograma, el reloj decorativo
  queda exactamente congelado aunque el control figure activado; las dos
  capturas del mapa coinciden (diferencia máxima 0).
- Responsive de escritorio **393×852**: veinte combinaciones (cinco fechas ×
  cuatro capas), sin desbordamiento horizontal, sin errores, fecha y guías
  coincidentes; panel DOM AR comparte fecha/SI/estado de pausa. No es AR físico.
- Liberar: cero texturas temporales, canvas retirado. Reintentar: una instancia,
  veinte texturas en caché y sin errores. `/phase5/` carga su GLB/material
  anterior; `/` carga el cubo Unity verificado. No se alteró la simulación
  Three.js principal.

### Rendimiento de la entrega inicial (histórico)

Navegador integrado de escritorio, mismo Mac, 1280×720, DPR 1,5, cámara a
distancia 2, escala 1, vista solar, HMI del 24, sin giro ni Play. Ventanas de
30 s, sin grabación ni build simultáneos. La posterior tiene animación activa.

| Medida | Antes, Fase 7 | Después, Fase 7.1 revisión 1 |
| --- | ---: | ---: |
| Callbacks completados | 1.780 | 1.777 |
| Callbacks/s | 59,32997 | 59,23096 |
| Intervalo mediano | 16,7 ms | 16,7 ms |
| p95 | 17,5 ms | 17,5 ms |
| Intervalos >50 ms | 0 | 0 |

Cambio de cadencia: −0,17 %. No muestra una regresión relevante en esta muestra,
pero el techo de sincronización de pantalla oculta posibles costes GPU.
Es cadencia de `post_render_callbacks`, no tiempo GPU, batería, tracking ni
rendimiento móvil. Los JSON conservan condiciones y muestras. El guard de
visibilidad XR añadido al cierre no afecta la rama web visible de esta prueba.

### Rendimiento y verificación de la corrección (revisión 2)

Misma sesión, HMI 24, cámara fija, 1280×720, DPR 1,5, vista solar y animación
activa; dos muestras de 30 s sin grabación, codificación ni build concurrentes:

| Medida | Revisión 1 antes de corregir | Revisión 2 con partículas |
| --- | ---: | ---: |
| Callbacks | 1.780 | 1.782 |
| Callbacks/s | 59,33195 | 59,39703 |
| Mediana | 16,7 ms | 16,7 ms |
| p95 | 17,5 ms | 17,6 ms |
| Intervalos >50 ms | 0 | 0 |
| Draw calls solares | 2 | 3 |

No se observa caída de cadencia en esta muestra; no mide tiempo GPU ni móvil.
Los nuevos artefactos están en `evidence/phase71/revision2/`. El vídeo corregido
conserva fecha, SI, predicción, hashes, guías y cámara en sus veinte muestras;
el tiempo visual avanza de 0 a 5,9914 s y queda congelado en la pausa final.
La inspección del vídeo confirma puntos claros y estelas moviéndose sobre el
disco; los núcleos permanecen anclados. Los 26 tests comprueban también buffers
deterministas, uniformes compartidos y liberación de los nuevos recursos sin
disponer la geometría/material de la esfera. TypeScript/build y los 1.590 hashes
protegidos vuelven a pasar con esta revisión.

## Qué conserva cada recorrido AR

| Recorrido | Material y movimiento | Estado de verificación |
| --- | --- | --- |
| Web 3D | Shader procedural, partículas, reloj, atlas y guías seleccionados | Navegador verificado |
| Android WebXR | Mismo scene/material y callbacks del render web | Fuente revisada; teléfono no probado |
| iPhone Safari → Needle Go | Carga la página y renderiza mediante el canvas web/WebXR sobre ARKit | Fuente revisada; ejecución física pendiente |
| iPhone Quick Look | Textura horneada del estado seleccionado; sin este shader, partículas, reloj ni timeline | Exportador revisado; visor físico pendiente |

Las partículas se ocultan durante la exportación Quick Look y se restauran al
terminar; no se presupone que USDZ reproduzca el shader de puntos.

El render web/XR y la exportación de `material.map` se documentan con líneas de
la dependencia instalada en `ar-source-review.md`. La [documentación oficial de
Needle Go](https://engine.needle.tools/docs/reference/faq) explica que el App Clip
carga la escena web sobre ARKit y requiere HTTPS público; [Everywhere Actions /
Quick Look](https://engine.needle.tools/docs/how-to-guides/everywhere-actions/)
describe la vía de exportación USDZ separada. Ninguna de estas fuentes acredita
que esta fase ya haya funcionado en el iPhone del usuario.

No se garantiza trasladar automáticamente fecha/tiempo visual de Safari a un
nuevo contexto de Needle Go. Hay que comprobar materiales, controles,
colocación y pausa en la sesión real. La prueba de unos cinco minutos está en
`evidence/phase71/PRUEBA-IPHONE.md`. **No realizada.**

## Archivos y entrega

Dentro de `prototypes/phase4-unity-needle/web/`:

- Modificados: `src/phase5/main.ts`, `src/phase5/visual-materials.ts`,
  `src/phase6/temporal.ts`, `phase6/index.html`.
- Añadidos: `src/phase6/surface-motion.mjs`, `src/phase6/surface-shader.ts`,
  `src/phase6/surface-particles.ts`, `tests/phase71.test.mjs`, `dev/phase71-capture.mjs`.

También: `scripts/verify-phase71.py`, evidencias bajo `evidence/phase71/`,
este informe y la actualización de `AGENTS.md`. `dist/` se regenera por el build.
El resto de cambios preexistentes del repositorio se conserva.

Reproducir: `npm test`, `npm run build` desde `web/`;
`python3 scripts/verify-phase71.py` desde el prototipo. Para grabar, ejecutar
Vite, abrir `/phase6/?capture`, seleccionar el 24, cámara restablecida y usar
«Grabar evidencia 10 s». El textarea local de evidencia contiene WebM y las
muestras; no se envía a ningún servicio.

La URL pública existente continúa en **versión 11 / Fase 7**. La URL local
entregada sí contiene 7.1; no funciona como enlace del teléfono al Mac. Publicar
esta modificación mediante Sites requiere commit/push autorizado: se respeta
la restricción del usuario. El permiso y los resultados físicos son pendientes
separados. No se ha iniciado otra fase.

**FASE 7.1: PARCIALMENTE CUMPLIDA**
