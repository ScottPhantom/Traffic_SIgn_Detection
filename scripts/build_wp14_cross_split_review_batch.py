# ruff: noqa: E501
"""Build and verify the M0-WP14 cross-split visual-review Batch-D package."""

from __future__ import annotations

import argparse
import importlib.util
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

BASE_PATH = Path(__file__).with_name("build_wp12_cross_split_review_batch.py")
SPEC = importlib.util.spec_from_file_location("wp14_hardened_base", BASE_PATH)
assert SPEC is not None and SPEC.loader is not None
base = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = base
SPEC.loader.exec_module(base)
BASE_RENDER_ATLAS = base.render_atlas

PACKAGE_STATUS = "WP14_AWAITING_QA_BATCH_D_PM_PROVISIONAL_REVIEW"
ANNOTATION_STATUS = "PM_REVIEWED_AWAITING_INDEPENDENT_QA"
EVIDENCE_BOUNDARY = (
    "BATCH_D_PM_PROVISIONAL_VISUAL_REVIEW_ONLY_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_"
    "NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING"
)
BATCH_ID = "M0-WP14-BATCH-D"
EXPECTED_SELECTION_COUNT = 250
EXPECTED_BATCH_A_COUNT = 100
EXPECTED_BATCH_B_COUNT = 250
EXPECTED_BATCH_C_COUNT = 250
EXPECTED_SELECTED_ENDPOINT_BOX_COUNT = 1413
EXPECTED_PAGE_COUNT = 50
REVIEWED_AT = "2026-10-11T14:46:34+07:00"

# Pinned only after the PM inspected all 50 prepared atlas pages / 250 pairs.
EXPECTED_REVIEW_NOTES_SHA256 = (
    "ac63ad6fafc767a81263ad181fa3a96a19d8c493e648d145abedc641bc09b84e"
)
EXPECTED_CAPTURE_COUNTS = {
    "SAME_CAPTURE_CANDIDATE": 246,
    "NOT_RELATED": 4,
}
EXPECTED_PHYSICAL_SIGN_COUNTS = {
    "SAME_PHYSICAL_SIGN_CANDIDATE": 238,
    "NOT_RELATED": 12,
}
EXPECTED_CONFIDENCE_COUNTS = {"HIGH": 250}
EXPECTED_CAPTURE_UNRESOLVED_IDS: set[str] = set()
EXPECTED_PHYSICAL_SIGN_UNRESOLVED_IDS: set[str] = set()
EXPECTED_CAPTURE_NOT_RELATED_IDS = {
    "edge_001968",
    "edge_002032",
    "edge_002453",
    "edge_002568",
}
EXPECTED_PHYSICAL_SIGN_NOT_RELATED_IDS = {
    "edge_001968",
    "edge_002032",
    "edge_002107",
    "edge_002108",
    "edge_002161",
    "edge_002162",
    "edge_002172",
    "edge_002173",
    "edge_002262",
    "edge_002263",
    "edge_002453",
    "edge_002568",
}

MANIFEST_RELATIVE_PATH = "docs/review/generated/wp14_batch_d_manifest.json"
SELECTION_RELATIVE_PATH = "docs/review/generated/wp14_batch_d_selection.csv"
LINEAGE_RELATIVE_PATH = "docs/review/generated/wp14_batch_d_source_lineage.csv"
LAYOUT_RELATIVE_PATH = "docs/review/generated/wp14_batch_d_layout_audit.json"
REPORT_RELATIVE_PATH = "docs/review/wp14_cross_split_review_batch_d_report.md"
ANNOTATIONS_RELATIVE_PATH = "docs/review/wp14_visual_review_annotations_batch_d.json"
REVIEW_NOTES_RELATIVE_PATH = "docs/review/wp14_visual_review_notes_batch_d.csv"
ASSETS_RELATIVE_PATH = "docs/review/assets/wp14/batch_d"

PINNED = {
    **base.EXPECTED_PINNED_HASHES,
    "wp12_manifest": "8e576954bc3de456704aecdb67e8625d8621ca017fb08e3b866635db6afcc0f0",
    "wp12_selection": "3e46ff57c5e99107254c742922010865cf2659495cef7ad8c2b662dcef06e062",
    "wp12_annotations": "44e3b181bb277c07851da44ea3ed6659241bd3048438964ad60472380f2f85c0",
    "wp12_builder": "f2569636e26a48984e432bbfc35735f2099e855db27b2b3ce76f001c33c197df",
    "wp13_manifest": "5db80e215f318a6b782d813b4560c20e35e4f3e51ef0423d7298f4818ea3db65",
    "wp13_selection": "e551ea02758deef02af1db6ad5e9da4de91ce84b5c06d38616265dbb55e86a22",
    "wp13_annotations": "47361b9a9c2c0f837c9d82393a3128de7639c4458fe28b76bd78966a4a03e603",
    "wp13_builder": "970dd17ae0483fe2d096862c09342c7f4792fd2e102cf0c133a94d9d48107680",
}


def source_contract(repo_root: Path) -> list[tuple[str, Path, str | None]]:
    generated = repo_root / "docs/review/generated"
    audit = repo_root / "results/data_audit/DATASET01_052bc980a7206f8d"
    return [
        ("wp5_manifest", generated / "wp5_evidence_manifest.json", PINNED["wp5_manifest"]),
        ("wp5_decisions", generated / "wp5_provisional_edge_decisions.csv", PINNED["wp5_decisions"]),
        ("wp5_layout", generated / "wp5_pair_layout_audit.json", PINNED["wp5_layout"]),
        ("image_inventory", audit / "image_inventory.csv", PINNED["image_inventory"]),
        ("source_preservation", audit / "source_preservation_proof.json", PINNED["source_preservation"]),
        ("decision_status", repo_root / "docs/review/decision_status.json", PINNED["decision_status"]),
        ("wp6_manifest", generated / "wp6_e0_compute_manifest.json", PINNED["wp6_manifest"]),
        ("wp7_manifest", generated / "wp7_batch_a_manifest.json", PINNED["wp7_manifest"]),
        ("wp7_selection", generated / "wp7_batch_a_selection.csv", PINNED["wp7_selection"]),
        ("wp7_annotations", repo_root / "docs/review/wp7_visual_review_annotations_batch_a.json", PINNED["wp7_annotations"]),
        ("wp12_manifest", generated / "wp12_batch_b_manifest.json", PINNED["wp12_manifest"]),
        ("wp12_selection", generated / "wp12_batch_b_selection.csv", PINNED["wp12_selection"]),
        ("wp12_annotations", repo_root / "docs/review/wp12_visual_review_annotations_batch_b.json", PINNED["wp12_annotations"]),
        (
            "wp12_builder",
            repo_root / "scripts/build_wp12_cross_split_review_batch.py",
            PINNED["wp12_builder"],
        ),
        ("wp13_manifest", generated / "wp13_batch_c_manifest.json", PINNED["wp13_manifest"]),
        ("wp13_selection", generated / "wp13_batch_c_selection.csv", PINNED["wp13_selection"]),
        ("wp13_annotations", repo_root / "docs/review/wp13_visual_review_annotations_batch_c.json", PINNED["wp13_annotations"]),
        (
            "wp13_builder",
            repo_root / "scripts/build_wp13_cross_split_review_batch.py",
            PINNED["wp13_builder"],
        ),
        ("wp14_review_notes", repo_root / REVIEW_NOTES_RELATIVE_PATH, EXPECTED_REVIEW_NOTES_SHA256),
        ("wp14_builder", repo_root / "scripts/build_wp14_cross_split_review_batch.py", None),
    ]


def derive_selection(
    repo_root: Path, raw_root: Path
) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    rows = base.load_wp5_rows(repo_root)
    inventory = base.load_inventory(repo_root)
    pending = [
        row
        for row in rows
        if row["cross_split"] == "True" and row["review_status"] == "PENDING"
    ]
    batch_a = base.read_csv(repo_root / "docs/review/generated/wp7_batch_a_selection.csv")
    batch_b = base.read_csv(repo_root / "docs/review/generated/wp12_batch_b_selection.csv")
    batch_c = base.read_csv(repo_root / "docs/review/generated/wp13_batch_c_selection.csv")
    batch_a_ids = [row["edge_id"] for row in batch_a]
    batch_b_ids = [row["edge_id"] for row in batch_b]
    batch_c_ids = [row["edge_id"] for row in batch_c]
    pending_ids = [row["edge_id"] for row in pending]
    if batch_a_ids != pending_ids[:EXPECTED_BATCH_A_COUNT]:
        raise ValueError("WP7 Batch-A exclusion roster/order differs from canonical WP5 prefix")
    if batch_b_ids != pending_ids[EXPECTED_BATCH_A_COUNT:EXPECTED_BATCH_A_COUNT + EXPECTED_BATCH_B_COUNT]:
        raise ValueError("WP12 Batch-B exclusion roster/order differs from canonical continuation")
    batch_c_start = EXPECTED_BATCH_A_COUNT + EXPECTED_BATCH_B_COUNT
    batch_c_end = batch_c_start + EXPECTED_BATCH_C_COUNT
    if batch_c_ids != pending_ids[batch_c_start:batch_c_end]:
        raise ValueError("WP13 Batch-C exclusion roster/order differs from canonical continuation")
    excluded = set(batch_a_ids) | set(batch_b_ids) | set(batch_c_ids)
    if len(excluded) != EXPECTED_BATCH_A_COUNT + EXPECTED_BATCH_B_COUNT + EXPECTED_BATCH_C_COUNT:
        raise ValueError("WP7/WP12/WP13 exclusion rosters overlap or contain duplicates")
    candidates = [row for row in pending if row["edge_id"] not in excluded][
        :EXPECTED_SELECTION_COUNT
    ]
    if len(candidates) != EXPECTED_SELECTION_COUNT:
        raise ValueError("could not derive exactly 250 Batch-D pending cross-split edges")
    selected: list[dict[str, str]] = []
    for position, edge in enumerate(candidates, start=1):
        if edge["edge_id"] in base.EXPECTED_WP5_REVIEWED_IDS or edge["edge_id"] in excluded:
            raise ValueError("WP14 selection contains an ineligible prior-review edge")
        left = inventory[edge["left_stem"]]
        right = inventory[edge["right_stem"]]
        base.verify_raw_record(left, raw_root)
        base.verify_raw_record(right, raw_root)
        for side, source in (("left", left), ("right", right)):
            if (
                edge[f"{side}_image_sha256"] != source["image_sha256"]
                or edge[f"{side}_label_sha256"] != source["label_sha256"]
            ):
                raise ValueError(f"WP5/inventory source binding drift for {edge['edge_id']}")
        page = math.ceil(position / base.PAIRS_PER_PAGE)
        slot = (position - 1) % base.PAIRS_PER_PAGE + 1
        selected.append(
            {
                "batch_position": str(position),
                "edge_id": edge["edge_id"],
                "wp5_review_order": edge["review_order"],
                "wp5_review_status": edge["review_status"],
                "left_stem": edge["left_stem"],
                "left_split": edge["left_split"],
                "right_stem": edge["right_stem"],
                "right_split": edge["right_split"],
                "cross_split": edge["cross_split"],
                "same_dimensions": edge["same_dimensions"],
                "thumbnail_mae": edge["thumbnail_mae"],
                "dhash_distance": edge["dhash_distance"],
                "rgb_histogram_cosine": edge["rgb_histogram_cosine"],
                "proxy_status": edge["proxy_status"],
                "proxy_sequence_id": edge["proxy_sequence_id"],
                "left_class_ids": edge["left_class_ids"],
                "right_class_ids": edge["right_class_ids"],
                "left_image_path": left["image_path"],
                "right_image_path": right["image_path"],
                "left_label_path": left["label_path"],
                "right_label_path": right["label_path"],
                "left_image_sha256": left["image_sha256"],
                "right_image_sha256": right["image_sha256"],
                "left_label_sha256": left["label_sha256"],
                "right_label_sha256": right["label_sha256"],
                "wp5_atlas_page": edge["atlas_page"],
                "wp5_atlas_slot": edge["atlas_slot"],
                # Compatibility field names are retained because the hardened WP12 renderer and
                # verifier are imported unchanged; values point only to the separate WP14 atlas.
                "wp12_atlas_page": f"{ASSETS_RELATIVE_PATH}/page_{page:03d}.jpg",
                "wp12_atlas_slot": str(slot),
                "selection_status": "SELECTED_PENDING_CROSS_SPLIT_BATCH_D",
                "evidence_boundary": EVIDENCE_BOUNDARY,
            }
        )
    if any(base.QUARANTINED_STEM in {row["left_stem"], row["right_stem"]} for row in selected):
        raise ValueError("WP14 selection must exclude quarantined stem 0248")
    return selected, inventory


class _DrawProxy:
    def __init__(self, wrapped: Any) -> None:
        self._wrapped = wrapped

    def text(self, xy: Any, text: str, *args: Any, **kwargs: Any) -> Any:
        text = text.replace("M0-WP12-R1 Batch B", "M0-WP14 Batch D")
        text = text.replace("WP12 slot", "WP14 slot")
        return self._wrapped.text(xy, text, *args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._wrapped, name)


def render_atlas(
    selection: list[dict[str, str]],
    inventory: dict[str, dict[str, str]],
    raw_root: Path,
    assets_dir: Path,
    decisions: list[dict[str, Any]] | None,
) -> tuple[list[Path], dict[str, Any]]:
    original_draw = base.ImageDraw.Draw
    base.ImageDraw.Draw = lambda image: _DrawProxy(original_draw(image))
    try:
        paths, layout = BASE_RENDER_ATLAS(
            selection, inventory, raw_root, assets_dir, decisions
        )
    finally:
        base.ImageDraw.Draw = original_draw
    index_path = assets_dir / "index.html"
    index_text = index_path.read_text(encoding="utf-8")
    index_text = index_text.replace("M0-WP12-R1", "M0-WP14").replace(
        "Batch B", "Batch D"
    )
    index_path.write_text(index_text, encoding="utf-8")
    return paths, layout


def summary_from_decisions(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "batch": BATCH_ID,
        "status": PACKAGE_STATUS,
        "selected_pairs": EXPECTED_SELECTION_COUNT,
        "outcome_counts": dict(sorted(Counter(row["provisional_outcome"] for row in decisions).items())),
        "confidence_counts": dict(sorted(Counter(row["confidence"] for row in decisions).items())),
        "capture_hypothesis_counts": dict(sorted(Counter(row["capture_hypothesis"] for row in decisions).items())),
        "physical_sign_hypothesis_counts": dict(sorted(Counter(row["physical_sign_hypothesis"] for row in decisions).items())),
        "first_edge": decisions[0]["edge_id"],
        "last_edge": decisions[-1]["edge_id"],
        "canonical_wp5_pending_unchanged": base.EXPECTED_WP5_PENDING_COUNT,
        "pending_outside_wp7_wp12_overlays": base.EXPECTED_WP5_PENDING_COUNT - EXPECTED_BATCH_A_COUNT - EXPECTED_BATCH_B_COUNT - EXPECTED_BATCH_C_COUNT - EXPECTED_SELECTION_COUNT,
        "cross_split_pending_outside_wp7_wp12_overlays": base.EXPECTED_WP5_CROSS_SPLIT_COUNT - 5 - EXPECTED_BATCH_A_COUNT - EXPECTED_BATCH_B_COUNT - EXPECTED_BATCH_C_COUNT - EXPECTED_SELECTION_COUNT,
        "all_wp5_sequences_pending": base.EXPECTED_WP5_SEQUENCE_COUNT,
        "d02_a_preferred": True,
        "d02_b_budget_approved": False,
        "final_group_truth_created": False,
        "split_assignment_created": False,
        "training_authorized": False,
        "gate0": "BLOCKED",
        "evidence_boundary": EVIDENCE_BOUNDARY,
    }


def validate_review_decision_contract(rows: list[dict[str, Any]]) -> None:
    """Pin both aggregate counts and the exact exceptional edge rosters."""
    capture_counts = Counter(row["capture_hypothesis"] for row in rows)
    physical_counts = Counter(row["physical_sign_hypothesis"] for row in rows)
    confidence_counts = Counter(row["confidence"] for row in rows)
    capture_unresolved = {
        row["edge_id"] for row in rows if row["capture_hypothesis"] == "UNRESOLVED"
    }
    physical_unresolved = {
        row["edge_id"]
        for row in rows
        if row["physical_sign_hypothesis"] == "UNRESOLVED"
    }
    capture_not_related = {
        row["edge_id"] for row in rows if row["capture_hypothesis"] == "NOT_RELATED"
    }
    physical_not_related = {
        row["edge_id"]
        for row in rows
        if row["physical_sign_hypothesis"] == "NOT_RELATED"
    }
    if dict(capture_counts) != EXPECTED_CAPTURE_COUNTS:
        raise ValueError("WP14 capture decision counts differ from approved PM review")
    if dict(physical_counts) != EXPECTED_PHYSICAL_SIGN_COUNTS:
        raise ValueError("WP14 physical-sign decision counts differ from approved PM review")
    if dict(confidence_counts) != EXPECTED_CONFIDENCE_COUNTS:
        raise ValueError("WP14 confidence counts differ from approved PM review")
    if capture_unresolved != EXPECTED_CAPTURE_UNRESOLVED_IDS:
        raise ValueError("WP14 capture UNRESOLVED edge IDs differ from approved PM review")
    if physical_unresolved != EXPECTED_PHYSICAL_SIGN_UNRESOLVED_IDS:
        raise ValueError("WP14 physical-sign UNRESOLVED edge IDs differ from approved PM review")
    if capture_not_related != EXPECTED_CAPTURE_NOT_RELATED_IDS:
        raise ValueError("WP14 capture NOT_RELATED edge IDs differ from approved PM review")
    if physical_not_related != EXPECTED_PHYSICAL_SIGN_NOT_RELATED_IDS:
        raise ValueError("WP14 physical-sign NOT_RELATED edge IDs differ from approved PM review")


def render_report(summary: dict[str, Any], annotation_payload: dict[str, Any]) -> str:
    def counts(name: str) -> str:
        return "\n".join(
            f"- `{key}`: {value}" for key, value in summary[name].items()
        )

    return f"""# M0-WP14 — D02-B cross-split manual review, Batch D

Status: `{PACKAGE_STATUS}`  
Boundary: `{EVIDENCE_BOUNDARY}`

This package records one PM/Codex provisional visual pass over exactly 250 canonical WP5 pending
cross-split pairs. It does not approve D-02, create final/transitive group truth or a split, or
authorize training. D02-A creator/session metadata remains preferred.

## Selection and review protocol

- Selection: exact next 250 unique canonical WP5 rows with `cross_split=True` and
  `review_status=PENDING`, preserving WP5 order and excluding exact WP7 Batch-A, WP12 Batch-B,
  and WP13 Batch-C rosters. Canonical WP5 reviewed rows are ineligible.
- Selected edge range: `{summary['first_edge']}` through `{summary['last_edge']}`.
- Source coverage: 500 endpoint rows with {EXPECTED_SELECTED_ENDPOINT_BOX_COUNT} total boxes;
  quarantined stem `0248` is absent.
- Reviewer: `{annotation_payload['reviewer']}` at `{annotation_payload['reviewed_at']}`.
- All 250 pairs/500 raw frames were directly inspected in the dedicated 50-page WP14 atlas.
  Proxy fields were context only; identity metadata is unavailable.

## Hardened verifier contract

- Exact 51-file atlas roster; extra/missing/wrong-type/symlink/path attacks fail closed.
- Index, 50 JPEG pages and layout are regenerated in isolation and byte/deep-compared.
- Trusted review-notes SHA-256 `{EXPECTED_REVIEW_NOTES_SHA256}` pins exact outcomes and unresolved
  IDs. Coherent downstream rebuild cannot override the source anchor.

## Provisional capture outcomes

{counts('capture_hypothesis_counts')}

## Provisional physical-sign outcomes

{counts('physical_sign_hypothesis_counts')}

## Confidence

{counts('confidence_counts')}

## Remaining workload and governance

- Canonical WP5 remains unchanged at {summary['canonical_wp5_pending_unchanged']} PENDING edges.
- Outside WP7, WP12, WP13 and WP14 overlays, {summary['pending_outside_wp7_wp12_overlays']} pending edges
  remain, including {summary['cross_split_pending_outside_wp7_wp12_overlays']} cross-split edges.
- All {summary['all_wp5_sequences_pending']} WP5 sequences remain PENDING.
- D-02 remains PENDING; Gate 0 remains BLOCKED; `training_authorized=false`.

## Artifacts

- Decisions: `{ANNOTATIONS_RELATIVE_PATH}`.
- Selection: `{SELECTION_RELATIVE_PATH}`.
- Source lineage: `{LINEAGE_RELATIVE_PATH}`.
- Layout audit: `{LAYOUT_RELATIVE_PATH}`.
- Atlas: `{ASSETS_RELATIVE_PATH}/index.html` and {EXPECTED_PAGE_COUNT} JPEG pages.
- Manifest: `{MANIFEST_RELATIVE_PATH}`.
"""


def configure_base() -> None:
    values = {
        "PACKAGE_STATUS": PACKAGE_STATUS,
        "ANNOTATION_STATUS": ANNOTATION_STATUS,
        "EVIDENCE_BOUNDARY": EVIDENCE_BOUNDARY,
        "BATCH_ID": BATCH_ID,
        "EXPECTED_SELECTION_COUNT": EXPECTED_SELECTION_COUNT,
        "EXPECTED_BATCH_A_COUNT": EXPECTED_BATCH_A_COUNT,
        "EXPECTED_BATCH_C_COUNT": EXPECTED_BATCH_C_COUNT,
        "EXPECTED_SELECTED_ENDPOINT_BOX_COUNT": EXPECTED_SELECTED_ENDPOINT_BOX_COUNT,
        "EXPECTED_PAGE_COUNT": EXPECTED_PAGE_COUNT,
        "EXPECTED_REVIEW_NOTES_SHA256": EXPECTED_REVIEW_NOTES_SHA256,
        "EXPECTED_CAPTURE_COUNTS": EXPECTED_CAPTURE_COUNTS,
        "EXPECTED_PHYSICAL_SIGN_COUNTS": EXPECTED_PHYSICAL_SIGN_COUNTS,
        "EXPECTED_CONFIDENCE_COUNTS": EXPECTED_CONFIDENCE_COUNTS,
        "EXPECTED_CAPTURE_UNRESOLVED_IDS": EXPECTED_CAPTURE_UNRESOLVED_IDS,
        "EXPECTED_PHYSICAL_SIGN_UNRESOLVED_IDS": EXPECTED_PHYSICAL_SIGN_UNRESOLVED_IDS,
        "MANIFEST_RELATIVE_PATH": MANIFEST_RELATIVE_PATH,
        "SELECTION_RELATIVE_PATH": SELECTION_RELATIVE_PATH,
        "LINEAGE_RELATIVE_PATH": LINEAGE_RELATIVE_PATH,
        "LAYOUT_RELATIVE_PATH": LAYOUT_RELATIVE_PATH,
        "REPORT_RELATIVE_PATH": REPORT_RELATIVE_PATH,
        "ANNOTATIONS_RELATIVE_PATH": ANNOTATIONS_RELATIVE_PATH,
        "REVIEW_NOTES_RELATIVE_PATH": REVIEW_NOTES_RELATIVE_PATH,
        "ASSETS_RELATIVE_PATH": ASSETS_RELATIVE_PATH,
        "REVIEWED_AT": REVIEWED_AT,
    }
    for name, value in values.items():
        setattr(base, name, value)
    base.source_contract = source_contract
    base.derive_selection = derive_selection
    base.render_atlas = render_atlas
    base.summary_from_decisions = summary_from_decisions
    base.render_report = render_report
    base.validate_review_decision_contract = validate_review_decision_contract


def prepare(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    configure_base()
    result = base.prepare(repo_root, raw_root)
    result["status"] = "WP14_BATCH_D_PREPARED_AWAITING_PM_VISUAL_REVIEW"
    return result


def build(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    configure_base()
    return base.build(repo_root, raw_root)


def verify(manifest_path: Path, repo_root: Path, raw_root: Path) -> dict[str, Any]:
    configure_base()
    return base.verify_manifest(manifest_path, repo_root, raw_root)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("prepare", "build", "verify"):
        command = commands.add_parser(name)
        command.add_argument("--repo-root", type=Path, required=True)
        command.add_argument("--raw-root", type=Path, required=True)
    commands.choices["verify"].add_argument(
        "--manifest", type=Path, default=Path(MANIFEST_RELATIVE_PATH)
    )
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    raw_root = args.raw_root.resolve()
    if args.command == "prepare":
        result = prepare(repo_root, raw_root)
    elif args.command == "build":
        result = build(repo_root, raw_root)
    else:
        manifest = args.manifest
        if not manifest.is_absolute():
            manifest = repo_root / manifest
        result = verify(manifest, repo_root, raw_root)
    print(base.json.dumps(result, indent=2, sort_keys=True))
    return 0 if args.command != "verify" or result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
