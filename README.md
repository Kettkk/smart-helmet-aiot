# Smart Helmet AIoT: Edge-to-Cloud Safety Monitoring

A reproducible research prototype for outdoor safety monitoring. The project
combines low-cost telemetry, camera-based perception, and multi-client
monitoring in an edge-to-cloud pipeline.

## Research question

How do sensing frequency, frame sampling, and network conditions affect
end-to-end latency and detection utility in a resource-constrained outdoor
monitoring system?

## System concept

```text
Sensors / ESP device ──MQTT──> ingestion service ──> database ──> dashboard / Android app
Camera stream ───────────────> vision service ─────> structured detections ─┘
```

The portfolio version is intentionally hardware-independent: the `simulator/`
module will provide reproducible telemetry and video inputs, while hardware
firmware remains an optional integration layer.

## Repository structure

```text
docs/             Architecture, design decisions, demo, and limitations
firmware/         Optional ESP8266 / ESP32-CAM integration code
vision-service/   Reproducible object-detection service
backend/          Telemetry ingestion and application API
dashboard/        Web visualisation client
android/          Android monitoring client
simulator/        Hardware-independent telemetry and video simulators
experiments/      Benchmark scripts, anonymised results, and plots
data/             Small, non-sensitive sample data only
```

## Current status

This repository is being reconstructed from a graduation-project prototype.
Only code, data, and results that can be reproduced and safely shared will be
added. No production credentials, cloud endpoints, personal data, or raw user
records belong in this repository.

## Reproduction

The local runnable pipeline and experiments will be documented here as each
module is migrated. Development configuration must be supplied through local
environment variables; see `.env.example`.

## Responsible disclosure

Please report potential security issues privately as described in
[SECURITY.md](SECURITY.md).
