"""Validation-only B0 cascade inference and common-method full-scene scoring."""

from __future__ import annotations

import argparse
import csv
import json
import math
import pickle
import stat
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch
from PIL import Image
from run_cascade_b0_r1 import (
    CONFIG,
    CheckpointStore,
    CompactCNN,
    classification_metrics,
    require_safe_directory,
    require_source_qa,
    sha256_file,
    verify_package,
)

from m1.metrics import (
    Frame,
    ap_small,
    confusion_matrix,
    group_bootstrap,
    iou_matrix,
    operating_point,
    resolution_breakdown,
    select_threshold,
)

FIXED_CONFIDENCE = 0.20
GLOBAL_CONFIDENCE_GRID = tuple(round(value, 2) for value in np.arange(0.05, 1.0, 0.05))
PINNED_YOLO54_PREDICTIONS = "data/yolo54_predictions_val.csv"
PINNED_YOLO54_SHA256 = "87884c536e16ac890c11114c85c7c12731571df15d244071a38e3d1db271c893"


def crop_bounds(image: Image.Image, box: np.ndarray) -> tuple[int, int, int, int]:
    """Return the frozen 10%/minimum-5px border clipped to source-frame pixels."""
    x1, y1, x2, y2 = map(float, box)
    if not all(math.isfinite(v) for v in box) or not (
        0 <= x1 < x2 <= image.width and 0 <= y1 < y2 <= image.height
    ):
        raise ValueError("invalid predicted box")
    dx, dy = max(5, (x2 - x1) * 0.1), max(5, (y2 - y1) * 0.1)
    return (
        max(0, math.floor(round(x1 - dx, 6))),
        max(0, math.floor(round(y1 - dy, 6))),
        min(image.width, math.ceil(round(x2 + dx, 6))),
        min(image.height, math.ceil(round(y2 + dy, 6))),
    )


def crop_prediction(image: Image.Image, box: np.ndarray) -> np.ndarray:
    return np.asarray(
        image.crop(crop_bounds(image, box)).resize((32, 32), Image.Resampling.BILINEAR),
        dtype=np.uint8,
    )


def cascade_predictions(
    detector_scores: np.ndarray, probabilities: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Apply the frozen class argmax and detector×classifier confidence rule."""
    detector_scores = np.asarray(detector_scores, dtype=np.float64)
    probabilities = np.asarray(probabilities, dtype=np.float64)
    if (
        detector_scores.ndim != 1
        or probabilities.shape != (len(detector_scores), 54)
        or not np.all(np.isfinite(detector_scores))
        or not np.all(np.isfinite(probabilities))
        or np.any((detector_scores < 0) | (detector_scores > 1))
        or np.any(probabilities < 0)
        or not np.allclose(probabilities.sum(axis=1), 1.0, atol=1e-6)
    ):
        raise ValueError("invalid detector scores or 54-class probabilities")
    return probabilities.argmax(1), detector_scores * probabilities.max(1)


def average_precision(frames: list[Frame], *, agnostic: bool = False) -> dict:
    """Use the pinned Ultralytics matcher and AP integrator for both compared architectures."""
    from ultralytics.engine.validator import BaseValidator
    from ultralytics.utils.metrics import ap_per_class

    validator = SimpleNamespace(iouv=torch.linspace(0.5, 0.95, 10))
    correct, conf, pred, targets = [], [], [], []
    for frame in frames:
        pc = np.zeros_like(frame.pred_classes) if agnostic else frame.pred_classes
        gc = np.zeros_like(frame.gt_classes) if agnostic else frame.gt_classes
        matched = BaseValidator.match_predictions(
            validator,
            torch.as_tensor(pc),
            torch.as_tensor(gc),
            torch.as_tensor(iou_matrix(frame.gt_boxes, frame.pred_boxes)),
        )
        correct.append(matched.numpy())
        conf.append(frame.pred_scores)
        pred.append(pc)
        targets.append(gc)
    target = np.concatenate(targets)
    if not len(target) or not sum(map(len, pred)):
        return {"map50": 0.0, "map50_95": 0.0, "supported_classes": np.unique(target).tolist()}
    result = ap_per_class(
        np.concatenate(correct),
        np.concatenate(conf),
        np.concatenate(pred),
        target,
        plot=False,
        names={i: str(i) for i in range(54)},
    )
    ap, classes = result[5], result[6]
    return {
        "map50": float(ap[:, 0].mean()),
        "map50_95": float(ap.mean()),
        "supported_classes": classes.tolist(),
        "per_class_ap50": dict(zip(map(int, classes), map(float, ap[:, 0]), strict=True)),
    }


def report(frames: list[Frame]) -> dict:
    fixed = operating_point(frames, FIXED_CONFIDENCE)
    selected = select_threshold(frames, target_recall=0.85, grid=GLOBAL_CONFIDENCE_GRID)
    return {
        "method": "pinned Ultralytics IoU matching/AP; m1 D-05 operating points",
        "exact_class_ap": average_precision(frames),
        "agnostic_ap": average_precision(frames, agnostic=True),
        "fixed_conf_020": asdict(fixed),
        "selected_on_val": asdict(selected),
        "selected_recall_target_met": selected.agnostic_recall >= 0.85,
        "ap_small_project_method": ap_small(frames),
        "confidence_grid": list(GLOBAL_CONFIDENCE_GRID),
        "selection_policy": "recall>=0.85, then minimum FP/image, then highest confidence",
        "confusion_fixed_020": confusion_matrix(frames, FIXED_CONFIDENCE, 54),
        "resolution_fixed_020": resolution_breakdown(frames, FIXED_CONFIDENCE),
        "bootstrap_fixed_020": group_bootstrap(frames, FIXED_CONFIDENCE),
        "sealed_test_accessed": False,
    }


def infer(
    root: Path, detector_weights: Path, classifier_weights: Path, device: str
) -> tuple[list[Frame], list[Frame], dict]:
    from ultralytics import YOLO, settings
    from ultralytics.utils import checks

    checks.AUTOINSTALL = checks.ONLINE = False
    settings.update({"sync": False, "wandb": False, "mlflow": False, "clearml": False})
    detector = YOLO(str(detector_weights))
    classifier = CompactCNN().to(device)
    saved = torch.load(classifier_weights, map_location="cpu", weights_only=False)
    classifier.load_state_dict(saved["model"])
    classifier.eval()
    with (root / "data/valid.p").open("rb") as handle:
        validation = pickle.load(handle)
    with torch.inference_mode():
        inputs = (
            torch.from_numpy(validation["features"].transpose(0, 3, 1, 2).copy()).float().to(device)
            / 255
        )
        probabilities = torch.softmax(classifier((inputs - 0.5) / 0.5), 1).cpu().numpy()
    gt_classifier = classification_metrics(validation["labels"], probabilities)
    groups = json.loads((root / "data/val_groups.json").read_text())
    frames = []
    detector_frames = []
    for path in sorted((root / "data/images/val").iterdir()):
        with Image.open(path) as source:
            image = source.convert("RGB")
        gt_classes, gt_boxes = [], []
        for row in (root / f"data/labels54/val/{path.stem}.txt").read_text().splitlines():
            cls, cx, cy, w, h = map(float, row.split())
            gt_classes.append(int(cls))
            gt_boxes.append(
                [
                    (cx - w / 2) * image.width,
                    (cy - h / 2) * image.height,
                    (cx + w / 2) * image.width,
                    (cy + h / 2) * image.height,
                ]
            )
        result = detector.predict(
            image, conf=0.001, iou=0.70, imgsz=1280, device=device, verbose=False
        )[0]
        boxes = result.boxes.xyxy.cpu().numpy()
        boxes[:, [0, 2]] = boxes[:, [0, 2]].clip(0, image.width)
        boxes[:, [1, 3]] = boxes[:, [1, 3]].clip(0, image.height)
        keep = np.isfinite(boxes).all(1) & (boxes[:, 2] > boxes[:, 0]) & (boxes[:, 3] > boxes[:, 1])
        boxes, detector_scores = boxes[keep], result.boxes.conf.cpu().numpy()[keep]
        classes, scores = np.zeros(0, dtype=int), np.zeros(0)
        if len(boxes):
            crops = np.stack([crop_prediction(image, box) for box in boxes])
            with torch.inference_mode():
                tensor = (
                    torch.from_numpy(crops.transpose(0, 3, 1, 2).copy()).float().to(device) / 255
                )
                probs = torch.softmax(classifier((tensor - 0.5) / 0.5), 1).cpu().numpy()
            classes, scores = cascade_predictions(detector_scores, probs)
        frames.append(
            Frame(
                path.stem,
                groups[path.stem],
                np.asarray(gt_boxes).reshape(-1, 4),
                np.asarray(gt_classes, dtype=int),
                boxes,
                classes,
                scores,
                image.width,
                image.height,
            )
        )
        detector_frames.append(
            replace(
                frames[-1],
                gt_classes=np.zeros(len(gt_classes), dtype=int),
                pred_classes=np.zeros(len(boxes), dtype=int),
                pred_scores=detector_scores,
            )
        )
    return frames, detector_frames, gt_classifier


def verify_stage_weights(root: Path, state: Path, stage: str, weights: Path) -> None:
    binding = {"manifest": sha256_file(root / "manifest.json"), "config": CONFIG, "stage": stage}
    store = CheckpointStore(state / stage / "recovery", retention=1000)
    checkpoint = store.load_latest(binding)
    if checkpoint["completed_epoch"] != CONFIG[f"{stage}_epochs"]:
        raise RuntimeError("evaluation requires a completed verified stage")
    expected = next(entry for entry in checkpoint["files"] if entry["path"] == "weights/best.pt")
    require_safe_directory(weights.parent)
    info = weights.lstat()

    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_nlink != 1
        or sha256_file(weights) != expected["sha256"]
    ):
        raise RuntimeError("weights differ from verified completed Drive checkpoint")


def verify_evaluation_scope(root: Path, baseline_csv: Path, baseline_sha256: str) -> dict:
    """Bind evaluation to the bundle's validation-only roster and pinned YOLO54 predictions."""
    expected_baseline = root / PINNED_YOLO54_PREDICTIONS
    if baseline_csv != expected_baseline:
        raise RuntimeError("baseline must be the pinned prediction CSV inside the verified bundle")
    if baseline_sha256 != PINNED_YOLO54_SHA256 or sha256_file(baseline_csv) != baseline_sha256:
        raise RuntimeError("baseline prediction anchor differs")
    manifest = json.loads((root / "manifest.json").read_text())
    if (
        manifest.get("test_included") is not False
        or manifest.get("sealed_test_accessed") is not False
        or manifest.get("counts") != {
            "train": {"images": 3712, "boxes": 12621},
            "val": {"images": 376, "boxes": 624},
        }
        or (root / "data/test").exists()
        or (root / "data/images/test").exists()
        or (root / "data/labels/test").exists()
    ):
        raise RuntimeError("evaluation scope is not the governed validation-only package")
    image_stems = {
        path.stem for path in (root / "data/images/val").iterdir() if path.is_file()
    }
    label_stems = {
        path.stem for path in (root / "data/labels54/val").iterdir() if path.is_file()
    }
    groups = json.loads((root / "data/val_groups.json").read_text())
    if len(image_stems) != 376 or label_stems != image_stems or set(groups) != image_stems:
        raise RuntimeError("validation roster differs from the governed 376-frame roster")
    boxes = sum(
        len([row for row in path.read_text().splitlines() if row.strip()])
        for path in (root / "data/labels54/val").iterdir()
        if path.is_file()
    )
    if boxes != 624:
        raise RuntimeError("validation GT differs from the governed 624-box roster")
    return {
        "split": "val",
        "frames": len(image_stems),
        "gt_boxes": boxes,
        "yolo54_predictions_sha256": baseline_sha256,
        "sealed_test_accessed": False,
    }


def load_pinned_baseline(frames: list[Frame], path: Path) -> list[Frame]:
    """Load the already hash-verified comparison CSV and reject malformed/out-of-scope rows."""
    by_stem = {frame.stem: [] for frame in frames}
    dimensions = {frame.stem: (frame.image_width, frame.image_height) for frame in frames}
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        expected = ["stem", "rank", "yolo_id", "conf", "x1", "y1", "x2", "y2"]
        if reader.fieldnames != expected:
            raise RuntimeError("baseline prediction schema differs")
        for row in reader:
            stem = row["stem"]
            if stem not in by_stem:
                raise RuntimeError("baseline contains a non-validation stem")
            try:
                rank = int(row["rank"])
                class_id = int(row["yolo_id"])
                confidence = float(row["conf"])
                box = [float(row[key]) for key in ("x1", "y1", "x2", "y2")]
            except (TypeError, ValueError) as error:
                raise RuntimeError("baseline contains malformed prediction values") from error
            width, height = dimensions[stem]
            if (
                rank < 0
                or not 0 <= class_id < 54
                or not math.isfinite(confidence)
                or not 0 <= confidence <= 1
                or not all(math.isfinite(value) for value in box)
                # Preserve the pinned YOLO54 CSV exactly. It contains boundary-clipped,
                # zero-area low-confidence rows that the common matcher treats as non-matches.
                or not (0 <= box[0] <= box[2] <= width and 0 <= box[1] <= box[3] <= height)
            ):
                raise RuntimeError("baseline contains an invalid prediction")
            by_stem[stem].append((box, class_id, confidence))
    return [
        replace(
            frame,
            pred_boxes=np.asarray([row[0] for row in by_stem[frame.stem]]).reshape(-1, 4),
            pred_classes=np.asarray([row[1] for row in by_stem[frame.stem]], dtype=int),
            pred_scores=np.asarray([row[2] for row in by_stem[frame.stem]], dtype=float),
        )
        for frame in frames
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--source-qa-sha256", required=True)
    parser.add_argument("--source-qa-record", type=Path, required=True)
    parser.add_argument("--detector", type=Path, required=True)
    parser.add_argument("--classifier", type=Path, required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--baseline-csv", type=Path, required=True)
    parser.add_argument("--baseline-csv-sha256", required=True)
    args = parser.parse_args()
    root = require_safe_directory(args.root)
    verify_package(root, args.manifest_sha256)
    require_source_qa(root, args.source_qa_record, args.source_qa_sha256)
    require_safe_directory(args.output.parent)
    csv_output = args.output.with_suffix(".csv")
    if any(path.exists() or path.is_symlink() for path in (args.output, csv_output)):
        raise RuntimeError("refuse overwriting comparison results")
    preflight = verify_evaluation_scope(root, args.baseline_csv, args.baseline_csv_sha256)
    state = require_safe_directory(args.state)
    verify_stage_weights(root, state, "detector", args.detector)
    verify_stage_weights(root, state, "classifier", args.classifier)
    frames, detector_frames, gt_classifier = infer(
        root, args.detector, args.classifier, args.device
    )
    result = {
        **report(frames),
        "gt_crop_classifier": gt_classifier,
        "detector_only": report(detector_frames),
        "weights": {
            "detector": sha256_file(args.detector),
            "classifier": sha256_file(args.classifier),
        },
        "evaluation_preflight": preflight,
    }
    baseline = load_pinned_baseline(frames, args.baseline_csv)
    result["yolo54_common_method"] = report(baseline)
    result["yolo54_predictions_sha256"] = args.baseline_csv_sha256
    with csv_output.open("x", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["stem", "class_id", "confidence", "x1", "y1", "x2", "y2"])
        for frame in frames:
            for box, cls, score in zip(
                frame.pred_boxes, frame.pred_classes, frame.pred_scores, strict=True
            ):
                writer.writerow([frame.stem, int(cls), float(score), *map(float, box)])
    result["prediction_csv_sha256"] = sha256_file(csv_output)
    # JSON is the last publication marker; absence means the comparison is incomplete.
    with args.output.open("x") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)


if __name__ == "__main__":
    main()
