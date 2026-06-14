# Auralis Frontend

React, TypeScript, Vite, and Tailwind interface for the Auralis research demo.
The dashboard reads model results and dataset metadata from the FastAPI backend;
it does not provide operational space-weather forecasts or live NASA telemetry.

## Local Development

```bash
npm install
npm run dev
```

The development server runs at `http://localhost:5173` by default. Set
`VITE_API_URL` to override the backend URL; otherwise the frontend uses
`http://localhost:8000`.

## Production Build

```bash
npm run build
```

Generated files under `dist/` are intentionally not committed.
