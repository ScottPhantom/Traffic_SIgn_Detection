from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from m1 import corrected_val_r9 as evaluator


@dataclass(frozen=True)
class _Binding:
    content_uri: str
    sha256: str
    bytes: int
    locator: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "bytes": self.bytes,
            "content_uri": self.content_uri,
            "locator": self.locator,
            "sha256": self.sha256,
        }


def _payload(map50: float = 0.8) -> dict[str, Any]:
    return {
        "status": "CORRECTED_VALIDATION_COMPLETE",
        "map50": map50,
        "map50_95": 0.6,
        "operating_point": {"conf": 0.2},
        "gates": {"single_seed_checks_passed": False},
        "test_included": False,
        "sealed_test_accessed": False,
    }


def _canonical(payload: dict[str, Any]) -> bytes:
    return (
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode()


def _binding_for(payload_bytes: bytes, locator: str) -> _Binding:
    digest = hashlib.sha256(payload_bytes).hexdigest()
    return _Binding(
        content_uri=f"sha256:{digest}",
        sha256=digest,
        bytes=len(payload_bytes),
        locator=locator,
    )


@pytest.fixture
def fake_predecessor(monkeypatch: pytest.MonkeyPatch):
    predecessor = SimpleNamespace(REPORT_NAME="old.json")

    def safe_write(run_dir: Path, payload: dict[str, Any]) -> _Binding:
        data = _canonical(payload)
        (run_dir / predecessor.REPORT_NAME).write_bytes(data)
        return _binding_for(data, predecessor.REPORT_NAME)

    def open_bound(run_dir: Path, binding: dict[str, Any]):
        data = (run_dir / binding["locator"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != binding["sha256"]:
            raise RuntimeError("bound hash differs")
        return data, json.loads(data)

    predecessor._safe_write_report = safe_write
    predecessor._open_bound_report = open_bound
    predecessor.consume_report = lambda run_dir, binding: open_bound(run_dir, binding)[1]
    monkeypatch.setattr(evaluator, "verify_pins", lambda: None)
    monkeypatch.setattr(evaluator, "load_predecessor", lambda: predecessor)
    return predecessor


def test_parser_is_validation_only() -> None:
    assert set(evaluator.parser()._subparsers._group_actions[0].choices) == {
        "check",
        "evaluate",
    }
    source = Path(evaluator.__file__).read_text()
    assert "final-eval" not in source
    assert "export-test" not in source


def test_writer_binds_exact_intended_payload(tmp_path: Path, fake_predecessor) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    intended = _payload()
    binding = evaluator._safe_write_report(run_dir, intended)
    assert binding.sha256 == hashlib.sha256(_canonical(intended)).hexdigest()
    assert binding.bytes == len(_canonical(intended))
    assert binding.locator == evaluator.REPORT_NAME
    assert evaluator.consume_report(run_dir, binding.to_dict()) == intended


def test_replacement_between_publication_and_binding_is_rejected(
    tmp_path: Path,
    fake_predecessor,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    substitute = _payload(map50=0.01)

    def substituted_write(run_dir: Path, _payload: dict[str, Any]) -> _Binding:
        data = _canonical(substitute)
        (run_dir / fake_predecessor.REPORT_NAME).write_bytes(data)
        return _binding_for(data, fake_predecessor.REPORT_NAME)

    monkeypatch.setattr(fake_predecessor, "_safe_write_report", substituted_write)
    with pytest.raises(RuntimeError, match="binding differs from intended payload"):
        evaluator._safe_write_report(run_dir, _payload())


def test_noncanonical_publication_of_same_document_is_rejected(
    tmp_path: Path,
    fake_predecessor,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    def compact_write(run_dir: Path, payload: dict[str, Any]) -> _Binding:
        data = (json.dumps(payload, sort_keys=True) + "\n").encode()
        (run_dir / fake_predecessor.REPORT_NAME).write_bytes(data)
        return _binding_for(data, fake_predecessor.REPORT_NAME)

    monkeypatch.setattr(fake_predecessor, "_safe_write_report", compact_write)
    with pytest.raises(RuntimeError, match="binding differs from intended payload"):
        evaluator._safe_write_report(run_dir, _payload())


def test_changed_bytes_after_binding_are_rejected(
    tmp_path: Path,
    fake_predecessor,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    original_open = fake_predecessor._open_bound_report

    def replace_then_open(run_dir: Path, binding: dict[str, Any]):
        (run_dir / binding["locator"]).write_bytes(_canonical(_payload(map50=0.01)))
        return original_open(run_dir, binding)

    monkeypatch.setattr(fake_predecessor, "_open_bound_report", replace_then_open)
    with pytest.raises(RuntimeError, match="bound hash differs"):
        evaluator._safe_write_report(run_dir, _payload())


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("sha256", "0" * 64),
        ("content_uri", "file:///tmp/report"),
        ("bytes", 1),
        ("locator", "other.json"),
    ],
)
def test_published_authority_tamper_is_rejected(
    tmp_path: Path,
    fake_predecessor,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    original_write = fake_predecessor._safe_write_report

    def tampered_write(run_dir: Path, payload: dict[str, Any]):
        binding = original_write(run_dir, payload)
        changed = copy.deepcopy(binding.to_dict())
        changed[field] = value
        return SimpleNamespace(to_dict=lambda: changed)

    monkeypatch.setattr(fake_predecessor, "_safe_write_report", tampered_write)
    with pytest.raises(RuntimeError, match="binding differs from intended payload"):
        evaluator._safe_write_report(run_dir, _payload())


def test_evaluate_returns_only_consumed_report_metrics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    payload = _payload()
    data = _canonical(payload)
    binding = _binding_for(data, evaluator.REPORT_NAME)
    predecessor = SimpleNamespace(REPORT_NAME="old.json")

    def inherited_evaluate(*_args, **_kwargs):
        issued = predecessor._safe_write_report(run_dir, payload)
        return {"report": issued.content_uri, "map50": -1.0}

    predecessor.evaluate = inherited_evaluate
    predecessor._safe_write_report = lambda *_args, **_kwargs: None
    monkeypatch.setattr(evaluator, "verify_pins", lambda: None)
    monkeypatch.setattr(evaluator, "load_predecessor", lambda: predecessor)
    monkeypatch.setattr(evaluator, "_safe_write_report", lambda *_args, **_kwargs: binding)
    monkeypatch.setattr(evaluator, "consume_report", lambda *_args, **_kwargs: payload)
    result = evaluator.evaluate("weights.pt")
    assert result["map50"] == payload["map50"]
    assert result["report"] == binding.content_uri
    assert result["report_matches_intended_payload"] is True
    assert result["sealed_test_accessed"] is False


def test_authority_check_stays_sealed_safe() -> None:
    result = evaluator.verify_corrected_data()
    assert result["val_frames"] == 376
    assert result["corrected_frames"] == 39
    assert result["test_included"] is False
    assert result["sealed_test_accessed"] is False
