> **Final status — 2026-09-17:** the user confirmed successful PC and phone/AR tests, including active version, predictions, metrics, Agent Lab, Grad-CAM, five states, layers, timeline and AR, with no reported visual regressions. Source: user confirmation; device/browser versions, execution dates, recordings and performance measurements were not recorded. See [final closure](closure/REPORT.md). Earlier pending statements below describe the original test stage and are preserved as history. Local promotion and the subsequently refreshed temporary Sites are distinct from a definitive publication, which is not performed here.

> **Activation update:** The user explicitly authorized local promotion after reviewing QA. Coronium V3.2 C1_s42 epoch27 is now the default; normal startup and explicit V3.1 recovery passed. See [activation/REPORT.md](activation/REPORT.md) for final status, checks and limitations. **FASE V3.2-H: CUMPLIDA** for release preparation, functional QA and authorized local promotion; physical validation remains pending.
>
> The report below is the preserved preparation-stage record, before that authorization. Its pending/default3.1 statements refer to that earlier stage.

# V3.2-H — release prepared, local promotion pending

## Decision and status

The user confirmed **C1_s42, epoch 27** after B–G. The stated criterion was continuity with the initial pilot among three candidates meeting the mitigated formal guards, not automatic minimum MAE or selection of a favorable round. This is a post-experiment choice. There is no ensemble.

**Release prepared: yes. Automated functional QA: passed, with pre-existing project-wide TypeScript debt recorded below. Physical PC/phone/AR QA: pending. Locally promoted: no. Default: Coronium V3.1, original runtime.** Separate explicit user authorization is required before changing that default.

No training, export, quantization, MC/XAI sweep, dependency update, commit, tag, push or publication. The twenty input-noise passes plus one deterministic prediction remain. Input-noise spread is not MC Dropout or calibrated uncertainty.

## Frozen release

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `models/best_coronium_v3_2.pth` | 846093 | `0b6778ee9518af689fb800ee502c25e7c05d51f7191b5ed50ac199e1a5342179` |
| `models/best_coronium_v3_2.onnx` | 835234 | `23b4658ba8817355c91b22b617db8dedc91a249d0294b45128623a3dbfdf1b0a` |

Exact copies of existing s42 artifacts, 206875 parameters (<512000), unchanged CoroniumV3/ECA structure, backbone dropout 0 and head dropout 0.3. Eval freezes BatchNorm and disables Dropout. ONNX FP32, opset18, dynamic N×2×512×512, self-contained, same clip400/B+/B− and raw SI contracts. Metrics, 263-row validation CSV and manifest are under `models/`; the ordinary release does not read experiment scripts or require `AURALIS_TEST_*`. Provenance references to experiments are not serving dependencies.

Runtime: Apple M5, 24 GiB, macOS26.6.2 arm64, Python3.12.7, torch2.11.0, numpy1.26.4, ORT1.25.1 CPU. Four intra-op threads, one inter-op, sequential execution, ORT_ENABLE_ALL, exactly `mlas.disable_kleidiai=1`. The validated native library SHA-256 is pinned and checked; option readback is also checked. An unvalidated binary fails clearly instead of assuming that accepting an option proves it works. This pin deliberately limits portability until equivalent validation exists.

## Chosen model metrics (not an across-seed average)

| Metric | s42 ONNX mitigated, 263 selection-validation observations |
|---|---:|
| MAE, SI percentage points | 0.04833447615909939 |
| RMSE, SI percentage points | 0.05905530431219216 |
| R² | 0.9714300369736174 |
| MAPE, % | 2.908886965683121 |
| Bias, prediction − SI, SI percentage points | 0.013237384788890291 |
| p95 absolute error, SI percentage points | 0.10974993705749511 |

Low band: N=43, MAE 0.058247455330782134, R² **−0.6164045953225932**. The tolerated low-activity deterioration remains visible; validation was used for selection, not an independent or temporal test. Tail SI>2: N=71, MAE 0.04416566835322849, a subset of the high band. Border/background XAI concerns remain unresolved. No MC performance is claimed for the release.

## Prior evidence reused

298 prior source artifacts and all three candidate identities were checked against actual manifests in preflight and checked again after implementation. B–G reports/protocols, G `CONSUMERS.md` and `RUNBOOK.md`, and F's index informed this scope. E's original memory failures remain valid for the original runtime; E.1/E.2/G mitigated evidence is separately applicable. The selected s42 formal forward/preparation latency and RSS guards pass in E.1; E.2 resolves s2026, not a new s42 benchmark. G's two rounds of mitigated HTTP remain supplementary service evidence. No unfavorable round was replaced.

E.1 parity reuses the identical checkpoint, ONNX and native runtime: 263 observations, atol=rtol=1e-5, zero exceedances. H adds only small fixture checks and five authorized temporal predictions. No repeated full evaluation or 704-request bank.

## Additional service QA (bounded, not a new formal forward benchmark)

Protocol was saved before execution in `protocol.json`. Real FastAPI handlers, no AST-modified endpoint copy. A thin isolated observer counts forwards and records tensors/weights; a Python file audit rejects release reads from other experimental directories. Fresh sequential processes, both PyTorch and ONNX resident, no training. Same G sample sequence, 3 warmups, 30 result-cache-cold and 60 result-cache-hot HTTP observations per arm. Full individual timing and external 5 ms RSS traces are preserved under `runs/round1/`.

| Arm | Cold HTTP p50 / p95 ms | Hot HTTP p50 / p95 ms | HTTP-stage lifetime peak MiB | Full peak including one Grad-CAM MiB |
|---|---:|---:|---:|---:|
| V3.1 mitigated | 495.956958 / 509.465958 | 0.432813 / 0.591441 | 569.343750 | 1079.796875 |
| V3.2 s42 mitigated | 510.342313 / 516.105693 | 0.436021 / 0.557919 | 567.921875 | 1077.328125 |

Cold HTTP changes: +2.90% p50, +1.30% p95; full peak −0.23%. These are additional bounded QA observations, not forward-only timings or new acceptance thresholds. The +5% formal latency guard remains evaluated on the agreed E.1 paths. Models, filesystem and connection stay warm in the HTTP comparison; result cache alone is cold/hot. Cold requests execute exactly 20 noise passes plus 1 deterministic forward; hot requests execute zero forwards. RSS includes interpreter/libraries, both models, allocators and transient XAI tensors. Mac results do not certify mobile or low-resource hardware.

Each arm passes 12 fixture checks (3 representative inputs × predict/alias/upload single channel/upload dual channel). Full unrounded ONNX output and prepared-tensor hashes match offline; the public response matches 4-decimal rounding. Missing and malformed requests return errors, then a valid request succeeds. Metrics and all five Agent Lab reports identify the actual artifact. Release MC resources return unavailable rather than V3.1 metrics. Cache identity includes model version and runtime. One Grad-CAM per arm preserves state-dict hash and subsequent deterministic value exactly. The service stage4.conv hook is not D's full-block procedure and resolves no faithfulness concern.

`runs/round0/unconfigured/` additionally confirms real ordinary startup with no release/test variables: V3.1 original, original runtime settings and separate V3.1 MC metrics. All measured temporary processes shut down cleanly.

## Consumers, temporal revision and visual QA

See `CONSUMERS.md` and `FILES.md`. API/CLI/XAI constructors and version labels follow the registry. Agent Lab strictly joins the copied 263 predictions with source identities/targets and reports SI percentage points. Historical metrics remain labeled historical. MC tools remain available through an explicit release argument, with no new sweep executed.

The five temporal outputs are a new versioned overlay plus a separate revised scientific contract. Original V3.1 contract, maps, dates, observations, B+/B−, textures and sequence remain unchanged. Results for March24/25/28/29/30 are 1.6771135330200195, 1.6957380771636963, 1.950901746749878, 2.049825668334961 and 2.0041637420654297. Four observations are train and one selection-validation; this is not independent evidence.

The local dashboard selects the overlay only after verifying backend identity; an unavailable backend produces a clear error without a V3.1 fallback. Retry after restarting the isolated backend loads V3.2. Frozen public Site behavior remains historical. AR links carry the selected release but no physical AR or publication was performed.

All eight dashboard tabs were visited and the five dates selected, including return to HMI29. Captures and DOM records are retained. Fixed HMI29, same camera and surface t=0: **before/after canvas images are pixel-identical (0 differing channel values)**. Materials, geometry, shaders, animation and controls were not modified. Numerical panel content changes as authorized. This desktop image comparison is not phone/AR validation.

## Tests, incidents and limits

- 6 release tests: default, validated runtime/metrics, corrupt/missing artifacts, invalid/conflicting selection, Agent Lab strict join/MC constructor, preserved G candidates.
- 7 reused Phase16/17 regression checks passed.
- 29 temporal/solar tests passed (26 existing + 3 overlay checks); Needle TypeScript and both builds passed.
- CLI processed-NPY prediction passes; full PyTorch result 2.049833059 versus ONNX 2.049825668334961, within established tolerance, both round to 2.0498. No FITS fixture was acquired; the shared FITS preprocessing remains unchanged.
- Changed Python sources parse successfully. Final Agent Lab report generation passes without new inference.
- Main frontend TypeScript audit: **15 existing errors, baseline16, zero introduced diagnostics**. Installed TypeScript5.9.3 rejects the repository's pre-existing ignoreDeprecations=6.0, so audit uses command-only override5.0. Full logs and normalized comparison retained. Existing Recharts/type/library/language errors remain; do not claim a clean project-wide tsc. No dependency/config upgrade. Build retains its pre-existing large-chunk warning.
- Browser initially exposed a pre-existing missing `CheckCircle2` import causing a blank dashboard; fixed narrowly. Agent Lab inherited log-SI/tail wording was corrected to match the actual results. Initial CLI NPY metadata lookup lacked the extension; fixed and rechecked. An inherited temporal test's data-URL loader needed the new import included in its explicit URL mapping; fixed without changing assertions. Initial failed logs are retained.
- During deliberate isolated API restart, the viewer exposed a stale-version fallback; fixed by requiring verified identity before mounting. Error/no-iframe and retry recovery are recorded. No user service was stopped.
- PC/phone user acceptance, touch/AR placement and physical performance remain unperformed; see `PRUEBA-PC-TELEFONO.md`.

## Figures and promotion gate

The 26 scientific figures remain at `../v32f_scientific_package_v1/package/figures/`; the index is `../v32f_scientific_package_v1/package/INDEX.md`. All PNG/SVG/PDF triples remain untouched. H QA images are grouped here and are not replacement scientific figures.

Recommendation: prepared for a user-reviewed local promotion decision, with explicit TypeScript debt and physical-validation limits. No guard is relaxed. Promotion would change only the default registry version to3.2 and its documented status, thereby selecting the already-tested runtime/artifacts/consumer paths. Recovery uses explicit `AURALIS_RELEASE=3.1` with retained original artifacts; `RUNBOOK.md` documents persistent recovery. Pending authorization, V3.1 stays default and no promotion has occurred.

**FASE V3.2-H: PARCIALMENTE CUMPLIDA** — release prepared and functional QA passed; promotion authorization and physical user checks pending. Approved solar design remains intact.
