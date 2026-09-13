# Validación mínima — iPhone 15 Pro / Fase 7.4

Estado: **no realizada**. La web pública sigue en Fase 7; no valida esta revisión.

1. **Web local:** Mac e iPhone en la misma Wi-Fi. Con Vite iniciado en el Mac,
   abrir `http://<IP-local-del-Mac>:5184/phase6/` en Brave/Chrome. La IP se obtiene
   en Ajustes del Sistema → Red → Wi-Fi → Detalles → TCP/IP. `localhost` y el QR
   local no apuntan al Mac desde el teléfono. Comprobar el rótulo **FASE 07.4** y
   `phase74-v1` en Verificación técnica, con HMI29 a 00:00:53 UTC.
2. **Revisión visual, 1 minuto:** ver el disco completo, acercar suavemente y
   orbitar. Evaluar grano/parpadeo, volumen y borde, integración de núcleos, halo
   y conservación del dorado. Alternar Animar/Pausar y Congelar en t=0: no debe
   vibrar estando pausado. El detalle sigue siendo recreación, también detrás.
3. **Controles, 1 minuto:** recorrer 24→25→28→29→30 y volver a 29; probar Play
   en ambos sentidos, HMI/B+/B−, escala y retorno a solar. En 29: SI 2,057672 y
   Coronium 1,683445; en 30: SI 2,050173 (declive real conservado). Comprobar que
   cambiar un evento GOES no cambie el HMI. Registrar tirones, legibilidad y calor.
4. **AR, cuando exista una URL HTTPS autorizada que sirva realmente 7.4:**
   Safari → Needle Go/App Clip; colocar el Sol, acercarse, variar escala, cambiar
   fecha/capa y pausar superficie. Salir y volver al visor. Registrar versión de
   iOS/navegador, colocación y fallos en el formulario de prueba física. No usar
   la versión pública 11 como evidencia de 7.4. Esta tarea no publica ni crea un
   túnel. La URL HTTP local permite revisar web3D, no valida el recorrido App Clip.

Quick Look es una ruta distinta: instantánea horneada, sin el nuevo detalle web
ni timeline. No esperar paridad visual 7.4 en esa exportación reducida.

Aceptar o rechazar visualmente comparando `comparison.png` y los PNG originales.
Los resultados de escritorio y los tests no certifican AR físico.
