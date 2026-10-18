from __future__ import annotations

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
