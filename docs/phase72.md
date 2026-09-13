# Fase 7.2 — Auditoría del estado y pulido hero

Implementación local en `/phase6/`, build `phase72-v1`. Hero único: **29 de marzo
2022, 00:00:53 UTC**, `hmi-2022-03-29`. Sin commit, push ni publicación. El sitio
público sigue en versión 11. La aceptación estética final y las pruebas físicas
con iPhone/AR quedan pendientes; las verificaciones técnicas no certifican realismo.

## Auditoría realizada antes de modificar

La comparación más reciente **no trabajaba el 29 ni el 30**, sino el **24 de marzo
2022, 00:00:53 UTC**, `hmi-2022-03-24`, índice 0, SI 1.679617166519165 y ONNX
1.4705196619033813. Se cruzaron:

- `evidence/phase71/revision4/before-full.json` y `before-close.json`: revisión 2,
  HMI24, distancias 2 y 1.15, escala 1.
- `evidence/phase71/revision4/after-full.json` y `after-close.json`: revisión 4,
  misma fecha, cámaras y escala. Son los registros de `comparison-18s.mp4`.
- `evidence/phase71/revision4/verification.json`, incluidas ambas mediciones de
  rendimiento, y `docs/phase71-revision4.md`.
- `web/src/phase6/temporal.ts`: inicialmente `index=0`, `target=0`, carga de
  `bundles[0]`; `web/public/phase6/sequence.json` identifica ese elemento como HMI24.
- Navegador local antes de editar: 24 de marzo, posición 1/5, build `phase71-v4`.

La auditoría fue comunicada explícitamente antes del primer cambio. `audit.json`
y los seis archivos originales en `evidence/phase72/baseline/` conservan el punto
de partida. El shader era compartido por las cinco fechas: no existía un pulido
especial del 30. Los PNG `forward-29.png` y `forward-30.png` de revisión 4 eran
pruebas de retorno de fecha, no los protagonistas de la comparación.

Se eligió el **29**, conforme a la preferencia del usuario y por el grupo más
extendido de concentraciones frontales en las imágenes con igual cámara. Es una
decisión visual, no una inferencia a partir de la llamarada X1.3 ni una nueva
selección científica. SI conservado: 2.057671546936035%; ONNX:
1.6834452152252197%. El descenso real del SI el 30 se conserva.

## Cambio acotado

- `web/src/phase6/temporal.ts` busca el hero por su ID después de comprobar y cargar
  los recursos. Inicializa índice/objetivo al 29 y falla si falta. El orden 24,
  25, 28, 29, 30, la cadencia y los controles temporales permanecen.
- `web/phase6/index.html` identifica Fase 7.2 y muestra la marca de hero solo
  cuando el 29 está seleccionado. `web/src/phase5/main.ts` actualiza esa marca y
  los identificadores diagnósticos únicamente en la ruta temporal.
- `web/src/phase6/surface-shader.ts` conserva el atlas HMI y sus UV fijos, las
  guías B+/B−, la semilla 71 y la decoración original de Unity. Separa mediante
  una razón de color el oscurecimiento ya horneado de los filamentos decorativos
  gruesos. Aplica atenuación escalar para evitar colores azul/verde espurios;
  las transiciones de polaridad siguen siendo cálidas y discretas.
- Granulación ilustrativa continua en espacio del objeto: centros irregulares,
  interiores suaves, deformación local acotada, detalle a varias escalas y
  filtrado por derivadas para reducir aliasing. Se atenúan los grandes filamentos
  y el contraste excesivo de la base que producía apariencia de lava.
- `web/src/phase5/visual-materials.ts` reduce únicamente el halo temporal.
  `web/src/phase6/surface-particles.ts` conserva los 96 trazadores y sus tres
  muestras, con menor opacidad y velocidad. Se mantienen los relojes separados,
  pausas y congelación; no se recupera el giro uniforme del material.

No se cambian geometría, GLB Unity, texturas PNG, dependencias, resolución de HMI,
modelos ni datos. Los detalles añadidos son visuales; **no aumentan la resolución
científica ni representan una observación 3D directa**, velocidades medidas,
manchas confirmadas o una reconstrucción física. La misma transferencia se aplica
a las cinco fechas; no hay parámetros particulares derivados de SI o GOES.
Se conservan recursos y mejoras de continuidad de revisión 4.

## Comparación y verificación

Evidencia bajo `prototypes/phase4-unity-needle/evidence/phase72/`:

- `comparison.png`: antes/después del **mismo HMI29**, disco completo y detalle,
  escala 1, mismas cámaras, iluminación y lienzos nativos 1119×660 a DPR 1.5.
  Distancias 2 y 1.15; tolerancia de cámara 1e-12 por redondeo de OrbitControls.
  PNG originales con alfa conservados; composición sobre el mismo fondo del visor.
  La captura cercana original tiene un diagnóstico de reloj previo, actualizado
  cada 500 ms, aunque se capturó tras el control de congelación. No se usa ese
  campo atrasado como medición del tiempo exacto del fotograma.
- `comparison-motion.mp4`: 9 s, misma cámara cercana/fecha/escala, 8 s de animación
  a velocidad de presentación normal y último segundo pausado. WebM nativos,
  estados durante el vídeo y dos PNG pausados por versión quedan guardados.
  La composición regulariza la cadencia a 30 fps sin acelerar ni colorear las
  imágenes; alfa decodificado con libvpx-vp9. Script `make-video.py`.
- `verify.py` / `verification.json`: igualdad de ciencia/cámara/escala en ambos
  lados; cinco retornos de fecha con igualdad exacta de píxeles; capas científicas
  y último segundo de vídeos congelados con igualdad exacta. 2.057 hashes
  protegidos sin cambios, incluidos backend, frontend principal, datos, contratos,
  recursos públicos, Unity y contexto de Fase 7.
- `tests.log` y `build.log`: 26 pruebas existentes y TypeScript/Vite pasan.
  Avisos previos de tamaño de chunks y externalización MaterialX persisten.
- `controls.json`: órbita, pausa superficial independiente, reproducción hasta
  ambos extremos, evento externo que conserva HMI, liberación y recarga del hero.
- `dev/phase72-capture.mjs` es un instrumento local de evidencia bajo DEV +
  `?capture`: cámaras fijas, PNG posterior al render y vídeo del canvas. No forma
  parte de la compilación publicada y no cambia datos científicos.

Muestras de 30 s en el mismo navegador, HMI29, cámara cercana, DPR 1.5 y lienzo:
59.9962 → 59.9948 callbacks/s; mediana 16.7 ms en ambos; p95 17.5 → 18.3 ms;
cero intervalos mayores a 50 ms. Sin build ni codificación simultánea durante
cada muestra. Son cadencias de render de escritorio, **no tiempos GPU ni
rendimiento móvil**. El shader añade cálculo por píxel; conservar cadencia no
prueba igual coste energético. Cache de 20 texturas temporales más la decoración
original; tres draw calls. Se mantiene liberación explícita.

## Límites pendientes

WebXR y Needle Go comparten el camino de material y controles por código. La
prueba física en iPhone 15 Pro, colocación AR, estabilidad, calor y rendimiento
siguen pendientes. Quick Look conserva el atlas horneado seleccionado y no incluye
este shader, movimiento o timeline. Esa diferencia sigue visible en la interfaz.

Publicación solo después de autorización. No se ha iniciado ninguna fase posterior.
