> **Closure addendum — 2026-09-17:** the user confirmed that the mobile review after the coherence correction is resolved. Source: user confirmation; device/browser/version, test date, recordings and measurements not recorded. The subsequent [TypeScript closure](../typescript/REPORT.md) resolves the 15 source diagnostics and the compiler-option incompatibility. Earlier results and pending statements below are historical, preserved unchanged. No new physical AR session or publication is claimed.

# V3.2 presentation consistency — local correction

Coronium V3.2 C1_s42, epoch27 remains the default. This correction follows the local model tag `coronium-v3.2`; the tag is not moved. Content/data connections only: no inference, runtime, architecture, weights, preprocessing, partitions, frozen predictions, Sun resources or layout changes.

## Audit and corrections

| Location | Inconsistency | Correction | Source |
|---|---|---|---|
| Landing hero | Dynamic V3.2 name followed by V3.1 MAE | Same verified response supplies name/protocol/MAE; individual seed/epoch from derived manifest metadata, EN/ES | Release manifests, metrics and `/api/stats` |
| Landing architecture/specifications | Approximate parameters, fixed size, “Detection” | Exact parameters and complete ONNX bytes from the matching manifest/artifact; SI regression and clip400/B+/B− | Hash-verified production artifacts |
| Overview | Independent prediction and metrics could have different identities | Current-state values require a matching verified stats version; error units are SI percentage points | Actual prediction identity and release stats |
| Experiments/scatter | Could request results before verifying identity; historical references called candidates | Clear stale rows; validate supported protocol, row count, identity and MAE; preserve historical charts and illustrative K-fold | Real `/api/results-comparison` responses for both releases, B–G/F |
| Settings | Serving batch32; fixed runtime label | Batch parsed from the deterministic serving protocol; validated CPU4/1 mitigation shown for V3.2; unknown identity stays unavailable | Release manifest runtime and deterministic protocol |
| Monitoring/XAI/logs | Fixed ONNX size, normalized-index caption, V3 PRO live log | Remove unsourced size from per-image result; SI-percent caption; actual model name in new logs; bilingual XAI-unavailable notice | Prediction contract, registry, existing XAI scope |
| README/dossier | Active metrics attributed to MC; insufficient current contract/runtime scope | Deterministic release separated from MC/noise; current addendum with own metrics, execution/recovery and limitations; archive retained | Release manifest/metrics and H activation |
| EN/ES copy | V3.1 subtitle, MAPE described as accuracy | Version-neutral subtitle, relative-error terminology; corrected visible statements translated | Scientific input/target/evaluation contract |

All eight dashboard tabs were inspected. Pipeline counts, Agent Lab's identity-joined results, historical experiment log, benchmark labels and illustrative K-fold were retained as such. The Sun tab rendered the original scene and numerical overlay. No new XAI sweep or benchmark was run; ordinary overview/monitoring requests occurred during functional UI checking. Earlier log entries remain historical; new logging labels use the selected model.

## Source linkage and unavailable data

`python3 -B scripts/build-release-presentation.py` derives the small frontend metadata JSON from verified V3.1/V3.2 manifests and full-precision metrics. It hashes every release dependency and obtains ONNX bytes from the actual file. It performs no inference. This is display provenance, not a substitute evaluation or a newly selected model.

The frontend rejects unknown/mismatched names, versions, unsupported evaluation protocols, inconsistent metrics and nonfinite numbers. No fallback to another release is used. The scatter additionally checks the real returned rows against that protocol; tolerance1e-6 is a display-integrity check for accumulated CSV rounding, not a changed ONNX parity tolerance. Existing scientific parity tolerances remain unchanged. Stored Sites responses were checked without modifying them. No refreshed Site deployment was made.

V3.1 control startup with `AURALIS_RELEASE=3.1` retains its original protocol: landing s42/epoch40, MC T20 MAE0.10156; deterministic results remain distinct. V3.2 shows C1/s42/epoch27, ONNX MAE0.04833 and MC unavailable. Both real HTTP controls returned their own263-row saved results. This task did not rerun model evaluation.

## Verification and limits

Five presentation tests, six release tests and twenty-nine solar/temporal tests passed. Main frontend and embedded Needle builds passed. Global TypeScript retains15 pre-existing diagnostics with zero introduced after normalizing diagnostic line numbers and TypeScript's reordered truncated union text. No dependencies or compiler settings were changed; the audit uses installed TypeScript5.9.3 with command-only `--ignoreDeprecations 5.0`.

Desktop browser inspection covered landing, all dashboard tabs, both languages, active metrics/scatter and the V3.1 landing control. Screenshots show readable content; actual viewport1280×720, document width1280. A requested390px viewport override did not apply (actual1280), so this run does **not** claim a new mobile-width/physical-phone inspection. Prior user PC/phone/AR acceptance remains historical evidence. The same classes/styles/layout and unchanged Sun assets are checked separately; no new pixel-identical before/after claim is made.

Initial sandbox port binds were denied; temporary processes were restarted with approved loopback access. Browser access required localhost and matching test CORS; no production CORS/runtime setting was changed. No existing user process was stopped. Only this task's temporary ports5174/5188/8788/8789 were used and closed afterward.

[verification.json](verification.json) records hash protection, text-only backend substitutions, unchanged layout classes, TypeScript comparison and unchanged tag. Full original F figures and INDEX remain byte-identical at [figures](../../v32f_scientific_package_v1/package/figures/) and [INDEX](../../v32f_scientific_package_v1/package/INDEX.md). They continue to describe candidates and distinct protocols, not exclusively this release.

Scientific limits remain: selection-validation exposure, tolerated low-activity deterioration/negative low-band R², unresolved border/background XAI, no evaluated V3.2 MC, no mobile-inference performance claim. Noise20+deterministic1 remains active. Model file bytes, process RSS, forward latency, HTTP latency and cached response time are distinct. Historical DOI/citations and archived claims retain their identity beneath explicit correction notices.

**COHERENCIA V3.2: COMPLETADA** for the audited active content and source connections. Pending: existing TypeScript debt and a new mobile-width visual check (the browser override was ineffective); scientific limitations remain independent of this content correction. No push, Site publication, GitHub release or Zenodo action. The correction is a separate local commit after the existing tag.
