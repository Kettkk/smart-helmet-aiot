from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator


BLUE = "#0969da"
ORANGE = "#bf8700"
GREEN = "#1a7f37"
RED = "#cf222e"
GRAY = "#57606a"
GRID = "#d8dee4"


def read_csv(path: Path) -> list[dict[str, float]]:
    with path.open(encoding="utf-8", newline="") as source:
        return [
            {key: float(value) for key, value in row.items()}
            for row in csv.DictReader(source)
        ]


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
            "xtick.color": "#57606a",
            "ytick.color": "#57606a",
            "grid.color": GRID,
            "grid.linewidth": 0.7,
            "grid.alpha": 0.75,
            "legend.frameon": False,
            "savefig.facecolor": "white",
            "savefig.bbox": "tight",
        }
    )


def finish(fig, output: Path) -> None:
    fig.savefig(output.with_suffix(".png"), dpi=200)
    fig.savefig(output.with_suffix(".svg"))
    plt.close(fig)


def latency_over_time(rows: list[dict[str, float]], output_dir: Path) -> None:
    times = [row["timestamp_s"] for row in rows]
    latencies = [row["inference_latency_ms"] for row in rows]
    mean = sum(latencies) / len(latencies)

    fig, ax = plt.subplots(figsize=(8.4, 4.3))
    ax.plot(times, latencies, color=BLUE, linewidth=1.5, label="Inference latency")
    ax.axhline(mean, color=ORANGE, linewidth=1.3, linestyle="--", label=f"Mean {mean:.1f} ms")
    ax.set(title="Per-frame inference latency", xlabel="Video time (s)", ylabel="Latency (ms)")
    ax.grid(axis="y")
    ax.legend(loc="upper right")
    ax.set_xlim(min(times), max(times))
    finish(fig, output_dir / "latency-over-time")


def latency_distribution(rows: list[dict[str, float]], output_dir: Path) -> None:
    latencies = sorted(row["inference_latency_ms"] for row in rows)
    mean = sum(latencies) / len(latencies)
    p95_index = round(0.95 * (len(latencies) - 1))
    p95 = latencies[p95_index]

    fig, ax = plt.subplots(figsize=(7.2, 4.3))
    ax.hist(latencies, bins=18, color=BLUE, alpha=0.86, edgecolor="white")
    ax.axvline(mean, color=ORANGE, linewidth=1.5, linestyle="--", label=f"Mean {mean:.1f} ms")
    ax.axvline(p95, color=RED, linewidth=1.5, linestyle=":", label=f"p95 {p95:.1f} ms")
    ax.set(title="Inference latency distribution", xlabel="Latency (ms)", ylabel="Sampled frames")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(axis="y")
    ax.legend()
    finish(fig, output_dir / "latency-distribution")


def confidence_over_time(rows: list[dict[str, float]], output_dir: Path) -> None:
    times = [row["timestamp_s"] for row in rows]
    confidence = [row["max_confidence"] for row in rows]

    fig, ax = plt.subplots(figsize=(8.4, 4.3))
    ax.plot(times, confidence, color=GREEN, linewidth=1.6)
    ax.fill_between(times, confidence, color=GREEN, alpha=0.1)
    ax.axhline(0.25, color=GRAY, linewidth=1.2, linestyle="--", label="Threshold 0.25")
    ax.set(
        title="Maximum person confidence over time",
        xlabel="Video time (s)",
        ylabel="Confidence",
        ylim=(0, 1.0),
        xlim=(min(times), max(times)),
    )
    ax.grid(axis="y")
    ax.legend(loc="lower right")
    finish(fig, output_dir / "confidence-over-time")


def frame_sampling_comparison(
    rows: list[dict[str, float]], output_dir: Path
) -> None:
    rows = sorted(rows, key=lambda row: row["effective_sampling_fps"])
    sampling = [row["effective_sampling_fps"] for row in rows]
    mean_latency = [row["mean_inference_latency_ms"] for row in rows]
    p95_latency = [row["p95_inference_latency_ms"] for row in rows]
    pipeline_fps = [row["pipeline_fps"] for row in rows]

    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.4))
    latency_ax, throughput_ax = axes
    latency_ax.plot(sampling, mean_latency, color=BLUE, marker="o", label="Mean")
    latency_ax.plot(sampling, p95_latency, color=ORANGE, marker="s", label="p95")
    latency_ax.set(
        title="Latency vs. sampling rate",
        xlabel="Effective sampling rate (fps)",
        ylabel="Inference latency (ms)",
    )
    latency_ax.grid()
    latency_ax.legend()

    throughput_ax.plot(sampling, pipeline_fps, color=GREEN, marker="o", label="Pipeline rate")
    throughput_ax.axhline(30, color=GRAY, linestyle="--", linewidth=1.2, label="Source rate (30 fps)")
    throughput_ax.set(
        title="Pipeline capacity vs. sampling rate",
        xlabel="Effective sampling rate (fps)",
        ylabel="Processed source frames per second",
    )
    throughput_ax.grid()
    throughput_ax.legend()
    fig.suptitle("Frame-sampling trade-off on the fixed hiking video", fontsize=13, fontweight="bold")
    fig.tight_layout()
    finish(fig, output_dir / "frame-sampling-comparison")


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot fixed-video benchmark results.")
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("experiments/results/frame-sampling"),
    )
    parser.add_argument(
        "--baseline-stride", type=int, default=5, help="Stride used for frame-level plots."
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("experiments/plots/vision")
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    baseline = read_csv(
        args.results_dir / f"stride-{args.baseline_stride}" / "frame-metrics.csv"
    )
    comparison = read_csv(args.results_dir / "summary.csv")
    apply_style()
    latency_over_time(baseline, args.output_dir)
    latency_distribution(baseline, args.output_dir)
    confidence_over_time(baseline, args.output_dir)
    frame_sampling_comparison(comparison, args.output_dir)
    print(f"Generated four plot sets in {args.output_dir}")


if __name__ == "__main__":
    main()
