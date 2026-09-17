# Frontend TypeScript debt closure — 2026-09-17

**DEUDA TYPESCRIPT: RESUELTA.** Full frontend `src` and the referenced Vite configuration pass with the installed TypeScript 5.9.3. Coronium V3.2 C1_s42 epoch27 remains active. No model, scientific contract, inference/runtime setting, dataset, frozen prediction, visual asset or approved interface text was changed.

## Initial state and minimal plan

Tracked working tree was clean at the baseline in [baseline.json](baseline.json); existing untracked research was preserved. The main frontend has no installed TypeScript binary of its own. Its existing Needle workspace has TypeScript 5.9.3, also used by the earlier audit and the existing frontend prebuild. No compiler was downloaded.

The ordinary initial check failed with TS5103 because `ignoreDeprecations=6.0` is invalid in 5.9.3. A diagnostic-only command override (`--ignoreDeprecations 5.0`) exposed the same 15 source diagnostics as the prior report: [before.txt](before.txt). This override is not needed by the final command.

Plan executed: correct Recharts content types and optional values; remove the unused import and obsolete suppression; type both translations; retain ES2020 through an equivalent own-property check; remove only the unsupported configuration option. No strictness, library target, skipLibCheck, exclusions or dependency versions changed.

| Cause | Files | Minimal correction | Verification |
|---|---|---|---|
| Tooltip/legend wrapper props omit content payload | `src/app/components/ui/chart.tsx` | Installed Recharts content types; dataKey function narrowed and explicitly stringified for the React key, preserving React key coercion | Full typecheck; unchanged JSX text/style audit |
| Mutable custom payload and unused import | `src/features/dashboard/components/xai-faithfulness.tsx` | Reuse readonly Recharts payload/label types, optional numeric formatting; remove unused Eye | Full typecheck; content/stylesheet audit |
| Formatter parameters may be undefined | `magnetogram-panel.tsx`, `prediction-chart.tsx` | Correct optional parameter types and optional access; retain all formatting for present numbers, no invented zero; remove obsolete expect-error | Typecheck; browser monitoring/pipeline |
| Context admitted only English literal values | `src/lib/i18n/translations.ts` | Union indexed by the existing Language type | Emitted translation JavaScript byte-identical; English/Spanish navigation |
| Object.hasOwn exceeds ES2020 library | `src/lib/frozen-demo.ts` | Equivalent Object.prototype.hasOwnProperty.call; keeps own-property semantics, including inherited-key rejection | Saved-response navigation; unchanged ES2020 target |
| Unsupported compiler option and no ordinary script | `tsconfig.json`, `package.json` | Remove ignoreDeprecations; add local-compiler typecheck for src and Vite config | Normal command exits 0, no manual override |

Correct content typing also exposed the function-valued dataKey branch previously hidden by missing payload types. Its explicit React key conversion is included above. No new any, suppression, double assertion, catch-all declaration or node_modules edit was introduced.

## Reproduce from repository root

```sh
npm --prefix auralis-front run typecheck
npm --prefix auralis-front run build
node --test auralis-back/experiments/v32h_release_v1/coherence/presentation.test.mjs auralis-back/experiments/v32h_release_v1/temporal.test.mjs prototypes/phase4-unity-needle/web/tests/*.test.mjs
node auralis-back/experiments/v32h_release_v1/typescript/verify.mjs
git diff --check
```

The typecheck script explicitly uses the already installed compiler at `prototypes/phase4-unity-needle/web/node_modules/typescript/bin/tsc`. Both project configurations are checked with `--noEmit`. The main build invokes the existing Needle `prebuild` (including its own typecheck), then builds the main frontend. No lockfile changes or installation commands are required in this installed workspace.

## Results and scope

- Before: one blocking configuration diagnostic, then 15 source diagnostics under the temporary diagnostic override. After: **0 diagnostics for the complete frontend and Vite configuration**, ordinary command exits 0; [typecheck.txt](typecheck.txt).
- Both main and Needle builds pass; [build.txt](build.txt). Existing warnings remain: large bundles and Needle MaterialX's browser externalization of node:module. These are not TypeScript failures; no bundling refactor was attempted.
- **34/34 tests pass**: five release-presentation tests, three release temporal tests, twenty-six existing solar/controller tests; [tests.txt](tests.txt).
- Browser QA used an isolated Vite instance on localhost:5188 with `VITE_FROZEN_DEMO=true`, preserving and displaying saved responses; it did not execute inference or XAI. Spanish/English tabs, monitoring, pipeline, experiments/scatter, Agent Lab, logs, settings, embedded viewer loading and standalone viewer were checked. All five dates, return to March29 and magnetogram/B+/B−/solar layers worked. [browser.json](browser.json), [experiments.png](experiments.png), [solar.png](solar.png); no captured browser errors in [browser-errors.json](browser-errors.json).
- One automation click failed to resolve inside the iframe despite a visible locator; the same loaded viewer's own linked route was used for the five-state/layer interaction checks. This tooling incident did not require application changes. No claim of pixel-equivalent screenshots or new physical AR session is made.
- [verification.json](verification.json) verifies 273 protected hashes, unchanged model tag, translations' emitted runtime, JSX text and styling expressions, and compiler/package configuration limits. [protected.json](protected.json) includes backend source/models/contracts, frontend public resources, Needle source/public resources and the unchanged F package. All match the before snapshot.
- The temporary server and both QA tabs were closed. No user service was interrupted.

## User acceptance, history and publication

The user confirmed that **the mobile review after the presentation-consistency correction is resolved**. Source: user confirmation in this task. Device, browser/version, physical test date, recordings, FPS and other measurements: **not recorded**. This resolves the mobile-review pending item in the historical coherence report; it does not represent a newly performed automated or physical AR validation.

The previous reports remain historical evidence. The scientific limitations (selection validation, low-activity deterioration, border/background XAI) remain unchanged. V3.1 recovery remains available via `AURALIS_RELEASE=3.1`; no runtime was switched here.

This is a separate local correction after `coronium-v3.2`; that tag is unchanged. No push, Site update, public release or Zenodo action. There are no remaining TypeScript diagnostics in the checked frontend scope. Bundle warnings and scientific limitations are separate from this closure.
