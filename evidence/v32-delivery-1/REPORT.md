# Coronium V3.2 — approved delivery 1

Delivery record: 2026-09-17. **ENTREGA V3.2: COMPLETADA** once the checked delivery commit and annotated `coronium-v3.2-delivery-1` tag reach origin/main. The tag points to this documentation commit, which includes the approved functional revision `c159a67a89a6217c4d3de8224e22cf28a82cbfb9`, presentation correction `5ea8d07b` and local release closure `eb222b18`. Resolve the final full delivery commit with `git rev-parse coronium-v3.2-delivery-1^{commit}`. The model name remains V3.2; the existing `coronium-v3.2` tag is not moved.

## Published sites

| Site | Version and source commit | Mode / access |
|---|---|---|
| [Dashboard](https://auralis-dashboard.alejandro-cornejog4.chatgpt.site/) | v6 / `270284bec2c80c69b23cd59ba1d89dc9534d30b7` | Owner-private; saved results, not live inference |
| [Solar viewer / QR](https://auralis-phase4-needle-probe.alejandro-cornejog4.chatgpt.site/phase6/) | v14 / `8810f6c694036ac252a97a9f76e4dac0f7512482` | Public; five frozen observations/results |

Both deployments succeeded; [deployment.json](deployment.json) records their exact IDs. The unchanged solar source was rebuilt, verified and republished as the existing v14, not relabeled as a new visual revision. Dashboard v6 contains the actual updated Sites-mode build from c159a67a. Domains, access policy, historical pages, maps, materials, timeline and compact AR panel remain unchanged. No API, tunnel, new infrastructure, runtime weakening or paid service was introduced. No GitHub Release or Zenodo publication was created.

Active local model: **Coronium V3.2 C1_s42 epoch27**, CPU4/1 with `mlas.disable_kleidiai=1`, noise20 + deterministic1 retained. The static sites do not run this backend; saved responses remain identified as such and unavailable diagnostics are not fabricated. Local V3.1 recovery remains available.

## Preflight and checks

- Verified main HEAD c159a67a, the approved commit ancestry, clean tracked working tree and origin/main with no remote-only commits (three approved local commits ahead). Existing untracked research excluded. Pattern scan of259 approved changed paths found no credential/private-key tokens. Existing public Vite `.env.production` contains only the dashboard origin and default release3.2: user delegated the explicit exception decision, and it was retained without rewriting history. No private environment files or credentials were added. Site archives contain only hosting metadata and generated static output, never .env files or backend source/weights/raw NPY data.
- `npm --prefix auralis-front run typecheck`:0 diagnostics, installed TypeScript5.9.3, no override. `npm --prefix auralis-front run build -- --mode sites`: main frontend and Needle builds pass. Existing large-bundle and MaterialX node:module externalization warnings remain non-blocking. [Logs](build.txt).
-34 presentation/temporal/solar tests and6 activation/recovery tests pass; [tests](tests.txt), [release](release.txt). No training, export, benchmark or scientific sweep.
-273 protected hashes remain identical to the [TypeScript closure baseline](../../auralis-back/experiments/v32h_release_v1/typescript/protected.json), including weights, backend, visual sources/assets and F. Served assets verified over HTTPS:69 solar +46 dashboard files byte-identical to the approved output, in addition to HTML/routes and JSON checks. See [solar-assets.json](solar-assets.json), [dashboard-assets.json](dashboard-assets.json). HTML may include hosting injection; JS/CSS/data/visual assets are checked byte for byte.
- Public browser checks: dashboard authenticated by the user, landing identity/metrics, all tabs, saved monitoring/Agent Lab, scatter, languages, mobile menu, embedded viewer; solar five dates, four layers and numerical values. Real CSS viewports390×844 and1280×900, page scrollWidth matching width; [viewports.json](viewports.json), browser records and viewport screenshots. No captured JavaScript errors. QR decoded in software to the HTTPS selected state with release3.2; [qr.json](qr.json). No new physical AR placement/performance test is claimed. Prior PC/phone/AR acceptance remains user-confirmed.
- An initial private HTTP probe omitted the documented Bearer prefix and returned401; corrected verification passed without changing authentication. Browser initially required login; the user supplied it, then visual checks completed. A full-page stitched screenshot was discarded because it duplicated sections; viewport screenshots and actual DOM dimensions were used instead.
- Sites skill packaging helper was unavailable locally. Static tar archives were built from the existing hosting configuration and validated generated output only; save/version/deploy used the existing Sites connector. Temporary credentials stayed outside files/commits. No new site was created.

Reproduction commands: normal typecheck/build above; existing test commands are in the [TypeScript closure](../../auralis-back/experiments/v32h_release_v1/typescript/REPORT.md). `verify-published.py` checks the current deployed bytes against the local delivery output and expects the private Site's existing short-lived access token in SITES_VERIFY_TOKEN, never hardcode it. It is an HTTP verifier, not a backend.

## Recovery and limits

- Local backend: restart only the owned instance with `AURALIS_RELEASE=3.1`; [RUNBOOK](../../auralis-back/experiments/v32h_release_v1/RUNBOOK.md). Preserve all V3.2 and user files. The explicit viewer `?release=3.1` retains its historical results.
- Site rollback: redeploy the existing saved dashboard v5 using the private deployment operation and unchanged owner access; solar v14 already matches its pre-delivery revision. Exact saved-version IDs in [rollback.json](rollback.json). No reset, force-push, data deletion or access-policy change is needed.
- Validation is checkpoint-selection validation, not an independent/temporal test; low-activity deterioration and border/background XAI doubts remain. MC, input noise and deterministic results remain distinct. Mac timing is not mobile performance evidence.
- [F figures](../../auralis-back/experiments/v32f_scientific_package_v1/package/figures/) and [INDEX](../../auralis-back/experiments/v32f_scientific_package_v1/package/INDEX.md) remain unchanged, including comparisons among candidates rather than just the served seed.

No functional source changes in this delivery. New commit scope: this record/evidence, publication note and generated dashboard build hash manifest. Existing model tag unchanged; only main and the new delivery tag are authorized for this push. Browser viewport override restored; only agent-created QA tabs closed, user dashboard tab preserved. No local servers were started or user services interrupted. No later phase is opened.
