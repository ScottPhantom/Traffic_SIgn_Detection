from __future__ import annotations

import hashlib
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from m1 import corrected_val_r4 as evaluator


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
    r2 = SimpleNamespace(load_integration=lambda: _Integration())
    predecessor = SimpleNamespace(load_predecessor=lambda: r2)
    monkeypatch.setattr(evaluator, "load_predecessor", lambda: predecessor)
    return predecessor


def test_parser_remains_validation_only() -> None:
    assert set(evaluator.parser()._subparsers._group_actions[0].choices) == {
        "check",
        "evaluate",
    }
    source = Path(evaluator.__file__).read_text()
    assert "final-eval" not in source
    assert "export-test" not in source


def test_descriptor_copy_consumes_pinned_bytes_after_public_replacement(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"GOOD")
    source_fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        original = tmp_path / "original.bin"
        source.rename(original)
        source.write_bytes(b"EVIL")
        destination = tmp_path / "snapshot.bin"
        result = evaluator._copy_open_fd(
            source_fd, destination, hashlib.sha256(b"GOOD").hexdigest()
        )
    finally:
        os.close(source_fd)
    assert destination.read_bytes() == b"GOOD"
    assert result["sha256"] == hashlib.sha256(b"GOOD").hexdigest()


def test_descriptor_copy_hash_failure_removes_only_owned_destination(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"EVIL")
    source_fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW)
    destination = tmp_path / "snapshot.bin"
    try:
        with pytest.raises(RuntimeError, match="source hash differs"):
            evaluator._copy_open_fd(
                source_fd, destination, hashlib.sha256(b"GOOD").hexdigest()
            )
    finally:
        os.close(source_fd)
    assert not destination.exists()


def test_safe_report_does_not_delete_preexisting_partial_collision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_predecessor,
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    collision = run_dir / f".{evaluator.REPORT_NAME}.fixed.partial"
    collision.write_text("OWNER", encoding="utf-8")
    values = iter(["fixed", "fresh"])
    monkeypatch.setattr(evaluator.secrets, "token_hex", lambda _size: next(values))
    result = evaluator._safe_write_report(run_dir, {"status": "complete"})
    assert result == run_dir / evaluator.REPORT_NAME
    assert collision.read_text(encoding="utf-8") == "OWNER"
    assert not (run_dir / f".{evaluator.REPORT_NAME}.fresh.partial").exists()


def test_safe_report_publish_needs_no_post_publish_unlink(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_predecessor,
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    real_unlink = evaluator.os.unlink
    calls = 0

    def fail_once(path, *args, **kwargs):
        nonlocal calls
        calls += 1
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(evaluator.os, "unlink", fail_once)
    result = evaluator._safe_write_report(run_dir, {"status": "complete"})
    assert result == run_dir / evaluator.REPORT_NAME
    assert calls == 0
    assert [path.name for path in run_dir.iterdir()] == [evaluator.REPORT_NAME]


def test_safe_report_rolls_back_after_relation_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    class FailingIntegration(_Integration):
        @staticmethod
        def _validate_relations(_relations) -> None:
            raise RuntimeError("injected relation failure")

    r2 = SimpleNamespace(load_integration=lambda: FailingIntegration())
    predecessor = SimpleNamespace(load_predecessor=lambda: r2)
    monkeypatch.setattr(evaluator, "load_predecessor", lambda: predecessor)
    with pytest.raises(RuntimeError, match="injected relation failure"):
        evaluator._safe_write_report(run_dir, {"status": "complete"})
    assert list(run_dir.iterdir()) == []


def test_safe_report_refuses_final_symlink_without_external_write(
    tmp_path: Path,
    fake_predecessor,
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    owner = tmp_path / "owner.json"
    owner.write_text("OWNER", encoding="utf-8")
    (run_dir / evaluator.REPORT_NAME).symlink_to(owner)
    with pytest.raises(FileExistsError):
        evaluator._safe_write_report(run_dir, {"status": "complete"})
    assert owner.read_text(encoding="utf-8") == "OWNER"
    assert (run_dir / evaluator.REPORT_NAME).is_symlink()


def test_atomic_final_replacement_race_never_deletes_owner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_predecessor,
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    owner = tmp_path / "owner.json"
    owner.write_text("OWNER", encoding="utf-8")
    real_rename = evaluator._rename_exclusive

    def race(source_dir_fd, source, destination_dir_fd, destination):
        os.rename(owner, run_dir / destination)
        return real_rename(source_dir_fd, source, destination_dir_fd, destination)

    monkeypatch.setattr(evaluator, "_rename_exclusive", race)
    with pytest.raises(OSError) as captured:
        evaluator._safe_write_report(run_dir, {"status": "complete"})
    assert captured.value.errno == 17
    assert (run_dir / evaluator.REPORT_NAME).read_text(encoding="utf-8") == "OWNER"
    assert not owner.exists()
    assert [path.name for path in run_dir.iterdir()] == [evaluator.REPORT_NAME]


def test_authority_check_stays_sealed_safe() -> None:
    result = evaluator.verify_corrected_data()
    assert result["val_frames"] == 376
    assert result["corrected_frames"] == 39
    assert result["test_included"] is False
    assert result["sealed_test_accessed"] is False
