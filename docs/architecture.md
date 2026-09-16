# Architecture notes

The public portfolio will separate hardware-specific integration from the
reproducible evaluation path. The evaluation path will run from simulated
telemetry and a fixed video sample, allowing reviewers to repeat latency and
throughput measurements without an ESP device or cloud account.

## Planned measurements

- Telemetry ingestion latency (median and p95)
- Vision inference throughput and per-frame latency
- Delivery success under simulated packet loss or reconnects
- Accuracy-latency trade-off at different frame-sampling rates
