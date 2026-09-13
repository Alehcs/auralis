# Fase 7.1 — prueba física breve (pendiente)

Dispositivo previsto: iPhone 15 Pro. **No realizada por el agente.**

La implementación está en http://localhost:5184/phase6/ en el Mac. Esa URL no
abre el Mac desde el teléfono. El sitio público sigue en Fase 7, versión 11;
no sirve para validar 7.1 hasta autorizar y completar commit, push y publicación.
Needle Go requiere una URL pública HTTPS. No se creó un túnel ni se publicó.

Tras publicar 7.1, abrir la URL habitual terminada en `/phase6/` y comprobar
«FASE 07.1» y `build: phase71-v2` en Verificación técnica. Evitar caché antigua.

1. **Web, 1 min — Brave o Chrome:** mantener el 24 de marzo, detener el giro y la
   secuencia. Mirar durante 10 s con cámara fija. Deben verse partículas con pequeñas estelas y granulación móvil; los núcleos no se desplazan. SI 1,679617 y ONNX 1,470520 permanecen.
   Pulsar «Pausar superficie»: el movimiento se detiene. «Animar superficie»
   lo reanuda sin cambiar de fecha.
2. **Comparación, 1 min:** «Congelar en t=0». Recorrer 24→25→28→29→30 y volver.
   Regresar al 24 reproduce su superficie. Entre 29 y 30 SI baja de 2,057672 a
   2,050173. Probar Play y Atrás con superficie pausada; luego pausar la secuencia
   y animar superficie. Magnetograma, B+ y B− deben quedar fijos sin ondulaciones.
3. **Safari → Needle Go, 2 min:** abrir AR, conceder cámara y colocar. Comprobar
   que el material conserva movimiento, pausa y t=0; cambiar fecha/capas en el
   panel AR. Girar físicamente alrededor: dorso ilustrativo, sin HMI. Probar
   escala, salida/reentrada y bloquear/desbloquear. Si el panel o material falla,
   registrar exactamente la ruta y el síntoma. No asumir que el estado anterior
   del navegador se transfiere al nuevo contexto de Needle Go.
4. **Quick Look, 30 s:** probar separadamente. Debe mostrar la textura horneada
   de la fecha seleccionada, sin partículas ni granulación animada, timeline ni controles web.
   Es una alternativa de instantánea, no prueba de la animación AR.
5. **Rendimiento, 1 min:** usar «Medir 30 s de render» una vez en web y otra en AR
   colocado, mantener visible y sin tocar. Registrar calor, tirones, seguimiento,
   escala y resolución aparente. Descargar el registro desde cada contexto que
   lo permita. La cifra de render no equivale a tiempo GPU ni calidad de tracking.

Enviar: iOS y versiones de navegadores, ruta exacta, resultado web/Needle Go/Quick
Look por separado, registros JSON y, si es posible, vídeo de 10 s en AR colocado.
El estado físico de la fase solo se actualizará tras recibir esos resultados.
