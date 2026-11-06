"""Paired A2 − pilot group-bootstrap CIs on the pinned common validation set (D1-A2-PILOT-CI-R1).

Append-only successor of ``m1.a3_pilot_paired_ci_r1`` (SHA-256 ``7edb3824…``), whose loaders,
per-frame statistics, group resampler and paired block are reused by import. Validation-only and
prediction-CSV-only: no model is loaded and no inference, training, threshold change or
sealed-test access happens here. Both models are scored on the same resampled frames in every
round (1,000 rounds, seed 20261018); the resampling unit is the intact D-02 capture group (9).

Inputs:

* the corrected train/val-only bundle (manifest ``8e6ffe77…``) and its pinned pilot CSV, plus the
  QA-passed A3 anchors, all verified by the predecessor's own ``verify_pins``;
* the A2 prediction CSV and result JSON written by
  ``detector/colab/evaluate_d1_a2_r1_common_r1.py``. Their hashes are unknown until the A2 run is
  scored, so they are required CLI inputs.

The A2 JSON's pilot side must equal the QA-passed A3 JSON's pilot side exactly. The point estimates
(TP/FP/per-class hits at 0.20 and at the validation-selected point, per-model group-bootstrap CIs,
exact-class mAP50 and mAP50-95) are then reproduced from the CSVs; any mismatch aborts before a CI
is computed.

R3 §5 A2 criteria are read at conf 0.20 on derived keys 7/32/41 (yolo_id 7/33/42; the mapping is
taken from the bundle class map and checked against ``a2_repeat_list_r1.EXPECTED_YOLO_IDS``).
"Overall recall" is the D-05 class-agnostic detection recall (the pilot's 0.8766 in R3 §5).

Usage (from ``detector/``)::

    uv run python -m m1.a2_pilot_paired_ci_r1 write \\
        --a2-csv-sha256 <sha> --a2-json-sha256 <sha>   # create the canonical JSON (no overwrite)
    uv run python -m m1.a2_pilot_paired_ci_r1 verify \\
        --a2-csv-sha256 <sha> --a2-json-sha256 <sha>   # recompute and byte-compare
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np

from m1 import a2_repeat_list_r1 as a2list
from m1 import a3_pilot_paired_ci_r1 as a3ci
from m1 import yolo54_improvement_r3 as r3
from m1.metrics import Frame, group_bootstrap, operating_point, select_threshold

PACKAGE = "D1-A2-PILOT-PAIRED-CI-R1"
EXPERIMENT = "D1-A2-R1"
REPO_ROOT = Path(__file__).resolve().parents[2]

PREDECESSOR = Path("detector/m1/a3_pilot_paired_ci_r1.py")
PREDECESSOR_SHA256 = "7edb3824a0f69f385fcb07628d4a5720688ee55af5cc4421c7b118165c0bdea4"
EVALUATOR = Path("detector/colab/evaluate_d1_a2_r1_common_r1.py")
EVALUATOR_SHA256 = "c08f5de603037aa3289dfc91d44bb2d67b3a29f7e94eba5f2967815fb0c08317"
EVALUATOR_PACKAGE = "D1-A2-R1-COMMON-VALIDATION-R1"
A2_DIR = Path("results/experiments/d1_a2_seed_20261018_r1/evaluation_common_r1")
A2_CSV_NAME, A2_JSON_NAME = "a2_predictions.csv", "comparison_a2_r1.json"
OUT = Path("docs/review/generated/d1_a2_pilot_paired_ci_r1.json")

# Shared with the predecessor (same validation set, same bootstrap).
BUNDLE, PILOT_CSV = a3ci.BUNDLE, a3ci.PILOT_CSV
BUNDLE_MANIFEST_SHA256 = a3ci.BUNDLE_MANIFEST_SHA256
FRAMES, GT_BOXES, GROUPS = a3ci.FRAMES, a3ci.GT_BOXES, a3ci.GROUPS
FIXED_CONF, SELECTION_GRID = a3ci.FIXED_CONF, a3ci.SELECTION_GRID
ROUNDS, SEED = a3ci.ROUNDS, a3ci.SEED
METRICS = a3ci.METRICS
PILOT_SELECTED_CONF = a3ci.PILOT_SELECTED_CONF

FOCUS_KEYS = r3.FOCUS_KEYS  # derived keys 7/32/41/46 (not yolo_ids)
CRITERIA_KEYS = r3.A2_REPEAT_KEYS  # derived keys 7/32/41
EXPECTED_YOLO_IDS = a2list.EXPECTED_YOLO_IDS  # {"7": 7, "32": 33, "41": 42}
CLASS_RECALL_GAIN, FP_INCREASE_MAX, AGNOSTIC_RECALL_MIN = 0.05, 0.03, 0.85
if not set(CRITERIA_KEYS) <= set(FOCUS_KEYS) or set(CRITERIA_KEYS) != set(EXPECTED_YOLO_IDS):
    raise RuntimeError("A2 criteria keys differ from the R3 focus keys / A2 class map")

_RELABEL = {
    "a3": "a2",
    "difference_a3_minus_pilot": "difference_a2_minus_pilot",
    "a3_marginal_ci95": "a2_marginal_ci95",
}


# ------------------------------------------------------------------------------------ pins


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def verify_a2_pins(
    root: Path, a2_dir: Path, csv_sha256: str, json_sha256: str, a3_json: dict[str, Any]
) -> dict[str, str]:
    """A2-side pins: CLI hashes, the A2 evaluator source, and the result JSON binding."""
    if not _is_sha256(csv_sha256) or not _is_sha256(json_sha256):
        raise RuntimeError("A2 CSV/JSON SHA-256 must be 64 lowercase hex digits")
    a3ci._require(root / a2_dir / A2_CSV_NAME, csv_sha256, "A2 prediction CSV")
    a3ci._require(root / a2_dir / A2_JSON_NAME, json_sha256, "A2 result JSON")
    a3ci._require(root / EVALUATOR, EVALUATOR_SHA256, "A2 common evaluator")
    a3ci._require(root / PREDECESSOR, PREDECESSOR_SHA256, "A3 paired-CI predecessor")
    result = json.loads((root / a2_dir / A2_JSON_NAME).read_text(encoding="utf-8"))
    if result.get("sealed_test_accessed") is not False:
        raise RuntimeError("A2 result JSON does not record sealed_test_accessed=false")
    if (
        result.get("package") != EVALUATOR_PACKAGE
        or result.get("experiment") != EXPERIMENT
        or result.get("split") != "val"
        or result.get("frames") != FRAMES
        or result.get("gt_boxes") != GT_BOXES
        or result.get("prediction_csv_sha256") != csv_sha256
        or result.get("bundle_manifest_sha256") != BUNDLE_MANIFEST_SHA256
    ):
        raise RuntimeError("A2 result JSON binding differs")
    if result.get("pilot_common_method") != a3_json.get("pilot_common_method"):
        raise RuntimeError("A2 result JSON pilot side differs from the QA-passed common anchor")
    return {
        "a2_prediction_csv": csv_sha256,
        "a2_result_json": json_sha256,
        "a2_common_evaluator": EVALUATOR_SHA256,
        "a2_result_archive": str(result.get("a2_result_archive_sha256")),
        "a2_best_weight": str(result.get("a2_best_weight_sha256")),
        "a3_paired_ci_predecessor": PREDECESSOR_SHA256,
    }


def verify_pins(
    root: Path, bundle: Path, a2_dir: Path, csv_sha256: str, json_sha256: str
) -> dict[str, str]:
    base = a3ci.verify_pins(root, bundle)  # bundle, pilot CSV, A3 anchors, A3 evaluator, report
    a3_json = json.loads((root / a3ci.A3_JSON).read_text(encoding="utf-8"))
    a2 = verify_a2_pins(root, a2_dir, csv_sha256, json_sha256, a3_json)
    return {**base, **a2}


# ------------------------------------------------------------------------------------ load


def focus_ids(names: Sequence[str]) -> dict[str, int]:
    """Derived key -> yolo_id through the bundle class map; never the raw key as an id."""
    ids = {key: list(names).index(key) for key in FOCUS_KEYS}
    if any(ids[key] != EXPECTED_YOLO_IDS[key] for key in CRITERIA_KEYS):
        raise RuntimeError(f"derived-key/yolo_id mapping differs: {ids}")
    return ids


def load(
    root: Path, bundle: Path, a2_dir: Path, csv_sha256: str, json_sha256: str
) -> tuple[list[Frame], list[Frame], list[str], dict[str, str]]:
    pins = verify_pins(root, bundle, a2_dir, csv_sha256, json_sha256)
    base = a3ci.gt_frames(bundle)
    a2 = a3ci.with_predictions(base, root / a2_dir / A2_CSV_NAME, "class_id", "confidence")
    pilot = a3ci.with_predictions(base, bundle / PILOT_CSV, "yolo_id", "conf")
    return a2, pilot, a3ci.class_names(bundle), pins


# ------------------------------------------------------------------------------- statistics


def relabel(value: Any) -> Any:
    """Rename the predecessor's ``a3`` keys to ``a2``; the numbers are untouched."""
    if isinstance(value, dict):
        return {_RELABEL.get(key, key): relabel(item) for key, item in value.items()}
    if isinstance(value, list):
        return [relabel(item) for item in value]
    return value


def _zero_width(interval: Sequence[float]) -> bool:
    return bool(interval[0] == interval[1])


def paired_block(
    a2: dict[str, np.ndarray],
    pilot: dict[str, np.ndarray],
    samples: Sequence[np.ndarray],
    focus: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Predecessor paired block, relabelled, plus explicit degenerate-interval flags."""
    block = relabel(a3ci.paired_block(a2, pilot, samples, focus))
    flagged = []
    for metric in METRICS:
        entry = block[metric]
        entry["zero_width_ci"] = _zero_width(entry["paired_ci95"])
        entry["ci_degenerate"] = entry["zero_width_ci"]
        if entry["ci_degenerate"]:
            flagged.append(metric)
    for key, entry in block.get("per_class_correct_class_recall", {}).items():
        entry["derived_key"] = key
        entry["a2_criteria_class"] = key in CRITERIA_KEYS
        if "paired_ci95" in entry:
            entry["zero_width_ci"] = _zero_width(entry["paired_ci95"])
            entry["ci_degenerate"] = entry["zero_width_ci"] or not entry["ci_interpretable"]
        else:
            entry["zero_width_ci"] = None
            entry["ci_degenerate"] = True
        if entry["ci_degenerate"]:
            flagged.append(f"class_{key}")
    block["degenerate_ci_flags"] = flagged
    block["degenerate_ci_note"] = (
        "9 validation groups: a zero-width or single-group interval shows too little group "
        "variation, not precision (contract §4 caveat)"
    )
    return block


def _maps(frames: Sequence[Frame], correct: Sequence[np.ndarray], index: np.ndarray) -> tuple:
    """mAP50 and mAP50-95 from one pinned Ultralytics ``ap_per_class`` call."""
    from ultralytics.utils.metrics import ap_per_class

    ap = ap_per_class(
        np.concatenate([correct[i] for i in index]),
        np.concatenate([frames[i].pred_scores for i in index]),
        np.concatenate([frames[i].pred_classes for i in index]),
        np.concatenate([frames[i].gt_classes for i in index]),
        plot=False,
        names={i: str(i) for i in range(a3ci.CLASSES)},
    )[5]
    return float(ap[:, 0].mean()), float(ap.mean())


def map_block(
    a2: Sequence[Frame], pilot: Sequence[Frame], samples: Sequence[np.ndarray]
) -> dict[str, Any]:
    ca2, cpilot = a3ci._correct_matrices(a2), a3ci._correct_matrices(pilot)
    full = np.arange(len(a2))
    pa2, ppilot = _maps(a2, ca2, full), _maps(pilot, cpilot, full)
    draws = [(_maps(a2, ca2, s), _maps(pilot, cpilot, s)) for s in samples]
    out: dict[str, Any] = {}
    for position, name in enumerate(("map50", "map50_95")):
        diffs = [x[position] - y[position] for x, y in draws]
        interval = a3ci.ci95(diffs)
        out[name] = {
            "a2": pa2[position],
            "pilot": ppilot[position],
            "difference_a2_minus_pilot": pa2[position] - ppilot[position],
            "paired_ci95": interval,
            "ci_excludes_zero": a3ci.excludes_zero(interval),
            "zero_width_ci": _zero_width(interval),
            "share_rounds_difference_gt_0": float(np.mean(np.asarray(diffs) > 0)),
        }
    out["note"] = "class set averaged = classes present in each resample (Ultralytics ap_per_class)"
    return out


def criteria_readout(block: dict[str, Any]) -> dict[str, Any]:
    """R3 §5 A2 criteria at conf 0.20, on point estimates; descriptive, not an acceptance."""
    classes = block["per_class_correct_class_recall"]
    per_class = {}
    for key in CRITERIA_KEYS:
        entry = classes[key]
        difference = entry.get("difference_a2_minus_pilot")
        gain = None if difference is None else bool(difference >= CLASS_RECALL_GAIN)
        per_class[key] = {
            "yolo_id": entry["yolo_id"],
            "support": entry["support"],
            "difference_a2_minus_pilot": difference,
            "meets_gain_0_05": gain,
            "ci_degenerate": entry["ci_degenerate"],
        }
    fp = block["fp_per_image"]["difference_a2_minus_pilot"]
    agnostic = block["agnostic_recall"]["a2"]
    met = [
        *(item["meets_gain_0_05"] for item in per_class.values()),
        bool(fp <= FP_INCREASE_MAX),
        bool(agnostic >= AGNOSTIC_RECALL_MIN),
    ]
    return {
        "label": "R3_A2_CRITERIA_POINT_READOUT_NOT_ACCEPTANCE",
        "conf": FIXED_CONF,
        "class_recall_gain_min": CLASS_RECALL_GAIN,
        "per_class": per_class,
        "fp_per_image_increase": fp,
        "fp_per_image_increase_within_0_03": bool(fp <= FP_INCREASE_MAX),
        "overall_recall_metric": "agnostic_recall (D-05 class-agnostic detection recall)",
        "a2_overall_recall": agnostic,
        "overall_recall_at_least_0_85": bool(agnostic >= AGNOSTIC_RECALL_MIN),
        "paired_cis_reported": True,
        "all_point_criteria_met": all(value is True for value in met),
        "note": "point estimates only; read with the paired CIs and degenerate flags; does not "
        "change D-05 or accept the model",
    }


# ----------------------------------------------------------------------------- reproduction


def reproduce(
    a2: list[Frame], pilot: list[Frame], stored: dict[str, Any], *, with_map: bool = True
) -> dict[str, Any]:
    """Stop unless the CSVs reproduce the A2 evaluator's JSON exactly (both models)."""
    checks: dict[str, Any] = {}
    for label, frames, key in (
        ("a2", a2, "a2_common_method"),
        ("pilot", pilot, "pilot_common_method"),
    ):
        ref = stored[key]
        selected_conf = ref["selected_on_val"]["conf"]
        if label == "pilot" and selected_conf != PILOT_SELECTED_CONF:
            raise RuntimeError("pilot validation-selected confidence differs from the anchor")
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
        if with_map:
            correct = a3ci._correct_matrices(frames)
            map50, map50_95 = _maps(frames, correct, np.arange(len(frames)))
            exact = ref["exact_class_ap"]
            if abs(map50 - exact["map50"]) > 1e-12 or abs(map50_95 - exact["map50_95"]) > 1e-12:
                raise RuntimeError(f"{label} exact-class mAP does not reproduce")
        fixed = operating_point(frames, FIXED_CONF)
        checks[label] = {
            "true_positives_020": fixed.true_positives,
            "false_positives_020": fixed.false_positives,
            "correct_class_hits_020": sum(fixed.per_class_hits.values()),
            "agnostic_recall_020": fixed.agnostic_recall,
            "fp_per_image_020": fixed.fp_per_image,
            "selected_conf": selected_conf,
            "exact_class_map50_reference": ref["exact_class_ap"]["map50"],
            "exact_class_map50_95_reference": ref["exact_class_ap"]["map50_95"],
            "per_model_bootstrap_reproduced": True,
            "operating_points_reproduced": True,
            "exact_class_map_reproduced": with_map,
        }
    return checks


# --------------------------------------------------------------------------------- evaluate


def evaluate(
    root: Path,
    csv_sha256: str,
    json_sha256: str,
    *,
    bundle: Path | None = None,
    a2_dir: Path = A2_DIR,
    with_map: bool = True,
) -> dict[str, Any]:
    bundle = (bundle or root / BUNDLE).resolve(strict=True)
    a2, pilot, names, pins = load(root, bundle, a2_dir, csv_sha256, json_sha256)
    if [f.group_id for f in a2] != [f.group_id for f in pilot]:
        raise RuntimeError("frame alignment differs")
    stored = json.loads((root / a2_dir / A2_JSON_NAME).read_text(encoding="utf-8"))
    focus = focus_ids(names)
    reproduction = reproduce(a2, pilot, stored, with_map=with_map)
    samples = a3ci.resample_indices(a2, ROUNDS, SEED)
    a2_fixed, pilot_fixed = a3ci.frame_stats(a2, FIXED_CONF), a3ci.frame_stats(pilot, FIXED_CONF)
    a2_selected_conf = reproduction["a2"]["selected_conf"]
    fixed_block = paired_block(a2_fixed, pilot_fixed, samples, focus)
    return {
        "package": PACKAGE,
        "experiment": EXPERIMENT,
        "split": "val",
        "frames": FRAMES,
        "gt_boxes": GT_BOXES,
        "groups": GROUPS,
        "bootstrap": {
            "rounds": ROUNDS,
            "seed": SEED,
            "unit": "intact D-02 validation capture group (9), resampled with replacement",
            "paired": "both models scored on the same resampled frames in every round",
            "interval": "95% percentile (numpy linear), difference = A2 minus pilot",
        },
        "focus_derived_key_to_yolo_id": focus,
        "input_sha256": pins,
        "reproduction_check": reproduction,
        "fixed_conf_020": fixed_block,
        "r3_a2_criteria_fixed_020": criteria_readout(fixed_block),
        "validation_selected_recall_085": {
            "label": "VALIDATION_SELECTED_DIAGNOSTIC_ONLY",
            "a2_conf": a2_selected_conf,
            "pilot_conf": PILOT_SELECTED_CONF,
            **paired_block(
                a3ci.frame_stats(a2, a2_selected_conf),
                a3ci.frame_stats(pilot, PILOT_SELECTED_CONF),
                samples,
            ),
        },
        "per_group_point_difference_fixed_020": a3ci.per_group(a2_fixed, pilot_fixed),
        "exact_class_map": map_block(a2, pilot, samples) if with_map else None,
        "inference_run": False,
        "training_run": False,
        "thresholds_changed": False,
        "sealed_test_accessed": False,
        "claim_scope": (
            "single-seed validation description of A2 (train-list repeat of derived keys "
            "7/32/41) versus the pilot; A2 is not compute-matched (about 26% more optimizer "
            "steps), so a difference mixes exposure and step count; not a sealed-test result"
        ),
    }


def canonical(payload: dict) -> str:
    return a3ci.canonical(payload)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=PACKAGE)
    parser.add_argument("command", choices=("write", "verify"))
    parser.add_argument("--a2-csv-sha256", required=True)
    parser.add_argument("--a2-json-sha256", required=True)
    parser.add_argument("--a2-dir", type=Path, default=A2_DIR)
    parser.add_argument("--bundle", type=Path, default=None)
    args = parser.parse_args(argv)
    text = canonical(
        evaluate(
            REPO_ROOT,
            args.a2_csv_sha256,
            args.a2_json_sha256,
            bundle=args.bundle,
            a2_dir=args.a2_dir,
        )
    )
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
    print(f"VERIFY PASS: {OUT} sha256={a3ci.sha256_file(target)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
