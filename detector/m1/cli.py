"""M1 training/evaluation CLI for the Vietnamese traffic-sign detector (track D1).

Run from `detector/`:

    uv run python -m m1.cli check
    uv run python -m m1.cli train --seed 20261018 --model yolo11n.yaml --epochs 100
    uv run python -m m1.cli evaluate --weights <run>/weights/best.pt --split val
    uv run python -m m1.cli latency --weights <run>/weights/best.pt

Every run first checks the governed contract (D-05 record, M1 export manifest, exported stems).
Train/val use `data.yaml`, which has no test entry. `evaluate --split test` needs `--final-eval
--reason` and is logged in the sealed-test access log. Horizontal flip is forced to 0.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

from m1 import contract
from m1.metrics import (
    Frame,
    ap_small,
    confusion_matrix,
    error_samples,
    group_bootstrap,
    latency_stats,
    operating_point,
    resolution_breakdown,
    select_threshold,
    unknown_false_recognition,
)

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
METRIC_TOLERANCE = 1e-6


def run_name(model: str, seed: int, tag: str, seal: str) -> str:
    stem = Path(model).stem
    return f"D1_{stem}_wp33_{seal[:8]}_{seed}_{contract.now()}{('_' + tag) if tag else ''}"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def cmd_check(_args: argparse.Namespace) -> dict[str, Any]:
    return {
        "contract": contract.check_contract(),
        "environment": contract.environment(),
        "gates": contract.GATES,
    }


def cmd_train(args: argparse.Namespace) -> dict[str, Any]:
    if args.seed not in contract.SEEDS:
        raise SystemExit(f"seed {args.seed} is not one of the D-05 seeds {contract.SEEDS}")
    model_binding = contract.bind_training_model(args.model)
    bound = contract.check_contract()
    contract.disable_telemetry()
    from ultralytics import YOLO

    name = run_name(
        model_binding["path"], args.seed, args.tag, bound["split_stem_sha256"]["test"]
    )
    results_dir = Path(args.results_dir).resolve() if args.results_dir else contract.RESULTS_DIR
    out = results_dir / name
    if out.exists():
        raise SystemExit(f"run directory already exists: {out}")
    train_args = {
        "data": bound["data_yaml"],
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "device": args.device,
        "seed": args.seed,
        "deterministic": True,
        "workers": args.workers,
        "fraction": args.fraction,
        "patience": args.patience,
        "plots": args.plots,
        "project": str(results_dir),
        "name": name,
        "exist_ok": True,  # the run dir is new (checked above) and holds run_contract.json
        "pretrained": True,
        **contract.FORBIDDEN_OVERRIDES,
    }
    write_json(
        out / "run_contract.json",
        {
            "experiment": "D1",
            "run": name,
            "seed": args.seed,
            "model": model_binding,
            "train_args": train_args,
            "contract": bound,
            "environment": contract.environment(),
            "d05_gates": contract.GATES,
            "status": "STARTED",
        },
    )
    model = YOLO(model_binding["path"])
    model.train(**train_args)
    record = json.loads((out / "run_contract.json").read_text(encoding="utf-8"))
    weight_artifacts = {}
    for filename in ("best.pt", "last.pt"):
        path = out / "weights" / filename
        if not path.is_file():
            raise RuntimeError(f"training did not produce required weight: {path}")
        weight_artifacts[filename] = {
            "path": str(path),
            "sha256": contract.sha256_file(path),
        }
    record["artifacts"] = {"weights": weight_artifacts}
    record["status"] = "TRAINED"
    write_json(out / "run_contract.json", record)
    return {"run": name, "dir": str(out)}


def load_frames(
    split: str, weights: str, imgsz: int, device: str, nms_iou: float
) -> list[Frame]:
    from PIL import Image
    from ultralytics import YOLO

    images = sorted(
        p
        for p in (contract.EXPORT_DIR / "images" / split).iterdir()
        if p.suffix.lower() in IMAGE_SUFFIXES
    )
    groups = contract.group_of()
    unknown = contract.unknown_boxes()
    model = YOLO(weights)
    frames = []
    results = model.predict(
        source=[str(p) for p in images],
        conf=0.001,
        iou=nms_iou,
        imgsz=imgsz,
        device=device,
        max_det=300,
        stream=True,
        verbose=False,
    )
    for path, result in zip(images, results, strict=True):
        with Image.open(path) as image:
            width, height = image.size
        rows = [
            line.split()
            for line in (contract.EXPORT_DIR / "labels" / split / f"{path.stem}.txt")
            .read_text()
            .splitlines()
            if line.strip()
        ]
        gt = np.array([[float(v) for v in r[1:]] for r in rows]).reshape(-1, 4)
        xyxy = (
            np.column_stack(
                [
                    (gt[:, 0] - gt[:, 2] / 2) * width,
                    (gt[:, 1] - gt[:, 3] / 2) * height,
                    (gt[:, 0] + gt[:, 2] / 2) * width,
                    (gt[:, 1] + gt[:, 3] / 2) * height,
                ]
            )
            if len(gt)
            else np.zeros((0, 4))
        )
        boxes = result.boxes
        unknown_xywh = np.asarray(unknown.get(path.stem, []), dtype=float).reshape(-1, 4)
        unknown_xyxy = (
            np.column_stack(
                [
                    (unknown_xywh[:, 0] - unknown_xywh[:, 2] / 2) * width,
                    (unknown_xywh[:, 1] - unknown_xywh[:, 3] / 2) * height,
                    (unknown_xywh[:, 0] + unknown_xywh[:, 2] / 2) * width,
                    (unknown_xywh[:, 1] + unknown_xywh[:, 3] / 2) * height,
                ]
            )
            if len(unknown_xywh)
            else np.zeros((0, 4))
        )
        frames.append(
            Frame(
                stem=path.stem,
                group_id=groups[path.stem],
                gt_boxes=xyxy,
                gt_classes=np.array([int(r[0]) for r in rows], dtype=int),
                pred_boxes=boxes.xyxy.cpu().numpy(),
                pred_classes=boxes.cls.cpu().numpy().astype(int),
                pred_scores=boxes.conf.cpu().numpy(),
                image_width=width,
                image_height=height,
                unknown_boxes=unknown_xyxy,
            )
        )
    return frames


def gate_report(map50: float, map50_95: float, point: Any, ids: dict[str, int]) -> dict[str, Any]:
    gates = contract.GATES
    names = {v: k for k, v in ids.items()}
    critical = {ids[k] for k in contract.CRITICAL_KEYS}
    classes = {}
    for cls, recall in point.per_class_recall.items():
        support = point.per_class_support[cls]
        gated = support >= gates["min_support_for_class_gate"]
        threshold = (
            gates["critical_class_recall"] if cls in critical else gates["other_class_recall"]
        )
        classes[names[cls]] = {
            "hits": point.per_class_hits[cls],
            "recall": recall,
            "support": support,
            "critical": cls in critical,
            "gated": gated,
            "passed": (recall >= threshold) if gated else None,
        }
    checks = {
        "map50": map50 >= gates["map50"],
        "map50_95": map50_95 >= gates["map50_95"],
        "agnostic_recall": point.agnostic_recall >= gates["agnostic_recall"],
        "fp_per_image": point.fp_per_image <= gates["fp_per_image"],
        "critical_classes": all(
            c["passed"] for c in classes.values() if c["critical"] and c["gated"]
        ),
    }
    return {
        "single_seed_checks": checks,
        "single_seed_checks_passed": all(checks.values()),
        "final_verdict": None,
        "classes": classes,
        "unverified_classes": sorted(
            key for key, cls in ids.items() if cls not in point.per_class_support
        ),
        "low_support_classes": sorted(
            key for key, row in classes.items() if not row["gated"]
        ),
    }


def _unit_interval(name: str, value: float) -> None:
    if type(value) not in (int, float) or not np.isfinite(value) or not 0.0 <= value <= 1.0:
        raise SystemExit(f"{name} must be finite and between 0 and 1")


def _evaluation_preflight(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Validate every non-test input before a sealed-test access is logged or read."""
    _unit_interval("--nms-iou", args.nms_iou)
    if args.split != "test":
        if args.final_eval or args.reason.strip() or args.threshold_lock:
            raise SystemExit("final-eval options are valid only for the sealed test split")
        return contract.bind_run_weights(args.weights), None
    if not (args.final_eval and args.reason.strip()):
        raise SystemExit(
            "refused: the sealed test is evaluated only with --final-eval and --reason (D-05)"
        )
    if args.conf is None:
        raise SystemExit("--conf is required and must equal the committed val threshold lock")
    _unit_interval("--conf", args.conf)
    if not args.threshold_lock:
        raise SystemExit("--threshold-lock is required for the sealed test split")
    if not args.bootstrap:
        raise SystemExit("--bootstrap is required for the D-05 sealed-test report")
    weights = contract.bind_run_weights(args.weights)
    locked = contract.bind_threshold_lock(args.threshold_lock, weights)
    if abs(args.conf - locked["conf"]) > 1e-12:
        raise SystemExit("--conf differs from the committed val threshold lock")
    if abs(args.nms_iou - locked["nms_iou"]) > 1e-12:
        raise SystemExit("--nms-iou differs from the committed val threshold lock")
    return weights, locked


def cmd_evaluate(args: argparse.Namespace) -> dict[str, Any]:
    weight_binding, threshold_lock = _evaluation_preflight(args)
    if args.split == "test":
        contract.log_test_access(
            "evaluate",
            f"{args.reason.strip()} | weights_sha256={weight_binding['sha256']} | "
            f"threshold_lock_sha256={threshold_lock['sha256']}",
        )
    bound = contract.check_contract(args.split)
    contract.disable_telemetry()
    from ultralytics import YOLO

    validation = YOLO(weight_binding["path"]).val(
        data=bound["data_yaml"],
        split=args.split,
        imgsz=args.imgsz,
        device=args.device,
        conf=0.001,
        iou=args.nms_iou,
        plots=False,
        verbose=False,
        project=weight_binding["run_dir"],
        name=f"ultralytics_{args.split}",
        exist_ok=True,
    )
    frames = load_frames(
        args.split, weight_binding["path"], args.imgsz, args.device, args.nms_iou
    )
    if args.split == "val":
        point = select_threshold(frames, contract.GATES["agnostic_recall"])
    else:
        assert args.conf is not None
        point = operating_point(frames, args.conf)
    ids = contract.class_ids()
    names = {v: k for k, v in ids.items()}
    report = {
        "split": args.split,
        "seed": weight_binding["seed"],
        "weights": weight_binding,
        "threshold_lock": threshold_lock,
        "imgsz": args.imgsz,
        "nms_iou": args.nms_iou,
        "map50": float(validation.box.map50),
        "map50_95": float(validation.box.map),
        "ap_small": ap_small(frames),
        "per_class_ap50": {
            names[int(cls)]: float(validation.box.ap50[i])
            for i, cls in enumerate(validation.box.ap_class_index.tolist())
        },
        "operating_point": {
            "conf": point.conf,
            "precision": point.precision,
            "agnostic_recall": point.agnostic_recall,
            "fp_per_image": point.fp_per_image,
            "images": point.images,
            "ground_truth": point.ground_truth,
            "true_positives": point.true_positives,
            "false_positives": point.false_positives,
        },
        "resolution_breakdown": resolution_breakdown(frames, point.conf),
        "unknown_false_recognition": unknown_false_recognition(frames, point.conf),
        "confusion_matrix": {
            "labels": [names[index] for index in range(len(names))] + ["BACKGROUND"],
            "rows_gt_cols_pred": confusion_matrix(frames, point.conf, len(names)),
        },
        "error_samples": error_samples(frames, point.conf),
        "ci95_group_bootstrap": group_bootstrap(frames, point.conf) if args.bootstrap else None,
        "gates": gate_report(float(validation.box.map50), float(validation.box.map), point, ids),
        "note": "val is indicative; D-05 gates are judged on the sealed test (3-seed mean)",
    }
    out = Path(weight_binding["run_dir"]) / f"eval_{args.split}.json"
    write_json(out, report)
    return {
        "report": str(out),
        "map50": report["map50"],
        "operating_point": report["operating_point"],
        "all_gates_passed": None,
        "note": "A single seed cannot produce the D-05 final verdict; aggregate exactly 3 seeds.",
    }


def cmd_latency(args: argparse.Namespace) -> dict[str, Any]:
    weight_binding = contract.bind_run_weights(args.weights)
    _unit_interval("--conf", args.conf)
    _unit_interval("--nms-iou", args.nms_iou)
    threshold_lock = None
    if args.threshold_lock:
        threshold_lock = contract.bind_threshold_lock(args.threshold_lock, weight_binding)
        if abs(args.conf - threshold_lock["conf"]) > 1e-12:
            raise RuntimeError("latency confidence differs from the committed threshold lock")
        if abs(args.nms_iou - threshold_lock["nms_iou"]) > 1e-12:
            raise RuntimeError("latency NMS differs from the committed threshold lock")
    contract.check_contract()
    contract.disable_telemetry()
    import torch
    from ultralytics import YOLO

    images = sorted((contract.EXPORT_DIR / "images" / "val").glob("*.jpg"))
    model = YOLO(weight_binding["path"])
    timings = []
    for index in range(contract.LATENCY_WARMUP + contract.LATENCY_ITERATIONS):
        path = str(images[index % len(images)])
        start = time.perf_counter()
        model.predict(
            path,
            imgsz=args.imgsz,
            conf=args.conf,
            iou=args.nms_iou,
            device=args.device,
            verbose=False,
        )
        if args.device == "mps":
            torch.mps.synchronize()
        if index >= contract.LATENCY_WARMUP:
            timings.append((time.perf_counter() - start) * 1000)
    stats = latency_stats(timings)
    stats.update(
        device=args.device,
        imgsz=args.imgsz,
        batch=1,
        warmup=contract.LATENCY_WARMUP,
        passed=stats["p95_ms"] <= contract.GATES["latency_p95_ms"],
    )
    out = Path(weight_binding["run_dir"]) / f"latency_{args.device}.json"
    write_json(
        out,
        {
            **stats,
            "seed": weight_binding["seed"],
            "weights": weight_binding,
            "threshold_lock": threshold_lock,
            "conf": args.conf,
            "nms_iou": args.nms_iou,
            "environment": contract.environment(),
        },
    )
    return {"report": str(out), **stats}


def _read_json(path_value: str) -> tuple[Path, dict[str, Any]]:
    path = Path(path_value).expanduser().resolve()
    if not path.is_file():
        raise RuntimeError(f"JSON artifact is missing: {path}")
    payload = contract.strict_json(path)
    if not isinstance(payload, dict):
        raise RuntimeError(f"JSON artifact must contain an object: {path}")
    return path, payload


def cmd_register_runs(args: argparse.Namespace) -> dict[str, Any]:
    bound = contract.check_contract()
    entries = []
    if contract.RUN_REGISTRY.is_file():
        contract._require_git_tracked_clean(contract.RUN_REGISTRY, "existing run registry")
        current = contract.strict_json(contract.RUN_REGISTRY)
        entries.extend(current.get("entries", []))
    for weights in args.weights:
        claim = contract.inspect_run_weights(weights)
        entries.append(claim["attestation"])
    unique = {contract.canonical_sha256(entry): entry for entry in entries}
    payload = {
        "schema_version": 1,
        "status": "RUNS_REGISTERED",
        "approved_pretrained_sha256": contract.PRETRAINED_WEIGHTS_SHA256,
        "export_manifest_sha256": bound["export_manifest_sha256"],
        "detector_lock_sha256": contract.DETECTOR_LOCK_SHA256,
        "entries": sorted(unique.values(), key=lambda item: (item["seed"], item["run"])),
    }
    write_json(contract.RUN_REGISTRY, payload)
    return {
        "run_registry": str(contract.RUN_REGISTRY),
        "sha256": contract.sha256_file(contract.RUN_REGISTRY),
        "entries": len(payload["entries"]),
        "ready_for_evaluation": False,
        "next": "independently review and commit the registry unchanged before evaluation",
    }


def cmd_lock_thresholds(args: argparse.Namespace) -> dict[str, Any]:
    bound = contract.check_contract()
    candidates = []
    report_hashes = []
    for report_value in args.reports:
        path, report = _read_json(report_value)
        if report.get("split") != "val" or report.get("threshold_lock") is not None:
            raise RuntimeError(f"threshold input is not a val-only report: {path}")
        weight = contract.bind_run_weights(report["weights"]["path"])
        if weight["sha256"] != report["weights"].get("sha256"):
            raise RuntimeError(f"val report weight binding differs: {path}")
        if report.get("seed") != weight["seed"]:
            raise RuntimeError(f"val report seed differs from run binding: {path}")
        point = report["operating_point"]
        report_sha256 = contract.sha256_file(path)
        candidates.append(
            {
                "seed": weight["seed"],
                "weight_path": weight["path"],
                "weight_sha256": weight["sha256"],
                "run_contract_sha256": weight["run_contract_sha256"],
                "run_attestation_sha256": weight["run_attestation_sha256"],
                "conf": float(point["conf"]),
                "nms_iou": float(report["nms_iou"]),
                "val_report_sha256": report_sha256,
            }
        )
        report_hashes.append({"path": str(path), "sha256": report_sha256})
    if len(candidates) != 3 or {item["seed"] for item in candidates} != set(contract.SEEDS):
        raise RuntimeError("threshold lock requires exactly one val report for each D-05 seed")
    if len({item["weight_sha256"] for item in candidates}) != 3:
        raise RuntimeError("threshold lock requires three distinct run weights")
    payload = {
        "schema_version": 1,
        "status": "LOCKED_ON_VAL",
        "selection": "per-seed confidence selected on val for recall >= 0.85 with minimum FP/image",
        "test_seal_sha256": bound["split_stem_sha256"]["test"],
        "export_manifest_sha256": bound["export_manifest_sha256"],
        "candidates": sorted(candidates, key=lambda item: item["seed"]),
        "input_val_reports": sorted(report_hashes, key=lambda item: item["path"]),
        "sealed_test_seen": False,
    }
    out = Path(args.out).expanduser().resolve()
    try:
        out.relative_to(contract.REPO_ROOT)
    except ValueError as error:
        raise RuntimeError("threshold lock output must be inside the repository") from error
    write_json(out, payload)
    return {
        "threshold_lock": str(out),
        "sha256": contract.sha256_file(out),
        "ready_for_test": False,
        "next": "commit the lock unchanged before sealed-test access",
    }


def _mean_std(values: list[float]) -> dict[str, float]:
    if not values or any(
        type(value) not in (int, float) or not np.isfinite(value) for value in values
    ):
        raise RuntimeError("aggregate inputs must be finite real numbers, not booleans")
    data = np.asarray(values, dtype=float)
    return {"mean": float(data.mean()), "std_population": float(data.std(ddof=0))}


def _exact_object(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise RuntimeError(f"{label} schema differs: expected exactly {sorted(expected)}")
    return value


def _report_number(
    value: Any,
    label: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    if type(value) not in (int, float) or not np.isfinite(value):
        raise RuntimeError(f"{label} must be a finite real number, not a boolean")
    result = float(value)
    if minimum is not None and result < minimum:
        raise RuntimeError(f"{label} must be at least {minimum}")
    if maximum is not None and result > maximum:
        raise RuntimeError(f"{label} must be at most {maximum}")
    return result


def _report_rate(value: Any, label: str) -> float:
    return _report_number(value, label, minimum=0.0, maximum=1.0)


def _report_count(value: Any, label: str, *, positive: bool = False) -> int:
    minimum = 1 if positive else 0
    if type(value) is not int or value < minimum:
        qualifier = "positive" if positive else "non-negative"
        raise RuntimeError(f"{label} must be a {qualifier} integer, not a boolean")
    return value


def _report_bool(value: Any, label: str) -> bool:
    if type(value) is not bool:
        raise RuntimeError(f"{label} must be a boolean")
    return value


def _report_string(value: Any, label: str) -> str:
    if type(value) is not str or not value.strip():
        raise RuntimeError(f"{label} must be a non-empty string")
    return value


def _validate_interval(value: Any, label: str, *, rate: bool) -> None:
    if not isinstance(value, list) or len(value) != 2:
        raise RuntimeError(f"{label} must be a two-value JSON array")
    validator = _report_rate if rate else (
        lambda item, item_label: _report_number(item, item_label, minimum=0.0)
    )
    low = validator(value[0], f"{label}[0]")
    high = validator(value[1], f"{label}[1]")
    if low > high:
        raise RuntimeError(f"{label} lower bound exceeds its upper bound")


def _validate_test_report(
    path: Path, report: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    required = {
        "split",
        "seed",
        "weights",
        "threshold_lock",
        "imgsz",
        "nms_iou",
        "map50",
        "map50_95",
        "ap_small",
        "per_class_ap50",
        "operating_point",
        "resolution_breakdown",
        "unknown_false_recognition",
        "confusion_matrix",
        "error_samples",
        "ci95_group_bootstrap",
        "gates",
        "note",
    }
    _exact_object(report, required, f"test report {path}")
    if report["split"] != "test":
        raise RuntimeError(f"final aggregate accepts only test reports: {path}")
    weights = report["weights"]
    if not isinstance(weights, dict) or type(weights.get("path")) is not str:
        raise RuntimeError(f"test report has no run-weight binding: {path}")
    weight = contract.bind_run_weights(weights["path"])
    if weights != weight or report["seed"] != weight["seed"]:
        raise RuntimeError(f"test report seed/weight differs from run binding: {path}")
    lock = report["threshold_lock"]
    if not isinstance(lock, dict) or type(lock.get("path")) is not str:
        raise RuntimeError(f"test report has no threshold-lock binding: {path}")
    locked = contract.bind_threshold_lock(lock["path"], weight)
    if lock != locked:
        raise RuntimeError(f"test report threshold-lock binding differs: {path}")

    _report_count(report["seed"], f"test report seed: {path}", positive=True)
    _report_count(report["imgsz"], f"test report imgsz: {path}", positive=True)
    nms_iou = _report_rate(report["nms_iou"], f"test report nms_iou: {path}")
    map50 = _report_rate(report["map50"], f"test report map50: {path}")
    map50_95 = _report_rate(report["map50_95"], f"test report map50_95: {path}")
    if map50_95 > map50:
        raise RuntimeError(f"test report mAP50-95 exceeds mAP50: {path}")

    point = _exact_object(
        report["operating_point"],
        {
            "conf",
            "precision",
            "agnostic_recall",
            "fp_per_image",
            "images",
            "ground_truth",
            "true_positives",
            "false_positives",
        },
        f"test report operating point: {path}",
    )
    conf = _report_rate(point["conf"], f"test report confidence: {path}")
    precision = _report_rate(point["precision"], f"test report precision: {path}")
    recall = _report_rate(point["agnostic_recall"], f"test report recall: {path}")
    fp_per_image = _report_number(
        point["fp_per_image"], f"test report FP/image: {path}", minimum=0.0
    )
    point_images = _report_count(point["images"], f"test report image count: {path}", positive=True)
    point_support = _report_count(point["ground_truth"], f"test report GT count: {path}")
    point_hits = _report_count(point["true_positives"], f"test report TP count: {path}")
    point_fps = _report_count(point["false_positives"], f"test report FP count: {path}")
    if point_hits > point_support:
        raise RuntimeError(f"test report true positives exceed ground truth: {path}")
    expected_recall = point_hits / point_support if point_support else 0.0
    expected_precision = point_hits / (point_hits + point_fps) if point_hits + point_fps else 0.0
    expected_fp_per_image = point_fps / point_images
    if (
        abs(recall - expected_recall) > METRIC_TOLERANCE
        or abs(precision - expected_precision) > METRIC_TOLERANCE
        or abs(fp_per_image - expected_fp_per_image) > METRIC_TOLERANCE
    ):
        raise RuntimeError(f"test report operating-point metrics differ from counts: {path}")
    if conf != locked["conf"]:
        raise RuntimeError(f"test report confidence differs from threshold lock: {path}")
    if nms_iou != locked["nms_iou"]:
        raise RuntimeError(f"test report NMS differs from threshold lock: {path}")

    ap_small = _exact_object(
        report["ap_small"],
        {"value", "classes", "support", "method"},
        f"test report AP-small: {path}",
    )
    small_value = _report_rate(ap_small["value"], f"test report AP-small value: {path}")
    small_classes = _report_count(ap_small["classes"], f"test report AP-small classes: {path}")
    small_support = _report_count(ap_small["support"], f"test report AP-small support: {path}")
    if ap_small["method"] != "project_class_aware_101point_iou_0.50_0.95_original_area_lt_32sq":
        raise RuntimeError(f"test report AP-small method differs: {path}")
    if (small_classes == 0) != (small_support == 0) or (
        small_support == 0 and small_value != 0.0
    ):
        raise RuntimeError(f"test report AP-small value/classes/support are inconsistent: {path}")

    resolutions = report["resolution_breakdown"]
    if not isinstance(resolutions, dict) or not resolutions:
        raise RuntimeError(f"test report resolution breakdown is absent: {path}")
    resolution_totals = {
        "images": 0,
        "ground_truth": 0,
        "true_positives": 0,
        "false_positives": 0,
    }
    for resolution, row in resolutions.items():
        if type(resolution) is not str or len(parts := resolution.split("x")) != 2 or not all(
            part.isdigit() and int(part) > 0 for part in parts
        ):
            raise RuntimeError(f"test report resolution key is invalid: {resolution!r}")
        row = _exact_object(
            row,
            {
                "images",
                "ground_truth",
                "true_positives",
                "false_positives",
                "precision",
                "agnostic_recall",
                "fp_per_image",
            },
            f"test report resolution {resolution}: {path}",
        )
        images = _report_count(row["images"], f"resolution {resolution} images", positive=True)
        support = _report_count(row["ground_truth"], f"resolution {resolution} GT")
        hits = _report_count(row["true_positives"], f"resolution {resolution} TP")
        fps = _report_count(row["false_positives"], f"resolution {resolution} FP")
        row_precision = _report_rate(row["precision"], f"resolution {resolution} precision")
        row_recall = _report_rate(row["agnostic_recall"], f"resolution {resolution} recall")
        row_fp_per_image = _report_number(
            row["fp_per_image"], f"resolution {resolution} FP/image", minimum=0.0
        )
        if hits > support or (
            abs(row_recall - (hits / support if support else 0.0)) > METRIC_TOLERANCE
            or abs(row_precision - (hits / (hits + fps) if hits + fps else 0.0))
            > METRIC_TOLERANCE
            or abs(row_fp_per_image - fps / images) > METRIC_TOLERANCE
        ):
            raise RuntimeError(f"test report resolution {resolution} metrics differ from counts")
        for key, value in (
            ("images", images),
            ("ground_truth", support),
            ("true_positives", hits),
            ("false_positives", fps),
        ):
            resolution_totals[key] += value
    if resolution_totals != {
        "images": point_images,
        "ground_truth": point_support,
        "true_positives": point_hits,
        "false_positives": point_fps,
    }:
        raise RuntimeError(f"test report resolution totals differ from operating point: {path}")

    unknown = _exact_object(
        report["unknown_false_recognition"],
        {"support", "recognized_as_known", "rate"},
        f"test report UNKNOWN evidence: {path}",
    )
    unknown_support = _report_count(unknown["support"], f"UNKNOWN support: {path}")
    recognized = _report_count(
        unknown["recognized_as_known"], f"UNKNOWN recognized count: {path}"
    )
    if recognized > unknown_support:
        raise RuntimeError(f"UNKNOWN recognized count exceeds support: {path}")
    if unknown_support == 0:
        if unknown["rate"] is not None:
            raise RuntimeError(f"UNKNOWN rate must be null when support is zero: {path}")
    else:
        unknown_rate = _report_rate(unknown["rate"], f"UNKNOWN rate: {path}")
        if abs(unknown_rate - recognized / unknown_support) > 1e-12:
            raise RuntimeError(f"UNKNOWN rate differs from counts: {path}")

    ids = contract.class_ids()
    ordered_keys = [key for key, _index in sorted(ids.items(), key=lambda item: item[1])]
    confusion = _exact_object(
        report["confusion_matrix"],
        {"labels", "rows_gt_cols_pred"},
        f"test report confusion matrix: {path}",
    )
    expected_labels = ordered_keys + ["BACKGROUND"]
    if confusion["labels"] != expected_labels:
        raise RuntimeError(f"test report confusion labels differ: {path}")
    matrix = confusion["rows_gt_cols_pred"]
    if not isinstance(matrix, list) or len(matrix) != len(expected_labels):
        raise RuntimeError(f"test report confusion matrix shape differs: {path}")
    for row_index, row in enumerate(matrix):
        if not isinstance(row, list) or len(row) != len(expected_labels):
            raise RuntimeError(f"test report confusion row shape differs at {row_index}: {path}")
        for column_index, value in enumerate(row):
            _report_count(value, f"confusion[{row_index}][{column_index}]: {path}")
    support_by_key = {
        key: sum(matrix[index]) for index, key in enumerate(ordered_keys)
    }
    background = len(ordered_keys)
    matrix_support = sum(support_by_key.values())
    matrix_hits = sum(
        matrix[row][column]
        for row in range(background)
        for column in range(background)
    )
    matrix_fps = sum(matrix[background][column] for column in range(background))
    if (matrix_support, matrix_hits, matrix_fps) != (point_support, point_hits, point_fps):
        raise RuntimeError(f"test report confusion counts differ from operating point: {path}")
    observed_keys = {key for key, support in support_by_key.items() if support > 0}
    if small_classes > len(observed_keys) or small_support > sum(support_by_key.values()):
        raise RuntimeError(f"test report AP-small support exceeds test support: {path}")

    per_class_ap50 = report["per_class_ap50"]
    if not isinstance(per_class_ap50, dict) or set(per_class_ap50) != observed_keys:
        raise RuntimeError(f"test report per-class AP50 roster differs from support: {path}")
    ap50_values = [
        _report_rate(value, f"test report AP50 class {key}: {path}")
        for key, value in per_class_ap50.items()
    ]
    if abs(map50 - float(np.mean(ap50_values))) > METRIC_TOLERANCE:
        raise RuntimeError(f"test report mAP50 differs from per-class AP50 mean: {path}")

    errors = _exact_object(
        report["error_samples"],
        {"missed_sign", "wrong_class", "false_or_wrong_box"},
        f"test report error samples: {path}",
    )
    for category, stems in errors.items():
        if (
            not isinstance(stems, list)
            or len(stems) > 20
            or len(stems) != len(set(stems))
            or any(type(stem) is not str or not stem.strip() for stem in stems)
        ):
            raise RuntimeError(f"test report error samples are invalid for {category}: {path}")

    bootstrap = _exact_object(
        report["ci95_group_bootstrap"],
        {"agnostic_recall", "fp_per_image"},
        f"test report bootstrap evidence: {path}",
    )
    _validate_interval(bootstrap["agnostic_recall"], "bootstrap recall", rate=True)
    _validate_interval(bootstrap["fp_per_image"], "bootstrap FP/image", rate=False)

    gates = _exact_object(
        report["gates"],
        {
            "single_seed_checks",
            "single_seed_checks_passed",
            "final_verdict",
            "classes",
            "unverified_classes",
            "low_support_classes",
        },
        f"test report gates: {path}",
    )
    classes = gates["classes"]
    if not isinstance(classes, dict) or set(classes) != observed_keys:
        raise RuntimeError(f"test report class-gate roster differs from support: {path}")
    expected_low_support: list[str] = []
    critical_passed = True
    for key, row in classes.items():
        row = _exact_object(
            row,
            {"hits", "recall", "support", "critical", "gated", "passed"},
            f"test report class gate {key}: {path}",
        )
        class_recall = _report_rate(row["recall"], f"class {key} recall: {path}")
        hits = _report_count(row["hits"], f"class {key} hits: {path}")
        support = _report_count(row["support"], f"class {key} support: {path}")
        if (
            support != support_by_key[key]
            or hits > support
            or abs(class_recall - hits / support) > METRIC_TOLERANCE
        ):
            raise RuntimeError(f"test report class {key} counts/recall are inconsistent: {path}")
        critical = _report_bool(row["critical"], f"class {key} critical flag: {path}")
        gated = _report_bool(row["gated"], f"class {key} gated flag: {path}")
        expected_critical = key in contract.CRITICAL_KEYS
        expected_gated = support >= contract.GATES["min_support_for_class_gate"]
        threshold = (
            contract.GATES["critical_class_recall"]
            if expected_critical
            else contract.GATES["other_class_recall"]
        )
        expected_passed = class_recall >= threshold if expected_gated else None
        if (
            critical != expected_critical
            or gated != expected_gated
            or row["passed"] != expected_passed
        ):
            raise RuntimeError(f"test report class {key} gate row is inconsistent: {path}")
        if not gated:
            expected_low_support.append(key)
        if critical and gated:
            critical_passed = critical_passed and bool(expected_passed)

    expected_unverified = sorted(set(ids) - observed_keys)
    if gates["unverified_classes"] != expected_unverified:
        raise RuntimeError(f"test report unverified-class roster differs: {path}")
    if gates["low_support_classes"] != sorted(expected_low_support):
        raise RuntimeError(f"test report low-support roster differs: {path}")
    if gates["final_verdict"] is not None:
        raise RuntimeError(f"single-seed test report contains a final verdict: {path}")
    expected_checks = {
        "map50": map50 >= contract.GATES["map50"],
        "map50_95": map50_95 >= contract.GATES["map50_95"],
        "agnostic_recall": recall >= contract.GATES["agnostic_recall"],
        "fp_per_image": fp_per_image <= contract.GATES["fp_per_image"],
        "critical_classes": critical_passed,
    }
    checks = _exact_object(
        gates["single_seed_checks"],
        set(expected_checks),
        f"test report single-seed checks: {path}",
    )
    if any(
        _report_bool(checks[key], f"single-seed check {key}: {path}") != value
        for key, value in expected_checks.items()
    ):
        raise RuntimeError(f"test report single-seed checks differ from metrics: {path}")
    checks_passed = _report_bool(
        gates["single_seed_checks_passed"], f"single-seed verdict flag: {path}"
    )
    if checks_passed != all(expected_checks.values()):
        raise RuntimeError(f"test report single-seed verdict differs from checks: {path}")
    _report_string(report["note"], f"test report note: {path}")
    return weight, locked


def _validate_latency_report(
    path: Path, report: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    required = {
        "n",
        "mean_ms",
        "p50_ms",
        "p95_ms",
        "max_ms",
        "device",
        "imgsz",
        "batch",
        "warmup",
        "passed",
        "seed",
        "weights",
        "threshold_lock",
        "conf",
        "nms_iou",
        "environment",
    }
    _exact_object(report, required, f"latency report {path}")
    weights = report["weights"]
    if not isinstance(weights, dict) or type(weights.get("path")) is not str:
        raise RuntimeError(f"latency report has no run-weight binding: {path}")
    weight = contract.bind_run_weights(weights["path"])
    if weights != weight or report["seed"] != weight["seed"]:
        raise RuntimeError(f"latency report seed/weight differs from run binding: {path}")
    lock = report["threshold_lock"]
    if not isinstance(lock, dict) or type(lock.get("path")) is not str:
        raise RuntimeError(f"latency report has no threshold-lock binding: {path}")
    locked = contract.bind_threshold_lock(lock["path"], weight)
    if lock != locked:
        raise RuntimeError(f"latency report threshold-lock binding differs: {path}")
    conf = _report_rate(report["conf"], f"latency confidence: {path}")
    nms_iou = _report_rate(report["nms_iou"], f"latency NMS: {path}")
    if conf != locked["conf"] or nms_iou != locked["nms_iou"]:
        raise RuntimeError(f"latency report thresholds differ from committed lock: {path}")
    _report_count(report["seed"], f"latency seed: {path}", positive=True)
    if (
        _report_count(report["n"], f"latency count: {path}", positive=True)
        != contract.LATENCY_ITERATIONS
    ):
        raise RuntimeError(f"latency report must contain {contract.LATENCY_ITERATIONS} iterations")
    if _report_count(report["warmup"], f"latency warm-up: {path}") != contract.LATENCY_WARMUP:
        raise RuntimeError(f"latency report must contain {contract.LATENCY_WARMUP} warm-ups")
    if _report_count(report["batch"], f"latency batch: {path}", positive=True) != 1:
        raise RuntimeError(f"latency report must use batch 1: {path}")
    _report_count(report["imgsz"], f"latency imgsz: {path}", positive=True)
    mean = _report_number(report["mean_ms"], f"latency mean: {path}", minimum=0.0)
    p50 = _report_number(report["p50_ms"], f"latency p50: {path}", minimum=0.0)
    p95 = _report_number(report["p95_ms"], f"latency p95: {path}", minimum=0.0)
    maximum = _report_number(report["max_ms"], f"latency max: {path}", minimum=0.0)
    if p50 > p95 or p95 > maximum or mean > maximum:
        raise RuntimeError(f"latency report statistics are not ordered consistently: {path}")
    passed = _report_bool(report["passed"], f"latency passed flag: {path}")
    if passed != (p95 <= contract.GATES["latency_p95_ms"]):
        raise RuntimeError(f"latency passed flag differs from p95: {path}")
    environment = _exact_object(
        report["environment"],
        {
            "git_commit",
            "git_dirty_files",
            "detector_lock_sha256",
            "python",
            "platform",
            "machine",
            "hardware_chip",
            "torch",
            "ultralytics",
            "mps_available",
        },
        f"latency environment: {path}",
    )
    for key in (
        "git_commit",
        "python",
        "platform",
        "machine",
        "hardware_chip",
        "torch",
        "ultralytics",
    ):
        _report_string(environment[key], f"latency environment {key}: {path}")
    _report_count(environment["git_dirty_files"], f"latency environment dirty files: {path}")
    _report_bool(environment["mps_available"], f"latency environment MPS flag: {path}")
    if not (
        report["device"] == "mps"
        and environment.get("hardware_chip") == "Apple M1 Pro"
        and environment.get("machine") == "arm64"
        and environment.get("mps_available") is True
        and environment.get("detector_lock_sha256") == contract.DETECTOR_LOCK_SHA256
        and str(environment.get("platform", "")).startswith("macOS-")
    ):
        raise RuntimeError(f"latency report is not verified Apple M1 Pro MPS evidence: {path}")
    return weight, locked


def cmd_aggregate(args: argparse.Namespace) -> dict[str, Any]:
    reports = []
    input_reports = []
    report_bindings = []
    for value in args.reports:
        path, report = _read_json(value)
        weight, locked = _validate_test_report(path, report)
        reports.append(report)
        report_bindings.append((weight, locked))
        input_reports.append({"path": str(path), "sha256": contract.sha256_file(path)})
    if len(reports) != 3 or {report.get("seed") for report in reports} != set(contract.SEEDS):
        raise RuntimeError("final aggregate requires exactly the three D-05 seeds")
    if len({weight["sha256"] for weight, _lock in report_bindings}) != 3:
        raise RuntimeError("final aggregate requires three distinct weights")
    if len({weight["run_dir"] for weight, _lock in report_bindings}) != 3:
        raise RuntimeError("final aggregate requires three distinct run directories")
    if len({weight["run_attestation_sha256"] for weight, _lock in report_bindings}) != 3:
        raise RuntimeError("final aggregate requires three distinct run attestations")
    lock_hashes = {locked["sha256"] for _weight, locked in report_bindings}
    if len(lock_hashes) != 1 or None in lock_hashes:
        raise RuntimeError("three test reports must use the same committed threshold lock")
    class_rosters = {frozenset(report["gates"]["classes"]) for report in reports}
    unverified_rosters = {
        tuple(report["gates"]["unverified_classes"]) for report in reports
    }
    if len(class_rosters) != 1 or len(unverified_rosters) != 1:
        raise RuntimeError("three test reports have inconsistent class rosters")

    latency_reports = []
    input_latency_reports = []
    latency_bindings = []
    for value in args.latency_reports:
        path, report = _read_json(value)
        weight, locked = _validate_latency_report(path, report)
        latency_reports.append(report)
        latency_bindings.append((weight, locked))
        input_latency_reports.append({"path": str(path), "sha256": contract.sha256_file(path)})
    if len(latency_reports) != 3 or {
        report.get("seed") for report in latency_reports
    } != set(contract.SEEDS):
        raise RuntimeError("final aggregate requires one M1-Pro latency report per D-05 seed")
    if len({weight["sha256"] for weight, _lock in latency_bindings}) != 3:
        raise RuntimeError("final aggregate requires three distinct latency weights")
    if {locked["sha256"] for _weight, locked in latency_bindings} != lock_hashes:
        raise RuntimeError("latency reports must use the final committed threshold lock")
    if len({report["imgsz"] for report in reports}) != 1 or len(
        {report["imgsz"] for report in latency_reports}
    ) != 1:
        raise RuntimeError("all final test and latency reports must use one image size")
    latency_by_seed = {report["seed"]: report for report in latency_reports}
    for report in reports:
        latency = latency_by_seed[report["seed"]]
        if latency["weights"]["sha256"] != report["weights"]["sha256"]:
            raise RuntimeError("latency and test reports bind different weights")
        if (
            latency["threshold_lock"] != report["threshold_lock"]
            or latency["imgsz"] != report["imgsz"]
            or latency["conf"] != report["operating_point"]["conf"]
            or latency["nms_iou"] != report["nms_iou"]
        ):
            raise RuntimeError("latency and test reports use different final configurations")
        if latency.get("device") != "mps":
            raise RuntimeError("D-05 final latency must be measured on Apple M1 Pro MPS")

    metrics = {
        "map50": _mean_std([report["map50"] for report in reports]),
        "map50_95": _mean_std([report["map50_95"] for report in reports]),
        "ap_small": _mean_std([report["ap_small"]["value"] for report in reports]),
        "agnostic_recall": _mean_std(
            [report["operating_point"]["agnostic_recall"] for report in reports]
        ),
        "fp_per_image": _mean_std(
            [report["operating_point"]["fp_per_image"] for report in reports]
        ),
        "latency_p95_ms": _mean_std([report["p95_ms"] for report in latency_reports]),
    }
    class_keys = sorted(set().union(*(report["gates"]["classes"] for report in reports)))
    classes = {}
    for key in class_keys:
        rows = [report["gates"]["classes"].get(key) for report in reports]
        available = [row for row in rows if row is not None]
        supports = {row["support"] for row in available}
        if len(available) != 3 or len(supports) != 1:
            raise RuntimeError(f"class support is inconsistent across seeds: {key}")
        mean_recall = _mean_std([row["recall"] for row in available])
        sample = available[0]
        threshold = (
            contract.GATES["critical_class_recall"]
            if sample["critical"]
            else contract.GATES["other_class_recall"]
        )
        classes[key] = {
            "recall": mean_recall,
            "support": sample["support"],
            "critical": sample["critical"],
            "gated": sample["gated"],
            "passed": mean_recall["mean"] >= threshold if sample["gated"] else None,
        }
    checks = {
        "map50": metrics["map50"]["mean"] >= contract.GATES["map50"],
        "map50_95": metrics["map50_95"]["mean"] >= contract.GATES["map50_95"],
        "agnostic_recall": metrics["agnostic_recall"]["mean"]
        >= contract.GATES["agnostic_recall"],
        "fp_per_image": metrics["fp_per_image"]["mean"] <= contract.GATES["fp_per_image"],
        "critical_classes": all(
            row["passed"] for row in classes.values() if row["critical"] and row["gated"]
        ),
        "latency_p95_ms": metrics["latency_p95_ms"]["mean"]
        <= contract.GATES["latency_p95_ms"],
    }
    payload = {
        "status": "D1_FINAL_3_SEED_AGGREGATE",
        "seeds": list(contract.SEEDS),
        "threshold_lock_sha256": next(iter(lock_hashes)),
        "metrics_mean_std": metrics,
        "classes": classes,
        "unverified_classes": reports[0]["gates"]["unverified_classes"],
        "checks": checks,
        "all_gates_passed": all(checks.values()),
        "ordinary_class_failures_do_not_fail_global_gate": True,
        "safety_claim": False,
        "input_test_reports": sorted(input_reports, key=lambda item: item["path"]),
        "input_latency_reports": sorted(
            input_latency_reports, key=lambda item: item["path"]
        ),
    }
    out = Path(args.out).expanduser().resolve()
    write_json(out, payload)
    return {"report": str(out), "all_gates_passed": payload["all_gates_passed"]}


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("check")
    train = commands.add_parser("train")
    train.add_argument("--seed", type=int, required=True)
    train.add_argument(
        "--model",
        default=str(contract.PRETRAINED_WEIGHTS),
        help="exact local Owner-approved yolo11s.pt path",
    )
    train.add_argument("--epochs", type=int, default=100)
    train.add_argument("--imgsz", type=int, default=1280)
    train.add_argument("--batch", type=int, default=8)
    train.add_argument("--device", default="mps")
    train.add_argument("--workers", type=int, default=4)
    train.add_argument("--fraction", type=float, default=1.0)
    train.add_argument("--patience", type=int, default=30)
    train.add_argument("--plots", action="store_true")
    train.add_argument("--tag", default="")
    train.add_argument("--results-dir", default="", help="override for smoke runs")
    for name in ("evaluate", "latency"):
        command = commands.add_parser(name)
        command.add_argument("--weights", required=True)
        command.add_argument("--imgsz", type=int, default=1280)
        command.add_argument("--device", default="mps")
    commands.choices["evaluate"].add_argument("--split", choices=("val", "test"), default="val")
    commands.choices["evaluate"].add_argument("--conf", type=float)
    commands.choices["evaluate"].add_argument("--nms-iou", type=float, default=0.7)
    commands.choices["evaluate"].add_argument("--bootstrap", action="store_true")
    commands.choices["evaluate"].add_argument("--final-eval", action="store_true")
    commands.choices["evaluate"].add_argument("--reason", default="")
    commands.choices["evaluate"].add_argument("--threshold-lock", default="")
    commands.choices["latency"].add_argument("--conf", type=float, default=0.25)
    commands.choices["latency"].add_argument("--nms-iou", type=float, default=0.7)
    commands.choices["latency"].add_argument(
        "--threshold-lock",
        default="",
        help="committed final threshold lock; required for reports used by aggregate-final",
    )
    register = commands.add_parser("register-runs")
    register.add_argument("--weights", nargs="+", required=True)
    lock = commands.add_parser("lock-thresholds")
    lock.add_argument("--reports", nargs=3, required=True)
    lock.add_argument(
        "--out",
        default=str(contract.REPO_ROOT / "docs/review/generated/d1_threshold_lock.json"),
    )
    aggregate = commands.add_parser("aggregate-final")
    aggregate.add_argument("--reports", nargs=3, required=True)
    aggregate.add_argument("--latency-reports", nargs=3, required=True)
    aggregate.add_argument("--out", required=True)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    handler = {
        "check": cmd_check,
        "train": cmd_train,
        "evaluate": cmd_evaluate,
        "latency": cmd_latency,
        "register-runs": cmd_register_runs,
        "lock-thresholds": cmd_lock_thresholds,
        "aggregate-final": cmd_aggregate,
    }[args.command]
    try:
        result = handler(args)
    except RuntimeError as error:
        print(f"contract check failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
