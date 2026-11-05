"""Paired A3 − pilot group-bootstrap CIs on the pinned common validation set (D1-A3-PILOT-CI-R1).

Validation-only, prediction-CSV-only description. No model is loaded and no inference, training,
threshold change or sealed-test access happens here. Both models are scored on the same
resampled frames in every bootstrap round; the resampling unit is the intact D-02 capture group.

Inputs are the exact files the append-only common evaluator
``detector/colab/evaluate_d1_a3_r2_common_r1.py`` bound:

* the corrected train/val-only bundle (manifest SHA ``8e6ffe77…``): validation images (for pixel
  dimensions only), ``labels54/val`` GT, ``val_groups.json`` and ``classes.csv``;
* the pilot comparison anchor ``data/yolo54_predictions_val.csv`` inside that bundle;
* the exported A3 prediction CSV and its result JSON.

The point estimates are first checked against the QA-passed result JSON (TP/FP/per-class hits at
0.20 and at the validation-selected point, per-model group-bootstrap CIs, exact-class mAP). Any
mismatch aborts before a CI is computed.

Usage (from ``detector/``)::

    uv run python -m m1.a3_pilot_paired_ci_r1 write    # create the canonical JSON (no overwrite)
    uv run python -m m1.a3_pilot_paired_ci_r1 verify   # recompute and byte-compare
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np

from m1.metrics import Frame, group_bootstrap, iou_matrix, match, operating_point, select_threshold

PACKAGE = "D1-A3-PILOT-PAIRED-CI-R1"
REPO_ROOT = Path(__file__).resolve().parents[2]

BUNDLE = Path("tmp/yolo11n_n1_extract_r1")
BUNDLE_MANIFEST_SHA256 = "8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da"
PILOT_CSV = "data/yolo54_predictions_val.csv"
PILOT_CSV_SHA256 = "87884c536e16ac890c11114c85c7c12731571df15d244071a38e3d1db271c893"
A3_DIR = Path("results/experiments/d1_a3_seed_20261018_r2/evaluation_common_r1")
A3_CSV = A3_DIR / "a3_predictions.csv"
A3_CSV_SHA256 = "e6a25b017bc94a3cf75220fcce1acdfd7bfacb088ca375143e3f0e5046b99ada"
A3_JSON = A3_DIR / "comparison_a3_r1.json"
A3_JSON_SHA256 = "98b8947e379e2dbf88066884ee4540bc669f8402d459b1891b071b53ee2c2c73"
EVALUATOR = Path("detector/colab/evaluate_d1_a3_r2_common_r1.py")
EVALUATOR_SHA256 = "5d8e49bfafc1343ff1cc3fd4064410914ab6e75c23a1108240b09c36dc3ecca6"
REPORT = Path("docs/review/d1_a3_r2_common_validation_report_r1.md")
REPORT_SHA256 = "2c893e0222275d735dbbafb4d7a8e74146e9906dfa16054e087cc507608e5494"
OUT = Path("docs/review/generated/d1_a3_pilot_paired_ci_r1.json")

FRAMES, GT_BOXES, GROUPS, CLASSES = 376, 624, 9, 54
FIXED_CONF = 0.20
A3_SELECTED_CONF, PILOT_SELECTED_CONF = 0.05, 0.20
SELECTION_GRID = tuple(round(value, 2) for value in np.arange(0.05, 1.0, 0.05))
ROUNDS, SEED = 1000, 20261018
FOCUS_KEYS = ("7", "32", "41")  # R3 derived keys (not raw yolo_ids)
LOW_SUPPORT = 30
METRICS = ("correct_class_recall", "agnostic_recall", "fp_per_image")


# ------------------------------------------------------------------------------------ pins


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require(path: Path, expected: str, label: str) -> None:
    if path.is_symlink() or not path.is_file() or sha256_file(path) != expected:
        raise RuntimeError(f"pinned input differs: {label}")


def verify_pins(root: Path, bundle: Path) -> dict[str, str]:
    """Hash every input; validation members are checked against the bundle manifest."""
    _require(root / A3_CSV, A3_CSV_SHA256, "A3 prediction CSV")
    _require(root / A3_JSON, A3_JSON_SHA256, "A3 result JSON")
    _require(root / EVALUATOR, EVALUATOR_SHA256, "common evaluator")
    _require(root / REPORT, REPORT_SHA256, "common validation report")
    _require(bundle / "manifest.json", BUNDLE_MANIFEST_SHA256, "bundle manifest")
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    if (
        manifest.get("test_included") is not False
        or manifest.get("sealed_test_accessed") is not False
        or manifest.get("counts", {}).get("val") != {"images": FRAMES, "boxes": GT_BOXES}
    ):
        raise RuntimeError("bundle is not the governed validation-only package")
    members = manifest["members"]
    used = [
        name
        for name in members
        if name.startswith(("data/images/val/", "data/labels54/val/"))
        or name in ("data/val_groups.json", "data/classes.csv", PILOT_CSV)
    ]
    if any("test" in Path(name).parts for name in used):
        raise RuntimeError("test member requested")
    for name in used:
        _require(bundle / name, members[name]["sha256"], name)
    if members[PILOT_CSV]["sha256"] != PILOT_CSV_SHA256:
        raise RuntimeError("bundle pilot CSV is not the pinned comparison anchor")
    result = json.loads((root / A3_JSON).read_text(encoding="utf-8"))
    if (
        result.get("split") != "val"
        or result.get("sealed_test_accessed") is not False
        or result.get("prediction_csv_sha256") != A3_CSV_SHA256
        or result.get("bundle_manifest_sha256") != BUNDLE_MANIFEST_SHA256
    ):
        raise RuntimeError("A3 result JSON binding differs")
    return {
        "a3_prediction_csv": A3_CSV_SHA256,
        "a3_result_json": A3_JSON_SHA256,
        "bundle_manifest": BUNDLE_MANIFEST_SHA256,
        "bundle_val_classes_csv": members["data/classes.csv"]["sha256"],
        "bundle_val_groups_json": members["data/val_groups.json"]["sha256"],
        "common_evaluator": EVALUATOR_SHA256,
        "common_validation_report": REPORT_SHA256,
        "pilot_prediction_csv": PILOT_CSV_SHA256,
    }


# ------------------------------------------------------------------------------------ load


def class_names(bundle: Path) -> list[str]:
    with (bundle / "data/classes.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    names = [""] * len(rows)
    for row in rows:
        names[int(row["yolo_id"])] = row["derived_key"]
    if len(names) != CLASSES or "" in names or len(set(names)) != CLASSES:
        raise RuntimeError("class map differs")
    return names


def gt_frames(bundle: Path) -> list[Frame]:
    """Rebuild GT exactly as the evaluator does; images are opened for their size only."""
    from PIL import Image

    groups = json.loads((bundle / "data/val_groups.json").read_text(encoding="utf-8"))
    frames: list[Frame] = []
    for path in sorted((bundle / "data/images/val").iterdir()):
        with Image.open(path) as source:
            width, height = source.size
        gt_classes, gt_boxes = [], []
        for row in (bundle / f"data/labels54/val/{path.stem}.txt").read_text().splitlines():
            cls, cx, cy, w, h = map(float, row.split())
            gt_classes.append(int(cls))
            gt_boxes.append(
                [
                    (cx - w / 2) * width,
                    (cy - h / 2) * height,
                    (cx + w / 2) * width,
                    (cy + h / 2) * height,
                ]
            )
        frames.append(
            Frame(
                path.stem,
                groups[path.stem],
                np.asarray(gt_boxes).reshape(-1, 4),
                np.asarray(gt_classes, dtype=int),
                np.zeros((0, 4)),
                np.zeros(0, dtype=int),
                np.zeros(0),
                width,
                height,
            )
        )
    if (
        len(frames) != FRAMES
        or sum(len(f.gt_boxes) for f in frames) != GT_BOXES
        or len({f.group_id for f in frames}) != GROUPS
    ):
        raise RuntimeError("validation roster differs")
    return frames


def with_predictions(
    frames: Sequence[Frame], path: Path, class_field: str, conf_field: str
) -> list[Frame]:
    """Attach CSV predictions in file order, with the evaluator's row validation."""
    by_stem: dict[str, list[tuple[list[float], int, float]]] = {f.stem: [] for f in frames}
    size = {f.stem: (f.image_width, f.image_height) for f in frames}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            stem = row["stem"]
            if stem not in by_stem:
                raise RuntimeError("prediction outside the validation roster")
            box = [float(row[key]) for key in ("x1", "y1", "x2", "y2")]
            cls, conf = int(row[class_field]), float(row[conf_field])
            width, height = size[stem]
            if (
                not 0 <= cls < CLASSES
                or not math.isfinite(conf)
                or not 0 <= conf <= 1
                or not all(math.isfinite(v) for v in box)
                or not (0 <= box[0] <= box[2] <= width and 0 <= box[1] <= box[3] <= height)
            ):
                raise RuntimeError("invalid prediction row")
            by_stem[stem].append((box, cls, conf))
    return [
        replace(
            f,
            pred_boxes=np.asarray([r[0] for r in by_stem[f.stem]]).reshape(-1, 4),
            pred_classes=np.asarray([r[1] for r in by_stem[f.stem]], dtype=int),
            pred_scores=np.asarray([r[2] for r in by_stem[f.stem]], dtype=float),
        )
        for f in frames
    ]


def load(root: Path, bundle: Path) -> tuple[list[Frame], list[Frame], list[str], dict[str, str]]:
    pins = verify_pins(root, bundle)
    base = gt_frames(bundle)
    a3 = with_predictions(base, root / A3_CSV, "class_id", "confidence")
    pilot = with_predictions(base, bundle / PILOT_CSV, "yolo_id", "conf")
    return a3, pilot, class_names(bundle), pins


# ------------------------------------------------------------------------------- statistics


def frame_stats(frames: Sequence[Frame], conf: float) -> dict[str, np.ndarray]:
    """Per-frame additive counts so a resample's score is a sum (identical to operating_point)."""
    n = len(frames)
    stats = {
        "gt": np.zeros(n),
        "agnostic_hits": np.zeros(n),
        "aware_hits": np.zeros(n),
        "fp": np.zeros(n),
        "class_hits": np.zeros((n, CLASSES)),
        "class_support": np.zeros((n, CLASSES)),
        "group": np.asarray([frame.group_id for frame in frames]),
    }
    for i, frame in enumerate(frames):
        agnostic, fps = match(frame, conf, class_aware=False)
        aware, _ = match(frame, conf, class_aware=True)
        stats["gt"][i] = len(frame.gt_boxes)
        stats["agnostic_hits"][i] = agnostic.sum()
        stats["aware_hits"][i] = aware.sum()
        stats["fp"][i] = fps
        np.add.at(stats["class_support"][i], frame.gt_classes, 1)
        np.add.at(stats["class_hits"][i], frame.gt_classes, aware.astype(float))
    return stats


def summarize(stats: dict[str, np.ndarray], index: np.ndarray) -> dict[str, Any]:
    gt = stats["gt"][index].sum()
    support = stats["class_support"][index].sum(0)
    hits = stats["class_hits"][index].sum(0)
    return {
        "correct_class_recall": stats["aware_hits"][index].sum() / gt,
        "agnostic_recall": stats["agnostic_hits"][index].sum() / gt,
        "fp_per_image": stats["fp"][index].sum() / len(index),
        "class_support": support,
        "class_recall": np.divide(hits, support, out=np.full(CLASSES, np.nan), where=support > 0),
    }


def ci95(values: Sequence[float]) -> list[float]:
    return [float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))]


def excludes_zero(interval: Sequence[float]) -> bool:
    return bool(interval[0] > 0 or interval[1] < 0)


def resample_indices(frames: Sequence[Frame], rounds: int, seed: int) -> list[np.ndarray]:
    """Same draw sequence as ``m1.metrics.group_bootstrap``: marginals reproduce its CIs."""
    groups: dict[str, list[int]] = {}
    for i, frame in enumerate(frames):
        groups.setdefault(frame.group_id, []).append(i)
    names = sorted(groups)
    rng = np.random.default_rng(seed)
    return [
        np.asarray([i for g in rng.choice(names, size=len(names), replace=True) for i in groups[g]])
        for _ in range(rounds)
    ]


def paired_block(
    a3: dict[str, np.ndarray],
    pilot: dict[str, np.ndarray],
    samples: Sequence[np.ndarray],
    focus: dict[str, int] | None = None,
) -> dict[str, Any]:
    full = np.arange(len(a3["gt"]))
    point_a3, point_pilot = summarize(a3, full), summarize(pilot, full)
    draws = [(summarize(a3, s), summarize(pilot, s)) for s in samples]
    block: dict[str, Any] = {}
    for metric in METRICS:
        diffs = [x[metric] - y[metric] for x, y in draws]
        interval = ci95(diffs)
        block[metric] = {
            "a3": float(point_a3[metric]),
            "pilot": float(point_pilot[metric]),
            "difference_a3_minus_pilot": float(point_a3[metric] - point_pilot[metric]),
            "paired_ci95": interval,
            "ci_excludes_zero": excludes_zero(interval),
            "a3_marginal_ci95": ci95([x[metric] for x, _ in draws]),
            "pilot_marginal_ci95": ci95([y[metric] for _, y in draws]),
            "share_rounds_difference_gt_0": float(np.mean(np.asarray(diffs) > 0)),
        }
    if focus:
        per_class: dict[str, Any] = {}
        for key, cls in focus.items():
            support = int(point_a3["class_support"][cls])
            entry: dict[str, Any] = {"yolo_id": cls, "support": support}
            if support == 0:
                entry.update(
                    status="UNKNOWN_NO_VALIDATION_SUPPORT", low_support=True, ci_interpretable=False
                )
                per_class[key] = entry
                continue
            defined = [
                x["class_recall"][cls] - y["class_recall"][cls]
                for x, y in draws
                if x["class_support"][cls] > 0
            ]
            interval = ci95(defined)
            groups_with_support = len(set(a3["group"][a3["class_support"][:, cls] > 0]))
            entry.update(
                a3=float(point_a3["class_recall"][cls]),
                pilot=float(point_pilot["class_recall"][cls]),
                difference_a3_minus_pilot=float(
                    point_a3["class_recall"][cls] - point_pilot["class_recall"][cls]
                ),
                paired_ci95=interval,
                ci_excludes_zero=excludes_zero(interval),
                rounds_with_support=len(defined),
                groups_with_support=groups_with_support,
                low_support=bool(support < LOW_SUPPORT or groups_with_support < 3),
                # With one supporting group the resample never varies the class's frames, so the
                # interval collapses to the point estimate and carries no sampling information.
                ci_interpretable=groups_with_support >= 2,
                status=(
                    "ESTIMATED"
                    if groups_with_support >= 2
                    else "DEGENERATE_SINGLE_GROUP_CI_NOT_INFORMATIVE"
                ),
            )
            per_class[key] = entry
        block["per_class_correct_class_recall"] = per_class
    return block


def per_group(a3: dict[str, np.ndarray], pilot: dict[str, np.ndarray]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for group in sorted(set(a3["group"].tolist())):
        index = np.flatnonzero(a3["group"] == group)
        x, y = summarize(a3, index), summarize(pilot, index)
        out[group] = {
            "frames": len(index),
            "gt": int(a3["gt"][index].sum()),
            **{f"{m}_difference": float(x[m] - y[m]) for m in METRICS},
        }
    return out


# ------------------------------------------------------------------------------------- mAP


def _correct_matrices(frames: Sequence[Frame]) -> list[np.ndarray]:
    """Pinned Ultralytics matcher, exactly as ``evaluate_cascade_b0_r1.average_precision``."""
    from types import SimpleNamespace

    import torch
    from ultralytics.engine.validator import BaseValidator

    validator = SimpleNamespace(iouv=torch.linspace(0.5, 0.95, 10))
    return [
        BaseValidator.match_predictions(
            validator,
            torch.as_tensor(f.pred_classes),
            torch.as_tensor(f.gt_classes),
            torch.as_tensor(iou_matrix(f.gt_boxes, f.pred_boxes)),
        ).numpy()
        for f in frames
    ]


def _map50_95(frames: Sequence[Frame], correct: Sequence[np.ndarray], index: np.ndarray) -> float:
    from ultralytics.utils.metrics import ap_per_class

    result = ap_per_class(
        np.concatenate([correct[i] for i in index]),
        np.concatenate([frames[i].pred_scores for i in index]),
        np.concatenate([frames[i].pred_classes for i in index]),
        np.concatenate([frames[i].gt_classes for i in index]),
        plot=False,
        names={i: str(i) for i in range(CLASSES)},
    )
    return float(result[5].mean())


def map_block(
    a3: Sequence[Frame], pilot: Sequence[Frame], samples: Sequence[np.ndarray]
) -> dict[str, Any]:
    ca3, cpilot = _correct_matrices(a3), _correct_matrices(pilot)
    full = np.arange(len(a3))
    pa3, ppilot = _map50_95(a3, ca3, full), _map50_95(pilot, cpilot, full)
    diffs = [_map50_95(a3, ca3, s) - _map50_95(pilot, cpilot, s) for s in samples]
    interval = ci95(diffs)
    return {
        "a3": pa3,
        "pilot": ppilot,
        "difference_a3_minus_pilot": pa3 - ppilot,
        "paired_ci95": interval,
        "ci_excludes_zero": excludes_zero(interval),
        "share_rounds_difference_gt_0": float(np.mean(np.asarray(diffs) > 0)),
        "note": "class set averaged = classes present in each resample (Ultralytics ap_per_class)",
    }


# ----------------------------------------------------------------------------- reproduction


def reproduce(a3: list[Frame], pilot: list[Frame], root: Path) -> dict[str, Any]:
    """Stop unless the matcher reproduces the QA-passed common-evaluator numbers exactly."""
    stored = json.loads((root / A3_JSON).read_text(encoding="utf-8"))
    checks: dict[str, Any] = {}
    for label, frames, key, selected_conf in (
        ("a3", a3, "a3_common_method", A3_SELECTED_CONF),
        ("pilot", pilot, "pilot_common_method", PILOT_SELECTED_CONF),
    ):
        ref = stored[key]
        for point_name, conf in (
            ("fixed_conf_020", FIXED_CONF),
            ("selected_on_val", selected_conf),
        ):
            point = operating_point(frames, conf)
            want = ref[point_name]
            got = {
                "conf": point.conf,
                "true_positives": point.true_positives,
                "false_positives": point.false_positives,
                "ground_truth": point.ground_truth,
                "agnostic_recall": point.agnostic_recall,
                "fp_per_image": point.fp_per_image,
                "per_class_hits": {str(c): h for c, h in point.per_class_hits.items()},
                "per_class_support": {str(c): s for c, s in point.per_class_support.items()},
            }
            if any(got[k] != want[k] for k in got):
                raise RuntimeError(f"{label} {point_name} does not reproduce the result JSON")
        if select_threshold(frames, 0.85, SELECTION_GRID).conf != selected_conf:
            raise RuntimeError(f"{label} validation-selected confidence differs")
        boot = group_bootstrap(frames, FIXED_CONF, ROUNDS, SEED)
        if {k: list(v) for k, v in boot.items()} != ref["bootstrap_fixed_020"]:
            raise RuntimeError(f"{label} per-model group bootstrap does not reproduce")
        fixed = operating_point(frames, FIXED_CONF)
        checks[label] = {
            "true_positives_020": fixed.true_positives,
            "false_positives_020": fixed.false_positives,
            "correct_class_hits_020": sum(fixed.per_class_hits.values()),
            "agnostic_recall_020": fixed.agnostic_recall,
            "fp_per_image_020": fixed.fp_per_image,
            "selected_conf": selected_conf,
            "exact_class_map50_95_reference": ref["exact_class_ap"]["map50_95"],
            "per_model_bootstrap_reproduced": True,
            "operating_points_reproduced": True,
        }
    return checks


# --------------------------------------------------------------------------------- evaluate


def evaluate(root: Path = REPO_ROOT, bundle: Path | None = None, with_map: bool = True) -> dict:
    bundle = (bundle or root / BUNDLE).resolve(strict=True)
    a3, pilot, names, pins = load(root, bundle)
    if [f.group_id for f in a3] != [f.group_id for f in pilot]:
        raise RuntimeError("frame alignment differs")
    reproduction = reproduce(a3, pilot, root)
    samples = resample_indices(a3, ROUNDS, SEED)
    focus = {key: names.index(key) for key in FOCUS_KEYS}
    a3_fixed, pilot_fixed = frame_stats(a3, FIXED_CONF), frame_stats(pilot, FIXED_CONF)
    result: dict[str, Any] = {
        "package": PACKAGE,
        "split": "val",
        "frames": FRAMES,
        "gt_boxes": GT_BOXES,
        "groups": GROUPS,
        "bootstrap": {
            "rounds": ROUNDS,
            "seed": SEED,
            "unit": "intact D-02 validation capture group (9), resampled with replacement",
            "paired": "both models scored on the same resampled frames in every round",
            "interval": "95% percentile (numpy linear), difference = A3 minus pilot",
        },
        "input_sha256": pins,
        "reproduction_check": reproduction,
        "fixed_conf_020": paired_block(a3_fixed, pilot_fixed, samples, focus),
        "validation_selected_recall_085": {
            "label": "VALIDATION_SELECTED_DIAGNOSTIC_ONLY",
            "a3_conf": A3_SELECTED_CONF,
            "pilot_conf": PILOT_SELECTED_CONF,
            **paired_block(
                frame_stats(a3, A3_SELECTED_CONF), frame_stats(pilot, PILOT_SELECTED_CONF), samples
            ),
        },
        "per_group_point_difference_fixed_020": per_group(a3_fixed, pilot_fixed),
        "exact_class_map50_95": map_block(a3, pilot, samples) if with_map else None,
        "inference_run": False,
        "training_run": False,
        "thresholds_changed": False,
        "sealed_test_accessed": False,
        "claim_scope": (
            "single-seed validation description; not a causal test of cos_lr "
            "(epochs 40 vs 100 and LR schedule both differ); not a sealed-test result"
        ),
    }
    if result["exact_class_map50_95"] is not None:
        for label, key in (("a3", "a3"), ("pilot", "pilot")):
            ref = reproduction[label]["exact_class_map50_95_reference"]
            if abs(result["exact_class_map50_95"][key] - ref) > 1e-12:
                raise RuntimeError(f"{label} exact-class mAP50-95 does not reproduce")
    return result


def canonical(payload: dict) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=PACKAGE)
    parser.add_argument("command", choices=("write", "verify"))
    parser.add_argument("--bundle", type=Path, default=None)
    args = parser.parse_args(argv)
    text = canonical(evaluate(REPO_ROOT, args.bundle))
    target = REPO_ROOT / OUT
    if args.command == "write":
        with target.open("x", encoding="utf-8") as sink:
            sink.write(text)
        print(f"wrote {OUT} sha256={hashlib.sha256(text.encode()).hexdigest()}")
        return 0
    stored = target.read_text(encoding="utf-8")
    if stored != text:
        print(f"VERIFY FAIL: {OUT} differs from recomputation", file=sys.stderr)
        return 1
    print(f"VERIFY PASS: {OUT} sha256={sha256_file(target)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
