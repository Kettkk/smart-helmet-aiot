# Local telemetry closed loop

This is the smallest independently reproducible slice of the Smart Helmet
system. It deliberately excludes Huawei Cloud, physical sensors, camera input,
and user interfaces so that the data path can be verified before more modules
are added.

```text
Python simulator -> MQTT topic -> Spring Boot validator -> MySQL -> REST API
                         Mosquitto                  Flyway
```

## Start and verify

1. Start Docker Desktop and wait until its engine reports that it is running.
2. Copy the safe local defaults and start the four services:

   ```bash
   cp .env.example .env
   docker compose up --build -d
   docker compose ps
   ```

3. Wait until `backend`, `mysql`, and `mosquitto` are healthy, then run:

   ```bash
   ./scripts/smoke-test.sh
   ```

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
- Data remains queryable after restarting the backend container.
- No cloud credentials, production endpoints, or personal measurements are
  required.

## Troubleshooting

- `Cannot connect to the Docker daemon`: launch Docker Desktop, then retry.
- Port `8080` or `1883` already in use: edit `BACKEND_PORT` or `MQTT_PORT` in
  `.env`.
- No sample returned: inspect `docker compose ps` and then
  `docker compose logs backend simulator mosquitto`.
- Schema startup failure after a local schema change: this prototype uses a
  persistent named volume. For disposable test data only, stop the stack and
  remove its volume before rebuilding.

The anonymous Mosquitto listener is for local reproducibility only. It must not
be exposed to an untrusted network or reused for deployment.
