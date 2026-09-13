# Fase 7 — Contexto científico del gemelo temporal

La ruta `/phase6/` conserva la esfera temporal de Fase 6.1 y añade contexto de
NOAA 12975 / HARP 8088. Las cinco clases SRS guardadas son Beta, Beta, Beta,
Beta-Gamma y Beta-Gamma-Delta. Su validez/emisión se conserva por separado del HMI.
HARP es asociación de catálogo compartida, no máscara por instante ni identificación
exclusiva de NOAA 12975. SI sigue siendo de disco completo.

`public/phase7/context.json` es un adaptador offline del contrato Fase 3; contiene
los seis eventos ya seleccionados en Fase 2/3, sin ampliar el catálogo. Incluye
M4.0, M1.1, M2.2, M1.6, X1.3 y M9.6 con inicio/pico/fin UTC, relación temporal y
referencias a diez snapshots originales byte a byte, con hash y consulta original.
No se hizo consulta científica nueva ni inferencia. El catálogo no es exhaustivo.

Dos filas de la misma escala UTC: cinco HMI en sus horas de registro, seis eventos
en sus picos. Las etiquetas GOES ocupan carriles para evitar colisiones, sin mover
horizontalmente los picos. El dominio llega al fin del último evento del 31; una
zona marcada indica ausencia de más magnetogramas tras el 30 a las 00:00:53 UTC.
X1.3: pico 30-mar 17:37:00 UTC, 63,367 s = 17 h 36 min 07 s después del último HMI.
No es un sexto estado. Ninguna llamarada está capturada por las cinco observaciones.

Elegir evento pausa Play y conserva HMI, textura, mapas, SI, cámara y escala. El
inspector informa qué HMI continúa visible. Un botón explícito permite elegir el
HMI anterior del evento; cambiar estado o reanudar Play vuelve al contexto SRS.
Web y overlay AR usan una misma instancia de ScientificContext y TemporalSequence.
Quick Look conserva únicamente la instantánea seleccionada, sin timeline/contexto.

Clases de información visibles: observación real HMI/SRS; resultado Coronium SI;
recreación visual 3D; evento histórico externo GOES. No hay predicción de llamaradas.
Materiales, veinte texturas y GLB Unity conservan los hashes de Fase 6.1.

Validación y publicación: `docs/phase7.md` y `evidence/phase7/` en el proyecto padre.
La prueba física de iPhone/Needle Go continúa pendiente; DOM AR no certifica XR real.
