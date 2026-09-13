# Fase 5 — Primer estado solar en Unity + Needle

> Informe de la entrega inicial. El pulido posterior, solicitado por el usuario,
> completa la esfera ilustrativa y sustituye el rótulo del reverso. Véase
> [pulido visual solar](solar-visual-polish.md) para el estado vigente.

Fecha: 2026-09-09. **FASE 5: PARCIALMENTE CUMPLIDA**.
La escena real, los datos y el módulo web están implementados, publicados y
verificados en escritorio. Con autorización explícita del usuario se realizó
commit/push únicamente en el repositorio aislado del sitio. La validación física
del iPhone sigue pendiente.

## Resultado y acceso

- URL pública activa, **versión 7**:
  https://auralis-phase4-needle-probe.alejandro-cornejog4.chatgpt.site/phase5/
- Se mantiene el cubo de Fase 4.2 en `/`; no cambia Agent Lab ni la simulación Three.js.
- QR de destino y QR Needle Go: `evidence/phase5/qr-phase5-public.png` y
  `qr-phase5-ios.png`, dentro del prototipo. Decodificación por software verificada;
  el escaneo físico permanece pendiente.
- Guía para el teléfono indicado por el usuario: iPhone 15 Pro, Brave/Chrome,
  con Safari → Needle Go para el recorrido AR. Versiones y resultados físicos
  aún sin registrar: `evidence/phase5/PRUEBA-IPHONE.md` y `physical-validation.json`.

Commit publicado del repositorio `web`:
`b7c1c6ea1b02c549a97f53e9bdd31892df295094`. Despliegue completado a las
17:54:39 UTC del 9-sep-2026. Acceso HTTP anónimo comprobado: 37 archivos correctos;
los recursos binarios coinciden byte a byte. El HTML conserva el contenido del
build y la plataforma añade su script de Cloudflare, identificado por la auditoría.
El navegador público carga el GLB verificado y cambia a B− sin errores,
manteniendo identidad, fecha y valores. Evidencia: `publication.json`,
`public-http-verification.json`, `public-browser-verification.json`,
`public-solar.png` y `public-bminus.png`.

## Observación, estimación e ilustración

El adaptador lee exclusivamente el primer estado `hmi-2022-03-24` del contrato
congelado `auralis-back/reports/phase3_temporal_model/noaa12975.sequence.v1.json`.
La interfaz no contiene copias manuales de SI, predicción, medias, identidad de
archivo ni protocolo. Los obtiene del subconjunto público generado `state.json`.

| Naturaleza | Presentación | Límite |
|---|---|---|
| Observación procesada | Magnetograma firmado, blanco positivo/negro negativo/gris cero | Matriz local de disco completo, 512², sin WCS ni orientación solar certificada |
| Derivado observacional | B+ y magnitud B−, cada uno negro 0 → blanco 1 | `max(x,0)` y `max(-x,0)`, adimensionales; no son flujo magnético ni campo vectorial |
| Etiqueta observacional conservada | SI original (%) | Guardado en contrato; no se recalcula desde la matriz reducida/recortada en amplitud |
| Estimación | Coronium V3.1, ONNX CPU eval batch 1, cuatro hilos, sin ruido ni MC | Estima el SI de ese magnetograma; estado de entrenamiento, sin validación temporal independiente |
| Ilustración | Fotosfera, granulación multiescala, brillo y borde cálido/corona tenue | Procedural, no fotometría observada, manchas reconstruidas ni evolución solar |
| Sin datos | Hemisferio posterior gris con rótulo integrado y reverso del plano | No se inventa una observación de la cara posterior |

Registro: 24-mar-2022, 00:01:30 TAI / 00:00:53 UTC. UTC procede del contrato, no
de inferir la escala de la fecha CSV. SI conservado 1,679617166519165%; ONNX
1,4705196619033813%; el panel redondea ambos a seis decimales y muestra diferencia
en puntos porcentuales. El valor de API a cuatro decimales permanece en el contrato.

**No hay proyección de datos HMI sobre la esfera.** Las tres capas científicas
son planos Unity con la matriz completa, sin máscara ni recorte espacial. La
referencia HTML 2D se conserva, incluyendo cuando el motor falla. No se estira
el disco sobre un globo. La asociación NOAA 12975/HARP 8088 es de catálogo, sin
segmentación o posición de píxeles. Grad-CAM permanece no disponible. Las
métricas MC Dropout no se usan para caracterizar la predicción determinista.

## Cadena real y archivos

Todo reside en `prototypes/phase4-unity-needle/`, salvo este informe y AGENTS.md:

- `unity/Assets/Editor/Phase5Solar.cs`: autoría en editor y exportación real.
- `unity/Assets/Scenes/Phase5Solar.unity`: escena Unity persistida.
- `unity/Assets/Phase5/`: meshes, materiales, imágenes derivadas y metadatos Unity.
- `unity/Assets/Editor/Auralis.Phase4.Editor.asmdef`: añade únicamente referencia
  al ensamblado UnityGLTFScripts ya instalado para el callback de texturas.
- `unity/ProjectSettings/NeedleExporterSceneData.asset`: Needle registra la nueva
  escena; los bytes de la configuración anterior se conservan al quitar esa adición.
- `scripts/build-phase5-assets.py`: adaptador offline y comprobación `--check`.
- `scripts/verify-phase5.py`: verificación del GLB y archivos protegidos.
- `scripts/prepare-phase5.sh`: generación → Unity → comprobaciones → tests/build.
- `scripts/audit-phase5-public.py`: comprobación HTTP anónima de la publicación.
- `web/phase5/index.html`, `web/src/phase5/{main.ts,contract.mjs,style.css}`:
  interfaz, carga verificada, interacción y ciclo de vida del módulo aislado.
- `web/vite.config.ts`: añade entrada `/phase5/`, conservando la entrada original.
- `web/public/phase5/`: GLB, evidencia de exportación, subconjunto JSON y PNG.
- `web/tests/phase5.test.mjs`: casos positivos y negativos del consumo científico.
- `evidence/phase5/`: capturas, verificaciones, logs locales, build empaquetado,
  QR, guía y registro físico pendiente.

`evidence/phase5/phase5-source-additions.zip` y `source-manifest.json` contienen
las adiciones de fuente/recursos al prototipo existente; no son un proyecto Unity
independiente. El build publicable está en `phase5-site.tar.gz`.

Se reutilizan **Unity 6000.3.17f1 ARM64**, **Needle 5.1.12**, Vite, TypeScript,
Three del runtime y QRCode ya instalados. No se cambian versiones ni lockfiles.
El C# es tooling del editor; no se presupone su ejecución en el navegador.
Geometría, UV, texturas, materiales unlit, cámara, OrbitControls y raíz de
colocación vienen de la escena exportada. TypeScript conecta controles y los
componentes WebXR/USDZ del runtime; no crea una esfera sustituta.

La primera exportación produjo JPEG en los mapas: se rechazó para la entrega.
Un callback público `GLTFExportPluginContext.BeforeTextureExport`, acotado a
`Assets/Phase5/Data/`, exige PNG. La lista de plugins se restaura tras exportar;
no se parchean paquetes ni se altera configuración global persistente.
Las imágenes finales incrustadas coinciden exactamente con sus referencias.

## Procedencia y parámetros

`state.json` conserva hash del contrato, hashes de matriz/código de entrada,
checkpoint/ONNX/manifiesto y fuentes del SI/predicción, además de receta, escala,
dimensiones, orientación y hash del generador. No se publican esos binarios
originales. La fuente se comprueba contra los hashes congelados antes de derivar.

Derivación: módulo compartido `prepare_model_input`, sin cambiarlo. PNG RGBA de
512² con alfa 255; intensidad firmada `round(255*(x+1)/2)` y canales
`round(255*channel)`. Error máximo de cuantización: 1/255 firmado y 0,5/255 en
canales. Fila cero arriba, ninguna rotación, transposición ni espejo. Referencia
HTML con interpolación nearest; plano 3D con filtrado/mipmaps para evitar aliasing.

La ilustración se hornea en Unity a 1024²: granulación celular de escala 160,
semillas 53/97, modulación Perlin de escalas 13/390, oscurecimiento visual hacia
el limbo y paleta cálida. Corona RGBA 256², alfa máximo 0,15, anillo radial suave;
sin bloom ni shaders personalizados de posprocesado. Parámetros completos en
`Phase5Solar.cs`; su hash y el de la textura quedan en `export-evidence.json`.
Malla de dos hemisferios, 48 anillos × 128 segmentos por hemisferio, radio 0,42 m
de demostración. No son dimensiones inferidas de la observación.

## Verificación

- Exportación real final con código 0, generador incrustado de Needle, cabecera,
  longitud y SHA-256 coincidentes; detalles en `verification.json` y log final
  `unity-export-final-scene.log`. GLB autocontenido, sin URI de texturas externas.
  GLB final: 2.482.256 bytes, SHA-256
  `a0473d35c351e5ec15c75c284ae2ea34e6ed103a597449935e7419189d47f619`.
- Igualdad exacta de todos los píxeles RGBA de magnetograma/B+/B− entre PNG y GLB.
  Verificación de las UV respecto a la cámara exportada, sin inversión de signo
  ni espejo horizontal/vertical. La afirmación es relativa a la matriz, no a un
  norte solar que el contrato no certifica.
- Medias de ambos canales iguales al contrato en float64; canales disjuntos y
  reconstrucción exacta `B+ − |B−| = x`. Testigos asimétricos guardados.
- Doce tests Node pasan, incluyendo protocolo MC incorrecto, fecha/estado
  incorrectos, WCS inventado, canal negativo, URL ajena, GLB alterado y SI cambiado.
  TypeScript y build Vite pasan. Se conservan las advertencias del runtime sobre
  chunks grandes y MaterialX; no se añaden dependencias para resolverlas.
- Arrastre, escala, giro opcional, cambio de capas, restablecer, liberación y
  recarga comprobados. Un GLB retirado temporalmente del build produjo error
  explícito, controles desactivados y referencia 2D de 512²/SI todavía disponibles;
  al restaurarlo, Reintentar recuperó la escena. Ver `missing-glb.json`.
- Vista adaptable comprobada a 393 × 852 CSS px: ancho del documento 393 px,
  referencia cargada y cuatro controles activos. Es una prueba de disposición
  en escritorio, no una ejecución en el iPhone ni emulación de su GPU.
- 1.959 archivos de la línea base conservan sus hashes: datos, artefactos/modelos,
  contratos, resultados, código backend, frontend actual y escena GLB Fase4.
  La única excepción de configuración es la adición exacta de la nueva escena al
  registro de Needle. La comparación respeta los cambios previos del usuario.
- Auditoría de salida: sin `.npy`, `.pth`, `.onnx`, credenciales ni rutas privadas
  absolutas. `build-manifest.json` identifica los archivos publicables. Los logs
  del editor y la línea base permanecen locales, fuera de `web/public` y `dist`.

## Interacción, AR y límites pendientes

El arrastre orbita, el zoom se limita a distancias 1,15–3,8 m de demostración,
la escala del objeto a 0,4–1,5× y el giro automático es optativo. El estado y la
fecha no cambian. El reset de vista es inmediato para no competir con el zoom.
Al liberar se eliminan el contexto/renderer, callbacks, listener de colocación,
timers y URL blob del GLB; las URL de referencia duran hasta salir de la página.

El panel AR es un hijo `.ar` de `needle-engine`, usando el overlay soportado por
Needle 5.1.12 y su reparentado en Needle Go. Incluye fecha, SI/ONNX, referencia 2D,
leyenda, capas y escala. Evita propagar selecciones del panel a colocación XR.
Hay retícula, ajuste de colocación y salida/reentrada del runtime. Su operación
física y la fidelidad de estos materiales en Needle Go/Quick Look siguen pendientes.

Muestra final en el Mac: 30,001 s, 1.788 callbacks, **59,598 renders/s**, mediana
16,7 ms, p95 17,4 ms, ningún intervalo >50 ms. Registro en
`desktop-render-sample.json`, modo `web3d` y capa solar, cámara quieta.
Son cadencia de callbacks de render de Needle, no tiempo GPU, tracking AR ni
latencia de inferencia. Una carga con caché no es benchmark frío. Los modos 3D
y XR se registran separados e interrumpen la muestra al cambiar de modo/visibilidad.
El tamaño completo del build incluye recursos diferidos del motor; no equivale
a tráfico inicial. No hay cifras ni aprobación de rendimiento móvil.

Los QR público y Needle Go se decodificaron por software con OpenCV; ver
`qr-verification.json`. Esto no acredita escaneo físico ni colocación AR.

El usuario debe probar su iPhone y registrar los resultados. No se declara
aprobado Android, otro iPhone, Brave, Chrome, Safari ni Needle Go por esta prueba
de escritorio. Referencias oficiales consultadas:
[materiales/exportación](https://engine.needle.tools/docs/explanation/exporting-to-gltf.html),
[Needle Go e iOS](https://engine.needle.tools/docs/how-to-guides/xr/ios-webxr-app-clip.html).

## Reproducir

Desde el prototipo, con el editor cerrado: `sh scripts/prepare-phase5.sh`.
La orden reabre la escena existente; `Phase5Solar.RebuildAndExport` es una
operación explícita para reconstruir solo la escena generada de esta fase.
Para verificar sin reexportar: `python3 scripts/build-phase5-assets.py --check`
y `python3 scripts/verify-phase5.py`; desde `web/`, `npm test` y `npm run build`.
Para comprobar el sitio ya publicado: `python3 scripts/audit-phase5-public.py`.

No hay commits/push del repositorio padre. El commit/push del sitio y su publicación
se realizaron con autorización explícita del usuario. No se inicia ninguna otra fase.

**FASE 5: PARCIALMENTE CUMPLIDA.** Falta la prueba humana en iPhone 15 Pro:
Brave/Chrome en 3D y Safari → Needle Go en AR, verificando materiales, colocación,
escala, panel, salida/reentrada y rendimiento. Versiones y resultado permanecen
sin registrar; no hay dispositivos móviles aprobados.
