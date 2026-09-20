# Architecture notes

The repository separates the historical physical prototype from two public,
reproducible paths. This distinction prevents archived hardware and cloud
integrations from being mistaken for dependencies of the current system.

## Implemented public paths

### Live telemetry

```text
Seeded telemetry simulator
           |
           | MQTT QoS 1
           v
      Mosquitto broker
           |
           v
Spring Boot ingestion and REST API -> MySQL
           |
           | REST polling every 2 seconds
           v
       Vue dashboard
```

Docker Compose runs the broker, backend, database, simulator, and dashboard.
Flyway owns the database schema. The simulator uses a fixed seed so network and
ingestion experiments can begin with a controlled workload.

### Offline vision evaluation

```text
Public-domain source video
           |
           | download + source SHA-256 verification
           v
Pinned 20-second H.264 sample
           |
           | prepared-sample SHA-256 verification
           v
CPU YOLO batch inference
           |
           +--> annotated MP4
           +--> detections.jsonl
           +--> frame-metrics.csv / summary.json
                         |
                         +--> versioned plots
                         +--> POST /api/v1/vision/benchmarks
                                      |
                                      v
                              Spring Boot -> MySQL
                                      |
                                      v
                              Vue dashboard REST view
```

The vision pipeline is an offline, fixed-input experiment. Its summary is
converted to a validated API payload, persisted in `vision_benchmarks` and
`vision_runs`, and returned by `/api/v1/vision/benchmarks/latest`. The dashboard
does not contain a compiled fallback result. There is still no live video-frame
endpoint or WebSocket link from the vision service to the dashboard.

## Historical physical prototype

```text
Sensors -> STM32 acquisition board -> 31-byte UART frame -> ESP8266
                                                        -> MQTT/TLS -> Huawei IoTDA

ESP32-CAM -> HTTP JPEG/MJPEG stream -> historical server/client integration
```

The ESP8266 and ESP32-CAM sources are archived in `firmware/`. The STM32
firmware was developed outside this portfolio and is represented only as the
upstream producer of the documented UART frame. Photographs, ownership
boundaries, and hardware limitations are recorded in
`docs/hardware-prototype.md`.

Dashed lines in the architecture figure connect these archived physical inputs
to the controlled substitutes used by the public reconstruction. They describe
research provenance, not a runtime connection.

## Implemented measurements

- YOLO throughput, per-inference latency, and sampled-frame detection continuity
- MQTT delivery under seeded application-layer delay and loss
- MQTT reconnect and first-message recovery after real broker outages
- Latency-throughput trade-offs at different frame-sampling rates

The research question is limited to latency, throughput, detection continuity,
and reliability. The project makes no precision, recall, or mAP claim because
the fixed video is not labelled.
