# Architecture notes

The public portfolio will separate hardware-specific integration from the
reproducible evaluation path. The evaluation path will run from simulated
telemetry and a fixed video sample, allowing reviewers to repeat latency and
throughput measurements without an ESP device or cloud account.

## Physical prototype path

```text
Sensors -> STM32 acquisition board -> 31-byte UART frame -> ESP8266
                                                        -> MQTT/TLS -> Huawei IoTDA

ESP32-CAM -> HTTP JPEG/MJPEG stream -> server-side visual processing
```

The ESP8266 and ESP32-CAM integrations are archived in `firmware/`. The STM32
firmware was developed outside this portfolio and is represented only as the
upstream producer of the documented UART frame. Photographs and the ownership
boundary are recorded in `docs/hardware-prototype.md`.

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

## Implemented measurements

- Vision inference throughput and per-frame latency
- MQTT delivery success under controlled loss
- MQTT reconnect and first-message recovery after broker outages
- Latency-throughput trade-off at different frame-sampling rates
