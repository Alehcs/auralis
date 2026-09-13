# Gemelo aprobado dentro de Auralis

Integración web local completa en la pestaña existente **Simulation**. Validación AR física pendiente. No hubo commit, push ni publicación. La URL pública anterior continúa sirviendo su versión anterior; no se usa como fuente del iframe.

## Versión protegida

Se partió del visor local `/phase6/`, `phase75-v2` / `anchored-hmi-v75-2`, **con el panel AR compacto ya incorporado**. Antes de editar se guardaron estados Git, copias de los archivos que se modificarían, 291 hashes y una captura del Sol en `evidence/solar-integration/`. Las copias conservan los cambios locales previos; no se usó `git restore`.

La escena real sigue siendo `unity/Assets/Scenes/Phase5Solar.unity`, exportada a `web/public/phase5/Phase5Solar.glb` (SHA-256 `6694a42dd2f0b322c7a65dc9d55d17eb1fe653ab0ec85884ee68b20cb14999b5`). El inventario `protected-before.json` incluye fuentes del visor, materiales, shaders, animación, recursos públicos y Unity, además de fuentes del frontend y backend/contratos seleccionados. Ningún archivo existente del visor de ese inventario cambió, incluidos `src/phase5/main.ts` y `src/style.css`, que contienen el panel compacto aprobado. El único cambio dentro del inventario es el montaje de `dashboard-page.tsx`.

## Archivos de implementación

| Archivo | Cambio |
| --- | --- |
| `auralis-front/src/features/dashboard/dashboard-page.tsx` | Monta `SolarTwinPanel` bajo el mismo identificador de pestaña, mediante lazy import. |
| `auralis-front/src/features/dashboard/simulation/SolarTwinPanel.tsx` | Nuevo contenedor iframe, altura comunicada por el visor, carga/error/reintento y acceso directo al estado seleccionado. |
| `auralis-front/build/solar-viewer.mjs` | Sirve la distribución canónica en desarrollo y agrega sus archivos generados al build del dashboard; falla ante colisiones. |
| `auralis-front/vite.config.ts` | Registra ese adaptador de build. |
| `auralis-front/package.json` | `predev` y `prebuild` ejecutan el build existente del visor; sin cambios de dependencias. |
| `prototypes/phase4-unity-needle/web/phase6/index.html` | Carga solamente el adaptador de integración adicional. |
| `prototypes/phase4-unity-needle/web/src/dashboard-integration.ts` | Comunica estado/altura/carga al padre; prepara enlace y QR de este mismo build y acepta una selección inicial válida. |

También se añadió este informe, evidencia y una nota en `AGENTS.md`. Se conserva íntegro el código y las dependencias de `SolarSimulationPage` y su escena Three.js. Ya no se importan ni montan en esta pestaña. No se portó la escena a React.

El iframe aísla los estilos y contiene el visor completo, con su canvas y controles originales. Su altura sigue la del documento para conservar el scroll del dashboard; no se escala ni se recorta el canvas por CSS del padre. Al abandonar Simulation se elimina el iframe, destruyendo su documento y su bucle de render. Al volver se crea una instancia nueva con el estado inicial aprobado.

## Datos y selección

`web/src/phase6/temporal.ts` carga `/phase6/sequence.json`, sus evidencias, `/phase6/activity.json` y las texturas verificadas. La secuencia procede del contrato congelado de Fase 3 y contiene los cinco resultados ONNX V3.1 **precalculados**. `/phase7/context.json` aporta el contexto histórico. No hay una inferencia nueva al mover la timeline.

`MagnetogramPanel` sigue solicitando `predictDual(selected)` y predicciones de cargas al backend. Su selección permanece independiente. El adaptador no comunica magnetogramas del dashboard al gemelo ni altera las cinco observaciones. `?state=hmi-2022-03-30`, por ejemplo, selecciona una observación existente mediante su botón original después de cargar; no modifica el controlador temporal.

## Preparación reproducible y acceso AR

Desde la raíz:

```sh
npm --prefix auralis-front run dev
npm --prefix auralis-front run build
npm --prefix prototypes/phase4-unity-needle/web test
```

Los dos primeros comandos generan el visor usando su build TypeScript/Vite existente. Desarrollo sirve esos mismos archivos; producción los coloca automáticamente en `auralis-front/dist`. Solo hay una fuente mantenida del visor. Si se edita esa fuente mientras el dashboard está en desarrollo, se reinicia `npm run dev` para regenerarla.

Rutas verificadas: `http://localhost:5173/dashboard` y `http://localhost:5173/phase6/`. El despliegue futuro debe servir desde la raíz del mismo origen `/phase5/`, `/phase6/`, `/phase7/`, `/assets/` y `/unity/`, antes de cualquier fallback SPA. Los recursos conservan sus rutas absolutas originales. El backend existente permite el origen `localhost:5173`; no se amplió CORS para otros nombres de host.

El iframe concede únicamente a su propio origen `xr-spatial-tracking`, `camera` y `fullscreen`. Los mensajes requieren origen idéntico, ventana emisora del iframe y tipo esperado; estado y altura se validan. No se cambiaron cabeceras globales, CSP, CORS ni permisos del resto del sitio. La política del servidor/navegador todavía puede restringir XR.

El enlace superior abre el mismo `/phase6/?state=…` fuera del dashboard. El QR y el enlace a Needle Go también apuntan al estado seleccionado de ese mismo origen. Esto permite el recorrido Safari → Needle Go sin depender del iframe. En un teléfono, `localhost` no apunta a este ordenador: la prueba requiere entregar este build mediante HTTPS accesible, con autorización aparte. No se publicó para conseguirlo. Quick Look conserva su ruta reducida original y no equivale al visor animado con timeline.

## Verificación realizada

- Build final del visor (incluido TypeScript) y del frontend: correctos. 26 pruebas existentes del visor: correctas. Permanecen los avisos de tamaño de bundles y externalización de `node:module` en MaterialX.
- 73 archivos generados coinciden byte a byte entre la distribución canónica y la integrada; también se verificó su respuesta HTTP (`http-assets.json`).
- Comparación `sun-before.png` / `sun-after.png`: **todos los píxeles idénticos**. Fecha HMI29; cámara `[2.4492935982947064e-16, 0.5000000000000001, -2]`, distancia 2, escala 1, canvas 730 × 570, DPR 1, tiempo ilustrativo 0, misma configuración. Diagnósticos completos en los JSON contiguos. La captura usó el mecanismo de desarrollo existente; los controles auxiliares de inspección se retiraron del build final.
- Navegación por 24/25/28/29/30 comprobada dentro del iframe (`navigation.json`); anterior/siguiente, Play/Pause y capas Sol/HMI/B+/B− respondieron. La ruta directa con `?state=…30` mostró la fecha 30 y el enlace correspondiente.
- Panel AR plegado/recuperado inspeccionado mostrando temporalmente su DOM real dentro del iframe. Es evidencia de escritorio de los controles compartidos, **no una sesión XR ni una prueba física**. Restaurar/Salir conservan sus manejadores originales; colocación y salida nativa AR requieren teléfono.
- Dashboard y Monitoring cargaron consultas reales al backend, incluido el SI estimado 1.46 del estado local reciente. Recorrido de Dashboard, Monitoring, Data Pipeline, Experiments, Agent Lab, Logs y Settings: el dashboard siguió operativo; fuera de Simulation había cero iframes. Son comprobaciones funcionales de navegación, no una auditoría exhaustiva de cada herramienta.
- Fallo provocado retirando temporalmente solo el `sequence.json` generado: apareció el error del contenedor, el iframe se desmontó y la barra lateral siguió disponible. Tras restaurarlo, Reintentar cargó una sola instancia correcta (`load-error.png`).
- Sin solapamientos observados en la captura de escritorio. El intento de cambiar el viewport a móvil no se aplicó; se conserva identificado como tal, sin atribuirle validación responsive. Safe areas, orientación y rendimiento AR móvil siguen pendientes.

Captura integrada: `evidence/solar-integration/dashboard-final.png`. Comprobación resumida: `verification.json`. No se cambiaron backend, modelo, dataset, métricas, contratos ni los archivos visuales aprobados.

## Prueba física pendiente (3–5 minutos)

Después de entregar **este mismo build** mediante HTTPS autorizado:

1. En el teléfono, abrir Auralis → Simulation. Comprobar el Sol inicial HMI29 y recorrer las cinco fechas, capas y Play/Pause. Cambiar de pestaña y regresar.
2. Elegir HMI25, pulsar «Abrir este estado para móvil / AR» y abrirlo en Safari. Comprobar que sigue HMI25; continuar a Needle Go, conceder cámara y colocar el Sol.
3. Plegar/recuperar el panel, desplegar capas/datos, tocar anterior/siguiente y Play/Pause. Comprobar Sol visible, botones cómodos, sin solapamiento con controles nativos en ambas orientaciones; restablecer vista, salir y volver a entrar.
4. Mostrar el QR de HMI30 en otro dispositivo, escanearlo y repetir la entrada AR. Confirmar fecha 30 y mismo aspecto. Informar modelo/teléfono, navegador, fecha visible y cualquier solapamiento o fallo.

Esta prueba no está realizada ni aprobada por el agente.

## Volver al montaje anterior

El script `evidence/solar-integration/rollback.py` verifica hashes antes de escribir y utiliza las copias previas a esta integración, incluyendo trabajo local del usuario. No usa el estado de Git como origen de restauración.

```sh
# Solo inspección: no modifica nada.
python3 evidence/solar-integration/rollback.py --mount-only
# Cuando se decida volver a la escena anterior:
python3 evidence/solar-integration/rollback.py --mount-only --apply
# Sin --mount-only permite revisar/restaurar todos los cambios de integración.
```

Si algún archivo objetivo cambió posteriormente, se detiene sin restaurar ninguno. Tras aplicar una reversión se vuelve a ejecutar el build. Las evidencias se conservan. No se ejecutó la reversión durante la entrega.
