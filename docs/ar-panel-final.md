# Panel AR compacto y auditoría de integración — 12 septiembre 2026

Cambio local sobre el Sol aprobado `phase75-v2`. La versión pública sigue siendo Site 12; no commit, push ni publicación en esta tarea.

## Panel

Solo se modificaron `prototypes/phase4-unity-needle/web/src/phase5/main.ts` y `src/phase5/style.css` (esta última ruta dentro del mismo web). El ajuste se aplica únicamente al panel AR temporal de `/phase6/`; el visor web, Phase5 y el dashboard no se rediseñaron.

- Fecha UTC y Anterior/Reproducir/Siguiente siempre disponibles con el panel abierto.
- «Capas y vista»: los mismos botones de capas, tamaño, contraste y movimiento.
- «Datos y contexto»: referencia HMI, SI/ONNX, distinción observación/estimación/recreación, timeline proporcional original, seis eventos, fuentes y dirección de reproducción. No se reemplazan controles ni listeners; permanecen bajo su contenedor científico original.
- «Plegar/Mostrar»: oculta solo el cuerpo; conserva fecha, restablecer vista y salida.
- Restablecer llama al reset existente (en XR no reposiciona la colocación). Salir usa `.quit-ar`, enlazado por el AROverlayHandler de Needle en la entrada a sesión.
- Botones principales de al menos 44 px, sin reducción general de tipografía. Detalles con desplazamiento interno; cabecera y pie quedan fuera de ese desplazamiento.

Comparativa en `prototypes/phase4-unity-needle/evidence/ar-panel-final/comparison.png`: ancho 369 px en viewport 393×852. Antes 460.08 px visibles (contenido total 1130 px); después 248 px; plegado 110 px. Reducción normal de aproximadamente 46%. Con datos abiertos, el panel alcanza 460.08 px y el cuerpo desplaza 1056 px de contenido manteniendo pie visible. Capturas antes/después/plegado/detalles conservadas.

## Recorrido AR auditado

`web/phase6/index.html` y `web/src/phase5/main.ts` implementan Safari → enlace `https://appclip.needle.tools/ar?url=...` → Needle Go. El panel es hijo directo de `needle-engine` con clase `ar`. En la dependencia instalada 5.1.12, `src/engine/webcomponents/needle-engine.ar-overlay.ts` mueve los hijos y el overlay a body para App Clip, conserva eventos y enlaza `.quit-ar` a la salida existente. No se editaron dependencias.

WebXR usa este panel DOM; Quick Look es una instantánea USDZ, sin este panel, timeline ni animación web. El ajuste no cambia selección inicial del nuevo contexto Needle Go, colocación, materiales ni la ruta de lanzamiento.

La comparación se hizo mostrando el panel DOM real mediante un control temporal de desarrollo, **sin crear sesión XR**, cámara ni colocación. El harness temporal está archivado como evidencia y se restauró el archivo de desarrollo original. Esta comprobación no certifica safe areas, interacción nativa ni reentrada física en Needle Go.

## Integración con el dashboard: pendiente

| Evidencia | Estado comprobado en código |
| --- | --- |
| `auralis-front/src/features/dashboard/dashboard-page.tsx:15`, `:80` | La pestaña `simulation` carga `SolarSimulationPage` mediante lazy import. |
| `auralis-front/src/features/dashboard/simulation/SolarSimulationPage.tsx:71` | Componente sin props temporales; actividad inicial M, toggles y rotación locales. Renderiza `SolarScene`. |
| `auralis-front/src/features/dashboard/simulation/SolarScene.tsx:24`, `:407` | Three.js y `WebGLRenderer`, escena procedural anterior. No Unity/Needle, iframe ni enlace al gemelo en esta pestaña. |
| `prototypes/phase4-unity-needle/web/phase6/index.html` | Gemelo en aplicación Vite separada, ruta `/phase6/`, servidor local 5184 y Site propio. |
| `web/src/phase6/temporal.ts:15` | Carga `/phase6/sequence.json` y evidencia/hash; posteriormente activity/atlas/mapas. Selección local HMI29, cinco entradas; comparte controlador entre web y AR de esta aplicación, no con React/dashboard. |
| `prototypes/phase4-unity-needle/scripts/build-phase6-assets.py:14` | Adaptador offline del contrato congelado `auralis-back/reports/phase3_temporal_model/noaa12975.sequence.v1.json`. Copia los resultados Coronium deterministas guardados; no hace inferencia. |
| `auralis-front/src/features/dashboard/magnetogram-panel.tsx:188`, `src/lib/api.ts:111` | El panel de magnetogramas tiene selección propia y llama `predictDual(selected)` al backend. No alimenta `SolarSimulationPage` ni Needle. |
| `auralis-back/src/api/main.py:708`, `:734` | `/api/predict-dual/{filename}` ejecuta ONNX en la petición (además del diagnóstico de ruido separado). Es distinto de leer los resultados congelados del gemelo. |

Los cinco resultados del gemelo pertenecen a Coronium V3.1 determinista; no son MC ni inferencias nuevas por mover la timeline. SI original y estimación siguen separados. Ni nombre Auralis ni hostname implican integración.

Cambios mínimos futuros, **no implementados**:

1. Para dar acceso: añadir un enlace explícito al visor `/phase6/` desde el dashboard. Eso solo conecta la navegación.
2. Para mostrarlo dentro del panel: añadir un contenedor del visor (p. ej. iframe) preservando la salida de nivel superior a Safari/Needle Go para AR. Revisar permisos de embedding del host elegido.
3. Para sincronizar: definir selección por ID de observación/filename, elevar el estado React y añadir un puente explícito validado por origen y mensajes, con acuse al commit temporal. Mapear únicamente los cinco estados disponibles y mostrar el caso no disponible; nunca sustituir silenciosamente un estado o inferir sincronía por fecha/nombre.
4. Mantener visibles la procedencia precalculada del visor y las inferencias por petición del dashboard. Integrar navegación no exige cambiar backend ni volver a ejecutar el modelo.

## Verificación

- TypeScript + Vite build: correcto; advertencia existente de bundle >500 kB.
- 26 pruebas Node existentes: pasan.
- DOM real en navegador desktop a 393×852: plegar/recuperar, anterior/siguiente, Play/Pause, cinco selecciones 24→25→28→29→30→29, capas B+/Sol y leyenda de contraste; detalles desplazables con pie y cabecera sin solapamiento.
- HMI29, cámara fija de disco, superficie congelada t=0, mismo canvas 359×440: `sun-before.png` y `sun-after.png` tienen píxeles idénticos.
- Hashes de frontend, backend fuente/modelos/contratos, recursos públicos y código del visor: solo cambian los dos archivos UI indicados. Materiales, animación, controladores temporal/científico, geometrías, mapas, GLB y resultados se conservan. Manifiesto y resultado en `evidence/ar-panel-final/verification.json`.
- Salida real de sesión, colocación, panel en App Clip y teléfono físico: **no probados**. No se declara aceptación AR física.

## Prueba breve en iPhone 15 Pro (pendiente)

Este cambio es local; el enlace público aún muestra el panel anterior. Tras una publicación autorizada o un entorno HTTPS de prueba accesible al teléfono:

1. Abrir `/phase6/` en Safari, entrar en Needle Go, conceder cámara y colocar el Sol. Confirmar aspecto/animación aprobados.
2. Plegar/Mostrar varias veces: fecha, recuperación, restablecer y salida deben quedar cómodos y fuera de los controles nativos y del indicador inferior de iOS.
3. Recorrer las cinco fechas, reproducir/pausar y cambiar Sol/HMI/B+/B−. Abrir datos, desplazar y cerrar; ningún toque al panel debe recolocar el Sol.
4. Probar restablecer, salir y volver a entrar; repetir en horizontal y tras bloquear/desbloquear. Anotar si la colocación permanece estable y si aparece algún solapamiento.

Quick Look no sirve para validar este panel. La emulación móvil y las capturas de esta entrega no sustituyen estos pasos.
