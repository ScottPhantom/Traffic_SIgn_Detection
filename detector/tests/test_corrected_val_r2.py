from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from m1 import corrected_val_r2 as evaluator


def test_parser_remains_validation_only() -> None:
    assert set(evaluator.parser()._subparsers._group_actions[0].choices) == {
        "check",
        "evaluate",
    }
    source = Path(evaluator.__file__).read_text()
    assert "export-test" not in source
    assert "--final-eval" not in source


def test_weight_guard_rejects_replacement(tmp_path: Path) -> None:
    weight = tmp_path / "best.pt"
    weight.write_bytes(b"governed")
    expected = evaluator.sha256_file(weight)
    fd, opened = evaluator._open_weight_guard(weight, expected)
    try:
        replacement = tmp_path / "replacement.pt"
        replacement.write_bytes(b"governed")
        os.replace(replacement, weight)
        with pytest.raises(RuntimeError, match="binding changed"):
            evaluator._validate_weight_guard(weight, fd, opened, expected)
    finally:
        os.close(fd)


def test_safe_report_refuses_symlink_without_external_write(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    external = tmp_path / "owner.json"
    external.write_text("OWNER", encoding="utf-8")
    (run_dir / evaluator.REPORT_NAME).symlink_to(external)
    with pytest.raises(FileExistsError):
        evaluator._safe_write_report(run_dir, {"status": "complete"})
    assert external.read_text(encoding="utf-8") == "OWNER"
    assert (run_dir / evaluator.REPORT_NAME).is_symlink()


def test_safe_report_handles_creation_race_without_following_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    external = tmp_path / "owner.json"
    external.write_text("OWNER", encoding="utf-8")
    real_link = evaluator.os.link

    def racing_link(source, destination, **kwargs):
        (run_dir / destination).symlink_to(external)
        return real_link(source, destination, **kwargs)

    monkeypatch.setattr(evaluator.os, "link", racing_link)
    with pytest.raises(FileExistsError):
        evaluator._safe_write_report(run_dir, {"status": "complete"})
    assert external.read_text(encoding="utf-8") == "OWNER"
    assert not (run_dir / f".{evaluator.REPORT_NAME}.partial").exists()


def test_safe_report_creates_exact_regular_file(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    payload = {"status": "complete", "sealed_test_accessed": False}
    path = evaluator._safe_write_report(run_dir, payload)
    assert path == run_dir / evaluator.REPORT_NAME
    assert not path.is_symlink()
    assert json.loads(path.read_text(encoding="utf-8")) == payload
    assert path.stat().st_nlink == 1


def test_authority_check_stays_sealed_safe() -> None:
    result = evaluator.verify_corrected_data()
    assert result["val_frames"] == 376
    assert result["corrected_frames"] == 39
    assert result["test_included"] is False
    assert result["sealed_test_accessed"] is False
