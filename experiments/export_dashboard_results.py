#!/usr/bin/env python3
"""Export the measured frame-sampling benchmark as a backend API payload."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPOSITORY_ROOT / "experiments/results/frame-sampling/benchmark.json"
DEFAULT_OUTPUT = REPOSITORY_ROOT / "experiments/results/frame-sampling/dashboard-payload.json"


def export_results(input_path: Path, output_path: Path) -> None:
    benchmark = json.loads(input_path.read_text(encoding="utf-8"))
    runs = benchmark["runs"]
    source_fps = float(runs[0]["input"]["fps"])

    rows = [
        {
            "frameStride": run["configuration"]["frame_stride"],
            "samplingFps": run["configuration"]["effective_sampling_fps"],
            "processedFrames": run["performance"]["processed_frames"],
            "meanLatencyMs": run["performance"]["mean_inference_latency_ms"],
            "p95LatencyMs": run["performance"]["p95_inference_latency_ms"],
            "pipelineFps": run["performance"]["pipeline_fps"],
            "continuityRate": run["detections"]["sampled_frame_detection_rate"],
        }
        for run in runs
    ]

    realtime_rows = [row for row in rows if row["pipelineFps"] >= source_fps]
    operating_point = max(realtime_rows, key=lambda row: row["samplingFps"]) if realtime_rows else max(
        rows, key=lambda row: row["pipelineFps"]
    )

    first_run = runs[0]
    payload = {
        "schemaVersion": benchmark["schema_version"],
        "measurementTimestamp": max(run["created_at"] for run in runs),
        "input": {
            "file": benchmark["input"],
            "durationSeconds": first_run["input"]["duration_s"],
            "sourceFps": source_fps,
            "resolution": f'{first_run["input"]["width"]}x{first_run["input"]["height"]}',
        },
        "configuration": {
            "model": benchmark["model"],
            "device": benchmark["device"].upper(),
            "imageSize": first_run["configuration"]["image_size"],
            "confidence": first_run["configuration"]["confidence"],
            "targetClasses": first_run["configuration"]["target_classes"],
        },
        "operatingPointStride": operating_point["frameStride"],
        "runs": rows,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    export_results(args.input, args.output)


if __name__ == "__main__":
    main()
