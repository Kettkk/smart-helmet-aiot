# Local system closed loop

This is the independently reproducible Smart Helmet system. It excludes Huawei
Cloud and physical devices, replacing them with controlled telemetry and video
inputs. The two paths meet at the Spring Boot/MySQL boundary and are read by the
Vue dashboard.

```text
Python simulator -> MQTT topic -> Spring Boot validator -> MySQL -> REST -> Vue
                         Mosquitto                  Flyway             dashboard

Fixed video -> YOLO benchmark -> POST Spring Boot -> MySQL -> REST dashboard
```

## Start and verify

1. Start Docker Desktop and wait until its engine reports that it is running.
2. Copy the safe local defaults and start the five live services:

   ```bash
   cp .env.example .env
   docker compose up --build -d
   docker compose ps
   ```

3. Wait until `backend`, `mysql`, and `mosquitto` are healthy, then run:

   ```bash
   ./scripts/smoke-test.sh
   ```

   The smoke test publishes the committed vision benchmark payload before
   checking that it can be read through the backend.

4. Inspect a short history or follow the publisher logs:

   ```bash
   curl 'http://localhost:8080/api/v1/devices/helmet-sim-001/telemetry?limit=3'
   docker compose logs -f simulator
   ```

5. Restart the application layer and confirm that database-backed history is
   still present:

   ```bash
   docker compose restart backend simulator
   ./scripts/smoke-test.sh
   ```

6. Stop the stack. The named MySQL volume is retained unless it is explicitly
   removed.

   ```bash
   docker compose down
   ```

## MQTT contract

- Topic: `smart-helmet/telemetry`
- Quality of service: QoS 1
- Encoding: UTF-8 JSON
- Timestamp: UTC ISO 8601

Example payload:

```json
{
  "deviceId": "helmet-sim-001",
  "timestamp": "2026-09-17T10:00:00Z",
  "wearing": true,
  "bodyTemperatureC": 36.6,
  "ambientTemperatureC": 22.0,
  "ambientHumidityPct": 62.0,
  "heartRateBpm": 78,
  "latitude": 30.2741,
  "longitude": 120.1551,
  "impactPressurePa": 1013.0,
  "speedMps": 1.25
}
```

The backend rejects malformed JSON and values outside basic physical ranges.
This is input validation, not medical interpretation.

## Acceptance criteria

The first loop is accepted when all of the following hold:

- `docker compose config --quiet` succeeds.
- `mvn -f backend/pom.xml test` reports zero failures.
- The simulator publishes a sample every configured interval.
- The backend subscribes to the configured topic and stores valid messages.
- The health endpoint reports `UP`.
- Latest and history endpoints return `helmet-sim-001`.
- A benchmark payload can be persisted idempotently and returned from
  `/api/v1/vision/benchmarks/latest`.
- The dashboard proxy returns the persisted vision result rather than a bundled
  frontend JSON file.
- Data remains queryable after restarting the backend container.
- No cloud credentials, production endpoints, or personal measurements are
  required.

## Troubleshooting

- `Cannot connect to the Docker daemon`: launch Docker Desktop, then retry.
- `failed to fetch anonymous token` or an `auth.docker.io` timeout: this is a
  Docker Hub connectivity failure before project compilation starts. Pull the
  two backend base images separately, then rerun Compose:

  ```bash
  docker pull eclipse-temurin:17-jre
  docker pull maven:3.9.9-eclipse-temurin-17
  docker compose up --build -d
  ```

  A successful pull is cached locally, so the following build no longer needs
  to fetch those layers. If a pull times out, retry it after confirming Docker
  Desktop's proxy or VPN can reach `https://auth.docker.io`.
- Port `8080` or `1883` already in use: edit `BACKEND_PORT` or `MQTT_PORT` in
  `.env`.
- No sample returned: inspect `docker compose ps` and then
  `docker compose logs backend simulator mosquitto`.
- Schema startup failure after a local schema change: this prototype uses a
  persistent named volume. For disposable test data only, stop the stack and
  remove its volume before rebuilding.

The anonymous Mosquitto listener is for local reproducibility only. It must not
be exposed to an untrusted network or reused for deployment.

## Hybrid fallback when Java images still cannot be pulled

If Docker Hub times out while resolving the Maven or Eclipse Temurin images,
run only the already downloaded infrastructure images and start the application
processes on the host:

```bash
docker compose up -d mysql mosquitto

SPRING_DATASOURCE_URL='jdbc:mysql://localhost:3306/smart_helmet?serverTimezone=UTC&useSSL=false&allowPublicKeyRetrieval=true' \
SPRING_DATASOURCE_USERNAME=smart_helmet \
SPRING_DATASOURCE_PASSWORD=local-development-only \
MQTT_BROKER_URI=tcp://localhost:1883 \
mvn -f backend/pom.xml spring-boot:run
```

In a second terminal, create a disposable Python environment outside the
repository and start the simulator:

```bash
python3 -m venv /tmp/smart-helmet-simulator-venv
/tmp/smart-helmet-simulator-venv/bin/pip install -r simulator/requirements.txt
/tmp/smart-helmet-simulator-venv/bin/python simulator/telemetry_simulator.py
```

In a third terminal, run the dashboard development server:

```bash
npm --prefix dashboard ci --no-audit --no-fund
npm --prefix dashboard run dev
```

Run `DASHBOARD_URL=http://localhost:5173 ./scripts/smoke-test.sh` from a fourth
terminal. Stop the three host processes with `Ctrl+C`, then stop the
infrastructure with `docker compose down`.
