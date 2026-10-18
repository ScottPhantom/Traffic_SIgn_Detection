from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/build_wp31_group_id_proposal.py"
SPEC = importlib.util.spec_from_file_location("build_wp31_group_id_proposal", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
wp31 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp31
SPEC.loader.exec_module(wp31)
graph = wp31.dataset_graph


def read_csv(relative: Path) -> list[dict[str, str]]:
    with (REPO_ROOT / relative).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="module")
def frames() -> list[dict[str, str]]:
    return read_csv(wp31.FRAMES_PATH)


@pytest.fixture(scope="module")
def payload() -> dict:
    return graph.build_graph_payload(REPO_ROOT)


def test_official_package_verifies() -> None:
    result = wp31.verify(REPO_ROOT)
    assert result == {
        "valid": True,
        "errors": [],
        "artifact_count": 7,
        "status": "WP31_GROUP_ID_PROPOSAL_AWAITING_OWNER_D02_DECISION",
    }
    manifest = json.loads((REPO_ROOT / wp31.MANIFEST_PATH).read_text(encoding="utf-8"))
    assert manifest["d02_status"] == "PENDING" and manifest["gate0"] == "BLOCKED"
    assert manifest["split_authorized"] is False and manifest["training_authorized"] is False
    assert manifest["final_group_truth_created"] is False
    assert manifest["summary"]["capture"]["groups"] == 85
    assert manifest["summary"]["scene"]["groups"] == 99


def test_every_frame_has_one_group_except_quarantined_0248(frames: list[dict[str, str]]) -> None:
    assert len(frames) == 3216
    ungrouped = [
        row["stem"] for row in frames if not row["capture_group_id"] or not row["scene_group_id"]
    ]
    assert ungrouped == ["0248"]
    by_stem = {row["stem"]: row for row in frames}
    assert by_stem["0247"]["capture_group_id"] == by_stem["0249"]["capture_group_id"]
    assert by_stem["0247"]["scene_group_id"] == by_stem["0249"]["scene_group_id"]


def test_no_same_capture_edge_crosses_capture_groups(
    frames: list[dict[str, str]], payload: dict
) -> None:
    for left, right, edge_id, *_rest, capture, _phy, _src, _conf in (
        (*edge[:6], edge[6], edge[7], edge[8], edge[9]) for edge in payload["edges"]
    ):
        if capture in {"S", "U"}:
            assert frames[left]["capture_group_id"] == frames[right]["capture_group_id"], edge_id


def test_scene_groups_nest_inside_capture_groups(frames: list[dict[str, str]]) -> None:
    parents: dict[str, set[str]] = defaultdict(set)
    for row in frames:
        if row["scene_group_id"]:
            parents[row["scene_group_id"]].add(row["capture_group_id"])
    assert all(len(capture) == 1 for capture in parents.values())


def test_scene_cuts_only_at_physical_sign_changes(payload: dict) -> None:
    cuts = read_csv(wp31.CUTS_PATH)
    edges = {f"edge_{edge[2]:06d}": edge for edge in payload["edges"]}
    assert cuts
    for row in cuts:
        edge = edges[row["edge_id"]]
        assert edge[6] in {"S", "U"} and edge[7] == "N"
    assert sum(row["cut_effective"] == "True" for row in cuts) == 40


def test_out_of_order_scenes_are_remerged(frames: list[dict[str, str]]) -> None:
    by_stem = {row["stem"]: row for row in frames}
    # WP30 edge_002977: stem 3015 continues the 3000-3004 scene after the 3005-3014 bridge segment,
    # and the bridge segment itself resumes the 2990-2998 cls13 scene across negative stem 2999.
    assert by_stem["3004"]["scene_group_id"] == by_stem["3015"]["scene_group_id"]
    assert by_stem["2998"]["scene_group_id"] == by_stem["3005"]["scene_group_id"]
    assert by_stem["3004"]["scene_group_id"] != by_stem["3005"]["scene_group_id"]


def test_negative_gaps_are_bridged_and_split_is_read_from_inventory(
    frames: list[dict[str, str]],
) -> None:
    gaps = read_csv(wp31.GAPS_PATH)
    assert len(gaps) == 12
    negatives = [stem for row in gaps for stem in row["negative_stems"].split()]
    assert len(negatives) == 25
    by_stem = {row["stem"]: row for row in frames}
    for row in gaps:
        group = by_stem[row["left_stem"]]["capture_group_id"]
        assert by_stem[row["right_stem"]]["capture_group_id"] == group
        assert all(
            by_stem[stem]["capture_group_id"] == group for stem in row["negative_stems"].split()
        )
        assert all(by_stem[stem]["split"] == "unassigned" for stem in row["negative_stems"].split())
    assert sum(row["split"] == "unassigned" for row in frames) == 25


def test_class_support_counts_independent_groups(frames: list[dict[str, str]]) -> None:
    support = {int(row["class_id"]): row for row in read_csv(wp31.SUPPORT_PATH)}
    assert len(support) == 52
    groups = {row["capture_group_id"] for row in frames if "36" in row["class_ids"].split()}
    assert int(support[36]["capture_groups"]) == len(groups) == 1
    assert support[36]["split_feasible_capture"] == "False"
    assert sum(row["split_feasible_capture"] == "False" for row in support.values()) == 18


@pytest.mark.parametrize("target", ["frames", "manifest", "overlay"])
def test_tampering_fails_closed(tmp_path: Path, target: str) -> None:
    manifest = json.loads((REPO_ROOT / wp31.MANIFEST_PATH).read_text(encoding="utf-8"))
    for record in manifest["sources"] + manifest["artifacts"]:
        destination = tmp_path / record["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / record["path"], destination)
    (tmp_path / wp31.MANIFEST_PATH).write_bytes((REPO_ROOT / wp31.MANIFEST_PATH).read_bytes())
    for relative in (graph.REVIEW_DIR,):
        for name in graph.SEQUENCE_OVERLAYS:
            shutil.copy2(REPO_ROOT / relative / name, tmp_path / relative / name)
    shutil.copy2(
        REPO_ROOT / "src/cpv301_autodrive/assets/dataset_graph.html",
        tmp_path / "dataset_graph.html",
    )
    assert wp31.verify(tmp_path)["valid"] is True
    if target == "frames":
        path = tmp_path / wp31.FRAMES_PATH
        path.write_text(
            path.read_text(encoding="utf-8").replace("D02-C0017", "D02-C0018", 1), encoding="utf-8"
        )
    elif target == "manifest":
        path = tmp_path / wp31.MANIFEST_PATH
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                '"training_authorized": false', '"training_authorized": true'
            ),
            encoding="utf-8",
        )
    else:
        path = tmp_path / graph.REVIEW_DIR / graph.EDGE_OVERLAYS[-1].annotations
        data = json.loads(path.read_text(encoding="utf-8"))
        data["decisions"][0]["physical_sign_hypothesis"] = "NOT_RELATED"
        path.write_text(json.dumps(data), encoding="utf-8")
    assert wp31.verify(tmp_path)["valid"] is False
