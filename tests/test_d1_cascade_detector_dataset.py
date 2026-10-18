from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_d1_cascade_detector_dataset",
    REPO_ROOT / "scripts/build_d1_cascade_detector_dataset.py",
)
assert SPEC is not None and SPEC.loader is not None
cascade = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = cascade
SPEC.loader.exec_module(cascade)
RAW = cascade.m1.DEFAULT_RAW_ROOT
WP35 = cascade.m1.DEFAULT_WP35_ROOT
HAVE_DATA = RAW.is_dir() and WP35.is_dir()


def test_collapse_preserves_coordinates_and_rewrites_only_class() -> None:
    source = "53 0.1 0.2 0.3 0.4\n7 0.9 0.8 0.1 0.2\n"
    assert cascade.collapse_label_text(source) == (
        "0 0.1 0.2 0.3 0.4\n0 0.9 0.8 0.1 0.2\n"
    )
    assert cascade.collapse_label_text("") == ""


@pytest.mark.parametrize(
    "source",
    [
        "54 0.1 0.2 0.3 0.4\n",
        "0 0.1 0.2 0.3\n",
        "0 nan 0.2 0.3 0.4\n",
        "0 -0.1 0.2 0.3 0.4\n",
    ],
)
def test_collapse_rejects_invalid_source_labels(source: str) -> None:
    with pytest.raises(ValueError):
        cascade.collapse_label_text(source)


def test_manifest_is_train_val_only_and_binds_governed_source() -> None:
    payload = cascade.manifest_payload(REPO_ROOT)
    assert payload["classes"] == {"count": 1, "names": {"0": "traffic_sign"}}
    assert payload["allowed_splits"] == ["train", "val"]
    assert payload["test_included"] is False
    assert payload["counts"] == {
        "raw_train_frames": 1912,
        "raw_train_boxes": 5415,
        "raw_val_frames": 376,
        "raw_val_boxes": 560,
        "wp35_train_images": 1800,
    }
    assert payload["source_bindings"]["sealed_test_stem_list_sha256"].startswith("afa03d4b")


def test_cli_has_no_test_export_route() -> None:
    choices = cascade.parser()._subparsers._group_actions[0].choices
    assert set(choices) == {"manifest", "verify", "export", "verify-export"}
    assert all("test" not in name for name in choices)


def test_committed_manifest_verifies() -> None:
    result = cascade.verify_manifest(REPO_ROOT)
    assert result["valid"] is True, result["errors"]


@pytest.mark.skipif(not HAVE_DATA, reason="no local DATASET01/WP35")
def test_export_is_exact_idempotent_and_has_no_test(tmp_path: Path) -> None:
    out = tmp_path / "cascade"
    first = cascade.export(REPO_ROOT, RAW, WP35, out)
    assert first["frames"] == {"train": 3712, "val": 376}
    assert first["boxes"] == {"train": 12621, "val": 560}
    assert first["test_included"] is False
    assert not (out / "images/test").exists()
    assert not (out / "labels/test").exists()
    assert (out / "data.yaml").read_text(encoding="utf-8").count("traffic_sign") == 1
    labels = [path for path in (out / "labels/train").iterdir() if path.read_text().strip()]
    assert labels
    assert {line.split()[0] for line in labels[0].read_text().splitlines()} == {"0"}
    assert cascade.verify_export(REPO_ROOT, RAW, WP35, out)["valid"] is True

    second = cascade.export(REPO_ROOT, RAW, WP35, out)
    assert second["actions"] == {"reused": 8177}


@pytest.mark.skipif(not HAVE_DATA, reason="no local DATASET01/WP35")
def test_verifier_rejects_extra_or_tampered_output(tmp_path: Path) -> None:
    out = tmp_path / "cascade"
    cascade.export(REPO_ROOT, RAW, WP35, out)
    (out / "unexpected.bin").write_bytes(b"extra")
    result = cascade.verify_export(REPO_ROOT, RAW, WP35, out)
    assert result["valid"] is False
    assert "cascade output root roster differs" in result["errors"]
    (out / "unexpected.bin").unlink()

    label = next(path for path in (out / "labels/val").iterdir() if path.read_text().strip())
    label.write_text("0 0.5 0.5 1 1\n", encoding="utf-8")
    result = cascade.verify_export(REPO_ROOT, RAW, WP35, out)
    assert result["valid"] is False
    assert any("cascade label differs" in error for error in result["errors"])


@pytest.mark.skipif(not HAVE_DATA, reason="no local DATASET01/WP35")
def test_verifier_rejects_test_split_and_output_directory_symlinks(tmp_path: Path) -> None:
    out = tmp_path / "cascade"
    cascade.export(REPO_ROOT, RAW, WP35, out)
    test_dir = out / "images/test"
    test_dir.mkdir()
    (test_dir / "forbidden.jpg").write_bytes(b"sealed-test-sentinel")
    result = cascade.verify_export(REPO_ROOT, RAW, WP35, out)
    assert result["valid"] is False
    assert "cascade images split roster differs" in result["errors"]

    external = tmp_path / "external"
    external.mkdir()
    linked = tmp_path / "linked-output"
    linked.symlink_to(external, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink component"):
        cascade.export(REPO_ROOT, RAW, WP35, linked)


@pytest.mark.skipif(not HAVE_DATA, reason="no local DATASET01/WP35")
def test_real_cli_rejects_root_parent_and_nested_symlinks_before_writing(tmp_path: Path) -> None:
    script = REPO_ROOT / "scripts/build_d1_cascade_detector_dataset.py"

    def run(out: Path, command: str = "export") -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(script),
                command,
                "--repo-root",
                str(REPO_ROOT),
                "--raw-root",
                str(RAW),
                "--wp35-root",
                str(WP35),
                "--out",
                str(out),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

    external_root = tmp_path / "external-root"
    external_root.mkdir()
    linked_root = tmp_path / "linked-root"
    linked_root.symlink_to(external_root, target_is_directory=True)
    result = run(linked_root)
    assert result.returncode == 1 and "symlink component" in result.stderr
    assert list(external_root.iterdir()) == []
    verify = run(linked_root, "verify-export")
    assert verify.returncode == 1 and list(external_root.iterdir()) == []

    external_parent = tmp_path / "external-parent"
    external_parent.mkdir()
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(external_parent, target_is_directory=True)
    result = run(linked_parent / "nested")
    assert result.returncode == 1 and list(external_parent.iterdir()) == []

    nested_out = tmp_path / "nested-out"
    nested_out.mkdir()
    nested_target = tmp_path / "nested-target"
    nested_target.mkdir()
    (nested_out / "images").symlink_to(nested_target, target_is_directory=True)
    result = run(nested_out)
    assert result.returncode == 1 and list(nested_target.iterdir()) == []
