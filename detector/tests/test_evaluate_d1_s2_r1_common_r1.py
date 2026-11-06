"""Synthetic S2 attestation guards plus read-only pilot-R3 baseline reproduction."""

from __future__ import annotations

import copy
import json
import sys
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

import pytest

from m1 import contract

sys.path.insert(0, str(contract.DETECTOR_ROOT / "colab"))
import evaluate_d1_s2_r1_common_r1 as s2eval  # noqa: E402


def record(tmp_path: Path) -> tuple[dict, str, str, str]:
    run = "D1_yolo11s_wp33_afa03d4b_20261019_20261106T120000_s2_r1"
    checkout = "a" * 40
    auth = "b" * 64
    run_dir = tmp_path / "results/experiments" / run
    source = {
        "experiment": "D1-S2-R1",
        "run": run,
        "seed": 20261019,
        "status": "TRAINED",
        "pilot_run": s2eval.launcher.PILOT_RUN,
        "single_change": "seed",
        "pilot_contract_sha256": s2eval.launcher.PILOT_CONTRACT_SHA256,
        "owner_authorization": {
            "path": "docs/review/d1_s2_r1_owner_authorization_2026-11-06.md",
            "sha256": auth,
        },
        "sealed_test_accessed": False,
        "model": {
            "path": "/pretrained/yolo11s.pt",
            "sha256": s2eval.contract.PRETRAINED_WEIGHTS_SHA256,
            "origin": "approved",
        },
        "contract": {
            **s2eval.predecessor.GOVERNED_DATA_CONTRACT,
            "data_yaml": "/content/repo/data/processed/m1_yolo/data.yaml",
        },
        "d05_gates": s2eval.contract.GATES,
        "environment": {
            "runtime_backend": "cuda",
            "gpu_name": "NVIDIA L4",
            "git_commit": checkout,
            "git_dirty_files": 0,
        },
        "artifacts": {
            "weights": {
                name: {"path": str(run_dir / "weights" / name), "sha256": char * 64}
                for name, char in (("best.pt", "1"), ("last.pt", "2"))
            }
        },
        "train_args": s2eval.launcher.expected_train_args(
            run_dir, "/content/repo/data/processed/m1_yolo/data.yaml"
        ),
    }
    return source, run, checkout, auth


def test_s2_run_contract_attestation_matches_launcher_fields(monkeypatch, tmp_path: Path) -> None:
    source, run, checkout, auth = record(tmp_path)
    monkeypatch.setattr(s2eval.contract, "validate_environment_record", lambda *_a, **_k: None)
    claim = s2eval.verify_run_contract(source, run, checkout, auth)
    assert claim["experiment"] == "D1-S2-R1"
    assert claim["seed"] == 20261019
    assert claim["weights"] == {"best.pt": "1" * 64, "last.pt": "2" * 64}
    assert claim["owner_authorization_sha256"] == auth


def test_offline_attestation_matches_s2_launcher_formula(monkeypatch, tmp_path: Path) -> None:
    source, run, checkout, auth = record(tmp_path)
    run_dir = tmp_path / "results/experiments" / run
    weights_dir = run_dir / "weights"
    weights_dir.mkdir(parents=True)
    for name, payload in (("best.pt", b"best"), ("last.pt", b"last")):
        target = weights_dir / name
        target.write_bytes(payload)
        source["artifacts"]["weights"][name]["sha256"] = s2eval.sha256(target)
    contract_path = run_dir / "run_contract.json"
    contract_path.write_text(json.dumps(source, sort_keys=True) + "\n")
    monkeypatch.setattr(s2eval.contract, "validate_environment_record", lambda *_a, **_k: None)
    real = SimpleNamespace(
        RESULTS_DIR=tmp_path / "results/experiments",
        strict_json=lambda path: json.loads(path.read_text()),
        check_contract=lambda: source["contract"],
        PRETRAINED_WEIGHTS_SHA256=s2eval.contract.PRETRAINED_WEIGHTS_SHA256,
        DETECTOR_LOCK_SHA256=s2eval.contract.DETECTOR_LOCK_SHA256,
        GATES=s2eval.contract.GATES,
        validate_environment_record=lambda *_a, **_k: None,
        sha256_file=s2eval.sha256,
        canonical_sha256=s2eval.contract.canonical_sha256,
    )
    direct = s2eval.launcher.inspect_s2_run_weights(
        real, str(weights_dir / "best.pt"), source["owner_authorization"], checkout
    )
    offline = s2eval.verify_run_contract(source, run, checkout, auth)
    offline["run_contract_sha256"] = s2eval.sha256(contract_path)
    assert direct["attestation"] == offline
    assert direct["run_attestation_sha256"] == s2eval.contract.canonical_sha256(offline)


@pytest.mark.parametrize(
    "mutation",
    [
        ("experiment", "D1-A2-R1"),
        ("seed", 20261018),
        ("status", "STARTED"),
        ("single_change", "data"),
        ("sealed_test_accessed", True),
    ],
)
def test_s2_identity_mutations_fail_closed(monkeypatch, tmp_path: Path, mutation) -> None:
    source, run, checkout, auth = record(tmp_path)
    monkeypatch.setattr(s2eval.contract, "validate_environment_record", lambda *_a, **_k: None)
    source[mutation[0]] = mutation[1]
    with pytest.raises(RuntimeError, match="identity differs"):
        s2eval.verify_run_contract(source, run, checkout, auth)


def test_train_argument_mutation_fails_closed(monkeypatch, tmp_path: Path) -> None:
    source, run, checkout, auth = record(tmp_path)
    monkeypatch.setattr(s2eval.contract, "validate_environment_record", lambda *_a, **_k: None)
    source["train_args"]["batch"] = 8
    with pytest.raises(RuntimeError, match="train args differ"):
        s2eval.verify_run_contract(source, run, checkout, auth)


def test_data_yaml_mutation_fails_closed(monkeypatch, tmp_path: Path) -> None:
    source, run, checkout, auth = record(tmp_path)
    monkeypatch.setattr(s2eval.contract, "validate_environment_record", lambda *_a, **_k: None)
    source["contract"]["data_yaml"] = "/tmp/data.yaml"
    source["train_args"]["data"] = "/tmp/data.yaml"
    with pytest.raises(RuntimeError, match="data.yaml path differs"):
        s2eval.verify_run_contract(source, run, checkout, auth)


def test_dirty_checkout_fails_closed(monkeypatch, tmp_path: Path) -> None:
    source, run, checkout, auth = record(tmp_path)
    monkeypatch.setattr(s2eval.contract, "validate_environment_record", lambda *_a, **_k: None)
    source["environment"]["git_dirty_files"] = 1
    with pytest.raises(RuntimeError, match="clean L4"):
        s2eval.verify_run_contract(source, run, checkout, auth)


def test_early_stop_and_seal_fail_closed() -> None:
    source = {
        "status": "COMPLETED_EARLY_STOPPED",
        "completed_epoch": 46,
        "sealed_test_accessed": False,
        "run": "run",
    }
    with pytest.raises(RuntimeError, match="early-stopped"):
        s2eval.predecessor._check_outcome(source, "run", "S2")
    source = copy.deepcopy(source)
    source.update(status="COMPLETED", completed_epoch=100, sealed_test_accessed=True)
    with pytest.raises(RuntimeError, match="identity differs"):
        s2eval.predecessor._check_outcome(source, "run", "S2")


def test_evaluator_refuses_missing_s2_result_qa() -> None:
    args = Namespace(
        s2_result_qa_record=Path("docs/review/missing_s2_result_qa.md"),
        s2_result_qa_sha256="0" * 64,
        archive_sha256="1" * 64,
        manifest_sha256="2" * 64,
    )
    with pytest.raises(RuntimeError, match="record hash differs"):
        s2eval.verify_execution_prerequisites(args)


def test_pinned_pilot_r3_reproduces_qa_numbers() -> None:
    bundle = s2eval.contract.REPO_ROOT / "tmp/yolo11n_n1_extract_r2"
    s2eval.a3eval.verify_package(bundle, s2eval.BUNDLE_SHA256)
    from m1 import a3_pilot_paired_ci_r1 as ci
    from m1.metrics import operating_point

    frames = ci.with_predictions(ci.gt_frames(bundle), bundle / ci.PILOT_CSV, "yolo_id", "conf")
    point = operating_point(frames, 0.20)
    assert (point.true_positives, point.false_positives, sum(point.per_class_hits.values())) == (
        547,
        150,
        457,
    )
    scores = s2eval.common.average_precision(frames)
    assert abs(scores["map50"] - 0.8521) < 1e-4
    assert abs(scores["map50_95"] - 0.6089) < 1e-4
