# Fase 6.1 — Evolución visual 3D del gemelo temporal

**Estado: PARCIALMENTE CUMPLIDA.** Implementación y pruebas web realizadas.
La validación física de iPhone/AR continúa pendiente. No se inicia otra fase.

URL: https://auralis-phase4-needle-probe.alejandro-cornejog4.chatgpt.site/phase6/

Publicada como **versión 10**, 9 de septiembre de 2026, 22:04:13 UTC.
Commit exclusivo del sitio: `736589f4e0a17332c91b8431804ed67e723c5b9c`.
No se hace commit del repositorio padre. Detalles: `evidence/phase61/publication.json`.

## Representación espacial

La misma esfera real exportada desde Unity recibe cinco texturas de superficie
distintas, derivadas directamente de los cinco `.npy` originales de marzo de 2022.
No se sustituye la geometría ni se afirma una nueva exportación Unity. El GLB
permanece en `web/public/phase5/Phase5Solar.glb`, SHA-256
`6694a42dd2f0b322c7a65dc9d55d17eb1fe653ab0ec85884ee68b20cb14999b5`.

El adaptador `scripts/build-phase61-assets.py` verifica cada hash de entrada contra
el contrato congelado. La secuencia de Fase 6 y sus quince PNG lineales se conservan.
Un manifiesto separado `web/public/phase6/activity.json` enlaza estado, hash de
magnetograma, círculo ajustado, atlas, contrato, secuencia, script y GLB.

1. Se detecta la silueta del disco por el exterior cero de la matriz procesada,
   rellenando huecos internos, y se ajusta un círculo por mínimos cuadrados.
   Radios: 251.42–251.87 px. Residuo de contorno p95: 0.67–0.75 px; máximo <2 px.
   Es una geometría de presentación estimada desde la matriz, no calibración WCS.
2. Para una posición de imagen `(col,row)`, derecha normalizada es
   `r=(col-cx)/R` y arriba `h=(cy-row)/R`. Su punto en el hemisferio frontal es
   `(-r,h,-sqrt(1-r²-h²))` en glTF. La cámara original mira desde −Z. Se implementa
   el muestreo inverso para no dejar agujeros: cada texel UV de la esfera toma su
   posición correspondiente del disco. Derecha/arriba concuerdan con las matrices
   locales y los UV/POSITION de todos los vértices reales exportados.
3. Se usan `B+=max(x,0)` y `B−=max(-x,0)` del float32 original. A cada polaridad
   se aplica umbral **visual** 0.04 y filtro gaussiano sigma 1.15 px. La suma de
   magnitudes controla concentraciones oscuras; un halo sigma 3 px mezcla ámbar
   para B+ y coral para B−. Transferencias exponenciales y ganancias son idénticas
   para todas las fechas. No se normaliza por fecha y **SI/ONNX no intervienen**.
4. La contribución HMI se desvanece en aproximadamente el último píxel del borde
   del disco. El dorso es exactamente la misma ilustración en los cinco atlas;
   nunca recibe una repetición o espejo del magnetograma. No se divide por coseno
   para inferir campo radial y no se corrige la distorsión LOS.

La proyección preserva la distribución de la matriz, pero no certifica norte/este,
latitud/longitud heliográfica ni registro de regiones entre fechas. La órbita de
perspectiva hace que el disco se vea escorzado al girar: el mapa queda anclado al
objeto, no a la cámara. Los extremos cercanos al limbo tienen menor fidelidad.

## Qué es real y qué es recreación

- Reales/procesados: las cinco matrices HMI, su signo, magnitud y distribución;
  sus referencias 2D, tiempos, SI conservado y resultados deterministas V3.1 ya
  guardados. No se ejecuta nueva inferencia ni se modifica ningún resultado.
- Derivados visuales: ajuste geométrico del disco, filtrado, umbral y asignación
  espacial sobre la esfera. No constituyen una medida científica nueva.
- Recreación: temperatura/color, granulación, corona, halos y núcleos oscuros.
  **Los núcleos no se identifican como manchas solares observadas.** No hay imagen
  de intensidad continuum para confirmarlas. HMI distingue magnetogramas y
  continuum como observables separados; referencia primaria:
  https://arxiv.org/abs/1606.02368 .
- No se identifican píxeles como NOAA 12975. La asociación de catálogo continúa
  siendo contextual; no hay máscara regional, WCS, campo 3D ni Grad-CAM.
- No hay reconstrucción de evolución física, flare observado ni pronóstico.
  Se conserva el descenso real del SI entre el 29 y el 30.

Estas distinciones aparecen en web y en el panel AR. La cara posterior está
identificada en la explicación/leyenda, sin introducir una superficie vacía.

## Control temporal y rutas

La ruta existente `/phase6/` se actualiza; `/` y `/phase5/` permanecen disponibles.
El controlador precarga y verifica 20 texturas: quince referencias y cinco atlas
solares PNG 2048×1024. Los atlas suman 21,607,068 bytes de transferencia. Sus cinco
texturas RGBA con mipmaps representan aproximadamente 53.3 MiB GPU, antes de sumar
los mapas/escena y copias del navegador. Es una estimación de almacenamiento, no
una medida de memoria móvil ni una garantía para todos los dispositivos.

La selección mantiene cámara, escala, capa y contraste. La esfera usa un fundido
gráfico suave de 260 ms entre dos atlas; fecha, SI, ONNX y mapas se actualizan
atómicamente en el punto medio. No se interpolan datos científicos. Interrumpir
el fundido lo resuelve en el estado confirmado. Movimiento reducido elimina el
fundido. Se mantienen ambos sentidos, pasos, selección directa y Play/Pause.

En esta ruta se detiene el desplazamiento ornamental del plasma para que la
actividad permanezca fija al volver a una fecha. El giro/orbitado sigue activo.
Fase 5 conserva su plasma original. WebXR/Needle Go usa el mismo objeto, material
y controlador que web; el panel AR muestra sus mismos datos y controles.
Quick Look recibe `material.map` del estado seleccionado, como instantánea baked,
sin el shader de fundido/limbo web ni timeline. Su resultado físico no se certifica.

## Verificación y evidencia

Evidencias: `prototypes/phase4-unity-needle/evidence/phase61/`.

- `asset-verification.json`: cinco entradas, hashes, ajuste geométrico, igualdad
  exacta del dorso, UV de la malla real; **1.497 archivos protegidos sin cambios**.
  Incluye backend/modelos/datos/contrato/frontend principal y originales Fase 5.
- `spatial-verification.json`: impulso sintético superior derecho cae en el frente
  correcto. Invertir polaridad modifica el color con igual magnitud; espejar la
  distribución modifica la superficie con igual magnitud global. Dorso intacto.
- **19 tests Node aprobados**, incluido rechazo de atlas/estado/fuente intercambiados
  y prueba del controlador real con reloj determinista para pausa, selección rápida,
  ambas direcciones y movimiento reducido. TypeScript y Vite aprobados. Permanecen
  avisos heredados de MaterialX externalizado y tamaño de chunks del motor.
- Navegador: cinco estados/capturas con hashes y datos correctos; reproducción
  completa en ambos sentidos y parada en extremos. Regreso 29→28→25→24 recupera
  **exactamente los mismos píxeles** de la esfera con cámara fija (diferencia 0).
  Capturas individuales `DD-desktop.png`/`DD-back.png`; composición comparativa
  `comparativa-cinco-estados.png`. Debajo se muestran PNG HMI con contraste ×4
  expresamente indicado; no son nuevas mediciones.
- Capas, zoom (distancia 2→1.7), órbita con fecha constante, liberación con caché
  cero y sin motor adjunto, seguida de Reintentar y recuperación comprobados.
- Prueba responsive **393×852 en escritorio**, cinco fechas y retroceso, botones
  de fecha 44×44 px, ancho de documento 393 px (sin desbordamiento). Panel AR DOM
  sincronizado. Esto **no** acredita iOS, interacción táctil, colocación o AR física.
- Regresión: `/phase5/` carga la ilustración original, sin timeline; `/` carga el
  cubo real y permite girarlo. Los archivos protegidos y la simulación principal
  conservan sus bytes anteriores, incluyendo los cambios previos del usuario.
- Publicación: **61 archivos** verificados por HTTPS anónimo; assets idénticos al
  build y HTML con inserción Cloudflare registrada por separado. Las cinco fechas
  de la web pública cargan `phase61-v1`, sus atlas correctos y cero errores de
  consola. Captura pública de 393×852 guardada por separado. La lectura DOM
  suplementaria pública devolvió 1×1 tras el cambio de panel y se marca inválida
  como prueba geométrica; la prueba DOM local 393×852 sí verificó el ancho.

Reproducción desde la raíz:

```sh
python3 prototypes/phase4-unity-needle/scripts/build-phase61-assets.py --check
python3 prototypes/phase4-unity-needle/scripts/verify-phase61-projection.py
npm --prefix prototypes/phase4-unity-needle/web test
npm --prefix prototypes/phase4-unity-needle/web run build
```

## Cierre móvil pendiente

No hay observación física nueva en el iPhone 15 Pro. Se requiere comprobar en
Brave/Chrome la superficie y los controles; luego Safari→Needle Go, colocar el
objeto y recorrer las cinco fechas desde el panel AR. No se reportan rendimiento,
estabilidad, cámara, seguimiento ni temperatura del teléfono como verificados.

Guía concreta: `evidence/phase61/PRUEBA-IPHONE.md`. El registro descargable de la
interfaz permite recoger dispositivo, navegador, modo XR y observaciones humanas.
Mientras falte ese resultado, **FASE 6.1: PARCIALMENTE CUMPLIDA**.
