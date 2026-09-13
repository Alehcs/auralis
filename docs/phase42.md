# Fase 4.2 — Unity → Needle → Web real

2026-09-09. **Preparación técnica completada. Cadena Unity → Needle → Web demostrada.**
La validación física WebAR/WebXR y rendimiento móvil sigue pendiente. No se
construyó el Sol ni el gemelo temporal y no se reemplazó la simulación Three.js.

## Resultado

Unity **6000.3.17f1 ARM64** creó `Assets/Scenes/Phase4Probe.unity`, con cubo de
20 cm, material, cámara, luz, OrbitControls y WebARSessionRoot. Needle exporter
**5.1.12** exportó realmente `web/public/unity/Phase4Probe.glb` (73.316 bytes).
La web carga ese archivo por defecto, verifica su evidencia/SHA-256 y conserva
sus componentes. La escena provisional histórica solo queda en `?scene=provisional`.

**URL pública:** https://auralis-phase4-needle-probe.alejandro-cornejog4.chatgpt.site/?scene=unity

**GLB SHA-256:** `92ce99f4e279eaf47110ddaee595e0c52daa566d806bb05204f9e458fe9d413b`.
Generador incrustado: `Needle Engine Unity Integration 5.1.12`.
Exportación: `2026-09-09T17:00:59.9602080Z`. Publicación 6:
`08c481f707f2d7ca865beb1a5826b48a0f6e2414`.

## Qué se automatizó

- Comprobación del editor y directorios Android/iOS/WebGL; Java 17.0.18,
  CMake 3.22.1, adb 36.0.0, NDK clang 18.0.3 y aapt2 respondieron correctamente.
- Importación de Needle desde `https://packages.needle.tools`, versión fijada y
  dependencias resueltas en `unity/Packages/packages-lock.json`. No se importó el
  instalador `.unitypackage` de Descargas ni se modificó el paquete del proveedor.
- Compilación C#, creación de escena real, captura de referencia desde su cámara,
  exportación Needle y evidencia escrita por el editor; comprobación GLB y build.
- Verificación de nodos, cámara, luz, OrbitControls, WebARSessionRoot, material,
  cubo escala `[0.2,0.2,0.2]`, altura `[0,0.1,0]`, 1 mesh y 12 triángulos.
- Comparación visual básica entre `unity-camera.png` y `web-initial.png`: cubo,
  material cian, orientación y encuadre coherentes. No se afirma igualdad píxel
  a píxel ni fidelidad para shaders ajenos a esta escena mínima.
- Interacción real: color, giro de 45°, escala 2×, restablecimiento del color
  original importado/escala 1/giro 0 y arrastre orbital. La cámara pasó de
  `[-0.5,0.4,-0.7]` a `[0.387606,0.282665,-0.803987]` tras el arrastre.
- Ocho tests Node y compilación TypeScript/Vite correctos. El visor mantiene error
  explícito si GLB/evidencia faltan o no coinciden; no sustituye por geometría TS.
- Publicación HTTPS sin autenticación; auditoría de 26 archivos. Recursos exactos
  por SHA-256, HTML de aplicación comprobado separando el script añadido por
  Cloudflare. Diagnóstico público confirma el mismo SHA y `unity-glb-loaded`.
- QR público e iOS generados y decodificados independientemente con Apple Vision.
  La decodificación software no se presenta como escaneo físico con un teléfono.

## Rendimiento del Mac

Muestra de render **30,0012 s**, 1.786 frames, **59,531 renders/s**, mediana
16,7 ms, p95 17,5 ms, cero intervalos superiores a 50 ms. Se ejercitaron controles
antes de la muestra. Un draw call, 12 triángulos, DPR máximo 1,5.

La instrumentación cuenta callbacks de render de Needle, separa 3D/XR y registra
interrupciones. No mide tiempo GPU ni certifica tracking o rendimiento móvil.
La inicialización pública inicial observada fue 1.579 ms con caché/red no controladas;
no es un benchmark frío ni un presupuesto para el futuro gemelo.

## Bloqueos resueltos y límites

El primer intento terminó con código 198 por licencia ausente. Tras la activación
realizada por el usuario, Unity permitió importar y ejecutar. Se conserva el log
inicial como histórico y el último intento terminó correctamente.

La primera compilación reveló referencias ausentes porque los ensamblados editor
Needle no se incluyen automáticamente. Se añadió `Auralis.Phase4.Editor.asmdef`
con las referencias verificadas. También se corrigió el chequeo de exportación:
`Export.AsGlb` devuelve una URI relativa, y hay que comprobar la ruta de salida
absoluta del contexto. El archivo ya se exportaba, pero la herramienta local lo
marcaba incorrectamente como fallo. La ejecución final exportó y generó evidencia
con código 0; no se fabricó un GLB ni se escribió manualmente su procedencia.

Se corrigió además una espera al recargar con el visor fuera de pantalla:
la inicialización usa el evento `loadfinished`, independiente del primer render,
en lugar de `onStart`. Se verificó localmente y en la publicación 6 con desplazamiento conservado:
visor fuera de pantalla, controles activos y GLB correcto. Evidencia:
`public-reload-fixed.json`. El diagnóstico final indica build `phase4.2-20260909-b`.

Persisten advertencias de módulos nativos durante el arranque de Unity, shaders
opcionales durante importación, y chunks grandes/MaterialX al construir la web.
No impidieron esta exportación ni el render probado. No se certifican builds
nativos Android/iOS/WebGL de Unity: este recorrido usa glTF y runtime web Needle.
El build completo incluye recursos diferidos; su tamaño no equivale al tráfico
inicial. No hay errores/warnings de consola en el visor público observado.

## Única intervención pendiente

No hace falta crear/exportar manualmente en Unity. En teléfonos físicos faltan
QR → página → 3D → AR, permisos, retícula, colocación, ajuste, escala física,
deriva, salida/reentrada, bloqueo/reanudación y observación de rendimiento/calor.

Android: Chrome + ARCore compatible. iPhone: Safari → Needle Go; Quick Look se
prueba aparte, sin asumir que conserve los controles HTML/TS. Las limitaciones
conocidas de anclas de Needle Go siguen vigentes; no se verificaron en este intento.
Pasos mínimos: `evidence/phase42/PRUEBA-MOVIL.md`. Usar el QR de esta fase y
registrar que el diagnóstico indica `unity-glb-loaded` y el hash de arriba.

La cadena de escritorio sí está demostrada. La aprobación definitiva para el
gemelo móvil aún requiere esos resultados físicos. No se inició otra fase.

## Reproducir y evidencia

```sh
cd /Users/alejandro/Documents/ProyectosAG/Auralis/prototypes/phase4-unity-needle
sh scripts/prepare-phase42.sh
cd web
npm run dev
# http://localhost:5184/?scene=unity
```

El script reabre la escena existente; no la sobrescribe con una escena vacía.
El editor debe estar cerrado antes de ejecutar batchmode sobre el mismo proyecto.
Conservar nuevos logs/hashes: una nueva exportación puede cambiar metadatos internos.
Para comprobar el sitio sin sobrescribir evidencia histórica de Fase 4.1:
`python3 scripts/audit-phase41-public.py --phase phase42`.

Evidencia bajo `evidence/phase42/`: log final
`unity-export-20260909T170054Z.log`, imagen Unity, capturas web, interacción JSON,
muestra de render, estructura GLB, auditoría HTTP, diagnóstico público, QR y
manifiesto SHA-256. Los logs locales del editor no se publicaron en el sitio.
El código/promoción web se guardó únicamente en el repositorio aislado `web/`;
no se hicieron commits en el repositorio padre de Auralis.
