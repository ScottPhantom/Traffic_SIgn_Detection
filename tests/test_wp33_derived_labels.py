from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_wp33_derived_labels", REPO_ROOT / "scripts/build_wp33_derived_labels.py"
)
assert SPEC is not None and SPEC.loader is not None
wp33 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp33
SPEC.loader.exec_module(wp33)
RAW_ROOT = wp33.DEFAULT_RAW_ROOT
pytestmark = pytest.mark.skipif(not RAW_ROOT.is_dir(), reason="local DATASET01 copy not present")


@pytest.fixture(scope="module")
def boxes() -> dict[str, dict[str, str]]:
    with (REPO_ROOT / wp33.BOXES_PATH).open(newline="", encoding="utf-8") as handle:
        return {f"{row['stem']}:{row['line']}": row for row in csv.DictReader(handle)}


def test_package_verifies() -> None:
    result = wp33.verify(REPO_ROOT, RAW_ROOT)
    assert result["valid"] is True, result["errors"]


def test_every_raw_box_is_present_once(boxes: dict[str, dict[str, str]]) -> None:
    assert len(boxes) == 8334


def test_class_23_is_one_combined_class(boxes: dict[str, dict[str, str]]) -> None:
    rows = [row for row in boxes.values() if row["raw_class"] == "23" and row["stem"] != "0248"]
    assert len(rows) == 465
    assert {row["derived_key"] for row in rows} == {"23"}
    assert {row["derived_code"] for row in rows} == {"P.111a+P.111b"}


def test_height_values_and_exclusions(boxes: dict[str, dict[str, str]]) -> None:
    assert boxes["0580:1"]["derived_key"] == "16:2.0"
    assert boxes["0600:2"]["derived_key"] == "16:2.5"
    assert boxes["0810:4"]["derived_key"] == "16:2.2"
    assert boxes["0590:1"]["derived_key"] == "43:2.5"
    assert boxes["0753:10"]["derived_key"] == "43:2.7"
    for box_id in ("2088:2", "2278:2", "2279:2", "0776:7"):
        assert boxes[box_id]["derived_key"] == "16:UNREADABLE"
        assert boxes[box_id]["train_eligible"] == "False"
    assert boxes["0776:7"]["raw_class"] == "18"


def test_unknown_and_quarantine_are_not_trainable(boxes: dict[str, dict[str, str]]) -> None:
    unknown = [row for row in boxes.values() if row["raw_class"] == "31"]
    assert unknown and all(
        row["derived_key"] == "UNKNOWN" and row["train_eligible"] == "False" for row in unknown
    )
    quarantined = [row for row in boxes.values() if row["stem"] == "0248"]
    assert len(quarantined) == 2 and all(row["train_eligible"] == "False" for row in quarantined)


def test_raw_labels_are_unchanged() -> None:
    with (REPO_ROOT / wp33.INVENTORY).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            assert (
                wp33.sha256_bytes((RAW_ROOT / row["label_path"]).read_bytes())
                == row["label_sha256"]
            )


def test_changed_decision_fails_closed(tmp_path: Path) -> None:
    for relative in wp33.PINNED_SOURCES:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPO_ROOT / relative).read_bytes())
    wp33.verify_pins(tmp_path)
    heights = tmp_path / wp33.HEIGHTS
    heights.write_text(
        heights.read_text(encoding="utf-8").replace(",2.0,", ",2.2,", 1), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="pinned WP33 source changed"):
        wp33.verify_pins(tmp_path)
