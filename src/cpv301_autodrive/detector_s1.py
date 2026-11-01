"""YOLO11s one-class sign localization for the still-image teaching demo.

This detector returns boxes for ``traffic_sign`` only. It does not identify sign types
and never produces a simulated vehicle command. The local checkpoint is the same
SHA-256-pinned Cascade B0 detector artifact reviewed in
``docs/review/cascade_b0_r1_result_independent_qa_record.md``.
"""

from __future__ import annotations

import hashlib
import math
import os
import threading
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[2]
WEIGHTS = (
    REPO_ROOT
    / "results/experiments/cascade_classifier_improvement_r1/latency_input_r1/s1_best.pt"
)
WEIGHTS_SHA256 = "30d1d6e0162c4da54ef3c2c1b31f6bbc25f0ea2fa9e76090190addff1307d218"
IMGSZ = 1280
NMS_IOU = 0.70
DEFAULT_CONF = 0.20


@dataclass(frozen=True)
class SignBox:
    confidence: float
    box: tuple[float, float, float, float]


def weights_available(path: Path = WEIGHTS) -> bool:
    return path.is_file()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class S1Detector:
    """Lazy, offline, hash-checked loader for the one-class Cascade detector."""

    def __init__(self, weights: Path = WEIGHTS) -> None:
        if not weights.is_file():
            raise FileNotFoundError(f"S1 weights not found: {weights}")
        if sha256_file(weights) != WEIGHTS_SHA256:
            raise RuntimeError("S1 weights differ from the QA-reviewed Cascade B0 checkpoint")
        os.environ["YOLO_AUTOINSTALL"] = "false"
        os.environ["YOLO_OFFLINE"] = "true"
        import torch
        from ultralytics import YOLO
        from ultralytics.utils import checks

        checks.AUTOINSTALL = False
        checks.ONLINE = False
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        self.model = YOLO(str(weights))
        if len(self.model.names) != 1 or 0 not in self.model.names:
            raise RuntimeError("S1 checkpoint does not have exactly one detector class")
        self._lock = threading.Lock()

    def detect(self, image: Image.Image, conf: float = DEFAULT_CONF) -> list[SignBox]:
        if not math.isfinite(conf) or not 0 < conf <= 1:
            raise ValueError("confidence must be finite and in (0, 1]")
        rgb = image.convert("RGB")
        with self._lock:
            result = self.model.predict(
                source=rgb,
                conf=conf,
                iou=NMS_IOU,
                imgsz=IMGSZ,
                device=self.device,
                max_det=300,
                verbose=False,
            )[0]
        if result.boxes is None:
            return []
        detections = []
        for b, c, score in zip(
            result.boxes.xyxy.cpu().numpy(),
            result.boxes.cls.cpu().numpy(),
            result.boxes.conf.cpu().numpy(),
            strict=True,
        ):
            values = [float(v) for v in b]
            confidence = float(score)
            class_id = float(c)
            if not all(math.isfinite(v) for v in [*values, confidence, class_id]):
                continue
            if class_id != 0 or not conf <= confidence <= 1:
                continue
            x1, y1, x2, y2 = (
                max(0.0, min(rgb.width, values[0])),
                max(0.0, min(rgb.height, values[1])),
                max(0.0, min(rgb.width, values[2])),
                max(0.0, min(rgb.height, values[3])),
            )
            if x2 <= x1 or y2 <= y1:
                continue
            detections.append(SignBox(confidence, (x1, y1, x2, y2)))
        return sorted(detections, key=lambda d: -d.confidence)


def draw_boxes(image: Image.Image, detections: list[SignBox]) -> Image.Image:
    canvas = image.convert("RGB").copy()
    draw = ImageDraw.Draw(canvas)
    width = max(2, round(canvas.width / 400))
    try:
        font = ImageFont.truetype("Arial.ttf", max(16, canvas.width // 45))
    except OSError:
        font = ImageFont.load_default()
    for number, detection in reversed(list(enumerate(detections, start=1))):
        x1, y1, x2, y2 = detection.box
        draw.rectangle((x1, y1, x2, y2), outline="#176153", width=width)
        label = f"#{number}  {detection.confidence:.2f}"
        left, top, right, bottom = draw.textbbox((x1, y1), label, font=font)
        label_y = max(0, y1 - (bottom - top) - 8)
        draw.rectangle(
            (x1, label_y, x1 + right - left + 8, label_y + bottom - top + 8),
            fill="#176153",
        )
        draw.text((x1 + 4, label_y + 4), label, fill="white", font=font)
    return canvas


def detection_rows(detections: list[SignBox]) -> list[dict[str, object]]:
    return [
        {
            "#": number,
            "Đối tượng": "Biển báo",
            "Tin cậy": round(detection.confidence, 3),
            "Khung (x1, y1, x2, y2)": ", ".join(f"{value:.0f}" for value in detection.box),
        }
        for number, detection in enumerate(detections, start=1)
    ]
