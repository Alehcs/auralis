# Auralis dashboard — generated static V3.2 demo

The editable application remains in ../../auralis-front. This delivery repository
contains the exact Sites-mode build; no Python backend, weights or raw NPY inputs.

Refresh intentionally from the Auralis root with scripts/export-sites-v32.py
(read-only metadata plus verified saved predictions; zero new inference),
then build the frontend in --mode sites and run scripts/prepare-dashboard-site.mjs.
Legacy scripts/export-sites-demo.py and prepare-monitoring-five.py preserve the
historical V3.1 workflow and must not be used for this V3.2 release.

Sixteen existing cases and images are preserved, with s42/epoch27 deterministic
predictions from E.1/H and the release's own263 selection-validation results.
Missing confidence/noise is null, not zero. Historical V3.1 Grad-CAM PNGs and
provenance remain preserved but are not shown as V3.2 explanations. Five March2022
quick-access buttons remain available independently of Grad-CAM availability.

Simulation embeds the existing solar Site with explicit release3.2, retaining
the selected state in its HTTPS QR. The public solar default is also3.2 so old
QR links receive the update. Explicit release3.1 remains available for history.

Only the two Sites delivery repositories are committed/pushed for publication;
no parent Auralis commit. See ../../evidence/sites-v32 and ../../docs/two-sites-demo.md.
