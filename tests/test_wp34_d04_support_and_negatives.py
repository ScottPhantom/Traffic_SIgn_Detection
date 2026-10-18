from __future__ import annotations

import csv
import importlib.util
import sys
from collections import Counter
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_wp34_d04_support_and_negatives",
    REPO_ROOT / "scripts/build_wp34_d04_support_and_negatives.py",
)
assert SPEC is not None and SPEC.loader is not None
wp34 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp34
SPEC.loader.exec_module(wp34)


def rows(relative: Path) -> list[dict[str, str]]:
    with (REPO_ROOT / relative).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@pytest.mark.skipif(not wp34.DEFAULT_RAW_ROOT.is_dir(), reason="local DATASET01 copy not present")
def test_package_verifies() -> None:
    result = wp34.verify(REPO_ROOT, wp34.DEFAULT_RAW_ROOT)
    assert result["valid"] is True, result["errors"]


def test_every_class_has_a_rule_consistent_proposal() -> None:
    matrix = rows(wp34.MATRIX_PATH)
    assert len(matrix) == 54
    for row in matrix:
        option, _reason = wp34.propose(int(row["groups"]), int(row["images"]))
        assert row["proposed_option"] == option
        assert row["owner_status"] == "PENDING"
    assert Counter(row["proposed_option"] for row in matrix) == Counter(
        {
            "KEEP_FULL": 27,
            "DROP_FROM_V1_COLLECT_MORE": 12,
            "KEEP_TRAIN_ONLY_UNVERIFIED": 9,
            "KEEP_TRAIN_AND_TEST_NO_VAL": 6,
        }
    )


@pytest.mark.parametrize(
    ("groups", "images", "expected"),
    [
        (3, 5, "KEEP_FULL"),
        (2, 500, "KEEP_TRAIN_AND_TEST_NO_VAL"),
        (1, 30, "KEEP_TRAIN_ONLY_UNVERIFIED"),
        (1, 29, "DROP_FROM_V1_COLLECT_MORE"),
    ],
)
def test_proposal_rule_boundaries(groups: int, images: int, expected: str) -> None:
    assert wp34.propose(groups, images)[0] == expected


def test_negative_audit_covers_all_25_and_flags_known_cases() -> None:
    audit = {row["stem"]: row for row in rows(wp34.NEGATIVES_PATH)}
    assert len(audit) == 25
    assert audit["1514"]["decision"] == audit["1515"]["decision"] == "UNLABELLED_SIGN_PRESENT"
    assert Counter(row["decision"] for row in audit.values()) == Counter(
        {"UNLABELLED_SIGN_PRESENT": 13, "TRUE_NEGATIVE": 7, "UNCLEAR": 5}
    )


def test_notes_are_pinned(tmp_path: Path) -> None:
    target = tmp_path / wp34.NOTES_PATH
    target.parent.mkdir(parents=True)
    target.write_text(
        (REPO_ROOT / wp34.NOTES_PATH)
        .read_text(encoding="utf-8")
        .replace("UNCLEAR", "TRUE_NEGATIVE"),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="notes anchor"):
        wp34.load_notes(tmp_path, [])
