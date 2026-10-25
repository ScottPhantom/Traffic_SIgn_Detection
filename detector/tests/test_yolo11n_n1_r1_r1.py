from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

from m1 import checkpoint_store

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "detector/colab/run_yolo11n_n1_r1_r1.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("test_yolo11n_n1_r1_r1_runner", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_repair_uses_checkpoint_store_compliant_run_identity() -> None:
    runner = load_runner()
    assert runner.REPAIR == "R1-R1"
    assert re.fullmatch(r"D1_[A-Za-z0-9_.-]+", runner.RUN_NAME)
    assert checkpoint_store.RUN_PATTERN.fullmatch(runner.RUN_NAME)
    assert runner.RUN_NAME == "D1_yolo11n_n1_detector"


def test_checkpoint_store_accepts_repair_run_identity(tmp_path: Path) -> None:
    runner = load_runner()
    run = tmp_path / runner.RUN_NAME
    for relative in checkpoint_store.REQUIRED_ARTIFACTS:
        artifact = run / relative
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_bytes(f"fixture:{relative}".encode())
    store = checkpoint_store.CheckpointStore(tmp_path / "recovery")
    manifest = store.save(run, epoch=1, binding={"repair": runner.REPAIR})
    assert manifest["run"] == runner.RUN_NAME
    assert manifest["completed_epoch"] == 1
    assert store.load_latest({"repair": runner.REPAIR}) == manifest


def test_repair_preserves_owner_frozen_training_contract() -> None:
    runner = load_runner()
    assert runner.PACKAGE == "YOLO11N-N1-R1"
    assert runner.CONFIG["architecture"] == "YOLO11n"
    assert runner.CONFIG["detector_epochs"] == 100
    assert runner.CONFIG["detector_batch"] == 4
    assert runner.CONFIG["imgsz"] == 1280
    assert runner.CONFIG["fliplr"] == 0.0
    assert runner.EXPECTED_STATE_SUFFIX.endswith("yolo11n_n1_seed_20261018_r1_r1")


def test_repair_remains_sealed_test_closed() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "export-test" not in source
    assert "--final-eval" not in source
    assert 'choices=("check", "detector")' in source


def test_repair_qa_must_bind_exact_repair_runner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = load_runner()
    root = tmp_path / "bundle"
    (root / "manifest.json").parent.mkdir(parents=True)
    (root / "manifest.json").write_text('{"members": {}}', encoding="utf-8")
    record = tmp_path / "qa.md"
    record.write_text("Verdict: **PASS**\n", encoding="utf-8")
    monkeypatch.setattr(runner.base, "require_source_qa", lambda *_args: None)
    with pytest.raises(RuntimeError, match="does not bind the repair runner"):
        runner.require_source_qa(root, record, "a" * 64)
    record.write_text(
        "Verdict: **PASS**\n" + runner.base.sha256_file(SOURCE) + "\n",
        encoding="utf-8",
    )
    runner.require_source_qa(root, record, runner.base.sha256_file(record))
