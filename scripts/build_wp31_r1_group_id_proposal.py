#!/usr/bin/env python3
# ruff: noqa: E501
"""Build and verify M0-WP31-R1: the corrected D-02 group_id proposal for DATASET01.

WP31 failed independent QA (docs/review/wp31_independent_qa_record.md): P1-1 adjacency-only
linking split interleaved ride blocks, P1-2 the scene re-merge skipped interleaved siblings,
P2 the verifier did not pin its sources, P3 the report overstated leak safety. The initial WP31
package stays byte-identical as an immutable QA-fail record. R1:

- adds the WP32 reviewed cross-block links (capture and physical-sign level) on top of the
  QA-passed adjacency overlays;
- re-merges sibling scenes inside a capture group when their stem ranges interleave and any
  labelled frame of one shares a class with any labelled frame of the other (over-merge is the
  leak-safe direction), in addition to the WP31 resume rule;
- pins every input by SHA-256, so a changed overlay, review note or builder fails verification;
- states leak safety only as far as the reviewed evidence goes.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "wp31_r1_initial_package", Path(__file__).with_name("build_wp31_group_id_proposal.py")
)
assert _SPEC is not None and _SPEC.loader is not None
wp31 = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = wp31
_SPEC.loader.exec_module(wp31)
dataset_graph = wp31.dataset_graph

PACKAGE_STATUS = "WP31_R1_GROUP_ID_PROPOSAL_AWAITING_QA_AND_OWNER_D02_DECISION"
EVIDENCE_BOUNDARY = wp31.EVIDENCE_BOUNDARY
LARGE_GROUP_THRESHOLD = wp31.LARGE_GROUP_THRESHOLD

GENERATED = Path("docs/review/generated")
FRAMES_PATH = GENERATED / "wp31_r1_group_id_frames.csv"
GROUPS_PATH = GENERATED / "wp31_r1_group_id_groups.csv"
CUTS_PATH = GENERATED / "wp31_r1_scene_cut_edges.csv"
GAPS_PATH = GENERATED / "wp31_r1_unreviewed_negative_gaps.csv"
SUPPORT_PATH = GENERATED / "wp31_r1_class_group_support.csv"
REPORT_PATH = Path("docs/review/wp31_r1_group_id_proposal_report.md")
MANIFEST_PATH = GENERATED / "wp31_r1_group_id_manifest.json"
WP32_LINKS = GENERATED / "wp32_cross_block_links.csv"

# Every input is pinned. Initial WP31 bytes are the immutable QA-fail record.
PINNED_SOURCES: dict[str, str] = {
    "results/data_audit/DATASET01_052bc980a7206f8d/image_inventory.csv": "d45aa7f398a040c44cbc040f4ec005d7e5a8ef50586e905315f76c792ca29022",
    "docs/review/generated/wp5_provisional_edge_decisions.csv": "3f4cda85d10ea3dbcb9d9c83bbe2d5651991c00fb98b5e0fffbf28716e34fa1a",
    "src/cpv301_autodrive/dataset_graph.py": "339972e5bbd6789b7702c0726ac7644f01efb86b514261eb48927289f149f00d",
    "scripts/build_wp31_group_id_proposal.py": "b08a394192a9f0c6d5f3df306cb18b2aef56817e07c5e0fa6f47ca1ce890b08d",
    "tests/test_wp31_group_id_proposal.py": "fb383fac5dd9a4f9ea2f01e9531826fd91431ed6fd5dd28703032edb33906efd",
    "docs/review/wp31_group_id_proposal_report.md": "093ec24c77e227d0d3a0c8f3ba4555bc18d5d5b6180a577028dc3c94a509e1b3",
    "docs/review/generated/wp31_group_id_manifest.json": "15a61fcc118414b5499f7fc4b6fd49fd2974a4cac6e989198e548630bc549bd2",
    "docs/review/wp31_independent_qa_record.md": "5639265731217e77dc7b04cecb0133a1f43c78497e18f11ae412b7a160f9d4d9",
    "scripts/wp31_r1_pinned_overlays.json": "2c28eaf3de6d6d57835703df01c5edbbca81031fe9847410bbe5975b37fbedae",
    "scripts/build_wp32_cross_block_link_review.py": "92720010624230494a2ed5a65204cf1453f98624f3052eb762ffcfec0a55941c",
    "docs/review/generated/wp32_cross_block_manifest.json": "c73206e2388849a2f4d5fa11367f9500711c4eed932bc607a431cda737db4fd9",
    "docs/review/generated/wp32_cross_block_links.csv": "3cc0157e2b9df0f3f832edfc9a95dfd14a378a18fccdc983b8e0a9c2b7efb813",
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def overlay_paths() -> list[str]:
    review = dataset_graph.REVIEW_DIR.as_posix()
    names = [overlay.annotations for overlay in dataset_graph.EDGE_OVERLAYS] + list(dataset_graph.SEQUENCE_OVERLAYS)
    return [f"{review}/{name}" for name in names] + list(wp31.QA_RECORDS)


PINNED_OVERLAYS: dict[str, str] = json.loads(
    (Path(__file__).with_name("wp31_r1_pinned_overlays.json")).read_text(encoding="utf-8")
)


def verify_pins(repo_root: Path) -> None:
    expected = {**PINNED_SOURCES, **PINNED_OVERLAYS}
    if set(PINNED_OVERLAYS) != set(overlay_paths()):
        raise ValueError("WP31-R1 overlay pin roster differs from dataset_graph overlays")
    for relative, digest in expected.items():
        path = repo_root / relative
        if not path.is_file() or path.is_symlink() or sha256_bytes(path.read_bytes()) != digest:
            raise ValueError(f"pinned WP31-R1 source changed: {relative}")


def wp32_links(repo_root: Path) -> list[dict[str, str]]:
    rows = wp31.dataset_graph._read_csv(repo_root / WP32_LINKS)
    if {row["relation"] for row in rows} - {"LINK", "NO_LINK"} or {row["level"] for row in rows} - {"capture", "scene"}:
        raise ValueError("unexpected WP32 link vocabulary")
    return rows


def derive(repo_root: Path) -> dict[str, Any]:
    verify_pins(repo_root)
    payload = dataset_graph.build_graph_payload(repo_root)
    nodes, edges, sources = payload["nodes"], payload["edges"], payload["sources"]
    if any(payload["qa"][name] != "pass" for name in sources):
        raise ValueError("every edge overlay must be independently QA-passed")
    index = {node[0]: position for position, node in enumerate(nodes)}
    quarantined = index[wp31.QUARANTINED_STEM]
    bridge = (index[wp31.QUARANTINE_BRIDGE[0]], index[wp31.QUARANTINE_BRIDGE[1]])
    inventory_split = {
        row["stem"]: row["split"] for row in dataset_graph._read_csv(repo_root / dataset_graph.INVENTORY_PATH)
    }
    runs = wp31.negative_runs(nodes, edges)
    links = wp32_links(repo_root)

    capture = wp31.UnionFind(len(nodes))
    for edge in edges:
        if edge[6] in {"S", "U"}:
            capture.union(edge[0], edge[1])
    capture.union(*bridge)
    for left, negatives, right in runs:
        for position in [*negatives, right]:
            capture.union(left, position)
    cross_capture = 0
    for link in links:
        if link["level"] == "capture" and link["relation"] == "LINK":
            left, right = index[link["left_stem"]], index[link["right_stem"]]
            if capture.find(left) != capture.find(right):
                cross_capture += 1
            capture.union(left, right)
    capture_roots: list[int | None] = [capture.find(i) for i in range(len(nodes))]
    capture_roots[quarantined] = None
    capture_ids = wp31.number_groups(capture_roots, "D02-C")

    scene = wp31.UnionFind(len(nodes))
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
        joined = wp31.overlaps(wp31.classes(nodes[left]), wp31.classes(nodes[right]))
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
    for link in links:
        if link["level"] == "scene" and link["relation"] == "LINK":
            scene.union(index[link["left_stem"]], index[link["right_stem"]])

    remerged_pairs = 0
    changed = True
    while changed:  # repeat until stable: a merge can create new interleavings
        changed = False
        raw_scene = [scene.find(i) for i in range(len(nodes))]
        members: dict[int, list[int]] = defaultdict(list)
        for position, root in enumerate(raw_scene):
            if position != quarantined and nodes[position][3] != 0:
                members[root].append(position)
        by_capture: dict[str, list[int]] = defaultdict(list)
        for root, positions in members.items():
            by_capture[capture_ids[positions[0]]].append(root)
        for siblings in by_capture.values():
            for a in range(len(siblings)):
                for b in range(a + 1, len(siblings)):
                    if scene.find(siblings[a]) == scene.find(siblings[b]):
                        continue
                    pa, pb = members[siblings[a]], members[siblings[b]]
                    first_a, last_a, first_b, last_b = pa[0], pa[-1], pb[0], pb[-1]
                    resumes = (
                        first_b - last_a > 1 and wp31.overlaps(wp31.classes(nodes[last_a]), wp31.classes(nodes[first_b]))
                    ) or (
                        first_a - last_b > 1 and wp31.overlaps(wp31.classes(nodes[last_b]), wp31.classes(nodes[first_a]))
                    )
                    interleave = first_a < last_b and first_b < last_a
                    shared = interleave and bool(
                        set().union(*(wp31.classes(nodes[i]) for i in pa))
                        & set().union(*(wp31.classes(nodes[i]) for i in pb))
                    )
                    if resumes or shared:
                        scene.union(siblings[a], siblings[b])
                        remerged_pairs += 1
                        changed = True
    scene_roots: list[int | None] = [scene.find(i) for i in range(len(nodes))]
    scene_roots[quarantined] = None
    scene_ids = wp31.number_groups(scene_roots, "D02-S")

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
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for frame in frames:
            if frame[key]:
                grouped[frame[key]].append(frame)
        for group_id in sorted(grouped):
            rows = grouped[group_id]
            split_counts = Counter(row["split"] for row in rows)
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
                    "class_ids": " ".join(sorted({c for row in rows for c in row["class_ids"].split()}, key=int)),
                    "mixed_split": split_counts["train"] > 0 and split_counts["test"] > 0,
                    "large_group": len(rows) > LARGE_GROUP_THRESHOLD,
                }
            )

    cut_rows = [
        {
            "edge_id": f"edge_{edge[2]:06d}",
            "left_stem": nodes[edge[0]][0],
            "right_stem": nodes[edge[1]][0],
            "capture_group_id": capture_ids[edge[0]],
            "source_wp": sources[edge[8]] if edge[8] >= 0 else "",
            "confidence": {"H": "HIGH", "M": "MEDIUM", "L": "LOW"}.get(edge[9], ""),
            "left_scene_group_id": scene_ids[edge[0]],
            "right_scene_group_id": scene_ids[edge[1]],
            "cut_effective": scene_ids[edge[0]] != scene_ids[edge[1]],
        }
        for edge in cuts
    ]

    support = []
    for class_id in sorted({c for node in nodes for c in wp31.classes(node)}, key=int):
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
        "cross_capture_merges": cross_capture,
        "sources": sources,
    }


def render_report(derived: dict[str, Any], summary: dict[str, Any]) -> str:
    capture, scene = summary["capture"], summary["scene"]
    effective = sum(row["cut_effective"] for row in derived["cuts"])
    large = [row for row in derived["groups"] if row["level"] == "scene" and row["large_group"]]
    large_lines = "\n".join(
        f"| `{row['group_id']}` | `{row['parent_capture_group_id']}` | {row['size']} | "
        f"{row['first_stem']}–{row['last_stem']} | {row['train']}/{row['test']}/{row['unassigned']} | {row['class_ids']} |"
        for row in large
    )
    infeasible = [row for row in derived["support"] if not row["split_feasible_capture"]]
    infeasible_scene = [row for row in derived["support"] if not row["split_feasible_scene"]]
    return f"""# M0-WP31-R1 — corrected D-02 group_id proposal for DATASET01

Status: `{PACKAGE_STATUS}`
Boundary: `{EVIDENCE_BOUNDARY}`

This R1 reissue corrects the QA-failed WP31 proposal (record
`docs/review/wp31_independent_qa_record.md`: 2 P1, 1 P2, 2 P3). Initial WP31 stays byte-identical
as an immutable QA-fail record. Nothing here approves D-02, writes a split or authorizes training;
Gate 0 remains BLOCKED.

## What changed

- **P1-1 (interleaved ride blocks):** the WP32 cross-block review added
  {derived['cross_capture_merges']} capture-group merges from reviewed near-duplicate and
  label-geometry candidates (`docs/review/wp32_cross_block_review_report.md`).
- **P1-2 (interleaved sibling scenes):** sibling scenes in one capture group are re-merged when
  their stem ranges interleave and they share any labelled class, in addition to the WP31 resume
  rule; WP32 physical-sign links are applied first. {derived['remerged_scene_pairs']} re-merges.
  The C0079 cls23 single-pole sub-sequence was re-reviewed in WP32: same ride, but a different
  pole from the cls10/cls23 pole in the main sequence.
- **P2 (unpinned sources):** every input (inventory, WP5 CSV, `dataset_graph.py`, all overlay
  JSONs, QA records, the initial WP31 package and the WP32 package) is pinned by SHA-256.
- **P3 (wording):** see "Limits" below.

## Grouping rules

1. Capture group (`D02-C`): adjacency edges reviewed `SAME_CAPTURE_CANDIDATE`/`UNRESOLVED`, the
   twelve unreviewed negative runs, `0247`–`0249`, and WP32 capture links.
2. Scene group (`D02-S`): capture groups cut only at physical-sign `NOT_RELATED` edges, joined by
   WP32 physical-sign links, then re-merged for resumed or interleaved siblings.

## Result

| Level | Groups | Multi-frame | Singletons | Mixed train/test | > {LARGE_GROUP_THRESHOLD} frames | Largest sizes | Largest share |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Capture | {capture['groups']} | {capture['multi_frame_groups']} | {capture['singletons']} | {capture['mixed_split_groups']} | {capture['large_groups']} | {capture['largest_sizes']} | {capture['largest_share']:.1%} |
| Scene | {scene['groups']} | {scene['multi_frame_groups']} | {scene['singletons']} | {scene['mixed_split_groups']} | {scene['large_groups']} | {scene['largest_sizes']} | {scene['largest_share']:.1%} |

{effective} scene cuts remain effective. Large scene groups:

| Scene group | Capture group | Frames | Stems | Train/test/unassigned | Classes |
| --- | --- | --- | --- | --- | --- |
{large_lines}

## Independent support per class

- Fewer than 3 capture groups ({len(infeasible)} classes): {', '.join(f"{r['class_id']} ({r['capture_groups']} grp/{r['images']} img)" for r in infeasible)}.
- Fewer than 3 scene groups ({len(infeasible_scene)} classes): {', '.join(str(r['class_id']) for r in infeasible_scene)}.

## Limits

- Cross-block linking only covers candidates found by near-identical thumbnails or matching label
  geometry. The same sign seen from a clearly different distance or angle in another block may
  still be in a separate group, so neither level is proven leak-free.
- The twelve negative runs are bridged at capture level but were never reviewed visually.
- Over-merge is accepted as the safe direction; very large groups make a balanced split harder.

## Owner decision options for D-02

- **D02-P1 — capture groups:** coarsest; lowest residual leak risk among the two levels.
- **D02-P2 — scene groups:** finer; relies additionally on the physical-sign cuts.
- **D02-A — creator/session metadata:** still preferred if it can be obtained.

## Artifacts

- Frames `{FRAMES_PATH.as_posix()}`, groups `{GROUPS_PATH.as_posix()}`, cuts
  `{CUTS_PATH.as_posix()}`, negative gaps `{GAPS_PATH.as_posix()}`, class support
  `{SUPPORT_PATH.as_posix()}`, manifest `{MANIFEST_PATH.as_posix()}`.
"""


def render(repo_root: Path) -> dict[Path, bytes]:
    derived = derive(repo_root)
    summary = {
        "capture": wp31.level_summary(derived["groups"], "capture"),
        "scene": wp31.level_summary(derived["groups"], "scene"),
    }
    artifacts = {
        FRAMES_PATH: wp31.to_csv(derived["frames"], wp31.FRAME_FIELDS),
        GROUPS_PATH: wp31.to_csv(derived["groups"], wp31.GROUP_FIELDS),
        CUTS_PATH: wp31.to_csv(derived["cuts"], wp31.CUT_FIELDS),
        GAPS_PATH: wp31.to_csv(derived["gaps"], wp31.GAP_FIELDS),
        SUPPORT_PATH: wp31.to_csv(derived["support"], wp31.SUPPORT_FIELDS),
        REPORT_PATH: render_report(derived, summary).encode("utf-8"),
    }
    manifest = {
        "schema_version": 1,
        "package": "M0-WP31-R1",
        "status": PACKAGE_STATUS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "summary": summary,
        "cross_capture_merges": derived["cross_capture_merges"],
        "remerged_scene_pairs": derived["remerged_scene_pairs"],
        "effective_scene_cuts": sum(row["cut_effective"] for row in derived["cuts"]),
        "pinned_sources": {**PINNED_SOURCES, **PINNED_OVERLAYS},
        "builder_sha256": sha256_bytes(Path(__file__).read_bytes()),
        "artifacts": [{"path": path.as_posix(), "sha256": sha256_bytes(payload)} for path, payload in artifacts.items()],
        "d02_status": "PENDING",
        "gate0": "BLOCKED",
        "split_authorized": False,
        "training_authorized": False,
        "final_group_truth_created": False,
    }
    artifacts[MANIFEST_PATH] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return artifacts


def build(repo_root: Path) -> dict[str, Any]:
    artifacts = render(repo_root)
    for path, payload in artifacts.items():
        (repo_root / path).parent.mkdir(parents=True, exist_ok=True)
        (repo_root / path).write_bytes(payload)
    summary = json.loads(artifacts[MANIFEST_PATH])["summary"]
    return {
        "status": PACKAGE_STATUS,
        "capture_groups": summary["capture"]["groups"],
        "scene_groups": summary["scene"]["groups"],
        "manifest_sha256": sha256_bytes(artifacts[MANIFEST_PATH]),
    }


def verify(repo_root: Path) -> dict[str, Any]:
    try:
        expected = render(repo_root)
    except (OSError, KeyError, ValueError) as exc:
        return {"valid": False, "errors": [f"cannot re-derive WP31-R1: {exc}"], "status": PACKAGE_STATUS}
    errors = [
        f"artifact differs from deterministic re-derivation: {path.as_posix()}"
        for path, payload in expected.items()
        if not (repo_root / path).is_file() or (repo_root / path).is_symlink() or (repo_root / path).read_bytes() != payload
    ]
    return {"valid": not errors, "errors": errors, "artifact_count": len(expected), "status": PACKAGE_STATUS}


def main(argv: list[str] | None = None) -> int:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("build", "verify"):
        commands.add_parser(name).add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = root.parse_args(argv)
    repo_root = args.repo_root.resolve()
    result = build(repo_root) if args.command == "build" else verify(repo_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if args.command == "build" or result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
