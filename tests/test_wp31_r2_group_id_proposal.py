from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_wp31_r2_group_id_proposal", REPO_ROOT / "scripts/build_wp31_r2_group_id_proposal.py"
)
assert SPEC is not None and SPEC.loader is not None
wp31_r2 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp31_r2
SPEC.loader.exec_module(wp31_r2)


def frames(relative: Path) -> dict[str, dict[str, str]]:
    with (REPO_ROOT / relative).open(newline="", encoding="utf-8") as handle:
        return {row["stem"]: row for row in csv.DictReader(handle)}


@pytest.fixture(scope="module")
def r2() -> dict[str, dict[str, str]]:
    return frames(wp31_r2.FRAMES_PATH)


def test_r2_package_verifies_and_keeps_boundary() -> None:
    result = wp31_r2.verify(REPO_ROOT)
    assert result["valid"] is True, result["errors"]
    manifest = json.loads((REPO_ROOT / wp31_r2.MANIFEST_PATH).read_text(encoding="utf-8"))
    assert manifest["package"] == "M0-WP31-R2"
    assert manifest["d02_status"] == "PENDING" and manifest["training_authorized"] is False
    assert manifest["summary"]["capture"]["groups"] == 54
    assert manifest["summary"]["scene"]["groups"] == 61


def test_capture_groups_are_identical_to_r1(r2: dict[str, dict[str, str]]) -> None:
    r1 = frames(Path("docs/review/generated/wp31_r1_group_id_frames.csv"))
    assert {s: row["capture_group_id"] for s, row in r1.items()} == {
        s: row["capture_group_id"] for s, row in r2.items()
    }


def test_every_negative_run_joins_both_bounding_scenes(r2: dict[str, dict[str, str]]) -> None:
    with (REPO_ROOT / wp31_r2.GAPS_PATH).open(newline="", encoding="utf-8") as handle:
        gaps = list(csv.DictReader(handle))
    assert len(gaps) == 12
    for gap in gaps:
        stems = [gap["left_stem"], *gap["negative_stems"].split(), gap["right_stem"]]
        assert len({r2[stem]["scene_group_id"] for stem in stems}) == 1, gap
        assert gap["scene_joined"] == "True"


def test_qa_p2_examples_are_fixed(r2: dict[str, dict[str, str]]) -> None:
    assert (
        r2["1514"]["scene_group_id"] == r2["1515"]["scene_group_id"] == r2["1516"]["scene_group_id"]
    )
    assert r2["2017"]["scene_group_id"] == r2["2018"]["scene_group_id"]
    assert r2["2051"]["scene_group_id"] == r2["2052"]["scene_group_id"]


def test_report_documents_the_p3_notes() -> None:
    report = (REPO_ROOT / wp31_r2.REPORT_PATH).read_text(encoding="utf-8")
    assert "R1 P3-1" in report and "x055–x063" in report
    assert "gains little" in report
    assert "neither level is proven leak-free" in report


def test_changed_r1_lineage_fails_closed(tmp_path: Path) -> None:
    for relative in {**wp31_r2.PINNED_SOURCES, **wp31_r2.PINNED_OVERLAYS}:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPO_ROOT / relative).read_bytes())
    wp31_r2.verify_pins(tmp_path)
    record = tmp_path / "docs/review/wp31_r1_wp32_independent_qa_record.md"
    record.write_text(record.read_text(encoding="utf-8").replace("P2", "P3"), encoding="utf-8")
    with pytest.raises(ValueError, match="pinned WP31-R2 source changed"):
        wp31_r2.verify_pins(tmp_path)
