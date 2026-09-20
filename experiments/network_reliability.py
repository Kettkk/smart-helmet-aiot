"""Run reproducible MQTT latency, loss, and outage-recovery experiments."""

from __future__ import annotations

import argparse
import csv
import json
import platform
import random
import socket
import statistics
import subprocess
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import paho.mqtt.client as mqtt


DEFAULT_TOPIC = "smart-helmet/experiments/network"


def percentile(values: Iterable[float], quantile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("percentile requires at least one value")
    if not 0 <= quantile <= 1:
        raise ValueError("quantile must be between zero and one")
    position = quantile * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + fraction * (ordered[upper] - ordered[lower])


def deterministic_delivery_plan(
    message_count: int, loss_ratio: float, seed: int
) -> list[bool]:
    if message_count <= 0:
        raise ValueError("message_count must be positive")
    if not 0 <= loss_ratio <= 1:
        raise ValueError("loss_ratio must be between zero and one")
    rng = random.Random(seed)
    return [rng.random() >= loss_ratio for _ in range(message_count)]


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"no rows to write to {path}")
    with path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(
            destination, fieldnames=list(rows[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def run_command(arguments: list[str], *, capture: bool = False) -> str:
    result = subprocess.run(
        arguments,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
        stderr=subprocess.PIPE if capture else subprocess.DEVNULL,
    )
    return result.stdout.strip() if capture else ""


def wait_for_port(host: str, port: int, timeout_s: float = 10.0) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.25):
                return
        except OSError:
            time.sleep(0.05)
    raise TimeoutError(f"broker at {host}:{port} did not become ready")


class DockerBroker:
    def __init__(self, port: int, image: str, config: Path) -> None:
        self.host = "127.0.0.1"
        self.port = port
        self.image = image
        self.config = config.resolve()
        self.name = f"smart-helmet-network-benchmark-{uuid.uuid4().hex[:8]}"
        self.running = False

    def create(self) -> None:
        run_command(["docker", "info"])
        run_command(
            [
                "docker",
                "run",
                "--detach",
                "--name",
                self.name,
                "--publish",
                f"127.0.0.1:{self.port}:1883",
                "--volume",
                f"{self.config}:/mosquitto/config/mosquitto.conf:ro",
                self.image,
            ]
        )
        self.running = True
        wait_for_port(self.host, self.port)

    def stop(self) -> None:
        run_command(["docker", "stop", "--time", "1", self.name])
        self.running = False

    def start(self) -> None:
        run_command(["docker", "start", self.name])
        self.running = True
        wait_for_port(self.host, self.port)

    def remove(self) -> None:
        subprocess.run(
            ["docker", "rm", "--force", self.name],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.running = False


class MqttProbe:
    def __init__(self, host: str, port: int, topic: str) -> None:
        suffix = uuid.uuid4().hex[:8]
        self.host = host
        self.port = port
        self.topic = topic
        self.condition = threading.Condition()
        self.received_latency_ms: dict[str, float] = {}
        self.subscriber_connected = threading.Event()
        self.subscriber_subscribed = threading.Event()
        self.publisher_connected = threading.Event()
        self.subscriber_disconnected = threading.Event()
        self.publisher_disconnected = threading.Event()
        self.subscriber_connect_time = 0.0
        self.subscriber_subscribe_time = 0.0
        self.publisher_connect_time = 0.0

        self.subscriber = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"network-benchmark-subscriber-{suffix}",
            clean_session=True,
        )
        self.publisher = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"network-benchmark-publisher-{suffix}",
            clean_session=True,
        )
        self.subscriber.reconnect_delay_set(min_delay=1, max_delay=1)
        self.publisher.reconnect_delay_set(min_delay=1, max_delay=1)
        self.subscriber.on_connect = self._on_subscriber_connect
        self.subscriber.on_disconnect = self._on_subscriber_disconnect
        self.subscriber.on_subscribe = self._on_subscribe
        self.subscriber.on_message = self._on_message
        self.publisher.on_connect = self._on_publisher_connect
        self.publisher.on_disconnect = self._on_publisher_disconnect

    def _on_subscriber_connect(
        self, client, _userdata, _flags, reason_code, _properties
    ) -> None:
        if reason_code == 0:
            client.subscribe(self.topic, qos=1)
            self.subscriber_connect_time = time.monotonic()
            self.subscriber_connected.set()

    def _on_subscribe(
        self, _client, _userdata, _mid, reason_code_list, _properties
    ) -> None:
        if all(reason_code < 128 for reason_code in reason_code_list):
            self.subscriber_subscribe_time = time.monotonic()
            self.subscriber_subscribed.set()

    def _on_publisher_connect(
        self, _client, _userdata, _flags, reason_code, _properties
    ) -> None:
        if reason_code == 0:
            self.publisher_connect_time = time.monotonic()
            self.publisher_connected.set()

    def _on_subscriber_disconnect(
        self, _client, _userdata, _disconnect_flags, _reason_code, _properties
    ) -> None:
        self.subscriber_connected.clear()
        self.subscriber_disconnected.set()

    def _on_publisher_disconnect(
        self, _client, _userdata, _disconnect_flags, _reason_code, _properties
    ) -> None:
        self.publisher_connected.clear()
        self.publisher_disconnected.set()

    def _on_message(self, _client, _userdata, message) -> None:
        payload = json.loads(message.payload.decode("utf-8"))
        latency_ms = (
            time.monotonic_ns() - payload["origin_monotonic_ns"]
        ) / 1_000_000
        with self.condition:
            self.received_latency_ms[payload["message_id"]] = latency_ms
            self.condition.notify_all()

    def connect(self, timeout_s: float = 10.0) -> None:
        self.subscriber.connect_async(self.host, self.port, keepalive=5)
        self.publisher.connect_async(self.host, self.port, keepalive=5)
        self.subscriber.loop_start()
        self.publisher.loop_start()
        if not self.subscriber_connected.wait(timeout_s):
            raise TimeoutError("subscriber did not connect")
        if not self.subscriber_subscribed.wait(timeout_s):
            raise TimeoutError("subscriber did not confirm its subscription")
        if not self.publisher_connected.wait(timeout_s):
            raise TimeoutError("publisher did not connect")

    def close(self) -> None:
        for client in (self.publisher, self.subscriber):
            try:
                client.disconnect()
            except Exception:
                pass
            client.loop_stop()

    def publish(self, message_id: str, origin_monotonic_ns: int) -> None:
        payload = json.dumps(
            {
                "message_id": message_id,
                "origin_monotonic_ns": origin_monotonic_ns,
            }
        )
        result = self.publisher.publish(self.topic, payload, qos=1)
        result.wait_for_publish(timeout=5)

    def wait_for(self, message_ids: set[str], timeout_s: float) -> set[str]:
        deadline = time.monotonic() + timeout_s
        with self.condition:
            while time.monotonic() < deadline:
                received = message_ids.intersection(self.received_latency_ms)
                if received == message_ids:
                    return received
                self.condition.wait(timeout=min(0.1, deadline - time.monotonic()))
            return message_ids.intersection(self.received_latency_ms)

    def clear_events_for_outage(self) -> None:
        self.subscriber_disconnected.clear()
        self.publisher_disconnected.clear()
        self.subscriber_connected.clear()
        self.subscriber_subscribed.clear()
        self.publisher_connected.clear()


@dataclass
class Configuration:
    schema_version: int
    created_at: str
    host_platform: str
    python_version: str
    docker_version: str
    broker_image: str
    broker_port: int
    mqtt_qos: int
    topic: str
    random_seed: int
    added_delay_ms: list[int]
    packet_loss_pct: list[int]
    outage_s: list[int]
    trials: int
    latency_messages_per_trial: int
    loss_messages_per_trial: int
    impairment_model: str


def run_latency_experiment(
    probe: MqttProbe,
    delays_ms: list[int],
    trials: int,
    messages_per_trial: int,
) -> list[dict]:
    rows = []
    for delay_ms in delays_ms:
        for trial in range(1, trials + 1):
            ids: set[str] = set()
            for sequence in range(messages_per_trial):
                message_id = f"latency-{delay_ms}-{trial}-{sequence}-{uuid.uuid4().hex[:6]}"
                ids.add(message_id)
                origin = time.monotonic_ns()
                time.sleep(delay_ms / 1000)
                probe.publish(message_id, origin)
            delivered = probe.wait_for(ids, timeout_s=5)
            latencies = [probe.received_latency_ms[item] for item in delivered]
            rows.append(
                {
                    "added_delay_ms": delay_ms,
                    "trial": trial,
                    "intended_messages": messages_per_trial,
                    "delivered_messages": len(delivered),
                    "delivery_rate_pct": round(100 * len(delivered) / messages_per_trial, 3),
                    "mean_end_to_end_latency_ms": round(statistics.mean(latencies), 3),
                    "p50_end_to_end_latency_ms": round(percentile(latencies, 0.5), 3),
                    "p95_end_to_end_latency_ms": round(percentile(latencies, 0.95), 3),
                }
            )
    return rows


def run_loss_experiment(
    probe: MqttProbe,
    losses_pct: list[int],
    trials: int,
    messages_per_trial: int,
    seed: int,
) -> list[dict]:
    rows = []
    for loss_pct in losses_pct:
        for trial in range(1, trials + 1):
            plan = deterministic_delivery_plan(
                messages_per_trial,
                loss_pct / 100,
                seed + loss_pct * 100 + trial,
            )
            intended_ids = {
                f"loss-{loss_pct}-{trial}-{sequence}"
                for sequence in range(messages_per_trial)
            }
            published_ids: set[str] = set()
            for sequence, should_publish in enumerate(plan):
                if not should_publish:
                    continue
                message_id = f"loss-{loss_pct}-{trial}-{sequence}"
                published_ids.add(message_id)
                probe.publish(message_id, time.monotonic_ns())
            delivered = probe.wait_for(published_ids, timeout_s=5)
            rows.append(
                {
                    "injected_packet_loss_pct": loss_pct,
                    "trial": trial,
                    "intended_messages": len(intended_ids),
                    "injected_dropped_messages": messages_per_trial - len(published_ids),
                    "published_messages": len(published_ids),
                    "delivered_messages": len(delivered),
                    "delivery_rate_pct": round(100 * len(delivered) / messages_per_trial, 3),
                    "post_publish_delivery_rate_pct": round(
                        100 * len(delivered) / len(published_ids), 3
                    )
                    if published_ids
                    else 0,
                }
            )
    return rows


def run_outage_experiment(
    broker: DockerBroker,
    probe: MqttProbe,
    outages_s: list[int],
    trials: int,
) -> list[dict]:
    rows = []
    for outage_s in outages_s:
        for trial in range(1, trials + 1):
            probe.clear_events_for_outage()
            stop_started = time.monotonic()
            broker.stop()
            disconnected = probe.subscriber_disconnected.wait(timeout=5)
            disconnect_detected_ms = (
                (time.monotonic() - stop_started) * 1000 if disconnected else -1
            )
            time.sleep(outage_s)
            restart_started = time.monotonic()
            broker.start()
            subscriber_reconnected = probe.subscriber_connected.wait(timeout=10)
            subscription_recovered = probe.subscriber_subscribed.wait(timeout=10)
            publisher_reconnected = probe.publisher_connected.wait(timeout=10)
            if not (
                subscriber_reconnected
                and subscription_recovered
                and publisher_reconnected
            ):
                raise TimeoutError(
                    "MQTT clients did not reconnect and resubscribe after broker restart"
                )
            reconnect_time_ms = (
                max(probe.subscriber_subscribe_time, probe.publisher_connect_time)
                - restart_started
            ) * 1000
            probe_id = f"recovery-{outage_s}-{trial}-{uuid.uuid4().hex[:6]}"
            probe.publish(probe_id, time.monotonic_ns())
            delivered = probe.wait_for({probe_id}, timeout_s=5)
            first_message_recovery_ms = (time.monotonic() - restart_started) * 1000
            rows.append(
                {
                    "outage_s": outage_s,
                    "trial": trial,
                    "disconnect_detected_ms": round(disconnect_detected_ms, 3),
                    "reconnect_time_ms": round(reconnect_time_ms, 3),
                    "first_message_recovery_ms": round(first_message_recovery_ms, 3),
                    "probe_delivered": int(probe_id in delivered),
                }
            )
            time.sleep(0.25)
    return rows


def parse_int_list(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("experiments/results/network")
    )
    parser.add_argument("--broker-port", type=int, default=18883)
    parser.add_argument("--broker-image", default="eclipse-mosquitto:2.0")
    parser.add_argument(
        "--broker-config",
        type=Path,
        default=Path("infrastructure/mosquitto/mosquitto.conf"),
    )
    parser.add_argument("--topic", default=DEFAULT_TOPIC)
    parser.add_argument(
        "--delays-ms",
        type=parse_int_list,
        default=parse_int_list("0,25,50,100,200"),
    )
    parser.add_argument(
        "--losses-pct",
        type=parse_int_list,
        default=parse_int_list("0,5,10,20,30,40"),
    )
    parser.add_argument(
        "--outages-s", type=parse_int_list, default=parse_int_list("1,3,5")
    )
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--latency-messages", type=int, default=20)
    parser.add_argument("--loss-messages", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20260920)
    args = parser.parse_args()

    broker = DockerBroker(args.broker_port, args.broker_image, args.broker_config)
    probe: MqttProbe | None = None
    try:
        broker.create()
        probe = MqttProbe(broker.host, broker.port, args.topic)
        probe.connect()
        latency_rows = run_latency_experiment(
            probe, args.delays_ms, args.trials, args.latency_messages
        )
        loss_rows = run_loss_experiment(
            probe,
            args.losses_pct,
            args.trials,
            args.loss_messages,
            args.seed,
        )
        outage_rows = run_outage_experiment(
            broker, probe, args.outages_s, args.trials
        )
        args.output_dir.mkdir(parents=True, exist_ok=True)
        write_csv(args.output_dir / "latency.csv", latency_rows)
        write_csv(args.output_dir / "packet-loss.csv", loss_rows)
        write_csv(args.output_dir / "reconnect.csv", outage_rows)
        configuration = Configuration(
            schema_version=1,
            created_at=datetime.now(timezone.utc).isoformat(),
            host_platform=platform.platform(),
            python_version=platform.python_version(),
            docker_version=run_command(
                ["docker", "version", "--format", "{{.Server.Version}}"],
                capture=True,
            ),
            broker_image=args.broker_image,
            broker_port=args.broker_port,
            mqtt_qos=1,
            topic=args.topic,
            random_seed=args.seed,
            added_delay_ms=args.delays_ms,
            packet_loss_pct=args.losses_pct,
            outage_s=args.outages_s,
            trials=args.trials,
            latency_messages_per_trial=args.latency_messages,
            loss_messages_per_trial=args.loss_messages,
            impairment_model=(
                "Seeded application-layer delay and pre-publish loss; actual Docker "
                "broker stop/start for outages"
            ),
        )
        (args.output_dir / "configuration.json").write_text(
            json.dumps(asdict(configuration), indent=2) + "\n", encoding="utf-8"
        )
        print(f"Network experiments complete: {args.output_dir}")
    finally:
        if probe is not None:
            probe.close()
        broker.remove()


if __name__ == "__main__":
    main()
