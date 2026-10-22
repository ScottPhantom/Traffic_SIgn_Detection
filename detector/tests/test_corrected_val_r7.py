from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from m1 import corrected_val_r7 as evaluator


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
        _report_integration=lambda: _Integration(),
    )

    def safe_write(run_dir: Path, payload: dict) -> Path:
        path = run_dir / predecessor.REPORT_NAME
        fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o000)
        try:
            data = evaluator._expected_bytes(payload)
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


def test_parser_is_validation_only() -> None:
    assert set(evaluator.parser()._subparsers._group_actions[0].choices) == {
        "check",
        "evaluate",
    }
    source = Path(evaluator.__file__).read_text()
    assert "final-eval" not in source
    assert "export-test" not in source


def test_public_round_trip_accepts_exact_publication(
    tmp_path: Path, fake_predecessor
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    result = evaluator._safe_write_report(run_dir, {"status": "complete"})
    assert result == run_dir / evaluator.REPORT_NAME
    assert result.read_text(encoding="utf-8").endswith("\n")


def test_ancestor_swap_after_predecessor_publication_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_predecessor,
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    detached = tmp_path / "detached"
    original = fake_predecessor._safe_write_report

    def swap(run: Path, payload: dict) -> Path:
        output = original(run, payload)
        run.rename(detached)
        run.mkdir()
        (run / evaluator.REPORT_NAME).write_text("OWNER\n", encoding="utf-8")
        return output

    fake_predecessor._safe_write_report = swap
    with pytest.raises(RuntimeError, match="mode differs|hash differs"):
        evaluator._safe_write_report(run_dir, {"status": "complete"})
    assert (run_dir / evaluator.REPORT_NAME).read_text(encoding="utf-8") == "OWNER\n"
    assert (detached / evaluator.REPORT_NAME).is_file()


def test_public_path_symlink_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_predecessor,
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    owner = tmp_path / "owner"
    owner.write_text("OWNER", encoding="utf-8")
    original = fake_predecessor._safe_write_report

    def swap(run: Path, payload: dict) -> Path:
        output = original(run, payload)
        output.rename(tmp_path / "published")
        output.symlink_to(owner)
        return output

    fake_predecessor._safe_write_report = swap
    with pytest.raises(OSError):
        evaluator._safe_write_report(run_dir, {"status": "complete"})
    assert owner.read_text(encoding="utf-8") == "OWNER"


def test_predecessor_name_is_restored_on_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_predecessor,
) -> None:
    original_name = fake_predecessor.REPORT_NAME

    def fail(_run_dir: Path, _payload: dict) -> Path:
        raise RuntimeError("injected")

    fake_predecessor._safe_write_report = fail
    with pytest.raises(RuntimeError, match="injected"):
        evaluator._safe_write_report(tmp_path, {"status": "complete"})
    assert fake_predecessor.REPORT_NAME == original_name


def test_authority_check_stays_sealed_safe() -> None:
    result = evaluator.verify_corrected_data()
    assert result["val_frames"] == 376
    assert result["corrected_frames"] == 39
    assert result["test_included"] is False
    assert result["sealed_test_accessed"] is False
