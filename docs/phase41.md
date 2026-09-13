# FASE 4.1 — Cierre de validación Unity + Needle + WebAR

2026-09-09. **FASE 4.1: PARCIALMENTE CUMPLIDA.**

Se completó el acceso público sin autenticación, se publicó el visor con un
registro de pruebas móviles, se verificaron los QR y se repitió la interacción
web. **No se ejecutó Unity, no se exportó un GLB real y no se realizó colocación
AR ni medición en un teléfono físico.** No hay evidencia suficiente para aprobar
Unity + Needle como tecnología definitiva del gemelo.

## Resultado por requisito

| Requisito | Resultado real |
|---|---|
| Escena mínima en Unity | Proyecto y herramienta C# preparados; editor ausente. No hay `.unity` generado por el editor. |
| Exportación mediante Needle | Pendiente; el preflight termina con código 2 y el verificador GLB con código 1. |
| Unity → Needle → navegador | **No demostrado.** El modo `?scene=unity` muestra error y mantiene controles deshabilitados al faltar GLB/evidencia. |
| Needle → navegador | Probado localmente y en HTTPS público con cubo provisional TypeScript. |
| Interacción básica | Color, giro 45°, escala 1.5, reset y arrastre orbital comprobados en escritorio. Pellizco físico pendiente. |
| Android | `adb devices -l` sin dispositivos. ARCore, retícula, colocación y seguimiento físicos pendientes. |
| iPhone | CoreDevice identifica iPhone 15 Pro como `unavailable`; además advierte `No provider was found`. No es una conexión utilizable. |
| Recorrido iOS | Enlace Safari → Needle Go preparado, URL de lanzamiento HTTP 200; apertura App Clip/cámara/ARKit no verificadas físicamente. Quick Look pendiente. |
| HTTPS público sin cuenta | Configurado `access_mode=public`; verificado por solicitudes sin cookies ni Authorization y por render en navegador. |
| QR → página → 3D | QR generado y decodificado con Apple Vision; destino exacto abre el visor 3D. Escaneo con cámara de teléfono pendiente. |
| QR → página → 3D → AR | **Pendiente de prueba física.** Un QR decodificable y HTTP 200 no completan este recorrido. |
| Rendimiento móvil | Instrumentación y pasos preparados; ninguna medición física Android/iPhone. |

## URL, QR y paquetes

[Visor público](https://auralis-phase4-needle-probe.alejandro-cornejog4.chatgpt.site/).
La portada continúa identificando el cubo como provisional; no se presenta como
exportación Unity. [Modo Unity](https://auralis-phase4-needle-probe.alejandro-cornejog4.chatgpt.site/?scene=unity)
exige el archivo real y su evidencia. No tiene escena de sustitución.

Carpeta: `prototypes/phase4-unity-needle/evidence/phase41/`:

- `qr-public.png`: página 3D pública.
- `qr-ios-needle-go.png`: enlace explícito Needle Go con esa página como destino.
- `qr-decoded.txt`: decodificación independiente de ambos PNG con Apple Vision.
- `phase41-web-build.zip`: build publicado completo, **escena provisional**.
- `phase41-unity-source-kit.zip`: proyecto/editor/scripts/fuente web para producir
  el GLB real cuando Unity esté instalado y activado; no contiene un GLB ficticio.
- `PRUEBA-HUMANA.md`: pasos mínimos, instalación/exportación, Android, iPhone y
  registro; no depende de conocer la conversación.

Publicación 4, fuente `0b7869bea536ce5267d84ba4070975fdd8b7aa22`, estado `succeeded`.
Solo se hizo commit/push en el repositorio aislado `web/`, rama `main`.
El repositorio padre, frontend, backend y simulación solar no se refactorizaron.

## Pruebas realizadas y evidencia

- `npm test`: 8/8. Incluye decisiones de compatibilidad y cadencia con pausas o
  ausencia total de frames; ningún test simula una aprobación física.
- `npm run build`: TypeScript y Vite correctos. Advertencias previas de chunks
  grandes y MaterialX/Node siguen presentes; MaterialX no fue probado.
- `scripts/prepare-phase41.sh`: detiene la preparación al faltar Unity. Una vez
  instalado, llama al editor real, verifica GLB y solo entonces construye la web.
- `scripts/verify-unity-export.py`: detecta ausencia de GLB/evidencia; no aprueba
  el recorrido. `unity-preflight.txt` conserva el bloqueo.
- `?scene=unity`: error visible y controles deshabilitados. Antes de montar el
  visor ahora comprueba cabecera GLB, bytes, SHA-256 y versión 5.1.12 contra la
  evidencia. Esa comprobación tampoco certifica por sí sola la autoría o paridad.
- Navegador Chromium de Codex: cambio de color, giro `0.7853981634` rad, escala
  1.5, reset a escala 1/giro 0/color inicial. Arrastre público cambia cámara de
  `[0.5, 0.4, 0.7]` a `[-2.778681, -0.958071, -2.746888]`; capturas y JSON guardados.
- Formulario de observaciones y acción de descarga del diagnóstico ejercitados
  en escritorio. La entrega/descarga dentro del App Clip requiere prueba física;
  el protocolo prevé captura/transcripción si su interfaz impide descargar.
- QR público e iOS decodificados correctamente. La primera ejecución Apple Vision
  restringida falló al cargar ANE; la ejecución con acceso al framework terminó
  correctamente. No equivale al escaneo físico con cámara.
- `scripts/audit-phase41-public.py`: 24 respuestas HTTP 200 sin credenciales.
  Los 23 recursos tienen SHA-256 idéntico al build; el HTML de la aplicación es
  idéntico con 938 bytes adicionales de comprobación Cloudflare. Se conserva el
  hash bruto distinto; no se afirma igualdad binaria del HTML servido.
- La primera auditoría capturó transitoriamente HTML en lugar de un módulo JS
  recién publicado. Una petición posterior y la auditoría completa obtuvieron
  el JS correcto. Ambos informes se conservan. No se ocultó como prueba aprobada.
- El destino público de Needle Go respondió HTTP 200. Solo comprueba alcance HTTP,
  no que iOS muestre la tarjeta, arranque el App Clip o coloque el objeto.

## Rendimiento observado

**Escritorio, no móvil:** muestra explícita de 30,0011 s, 1.786 callbacks de
render, **59,5312 renders/s**, mediana de intervalo 16,7 ms, p95 17,4 ms,
0 intervalos mayores de 50 ms. Cubo: 12 triángulos, 1 llamada de dibujo,
DPR limitado a 1,5. `desktop-render-sample.json` conserva el resultado.

Se mide cadencia desde `Needle post_render_callbacks`, separada del
`requestAnimationFrame` general de la página. Se distingue 3D/XR y se registran
interrupciones por cambio de sesión, modo o visibilidad. Tras colocación AR se
inicia una muestra de 30 s; ese disparo XR aún no se probó en hardware real.
No es tiempo GPU, estabilidad de tracking ni garantía para una escena solar.

Build: 11.834.457 bytes sin comprimir, 24 archivos; JS principal aproximadamente
3,06 MB y 0,85 MB gzip. Incluye módulos diferidos; no representa tráfico inicial.
Los tiempos de inicialización en escritorio con caché no son carga móvil fría.
El protocolo exige tres aperturas frías, muestra de 30 s y observación de 5 min
por teléfono, con red/caché y fuente declaradas.

## Limitaciones y criterio de decisión

El obstáculo Unity es real: búsqueda Spotlight y ubicaciones habituales sin
editor; sin instalación/licencia utilizable no se puede crear ni exportar una
escena mediante Unity. Se solicitó al usuario instalar/activar el editor o
proporcionar su ruta. No se fabricaron artefactos ni resultados de exportación.

Android necesita dispositivo compatible con ARCore, Chrome y Google Play
Services for AR; emular una pantalla no valida colocación. [Requisitos Google](https://developers.google.com/ar/develop/webxr/requirements).

iPhone usa Safari → Needle Go/ARKit. El proveedor documenta URL HTTPS pública,
limitaciones de anclas/deriva y captura del fondo de cámara. El flag `useXRAnchor`
no demuestra anclas funcionales en iOS. Quick Look es una ruta USDZ reducida que
no conserva la UI/lógica TypeScript de esta prueba. [Documentación Needle Go](https://engine.needle.tools/docs/how-to-guides/xr/ios-webxr-app-clip.html).

**Recomendación de adopción: no aprobar Unity + Needle como tecnología definitiva
con la evidencia disponible; conservar la simulación Three.js actual.** La
validación web es positiva, pero no resuelve el requisito de exportación Unity
ni el de funcionamiento/rendimiento móvil. Esto es una decisión de aceptación
basada en evidencia faltante, no una demostración de incapacidad de Needle.
La decisión técnica definitiva sobre viabilidad móvil sigue pendiente de esas
pruebas; afirmar ahora un sí definitivo sería inventar resultados.

Para reconsiderar la adopción deben existir: escena/GLB genuinos y log/hash,
paridad visual editor/web, mismo build público con GLB, QR físico, colocación,
ajuste/salida/reentrada y perfil básico documentados en Android e iPhone. Si no
se acepta depender de Needle Go para iOS, esta ruta no satisface ese requisito.
No se construyó el Sol, el gemelo temporal ni ninguna fase posterior.
