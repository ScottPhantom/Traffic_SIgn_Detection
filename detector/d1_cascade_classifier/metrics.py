"""Classifier metrics computed from integer targets and finite probabilities."""

from __future__ import annotations

from typing import Any

import numpy as np

from .contract import CLASSES


def classification_metrics(
    targets: np.ndarray, probabilities: np.ndarray, *, bins: int = 15
) -> dict[str, Any]:
    targets = np.asarray(targets)
    probabilities = np.asarray(probabilities, dtype=np.float64)
    if targets.ndim != 1 or probabilities.shape != (len(targets), CLASSES) or len(targets) == 0:
        raise ValueError("targets/probabilities shape differs")
    if not np.issubdtype(targets.dtype, np.integer) or np.any((targets < 0) | (targets >= CLASSES)):
        raise ValueError("targets must be integer class ids 0..53")
    if not np.all(np.isfinite(probabilities)) or np.any(probabilities < 0):
        raise ValueError("probabilities must be finite and non-negative")
    if not np.allclose(probabilities.sum(axis=1), 1.0, atol=1e-6):
        raise ValueError("probability rows must sum to one")
    predictions = probabilities.argmax(axis=1)
    per_class: dict[str, dict[str, float | int | None]] = {}
    recalls: list[float] = []
    f1s: list[float] = []
    for class_id in range(CLASSES):
        true = targets == class_id
        predicted = predictions == class_id
        support = int(true.sum())
        tp = int(np.sum(true & predicted))
        fp = int(np.sum(~true & predicted))
        fn = support - tp
        recall = tp / support if support else None
        precision = tp / (tp + fp) if tp + fp else None
        f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None
        per_class[str(class_id)] = {
            "support": support,
            "true_positives": tp,
            "recall": recall,
            "precision": precision,
            "f1": f1,
        }
        if recall is not None:
            recalls.append(recall)
            assert f1 is not None
            f1s.append(f1)
    confidence = probabilities.max(axis=1)
    correct = predictions == targets
    edges = np.linspace(0.0, 1.0, bins + 1)
    ece = 0.0
    calibration: list[dict[str, float | int | None]] = []
    for index in range(bins):
        mask = (confidence >= edges[index]) & (
            confidence <= edges[index + 1] if index == bins - 1 else confidence < edges[index + 1]
        )
        count = int(mask.sum())
        average_confidence = float(confidence[mask].mean()) if count else None
        accuracy = float(correct[mask].mean()) if count else None
        if count:
            assert average_confidence is not None and accuracy is not None
            ece += count / len(targets) * abs(accuracy - average_confidence)
        calibration.append(
            {
                "lower": float(edges[index]),
                "upper": float(edges[index + 1]),
                "count": count,
                "accuracy": accuracy,
                "average_confidence": average_confidence,
            }
        )
    return {
        "samples": int(len(targets)),
        "top1_accuracy": float(correct.mean()),
        "macro_f1_supported_classes": float(np.mean(f1s)),
        "balanced_accuracy_supported_classes": float(np.mean(recalls)),
        "ece_15_bin": float(ece),
        "represented_classes": len(recalls),
        "unrepresented_classes": [
            int(i) for i in range(CLASSES) if per_class[str(i)]["support"] == 0
        ],
        "per_class": per_class,
        "calibration_bins": calibration,
    }


def latency_stats(milliseconds: list[float]) -> dict[str, float | int]:
    values = np.asarray(milliseconds, dtype=np.float64)
    if values.shape != (300,) or not np.all(np.isfinite(values)) or np.any(values < 0):
        raise ValueError("latency requires exactly 300 finite non-negative measurements")
    return {
        "n": 300,
        "mean_ms": float(values.mean()),
        "p50_ms": float(np.percentile(values, 50)),
        "p95_ms": float(np.percentile(values, 95)),
        "max_ms": float(values.max()),
    }
