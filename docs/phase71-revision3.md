# Fase 7.1 — Corrección de naturalidad, revisión 3

**Implementación y comprobaciones locales completas; aceptación visual y AR físico pendientes.**
Build `phase71-v3`. No publicación, commit, push ni nueva fase.

Prueba local: http://localhost:5184/phase6/ . El sitio público sigue en versión 11 / Fase 7.

## Referencias revisadas antes de corregir

Se recuperaron de la tarea **«Construye gemelo solar Fase 5»**:

- [Primera referencia](https://x.com/konstructivizm/status/2097602156287385966): disco dorado, estructuras en arco, brillo difuso; rótulo PROBA2/SWAP 174, fechas de junio de 2012.
- [Segunda referencia](https://x.com/konstructivizm/status/2097578751722999827): disco rojizo, tejido brillante y prominencia en el borde, con rótulo GOES-19/SUVI.

Ambos reproductores embebidos se reprodujeron y se inspeccionaron en distintos momentos. La ampliación solicita sesión en X; se mantuvo la vista embebida. Son republicaciones: no se certificaron procedencia, calibración ni velocidad temporal. El texto de la primera publicación habla de Voyager y no se usa como explicación del vídeo.

La interpretación visual es **estructura atmosférica**, no trazadores individuales ni una medición de granulación fotosférica. Se toma su evolución local de formas/brillo como referencia. El resultado de Auralis sigue siendo microestructura granular ilustrativa; no copia erupciones ni reconstruye movimientos atmosféricos o velocidades físicas.

Capturas y notas: `prototypes/phase4-unity-needle/evidence/phase71/revision3/references.md` y `reference1.png` / `reference2.png`.

## Diagnóstico y corrección localizada

La revisión 2 superponía puntos claros con cinco muestras por estela, persistentes y con trayectorias sinusoidales cerradas. El ruido superficial de escala 45 se desplazaba con un campo periódico amplio. Esta combinación favorecía el aspecto de chispas y circulación, aunque los atlas magnéticos permanecían fijos.

La revisión 3 elimina los trazadores y su geometría/material auxiliar. Extiende el mismo material de **IllustrativeSphere** del GLB real Unity, conservando color horneado, iluminación, corona, cámara y geometría.

El ruido se evalúa en coordenadas espaciales fijas. Sus valores vecinos tienen fases, duraciones y generaciones deterministas independientes, con interpolación quíntica: las formas pequeñas emergen, se transforman y se disuelven gradualmente. No hay un vector de circulación, desplazamiento UV ni pulsación global.

- Detalle principal: escala espacial 105; transiciones locales de 3,5–8,5 segundos de presentación.
- Detalle fino: escala 181 y otro ritmo (factor 1,31). El brillo local cambia más lentamente (factor 0,38).
- Filtro por huella de píxel `fwidth`: reduce detalle no resoluble al alejar y junto al limbo. La escala permanece fijada a la esfera al acercar.
- Misma semilla 71 y transferencia para las cinco fechas. Las guías B+/B− atenúan la variación en concentraciones fuertes; no mueven ni sustituyen núcleos del atlas.

Estas duraciones y escalas son decisiones gráficas, no valores solares medidos. El ruido introduce detalle ilustrativo, no nuevas regiones científicas. La base horneada sigue siendo una aproximación estilizada; no se declara equivalencia fotográfica con las referencias.

## Ciencia y controles

Los atlas, quince mapas lineales, cinco HMI, SI, predicciones, fechas y contrato permanecen iguales. Se conserva el GLB de 6.206.672 bytes con SHA-256 `6694a42dd2f0b322c7a65dc9d55d17eb1fe653ab0ec85884ee68b20cb14999b5`.

No se modificó el controlador temporal, su fundido de 260 ms ni el reloj de superficie. Pausa/reanudación mantiene el tiempo acumulado; la sincronización al volver de una pausa evita incorporar el intervalo invisible. Play histórico, selección de fechas, capas, órbita, zoom, escala y overlay AR conservan sus controles. Los modos HMI/B+/B− no reciben el shader granular.

La aclaración existente sigue visible: «Movimiento ilustrativo; estados magnéticos basados en observaciones HMI», con explicación de que no es medición continua ni simulación física.

## Vídeo comparativo

`prototypes/phase4-unity-needle/evidence/phase71/revision3/comparison-18s.mp4`

**18,000 s, 1320×766, 30 fps.** Antes a la izquierda, después a la derecha:

- 0–9 s: disco completo, distancia de cámara 2.
- 9–18 s: acercamiento, distancia 1,15, con el mismo recorte central por lado.
- Cada segmento reinicia en t=0, anima 8 s y pausa el último segundo. Velocidad de presentación 1×, sin aceleración en edición. El reloj real difiere unas centésimas entre capturas por la cadencia de render, registradas en los JSON.

Las cuatro tomas mantienen HMI del 24 de marzo, cámara, escala 1, atlas, iluminación y material base. Se capturó el canvas nativo a 1119×660. Solo se compuso su alfa sobre el fondo oscuro del visor, se aplicó el mismo recorte y se añadieron rótulos; no se ajustó color ni velocidad. Los WebM originales y 18 muestras de diagnóstico por toma se conservan.

La inspección de fotogramas confirma la retirada de puntos/estelas y núcleos en las mismas posiciones. **La preferencia y naturalidad visual requieren la revisión del usuario; los tests no la acreditan.**

Reproducir el montaje: `python3 prototypes/phase4-unity-needle/evidence/phase71/revision3/make-comparison.py` (FFmpeg y Pillow instalados, sin dependencias nuevas del proyecto).

## Verificación

- 25/25 tests Node pasan. Se retiró el test específico del sistema de partículas eliminado; se mantienen tests de contrato, mapas, navegación, eventos, reloj y aislamiento del material científico.
- TypeScript + Vite build pasan. Continúan los avisos anteriores de bundles grandes y externalización de `node:module` en MaterialX.
- Shader compilado/renderizado en el navegador sin errores. No se crean materiales/geometrías/texturas por fotograma; veinte texturas en caché, dos llamadas de dibujo solares y 24.578 triángulos.
- 1.590 archivos protegidos conservan sus hashes. Descenso final de SI conservado.
- Cinco fechas, recorrido adelante/atrás con t=0: diferencia RGBA máxima **0** al regresar a cada fecha, con imagen no vacía.
- Pausa: dos capturas sin pérdida separadas en el tiempo, diferencia máxima **0** y mismo reloj. Reanudar vuelve a avanzar desde el tiempo acumulado.
- HMI, B+ y B−: dos capturas por capa coinciden exactamente mientras el reloj superficial permanece detenido aunque la animación esté habilitada.
- Play llega al 30 y se detiene; dirección inversa vuelve al 24 y se detiene. Se conserva la independencia de la pausa superficial.
- Liberación/reintento comprobados; ver JSON de estado. No se afirma prueba física ni medición móvil.

Las capturas PNG se leen dentro de un callback posterior al render real. Los primeros intentos fuera del render devolvieron buffers vacíos y se descartaron; el verificador rechaza imágenes vacías. Los PNG sin componer conservan alfa y pueden verse con halo incorrecto en lectores que lo ignoren; el MP4 muestra la composición correcta.

Verificación reproducible: `python3 prototypes/phase4-unity-needle/evidence/phase71/revision3/verify.py`. Resultado en `verification.json`; capturas/diagnósticos en la misma carpeta.

## Rendimiento antes/después

Mismo navegador integrado y sesión en el Mac, HMI 24, cámara a 2, escala 1, DPR 1,5, animación activa. Ventanas de 30 s sin grabación/build concurrentes. Canvas de las tomas 1119×660; la página efectiva se comprobó a 780×709. El intento de override 1280×720 no se aplicó: no se atribuyen esas dimensiones a esta prueba.

| Medida | Revisión 2 | Revisión 3 |
| --- | ---: | ---: |
| Callbacks | 911 | 911 |
| Cadencia | 30,36586/s | 30,36535/s |
| Mediana de intervalo | 33,3 ms | 33,3 ms |
| p95 | 34,0 ms | 34,6 ms |
| Intervalos >50 ms | 1 | 1 |
| Llamadas de dibujo solares | 3 | 2 |

No se observa caída de cadencia en estas muestras; el p95 aumenta 0,6 ms. Es cadencia de callbacks de escritorio, no tiempo GPU, batería, tracking ni rendimiento físico móvil. No se compara con los ~60 callbacks/s de otra sesión anterior. Los dos JSON incluyen condiciones, cámara, estado y diagnósticos.

## Navegador, AR y Quick Look

Web 3D: material corregido, movimiento, pausas, capas y navegación comprobados. WebXR y Needle Go conservan la ruta del material web y los controles compartidos; **requieren nueva prueba física** de detalle, filtrado, pausa/reanudación, cambios de fecha, tracking, calor y rendimiento en el iPhone 15 Pro. No se inició ninguna sesión AR física en esta revisión.

Quick Look sigue siendo una instantánea de la textura horneada seleccionada: **sin shader procedural, movimiento granular, timeline ni controles web**. Al eliminar los puntos se retiró únicamente la ocultación/restauración de esos puntos durante su exportación; se conserva la ruta USDZ.

Guía física existente: `prototypes/phase4-unity-needle/evidence/phase71/PRUEBA-IPHONE.md`. La versión pública no incluye esta corrección y el localhost no es accesible desde el teléfono como enlace al Mac. Publicar requiere autorización del usuario, separada de la validación visual/física.

## Archivos de esta corrección

Bajo `prototypes/phase4-unity-needle/web/`:

- `src/phase6/surface-shader.ts`: evolución local, ritmos y filtro de detalle.
- `src/phase5/main.ts`: retirada de partículas y etiqueta `phase71-v3`.
- `src/phase5/visual-materials.ts`: nueva clave de caché del shader.
- Eliminado `src/phase6/surface-particles.ts`; copia histórica en `revision3/baseline/`.
- `tests/phase71.test.mjs`: retirada del test del sistema eliminado.
- `dev/phase71-capture.mjs`: capturas comparables y PNG después del render, solo DEV + `?capture`; excluido de producción.

Evidencia y diferencias respecto a la revisión 2: `evidence/phase71/revision3/product-changes.patch`, scripts de montaje/verificación, originales, diagnósticos y hashes. Actualizados este informe, `docs/phase71.md` y `AGENTS.md`. Los cambios preexistentes del repositorio se conservan.

**FASE 7.1: PARCIALMENTE CUMPLIDA — revisión visual del usuario y validación física AR pendientes.**
