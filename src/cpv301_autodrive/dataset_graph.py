"""Read-only DATASET01 proxy-grouping graph for the Streamlit evidence view.

Nodes are the 3,216 audited frames in stem order. Edges are the canonical WP5 numeric-adjacency
proxy edges, coloured by the provisional visual-review overlays (WP5 and WP7…WP29). Capture
components are a transitive closure over `SAME_CAPTURE_CANDIDATE` edges and are evidence only:
they are not owner-approved group truth, a final `group_id`, or a split.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cpv301_autodrive.config import PROJECT_ROOT

INVENTORY_PATH = Path("results/data_audit/DATASET01_052bc980a7206f8d/image_inventory.csv")
EDGE_DECISIONS_PATH = Path("docs/review/generated/wp5_provisional_edge_decisions.csv")
REVIEW_DIR = Path("docs/review")
TEMPLATE_PATH = Path(__file__).with_name("assets") / "dataset_graph.html"
QUARANTINED_STEMS = frozenset({"0248"})


@dataclass(frozen=True)
class Overlay:
    name: str
    annotations: str
    qa_passed: bool


# Effective edge-review overlays in canonical order. Corrected reissues (R1/R2) replace their
# QA-failed originals; WP27's decisions are unchanged by its R1/R2 layout/verifier fixes.
EDGE_OVERLAYS: tuple[Overlay, ...] = (
    Overlay("WP7", "wp7_visual_review_annotations_batch_a.json", True),
    Overlay("WP12-R1", "wp12_visual_review_annotations_batch_b.json", True),
    Overlay("WP13", "wp13_visual_review_annotations_batch_c.json", True),
    Overlay("WP14", "wp14_visual_review_annotations_batch_d.json", True),
    Overlay("WP15", "wp15_visual_review_annotations_batch_e.json", True),
    Overlay("WP22", "wp22_remaining_edge_review_annotations_batch_a.json", True),
    Overlay("WP23-R1", "wp23_r1_remaining_edge_review_annotations_batch_b.json", True),
    Overlay("WP24", "wp24_remaining_edge_review_annotations_batch_c.json", True),
    Overlay("WP25-R1", "wp25_r1_remaining_edge_review_annotations_batch_d.json", True),
    Overlay("WP26", "wp26_remaining_edge_review_annotations_batch_e.json", True),
    Overlay("WP27-R2", "wp27_remaining_edge_review_annotations_batch_f.json", True),
    # QA closure: docs/review/wp28_r2_wp29_independent_qa_record.md.
    Overlay("WP28-R2", "wp28_r2_remaining_edge_review_annotations_batch_g.json", True),
    Overlay("WP29", "wp29_remaining_edge_review_annotations_batch_h.json", True),
    # WP30 failed QA on one edge; the effective overlay is the WP30-R1 reissue, QA closure in
    # docs/review/wp30_r1_independent_qa_record.md.
    Overlay("WP30-R1", "wp30_r1_remaining_edge_review_annotations_batch_i.json", True),
)
SEQUENCE_OVERLAYS: tuple[str, ...] = (
    "wp16_sequence_review_annotations_batch_a.json",
    "wp17_sequence_review_annotations_batch_b.json",
    "wp18_sequence_review_annotations_batch_c.json",
    "wp19_sequence_review_annotations_batch_d.json",
    "wp20_sequence_review_annotations_batch_e.json",
    "wp21_final_eligible_sequence_review_annotations.json",
)
CAPTURE_CODES = {"SAME_CAPTURE_CANDIDATE": "S", "NOT_RELATED": "N", "UNRESOLVED": "U"}
PHYSICAL_CODES = {
    "SAME_PHYSICAL_SIGN_CANDIDATE": "S",
    "NOT_RELATED": "N",
    "UNRESOLVED": "U",
    "VISUALLY_RELATED_UNCERTAIN": "U",
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


Decision = tuple[str, str, str, str]


def _decisions(repo_root: Path, edges: list[dict[str, str]]) -> dict[str, Decision]:
    """Map edge_id -> (source, capture, physical_sign, confidence); fail on overlap or drift."""
    decisions: dict[str, Decision] = {}
    for edge in edges:
        if edge["review_status"] == "REVIEWED":
            decisions[edge["edge_id"]] = (
                "WP5",
                edge["capture_hypothesis"],
                edge["physical_sign_hypothesis"],
                edge["confidence"],
            )
    for overlay in EDGE_OVERLAYS:
        payload = json.loads((repo_root / REVIEW_DIR / overlay.annotations).read_text("utf-8"))
        for row in payload["decisions"]:
            if row["edge_id"] in decisions:
                raise ValueError(f"{overlay.name} re-reviews {row['edge_id']}")
            decisions[row["edge_id"]] = (
                overlay.name,
                row["capture_hypothesis"],
                row["physical_sign_hypothesis"],
                row["confidence"],
            )
    for source, capture, physical, _ in decisions.values():
        if capture not in CAPTURE_CODES or physical not in PHYSICAL_CODES:
            raise ValueError(f"{source} has unknown outcome {capture}/{physical}")
    return decisions


def _components(node_count: int, links: list[tuple[int, int]]) -> list[int]:
    parent = list(range(node_count))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for left, right in links:
        parent[find(left)] = find(right)
    return [find(index) for index in range(node_count)]


def build_graph_payload(repo_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    """Assemble the compact graph payload consumed by the HTML view."""
    inventory = _read_csv(repo_root / INVENTORY_PATH)
    edges = _read_csv(repo_root / EDGE_DECISIONS_PATH)
    decisions = _decisions(repo_root, edges)
    sources = ["WP5", *(overlay.name for overlay in EDGE_OVERLAYS)]
    qa = {"WP5": "pass"} | {o.name: "pass" if o.qa_passed else "await" for o in EDGE_OVERLAYS}

    index = {row["stem"]: position for position, row in enumerate(inventory)}
    nodes = [
        [row["stem"], 0 if row["split"] == "train" else 1, row["class_ids"], int(row["box_count"])]
        for row in inventory
    ]
    graph_edges: list[list[Any]] = []
    for edge in edges:
        left, right = edge["left_stem"], edge["right_stem"]
        if edge["edge_id"] in decisions:
            source, capture, physical, confidence = decisions[edge["edge_id"]]
            state = [CAPTURE_CODES[capture], PHYSICAL_CODES[physical], sources.index(source)]
            state.append(confidence[0])
        elif {left, right} & QUARANTINED_STEMS:
            state = ["Q", "Q", -1, "-"]
        else:
            state = ["P", "P", -1, "-"]
        graph_edges.append(
            [
                index[left],
                index[right],
                int(edge["edge_id"].removeprefix("edge_")),
                edge["proxy_status"][0],
                1 if edge["cross_split"] == "True" else 0,
                edge["proxy_sequence_id"],
                *state,
            ]
        )

    sequences: dict[str, str] = {}
    for name in SEQUENCE_OVERLAYS:
        payload = json.loads((repo_root / REVIEW_DIR / name).read_text("utf-8"))
        for row in payload["decisions"]:
            same = row["physical_sign_sequence"].startswith("SAME")
            sequences[row["proxy_sequence_id"]] = "S" if same else "M"

    comp = _components(len(nodes), [(e[0], e[1]) for e in graph_edges if e[6] == "S"])
    members = Counter(comp)
    split_sets: dict[int, set[int]] = {}
    for position, root in enumerate(comp):
        split_sets.setdefault(root, set()).add(nodes[position][1])
    multi = {root for root, size in members.items() if size > 1}
    mixed = {root for root in multi if len(split_sets[root]) == 2}

    summary = {
        "nodes": len(nodes),
        "edges": len(graph_edges),
        "train": sum(1 for node in nodes if node[1] == 0),
        "test": sum(1 for node in nodes if node[1] == 1),
        "cap": dict(Counter(e[6] for e in graph_edges)),
        "phy": dict(Counter(e[7] for e in graph_edges)),
        "cross": sum(e[4] for e in graph_edges),
        "bySource": {
            name: sum(1 for e in graph_edges if e[8] == i) for i, name in enumerate(sources)
        },
        "components": len(multi),
        "mixedComponents": len(mixed),
        "testImagesInMixed": sum(
            1 for position, root in enumerate(comp) if root in mixed and nodes[position][1] == 1
        ),
        "largest": max(members.values()),
        "sequences": len(sequences),
    }
    return {
        "nodes": nodes,
        "edges": graph_edges,
        "comp": comp,
        "sources": sources,
        "qa": qa,
        "seq": sequences,
        "summary": summary,
    }


def render_graph_html(payload: dict[str, Any], *, embedded: bool = False) -> str:
    """Inline the payload into the self-contained HTML/canvas view."""
    data = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    return template.replace("__EMBED__", "1" if embedded else "0").replace("__DATA__", data)
