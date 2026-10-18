from __future__ import annotations

import csv
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_wp37_dataset_card", REPO_ROOT / "scripts/build_wp37_dataset_card.py"
)
assert SPEC is not None and SPEC.loader is not None
wp37 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp37
SPEC.loader.exec_module(wp37)
RAW = wp37.DEFAULT_RAW_ROOT


def rows(relative: Path) -> list[dict[str, str]]:
    with (REPO_ROOT / relative).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@pytest.mark.skipif(not RAW.is_dir(), reason="no local DATASET01")
def test_package_verifies() -> None:
    result = wp37.verify(REPO_ROOT, RAW)
    assert result["valid"] is True, result["errors"]


def test_capture_rows_cover_every_raw_frame_and_match_split() -> None:
    capture = rows(wp37.CAPTURE_PATH)
    assert len(capture) == 3216
    uses = Counter(row["use"] for row in capture)
    assert uses["QUARANTINED_G04"] == 1 and uses["QUARANTINED"] == 24 and uses["BACKGROUND"] == 1
    split = {row["stem"]: row for row in rows(wp37.SPLIT_FRAMES)}
    for row in capture:
        if row["stem"] in split:
            assert row["split"] == split[row["stem"]]["split"]


def test_card_numbers_match_the_split_manifest() -> None:
    manifest = json.loads((REPO_ROOT / wp37.MANIFEST_PATH).read_text(encoding="utf-8"))
    split = json.loads((REPO_ROOT / wp37.SPLIT_MANIFEST).read_text(encoding="utf-8"))
    summary = manifest["summary"]
    assert summary["test_seal_sha256"] == split["test_seal_sha256"]
    assert {s: summary["per_split"][s]["frames"] for s in wp37.SPLITS} == split["usable_frames"]
    assert summary["usable_frames"] == 3191
    assert summary["exif_frames"] == 0 and summary["gps_frames"] == 0
    card = (REPO_ROOT / wp37.CARD_PATH).read_text(encoding="utf-8")
    assert split["test_seal_sha256"] in card
    assert "052bc980a7206f8ddd1ec2e59098dbd60a42036d3c7f7384ace4fe6416cbaa76" in card


def test_group_lineage_and_class_card() -> None:
    groups = rows(wp37.LINEAGE_PATH)
    assert len(groups) == 54
    assert sum(int(row["frames"]) for row in groups) == 3215
    assert len({row["split"] for row in groups}) == 3
    classes = {row["derived_key"]: row for row in rows(wp37.CLASSES_PATH)}
    trained = [row for row in classes.values() if row["role"] == "CLASS"]
    assert len(trained) == 54
    assert sum(row["sealed_test"] == "False" for row in trained) == 22
    assert classes["38"]["d04_decision"] == "TRAIN_ONLY_UNVERIFIED"


@pytest.mark.parametrize(("value", "bucket"), [(59.9, "DARK"), (60.0, "DIM"), (100.0, "BRIGHT")])
def test_luma_bucket_edges(value: float, bucket: str) -> None:
    assert wp37.luma_bucket(value) == bucket


def test_tampered_input_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    pins = dict(wp37.PINNED_SOURCES)
    pins[str(wp37.SPLIT_MANIFEST)] = "0" * 64
    monkeypatch.setattr(wp37, "PINNED_SOURCES", pins)
    result = wp37.verify(REPO_ROOT, RAW)
    assert result["valid"] is False
