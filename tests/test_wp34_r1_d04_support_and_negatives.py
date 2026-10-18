from __future__ import annotations

import csv
import importlib.util
import sys
from collections import Counter
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_wp34_r1_d04_support_and_negatives",
    REPO_ROOT / "scripts/build_wp34_r1_d04_support_and_negatives.py",
)
assert SPEC is not None and SPEC.loader is not None
wp34_r1 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp34_r1
SPEC.loader.exec_module(wp34_r1)


def rows(relative: Path) -> list[dict[str, str]]:
    with (REPO_ROOT / relative).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@pytest.mark.skipif(not wp34_r1.DEFAULT_RAW_ROOT.is_dir(), reason="no local DATASET01")
def test_package_verifies() -> None:
    result = wp34_r1.verify(REPO_ROOT, wp34_r1.DEFAULT_RAW_ROOT)
    assert result["valid"] is True, result["errors"]


def test_initial_wp34_stays_pinned() -> None:
    wp34_r1.verify_pins(REPO_ROOT)


def test_owner_part1_applied_and_42_classes_stay_pending() -> None:
    matrix = rows(wp34_r1.MATRIX_PATH)
    assert len(matrix) == 54
    assert Counter(row["proposed_option"] for row in matrix) == Counter(
        {
            "KEEP_FULL": 27,
            "OWNER_TRAIN_WITH_ENRICHMENT": 12,
            "KEEP_TRAIN_ONLY_UNVERIFIED": 9,
            "KEEP_TRAIN_AND_TEST_NO_VAL": 6,
        }
    )
    for row in matrix:
        owner = row["proposed_option"] == "OWNER_TRAIN_WITH_ENRICHMENT"
        assert row["owner_status"] == ("OWNER_APPROVED_D04_PART1" if owner else "PENDING")


def test_height_families_and_dominance_flag() -> None:
    matrix = rows(wp34_r1.MATRIX_PATH)
    families = Counter(row["family"] for row in matrix if row["family"])
    assert families == Counter({wp34_r1.FAMILIES["16"]: 3, wp34_r1.FAMILIES["43"]: 2})
    for row in matrix:
        expected = int(row["groups"]) >= 2 and float(row["largest_group_box_share"]) > 0.8
        assert (row["dominated"] == "True") == expected


def test_negative_audit_corrects_qa_findings() -> None:
    audit = {row["stem"]: row for row in rows(wp34_r1.NEGATIVES_PATH)}
    assert len(audit) == 25
    assert {row["decision"] for row in audit.values()} <= wp34_r1.DECISIONS
    for stem in ("2015", "2016", "2017", "2031", "2051"):
        assert audit[stem]["visible_classes_if_any"] == "32"
    for stem in ("2793", "2794", "2795", "2796", "2797"):
        assert audit[stem]["visible_classes_if_any"] == "50"
    for stem in ("1703", "1704", "1705", "1706", "1707", "1708"):
        assert audit[stem]["visible_classes_if_any"] == "39 40"
    assert audit["2766"]["visible_classes_if_any"] == "13"
    assert "cls41" not in audit["2723"]["rationale"]
    for row in audit.values():
        background = row["decision"] == "TRUE_NEGATIVE"
        assert row["proposed_use"] == (
            "DETECTOR_BACKGROUND" if background else "QUARANTINE_UNTIL_RELABELLED"
        )


def test_notes_require_classes_exactly_when_a_sign_is_present(tmp_path: Path) -> None:
    notes = rows(wp34_r1.NOTES_PATH)
    notes[3]["visible_classes_if_any"] = "13"
    target = tmp_path / wp34_r1.NOTES_PATH
    target.parent.mkdir(parents=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=wp34_r1.NOTE_FIELDS)
        writer.writeheader()
        writer.writerows(notes)
    original = wp34_r1.EXPECTED_NOTES_SHA256
    wp34_r1.EXPECTED_NOTES_SHA256 = wp34_r1.wp34.sha256_bytes(target.read_bytes())
    try:
        with pytest.raises(ValueError, match="exactly when a sign is present"):
            wp34_r1.load_notes(tmp_path, notes)
    finally:
        wp34_r1.EXPECTED_NOTES_SHA256 = original
