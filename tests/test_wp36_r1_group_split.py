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
    "build_wp36_r1_group_split", REPO_ROOT / "scripts/build_wp36_r1_group_split.py"
)
assert SPEC is not None and SPEC.loader is not None
wp36_r1 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp36_r1
SPEC.loader.exec_module(wp36_r1)


def rows(relative: Path) -> list[dict[str, str]]:
    with (REPO_ROOT / relative).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def manifest() -> dict:
    return json.loads((REPO_ROOT / wp36_r1.MANIFEST_PATH).read_text(encoding="utf-8"))


def write_candidate(tmp_path: Path, splits: dict[str, list[str]]) -> Path:
    path = tmp_path / "candidate.json"
    path.write_text(json.dumps({"splits": splits}), encoding="utf-8")
    return path


def test_package_verifies_and_wp36_stays_pinned() -> None:
    result = wp36_r1.verify(REPO_ROOT)
    assert result["valid"] is True, result["errors"]


def test_owner_literal_ranking_outcome() -> None:
    data = manifest()
    assert data["objective_order"][:3] == [
        "unmet_requirements",
        "classes_with_2plus_test_groups",
        "band_violation",
    ]
    assert data["unmet_class_requirements"] == ["22"]
    assert data["objective"]["classes_with_2plus_test_groups"] == 17
    coverage = {row["derived_key"]: row for row in rows(wp36_r1.COVERAGE_PATH)}
    assert coverage["25"]["requirement_met"] == "True"
    assert int(coverage["22"]["val_groups"]) == 0


def test_hard_rules_hold() -> None:
    frames = rows(wp36_r1.FRAMES_PATH)
    splits_of: dict[str, set[str]] = {}
    for row in frames:
        splits_of.setdefault(row["group_id"], set()).add(row["split"])
    assert all(len(splits) == 1 for splits in splits_of.values())
    uses = Counter(row["use"] for row in frames)
    assert uses["QUARANTINED"] == 24 and uses["BACKGROUND"] == 1
    for row in rows(wp36_r1.GROUPS_PATH):
        if row["assignment"] == "FORCED_TRAIN":
            assert row["split"] == "train"


def test_ratio_uses_usable_frames() -> None:
    data = manifest()
    groups = rows(wp36_r1.GROUPS_PATH)
    assert sum(int(row["usable_frames"]) for row in groups) == sum(data["usable_frames"].values())
    assert sum(data["usable_frames"].values()) == 3215 - 24


def test_check_candidate_accepts_package_lists(tmp_path: Path) -> None:
    candidate = REPO_ROOT / wp36_r1.CANDIDATE_PATH
    assert wp36_r1.check_candidate(REPO_ROOT, candidate)["accepted"] is True


@pytest.mark.parametrize("stem", ["0060", "2999"])
def test_check_candidate_rejects_quarantined_stem(tmp_path: Path, stem: str) -> None:
    splits = json.loads((REPO_ROOT / wp36_r1.CANDIDATE_PATH).read_text(encoding="utf-8"))["splits"]
    group = next(row["group_id"] for row in rows(wp36_r1.FRAMES_PATH) if row["stem"] == stem)
    split = next(row["split"] for row in rows(wp36_r1.GROUPS_PATH) if row["group_id"] == group)
    splits[split] = sorted([*splits[split], stem])
    result = wp36_r1.check_candidate(REPO_ROOT, write_candidate(tmp_path, splits))
    assert result["accepted"] is False
    assert any("quarantined stem" in error for error in result["errors"])


def test_check_candidate_rejects_changed_test_list(tmp_path: Path) -> None:
    splits = json.loads((REPO_ROOT / wp36_r1.CANDIDATE_PATH).read_text(encoding="utf-8"))["splits"]
    splits["test"] = splits["test"][1:]
    result = wp36_r1.check_candidate(REPO_ROOT, write_candidate(tmp_path, splits))
    assert result["accepted"] is False
    assert any("test list differs" in error for error in result["errors"])


def test_render_leaves_no_temp_file_in_repo() -> None:
    wp36_r1.render(REPO_ROOT)
    assert not list((REPO_ROOT / wp36_r1.GENERATED).glob(".wp36*"))


def test_tampered_wp36_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    pins = dict(wp36_r1.PINNED_SOURCES)
    pins["docs/review/wp36_independent_qa_record.md"] = "0" * 64
    monkeypatch.setattr(wp36_r1, "PINNED_SOURCES", pins)
    result = wp36_r1.verify(REPO_ROOT)
    assert result["valid"] is False
