# Active local release and recovery

Commands below run from repository root unless stated. Existing Python environment is `~/.pyenv/versions/3.12.7/bin/python3`; ordinary serving needs only package source, `models/` artifacts and processed inputs, never scripts from this experiment. Check that ports are free before starting; stop only processes you started. Local promotion was explicitly authorized and verified; see `activation/REPORT.md`.

## Normal local startup (default V3.2)

From `auralis-back/`, with no AURALIS_RELEASE or AURALIS_TEST_* variables:

```sh
~/.pyenv/versions/3.12.7/bin/python3 -B -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000
```

This uses s42 epoch27, the validated mitigation and noise20+det1. Do not replace a service already using this port; use a free port for an additional instance. Local default promotion does not restart existing user processes or publish the site.

## Explicit per-process selection

```sh
cd auralis-back
AURALIS_RELEASE=3.2 CORS_ORIGINS=http://127.0.0.1:5188 ~/.pyenv/versions/3.12.7/bin/python3 -B -m uvicorn src.api.main:app --host 127.0.0.1 --port 8788
```

In another terminal from repository root:

```sh
cd auralis-front
VITE_API_URL=http://127.0.0.1:8788 npm run dev -- --host 127.0.0.1 --port 5188 --strictPort
```

Open `http://127.0.0.1:5188/dashboard`. Simulation automatically uses the numeric V3.2 overlay after checking the backend identity. No experimental variables are needed. To run V3.1 control, change only `AURALIS_RELEASE=3.1`; its original runtime and resources are selected. Never mix `AURALIS_RELEASE` and `AURALIS_TEST_MODEL`.

CLI from backend:

```sh
AURALIS_RELEASE=3.2 ~/.pyenv/versions/3.12.7/bin/python3 -B scripts/predict.py --image data/processed/hmi.m_45s.2022.03.29_00_01_30_TAI.magnetogram_processed.npy
```

G's explicit `AURALIS_TEST_MODEL=V3.1|C1_s42|C1_s137|C1_s2026` and `AURALIS_TEST_RUNTIME=default|kleidiai_off` mechanism is preserved. Refer to G's runbook for those experimental processes; normal releases do not use that catalog.

## Reproduce checks without research reruns

From repository root:

```sh
~/.pyenv/versions/3.12.7/bin/python3 -B auralis-back/experiments/v32h_release_v1/activation/tests.py
AURALIS_RELEASE=3.1 ~/.pyenv/versions/3.12.7/bin/python3 -B auralis-back/experiments/v32h_release_v1/baseline_tests.py
node --test auralis-back/experiments/v32h_release_v1/temporal.test.mjs prototypes/phase4-unity-needle/web/tests/*.test.mjs
npm --prefix auralis-front run build
~/.pyenv/versions/3.12.7/bin/python3 -B auralis-back/experiments/v32h_release_v1/closure/verify.py
```

`prepare_release.py` and `prepare_temporal.py` document generation but should not overwrite the completed release. `qa_http.py` preserves the measured protocol and refuses existing run directories; use a separately versioned evidence directory for a deliberately authorized rerun. There is no need to repeat it for promotion. `finalize.py` is a prepared-state audit and deliberately asserts default3.1; after an authorized promotion retain this snapshot and write a separate activation check.

## Promotion gate — completed locally

The user's explicit authorization is stored in `activation/authorization.json`. The only execution change at activation is DEFAULT_VERSION=3.2; weights, graph, preprocessing and runtime implementation retain their preparation hashes. `activation/normal_default/` confirms ordinary uvicorn startup with no AURALIS_* variables and correct prediction/alias/uploads/caches/metrics/Agent Lab identity. `activation/rollback_explicit/` confirms V3.1 recovery. Both processes shut down cleanly. No broader benchmark, new XAI sweep or publication was performed.

`activation/smoke.py` preserves the additional checks and refuses existing output directories; do not overwrite recorded results. The preparation `test_release.py`/`finalize.py` remain historical default3.1 checks; use activation checks above for the current state.

## Recovery

For immediate process recovery, stop only the affected owned process and start with `AURALIS_RELEASE=3.1`. This uses the original V3.1 constructor, weights, ONNX, runtime and metrics; its real HTTP startup/fixtures were verified in `runs/round0/unconfigured/`. Frontend labels follow the responding instance and the viewer uses the original V3.1 sequence. A new process resets caches, preventing mixed versions.

For persistent rollback for this local release, set registry DEFAULT_VERSION back to3.1, update only current-status notices, then start normally without environment overrides and verify health/predict. Preserve V3.2 artifacts, temporal overlay and all user edits. Never use git reset/clean or restore whole files from before/ over later user work. No publication or user-service restart is implied.

## Final user acceptance and evidence

PC and phone/AR accepted by user confirmation; see [closure](closure/REPORT.md). The original `activation/verify.py` is a historical activation-snapshot audit; later authorized Sites changes mean it is not the final-tree verifier. Keep its outputs intact. The closure verifier checks frozen release/product/figures and the historical research sources without launching inference.
