# Web telemetry dashboard

The dashboard is a responsive working surface for observing the reproducible
local telemetry loop. It is implemented with Vue 3, Vite, ECharts, and Nginx.

## What it shows

- Active-device selection from the backend device registry
- API and telemetry freshness state
- Latest heart rate, body temperature, ambient temperature and humidity, and
  movement speed
- A rolling 30-sample chart for heart rate and temperature
- Observed simulator, MQTT stream, application API, and persistence stages
- Latest synthetic coordinates and pressure value
- The eight newest raw telemetry records
- A measured frame-sampling benchmark with the selected real-time operating
  point, throughput chart, and complete latency table
- Explicit loading, empty, stale-data, and connection-error states

The client polls the local REST API every two seconds. Nginx serves the static
production build and proxies `/api` and `/actuator` to the backend, so the
browser uses one origin and requires no permissive CORS configuration.

The vision benchmark is static, versioned research evidence rather than a live
API response. Regenerate `dashboard/src/vision-results.json` from the canonical
benchmark artifact whenever the experiment changes:

```bash
python experiments/export_dashboard_results.py
```

CI repeats this export and fails if the committed dashboard data no longer
matches `experiments/results/frame-sampling/benchmark.json`.

## Run

Start the complete system from the repository root:

```bash
docker compose up --build -d
./scripts/smoke-test.sh
```

Open `http://localhost:3000`. Override the published port with
`DASHBOARD_PORT` in `.env` if necessary.

For frontend development with the Compose backend still running:

```bash
cd dashboard
npm ci
npm run dev
```

Vite serves the development dashboard at `http://localhost:5173` and proxies
API requests to `http://localhost:8080`.

## Interpretation limits

The current UI labels values as nominal when heart rate is between 50 and 120
BPM, body temperature is between 35 and 38 degrees Celsius, and the helmet is
reported as worn. These are interface demonstration thresholds, not clinically
validated decision rules. The dashboard must not be used to diagnose health
conditions or make safety-critical decisions.

Pipeline indicators are observations derived from reachable APIs, available
records, and data freshness. They are not independent health probes for every
internal component.
