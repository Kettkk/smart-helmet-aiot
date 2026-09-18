from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Detection:
    class_id: int
    class_name: str
    confidence: float
    bbox_xyxy: list[float]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class UltralyticsDetector:
    """Small adapter that keeps the third-party model outside pipeline logic."""

    def __init__(self, model: str, device: str = "cpu") -> None:
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError(
                "Ultralytics is not installed. Install vision-service/requirements.txt."
            ) from exc

        self.model_name = Path(model).name
        self.device = device
        self._model = YOLO(model)
        names = self._model.names
        self._names = names if isinstance(names, dict) else dict(enumerate(names))

    def _class_ids(self, target_classes: list[str]) -> list[int] | None:
        if not target_classes:
            return None
        name_to_id = {name: class_id for class_id, name in self._names.items()}
        unknown = sorted(set(target_classes) - set(name_to_id))
        if unknown:
            raise ValueError(f"Unknown model classes: {', '.join(unknown)}")
        return [name_to_id[name] for name in target_classes]

    def predict(
        self,
        frame: Any,
        *,
        confidence: float,
        image_size: int,
        target_classes: list[str],
    ) -> list[Detection]:
        result = self._model.predict(
            source=frame,
            conf=confidence,
            imgsz=image_size,
            device=self.device,
            classes=self._class_ids(target_classes),
            verbose=False,
        )[0]

        if result.boxes is None:
            return []

        xyxy = result.boxes.xyxy.cpu().tolist()
        confidences = result.boxes.conf.cpu().tolist()
        class_ids = result.boxes.cls.cpu().tolist()
        return [
            Detection(
                class_id=int(class_id),
                class_name=result.names[int(class_id)],
                confidence=round(float(score), 6),
                bbox_xyxy=[round(float(value), 2) for value in bounds],
            )
            for bounds, score, class_id in zip(xyxy, confidences, class_ids)
        ]

    def warmup(
        self,
        frame: Any,
        *,
        confidence: float,
        image_size: int,
        target_classes: list[str],
        runs: int,
    ) -> None:
        for _ in range(runs):
            self.predict(
                frame,
                confidence=confidence,
                image_size=image_size,
                target_classes=target_classes,
            )
