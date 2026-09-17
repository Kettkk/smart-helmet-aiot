# Architecture notes

The public portfolio will separate hardware-specific integration from the
reproducible evaluation path. The evaluation path will run from simulated
telemetry and a fixed video sample, allowing reviewers to repeat latency and
throughput measurements without an ESP device or cloud account.

## Implemented local telemetry path

The first executable slice is intentionally narrow:

```text
Synthetic telemetry -> Mosquitto -> Spring Boot -> MySQL -> REST clients
```

Docker Compose owns the local services. Flyway owns the database schema, and
the simulator uses a configurable random seed so later performance experiments
can start from a controlled workload. Cloud adapters and physical-device
adapters will remain outside this core path and map into the same telemetry
contract.

## Planned measurements

- Telemetry ingestion latency (median and p95)
- Vision inference throughput and per-frame latency
- Delivery success under simulated packet loss or reconnects
- Accuracy-latency trade-off at different frame-sampling rates
