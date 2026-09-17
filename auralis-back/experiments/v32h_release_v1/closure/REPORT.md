# Coronium V3.2 — final local closure and release notes

Recorded 2026-09-17. **Release prepared, functional QA passed, locally promoted; PC and phone/AR acceptance confirmed by the user.** This records the existing release; no runtime, inference, architecture, weights, preprocessing, dataset or visual change was made during closure.

The final request is the source of manual acceptance: active version, predictions, metrics, Agent Lab, Grad-CAM, five states, layers, timeline and AR worked without reported visual regressions. Browser/device versions, precise test dates, recordings, FPS and per-function local/Site attribution were **not recorded**. This is not an agent-performed physical test. Machine-readable record: [user-validation.json](user-validation.json).

## Release and scientific scope

- Individual C1 seed42, epoch27; post-experiment user choice, followed by explicit local promotion authorization. No ensemble or cross-seed mean is served.
- 206,875 parameters; unchanged CoroniumV3/ECA, backbone dropout0/head0.3, eval/frozen BatchNorm.
- Input float32 `(N,2,512,512)`, clip400 polarity B+/B−. Output original SI pixel percentage, not log-SI or official sunspot number.
- Checkpoint 846,093 bytes, SHA-256 `0b6778ee9518af689fb800ee502c25e7c05d51f7191b5ed50ac199e1a5342179`.
- Self-contained ONNX 835,234 bytes, SHA-256 `23b4658ba8817355c91b22b617db8dedc91a249d0294b45128623a3dbfdf1b0a`.
- [Release manifest](../../../models/coronium_v3_2_manifest.json), [metrics](../../../models/coronium_v3_2_metrics.json), [263 predictions](../../../models/coronium_v3_2_validation.csv), [five-state numerical overlay](../../../models/coronium_v3_2_temporal.json).

| Deterministic mitigated ONNX, s42 | Value |
|---|---:|
| MAE, SI percentage points | 0.04833447615909939 |
| RMSE, SI percentage points | 0.05905530431219216 |
| R² | 0.9714300369736174 |
| MAPE, percent | 2.908886965683121 |
| Bias, SI percentage points | 0.013237384788890291 |
| p95 absolute error, SI percentage points | 0.10974993705749511 |

These are 263 selection-validation observations, not independent or temporal testing. Low-band R² −0.6164 and tolerated deterioration remain; border/background XAI concerns remain. Neither R² nor 100−MAPE is accuracy. V3.2 MC performance remains unevaluated. The twenty input-noise passes are an uncalibrated diagnostic, separate from the deterministic prediction and MC Dropout.

## Runtime, operation and recovery

CPU FP32, batch1, intra-op4/inter-op1, sequential ORT, ENABLE_ALL, `mlas.disable_kleidiai=1`. Validated ORT1.25.1 native binary is pinned by SHA-256 in the manifest. Tested environment: Apple M5/24 GiB, macOS26.6.2 arm64, Python3.12.7. Other ORT binaries/platforms need validation; runtime rejects unverified mitigation builds. Mac costs do not establish mobile inference performance. Weight bytes are not process RSS; forward, full HTTP and cached HTTP are distinct measurements. E original-runtime failures and E.1/E.2 mitigated results remain separate.

Use [RUNBOOK](../RUNBOOK.md) for backend/frontend/CLI commands. Normal startup selects V3.2 with no experimental or model-selection variables. Start a fresh backend process with `AURALIS_RELEASE=3.1` for recovery; preserve V3.2 artifacts and user changes. Never reset/clean the working tree to recover a model. The [actual activation](../activation/REPORT.md) and its saved normal/default and rollback checks supersede preparation-stage “pending” statements.

The release manifest's physical-validation-pending wording is a frozen activation-stage record, superseded by this dated addendum. It is deliberately byte-preserved, as are metrics and the temporal overlay; historical checksums remain valid. No runtime-facing metadata is changed by closure.

## Frozen scientific evidence

One location: [F figures](../../v32f_scientific_package_v1/package/figures/) and [F INDEX](../../v32f_scientific_package_v1/package/INDEX.md). All 26 PNG/SVG/PDF triples and the index remain byte-identical. F's “V3.1 remains active” describes the time of F, not the current registry.

Figures 01–15 compare configurations, seeds, references or runtimes as labeled. Figure13 is the s2026 E.2 runtime study, not s42 release latency. Figure14 is original-runtime HTTP and is not mitigated forward evidence. Figure16 documents shared C1 architecture. Only the three `17_xai_s42_*` panels specifically identify s42; other `17_xai_*` panels belong to their named seeds. Figure18 retains occlusion controls. None of these panels is relabeled as an exclusive release evaluation. Use the release metrics/CSV above for the promoted artifact's exact numerical results.

`protected.json` freezes product code/assets, release artifacts and F at closure entry. `verify.py` checks those hashes, F's original artifact manifest, all 298 sources verified before H, both release registries and local documentation links. These checks reuse existing evidence; they perform no inference or research rerun.

## Checks and known pending items

- Six activated-release tests pass, including default3.2, explicit3.1, hashes, invalid selection, native runtime option and Agent Lab identity join.
- Twenty-nine temporal/solar tests pass; main frontend and embedded Needle builds pass. No source/visual resources changed in this closure.
- Main frontend global TypeScript check remains a separate pre-existing debt; see [verification.json](verification.json) and saved diagnostics. No dependency/configuration fix was attempted.
- **Existing landing-page label inconsistency:** `auralis-front/src/features/landing/landing-hero.tsx` retains a sentence with V3.1 MC/API MAE values0.10156/0.20408 immediately after a dynamic model-name sentence. These are not V3.2 metrics. This was discovered during diff review and left unchanged under the absolute no-product/UI-change restriction. It needs a separately authorized text-only correction before claiming every public label is consistent. No new scientific result or inference defect is implied.
- Git whitespace checks flag original generated F SVG/CSV/INDEX and the pinned release CSV (including CRLF). They are preserved byte-for-byte; newly edited closure documentation passes the scoped check.
- Build bundle-size warnings remain advisory. No new benchmark, training, export or XAI/MC sweep was run. Existing user services were not interrupted.

## Local version control and publication

The local commit captures reviewed prior V3.2 integration/Sites-source changes, release artifacts, active docs and curated evidence. Only documentation, closure checks and the two production-artifact Git exceptions were newly edited here. V3/V3.1 artifacts remain tracked. The model tag `coronium-v3.2` is distinct from Auralis's software version; it records this local snapshot and its documented limitations, not a public release or clean global TypeScript bill.

The large raw research archive remains locally preserved with its original manifests; process inventories, runtime caches, personal-path environment dumps and unrelated local files are excluded from this commit. [commit-files.json](commit-files.json) enumerates the explicit staged scope. F figures/tables/index are included without changes; original research sources remain locally available for the provenance verifier. A Git checkout is not a redistribution of the full raw dataset/research archive or installed runtime.

Temporary Sites were already refreshed in the separately authorized preceding task: solar v14 and private static dashboard v5, documented in [Sites history](../../../../docs/two-sites-demo.md). They serve saved results, not a hosted Python model. This closure does **not** push, deploy, publish a definitive release or change DOI/CITATION/Zenodo metadata. Git identity uses the user's existing configuration; no coauthor or attribution edits.

**CIERRE V3.2: PARCIAL** — technical/documentary snapshot and user acceptance recorded, local recovery retained; the discovered landing-label inconsistency remains open under this task's no-UI-change restriction. No definitive publication is claimed and scientific limitations remain.
