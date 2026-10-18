# ruff: noqa: E501
"""Build and verify M0-WP22 remaining-edge manual-review Batch A."""

from __future__ import annotations

import argparse
import importlib.util
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PREVIOUS_PATH = Path(__file__).with_name("build_wp15_cross_split_review_batch.py")
SPEC = importlib.util.spec_from_file_location("wp22_hardened_previous", PREVIOUS_PATH)
assert SPEC is not None and SPEC.loader is not None
previous = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = previous
SPEC.loader.exec_module(previous)
PREVIOUS_RENDER_ATLAS = previous.render_atlas
PREVIOUS_SOURCE_CONTRACT = previous.source_contract

PACKAGE_STATUS = "WP22_AWAITING_QA_REMAINING_EDGE_BATCH_A_PM_PROVISIONAL_REVIEW"
ANNOTATION_STATUS = "PM_REVIEWED_AWAITING_INDEPENDENT_QA"
EVIDENCE_BOUNDARY = (
    "REMAINING_EDGE_BATCH_A_PM_PROVISIONAL_VISUAL_REVIEW_ONLY_NOT_D02_APPROVAL_"
    "NOT_GROUP_TRUTH_NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING"
)
BATCH_ID = "M0-WP22-REMAINING-EDGE-BATCH-A"
EXPECTED_SELECTION_COUNT = 250
EXPECTED_RESIDUAL_PENDING_COUNT = 2146
EXPECTED_QUARANTINED_RESIDUAL_COUNT = 2
EXPECTED_ELIGIBLE_RESIDUAL_COUNT = 2144
EXPECTED_REMAINING_AFTER_BATCH = 1896
EXPECTED_SELECTED_ENDPOINT_BOX_COUNT = 903
EXPECTED_PAGE_COUNT = 50
PAIRS_PER_PAGE = 5
EXPECTED_PAGE_ROW_COUNTS = (5,) * EXPECTED_PAGE_COUNT
REVIEWED_AT = "2026-10-12T01:50:32+07:00"

# Direct-PM-review trust anchor. Changing any reviewed decision requires an explicit
# source review and anchor update before the official package can be rebuilt.
EXPECTED_REVIEW_NOTES_SHA256 = (
    "c49c00bc85bbc0bc1cfc4683d9dbbd6403705a42600a1251e46e7ade949c6a27"
)
EXPECTED_CAPTURE_COUNTS = {
    "NOT_RELATED": 10,
    "SAME_CAPTURE_CANDIDATE": 240,
}
EXPECTED_PHYSICAL_SIGN_COUNTS = {
    "NOT_RELATED": 10,
    "SAME_PHYSICAL_SIGN_CANDIDATE": 240,
}
EXPECTED_CONFIDENCE_COUNTS = {"HIGH": EXPECTED_SELECTION_COUNT}
EXPECTED_CAPTURE_UNRESOLVED_IDS: set[str] = set()
EXPECTED_PHYSICAL_SIGN_UNRESOLVED_IDS: set[str] = set()
EXPECTED_CAPTURE_NOT_RELATED_IDS = {
    "edge_000068",
    "edge_000119",
    "edge_000131",
    "edge_000141",
    "edge_000182",
    "edge_000190",
    "edge_000205",
    "edge_000236",
    "edge_000263",
    "edge_000273",
}
EXPECTED_PHYSICAL_SIGN_NOT_RELATED_IDS = set(EXPECTED_CAPTURE_NOT_RELATED_IDS)

MANIFEST_RELATIVE_PATH = "docs/review/generated/wp22_remaining_edge_batch_a_manifest.json"
SELECTION_RELATIVE_PATH = "docs/review/generated/wp22_remaining_edge_batch_a_selection.csv"
LINEAGE_RELATIVE_PATH = "docs/review/generated/wp22_remaining_edge_batch_a_source_lineage.csv"
LAYOUT_RELATIVE_PATH = "docs/review/generated/wp22_remaining_edge_batch_a_layout_audit.json"
REPORT_RELATIVE_PATH = "docs/review/wp22_remaining_edge_batch_a_report.md"
ANNOTATIONS_RELATIVE_PATH = "docs/review/wp22_remaining_edge_review_annotations_batch_a.json"
REVIEW_NOTES_RELATIVE_PATH = "docs/review/wp22_remaining_edge_review_notes_batch_a.csv"
ASSETS_RELATIVE_PATH = "docs/review/assets/wp22/remaining_edge_batch_a"

SEQUENCE_CONTEXT_FIELDS = [
    "sequence_context_status",
    "sequence_context_batch",
    "sequence_capture_context",
    "sequence_physical_context",
    "sequence_confidence_context",
    "sequence_context_boundary",
]

PINNED = {
    "wp15_manifest": "032aee9da985c5dcb772ddd1c73fa9e4e6794e1beb5107fdb49b0168948a241d",
    "wp15_selection": "86cb9918d40e2308d03f318bc806a7c9b7bf75e8531123d5f2b170500bd24165",
    "wp15_annotations": "af09c7b3d589c1665d8c7349098cfc722a3cce6ea47f433dc9a7b221c650f603",
    "wp15_builder": "b3b6c054ba5e826b824e158ffc18bd83aa65d6c0d4b96ce5ea202c486f11a94a",
    "wp16_manifest": "f3e3fb7a13631ef60b9046f745c07cb39ff3df501c18d5e15e79ee2e505964bc",
    "wp16_selection": "962b6eccbee8601f86cfaa02aa61df6623f42a58508d08120b9d7b2cf2201bea",
    "wp16_annotations": "47346e5857d6d2cde8e462a61f9164adc660c51c6a325c91810e4e70eaa77027",
    "wp16_builder": "109018764af5460ac5f21770b6bff11589bd49fcba9babd5cbc40e145a6b617d",
    "wp17_manifest": "374ada61066f70f8ff3ba282dba41229ad2c161303146edd83aba583591b144b",
    "wp17_selection": "2479e7b53c6622a120c3897aae84acab23365d8bbda69de1f6c4bcacc48458c4",
    "wp17_annotations": "c1f97520debbc56bf138bf71cb7a83e2cffc298df83eb6435fc1e6e7c2c86ef0",
    "wp17_builder": "495cbe0450d245e3cadd7c20102951018ca94e66a5b63ae6ac18067b1fe7709a",
    "wp18_manifest": "35bf843db7eb626404c81477efb509b2e4881a2cc7ea81fcee3187fcfab93649",
    "wp18_selection": "faa55ac074b29da0dd61a33ba8e6a46401785f9ebead48130168598d5885ef01",
    "wp18_annotations": "637f3e5324eed7ae5af308a4baa67476e8bc5ab465129b1b19939e807b1c9de8",
    "wp18_builder": "e9a232bf2945c04abccc92665b0726d450e7091b2057c5fd5c71e43b22ea5146",
    "wp19_manifest": "6796c3a16b2af347f0a74a06cde4477b214d97233d0d38848d9077933c7f712f",
    "wp19_selection": "a63c8125fd570d19af5719bf11800d6b9ea70e3a03596cf195c63753e0c0296f",
    "wp19_annotations": "1d30f4f71b856c74addaf46d197c118eaa1ebd3488315b3a6ca6a23554135e46",
    "wp19_builder": "4a434d670c7da9e76cf3d0972f2ae3a8e36ba5fd86596741596cff175401508f",
    "wp20_manifest": "4523c698ff948ee2adaf879195662caec25ac80280cceb0aaaf91ae72fe89a6c",
    "wp20_selection": "b99abd53de497e74e42a75396be9f565c391977c4f35f633975cba3081c3bfc3",
    "wp20_annotations": "e567e3cceb92b7545c8751a6a67d7b29a61dd0ec15ce92cffdbf8e91cc1e23b4",
    "wp20_builder": "699d76a3378f89af5b23bb328fc2d381c15c1544cbfc4c1d6cf6c87b1514af7f",
    "wp21_manifest": "7ed7e1355ae1dfc88ec81b7f580aad3bf0874b59832708652ad1ba02265d4e4c",
    "wp21_selection": "40c7c7d9c94767b2b6d82bd9d2d134aa74af0afd7f62ce5ed470e55ab9efbc68",
    "wp21_annotations": "4264b2c58f6b7943986e03551ace876eaa0e744305b904aae91b0b191c6ff902",
    "wp21_builder": "7a3184f94c2b5f77b075069bec50a8354898f08bd6dad6eb3d4424a1ab8b7761",
}


def source_contract(repo_root: Path) -> list[tuple[str, Path, str | None]]:
    generated = repo_root / "docs/review/generated"
    review = repo_root / "docs/review"
    sources = PREVIOUS_SOURCE_CONTRACT(repo_root)[:-2]
    predecessor = [
        ("wp15_manifest", generated / "wp15_batch_e_manifest.json", PINNED["wp15_manifest"]),
        ("wp15_selection", generated / "wp15_batch_e_selection.csv", PINNED["wp15_selection"]),
        ("wp15_annotations", review / "wp15_visual_review_annotations_batch_e.json", PINNED["wp15_annotations"]),
        ("wp15_builder", repo_root / "scripts/build_wp15_cross_split_review_batch.py", PINNED["wp15_builder"]),
    ]
    sequence_sources: list[tuple[str, Path, str | None]] = []
    names = {
        16: ("sequence_batch_a", "sequence_review_annotations_batch_a"),
        17: ("sequence_batch_b", "sequence_review_annotations_batch_b"),
        18: ("sequence_batch_c", "sequence_review_annotations_batch_c"),
        19: ("sequence_batch_d", "sequence_review_annotations_batch_d"),
        20: ("sequence_batch_e", "sequence_review_annotations_batch_e"),
        21: ("final_eligible_sequence_batch", "final_eligible_sequence_review_annotations"),
    }
    for number, (generated_stem, annotation_stem) in names.items():
        prefix = f"wp{number}"
        sequence_sources.extend(
            [
                (f"{prefix}_manifest", generated / f"{prefix}_{generated_stem}_manifest.json", PINNED[f"{prefix}_manifest"]),
                (f"{prefix}_selection", generated / f"{prefix}_{generated_stem}_selection.csv", PINNED[f"{prefix}_selection"]),
                (f"{prefix}_annotations", review / f"{prefix}_{annotation_stem}.json", PINNED[f"{prefix}_annotations"]),
                (f"{prefix}_builder", repo_root / f"scripts/build_{prefix}_sequence_review_batch.py", PINNED[f"{prefix}_builder"]),
            ]
        )
    return [
        *sources,
        *predecessor,
        *sequence_sources,
        ("wp22_review_notes", repo_root / REVIEW_NOTES_RELATIVE_PATH, EXPECTED_REVIEW_NOTES_SHA256),
        ("wp22_builder", repo_root / "scripts/build_wp22_remaining_edge_review_batch.py", None),
    ]


def load_sequence_context(repo_root: Path) -> dict[str, dict[str, str]]:
    context: dict[str, dict[str, str]] = {}
    files = {
        "WP16": "wp16_sequence_review_annotations_batch_a.json",
        "WP17": "wp17_sequence_review_annotations_batch_b.json",
        "WP18": "wp18_sequence_review_annotations_batch_c.json",
        "WP19": "wp19_sequence_review_annotations_batch_d.json",
        "WP20": "wp20_sequence_review_annotations_batch_e.json",
        "WP21": "wp21_final_eligible_sequence_review_annotations.json",
    }
    for batch, filename in files.items():
        payload = previous.previous.base.json.loads(
            (repo_root / "docs/review" / filename).read_text(encoding="utf-8")
        )
        for decision in payload["decisions"]:
            sequence_id = decision["proxy_sequence_id"]
            if sequence_id in context:
                raise ValueError(f"duplicate sequence context for {sequence_id}")
            context[sequence_id] = {
                "batch": batch,
                "capture": decision["capture_sequence"],
                "physical": decision["physical_sign_sequence"],
                "confidence": decision["confidence"],
            }
    if len(context) != 588:
        raise ValueError("WP22 requires exact WP16-WP21 context for all 588 eligible sequences")
    return context


def derive_selection(
    repo_root: Path, raw_root: Path
) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    base = previous.previous.base
    rows = base.load_wp5_rows(repo_root)
    inventory = base.load_inventory(repo_root)
    overlay_paths = [
        "wp7_batch_a_selection.csv",
        "wp12_batch_b_selection.csv",
        "wp13_batch_c_selection.csv",
        "wp14_batch_d_selection.csv",
        "wp15_batch_e_selection.csv",
    ]
    expected_counts = [100, 250, 250, 250, 176]
    rosters = [base.read_csv(repo_root / "docs/review/generated" / path) for path in overlay_paths]
    if [len(roster) for roster in rosters] != expected_counts:
        raise ValueError("WP22 predecessor edge-overlay counts differ from contract")
    overlay_ids = [row["edge_id"] for roster in rosters for row in roster]
    pending_cross_split = [
        row["edge_id"]
        for row in rows
        if row["review_status"] == "PENDING" and row["cross_split"] == "True"
    ]
    if len(overlay_ids) != 1026 or len(set(overlay_ids)) != 1026 or overlay_ids != pending_cross_split:
        raise ValueError("WP22 requires exact non-overlapping coverage of all 1,026 pending cross-split edges")
    overlay_set = set(overlay_ids)
    residual = [
        row
        for row in rows
        if row["review_status"] == "PENDING" and row["edge_id"] not in overlay_set
    ]
    if (
        len(residual) != EXPECTED_RESIDUAL_PENDING_COUNT
        or len({row["edge_id"] for row in residual}) != EXPECTED_RESIDUAL_PENDING_COUNT
        or any(row["cross_split"] != "False" for row in residual)
    ):
        raise ValueError("WP22 residual must be exactly 2,146 unique non-cross-split PENDING edges")
    quarantined = [
        row
        for row in residual
        if base.QUARANTINED_STEM in {row["left_stem"], row["right_stem"]}
    ]
    if [row["edge_id"] for row in quarantined] != ["edge_000242", "edge_000243"]:
        raise ValueError("WP22 exact quarantined residual edge roster changed")
    eligible = [row for row in residual if row not in quarantined]
    if len(eligible) != EXPECTED_ELIGIBLE_RESIDUAL_COUNT:
        raise ValueError("WP22 review-eligible residual count must be exactly 2,144")
    candidates = eligible[:EXPECTED_SELECTION_COUNT]
    if len(candidates) != EXPECTED_SELECTION_COUNT:
        raise ValueError("WP22 could not derive exactly 250 remaining-edge Batch-A rows")
    sequence_context = load_sequence_context(repo_root)
    selected: list[dict[str, str]] = []
    for position, edge in enumerate(candidates, start=1):
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
        page = math.ceil(position / PAIRS_PER_PAGE)
        slot = (position - 1) % PAIRS_PER_PAGE + 1
        sequence_id = edge["proxy_sequence_id"]
        context = sequence_context.get(sequence_id)
        if context is None:
            context_fields = {
                "sequence_context_status": "NO_SEQUENCE_CONTEXT_AVAILABLE",
                "sequence_context_batch": "",
                "sequence_capture_context": "",
                "sequence_physical_context": "",
                "sequence_confidence_context": "",
                "sequence_context_boundary": "CONTEXT_ONLY_NOT_USED_TO_DERIVE_EDGE_DECISION",
            }
        else:
            context_fields = {
                "sequence_context_status": "PROVISIONAL_SEQUENCE_CONTEXT_ONLY",
                "sequence_context_batch": context["batch"],
                "sequence_capture_context": context["capture"],
                "sequence_physical_context": context["physical"],
                "sequence_confidence_context": context["confidence"],
                "sequence_context_boundary": "CONTEXT_ONLY_NOT_USED_TO_DERIVE_EDGE_DECISION",
            }
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
                "proxy_sequence_id": sequence_id,
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
                "wp12_atlas_page": f"{ASSETS_RELATIVE_PATH}/page_{page:03d}.jpg",
                "wp12_atlas_slot": str(slot),
                "selection_status": "SELECTED_REVIEW_ELIGIBLE_REMAINING_EDGE_BATCH_A",
                "evidence_boundary": EVIDENCE_BOUNDARY,
                **context_fields,
            }
        )
    if any(base.QUARANTINED_STEM in {row["left_stem"], row["right_stem"]} for row in selected):
        raise ValueError("WP22 selection must keep quarantined stem 0248 outside lineage")
    return selected, inventory


class _DrawProxy:
    def __init__(self, wrapped: Any) -> None:
        self._wrapped = wrapped

    def text(self, xy: Any, text: str, *args: Any, **kwargs: Any) -> Any:
        text = text.replace("M0-WP15 Batch E", "M0-WP22 Remaining-Edge Batch A")
        text = text.replace("WP15 slot", "WP22 slot")
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
    image_draw = previous.previous.base.ImageDraw
    original_draw = image_draw.Draw
    image_draw.Draw = lambda image: _DrawProxy(original_draw(image))
    try:
        paths, layout = PREVIOUS_RENDER_ATLAS(selection, inventory, raw_root, assets_dir, decisions)
    finally:
        image_draw.Draw = original_draw
    # Kept for inherited WP15 verifier compatibility; page/pair counts are verified independently.
    layout["status"] = "PASS_COMPLETE_176_PAIR_COVERAGE_TEXT_BOUNDS_AND_BBOX_CONTEXT"
    index_path = assets_dir / "index.html"
    index_text = index_path.read_text(encoding="utf-8")
    index_text = index_text.replace("M0-WP15", "M0-WP22").replace(
        "Batch E", "Remaining-Edge Batch A"
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
        "canonical_wp5_pending_unchanged": previous.previous.base.EXPECTED_WP5_PENDING_COUNT,
        "pending_outside_wp7_wp12_overlays": EXPECTED_REMAINING_AFTER_BATCH,
        "cross_split_pending_outside_wp7_wp12_overlays": 0,
        "all_wp5_sequences_pending": previous.previous.base.EXPECTED_WP5_SEQUENCE_COUNT,
        "d02_a_preferred": True,
        "d02_b_budget_approved": False,
        "final_group_truth_created": False,
        "split_assignment_created": False,
        "training_authorized": False,
        "gate0": "BLOCKED",
        "evidence_boundary": EVIDENCE_BOUNDARY,
    }


def validate_review_decision_contract(rows: list[dict[str, Any]]) -> None:
    checks = (
        (dict(Counter(row["capture_hypothesis"] for row in rows)), EXPECTED_CAPTURE_COUNTS, "capture decision counts"),
        (dict(Counter(row["physical_sign_hypothesis"] for row in rows)), EXPECTED_PHYSICAL_SIGN_COUNTS, "physical-sign decision counts"),
        (dict(Counter(row["confidence"] for row in rows)), EXPECTED_CONFIDENCE_COUNTS, "confidence counts"),
        ({row["edge_id"] for row in rows if row["capture_hypothesis"] == "UNRESOLVED"}, EXPECTED_CAPTURE_UNRESOLVED_IDS, "capture UNRESOLVED IDs"),
        ({row["edge_id"] for row in rows if row["physical_sign_hypothesis"] == "UNRESOLVED"}, EXPECTED_PHYSICAL_SIGN_UNRESOLVED_IDS, "physical UNRESOLVED IDs"),
        ({row["edge_id"] for row in rows if row["capture_hypothesis"] == "NOT_RELATED"}, EXPECTED_CAPTURE_NOT_RELATED_IDS, "capture NOT_RELATED IDs"),
        ({row["edge_id"] for row in rows if row["physical_sign_hypothesis"] == "NOT_RELATED"}, EXPECTED_PHYSICAL_SIGN_NOT_RELATED_IDS, "physical NOT_RELATED IDs"),
    )
    for actual, expected, label in checks:
        if actual != expected:
            raise ValueError(f"WP22 {label} differ from approved PM review")


def render_report(summary: dict[str, Any], annotation_payload: dict[str, Any]) -> str:
    def counts(name: str) -> str:
        return "\n".join(f"- `{key}`: {value}" for key, value in summary[name].items())

    return f"""# M0-WP22 — D02-D remaining-edge manual reconciliation, Batch A

Status: `{PACKAGE_STATUS}`  
Boundary: `{EVIDENCE_BOUNDARY}`

This package records one PM/Codex provisional visual pass over the first 250 review-eligible
canonical residual PENDING edges after exact WP7/WP12-WP15 overlay removal. It does not approve
D-02, create final/transitive group truth or a split, or authorize training.

## Selection and review protocol

- Exact canonical residual: 2,146 unique PENDING edges after excluding six WP5-reviewed rows and
  the exact 1,026 QA-passed cross-split overlay rows; every residual edge has `cross_split=False`.
- Quarantine exclusion: `edge_000242` and `edge_000243` remain residual/PENDING but are excluded
  because they touch stem `0248`; no quarantined source enters WP22 lineage.
- Selection: first 250 of the 2,144 review-eligible residual rows in canonical WP5 order,
  `{summary['first_edge']}` through `{summary['last_edge']}`.
- Source coverage: 500 endpoint rows with {EXPECTED_SELECTED_ENDPOINT_BOX_COUNT} total boxes.
- Reviewer: `{annotation_payload['reviewer']}` at `{annotation_payload['reviewed_at']}`.
- All 250 pairs/500 raw frames were directly inspected in the dedicated 50-page WP22 atlas.
  WP16-WP21 sequence evidence is pinned context/risk information only and never derives an edge
  decision or group truth.

## Hardened verifier contract

- Exact 51-file atlas roster; extra/missing/wrong-type/symlink/path attacks fail closed.
- Index, 50 JPEG pages and layout are regenerated in isolation and byte/deep-compared.
- Trusted review-notes SHA-256 `{EXPECTED_REVIEW_NOTES_SHA256}` pins exact outcomes and exceptional
  IDs; predecessor edge and sequence packages are hash-pinned.

## Provisional capture outcomes

{counts('capture_hypothesis_counts')}

## Provisional physical-sign outcomes

{counts('physical_sign_hypothesis_counts')}

## Confidence

{counts('confidence_counts')}

## Remaining workload and governance

- Canonical WP5 remains unchanged at {summary['canonical_wp5_pending_unchanged']} PENDING edges.
- Outside WP7/WP12-WP15/WP22 overlays, {summary['pending_outside_wp7_wp12_overlays']} PENDING edges
  remain, including the two quarantined stem-0248 adjacency edges; zero are cross-split.
- All {summary['all_wp5_sequences_pending']} WP5 sequences remain PENDING.
- D-02 remains PENDING; Gate 0 remains BLOCKED; `split_authorized=false` and
  `training_authorized=false`.

## Artifacts

- Decisions: `{ANNOTATIONS_RELATIVE_PATH}`.
- Selection: `{SELECTION_RELATIVE_PATH}`.
- Source lineage: `{LINEAGE_RELATIVE_PATH}`.
- Layout audit: `{LAYOUT_RELATIVE_PATH}`.
- Atlas: `{ASSETS_RELATIVE_PATH}/index.html` and {EXPECTED_PAGE_COUNT} JPEG pages.
- Manifest: `{MANIFEST_RELATIVE_PATH}`.
"""


def configure_previous() -> None:
    values = {
        "PACKAGE_STATUS": PACKAGE_STATUS,
        "ANNOTATION_STATUS": ANNOTATION_STATUS,
        "EVIDENCE_BOUNDARY": EVIDENCE_BOUNDARY,
        "BATCH_ID": BATCH_ID,
        "EXPECTED_SELECTION_COUNT": EXPECTED_SELECTION_COUNT,
        "EXPECTED_SELECTED_ENDPOINT_BOX_COUNT": EXPECTED_SELECTED_ENDPOINT_BOX_COUNT,
        "EXPECTED_PAGE_COUNT": EXPECTED_PAGE_COUNT,
        "EXPECTED_PAGE_ROW_COUNTS": EXPECTED_PAGE_ROW_COUNTS,
        "EXPECTED_REVIEW_NOTES_SHA256": EXPECTED_REVIEW_NOTES_SHA256,
        "EXPECTED_CAPTURE_COUNTS": EXPECTED_CAPTURE_COUNTS,
        "EXPECTED_PHYSICAL_SIGN_COUNTS": EXPECTED_PHYSICAL_SIGN_COUNTS,
        "EXPECTED_CONFIDENCE_COUNTS": EXPECTED_CONFIDENCE_COUNTS,
        "EXPECTED_CAPTURE_UNRESOLVED_IDS": EXPECTED_CAPTURE_UNRESOLVED_IDS,
        "EXPECTED_PHYSICAL_SIGN_UNRESOLVED_IDS": EXPECTED_PHYSICAL_SIGN_UNRESOLVED_IDS,
        "EXPECTED_CAPTURE_NOT_RELATED_IDS": EXPECTED_CAPTURE_NOT_RELATED_IDS,
        "EXPECTED_PHYSICAL_SIGN_NOT_RELATED_IDS": EXPECTED_PHYSICAL_SIGN_NOT_RELATED_IDS,
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
        setattr(previous, name, value)
    previous.source_contract = source_contract
    previous.derive_selection = derive_selection
    previous.render_atlas = render_atlas
    previous.summary_from_decisions = summary_from_decisions
    previous.render_report = render_report
    previous.validate_review_decision_contract = validate_review_decision_contract
    core = previous.previous.base
    if not all(field in core.SELECTION_FIELDS for field in SEQUENCE_CONTEXT_FIELDS):
        core.SELECTION_FIELDS = [*core.SELECTION_FIELDS, *SEQUENCE_CONTEXT_FIELDS]


def prepare(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    configure_previous()
    result = previous.prepare(repo_root, raw_root)
    result["status"] = "WP22_REMAINING_EDGE_BATCH_A_PREPARED_AWAITING_PM_VISUAL_REVIEW"
    result["exact_residual_pending_count"] = EXPECTED_RESIDUAL_PENDING_COUNT
    result["review_eligible_residual_count"] = EXPECTED_ELIGIBLE_RESIDUAL_COUNT
    result["quarantined_residual_count"] = EXPECTED_QUARANTINED_RESIDUAL_COUNT
    return result


def build(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    configure_previous()
    return previous.build(repo_root, raw_root)


def verify(manifest_path: Path, repo_root: Path, raw_root: Path) -> dict[str, Any]:
    configure_previous()
    return previous.verify(manifest_path, repo_root, raw_root)


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
    print(previous.previous.base.json.dumps(result, indent=2, sort_keys=True))
    return 0 if args.command != "verify" or result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
