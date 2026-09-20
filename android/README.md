# Android client — historical boundary

The undergraduate prototype included an Android monitoring client for sensor
status, location, navigation, and image-stream viewing. Its original source is
not included in this public reconstruction because it was coupled to private
deployment endpoints and accessed application data through architecture that is
not reproduced here.

This directory documents scope; it is not an empty claim of a runnable module.
The tested public client is the Vue dashboard.

## Intended public boundary

A future Android reconstruction should consume only documented backend APIs:

- `GET /api/v1/devices`
- `GET /api/v1/devices/{deviceId}/latest`
- `GET /api/v1/devices/{deviceId}/telemetry`
- `GET /api/v1/vision/benchmarks/latest`

It should not connect directly to MySQL, embed credentials, or assume access to
the historical Huawei Cloud deployment. Live camera delivery would require a
separately designed, authenticated streaming interface; the current backend
serves benchmark summaries, not video frames.

## Portfolio status

- Historical Android functionality is described as prototype evidence only.
- No Android build is included in CI or Docker Compose.
- No Android feature is required to reproduce the telemetry or vision-result
  loops.
- Rebuilding this client is outside the current research question, which is
  limited to latency, throughput, detection continuity, and reliability.
