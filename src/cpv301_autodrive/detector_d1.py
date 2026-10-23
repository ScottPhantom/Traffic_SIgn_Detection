"""D1 detector (YOLO11s, 54 Vietnamese sign classes) for the Streamlit simulation demo.

Loads the registered pilot checkpoint (seed 20261018, `best.pt`, SHA-256 pinned) and runs it on a
full-scene frame with the evaluated settings: 1280 px, NMS IoU 0.70, MPS when available. Results
are simulation-only. The checkpoint has validation evidence only (R10: mAP50 0.869, FP/image 0.569
at conf 0.20) and has not passed D-05 acceptance.

Classes without held-out support and classes 7/32/41 failing the current validation checks are
display-only. Remaining classes can illustrate a command, without a D-05 acceptance claim.
"""

from __future__ import annotations

import csv
import hashlib
import math
import os
import re
import threading
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from cpv301_autodrive import centercam
from cpv301_autodrive.behavior import VehicleCommand

REPO_ROOT = Path(__file__).resolve().parents[2]
RUN = "D1_yolo11s_wp33_afa03d4b_20261018_20261021T111233_pilot_100e_seed_20261018_r2"
WEIGHTS = REPO_ROOT / "results/experiments" / RUN / "weights/best.pt"
WEIGHTS_SHA256 = "5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633"
CLASS_MAP = REPO_ROOT / "docs/review/generated/m1_yolo_classes.csv"
CLASS_MAP_SHA256 = "7cda296a95bd8512a1bb2e85109ce9a1574fb882e692b11d4d0ee6a1cb58d242"
SAMPLE_DIR = REPO_ROOT / "data/processed/m1_yolo_wp38_r1_integration_r4/images/val"
# Hand-picked validation frames where D1 is right (multi-sign 1231, 40/60 km/h, no turns, no entry,
# crossing). They illustrate the pipeline; they are not representative of D1's error rate.
SAMPLE_STEMS = ("1231", "1951", "1227", "1807", "0708", "1822", "1724")

IMGSZ = 1280
NMS_IOU = 0.70
DEFAULT_CONF = 0.20

# Classes without sealed-test support (docs/dataset01_card_r1.md, section 6): display only.
UNVERIFIED_KEYS = frozenset(
    "1 15 16:2.0 16:2.2 16:2.5 21 24 27 29 33 35 36 37 38 42 43:2.5 43:2.7 44 47 48 49 51".split()
)
_SPEED = re.compile(r"\((\d+) km/h\)")
VALIDATION_FAILED_KEYS = frozenset({"7", "32", "41"})


@dataclass(frozen=True)
class SignClass:
    yolo_id: int
    key: str
    code: str
    name_vi: str

    @property
    def verified(self) -> bool:
        """Historical support flag; support alone is not a quality/acceptance verdict."""
        return self.key not in UNVERIFIED_KEYS

    @property
    def behavior_eligible(self) -> bool:
        return self.verified and self.key not in VALIDATION_FAILED_KEYS

    @property
    def status(self) -> str:
        if not self.verified:
            return "Chưa kiểm chứng"
        if self.key in VALIDATION_FAILED_KEYS:
            return "Chưa đạt validation"
        return "Chỉ mô phỏng; chưa nghiệm thu D-05"


@dataclass(frozen=True)
class Detection:
    sign: SignClass
    confidence: float
    box: tuple[float, float, float, float]  # xyxy pixels

    @property
    def label(self) -> str:
        return f"{self.sign.code} · {self.sign.name_vi}"


def load_classes(path: Path = CLASS_MAP) -> list[SignClass]:
    if sha256_file(path) != CLASS_MAP_SHA256:
        raise RuntimeError("D1 class map differs from the governed 54-class map")
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
        # The demo uses a local pinned checkpoint; missing plugins must never trigger installs.
        os.environ["YOLO_AUTOINSTALL"] = "false"
        os.environ["YOLO_OFFLINE"] = "true"
        import torch
        from ultralytics import YOLO
        from ultralytics.utils import checks

        # Also enforce this when another library imported Ultralytics earlier in this process.
        checks.AUTOINSTALL = False
        checks.ONLINE = False

        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        self.model = YOLO(str(weights))
        self.classes = load_classes()
        self._lock = threading.Lock()

    def detect(self, image: Image.Image, conf: float = DEFAULT_CONF) -> list[Detection]:
        if not math.isfinite(conf) or not 0 < conf <= 1:
            raise ValueError("confidence must be finite and in (0, 1]")
        with self._lock:
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
        detections = []
        for b, c, s in zip(
            boxes.xyxy.cpu().numpy(),
            boxes.cls.cpu().numpy(),
            boxes.conf.cpu().numpy(),
            strict=True,
        ):
            values = [float(v) for v in b]
            if not all(math.isfinite(v) for v in [*values, float(c), float(s)]):
                continue
            if int(c) != c or not 0 <= int(c) < len(self.classes) or not conf <= s <= 1:
                continue
            box = (
                max(0.0, min(image.width, values[0])),
                max(0.0, min(image.height, values[1])),
                max(0.0, min(image.width, values[2])),
                max(0.0, min(image.height, values[3])),
            )
            try:
                centercam.image_position(box, image.width, image.height)
            except ValueError:
                continue
            detections.append(Detection(self.classes[int(c)], float(s), box))
        return sorted(detections, key=lambda d: -d.confidence)


def draw_detections(
    image: Image.Image, detections: list[Detection], vanish_x: float | None = None
) -> Image.Image:
    canvas = image.convert("RGB").copy()
    draw = ImageDraw.Draw(canvas)
    for x in (canvas.width / 3, canvas.width * 2 / 3):
        for y in range(0, canvas.height, 24):
            draw.line((x, y, x, min(y + 12, canvas.height)), fill="#64748b", width=2)
    if vanish_x is not None:  # CenterCam dashed line: left/right of it decides the roadside
        for y in range(0, canvas.height, 24):
            draw.line((vanish_x, y, vanish_x, y + 12), fill="#f59e0b", width=3)
    width = max(2, round(canvas.width / 400))
    try:
        font = ImageFont.truetype("Arial.ttf", max(18, canvas.width // 40))
    except OSError:
        font = ImageFont.load_default()
    # Draw the highest number first so that label 1 (most confident) ends up on top.
    for number, detection in reversed(list(enumerate(detections, start=1))):
        x1, y1, x2, y2 = detection.box
        colour = "#2563eb" if detection.sign.behavior_eligible else "#94a3b8"
        draw.rectangle((x1, y1, x2, y2), outline=colour, width=width)
        text = f"{number} · {detection.sign.code} {detection.confidence:.2f}"
        left, top, right, bottom = draw.textbbox((x1, y1), text, font=font)
        lift = bottom - top + 4
        if top - lift < 0:  # no room above the box: put the label just below it
            lift = -(y2 - y1) - 4
        draw.rectangle((left - 2, top - lift - 2, right + 2, bottom - lift + 2), fill=colour)
        draw.text((x1, y1 - lift), text, fill="white", font=font)
    return canvas


def plan_vn_behavior(detections: list[Detection], cruise_speed_kmh: int = 30) -> VehicleCommand:
    """Deterministic illustrative command; unsupported/failed classes never trigger it."""
    verified = [d for d in detections if d.sign.behavior_eligible]
    if not verified:
        reason = (
            "Mô phỏng: không có biển trong khung hình; giữ tốc độ hành trình."
            if not detections
            else "Chỉ thấy lớp chưa kiểm chứng hoặc chưa đạt validation; không đổi hành vi."
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


def detection_rows(
    detections: list[Detection], frame_w: int | None = None, frame_h: int | None = None
) -> list[dict[str, Any]]:
    return [
        {
            "#": number,
            "Mã QCVN": d.sign.code,
            "Biển": d.sign.name_vi,
            "Tin cậy": round(d.confidence, 3),
            "Trạng thái": d.sign.status,
            **(
                {
            "Vị trí trong ảnh": centercam.image_position(d.box, frame_w, frame_h).side,
                    "Tâm X (%)": round(
                        centercam.image_position(d.box, frame_w, frame_h).normalized_x * 100, 1
                    ),
                }
                if frame_w is not None and frame_h is not None
                else {}
            ),
            "Khung (x1, y1, x2, y2)": ", ".join(f"{v:.0f}" for v in d.box),
        }
        for number, d in enumerate(detections, start=1)
    ]


# ------------------------------------------------------------------------------------- scene
# Road heading, roadside side and scene layout live in the model-agnostic `centercam` module;
# this module only adds the D1 sign codes, numbering and colours.


def _layout(
    detections: list[Detection],
    frame_w: int,
    frame_h: int,
    heading_x: float | None,
    *,
    image_regions: bool = False,
) -> list[centercam.Placement]:
    heading = frame_w / 2 if heading_x is None or image_regions else heading_x
    return centercam.layout(
        [d.box for d in detections], frame_w, frame_h, heading, image_regions=image_regions
    )


def scene_svg(
    detections: list[Detection],
    frame_w: int,
    frame_h: int,
    command: VehicleCommand,
    vanish_x: float | None = None,
    *,
    image_regions: bool = False,
) -> str:
    """Perspective road with each detected sign at its image position (numbered as in the image)."""
    w, h, hy = centercam.SCENE_W, centercam.SCENE_H, centercam.HORIZON_Y
    road = f"{w * 0.45},{hy} {w * 0.55},{hy} {w * 0.97},{h} {w * 0.03},{h}"
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" '
        'role="img" aria-label="Cảnh mô phỏng: vị trí từng biển báo theo ảnh">',
        f'<rect width="{w}" height="{hy}" fill="#bfdbfe"/>',
        f'<rect y="{hy}" width="{w}" height="{h - hy}" fill="#86a77a"/>',
        f'<polygon points="{road}" fill="#4b5563"/>',
        f'<line x1="{w / 2}" y1="{hy}" x2="{w / 2}" y2="{h}" stroke="#fde68a" '
        'stroke-width="5" stroke-dasharray="18 16"/>',
    ]
    places = _layout(detections, frame_w, frame_h, vanish_x, image_regions=image_regions)
    order = sorted(range(len(detections)), key=lambda i: places[i].y)  # far first
    for index in order:
        detection, place = detections[index], places[index]
        x, y, r = place.x, place.y, place.r
        colour = "#2563eb" if detection.sign.behavior_eligible else "#94a3b8"
        pole = min(h - 10, place.pole_y + places[place.pole_of or index].r * 2.4)
        label_room = 9 * len(detection.sign.code) + 10
        outer = 1 if x >= w / 2 else -1
        if outer < 0 and x - r - label_room < 0:
            outer = 1  # no room on the left edge: label on the right
        elif outer > 0 and x + r + label_room > w:
            outer = -1
        anchor = "start" if outer > 0 else "end"
        parts += [
            f'<line x1="{x:.1f}" y1="{y + r:.1f}" x2="{x:.1f}" y2="{pole:.1f}" '
            'stroke="#e5e7eb" stroke-width="3"/>',
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#ffffff" '
            f'stroke="{colour}" stroke-width="{max(3, r / 5):.1f}"/>',
            f'<text x="{x:.1f}" y="{y + r * 0.35:.1f}" font-size="{r:.0f}" font-weight="700" '
            f'text-anchor="middle" fill="#0f172a" font-family="sans-serif">{index + 1}</text>',
            f'<text x="{x + outer * (r + 6):.1f}" y="{y + 5:.1f}" font-size="15" '
            f'font-weight="600" text-anchor="{anchor}" fill="#0f172a" '
            f'font-family="sans-serif">{escape(detection.sign.code)}</text>',
        ]
    arrow = {"left": "↖", "right": "↗", "stop": "■"}.get(command.steering, "↑")
    car_y = centercam.CAR_Y
    parts += [
        f'<rect x="{w / 2 - 34}" y="{car_y}" width="68" height="44" rx="10" fill="#f97316"/>',
        f'<text x="{w / 2}" y="{car_y + 31}" font-size="26" text-anchor="middle" fill="white" '
        f'font-family="sans-serif">{arrow}</text>',
        f'<text x="{w - 14}" y="30" font-size="18" text-anchor="end" fill="#0f172a" '
        f'font-family="sans-serif" font-weight="700">{command.target_speed_kmh} km/h</text>',
        "</svg>",
    ]
    return "".join(parts)


def _iou(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    w = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    h = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - w * h
    return w * h / union if union > 0 else 0.0


def same_board(detections: list[Detection], iou: float = 0.8) -> dict[int, int]:
    """Later detection index -> earlier index with the same box (one board, two classes)."""
    out: dict[int, int] = {}
    for i, det in enumerate(detections):
        for j in range(i):
            if _iou(det.box, detections[j].box) >= iou:
                out[i] = j
                break
    return out


def scene_rows(
    detections: list[Detection],
    frame_w: int,
    frame_h: int,
    vanish_x: float | None = None,
    *,
    image_regions: bool = False,
) -> list[dict[str, Any]]:
    twins = same_board(detections)
    places = _layout(detections, frame_w, frame_h, vanish_x, image_regions=image_regions)
    rows = []
    for index, (d, p) in enumerate(zip(detections, places, strict=True)):
        near = p.near
        rows.append(
            {
                "#": index + 1,
                "Mã QCVN": d.sign.code,
                "Vị trí": f"bên {p.side}",
                "Khoảng cách (ước lượng từ cỡ khung)": (
                    "gần" if near > 0.6 else ("vừa" if near > 0.25 else "xa")
                ),
                "Vị trí trong ảnh": centercam.image_position(d.box, frame_w, frame_h).side,
                "Tác động": "chỉ mô phỏng"
                if d.sign.behavior_eligible
                else "không (chưa đạt/chưa kiểm chứng)",
                "Ghi chú": (
                    f"trùng khung với #{twins[index] + 1}: một bảng, model gán hai lớp"
                    if index in twins
                    else ""
                ),
            }
        )
    return rows
