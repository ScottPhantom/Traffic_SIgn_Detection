from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def load():
    path = REPO_ROOT / "scripts/build_m1_yolo_dataset_wp38_r1_integration_r3.py"
    spec = importlib.util.spec_from_file_location("m1_wp38_r1_integration_r3_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


exporter = load()


def valid_marker() -> dict[str, object]:
    return {
        "package": exporter.PACKAGE,
        "sealed_test_accessed": False,
        "status": "COMPLETE",
        "test_included": False,
        "written": dict(exporter.EXPECTED_WRITTEN),
    }


def test_r3_manifest_verifies_without_test_access() -> None:
    assert exporter.verify(REPO_ROOT) == {
        "package": exporter.PACKAGE,
        "status": exporter.STATUS,
        "valid": True,
        "errors": [],
        "sealed_test_accessed": False,
        "training_authorized": False,
    }


@pytest.mark.parametrize("attack", ["zero", "missing", "extra", "bool", "sealed", "package"])
def test_completion_marker_schema_and_counts_fail_closed(attack: str) -> None:
    marker = valid_marker()
    if attack == "zero":
        marker["written"] = {"train": 0, "train_wp35": 0, "val": 0}
    elif attack == "missing":
        del marker["written"]
    elif attack == "extra":
        marker["unexpected"] = True
    elif attack == "bool":
        marker["written"] = {"train": True, "train_wp35": 1800, "val": 376}
    elif attack == "sealed":
        marker["sealed_test_accessed"] = True
    else:
        marker["package"] = "M1-YOLO-WP38-R1-INTEGRATION-R2"
    with pytest.raises(RuntimeError, match="completion marker"):
        exporter._validate_marker(marker)


def test_partial_tree_failure_closes_every_descendant_fd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    root_fd = os.open(root, os.O_RDONLY)
    predecessor = exporter.load_predecessor(REPO_ROOT)
    calls = 0

    def failing_mkdir_open(parent_fd: int, name: str) -> int:
        nonlocal calls
        calls += 1
        if calls == 4:
            raise RuntimeError("injected partial-tree failure")
        return predecessor._mkdir_open(parent_fd, name)

    monkeypatch.setattr(
        exporter,
        "load_predecessor",
        lambda _repo_root: SimpleNamespace(_mkdir_open=failing_mkdir_open),
    )
    before = set(os.listdir("/dev/fd"))
    try:
        with pytest.raises(RuntimeError, match="injected partial-tree failure"):
            exporter._safe_tree_fd(root_fd)
        assert set(os.listdir("/dev/fd")) == before
    finally:
        os.close(root_fd)


def test_r3_materialisation_and_strict_verification(tmp_path: Path) -> None:
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
    marker = valid_marker()
    assert (out / exporter.COMPLETE_MARKER).read_text() == (
        json.dumps(marker, indent=2, sort_keys=True) + "\n"
    )
    assert exporter.verify_materialised(
        REPO_ROOT,
        exporter.DEFAULT_RAW_ROOT,
        exporter.DEFAULT_WP35_ROOT,
        exporter.DEFAULT_WP38_ROOT,
        out,
    )["valid"] is True
    assert not (out / "images/test").exists()
    assert not (out / "labels/test").exists()


def test_r3_has_no_sealed_test_export_command() -> None:
    actions = exporter.parser()._subparsers._group_actions[0].choices
    assert set(actions) == {"manifest", "verify", "export", "verify-export"}
    source = (REPO_ROOT / "scripts/build_m1_yolo_dataset_wp38_r1_integration_r3.py").read_text()
    assert "export-test" not in source
    assert "--final-eval" not in source
