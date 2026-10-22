from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def load():
    path = REPO_ROOT / "scripts/build_m1_yolo_dataset_wp38_r1_integration_r2.py"
    spec = importlib.util.spec_from_file_location("m1_wp38_r1_integration_r2_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


exporter = load()


def _close_fds(parent_fd: int, root_fd: int, children: dict[str, int]) -> None:
    for fd in children.values():
        os.close(fd)
    os.close(root_fd)
    os.close(parent_fd)


def test_r2_manifest_verifies_without_test_access() -> None:
    assert exporter.verify(REPO_ROOT) == {
        "package": exporter.PACKAGE,
        "status": exporter.STATUS,
        "valid": True,
        "errors": [],
        "sealed_test_accessed": False,
        "training_authorized": False,
    }


def test_directory_fd_writes_stay_on_open_inode_after_path_swap(tmp_path: Path) -> None:
    out = tmp_path / "export"
    detached = tmp_path / "detached"
    victim = tmp_path / "victim"
    victim.mkdir()
    sentinel = victim / "sentinel.txt"
    sentinel.write_bytes(b"unchanged")
    predecessor = exporter.load_predecessor(REPO_ROOT)
    parent_fd, root_fd, _output, _created = exporter._open_new_root(predecessor, out)
    children: dict[str, int] = {}
    try:
        out.rename(detached)
        out.symlink_to(victim, target_is_directory=True)
        children = exporter._safe_tree_fd(root_fd)
        exporter._write_exclusive_at(children["label_train"], "proof.txt", b"anchored")
        assert (detached / "labels/train/proof.txt").read_bytes() == b"anchored"
        assert sentinel.read_bytes() == b"unchanged"
        assert not (victim / "labels").exists()
        with pytest.raises(RuntimeError, match="output root identity changed"):
            exporter._require_root_identity(parent_fd, out, root_fd)
    finally:
        _close_fds(parent_fd, root_fd, children)


def test_directory_fd_exclusive_write_rejects_hardlinked_leaf(tmp_path: Path) -> None:
    out = tmp_path / "export"
    victim = tmp_path / "victim.txt"
    victim.write_bytes(b"owner")
    predecessor = exporter.load_predecessor(REPO_ROOT)
    parent_fd, root_fd, _output, _created = exporter._open_new_root(predecessor, out)
    children: dict[str, int] = {}
    try:
        children = exporter._safe_tree_fd(root_fd)
        os.link(victim, out / "labels/train/blocked.txt")
        with pytest.raises(FileExistsError):
            exporter._write_exclusive_at(
                children["label_train"], "blocked.txt", b"attacker"
            )
        assert victim.read_bytes() == b"owner"
    finally:
        _close_fds(parent_fd, root_fd, children)


def test_incomplete_output_without_last_marker_is_rejected(tmp_path: Path) -> None:
    out = tmp_path / "export"
    out.mkdir()
    with pytest.raises(FileNotFoundError):
        (out / exporter.COMPLETE_MARKER).lstat()
    result = exporter.verify_materialised(
        REPO_ROOT,
        exporter.DEFAULT_RAW_ROOT,
        exporter.DEFAULT_WP35_ROOT,
        exporter.DEFAULT_WP38_ROOT,
        out,
    )
    assert result["valid"] is False
    assert any("EXPORT_COMPLETE.json" in error for error in result["errors"])


def test_r2_materialisation_is_complete_train_val_only(tmp_path: Path) -> None:
    out = tmp_path / "export"
    result = exporter.materialise(
        REPO_ROOT,
        exporter.DEFAULT_RAW_ROOT,
        exporter.DEFAULT_WP35_ROOT,
        exporter.DEFAULT_WP38_ROOT,
        out,
    )
    assert result["verified"] is True
    assert result["sealed_test_accessed"] is False
    assert (out / exporter.COMPLETE_MARKER).is_file()
    assert (out / "images/val/1319.png").is_symlink()
    assert len(list((out / "images/train").iterdir())) == 3712
    assert len(list((out / "images/val").iterdir())) == 376
    assert not (out / "images/test").exists()
    assert not (out / "labels/test").exists()


def test_r2_has_no_sealed_test_export_command() -> None:
    actions = exporter.parser()._subparsers._group_actions[0].choices
    assert set(actions) == {"manifest", "verify", "export", "verify-export"}
    source = (REPO_ROOT / "scripts/build_m1_yolo_dataset_wp38_r1_integration_r2.py").read_text()
    assert "export-test" not in source
    assert "--final-eval" not in source
