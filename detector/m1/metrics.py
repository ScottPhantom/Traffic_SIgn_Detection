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
from dataclasses import dataclass, field

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
    image_width: int = 0
    image_height: int = 0
    unknown_boxes: np.ndarray = field(default_factory=lambda: np.zeros((0, 4), dtype=float))


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
    precision: float
    agnostic_recall: float
    fp_per_image: float
    images: int
    ground_truth: int
    true_positives: int
    false_positives: int
    per_class_hits: dict[int, int]
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
        precision=hits / (hits + fps) if hits + fps else 0.0,
        agnostic_recall=hits / support if support else 0.0,
        fp_per_image=fps / len(frames) if frames else 0.0,
        images=len(frames),
        ground_truth=support,
        true_positives=hits,
        false_positives=fps,
        per_class_hits=dict(sorted(class_hits.items())),
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


def resolution_breakdown(frames: Sequence[Frame], conf: float) -> dict[str, dict[str, float | int]]:
    groups: dict[str, list[Frame]] = {}
    for frame in frames:
        key = f"{frame.image_width}x{frame.image_height}"
        groups.setdefault(key, []).append(frame)
    report: dict[str, dict[str, float | int]] = {}
    for key, members in sorted(groups.items()):
        point = operating_point(members, conf)
        report[key] = {
            "images": len(members),
            "ground_truth": point.ground_truth,
            "true_positives": point.true_positives,
            "false_positives": point.false_positives,
            "precision": point.precision,
            "agnostic_recall": point.agnostic_recall,
            "fp_per_image": point.fp_per_image,
        }
    return report


def _greedy_pairs(
    frame: Frame, conf: float, iou_threshold: float = IOU_MATCH
) -> tuple[list[tuple[int, int]], list[int], list[int]]:
    pred_indices = np.flatnonzero(frame.pred_scores >= conf)
    pred_indices = pred_indices[np.argsort(-frame.pred_scores[pred_indices], kind="stable")]
    ious = iou_matrix(frame.pred_boxes, frame.gt_boxes)
    used_gt: set[int] = set()
    pairs: list[tuple[int, int]] = []
    unmatched_predictions: list[int] = []
    for pred_index in pred_indices.tolist():
        candidates = ious[pred_index].copy()
        for gt_index in used_gt:
            candidates[gt_index] = -1.0
        best = int(np.argmax(candidates)) if len(candidates) else -1
        if best >= 0 and candidates[best] >= iou_threshold:
            used_gt.add(best)
            pairs.append((best, pred_index))
        else:
            unmatched_predictions.append(pred_index)
    unmatched_gt = [index for index in range(len(frame.gt_boxes)) if index not in used_gt]
    return pairs, unmatched_gt, unmatched_predictions


def confusion_matrix(frames: Sequence[Frame], conf: float, classes: int) -> list[list[int]]:
    """Rows are ground truth and columns predictions; the last index is background."""
    background = classes
    matrix = np.zeros((classes + 1, classes + 1), dtype=int)
    for frame in frames:
        pairs, missed, false_predictions = _greedy_pairs(frame, conf)
        for gt_index, pred_index in pairs:
            matrix[int(frame.gt_classes[gt_index]), int(frame.pred_classes[pred_index])] += 1
        for gt_index in missed:
            matrix[int(frame.gt_classes[gt_index]), background] += 1
        for pred_index in false_predictions:
            matrix[background, int(frame.pred_classes[pred_index])] += 1
    return matrix.tolist()


def error_samples(frames: Sequence[Frame], conf: float, limit: int = 20) -> dict[str, list[str]]:
    samples = {"missed_sign": [], "wrong_class": [], "false_or_wrong_box": []}
    for frame in frames:
        pairs, missed, false_predictions = _greedy_pairs(frame, conf)
        if missed and len(samples["missed_sign"]) < limit:
            samples["missed_sign"].append(frame.stem)
        if any(
            frame.gt_classes[gt] != frame.pred_classes[pred] for gt, pred in pairs
        ) and len(samples["wrong_class"]) < limit:
            samples["wrong_class"].append(frame.stem)
        if false_predictions and len(samples["false_or_wrong_box"]) < limit:
            samples["false_or_wrong_box"].append(frame.stem)
    return samples


def unknown_false_recognition(
    frames: Sequence[Frame], conf: float
) -> dict[str, float | int | None]:
    support = recognized = 0
    for frame in frames:
        support += len(frame.unknown_boxes)
        predictions = frame.pred_boxes[frame.pred_scores >= conf]
        if len(frame.unknown_boxes) and len(predictions):
            hits = iou_matrix(frame.unknown_boxes, predictions).max(axis=1) >= IOU_MATCH
            recognized += int(hits.sum())
    return {
        "support": support,
        "recognized_as_known": recognized,
        "rate": recognized / support if support else None,
    }


def ap_small(frames: Sequence[Frame], max_area: float = 32.0**2) -> dict[str, float | int | str]:
    """Class-aware 101-point AP for small GT boxes, averaged over IoU 0.50:0.95.

    This is a dependency-free, explicitly named project metric. It uses original-image pixel area
    and is not claimed to be byte-identical to pycocotools area-range handling.
    """
    small_by_class: dict[int, dict[int, np.ndarray]] = {}
    for frame_index, frame in enumerate(frames):
        areas = (
            (frame.gt_boxes[:, 2] - frame.gt_boxes[:, 0])
            * (frame.gt_boxes[:, 3] - frame.gt_boxes[:, 1])
        )
        for cls in sorted(set(frame.gt_classes[areas < max_area].tolist())):
            indices = np.flatnonzero((frame.gt_classes == cls) & (areas < max_area))
            small_by_class.setdefault(int(cls), {})[frame_index] = indices
    values: list[float] = []
    for threshold in np.arange(0.50, 0.96, 0.05):
        class_values: list[float] = []
        for cls, gt_by_frame in small_by_class.items():
            support = sum(len(indices) for indices in gt_by_frame.values())
            predictions = sorted(
                (
                    (float(frame.pred_scores[index]), frame_index, index)
                    for frame_index, frame in enumerate(frames)
                    for index in np.flatnonzero(frame.pred_classes == cls)
                ),
                reverse=True,
            )
            matched = {
                frame_index: np.zeros(len(indices), dtype=bool)
                for frame_index, indices in gt_by_frame.items()
            }
            tp: list[int] = []
            fp: list[int] = []
            for _score, frame_index, pred_index in predictions:
                indices = gt_by_frame.get(frame_index)
                if indices is None:
                    tp.append(0)
                    fp.append(1)
                    continue
                overlaps = iou_matrix(
                    frames[frame_index].pred_boxes[pred_index : pred_index + 1],
                    frames[frame_index].gt_boxes[indices],
                )[0]
                overlaps[matched[frame_index]] = -1.0
                best = int(np.argmax(overlaps)) if len(overlaps) else -1
                hit = best >= 0 and overlaps[best] >= threshold
                tp.append(int(hit))
                fp.append(int(not hit))
                if hit:
                    matched[frame_index][best] = True
            if not predictions:
                class_values.append(0.0)
                continue
            cum_tp, cum_fp = np.cumsum(tp), np.cumsum(fp)
            recall = cum_tp / support
            precision = cum_tp / np.maximum(cum_tp + cum_fp, 1)
            interpolated = [
                float(precision[recall >= level].max()) if np.any(recall >= level) else 0.0
                for level in np.linspace(0.0, 1.0, 101)
            ]
            class_values.append(float(np.mean(interpolated)))
        if class_values:
            values.append(float(np.mean(class_values)))
    return {
        "value": float(np.mean(values)) if values else 0.0,
        "classes": len(small_by_class),
        "support": sum(
            len(indices) for rows in small_by_class.values() for indices in rows.values()
        ),
        "method": "project_class_aware_101point_iou_0.50_0.95_original_area_lt_32sq",
    }


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
