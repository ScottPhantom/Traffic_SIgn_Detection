from __future__ import annotations

import ast
import hashlib
import os
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from m1 import corrected_val_r6 as evaluator


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
    integration = SimpleNamespace(load_integration=lambda: _Integration())
    predecessor = SimpleNamespace(load_predecessor=lambda: integration)
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
    tree = ast.parse(source)
    called = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert called.isdisjoint({"rename", "replace", "unlink", "remove", "rmtree"})


def test_report_is_exact_private_regular_inode(
    tmp_path: Path, fake_predecessor
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    payload = {"status": "complete", "sealed_test_accessed": False}
    result = evaluator._safe_write_report(run_dir, payload)
    expected = b'{\n  "sealed_test_accessed": false,\n  "status": "complete"\n}\n'
    info = result.lstat()
    assert result.read_bytes() == expected
    assert hashlib.sha256(result.read_bytes()).hexdigest() == hashlib.sha256(expected).hexdigest()
    assert stat.S_IMODE(info.st_mode) == 0o400
    assert info.st_nlink == 1
    assert [path.name for path in run_dir.iterdir()] == [evaluator.REPORT_NAME]


@pytest.mark.parametrize("kind", ["regular", "symlink", "hardlink"])
def test_final_collision_is_preserved(
    tmp_path: Path, fake_predecessor, kind: str
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    final = run_dir / evaluator.REPORT_NAME
    owner = tmp_path / "owner"
    owner.write_text("OWNER", encoding="utf-8")
    if kind == "regular":
        final.write_text("OWNER", encoding="utf-8")
    elif kind == "symlink":
        final.symlink_to(owner)
    else:
        os.link(owner, final)
    with pytest.raises(FileExistsError):
        evaluator._safe_write_report(run_dir, {"status": "complete"})
    assert owner.read_text(encoding="utf-8") == "OWNER"
    assert final.exists() or final.is_symlink()


def test_injected_content_swap_is_detected_and_quarantined(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_predecessor,
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    real_write = evaluator._write_all

    def swap(fd: int, data: bytes) -> None:
        real_write(fd, data)
        os.lseek(fd, 0, os.SEEK_SET)
        os.write(fd, b"EVIL")
        os.ftruncate(fd, 4)

    monkeypatch.setattr(evaluator, "_write_all", swap)
    with pytest.raises(RuntimeError, match="hash differs"):
        evaluator._safe_write_report(run_dir, {"status": "complete"})
    final = run_dir / evaluator.REPORT_NAME
    assert stat.S_IMODE(final.stat().st_mode) == 0


def test_injected_hardlink_is_detected_and_quarantined(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_predecessor,
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    alias = tmp_path / "alias"
    real_write = evaluator._write_all

    def link(fd: int, data: bytes) -> None:
        real_write(fd, data)
        os.link(run_dir / evaluator.REPORT_NAME, alias)

    monkeypatch.setattr(evaluator, "_write_all", link)
    with pytest.raises(RuntimeError, match="descriptor is unsafe"):
        evaluator._safe_write_report(run_dir, {"status": "complete"})
    final = run_dir / evaluator.REPORT_NAME
    assert stat.S_IMODE(final.stat().st_mode) == 0
    assert final.stat().st_nlink == 2


def test_final_path_replacement_is_detected_without_deleting_owner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_predecessor,
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    displaced = tmp_path / "displaced"
    final = run_dir / evaluator.REPORT_NAME
    real_write = evaluator._write_all

    def replace(fd: int, data: bytes) -> None:
        real_write(fd, data)
        final.rename(displaced)
        final.write_text("OWNER", encoding="utf-8")

    monkeypatch.setattr(evaluator, "_write_all", replace)
    with pytest.raises(RuntimeError, match="binding differs"):
        evaluator._safe_write_report(run_dir, {"status": "complete"})
    assert final.read_text(encoding="utf-8") == "OWNER"
    assert stat.S_IMODE(displaced.stat().st_mode) == 0


def test_relation_failure_precedes_final_reservation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    class FailingIntegration(_Integration):
        @staticmethod
        def _validate_relations(_relations) -> None:
            raise RuntimeError("injected relation failure")

    integration = SimpleNamespace(load_integration=lambda: FailingIntegration())
    predecessor = SimpleNamespace(load_predecessor=lambda: integration)
    monkeypatch.setattr(evaluator, "load_predecessor", lambda: predecessor)
    with pytest.raises(RuntimeError, match="injected relation failure"):
        evaluator._safe_write_report(run_dir, {"status": "complete"})
    assert list(run_dir.iterdir()) == []


def test_second_relation_failure_quarantines_reserved_final(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    class LaterFailingIntegration(_Integration):
        calls = 0

        @classmethod
        def _validate_relations(cls, _relations) -> None:
            cls.calls += 1
            if cls.calls == 2:
                raise RuntimeError("injected second relation failure")

    integration = SimpleNamespace(load_integration=lambda: LaterFailingIntegration())
    predecessor = SimpleNamespace(load_predecessor=lambda: integration)
    monkeypatch.setattr(evaluator, "load_predecessor", lambda: predecessor)
    with pytest.raises(RuntimeError, match="second relation failure"):
        evaluator._safe_write_report(run_dir, {"status": "complete"})
    final = run_dir / evaluator.REPORT_NAME
    assert stat.S_IMODE(final.stat().st_mode) == 0


def test_post_publish_close_failure_cannot_reverse_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_predecessor,
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    real_open = evaluator.os.open
    real_close = evaluator.os.close
    report_fd: int | None = None
    injected = False

    def capture_open(path, *args, **kwargs):
        nonlocal report_fd
        fd = real_open(path, *args, **kwargs)
        if path == evaluator.REPORT_NAME:
            report_fd = fd
        return fd

    def fail_after_close(fd):
        nonlocal injected
        if fd == report_fd and not injected:
            injected = True
            real_close(fd)
            raise OSError("injected post-publication close failure")
        return real_close(fd)

    monkeypatch.setattr(evaluator.os, "open", capture_open)
    monkeypatch.setattr(evaluator.os, "close", fail_after_close)
    result = evaluator._safe_write_report(run_dir, {"status": "complete"})
    assert injected is True
    assert result.read_text(encoding="utf-8").endswith("\n")
    assert stat.S_IMODE(result.stat().st_mode) == 0o400


def test_authority_check_stays_sealed_safe() -> None:
    result = evaluator.verify_corrected_data()
    assert result["val_frames"] == 376
    assert result["corrected_frames"] == 39
    assert result["test_included"] is False
    assert result["sealed_test_accessed"] is False
