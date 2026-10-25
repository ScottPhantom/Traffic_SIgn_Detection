from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


builder = load("test_yolo11n_n1_builder", "detector/colab/build_yolo11n_n1_bundle_r1.py")
runner = load("test_yolo11n_n1_runner", "detector/colab/run_yolo11n_n1_r1.py")


def write_package(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str]:
    root = tmp_path / "bundle"
    weight = root / "models/yolo11n.pt"
    weight.parent.mkdir(parents=True)
    weight.write_bytes(b"nano-weight-fixture")
    digest = hashlib.sha256(weight.read_bytes()).hexdigest()
    monkeypatch.setattr(runner, "WEIGHT_SHA256", digest)
    members = {
        "models/yolo11n.pt": {
            "bytes": weight.stat().st_size,
            "sha256": digest,
        }
    }
    manifest = {
        "schema": 1,
        "package": runner.PACKAGE,
        "architecture": "YOLO11n",
        "detector_classes": 1,
        "pretrained_weight_sha256": digest,
        "counts": runner.base.EXPECTED_COUNTS,
        "members": members,
        "test_included": False,
        "sealed_test_accessed": False,
        "ignore_subtraction": False,
        "train_val_overlap": False,
    }
    path = root / "manifest.json"
    path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    return root, runner.base.sha256_file(path)


def test_owner_frozen_n1_configuration() -> None:
    assert runner.CONFIG["architecture"] == "YOLO11n"
    assert runner.CONFIG["detector_epochs"] == 100
    assert runner.CONFIG["detector_batch"] == 4
    assert runner.CONFIG["imgsz"] == 1280
    assert runner.CONFIG["fliplr"] == 0.0
    assert runner.CONFIG["classifier"] == "reuse_existing_compactcnn_and_vgg16_54"


def test_n1_state_is_isolated_from_b0(tmp_path: Path) -> None:
    state = tmp_path / runner.EXPECTED_STATE_SUFFIX
    assert runner.normalized_state(state) == state.absolute()
    with pytest.raises(RuntimeError, match="requires state suffix"):
        runner.normalized_state(tmp_path / "M1_D1_Colab/runs/cascade_b0_seed_20261018_r1")


def test_verify_package_accepts_nano_and_rejects_yolo11s(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, digest = write_package(tmp_path, monkeypatch)
    observed = runner.verify_package(root, digest)
    assert observed["package"] == runner.PACKAGE
    assert observed["sealed_test_accessed"] is False
    legacy = root / "models/yolo11s.pt"
    legacy.write_bytes(b"forbidden")
    with pytest.raises(RuntimeError, match="roster differs|must not contain"):
        runner.verify_package(root, digest)


def test_verify_package_rejects_weight_hash_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, digest = write_package(tmp_path, monkeypatch)
    (root / "models/yolo11n.pt").write_bytes(b"tampered")
    with pytest.raises(RuntimeError, match="bytes differ|weight binding"):
        runner.verify_package(root, digest)


def test_builder_routes_nano_weight_without_legacy_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected_counts = {"train_images": 3712, "val_images": 376}
    monkeypatch.setattr(builder.base, "file_hash", lambda path: builder.WEIGHT_SHA256)
    monkeypatch.setattr(
        builder.base,
        "inputs",
        lambda: (
            {"models/yolo11s.pt": builder.WEIGHT},
            expected_counts,
        ),
    )
    monkeypatch.setattr(Path, "is_file", lambda self: True)
    monkeypatch.setattr(Path, "is_symlink", lambda self: False)
    members, counts = builder.inputs()
    assert counts == expected_counts
    assert members["models/yolo11n.pt"] == builder.WEIGHT
    assert "models/yolo11s.pt" not in members


def test_n1_source_has_no_sealed_test_route() -> None:
    source = (ROOT / "detector/colab/run_yolo11n_n1_r1.py").read_text(encoding="utf-8")
    assert "export-test" not in source
    assert "--final-eval" not in source
    assert 'choices=("check", "detector")' in source


def test_n1_source_qa_binds_successor_governance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "bundle"
    source = root / "detector/colab/run_yolo11n_n1_r1.py"
    decision = root / "docs/review/yolo11n_dual_track_r1_owner_decision_record.md"
    source.parent.mkdir(parents=True)
    decision.parent.mkdir(parents=True)
    source.write_text("runner", encoding="utf-8")
    decision.write_text("decision", encoding="utf-8")
    members = {
        source.relative_to(root).as_posix(): {},
        decision.relative_to(root).as_posix(): {},
    }
    (root / "manifest.json").write_text(json.dumps({"members": members}), encoding="utf-8")
    record = tmp_path / "qa.md"
    record.write_text(
        "Verdict: **PASS**\n"
        + hashlib.sha256(source.read_bytes()).hexdigest()
        + "\n"
        + hashlib.sha256(decision.read_bytes()).hexdigest()
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(runner.base, "require_source_qa", lambda *_args: None)
    runner.require_source_qa(
        root,
        record,
        hashlib.sha256(record.read_bytes()).hexdigest(),
    )
    record.write_text("Verdict: **PASS**\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="does not bind"):
        runner.require_source_qa(
            root,
            record,
            hashlib.sha256(record.read_bytes()).hexdigest(),
        )


def test_n1_long_run_requires_resume(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, digest = write_package(tmp_path, monkeypatch)
    state = tmp_path / runner.EXPECTED_STATE_SUFFIX
    monkeypatch.setattr(runner, "require_source_qa", lambda *_args: None)
    monkeypatch.setattr(runner, "require_long_run_qa", lambda *_args: None)
    with pytest.raises(RuntimeError, match="long run requires MODE=resume"):
        runner.main(
            [
                "detector",
                "--root",
                str(root),
                "--state",
                str(state),
                "--manifest-sha256",
                digest,
                "--mode",
                "fresh",
            ]
        )


def test_n1_long_proof_binds_state_and_checkpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = (tmp_path / runner.EXPECTED_STATE_SUFFIX).absolute()
    latest = state / "detector/recovery/latest.json"
    latest.parent.mkdir(parents=True)
    latest.write_text('{"generation":"epoch-0002"}\n', encoding="utf-8")
    proof = tmp_path / "proof.json"
    payload = {
        "package": runner.PACKAGE,
        "state_path_sha256": hashlib.sha256(str(state).encode()).hexdigest(),
        "checkpoint_latest_sha256": hashlib.sha256(latest.read_bytes()).hexdigest(),
    }
    proof.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(runner.base, "require_long_run_qa", lambda *_args: None)
    completed_epoch = 2
    monkeypatch.setattr(
        runner.base,
        "CheckpointStore",
        lambda *_args, **_kwargs: SimpleNamespace(
            load_latest=lambda _binding: {"completed_epoch": completed_epoch}
        ),
    )
    runner.require_long_run_qa(proof, "a" * 64, "b" * 64, state)
    payload["state_path_sha256"] = "0" * 64
    proof.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(RuntimeError, match="does not bind state/checkpoint"):
        runner.require_long_run_qa(proof, "a" * 64, "b" * 64, state)
    payload["state_path_sha256"] = hashlib.sha256(str(state).encode()).hexdigest()
    proof.write_text(json.dumps(payload), encoding="utf-8")
    completed_epoch = 1
    with pytest.raises(RuntimeError, match="does not bind state/checkpoint"):
        runner.require_long_run_qa(proof, "a" * 64, "b" * 64, state)
