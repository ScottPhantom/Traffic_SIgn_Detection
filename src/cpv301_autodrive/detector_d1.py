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
    # Draw the highest number first so that label 1 (most confident) ends up on top.
    for number, detection in reversed(list(enumerate(detections, start=1))):
        x1, y1, x2, y2 = detection.box
        colour = "#2563eb" if detection.sign.verified else "#94a3b8"
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
            "#": number,
            "Mã QCVN": d.sign.code,
            "Biển": d.sign.name_vi,
            "Tin cậy": round(d.confidence, 3),
            "Kiểm chứng": "Có" if d.sign.verified else "Chưa",
            "Khung (x1, y1, x2, y2)": ", ".join(f"{v:.0f}" for v in d.box),
        }
        for number, d in enumerate(detections, start=1)
    ]


# ------------------------------------------------------------------------------------- scene

SCENE_W, SCENE_H = 960, 420
HORIZON_Y = 70
CAR_Y = SCENE_H - 70
NEAR_BOX_FRACTION = 0.18  # a box this tall (fraction of frame height) is drawn at the car line


def _half_road(y: float) -> float:
    """Half the road width at scene height y (matches the drawn trapezoid)."""
    t = (y - HORIZON_Y) / (SCENE_H - HORIZON_Y)
    return SCENE_W * (0.05 + 0.42 * t)


def scene_positions(
    detections: list[Detection], frame_w: int, frame_h: int
) -> list[dict[str, float]]:
    """Map each box to the perspective scene.

    Depth: a taller box is nearer, so it is drawn lower and larger. Side: a box left or right of
    the image centre stands on that roadside, further out the further it is from the centre; a box
    near the centre hangs over the road. Signs that would overlap are stacked on one pole, as
    combined signs are in reality. A visual cue from the image, not a measured distance.
    """
    out = []
    for detection in detections:
        x1, y1, x2, y2 = detection.box
        u = min(1.0, max(0.0, (x1 + x2) / 2 / max(frame_w, 1)))
        near = min(1.0, max(0.0, (y2 - y1) / max(frame_h, 1) / NEAR_BOX_FRACTION))
        y = HORIZON_Y + 30 + near * (CAR_Y - HORIZON_Y - 90)
        r = 12 + 22 * near
        offset = (u - 0.5) * 2
        if abs(offset) < 0.15:
            x = SCENE_W / 2 + offset * _half_road(y)
        else:
            side = 1 if offset > 0 else -1
            x = SCENE_W / 2 + side * (_half_road(y) + r + 8 + abs(offset) * 60 * (0.4 + near))
        out.append({"x": x, "y": y, "r": r, "u": u, "near": near, "pole_y": y})
    for i, pos in enumerate(out):  # stack overlapping signs on the earlier sign's pole
        for other in out[:i]:
            if (
                abs(pos["x"] - other["x"]) < pos["r"] + other["r"]
                and abs(pos["y"] - other["y"]) < pos["r"] + other["r"]
            ):
                pos["x"] = other["x"]
                pos["y"] = other["y"] - other["r"] - pos["r"] - 4
                pos["pole_y"] = other["pole_y"]
    for pos in out:
        pos["x"] = min(SCENE_W - pos["r"] - 4, max(pos["r"] + 4, pos["x"]))
        pos["y"] = max(pos["r"] + 4, pos["y"])
    return out


def _side(u: float) -> str:
    return "trái" if u < 0.4 else ("phải" if u > 0.6 else "giữa")


def scene_svg(
    detections: list[Detection], frame_w: int, frame_h: int, command: VehicleCommand
) -> str:
    """Perspective road with each detected sign at its image position (numbered as in the image)."""
    w, h, hy = SCENE_W, SCENE_H, HORIZON_Y
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
    positions = scene_positions(detections, frame_w, frame_h)
    order = sorted(range(len(detections)), key=lambda i: positions[i]["y"])  # far first
    for index in order:
        detection, pos = detections[index], positions[index]
        x, y, r = pos["x"], pos["y"], pos["r"]
        colour = "#2563eb" if detection.sign.verified else "#94a3b8"
        pole = min(h - 10, pos["pole_y"] + pos["r"] * 2.4)
        outer = 1 if x >= w / 2 else -1
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
            f'font-family="sans-serif">{detection.sign.code}</text>',
        ]
    arrow = {"left": "↖", "right": "↗", "stop": "■"}.get(command.steering, "↑")
    parts += [
        f'<rect x="{w / 2 - 34}" y="{CAR_Y}" width="68" height="44" rx="10" fill="#f97316"/>',
        f'<text x="{w / 2}" y="{CAR_Y + 31}" font-size="26" text-anchor="middle" fill="white" '
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


def scene_rows(detections: list[Detection], frame_w: int, frame_h: int) -> list[dict[str, Any]]:
    twins = same_board(detections)
    positions = scene_positions(detections, frame_w, frame_h)
    rows = []
    for index, (d, p) in enumerate(zip(detections, positions, strict=True)):
        near = p["near"]
        rows.append(
            {
                "#": index + 1,
                "Mã QCVN": d.sign.code,
                "Vị trí": f"bên {_side(p['u'])}",
                "Khoảng cách (ước lượng từ cỡ khung)": (
                    "gần" if near > 0.6 else ("vừa" if near > 0.25 else "xa")
                ),
                "Tác động": "có" if d.sign.verified else "không (chưa kiểm chứng)",
                "Ghi chú": (
                    f"trùng khung với #{twins[index] + 1}: một bảng, model gán hai lớp"
                    if index in twins
                    else ""
                ),
            }
        )
    return rows
