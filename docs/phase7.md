# Fase 7 — Integración científica del gemelo temporal

Estado al 9 de septiembre de 2026: **PARCIALMENTE CUMPLIDA**. Implementación,
verificación web y publicación terminadas. La validación AR en teléfono físico
permanece pendiente.

## Resultado implementado

La ruta existente `/phase6/` incorpora contexto regional SRS y seis eventos GOES
conservados en Fases 2/3. No añade magnetogramas, inferencia, predicción de
llamaradas ni estados físicos interpolados. Conserva el controlador temporal,
las cinco superficies derivadas de HMI, mapas, SI y resultados ONNX de V3.1.

| HMI, marzo de 2022 · 00:00:53 UTC | Clasificación SRS | Ubicación textual SRS | Área (millonésimas del hemisferio) |
| --- | --- | --- | --- |
| 24 | Beta | N13E63 | 160 |
| 25 | Beta | N14E55 | 160 |
| 28 | Beta | N12E05 | 50 |
| 29 | Beta-Gamma | N13W12 | 210 |
| 30 | Beta-Gamma-Delta | N13W25 | 300 |

Cada SRS tiene validez a las 00:00 UTC y emisión a las 00:30 UTC de su fecha.
Estas horas se muestran separadas del registro HMI. La clasificación y ubicación
son contexto catalogado, no una segmentación de los píxeles. HARP 8088 también
está asociado durante su vida a NOAA 12976, 12977 y 12984; no es máscara exclusiva
de NOAA 12975. El SI y los mapas continúan representando el disco completo.

| GOES G16 / NOAA 12975 | Inicio UTC | Pico UTC (posición del marcador) | Fin UTC |
| --- | --- | --- | --- |
| M4.0 | 28 mar 10:58 | 28 mar 11:29 | 28 mar 11:45 |
| M1.1 | 28 mar 20:49 | 28 mar 20:59 | 28 mar 21:09 |
| M2.2 | 29 mar 00:57 | 29 mar 01:11 | 29 mar 01:26 |
| M1.6 | 29 mar 21:43 | 29 mar 21:52 | 29 mar 21:57 |
| X1.3 | 30 mar 17:21 | 30 mar 17:37 | 30 mar 17:46 |
| M9.6 | 31 mar 18:17 | 31 mar 18:35 | 31 mar 18:45 |

Es el conjunto de seis eventos seleccionado en el contrato, no un catálogo
exhaustivo. La X1.3 queda **63.367 segundos = 17 h 36 min 07 s** después del HMI
del 30 de marzo. Ningún estado seleccionado captura ese evento. Tampoco existe
un magnetograma posterior seleccionado que lo encierre.

La escala UTC llega hasta el último evento externo; la zona posterior al último
HMI está rotulada. Las etiquetas se reparten en filas para evitar colisiones,
sin desplazar horizontalmente sus horas. Play recorre solamente los cinco HMI.
Seleccionar un evento pausa Play y conserva fecha, textura y SI del HMI actual;
un botón explícito permite ir a su HMI precedente. Cambiar de estado muestra su
contexto SRS y limpia la selección de evento. El selector de eventos facilita el
uso móvil sin exigir arrastrar toda la escala.

Las cuatro categorías están visibles: observación HMI/SRS, resultado Coronium,
recreación visual y evento histórico externo. Coronium estima SI actual; no
anticipa las llamaradas catalogadas. Las concentraciones oscuras del Sol siguen
siendo recreaciones magnéticas, no manchas solares observadas.

## Trazabilidad e implementación

- Adaptador offline: `prototypes/phase4-unity-needle/scripts/build-phase7-context.py`.
  `--check` verifica correspondencia con el contrato, líneas originales, hashes,
  tiempos de los eventos, relaciones temporales y archivos protegidos.
- Única fuente: `auralis-back/reports/phase3_temporal_model/noaa12975.sequence.v1.json`,
  SHA-256 `0926747125d84a10a20611cf523c42293aa7dd2125567c67ed6e9554bb337ad6`.
- Nuevo contexto: `web/public/phase7/context.json`, SHA-256
  `5a52347adada96acdea45b1a04d146075e83aa643c81e83a2b5752e9c2fc7fc8`.
  Diez snapshots originales (cinco SRS, cuatro catálogos de eventos y un mapeo
  HARP) se copian sin cambiar sus bytes. El inspector ofrece líneas y enlaces.
- `web/src/phase7/history.mjs` valida contexto y calcula posiciones UTC;
  `scientific-context.mjs` comparte selección entre web y overlay DOM de Needle AR.
  Cambios acotados de integración en `web/src/phase5/main.ts` y `/phase6/index.html`.
- No cambian la secuencia congelada, veinte texturas, GLB real de Unity, materiales
  solares, dataset, backend, pesos, métricas ni simulación Three.js principal.

## Verificación realizada

Evidencias en `prototypes/phase4-unity-needle/evidence/phase7/`.

- **23/23 tests Node**: contrato, fuentes, relaciones, selección independiente,
  rechazo de tiempos/capturas falsas y pruebas anteriores de controles/texturas.
- **Build correcto**: TypeScript y Vite. Persisten avisos de tamaño de bundles y
  externalización de `node:module` en MaterialX; no errores de compilación.
- Adaptador `--check` correcto: cinco estados, seis eventos, diez snapshots y
  **1.521 archivos protegidos idénticos** a la línea base de esta fase.
- Nueve selecciones adelante/atrás conservan estado, clasificación y hash solar.
  Play avanza y retrocede hasta sus extremos; seleccionar evento pausa Play.
- Los seis eventos mantienen el mismo HMI y superficie durante su inspección.
  M4.0 navega explícitamente al HMI del 28; X1.3 permanece fuera del HMI del 30.
- **Prueba responsive 393 × 852** en navegador de escritorio: ancho de documento
  393 px, escala horizontal interna, selector de eventos y cuatro capas en cada
  una de las cinco fechas (20 verificaciones). No equivale a teléfono físico.
- Panel DOM AR: contexto, fecha, SI, mapas, seis eventos y selección sincronizados
  con web. No se simula una sesión XR ni se afirma colocación real.
- Liberar/reintentar elimina y reconstruye visor/controladores: seis marcadores
  por vista, sin duplicados ni errores. `/phase5/` carga sin panel histórico.

Capturas locales: `x13-desktop.png`, `mobile-context.png`, `mobile-x13-detail.png`,
`mobile-solar.png`, `x13-final-local.png`. Captura del sitio publicado:
`public-x13.png`. Ninguna acredita ejecución en AR físico.

## Publicación y límites pendientes

URL existente: https://auralis-phase4-needle-probe.alejandro-cornejog4.chatgpt.site/phase6/

Fase 7 publicada como versión pública **11**, autorizada explícitamente por el
usuario. Repositorio aislado del sitio, commit
`e4e99fc2d478277753ae44dc444b25b424bcb4b0`. No se hizo commit del repositorio padre.

Despliegue confirmado el 9 de septiembre de 2026 a las 22:43:20 UTC. Auditoría
HTTPS anónima: **73/73 archivos correctos**, incluidos el contexto científico y
los diez snapshots originales. Los assets coinciden exactamente; en HTML se
registra por separado la adición de Cloudflare. Evidencia:
`public-http-verification.json` y `publication.json`.

En el navegador público se verificaron las cinco fechas, clases SRS, hashes
solares, SI y ONNX; M4.0, M2.2 y X1.3 mantienen el HMI seleccionado y comparten
contexto con el panel DOM AR (`public-browser.json`).

La revisión automática del primer envío requirió autorización explícita; el
usuario la otorgó y la publicación posterior concluyó correctamente.

Pendiente únicamente la prueba física de iPhone/Needle Go: colocar el objeto y
recorrer estados/eventos durante la sesión AR. Instrucciones en
`evidence/phase7/PRUEBA-IPHONE.md`. No se ha iniciado otra fase.
