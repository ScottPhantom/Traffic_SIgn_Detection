from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pytest

from m1 import cli, contract
from m1.metrics import Frame, latency_stats, match, operating_point, select_threshold


def frame(
    gt: list[list[float]],
    gt_cls: list[int],
    pred: list[list[float]],
    pred_cls: list[int],
    scores: list[float],
    group: str = "G1",
) -> Frame:
    return Frame(
        stem="x",
        group_id=group,
        gt_boxes=np.array(gt, dtype=float).reshape(-1, 4),
        gt_classes=np.array(gt_cls, dtype=int),
        pred_boxes=np.array(pred, dtype=float).reshape(-1, 4),
        pred_classes=np.array(pred_cls, dtype=int),
        pred_scores=np.array(scores, dtype=float),
    )


def test_class_aware_match_rejects_wrong_class_but_agnostic_accepts() -> None:
    f = frame([[0, 0, 10, 10]], [3], [[0, 0, 10, 10]], [5], [0.9])
    aware, aware_fp = match(f, 0.5, class_aware=True)
    agnostic, agnostic_fp = match(f, 0.5, class_aware=False)
    assert not aware[0] and aware_fp == 1
    assert agnostic[0] and agnostic_fp == 0


def test_duplicate_prediction_counts_as_false_positive() -> None:
    f = frame([[0, 0, 10, 10]], [1], [[0, 0, 10, 10], [1, 1, 10, 10]], [1, 1], [0.9, 0.8])
    matched, false_positives = match(f, 0.5, class_aware=True)
    assert matched.all() and false_positives == 1


def test_operating_point_and_threshold_selection() -> None:
    frames = [
        frame([[0, 0, 10, 10]], [1], [[0, 0, 10, 10]], [1], [0.9]),
        frame([[0, 0, 10, 10]], [2], [[0, 0, 10, 10], [50, 50, 60, 60]], [2, 2], [0.3, 0.2]),
    ]
    low = operating_point(frames, 0.1)
    assert low.agnostic_recall == 1.0 and low.fp_per_image == 0.5
    chosen = select_threshold(frames, 0.85, grid=[0.1, 0.25, 0.5])
    assert chosen.conf == 0.25 and chosen.fp_per_image == 0.0
    fallback = select_threshold(frames, 0.99, grid=[0.5, 0.95])
    assert fallback.agnostic_recall == 0.5


def test_latency_stats() -> None:
    stats = latency_stats(list(range(1, 101)))
    assert stats["n"] == 100 and stats["p95_ms"] == pytest.approx(95.05)


def test_contract_binds_d05_and_export() -> None:
    bound = contract.check_contract()
    assert bound["split_stem_sha256"]["test"].startswith("afa03d4b")
    assert contract.FORBIDDEN_OVERRIDES == {"fliplr": 0.0}
    assert set(contract.CRITICAL_KEYS) <= set(contract.class_ids())


def test_train_refuses_non_d05_seed() -> None:
    with pytest.raises(SystemExit, match="not one of the D-05 seeds"):
        cli.main(["train", "--seed", "1"])


def test_evaluate_test_refused_without_final_eval() -> None:
    with pytest.raises(SystemExit, match="refused"):
        cli.main(["evaluate", "--weights", "missing.pt", "--split", "test"])


def test_test_preflight_refuses_missing_conf_before_weight_or_test_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(_weights: str) -> dict[str, object]:
        raise AssertionError("weight binding must not run before argument validation")

    monkeypatch.setattr(contract, "bind_run_weights", forbidden)
    args = argparse.Namespace(
        split="test",
        final_eval=True,
        reason="synthetic",
        conf=None,
        nms_iou=0.7,
        threshold_lock="synthetic.json",
        bootstrap=True,
        weights="missing.pt",
    )
    with pytest.raises(SystemExit, match="--conf is required"):
        cli._evaluation_preflight(args)


def test_arbitrary_pretrained_weight_is_rejected(tmp_path: Path) -> None:
    arbitrary = tmp_path / "yolo11s.pt"
    arbitrary.write_bytes(b"not approved")
    with pytest.raises(RuntimeError, match="Owner-approved"):
        contract.bind_training_model(str(arbitrary))


def test_self_authored_run_contract_outside_registry_is_rejected(tmp_path: Path) -> None:
    run = tmp_path / "run"
    weights = run / "weights"
    weights.mkdir(parents=True)
    best = weights / "best.pt"
    best.write_bytes(b"trained checkpoint")
    (run / "run_contract.json").write_text(
        json.dumps(
            {
                "status": "TRAINED",
                "seed": 20261018,
                    "artifacts": {"weights": {"best.pt": {"sha256": "self-issued"}}},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="must be under"):
        contract.bind_run_weights(str(best))


def test_strict_json_rejects_nan_and_duplicate_keys(tmp_path: Path) -> None:
    payload = tmp_path / "bad.json"
    payload.write_text('{"conf": NaN}', encoding="utf-8")
    with pytest.raises(ValueError, match="non-finite"):
        contract.strict_json(payload)
    payload.write_text('{"seed": 1, "seed": 2}', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        contract.strict_json(payload)


def test_run_weight_requires_independent_registry_anchor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(contract, "RESULTS_DIR", tmp_path)
    bound = {
        "export_manifest_sha256": "export",
        "class_map_sha256": "classes",
        "split_stem_sha256": {"train": "train", "val": "val", "test": "test"},
        "data_yaml": "/colab/data.yaml",
    }
    monkeypatch.setattr(contract, "check_contract", lambda *_args: bound)
    run = tmp_path / "run"
    weights = run / "weights"
    weights.mkdir(parents=True)
    best, last = weights / "best.pt", weights / "last.pt"
    best.write_bytes(b"best")
    last.write_bytes(b"last")
    weight_records = {
        path.name: {"path": str(path), "sha256": contract.sha256_file(path)}
        for path in (best, last)
    }
    environment = {
        "git_commit": "commit",
        "git_dirty_files": 0,
        "detector_lock_sha256": contract.DETECTOR_LOCK_SHA256,
        "python": "3.12",
        "platform": "Linux",
        "machine": "x86_64",
        "hardware_chip": "UNKNOWN",
        "torch": "2.14.1",
        "ultralytics": "8.4.172",
        "mps_available": False,
        "cuda_available": True,
        "cuda_version": "13.0",
        "gpu_name": "NVIDIA L4",
        "nvidia_driver": "580.00",
        "runtime_backend": "cuda",
    }
    record = {
        "experiment": "D1",
        "run": "run",
        "seed": 20261018,
        "model": {
            "path": "/colab/yolo11s.pt",
            "sha256": contract.PRETRAINED_WEIGHTS_SHA256,
            "origin": "ultralytics/assets v8.4.0",
        },
        "train_args": {
            "data": bound["data_yaml"],
            "seed": 20261018,
            "deterministic": True,
            "pretrained": True,
            "fliplr": 0.0,
        },
        "contract": bound,
        "environment": environment,
        "d05_gates": contract.GATES,
        "status": "TRAINED",
        "artifacts": {"weights": weight_records},
    }
    (run / "run_contract.json").write_text(json.dumps(record), encoding="utf-8")
    claim = contract.inspect_run_weights(str(best))
    registry = tmp_path / "registry.json"
    monkeypatch.setattr(contract, "RUN_REGISTRY", registry)
    with pytest.raises(RuntimeError, match="inside the repository"):
        contract.bind_run_weights(str(best))
    registry.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": "RUNS_REGISTERED",
                "approved_pretrained_sha256": contract.PRETRAINED_WEIGHTS_SHA256,
                "export_manifest_sha256": bound["export_manifest_sha256"],
                "detector_lock_sha256": contract.DETECTOR_LOCK_SHA256,
                "entries": [claim["attestation"]],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(contract, "_require_git_tracked_clean", lambda *_args: None)
    assert contract.bind_run_weights(str(best))["run_attestation_sha256"] == claim[
        "run_attestation_sha256"
    ]
    last.write_bytes(b"tampered last checkpoint")
    with pytest.raises(RuntimeError, match="last.pt"):
        contract.inspect_run_weights(str(best))


def test_final_aggregate_rejects_one_weight_relabelled_as_three_seeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report_paths = []
    for seed in contract.SEEDS:
        path = tmp_path / f"test_{seed}.json"
        path.write_text(
            json.dumps({"split": "test", "seed": seed, "threshold_lock": {"sha256": "lock"}}),
            encoding="utf-8",
        )
        report_paths.append(str(path))
    same_weight = {
        "sha256": "one-weight",
        "run_dir": "one-run",
        "run_attestation_sha256": "one-attestation",
    }
    monkeypatch.setattr(
        cli,
        "_validate_test_report",
        lambda _path, _report: (same_weight, {"sha256": "lock"}),
    )
    args = argparse.Namespace(
        reports=report_paths,
        latency_reports=["unused-1", "unused-2", "unused-3"],
        out=str(tmp_path / "aggregate.json"),
    )
    with pytest.raises(RuntimeError, match="three distinct weights"):
        cli.cmd_aggregate(args)


def test_single_seed_gate_report_never_returns_final_verdict() -> None:
    point = operating_point(
        [frame([[0, 0, 10, 10]], [0], [[0, 0, 10, 10]], [0], [0.9])], 0.5
    )
    ids = {key: index for index, key in enumerate(contract.CRITICAL_KEYS)}
    report = cli.gate_report(1.0, 1.0, point, ids)
    assert report["final_verdict"] is None
    assert "all_passed" not in report


def valid_test_report() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    ids = contract.class_ids()
    ordered = [key for key, _index in sorted(ids.items(), key=lambda item: item[1])]
    labels = ordered + ["BACKGROUND"]
    matrix = [[0 for _column in labels] for _row in labels]
    matrix[ids["0"]][ids["0"]] = 20
    weight: dict[str, object] = {
        "path": "best.pt",
        "sha256": "weight-sha",
        "seed": contract.SEEDS[0],
        "run_dir": "run-0",
        "run_attestation_sha256": "attestation-0",
    }
    locked: dict[str, object] = {
        "path": "threshold-lock.json",
        "sha256": "lock-sha",
        "conf": 0.5,
        "nms_iou": 0.7,
        "candidate": {"seed": contract.SEEDS[0]},
    }
    report: dict[str, object] = {
        "split": "test",
        "seed": contract.SEEDS[0],
        "weights": weight,
        "threshold_lock": locked,
        "imgsz": 1280,
        "nms_iou": 0.7,
        "map50": 0.7,
        "map50_95": 0.5,
        "ap_small": {
            "value": 0.4,
            "classes": 1,
            "support": 20,
            "method": "project_class_aware_101point_iou_0.50_0.95_original_area_lt_32sq",
        },
        "per_class_ap50": {"0": 0.7},
        "operating_point": {
            "conf": 0.5,
            "precision": 1.0,
            "agnostic_recall": 1.0,
            "fp_per_image": 0.0,
            "images": 1,
            "ground_truth": 20,
            "true_positives": 20,
            "false_positives": 0,
        },
        "resolution_breakdown": {
            "960x540": {
                "images": 1,
                "ground_truth": 20,
                "true_positives": 20,
                "false_positives": 0,
                "precision": 1.0,
                "agnostic_recall": 1.0,
                "fp_per_image": 0.0,
            }
        },
        "unknown_false_recognition": {
            "support": 0,
            "recognized_as_known": 0,
            "rate": None,
        },
        "confusion_matrix": {"labels": labels, "rows_gt_cols_pred": matrix},
        "error_samples": {
            "missed_sign": [],
            "wrong_class": [],
            "false_or_wrong_box": [],
        },
        "ci95_group_bootstrap": {
            "agnostic_recall": [0.8, 0.95],
            "fp_per_image": [0.05, 0.2],
        },
        "gates": {
            "single_seed_checks": {
                "map50": True,
                "map50_95": True,
                "agnostic_recall": True,
                "fp_per_image": True,
                "critical_classes": True,
            },
            "single_seed_checks_passed": True,
            "final_verdict": None,
            "classes": {
                "0": {
                    "hits": 20,
                    "recall": 1.0,
                    "support": 20,
                    "critical": True,
                    "gated": True,
                    "passed": True,
                }
            },
            "unverified_classes": sorted(set(ids) - {"0"}),
            "low_support_classes": [],
        },
        "note": "Synthetic complete report for domain validation only.",
    }
    return report, weight, locked


def valid_latency_report(weight: dict[str, object]) -> dict[str, object]:
    return {
        "n": contract.LATENCY_ITERATIONS,
        "mean_ms": 30.0,
        "p50_ms": 28.0,
        "p95_ms": 40.0,
        "max_ms": 50.0,
        "device": "mps",
        "imgsz": 1280,
        "batch": 1,
        "warmup": contract.LATENCY_WARMUP,
        "passed": True,
        "seed": contract.SEEDS[0],
        "weights": weight,
        "threshold_lock": {
            "path": "threshold-lock.json",
            "sha256": "lock-sha",
            "conf": 0.5,
            "nms_iou": 0.7,
            "candidate": {"seed": contract.SEEDS[0]},
        },
        "conf": 0.5,
        "nms_iou": 0.7,
        "environment": {
            "git_commit": "abc123",
            "git_dirty_files": 0,
            "detector_lock_sha256": contract.DETECTOR_LOCK_SHA256,
            "python": "3.12.0",
            "platform": "macOS-26.0-arm64-arm-64bit",
            "machine": "arm64",
            "hardware_chip": "Apple M1 Pro",
            "torch": "2.14.1",
            "ultralytics": "8.4.172",
            "mps_available": True,
            "cuda_available": False,
            "cuda_version": None,
            "gpu_name": "Apple M1 Pro",
            "nvidia_driver": None,
            "runtime_backend": "mps",
        },
    }


def set_nested(payload: dict[str, object], path: tuple[str, ...], value: object) -> None:
    target = payload
    for key in path[:-1]:
        child = target[key]
        assert isinstance(child, dict)
        target = child
    target[path[-1]] = value


def bind_synthetic_report(
    monkeypatch: pytest.MonkeyPatch,
    weight: dict[str, object],
    locked: dict[str, object],
) -> None:
    monkeypatch.setattr(contract, "bind_run_weights", lambda _path: weight)
    monkeypatch.setattr(contract, "bind_threshold_lock", lambda _path, _weight: locked)


def test_final_report_and_latency_domain_positive_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report, weight, locked = valid_test_report()
    bind_synthetic_report(monkeypatch, weight, locked)
    assert cli._validate_test_report(tmp_path / "test.json", report) == (weight, locked)
    latency = valid_latency_report(weight)
    assert cli._validate_latency_report(tmp_path / "latency.json", latency) == (weight, locked)


def test_environment_contract_records_cuda_gpu_driver_and_rejects_contradictions() -> None:
    cuda = {
        "git_commit": "a" * 40,
        "git_dirty_files": 0,
        "detector_lock_sha256": contract.DETECTOR_LOCK_SHA256,
        "python": "3.12.0",
        "platform": "Linux-6-x86_64",
        "machine": "x86_64",
        "hardware_chip": "UNKNOWN",
        "torch": "2.14.1",
        "ultralytics": "8.4.172",
        "mps_available": False,
        "cuda_available": True,
        "cuda_version": "13.0",
        "gpu_name": "NVIDIA L4",
        "nvidia_driver": "580.00",
        "runtime_backend": "cuda",
    }
    assert contract.validate_environment_record(cuda, "synthetic", require_clean=True) is cuda
    cuda["nvidia_driver"] = None
    with pytest.raises(RuntimeError, match="must record CUDA"):
        contract.validate_environment_record(cuda, "synthetic")
    cuda["nvidia_driver"] = "UNKNOWN"
    with pytest.raises(RuntimeError, match="exact observed value"):
        contract.validate_environment_record(cuda, "synthetic")


@pytest.mark.parametrize(
    ("path", "invalid"),
    [
        *((field, value) for field in [("map50",)] for value in (-0.1, 1.1, float("inf"), True)),
        *(
            (field, value)
            for field in [("map50_95",)]
            for value in (-0.1, 1.1, float("inf"), True)
        ),
        *(
            (field, value)
            for field in [("ap_small", "value")]
            for value in (-0.1, 1.1, float("inf"), True)
        ),
        *(
            (field, value)
            for field in [("operating_point", "agnostic_recall")]
            for value in (-0.1, 1.1, float("inf"), True)
        ),
        *(
            (field, value)
            for field in [("gates", "classes", "0", "recall")]
            for value in (-0.1, 1.1, float("inf"), True)
        ),
        *(
            (field, value)
            for field in [("operating_point", "fp_per_image")]
            for value in (-0.1, float("inf"), True)
        ),
    ],
)
def test_final_report_rejects_invalid_aggregate_numeric_domains(
    path: tuple[str, ...],
    invalid: object,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report, weight, locked = valid_test_report()
    bind_synthetic_report(monkeypatch, weight, locked)
    set_nested(report, path, invalid)
    with pytest.raises(RuntimeError):
        cli._validate_test_report(tmp_path / "test.json", report)


@pytest.mark.parametrize("invalid", [-0.1, float("inf"), True])
def test_latency_report_rejects_invalid_p95_domain(
    invalid: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _report, weight, locked = valid_test_report()
    bind_synthetic_report(monkeypatch, weight, locked)
    latency = valid_latency_report(weight)
    latency["p95_ms"] = invalid
    with pytest.raises(RuntimeError):
        cli._validate_latency_report(tmp_path / "latency.json", latency)


@pytest.mark.parametrize(
    ("field", "invalid"),
    [
        ("conf", 0.4),
        ("nms_iou", 0.6),
        ("threshold_lock", None),
        (
            "threshold_lock",
            {
                "path": "threshold-lock.json",
                "sha256": "tampered",
                "conf": 0.5,
                "nms_iou": 0.7,
                "candidate": {"seed": contract.SEEDS[0]},
            },
        ),
    ],
)
def test_latency_report_rejects_unbound_or_changed_final_configuration(
    field: str,
    invalid: object,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _report, weight, locked = valid_test_report()
    bind_synthetic_report(monkeypatch, weight, locked)
    latency = valid_latency_report(weight)
    latency[field] = invalid
    with pytest.raises(RuntimeError):
        cli._validate_latency_report(tmp_path / "latency.json", latency)


def test_final_reports_reject_unknown_fields_and_exponent_overflow(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report, weight, locked = valid_test_report()
    bind_synthetic_report(monkeypatch, weight, locked)
    report["unexpected"] = "forbidden"
    with pytest.raises(RuntimeError, match="schema differs"):
        cli._validate_test_report(tmp_path / "unknown.json", report)

    report, _weight, _locked = valid_test_report()
    encoded = json.dumps(report)
    encoded = encoded.replace('"map50": 0.7', '"map50": 1e999')
    assert '"map50": 1e999' in encoded
    overflow_path = tmp_path / "overflow.json"
    overflow_path.write_text(encoded, encoding="utf-8")
    _path, overflow = cli._read_json(str(overflow_path))
    with pytest.raises(RuntimeError, match="finite"):
        cli._validate_test_report(overflow_path, overflow)

    latency = valid_latency_report(weight)
    latency["unexpected"] = "forbidden"
    with pytest.raises(RuntimeError, match="schema differs"):
        cli._validate_latency_report(tmp_path / "latency.json", latency)


def test_invalid_report_fails_before_aggregate_file_is_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report, weight, locked = valid_test_report()
    bind_synthetic_report(monkeypatch, weight, locked)
    report["map50"] = 2.0
    report_path = tmp_path / "invalid.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    out = tmp_path / "aggregate.json"
    args = argparse.Namespace(
        reports=[str(report_path)] * 3,
        latency_reports=[],
        out=str(out),
    )
    with pytest.raises(RuntimeError):
        cli.cmd_aggregate(args)
    assert not out.exists()


def test_final_report_rejects_confusion_and_metric_contradictions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report, weight, locked = valid_test_report()
    bind_synthetic_report(monkeypatch, weight, locked)
    matrix = report["confusion_matrix"]["rows_gt_cols_pred"]
    labels = report["confusion_matrix"]["labels"]
    matrix[0][0] = 0
    matrix[0][len(labels) - 1] = 20
    with pytest.raises(RuntimeError, match="confusion counts differ"):
        cli._validate_test_report(tmp_path / "miss-all.json", report)

    report, _weight, _locked = valid_test_report()
    report["per_class_ap50"]["0"] = 0.0
    with pytest.raises(RuntimeError, match="mAP50 differs"):
        cli._validate_test_report(tmp_path / "map-mismatch.json", report)

    report, _weight, _locked = valid_test_report()
    report["gates"]["classes"]["0"]["hits"] = 0
    with pytest.raises(RuntimeError, match="counts/recall are inconsistent"):
        cli._validate_test_report(tmp_path / "class-hit-mismatch.json", report)


def test_final_report_rejects_ap_small_and_resolution_count_contradictions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report, weight, locked = valid_test_report()
    bind_synthetic_report(monkeypatch, weight, locked)
    report["ap_small"].update({"value": 1.0, "classes": 0, "support": 0})
    with pytest.raises(RuntimeError, match="AP-small value/classes/support"):
        cli._validate_test_report(tmp_path / "ap-small.json", report)

    report, _weight, _locked = valid_test_report()
    report["resolution_breakdown"]["960x540"]["images"] = 2
    with pytest.raises(RuntimeError):
        cli._validate_test_report(tmp_path / "resolution.json", report)


@pytest.mark.parametrize(
    ("field", "invalid"),
    [
        ("imgsz", 32),
        ("conf", 0.4),
        ("nms_iou", 0.6),
        ("threshold_lock", {"sha256": "different-lock"}),
    ],
)
def test_aggregate_rejects_latency_configuration_mismatch_before_output(
    field: str,
    invalid: object,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    test_paths = []
    latency_paths = []
    bindings: dict[int, dict[str, object]] = {}
    for index, seed in enumerate(contract.SEEDS):
        weight = {
            "sha256": f"weight-{index}",
            "run_dir": f"run-{index}",
            "run_attestation_sha256": f"attestation-{index}",
        }
        bindings[seed] = weight
        test_report = {
            "seed": seed,
            "weights": {"sha256": weight["sha256"]},
            "threshold_lock": {"sha256": "lock"},
            "imgsz": 1280,
            "nms_iou": 0.7,
            "operating_point": {"conf": 0.5},
            "gates": {"classes": {}, "unverified_classes": []},
        }
        latency_report = {
            "seed": seed,
            "weights": {"sha256": weight["sha256"]},
            "threshold_lock": {"sha256": "lock"},
            "imgsz": 1280,
            "conf": 0.5,
            "nms_iou": 0.7,
            "device": "mps",
        }
        if index == 0:
            latency_report[field] = invalid
        test_path = tmp_path / f"test-{seed}.json"
        latency_path = tmp_path / f"latency-{seed}.json"
        test_path.write_text(json.dumps(test_report), encoding="utf-8")
        latency_path.write_text(json.dumps(latency_report), encoding="utf-8")
        test_paths.append(str(test_path))
        latency_paths.append(str(latency_path))

    monkeypatch.setattr(
        cli,
        "_validate_test_report",
        lambda _path, report: (bindings[report["seed"]], {"sha256": "lock"}),
    )
    monkeypatch.setattr(
        cli,
        "_validate_latency_report",
        lambda _path, report: (bindings[report["seed"]], {"sha256": "lock"}),
    )
    out = tmp_path / "aggregate.json"
    args = argparse.Namespace(
        reports=test_paths,
        latency_reports=latency_paths,
        out=str(out),
    )
    with pytest.raises(RuntimeError, match="image size|final configurations"):
        cli.cmd_aggregate(args)
    assert not out.exists()
