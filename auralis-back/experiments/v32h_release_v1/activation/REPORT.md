> **Final status — 2026-09-17:** the user confirmed successful PC and phone/AR tests, including active version, predictions, metrics, Agent Lab, Grad-CAM, five states, layers, timeline and AR, with no reported visual regressions. Source: user confirmation; device/browser versions, execution dates, recordings and performance measurements were not recorded. See [final closure](../closure/REPORT.md). Earlier pending statements below describe the original test stage and are preserved as history. Local promotion and the subsequently refreshed temporary Sites are distinct from a definitive publication, which is not performed here.

# V3.2-H — authorized local activation

## Final status

**Release prepared: yes. Functional QA: passed. Locally promoted: yes.** The user explicitly authorized option1, “Autorizar promoción local de V3.2 s42,” after receiving preparation hashes, QA results, limits and recovery procedure. `authorization.json` preserves that authorization and verification of all158 prepared artifact hashes before activation.

Default is now **Coronium V3.2 C1_s42, epoch27**, with exactly the validated `mlas.disable_kleidiai=1` configuration. Ordinary startup requires no AURALIS_RELEASE or AURALIS_TEST_* variables and reads release artifacts from `models/`. No user service was stopped or restarted; the next ordinary startup selects V3.2. No public deployment, commit, tag or push was performed.

Selection was post-experiment and already confirmed by the user, for continuity with the initial pilot among the three eligible mitigated candidates. It is not an ensemble or an automatic best-MAE/favorable-round choice.

## Changes at activation

- `src/models/active_model.py`: DEFAULT_VERSION3.1→3.2. No constructor, inference, preprocessing, diagnostic or cache implementation change at this step.
- `models/coronium_v3_2_manifest.json`: records local promotion authorization/status. Its initial selection record retains the fact that checkpoint confirmation did not authorize promotion at that earlier time.
- README, AGENTS and dossier current-version notice: identify active local V3.2 and its own metrics; V3.1/publication history and DOI remain intact.
- H runbook and report: current activation notice, ordinary-startup and recovery commands. Preparation snapshots and hashes remain preserved under `before/` and the original H manifest.

The prepared temporal overlay records its creation-stage status and remains byte-identical; active identity is selected by the verified release. Five observations, B+/B−, dates, maps and visual assets are unchanged. No frontend, Sun material/shader/animation/timeline or WebAR code changed at activation. The earlier pixel-identical HMI29 comparison and build/browser QA remain applicable.

## Unchanged artifact hashes and metrics

| Artifact | SHA-256 |
|---|---|
| best_coronium_v3_2.pth | `0b6778ee9518af689fb800ee502c25e7c05d51f7191b5ed50ac199e1a5342179` |
| best_coronium_v3_2.onnx | `23b4658ba8817355c91b22b617db8dedc91a249d0294b45128623a3dbfdf1b0a` |

206875 parameters; checkpoint846093 bytes; ONNX835234 bytes self-contained. Backbone dropout0/head0.3; eval/frozen BatchNorm. CPU FP32, four intra-op/one inter-op, sequential execution, ORT_ENABLE_ALL, ORT1.25.1 native binary SHA pinned exactly as E.1/E.2/G/H. Twenty synthetic input-noise passes plus deterministic forward remain unchanged. Noise spread is not MC Dropout or calibrated uncertainty.

This s42 artifact's deterministic mitigated results on263 selection-validation observations: MAE0.04833447615909939, RMSE0.05905530431219216, R²0.9714300369736174, MAPE2.908886965683121%, bias0.013237384788890291 and p95 absolute error0.10974993705749511. Error units are SI percentage points. No across-seed average is served.

## Post-activation checks

`smoke.py` launches ordinary `python -m uvicorn src.api.main:app` on an isolated inherited loopback socket; it does not replace handlers, lifespan or add observer endpoints. It runs two fresh sequential processes:

1. **Normal default:** all AURALIS_* variables removed. Health, prediction, alias, two upload formats, exact cached response, malformed/missing errors and recovery, own263-row deterministic metrics/default scatter, MC-unavailable response and all five Agent Lab routes passed. Prediction identifies `locally_promoted; seed=42; epoch=27` and runtime `kleidiai_off`.
2. **Recovery:** only AURALIS_RELEASE=3.1. Health, prediction, alias, both uploads, cache, errors/recovery and original MC-default metrics passed. Original artifacts/runtime remain available.

One fixed previously validated fixture per process suffices for the activation change; no new full parity, Grad-CAM sweep or latency bank was run. Both temporary servers closed their sockets and completed lifespan shutdown. Full responses, selected environment, process IDs and cleanup records are under `normal_default/` and `rollback_explicit/`.

Six release checks passed with only the two default/status assertions adapted for the authorized activation. Seven historical V3.1 regression checks passed under explicit V3.1 selection. The earlier42 preparation tests, both builds, HTTP/parity, Grad-CAM invariance and pixel comparison remain retained and applicable because their execution paths and artifacts are unchanged.

Formal E.1 s42 memory/latency guards and E.1 parity remain applicable. E's original memory failures are not claimed resolved without mitigation. H's additional HTTP numbers remain HTTP, not forward latency; see the preparation report for all results and limitations. No guard was changed.

## Recovery and remaining limits

Immediate per-process recovery: start with `AURALIS_RELEASE=3.1`. Persistent recovery: change DEFAULT_VERSION back to3.1, update current-version notices and verify ordinary startup. Keep all V3.2 artifacts/results and user edits. Never reset or clean the working tree. See [RUNBOOK.md](../RUNBOOK.md).

- Physical PC/phone/AR acceptance remains **pending**, not implied by authorization. See [human test guide](../PRUEBA-PC-TELEFONO.md).
- Main frontend retains15 pre-existing TypeScript errors (baseline16, zero introduced); both builds and functional QA passed. No dependency upgrade or unrelated refactor was made.
- Validation was used for selection, not independent/temporal generalization. Low-band R²−0.6164 and tolerated low-activity deterioration remain. Border/background XAI concerns are unresolved. V3.2 MC metrics are not evaluated.
- Mac measurements do not establish mobile/low-resource performance. Public frozen Site remains historical; local promotion did not publish it.

The26 scientific figure triples remain untouched at `../../v32f_scientific_package_v1/package/figures/`, indexed by `../../v32f_scientific_package_v1/package/INDEX.md`.

**FASE V3.2-H: CUMPLIDA** — preparation, functional QA and explicitly authorized local promotion completed. Physical user validation remains pending. V3.1 is preserved for verified recovery; the approved product design remains intact. No next phase has started.
