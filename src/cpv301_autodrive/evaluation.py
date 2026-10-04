from __future__ import annotations

import csv
import hashlib
import json
import pickle
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_recall_fscore_support,
)

from cpv301_autodrive.labels import GTSRB_LABELS


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_gtsrb_split(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Load one trusted GTSRB pickle and validate the classifier contract."""

    with path.open("rb") as stream:
        payload = pickle.load(stream)  # noqa: S301 - local artifact has a recorded checksum
    if not isinstance(payload, dict) or not {"features", "labels"} <= payload.keys():
        raise ValueError(f"{path} must contain features and labels")
    images = np.asarray(payload["features"])
    labels = np.asarray(payload["labels"])
    if images.ndim != 4 or images.shape[1:] != (32, 32, 3):
        raise ValueError(f"Expected images shaped (N, 32, 32, 3), got {images.shape}")
    if labels.ndim != 1 or len(labels) != len(images):
        raise ValueError(f"Expected one class id per image, got labels {labels.shape}")
    if images.dtype != np.uint8 or images.min() < 0 or images.max() > 255:
        raise ValueError("Expected raw uint8 pixels in the range 0..255")
    if np.any((labels < 0) | (labels >= len(GTSRB_LABELS))):
        raise ValueError("Class ids must be in the range 0..42")
    return images.astype(np.float32) / np.float32(255.0), labels.astype(np.int64)


def expected_calibration_error(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    confidence: np.ndarray,
    n_bins: int = 10,
) -> float:
    """Return top-label expected calibration error using equal-width bins."""

    if n_bins < 1:
        raise ValueError("n_bins must be positive")
    correct = (y_true == y_pred).astype(np.float64)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    result = 0.0
    for index in range(n_bins):
        lower, upper = edges[index], edges[index + 1]
        mask = (confidence >= lower) & (confidence <= upper)
        if index > 0:
            mask &= confidence > lower
        if mask.any():
            result += float(mask.mean()) * abs(
                float(correct[mask].mean()) - float(confidence[mask].mean())
            )
    return result


def evaluate_classifier(
    model_path: Path,
    split_path: Path,
    output_dir: Path,
    batch_size: int = 256,
    threshold: float = 0.50,
) -> dict[str, Any]:
    """Evaluate the 43-class model and persist reproducible diagnostic tables."""

    from tensorflow import keras

    images, y_true = load_gtsrb_split(split_path)
    model = keras.models.load_model(model_path, compile=False)
    probabilities = np.asarray(
        model.predict(images, batch_size=batch_size, verbose=0),
        dtype=np.float64,
    )
    expected_shape = (len(y_true), len(GTSRB_LABELS))
    if probabilities.shape != expected_shape:
        raise ValueError(f"Expected model output {expected_shape}, got {probabilities.shape}")
    if not np.isfinite(probabilities).all() or np.any(probabilities < 0):
        raise ValueError("Model probabilities must be finite and non-negative")
    probability_sums = probabilities.sum(axis=1, keepdims=True)
    if np.any(probability_sums <= 0):
        raise ValueError("Every model output row must have a positive sum")
    probabilities /= probability_sums

    y_pred = probabilities.argmax(axis=1)
    confidence = probabilities.max(axis=1)
    accepted = confidence >= threshold
    wrong = y_pred != y_true
    labels = np.arange(len(GTSRB_LABELS))
    precision, recall, per_class_f1, support = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=labels,
        zero_division=0,
    )
    matrix = confusion_matrix(y_true, y_pred, labels=labels)

    confusion_rows: list[dict[str, Any]] = []
    for true_id in labels:
        for predicted_id in labels:
            count = int(matrix[true_id, predicted_id])
            if true_id != predicted_id and count:
                confusion_rows.append(
                    {
                        "count": count,
                        "true_class_id": int(true_id),
                        "true_label": GTSRB_LABELS[true_id],
                        "predicted_class_id": int(predicted_id),
                        "predicted_label": GTSRB_LABELS[predicted_id],
                    }
                )
    confusion_rows.sort(key=lambda row: row["count"], reverse=True)

    summary: dict[str, Any] = {
        "created_utc": datetime.now(UTC).isoformat(),
        "scope": "Closed-set evaluation on the downloaded GTSRB test split",
        "model": {
            "path": str(model_path),
            "sha256": sha256_file(model_path),
        },
        "dataset": {
            "path": str(split_path),
            "sha256": sha256_file(split_path),
            "samples": int(len(y_true)),
            "classes": len(GTSRB_LABELS),
        },
        "metrics": {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "macro_f1": float(f1_score(y_true, y_pred, average="macro")),
            "weighted_f1": float(f1_score(y_true, y_pred, average="weighted")),
            "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
            "negative_log_loss": float(log_loss(y_true, probabilities, labels=labels)),
            "top_label_ece_10_bins": expected_calibration_error(
                y_true,
                y_pred,
                confidence,
            ),
            "mean_confidence": float(confidence.mean()),
            "wrong_predictions": int(wrong.sum()),
            "wrong_predictions_confidence_ge_0_90": int((wrong & (confidence >= 0.90)).sum()),
            "threshold": threshold,
            "coverage_at_threshold": float(accepted.mean()),
            "accepted_accuracy": float((y_pred[accepted] == y_true[accepted]).mean()),
        },
        "top_confusions": confusion_rows[:10],
        "evidence_boundary": (
            "These metrics measure cropped German GTSRB signs only. They do not establish "
            "performance on Vietnamese signs, full camera scenes, unknown signs, or driving safety."
        ),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    with (output_dir / "per_class_metrics.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["class_id", "label", "precision", "recall", "f1", "support"])
        for class_id in labels:
            writer.writerow(
                [
                    int(class_id),
                    GTSRB_LABELS[class_id],
                    float(precision[class_id]),
                    float(recall[class_id]),
                    float(per_class_f1[class_id]),
                    int(support[class_id]),
                ]
            )

    with (output_dir / "confusion_matrix.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["true_class_id", *[int(class_id) for class_id in labels]])
        for class_id, row in enumerate(matrix):
            writer.writerow([class_id, *[int(value) for value in row]])

    mistake_indices = np.flatnonzero(wrong)
    ranked_mistakes = mistake_indices[np.argsort(confidence[mistake_indices])[::-1]]
    with (output_dir / "high_confidence_mistakes.csv").open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "sample_index",
                "true_class_id",
                "true_label",
                "predicted_class_id",
                "predicted_label",
                "confidence",
            ]
        )
        for sample_index in ranked_mistakes:
            writer.writerow(
                [
                    int(sample_index),
                    int(y_true[sample_index]),
                    GTSRB_LABELS[y_true[sample_index]],
                    int(y_pred[sample_index]),
                    GTSRB_LABELS[y_pred[sample_index]],
                    float(confidence[sample_index]),
                ]
            )

    return summary
