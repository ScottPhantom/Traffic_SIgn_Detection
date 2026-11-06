"""Validation-R3 confidence diagnostics from QA-pinned predictions; no model inference.

The pilot curve is read from the QA-passed NMS R1 JSON. Other curves reuse the
project's D-05 operating-point scorer on frozen prediction rows. This package
does not lock a threshold or access the sealed test.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

from m1 import a3_pilot_paired_ci_r1 as a3ci
from m1.metrics import Frame, operating_point

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "tmp/yolo11n_n1_extract_r2"
GRID = tuple(round(i / 20, 2) for i in range(1, 21))
OUTPUT = ROOT / "docs/review/generated"
FIGURES = ROOT / "docs/review/figures"
NMS_JSON = "docs/review/generated/d1_nms_sweep_r1.json"
NMS_SHA = "6be704d21edacd92aeb142f9fc4a5ffb6988686f24ebda9321224634f5460057"
NMS_QA = "docs/review/d1_nms_sweep_r1_result_independent_qa_record.md"
NMS_QA_SHA = "75808758357b099adb5b43968dcaba594196875535689fa76256406625ace320"
SCORER_SHA = "d24570f85795e3bc5a2e754ace80a8081c510ff4a78833f2ab5316953a017f9f"
A3CI_SHA = "7edb3824a0f69f385fcb07628d4a5720688ee55af5cc4421c7b118165c0bdea4"
FOCUS = {"7": 7, "32": 33, "41": 42}
FUSION_DIR = (
    "results/experiments/"
    "D1_yolo11s_wp33_afa03d4b_20261018_20261021T111233_pilot_100e_seed_20261018_r2/"
    "classifier_fusion_r1"
)


@dataclass(frozen=True)
class Spec:
    name: str
    csv_path: str | None
    csv_sha: str | None
    result_path: str
    result_sha: str
    qa_path: str
    qa_sha: str
    reference: tuple[str, ...]
    cls_field: str = "class_id"
    conf_field: str = "confidence"


SPECS = (
    Spec(
        "yolo11s_54_a3",
        "results/experiments/d1_a3_seed_20261018_r2/evaluation_common_r1/a3_predictions.csv",
        "e6a25b017bc94a3cf75220fcce1acdfd7bfacb088ca375143e3f0e5046b99ada",
        "results/experiments/d1_a3_seed_20261018_r2/evaluation_common_r1/comparison_a3_r1.json",
        "98b8947e379e2dbf88066884ee4540bc669f8402d459b1891b071b53ee2c2c73",
        "docs/review/d1_a3_r2_common_validation_independent_qa_record.md",
        "624e3994f92dc0e00274674f46eddf54471a8f8832a22ecce318b78ccd916058",
        ("a3_common_method",),
    ),
    Spec(
        "yolo11s_54_a2",
        "results/experiments/d1_a2_seed_20261018_r1/evaluation_common_r1/a2_predictions.csv",
        "c45dcf1dd5446b7e5afe3458afcd43f75b8b7b5afc5434d244d80a0e3e1dd7f1",
        "results/experiments/d1_a2_seed_20261018_r1/evaluation_common_r1/comparison_a2_r1.json",
        "d7872b872b4db01ec27662a323ad9edcf416cd318345a45a68038ebe2bef641b",
        "docs/review/d1_a2_r1_common_validation_result_independent_qa_record.md",
        "d29173787d6223a053745d127d9aae93be2062b0e41ef349b19e5a39a80666e6",
        ("a2_common_method",),
    ),
    Spec(
        "pilot_classifier_fusion",
        f"{FUSION_DIR}/fusion_r1_predictions_conf0001.csv",
        "916ad347abab19de1c0256966e78be640bea4fabc959a2213628ed8167b5084e",
        f"{FUSION_DIR}/fusion_r1_eval.json",
        "e425f38f2c895449519263873cad64cda19571045ac8023ce274f17d000d2edf",
        "docs/review/d1_yolo54_classifier_fusion_r1_result_independent_qa_record.md",
        "8ee15824f81991d9ef40e5eb53ddbf33480bfc138edeffee18898a75b3e11e23",
        ("arm_b",),
        "fused_id",
        "conf",
    ),
    Spec(
        "s1_compact_b0",
        "results/experiments/cascade_b0_seed_20261018_r1/evaluation/comparison_b0_r1.csv",
        "1aef01a1d8e1532e405c025db43a2683cf1573644fe301fa8aa065ec6fd0c81a",
        "results/experiments/cascade_b0_seed_20261018_r1/evaluation/comparison_b0_r1.json",
        "ac1834204b3f38a7838913278241c2c37b72ffb75d01c9252eb638e56151841a",
        "docs/review/cascade_b0_r1_result_independent_qa_record.md",
        "d66e157bb839f9c7e395249fa3e8d17adb8fcb772d1c8a4b7b68671cb1dd720b",
        (),
    ),
    Spec(
        "s1_compact_r2",
        "results/experiments/cascade_classifier_improvement_r1/combined_e2e_eval_r2/s1_predictions.csv",
        "b2441a45630292ced2a1140cf04a9768d5db639e627decac12c28b3c48be3a61",
        "results/experiments/cascade_classifier_improvement_r1/combined_e2e_eval_r2/comparison.json",
        "2dbc63f3ba17b4defe8b5d948e5517e92c526ec81a2f28ca1ed8fa6455c41ae7",
        "docs/review/cascade_classifier_improvement_r2_combined_e2e_result_independent_qa_record.md",
        "3e7aef8227addd1fb183d3c8df174aa1b519751ba5ef9783bfcbde6f67cc46fa",
        ("results", "s1", "exact_class"),
    ),
    Spec(
        "s1_vgg16_54",
        None,
        None,
        "results/experiments/vgg16_54_seed_20261018_r2/evaluation_r4/comparison_vgg16_54_r4.json",
        "e67c54d738e13bf2809f8ec3623bdb2f8c0dfa1f3115428895232e58c382fde7",
        "docs/review/vgg16_54_r4_validation_result_independent_qa_record.md",
        "d15d076d399deb8abd8e17b846ddf27a5347f4af00499af87ada4ac80b7a5b42",
        (),
    ),
    Spec(
        "n1_compact",
        "results/experiments/yolo11n_n1_seed_20261018_r1_r1/evaluation_r1/n1_compact_predictions.csv",
        "d6d41e1d3cd89b557d29ada373d3836322f60ce2c719a291dd3e37b723b56fdd",
        "results/experiments/yolo11n_n1_seed_20261018_r1_r1/evaluation_r1/comparison_n1_r1.json",
        "0447a1bdc2aec56980b63f3fea5340be9a1d455ed9b7872ac503c4d65779a0db",
        "docs/review/yolo11n_n1_r1_validation_independent_qa_record.md",
        "cf23bc5bf58d179105a68f181266fd961dfe66fa9aa9f084e9d50f76ba25fb8c",
        ("n1_plus_compact",),
    ),
    Spec(
        "n1_compact_r2",
        "results/experiments/cascade_classifier_improvement_r1/combined_e2e_eval_r2/n1_predictions.csv",
        "3d2fd4f69b0e71a6fe44dacb44d68302cb93a0b5045da331fb58138ead5d2b9a",
        "results/experiments/cascade_classifier_improvement_r1/combined_e2e_eval_r2/comparison.json",
        "2dbc63f3ba17b4defe8b5d948e5517e92c526ec81a2f28ca1ed8fa6455c41ae7",
        "docs/review/cascade_classifier_improvement_r2_combined_e2e_result_independent_qa_record.md",
        "3e7aef8227addd1fb183d3c8df174aa1b519751ba5ef9783bfcbde6f67cc46fa",
        ("results", "n1", "exact_class"),
    ),
    Spec(
        "n1_vgg16_54",
        "results/experiments/yolo11n_n1_seed_20261018_r1_r1/evaluation_r1/n1_vgg_predictions.csv",
        "4b99a347a1ac7cf431561c3964f06888692dad58e64573d61f259f073b54c010",
        "results/experiments/yolo11n_n1_seed_20261018_r1_r1/evaluation_r1/comparison_n1_r1.json",
        "0447a1bdc2aec56980b63f3fea5340be9a1d455ed9b7872ac503c4d65779a0db",
        "docs/review/yolo11n_n1_r1_validation_independent_qa_record.md",
        "cf23bc5bf58d179105a68f181266fd961dfe66fa9aa9f084e9d50f76ba25fb8c",
        ("n1_plus_vgg16_54",),
    ),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(path: Path, expected: str) -> None:
    if path.is_symlink() or not path.is_file() or sha256(path) != expected:
        raise RuntimeError(f"pinned input differs: {path}")


def qa_passed(path: Path, expected: str, artifact_hashes: tuple[str, ...]) -> None:
    require(path, expected)
    text = path.read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if "Verdict:" in line or "Decision:" in line]
    if not lines or not any("PASS" in line for line in lines):
        raise RuntimeError(f"QA PASS missing: {path}")
    if any(digest not in text for digest in artifact_hashes):
        raise RuntimeError(f"QA record does not bind input: {path}")


def reference(result: dict, path: tuple[str, ...]) -> dict:
    value = result
    for key in path:
        value = value[key]
    return value


def point(frames: list[Frame], conf: float) -> dict:
    p = operating_point(frames, conf)
    correct = sum(p.per_class_hits.values())
    f1 = (
        2 * p.precision * p.agnostic_recall / (p.precision + p.agnostic_recall)
        if p.precision + p.agnostic_recall
        else 0.0
    )
    return {
        "confidence": conf,
        "agnostic_recall": p.agnostic_recall,
        "correct_class_recall": correct / p.ground_truth,
        "precision": p.precision,
        "fp": p.false_positives,
        "fp_per_image": p.fp_per_image,
        "tp": p.true_positives,
        "correct_class_hits": correct,
        "f1_agnostic": f1,
        "focus": {
            key: {
                "yolo_id": cls,
                "support": p.per_class_support.get(cls, 0),
                "hits": p.per_class_hits.get(cls, 0),
                "recall": p.per_class_recall.get(cls, 0.0),
            }
            for key, cls in FOCUS.items()
        },
    }


def pilot_cells() -> tuple[list[dict], dict]:
    qa_passed(ROOT / NMS_QA, NMS_QA_SHA, (NMS_SHA,))
    require(ROOT / NMS_JSON, NMS_SHA)
    result = json.loads((ROOT / NMS_JSON).read_text(encoding="utf-8"))
    if (
        result.get("sealed_test_accessed") is not False
        or result.get("thresholds_locked") is not False
    ):
        raise RuntimeError("pilot diagnostic boundary differs")
    config = result["configurations"]["classaware_0.70"]
    cells = config["cells"]
    if [cell["confidence"] for cell in cells] != list(GRID):
        raise RuntimeError("pilot confidence grid differs")
    fixed = next(cell for cell in cells if cell["confidence"] == 0.20)
    if (fixed["tp"], fixed["fp"], fixed["correct_class_hits"]) != (547, 150, 457):
        raise RuntimeError("pilot step 0 differs")
    return cells, result


def load_model(spec: Spec, base: list[Frame]) -> tuple[list[Frame], float, dict]:
    result_path, qa_path = ROOT / spec.result_path, ROOT / spec.qa_path
    require(result_path, spec.result_sha)
    hashes = (spec.result_sha,) + ((spec.csv_sha,) if spec.csv_sha else ())
    qa_passed(qa_path, spec.qa_sha, hashes)
    result = json.loads(result_path.read_text(encoding="utf-8"))
    seal = (
        result.get("flags", {}).get("sealed_test_accessed")
        if spec.name == "pilot_classifier_fusion"
        else result.get("sealed_test_accessed")
    )
    if seal is not False:
        raise RuntimeError(f"seal flag differs: {spec.name}")
    if spec.csv_path:
        csv_path = ROOT / spec.csv_path
        require(csv_path, spec.csv_sha)
        frames = a3ci.with_predictions(base, csv_path, spec.cls_field, spec.conf_field)
        floor = min(float(score) for frame in frames for score in frame.pred_scores)
    else:
        rows = result["predictions"]
        by_stem: dict[str, list[dict]] = {frame.stem: [] for frame in base}
        dimensions = {frame.stem: (frame.image_width, frame.image_height) for frame in base}
        for row in rows:
            if row["stem"] not in by_stem:
                raise RuntimeError("embedded prediction outside R3")
            box = row["bbox_xyxy"]
            width, height = dimensions[row["stem"]]
            if not (
                isinstance(row["class_id"], int)
                and 0 <= row["class_id"] < 54
                and math.isfinite(row["confidence"])
                and 0 <= row["confidence"] <= 1
                and len(box) == 4
                and all(math.isfinite(value) for value in box)
                and 0 <= box[0] < box[2] <= width
                and 0 <= box[1] < box[3] <= height
            ):
                raise RuntimeError("invalid embedded prediction")
            by_stem[row["stem"]].append(row)
        frames = [
            replace(
                frame,
                pred_boxes=np.asarray(
                    [row["bbox_xyxy"] for row in by_stem[frame.stem]], dtype=float
                ).reshape(-1, 4),
                pred_classes=np.asarray(
                    [row["class_id"] for row in by_stem[frame.stem]], dtype=int
                ),
                pred_scores=np.asarray(
                    [row["confidence"] for row in by_stem[frame.stem]], dtype=float
                ),
            )
            for frame in base
        ]
        floor = min(float(row["confidence"]) for row in rows)
    ref = (
        result["arm_b"]
        if spec.name == "pilot_classifier_fusion"
        else reference(result, spec.reference)["fixed_conf_020"]
    )
    actual = point(frames, 0.20)
    if "per_class_hits" in ref:
        expected_hits = sum(ref["per_class_hits"].values())
    elif "per_class" in ref:
        expected_hits = sum(item["hits"] for item in ref["per_class"].values())
    else:
        raise RuntimeError(f"step 0 class-hit reference missing: {spec.name}")
    if (
        abs(actual["agnostic_recall"] - ref["agnostic_recall"]) > 1e-10
        or actual["fp"] != ref["false_positives"]
        or actual["tp"] != ref.get("true_positives", actual["tp"])
        or actual["correct_class_hits"] != expected_hits
    ):
        raise RuntimeError(f"step 0 differs: {spec.name}")
    if spec.name == "yolo11s_54_a2" and (
        round(actual["agnostic_recall"], 4),
        actual["fp"],
        actual["correct_class_hits"],
    ) != (0.7612, 92, 406):
        raise RuntimeError("A2 step 0 anchor differs")
    return frames, floor, actual


def choose(cells: list[dict]) -> dict:
    eligible = [cell for cell in cells if cell["agnostic_recall"] >= 0.85]
    if eligible:
        selected = min(eligible, key=lambda cell: (cell["fp_per_image"], -cell["confidence"]))
        return {"status": "MEETS_RECALL_0_85", "cell": selected}
    selected = max(cells, key=lambda cell: (cell["agnostic_recall"], cell["confidence"]))
    return {"status": "NO_POINT_MEETS_RECALL_0_85", "cell": selected}


def interpolate(cells: list[dict], target: float) -> dict | None:
    """Linear descriptive interpolation between adjacent confidence-grid points only."""
    for left, right in zip(cells, cells[1:], strict=False):
        x0, x1 = left["fp_per_image"], right["fp_per_image"]
        if x0 == target:
            return {
                "agnostic_recall": left["agnostic_recall"],
                "correct_class_recall": left["correct_class_recall"],
                "between": [left["confidence"], left["confidence"]],
            }
        if x0 >= target >= x1 and x0 != x1:
            ratio = (target - x0) / (x1 - x0)
            return {
                "agnostic_recall": left["agnostic_recall"]
                + ratio * (right["agnostic_recall"] - left["agnostic_recall"]),
                "correct_class_recall": left["correct_class_recall"]
                + ratio * (right["correct_class_recall"] - left["correct_class_recall"]),
                "between": [left["confidence"], right["confidence"]],
            }
    last = cells[-1]
    if last["fp_per_image"] == target:
        return {
            "agnostic_recall": last["agnostic_recall"],
            "correct_class_recall": last["correct_class_recall"],
            "between": [last["confidence"], last["confidence"]],
        }
    return None


def describe(cells: list[dict], ci: dict | None, floor: float, source: dict) -> dict:
    selected = choose(cells)
    f1 = max(cells, key=lambda cell: (cell["f1_agnostic"], cell["confidence"]))
    both = [
        cell["confidence"]
        for cell in cells
        if cell["agnostic_recall"] >= 0.85 and cell["fp_per_image"] <= 0.30
    ]
    return {
        "source": source,
        "observed_score_floor": floor,
        "cells": cells,
        "selected_diagnostic": selected,
        "ci95_at_selected": ci,
        "max_f1_diagnostic": f1["confidence"],
        "both_d05_val_markers": both,
        "interpolated_at_fp_per_image": {
            str(value): interpolate(cells, value) for value in (0.20, 0.25, 0.30)
        },
    }


def grouped_bootstrap(frames: list[Frame], conf: float) -> dict[str, list[float]]:
    """Same D-02 draws as metrics.group_bootstrap, with additive group counts cached."""
    grouped: dict[str, list[Frame]] = {}
    for frame in frames:
        grouped.setdefault(frame.group_id, []).append(frame)
    names = sorted(grouped)
    if len(names) != 9:
        raise RuntimeError("D-02 group count differs")
    points = [operating_point(grouped[name], conf) for name in names]
    gt = np.asarray([p.ground_truth for p in points], dtype=int)
    tp = np.asarray([p.true_positives for p in points], dtype=int)
    fp = np.asarray([p.false_positives for p in points], dtype=int)
    images = np.asarray([p.images for p in points], dtype=int)
    rng = np.random.default_rng(20261018)
    indices = {name: index for index, name in enumerate(names)}
    recalls, fps = [], []
    for _ in range(1000):
        draw = [indices[name] for name in rng.choice(names, size=len(names), replace=True)]
        recalls.append(float(tp[draw].sum() / gt[draw].sum()))
        fps.append(float(fp[draw].sum() / images[draw].sum()))
    return {
        "agnostic_recall": [float(v) for v in np.percentile(recalls, [2.5, 97.5])],
        "fp_per_image": [float(v) for v in np.percentile(fps, [2.5, 97.5])],
    }


def compute() -> dict:
    require(Path(a3ci.__file__), A3CI_SHA)
    require(Path(operating_point.__code__.co_filename), SCORER_SHA)
    a3ci.verify_pins(ROOT, BUNDLE)
    base = a3ci.gt_frames(BUNDLE)
    if (
        len(base) != 376
        or sum(len(f.gt_boxes) for f in base) != 624
        or len({f.group_id for f in base}) != 9
    ):
        raise RuntimeError("R3 roster differs")
    names = a3ci.class_names(BUNDLE)
    if {key: names.index(key) for key in FOCUS} != FOCUS:
        raise RuntimeError("derived-key map differs")
    pilot, _ = pilot_cells()
    pilot_report = json.loads((ROOT / a3ci.A3_JSON).read_text(encoding="utf-8"))
    pilot_ci = pilot_report["pilot_common_method"]["bootstrap_fixed_020"]
    with (BUNDLE / a3ci.PILOT_CSV).open(newline="", encoding="utf-8") as source:
        pilot_floor = min(float(row["conf"]) for row in csv.DictReader(source))
    pilot = [
        dict(
            cell,
            f1_agnostic=(
                2
                * cell["precision"]
                * cell["agnostic_recall"]
                / (cell["precision"] + cell["agnostic_recall"])
                if cell["precision"] + cell["agnostic_recall"]
                else 0.0
            ),
        )
        for cell in pilot
    ]
    models = {
        "yolo11s_54_pilot": describe(
            pilot,
            pilot_ci,
            pilot_floor,
            {"diagnostic_json": NMS_JSON, "sha256": NMS_SHA, "qa": NMS_QA},
        )
    }
    skipped = {}
    for spec in SPECS:
        if not (ROOT / spec.result_path).is_file() or (
            spec.csv_path and not (ROOT / spec.csv_path).is_file()
        ):
            skipped[spec.name] = (
                "QA-pinned prediction/result file missing; no new inference authorized"
            )
            continue
        frames, floor, fixed = load_model(spec, base)
        cells = [point(frames, conf) for conf in GRID if conf >= floor]
        if not cells or next(cell for cell in cells if cell["confidence"] == 0.20) != fixed:
            raise RuntimeError(f"step 0 grid differs: {spec.name}")
        selected = choose(cells)
        ci = grouped_bootstrap(frames, selected["cell"]["confidence"])
        models[spec.name] = describe(
            cells,
            ci,
            floor,
            {
                "prediction": spec.csv_path or spec.result_path + "#predictions",
                "prediction_sha256": spec.csv_sha or spec.result_sha,
                "result": spec.result_path,
                "result_sha256": spec.result_sha,
                "qa": spec.qa_path,
                "qa_sha256": spec.qa_sha,
                "confidence_field": spec.conf_field
                if spec.csv_path
                else "predictions[].confidence",
            },
        )
    return {
        "package": "D1-THRESHOLD-SWEEP-R1",
        "scope": "validation R3; single-seed descriptive diagnostic; no threshold lock",
        "frames": 376,
        "gt_boxes": 624,
        "groups": 9,
        "grid": list(GRID),
        "bundle_manifest_sha256": a3ci.BUNDLE_MANIFEST_SHA256,
        "models": models,
        "skipped": skipped,
        "sealed_test_accessed": False,
        "thresholds_locked": False,
        "training_run": False,
        "model_inference_run": False,
    }


def svg_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")


def model_svg(name: str, item: dict) -> str:
    cells = item["cells"]

    def x(conf: float) -> float:
        return 40 + (conf - 0.05) / 0.95 * 1040

    def y(value: float) -> float:
        return 500 - min(value, 1.2) / 1.2 * 480

    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 520" '
        f'role="img" aria-label="Quét ngưỡng {svg_escape(name)}: recall và báo nhầm trên ảnh">',
        '<rect width="1100" height="520" fill="white"/>',
        '<text x="50" y="48" font-size="24" font-family="sans-serif">'
        f"{svg_escape(name)} · validation R3</text>",
    ]
    for value in (0, 0.30, 0.60, 0.85, 1.2):
        lines.append(
            f'<line x1="40" x2="1080" y1="{y(value):.1f}" y2="{y(value):.1f}" stroke="#cbd5e1"/>'
        )
        lines.append(
            f'<text x="42" y="{min(y(value) + 24, 498):.1f}" font-size="22" '
            f'font-family="sans-serif">{value:g}</text>'
        )
    for value in (0.30, 0.85):
        lines.append(
            f'<line x1="40" x2="1080" y1="{y(value):.1f}" y2="{y(value):.1f}" '
            'stroke="#94a3b8" stroke-dasharray="8 7"/>'
        )
    for key, color in (("agnostic_recall", "#2563eb"), ("fp_per_image", "#7c3aed")):
        pts = " ".join(f"{x(c['confidence']):.1f},{y(c[key]):.1f}" for c in cells)
        lines.append(f'<polyline fill="none" stroke="{color}" stroke-width="5" points="{pts}"/>')
    chosen = item["selected_diagnostic"]["cell"]
    xx = x(chosen["confidence"])
    lines.append(
        f'<line x1="{xx:.1f}" x2="{xx:.1f}" y1="20" y2="500" '
        'stroke="#c2410c" stroke-width="3" stroke-dasharray="9 7"/>'
    )
    for key, color in (("agnostic_recall", "#2563eb"), ("fp_per_image", "#7c3aed")):
        lines.append(f'<circle cx="{xx:.1f}" cy="{y(chosen[key]):.1f}" r="7" fill="{color}"/>')
    lines += [
        '<text x="50" y="80" font-size="22" fill="#2563eb" '
        'font-family="sans-serif">Recall biển</text>',
        '<text x="275" y="80" font-size="22" fill="#7c3aed" font-family="sans-serif">FP/ảnh</text>',
        '<text x="450" y="80" font-size="22" fill="#c2410c" '
        'font-family="sans-serif">Điểm chọn mô tả</text>',
        '<text x="850" y="80" font-size="22" font-family="sans-serif">Confidence →</text>',
        "</svg>",
    ]
    return "\n".join(lines) + "\n"


def tradeoff_svg(models: dict) -> str:
    colors = (
        "#2563eb",
        "#7c3aed",
        "#059669",
        "#dc2626",
        "#0f766e",
        "#a16207",
        "#be185d",
        "#4f46e5",
        "#334155",
        "#ea580c",
    )

    def x(value: float) -> float:
        return 40 + min(value, 1.2) / 1.2 * 1040

    def y(value: float) -> float:
        return 500 - value * 480

    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 520" '
        'role="img" aria-label="Đánh đổi recall và báo nhầm trên ảnh của các pipeline, '
        'validation R3">',
        '<rect width="1100" height="520" fill="white"/>',
        '<text x="50" y="48" font-size="24" font-family="sans-serif">'
        "Recall theo FP/ảnh · validation R3</text>",
    ]
    for value in (0, 0.3, 0.6, 0.9, 1.2):
        lines.append(
            f'<line x1="{x(value):.1f}" x2="{x(value):.1f}" y1="20" y2="500" stroke="#cbd5e1"/>'
        )
    for value in (0, 0.3, 0.6, 0.85, 1):
        lines.append(
            f'<line x1="40" x2="1080" y1="{y(value):.1f}" y2="{y(value):.1f}" stroke="#cbd5e1"/>'
        )
    lines.append(
        f'<line x1="{x(0.3):.1f}" x2="{x(0.3):.1f}" y1="20" y2="500" '
        'stroke="#94a3b8" stroke-dasharray="8 7"/>'
    )
    lines.append(
        f'<line x1="40" x2="1080" y1="{y(0.85):.1f}" y2="{y(0.85):.1f}" '
        'stroke="#94a3b8" stroke-dasharray="8 7"/>'
    )
    for index, (name, item) in enumerate(models.items()):
        color = colors[index % len(colors)]
        pts = " ".join(
            f"{x(c['fp_per_image']):.1f},{y(c['agnostic_recall']):.1f}" for c in item["cells"]
        )
        lines.append(f'<polyline fill="none" stroke="{color}" stroke-width="3" points="{pts}"/>')
        lines.append(
            f'<text x="740" y="{110 + index * 38}" font-size="22" '
            f'fill="{color}" font-family="sans-serif">{svg_escape(name)}</text>'
        )
    lines += [
        '<text x="50" y="485" font-size="22" font-family="sans-serif">FP/ảnh →</text>',
        '<text x="430" y="485" font-size="22" font-family="sans-serif">Recall ↑</text>',
        "</svg>",
    ]
    return "\n".join(lines) + "\n"


def artifacts(data: dict) -> dict[Path, bytes]:
    output = {
        OUTPUT / "d1_threshold_sweep_r1.json": (
            json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n"
        ).encode()
    }
    table = io.StringIO()
    fields = (
        "model",
        "confidence",
        "agnostic_recall",
        "correct_class_recall",
        "precision",
        "fp",
        "fp_per_image",
        "tp",
        "correct_class_hits",
        "f1_agnostic",
        "focus_7",
        "focus_32",
        "focus_41",
    )
    writer = csv.DictWriter(table, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for name, item in data["models"].items():
        for cell in item["cells"]:
            writer.writerow(
                {
                    "model": name,
                    **{key: cell[key] for key in fields[1:-3]},
                    **{f"focus_{key}": cell["focus"][key]["recall"] for key in FOCUS},
                }
            )
    output[OUTPUT / "d1_threshold_sweep_r1.csv"] = table.getvalue().encode()
    for name, item in data["models"].items():
        output[FIGURES / f"d1_threshold_sweep_r1_{name}.svg"] = model_svg(name, item).encode()
    output[FIGURES / "d1_threshold_sweep_r1_tradeoff.svg"] = tradeoff_svg(data["models"]).encode()
    if any(len(payload) > 50_000 for path, payload in output.items() if path.suffix == ".svg"):
        raise RuntimeError("SVG exceeds 50 KB")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("write", "verify"))
    args = parser.parse_args()
    content = artifacts(compute())
    for path, payload in content.items():
        if args.mode == "write":
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as handle:
                handle.write(payload)
        elif path.read_bytes() != payload:
            raise RuntimeError(f"reproduction differs: {path}")
    print(f"{args.mode.upper()} PASS: {len(content)} artifacts, sealed_test_accessed=false")


if __name__ == "__main__":
    main()
