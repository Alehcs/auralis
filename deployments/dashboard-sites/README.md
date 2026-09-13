# Auralis dashboard — generated static demo

This checkout is the delivery repository for the dashboard Site. The editable
application remains in `../../auralis-front`; do not maintain an independent
source copy here or manually edit `dist`.

Preparation from the Auralis project root:

```sh
# Only when intentionally refreshing saved read-only views; no inference calls:
python3 scripts/export-sites-demo.py
python3 scripts/prepare-monitoring-five.py
npm --prefix auralis-front run build -- --mode sites
node scripts/prepare-dashboard-site.mjs
```

`dist` is a complete static deliverable. `/dashboard/index.html` supports direct
entry independently of an SPA fallback. It has no deployed Python backend.
Simulation embeds the separate, canonical solar Site. Its QR and mobile link
open that solar Site with the selected HMI state.

The public demo includes frozen metrics, an original 1,314-entry catalog and
11 saved HTTP SI results plus the five historical HMI states and their archived
Grad-CAM figures. It contains no model
weights or original `.npy` dataset. Uploads and new inference/XAI requests in Sites are disabled. The five Grad-CAM
figures are generated once locally with the existing backend and then reused. Missing confidence/noise diagnostics remain absent; no values are
invented. `demo/manifest.json` records provenance and hashes.

Only this delivery repository and the existing solar Site repository are used
for Sites publishing. Never commit or push the parent Auralis repository as part
of that operation. Current publication status is recorded in
`../../docs/two-sites-demo.md`.
