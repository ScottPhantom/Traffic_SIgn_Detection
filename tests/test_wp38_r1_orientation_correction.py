from __future__ import annotations

import importlib.util
import io
import json
import shutil
from pathlib import Path

import pytest
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts/build_wp38_r1_orientation_correction.py"
SPEC = importlib.util.spec_from_file_location("wp38_r1", SCRIPT)
assert SPEC and SPEC.loader
wp38_r1 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(wp38_r1)
RAW_ROOT = REPO_ROOT / wp38_r1.RAW_ROOT_RELATIVE


def _copy_file(source_root: Path, target_root: Path, relative: Path) -> None:
    target = target_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_root / relative, target)


def _source_fixture(target_root: Path) -> Path:
    for relative in wp38_r1.PINNED_SOURCES:
        _copy_file(REPO_ROOT, target_root, Path(relative))
    _copy_file(REPO_ROOT, target_root, wp38_r1.BUILDER_PATH)
    for stem in wp38_r1.EXPECTED_STEMS:
        _copy_file(
            REPO_ROOT,
            target_root,
            wp38_r1.RAW_ROOT_RELATIVE / "archive/images" / f"{stem}.jpg",
        )
        _copy_file(
            REPO_ROOT,
            target_root,
            Path("data/processed/m1_yolo/labels/val") / f"{stem}.txt",
        )
    return target_root / wp38_r1.RAW_ROOT_RELATIVE


def test_exact_source_authorities_and_materialized_labels() -> None:
    records = wp38_r1.verify_exact_sources(REPO_ROOT, RAW_ROOT)
    assert tuple(records) == wp38_r1.EXPECTED_STEMS
    expected = wp38_r1.expected_materialized_labels(REPO_ROOT)
    assert sum(payload.count(b"\n") for payload in expected.values()) == 29
    assert [stem for stem, payload in expected.items() if not payload] == [
        f"{value:04d}" for value in range(1319, 1329)
    ]


def test_render_is_deterministic_and_pixel_exact() -> None:
    first = wp38_r1.render(REPO_ROOT, RAW_ROOT)
    second = wp38_r1.render(REPO_ROOT, RAW_ROOT)
    assert {path: wp38_r1.sha256_bytes(data) for path, data in first.items()} == {
        path: wp38_r1.sha256_bytes(data) for path, data in second.items()
    }
    source = Image.open(RAW_ROOT / "archive/images/1340.jpg").convert("RGB")
    derived = Image.open(
        io.BytesIO(first[wp38_r1.IMAGES_DIR / "1340.png"])
    ).convert("RGB")
    assert derived.tobytes() == source.transpose(Image.Transpose.ROTATE_90).tobytes()


def test_manifest_binds_independent_authorities_and_governance() -> None:
    manifest = json.loads(wp38_r1.render(REPO_ROOT, RAW_ROOT)[wp38_r1.MANIFEST_PATH])
    assert manifest["package"] == "M0-WP38-R1"
    assert manifest["frame_count"] == 39
    assert manifest["box_count"] == 29
    assert manifest["yolo_class_ids"] == [12, 14]
    assert manifest["source_authority_sha256"] == wp38_r1.PINNED_SOURCES[
        str(wp38_r1.IMAGE_INVENTORY)
    ]
    assert manifest["label_authority_sha256"] == wp38_r1.PINNED_SOURCES[
        str(wp38_r1.BOXES)
    ]
    assert manifest["raw_mutated"] is False
    assert manifest["sealed_test_accessed"] is False
    assert manifest["training_authorized"] is False


def test_tampered_raw_image_is_rejected_before_render(tmp_path: Path) -> None:
    raw_root = _source_fixture(tmp_path)
    path = raw_root / "archive/images/1319.jpg"
    with Image.open(path) as source:
        changed = source.convert("RGB")
    changed.putpixel((0, 0), (255, 0, 255))
    changed.save(path, format="JPEG")
    with pytest.raises(RuntimeError, match="raw image hash mismatch against authority: 1319"):
        wp38_r1.verify_exact_sources(tmp_path, raw_root)


def test_tampered_materialized_label_is_rejected_before_render(tmp_path: Path) -> None:
    raw_root = _source_fixture(tmp_path)
    path = tmp_path / "data/processed/m1_yolo/labels/val/1329.txt"
    fields = path.read_text(encoding="utf-8").split()
    fields[1] = f"{float(fields[1]) + 0.001:.6f}"
    path.write_text(" ".join(fields) + "\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="materialized val label differs from WP33 rules: 1329"):
        wp38_r1.verify_exact_sources(tmp_path, raw_root)


def test_noncanonical_and_symlinked_raw_roots_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="raw root is not canonical"):
        wp38_r1.canonical_raw_root(REPO_ROOT, tmp_path)

    expected = tmp_path / wp38_r1.RAW_ROOT_RELATIVE
    expected.parent.mkdir(parents=True)
    expected.symlink_to(RAW_ROOT, target_is_directory=True)
    with pytest.raises(RuntimeError, match="symlink component"):
        wp38_r1.canonical_raw_root(tmp_path, expected)


def test_current_r1_package_verifies_after_build() -> None:
    result = wp38_r1.verify(REPO_ROOT, RAW_ROOT)
    assert result["valid"] is True, result["errors"]
    assert result["sealed_test_accessed"] is False
