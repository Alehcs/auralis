# V3.2-E.2 — registro previo

Solo nuevos archivos en este directorio. V3.1 activa; ningún C1 promovido.
Revisados B/E/E.1: s2026 mitigado quedó inconcluso en p95 forward (+8.69% /−0.57%)
y p95 preparación+forward (+8.42% /−2.15%). No escoger otra semilla.

Cuatro brazos exclusivamente: A=V3.1 default, B=V3.1 mitigado,
C=C1_s2026 default, D=C1_s2026 mitigado. Mitigación EXACTA de E.1:
`SessionOptions.add_session_config_entry('mlas.disable_kleidiai','1')`.
Se reutiliza directamente E.1 intervention.session; ninguna otra opción nueva.
CPUExecutionProvider, FP32, batch1,4 intra/1 inter,ORT_SEQUENTIAL,ORT_ENABLE_ALL,
arena y memory-pattern por defecto. Un PyTorch eval CPU y una sesión ORT
residentes, importación de API/XAI equivalente. Sin forwards PyTorch ni Grad-CAM.

Cuatro rondas,16 procesos nuevos secuenciales. Diseño Williams equilibrado:
R1 A B D C; R2 B C A D; R3 C D B A; R4 D A C B.
Cada brazo ocupa cada posición una vez; cada transición dirigida aparece una vez
 dentro de rondas. Orden irrevocable antes de medir. Sin calentamientos extra,
pausas elegidas por resultados ni prolongaciones del presupuesto.

Mismas18 muestras y orden de E/E.1. Diez warmups POR recorrido, índices0–9.
216 mediciones POR recorrido,12 ciclos exactos de18 muestras. Orden de recorridos
intercalado por RNG NumPy seed42, preconstruido e idéntico en todos los procesos.
1. Forward: xs preparados residentes → session.run → float(item()).
2. Preparación: NPY crudo residente → API._prepare_numpy → mismo forward.
Cuerpos equivalentes a B.cost. Sin disco, ruido, HTTP, startup o carga de modelo
 dentro del reloj. Cronómetro perf_counter_ns monotónico y síncrono CPU.
Asignaciones mínimas del propio recorrido se incluyen. Hashes, profiling,
comprobaciones de paridad, listas de resultados/serialización fuera del reloj.
Todos los tiempos se conservan; percentiles NumPy lineales sin recorte ni filtros.

Después de medir:6 forwards pequeños (3 muestras índices0,6,12 ×2 recorridos),
contra valores E.1 y paridad exacta entre recorridos. Revisar también outputs
escalares ya obtenidos, sin repetir inferencia. Tolerancia original combinada
atol=rtol=1e-5; estado PyTorch/BN antes/después. No nueva evaluación263.

Reutilizar paridad263, memoria con ruido y tamaño/parámetros de E.1 SOLO si sus
hashes, modelos, código de sesión, preprocesamiento y entorno siguen idénticos.
Hashes de fuentes y del binario ORT verificados antes de medir. Versiones/hardware
actuales deben coincidir. Si no, parar y declarar evidencia no aplicable.
No repetir s42/s137, HTTP704 ni XAI. RSS de estos nuevos procesos es contextual:
NO sustituye la guarda de memoria del servicio con ruido de E.1.

Comparaciones por ronda y recorrido (p50 y p95):
- modelo: D/B; runtime V3.1:B/A; runtime s2026:D/C; completo:D/A.
- C/A informativa adicional, sin otros brazos.
Cambio porcentual=100*(numerador/denominador−1). Límite<=+5% aplicado sin redondeo.
Por percentil:4 pasan=cumple;4 fallan=incumple;mezcla=inconcluso.
Por recorrido:incumple si algún percentil falla las4 rondas;cumple si ambos
pasan las4;en otro caso inconcluso. No promediar para borrar incumplimientos.
Comparaciones de modelo/runtime/completo se juzgan separadamente. Una mejora de
RSS no autoriza una ralentización>5% del runtime o del cambio completo.
Si alguna comparación requerida queda incumplida/inconclusa, mantener bloqueo;
si todas cumplen, recomendar solo continuar evaluación de integración autorizada,
sin aprobar producción. No se selecciona s2026 por ser favorable: es el pendiente.

Monitor externo de E.1 desde lanzamiento: RSS5ms, sistema1s, CPU,load,swap,memoria
disponible y procesos antes/después. No bancos/entrenamientos concurrentes.
No cerrar apps del usuario. Interrupciones/suspensión/competencia identificada
se documentan y vuelven inconclusa la ronda afectada; no reemplazarla. Registrar
alerta si CPU sistema>=85% durante3 muestras1s consecutivas, available<2GiB o
swap-in/out aumenta durante medición; estas alertas por sí solas no atribuyen
causa ni eliminan tiempos. Seguridad heredada:RSS hijo>8GiB oavailable<1GiB3s
termina hijo y conserva incidente. No reintentar un brazo medido automáticamente.

Limites: validation de selección, baja actividad y dudas XAI borde/fondo siguen
vigentes. No inferir HTTP total, móviles, equipos modestos ni uso prolongado.
Completar la medición no aprueba al candidato. No comienza otra fase.
