"""D1 detector (YOLO11s, 54 Vietnamese sign classes) for the Streamlit simulation demo.

Loads the registered pilot checkpoint (seed 20261018, `best.pt`, SHA-256 pinned) and runs it on a
full-scene frame with the evaluated settings: 1280 px, NMS IoU 0.70, MPS when available. Results
are simulation-only. The checkpoint has validation evidence only (R10: mAP50 0.869, FP/image 0.569
at conf 0.20) and has not passed D-05 acceptance.

Behaviour is triggered only for classes that have sealed-test support (dataset card section 6);
the other classes are shown as "chưa kiểm chứng" and never change the simulated command.
"""

from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from cpv301_autodrive.behavior import VehicleCommand

REPO_ROOT = Path(__file__).resolve().parents[2]
RUN = "D1_yolo11s_wp33_afa03d4b_20261018_20261021T111233_pilot_100e_seed_20261018_r2"
WEIGHTS = REPO_ROOT / "results/experiments" / RUN / "weights/best.pt"
WEIGHTS_SHA256 = "5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633"
CLASS_MAP = REPO_ROOT / "docs/review/generated/m1_yolo_classes.csv"
SAMPLE_DIR = REPO_ROOT / "data/processed/m1_yolo_wp38_r1_integration_r4/images/val"
# Hand-picked validation frames where D1 is right (40/60 km/h, no left/right turn, no entry,
# crossing). They illustrate the pipeline; they are not representative of D1's error rate.
SAMPLE_STEMS = ("1951", "1227", "1807", "0708", "1822", "1724")

IMGSZ = 1280
NMS_IOU = 0.70
DEFAULT_CONF = 0.20

# Classes without sealed-test support (docs/dataset01_card_r1.md, section 6): display only.
UNVERIFIED_KEYS = frozenset(
    "1 15 16:2.0 16:2.2 16:2.5 21 24 27 29 33 35 36 37 38 42 43:2.5 43:2.7 44 47 48 49 51".split()
)
_SPEED = re.compile(r"\((\d+) km/h\)")


@dataclass(frozen=True)
class SignClass:
    yolo_id: int
    key: str
    code: str
    name_vi: str

    @property
    def verified(self) -> bool:
        return self.key not in UNVERIFIED_KEYS


@dataclass(frozen=True)
class Detection:
    sign: SignClass
    confidence: float
    box: tuple[float, float, float, float]  # xyxy pixels

    @property
    def label(self) -> str:
        return f"{self.sign.code} · {self.sign.name_vi}"


def load_classes(path: Path = CLASS_MAP) -> list[SignClass]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    classes = sorted(
        (
            SignClass(int(r["yolo_id"]), r["derived_key"], r["derived_code"], r["name_vi"])
            for r in rows
        ),
        key=lambda c: c.yolo_id,
    )
    if [c.yolo_id for c in classes] != list(range(54)):
        raise RuntimeError("D1 class map is not the dense 54-class range")
    return classes


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def weights_available(path: Path = WEIGHTS) -> bool:
    return path.is_file()


def sample_images() -> list[Path]:
    """A few corrected validation frames for the live demo (display only, never training)."""
    found = []
    for stem in SAMPLE_STEMS:
        matches = sorted(SAMPLE_DIR.glob(f"{stem}.*")) if SAMPLE_DIR.is_dir() else []
        found += matches[:1]
    return found


class D1Detector:
    """Lazy, hash-checked Ultralytics loader; one instance is cached by the app."""

    def __init__(self, weights: Path = WEIGHTS) -> None:
        if not weights.is_file():
            raise FileNotFoundError(f"D1 weights not found: {weights}")
        if sha256_file(weights) != WEIGHTS_SHA256:
            raise RuntimeError("D1 weights differ from the registered best.pt (5d5815a9…)")
        import torch
        from ultralytics import YOLO

        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        self.model = YOLO(str(weights))
        self.classes = load_classes()

    def detect(self, image: Image.Image, conf: float = DEFAULT_CONF) -> list[Detection]:
        result = self.model.predict(
            source=image.convert("RGB"),
            conf=conf,
            iou=NMS_IOU,
            imgsz=IMGSZ,
            device=self.device,
            max_det=300,
            verbose=False,
        )[0]
        boxes = result.boxes
        detections = [
            Detection(self.classes[int(c)], float(s), tuple(float(v) for v in b))
            for b, c, s in zip(
                boxes.xyxy.cpu().numpy(),
                boxes.cls.cpu().numpy(),
                boxes.conf.cpu().numpy(),
                strict=True,
            )
        ]
        return sorted(detections, key=lambda d: -d.confidence)


def draw_detections(image: Image.Image, detections: list[Detection]) -> Image.Image:
    canvas = image.convert("RGB").copy()
    draw = ImageDraw.Draw(canvas)
    width = max(2, round(canvas.width / 400))
    try:
        font = ImageFont.truetype("Arial.ttf", max(18, canvas.width // 40))
    except OSError:
        font = ImageFont.load_default()
    for detection in detections:
        x1, y1, x2, y2 = detection.box
        colour = "#2563eb" if detection.sign.verified else "#94a3b8"
        draw.rectangle((x1, y1, x2, y2), outline=colour, width=width)
        text = f"{detection.sign.code} {detection.confidence:.2f}"
        left, top, right, bottom = draw.textbbox((x1, y1), text, font=font)
        lift = bottom - top + 4
        draw.rectangle((left - 2, top - lift - 2, right + 2, bottom - lift + 2), fill=colour)
        draw.text((x1, y1 - lift), text, fill="white", font=font)
    return canvas


def plan_vn_behavior(detections: list[Detection], cruise_speed_kmh: int = 30) -> VehicleCommand:
    """Deterministic simulated command from the verified detections (most restrictive wins)."""
    verified = [d for d in detections if d.sign.verified]
    if not verified:
        reason = (
            "Không có biển đã kiểm chứng trong khung hình; giữ tốc độ hành trình."
            if not detections
            else "Chỉ thấy lớp chưa kiểm chứng; hiển thị nhưng không đổi hành vi."
        )
        return VehicleCommand("continue", cruise_speed_kmh, "straight", reason)

    codes = {d.sign.code for d in verified}
    if "P.102" in codes:
        return VehicleCommand("stop", 0, "stop", "Biển P.102 cấm đi ngược chiều: dừng xe.")
    limits = [int(m.group(1)) for d in verified if (m := _SPEED.search(d.sign.name_vi))]
    speed = min([cruise_speed_kmh, *limits])
    reasons = [f"tốc độ tối đa {min(limits)} km/h"] if limits else []
    steering = "straight"
    if codes & {"P.123a", "P.124c"}:
        reasons.append("cấm rẽ trái: giữ làn đi thẳng")
    if codes & {"P.123b", "P.124d"}:
        reasons.append("cấm rẽ phải: giữ làn đi thẳng")
    if "R.302a" in codes:
        steering = "right"
        reasons.append("phải đi vòng sang bên phải")
    if any(code.startswith("W.") for code in codes):
        speed = min(speed, 20)
        reasons.append("biển cảnh báo: giảm tốc")
    if codes & {"W.224", "W.225"}:
        speed = min(speed, 15)
    action = (
        "set_speed_limit" if limits else ("slow_down" if speed < cruise_speed_kmh else "continue")
    )
    if not reasons:
        reasons.append("biển thông tin/cấm đỗ: không ảnh hưởng tốc độ")
    return VehicleCommand(action, speed, steering, "Mô phỏng: " + "; ".join(reasons) + ".")


def detection_rows(detections: list[Detection]) -> list[dict[str, Any]]:
    return [
        {
            "Mã QCVN": d.sign.code,
            "Biển": d.sign.name_vi,
            "Tin cậy": round(d.confidence, 3),
            "Kiểm chứng": "Có" if d.sign.verified else "Chưa",
            "Khung (x1, y1, x2, y2)": ", ".join(f"{v:.0f}" for v in d.box),
        }
        for d in detections
    ]
