from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from m1 import corrected_val_r8 as evaluator


class _Integration:
    @staticmethod
    def _open_directory_chain(path: Path):
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        return fd, [fd], []

    @staticmethod
    def _validate_relations(_relations) -> None:
        return None


@pytest.fixture
def fake_predecessor(monkeypatch: pytest.MonkeyPatch):
    predecessor = SimpleNamespace(
        REPORT_NAME="old.json",
        load_predecessor=lambda: SimpleNamespace(_report_integration=lambda: _Integration()),
    )

    def safe_write(run_dir: Path, payload: dict) -> Path:
        path = run_dir / predecessor.REPORT_NAME
        fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o000)
        try:
            data = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
            os.write(fd, data)
            os.fsync(fd)
            os.fchmod(fd, 0o400)
            os.fsync(fd)
        finally:
            os.close(fd)
        return path

    predecessor._safe_write_report = safe_write
    monkeypatch.setattr(evaluator, "load_predecessor", lambda: predecessor)
    return predecessor


def _payload() -> dict:
    return {
        "status": "CORRECTED_VALIDATION_COMPLETE",
        "map50": 0.8,
        "map50_95": 0.6,
        "operating_point": {"conf": 0.2},
        "gates": {"single_seed_checks_passed": False},
        "test_included": False,
        "sealed_test_accessed": False,
    }


def test_parser_is_validation_only() -> None:
    assert set(evaluator.parser()._subparsers._group_actions[0].choices) == {
        "check",
        "evaluate",
    }
    source = Path(evaluator.__file__).read_text()
    assert "final-eval" not in source
    assert "export-test" not in source


def test_writer_returns_content_binding_not_path(
    tmp_path: Path, fake_predecessor
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    binding = evaluator._safe_write_report(run_dir, _payload())
    assert isinstance(binding, evaluator.ReportBinding)
    assert str(binding) == f"sha256:{binding.sha256}"
    assert binding.locator == evaluator.REPORT_NAME
    assert binding.locator_policy == "REOPEN_AND_VERIFY_BEFORE_USE"
    assert binding.mode == 0o400
    assert binding.nlink == 1
    assert binding.sealed_test_accessed is False


def test_consumer_reads_payload_through_verified_descriptor(
    tmp_path: Path, fake_predecessor
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    expected = _payload()
    binding = evaluator._safe_write_report(run_dir, expected).to_dict()
    assert evaluator.consume_report(run_dir, binding) == expected
    data = (run_dir / evaluator.REPORT_NAME).read_bytes()
    assert binding["sha256"] == hashlib.sha256(data).hexdigest()
    assert binding["bytes"] == len(data)


def test_locator_replacement_after_binding_is_rejected(
    tmp_path: Path, fake_predecessor
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    binding = evaluator._safe_write_report(run_dir, _payload()).to_dict()
    published = run_dir / evaluator.REPORT_NAME
    published.rename(tmp_path / "bound-original")
    published.write_text("OWNER\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="descriptor binding differs"):
        evaluator.consume_report(run_dir, binding)
    assert published.read_text(encoding="utf-8") == "OWNER\n"


def test_locator_symlink_after_binding_is_rejected(
    tmp_path: Path, fake_predecessor
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    binding = evaluator._safe_write_report(run_dir, _payload()).to_dict()
    published = run_dir / evaluator.REPORT_NAME
    published.rename(tmp_path / "bound-original")
    owner = tmp_path / "owner"
    owner.write_text("OWNER", encoding="utf-8")
    published.symlink_to(owner)
    with pytest.raises(OSError):
        evaluator.consume_report(run_dir, binding)
    assert owner.read_text(encoding="utf-8") == "OWNER"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", True),
        ("bytes", True),
        ("sha256", "0" * 64),
        ("content_uri", "file:///tmp/report"),
        ("locator", "../report.json"),
        ("locator_policy", "TRUST_PATH"),
        ("mode", 0o600),
        ("nlink", 2),
        ("is_regular", False),
        ("sealed_test_accessed", True),
    ],
)
def test_binding_tamper_is_rejected(
    tmp_path: Path, fake_predecessor, field: str, value: object
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    binding = evaluator._safe_write_report(run_dir, _payload()).to_dict()
    changed = copy.deepcopy(binding)
    changed[field] = value
    with pytest.raises(RuntimeError):
        evaluator.consume_report(run_dir, changed)


def test_evaluate_returns_metrics_from_consumed_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    payload = _payload()
    binding = evaluator.ReportBinding(
        schema_version=1,
        content_uri="sha256:" + "a" * 64,
        sha256="a" * 64,
        bytes=123,
        locator=evaluator.REPORT_NAME,
        locator_policy="REOPEN_AND_VERIFY_BEFORE_USE",
        device=1,
        inode=2,
        mode=0o400,
        nlink=1,
        is_regular=True,
        sealed_test_accessed=False,
    )
    predecessor = SimpleNamespace(REPORT_NAME="old.json")

    def inherited_evaluate(*_args, **_kwargs):
        result = predecessor._safe_write_report(run_dir, payload)
        return {"report": str(result), "map50": -1.0}

    predecessor.evaluate = inherited_evaluate
    predecessor.verify_corrected_data = lambda: {}
    predecessor._safe_write_report = lambda *_args, **_kwargs: None
    monkeypatch.setattr(evaluator, "verify_pins", lambda: None)
    monkeypatch.setattr(evaluator, "load_predecessor", lambda: predecessor)
    monkeypatch.setattr(evaluator, "_safe_write_report", lambda *_args, **_kwargs: binding)
    monkeypatch.setattr(evaluator, "consume_report", lambda *_args, **_kwargs: payload)
    result = evaluator.evaluate("weights.pt")
    assert result["map50"] == payload["map50"]
    assert result["report"] == binding.content_uri
    assert result["report_binding"] == binding.to_dict()
    assert result["report_consumed_from_verified_descriptor"] is True


def test_authority_check_stays_sealed_safe() -> None:
    result = evaluator.verify_corrected_data()
    assert result["val_frames"] == 376
    assert result["corrected_frames"] == 39
    assert result["test_included"] is False
    assert result["sealed_test_accessed"] is False
