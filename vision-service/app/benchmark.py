from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from .detector import UltralyticsDetector
from .pipeline import run_video_inference


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Benchmark fixed-video inference across frame strides."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="yolo11n.pt")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--image-size", type=int, default=640)
    parser.add_argument("--confidence", type=float, default=0.25)
    parser.add_argument("--strides", type=int, nargs="+", default=[1, 2, 5, 10])
    parser.add_argument("--target-class", action="append")
    parser.add_argument("--warmup-runs", type=int, default=1)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    strides = list(dict.fromkeys(args.strides))
    if any(stride < 1 for stride in strides):
        raise ValueError("Every frame stride must be at least 1")

    targets = args.target_class or ["person"]
    detector = UltralyticsDetector(args.model, args.device)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summaries = []

    for stride in strides:
        print(f"Running frame stride {stride}...", flush=True)
        summary = run_video_inference(
            input_path=args.input,
            output_dir=args.output_dir / f"stride-{stride}",
            detector=detector,
            frame_stride=stride,
            confidence=args.confidence,
            image_size=args.image_size,
            target_classes=targets,
            warmup_runs=args.warmup_runs,
        )
        summaries.append(summary)

    aggregate_fields = [
        "frame_stride",
        "effective_sampling_fps",
        "processed_frames",
        "mean_inference_latency_ms",
        "p50_inference_latency_ms",
        "p95_inference_latency_ms",
        "inference_fps",
        "pipeline_fps",
        "sampled_frames_with_detections",
        "sampled_frame_detection_rate",
        "person_detections",
    ]
    with (args.output_dir / "summary.csv").open(
        "w", encoding="utf-8", newline=""
    ) as output:
        writer = csv.DictWriter(output, fieldnames=aggregate_fields)
        writer.writeheader()
        for summary in summaries:
            config = summary["configuration"]
            performance = summary["performance"]
            detections = summary["detections"]
            writer.writerow(
                {
                    "frame_stride": config["frame_stride"],
                    "effective_sampling_fps": config["effective_sampling_fps"],
                    "processed_frames": performance["processed_frames"],
                    "mean_inference_latency_ms": performance[
                        "mean_inference_latency_ms"
                    ],
                    "p50_inference_latency_ms": performance[
                        "p50_inference_latency_ms"
                    ],
                    "p95_inference_latency_ms": performance[
                        "p95_inference_latency_ms"
                    ],
                    "inference_fps": performance["inference_fps"],
                    "pipeline_fps": performance["pipeline_fps"],
                    "sampled_frames_with_detections": detections[
                        "sampled_frames_with_detections"
                    ],
                    "sampled_frame_detection_rate": detections[
                        "sampled_frame_detection_rate"
                    ],
                    "person_detections": detections["count_by_class"].get(
                        "person", 0
                    ),
                }
            )

    (args.output_dir / "benchmark.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "input": args.input.name,
                "model": detector.model_name,
                "device": detector.device,
                "strides": strides,
                "runs": summaries,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
