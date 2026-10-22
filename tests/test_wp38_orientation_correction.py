from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path

import pytest
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts/build_wp38_orientation_correction.py"
SPEC = importlib.util.spec_from_file_location("wp38", SCRIPT)
assert SPEC and SPEC.loader
wp38 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(wp38)
RAW_ROOT = REPO_ROOT / "data/raw/DATASET01/staging/052bc980a7206f8d/raw"


def test_ccw90_box_transform_is_exact_and_area_preserving() -> None:
    original = (7, 0.25, 0.75, 0.10, 0.20)
    derived = wp38.rotate_box_ccw90(original)
    assert derived == (7, 0.75, 0.75, 0.20, 0.10)
    assert original[3] * original[4] == pytest.approx(derived[3] * derived[4])


def test_exact_source_roster_and_split_binding() -> None:
    stems = wp38.discover_stems(REPO_ROOT)
    assert stems == tuple(f"{value:04d}" for value in range(1319, 1358))
    assert len(stems) == 39


def test_render_is_deterministic_and_preserves_decoded_pixels() -> None:
    first = wp38.render(REPO_ROOT, RAW_ROOT)
    second = wp38.render(REPO_ROOT, RAW_ROOT)
    assert {path: wp38.sha256_bytes(data) for path, data in first.items()} == {
        path: wp38.sha256_bytes(data) for path, data in second.items()
    }
    source = Image.open(RAW_ROOT / "archive/images/1340.jpg").convert("RGB")
    derived = Image.open(io.BytesIO(first[wp38.IMAGES_DIR / "1340.png"])).convert("RGB")
    expected = source.transpose(Image.Transpose.ROTATE_90)
    assert derived.size == (960, 540)
    assert derived.tobytes() == expected.tobytes()


def test_render_has_exact_geometry_and_governance() -> None:
    artifacts = wp38.render(REPO_ROOT, RAW_ROOT)
    manifest = json.loads(artifacts[wp38.MANIFEST_PATH])
    assert manifest["frame_count"] == 39
    assert manifest["box_count"] == 29
    assert manifest["yolo_class_ids"] == [12, 14]
    assert manifest["rotation"] == "CCW_90"
    assert manifest["raw_mutated"] is False
    assert manifest["sealed_test_accessed"] is False
    assert manifest["training_authorized"] is False
    assert manifest["builder_path"] == str(wp38.BUILDER_PATH)
    assert manifest["builder_sha256"] == wp38.sha256_file(SCRIPT)
    labels = [path for path in artifacts if path.parent == wp38.LABELS_DIR]
    boxes = sum(len(wp38.parse_label(artifacts[path], str(path))) for path in labels)
    assert len(labels) == 39 and boxes == 29


def test_safe_target_rejects_symlink_and_hardlink(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.write_bytes(b"owner-data")
    symlink = tmp_path / "linked"
    symlink.symlink_to(outside)
    with pytest.raises(RuntimeError, match="unsafe existing"):
        wp38._assert_safe_target(tmp_path, Path("linked"))
    hardlink = tmp_path / "hard"
    hardlink.hardlink_to(outside)
    with pytest.raises(RuntimeError, match="unsafe existing"):
        wp38._assert_safe_target(tmp_path, Path("hard"))
    assert outside.read_bytes() == b"owner-data"


def test_actual_roster_rejects_hardlinked_artifact(tmp_path: Path) -> None:
    package_root = tmp_path / wp38.PACKAGE_ROOT
    package_root.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.write_bytes(b"owner-data")
    (package_root / "artifact").hardlink_to(outside)
    with pytest.raises(RuntimeError, match="contains hardlink"):
        wp38._actual_roster(tmp_path)
    assert outside.read_bytes() == b"owner-data"


def test_current_package_verifies_after_build() -> None:
    result = wp38.verify(REPO_ROOT, RAW_ROOT)
    assert result["valid"] is True, result["errors"]
    assert result["sealed_test_accessed"] is False
