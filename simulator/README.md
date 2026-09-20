# Telemetry simulator

The simulator replaces unavailable helmet hardware with a deterministic MQTT
publisher. It produces non-sensitive wearable, environmental, motion, and
location-shaped values so the ingestion path can be tested without an ESP8266
or STM32 board.

## Data path

```text
telemetry_simulator.py -> MQTT QoS 1 -> Mosquitto -> Spring Boot -> MySQL
```

One JSON record is published per interval. Timestamps are real UTC timestamps;
the signal shapes and random variation are repeatable for a fixed seed.

## Configuration

| Variable | Default | Meaning |
| --- | --- | --- |
| `MQTT_HOST` | `localhost` | Broker hostname |
| `MQTT_PORT` | `1883` | Broker port |
| `MQTT_TOPIC` | `smart-helmet/telemetry` | Publication topic |
| `SIMULATOR_DEVICE_ID` | `helmet-sim-001` | Synthetic device identifier |
| `SIMULATOR_INTERVAL_SECONDS` | `1` | Time between records |
| `SIMULATOR_RANDOM_SEED` | `42` | Reproducible variation seed |

## Run

Docker Compose starts the simulator after the backend becomes healthy:

```bash
docker compose up --build -d simulator
docker compose logs -f simulator
```

For a host-side run, install `simulator/requirements.txt`, ensure Mosquitto is
reachable, and execute `python simulator/telemetry_simulator.py`.

All values are synthetic. They must not be interpreted as physiological
measurements, medical advice, or evidence from a deployed safety device.
