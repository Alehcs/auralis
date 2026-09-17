# Mapa de consumidores y promoción pendiente

La integración probada es del servicio HTTP. El dashboard aprobado y sus recursos
públicos siguen apuntando a V3.1. No se certifica que cambiar VITE_API_URL baste
para visualizar candidatos honestamente: varias etiquetas están fijadas a V3.1/MC.

| Consumidor | Dependencia real | Instancia candidata G | Trabajo futuro antes de promoción |
|---|---|---|---|
| API predict/alias/upload | `src/api/main.py`, sesión ONNX + checkpoint PyTorch | Artefacto seleccionado y validado; modelo/semilla/versión en respuesta, runtime/protocolo en cabeceras de prueba | Selección autorizada de un artefacto, manifiesto de release y decisión explícita sobre runtime |
| API health/logs/XAI | Clases y logger de main; checkpoint residente | Identidad propia; carga C1 p_backbone=0/p_head=.3; títulos XAI identifican el modelo | Mantener trazabilidad, revisar consumidores que ignoran metadata; no inferir validez XAI de una imagen |
| `/api/stats` | `active_model.load_release()` para V3.1; evidencia E/E1 para candidato | Métricas ONNX de esa semilla/runtime; sin ensemble. Histórico V3 permanece dentro de `historical_v3` | Revisar UI que actualmente interpreta campos superiores como MC20 |
| `/api/results-comparison` | CSV oficial MC/determinista V3.1; paridad E/E1 por C1 | Determinista devuelve263 puntos propios. MC candidato responde503 por recurso inexistente | Etiquetas/protocolo por artefacto; no crear MC candidato desde otras semillas |
| `/api/benchmark` | Benchmark histórico V3, split antiguo | Sigue explícitamente histórico V3; no se renombra C1 | Conservar histórico separado, no usarlo para aprobar promoción |
| Dashboard | `src/lib/api.ts`, `global-metrics.tsx`, `model-metrics.tsx`, `predicted-vs-actual.tsx`, `lib/types.ts` | No modificado ni certificado para C1. Tiene etiquetas V3.1/MC y MC por defecto | Cambios de texto/contratos y fallos de recurso compatibles autorizados en otra fase, sin alterar diseño |
| Agent Lab | `src/agents/data_loader.py`: `models/split_indices.json`, `reports/results_comparison.csv`, metadata |503 explícito en instancia candidata; no se relabelan datos legacy como C1 | Auditar/migrar join, split, protocolo, unidades y estados; comentarios actuales dicen log-SI/hold-out y requieren revisión científica separada |
| CLI `scripts/predict.py` | Checkpoint V3.1 por defecto, constructor dropout=.2 y etiquetas V3.1; flag `--model` manual | Variables G son API-only; CLI queda sin cambios y no se presenta como CLI C1 verificada | Parametrizar selección/configuración y etiquetas consistentemente antes de ofrecer C1; preservar herramientas MC |
| Herramientas MC | `train_model.py`, scripts de evaluación y registro activo | Intactas. No se sustituye MC por ruido ni se cambia dropout del checkpoint cargado para XAI | Evidencia específica si se desea otro protocolo; no extrapolar MC V3.1 a C1 |
| Gemelo/temporal | `reports/phase3_temporal_model/noaa12975.sequence.v1.json`, adaptadores Phase5–7 y manifests de assets | Estados congelados `coronium-3.1`, cinco predicciones originales; no regenerados | Nuevo contrato/versionado y recálculo solo si se autoriza; mantener estados/fechas/observación separados de recreación visual |
| Figuras/dossier/README público | Recursos aprobados y manifiestos históricos | Sin cambios. F es consulta experimental | Plan editorial posterior, sin sustituir evidencia histórica |

## Alcance de la identificación

La cabecera `X-Auralis-Model` identifica la instancia, no reclasifica el contenido
histórico de una respuesta. `evaluation_protocol`, `model_version` y los campos
históricos de cada recurso conservan su significado. La sensibilidad al ruido
permanece separada y no calibrada; la predicción puntual usa un forward eval.

## Pendientes científicos

Validation se usó para seleccionar checkpoint; no es test independiente/temporal.
C1 tolera deterioro en baja actividad y R² negativos en esa banda. La comprobación
funcional de Grad-CAM no resuelve borde/fondo ni causalidad. No hay rendimiento
móvil físico ni aprobación automática por una ronda favorable.
