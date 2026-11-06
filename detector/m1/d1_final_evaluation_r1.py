"""Prepared two-seed D1 final evaluator. Never run without the final Owner gates.

This module defines a future one-time entry point. Its current tests use only
synthetic frames and records; no sealed payload or real weight is needed.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
import os
import re
import subprocess
import tempfile
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

import numpy as np

from m1 import contract
from m1.metrics import (
    Frame,
    ap_small,
    confusion_matrix,
    error_samples,
    iou_matrix,
    latency_stats,
    operating_point,
    resolution_breakdown,
    unknown_false_recognition,
)

PACKAGE = "D1-FINAL-EVALUATION-R1"
SEEDS = (20261018, 20261019)
SOURCE_PATHS = frozenset(
    {
        "detector/m1/d1_final_evaluation_r1.py",
        "detector/m1/d1_threshold_lock_r3_successor.py",
        "detector/m1/contract.py",
        "detector/m1/metrics.py",
        "detector/colab/evaluate_cascade_b0_r1.py",
        "detector/uv.lock",
    }
)
CONTRACT_PATH = "docs/review/d1_final_evaluation_r4_contract.md"
ACCESS_LOG = "results/experiments/sealed_test_access_log.jsonl"
ACCESS_ACTION = "d1-final-evaluation-r4-open"
OPEN_MARKER = "OWNER_AUTHORIZES_TEST_OPEN: D1-FINAL-EVALUATION-R1"
CONTRACT_MARKER = "FINAL_EVALUATION_CONTRACT: APPROVED"
HEX = re.compile(r"[0-9a-f]{64}\Z")
ATTEMPT2_ENTRY = {
    "time": "20261106T231301",
    "action": "d1-final-evaluation-r1-open",
    "reason": (
        "One-time D1 final evaluation of seeds 20261018 and 20261019 under the approved "
        "R3 lock and D-05 gates. | "
        "plan_sha256=69f54ee3f6e6d10914d5347fa445d5457df43954dad063dbb0b90bb725b914a0 | "
        "contract_sha256=0f8bbf104e523f243f5f0e3c6b23b4e9545bf98a353a1f6b560c62cc3cfa86ff"
    ),
}
EXPECTED_ACCESS_LINE_SHA256 = (
    "ffef1b183ec8b4a20661c4bca71efa3cab64692c445432bc38eb3b3f2773b369",
    "21750b2d33fae93d3d67e3dfafb80ad239245885dc3fb1d0ef024f652431e23b",
    "85d4a64c574cd906402a68c2e606d1bd1325c5f835fd212853faf5624d2155d1",
)
TEST_EXPORT_NAME = "data_test.yaml"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def _relative(root: Path, name: str) -> Path:
    path = Path(name)
    if path.is_absolute() or not path.parts or ".." in path.parts or str(path) != path.as_posix():
        raise RuntimeError("path must be a canonical repository-relative path")
    target = root / path
    if any(part.is_symlink() for part in (target, *target.parents) if part != root.parent):
        raise RuntimeError(f"symlink in pinned path: {name}")
    if not target.resolve().is_relative_to(root.resolve()):
        raise RuntimeError(f"path leaves checkout: {name}")
    return target


def _committed(root: Path, name: str, expected: str) -> None:
    result = subprocess.run(
        ["git", "show", f"HEAD:{name}"], cwd=root, capture_output=True, check=False
    )
    if result.returncode or hashlib.sha256(result.stdout).hexdigest() != expected:
        raise RuntimeError(f"pinned file is not committed unchanged: {name}")


def pinned(root: Path, spec: dict[str, str], *, committed: bool = True) -> Path:
    if set(spec) != {"path", "sha256"} or HEX.fullmatch(spec["sha256"]) is None:
        raise RuntimeError("invalid path/hash pin")
    target = _relative(root, spec["path"])
    if not target.is_file() or sha256(target) != spec["sha256"]:
        raise RuntimeError(f"pinned file differs: {spec['path']}")
    if committed:
        _committed(root, spec["path"], spec["sha256"])
    return target


def _record_json(root: Path, spec: dict[str, str], *, committed: bool) -> dict[str, Any]:
    value = json.loads(pinned(root, spec, committed=committed).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("decision record must be an object")
    return value


def _decision_gates(record: dict[str, Any]) -> dict[str, float | int]:
    if (
        set(record) != {"package", "decision", "gates", "owner_quote", "sealed_test_accessed"}
        or record["package"] != PACKAGE
        or record["decision"] not in {"KEEP_ORIGINAL", "RECALIBRATE_ONCE"}
        or not isinstance(record["owner_quote"], str)
        or not record["owner_quote"].strip()
        or record["sealed_test_accessed"] is not False
        or not isinstance(record["gates"], dict)
        or set(record["gates"]) != set(contract.GATES)
    ):
        raise RuntimeError("Q4 Owner decision is incomplete")
    gates = record["gates"]
    if any(
        type(value) not in (int, float) or not math.isfinite(value) or value < 0
        for value in gates.values()
    ):
        raise RuntimeError("invalid Q4 gate value")
    if record["decision"] == "KEEP_ORIGINAL" and gates != contract.GATES:
        raise RuntimeError("unchanged Q4 decision altered a gate")
    if gates["min_support_for_class_gate"] != contract.GATES["min_support_for_class_gate"]:
        raise RuntimeError("Q4 cannot change the class support rule")
    return gates


def _label_decision(
    root: Path, record: dict[str, Any], *, committed: bool
) -> tuple[str, dict[str, str] | None]:
    if (
        record.get("package") != PACKAGE
        or record.get("mode") not in {"CURRENT_LABELS", "PREDICTION_BLIND_REVIEW"}
        or not isinstance(record.get("owner_quote"), str)
        or not record["owner_quote"].strip()
        or record.get("sealed_test_accessed") is not False
    ):
        raise RuntimeError("Owner label decision is incomplete")
    if record["mode"] == "PREDICTION_BLIND_REVIEW":
        review = record.get("blind_review_qa")
        overlay = record.get("approved_labels")
        if (
            set(record)
            != {
                "package",
                "mode",
                "owner_quote",
                "sealed_test_accessed",
                "blind_review_qa",
                "approved_labels",
            }
            or not isinstance(review, dict)
            or not isinstance(overlay, dict)
            or set(overlay) != {"path", "sha256"}
            or not isinstance(overlay["path"], str)
            or not isinstance(overlay["sha256"], str)
            or HEX.fullmatch(overlay["sha256"]) is None
        ):
            raise RuntimeError("blind review requires separate QA")
        _relative(root, overlay["path"])
        text = pinned(root, review, committed=committed).read_text(encoding="utf-8")
        if (
            len([line for line in text.splitlines() if line.startswith("Verdict:")]) != 1
            or "Verdict: PASS" not in text
            or overlay["sha256"] not in text
        ):
            raise RuntimeError("blind review QA is not PASS")
    elif set(record) != {"package", "mode", "owner_quote", "sealed_test_accessed"}:
        raise RuntimeError("current-label decision has unexpected fields")
    return record["mode"], overlay if record["mode"] == "PREDICTION_BLIND_REVIEW" else None


def _read_access_log(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("access log is not a regular file")
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        item = json.loads(line)
        if not isinstance(item, dict):
            raise RuntimeError("access log entry is invalid")
        entries.append(item)
    return entries


def _check_prior_openings(path: Path) -> None:
    """Allow only the exact three recorded prior events, in their original order."""
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("pinned final evaluation access history is absent")
    lines = path.read_bytes().splitlines(keepends=True)
    if tuple(hashlib.sha256(line).hexdigest() for line in lines) != EXPECTED_ACCESS_LINE_SHA256:
        raise RuntimeError("final evaluation access history differs from three pinned lines")
    entries = _read_access_log(path)
    if [entry.get("action") for entry in entries] != [
        "d1-final-evaluation-r1-open", "export-test", "d1-final-evaluation-r3-open"
    ]:
        raise RuntimeError("final evaluation access action sequence differs")


@dataclass(frozen=True)
class Approved:
    plan_sha256: str
    final_contract_sha256: str
    selection: dict[str, Any]
    gates: dict[str, float | int]
    label_mode: str
    label_overlay: dict[str, str] | None
    weights: tuple[dict[str, Any], dict[str, Any]]
    reason: str
    test_export: Path
    access_log: Path
    output_dir: Path


def preflight(
    plan_path: Path,
    *,
    root: Path = contract.REPO_ROOT,
    reader: Callable[..., dict[str, Any]] | None = None,
    committed: bool = True,
) -> Approved:
    """Read only approvals, source, weights, validation lock and access log."""
    root = root.resolve()
    if Path.cwd() != root / "detector":
        raise RuntimeError("preflight requires CWD at REPO_ROOT/detector")
    if plan_path.is_absolute():
        raise RuntimeError("plan must be repository-relative")
    plan_target = _relative(root, plan_path.as_posix())
    if not plan_target.is_file():
        raise RuntimeError("final evaluation plan is missing")
    plan_sha = sha256(plan_target)
    if committed:
        _committed(root, plan_path.as_posix(), plan_sha)
    plan = json.loads(plan_target.read_text(encoding="utf-8"))
    required = {
        "package",
        "schema_version",
        "lock_record",
        "lock_proof",
        "lock_result_qa",
        "owner_lock_approval",
        "bundle",
        "final_contract",
        "owner_open_approval",
        "q4_decision",
        "label_decision",
        "weights",
        "source_sha256",
        "output_dir",
        "reason",
        "imgsz",
        "device",
        "sealed_test_accessed",
    }
    if (
        not isinstance(plan, dict)
        or set(plan) != required
        or plan["package"] != PACKAGE
        or plan["schema_version"] != 1
        or plan["sealed_test_accessed"] is not False
    ):
        raise RuntimeError("final evaluation plan schema differs")
    if (
        plan["imgsz"] != 1280
        or plan["device"] != "mps"
        or not isinstance(plan["reason"], str)
        or not plan["reason"].strip()
    ):
        raise RuntimeError("final evaluation runtime or reason differs")
    weights = plan["weights"]
    if (
        not isinstance(weights, list)
        or len(weights) != 2
        or {x.get("seed") for x in weights} != set(SEEDS)
    ):
        raise RuntimeError("exactly the two approved seeds are required")
    if len({x.get("sha256") for x in weights}) != 2:
        raise RuntimeError("candidate weights must differ")

    # Gate 1: the R3 reader re-verifies the lock and its independent QA/approval.
    for key in ("lock_record", "lock_proof", "lock_result_qa", "owner_lock_approval"):
        pinned(root, plan[key], committed=committed)
    lock_path = _relative(root, plan["lock_record"]["path"])
    proof_path = _relative(root, plan["lock_proof"]["path"])
    lock_record = json.loads(lock_path.read_text(encoding="utf-8"))
    proof_binding = lock_record.get("proof") if isinstance(lock_record, dict) else None
    if not isinstance(proof_binding, dict) or set(proof_binding) != {"path", "sha256"}:
        raise RuntimeError("lock proof binding is absent")
    if not isinstance(proof_binding["path"], str):
        raise RuntimeError("lock proof path is invalid")
    bound_proof = Path(proof_binding["path"])
    if bound_proof.is_absolute() or not bound_proof.as_posix().startswith("../docs/"):
        raise RuntimeError("lock proof path is not detector-relative")
    try:
        same_proof = bound_proof.samefile(proof_path)
    except (OSError, ValueError, TypeError):
        same_proof = False
    if (
        not same_proof
        or proof_binding["sha256"] != plan["lock_proof"]["sha256"]
        or sha256(bound_proof) != plan["lock_proof"]["sha256"]
    ):
        raise RuntimeError("lock proof path or hash differs from plan")
    reader_lock = Path("..") / plan["lock_record"]["path"]
    if not reader_lock.samefile(lock_path):
        raise RuntimeError("lock path differs from plan")
    bundle_manifest = pinned(root, plan["bundle"], committed=False)
    bundle_record = json.loads(bundle_manifest.read_text(encoding="utf-8"))
    if (
        bundle_record.get("test_included") is not False
        or bundle_record.get("sealed_test_accessed") is not False
    ):
        raise RuntimeError("R3 bundle is not validation-only")
    if reader is None:
        from m1.d1_threshold_lock_r3_successor import read_for_final

        reader = read_for_final
    settings = []
    lock_qa = {
        **plan["lock_result_qa"],
        "path": str(_relative(root, plan["lock_result_qa"]["path"])),
    }
    lock_approval = {
        **plan["owner_lock_approval"],
        "path": str(_relative(root, plan["owner_lock_approval"]["path"])),
    }
    for weight in sorted(weights, key=lambda row: row["seed"]):
        settings.append(
            reader(
                reader_lock,
                bound_proof,
                bundle_manifest.parent,
                root,
                weight["sha256"],
                lock_qa,
                lock_approval,
            )
        )
    if settings[0] != settings[1] or set(settings[0]) != {"conf", "nms_iou", "agnostic_nms"}:
        raise RuntimeError("both candidates need one verified R3 setting")
    candidates = lock_record.get("candidates") if isinstance(lock_record, dict) else None
    if (
        not isinstance(candidates, list)
        or len(candidates) != 2
        or any(
            not isinstance(candidate, dict)
            or candidate.get("seed") not in SEEDS
            or not isinstance(candidate.get("weight"), dict)
            or not isinstance(candidate["weight"].get("sha256"), str)
            for candidate in candidates
        )
        or {candidate["seed"]: candidate["weight"]["sha256"] for candidate in candidates}
        != {weight["seed"]: weight["sha256"] for weight in weights}
    ):
        raise RuntimeError("candidate seed-to-weight binding differs from verified R3 lock")
    if (
        not 0 < settings[0]["conf"] <= 1
        or not 0 < settings[0]["nms_iou"] <= 1
        or type(settings[0]["agnostic_nms"]) is not bool
    ):
        raise RuntimeError("R3 setting is invalid")

    # Gates 2-5: the final contract and distinct Owner decisions must be committed.
    if plan["final_contract"] != CONTRACT_PATH:
        raise RuntimeError("final contract path differs")
    contract_file = _relative(root, CONTRACT_PATH)
    if not contract_file.is_file():
        raise RuntimeError("final contract is absent")
    contract_sha = sha256(contract_file)
    contract_text = contract_file.read_text(encoding="utf-8")
    if CONTRACT_MARKER not in contract_text or plan_sha not in contract_text:
        raise RuntimeError("final contract does not bind the plan")
    if committed:
        _committed(root, CONTRACT_PATH, contract_sha)
    owner_open = _relative(root, plan["owner_open_approval"])
    if not owner_open.is_file():
        raise RuntimeError("Owner has not approved opening")
    open_text = owner_open.read_text(encoding="utf-8")
    if (
        OPEN_MARKER not in open_text
        or contract_sha not in open_text
        or plan["reason"] not in open_text
    ):
        raise RuntimeError("Owner opening approval does not bind contract and reason")
    if committed:
        _committed(root, plan["owner_open_approval"], sha256(owner_open))
    q4 = _record_json(root, plan["q4_decision"], committed=committed)
    gates = _decision_gates(q4)
    labels = _record_json(root, plan["label_decision"], committed=committed)
    label_mode, label_overlay = _label_decision(root, labels, committed=committed)

    # Gate 6: all candidate weights and executable source bytes match the plan.
    if set(plan["source_sha256"]) != SOURCE_PATHS:
        raise RuntimeError("source pin set differs")
    for name, digest in plan["source_sha256"].items():
        pinned(root, {"path": name, "sha256": digest}, committed=committed)
    verified_weights = []
    for weight in weights:
        if set(weight) != {"seed", "path", "sha256"}:
            raise RuntimeError("candidate weight binding differs")
        path = Path(weight["path"])
        if not path.is_absolute():
            path = _relative(root, weight["path"])
        if (
            path.is_symlink()
            or not path.is_file()
            or HEX.fullmatch(weight["sha256"]) is None
            or sha256(path) != weight["sha256"]
        ):
            raise RuntimeError("candidate weight hash differs")
        verified_weights.append({**weight, "path": str(path)})

    # Gate 7: export presence and the pinned no-payload attempt precede any new opening.
    test_export = root / contract.EXPORT_DIR.relative_to(contract.REPO_ROOT) / TEST_EXPORT_NAME
    if test_export.is_symlink() or not test_export.is_file():
        raise RuntimeError("test export data_test.yaml is absent")
    access_log = root / ACCESS_LOG
    _check_prior_openings(access_log)
    output_dir = _relative(root, plan["output_dir"])
    if output_dir.exists() or not output_dir.is_relative_to(root / "results/experiments"):
        raise RuntimeError("final evaluation output is not a new experiment directory")
    return Approved(
        plan_sha,
        contract_sha,
        settings[0],
        gates,
        label_mode,
        label_overlay,
        tuple(sorted(verified_weights, key=lambda row: row["seed"])),
        plan["reason"],
        test_export,
        access_log,
        output_dir,
    )


def exact_class_ap(frames: list[Frame]) -> dict[str, Any]:
    """Pinned Ultralytics matching/AP method, with both per-class AP columns."""
    from types import SimpleNamespace

    import torch
    from ultralytics.engine.validator import BaseValidator
    from ultralytics.utils.metrics import ap_per_class

    validator = SimpleNamespace(iouv=torch.linspace(0.5, 0.95, 10))
    correct, conf, pred, target = [], [], [], []
    for frame in frames:
        matched = BaseValidator.match_predictions(
            validator,
            torch.as_tensor(frame.pred_classes),
            torch.as_tensor(frame.gt_classes),
            torch.as_tensor(iou_matrix(frame.gt_boxes, frame.pred_boxes)),
        )
        correct.append(matched.numpy())
        conf.append(frame.pred_scores)
        pred.append(frame.pred_classes)
        target.append(frame.gt_classes)
    gt = np.concatenate(target)
    classes = np.unique(gt).astype(int)
    if not len(gt) or not sum(map(len, pred)):
        return {
            "map50": 0.0,
            "map50_95": 0.0,
            "supported_classes": classes.tolist(),
            "per_class_ap50": {str(c): 0.0 for c in classes},
            "per_class_ap50_95": {str(c): 0.0 for c in classes},
        }
    result = ap_per_class(
        np.concatenate(correct),
        np.concatenate(conf),
        np.concatenate(pred),
        gt,
        plot=False,
        names={i: str(i) for i in range(54)},
    )
    ap, supported = result[5], result[6]
    if set(map(int, supported)) != set(classes):
        raise RuntimeError("AP class support differs from GT classes")
    return {
        "map50": float(ap[:, 0].mean()),
        "map50_95": float(ap.mean()),
        "supported_classes": list(map(int, supported)),
        "per_class_ap50": {str(int(c)): float(v) for c, v in zip(supported, ap[:, 0], strict=True)},
        "per_class_ap50_95": {
            str(int(c)): float(v) for c, v in zip(supported, ap.mean(1), strict=True)
        },
    }


def _same_roster(left: list[Frame], right: list[Frame]) -> None:
    if len(left) != len(right) or not left:
        raise RuntimeError("two seed rosters differ or are empty")
    for a, b in zip(left, right, strict=True):
        if (
            a.stem != b.stem
            or a.group_id != b.group_id
            or a.image_width != b.image_width
            or a.image_height != b.image_height
            or not np.array_equal(a.gt_boxes, b.gt_boxes)
            or not np.array_equal(a.gt_classes, b.gt_classes)
        ):
            raise RuntimeError("two seed GT/group/size roster differs")


def _seed_score(frames: list[Frame], conf: float, class_count: int) -> dict[str, Any]:
    point = operating_point(frames, conf)
    ap = exact_class_ap(frames)
    return {
        "exact_class_ap": ap,
        "operating_point": asdict(point),
        "ap_small_project_method": ap_small(frames),
        "resolution_breakdown": resolution_breakdown(frames, conf),
        "confusion_matrix": confusion_matrix(frames, conf, class_count),
        "error_samples": error_samples(frames, conf),
        "unknown_false_recognition": unknown_false_recognition(frames, conf),
    }


def _ci(values: list[float]) -> list[float]:
    return [float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))]


def paired_group_ci(
    by_seed: dict[int, list[Frame]], conf: float, *, rounds: int = 1000, seed: int = 20261018
) -> dict[str, Any]:
    """Resample intact D-02 groups with shared draws for both fixed weights."""
    first, second = (by_seed[item] for item in SEEDS)
    _same_roster(first, second)
    groups = sorted({frame.group_id for frame in first})
    if not groups or rounds < 1:
        raise RuntimeError("bootstrap requires groups and draws")
    indexed = {
        s: {group: [frame for frame in by_seed[s] if frame.group_id == group] for group in groups}
        for s in SEEDS
    }
    samples: dict[str, list[float]] = {
        "map50": [],
        "map50_95": [],
        "agnostic_recall": [],
        "fp_per_image": [],
    }
    rng = np.random.default_rng(seed)
    for _ in range(rounds):
        draw = rng.choice(groups, len(groups), replace=True)
        rows = {s: [frame for group in draw for frame in indexed[s][str(group)]] for s in SEEDS}
        points = [operating_point(rows[s], conf) for s in SEEDS]
        aps = [exact_class_ap(rows[s]) for s in SEEDS]
        for key in ("map50", "map50_95"):
            samples[key].append(sum(ap[key] for ap in aps) / 2)
        for key in ("agnostic_recall", "fp_per_image"):
            samples[key].append(sum(getattr(point, key) for point in points) / 2)
    return {
        "unit": "D-02 group",
        "groups": len(groups),
        "rounds": rounds,
        "seed": seed,
        "weights_fixed": True,
        "two_seed_mean_ci95": {key: _ci(values) for key, values in samples.items()},
    }


def score_two_seeds(
    by_seed: dict[int, list[Frame]],
    selection: dict[str, Any],
    gates: dict[str, float | int],
    class_ids: dict[str, int],
    *,
    rounds: int = 1000,
) -> dict[str, Any]:
    """Score only already provided frames; the caller controls all data access."""
    if set(by_seed) != set(SEEDS) or set(gates) != set(contract.GATES):
        raise RuntimeError("seed or gate set differs")
    if set(selection) != {"conf", "nms_iou", "agnostic_nms"}:
        raise RuntimeError("lock selection differs")
    _same_roster(by_seed[SEEDS[0]], by_seed[SEEDS[1]])
    conf = float(selection["conf"])
    if not 0 < conf <= 1 or len(set(class_ids.values())) != len(class_ids):
        raise RuntimeError("invalid threshold or class map")
    if not set(contract.CRITICAL_KEYS).issubset(class_ids):
        raise RuntimeError("critical class map is incomplete")
    class_count = max(class_ids.values()) + 1
    per_seed = {str(s): _seed_score(by_seed[s], conf, class_count) for s in SEEDS}
    first, second = (per_seed[str(s)] for s in SEEDS)
    if (
        first["exact_class_ap"]["supported_classes"]
        != second["exact_class_ap"]["supported_classes"]
    ):
        raise RuntimeError("AP class support differs between seeds")
    fields = {
        "map50": (first["exact_class_ap"]["map50"], second["exact_class_ap"]["map50"]),
        "map50_95": (first["exact_class_ap"]["map50_95"], second["exact_class_ap"]["map50_95"]),
        "agnostic_recall": (
            first["operating_point"]["agnostic_recall"],
            second["operating_point"]["agnostic_recall"],
        ),
        "fp_per_image": (
            first["operating_point"]["fp_per_image"],
            second["operating_point"]["fp_per_image"],
        ),
    }
    aggregate = {
        key: {
            "seed_20261018": pair[0],
            "seed_20261019": pair[1],
            "mean": sum(pair) / 2,
            "difference_19_minus_18": pair[1] - pair[0],
        }
        for key, pair in fields.items()
    }
    support = first["operating_point"]["per_class_support"]
    if support != second["operating_point"]["per_class_support"]:
        raise RuntimeError("class support differs between seeds")
    classes = {}
    excluded = []
    for key, cls in sorted(class_ids.items(), key=lambda row: (row[1], row[0])):
        count = support.get(cls, 0)
        critical = key in contract.CRITICAL_KEYS
        gated = count >= gates["min_support_for_class_gate"]
        pair = [per_seed[str(s)]["operating_point"]["per_class_recall"].get(cls) for s in SEEDS]
        mean = sum(pair) / 2 if gated else None
        threshold = gates["critical_class_recall"] if critical else gates["other_class_recall"]
        passed = mean >= threshold if gated else None
        if gated and not passed:
            excluded.append(key)
        classes[key] = {
            "yolo_id": cls,
            "support": count,
            "critical": critical,
            "gated": gated,
            "seed_recall": pair,
            "mean_recall": mean,
            "gate": threshold if gated else None,
            "passed": passed,
            "per_seed_ap50": [
                per_seed[str(s)]["exact_class_ap"]["per_class_ap50"].get(str(cls)) for s in SEEDS
            ],
            "per_seed_ap50_95": [
                per_seed[str(s)]["exact_class_ap"]["per_class_ap50_95"].get(str(cls)) for s in SEEDS
            ],
        }
    checks = {
        "map50": aggregate["map50"]["mean"] >= gates["map50"],
        "map50_95": aggregate["map50_95"]["mean"] >= gates["map50_95"],
        "agnostic_recall": aggregate["agnostic_recall"]["mean"] >= gates["agnostic_recall"],
        "fp_per_image": aggregate["fp_per_image"]["mean"] <= gates["fp_per_image"],
        "critical_classes": all(
            row["passed"] for row in classes.values() if row["critical"] and row["gated"]
        ),
    }
    return {
        "package": PACKAGE,
        "split": "synthetic_or_post_approval_test",
        "seeds": list(SEEDS),
        "images": len(by_seed[SEEDS[0]]),
        "ground_truth": sum(len(frame.gt_boxes) for frame in by_seed[SEEDS[0]]),
        "selection": selection,
        "per_seed": per_seed,
        "two_seed": aggregate,
        "per_class": classes,
        "excluded_from_simulated_behavior": excluded,
        "gate_checks_excluding_latency": checks,
        "paired_group_bootstrap": paired_group_ci(by_seed, conf, rounds=rounds),
        "sealed_test_accessed": False,
    }


def _real_test_roster(approved: Approved) -> list[tuple[Frame, Path]]:
    """Reachable only after the one-time access entry has been durably appended."""
    from PIL import Image

    contract.check_contract("test")
    image_root = contract.EXPORT_DIR / "images" / "test"
    label_root = contract.EXPORT_DIR / "labels" / "test"
    groups = contract.group_of()
    unknown = contract.unknown_boxes()
    images = sorted(
        path for path in image_root.iterdir() if path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )
    if not images or len({path.stem for path in images}) != len(images):
        raise RuntimeError("test image roster is empty or ambiguous")
    overlay = None
    if approved.label_overlay is not None:
        # This reviewed label payload is sealed too; resolve and read only after _open_once.
        overlay_path = pinned(contract.REPO_ROOT, approved.label_overlay, committed=False)
        overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
        if (
            not isinstance(overlay, dict)
            or set(overlay) != {path.stem for path in images}
            or any(
                not isinstance(lines, list) or any(not isinstance(line, str) for line in lines)
                for lines in overlay.values()
            )
        ):
            raise RuntimeError("reviewed label roster differs from image roster")
    roster = []
    for path in images:
        with Image.open(path) as image:
            width, height = image.size
        label_lines = (
            overlay[path.stem]
            if overlay is not None
            else (label_root / f"{path.stem}.txt").read_text(encoding="utf-8").splitlines()
        )
        rows = [line.split() for line in label_lines if line.strip()]
        normalized = np.asarray(
            [[float(value) for value in row[1:]] for row in rows], dtype=float
        ).reshape(-1, 4)
        if len(normalized):
            boxes = np.column_stack(
                (
                    (normalized[:, 0] - normalized[:, 2] / 2) * width,
                    (normalized[:, 1] - normalized[:, 3] / 2) * height,
                    (normalized[:, 0] + normalized[:, 2] / 2) * width,
                    (normalized[:, 1] + normalized[:, 3] / 2) * height,
                )
            )
        else:
            boxes = np.zeros((0, 4), dtype=float)
        ignored = np.asarray(unknown.get(path.stem, []), dtype=float).reshape(-1, 4)
        if len(ignored):
            ignored = np.column_stack(
                (
                    (ignored[:, 0] - ignored[:, 2] / 2) * width,
                    (ignored[:, 1] - ignored[:, 3] / 2) * height,
                    (ignored[:, 0] + ignored[:, 2] / 2) * width,
                    (ignored[:, 1] + ignored[:, 3] / 2) * height,
                )
            )
        else:
            ignored = np.zeros((0, 4), dtype=float)
        roster.append(
            (
                Frame(
                    stem=path.stem,
                    group_id=groups[path.stem],
                    gt_boxes=boxes,
                    gt_classes=np.asarray([int(row[0]) for row in rows], dtype=int),
                    pred_boxes=np.zeros((0, 4), dtype=float),
                    pred_classes=np.zeros(0, dtype=int),
                    pred_scores=np.zeros(0, dtype=float),
                    image_width=width,
                    image_height=height,
                    unknown_boxes=ignored,
                ),
                path,
            )
        )
    return roster


def _real_predict(
    roster: list[tuple[Frame, Path]], weight: Path, selection: dict[str, Any]
) -> list[Frame]:
    """One prediction pass per weight over the already opened roster."""
    from ultralytics import YOLO

    contract.disable_telemetry()
    model = YOLO(str(weight))
    frames = []
    for base, path in roster:
        predictions = iter(
            model.predict(
                source=str(path),
                conf=0.001,
                iou=selection["nms_iou"],
                agnostic_nms=selection["agnostic_nms"],
                imgsz=1280,
                device="mps",
                max_det=300,
                stream=True,
                verbose=False,
            )
        )
        result = next(predictions, None)
        if result is None or next(predictions, None) is not None:
            raise RuntimeError("one image did not yield exactly one prediction result")
        boxes = result.boxes
        frames.append(
            replace(
                base,
                pred_boxes=boxes.xyxy.cpu().numpy(),
                pred_classes=boxes.cls.cpu().numpy().astype(int),
                pred_scores=boxes.conf.cpu().numpy(),
            )
        )
    return frames


def _atomic_write(path: Path, payload: bytes) -> None:
    """Publish one complete output file without exposing partial bytes."""
    if path.exists():
        raise RuntimeError(f"output already exists: {path}")
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as sink:
            temporary = Path(sink.name)
            sink.write(payload)
            sink.flush()
            os.fsync(sink.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _save_predictions(
    frames: list[Frame], weight: dict[str, Any], selection: dict[str, Any],
    output_dir: Path, split: str,
) -> dict[str, Any]:
    rows = [
        {
            "stem": frame.stem,
            "class": int(cls),
            "confidence": float(conf),
            "box": [float(value) for value in box],
        }
        for frame in frames
        for box, cls, conf in zip(
            frame.pred_boxes, frame.pred_classes, frame.pred_scores, strict=True
        )
    ]
    name = f"predictions_seed_{weight['seed']}.json"
    payload = {
        "split": split,
        "seed": weight["seed"],
        "weight_sha256": weight["sha256"],
        "selection": selection,
        "images": len(frames),
        "predictions": rows,
    }
    prediction_path = output_dir / name
    _atomic_write(prediction_path, json.dumps(payload, indent=2, allow_nan=False).encode() + b"\n")
    record = {
        "path": name,
        "sha256": sha256(prediction_path),
        "weight_sha256": weight["sha256"],
        "images": len(frames),
        "boxes": len(rows),
    }
    _atomic_write(
        output_dir / f"predictions_seed_{weight['seed']}_manifest.json",
        json.dumps(record, indent=2, allow_nan=False).encode() + b"\n",
    )
    return record


def _predict_score_report(
    roster: list[tuple[Frame, Path]],
    weights: tuple[dict[str, Any], dict[str, Any]],
    selection: dict[str, Any],
    gates: dict[str, float | int],
    output_dir: Path,
    *,
    split: str,
    label_mode: str,
    plan_sha256: str,
    final_contract_sha256: str | None,
    latency: dict[str, Any] | None,
    access_event: dict[str, Any] | None,
    access_log_sha256: str | None,
) -> dict[str, Any]:
    """Shared post-opening path; validation rehearsal supplies only validation inputs."""
    if split not in {"test", "val"} or {row["seed"] for row in weights} != set(SEEDS):
        raise RuntimeError("post-opening seed or split differs")
    output_dir.mkdir(parents=True, exist_ok=False)
    by_seed: dict[int, list[Frame]] = {}
    prediction_records = []
    for row in sorted(weights, key=lambda item: item["seed"]):
        weight_path = Path(row["path"])
        if not weight_path.is_absolute():
            weight_path = contract.REPO_ROOT / weight_path
        frames = _real_predict(roster, weight_path, selection)
        by_seed[row["seed"]] = frames
        prediction_records.append(_save_predictions(frames, row, selection, output_dir, split))
    scored = score_two_seeds(by_seed, selection, gates, contract.class_ids())
    latency_gate = (
        latency["two_seed_mean_p95_ms"] <= gates["latency_p95_ms"]
        if latency is not None else None
    )
    scored.update(
        split=split,
        label_mode=label_mode,
        latency=latency,
        latency_gate_pass=latency_gate,
        final_gate_pass=(
            all(scored["gate_checks_excluding_latency"].values()) and latency_gate
            if latency_gate is not None else None
        ),
        plan_sha256=plan_sha256,
        final_contract_sha256=final_contract_sha256,
        access_event=access_event,
        access_log_sha256=access_log_sha256,
        candidate_weights=[{"seed": row["seed"], "sha256": row["sha256"]} for row in weights],
        prediction_artifacts=prediction_records,
        sealed_test_accessed=split == "test",
    )
    _atomic_write(
        output_dir / "d1_final_evaluation_r1.json",
        json.dumps(scored, indent=2, allow_nan=False).encode() + b"\n",
    )
    _atomic_write(output_dir / "d1_final_evaluation_r1.md", _markdown(scored).encode())
    return scored


def _validation_roster_from_manifest(
    bases: list[Frame], bundle: Path, manifest: dict[str, Any]
) -> list[tuple[Frame, Path]]:
    """Bind each validation stem to its verified image member, preserving its suffix."""
    members = manifest.get("members")
    if not isinstance(members, dict):
        raise RuntimeError("validation bundle members are absent")
    prefix = "data/images/val/"
    images: dict[str, Path] = {}
    for name in members:
        if not name.startswith(prefix):
            continue
        filename = name[len(prefix):]
        candidate = Path(filename)
        if (
            not filename
            or candidate.name != filename
            or candidate.suffix.lower() not in {".jpg", ".png"}
            or candidate.stem in images
        ):
            raise RuntimeError("validation image member is ambiguous or unsupported")
        image_path = bundle / name
        if image_path.is_symlink() or not image_path.is_file():
            raise RuntimeError("validation image member is absent or a symlink")
        images[candidate.stem] = image_path
    stems = [frame.stem for frame in bases]
    if len(stems) != len(set(stems)) or set(stems) != set(images):
        raise RuntimeError("validation image roster differs from the pinned manifest")
    return [(frame, images[frame.stem]) for frame in bases]


def rehearse_validation(plan_path: Path) -> dict[str, Any]:
    """Run the post-opening scoring path on the pinned R3 validation bundle only."""
    import torch

    from m1.d1_threshold_lock_r3_successor import _bundle, read_for_final

    root = contract.REPO_ROOT
    if Path.cwd() != root / "detector" or plan_path.as_posix() != (
        "docs/review/generated/d1_final_evaluation_r4_plan.json"
    ):
        raise RuntimeError("validation rehearsal requires detector CWD and the R4 plan")
    plan_target = _relative(root, plan_path.as_posix())
    plan = json.loads(plan_target.read_text(encoding="utf-8"))
    if (
        plan.get("package") != PACKAGE
        or plan.get("sealed_test_accessed") is not False
        or plan.get("bundle", {}).get("path") != "tmp/yolo11n_n1_extract_r2/manifest.json"
        or plan.get("source_sha256", {}).get("detector/m1/d1_final_evaluation_r1.py")
        != sha256(Path(__file__))
        or not torch.backends.mps.is_available()
    ):
        raise RuntimeError("R4 validation rehearsal pins or MPS differ")
    manifest = pinned(root, plan["bundle"], committed=False)
    bundle = manifest.parent
    bases, _bundle_proof = _bundle(bundle)
    bundle_record = json.loads(manifest.read_text(encoding="utf-8"))
    lock_path = pinned(root, plan["lock_record"], committed=True)
    proof_path = pinned(root, plan["lock_proof"], committed=True)
    lock_record = json.loads(lock_path.read_text(encoding="utf-8"))
    relative_proof = Path(lock_record["proof"]["path"])
    if (
        not relative_proof.samefile(proof_path)
        or sha256(relative_proof) != plan["lock_proof"]["sha256"]
    ):
        raise RuntimeError("validation rehearsal proof path differs")
    lock_qa = {**plan["lock_result_qa"], "path": str(pinned(root, plan["lock_result_qa"]))}
    owner_lock = {
        **plan["owner_lock_approval"],
        "path": str(pinned(root, plan["owner_lock_approval"])),
    }
    weights = tuple(sorted(plan["weights"], key=lambda item: item["seed"]))
    settings = []
    for row in weights:
        weight = _relative(root, row["path"])
        if weight.is_symlink() or sha256(weight) != row["sha256"]:
            raise RuntimeError("validation rehearsal weight differs")
        settings.append(read_for_final(
            Path("..") / plan["lock_record"]["path"], relative_proof, bundle, root,
            row["sha256"], lock_qa, owner_lock,
        ))
    if settings != [
        {"conf": 0.19, "nms_iou": 0.70, "agnostic_nms": False}
    ] * 2:
        raise RuntimeError("validation rehearsal lock setting differs")
    q4 = json.loads(pinned(root, plan["q4_decision"]).read_text(encoding="utf-8"))
    gates = _decision_gates(q4)
    output_dir = root / "results/experiments/d1_final_evaluation_r4_rehearsal_val"
    roster = _validation_roster_from_manifest(bases, bundle, bundle_record)
    scored = _predict_score_report(
        roster, weights, settings[0], gates, output_dir,
        split="val", label_mode="VALIDATION_R3", plan_sha256=sha256(plan_target),
        final_contract_sha256=None, latency=None, access_event=None, access_log_sha256=None,
    )
    points = [scored["per_seed"][str(seed)]["operating_point"] for seed in SEEDS]
    expected = ((555, 155), (512, 131))
    if any(abs(point["true_positives"] - tp) > 2 or abs(point["false_positives"] - fp) > 2
           for point, (tp, fp) in zip(points, expected, strict=True)):
        raise RuntimeError("validation rehearsal differs from R3 lock operating point")
    return scored


def _real_latency(
    weights: tuple[dict[str, Any], dict[str, Any]], selection: dict[str, Any]
) -> dict[str, Any]:
    """Q5 uses validation images, never the test roster."""
    import torch
    import ultralytics
    from ultralytics import YOLO

    hardware = subprocess.run(
        ["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True, check=False
    )
    if (
        hardware.returncode
        or "Apple M1 Pro" not in hardware.stdout
        or not torch.backends.mps.is_available()
    ):
        raise RuntimeError("Q5 requires an available Apple M1 Pro MPS runtime")
    validation = sorted((contract.EXPORT_DIR / "images" / "val").glob("*.jpg"))
    if not validation:
        raise RuntimeError("Q5 validation images are unavailable")
    timings = {}
    for row in weights:
        model = YOLO(str(row["path"]))
        measured = []
        for index in range(contract.LATENCY_WARMUP + contract.LATENCY_ITERATIONS):
            path = validation[index % len(validation)]
            start = time.perf_counter()
            model.predict(
                source=str(path),
                conf=selection["conf"],
                iou=selection["nms_iou"],
                agnostic_nms=selection["agnostic_nms"],
                imgsz=1280,
                device="mps",
                batch=1,
                max_det=300,
                verbose=False,
            )
            torch.mps.synchronize()
            if index >= contract.LATENCY_WARMUP:
                measured.append((time.perf_counter() - start) * 1000)
        timings[str(row["seed"])] = latency_stats(measured)
    mean_p95 = sum(item["p95_ms"] for item in timings.values()) / 2
    return {
        "hardware": hardware.stdout.strip(),
        "device": "mps",
        "batch": 1,
        "warmup": 50,
        "iterations": 300,
        "imgsz": 1280,
        "torch": torch.__version__,
        "ultralytics": ultralytics.__version__,
        "per_seed": timings,
        "two_seed_mean_p95_ms": mean_p95,
    }


def _open_once(approved: Approved) -> dict[str, Any]:
    """Append the access marker under a process lock before any sealed read."""
    if approved.test_export.is_symlink() or not approved.test_export.is_file():
        raise RuntimeError("test export data_test.yaml is absent")
    approved.access_log.parent.mkdir(parents=True, exist_ok=True)
    lock_path = approved.access_log.with_name(approved.access_log.name + ".lock")
    if lock_path.is_symlink():
        raise RuntimeError("access lock is a symlink")
    with lock_path.open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            if approved.test_export.is_symlink() or not approved.test_export.is_file():
                raise RuntimeError("test export data_test.yaml is absent")
            _check_prior_openings(approved.access_log)
            contract.log_test_access(
                ACCESS_ACTION,
                f"{approved.reason} | plan_sha256={approved.plan_sha256} | "
                f"contract_sha256={approved.final_contract_sha256}",
            )
            entries = _read_access_log(approved.access_log)
            if not entries or entries[-1].get("action") != ACCESS_ACTION:
                raise RuntimeError("append-only access marker was not observed")
            return entries[-1]
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def _markdown(result: dict[str, Any]) -> str:
    rows = [
        "# D1 final evaluation — validation rehearsal" if result["split"] == "val"
        else "# D1 final evaluation — one-time result",
        "",
        "Two fixed seeds; the same validation-locked confidence and NMS setting was used.",
        "The D-02 group bootstrap keeps both weights fixed and does not estimate "
        "training-seed uncertainty.",
        "",
        "| Q2 measure | Seed 20261018 | Seed 20261019 | Mean | Gate pass |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for key in ("map50", "map50_95", "agnostic_recall", "fp_per_image"):
        item = result["two_seed"][key]
        rows.append(
            f"| {key} | {item['seed_20261018']:.6f} | {item['seed_20261019']:.6f} | "
            f"{item['mean']:.6f} | {result['gate_checks_excluding_latency'][key]} |"
        )
    if result["latency"] is None:
        latency_line = "- Q5 latency and final verdict: not measured in validation rehearsal."
    else:
        latency_line = (
            f"- Q5 two-seed mean p95: {result['latency']['two_seed_mean_p95_ms']:.3f} ms; "
            f"pass: {result['latency_gate_pass']}."
        )
    rows += [
        "",
        f"- Q2 critical classes pass: "
        f"{result['gate_checks_excluding_latency']['critical_classes']}.",
        latency_line,
        f"- Overall D-05 gate: {result['final_gate_pass']}.",
        f"- Classes excluded from simulated behavior: "
        f"{', '.join(result['excluded_from_simulated_behavior']) or 'none'}.",
        "- AP-small, resolution breakdown, low-support classes, confusion matrices, "
        "per-class AP/recall, errors and CI are in the paired JSON.",
        "- Result QA is required before publication or any acceptance claim.",
        "",
        f"`sealed_test_accessed={str(result['sealed_test_accessed']).lower()}`.",
        "",
    ]
    return "\n".join(rows)


def execute(plan_path: Path) -> dict[str, Any]:
    """Future real entry point. Current work must not invoke this function."""
    approved = preflight(plan_path)
    latency = _real_latency(approved.weights, approved.selection)
    # Recheck mutable prerequisites after the lengthy validation-only Q5 loop.
    if preflight(plan_path) != approved:
        raise RuntimeError("preflight inputs changed during latency measurement")
    event = _open_once(approved)
    roster = _real_test_roster(approved)
    return _predict_score_report(
        roster, approved.weights, approved.selection, approved.gates, approved.output_dir,
        split="test", label_mode=approved.label_mode, plan_sha256=approved.plan_sha256,
        final_contract_sha256=approved.final_contract_sha256, latency=latency,
        access_event=event, access_log_sha256=sha256(approved.access_log),
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--rehearse-validation", action="store_true")
    args = parser.parse_args(argv)
    if args.rehearse_validation:
        rehearse_validation(args.plan)
    else:
        execute(args.plan)


if __name__ == "__main__":
    main()
