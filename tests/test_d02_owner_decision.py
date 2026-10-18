from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_d02_owner_decision", REPO_ROOT / "scripts/build_d02_owner_decision.py"
)
assert SPEC is not None and SPEC.loader is not None
d02 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = d02
SPEC.loader.exec_module(d02)


def registry() -> list[dict[str, str]]:
    with (REPO_ROOT / d02.REGISTRY_PATH).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_decision_package_verifies() -> None:
    result = d02.verify(REPO_ROOT)
    assert result["valid"] is True, result["errors"]
    overlay = json.loads((REPO_ROOT / d02.OVERLAY_PATH).read_text(encoding="utf-8"))
    assert overlay["decision"]["status"] == "OWNER_APPROVED"
    assert overlay["decision"]["selected_option"] == "D02-P1_WP31_R2_CAPTURE_GROUPS"
    assert overlay["governance"]["gate0"] == "BLOCKED"
    assert overlay["governance"]["training_authorized"] is False


def test_registry_matches_wp31_r2_capture_groups() -> None:
    rows = registry()
    assert len(rows) == 3215 and len({row["group_id"] for row in rows}) == 54
    assert "0248" not in {row["stem"] for row in rows}
    with (REPO_ROOT / d02.FRAMES).open(newline="", encoding="utf-8") as handle:
        frames = {row["stem"]: row["capture_group_id"] for row in csv.DictReader(handle)}
    assert all(frames[row["stem"]] == row["group_id"] for row in rows)


def write_candidate(tmp_path: Path, splits: dict[str, list[str]]) -> Path:
    path = tmp_path / "candidate.json"
    path.write_text(json.dumps({"splits": splits}), encoding="utf-8")
    return path


def test_group_aware_candidate_is_accepted(tmp_path: Path) -> None:
    rows = registry()
    groups = sorted({row["group_id"] for row in rows})
    test_groups = set(groups[:5])
    splits = {
        "train": [row["stem"] for row in rows if row["group_id"] not in test_groups],
        "test": [row["stem"] for row in rows if row["group_id"] in test_groups],
    }
    assert d02.check_candidate(REPO_ROOT, write_candidate(tmp_path, splits))["accepted"] is True


@pytest.mark.parametrize(
    ("splits", "message"),
    [
        ({"train": ["0001"], "test": ["0002"]}, "appears in both"),
        ({"train": ["0248"]}, "quarantined stem"),
        ({"train": ["9999"]}, "unknown stem"),
    ],
)
def test_leaking_candidates_are_rejected(tmp_path: Path, splits: dict, message: str) -> None:
    result = d02.check_candidate(REPO_ROOT, write_candidate(tmp_path, splits))
    assert result["accepted"] is False
    assert any(message in error for error in result["errors"])


def test_changed_lineage_fails_closed(tmp_path: Path) -> None:
    for relative in d02.PINNED_SOURCES:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPO_ROOT / relative).read_bytes())
    d02.verify_pins(tmp_path)
    frames = tmp_path / d02.FRAMES
    frames.write_text(
        frames.read_text(encoding="utf-8").replace("D02-C0002", "D02-C0003", 1), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="pinned D-02 source changed"):
        d02.verify_pins(tmp_path)
