# Dos Sites para Auralis — demo sin backend

El usuario eligió presupuesto cero y **solo Sites, con resultados guardados,
sin nuevas inferencias ni análisis de archivos subidos**. No se contrató ningún
servicio externo ni se modificaron modelo, backend, dataset original o contratos.

## Preparación local

- Dashboard registrado como Site independiente, todavía sin publicación de esta
  entrega: `appgprj_6aa5a31246f881919aec7fcca839323e`. Checkout de entrega:
  `deployments/dashboard-sites`. La fuente editable sigue en `auralis-front`.
- Visor solar: Site existente `appgprj_6a9dbce56b108191af6d13c5cdd1428c`.
  El diseño `phase75-v2`, las cinco fechas, shaders, materiales, recursos y panel
  compacto permanecen intactos. Se prepara una actualización del adaptador de
  comunicación para admitir exclusivamente el origen del nuevo dashboard.
- El dashboard en modo `sites` monta el visor desde su Site dedicado. No empaqueta
  una segunda copia del Sol. En modo local habitual conserva `/phase6/`.
- `VITE_SOLAR_VIEWER_URL` configura el origen del iframe; sus permisos se limitan
  a ese origen. El padre comprueba origen y ventana emisora. El visor solo envía
  metadatos al origen configurado en `VITE_DASHBOARD_ORIGIN` o al suyo propio en
  localhost. No se usan comodines ni se cambia la seguridad global.
- El enlace de móvil y el QR siguen la fecha seleccionada en el visor. No se
  comparten magnetogramas ni selecciones científicas con Monitoring.

## Alcance de la demo

`VITE_FROZEN_DEMO=true` activa un adaptador frontend explícito. Las pestañas
consultan `public/demo/responses.json`; no hay inferencia ejecutándose en Sites.
La modalidad local normal mantiene las llamadas reales al backend.

| Pestaña | Contenido de la demo |
| --- | --- |
| Dashboard | Métricas originales y ejemplo ONNX guardado más reciente de la selección; no se etiqueta como estado solar actual. |
| Monitoring | 11 ejemplos de la verificación HTTP Fase 1.7, sus PNG HMI y el proxy AIA sintético rotulado como tal. |
| Data Pipeline | Catálogo original completo de 1.314 archivos y su distribución temporal. |
| Experiments | Experimentos y protocolos guardados, MC y determinista separados. Curva XAI sin artefacto guardado identificada como no disponible. |
| Agent Lab | Informe de auditoría de los artefactos guardado al preparar la demo; no se ejecutan agentes en el servidor de Sites. |
| Simulation | Visor Unity/Needle completo desde el Site dedicado. |
| Logs | Registro explícito de la demo archivada; no son logs de un backend en ejecución ni se exponen logs locales de la máquina. |
| Settings | Idioma seleccionable; motor de inferencia y avisos identificados como desactivados. |

El exportador `scripts/export-sites-demo.py` solo usa rutas de lectura de
metadatos e imágenes; no llama a predict, explain, faithfulness ni upload.
Toma los SI ya guardados de
`auralis-back/reports/phase17_coronium_v3_1/http_parity.json`. Para el ejemplo que
conserva el payload completo, usa el original de Fase 1.6. No inventa diagnósticos
de confianza/ruido faltantes. Las bandas internas mantienen exactamente los
umbrales existentes; no se presentan como clases GOES.

La selección de Monitoring es una muestra explícita de 11 ejemplos, no la
totalidad del dataset. Los cinco estados históricos del Sol no se reducen.

## Comprobaciones

- Build del visor (incluido TypeScript) y del frontend en modo Sites correctos;
  26 pruebas del visor superadas. Avisos de bundle grande sin cambios de dependencias.
- 38 respuestas guardadas y 22 PNG; hashes de exportación comprobados. Los 11 SI
  coinciden exactamente con los resultados HTTP originales. Cero inferencias nuevas.
- Prueba local de Dashboard, Monitoring, Data Pipeline, Experiments, Agent Lab,
  Logs y Settings. Los 11 ejemplos se pueden seleccionar; no hay formulario de
  subida disponible. Guardas en las funciones de upload impiden solicitudes.
- 119 archivos originales protegidos del visor sin cambios. Los archivos
  protegidos del backend tampoco cambiaron. Solo el adaptador de integración,
  configuración de alojamiento y frontend de demo se modifican.
- Paquete de entrega del dashboard con 31 archivos generados, sin recursos solares
  duplicados. Cada Site tiene su paquete listo bajo `/private/tmp`.
- La comunicación entre los dos dominios publicados debe comprobarse después
  del despliegue del visor actualizado. La validación AR física sigue pendiente.

Evidencia: `evidence/two-sites/`; exportación/procedencia en
`auralis-front/public/demo/manifest.json`; copias previas a esta tarea en
`evidence/two-sites/baseline/`. El rollback de la integración anterior se detiene
si detecta estos cambios posteriores: no debe forzarse ni usar `git restore`.

## Estado de publicación

El commit `fe31b23c43465bed9acf2ae604f64aeb29c15113` existe solo en el repositorio
local del visor. La revisión automática rechazó su push por considerar
insuficiente la autorización de publicación frente a la restricción previa del
usuario. Se solicitó autorización explícita para commits/pushes únicamente de
los repositorios de los dos Sites y para publicar ambos. No se reintentará hasta
recibirla. El repositorio principal no tiene commits ni pushes de esta tarea.

El Site público del Sol continúa en su versión anterior. El dashboard nuevo
está registrado, pero no debe presentarse como ya publicado. No hay cargos ni
backend permanente contratado.

## Corrección de entrada y nombres — 2026-09-12

Inventario completo de Sites (sin cursor adicional): exactamente dos proyectos,
Dashboard y el visor existente. No se crearon ni eliminaron Sites. El visor tenía
metadatos «Auralis · Prueba técnica Fase 4» y su raíz montaba el cubo histórico,
aunque /phase6/ contenía el Sol. Nombre del Site actualizado a «Auralis · Sol y AR».
La API de metadatos solo permite título; su descripción histórica permanece.

Preparado localmente: index.html del visor redirige a /phase6/ conservando query
(incluida state) y fragmento; el título HTML de /phase6/ pasa a «Auralis · Sol y AR».
El dominio se conserva para mantener enlaces y QR existentes. No se modificó
la escena, sus controles ni el panel AR. Instantáneas anteriores, 64 hashes,
build y 26 tests correctos en evidence/two-sites-entry/. Navegación real en preview
comprobó raíz → /phase6/?state=hmi-2022-03-25, HMI25 y escena Unity cargada.

El cambio de título del Site ya se aplicó; el cambio de entrada NO está publicado.
Dashboard sigue sin versión publicada y el Sol sigue en v12. La aprobación de
publicación anteriormente solicitada continúa pendiente; no hubo nuevos commits,
push ni despliegue. No se ha validado AR físico.

### Revisión posterior de entrega de enlaces

El usuario pidió ver ambos enlaces y mostró la raíz pública todavía en Fase4.
Un nuevo intento de push del visor fue rechazado por aprobación automática:
considera que pedir ambos enlaces no autoriza explícitamente el push/despliegue
públicos frente a la restricción inicial. No se eludió el rechazo. La corrección
de entrada quedó en commit local d4249aa (solo repositorio del visor), sin push.
Dashboard continúa sin publicar; no debe entregarse su URL prevista como activa.
Para revisión se ofrecen dashboard local /dashboard y ruta pública solar /phase6/;
esta última todavía no incluye el panel compacto/puente preparados localmente.

## Publicación final autorizada — 2026-09-12

El usuario autorizó explícitamente subir ambos Sites después de aprobar los
ajustes. Publicados con estado succeeded:

- Visor v13, commit e2d9b0944bb78caaea3bb5080bf1516b4192f47c,
  deployment appgdep_6aa5b79dd8cc81919f09d3cc49ac9cf8.
  https://auralis-phase4-needle-probe.alejandro-cornejog4.chatgpt.site
  Raíz comprobada: redirige al visor Coronium /phase6/ con todos los recortes
  de texto aprobados; QR y Needle Go contienen HTTPS y el estado seleccionado.
- Dashboard v1, commit 1a3999829509b2aac22a16548309b44fdb1d54ec,
  deployment appgdep_6aa5b7a513848191a23c63e5dedc669b.
  https://auralis-dashboard.alejandro-cornejog4.chatgpt.site
  Se conserva acceso owner-private; requiere iniciar sesión con ChatGPT.

Se hicieron commits y pushes exclusivamente en los dos repositorios de Sites,
ninguno en el repositorio principal. Los 64 archivos protegidos de código y
recursos del visor mantienen hashes exactos. AR físico sigue pendiente.

## Monitoring: cinco estados y Grad-CAM — 2026-09-13

Dashboard v2 publicado correctamente: commit del repositorio de entrega
`a0563c723a4ed28f481c47e54d013167c951835e`, deployment
`appgdep_6aa6a6f59a788191a5e05b32d2779288`.
Acceso privado conservado; visor solar v13 sin cambios.

Monitoring ofrece acceso directo a los cinco HMI de marzo de 2022 y sus
Grad-CAM precalculados con el backend existente. Los valores SI proceden de
la secuencia guardada, sin nuevas inferencias SI. El sitio sirve imágenes
estáticas, sin necesitar el ordenador del usuario. Se retiraron los desplegables
About the data, AR en el móvil y el botón externo Abrir en móvil / AR.

Build correcto; cinco figuras cargadas en navegador local y cinco valores SI
verificados. 108 archivos protegidos sin cambios. Evidencias y captura en
`evidence/monitoring-five/`; procedencia pública en
`auralis-front/public/demo/gradcam-provenance.json`.

Dashboard v3 publicado el 2026-09-13: retirado el bloque completo Dataset summary
/ System status de ModelMetrics. Build correcto. Commit de entrega
`dcbda06327905cd642b771a013c331221e09b850`; deployment
`appgdep_6aa6a7672b7c8191af8809964e4006f0` succeeded. Copia previa y parche de
reversión en `evidence/remove-summary-status/`. Visor solar sin cambios.
