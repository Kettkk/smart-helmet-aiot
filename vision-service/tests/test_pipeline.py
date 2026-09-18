from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

from app.detector import Detection
from app.pipeline import percentile, run_video_inference


class FakeDetector:
    model_name = "fake-detector"
    device = "cpu"

    def predict(self, frame, **kwargs):
        return [Detection(0, "person", 0.9, [10.0, 10.0, 50.0, 70.0])]


def create_video(path: Path, frame_count: int = 12) -> None:
    writer = cv2.VideoWriter(
        str(path), cv2.VideoWriter_fourcc(*"mp4v"), 12.0, (96, 64)
    )
    assert writer.isOpened()
    for index in range(frame_count):
        frame = np.full((64, 96, 3), index * 10, dtype=np.uint8)
        writer.write(frame)
    writer.release()


def test_percentile_uses_linear_interpolation():
    assert percentile([10.0, 20.0, 30.0], 50) == 20.0
    assert percentile([10.0, 20.0], 95) == 19.5
    assert percentile([], 95) == 0.0


def test_pipeline_writes_reproducible_artifacts(tmp_path: Path):
    source = tmp_path / "source.mp4"
    output = tmp_path / "results"
    create_video(source)

    summary = run_video_inference(
        input_path=source,
        output_dir=output,
        detector=FakeDetector(),
        frame_stride=3,
        confidence=0.25,
        image_size=640,
        target_classes=["person"],
        warmup_runs=0,
    )

    assert summary["input"]["decoded_frames"] == 12
    assert summary["performance"]["processed_frames"] == 4
    assert summary["detections"]["count_by_class"] == {"person": 4}
    assert (output / "annotated.mp4").is_file()
    assert (output / "frame-metrics.csv").is_file()

    lines = (output / "detections.jsonl").read_text().splitlines()
    assert [json.loads(line)["frame_index"] for line in lines] == [0, 3, 6, 9]
