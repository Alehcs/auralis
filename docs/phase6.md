# Fase 6 — Gemelo temporal NOAA 12975

**Estado: PARCIALMENTE CUMPLIDA.** Implementación web y verificaciones locales
completadas y publicadas como **versión 9** el 9 de septiembre de 2026, 21:43 UTC.
La prueba física del iPhone sigue pendiente.

Commit del sitio: `f985d673d9eaebce7403eb6716781178abdf4ac1`. Sin commit del padre.

URL: https://auralis-phase4-needle-probe.alejandro-cornejog4.chatgpt.site/phase6/

## Alcance y arquitectura

Se amplía el módulo aislado, conservando `/phase5/` y el cubo real en `/`.
No se toca la simulación Three.js de Auralis, Agent Lab, backend, datos originales,
modelos, métricas ni dependencias. El repositorio padre no recibe commits.

Se reutiliza byte a byte el GLB real `Phase5Solar.glb` creado por Unity 6000.3.17f1
con Needle 5.1.12. Fase 6 carga esa escena y asigna mapas a sus planos exportados.
No se crea una esfera TypeScript alternativa ni se declara una nueva exportación
Unity: la autoría/exportación y su evidencia son las de Fase 5.

SHA-256 GLB: `6694a42dd2f0b322c7a65dc9d55d17eb1fe653ab0ec85884ee68b20cb14999b5`.
Tamaño: 6.206.672 bytes. Geometría, textura solar y corona conservadas.

## Fuente temporal y valores

Única fuente: `auralis-back/reports/phase3_temporal_model/noaa12975.sequence.v1.json`.
SHA-256: `0926747125d84a10a20611cf523c42293aa7dd2125567c67ed6e9554bb337ad6`.
La tabla se genera desde el subconjunto derivado de ese contrato; la interfaz
lee los valores completos y solo redondea su presentación a seis decimales.

| Registro UTC (00:00:53) | SI conservado % | ONNX determinista % | Estado |
| --- | ---: | ---: | --- |
| 2022-03-24 | 1.679617 | 1.470520 | `hmi-2022-03-24` |
| 2022-03-25 | 1.717091 | 1.477280 | `hmi-2022-03-25` |
| 2022-03-28 | 1.947987 | 1.656259 | `hmi-2022-03-28` |
| 2022-03-29 | 2.057672 | 1.683445 | `hmi-2022-03-29` |
| 2022-03-30 | 2.050173 | 1.712676 | `hmi-2022-03-30` |

Los cinco archivos corresponden a `hmi.m_45s.2022.03.DD_00_01_30_TAI.magnetogram_processed.npy`.
Se conservan identidad, escala TAI y conversión UTC del contrato. El SI del último
estado **desciende**; no se fuerza crecimiento y no se modifica ONNX para acompañarlo.
El 28 pertenece a validación utilizada en selección, los otros cuatro a entrenamiento.
La secuencia no es una evaluación temporal independiente. El protocolo de estimación
es `deterministic_onnx_cpu_eval_batch1_threads4_no_noise_no_mc`, distinto de las
métricas MC Dropout; no se ejecuta inferencia nueva.

## Navegación y transición

- Selección directa de las cinco fechas, Anterior/Siguiente, Reproducir/Pausar
  y selector Adelante/Atrás. Parada automática en ambos extremos. Reproducir desde
  un extremo reinicia desde el opuesto para volver a recorrerlo.
- Posiciones de la timeline proporcionales a los tiempos UTC: 0, 1/6, 4/6, 5/6, 1.
  El salto 25→28 queda visible. La reproducción espera dos segundos por estado:
  es una cadencia de presentación, no una reproducción del tiempo físico.
- Fundido de luminosidad de 260 ms, con cambio atómico de observación en su punto
  medio. No se mezclan mediciones, SI, predicciones ni campos entre fechas. Con
  movimiento reducido, la selección es inmediata. No hay estados intermedios.
- La selección conserva cámara, zoom, capa, contraste y escala. La rotación y el
  plasma ilustrativos no cambian fecha. Selección manual, cambio de dirección,
  documento oculto, entrada/salida XR, Quick Look y liberación pausan la secuencia.
- Las referencias 2D web/AR y los tres materiales cambian junto con el panel
  científico. El panel AR usa el mismo controlador; no mantiene otra timeline.

## Datos observados, estimados e ilustrativos

Los mapas son referencias 2D del **disco completo** HMI procesado; NOAA 12975 es
una asociación contextual, sin máscara regional, WCS o campo tridimensional.
La esfera completa sigue siendo una recreación visual 360°, sin atribuir su cara
posterior, plasma o filamentos a HMI. No se estira el disco sobre una textura global.
Grad-CAM no está disponible. No se añaden llamaradas ni predicción de eventos.

El adaptador offline lee los cinco `.npy` existentes y el contrato, verifica hashes
y calcula únicamente PNG de presentación. Usa la función compartida B+/B− sin
modificarla. Conserva filas/columnas, sin espejo ni recorte, y comprueba cada píxel:

- Firmado: `round((x + 1) * 127.5)`: negativo negro, cero gris, positivo blanco.
- B+: `round(max(x, 0) * 255)`; B−: `round(max(-x, 0) * 255)`.
- Canales no negativos, dimensión normalizada [0,1]; el campo firmado usa [-1,1].
  Ambos canales reconstruyen exactamente el float32 original antes de cuantizar.
  Medias float64 cotejadas con el contrato. Los PNG tienen cuantización de 8 bits;
  no se usan para recalcular resultados científicos.
- Se conserva contraste de presentación 1×/4×/12× con saturación y leyenda explícitas.
  La referencia original está disponible a 1×; no cambian valores subyacentes.

## Archivos de esta fase

Bajo `prototypes/phase4-unity-needle/`:

- Nuevo adaptador `scripts/build-phase6-assets.py`.
- Nuevos `web/phase6/index.html`, `web/src/phase6/sequence.mjs`, `temporal.ts`,
  `timeline.css`, `web/tests/phase6.test.mjs` y `web/PHASE6.md`.
- Nuevos `web/public/phase6/sequence.json`, `sequence-evidence.json` y quince PNG
  en `assets/hmi-2022-03-{24,25,28,29,30}/`.
- Ajustes mínimos en `web/src/phase5/main.ts`, `visual-materials.ts` y
  `web/vite.config.ts` para activar el controlador solo en la ruta Fase 6.
- `scripts/audit-phase5-public.py` admite todas las rutas index y `--route`,
  manteniendo su comportamiento predeterminado para Fase 5.
- Evidencias en `evidence/phase6/`: línea base, cotejo de activos, registros de
  navegador, capturas, publicación y guía física.

Fuera del prototipo: este informe y la nueva sección contextual de `AGENTS.md`.

## Verificación realizada

- Adaptador en modo `--check`: cinco fuentes y quince PNG exactos, manifiesto y
  evidencia reproducibles; **1.497 archivos protegidos sin cambios** frente a la
  línea base de inicio. Incluye backend, modelos, datos, contrato, frontend principal
  y recursos congelados de Fase 5. Los cambios anteriores del usuario se preservan.
- **16 tests Node aprobados**, TypeScript y build Vite aprobados. Se conservan las
  advertencias heredadas de MaterialX externalizado y chunks grandes del motor.
- Navegador integrado de escritorio: cinco fechas y quince mapas, SI/predicción,
  origen de cada textura, `flipY=false`, sincronización web/AR DOM, avance/retroceso,
  reproducción en ambos sentidos, pausa, selección rápida, órbita y zoom.
  Se corrigió un fallo del selector de dirección detectado durante esta prueba.
- Dos recorridos por las quince combinaciones fecha/capa: caché fija de quince
  mapas; tras calentamiento, 17 texturas GPU y dos geometrías, sin crecimiento
  en el segundo recorrido. Registros acotados a 500 eventos y 120 muestras.
- Liberar: cero motores adjuntos, caché vacía y reproducción cancelada; referencia
  2D conservada a 512². Reintentar vuelve a cargar el visor. Esto es evidencia de
  un ensayo acotado, no una garantía de ausencia de fugas en todos los navegadores.
- Prueba negativa local: se alteró temporalmente una copia derivada B+ del 28.
  El visor rechazó el hash con error explícito y vació la caché. Se restauró
  exactamente el PNG, se verificó su hash y Reintentar recuperó la carga.
- Regresión: `/phase5/` mantiene su estado único y capas; `/` carga su GLB real y
  permite girar el cubo. No se prueba ni modifica el frontend principal.
- Disposición responsive a 393×852 CSS px en escritorio, sin desbordamiento
  horizontal. No equivale a una prueba humana, de iOS, táctil o de AR.
- Muestra de escritorio, Sol y plasma activos: 1.784 callbacks en 30,0006 s,
  **59,465 renders/s**, mediana 16,7 ms, p95 17,5 ms, cero intervalos >50 ms.
  Cadencia de callbacks Needle, no tiempo GPU ni rendimiento del teléfono.

Publicación: **54 archivos** servidos por HTTPS anónimo coinciden con el build;
solo se admite la inserción Cloudflare identificada en HTML. Los cinco estados
fueron seleccionados en el navegador público con SI/predicción correctos, hashes
verificados y cero errores de consola. URL/QR y enlace Needle Go apuntan a `/phase6/`.
El PNG del QR se decodificó correctamente con Apple Vision en CPU; no se ha
escaneado físicamente. Evidencia: `qr-verification.json`.

La caché precarga quince PNG, por lo que la navegación espera a verificarlos todos;
se añade transferencia frente a Fase 5. No se acumulan texturas al seleccionar.
Needle conserva su carga y módulos actuales; no se hace una optimización general.

## Prueba móvil pendiente

Teléfono comunicado por el usuario: **iPhone 15 Pro**, Brave/Google Chrome.
Versiones iOS/navegador, colocación AR, materiales AR, estabilidad, temperatura y
rendimiento móvil: **no probados**. No se certifica ningún otro dispositivo.

1. Abrir `/phase6/` en Brave y Chrome. Probar fechas, ambas direcciones, pausa,
   tres mapas, giro, zoom y restablecer; comprobar el descenso de SI 29→30.
2. Abrir la misma URL en Safari y usar Needle Go para entrar en AR. Colocar en
   una superficie, ajustar escala y usar las fechas/capas del panel AR. Recorrer
   alrededor, salir y volver a entrar.
3. Quick Look se prueba por separado: es una instantánea del estado elegido;
   no ofrece timeline ni los shaders/controles web. No cuenta como AR temporal.
4. En «Prueba física y registro de este dispositivo», registrar versiones, red,
   resultado y observaciones; medir 30 s en web y AR y descargar el JSON.

Guía separada: `evidence/phase6/PRUEBA-IPHONE.md`. No se inicia otra fase.
