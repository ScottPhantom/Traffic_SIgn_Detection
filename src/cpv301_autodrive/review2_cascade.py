"""Pinned Cascade B0 inference adapter for the local Review 2 demonstration.

This adapter mirrors the validated B0 crop and score contract. Its outputs are
model predictions on an unlabeled clip, never traffic-sign ground truth.
"""

from __future__ import annotations

import math
import os
import threading
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch import nn

from cpv301_autodrive.detector_d1 import (
    CLASS_MAP_SHA256,
    Detection,
    SignClass,
    load_classes,
    sha256_file,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
WEIGHTS_DIR = REPO_ROOT / "models/pretrained/review2_cascade_b0_r1"
DETECTOR_WEIGHTS = WEIGHTS_DIR / "detector_best.pt"
CLASSIFIER_WEIGHTS = WEIGHTS_DIR / "classifier_best.pt"
DETECTOR_SHA256 = "30d1d6e0162c4da54ef3c2c1b31f6bbc25f0ea2fa9e76090190addff1307d218"
CLASSIFIER_SHA256 = "e4d96b8b2a42a96b0338df7f6fc39fa62f7a466bd94d3a90ef59122791e54e98"
CONFIDENCE = 0.20
CANDIDATE_CONFIDENCE = 0.001
NMS_IOU = 0.70
IMGSZ = 1280


@dataclass(frozen=True)
class _DemoOnlySignClass(SignClass):
    @property
    def behavior_eligible(self) -> bool:
        return False

    @property
    def status(self) -> str:
        return "Cascade B0: chỉ hiển thị; chưa kiểm chứng trên clip"


class _CompactCNN(nn.Module):
    """Frozen layer sequence from detector/d1_cascade_classifier/model.py."""

    def __init__(self) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d(1),
        )
        self.classifier = nn.Sequential(nn.Flatten(), nn.Dropout(0.2), nn.Linear(128, 54))

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.features(inputs))


def weights_available() -> bool:
    return DETECTOR_WEIGHTS.is_file() and CLASSIFIER_WEIGHTS.is_file()


def _crop_bounds(image: Image.Image, box: np.ndarray) -> tuple[int, int, int, int]:
    """B0 evaluator's 10%/minimum-5px crop, clipped to source pixels."""
    x1, y1, x2, y2 = map(float, box)
    if not all(math.isfinite(value) for value in box) or not (
        0 <= x1 < x2 <= image.width and 0 <= y1 < y2 <= image.height
    ):
        raise ValueError("Cascade box không hợp lệ.")
    dx, dy = max(5, (x2 - x1) * 0.1), max(5, (y2 - y1) * 0.1)
    return (
        max(0, math.floor(round(x1 - dx, 6))),
        max(0, math.floor(round(y1 - dy, 6))),
        min(image.width, math.ceil(round(x2 + dx, 6))),
        min(image.height, math.ceil(round(y2 + dy, 6))),
    )


class CascadeB0Detector:
    """Full-scene S1 detector followed by frozen 54-class CompactCNN."""

    def __init__(
        self, detector_weights: Path = DETECTOR_WEIGHTS,
        classifier_weights: Path = CLASSIFIER_WEIGHTS,
    ) -> None:
        if (
            not detector_weights.is_file()
            or sha256_file(detector_weights) != DETECTOR_SHA256
            or not classifier_weights.is_file()
            or sha256_file(classifier_weights) != CLASSIFIER_SHA256
        ):
            raise RuntimeError("Cascade B0 weights thiếu hoặc khác hash đã QA.")
        os.environ["YOLO_AUTOINSTALL"] = "false"
        os.environ["YOLO_OFFLINE"] = "true"
        from ultralytics import YOLO
        from ultralytics.utils import checks

        checks.AUTOINSTALL = False
        checks.ONLINE = False
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        self.detector = YOLO(str(detector_weights))
        self.classifier = _CompactCNN().to(self.device)
        saved = torch.load(classifier_weights, map_location="cpu", weights_only=False)
        self.classifier.load_state_dict(saved["model"])
        self.classifier.eval()
        self.classes = [
            _DemoOnlySignClass(c.yolo_id, c.key, c.code, c.name_vi)
            for c in load_classes()
        ]
        self._lock = threading.Lock()

    def detect(self, image: Image.Image, conf: float = CONFIDENCE) -> list[Detection]:
        if not math.isfinite(conf) or not 0 < conf <= 1:
            raise ValueError("Ngưỡng cascade phải thuộc (0, 1].")
        rgb = image.convert("RGB")
        with self._lock:
            result = self.detector.predict(
                rgb, conf=CANDIDATE_CONFIDENCE, iou=NMS_IOU, imgsz=IMGSZ,
                device=self.device, verbose=False,
            )[0]
            boxes = result.boxes.xyxy.cpu().numpy().astype(np.float64)
            detector_scores = result.boxes.conf.cpu().numpy().astype(np.float64)
            if not len(boxes):
                return []
            boxes[:, [0, 2]] = boxes[:, [0, 2]].clip(0, rgb.width)
            boxes[:, [1, 3]] = boxes[:, [1, 3]].clip(0, rgb.height)
            keep = (
                np.isfinite(boxes).all(1)
                & (boxes[:, 2] > boxes[:, 0])
                & (boxes[:, 3] > boxes[:, 1])
                & np.isfinite(detector_scores)
                & (detector_scores >= 0)
                & (detector_scores <= 1)
            )
            boxes, detector_scores = boxes[keep], detector_scores[keep]
            if not len(boxes):
                return []
            crops = np.stack([
                np.asarray(
                    rgb.crop(_crop_bounds(rgb, box)).resize(
                        (32, 32), Image.Resampling.BILINEAR
                    ), dtype=np.uint8,
                )
                for box in boxes
            ])
            with torch.inference_mode():
                inputs = torch.from_numpy(crops.transpose(0, 3, 1, 2).copy()).float()
                inputs = (inputs.to(self.device) / 255 - 0.5) / 0.5
                probabilities = torch.softmax(self.classifier(inputs), 1).cpu().numpy()
        classes = probabilities.argmax(1)
        scores = detector_scores * probabilities.max(1)
        detections = [
            Detection(self.classes[int(class_id)], float(score), tuple(map(float, box)))
            for box, class_id, score in zip(boxes, classes, scores, strict=True)
            if math.isfinite(float(score)) and score >= conf
        ]
        return sorted(detections, key=lambda detection: -detection.confidence)


def model_identity() -> dict[str, str]:
    return {
        "architecture": "cascade_b0_r1",
        "detector_sha256": DETECTOR_SHA256,
        "classifier_sha256": CLASSIFIER_SHA256,
        "class_map_sha256": CLASS_MAP_SHA256,
    }
