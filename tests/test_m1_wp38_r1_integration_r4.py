from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def load():
    path = REPO_ROOT / "scripts/build_m1_yolo_dataset_wp38_r1_integration_r4.py"
    spec = importlib.util.spec_from_file_location(
        "m1_wp38_r1_integration_r4_under_test", path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


exporter = load()


def write_marker(root: Path) -> Path:
    marker = root / exporter.COMPLETE_MARKER
    marker.write_bytes(exporter._marker_bytes())
    return marker


def test_r4_manifest_verifies_without_test_access() -> None:
    assert exporter.verify(REPO_ROOT) == {
        "package": exporter.PACKAGE,
        "status": exporter.STATUS,
        "valid": True,
        "errors": [],
        "sealed_test_accessed": False,
        "training_authorized": False,
    }


@pytest.mark.parametrize("attack", ["regular", "symlink", "hardlink"])
def test_marker_swap_during_semantic_replay_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, attack: str
) -> None:
    out = tmp_path / "out"
    out.mkdir()
    marker = write_marker(out)
    external = tmp_path / "external-marker.json"
    external.write_bytes(exporter._marker_bytes())

    def swap_marker(*_args, **_kwargs) -> None:
        marker.unlink()
        if attack == "regular":
            replacement = tmp_path / "replacement-marker.json"
            replacement.write_bytes(exporter._marker_bytes())
            os.replace(replacement, marker)
        elif attack == "symlink":
            marker.symlink_to(external)
        else:
            os.link(external, marker)

    monkeypatch.setattr(exporter, "_verify_descriptor_tree", swap_marker)
    result = exporter.verify_materialised(
        REPO_ROOT,
        exporter.DEFAULT_RAW_ROOT,
        exporter.DEFAULT_WP35_ROOT,
        exporter.DEFAULT_WP38_ROOT,
        out,
    )
    assert result["valid"] is False
    assert "EXPORT_COMPLETE.json" in result["errors"][0]


@pytest.mark.parametrize("attack", ["root", "parent"])
def test_output_directory_swap_during_replay_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, attack: str
) -> None:
    parent = tmp_path / "parent"
    out = parent / "out"
    out.mkdir(parents=True)
    write_marker(out)

    def swap_directory(*_args, **_kwargs) -> None:
        if attack == "root":
            detached = parent / "detached"
            out.rename(detached)
            out.mkdir()
            write_marker(out)
        else:
            detached_parent = tmp_path / "detached-parent"
            parent.rename(detached_parent)
            out.mkdir(parents=True)
            write_marker(out)

    monkeypatch.setattr(exporter, "_verify_descriptor_tree", swap_directory)
    result = exporter.verify_materialised(
        REPO_ROOT,
        exporter.DEFAULT_RAW_ROOT,
        exporter.DEFAULT_WP35_ROOT,
        exporter.DEFAULT_WP38_ROOT,
        out,
    )
    assert result["valid"] is False
    assert "binding changed" in result["errors"][0]


def test_expected_materialiser_inode_rejects_valid_public_replacement(
    tmp_path: Path,
) -> None:
    out = tmp_path / "out"
    out.mkdir()
    write_marker(out)
    result = exporter.verify_materialised(
        REPO_ROOT,
        exporter.DEFAULT_RAW_ROOT,
        exporter.DEFAULT_WP35_ROOT,
        exporter.DEFAULT_WP38_ROOT,
        out,
        expected_root_identity=(0, 0),
    )
    assert result["valid"] is False
    assert "not the inode created by materialiser" in result["errors"][0]


def test_r4_materialisation_and_descriptor_verification(tmp_path: Path) -> None:
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
    assert (out / exporter.COMPLETE_MARKER).read_text() == (
        json.dumps(exporter._expected_marker(), indent=2, sort_keys=True) + "\n"
    )
    verified = exporter.verify_materialised(
        REPO_ROOT,
        exporter.DEFAULT_RAW_ROOT,
        exporter.DEFAULT_WP35_ROOT,
        exporter.DEFAULT_WP38_ROOT,
        out,
    )
    assert verified["valid"] is True
    assert not (out / "images/test").exists()
    assert not (out / "labels/test").exists()


def test_r4_has_no_sealed_test_export_command() -> None:
    actions = exporter.parser()._subparsers._group_actions[0].choices
    assert set(actions) == {"manifest", "verify", "export", "verify-export"}
    source = (
        REPO_ROOT / "scripts/build_m1_yolo_dataset_wp38_r1_integration_r4.py"
    ).read_text()
    assert "export-test" not in source
    assert "--final-eval" not in source


def test_directory_chain_cleanup_on_open_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    parent = tmp_path / "parent"
    child = parent / "child"
    child.mkdir(parents=True)
    real_open = os.open
    calls = 0

    def failing_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal calls
        calls += 1
        if calls == 3:
            raise RuntimeError("injected chain failure")
        return real_open(path, flags, mode, dir_fd=dir_fd)

    before = set(os.listdir("/dev/fd"))
    monkeypatch.setattr(exporter.os, "open", failing_open)
    with pytest.raises(RuntimeError, match="injected chain failure"):
        exporter._open_directory_chain(child)
    assert set(os.listdir("/dev/fd")) == before


def test_r4_output_is_new_only(tmp_path: Path) -> None:
    out = tmp_path / "existing"
    out.mkdir()
    with pytest.raises(RuntimeError, match="already exists"):
        exporter.materialise(
            REPO_ROOT,
            exporter.DEFAULT_RAW_ROOT,
            exporter.DEFAULT_WP35_ROOT,
            exporter.DEFAULT_WP38_ROOT,
            out,
        )
    shutil.rmtree(out)
