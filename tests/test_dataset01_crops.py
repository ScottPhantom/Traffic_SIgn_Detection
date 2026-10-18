from __future__ import annotations

import importlib.util
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

REPO_ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_dataset01_crops", REPO_ROOT / "scripts/build_dataset01_crops.py"
)
assert SPEC is not None and SPEC.loader is not None
crops = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = crops
SPEC.loader.exec_module(crops)
RAW = crops.m1.DEFAULT_RAW_ROOT
WP35 = crops.m1.DEFAULT_WP35_ROOT
HAVE_DATA = RAW.is_dir() and WP35.is_dir()


def test_crop_keeps_gtsrb_border_and_box_coords() -> None:
    image = Image.new("RGB", (1000, 500), (0, 0, 0))
    patch, size, coords = crops.crop_one(image, 0.5, 0.5, 0.1, 0.2)
    assert patch.shape == (32, 32, 3) and patch.dtype == np.uint8
    assert size == (120, 120)  # 100 px box + 10 % border each side
    assert coords == (10, 10, 110, 110)


def test_small_sign_gets_minimum_five_pixel_border_and_clips_at_edge() -> None:
    image = Image.new("RGB", (100, 100))
    _patch, size, coords = crops.crop_one(image, 0.02, 0.5, 0.04, 0.1)
    assert coords[0] == 0 and size[0] == 4 + 5
    assert size[1] == 10 + 2 * 5


def test_manifest_shape_and_governance() -> None:
    manifest = json.loads((REPO_ROOT / crops.MANIFEST_PATH).read_text(encoding="utf-8"))
    assert set(manifest["splits"]) == {"train", "val"}
    assert manifest["splits"]["train"]["classes"] == 54
    assert manifest["splits"]["val"]["sources"] == {"DATASET01": 560}
    assert "sealed" in manifest["test"]


def test_export_test_refused_without_final_eval(capsys: pytest.CaptureFixture[str]) -> None:
    assert crops.main(["export-test"]) == 2
    assert "refused" in capsys.readouterr().err


@pytest.mark.skipif(not HAVE_DATA, reason="no local DATASET01/WP35")
def test_package_verifies() -> None:
    result = crops.verify(REPO_ROOT, RAW, WP35)
    assert result["valid"] is True, result["errors"]


@pytest.mark.skipif(not (crops.DEFAULT_OUT / "valid.p").is_file(), reason="package not exported")
def test_pickles_match_gtsrb_keys() -> None:
    with (crops.DEFAULT_OUT / "valid.p").open("rb") as handle:
        data = pickle.load(handle)
    assert set(data) == {"features", "labels", "sizes", "coords"}
    assert data["features"].shape[1:] == (32, 32, 3)
    assert len(data["labels"]) == len(data["features"]) == 560


def test_verify_rejects_missing_materialised_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    empty = {
        "features": np.zeros((0, 32, 32, 3), dtype=np.uint8),
        "labels": np.zeros((0,), dtype=np.uint8),
        "sizes": np.zeros((0, 2), dtype=np.uint16),
        "coords": np.zeros((0, 4), dtype=np.uint16),
    }
    built = {"train": (empty, []), "val": (empty, [])}
    summary = {
        split: crops.summarise(split, arrays, index)
        for split, (arrays, index) in built.items()
    }
    manifest = {"synthetic": True}
    monkeypatch.setattr(crops, "render", lambda *_args: (summary, built))
    monkeypatch.setattr(crops, "manifest_payload", lambda *_args: manifest)
    monkeypatch.setattr(crops, "signnames", lambda *_args: b"synthetic\n")
    monkeypatch.setattr(crops.m1, "verify_pins", lambda *_args: None)
    monkeypatch.setattr(crops, "MANIFEST_PATH", Path("manifest.json"))
    (tmp_path / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    result = crops.verify(tmp_path, tmp_path, tmp_path, tmp_path / "missing")
    assert result["valid"] is False
    assert any("materialised crop file missing" in error for error in result["errors"])

    out = tmp_path / "complete"
    crops.write(out, built, tmp_path)
    (out / "unexpected.bin").write_bytes(b"extra")
    result = crops.verify(tmp_path, tmp_path, tmp_path, out)
    assert result["valid"] is False
    assert any("crop roster differs" in error for error in result["errors"])
