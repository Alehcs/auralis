# G — controlled integration; registered before HTTP measurement

V3.1 remains active by default. Five arms, ten fresh processes, sequential rounds
with reversed arm order, specified in protocol.json. No candidate selection.

Actual API imports, actual lifespan, actual handlers. No AST-edited handler or
replacement lifespan. An isolated runner adds private observation/cache-reset
routes and a scalar wrapper around the loaded real ORT session, symmetrically.
The wrapper records the final full-precision output and forward count. Input
hashing is enabled only outside timing for fixtures. One PyTorch + one ORT model
remain resident. All twenty synthetic-noise passes and one deterministic pass
are retained in each uncached prediction; diagnostic is not MC Dropout.

CPU FP32 batch1,4 intra-op/1 inter-op,CPUExecutionProvider,ORT_SEQUENTIAL,
ORT_ENABLE_ALL. Original differs from mitigated solely in mlas.disable_kleidiai=1.
Native binary SHA/version must match E2 (which matches E1); option read-back and
process-memory observations complement existing native causal evidence.

E fixtures (11 cases,4formats),18 timing observations same order. Three cold
warmups,30 cold requests,18-cache priming,60 hot requests. Monotonic nanoseconds,
persistent loopback HTTP connection. No noise-free arm. Cold means empty result
cache, not cold weights/filesystem/connection. Each round keeps all results.

External5ms RSS starts at spawn: record entire process and separate timing,
fixtures and XAI stages. Single bounded Grad-CAM check after HTTP for each
mitigated instance; real explain handler, state/output invariance. No XAI sweep.
Maximum lifetime RSS is macOS bytes, conversionMiB=bytes/2^20. Neither monitors
nor off-process reporting are included in server RSS. Monitor observations are
not exclusive tensor memory. External process activity/pressure is recorded.

Formal B/E guards: weights<=+10%,parameters<512000,matched bank peakRSS<=+10%,
forward/preparation p50/p95<=+5%. Existing E1/E2 formal evidence is reused only
with matching artifact/runtime/threads. HTTP latency is an additional service
measurement; no new +5% HTTP approval threshold is invented. G HTTP RSS ratios
use symmetric G workloads as supplemental evidence, distinct from E1 formal bank
RSS. No compensation with removal of noise. Conflicting rounds remain inconclusive.

Default-control check starts real API without experimental environment and
verifies original registry/schemas/metrics/session options. Invalid configuration,
missing/corrupted artifacts and invalid requests must fail without substitution;
valid requests after request-level errors must recover. Clean shutdown includes
lifespan shutdown log, exited PID and closed bound port. Existing user services
are never stopped.
