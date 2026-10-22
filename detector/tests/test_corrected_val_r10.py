from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from m1 import corrected_val_r10 as evaluator


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
        "resolution_breakdown": {540: ("landscape", 39)},
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
def fake_chain(monkeypatch: pytest.MonkeyPatch):
    predecessor_r8 = SimpleNamespace(REPORT_NAME="r8.json")

    def safe_write(run_dir: Path, payload: dict[str, Any]) -> _Binding:
        data = _canonical(payload)
        (run_dir / predecessor_r8.REPORT_NAME).write_bytes(data)
        return _binding_for(data, predecessor_r8.REPORT_NAME)

    def open_bound(run_dir: Path, binding: dict[str, Any]):
        data = (run_dir / binding["locator"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != binding["sha256"]:
            raise RuntimeError("bound hash differs")
        return data, json.loads(data)

    predecessor_r8._safe_write_report = safe_write
    predecessor_r8._open_bound_report = open_bound
    predecessor_r9 = SimpleNamespace(
        REPORT_NAME="r9.json",
        load_predecessor=lambda: predecessor_r8,
    )

    def consume(run_dir: Path, binding: dict[str, Any]):
        original = predecessor_r8.REPORT_NAME
        predecessor_r8.REPORT_NAME = predecessor_r9.REPORT_NAME
        try:
            return open_bound(run_dir, binding)[1]
        finally:
            predecessor_r8.REPORT_NAME = original

    predecessor_r9.consume_report = consume
    monkeypatch.setattr(evaluator, "verify_pins", lambda: None)
    monkeypatch.setattr(evaluator, "load_predecessor", lambda: predecessor_r9)
    return predecessor_r9, predecessor_r8


def test_parser_is_validation_only() -> None:
    assert set(evaluator.parser()._subparsers._group_actions[0].choices) == {
        "check",
        "evaluate",
    }
    source = Path(evaluator.__file__).read_text()
    assert "final-eval" not in source
    assert "export-test" not in source


def test_json_normalized_live_payload_is_accepted(tmp_path: Path, fake_chain) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    intended = _payload()
    binding = evaluator._safe_write_report(run_dir, intended)
    consumed = evaluator.consume_report(run_dir, binding.to_dict())
    assert consumed == json.loads(_canonical(intended))
    assert consumed != intended
    assert binding.sha256 == hashlib.sha256(_canonical(intended)).hexdigest()


def test_replacement_between_publication_and_binding_is_rejected(
    tmp_path: Path,
    fake_chain,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    predecessor_r9, predecessor_r8 = fake_chain
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    substitute = _payload(map50=0.01)

    def substituted_write(run_dir: Path, _payload: dict[str, Any]) -> _Binding:
        data = _canonical(substitute)
        (run_dir / predecessor_r8.REPORT_NAME).write_bytes(data)
        return _binding_for(data, predecessor_r8.REPORT_NAME)

    monkeypatch.setattr(predecessor_r8, "_safe_write_report", substituted_write)
    with pytest.raises(RuntimeError, match="binding differs from intended payload"):
        evaluator._safe_write_report(run_dir, _payload())
    assert predecessor_r9.REPORT_NAME == "r9.json"


def test_noncanonical_same_document_is_rejected(
    tmp_path: Path,
    fake_chain,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _predecessor_r9, predecessor_r8 = fake_chain
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    def compact_write(run_dir: Path, payload: dict[str, Any]) -> _Binding:
        data = (json.dumps(payload, sort_keys=True) + "\n").encode()
        (run_dir / predecessor_r8.REPORT_NAME).write_bytes(data)
        return _binding_for(data, predecessor_r8.REPORT_NAME)

    monkeypatch.setattr(predecessor_r8, "_safe_write_report", compact_write)
    with pytest.raises(RuntimeError, match="binding differs from intended payload"):
        evaluator._safe_write_report(run_dir, _payload())


def test_changed_bytes_after_binding_are_rejected(
    tmp_path: Path,
    fake_chain,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _predecessor_r9, predecessor_r8 = fake_chain
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    original_open = predecessor_r8._open_bound_report

    def replace_then_open(run_dir: Path, binding: dict[str, Any]):
        (run_dir / binding["locator"]).write_bytes(_canonical(_payload(map50=0.01)))
        return original_open(run_dir, binding)

    monkeypatch.setattr(predecessor_r8, "_open_bound_report", replace_then_open)
    with pytest.raises(RuntimeError, match="bound hash differs"):
        evaluator._safe_write_report(run_dir, _payload())


def test_evaluate_returns_only_consumed_report_metrics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    payload = json.loads(_canonical(_payload()))
    binding = _binding_for(_canonical(_payload()), evaluator.REPORT_NAME)
    predecessor = SimpleNamespace(REPORT_NAME="r9.json")

    def inherited_evaluate(*_args, **_kwargs):
        issued = predecessor._safe_write_report(run_dir, _payload())
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
    assert result["report_compared_in_json_space"] is True
    assert result["sealed_test_accessed"] is False


def test_authority_check_stays_sealed_safe() -> None:
    result = evaluator.verify_corrected_data()
    assert result["val_frames"] == 376
    assert result["corrected_frames"] == 39
    assert result["test_included"] is False
    assert result["sealed_test_accessed"] is False
