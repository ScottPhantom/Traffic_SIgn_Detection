from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def load(name: str, relative: str):
    path = REPO_ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


exporter = load("test_m1_wp38_r1_exporter", "scripts/build_m1_yolo_dataset_wp38_r1.py")
bundle = load("test_m1_wp38_r1_bundle", "scripts/build_m1_colab_bundle_wp38_r1.py")


def test_integration_manifest_preserves_split_and_test_seal() -> None:
    result = exporter.verify(REPO_ROOT)
    assert result == {
        "package": exporter.PACKAGE,
        "status": exporter.STATUS,
        "valid": True,
        "errors": [],
        "sealed_test_accessed": False,
        "training_authorized": False,
    }
    successor = json.loads((REPO_ROOT / exporter.INTEGRATION_MANIFEST).read_text())
    base = json.loads(
        (REPO_ROOT / "docs/review/generated/m1_yolo_export_manifest.json").read_text()
    )
    for split in ("train", "val", "test"):
        assert (
            successor["splits"][split]["stem_list_sha256"]
            == base["splits"][split]["stem_list_sha256"]
        )
    assert successor["splits"]["train"]["labels_sha256"] == base["splits"]["train"][
        "labels_sha256"
    ]
    assert successor["splits"]["val"]["labels_sha256"] != base["splits"]["val"][
        "labels_sha256"
    ]
    assert successor["test_included"] is False
    assert successor["sealed_test_accessed"] is False


def test_derive_substitutes_only_the_39_validation_pairs() -> None:
    data = exporter.derive(REPO_ROOT)
    corrected = set(data["correction"]["records"])
    assert corrected == {f"{number:04d}" for number in range(1319, 1358)}
    assert corrected <= set(data["lists"]["val"])
    assert corrected.isdisjoint(data["lists"]["train"])
    assert corrected.isdisjoint(data["lists"]["test"])
    assert data["correction"]["manifest"]["box_count"] == 29
    assert data["correction"]["manifest"]["rotation"] == "CCW_90"


def test_materialised_export_has_corrected_pngs_and_no_test(tmp_path: Path) -> None:
    out = tmp_path / "m1_yolo_wp38_r1"
    result = exporter.materialise(
        REPO_ROOT,
        exporter.DEFAULT_RAW_ROOT,
        exporter.DEFAULT_WP35_ROOT,
        exporter.DEFAULT_WP38_ROOT,
        out,
    )
    assert result["verified"] is True
    assert result["sealed_test_accessed"] is False
    assert (out / "images/val/1319.png").is_file()
    assert not (out / "images/val/1319.jpg").exists()
    raw_val = next(
        stem
        for stem in exporter.derive(REPO_ROOT)["lists"]["val"]
        if not 1319 <= int(stem) <= 1357
    )
    assert (out / "images/val" / f"{raw_val}.jpg").is_file()
    assert not (out / "images/test").exists()
    assert not (out / "labels/test").exists()
    assert len(list((out / "images/val").iterdir())) == 376
    assert len(list((out / "images/train").iterdir())) == 3712


def test_successor_bundle_roster_is_exact_and_train_val_only() -> None:
    records, metadata = bundle.expected_records(REPO_ROOT)
    assert len(records) == 5927
    assert Counter(record["kind"] for record in records) == {
        "raw_image": 2249,
        "wp38_r1_image": 39,
        "wp38_r1_label": 39,
        "wp35_image": 1800,
        "wp35_label": 1800,
    }
    assert {record["source_split"] for record in records} == {"train", "val"}
    assert metadata["counts"]["raw_val_images"] == 337
    assert metadata["counts"]["wp38_r1_val_images"] == 39
    assert metadata["sealed_test_stem_list_sha256"].startswith("afa03d4b")


def test_bundle_build_refuses_dirty_checkout(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="clean committed checkout"):
        bundle.build_archive(REPO_ROOT, tmp_path / "candidate.tar.gz")


def test_successor_has_no_test_export_command() -> None:
    actions = exporter.parser()._subparsers._group_actions[0].choices
    assert set(actions) == {"manifest", "verify", "export", "verify-export"}
    source = (REPO_ROOT / exporter.BUILDER_PATH).read_text() if hasattr(
        exporter, "BUILDER_PATH"
    ) else (REPO_ROOT / "scripts/build_m1_yolo_dataset_wp38_r1.py").read_text()
    assert "export-test" not in source
    assert "--final-eval" not in source
