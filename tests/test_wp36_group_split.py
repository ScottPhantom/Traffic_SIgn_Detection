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
    "build_wp36_group_split", REPO_ROOT / "scripts/build_wp36_group_split.py"
)
assert SPEC is not None and SPEC.loader is not None
wp36 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp36
SPEC.loader.exec_module(wp36)


def rows(relative: Path) -> list[dict[str, str]]:
    with (REPO_ROOT / relative).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_package_verifies() -> None:
    result = wp36.verify(REPO_ROOT)
    assert result["valid"] is True, result["errors"]


def test_no_group_in_two_splits_and_exclusions() -> None:
    frames = rows(wp36.FRAMES_PATH)
    split_of: dict[str, set[str]] = {}
    for row in frames:
        split_of.setdefault(row["group_id"], set()).add(row["split"])
    assert all(len(splits) == 1 for splits in split_of.values())
    assert len(split_of) == 54
    assert "0248" not in {row["stem"] for row in frames}
    uses = Counter(row["use"] for row in frames)
    assert uses["QUARANTINED"] == 24
    assert uses["BACKGROUND"] == 1
    assert next(row for row in frames if row["stem"] == "0544")["split"] == "train"


def test_forced_groups_and_wp35_sources_are_train() -> None:
    groups = {row["group_id"]: row for row in rows(wp36.GROUPS_PATH)}
    for row in groups.values():
        if row["assignment"] == "FORCED_TRAIN":
            assert row["split"] == "train"
    for row in rows(wp36.WP35_LINEAGE):
        assert groups[row["source_group_id"]]["split"] == "train"


def test_option_a_classes_reach_test_and_38_is_train_only() -> None:
    coverage = {row["derived_key"]: row for row in rows(wp36.COVERAGE_PATH)}
    for key in wp36.ONE_FREE_TEST:
        assert coverage[key]["required_splits"] == "train test"
        assert int(coverage[key]["test_groups"]) >= 1
    assert coverage["38"]["required_splits"] == "train"
    assert coverage["38"]["d04_decision"] == "TRAIN_ONLY_UNVERIFIED"


def test_manifest_seals_test_list() -> None:
    manifest = json.loads((REPO_ROOT / wp36.MANIFEST_PATH).read_text(encoding="utf-8"))
    candidate = json.loads((REPO_ROOT / wp36.CANDIDATE_PATH).read_text(encoding="utf-8"))
    test = "\n".join(sorted(candidate["splits"]["test"])).encode("utf-8")
    assert manifest["test_seal_sha256"] == wp36.sha256_bytes(test)
    assert manifest["training_authorized"] is False
    assert manifest["unmet_class_requirements"] == ["25"]


def test_scorer_ranks_class_requirements_above_ratio() -> None:
    data = wp36.load_inputs(REPO_ROOT)
    forced = wp36.forced_train(data)
    scorer = wp36.Scorer(data, forced)
    free = sorted(set(data["sizes"]) - forced)
    all_train = scorer.score(dict.fromkeys(free, "train"))
    assert all_train[0] < 0  # every val/test requirement unmet


def test_tampered_input_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    pins = dict(wp36.PINNED_SOURCES)
    pins[str(wp36.REGISTRY)] = "0" * 64
    monkeypatch.setattr(wp36, "PINNED_SOURCES", pins)
    result = wp36.verify(REPO_ROOT)
    assert result["valid"] is False
    assert any("pinned source changed" in error for error in result["errors"])
