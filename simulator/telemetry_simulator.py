"""Publish deterministic, synthetic smart-helmet telemetry over MQTT."""

import json
import math
import os
import random
import signal
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt


MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "smart-helmet/telemetry")
DEVICE_ID = os.getenv("SIMULATOR_DEVICE_ID", "helmet-sim-001")
INTERVAL_SECONDS = float(os.getenv("SIMULATOR_INTERVAL_SECONDS", "1"))
RANDOM_SEED = int(os.getenv("SIMULATOR_RANDOM_SEED", "42"))

running = True


def stop(_signal_number, _frame):
    global running
    running = False


def connect_with_retry(client: mqtt.Client) -> None:
    while running:
        try:
            client.connect(MQTT_HOST, MQTT_PORT, keepalive=30)
            client.loop_start()
            print(f"Connected to mqtt://{MQTT_HOST}:{MQTT_PORT}", flush=True)
            return
        except OSError as exception:
            print(f"MQTT unavailable ({exception}); retrying in 2 seconds", flush=True)
            time.sleep(2)


def telemetry(sample_number: int, rng: random.Random) -> dict:
    phase = sample_number / 12.0
    return {
        "deviceId": DEVICE_ID,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "wearing": True,
        "bodyTemperatureC": round(36.6 + 0.12 * math.sin(phase), 2),
        "ambientTemperatureC": round(22.0 + 1.8 * math.sin(phase / 3), 2),
        "ambientHumidityPct": round(58.0 + 4.0 * math.cos(phase / 2), 2),
        "heartRateBpm": round(78 + 5 * math.sin(phase) + rng.uniform(-1.5, 1.5)),
        "latitude": round(30.2741 + sample_number * 0.00001, 6),
        "longitude": round(120.1551 + sample_number * 0.00001, 6),
        "impactPressurePa": round(1013.0 + rng.uniform(-4, 4), 2),
        "speedMps": round(max(0.0, 1.25 + 0.3 * math.sin(phase)), 2),
    }


def main() -> None:
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    rng = random.Random(RANDOM_SEED)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"{DEVICE_ID}-publisher")
    connect_with_retry(client)

    sample_number = 0
    while running:
        payload = telemetry(sample_number, rng)
        result = client.publish(MQTT_TOPIC, json.dumps(payload), qos=1)
        result.wait_for_publish(timeout=5)
        print(f"Published sample {sample_number} for {DEVICE_ID}", flush=True)
        sample_number += 1
        time.sleep(INTERVAL_SECONDS)

    client.disconnect()
    client.loop_stop()


if __name__ == "__main__":
    main()
