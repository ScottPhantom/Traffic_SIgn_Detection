"""Validation-only NMS IoU × confidence diagnostic for the pinned D1 pilot.

Run from ``detector/`` with ``PYTHONPATH=. uv run --no-sync python -m m1.nms_sweep_r1``.
This module never trains, opens sealed-test data, or changes application policy.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from m1.metrics import Frame, operating_point

REPO = Path(__file__).resolve().parents[2]
COLAB = REPO / "detector/colab"
WEIGHT = REPO / (
    "results/experiments/"
    "D1_yolo11s_wp33_afa03d4b_20261018_20261021T111233_pilot_100e_seed_20261018_r2/"
    "weights/best.pt"
)
BUNDLE = REPO / "tmp/yolo11n_n1_extract_r2"
OUT = REPO / "results/experiments/d1_nms_sweep_r1"
JSON_OUT = REPO / "docs/review/generated/d1_nms_sweep_r1.json"

PINS = {
    "pilot_weight": (WEIGHT, "5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633"),
    "bundle_manifest": (
        BUNDLE / "manifest.json",
        "8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da",
    ),
    "pilot_csv": (
        BUNDLE / "data/yolo54_predictions_val.csv",
        "87884c536e16ac890c11114c85c7c12731571df15d244071a38e3d1db271c893",
    ),
    "common_evaluator": (
        COLAB / "evaluate_d1_a3_r2_common_r1.py",
        "5d8e49bfafc1343ff1cc3fd4064410914ab6e75c23a1108240b09c36dc3ecca6",
    ),
    "common_scorer": (
        COLAB / "evaluate_cascade_b0_r1.py",
        "8bedb4c199f39eafbef240b614511ef8c40a5c7c4794772b0c6691a0df416b42",
    ),
    "metrics": (
        REPO / "detector/m1/metrics.py",
        "d24570f85795e3bc5a2e754ace80a8081c510ff4a78833f2ab5316953a017f9f",
    ),
    "paired_ci": (
        REPO / "detector/m1/a3_pilot_paired_ci_r1.py",
        "7edb3824a0f69f385fcb07628d4a5720688ee55af5cc4421c7b118165c0bdea4",
    ),
    "package_verifier": (
        COLAB / "run_yolo11n_n1_r1.py",
        "b60e829104f644248912acddf4397fe07ff647e709feefef6dd0443c393e5753",
    ),
    "d05_decision": (
        REPO / "docs/review/d05_owner_decision_record.md",
        "c81f37ed0236c019644914445776632dbe0fbcef0f7d5b964fb5c6d635555702",
    ),
    "classes": (
        BUNDLE / "data/classes.csv",
        "7cda296a95bd8512a1bb2e85109ce9a1574fb882e692b11d4d0ee6a1cb58d242",
    ),
    "groups": (
        BUNDLE / "data/val_groups.json",
        "fdb2ef8ff2cc684970b6330747d7746ccfe6dfd77d60903d10233de66697d682",
    ),
}
CONFIGS = [(v, False) for v in (0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80)] + [
    (v, True) for v in (0.80, 0.85, 0.90)
]
GRID = tuple(round(n / 100, 2) for n in range(5, 101, 5))
FOCUS = {"7": 7, "32": 33, "41": 42}
BASE = (0.70, False)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_pins() -> dict[str, str]:
    for name, (path, expected) in PINS.items():
        if path.is_symlink() or not path.is_file() or sha256(path) != expected:
            raise RuntimeError(f"pinned input differs: {name}")
    sys.path.insert(0, str(COLAB))
    from run_yolo11n_n1_r1 import verify_package

    verify_package(BUNDLE, PINS["bundle_manifest"][1])
    import evaluate_cascade_b0_r1 as common

    common.verify_evaluation_scope(BUNDLE, PINS["pilot_csv"][0], PINS["pilot_csv"][1])
    return {name: expected for name, (_, expected) in PINS.items()}


def key(config: tuple[float, bool]) -> str:
    iou, agnostic = config
    return f"{'agnostic' if agnostic else 'classaware'}_{iou:.2f}"


def infer(detector: object, iou: float, agnostic: bool, device: str) -> list[Frame]:
    """Same image/label/box path as the pinned common evaluator; vary NMS only."""
    groups = json.loads((BUNDLE / "data/val_groups.json").read_text(encoding="utf-8"))
    frames: list[Frame] = []
    for path in sorted((BUNDLE / "data/images/val").iterdir()):
        with Image.open(path) as source:
            image = source.convert("RGB")
        gt_classes, gt_boxes = [], []
        for row in (BUNDLE / f"data/labels54/val/{path.stem}.txt").read_text().splitlines():
            cls, cx, cy, width, height = map(float, row.split())
            gt_classes.append(int(cls))
            gt_boxes.append(
                [
                    (cx - width / 2) * image.width,
                    (cy - height / 2) * image.height,
                    (cx + width / 2) * image.width,
                    (cy + height / 2) * image.height,
                ]
            )
        result = detector.predict(
            image,
            conf=0.001,
            iou=iou,
            agnostic_nms=agnostic,
            imgsz=1280,
            device=device,
            verbose=False,
        )[0]
        boxes = result.boxes.xyxy.cpu().numpy()
        boxes[:, [0, 2]] = boxes[:, [0, 2]].clip(0, image.width)
        boxes[:, [1, 3]] = boxes[:, [1, 3]].clip(0, image.height)
        scores = result.boxes.conf.cpu().numpy()
        classes = result.boxes.cls.cpu().numpy().astype(int)
        if (
            not np.isfinite(boxes).all()
            or not np.isfinite(scores).all()
            or not np.all((0 <= scores) & (scores <= 1))
            or not np.all((0 <= classes) & (classes < 54))
            or not all(math.isfinite(float(v)) for row in gt_boxes for v in row)
        ):
            raise RuntimeError("invalid prediction or ground truth")
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
    if (
        len(frames) != 376
        or sum(len(f.gt_boxes) for f in frames) != 624
        or len({f.group_id for f in frames}) != 9
    ):
        raise RuntimeError("validation roster differs")
    return frames


def write_predictions(path: Path, frames: list[Frame]) -> str:
    with path.open("x", newline="", encoding="utf-8") as sink:
        writer = csv.writer(sink)
        writer.writerow(["stem", "class_id", "confidence", "x1", "y1", "x2", "y2"])
        for frame in frames:
            for box, cls, score in zip(
                frame.pred_boxes, frame.pred_classes, frame.pred_scores, strict=True
            ):
                writer.writerow([frame.stem, int(cls), float(score), *map(float, box)])
    return sha256(path)


def point(frames: list[Frame], conf: float) -> dict:
    op = operating_point(frames, conf)
    exact = sum(op.per_class_hits.values())
    return {
        "confidence": conf,
        "agnostic_recall": op.agnostic_recall,
        "correct_class_recall": exact / op.ground_truth,
        "precision": op.precision,
        "tp": op.true_positives,
        "fp": op.false_positives,
        "fp_per_image": op.fp_per_image,
        "correct_class_hits": exact,
        "focus": {
            derived: {
                "yolo_id": cls,
                "support": op.per_class_support.get(cls, 0),
                "hits": op.per_class_hits.get(cls, 0),
                "recall": op.per_class_recall.get(cls),
            }
            for derived, cls in FOCUS.items()
        },
    }


def select(cells: list[dict]) -> dict | None:
    eligible = [p for p in cells if p["agnostic_recall"] >= 0.85]
    return min(eligible, key=lambda p: (p["fp_per_image"], -p["confidence"])) if eligible else None


def choose(settings: dict[str, dict]) -> str | None:
    valid = [(name, item) for name, item in settings.items() if item["selected"] is not None]
    if not valid:
        return None
    return min(
        valid,
        key=lambda pair: (
            pair[1]["selected"]["fp_per_image"],
            -pair[1]["ap"]["map50_95"],
            abs(pair[1]["iou"] - 0.70),
            pair[1]["agnostic_nms"],
            pair[1]["iou"],
        ),
    )[0]


def baseline_gate(frames: list[Frame], reference: list[Frame], common: object) -> dict:
    new = point(frames, 0.20)
    old = point(reference, 0.20)
    ap = common.average_precision(frames)
    ref_ap = common.average_precision(reference)
    required = new["tp"] == old["tp"] == 547 and new["fp"] == old["fp"] == 150
    required &= new["correct_class_hits"] == old["correct_class_hits"] == 457
    required &= abs(ap["map50"] - 0.8521) <= 1e-4
    required &= abs(ap["map50_95"] - 0.6089) <= 1e-4
    required &= abs(ap["map50"] - ref_ap["map50"]) <= 1e-4
    required &= abs(ap["map50_95"] - ref_ap["map50_95"]) <= 1e-4
    evidence = {
        "passed": bool(required),
        "inferred_conf020": new,
        "pinned_csv_conf020": old,
        "inferred_ap": ap,
        "pinned_csv_ap": ref_ap,
    }
    if not required:
        raise RuntimeError(
            "baseline equivalence failed: " + json.dumps(evidence, ensure_ascii=False)
        )
    return evidence


def score_frames(frames: list[Frame], common: object) -> dict:
    cells = [point(frames, conf) for conf in GRID]
    return {"ap": common.average_precision(frames), "cells": cells, "selected": select(cells)}


def leave_one_group_out(all_frames: dict[str, list[Frame]], common: object) -> list[dict]:
    names = sorted({f.group_id for f in next(iter(all_frames.values()))})
    folds = []
    for held_out in names:
        train: dict[str, dict] = {}
        for name, frames in all_frames.items():
            fit = [f for f in frames if f.group_id != held_out]
            config = next(c for c in CONFIGS if key(c) == name)
            train[name] = {**score_frames(fit, common), "iou": config[0], "agnostic_nms": config[1]}
        winner = choose(train)
        if winner is None:
            folds.append({"held_out_group": held_out, "selection": None})
            continue
        conf = train[winner]["selected"]["confidence"]
        test = [f for f in all_frames[winner] if f.group_id == held_out]
        folds.append(
            {
                "held_out_group": held_out,
                "selection": winner,
                "confidence": conf,
                "held_out": point(test, conf),
            }
        )
    return folds


def paired_ci(
    candidate: list[Frame],
    baseline: list[Frame],
    candidate_conf: float,
    baseline_conf: float,
    common: object,
) -> dict:
    from m1 import a3_pilot_paired_ci_r1 as ci

    samples = ci.resample_indices(baseline, 1000, 20261018)
    candidate_stats = ci.frame_stats(candidate, candidate_conf)
    baseline_stats = ci.frame_stats(baseline, baseline_conf)
    fp_diffs = [
        float(
            ci.summarize(candidate_stats, indices)["fp_per_image"]
            - ci.summarize(baseline_stats, indices)["fp_per_image"]
        )
        for indices in samples
    ]
    candidate_correct = ci._correct_matrices(candidate)
    baseline_correct = ci._correct_matrices(baseline)
    map_diffs = [
        ci._map50_95(candidate, candidate_correct, indices)
        - ci._map50_95(baseline, baseline_correct, indices)
        for indices in samples
    ]
    full_candidate = common.average_precision(candidate)["map50_95"]
    full_baseline = common.average_precision(baseline)["map50_95"]
    return {
        "rounds": 1000,
        "seed": 20261018,
        "unit": "D-02 group",
        "paired": True,
        "fp_per_image_difference": point(candidate, candidate_conf)["fp_per_image"]
        - point(baseline, baseline_conf)["fp_per_image"],
        "fp_per_image_ci95": ci.ci95(fp_diffs),
        "map50_95_difference": full_candidate - full_baseline,
        "map50_95_ci95": ci.ci95(map_diffs),
    }


def adjacent_votes(folds: list[dict], winner: str) -> int:
    config = next(c for c in CONFIGS if key(c) == winner)
    same_mode = [c[0] for c in CONFIGS if c[1] == config[1]]
    index = same_mode.index(config[0])
    neighbors = same_mode[max(index - 1, 0) : index + 2]
    return sum(fold["selection"] in {key((v, config[1])) for v in neighbors} for fold in folds)


def run(device: str) -> dict:
    pins = check_pins()
    import evaluate_cascade_b0_r1 as common
    from ultralytics import YOLO, settings
    from ultralytics.utils import checks

    checks.AUTOINSTALL = checks.ONLINE = False
    settings.update({"sync": False, "wandb": False, "mlflow": False, "clearml": False})
    detector = YOLO(str(WEIGHT))
    if len(detector.names) != 54:
        raise RuntimeError("pilot checkpoint is not 54-class")
    baseline = infer(detector, *BASE, device)
    reference = common.load_pinned_baseline(baseline, PINS["pilot_csv"][0])
    gate = baseline_gate(baseline, reference, common)
    OUT.mkdir(mode=0o700, parents=True, exist_ok=False)
    csv_hashes = {key(BASE): write_predictions(OUT / f"predictions_{key(BASE)}.csv", baseline)}
    all_frames = {key(BASE): baseline}
    settings_out = {
        key(BASE): {"iou": BASE[0], "agnostic_nms": BASE[1], **score_frames(baseline, common)}
    }
    print("Baseline 0.70 PASS; beginning remaining ten configurations", flush=True)
    for config in CONFIGS:
        if config == BASE:
            continue
        name = key(config)
        frames = infer(detector, *config, device)
        csv_hashes[name] = write_predictions(OUT / f"predictions_{name}.csv", frames)
        all_frames[name] = frames
        settings_out[name] = {
            "iou": config[0],
            "agnostic_nms": config[1],
            **score_frames(frames, common),
        }
        print(f"{name} complete", flush=True)
    winner = choose(settings_out)
    base_selected = settings_out[key(BASE)]["selected"]
    folds = leave_one_group_out(all_frames, common)
    ci = None
    decision = "KEEP_0_70"
    if winner and winner != key(BASE) and base_selected is not None:
        ci = paired_ci(
            all_frames[winner],
            baseline,
            settings_out[winner]["selected"]["confidence"],
            base_selected["confidence"],
            common,
        )
        votes = adjacent_votes(folds, winner)
        if ci["fp_per_image_ci95"][1] < 0 and ci["map50_95_ci95"][1] >= 0 and votes >= 7:
            decision = f"CANDIDATE_{winner.upper()}"
    else:
        votes = adjacent_votes(folds, winner) if winner else 0
    base_hits = base_selected["correct_class_hits"] if base_selected else None
    variants = {
        name: {
            "selected_correct_class_hits": setting["selected"]["correct_class_hits"]
            if setting["selected"]
            else None,
            "correct_class_hits_delta_vs_0_70": setting["selected"]["correct_class_hits"]
            - base_hits
            if setting["selected"] and base_hits is not None
            else None,
        }
        for name, setting in settings_out.items()
        if setting["agnostic_nms"]
    }
    result = {
        "package": "D1-NMS-SWEEP-R1",
        "scope": "validation R3 only",
        "device": device,
        "images": 376,
        "gt_boxes": 624,
        "groups": 9,
        "configuration_count": len(CONFIGS),
        "cell_count": sum(len(s["cells"]) for s in settings_out.values()),
        "input_sha256": pins,
        "prediction_csv_sha256": csv_hashes,
        "baseline_equivalence": gate,
        "configurations": settings_out,
        "selected_configuration": winner,
        "paired_ci": ci,
        "leave_one_group_out": folds,
        "adjacent_votes_for_selected": votes,
        "agnostic_nms_variants": variants,
        "decision": decision,
        "thresholds_locked": False,
        "sealed_test_accessed": False,
    }
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    with JSON_OUT.open("x", encoding="utf-8") as sink:
        json.dump(result, sink, indent=2, ensure_ascii=False, allow_nan=False)
        sink.write("\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=("mps", "cpu"), default="mps")
    args = parser.parse_args()
    result = run(args.device)
    print(
        json.dumps({k: result[k] for k in ("decision", "selected_configuration", "cell_count")}),
        flush=True,
    )


if __name__ == "__main__":
    main()
