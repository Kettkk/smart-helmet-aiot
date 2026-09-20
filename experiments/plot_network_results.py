from __future__ import annotations

import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


BLUE = "#0969da"
ORANGE = "#bf8700"
GREEN = "#1a7f37"
GRAY = "#57606a"
GRID = "#d8dee4"


def read_csv(path: Path) -> list[dict[str, float]]:
    with path.open(encoding="utf-8", newline="") as source:
        return [
            {key: float(value) for key, value in row.items()}
            for row in csv.DictReader(source)
        ]


def group(rows: list[dict[str, float]], key: str) -> dict[float, list[dict[str, float]]]:
    grouped: dict[float, list[dict[str, float]]] = defaultdict(list)
    for row in rows:
        grouped[row[key]].append(row)
    return dict(sorted(grouped.items()))


def apply_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#8c959f",
            "axes.labelcolor": "#24292f",
            "axes.titlecolor": "#24292f",
            "axes.titlesize": 12,
            "axes.titleweight": "bold",
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "xtick.color": GRAY,
            "ytick.color": GRAY,
            "grid.color": GRID,
            "grid.linewidth": 0.7,
            "grid.alpha": 0.75,
            "legend.frameon": False,
            "savefig.facecolor": "white",
            "savefig.bbox": "tight",
            "svg.hashsalt": "smart-helmet-network",
        }
    )


def finish(fig, output: Path) -> None:
    fig.savefig(output.with_suffix(".png"), dpi=200)
    svg_path = output.with_suffix(".svg")
    fig.savefig(svg_path, metadata={"Date": None})
    svg_path.write_text(
        "\n".join(line.rstrip() for line in svg_path.read_text().splitlines()) + "\n",
        encoding="utf-8",
    )
    plt.close(fig)


def delivery_rate_vs_packet_loss(rows: list[dict[str, float]], output_dir: Path) -> None:
    grouped = group(rows, "injected_packet_loss_pct")
    losses = list(grouped)
    means = [statistics.mean(row["delivery_rate_pct"] for row in grouped[x]) for x in losses]
    minima = [min(row["delivery_rate_pct"] for row in grouped[x]) for x in losses]
    maxima = [max(row["delivery_rate_pct"] for row in grouped[x]) for x in losses]
    lower = [mean - minimum for mean, minimum in zip(means, minima)]
    upper = [maximum - mean for mean, maximum in zip(means, maxima)]

    fig, ax = plt.subplots(figsize=(7.4, 4.5))
    ax.errorbar(
        losses,
        means,
        yerr=[lower, upper],
        color=BLUE,
        marker="o",
        capsize=4,
        linewidth=1.8,
        label="Measured delivery rate",
    )
    ax.plot(losses, [100 - value for value in losses], color=GRAY, linestyle="--", label="Injected-loss reference")
    ax.set(
        title="MQTT delivery rate under controlled packet loss",
        xlabel="Injected packet loss (%)",
        ylabel="End-to-end delivery rate (%)",
        ylim=(50, 102),
    )
    ax.grid()
    ax.legend()
    finish(fig, output_dir / "delivery_rate_vs_packet_loss")


def reconnect_time_vs_outage(rows: list[dict[str, float]], output_dir: Path) -> None:
    grouped = group(rows, "outage_s")
    outages = list(grouped)
    reconnect_means = [statistics.mean(row["reconnect_time_ms"] for row in grouped[x]) for x in outages]
    recovery_means = [statistics.mean(row["first_message_recovery_ms"] for row in grouped[x]) for x in outages]

    fig, ax = plt.subplots(figsize=(7.4, 4.5))
    for outage in outages:
        ax.scatter(
            [outage] * len(grouped[outage]),
            [row["reconnect_time_ms"] for row in grouped[outage]],
            color=BLUE,
            alpha=0.45,
            s=28,
        )
    ax.plot(outages, reconnect_means, color=BLUE, marker="o", linewidth=1.8, label="Client reconnect")
    ax.plot(outages, recovery_means, color=GREEN, marker="s", linewidth=1.6, label="First message recovered")
    ax.set(
        title="MQTT recovery after broker outages",
        xlabel="Configured broker outage (s)",
        ylabel="Time after restart request (ms)",
    )
    ax.grid()
    ax.legend()
    finish(fig, output_dir / "reconnect_time_vs_outage")


def latency_vs_added_delay(rows: list[dict[str, float]], output_dir: Path) -> None:
    grouped = group(rows, "added_delay_ms")
    delays = list(grouped)
    means = [statistics.mean(row["mean_end_to_end_latency_ms"] for row in grouped[x]) for x in delays]
    p95 = [statistics.mean(row["p95_end_to_end_latency_ms"] for row in grouped[x]) for x in delays]

    fig, ax = plt.subplots(figsize=(7.4, 4.5))
    ax.plot(delays, means, color=BLUE, marker="o", linewidth=1.8, label="Mean")
    ax.plot(delays, p95, color=ORANGE, marker="s", linewidth=1.6, label="p95")
    ax.plot(delays, delays, color=GRAY, linestyle="--", label="Injected-delay reference")
    ax.set(
        title="End-to-end MQTT latency under added delay",
        xlabel="Added one-way delay (ms)",
        ylabel="Measured end-to-end latency (ms)",
    )
    ax.grid()
    ax.legend()
    finish(fig, output_dir / "latency_vs_added_delay")


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot network reliability results.")
    parser.add_argument("--results-dir", type=Path, default=Path("experiments/results/network"))
    parser.add_argument("--output-dir", type=Path, default=Path("experiments/plots/network"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    apply_style()
    delivery_rate_vs_packet_loss(read_csv(args.results_dir / "packet-loss.csv"), args.output_dir)
    reconnect_time_vs_outage(read_csv(args.results_dir / "reconnect.csv"), args.output_dir)
    latency_vs_added_delay(read_csv(args.results_dir / "latency.csv"), args.output_dir)
    print(f"Generated three network plot sets in {args.output_dir}")


if __name__ == "__main__":
    main()
