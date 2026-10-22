from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from m1 import corrected_val_r1 as evaluator


def test_ccw_unknown_box_transform_matches_wp38_policy() -> None:
    source = np.array([[0.25, 0.40, 0.10, 0.20]])
    assert evaluator.rotate_ccw_xywh(source).tolist() == [[0.4, 0.75, 0.2, 0.1]]


def test_ccw_transform_rejects_out_of_bounds() -> None:
    with pytest.raises(RuntimeError, match="outside normalized bounds"):
        evaluator.rotate_ccw_xywh(np.array([[1.5, 0.4, 0.1, 0.2]]))


def test_parser_exposes_validation_only_commands() -> None:
    choices = evaluator.parser()._subparsers._group_actions[0].choices
    assert set(choices) == {"check", "evaluate"}
    source = Path(evaluator.__file__).read_text()
    assert "export-test" not in source
    assert "--final-eval" not in source
    assert "split=\"test\"" not in source


def test_corrected_data_authority_verifies_without_test_access() -> None:
    result = evaluator.verify_corrected_data()
    assert result["val_frames"] == 376
    assert result["corrected_frames"] == 39
    assert result["test_included"] is False
    assert result["sealed_test_accessed"] is False


def test_evaluate_refuses_existing_report_before_model_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    report = run_dir / evaluator.REPORT_NAME
    report.write_text("owner result", encoding="utf-8")
    monkeypatch.setattr(evaluator, "verify_corrected_data", lambda: {"data_yaml": "data.yaml"})
    monkeypatch.setattr(
        evaluator.contract,
        "bind_run_weights",
        lambda _weights: {
            "path": str(tmp_path / "best.pt"),
            "run_dir": str(run_dir),
            "seed": 20261018,
        },
    )
    with pytest.raises(RuntimeError, match="refused to overwrite"):
        evaluator.evaluate("best.pt")
    assert report.read_text(encoding="utf-8") == "owner result"
