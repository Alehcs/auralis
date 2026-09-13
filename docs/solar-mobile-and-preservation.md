# Prueba móvil HTTPS y conservación del gemelo

Comprobación del 12 de septiembre de 2026. No se modificó código, configuración, diseño, animación ni recursos. No hubo commit, push ni publicación.

## Qué se puede probar ahora

`localhost` en el teléfono se refiere al propio teléfono. Una IP del ordenador por HTTP puede servir para una revisión web en la misma red, pero no resuelve el requisito HTTPS del recorrido AR.

El Site existente está activo, es público y conserva su versión 12:
https://auralis-phase4-needle-probe.alejandro-cornejog4.chatgpt.site/phase6/

Se verificaron HTTP 200 con curl y carga real en el navegador: Unity GLB cargado, hash de exportación válido, HMI29, shader `anchored-hmi-v75-2`, sin errores en los diagnósticos. Cinco recursos clave publicados coinciden byte a byte con los locales: GLB, secuencia, actividad, contexto histórico y atlas solar HMI29. Una petición automatizada con urllib recibió 403; curl y el navegador funcionaron. No se desactivaron protecciones de Cloudflare.

Esta URL permite probar el Sol aprobado ya publicado. **Todavía no incluye la última integración en el dashboard ni el panel AR compacto local.** No debe usarse para aceptar esas dos novedades.

## Sites y el dashboard completo

Sites ya sirve el visor estático y es una opción viable para entregar el gemelo por HTTPS sin reconstruirlo. La distribución integrada contiene las rutas y recursos necesarios del mismo visor; se comprobó previamente su carga por iframe y por `/phase6/` en un servidor estático local. No se ha desplegado ni probado el nuevo dashboard en Sites, por lo que esa compatibilidad de extremo a extremo aún no está certificada.

Para publicar solamente el visor actualizado, se reutiliza el Site existente y su flujo de build. Para publicar Auralis integrado, el artefacto a servir es `auralis-front/dist`, con `/phase6/` y los demás recursos en la raíz del mismo origen; además hay que configurar la ruta SPA `/dashboard`. No basta con publicar el directorio del prototipo, porque su página principal sigue siendo la prueba histórica.

El gemelo funciona con HMI y Coronium precalculados; no necesita inferencia remota. El resto del dashboard sí llama a FastAPI: `auralis-front/src/lib/api.ts` usa `VITE_API_URL` y por defecto `http://localhost:8000`. En un sitio público hay que alojar ese backend por HTTPS y autorizar únicamente el origen del frontend en CORS. La configuración actual de Sites es estática y no ejecuta ese backend Python/PyTorch/ONNX. No se modificó el backend ni se fingieron respuestas para ocultar esta dependencia.

El iframe mantiene permisos XR/cámara/fullscreen limitados a su propio origen. En iPhone, el recorrido de menor riesgo sigue siendo abrir el visor directo en Safari y continuar a Needle Go. Su enlace/QR conserva el estado seleccionado en la versión local integrada. No se presupone AR nativo dentro del iframe.

La [documentación oficial actual de Needle](https://engine.needle.tools/docs/how-to-guides/xr/ios-webxr-app-clip.html) exige URL HTTPS públicamente accesible y describe Safari → Needle Go / App Clip. Quick Look sigue siendo un resultado reducido, sin la animación procedural y timeline del visor web. La carga de escritorio no prueba cámara, colocación, panel nativo ni rendimiento físico.

## Animación comprobada sin cambios

En la versión integrada local, HMI29, cámara fija, DPR 1.5:

- Animación activa: dos capturas separadas tres segundos difieren en la región del Sol; el resto permanece igual.
- Pausa: dos capturas separadas tres segundos son exactamente iguales.
- Reanudación: vuelve a cambiar la región del Sol.
- Diagnósticos sin errores, mismo estado y cámara; los 291 archivos de la comprobación posterior a la integración siguen intactos. También coinciden todos los hashes del manifiesto de entrega de la integración.

Las primeras lecturas dejaron el canvas fuera de pantalla por el desplazamiento de la herramienta al consultar controles. Ese estado pausa el visor por diseño y no se tomó como prueba de animación. La comprobación definitiva mantuvo el Sol visible entre las capturas, sin consultar elementos que desplazaran la página.

Evidencia: `evidence/solar-followup/animation-check.json`, pares `animation-visible-*`, `paused-*`, `resumed-*`, `motion-samples.json`, `protected-check.json` y `public-diagnostics.json`. El build y las 26 pruebas ya aprobados pertenecen a estos mismos archivos: no hubo cambios de implementación que requirieran recompilarlos en esta comprobación.

## Mostrarlo dentro de un año

Se creó `evidence/solar-followup/auralis-web-frozen-2026-09-12.tar.gz` (37.9 MB): copia congelada de los 79 archivos del build web integrado, incluido el visor y sus recursos. Se abrió el archivo y se verificó el SHA-256 de cada miembro contra `frozen-web-files.json`; hash del archivo completo en `frozen-archive.json`.

Es un respaldo generado para recuperación, no otra fuente editable del visor. No contiene el backend, modelo ni dataset. Para revisar esta entrega sin volver a compilar, extraerla en una carpeta nueva y servir `dist` por HTTP local; para AR, alojar ese mismo contenido bajo HTTPS válido. `/phase6/` funciona como visor independiente; las consultas del resto de Auralis necesitan su backend.

Conservar fuera de este ordenador:

1. Este archivo congelado, sus hashes, capturas y un vídeo de referencia aprobado.
2. Una copia del repositorio completo con los cambios locales, fuentes, GLB, recursos y ambos `package-lock.json`. El archivo web congelado no sustituye el respaldo del código.
3. Para la demostración científica completa, copia privada adicional del backend, entorno Python, modelos, manifiestos y datos necesarios. No publicar esos archivos como recursos estáticos del sitio.

Entorno web comprobado: Node 22.23.2, npm 10.9.8, Needle 5.1.12. Para recompilar desde las fuentes conservadas, usar los lockfiles y `npm ci`, sin actualizar dependencias, y luego el build del frontend que prepara el visor automáticamente. Los hashes de lockfiles se guardan en `environment.json`.

Mantener la cuenta y el alojamiento; si se usa un dominio propio, mantener su registro y HTTPS permite conservar un QR estable aunque se cambie el alojamiento. No hay garantía verificada de permanencia de la URL de Sites durante un año. Tampoco puede congelarse el servicio externo Needle Go ni el comportamiento futuro de iOS/Android con un respaldo del sitio.

Una o dos semanas antes de mostrarlo: comprobar URL, cinco estados, animación, pausa/reanudación y QR, y repetir AR en el teléfono que se vaya a usar. Si hubiera incompatibilidad futura, investigar en una copia separada y conservar esta entrega aprobada; no actualizarla automáticamente. Llevar un vídeo aprobado como respaldo de presentación, identificado como vídeo.

## Prueba física breve

Abrir en Safari la URL HTTPS de la versión que se desee validar; comprobar fecha y animación, continuar a Needle Go, conceder cámara y colocar el Sol. Recorrer capas y fechas, plegar/recuperar el panel de la versión compacta cuando esté publicada, restablecer, salir y volver a entrar. Repetir desde QR y comprobar la fecha conservada. Informar modelo de teléfono, sistema, navegador y cualquier solapamiento o fallo. Esta prueba física permanece pendiente.

Publicar la última versión requerirá la autorización que el usuario reservó expresamente; esta tarea solo comprobó y preparó el respaldo.
