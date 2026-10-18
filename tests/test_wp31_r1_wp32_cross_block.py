from __future__ import annotations

import csv
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[1]


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


wp32 = load("build_wp32_cross_block_link_review")
wp31_r1 = load("build_wp31_r1_group_id_proposal")
RAW_ROOT = wp32.DEFAULT_RAW_ROOT


def read_csv(relative: Path) -> list[dict[str, str]]:
    with (REPO_ROOT / relative).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="module")
def frames() -> dict[str, dict[str, str]]:
    return {row["stem"]: row for row in read_csv(wp31_r1.FRAMES_PATH)}


@pytest.mark.skipif(not RAW_ROOT.is_dir(), reason="local DATASET01 copy not present")
def test_wp32_package_verifies() -> None:
    result = wp32.verify(REPO_ROOT, RAW_ROOT)
    assert result["valid"] is True, result["errors"]


def test_wp32_decisions_cover_every_candidate_and_c0079_rereview() -> None:
    decisions = read_csv(wp32.DECISIONS_PATH)
    assert len(decisions) == 71
    edges = [row for row in decisions if row["kind"].startswith("C0079_EDGE_")]
    assert len(edges) == 9
    assert all(
        (row["capture_decision"], row["physical_sign_decision"])
        == ("SAME_CAPTURE_CANDIDATE", "NOT_RELATED")
        for row in edges
    )
    subsequence = [row for row in decisions if row["kind"] == "C0079_SUBSEQUENCE"]
    assert len(subsequence) == 8
    assert all(
        row["physical_sign_decision"] == "SAME_PHYSICAL_SIGN_CANDIDATE" for row in subsequence
    )


def test_wp32_notes_are_pinned(tmp_path: Path) -> None:
    rows = read_csv(wp32.NOTES_PATH)
    rows[0]["capture_decision"] = "NOT_RELATED"
    target = tmp_path / wp32.NOTES_PATH
    target.parent.mkdir(parents=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    original = wp32.NOTES_PATH
    with pytest.raises(ValueError, match="review-notes anchor"):
        wp32.load_notes(tmp_path, [{"row_id": row["row_id"]} for row in rows])
    assert original == wp32.NOTES_PATH


def test_wp31_r1_package_verifies_and_keeps_boundary() -> None:
    result = wp31_r1.verify(REPO_ROOT)
    assert result["valid"] is True, result["errors"]
    manifest = json.loads((REPO_ROOT / wp31_r1.MANIFEST_PATH).read_text(encoding="utf-8"))
    assert manifest["d02_status"] == "PENDING" and manifest["gate0"] == "BLOCKED"
    assert manifest["training_authorized"] is False and manifest["split_authorized"] is False
    assert manifest["summary"]["capture"]["groups"] == 54
    assert manifest["summary"]["scene"]["groups"] == 63


def test_qa_p1_1_examples_are_now_one_capture_group(frames: dict[str, dict[str, str]]) -> None:
    # cls49 junction blocks and the cls29 sign chain named in the WP31 QA record.
    assert (
        len(
            {
                frames[s]["capture_group_id"]
                for s in ("0113", "0135", "0220", "0242", "0405", "0413")
            }
        )
        == 1
    )
    assert (
        len(
            {
                frames[s]["capture_group_id"]
                for s in ("1516", "1537", "1622", "1681", "1715", "1729")
            }
        )
        == 1
    )


def test_qa_p1_2_examples_are_now_one_scene_group(frames: dict[str, dict[str, str]]) -> None:
    assert len({frames[s]["scene_group_id"] for s in ("2068", "2070", "2103", "2112", "2155")}) == 1
    assert frames["2971"]["scene_group_id"] == frames["3000"]["scene_group_id"]


def test_every_wp32_link_is_respected(frames: dict[str, dict[str, str]]) -> None:
    for link in read_csv(wp32.LINKS_PATH):
        if link["relation"] != "LINK":
            continue
        key = "capture_group_id" if link["level"] == "capture" else "scene_group_id"
        assert frames[link["left_stem"]][key] == frames[link["right_stem"]][key], link["row_id"]


def test_scene_groups_nest_and_0248_is_ungrouped(frames: dict[str, dict[str, str]]) -> None:
    parents: dict[str, set[str]] = defaultdict(set)
    for row in frames.values():
        if row["scene_group_id"]:
            parents[row["scene_group_id"]].add(row["capture_group_id"])
    assert all(len(parent) == 1 for parent in parents.values())
    assert [stem for stem, row in frames.items() if not row["capture_group_id"]] == ["0248"]


def test_changed_overlay_fails_closed(tmp_path: Path) -> None:
    pins = {**wp31_r1.PINNED_SOURCES, **wp31_r1.PINNED_OVERLAYS}
    for relative in pins:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPO_ROOT / relative).read_bytes())
    wp31_r1.verify_pins(tmp_path)
    overlay = tmp_path / next(iter(wp31_r1.PINNED_OVERLAYS))
    overlay.write_bytes(overlay.read_bytes().replace(b"SAME_CAPTURE_CANDIDATE", b"NOT_RELATED", 1))
    with pytest.raises(ValueError, match="pinned WP31-R1 source changed"):
        wp31_r1.verify_pins(tmp_path)
