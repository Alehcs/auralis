# FASE 4 — Prueba técnica Unity + Needle Engine + WebAR

Ejecución inicial: 2026-09-06. Cierre de la revisión web: 2026-09-09. **FASE 4: PARCIALMENTE CUMPLIDA.**

Se implementó y ejecutó un runtime Needle con un cubo mínimo, interacción 3D,
comprobación de WebXR, configuración de colocación AR, alternativa Quick Look,
QR y diagnóstico. Se preparó el proyecto/editor de Unity y su exportación, pero
**Unity no se ejecutó y no existe un GLB genuino exportado por Unity**. No hay
resultados físicos Android/iOS. No se construyó el Sol ni la timeline y no se
modificaron el frontend, el backend o la simulación Three.js existentes.

## Arquitectura utilizada

```text
prototypes/phase4-unity-needle/
  unity/ — proyecto de autoría propuesto, Unity 6.3 LTS
    Phase4Probe.cs → escena/material/cámara/luz/cubo/raíz AR
    Needle exporter 5.1.12 → public/unity/Phase4Probe.glb
                          → export-evidence.json (versión, SHA-256)
  web/ — Vite + TypeScript + Needle Engine 5.1.12
    /                 → cubo provisional generado en TypeScript
    /?scene=unity     → exige GLB real; error si falta, sin sustitución
    Needle / three r169 → WebGL2 + controles 3D
                       → WebXR AR (Android compatible)
                       → Needle Go / ARKit (iOS App Clip)
                       → USDZ / Quick Look (alternativa limitada)
  evidence/ — mediciones, captura, versiones y protocolo físico
```

La exportación usa `Needle.Engine.Gltf.Export.AsGlb` y su `ObjectExportContext`
con ruta de salida explícita. La web consume el GLB con `<needle-engine>`.
No se usa el build Unity WebGL/WASM ni se compila C# como lógica del navegador.
La compatibilidad editorial sigue pendiente: consultar las API no sustituye
compilar el proyecto ni comprobar fidelidad visual.

**Responsabilidades:** Unity define geometría, escala métrica, pivote sobre el
suelo, material, cámara, iluminación y componentes serializados como
`WebARSessionRoot` y `OrbitControls`. El C# incluido es exclusivamente herramienta
de editor. TypeScript añade la UI, cambios de estado, diagnóstico, QR y `WebXR`;
configura retícula, colocación por toque, ajuste por gestos y anclas donde haya
soporte. La futura lectura del contrato temporal y API correspondería a TS;
no se implementó aquí. El ML permanece en FastAPI/ONNX.

## Archivos y ejecución

Carpeta aislada: `prototypes/phase4-unity-needle/`.

| Archivo/grupo | Función |
|---|---|
| `README.md` | Instrucciones completas |
| `unity/Assets/Editor/Phase4Probe.cs` | Crear escena y exportarla con Needle; sin ejecutar |
| `unity/Packages/manifest.json` | Registro oficial y exportador 5.1.12 |
| `unity/ProjectSettings/ProjectVersion.txt` | Editor objetivo 6000.3.0f1, no versión probada |
| `scripts/run-unity.sh` | Ejecución por lotes con editor/licencia ya instalados |
| `scripts/verify-unity-export.py` | GLB, nodos, referencias y hash; falla si no hay exportación |
| `web/index.html`, `src/style.css` | Vista 3D y controles adaptables |
| `web/src/main.ts` | Runtime Needle, AR, USDZ, QR y diagnóstico |
| `web/src/capabilities.mjs` | Compatibilidad y condiciones de URL |
| `web/tests/capabilities.test.mjs` | Seis pruebas de degradación/soporte |
| `web/package.json`, `package-lock.json` | Dependencias fijadas |
| `web/tsconfig.json`, `vite.config.ts` | Compilación aislada, puertos 5184/4184 |
| `web/.openai/hosting.json` | Alojamiento estático del prototipo |
| `evidence/device-matrix.json` | Resultados y pruebas pendientes |
| `evidence/browser-local.png`, `orbit-before.png`, `orbit-after.png` | Capturas del visor y arrastre |
| `evidence/qr-private-url.png` | QR de la URL HTTPS; conserva el requisito de sesión |
| `evidence/build-artifacts.json` | Tamaños y hashes del build |
| `evidence/needle-exporter-package.json` | Metadatos oficiales consultados |
| `evidence/physical-test-protocol.md` | Protocolo de aceptación móvil |
| `evidence/deployment.json` | Resultado del alojamiento, cuando termina |

El alojamiento usa un repositorio propio dentro de `web/`, rama `main`, para
no subir cambios ajenos de Auralis. No se creó un worktree ni se hicieron commits
en el repositorio padre. Las carpetas generadas se excluyen con `.gitignore`.

```sh
cd /Users/alejandro/Documents/ProyectosAG/Auralis/prototypes/phase4-unity-needle/web
npm ci
npm run dev
# http://localhost:5184/
npm test
npm run build
npm run preview
# http://localhost:4184/
```

Para completar Unity: instalar/activar Unity 6.3 LTS, abrir `unity/`, esperar
importación del paquete, ejecutar los dos menús `Auralis > Phase 4` descritos en
el README y abrir `/?scene=unity`. Guardar log, hash y comparación visual de
editor/web. Después reconstruir y desplegar. El `.unity`, material y GLB se
crearán en ese paso: no se entregan como si ya hubiesen sido producidos.

## Resultados verificables

| Requisito | Resultado de esta ejecución |
|---|---|
| Autoría Unity | Código/proyecto preparados; editor ausente en ubicación estándar y búsqueda Spotlight |
| Unity → Needle → Web | **No demostrado**; no compilación C#, exportación ni comparación visual |
| Needle → navegador | **Demostrado** con escena TypeScript provisional |
| Interacción 3D | Color, giro 45°, escala, reset y arrastre orbital probados; zoom/pellizco sin verificación física |
| Sin WebAR | `immersive-ar=false`; controles 3D disponibles en navegador del Mac |
| Colocación en entorno | Configurada, **no probada físicamente**; contador real de colocación = 0 |
| Android | `adb devices` sin dispositivos; no prueba física |
| iPhone | iPhone 15 Pro conocido por CoreDevice, estado `unavailable`; no prueba física |
| Pantalla estrecha | Disposición a 390 px inspeccionada; esto no emula iOS/ARKit |
| TypeScript/build | Correctos; seis pruebas Node aprobadas |
| Exportación faltante | Error visible en modo Unity, controles deshabilitados, sin cubo sustituto |
| WebMCP opcional | Escala 1.5 aceptada; valor 3 rechazado sin cambiar la escala |
| QR | Generado con la URL actual; localidad y requisito de URL pública indicados |

La revisión del 9 de septiembre corrigió la cámara provisional: además de habilitar
`camera-controls`, requiere un componente `Camera` de Needle activo para que
`OrbitControls` reciba entrada. El gesto registrado cambió la posición desde
`[0.5, 0.4, 0.7]` a `[-1.341, -0.180, 1.223]`. Se conservan capturas antes/después
y los valores en `device-matrix.json`; no es evidencia de seguimiento AR.

## Rendimiento básico y límites de la medición

En macOS 26.6.2 ARM64, navegador Chromium integrado de Codex: **12 triángulos,
1 llamada de dibujo y DPR máximo 1.5**. Una navegación local con caché indicó
166 ms hasta inicialización del runtime; ventana móvil de 600 intervalos
`requestAnimationFrame`, mediana 8.3 ms y p95 9.1 ms. No son carga móvil fría,
FPS de render sostenidos, tiempo GPU ni rendimiento en AR. El contador de dibujo
se recoge después del render para evitar reportar el contador reiniciado.

El build completo contiene **11,829,881 bytes (~11.83 MB)** sin comprimir,
incluyendo módulos/recursos que se cargan de forma diferida. El módulo JS principal
ronda 3.06 MB y 0.85 MB gzip; esto no equivale al tráfico total inicial. Vite avisa
por chunks grandes y una importación Node de MaterialX externalizada; no hubo
fallo de render con el material estándar de esta escena. MaterialX no fue probado.
No se añadió una optimización amplia fuera de alcance: medir red móvil y perfilar
los recursos realmente descargados antes de aceptar el presupuesto del gemelo.

## Compatibilidad real y fuentes

**Unity/Needle:** la guía actual recomienda Unity 6/6.3 LTS. Se fijaron exportador
y runtime en **5.1.12**; en la consulta del 6 de septiembre npm `stable` apuntaba a esa versión y `latest` a
`6.0.0-alpha.3`. El manifiesto del exportador declara mínimo Unity 2021.3, que
no constituye certificación de todas las versiones. La combinación elegida no
fue ejecutada. [Instalación oficial](https://engine.needle.tools/docs/getting-started/),
[integración Unity](https://engine.needle.tools/docs/unity/).

**Android:** ruta principal Chrome + dispositivo compatible con ARCore + Google
Play Services for AR instalado/habilitado + contexto seguro. No todo Android
es compatible. Google indica que el emulador Android no soporta este recorrido
WebXR; no se usa emulación como prueba de colocación.
[Requisitos oficiales Google](https://developers.google.com/ar/develop/webxr/requirements).

**iPhone/iOS:** Safari no ofrece WebXR nativo; Needle deriva a **Needle Go App Clip**,
un runtime que proporciona WebXR mediante ARKit. El proveedor documenta iOS 14+
y requiere una URL HTTPS pública. Esto añade una transición al App Clip y una
dependencia de distribución de Needle. Anclas, estimación de luz y captura de
cámara siguen con limitaciones/en desarrollo según la documentación consultada;
puede haber deriva. No prometer equivalencia con Android ni persistencia espacial.
[Needle Go y limitaciones](https://engine.needle.tools/docs/how-to-guides/xr/ios-webxr-app-clip.html).

**Quick Look:** vía USDZ separada. Esta prueba exporta el estado del cubo al pulsar
el botón iOS; el visor no ejecuta la UI HTML ni la lógica TypeScript de la aplicación.
No se implementaron Everywhere Actions ni se verificó generación/colocación USDZ
en un teléfono. Es una alternativa de visualización reducida, no una timeline
interactiva equivalente. [Needle USDZ](https://engine.needle.tools/docs/how-to-guides/everywhere-actions/),
[Apple Quick Look](https://developer.apple.com/quick-look-gallery/).

**Sin soporte:** mantener 3D WebGL2, texto explicativo y controles. HTTP por IP LAN
no es contexto seguro. `localhost` es especial para el navegador del Mac, pero
un QR con localhost no apunta al Mac desde un teléfono. Un hosting con login
puede servir la prueba 3D al propietario; no satisface el acceso anónimo necesario
para Needle Go. [Configuración XR Needle](https://engine.needle.tools/docs/how-to-guides/xr/).

## Recomendación y condición de cierre

**Decisión: mantener Unity → Needle → Web como recorrido candidato y completar
esta validación antes de construir el gemelo definitivo. No aprobar aún la
viabilidad de extremo a extremo.** Unity para autoría visual; TypeScript/Needle
para estado, datos y experiencia web; WebXR/ARCore como referencia Android;
Needle Go como ruta iPhone si se acepta App Clip y sus límites; Quick Look como
alternativa reducida; 3D web como respaldo universal dentro de WebGL2.

Para declarar CUMPLIDA faltan: (1) abrir/compilar Unity y exportar el GLB real,
(2) comprobar paridad visual editor/web, (3) URL pública sin login para Needle Go,
(4) pruebas físicas Android/iOS de cámara, retícula, colocación, ajuste, salida,
reentrada y estabilidad, (5) perfil móvil y carga fría. El protocolo está preparado.
Si el requisito definitivo exige Safari puro con toda la lógica AR, este recorrido
no lo satisface: se necesitaría reevaluar esa condición. No se inició otra fase.

## Alojamiento entregado

Despliegue privado completado:
[abrir prueba HTTPS](https://auralis-phase4-needle-probe.alejandro-cornejog4.chatgpt.site).
El propietario puede iniciar sesión y usar el QR desde la página. El acceso
público está pendiente de autorización; no se considera validada la entrada de
Needle Go desde esta URL privada. Fuente web desplegada:
`8f04403d3fc9b76bb1b609445f2eb13c3e7320fe`. El JSON de despliegue conserva el resultado.

La versión 3 quedó en estado `succeeded` el 9 de septiembre. La comprobación
visual final de esa URL quedó detenida en el inicio de sesión de ChatGPT; el
arrastre se verificó localmente con la misma fuente compilada y publicada.
No se interpreta la confirmación del despliegue como validación AR.
