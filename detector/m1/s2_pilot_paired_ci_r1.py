"""Prepared paired S2 seed-19 minus pilot seed-18 validation-R3 comparison.

This is a *seed-variation* measurement, not an improvement test. It reads only previously
QA-passed prediction CSVs and a completed S2 common-evaluator result; no model inference occurs.
Do not invoke until the S2 run has result QA PASS and threshold-lock contract b is committed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np

from m1 import a2_pilot_paired_ci_r1 as a2ci
from m1 import a3_pilot_paired_ci_r1 as a3ci
from m1.metrics import Frame, operating_point, select_threshold

PACKAGE = "D1-S2-PILOT-PAIRED-CI-R1"
ROOT = Path(__file__).resolve().parents[2]
EVALUATOR = ROOT / "detector/colab/evaluate_d1_s2_r1_common_r1.py"
EVALUATOR_SHA256 = "e63f63f4c3fde7e744a253929e3fe9e4b3e8a8716334571e709bc9859d207cf2"
PREDECESSOR_SHA256 = {
    "a2_ci": "2dc6088ccc9efc92fc85543960c028a5b1aadb8d23c321ff241a04d1deaf0e1d",
    "a3_ci": "7edb3824a0f69f385fcb07628d4a5720688ee55af5cc4421c7b118165c0bdea4",
    "metrics": "d24570f85795e3bc5a2e754ace80a8081c510ff4a78833f2ab5316953a017f9f",
}
RESULT_NAME = "comparison_s2_r1.json"
CSV_NAME = "s2_predictions.csv"
OUTPUT = ROOT / "docs/review/generated/d1_s2_pilot_paired_ci_r1.json"
BUNDLE = ROOT / "tmp/yolo11n_n1_extract_r2"
FOCUS = {"7": 7, "32": 33, "41": 42}
ROUNDS, SEED, FIXED_CONF = 1000, 20261018, 0.20
LOCK_CONTRACT_SHA256 = "726932dbcd32842658477c9d36f4dc7c240d412d92119e76e5b3536a4d278f0f"
LOCK_QA_SHA256 = "e85c1ac36973f82b85bc28842afd01aa0c286b83db388f065f72115cac11d4a6"


def _require(path: Path, digest: str, label: str) -> None:
    if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise RuntimeError(f"{label} SHA-256 is malformed")
    if path.is_symlink() or not path.is_file() or a3ci.sha256_file(path) != digest:
        raise RuntimeError(f"{label} SHA-256 differs")


def _verify_prerequisites(result: dict, qa_record: Path, qa_sha256: str) -> None:
    for relative, digest in (
        ("docs/review/d1_threshold_lock_r1_contract.md", LOCK_CONTRACT_SHA256),
        ("docs/review/d1_threshold_lock_r1_contract_independent_qa_record.md", LOCK_QA_SHA256),
    ):
        _require(ROOT / relative, digest, "committed threshold-selection contract")
        committed = subprocess.run(
            ["git", "show", f"HEAD:{relative}"], cwd=ROOT, capture_output=True, check=False
        )
        if committed.returncode != 0 or hashlib.sha256(committed.stdout).hexdigest() != digest:
            raise RuntimeError("threshold-selection contract is not committed")
    if (
        qa_record.is_absolute()
        or qa_record.parent.as_posix() != "docs/review"
        or qa_record.suffix != ".md"
        or "test" in qa_record.name.lower()
    ):
        raise RuntimeError("S2 result QA path is invalid")
    _require(ROOT / qa_record, qa_sha256, "S2 result QA")
    text = (ROOT / qa_record).read_text(encoding="utf-8")
    verdicts = [line for line in text.splitlines() if line.startswith("Verdict:")]
    archive_sha = result.get("s2_result_archive_sha256")
    manifest_sha = result.get("s2_result_manifest_sha256")
    if (
        len(verdicts) != 1
        or re.fullmatch(r"Verdict: PASS(?:\s+.*)?", verdicts[0]) is None
        or "D1-S2-R1" not in text
        or "sealed_test_accessed=false" not in text
        or not isinstance(archive_sha, str)
        or re.fullmatch(r"[0-9a-f]{64}", archive_sha) is None
        or archive_sha not in text
        or not isinstance(manifest_sha, str)
        or re.fullmatch(r"[0-9a-f]{64}", manifest_sha) is None
        or manifest_sha not in text
        or result.get("prerequisite_sha256")
        != {
            "contract_b": LOCK_CONTRACT_SHA256,
            "contract_b_qa": LOCK_QA_SHA256,
            "s2_result_qa": qa_sha256,
        }
    ):
        raise RuntimeError("S2 result QA does not bind the completed sealed-test-free run")


def verify_inputs(
    directory: Path,
    csv_sha256: str,
    result_sha256: str,
    qa_record: Path,
    qa_sha256: str,
) -> dict[str, Any]:
    _require(EVALUATOR, EVALUATOR_SHA256, "S2 common evaluator")
    for label, module in (
        ("a2_ci", a2ci),
        ("a3_ci", a3ci),
    ):
        _require(Path(module.__file__), PREDECESSOR_SHA256[label], label)
    _require(Path(operating_point.__code__.co_filename), PREDECESSOR_SHA256["metrics"], "metrics")
    _require(directory / CSV_NAME, csv_sha256, "S2 prediction CSV")
    _require(directory / RESULT_NAME, result_sha256, "S2 evaluation result")
    _require(BUNDLE / "manifest.json", a3ci.BUNDLE_MANIFEST_SHA256, "R3 bundle")
    _require(BUNDLE / a3ci.PILOT_CSV, a3ci.PILOT_CSV_SHA256, "pilot CSV")
    manifest = json.loads((BUNDLE / "manifest.json").read_text(encoding="utf-8"))
    if (
        manifest.get("test_included") is not False
        or manifest.get("sealed_test_accessed") is not False
        or manifest.get("counts", {}).get("val") != {"images": 376, "boxes": 624}
    ):
        raise RuntimeError("R3 bundle is not the governed validation-only package")
    members = manifest["members"]
    used = [
        name
        for name in members
        if name.startswith(("data/images/val/", "data/labels54/val/"))
        or name in ("data/val_groups.json", "data/classes.csv", a3ci.PILOT_CSV)
    ]
    if any("test" in Path(name).parts for name in used):
        raise RuntimeError("sealed-test member requested")
    for name in used:
        _require(BUNDLE / name, members[name]["sha256"], name)
    if members[a3ci.PILOT_CSV]["sha256"] != a3ci.PILOT_CSV_SHA256:
        raise RuntimeError("pilot CSV bundle member differs")
    result = json.loads((directory / RESULT_NAME).read_text(encoding="utf-8"))
    _verify_prerequisites(result, qa_record, qa_sha256)
    if (
        result.get("package") != "D1-S2-R1-COMMON-VALIDATION-R1"
        or result.get("experiment") != "D1-S2-R1"
        or result.get("split") != "val"
        or result.get("frames") != 376
        or result.get("gt_boxes") != 624
        or result.get("prediction_csv_sha256") != csv_sha256
        or result.get("bundle_manifest_sha256") != a3ci.BUNDLE_MANIFEST_SHA256
        or result.get("sealed_test_accessed") is not False
    ):
        raise RuntimeError("S2 common result binding differs")
    return result


def load_frames(directory: Path) -> tuple[list[Frame], list[Frame], dict[str, int]]:
    base = a3ci.gt_frames(BUNDLE)
    if len(base) != 376 or sum(len(f.gt_boxes) for f in base) != 624:
        raise RuntimeError("R3 validation roster differs")
    names = a3ci.class_names(BUNDLE)
    ids = {key: names.index(key) for key in FOCUS}
    if ids != FOCUS:
        raise RuntimeError(f"derived key class map differs: {ids}")
    s2 = a3ci.with_predictions(base, directory / CSV_NAME, "class_id", "confidence")
    pilot = a3ci.with_predictions(base, BUNDLE / a3ci.PILOT_CSV, "yolo_id", "conf")
    if [f.group_id for f in s2] != [f.group_id for f in pilot]:
        raise RuntimeError("S2/pilot frame groups differ")
    return s2, pilot, ids


def reproduce(s2: list[Frame], pilot: list[Frame], stored: dict[str, Any]) -> dict[str, Any]:
    checks = {}
    for label, frames, field in (
        ("s2", s2, "s2_common_method"),
        ("pilot", pilot, "pilot_common_method"),
    ):
        ref = stored[field]
        for point_name, conf in (
            ("fixed_conf_020", FIXED_CONF),
            ("selected_on_val", ref["selected_on_val"]["conf"]),
        ):
            actual = operating_point(frames, conf)
            expected = ref[point_name]
            for name in (
                "true_positives",
                "false_positives",
                "ground_truth",
                "agnostic_recall",
                "fp_per_image",
            ):
                if getattr(actual, name) != expected[name]:
                    raise RuntimeError(f"{label} {point_name} {name} differs")
            if {str(k): v for k, v in actual.per_class_hits.items()} != expected["per_class_hits"]:
                raise RuntimeError(f"{label} class hits differ")
        if (
            select_threshold(frames, 0.85, a3ci.SELECTION_GRID).conf
            != ref["selected_on_val"]["conf"]
        ):
            raise RuntimeError(f"{label} selected confidence differs")
        correct = a3ci._correct_matrices(frames)
        ap50, ap = a2ci._maps(frames, correct, np.arange(len(frames)))
        if (
            abs(ap50 - ref["exact_class_ap"]["map50"]) > 1e-12
            or abs(ap - ref["exact_class_ap"]["map50_95"]) > 1e-12
        ):
            raise RuntimeError(f"{label} mAP does not reproduce")
        point = operating_point(frames, FIXED_CONF)
        checks[label] = {
            "tp_020": point.true_positives,
            "fp_020": point.false_positives,
            "correct_class_hits_020": sum(point.per_class_hits.values()),
            "map50": ap50,
            "map50_95": ap,
            "selected_conf": ref["selected_on_val"]["conf"],
        }
    p = checks["pilot"]
    if (
        (p["tp_020"], p["fp_020"], p["correct_class_hits_020"]) != (547, 150, 457)
        or abs(p["map50"] - 0.8521) > 1e-4
        or abs(p["map50_95"] - 0.6089) > 1e-4
    ):
        raise RuntimeError("QA-passed pilot baseline is not reproduced")
    return checks


def _paired_map(s2: list[Frame], pilot: list[Frame], samples: list[np.ndarray]) -> dict:
    cs2, cpilot = a3ci._correct_matrices(s2), a3ci._correct_matrices(pilot)
    full = np.arange(len(s2))
    current, baseline = a2ci._maps(s2, cs2, full), a2ci._maps(pilot, cpilot, full)
    draws = [(a2ci._maps(s2, cs2, ids), a2ci._maps(pilot, cpilot, ids)) for ids in samples]
    out = {}
    for index, name in enumerate(("map50", "map50_95")):
        difference = [left[index] - right[index] for left, right in draws]
        out[name] = {
            "s2": current[index],
            "pilot": baseline[index],
            "difference_s2_minus_pilot": current[index] - baseline[index],
            "paired_ci95": a3ci.ci95(difference),
        }
    return out


def evaluate(
    directory: Path,
    csv_sha256: str,
    result_sha256: str,
    qa_record: Path,
    qa_sha256: str,
) -> dict:
    stored = verify_inputs(directory, csv_sha256, result_sha256, qa_record, qa_sha256)
    s2, pilot, focus = load_frames(directory)
    reproduced = reproduce(s2, pilot, stored)
    samples = a3ci.resample_indices(s2, ROUNDS, SEED)
    s2_stats = a3ci.frame_stats(s2, FIXED_CONF)
    pilot_stats = a3ci.frame_stats(pilot, FIXED_CONF)
    paired = a3ci.paired_block(s2_stats, pilot_stats, samples, focus)
    for section in ("agnostic_recall", "correct_class_recall", "fp_per_image"):
        item = paired[section]
        item["s2"] = item.pop("a3")
        item["difference_s2_minus_pilot"] = item.pop("difference_a3_minus_pilot")
        item["s2_marginal_ci95"] = item.pop("a3_marginal_ci95")
    for item in paired["per_class_correct_class_recall"].values():
        if "a3" in item:
            item["s2"] = item.pop("a3")
            item["difference_s2_minus_pilot"] = item.pop("difference_a3_minus_pilot")
    return {
        "package": PACKAGE,
        "description": "seed 20261019 minus seed 20261018 variation; not an improvement test",
        "split": "val",
        "frames": 376,
        "gt_boxes": 624,
        "groups": 9,
        "bootstrap": {"rounds": ROUNDS, "seed": SEED, "paired": True, "unit": "D-02 group"},
        "focus_derived_key_to_yolo_id": focus,
        "input_sha256": {
            "s2_evaluator": EVALUATOR_SHA256,
            "s2_result_qa": qa_sha256,
            "predecessors": PREDECESSOR_SHA256,
            "s2_prediction_csv": csv_sha256,
            "s2_common_result": result_sha256,
            "r3_bundle": a3ci.BUNDLE_MANIFEST_SHA256,
            "pilot_prediction_csv": a3ci.PILOT_CSV_SHA256,
        },
        "pilot_reproduction": reproduced,
        "fixed_conf_020": paired,
        "exact_class_map": _paired_map(s2, pilot, samples),
        "inference_run": False,
        "training_run": False,
        "thresholds_locked": False,
        "sealed_test_accessed": False,
    }


def canonical(value: dict) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("write", "verify"))
    parser.add_argument("--s2-dir", type=Path, required=True)
    parser.add_argument("--s2-csv-sha256", required=True)
    parser.add_argument("--s2-json-sha256", required=True)
    parser.add_argument("--s2-result-qa-record", type=Path, required=True)
    parser.add_argument("--s2-result-qa-sha256", required=True)
    args = parser.parse_args(argv)
    text = canonical(
        evaluate(
            args.s2_dir,
            args.s2_csv_sha256,
            args.s2_json_sha256,
            args.s2_result_qa_record,
            args.s2_result_qa_sha256,
        )
    )
    if args.command == "write":
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        with OUTPUT.open("x", encoding="utf-8") as sink:
            sink.write(text)
        print(f"wrote {OUTPUT} sha256={hashlib.sha256(text.encode()).hexdigest()}")
        return 0
    if OUTPUT.read_text(encoding="utf-8") != text:
        print("VERIFY FAIL: stored S2 paired CI differs", file=sys.stderr)
        return 1
    print(f"VERIFY PASS: {OUTPUT} sha256={a3ci.sha256_file(OUTPUT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
