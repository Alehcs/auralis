# V3.2-F — registered offline package protocol

Coronium V3.2 — candidatos. V3.1 remains active. No candidate selection or promotion.

Only saved B–E.2 evidence is consumed. No training, inference, export, benchmark,
new XAI, dependency change or public artifact replacement is permitted. All writes
are confined to this directory. Existing report/manifests and original observations
are hashed before consolidation; mismatches are reported rather than repaired.

Reuse the pure metrics and protection functions from B, figure export from the
existing scatter script, and architecture drawing primitives. Extract only those
functions through AST; never execute an experiment module or its main function.

Metrics use float64 parsed without presentation rounding, residual = prediction −
target, MAPE excludes zero targets, R² uses each group's mean, p95 uses NumPy's
linear quantile. Bands: low <1.41, medium [1.41,1.75), high >=1.75; tail SI>2 is a
subset of high. Source IDs, file names, target equality and split membership are
checked. Seed statistics summarize metrics with sample SD (ddof=1), not averaged
predictions. The same 263 selection-validation observations are not independent
between seeds. Train augmented/dropout curves are distinct from deterministic
train evaluation. C2 is preliminary seed42 only. MC20 is separate MPS protocol.

All saved rounds are retained. E default, E.1 default/mitigated and E.2 default/
mitigated are separate measurement cohorts. Mitigation is exactly the recorded
`mlas.disable_kleidiai=1`. No HTTP mitigation is inferred. Cost guards remain +5%
latency, +10% peak RSS and <512000 parameters. RSS describes the process, including
libraries and resident PyTorch/ONNX. Noise spread is not MC Dropout or calibrated
uncertainty. Mac results do not establish mobile performance.

Parity uses |ONNX−PT| <= 1e-5 + 1e-5*|PT|, separately for original and mitigated
runtime. Hashes and original full-precision predictions are the evidence, not
rounded public responses. XAI maps are reused at original orientation and [0,1]
normalization; HMI uses [-1,1]. No new masks or perturbations are computed.

Outputs: source inventory, metric/seed/curve/case/parity/cost/XAI tables, English
PNG (300 dpi)/SVG/PDF figures, provenance index, reproduction guide and report.
Visual inspection and source/protected-file checks are required for closure.
