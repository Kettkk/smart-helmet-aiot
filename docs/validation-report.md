# Local validation report

Validation date: 2026-09-20

## Environment

- macOS with Docker Desktop 27.5.1
- Docker Compose v2.32.4
- OpenJDK 23 executing a Java 17 target
- Maven 3.9.9
- MySQL 8.4 container
- Eclipse Mosquitto 2.0 container

The hybrid workflow was first used after Docker Hub timed out while resolving
the Java build images. After separately pulling the Maven and Eclipse Temurin
base images, the complete Compose workflow was built and validated. The Vue
dashboard was subsequently added as the fifth service and verified through its
Nginx reverse proxy.

## Results

| Check | Result |
|---|---|
| Backend integration tests | 7 passed, 0 failed |
| Compose configuration validation | Passed |
| Backend, simulator, and dashboard image builds | Passed |
| MySQL and Mosquitto health checks | Healthy |
| Backend container health check | Healthy |
| Dashboard container health check | Healthy |
| Five-container Compose startup | Passed |
| Flyway migration | Version 1 applied successfully |
| MQTT subscription | Connected to `smart-helmet/telemetry` |
| Synthetic telemetry publication | Passed |
| MQTT-to-MySQL ingestion | Passed |
| Health endpoint | `UP` |
| Device discovery endpoint | Returned `helmet-sim-001` |
| Latest telemetry endpoint | Returned a valid synthetic sample |
| Three-record history query | Returned 3 records |
| Dashboard production build | Passed |
| Dashboard dependency audit | 0 vulnerabilities |
| Dashboard page smoke check | Passed |
| Dashboard-to-API reverse proxy | Returned telemetry records |
| Data after backend restart | Still queryable |
| Fixed-video sample download and SHA-256 verification | Passed |
| YOLO fixed-video demo | Passed; structured detections and annotated video generated |
| Frame-sampling benchmark | Passed for strides 1, 2, 5, and 10 |
| Vision benchmark API validation and persistence tests | 4 passed, 0 failed |
| Vision plots and backend payload export | Passed |
| Dashboard retrieval through backend vision API | Passed |
| MQTT delay and controlled-loss benchmark | Passed; 3 repeats per condition |
| Broker outage and reconnect benchmark | Passed for 1, 3, and 5 seconds |

Example smoke-test output:

```text
Smoke test passed for helmet-sim-001
Dashboard available at http://localhost:3000
Device list: [{"deviceId":"helmet-sim-001", ...}]
History count: 3
Latest vision benchmark is available through the backend API.
```

All generated physiological and location values were synthetic. No cloud
credentials, hardware identifiers, or personal measurements were used.

## Scope

This report verifies the live local telemetry path from simulator to MQTT,
Spring Boot, MySQL, REST, and the web dashboard. It also verifies the separate
offline fixed-video pipeline, persistence of its structured benchmark summary
through Spring Boot, dashboard retrieval through REST, and the isolated MQTT
reliability experiment. There is no live video-frame or vision WebSocket path.

It does not validate the Android client, physical sensors, Huawei Cloud
deployment, long-duration load limits, vision accuracy, or medical/safety
suitability. Detailed methods and machine-specific results are recorded in
`docs/vision-demo.md` and `docs/network-reliability.md`.
