from __future__ import annotations

import csv
import json
import shutil
import subprocess
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

import cv2

from .detector import Detection


class Detector(Protocol):
    model_name: str
    device: str

    def predict(
        self,
        frame: Any,
        *,
        confidence: float,
        image_size: int,
        target_classes: list[str],
    ) -> list[Detection]: ...


def percentile(values: list[float], percentage: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentage / 100.0
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _draw_detections(frame: Any, detections: list[Detection], sampled: bool) -> Any:
    annotated = frame.copy()
    for detection in detections:
        x1, y1, x2, y2 = (int(value) for value in detection.bbox_xyxy)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (31, 111, 235), 2)
        label = f"{detection.class_name} {detection.confidence:.2f}"
        cv2.putText(
            annotated,
            label,
            (x1, max(22, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (31, 111, 235),
            2,
            cv2.LINE_AA,
        )

    state = "inference frame" if sampled else "carried-forward detection"
    cv2.putText(
        annotated,
        state,
        (20, 34),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return annotated


def _write_h264(intermediate: Path, output: Path, fps: float) -> str:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        intermediate.replace(output)
        return "mp4v"

    subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(intermediate),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "23",
            "-r",
            f"{fps:.6f}",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output),
        ],
        check=True,
    )
    intermediate.unlink()
    return "h264"


def run_video_inference(
    *,
    input_path: Path,
    output_dir: Path,
    detector: Detector,
    frame_stride: int = 5,
    confidence: float = 0.25,
    image_size: int = 640,
    target_classes: list[str] | None = None,
    warmup_runs: int = 1,
) -> dict[str, Any]:
    if frame_stride < 1:
        raise ValueError("frame_stride must be at least 1")
    if not 0.0 < confidence <= 1.0:
        raise ValueError("confidence must be in the range (0, 1]")
    if not input_path.is_file():
        raise FileNotFoundError(f"Input video does not exist: {input_path}")

    targets = target_classes or []
    output_dir.mkdir(parents=True, exist_ok=True)
    detections_path = output_dir / "detections.jsonl"
    frames_path = output_dir / "frame-metrics.csv"
    summary_path = output_dir / "summary.json"
    intermediate_path = output_dir / "annotated-intermediate.mp4"
    annotated_path = output_dir / "annotated.mp4"

    capture = cv2.VideoCapture(str(input_path))
    if not capture.isOpened():
        raise RuntimeError(f"OpenCV could not open: {input_path}")

    fps = float(capture.get(cv2.CAP_PROP_FPS))
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    declared_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    if fps <= 0 or width <= 0 or height <= 0:
        capture.release()
        raise RuntimeError("Input video has invalid metadata")

    ok, first_frame = capture.read()
    if not ok:
        capture.release()
        raise RuntimeError("Input video contains no decodable frames")

    warmup = getattr(detector, "warmup", None)
    if warmup is not None and warmup_runs > 0:
        warmup(
            first_frame,
            confidence=confidence,
            image_size=image_size,
            target_classes=targets,
            runs=warmup_runs,
        )
    capture.set(cv2.CAP_PROP_POS_FRAMES, 0)

    writer = cv2.VideoWriter(
        str(intermediate_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )
    if not writer.isOpened():
        capture.release()
        raise RuntimeError("OpenCV could not create the annotated video")

    frame_index = 0
    inference_latencies_ms: list[float] = []
    frames_with_detections = 0
    detection_classes: Counter[str] = Counter()
    last_detections: list[Detection] = []
    started = time.perf_counter()

    with detections_path.open("w", encoding="utf-8") as detections_file, frames_path.open(
        "w", encoding="utf-8", newline=""
    ) as frames_file:
        csv_writer = csv.DictWriter(
            frames_file,
            fieldnames=[
                "frame_index",
                "timestamp_s",
                "inference_latency_ms",
                "detection_count",
                "max_confidence",
            ],
        )
        csv_writer.writeheader()

        while True:
            ok, frame = capture.read()
            if not ok:
                break

            sampled = frame_index % frame_stride == 0
            if sampled:
                inference_started = time.perf_counter()
                last_detections = detector.predict(
                    frame,
                    confidence=confidence,
                    image_size=image_size,
                    target_classes=targets,
                )
                latency_ms = (time.perf_counter() - inference_started) * 1000.0
                inference_latencies_ms.append(latency_ms)
                if last_detections:
                    frames_with_detections += 1
                detection_classes.update(item.class_name for item in last_detections)

                record = {
                    "frame_index": frame_index,
                    "timestamp_s": round(frame_index / fps, 6),
                    "inference_latency_ms": round(latency_ms, 3),
                    "detections": [item.to_dict() for item in last_detections],
                }
                detections_file.write(json.dumps(record, ensure_ascii=False) + "\n")
                csv_writer.writerow(
                    {
                        "frame_index": frame_index,
                        "timestamp_s": record["timestamp_s"],
                        "inference_latency_ms": record["inference_latency_ms"],
                        "detection_count": len(last_detections),
                        "max_confidence": round(
                            max((item.confidence for item in last_detections), default=0.0),
                            6,
                        ),
                    }
                )

            writer.write(_draw_detections(frame, last_detections, sampled))
            frame_index += 1

    processing_seconds = time.perf_counter() - started
    capture.release()
    writer.release()
    codec = _write_h264(intermediate_path, annotated_path, fps)

    processed_frames = len(inference_latencies_ms)
    inference_seconds = sum(inference_latencies_ms) / 1000.0
    summary: dict[str, Any] = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input": {
            "file": input_path.name,
            "width": width,
            "height": height,
            "fps": round(fps, 6),
            "declared_frames": declared_frames,
            "decoded_frames": frame_index,
            "duration_s": round(frame_index / fps, 3),
        },
        "configuration": {
            "model": detector.model_name,
            "device": detector.device,
            "image_size": image_size,
            "confidence": confidence,
            "target_classes": targets,
            "frame_stride": frame_stride,
            "warmup_runs": warmup_runs,
            "effective_sampling_fps": round(fps / frame_stride, 3),
        },
        "performance": {
            "processed_frames": processed_frames,
            "processing_wall_time_s": round(processing_seconds, 3),
            "pipeline_fps": round(frame_index / processing_seconds, 3),
            "inference_fps": round(processed_frames / inference_seconds, 3)
            if inference_seconds
            else 0.0,
            "mean_inference_latency_ms": round(
                sum(inference_latencies_ms) / processed_frames, 3
            )
            if processed_frames
            else 0.0,
            "p50_inference_latency_ms": round(percentile(inference_latencies_ms, 50), 3),
            "p95_inference_latency_ms": round(percentile(inference_latencies_ms, 95), 3),
        },
        "detections": {
            "sampled_frames_with_detections": frames_with_detections,
            "sampled_frame_detection_rate": round(
                frames_with_detections / processed_frames, 6
            )
            if processed_frames
            else 0.0,
            "count_by_class": dict(sorted(detection_classes.items())),
        },
        "artifacts": {
            "annotated_video": annotated_path.name,
            "annotated_video_codec": codec,
            "detections_jsonl": detections_path.name,
            "frame_metrics_csv": frames_path.name,
        },
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary
