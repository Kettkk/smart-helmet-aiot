# Smart Helmet AIoT

## A Reproducible Edge-to-Cloud Safety Monitoring System

**Technical report, version 1.1**<br>
**September 2026**

**Author:** Tuoke Ke<br>
**Contact:** ketk0917@163.com | [github.com/Kettkk](https://github.com/Kettkk)<br>
**Research artifact:** [release v1.0.0](https://github.com/Kettkk/smart-helmet-aiot/releases/tag/v1.0.0), commit [`716644f`](https://github.com/Kettkk/smart-helmet-aiot/commit/716644fe3c1a0a9a2f04d10ef4b6d237b1ae2145). The reported measurements are pinned to this release baseline; version 1.1 adds reporting context and does not alter the experiments.

## Abstract

This report presents a reproducible research prototype for studying an edge-to-cloud monitoring pipeline derived from a physical smart-helmet project. The public system combines MQTT telemetry, a Spring Boot backend, MySQL persistence, a Vue dashboard, fixed-video person detection, and repeatable network-condition experiments. Its research question is deliberately narrow: how do frame-sampling frequency and network conditions affect latency, throughput, detection continuity, and delivery reliability? On a 20-second, 600-frame reference video, increasing frame stride from 1 to 10 raised processing throughput from 7.59 to 55.35 FPS while sampled-frame detection continuity changed from 99.50% to 98.33%. In controlled MQTT trials, application-level loss produced the expected reduction in delivery rate, while broker outages of 1-5 seconds were followed by subscription recovery in about 0.78 seconds after broker availability. These measurements establish a transparent systems baseline without making claims about detector accuracy, medical validity, or certified safety performance.

## 1. Problem and Research Scope

Outdoor monitoring systems must combine sensing, communication, perception, storage, and user-facing feedback under resource and network constraints. A prototype can appear functional while hiding important trade-offs: processing every frame can overload the pipeline, network impairment can delay or remove telemetry, and separate subsystems can produce outputs that never reach the user interface.

This project asks:

> How do frame-sampling frequency and network conditions affect the latency, throughput, reliability, and detection continuity of a resource-constrained edge-to-cloud monitoring pipeline?

The evaluation is limited to four measurable system properties:

- inference latency;
- pipeline throughput;
- sampled-frame detection continuity;
- MQTT delivery and recovery reliability.

The project does not claim detector precision, recall, mAP, medical validity, energy optimality, or production safety certification. Those questions require ground-truth labels, clinical or field protocols, and hardware instrumentation that are outside this release.

## 2. System Design

The repository exposes two reproducible paths that converge in the backend and dashboard.

### 2.1 Telemetry path

```text
Telemetry simulator / ESP8266
              |
          MQTT QoS 1
              v
        Eclipse Mosquitto
              |
              v
       Spring Boot backend
              |
              v
             MySQL
              |
           REST API
              v
         Vue dashboard
```

The simulator makes the public loop independent of physical hardware. The archived ESP8266 firmware documents the original bridge from an external STM32-based sensor board to cloud messaging. The STM32 firmware was not developed by the repository author and is not included.

### 2.2 Vision path

```text
SHA-256 verified 20-second video
              |
              v
       YOLO11n CPU inference
              |
     JSONL / CSV / annotated MP4
              |
          HTTP POST
              v
       Spring Boot backend
              |
             MySQL
              |
          HTTP GET latest
              v
         Vue dashboard
```

The video downloader records the source URL and verifies the expected SHA-256 digest. The benchmark runner executes the same clip with frame strides 1, 2, 5, and 10. A publication script submits the benchmark summary to the backend, which persists the run and exposes the latest result to the dashboard.

### 2.3 Physical prototype provenance

The physical helmet used an ESP32-CAM for imaging and an ESP8266 as a UART-to-network bridge. Sensor values originated from an STM32-based subsystem developed by another contributor. Hardware photographs and the two authored firmware modules are included as provenance, but the public Docker workflow uses simulators so that a reviewer can reproduce the software results without the device.

## 3. Implementation

The backend is implemented with Java and Spring Boot. Flyway migrations define telemetry and vision-benchmark tables, and integration tests verify API behavior and persistence. Mosquitto supplies the MQTT broker; MySQL stores the received records. The dashboard is a Vue application that polls the REST endpoints and presents telemetry status, alerts, and the most recent vision benchmark. Docker Compose provides a shared local environment.

The vision service uses Python, OpenCV, and Ultralytics YOLO. Each run records the effective sampling rate, mean and p95 inference latency, pipeline throughput, detection counts, and sampled-frame continuity. Raw detections are retained as JSONL and CSV. Plotting scripts regenerate PNG and SVG figures from the stored results.

Network experiments use a seeded simulator and repeat each condition three times. Added delay is applied before publication. Loss is intentionally applied at the application layer, making the realized send count observable and deterministic. Outage trials stop and restart the broker, then measure subscription recovery and time to the first delivered message. These experiments test the public messaging loop, not radio-layer loss or cellular handover.

The principal independent contributions are:

- the public edge-to-cloud architecture and reproducible Docker workflow;
- the ESP8266 parser and cloud integration, plus ESP32-CAM integration;
- telemetry ingestion, persistence, REST delivery, and dashboard presentation;
- fixed-input vision benchmarking and backend publication;
- controlled frame-sampling and network-reliability experiments;
- documentation of scope, provenance, limitations, and repeatability.

## 4. Experimental Method

### 4.1 Vision benchmark

The fixed input is a 20-second H.264 video at 1280 x 720 and 30 FPS, containing 600 frames. YOLO11n runs on CPU with image size 640, confidence threshold 0.25, and the `person` class as the target. Four frame strides are evaluated. Continuity is defined as the percentage of sampled frames in which at least one target detection is present. It is not an accuracy metric.

| Stride | Sampling rate | Mean latency | p95 latency | Pipeline throughput | Continuity |
|---:|---:|---:|---:|---:|---:|
| 1 | 30 FPS | 124.00 ms | 317.43 ms | 7.59 FPS | 99.50% |
| 2 | 15 FPS | 109.75 ms | 116.37 ms | 16.08 FPS | 99.33% |
| 5 | 6 FPS | 108.47 ms | 114.88 ms | 34.56 FPS | 99.17% |
| 10 | 3 FPS | 110.14 ms | 114.68 ms | 55.35 FPS | 98.33% |

### 4.2 Network benchmark

Delay trials use 0, 25, 50, 100, and 200 ms of added delay, with three repeats and 20 messages per repeat. Loss trials use seeded application-level loss rates of 0%, 5%, 10%, 20%, 30%, and 40%, with three repeats and 100 attempted messages per repeat. Outage trials stop the broker for 1, 3, and 5 seconds, with three repeats per condition.

## 5. Results

### 5.1 Frame sampling

Stride 1 could not process the 30 FPS source in real time on the evaluated CPU path, reaching 7.59 pipeline FPS. Stride 5 processed the sampled workload at 34.56 pipeline FPS while retaining 99.17% sampled-frame continuity. Stride 10 increased throughput further, but continuity fell to 98.33%. The result supports frame sampling as a practical load-control mechanism for this clip and configuration, while showing that continuity should be monitored rather than assumed.

### 5.2 Added delay and loss

Mean observed latency increased from 2.74 ms at the zero-delay condition to 207.91 ms with 200 ms added delay. Every message that was actually published was delivered in these trials. Seeded loss reduced the attempted-message delivery rate from 100% at the 0% condition to 62% at the nominal 40% condition. The realized rates differ from nominal values because each finite run samples a seeded Bernoulli process.

| Nominal loss | Attempted-message delivery rate |
|---:|---:|
| 0% | 100.00% |
| 5% | 94.67% |
| 10% | 88.00% |
| 20% | 83.33% |
| 30% | 67.67% |
| 40% | 62.00% |

### 5.3 Broker outage and recovery

After the broker became available, mean subscription recovery time remained between 776 and 794 ms for outages of 1-5 seconds. Mean time to the first delivered message remained between 818 and 836 ms. All nine outage trials recovered successfully. Outage duration therefore changed total interruption length, but did not materially change post-availability client recovery in this local setup.

## 6. Limitations

- Vision inference is an offline fixed-video benchmark rather than a live ESP32-CAM stream.
- The video has no human-annotated ground truth, so continuity must not be interpreted as precision, recall, or accuracy.
- Network experiments run on one Docker host. Application-level loss is not equivalent to link-layer packet loss.
- Public reproducibility relies on simulators; the physical prototype is documented but not required by the automated loop.
- The Android client is retained as historical project context and is not part of the current Docker validation path.
- The prototype has not undergone long-duration outdoor deployment, medical validation, or safety certification.

## 7. Threats to Validity

**Internal validity.** The benchmark runner fixes the video, model, image size, threshold, frame strides, random seed, and message counts. This supports repeatability, but a fixed clip and one CPU path cannot eliminate implementation- or machine-specific effects. The raw JSONL and CSV outputs, plotting scripts, and configurations are versioned so that each derived figure can be inspected.

**Construct validity.** Sampled-frame continuity measures whether the detector returned at least one `person` detection on a sampled frame. It is not precision, recall, mAP, or a safety outcome because the clip has no human-annotated ground truth. Application-level seeded loss intentionally measures attempted-message delivery rather than radio-layer packet loss. The report uses those names consistently to avoid stronger claims.

**External validity.** The one 20-second hiking clip, local Docker host, and simulator-driven telemetry do not represent all outdoor lighting, motion, device hardware, wireless conditions, or deployment durations. The physical ESP32-CAM and ESP8266 prototype provides provenance, but it is not required by the public experiments. Future field studies should repeat the tests across labeled clips, devices, networks, and durations.

**Conclusion validity.** Network conditions have three repeats per setting and the vision study reports deterministic fixed-input comparisons, not confidence intervals. The results support directional system trade-offs in this setup only. Longer runs, confidence intervals, independent hardware, and `tc netem` validation are planned before generalizing beyond the prototype.

## 8. Future Evaluation

Future work remains within the defined systems scope: longer repeated runs, confidence intervals, Linux `tc netem` validation, controlled tests on the physical ESP devices, and adaptive sampling policies evaluated only against latency, throughput, continuity, and reliability. Ground-truth accuracy evaluation would require a separately labeled dataset and a revised research protocol.

## 9. Reproducibility

```bash
git clone https://github.com/Kettkk/smart-helmet-aiot.git
cd smart-helmet-aiot
cp .env.example .env
docker compose up --build -d
./scripts/smoke-test.sh
./scripts/run-vision-benchmark.sh
./scripts/publish-vision-results.sh
./scripts/run-network-experiments.sh
```

Raw results, generated figures, test scripts, architecture documentation, and a validation report are versioned in the repository. The fixed video itself is excluded from Git and can be restored by the SHA-256-verifying downloader.

Regenerate the PDF report with:

```bash
python -m pip install --requirement scripts/requirements-report.txt
python scripts/build-technical-report.py
```

## 10. References

1. OASIS. *MQTT Version 5.0*. OASIS Standard, 2019. https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html
2. Jocher, G., and Qiu, J. *Ultralytics YOLO11*. Software documentation, 2024. https://docs.ultralytics.com/models/yolo11/
3. Kettkk. *Smart Helmet AIoT v1.0.0*. GitHub release and versioned experiment artifact, 2026. https://github.com/Kettkk/smart-helmet-aiot/releases/tag/v1.0.0
