from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_m1_yolo_dataset", REPO_ROOT / "scripts/build_m1_yolo_dataset.py"
)
assert SPEC is not None and SPEC.loader is not None
m1 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = m1
SPEC.loader.exec_module(m1)
RAW = m1.DEFAULT_RAW_ROOT
WP35 = m1.DEFAULT_WP35_ROOT


def test_manifest_verifies() -> None:
    result = m1.verify(REPO_ROOT)
    assert result["valid"] is True, result["errors"]


def test_class_map_is_the_54_wp33_classes_in_order() -> None:
    classes = m1.class_map(REPO_ROOT)
    assert [c["yolo_id"] for c in classes] == list(range(54))
    keys = [c["derived_key"] for c in classes]
    assert "UNKNOWN" not in keys and "16:UNREADABLE" not in keys
    assert len(set(keys)) == 54


def test_split_guard_matches_wp36_r1_and_excludes_quarantine() -> None:
    lists, frames = m1.split_lists(REPO_ROOT)
    manifest = json.loads((REPO_ROOT / m1.SPLIT_MANIFEST).read_text(encoding="utf-8"))
    assert {s: len(v) for s, v in lists.items()} == manifest["usable_frames"]
    quarantined = {r["stem"] for r in frames if r["use"] == "QUARANTINED"}
    assert len(quarantined) == 24
    assert not quarantined & {stem for stems in lists.values() for stem in stems}


def test_tampered_split_list_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    real = m1.read_csv

    def drop_one_test_frame(path: Path) -> list[dict[str, str]]:
        rows = real(path)
        if path.name == "wp36_r1_split_frames.csv":
            first = next(i for i, r in enumerate(rows) if r["split"] == "test")
            rows[first] = {**rows[first], "split": "train", "use": "TRAIN"}
        return rows

    monkeypatch.setattr(m1, "read_csv", drop_one_test_frame)
    with pytest.raises(ValueError, match="differs from the WP36-R1 manifest"):
        m1.split_lists(REPO_ROOT)


def test_label_text_uses_yolo_ids_in_line_order() -> None:
    boxes = [
        {"line": "2", "derived_key": "16:2.2", "x": "0.5", "y": "0.5", "w": "0.1", "h": "0.1"},
        {"line": "1", "derived_key": "0", "x": "0.1", "y": "0.2", "w": "0.03", "h": "0.04"},
    ]
    expected = "0 0.1 0.2 0.03 0.04\n17 0.5 0.5 0.1 0.1\n"
    assert m1.label_text(boxes, {"0": 0, "16:2.2": 17}) == expected


def test_export_test_is_refused_without_final_eval(capsys: pytest.CaptureFixture[str]) -> None:
    assert m1.main(["export-test", "--repo-root", str(REPO_ROOT)]) == 2
    assert "refused" in capsys.readouterr().err
    assert not (REPO_ROOT / m1.TEST_ACCESS_LOG).exists()


@pytest.mark.skipif(not (RAW.is_dir() and WP35.is_dir()), reason="no local DATASET01/WP35")
def test_export_writes_train_and_val_only(tmp_path: Path) -> None:
    result = m1.materialise(REPO_ROOT, RAW, WP35, tmp_path, ("train", "val"))
    assert result["written"] == {"train": 1912, "train_wp35": 1800, "val": 376}
    assert not (tmp_path / "images/test").exists()
    yaml = (tmp_path / "data.yaml").read_text(encoding="utf-8")
    assert "test:" not in yaml and '53: "51 W.246c"' in yaml
    label = (tmp_path / "labels/train/wp35_15_0000.txt").read_text(encoding="utf-8").split()
    assert label[0].isdigit()


@pytest.mark.skipif(not (RAW.is_dir() and WP35.is_dir()), reason="no local DATASET01/WP35")
def test_materialised_export_rejects_label_and_symlink_tampering(tmp_path: Path) -> None:
    m1.materialise(REPO_ROOT, RAW, WP35, tmp_path, ("train", "val"))
    label = tmp_path / "labels/train/0072.txt"
    label.write_text("0 0.5 0.5 0.9 0.9\n", encoding="utf-8")
    result = m1.verify_materialised(REPO_ROOT, RAW, WP35, tmp_path, ("train", "val"))
    assert result["valid"] is False
    assert any("0072.txt" in error for error in result["errors"])

    m1.materialise(REPO_ROOT, RAW, WP35, tmp_path, ("train", "val"))
    image = tmp_path / "images/train/0072.jpg"
    image.unlink()
    image.symlink_to(RAW / "archive/images/0073.jpg")
    result = m1.verify_materialised(REPO_ROOT, RAW, WP35, tmp_path, ("train", "val"))
    assert result["valid"] is False
    assert any("0072.jpg" in error for error in result["errors"])


def test_materialised_export_rejects_coherent_wp35_source_label_tamper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw_root = tmp_path / "raw"
    wp35_root = tmp_path / "wp35"
    out = tmp_path / "out"
    (raw_root / "archive/images").mkdir(parents=True)
    (wp35_root / "images").mkdir(parents=True)
    (wp35_root / "labels").mkdir(parents=True)
    for split in ("images/train", "labels/train"):
        (out / split).mkdir(parents=True)
    raw_bytes, image_bytes = b"raw-image", b"wp35-image"
    source_label = b"1 0.5 0.5 0.1 0.1\n"
    (raw_root / "archive/images/a.jpg").write_bytes(raw_bytes)
    (wp35_root / "images/wp.jpg").write_bytes(image_bytes)
    (wp35_root / "labels/wp.txt").write_bytes(source_label)
    (out / "images/train/a.jpg").write_bytes(raw_bytes)
    (out / "images/train/wp.jpg").write_bytes(image_bytes)
    (out / "labels/train/a.txt").write_bytes(b"")
    (out / "labels/train/wp.txt").write_bytes(b"0 0.5 0.5 0.1 0.1\n")
    names = {0: "class"}
    (out / "data.yaml").write_bytes(m1.dataset_yaml(out, ("train",), names))
    fake = {
        "classes": [{"yolo_id": 0, "name": "class"}],
        "ids": {"1": 0},
        "labels": {"train": {"a": ""}, "val": {}, "test": {}},
        "wp35": {
            "wp": {
                "image_sha256": hashlib.sha256(image_bytes).hexdigest(),
                "label_sha256": hashlib.sha256(source_label).hexdigest(),
            }
        },
    }
    monkeypatch.setattr(m1, "derive", lambda _root: fake)
    monkeypatch.setattr(
        m1,
        "read_csv",
        lambda _path: [{"stem": "a", "image_sha256": hashlib.sha256(raw_bytes).hexdigest()}],
    )
    assert m1.verify_materialised(
        tmp_path, raw_root, wp35_root, out, ("train",)
    )["valid"]
    changed = b"1 0.4 0.5 0.1 0.1\n"
    (wp35_root / "labels/wp.txt").write_bytes(changed)
    (out / "labels/train/wp.txt").write_bytes(b"0 0.4 0.5 0.1 0.1\n")
    result = m1.verify_materialised(tmp_path, raw_root, wp35_root, out, ("train",))
    assert result["valid"] is False
    assert any("source label differs" in error for error in result["errors"])
