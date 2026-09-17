# Alcance del almacenamiento y del RSS

## Pesos cargados para atender inferencia/XAI

Cada proceso E mantiene exactamente una sesión ORT del modelo medido y un
CoroniumV3 PyTorch con el mismo checkpoint para XAI. No mantiene V3.1 residente
junto a C1. La guarda B de tamaño compara esos pesos necesarios por modelo:

| Modelo | Checkpoint | ONNX autocontenido | Total pesos propios |
|---|---:|---:|---:|
| V3.1 | 848269 | 835234 | 1683503 |
| C1 s42, s137 o s2026, individual | 846093 | 835234 | 1681327 |

Bytes exactos. Sin cuantización. Los artefactos ONNX incluyen todos sus tensores.
Checkpoint requerido por la composición equivalente con PyTorch/XAI, aunque
la ruta determinista ONNX aislada podría funcionar sin ese checkpoint.
No retiramos PyTorch/XAI para reducir artificialmente el costo del candidato.

## Dependencias del banco, distintas de un release de producto

El banco también llama `load_release()` antes de medir para verificar que
V3.1 permanece íntegra. Por ello el experimento necesita en disco los pesos,
manifiesto, métricas y CSV de referencia V3.1, incluso al evaluar C1. Además
verifica config/completion/manifiesto fuente/CSV de D y el protocolo registrado.
Esas lecturas de auditoría no cargan otro modelo residente. No se ha creado un
paquete independiente de servicio candidato ni probado su arranque fuera del
repositorio. Sería falso llamar al directorio experimental completo “modelo
listo para desplegar”.

Peso único accesible en disco por el harness, contando la referencia de auditoría:
V3.1=1683503 bytes; cada C1=3364830 bytes (su pareja de pesos más V3.1).
El experimento completo conserva las tres parejas y V3.1. No se usa ese inventario
de auditoría como tamaño intrínseco del candidato ni se oculta: la guarda B
registrada es sobre los pesos propios requeridos para inferencia/XAI equivalente.
El tamaño completo de un futuro release, sus metadatos y dependencias de
instalación requiere definir ese paquete en una fase autorizada de integración.

Los archivos de código compartido, dependencias instaladas y metadatos también
son necesarios. No son pesos: versiones en protocol.json; hashes de API,
arquitectura, entrada y adaptadores en registro y revisiones; manifiestos por
candidato en artifacts/. Datos originales/fixtures son entradas de prueba,
logs/CSV/figuras son investigación, no artefactos de un modelo desplegado.

## Memoria observada y límites de atribución

RSS después de imports ronda376MiB, PyTorch residente añade aproximadamente
2.3MiB y la sesión ORT inicializada lleva el proceso a385–386MiB, antes del
trabajo estable. Estos cambios son instantáneas del proceso, no asignaciones
exclusivas ni magnitudes sumables. Importar arquitectura también importa
bibliotecas que el producto usa. Las ocho instantáneas exactas están en
cost/run*/<modelo>/environment.json.

El pico posterior incluye inputs, preparación, buffers/arenas del runtime,
generación temporal de ruido, Python, cachés y memoria retenida por asignadores.
La guarda primaria usa ese proceso completo bajo la misma secuencia B. No se
ha separado causalmente la contribución de cada componente ni diagnosticado
por qué ciertos checkpoints requieren más RSS. No se atribuye la diferencia
al número de parámetros: todos tienen206875 y un grafo de igual tamaño.

Las mediciones HTTP mantienen ambos modos en un mismo proceso e incluyen
fixtures; su pico no permite estimar ahorro de RSS exclusivo de retirar ruido.
No extrapolar este Mac a dispositivos móviles o de bajos recursos.
