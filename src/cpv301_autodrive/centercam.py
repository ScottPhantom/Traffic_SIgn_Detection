"""CenterCam ("xác định điểm giữa cam"): road heading and roadside layout from boxes.

Model-agnostic on purpose: it takes only an image and pixel boxes `(x1, y1, x2, y2)`, so any
detector (the current 54-class YOLO D1, a one-class detector + classifier, a future architecture)
can use it. It never imports a model.

1. `center_cam(image)` estimates the x of the road vanishing point, i.e. the road heading, which
   differs from the image centre when the camera is yawed. OpenCV Canny + probabilistic Hough run
   only inside the asphalt region; the estimate is declined (falls back to the image centre) when
   the frame shows too little road or the line evidence disagrees.
2. `side_of(box, heading)` says whether a sign stands left of, right of, or over the road.
3. `layout(boxes, ...)` places boxes in a perspective scene: side from the heading, depth from box
   height, and signs that are physically adjacent in the image (same pole) stacked together.

Everything here is a visual estimate from one image, not a measured position or distance.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np
from PIL import Image

Box = tuple[float, float, float, float]  # x1, y1, x2, y2 in image pixels

ROAD_MIN_FRACTION = 0.35  # of the lower 60 % of the frame; below it CenterCam declines
MIN_SUPPORT = 0.35  # share of intersection weight within ±6 % width of the median
CENTRE_BAND = 0.06  # |box centre - heading| below this fraction of the width = over the road


@dataclass(frozen=True)
class ImagePosition:
    """Position in the displayed image, independent of road/lane estimation."""

    side: str
    center_x: float
    center_y: float
    normalized_x: float


def image_position(box: Box, frame_w: int, frame_h: int) -> ImagePosition:
    """Thirds of the image by box centre; exact 1/3 and 2/3 belong to the middle.

    Coordinates must describe a positive-area box inside the original displayed frame.
    This describes image position only, never road side, lane applicability or distance.
    """
    if frame_w <= 0 or frame_h <= 0:
        raise ValueError("frame dimensions must be positive")
    if len(box) != 4 or not all(math.isfinite(value) for value in box):
        raise ValueError("box must contain four finite coordinates")
    x1, y1, x2, y2 = box
    if not (0 <= x1 < x2 <= frame_w and 0 <= y1 < y2 <= frame_h):
        raise ValueError("box must have positive area inside the frame")
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    side = "trái" if cx < frame_w / 3 else ("phải" if cx > frame_w * 2 / 3 else "giữa")
    return ImagePosition(side, cx, cy, cx / frame_w)


SCENE_W, SCENE_H = 960, 420
HORIZON_Y = 70
CAR_Y = SCENE_H - 70
NEAR_BOX_FRACTION = 0.18  # a box this tall (fraction of frame height) is drawn at the car line


@dataclass(frozen=True)
class Heading:
    x: float  # heading x used for left/right (CenterCam estimate or image centre)
    source: str  # "centercam" or "image_centre"
    info: dict[str, float] = field(default_factory=dict)

    @property
    def estimated(self) -> bool:
        return self.source == "centercam"


def vanishing_x(image: Image.Image) -> tuple[float | None, dict[str, float]]:
    """Road vanishing-point x, or None when not trustworthy (with the evidence used)."""
    import cv2

    rgb = np.asarray(image.convert("RGB"))
    h, w = rgb.shape[:2]
    top = int(h * 0.4)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)[top:]
    mask = ((hsv[..., 1] < 50) & (hsv[..., 2] > 50) & (hsv[..., 2] < 215)).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    best, area = 0, 0
    for index in range(1, count):
        _x, y, _w, height, size = stats[index]
        if y + height >= mask.shape[0] - 2 and size > area:
            best, area = index, int(size)
    info: dict[str, float] = {"road_fraction": round(area / mask.size, 3)}
    if best == 0 or area / mask.size < ROAD_MIN_FRACTION:
        return None, info
    road = cv2.dilate((labels == best).astype(np.uint8), np.ones((9, 9), np.uint8))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)[top:]
    edges = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 60, 160) * road
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 50, minLineLength=40, maxLineGap=20)
    segments = []
    for x1, y1, x2, y2 in lines.reshape(-1, 4) if lines is not None else []:
        if x2 == x1:
            continue
        slope = (y2 - y1) / (x2 - x1)
        if 0.15 < abs(slope) < 4:
            segments.append((slope, x1, y1 + top, float(np.hypot(x2 - x1, y2 - y1))))
    xs, weights = [], []
    for (m1, a1, b1, l1), (m2, a2, b2, l2) in itertools.combinations(segments, 2):
        if abs(m1 - m2) < 0.25 or ((m1 > 0) == (m2 > 0) and abs(1 / m1 - 1 / m2) < 0.3):
            continue
        x = (m1 * a1 - m2 * a2 + b2 - b1) / (m1 - m2)
        y = m1 * (x - a1) + b1
        if 0 <= x <= w and 0.15 * h <= y <= 0.75 * h:
            xs.append(x)
            weights.append(l1 * l2)
    info["intersections"] = len(xs)
    if len(xs) < 3:
        return None, info
    order = np.argsort(xs)
    xs_sorted, weights_sorted = np.asarray(xs)[order], np.asarray(weights)[order]
    cumulative = np.cumsum(weights_sorted)
    median = float(xs_sorted[np.searchsorted(cumulative, cumulative[-1] / 2)])
    support = float(weights_sorted[np.abs(xs_sorted - median) < 0.06 * w].sum() / cumulative[-1])
    info["support"] = round(support, 3)
    if support < MIN_SUPPORT:
        return None, info
    return median, info


def center_cam(image: Image.Image) -> Heading:
    """Road heading for left/right decisions; the image centre when CenterCam declines."""
    x, info = vanishing_x(image)
    if x is None:
        return Heading(image.width / 2, "image_centre", info)
    return Heading(x, "centercam", info)


def offset(box: Box, heading_x: float, frame_w: int) -> float:
    """Signed horizontal offset of the box centre from the heading, as a fraction of the width."""
    return ((box[0] + box[2]) / 2 - heading_x) / max(frame_w, 1)


def side_of(box: Box, heading_x: float, frame_w: int) -> str:
    """'trái', 'phải' or 'giữa' (over the road) relative to the road heading."""
    value = offset(box, heading_x, frame_w)
    return "giữa" if abs(value) < CENTRE_BAND else ("trái" if value < 0 else "phải")


def nearness(box: Box, frame_h: int) -> float:
    """0 (far, small box) … 1 (near, tall box); a size cue, not a distance."""
    return min(1.0, max(0.0, (box[3] - box[1]) / max(frame_h, 1) / NEAR_BOX_FRACTION))


def same_pole(a: Box, b: Box) -> bool:
    """Boxes physically adjacent in the image: overlapping columns and a small vertical gap."""
    overlap = min(a[2], b[2]) - max(a[0], b[0])
    narrower = min(a[2] - a[0], b[2] - b[0])
    gap = max(a[1], b[1]) - min(a[3], b[3])
    taller = max(a[3] - a[1], b[3] - b[1])
    return narrower > 0 and overlap >= 0.5 * narrower and gap <= 0.6 * taller


def _half_road(y: float) -> float:
    """Half the drawn road width at scene height y (matches the scene trapezoid)."""
    return SCENE_W * (0.05 + 0.42 * (y - HORIZON_Y) / (SCENE_H - HORIZON_Y))


@dataclass
class Placement:
    x: float
    y: float
    r: float
    side: str
    near: float
    pole_y: float
    pole_of: int | None = None  # index of the box whose pole this one shares


def layout(
    boxes: Sequence[Box],
    frame_w: int,
    frame_h: int,
    heading_x: float,
    *,
    image_regions: bool = False,
) -> list[Placement]:
    """Scene placement for boxes in detector order.

    Side from the heading; distance from the heading in the image sets how far out on that roadside
    a sign stands. Only boxes adjacent in the image (`same_pole`) are stacked on one pole; any other
    scene collision is resolved by moving the later sign outward, never by stacking.
    """
    placements: list[Placement] = []
    for box in boxes:
        position = image_position(box, frame_w, frame_h)
        near = nearness(box, frame_h)
        y = HORIZON_Y + 30 + near * (CAR_Y - HORIZON_Y - 90)
        r = 12 + 22 * near
        value = offset(box, heading_x, frame_w)
        side = position.side if image_regions else side_of(box, heading_x, frame_w)
        if side == "giữa":
            band = 1 / 6 if image_regions else CENTRE_BAND
            x = SCENE_W / 2 + value / band * 0.5 * _half_road(y)
        else:
            out = 1 if value > 0 else -1
            x = SCENE_W / 2 + out * (_half_road(y) + r + 8 + abs(value) * SCENE_W * 0.6)
        placements.append(Placement(x, y, r, side, near, y))
    for index, (box, place) in enumerate(zip(boxes, placements, strict=True)):
        for other in range(index):
            if same_pole(box, boxes[other]) and place.side == placements[other].side:
                base = placements[other]
                place.x, place.side = base.x, base.side
                above = box[1] < boxes[other][1]
                place.y = base.y + (-1 if above else 1) * (base.r + place.r + 4)
                place.pole_y, place.pole_of = base.pole_y, other
                break
    for index, place in enumerate(placements):  # push non-pole collisions outward
        if place.pole_of is not None:
            continue
        for other in placements[:index]:
            while (
                abs(place.x - other.x) < place.r + other.r + 6
                and abs(place.y - other.y) < place.r + other.r + 6
            ):
                place.x += (1 if place.x >= SCENE_W / 2 else -1) * (place.r + other.r + 6)
    for place in placements:
        place.x = min(SCENE_W - place.r - 4, max(place.r + 4, place.x))
        place.y = max(place.r + 4, place.y)
    return placements
