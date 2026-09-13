# Fase 6 — Secuencia temporal NOAA 12975

Ruta `/phase6/`. Conserva `/` (Fase 4) y `/phase5/` (estado único).
`npm run dev`: abrir `http://localhost:5184/phase6/`.
Validación: `npm test` y `npm run build`.

La secuencia pública deriva exclusivamente del contrato congelado de Fase 3.
El adaptador offline `../scripts/build-phase6-assets.py --check` verifica cinco
archivos originales, canales, todos los píxeles de quince PNG y sus hashes.
No ejecuta inferencia ni modifica datos. Requiere Python con NumPy y Pillow.

Se reutiliza **el GLB real de Unity de Fase 5**, con su evidencia y hash originales.
El controlador temporal cambia las texturas de los tres planos ya exportados;
no crea una esfera alternativa. La esfera completa sigue siendo ilustrativa.

Anterior/Siguiente y fechas seleccionan observaciones reales. Reproducir recorre
en la dirección elegida, espera dos segundos por estado y se detiene al extremo.
Desde un extremo, Reproducir reinicia desde el opuesto. Selección manual y cambio
de dirección pausan. Fundido de 260 ms exclusivamente visual, sin interpolar SI,
predicción ni campo magnético; se omite con movimiento reducido.

Una caché acotada contiene quince mapas verificados. Cada selección actualiza
atómicamente los tres materiales, las referencias web/AR, fecha, archivo, SI y
estimación determinista ONNX. Liberar cancela reproducción, listeners y carga;
dispone las texturas y mantiene solo las tres referencias 2D del estado actual
hasta recargar o abandonar. No cambia órbita, zoom, escala ni capa al seleccionar.

Needle Go usa el panel AR compartido con controles temporales. Quick Look conserva
solo una instantánea del estado elegido, sin timeline ni shaders del navegador.
La prueba física de AR y rendimiento en iPhone 15 Pro está pendiente. No hay
predicción de llamaradas, máscara NOAA, WCS o reconstrucción magnética 3D.
