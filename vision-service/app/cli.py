from __future__ import annotations

import argparse
import json
from pathlib import Path

from .detector import UltralyticsDetector
from .pipeline import run_video_inference


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run reproducible object detection on a fixed video."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="yolo11n.pt")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--image-size", type=int, default=640)
    parser.add_argument("--confidence", type=float, default=0.25)
    parser.add_argument("--frame-stride", type=int, default=5)
    parser.add_argument("--target-class", action="append")
    parser.add_argument("--warmup-runs", type=int, default=1)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    detector = UltralyticsDetector(args.model, args.device)
    summary = run_video_inference(
        input_path=args.input,
        output_dir=args.output_dir,
        detector=detector,
        frame_stride=args.frame_stride,
        confidence=args.confidence,
        image_size=args.image_size,
        target_classes=args.target_class or ["person"],
        warmup_runs=args.warmup_runs,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
