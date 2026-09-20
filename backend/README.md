# Backend

The backend is the persistence and API boundary for the public reconstruction.
It receives live telemetry through MQTT, stores validated records in MySQL, and
accepts measured vision benchmark results through REST. The dashboard reads
both data types from this service.

## Responsibilities

- Subscribe to `smart-helmet/telemetry` with MQTT QoS 1.
- Validate and persist synthetic or device telemetry.
- Persist structured frame-sampling benchmark summaries and their individual
  runs.
- Expose health, telemetry, and vision-result REST endpoints.
- Apply versioned MySQL migrations with Flyway.

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/actuator/health` | Backend and database health |
| `GET` | `/api/v1/devices` | Devices with their latest timestamps |
| `GET` | `/api/v1/devices/{deviceId}/latest` | Latest telemetry record |
| `GET` | `/api/v1/devices/{deviceId}/telemetry?limit=100` | Recent telemetry history |
| `POST` | `/api/v1/vision/benchmarks` | Validate and persist one benchmark payload |
| `GET` | `/api/v1/vision/benchmarks/latest` | Latest persisted benchmark and all runs |

The vision endpoint stores measured latency, throughput, and sampled-frame
continuity. It does not accept video frames and does not claim model accuracy.

## Run and test

The recommended workflow starts the backend with the complete stack:

```bash
cp .env.example .env
docker compose up --build -d
./scripts/smoke-test.sh
```

Run the backend integration tests without containers:

```bash
mvn --batch-mode --file backend/pom.xml test
```

Tests use an in-memory H2 database in MySQL compatibility mode and disable the
MQTT connection. Production configuration is supplied through environment
variables documented in `.env.example` and `compose.yaml`.

## Schema ownership

- `V1__create_telemetry_records.sql` creates the live telemetry store.
- `V2__create_vision_benchmarks.sql` creates benchmark and per-stride run tables.

The service uses Spring Data JPA with `ddl-auto=validate`; Flyway, rather than
Hibernate, owns changes to the MySQL schema.
