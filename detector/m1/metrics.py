"""D-05 detector metrics that Ultralytics does not report directly.

All functions are pure NumPy so they can be unit-tested without a model:
- greedy IoU matching of predictions to ground truth (class-aware or class-agnostic);
- recall per class and class-agnostic recall, false positives per image, at a confidence threshold;
- threshold selection on val (D-05 Q4: recall ≥ target with the fewest FP per image);
- cluster bootstrap over D-02 groups (D-05 Q2);
- latency statistics (D-05 Q5).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

IOU_MATCH = 0.5


@dataclass(frozen=True)
class Frame:
    """Ground truth and predictions of one image. Boxes are xyxy in pixels."""

    stem: str
    group_id: str
    gt_boxes: np.ndarray  # (n, 4)
    gt_classes: np.ndarray  # (n,)
    pred_boxes: np.ndarray  # (m, 4)
    pred_classes: np.ndarray  # (m,)
    pred_scores: np.ndarray  # (m,)


def iou_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    if len(a) == 0 or len(b) == 0:
        return np.zeros((len(a), len(b)))
    x1 = np.maximum(a[:, None, 0], b[None, :, 0])
    y1 = np.maximum(a[:, None, 1], b[None, :, 1])
    x2 = np.minimum(a[:, None, 2], b[None, :, 2])
    y2 = np.minimum(a[:, None, 3], b[None, :, 3])
    inter = np.clip(x2 - x1, 0, None) * np.clip(y2 - y1, 0, None)
    area_a = (a[:, 2] - a[:, 0]) * (a[:, 3] - a[:, 1])
    area_b = (b[:, 2] - b[:, 0]) * (b[:, 3] - b[:, 1])
    return inter / np.maximum(area_a[:, None] + area_b[None, :] - inter, 1e-12)


def match(frame: Frame, conf: float, class_aware: bool) -> tuple[np.ndarray, int]:
    """Greedy match by descending score. Returns (gt matched mask, false-positive count)."""
    keep = frame.pred_scores >= conf
    boxes, classes, scores = (
        frame.pred_boxes[keep],
        frame.pred_classes[keep],
        frame.pred_scores[keep],
    )
    order = np.argsort(-scores, kind="stable")
    ious = iou_matrix(boxes, frame.gt_boxes)
    matched = np.zeros(len(frame.gt_boxes), dtype=bool)
    false_positives = 0
    for index in order:
        candidates = ious[index].copy()
        candidates[matched] = -1.0
        if class_aware:
            candidates[frame.gt_classes != classes[index]] = -1.0
        best = int(np.argmax(candidates)) if len(candidates) else -1
        if best >= 0 and candidates[best] >= IOU_MATCH:
            matched[best] = True
        else:
            false_positives += 1
    return matched, false_positives


@dataclass(frozen=True)
class OperatingPoint:
    conf: float
    agnostic_recall: float
    fp_per_image: float
    per_class_recall: dict[int, float]
    per_class_support: dict[int, int]


def operating_point(frames: Sequence[Frame], conf: float) -> OperatingPoint:
    hits = support = fps = 0
    class_hits: dict[int, int] = {}
    class_support: dict[int, int] = {}
    for frame in frames:
        agnostic, false_positives = match(frame, conf, class_aware=False)
        aware, _ = match(frame, conf, class_aware=True)
        hits += int(agnostic.sum())
        support += len(agnostic)
        fps += false_positives
        for cls, hit in zip(frame.gt_classes.tolist(), aware.tolist(), strict=True):
            class_support[cls] = class_support.get(cls, 0) + 1
            class_hits[cls] = class_hits.get(cls, 0) + int(hit)
    return OperatingPoint(
        conf=conf,
        agnostic_recall=hits / support if support else 0.0,
        fp_per_image=fps / len(frames) if frames else 0.0,
        per_class_recall={c: class_hits[c] / class_support[c] for c in sorted(class_support)},
        per_class_support=dict(sorted(class_support.items())),
    )


def select_threshold(
    frames: Sequence[Frame], target_recall: float = 0.85, grid: Sequence[float] | None = None
) -> OperatingPoint:
    """Highest confidence whose class-agnostic recall still reaches the target (fewest FP).

    If no threshold reaches the target, the threshold with the highest recall is returned and the
    caller must report that the D-05 recall gate is not met on val.
    """
    grid = list(grid) if grid is not None else [round(x, 2) for x in np.arange(0.05, 0.96, 0.05)]
    points = [operating_point(frames, conf) for conf in sorted(grid)]
    reaching = [p for p in points if p.agnostic_recall >= target_recall]
    if reaching:
        return min(reaching, key=lambda p: (p.fp_per_image, -p.conf))
    return max(points, key=lambda p: (p.agnostic_recall, p.conf))


def group_bootstrap(
    frames: Sequence[Frame], conf: float, rounds: int = 1000, seed: int = 20261018
) -> dict[str, tuple[float, float]]:
    """95 % CI of agnostic recall and FP/image, resampling whole D-02 groups."""
    groups: dict[str, list[Frame]] = {}
    for frame in frames:
        groups.setdefault(frame.group_id, []).append(frame)
    names = sorted(groups)
    rng = np.random.default_rng(seed)
    recalls, fps = [], []
    for _ in range(rounds):
        sample = [f for g in rng.choice(names, size=len(names), replace=True) for f in groups[g]]
        point = operating_point(sample, conf)
        recalls.append(point.agnostic_recall)
        fps.append(point.fp_per_image)

    def ci(values: list[float]) -> tuple[float, float]:
        return float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))

    return {"agnostic_recall": ci(recalls), "fp_per_image": ci(fps)}


def latency_stats(milliseconds: Sequence[float]) -> dict[str, float]:
    values = np.asarray(milliseconds, dtype=float)
    return {
        "n": int(values.size),
        "mean_ms": float(values.mean()),
        "p50_ms": float(np.percentile(values, 50)),
        "p95_ms": float(np.percentile(values, 95)),
        "max_ms": float(values.max()),
    }
