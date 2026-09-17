# V3.2-E.1 — protocolo previo de diagnóstico de memoria

Solo escribir en este directorio nuevo. E y producto quedan protegidos por hash.
Se reutilizan exactamente los cuatro pesos/ONNX de E, sin exportar, entrenar,
cuantizar, cambiar arquitectura/BN/entrada/split ni dependencias. No promoción.

Primero: auditoría estática de B–E, trazas previas, manifiestos, retención,
contextos gradiente y normalización del grafo ONNX sin pesos/nombres; atributos
estructurales, operadores, conectividad y formas se comparan explícitamente.
El proceso de auditoría es separado y no aporta RSS a mediciones de inferencia.

Condiciones: CPU FP32 batch1, 4 intra/1 inter, ORT_SEQUENTIAL/ENABLE_ALL y
CPUExecutionProvider. Misma máquina disponible y entorno instalado, documentados.
Mismas18 muestras y orden de E. Ejecución secuencial sin entrenamientos.

Primer diagnóstico: 12 procesos nuevos = 4 modelos × ONNX solo / PyTorch solo /
ambos residentes. ONNX solo no importa Torch; PyTorch solo no crea ORT; ambos
importa API y retiene exactamente una instancia PyTorch XAI y una sesión ORT.
Las bibliotecas difieren entre brazos diagnósticos; NUNCA usarlos cruzados para
aprobar guardas. Grad-CAM no se ejecuta; hooks=0. PyTorch determinista usa
inference_mode en cada forward. No desactivar gradientes de una ruta XAI.

Monitor externo ligero (stdlib + psutil, sin numpy/torch/ORT) desde Popen hasta
salida, RSS del hijo cada5ms, eventos por operación con monotonic_ns y ru_maxrss
vitalicio del hijo. CSV se escribe incrementalmente en el monitor, no se retiene
una lista de tensores ni outputs grandes. Presión/swap/CPU/carga del sistema cada1s,
procesos antes/después. Medir también RSS del monitor; no sumar con hijo.
Un probe separado de64MiB tocados por página comprueba escala RSS/ru_maxrss en
macOS. Todos los bytes crudos; MiB=2^20, GiB=2^30.

Etapas: inicio; auditoría ligera de hashes; imports; PyTorch checkpoint si aplica;
creación ORT si aplica;18 raws+18 inputs preparados residentes (54MiB FP32);
primer forward;10 warmups;60 forwards sobre la primera muestra fija;
60 forwards ciclando18 muestras;3 warmups y30 solicitudes de ruido (20 ruidos
sigma.005 seed42 por solicitud +1 determinista) solo donde hay ORT; luego60
forwards deterministas cíclicos para comprobar estabilización. Con ambos
residentes se usa ORT en estos forwards. No ejecutar PyTorch innecesariamente
antes del banco equivalente: afectaría su pico vitalicio. Predicciones escalares
se verifican contra E y se registran tiempos individuales. No liberar modelos,
forzar GC/malloc_trim ni vaciar cachés del runtime para mejorar cifras.

Distinguir salto de inicialización, crecimiento por operación, meseta y picos.
No llamar fuga a RSS que permanece alto. Abort preventivo si RSS hijo>8GiB o
memoria disponible<1GiB persistente 3 muestras de sistema; conservar fallo.
No eliminar atípicos ni escoger rondas favorables.

Intervenciones adaptativas acotadas: SOLO tras evidencia registrada, una opción
por vez (p.ej. arena o patrón de memoria si las trazas/logs lo justifican), aplicada
a TODOS los modelos en procesos nuevos. Registrar hipótesis, evidencia, cambio
exacto y criterios antes de probar. Máximo dos mecanismos justificados, sin
búsqueda de una combinación favorable. Sin cambios de pesos/grafo exportado.
Logs detallados del runtime, si hacen falta, en procesos diagnósticos separados.

Si hay explicación/intervención suficiente, revalidar el banco cost() de B usado
en E (mismas18 muestras, warmup10/reps60 para forward/prepare/carga, handler
ruido warmup3/reps30, orden intercalado seed42). Dos rondas, orden invertido,
referencia y todos los candidatos con ambos residentes. Conserva diagnóstico de
ruido. Monitor externo desde arranque, además del muestreo interno histórico B;
pico primario conservador incluye todas las etapas, nunca empezar tras el pico.
También repetir configuración original si es necesaria para contraste actual.
No sumar análisis de paridad/perfilado al pico de esos procesos.

Todo cambio de ejecución se evalúa aparte sobre las263 observaciones en orden E,
contra ONNX E y PyTorch CPU determinista: atol=rtol=1e-5, sin relajar. Conservar
valores crudos, métricas global/bandas/cola y casos que exceden. Sin ensemble.
Guardas B intactas: RSS pico<=1.10 referencia; p50/p95 forward y prepare<=1.05;
pesos propios<=1.10 y parámetros<512000. Dar las dos rondas, cada semilla y
agregado sin ocultar fallos; discordancias=inconcluso. El ahorro al quitar ruido
no compensa un incumplimiento. Paridad no resuelve selección-validation ni XAI.
No aprobación de candidato ni siguiente fase por el solo cierre del diagnóstico.
