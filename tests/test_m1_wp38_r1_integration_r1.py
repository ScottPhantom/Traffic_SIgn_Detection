from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def load():
    path = REPO_ROOT / "scripts/build_m1_yolo_dataset_wp38_r1_integration_r1.py"
    spec = importlib.util.spec_from_file_location("m1_wp38_r1_integration_r1_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


exporter = load()


def test_r1_manifest_and_contract_verify_without_test_access() -> None:
    assert exporter.verify(REPO_ROOT) == {
        "package": exporter.PACKAGE,
        "status": exporter.STATUS,
        "valid": True,
        "errors": [],
        "sealed_test_accessed": False,
        "training_authorized": False,
    }
    data = exporter.derive(REPO_ROOT)
    assert set(data["correction"]["records"]) == {
        f"{number:04d}" for number in range(1319, 1358)
    }


def test_r1_materialisation_is_atomic_and_train_val_only(tmp_path: Path) -> None:
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
    assert (out / "images/val/1319.png").is_symlink()
    assert (out / "labels/val/1319.txt").is_file()
    assert not (out / "images/test").exists()
    assert not (out / "labels/test").exists()
    assert not list(tmp_path.glob(".export.tmp-*"))


@pytest.mark.parametrize("attack", ["root", "images", "labels", "split", "leaf"])
def test_r1_rejects_linked_writable_paths_before_victim_mutation(
    tmp_path: Path, attack: str
) -> None:
    victim = tmp_path / "victim"
    victim.mkdir()
    sentinel = victim / "sentinel.txt"
    sentinel.write_text("unchanged", encoding="utf-8")
    out = tmp_path / "export"
    if attack == "root":
        out.symlink_to(victim, target_is_directory=True)
    else:
        out.mkdir()
        if attack in {"images", "labels"}:
            (out / attack).symlink_to(victim, target_is_directory=True)
        elif attack == "split":
            (out / "images").mkdir()
            (out / "images/train").symlink_to(victim, target_is_directory=True)
        else:
            (out / "images").mkdir()
            (out / "images/train").mkdir()
            (out / "images/train/0072.jpg").symlink_to(sentinel)
    before = sentinel.read_bytes()
    with pytest.raises(RuntimeError, match="output path already exists|unsafe writable"):
        exporter.materialise(
            REPO_ROOT,
            exporter.DEFAULT_RAW_ROOT,
            exporter.DEFAULT_WP35_ROOT,
            exporter.DEFAULT_WP38_ROOT,
            out,
        )
    assert sentinel.read_bytes() == before
    assert not list(tmp_path.glob(".export.tmp-*"))


def test_r1_rejects_linked_parent(tmp_path: Path) -> None:
    victim = tmp_path / "victim"
    victim.mkdir()
    linked_parent = tmp_path / "linked"
    linked_parent.symlink_to(victim, target_is_directory=True)
    with pytest.raises(RuntimeError, match="unsafe writable path component"):
        exporter.require_new_output(linked_parent / "export")
    assert list(victim.iterdir()) == []


def test_r1_has_no_sealed_test_export_command() -> None:
    actions = exporter.parser()._subparsers._group_actions[0].choices
    assert set(actions) == {"manifest", "verify", "export", "verify-export"}
    source = (REPO_ROOT / "scripts/build_m1_yolo_dataset_wp38_r1_integration_r1.py").read_text()
    assert "export-test" not in source
    assert "--final-eval" not in source


def test_r1_refuses_existing_regular_output_without_mutation(tmp_path: Path) -> None:
    out = tmp_path / "export"
    out.mkdir()
    marker = out / "marker"
    marker.write_bytes(b"owner")
    with pytest.raises(RuntimeError, match="output path already exists"):
        exporter.require_new_output(out)
    assert marker.read_bytes() == b"owner"
