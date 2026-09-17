# Scientific package index — Coronium V3.2 — candidatos

V3.1 remains active. All labels in figures are English. Source paths below resolve relative to `auralis-back/`. SHA-256 for every referenced source is in [index.json](index.json) and [sources.json](sources.json).

## Figure and table catalog

### [inventory](tables/inventory.csv)

Initial artifact audit and reuse classification.

**Limits:** Historical evidence is not pooled with new protocols.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (0):** 

### [predictions](tables/predictions.csv)

Unrounded source predictions; no ensemble.

**Limits:** Selection validation; not an independent test.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (29):** `experiments/v32c_seed42_v1/evaluation/C2/train.csv`; `experiments/v32c_seed42_v1/evaluation/C2/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/V3.1/train.csv`; `experiments/v32d_stability_v1/evaluation/V3.1/validation.csv`; `experiments/v32d_stability_v1/evaluation/constant/train.csv`; `experiments/v32d_stability_v1/evaluation/constant/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/strong_affine_train/train.csv`; `experiments/v32d_stability_v1/evaluation/strong_affine_train/validation.csv`; `experiments/v32d_stability_v1/evaluation/strong_raw/train.csv`; `experiments/v32d_stability_v1/evaluation/strong_raw/validation.csv`; `reports/phase17_coronium_v3_1/analysis_v2/predictions.csv`

### [metrics](tables/metrics.csv)

Float64 metrics by partition and overlapping tail.

**Limits:** Selection validation; not an independent test.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (29):** `experiments/v32c_seed42_v1/evaluation/C2/train.csv`; `experiments/v32c_seed42_v1/evaluation/C2/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/V3.1/train.csv`; `experiments/v32d_stability_v1/evaluation/V3.1/validation.csv`; `experiments/v32d_stability_v1/evaluation/constant/train.csv`; `experiments/v32d_stability_v1/evaluation/constant/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/strong_affine_train/train.csv`; `experiments/v32d_stability_v1/evaluation/strong_affine_train/validation.csv`; `experiments/v32d_stability_v1/evaluation/strong_raw/train.csv`; `experiments/v32d_stability_v1/evaluation/strong_raw/validation.csv`; `reports/phase17_coronium_v3_1/analysis_v2/predictions.csv`

### [metric_reconciliation](tables/metric_reconciliation.csv)

Recalculation versus saved C/D metrics; absolute differences.

**Limits:** Tolerance 1e-11; no evidence overwritten.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (29):** `experiments/v32c_seed42_v1/evaluation/C2/train.csv`; `experiments/v32c_seed42_v1/evaluation/C2/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/V3.1/train.csv`; `experiments/v32d_stability_v1/evaluation/V3.1/validation.csv`; `experiments/v32d_stability_v1/evaluation/constant/train.csv`; `experiments/v32d_stability_v1/evaluation/constant/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/strong_affine_train/train.csv`; `experiments/v32d_stability_v1/evaluation/strong_affine_train/validation.csv`; `experiments/v32d_stability_v1/evaluation/strong_raw/train.csv`; `experiments/v32d_stability_v1/evaluation/strong_raw/validation.csv`; `reports/phase17_coronium_v3_1/analysis_v2/predictions.csv`

### [seed_statistics](tables/seed_statistics.csv)

Mean, sample SD and range of metrics across three seeds.

**Limits:** 263 shared validation observations, not 789 independent samples; mean is not a model.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (29):** `experiments/v32c_seed42_v1/evaluation/C2/train.csv`; `experiments/v32c_seed42_v1/evaluation/C2/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/V3.1/train.csv`; `experiments/v32d_stability_v1/evaluation/V3.1/validation.csv`; `experiments/v32d_stability_v1/evaluation/constant/train.csv`; `experiments/v32d_stability_v1/evaluation/constant/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/strong_affine_train/train.csv`; `experiments/v32d_stability_v1/evaluation/strong_affine_train/validation.csv`; `experiments/v32d_stability_v1/evaluation/strong_raw/train.csv`; `experiments/v32d_stability_v1/evaluation/strong_raw/validation.csv`; `reports/phase17_coronium_v3_1/analysis_v2/predictions.csv`

### [worst_cases](tables/worst_cases.csv)

Ten largest absolute errors per model/reference, including unfavorable cases.

**Limits:** Selection validation; not an independent test.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (29):** `experiments/v32c_seed42_v1/evaluation/C2/train.csv`; `experiments/v32c_seed42_v1/evaluation/C2/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/V3.1/train.csv`; `experiments/v32d_stability_v1/evaluation/V3.1/validation.csv`; `experiments/v32d_stability_v1/evaluation/constant/train.csv`; `experiments/v32d_stability_v1/evaluation/constant/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/strong_affine_train/train.csv`; `experiments/v32d_stability_v1/evaluation/strong_affine_train/validation.csv`; `experiments/v32d_stability_v1/evaluation/strong_raw/train.csv`; `experiments/v32d_stability_v1/evaluation/strong_raw/validation.csv`; `reports/phase17_coronium_v3_1/analysis_v2/predictions.csv`

### [training_curves](tables/training_curves.csv)

All epochs; selection markers taken from frozen completion manifests.

**Limits:** MPS training curves use augmentation/dropout; CPU deterministic train/validation table is a separate protocol.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (21):** `experiments/v32c_seed42_v1/C0/completion.json`; `experiments/v32c_seed42_v1/C0/config.json`; `experiments/v32c_seed42_v1/C0/history.jsonl`; `experiments/v32c_seed42_v1/C1/completion.json`; `experiments/v32c_seed42_v1/C1/config.json`; `experiments/v32c_seed42_v1/C1/history.jsonl`; `experiments/v32c_seed42_v1/C2/completion.json`; `experiments/v32c_seed42_v1/C2/config.json`; `experiments/v32c_seed42_v1/C2/history.jsonl`; `experiments/v32d_stability_v1/seed137/C0/completion.json`; `experiments/v32d_stability_v1/seed137/C0/config.json`; `experiments/v32d_stability_v1/seed137/C0/history.jsonl`; `experiments/v32d_stability_v1/seed137/C1/completion.json`; `experiments/v32d_stability_v1/seed137/C1/config.json`; `experiments/v32d_stability_v1/seed137/C1/history.jsonl`; `experiments/v32d_stability_v1/seed2026/C0/completion.json`; `experiments/v32d_stability_v1/seed2026/C0/config.json`; `experiments/v32d_stability_v1/seed2026/C0/history.jsonl`; `experiments/v32d_stability_v1/seed2026/C1/completion.json`; `experiments/v32d_stability_v1/seed2026/C1/config.json`; `experiments/v32d_stability_v1/seed2026/C1/history.jsonl`

### [parity_observations](tables/parity_observations.csv)

Original and mitigated saved PT/ONNX predictions; combined atol/rtol.

**Limits:** Selection validation; not an independent test.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (8):** `experiments/v32e1_memory_diagnostic_v1/parity/C1_s137.csv`; `experiments/v32e1_memory_diagnostic_v1/parity/C1_s2026.csv`; `experiments/v32e1_memory_diagnostic_v1/parity/C1_s42.csv`; `experiments/v32e1_memory_diagnostic_v1/parity/V3.1.csv`; `experiments/v32e_onnx_cost_v1/parity/C1_s137.csv`; `experiments/v32e_onnx_cost_v1/parity/C1_s2026.csv`; `experiments/v32e_onnx_cost_v1/parity/C1_s42.csv`; `experiments/v32e_onnx_cost_v1/parity/V3.1.csv`

### [parity_summary](tables/parity_summary.csv)

All 263 cases per model/configuration; no rounded-response comparison.

**Limits:** Selection validation; not an independent test.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (8):** `experiments/v32e1_memory_diagnostic_v1/parity/C1_s137.csv`; `experiments/v32e1_memory_diagnostic_v1/parity/C1_s2026.csv`; `experiments/v32e1_memory_diagnostic_v1/parity/C1_s42.csv`; `experiments/v32e1_memory_diagnostic_v1/parity/V3.1.csv`; `experiments/v32e_onnx_cost_v1/parity/C1_s137.csv`; `experiments/v32e_onnx_cost_v1/parity/C1_s2026.csv`; `experiments/v32e_onnx_cost_v1/parity/C1_s42.csv`; `experiments/v32e_onnx_cost_v1/parity/V3.1.csv`

### [latency_individual](tables/latency_individual.csv)

All recorded individual timings; no rounds discarded.

**Limits:** Cohorts/workloads differ; do not pool E/E1/E2.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (41):** `experiments/v32e1_memory_diagnostic_v1/cost_summary.csv`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/V3.1/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/V3.1/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/V3.1/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/V3.1/cost.json`; `experiments/v32e2_latency_v1/runs/round1/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round1/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round1/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round1/D/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/D/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/D/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/D/timings.csv`; `experiments/v32e_onnx_cost_v1/cost/run1/C1_s137/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run1/C1_s2026/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run1/C1_s42/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run1/V3.1/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/C1_s137/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/C1_s2026/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/C1_s42/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/V3.1/cost.json`

### [latency_summary](tables/latency_summary.csv)

p50/p95 recomputed separately for every round and route.

**Limits:** Milliseconds; CPU Mac M5, batch1, 4/1 threads; service keeps PyTorch resident.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (41):** `experiments/v32e1_memory_diagnostic_v1/cost_summary.csv`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/V3.1/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/V3.1/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/V3.1/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/V3.1/cost.json`; `experiments/v32e2_latency_v1/runs/round1/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round1/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round1/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round1/D/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/D/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/D/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/D/timings.csv`; `experiments/v32e_onnx_cost_v1/cost/run1/C1_s137/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run1/C1_s2026/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run1/C1_s42/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run1/V3.1/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/C1_s137/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/C1_s2026/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/C1_s42/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/V3.1/cost.json`

### [memory](tables/memory.csv)

Process RSS by original/mitigated configuration and cohort.

**Limits:** RSS includes libraries, resident models and temporaries; not tensor/model size.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (41):** `experiments/v32e1_memory_diagnostic_v1/cost_summary.csv`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/V3.1/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/V3.1/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/V3.1/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/V3.1/cost.json`; `experiments/v32e2_latency_v1/runs/round1/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round1/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round1/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round1/D/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/D/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/D/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/D/timings.csv`; `experiments/v32e_onnx_cost_v1/cost/run1/C1_s137/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run1/C1_s2026/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run1/C1_s42/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run1/V3.1/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/C1_s137/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/C1_s2026/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/C1_s42/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/V3.1/cost.json`

### [http_individual](tables/http_individual.csv)

Saved loopback HTTP, original runtime only.

**Limits:** Noise diagnostic is uncalibrated input perturbation, not MC Dropout.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (8):** `experiments/v32e_onnx_cost_v1/http/run1/C1_s137/http.json`; `experiments/v32e_onnx_cost_v1/http/run1/C1_s2026/http.json`; `experiments/v32e_onnx_cost_v1/http/run1/C1_s42/http.json`; `experiments/v32e_onnx_cost_v1/http/run1/V3.1/http.json`; `experiments/v32e_onnx_cost_v1/http/run2/C1_s137/http.json`; `experiments/v32e_onnx_cost_v1/http/run2/C1_s2026/http.json`; `experiments/v32e_onnx_cost_v1/http/run2/C1_s42/http.json`; `experiments/v32e_onnx_cost_v1/http/run2/V3.1/http.json`

### [http_summary](tables/http_summary.csv)

Cold/hot result-cache p50/p95, all rounds.

**Limits:** Model, filesystem and connection warm. Hot result cache performs no forward. Omitted diagnostic is not calculated, not zero.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (8):** `experiments/v32e_onnx_cost_v1/http/run1/C1_s137/http.json`; `experiments/v32e_onnx_cost_v1/http/run1/C1_s2026/http.json`; `experiments/v32e_onnx_cost_v1/http/run1/C1_s42/http.json`; `experiments/v32e_onnx_cost_v1/http/run1/V3.1/http.json`; `experiments/v32e_onnx_cost_v1/http/run2/C1_s137/http.json`; `experiments/v32e_onnx_cost_v1/http/run2/C1_s2026/http.json`; `experiments/v32e_onnx_cost_v1/http/run2/C1_s42/http.json`; `experiments/v32e_onnx_cost_v1/http/run2/V3.1/http.json`

### [e2_comparisons](tables/e2_comparisons.csv)

Model, runtime and complete deployment effects, all four rounds.

**Limits:** +5% guard; mixed passes/failures remain inconclusive.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (1):** `experiments/v32e2_latency_v1/comparisons.csv`

### [e2_verdicts](tables/e2_verdicts.csv)

Saved four-round verdicts; no favorable-round selection.

**Limits:** Selection validation; not an independent test.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (1):** `experiments/v32e2_latency_v1/verdicts.csv`

### [serving_sizes](tables/serving_sizes.csv)

Complete self-contained ONNX plus checkpoint for equivalent service.

**Limits:** Weights bytes exclude environment/libraries and research logs. C0/C2 serving costs not measured.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (2):** `experiments/v32e1_memory_diagnostic_v1/cost_summary.csv`; `experiments/v32e_onnx_cost_v1/SERVING_SCOPE.md`

### [xai_occlusions](tables/xai_occlusions.csv)

Saved XAI controls, unchanged masks, normalization and sample selection.

**Limits:** Structured untrained maps and magnetic-magnitude removal confound visual plausibility; border/background questions remain.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (11):** `experiments/v32d_stability_v1/xai/C0_s137/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/C0_s2026/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/C0_s42/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/C1_s137/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/C1_s2026/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/C1_s42/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/initial_s137/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/initial_s2026/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/initial_s42/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/map_comparison.csv`; `experiments/v32d_stability_v1/xai/square_effects.csv`

### [xai_effects](tables/xai_effects.csv)

Saved XAI controls, unchanged masks, normalization and sample selection.

**Limits:** Structured untrained maps and magnetic-magnitude removal confound visual plausibility; border/background questions remain.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (11):** `experiments/v32d_stability_v1/xai/C0_s137/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/C0_s2026/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/C0_s42/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/C1_s137/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/C1_s2026/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/C1_s42/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/initial_s137/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/initial_s2026/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/initial_s42/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/map_comparison.csv`; `experiments/v32d_stability_v1/xai/square_effects.csv`

### [xai_map_comparisons](tables/xai_map_comparisons.csv)

Saved XAI controls, unchanged masks, normalization and sample selection.

**Limits:** Structured untrained maps and magnetic-magnitude removal confound visual plausibility; border/background questions remain.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (11):** `experiments/v32d_stability_v1/xai/C0_s137/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/C0_s2026/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/C0_s42/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/C1_s137/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/C1_s2026/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/C1_s42/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/initial_s137/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/initial_s2026/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/initial_s42/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/map_comparison.csv`; `experiments/v32d_stability_v1/xai/square_effects.csv`

### [01_training](figures/01_training.png)

Selected epochs are frozen; all epochs retained.

**Limits:** Train augmentation/dropout and validation eval are different protocols; selection validation.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (21):** `experiments/v32c_seed42_v1/C0/completion.json`; `experiments/v32c_seed42_v1/C0/config.json`; `experiments/v32c_seed42_v1/C0/history.jsonl`; `experiments/v32c_seed42_v1/C1/completion.json`; `experiments/v32c_seed42_v1/C1/config.json`; `experiments/v32c_seed42_v1/C1/history.jsonl`; `experiments/v32c_seed42_v1/C2/completion.json`; `experiments/v32c_seed42_v1/C2/config.json`; `experiments/v32c_seed42_v1/C2/history.jsonl`; `experiments/v32d_stability_v1/seed137/C0/completion.json`; `experiments/v32d_stability_v1/seed137/C0/config.json`; `experiments/v32d_stability_v1/seed137/C0/history.jsonl`; `experiments/v32d_stability_v1/seed137/C1/completion.json`; `experiments/v32d_stability_v1/seed137/C1/config.json`; `experiments/v32d_stability_v1/seed137/C1/history.jsonl`; `experiments/v32d_stability_v1/seed2026/C0/completion.json`; `experiments/v32d_stability_v1/seed2026/C0/config.json`; `experiments/v32d_stability_v1/seed2026/C0/history.jsonl`; `experiments/v32d_stability_v1/seed2026/C1/completion.json`; `experiments/v32d_stability_v1/seed2026/C1/config.json`; `experiments/v32d_stability_v1/seed2026/C1/history.jsonl`

### [02_seed_stability](figures/02_seed_stability.png)

Individual seeds and metric mean/sample SD; no ensemble.

**Limits:** Selection validation (n=263); candidates, not promoted

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (29):** `experiments/v32c_seed42_v1/evaluation/C2/train.csv`; `experiments/v32c_seed42_v1/evaluation/C2/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/V3.1/train.csv`; `experiments/v32d_stability_v1/evaluation/V3.1/validation.csv`; `experiments/v32d_stability_v1/evaluation/constant/train.csv`; `experiments/v32d_stability_v1/evaluation/constant/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/strong_affine_train/train.csv`; `experiments/v32d_stability_v1/evaluation/strong_affine_train/validation.csv`; `experiments/v32d_stability_v1/evaluation/strong_raw/train.csv`; `experiments/v32d_stability_v1/evaluation/strong_raw/validation.csv`; `reports/phase17_coronium_v3_1/analysis_v2/predictions.csv`

### [03_references](figures/03_references.png)

Raw proxy is not the original-resolution target; affine calibration fit on train only.

**Limits:** Selection validation (n=263); candidates, not promoted

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (29):** `experiments/v32c_seed42_v1/evaluation/C2/train.csv`; `experiments/v32c_seed42_v1/evaluation/C2/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/V3.1/train.csv`; `experiments/v32d_stability_v1/evaluation/V3.1/validation.csv`; `experiments/v32d_stability_v1/evaluation/constant/train.csv`; `experiments/v32d_stability_v1/evaluation/constant/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/strong_affine_train/train.csv`; `experiments/v32d_stability_v1/evaluation/strong_affine_train/validation.csv`; `experiments/v32d_stability_v1/evaluation/strong_raw/train.csv`; `experiments/v32d_stability_v1/evaluation/strong_raw/validation.csv`; `reports/phase17_coronium_v3_1/analysis_v2/predictions.csv`

### [04_scatter_candidates](figures/04_scatter_candidates.png)

Identity line; no points omitted. Same limits in candidate/reference panels.

**Limits:** Selection validation (n=263); candidates, not promoted

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (29):** `experiments/v32c_seed42_v1/evaluation/C2/train.csv`; `experiments/v32c_seed42_v1/evaluation/C2/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/V3.1/train.csv`; `experiments/v32d_stability_v1/evaluation/V3.1/validation.csv`; `experiments/v32d_stability_v1/evaluation/constant/train.csv`; `experiments/v32d_stability_v1/evaluation/constant/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/strong_affine_train/train.csv`; `experiments/v32d_stability_v1/evaluation/strong_affine_train/validation.csv`; `experiments/v32d_stability_v1/evaluation/strong_raw/train.csv`; `experiments/v32d_stability_v1/evaluation/strong_raw/validation.csv`; `reports/phase17_coronium_v3_1/analysis_v2/predictions.csv`

### [05_scatter_references](figures/05_scatter_references.png)

Identity line; no points omitted. Same limits in candidate/reference panels.

**Limits:** Selection validation (n=263); candidates, not promoted

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (29):** `experiments/v32c_seed42_v1/evaluation/C2/train.csv`; `experiments/v32c_seed42_v1/evaluation/C2/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/V3.1/train.csv`; `experiments/v32d_stability_v1/evaluation/V3.1/validation.csv`; `experiments/v32d_stability_v1/evaluation/constant/train.csv`; `experiments/v32d_stability_v1/evaluation/constant/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/strong_affine_train/train.csv`; `experiments/v32d_stability_v1/evaluation/strong_affine_train/validation.csv`; `experiments/v32d_stability_v1/evaluation/strong_raw/train.csv`; `experiments/v32d_stability_v1/evaluation/strong_raw/validation.csv`; `reports/phase17_coronium_v3_1/analysis_v2/predictions.csv`

### [06_residuals](figures/06_residuals.png)

Residual sign is prediction − SI; all cases retained.

**Limits:** Selection validation (n=263); candidates, not promoted

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (29):** `experiments/v32c_seed42_v1/evaluation/C2/train.csv`; `experiments/v32c_seed42_v1/evaluation/C2/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/V3.1/train.csv`; `experiments/v32d_stability_v1/evaluation/V3.1/validation.csv`; `experiments/v32d_stability_v1/evaluation/constant/train.csv`; `experiments/v32d_stability_v1/evaluation/constant/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/strong_affine_train/train.csv`; `experiments/v32d_stability_v1/evaluation/strong_affine_train/validation.csv`; `experiments/v32d_stability_v1/evaluation/strong_raw/train.csv`; `experiments/v32d_stability_v1/evaluation/strong_raw/validation.csv`; `reports/phase17_coronium_v3_1/analysis_v2/predictions.csv`

### [07_bands_tail](figures/07_bands_tail.png)

Negative low-band R² and low-band deterioration remain visible.

**Limits:** Selection validation (n=263); candidates, not promoted

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (29):** `experiments/v32c_seed42_v1/evaluation/C2/train.csv`; `experiments/v32c_seed42_v1/evaluation/C2/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/V3.1/train.csv`; `experiments/v32d_stability_v1/evaluation/V3.1/validation.csv`; `experiments/v32d_stability_v1/evaluation/constant/train.csv`; `experiments/v32d_stability_v1/evaluation/constant/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/strong_affine_train/train.csv`; `experiments/v32d_stability_v1/evaluation/strong_affine_train/validation.csv`; `experiments/v32d_stability_v1/evaluation/strong_raw/train.csv`; `experiments/v32d_stability_v1/evaluation/strong_raw/validation.csv`; `reports/phase17_coronium_v3_1/analysis_v2/predictions.csv`

### [08_train_validation](figures/08_train_validation.png)

Same evaluation protocol; not the stochastic training curves.

**Limits:** Selection validation (n=263); candidates, not promoted

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (29):** `experiments/v32c_seed42_v1/evaluation/C2/train.csv`; `experiments/v32c_seed42_v1/evaluation/C2/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/V3.1/train.csv`; `experiments/v32d_stability_v1/evaluation/V3.1/validation.csv`; `experiments/v32d_stability_v1/evaluation/constant/train.csv`; `experiments/v32d_stability_v1/evaluation/constant/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/strong_affine_train/train.csv`; `experiments/v32d_stability_v1/evaluation/strong_affine_train/validation.csv`; `experiments/v32d_stability_v1/evaluation/strong_raw/train.csv`; `experiments/v32d_stability_v1/evaluation/strong_raw/validation.csv`; `reports/phase17_coronium_v3_1/analysis_v2/predictions.csv`

### [09_largest_errors](figures/09_largest_errors.png)

Original stored magnetograms, fixed [-1,1] scale; no new XAI.

**Limits:** Displayed SI values rounded only for labels; full precision in worst_cases.csv.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (36):** `data/processed/hmi.m_45s.2016.11.29_00_01_30_TAI.magnetogram_processed.npy`; `data/processed/hmi.m_45s.2016.12.15_00_01_30_TAI.magnetogram_processed.npy`; `data/processed/hmi.m_45s.2021.11.06_00_01_30_TAI.magnetogram_processed.npy`; `data/processed/hmi.m_45s.2024.02.20_00_01_30_TAI.magnetogram_processed.npy`; `data/processed/hmi.m_45s.2024.02.23_00_01_30_TAI.magnetogram_processed.npy`; `data/processed/hmi.m_45s.2025.02.06_00_01_30_TAI.magnetogram_processed.npy`; `data/processed/hmi.m_45s.2025.02.22_00_01_30_TAI.magnetogram_processed.npy`; `experiments/v32c_seed42_v1/evaluation/C2/train.csv`; `experiments/v32c_seed42_v1/evaluation/C2/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/C0_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/C0_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/C1_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/C1_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/V3.1/train.csv`; `experiments/v32d_stability_v1/evaluation/V3.1/validation.csv`; `experiments/v32d_stability_v1/evaluation/constant/train.csv`; `experiments/v32d_stability_v1/evaluation/constant/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s137/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s137/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s2026/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s2026/validation.csv`; `experiments/v32d_stability_v1/evaluation/initial_s42/train.csv`; `experiments/v32d_stability_v1/evaluation/initial_s42/validation.csv`; `experiments/v32d_stability_v1/evaluation/strong_affine_train/train.csv`; `experiments/v32d_stability_v1/evaluation/strong_affine_train/validation.csv`; `experiments/v32d_stability_v1/evaluation/strong_raw/train.csv`; `experiments/v32d_stability_v1/evaluation/strong_raw/validation.csv`; `reports/phase17_coronium_v3_1/analysis_v2/predictions.csv`

### [10_parity](figures/10_parity.png)

Combined tolerance is the pass criterion; max absolute differences retained in table.

**Limits:** 263 saved observations per model/configuration; no fresh inference.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (8):** `experiments/v32e1_memory_diagnostic_v1/parity/C1_s137.csv`; `experiments/v32e1_memory_diagnostic_v1/parity/C1_s2026.csv`; `experiments/v32e1_memory_diagnostic_v1/parity/C1_s42.csv`; `experiments/v32e1_memory_diagnostic_v1/parity/V3.1.csv`; `experiments/v32e_onnx_cost_v1/parity/C1_s137.csv`; `experiments/v32e_onnx_cost_v1/parity/C1_s2026.csv`; `experiments/v32e_onnx_cost_v1/parity/C1_s42.csv`; `experiments/v32e_onnx_cost_v1/parity/V3.1.csv`

### [11_memory](figures/11_memory.png)

Mitigation benefits reference and candidates; E/E1 measurement definitions are retained separately.

**Limits:** Both PyTorch and ONNX resident; mixed workload includes noise diagnostic. Mac M5 only.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (41):** `experiments/v32e1_memory_diagnostic_v1/cost_summary.csv`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/V3.1/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/V3.1/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/V3.1/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/V3.1/cost.json`; `experiments/v32e2_latency_v1/runs/round1/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round1/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round1/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round1/D/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/D/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/D/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/D/timings.csv`; `experiments/v32e_onnx_cost_v1/cost/run1/C1_s137/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run1/C1_s2026/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run1/C1_s42/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run1/V3.1/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/C1_s137/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/C1_s2026/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/C1_s42/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/V3.1/cost.json`

### [12_e1_latency](figures/12_e1_latency.png)

No compensation of a model cost failure by omitting noise.

**Limits:** E.1 cohort; p50 and individual measurements in tables. CPU Mac M5 only.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (41):** `experiments/v32e1_memory_diagnostic_v1/cost_summary.csv`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/V3.1/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/V3.1/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/V3.1/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/V3.1/cost.json`; `experiments/v32e2_latency_v1/runs/round1/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round1/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round1/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round1/D/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/D/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/D/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/D/timings.csv`; `experiments/v32e_onnx_cost_v1/cost/run1/C1_s137/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run1/C1_s2026/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run1/C1_s42/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run1/V3.1/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/C1_s137/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/C1_s2026/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/C1_s42/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/V3.1/cost.json`

### [13_e2_latency_effects](figures/13_e2_latency_effects.png)

All four rounds; mitigated comparison passes, original p95 remains inconclusive.

**Limits:** 216 timings/route/arm/round; 10 warmups. No HTTP or noise in timed forward routes.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (42):** `experiments/v32e1_memory_diagnostic_v1/cost_summary.csv`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/V3.1/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/V3.1/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/V3.1/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/V3.1/cost.json`; `experiments/v32e2_latency_v1/comparisons.csv`; `experiments/v32e2_latency_v1/runs/round1/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round1/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round1/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round1/D/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/D/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/D/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/D/timings.csv`; `experiments/v32e_onnx_cost_v1/cost/run1/C1_s137/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run1/C1_s2026/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run1/C1_s42/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run1/V3.1/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/C1_s137/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/C1_s2026/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/C1_s42/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/V3.1/cost.json`

### [14_http_original](figures/14_http_original.png)

Same model with/without noise diagnostic; result-cache hits make no inference.

**Limits:** Model, filesystem and connection warm; no_noise diagnostic not calculated. Not MC Dropout.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (8):** `experiments/v32e_onnx_cost_v1/http/run1/C1_s137/http.json`; `experiments/v32e_onnx_cost_v1/http/run1/C1_s2026/http.json`; `experiments/v32e_onnx_cost_v1/http/run1/C1_s42/http.json`; `experiments/v32e_onnx_cost_v1/http/run1/V3.1/http.json`; `experiments/v32e_onnx_cost_v1/http/run2/C1_s137/http.json`; `experiments/v32e_onnx_cost_v1/http/run2/C1_s2026/http.json`; `experiments/v32e_onnx_cost_v1/http/run2/C1_s42/http.json`; `experiments/v32e_onnx_cost_v1/http/run2/V3.1/http.json`

### [15_sizes](figures/15_sizes.png)

Self-contained ONNX; checkpoint remains for equivalent PyTorch/XAI service.

**Limits:** Environment libraries and research logs are not included in weight bytes.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (41):** `experiments/v32e1_memory_diagnostic_v1/cost_summary.csv`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/V3.1/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/V3.1/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/V3.1/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/V3.1/cost.json`; `experiments/v32e2_latency_v1/runs/round1/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round1/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round1/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round1/D/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/D/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/D/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/D/timings.csv`; `experiments/v32e_onnx_cost_v1/cost/run1/C1_s137/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run1/C1_s2026/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run1/C1_s42/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run1/V3.1/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/C1_s137/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/C1_s2026/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/C1_s42/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/V3.1/cost.json`

### [16_architecture](figures/16_architecture.png)

Same structural backbone as V3.1/C0; changed backbone dropout probability only.

**Limits:** Input: clip400 B+/B−. Output: original SI percentage points. Stage dimensions are before pooling.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (23):** `experiments/v32c_seed42_v1/C0/completion.json`; `experiments/v32c_seed42_v1/C0/config.json`; `experiments/v32c_seed42_v1/C0/history.jsonl`; `experiments/v32c_seed42_v1/C1/completion.json`; `experiments/v32c_seed42_v1/C1/config.json`; `experiments/v32c_seed42_v1/C1/history.jsonl`; `experiments/v32c_seed42_v1/C2/completion.json`; `experiments/v32c_seed42_v1/C2/config.json`; `experiments/v32c_seed42_v1/C2/history.jsonl`; `experiments/v32d_stability_v1/seed137/C0/completion.json`; `experiments/v32d_stability_v1/seed137/C0/config.json`; `experiments/v32d_stability_v1/seed137/C0/history.jsonl`; `experiments/v32d_stability_v1/seed137/C1/completion.json`; `experiments/v32d_stability_v1/seed137/C1/config.json`; `experiments/v32d_stability_v1/seed137/C1/history.jsonl`; `experiments/v32d_stability_v1/seed2026/C0/completion.json`; `experiments/v32d_stability_v1/seed2026/C0/config.json`; `experiments/v32d_stability_v1/seed2026/C0/history.jsonl`; `experiments/v32d_stability_v1/seed2026/C1/completion.json`; `experiments/v32d_stability_v1/seed2026/C1/config.json`; `experiments/v32d_stability_v1/seed2026/C1/history.jsonl`; `scripts/plot_architecture_diagram.py`; `src/models/train_model.py`

### [17_xai_s42_low](figures/17_xai_s42_low.png)

All fixed D samples, original normalization/orientation; untrained control retained.

**Limits:** Per-map normalized activation is not probability, area or physical localization; edge/background concerns remain.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (13):** `data/processed/hmi.m_45s.2016.06.05_00_01_30_TAI.magnetogram_processed.npy`; `data/processed/hmi.m_45s.2016.11.12_00_01_30_TAI.magnetogram_processed.npy`; `data/processed/hmi.m_45s.2017.07.06_00_01_30_TAI.magnetogram_processed.npy`; `experiments/v32d_stability_v1/protocol.json`; `experiments/v32d_stability_v1/xai/C0_s42/148-gradcam.npy`; `experiments/v32d_stability_v1/xai/C0_s42/284-gradcam.npy`; `experiments/v32d_stability_v1/xai/C0_s42/68-gradcam.npy`; `experiments/v32d_stability_v1/xai/C1_s42/148-gradcam.npy`; `experiments/v32d_stability_v1/xai/C1_s42/284-gradcam.npy`; `experiments/v32d_stability_v1/xai/C1_s42/68-gradcam.npy`; `experiments/v32d_stability_v1/xai/initial_s42/148-gradcam.npy`; `experiments/v32d_stability_v1/xai/initial_s42/284-gradcam.npy`; `experiments/v32d_stability_v1/xai/initial_s42/68-gradcam.npy`

### [17_xai_s42_medium](figures/17_xai_s42_medium.png)

All fixed D samples, original normalization/orientation; untrained control retained.

**Limits:** Per-map normalized activation is not probability, area or physical localization; edge/background concerns remain.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (13):** `data/processed/hmi.m_45s.2017.03.30_00_01_30_TAI.magnetogram_processed.npy`; `data/processed/hmi.m_45s.2021.10.09_00_01_30_TAI.magnetogram_processed.npy`; `data/processed/hmi.m_45s.2022.05.31_00_01_30_TAI.magnetogram_processed.npy`; `experiments/v32d_stability_v1/protocol.json`; `experiments/v32d_stability_v1/xai/C0_s42/230-gradcam.npy`; `experiments/v32d_stability_v1/xai/C0_s42/719-gradcam.npy`; `experiments/v32d_stability_v1/xai/C0_s42/848-gradcam.npy`; `experiments/v32d_stability_v1/xai/C1_s42/230-gradcam.npy`; `experiments/v32d_stability_v1/xai/C1_s42/719-gradcam.npy`; `experiments/v32d_stability_v1/xai/C1_s42/848-gradcam.npy`; `experiments/v32d_stability_v1/xai/initial_s42/230-gradcam.npy`; `experiments/v32d_stability_v1/xai/initial_s42/719-gradcam.npy`; `experiments/v32d_stability_v1/xai/initial_s42/848-gradcam.npy`

### [17_xai_s42_high](figures/17_xai_s42_high.png)

All fixed D samples, original normalization/orientation; untrained control retained.

**Limits:** Per-map normalized activation is not probability, area or physical localization; edge/background concerns remain.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (13):** `data/processed/hmi.m_45s.2022.08.10_00_01_30_TAI.magnetogram_processed.npy`; `data/processed/hmi.m_45s.2024.08.09_00_01_30_TAI.magnetogram_processed.npy`; `data/processed/hmi.m_45s.2025.11.08_00_01_30_TAI.magnetogram_processed.npy`; `experiments/v32d_stability_v1/protocol.json`; `experiments/v32d_stability_v1/xai/C0_s42/1312-gradcam.npy`; `experiments/v32d_stability_v1/xai/C0_s42/1645-gradcam.npy`; `experiments/v32d_stability_v1/xai/C0_s42/885-gradcam.npy`; `experiments/v32d_stability_v1/xai/C1_s42/1312-gradcam.npy`; `experiments/v32d_stability_v1/xai/C1_s42/1645-gradcam.npy`; `experiments/v32d_stability_v1/xai/C1_s42/885-gradcam.npy`; `experiments/v32d_stability_v1/xai/initial_s42/1312-gradcam.npy`; `experiments/v32d_stability_v1/xai/initial_s42/1645-gradcam.npy`; `experiments/v32d_stability_v1/xai/initial_s42/885-gradcam.npy`

### [17_xai_s137_low](figures/17_xai_s137_low.png)

All fixed D samples, original normalization/orientation; untrained control retained.

**Limits:** Per-map normalized activation is not probability, area or physical localization; edge/background concerns remain.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (13):** `data/processed/hmi.m_45s.2016.06.05_00_01_30_TAI.magnetogram_processed.npy`; `data/processed/hmi.m_45s.2016.11.12_00_01_30_TAI.magnetogram_processed.npy`; `data/processed/hmi.m_45s.2017.07.06_00_01_30_TAI.magnetogram_processed.npy`; `experiments/v32d_stability_v1/protocol.json`; `experiments/v32d_stability_v1/xai/C0_s137/148-gradcam.npy`; `experiments/v32d_stability_v1/xai/C0_s137/284-gradcam.npy`; `experiments/v32d_stability_v1/xai/C0_s137/68-gradcam.npy`; `experiments/v32d_stability_v1/xai/C1_s137/148-gradcam.npy`; `experiments/v32d_stability_v1/xai/C1_s137/284-gradcam.npy`; `experiments/v32d_stability_v1/xai/C1_s137/68-gradcam.npy`; `experiments/v32d_stability_v1/xai/initial_s137/148-gradcam.npy`; `experiments/v32d_stability_v1/xai/initial_s137/284-gradcam.npy`; `experiments/v32d_stability_v1/xai/initial_s137/68-gradcam.npy`

### [17_xai_s137_medium](figures/17_xai_s137_medium.png)

All fixed D samples, original normalization/orientation; untrained control retained.

**Limits:** Per-map normalized activation is not probability, area or physical localization; edge/background concerns remain.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (13):** `data/processed/hmi.m_45s.2017.03.30_00_01_30_TAI.magnetogram_processed.npy`; `data/processed/hmi.m_45s.2021.10.09_00_01_30_TAI.magnetogram_processed.npy`; `data/processed/hmi.m_45s.2022.05.31_00_01_30_TAI.magnetogram_processed.npy`; `experiments/v32d_stability_v1/protocol.json`; `experiments/v32d_stability_v1/xai/C0_s137/230-gradcam.npy`; `experiments/v32d_stability_v1/xai/C0_s137/719-gradcam.npy`; `experiments/v32d_stability_v1/xai/C0_s137/848-gradcam.npy`; `experiments/v32d_stability_v1/xai/C1_s137/230-gradcam.npy`; `experiments/v32d_stability_v1/xai/C1_s137/719-gradcam.npy`; `experiments/v32d_stability_v1/xai/C1_s137/848-gradcam.npy`; `experiments/v32d_stability_v1/xai/initial_s137/230-gradcam.npy`; `experiments/v32d_stability_v1/xai/initial_s137/719-gradcam.npy`; `experiments/v32d_stability_v1/xai/initial_s137/848-gradcam.npy`

### [17_xai_s137_high](figures/17_xai_s137_high.png)

All fixed D samples, original normalization/orientation; untrained control retained.

**Limits:** Per-map normalized activation is not probability, area or physical localization; edge/background concerns remain.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (13):** `data/processed/hmi.m_45s.2022.08.10_00_01_30_TAI.magnetogram_processed.npy`; `data/processed/hmi.m_45s.2024.08.09_00_01_30_TAI.magnetogram_processed.npy`; `data/processed/hmi.m_45s.2025.11.08_00_01_30_TAI.magnetogram_processed.npy`; `experiments/v32d_stability_v1/protocol.json`; `experiments/v32d_stability_v1/xai/C0_s137/1312-gradcam.npy`; `experiments/v32d_stability_v1/xai/C0_s137/1645-gradcam.npy`; `experiments/v32d_stability_v1/xai/C0_s137/885-gradcam.npy`; `experiments/v32d_stability_v1/xai/C1_s137/1312-gradcam.npy`; `experiments/v32d_stability_v1/xai/C1_s137/1645-gradcam.npy`; `experiments/v32d_stability_v1/xai/C1_s137/885-gradcam.npy`; `experiments/v32d_stability_v1/xai/initial_s137/1312-gradcam.npy`; `experiments/v32d_stability_v1/xai/initial_s137/1645-gradcam.npy`; `experiments/v32d_stability_v1/xai/initial_s137/885-gradcam.npy`

### [17_xai_s2026_low](figures/17_xai_s2026_low.png)

All fixed D samples, original normalization/orientation; untrained control retained.

**Limits:** Per-map normalized activation is not probability, area or physical localization; edge/background concerns remain.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (13):** `data/processed/hmi.m_45s.2016.06.05_00_01_30_TAI.magnetogram_processed.npy`; `data/processed/hmi.m_45s.2016.11.12_00_01_30_TAI.magnetogram_processed.npy`; `data/processed/hmi.m_45s.2017.07.06_00_01_30_TAI.magnetogram_processed.npy`; `experiments/v32d_stability_v1/protocol.json`; `experiments/v32d_stability_v1/xai/C0_s2026/148-gradcam.npy`; `experiments/v32d_stability_v1/xai/C0_s2026/284-gradcam.npy`; `experiments/v32d_stability_v1/xai/C0_s2026/68-gradcam.npy`; `experiments/v32d_stability_v1/xai/C1_s2026/148-gradcam.npy`; `experiments/v32d_stability_v1/xai/C1_s2026/284-gradcam.npy`; `experiments/v32d_stability_v1/xai/C1_s2026/68-gradcam.npy`; `experiments/v32d_stability_v1/xai/initial_s2026/148-gradcam.npy`; `experiments/v32d_stability_v1/xai/initial_s2026/284-gradcam.npy`; `experiments/v32d_stability_v1/xai/initial_s2026/68-gradcam.npy`

### [17_xai_s2026_medium](figures/17_xai_s2026_medium.png)

All fixed D samples, original normalization/orientation; untrained control retained.

**Limits:** Per-map normalized activation is not probability, area or physical localization; edge/background concerns remain.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (13):** `data/processed/hmi.m_45s.2017.03.30_00_01_30_TAI.magnetogram_processed.npy`; `data/processed/hmi.m_45s.2021.10.09_00_01_30_TAI.magnetogram_processed.npy`; `data/processed/hmi.m_45s.2022.05.31_00_01_30_TAI.magnetogram_processed.npy`; `experiments/v32d_stability_v1/protocol.json`; `experiments/v32d_stability_v1/xai/C0_s2026/230-gradcam.npy`; `experiments/v32d_stability_v1/xai/C0_s2026/719-gradcam.npy`; `experiments/v32d_stability_v1/xai/C0_s2026/848-gradcam.npy`; `experiments/v32d_stability_v1/xai/C1_s2026/230-gradcam.npy`; `experiments/v32d_stability_v1/xai/C1_s2026/719-gradcam.npy`; `experiments/v32d_stability_v1/xai/C1_s2026/848-gradcam.npy`; `experiments/v32d_stability_v1/xai/initial_s2026/230-gradcam.npy`; `experiments/v32d_stability_v1/xai/initial_s2026/719-gradcam.npy`; `experiments/v32d_stability_v1/xai/initial_s2026/848-gradcam.npy`

### [17_xai_s2026_high](figures/17_xai_s2026_high.png)

All fixed D samples, original normalization/orientation; untrained control retained.

**Limits:** Per-map normalized activation is not probability, area or physical localization; edge/background concerns remain.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (13):** `data/processed/hmi.m_45s.2022.08.10_00_01_30_TAI.magnetogram_processed.npy`; `data/processed/hmi.m_45s.2024.08.09_00_01_30_TAI.magnetogram_processed.npy`; `data/processed/hmi.m_45s.2025.11.08_00_01_30_TAI.magnetogram_processed.npy`; `experiments/v32d_stability_v1/protocol.json`; `experiments/v32d_stability_v1/xai/C0_s2026/1312-gradcam.npy`; `experiments/v32d_stability_v1/xai/C0_s2026/1645-gradcam.npy`; `experiments/v32d_stability_v1/xai/C0_s2026/885-gradcam.npy`; `experiments/v32d_stability_v1/xai/C1_s2026/1312-gradcam.npy`; `experiments/v32d_stability_v1/xai/C1_s2026/1645-gradcam.npy`; `experiments/v32d_stability_v1/xai/C1_s2026/885-gradcam.npy`; `experiments/v32d_stability_v1/xai/initial_s2026/1312-gradcam.npy`; `experiments/v32d_stability_v1/xai/initial_s2026/1645-gradcam.npy`; `experiments/v32d_stability_v1/xai/initial_s2026/885-gradcam.npy`

### [18_occlusion_controls](figures/18_occlusion_controls.png)

Nine fixed observations per seed/configuration; 15 random controls per guided mask.

**Limits:** No new masks; removal magnitude is a confound. Positive guided extra drop does not prove faithfulness.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (11):** `experiments/v32d_stability_v1/xai/C0_s137/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/C0_s2026/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/C0_s42/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/C1_s137/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/C1_s2026/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/C1_s42/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/initial_s137/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/initial_s2026/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/initial_s42/square_occlusion.csv`; `experiments/v32d_stability_v1/xai/map_comparison.csv`; `experiments/v32d_stability_v1/xai/square_effects.csv`

### [cost_guards_by_round](tables/cost_guards_by_round.csv)

Original unchanged guards, per round, under matched configurations.

**Limits:** E2 four-round effects are separate tables; no averaging erases failures. Parameters use strict <512000; ratios use <= limits.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (43):** `experiments/v32e1_memory_diagnostic_v1/cost_summary.csv`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/default/V3.1/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run1/kleidiai_off/V3.1/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/default/V3.1/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/C1_s137/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/C1_s2026/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/C1_s42/cost.json`; `experiments/v32e1_memory_diagnostic_v1/runs/cost/run2/kleidiai_off/V3.1/cost.json`; `experiments/v32e2_latency_v1/runs/round1/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round1/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round1/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round1/D/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round2/D/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round3/D/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/A/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/B/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/C/timings.csv`; `experiments/v32e2_latency_v1/runs/round4/D/timings.csv`; `experiments/v32e_onnx_cost_v1/cost/run1/C1_s137/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run1/C1_s2026/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run1/C1_s42/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run1/V3.1/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/C1_s137/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/C1_s2026/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/C1_s42/cost.json`; `experiments/v32e_onnx_cost_v1/cost/run2/V3.1/cost.json`; `experiments/v32e1_memory_diagnostic_v1/cost_summary.csv`; `experiments/v32e_onnx_cost_v1/SERVING_SCOPE.md`

### [onnx_metrics](tables/onnx_metrics.csv)

Saved ONNX accuracy recomputed by runtime and band; distinct from CPU PyTorch metrics.

**Limits:** Small kernel differences remain; parity does not require identical bits.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (8):** `experiments/v32e_onnx_cost_v1/parity/V3.1.csv`; `experiments/v32e_onnx_cost_v1/parity/C1_s42.csv`; `experiments/v32e_onnx_cost_v1/parity/C1_s137.csv`; `experiments/v32e_onnx_cost_v1/parity/C1_s2026.csv`; `experiments/v32e1_memory_diagnostic_v1/parity/V3.1.csv`; `experiments/v32e1_memory_diagnostic_v1/parity/C1_s42.csv`; `experiments/v32e1_memory_diagnostic_v1/parity/C1_s137.csv`; `experiments/v32e1_memory_diagnostic_v1/parity/C1_s2026.csv`

### [memory_stages](tables/memory_stages.csv)

Original E1 stage rows and missing samples preserved.

**Limits:** Instrumented diagnostic runs are not cost-guard measurements. Stages are cumulative, not additive allocations.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (1):** `experiments/v32e1_memory_diagnostic_v1/memory_stages.csv`

### [candidate_artifacts](tables/candidate_artifacts.csv)

Frozen C1 checkpoints and existing ONNX exports; no new export or selection.

**Limits:** Candidates remain unpromoted; registry V3.1 unchanged.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (3):** `experiments/v32e_onnx_cost_v1/artifacts/C1_s42/manifest.json`; `experiments/v32e_onnx_cost_v1/artifacts/C1_s137/manifest.json`; `experiments/v32e_onnx_cost_v1/artifacts/C1_s2026/manifest.json`

### [training_artifacts](tables/training_artifacts.csv)

All seven frozen selected checkpoints; parameter counts from original configs.

**Limits:** No checkpoint selected in F; no inferred ONNX costs for C0/C2.

**Reproduce:** `python3 -B experiments/v32f_scientific_package_v1/build.py --output-name thesis_rebuild_01 && python3 -B experiments/v32f_scientific_package_v1/finish.py --output-name thesis_rebuild_01`

**Sources (21):** `experiments/v32c_seed42_v1/C0/config.json`; `experiments/v32c_seed42_v1/C0/completion.json`; `experiments/v32c_seed42_v1/C0/best.pth`; `experiments/v32d_stability_v1/seed137/C0/config.json`; `experiments/v32d_stability_v1/seed137/C0/completion.json`; `experiments/v32d_stability_v1/seed137/C0/best.pth`; `experiments/v32d_stability_v1/seed2026/C0/config.json`; `experiments/v32d_stability_v1/seed2026/C0/completion.json`; `experiments/v32d_stability_v1/seed2026/C0/best.pth`; `experiments/v32c_seed42_v1/C1/config.json`; `experiments/v32c_seed42_v1/C1/completion.json`; `experiments/v32c_seed42_v1/C1/best.pth`; `experiments/v32d_stability_v1/seed137/C1/config.json`; `experiments/v32d_stability_v1/seed137/C1/completion.json`; `experiments/v32d_stability_v1/seed137/C1/best.pth`; `experiments/v32d_stability_v1/seed2026/C1/config.json`; `experiments/v32d_stability_v1/seed2026/C1/completion.json`; `experiments/v32d_stability_v1/seed2026/C1/best.pth`; `experiments/v32c_seed42_v1/C2/config.json`; `experiments/v32c_seed42_v1/C2/completion.json`; `experiments/v32c_seed42_v1/C2/best.pth`
