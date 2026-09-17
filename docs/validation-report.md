# Local validation report

Validation date: 2026-09-17

## Environment

- macOS with Docker Desktop 27.5.1
- Docker Compose v2.32.4
- OpenJDK 23 executing a Java 17 target
- Maven 3.9.9
- MySQL 8.4 container
- Eclipse Mosquitto 2.0 container

The hybrid workflow was used because Docker Hub timed out while resolving the
Java build images. MySQL and Mosquitto ran in containers; Spring Boot and the
Python simulator ran on the host.

## Results

| Check | Result |
|---|---|
| Backend integration tests | 3 passed, 0 failed |
| Compose configuration validation | Passed |
| MySQL and Mosquitto health checks | Healthy |
| Flyway migration | Version 1 applied successfully |
| MQTT subscription | Connected to `smart-helmet/telemetry` |
| Synthetic telemetry publication | Passed |
| MQTT-to-MySQL ingestion | Passed |
| Health endpoint | `UP` |
| Device discovery endpoint | Returned `helmet-sim-001` |
| Latest telemetry endpoint | Returned a valid synthetic sample |
| Three-record history query | Returned 3 records |
| Data after backend restart | Still queryable |

Example smoke-test output:

```text
Smoke test passed for helmet-sim-001
Device list: [{"deviceId":"helmet-sim-001", ...}]
History count: 3
```

All generated physiological and location values were synthetic. No cloud
credentials, hardware identifiers, or personal measurements were used.

## Scope

This report verifies the local telemetry path from simulator to MQTT, Spring
Boot, MySQL, and REST. It does not validate the planned vision service, web
dashboard, Android client, physical sensors, cloud deployment, load limits, or
medical/safety suitability.
