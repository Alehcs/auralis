# Fase 6.1 — Evolución visual 3D

Ruta existente `/phase6/`; se conservan `/` y `/phase5/`.

Cinco atlas solares PNG 2048×1024 derivados offline de los cinco magnetogramas
float32 originales, con su hash. `activity.json` enlaza cada atlas al estado,
fuente, contrato, secuencia congelada y GLB real. La secuencia científica y sus
quince referencias lineales permanecen byte a byte iguales.

Se ajusta el borde circular desde el exterior cero. Proyección ortográfica inversa
por UV de la malla real Unity: derecha de imagen = −X glTF, arriba = +Y, frente =
Z negativo. El ajuste no es WCS ni certifica norte/este heliográfico. No se divide
B_LOS por coseno ni se infiere campo radial. Suavizado espacial fijo por polaridad,
umbral visual 0.04, núcleos oscuros y halos ámbar/coral: recreaciones de actividad,
no manchas observadas. Sin continuum ni máscara regional. Dorso idéntico en las
cinco texturas, puramente ilustrativo. Ni SI ni predicción entran en el render.

La escena sigue siendo el GLB Unity real de Fase 5. Se reemplaza únicamente su
material en runtime. La esfera ya no deriva con el plasma animado; los detalles
permanecen anclados al objeto y a la fecha. La rotación orbital sigue disponible.
Fundido gráfico de 260 ms entre atlas, sin interpolar mediciones. Selección, pausa,
dirección, extremos y movimiento reducido usan el mismo controlador temporal.
WebXR/Needle Go comparten objeto/material y overlay; Quick Look recibe el material
baked seleccionado, sin shader web ni timeline. Validación física todavía pendiente.

Caché acotada: 20 texturas (15 mapas + 5 atlas). Atlas: 21,607,068 bytes PNG totales,
~53.3 MiB GPU RGBA+mipmaps para cinco atlas, además de referencias/escena. No es
una medición móvil ni garantiza memoria del navegador. Liberación explícita.

Verificación: 19 tests Node, TypeScript/Vite; procedencia, hashes, UV reales,
sensibilidad espacial/polaridad y retorno de capturas idéntico con cámara fija.
El adaptador reproducible y la evidencia están en el prototipo padre:
`scripts/build-phase61-assets.py --check`, `evidence/phase61/`, `docs/phase61.md`.
No cambia backend, datos originales, modelo, métricas o simulación principal.
