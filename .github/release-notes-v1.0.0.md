# Smart Helmet AIoT v1.0.0

This release turns the original smart-helmet capstone into a reproducible, evidence-backed research portfolio.

## Highlights

- Complete telemetry loop: simulator to MQTT to Spring Boot to MySQL to Vue dashboard
- Persistent vision benchmark API and dashboard integration
- Fixed 20-second video workflow with automatic download and SHA-256 verification
- YOLO11n frame-sampling benchmark at strides 1, 2, 5, and 10
- Versioned raw vision results and regenerable PNG/SVG figures
- Controlled MQTT delay, seeded loss, and real broker-outage recovery experiments
- Archived ESP8266 and ESP32-CAM firmware with physical prototype documentation
- Docker Compose quick start, automated smoke test, and GitHub Actions validation
- Four-page English technical report and GitHub Pages project homepage

## Research scope

The reported evidence is limited to latency, throughput, sampled-frame detection continuity, and network reliability. This release does not claim detector accuracy, medical validity, energy optimality, or safety certification.

## Selected measured results

- Stride 5: 34.56 pipeline FPS with 99.17% sampled-frame continuity
- Seeded application-level loss: delivery decreased from 100% at 0% loss to 62% at the nominal 40% condition
- Broker outages: all 9 recovery trials succeeded; mean subscription recovery after availability was approximately 0.78 seconds

## Reproduce

```bash
git clone https://github.com/Kettkk/smart-helmet-aiot.git
cd smart-helmet-aiot
cp .env.example .env
docker compose up --build -d
./scripts/smoke-test.sh
```

See the attached English technical report for system design, experiment details, results, and limitations.

PDF SHA-256: `d0c78e8d81a00c4fc18a378caa1026dc3cd2c53a40bea12131f2b3ebed94048d`
