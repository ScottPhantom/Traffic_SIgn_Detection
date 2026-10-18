#!/usr/bin/env python3
# ruff: noqa: E501
"""Build and verify M0-WP31: the D-02 group_id proposal package for DATASET01.

Reads the QA-passed provisional edge overlays (WP5, WP7, WP12-R1…WP15, WP22…WP30-R1) through
`cpv301_autodrive.dataset_graph` and proposes two leak-conservative grouping levels:

- capture group: connected components over edges reviewed as SAME_CAPTURE_CANDIDATE or
  UNRESOLVED (an unresolved edge is kept joined, never cut).
- scene group: a capture group cut only where the reviewed physical-sign relation is
  NOT_RELATED (the visible signs change), then sibling scenes inside the same capture group are
  re-merged when a non-adjacent scene starts where another stopped (last labelled frame of one and
  first labelled frame of the other overlap in classes (overlap coefficient |A∩B|/min(|A|,|B|) >= 0.5), because frames can be out of
  filename order (WP29 edge_002967, WP30 edge_002977) and the same physical sign may otherwise
  land on both sides of a cut.

WP5 has no proxy edge around the 25 empty-label ("unassigned") frames, so 37 consecutive stem
pairs were never reviewed. Capture groups join across each such negative run (leak-safe); scene
groups attach the negatives to the preceding scene and join the following scene only when the
two bounding labelled frames overlap in classes. Both levels also join stems 0247 and 0249 across
the quarantined stem 0248, whose two edges were never reviewed. Stem 0248 itself receives no group. Nothing here approves D-02, writes a split or
authorizes training.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from cpv301_autodrive import dataset_graph  # noqa: E402

PACKAGE_STATUS = "WP31_GROUP_ID_PROPOSAL_AWAITING_OWNER_D02_DECISION"
EVIDENCE_BOUNDARY = (
    "PROPOSAL_ONLY_FROM_PROVISIONAL_QA_PASSED_OVERLAYS_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_"
    "NO_SPLIT_NO_TRAINING"
)
SCENE_REMERGE_OVERLAP = 0.5
LARGE_GROUP_THRESHOLD = 100
QUARANTINE_BRIDGE = ("0247", "0249")
QUARANTINED_STEM = "0248"

GENERATED = Path("docs/review/generated")
FRAMES_PATH = GENERATED / "wp31_group_id_frames.csv"
GROUPS_PATH = GENERATED / "wp31_group_id_groups.csv"
CUTS_PATH = GENERATED / "wp31_scene_cut_edges.csv"
SUPPORT_PATH = GENERATED / "wp31_class_group_support.csv"
GAPS_PATH = GENERATED / "wp31_unreviewed_negative_gaps.csv"
REPORT_PATH = Path("docs/review/wp31_group_id_proposal_report.md")
MANIFEST_PATH = GENERATED / "wp31_group_id_manifest.json"
QA_RECORDS = (
    "docs/review/wp28_r2_wp29_independent_qa_record.md",
    "docs/review/wp30_independent_qa_record.md",
    "docs/review/wp30_r1_independent_qa_record.md",
)

FRAME_FIELDS = [
    "stem", "split", "class_ids", "box_count", "capture_group_id", "scene_group_id", "flags",
]
GAP_FIELDS = [
    "left_stem", "right_stem", "left_class_ids", "right_class_ids", "negative_stems",
    "capture_joined", "scene_joined",
]
GROUP_FIELDS = [
    "level", "group_id", "parent_capture_group_id", "size", "train", "test", "unassigned",
    "first_stem", "last_stem", "class_ids", "mixed_split", "large_group",
]
CUT_FIELDS = [
    "edge_id", "left_stem", "right_stem", "capture_group_id", "source_wp", "confidence",
    "left_scene_group_id", "right_scene_group_id", "cut_effective",
]
SUPPORT_FIELDS = [
    "class_id", "images", "capture_groups", "scene_groups", "largest_capture_group_share",
    "split_feasible_capture", "split_feasible_scene",
]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


class UnionFind:
    def __init__(self, size: int) -> None:
        self.parent = list(range(size))

    def find(self, index: int) -> int:
        while self.parent[index] != index:
            self.parent[index] = self.parent[self.parent[index]]
            index = self.parent[index]
        return index

    def union(self, left: int, right: int) -> None:
        self.parent[self.find(left)] = self.find(right)


def classes(node: list[Any]) -> set[str]:
    return set(node[2].split()) if node[2] else set()


def overlaps(left: set[str], right: set[str]) -> bool:
    return bool(left and right) and len(left & right) / min(len(left), len(right)) >= SCENE_REMERGE_OVERLAP


def negative_runs(nodes: list[list[Any]], edges: list[list[Any]]) -> list[tuple[int, list[int], int]]:
    """Return (left labelled, negatives, right labelled) for every run of edge-less adjacencies."""
    linked = {(edge[0], edge[1]) for edge in edges}
    runs: list[tuple[int, list[int], int]] = []
    position = 0
    while position < len(nodes) - 1:
        if (position, position + 1) in linked:
            position += 1
            continue
        start = position
        while position < len(nodes) - 1 and (position, position + 1) not in linked:
            position += 1
        negatives = list(range(start + 1, position))
        if any(nodes[i][3] != 0 for i in negatives) or nodes[start][3] == 0 or nodes[position][3] == 0:
            raise ValueError(f"unexpected edge-less adjacency at stem {nodes[start][0]}")
        runs.append((start, negatives, position))
    return runs


def number_groups(roots: list[int | None], prefix: str) -> list[str]:
    """Stable ids ordered by the first stem of each group."""
    names: dict[int, str] = {}
    for root in roots:
        if root is not None and root not in names:
            names[root] = f"{prefix}{len(names) + 1:04d}"
    return ["" if root is None else names[root] for root in roots]


def derive(repo_root: Path) -> dict[str, Any]:
    payload = dataset_graph.build_graph_payload(repo_root)
    nodes, edges, sources = payload["nodes"], payload["edges"], payload["sources"]
    if any(payload["qa"][name] != "pass" for name in sources):
        raise ValueError("every edge overlay must be independently QA-passed before WP31")
    if payload["summary"]["cap"].get("P", 0) != 0:
        raise ValueError("WP31 requires every review-eligible edge to be reviewed")
    index = {node[0]: position for position, node in enumerate(nodes)}
    quarantined = index[QUARANTINED_STEM]
    bridge = (index[QUARANTINE_BRIDGE[0]], index[QUARANTINE_BRIDGE[1]])

    inventory_split = {
        row["stem"]: row["split"] for row in dataset_graph._read_csv(repo_root / dataset_graph.INVENTORY_PATH)
    }
    runs = negative_runs(nodes, edges)
    if sum(len(negatives) + 1 for _l, negatives, _r in runs) != 37 or sum(len(n) for _l, n, _r in runs) != 25:
        raise ValueError("WP31 expects exactly 37 edge-less adjacencies around 25 negative frames")

    capture = UnionFind(len(nodes))
    for edge in edges:
        if edge[6] in {"S", "U"}:
            capture.union(edge[0], edge[1])
    capture.union(*bridge)
    for left, negatives, right in runs:
        for position in [*negatives, right]:
            capture.union(left, position)
    capture_roots: list[int | None] = [capture.find(i) for i in range(len(nodes))]
    capture_roots[quarantined] = None
    capture_ids = number_groups(capture_roots, "D02-C")

    scene = UnionFind(len(nodes))
    cuts: list[list[Any]] = []
    for edge in edges:
        if edge[6] not in {"S", "U"}:
            continue
        if edge[7] == "N":
            cuts.append(edge)
        else:
            scene.union(edge[0], edge[1])
    scene.union(*bridge)
    gap_rows = []
    for left, negatives, right in runs:
        for position in negatives:
            scene.union(left, position)
        joined = overlaps(classes(nodes[left]), classes(nodes[right]))
        if joined:
            scene.union(left, right)
        gap_rows.append(
            {
                "left_stem": nodes[left][0],
                "right_stem": nodes[right][0],
                "left_class_ids": nodes[left][2],
                "right_class_ids": nodes[right][2],
                "negative_stems": " ".join(nodes[i][0] for i in negatives),
                "capture_joined": True,
                "scene_joined": joined,
            }
        )
    raw_scene = [scene.find(i) for i in range(len(nodes))]
    # Boundary frames of each raw scene: the labelled frames at its first and last stem.
    members: dict[int, list[int]] = defaultdict(list)
    for position, root in enumerate(raw_scene):
        if position != quarantined and nodes[position][3] != 0:
            members[root].append(position)
    scene_capture = {root: capture_ids[positions[0]] for root, positions in members.items()}
    by_capture: dict[str, list[int]] = defaultdict(list)
    for root, capture_id in scene_capture.items():
        by_capture[capture_id].append(root)
    remerged_pairs = 0
    for siblings in by_capture.values():
        for a in range(len(siblings)):
            for b in range(a + 1, len(siblings)):
                first_a, last_a = members[siblings[a]][0], members[siblings[a]][-1]
                first_b, last_b = members[siblings[b]][0], members[siblings[b]][-1]
                # Out-of-order frames: one scene resumes where a non-adjacent sibling stopped.
                # Adjacent scenes are excluded: their boundary is the reviewed cut edge itself.
                resumes_b = first_b - last_a > 1 and overlaps(classes(nodes[last_a]), classes(nodes[first_b]))
                resumes_a = first_a - last_b > 1 and overlaps(classes(nodes[last_b]), classes(nodes[first_a]))
                if resumes_a or resumes_b:
                    if scene.find(siblings[a]) != scene.find(siblings[b]):
                        remerged_pairs += 1
                    scene.union(siblings[a], siblings[b])
    scene_roots: list[int | None] = [scene.find(i) for i in range(len(nodes))]
    scene_roots[quarantined] = None
    scene_ids = number_groups(scene_roots, "D02-S")

    frames = []
    for position, node in enumerate(nodes):
        flags = []
        if position == quarantined:
            flags.append("QUARANTINED_NO_GROUP")
        if position in bridge:
            flags.append("QUARANTINE_BRIDGE_0247_0249")
        if node[3] == 0:
            flags.append("NEGATIVE_NO_BOX_UNREVIEWED_BRIDGE")
        frames.append(
            {
                "stem": node[0],
                "split": inventory_split[node[0]],
                "class_ids": node[2],
                "box_count": node[3],
                "capture_group_id": capture_ids[position],
                "scene_group_id": scene_ids[position],
                "flags": ";".join(flags),
            }
        )

    groups = []
    for level, key in (("capture", "capture_group_id"), ("scene", "scene_group_id")):
        members: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for frame in frames:
            if frame[key]:
                members[frame[key]].append(frame)
        for group_id in sorted(members):
            rows = members[group_id]
            split_counts = Counter(row["split"] for row in rows)
            group_classes = sorted({c for row in rows for c in row["class_ids"].split()}, key=int)
            groups.append(
                {
                    "level": level,
                    "group_id": group_id,
                    "parent_capture_group_id": rows[0]["capture_group_id"],
                    "size": len(rows),
                    "train": split_counts["train"],
                    "test": split_counts["test"],
                    "unassigned": split_counts["unassigned"],
                    "first_stem": rows[0]["stem"],
                    "last_stem": rows[-1]["stem"],
                    "class_ids": " ".join(group_classes),
                    "mixed_split": split_counts["train"] > 0 and split_counts["test"] > 0,
                    "large_group": len(rows) > LARGE_GROUP_THRESHOLD,
                }
            )

    cut_rows = []
    for edge in cuts:
        left, right = edge[0], edge[1]
        cut_rows.append(
            {
                "edge_id": f"edge_{edge[2]:06d}",
                "left_stem": nodes[left][0],
                "right_stem": nodes[right][0],
                "capture_group_id": capture_ids[left],
                "source_wp": sources[edge[8]] if edge[8] >= 0 else "",
                "confidence": {"H": "HIGH", "M": "MEDIUM", "L": "LOW"}.get(edge[9], ""),
                "left_scene_group_id": scene_ids[left],
                "right_scene_group_id": scene_ids[right],
                "cut_effective": scene_ids[left] != scene_ids[right],
            }
        )

    support = []
    all_classes = sorted({c for node in nodes for c in classes(node)}, key=int)
    for class_id in all_classes:
        rows = [f for f in frames if class_id in f["class_ids"].split() and f["capture_group_id"]]
        capture_sizes = Counter(row["capture_group_id"] for row in rows)
        scene_count = len({row["scene_group_id"] for row in rows})
        support.append(
            {
                "class_id": int(class_id),
                "images": len(rows),
                "capture_groups": len(capture_sizes),
                "scene_groups": scene_count,
                "largest_capture_group_share": round(max(capture_sizes.values()) / len(rows), 4),
                # Train, validation and test each need at least one independent group.
                "split_feasible_capture": len(capture_sizes) >= 3,
                "split_feasible_scene": scene_count >= 3,
            }
        )
    return {
        "frames": frames,
        "groups": groups,
        "cuts": cut_rows,
        "support": support,
        "gaps": gap_rows,
        "remerged_scene_pairs": remerged_pairs,
        "sources": sources,
    }


def to_csv(rows: list[dict[str, Any]], fields: list[str]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def level_summary(groups: list[dict[str, Any]], level: str) -> dict[str, Any]:
    rows = [row for row in groups if row["level"] == level]
    sizes = sorted((row["size"] for row in rows), reverse=True)
    return {
        "groups": len(rows),
        "multi_frame_groups": sum(size > 1 for size in sizes),
        "singletons": sum(size == 1 for size in sizes),
        "mixed_split_groups": sum(row["mixed_split"] for row in rows),
        "large_groups": sum(row["large_group"] for row in rows),
        "largest_sizes": sizes[:8],
        "largest_share": round(sizes[0] / sum(sizes), 4),
    }


def render_report(derived: dict[str, Any], summary: dict[str, Any]) -> str:
    capture, scene = summary["capture"], summary["scene"]
    effective_cuts = [row for row in derived["cuts"] if row["cut_effective"]]
    large_scene = [
        row for row in derived["groups"] if row["level"] == "scene" and row["large_group"]
    ]
    infeasible = [row for row in derived["support"] if not row["split_feasible_capture"]]
    infeasible_scene = [row for row in derived["support"] if not row["split_feasible_scene"]]
    large_lines = "\n".join(
        f"| `{row['group_id']}` | `{row['parent_capture_group_id']}` | {row['size']} | "
        f"{row['first_stem']}–{row['last_stem']} | {row['train']}/{row['test']}/{row['unassigned']} | {row['class_ids']} |"
        for row in large_scene
    )
    infeasible_lines = ", ".join(
        f"{row['class_id']} ({row['capture_groups']} grp/{row['images']} img)" for row in infeasible
    )
    infeasible_scene_lines = ", ".join(str(row["class_id"]) for row in infeasible_scene)
    return f"""# M0-WP31 — D-02 group_id proposal for DATASET01

Status: `{PACKAGE_STATUS}`
Boundary: `{EVIDENCE_BOUNDARY}`

This package turns the independently QA-passed provisional edge overlays (WP5, WP7, WP12-R1,
WP13, WP14, WP15, WP22, WP23-R1, WP24, WP25-R1, WP26, WP27-R2, WP28-R2, WP29 and WP30-R1) into
two candidate `group_id` levels for the owner's D-02 decision. It writes no split, does not
change canonical WP5, and does not authorize training. Gate 0 remains BLOCKED.

## Grouping rules

1. **Capture group (`D02-C####`)**: connected components over edges reviewed as
   `SAME_CAPTURE_CANDIDATE` or `UNRESOLVED`. An unresolved edge is kept joined, because cutting
   it is the leak-risk direction.
2. **Scene group (`D02-S####`)**: inside each capture group, cut only edges whose physical-sign
   relation is `NOT_RELATED` (the visible signs change), then re-merge two sibling scenes in the
   same capture group when they are not adjacent and the last labelled frame of one and the first
   labelled frame of the other overlap in classes (overlap coefficient ≥ {SCENE_REMERGE_OVERLAP}). The
   re-merge protects against frames that are out of filename order (WP29 `edge_002967`, WP30
   `edge_002977`), where the same physical sign could otherwise end up in two groups.
   {derived['remerged_scene_pairs']} sibling pairs were re-merged.
3. **Unreviewed negative gaps.** WP5 created no proxy edge next to the 25 empty-label frames
   (vendor split `unassigned`), so {len(derived['gaps'])} negative runs covering 37 consecutive
   stem pairs were never reviewed. Capture groups join across every run (leak-safe). Scene groups
   attach the negatives to the preceding scene and join the following scene only when the two
   bounding labelled frames overlap in classes ({sum(row['scene_joined'] for row in derived['gaps'])}
   of {len(derived['gaps'])} runs). The runs are listed in `{GAPS_PATH.as_posix()}` and should be
   reviewed visually before the owner finalizes D-02.
4. Both levels join stems `0247` and `0249`, whose connecting edges through quarantined stem
   `0248` were never reviewed. Stem `0248` gets no group and stays excluded.
5. Sequence overlays (WP16–WP21) remain context only and are not used.

## Result

| Level | Groups | Multi-frame | Singletons | Mixed train/test | > {LARGE_GROUP_THRESHOLD} frames | Largest sizes | Largest share |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Capture | {capture['groups']} | {capture['multi_frame_groups']} | {capture['singletons']} | {capture['mixed_split_groups']} | {capture['large_groups']} | {capture['largest_sizes']} | {capture['largest_share']:.1%} |
| Scene | {scene['groups']} | {scene['multi_frame_groups']} | {scene['singletons']} | {scene['mixed_split_groups']} | {scene['large_groups']} | {scene['largest_sizes']} | {scene['largest_share']:.1%} |

"Mixed train/test" counts groups that the vendor split currently places on both sides; every
such group is a leak in the vendor split and confirms that the vendor split cannot be used as a
holdout.

The scene level applies {len(effective_cuts)} effective cuts (listed in
`{CUTS_PATH.as_posix()}`). The remaining large scene groups cannot be split further from the
reviewed evidence, because every adjacent pair inside them shares at least one physical sign:

| Scene group | Capture group | Frames | Stems | Train/test/unassigned | Classes |
| --- | --- | --- | --- | --- | --- |
{large_lines}

## Independent support per class

`{SUPPORT_PATH.as_posix()}` counts, for each of the {len(derived['support'])} observed classes,
how many distinct groups contain it. A class needs at least three independent groups to appear
in train, validation and test.

- Not feasible at capture level ({len(infeasible)} classes): {infeasible_lines}.
- Not feasible at scene level ({len(infeasible_scene)} classes): {infeasible_scene_lines}.

This is direct input for D-04: image counts overstate independent support.

## Owner decision options for D-02

- **D02-P1 — adopt capture groups.** Most conservative; the largest group holds
  {capture['largest_share']:.1%} of frames, which still allows a group-aware split.
- **D02-P2 — adopt scene groups.** Finer groups and more classes become split-feasible; relies on
  the physical-sign `NOT_RELATED` cuts and the class-overlap re-merge being sufficient.
- **D02-A — wait for creator/session metadata.** Remains preferred if it can be obtained.

Whichever option is chosen, the owner should spot-check the effective cut list before a split is
generated. Choosing an option does not by itself open Gate 0: D-01, D-03 and D-04 also remain
pending.

## Artifacts

- Frames: `{FRAMES_PATH.as_posix()}` (one row per stem, both group ids and flags).
- Groups: `{GROUPS_PATH.as_posix()}`.
- Scene cuts: `{CUTS_PATH.as_posix()}`.
- Unreviewed negative gaps: `{GAPS_PATH.as_posix()}`.
- Class support: `{SUPPORT_PATH.as_posix()}`.
- Manifest: `{MANIFEST_PATH.as_posix()}`.
"""


def source_paths(repo_root: Path) -> list[Path]:
    review = repo_root / dataset_graph.REVIEW_DIR
    paths = [
        repo_root / dataset_graph.INVENTORY_PATH,
        repo_root / dataset_graph.EDGE_DECISIONS_PATH,
        *(review / overlay.annotations for overlay in dataset_graph.EDGE_OVERLAYS),
        *(repo_root / record for record in QA_RECORDS),
        repo_root / "src/cpv301_autodrive/dataset_graph.py",
        repo_root / "scripts/build_wp31_group_id_proposal.py",
    ]
    return paths


def render(repo_root: Path) -> dict[Path, bytes]:
    derived = derive(repo_root)
    summary = {
        "capture": level_summary(derived["groups"], "capture"),
        "scene": level_summary(derived["groups"], "scene"),
    }
    artifacts = {
        FRAMES_PATH: to_csv(derived["frames"], FRAME_FIELDS),
        GROUPS_PATH: to_csv(derived["groups"], GROUP_FIELDS),
        CUTS_PATH: to_csv(derived["cuts"], CUT_FIELDS),
        GAPS_PATH: to_csv(derived["gaps"], GAP_FIELDS),
        SUPPORT_PATH: to_csv(derived["support"], SUPPORT_FIELDS),
        REPORT_PATH: render_report(derived, summary).encode("utf-8"),
    }
    manifest = {
        "schema_version": 1,
        "package": "M0-WP31",
        "status": PACKAGE_STATUS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "summary": summary,
        "effective_scene_cuts": sum(row["cut_effective"] for row in derived["cuts"]),
        "remerged_scene_pairs": derived["remerged_scene_pairs"],
        "overlay_sources": derived["sources"],
        "sources": [
            {"path": path.relative_to(repo_root).as_posix(), "sha256": sha256_file(path)}
            for path in source_paths(repo_root)
        ],
        "artifacts": [
            {"path": path.as_posix(), "sha256": sha256_bytes(payload)}
            for path, payload in artifacts.items()
        ],
        "d02_status": "PENDING",
        "gate0": "BLOCKED",
        "split_authorized": False,
        "training_authorized": False,
        "final_group_truth_created": False,
    }
    artifacts[MANIFEST_PATH] = (
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    return artifacts


def build(repo_root: Path) -> dict[str, Any]:
    artifacts = render(repo_root)
    for path, payload in artifacts.items():
        target = repo_root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    manifest = json.loads(artifacts[MANIFEST_PATH])
    return {
        "status": PACKAGE_STATUS,
        "capture_groups": manifest["summary"]["capture"]["groups"],
        "scene_groups": manifest["summary"]["scene"]["groups"],
        "manifest_sha256": sha256_bytes(artifacts[MANIFEST_PATH]),
    }


def verify(repo_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    try:
        expected = render(repo_root)
    except (OSError, KeyError, ValueError) as exc:
        return {"valid": False, "errors": [f"cannot re-derive WP31: {exc}"], "status": PACKAGE_STATUS}
    for path, payload in expected.items():
        target = repo_root / path
        if not target.is_file() or target.is_symlink():
            errors.append(f"missing artifact: {path.as_posix()}")
        elif target.read_bytes() != payload:
            errors.append(f"artifact differs from deterministic re-derivation: {path.as_posix()}")
    return {
        "valid": not errors,
        "errors": errors,
        "artifact_count": len(expected),
        "status": PACKAGE_STATUS,
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("build", "verify"):
        commands.add_parser(name).add_argument("--repo-root", type=Path, default=REPO_ROOT)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    result = build(repo_root) if args.command == "build" else verify(repo_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if args.command == "build" or result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
