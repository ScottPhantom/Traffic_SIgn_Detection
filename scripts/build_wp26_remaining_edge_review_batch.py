# ruff: noqa: E501
"""Build and verify M0-WP26 remaining-edge manual-review Batch E."""

from __future__ import annotations

import argparse
import importlib.util
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

IMPL_PATH = Path(__file__).with_name("build_wp25_remaining_edge_review_batch.py")
IMPL_SPEC = importlib.util.spec_from_file_location("wp26_hardened_impl", IMPL_PATH)
assert IMPL_SPEC is not None and IMPL_SPEC.loader is not None
hardened = importlib.util.module_from_spec(IMPL_SPEC)
sys.modules[IMPL_SPEC.name] = hardened
IMPL_SPEC.loader.exec_module(hardened)

PREDECESSOR_PATH = Path(__file__).with_name("build_wp25_r1_remaining_edge_review_batch.py")
PREDECESSOR_SPEC = importlib.util.spec_from_file_location(
    "wp26_qa_passed_predecessor", PREDECESSOR_PATH
)
assert PREDECESSOR_SPEC is not None and PREDECESSOR_SPEC.loader is not None
predecessor = importlib.util.module_from_spec(PREDECESSOR_SPEC)
sys.modules[PREDECESSOR_SPEC.name] = predecessor
PREDECESSOR_SPEC.loader.exec_module(predecessor)

impl = hardened.impl
core = hardened.core
ORIGINAL_RENDER_ATLAS = hardened.ORIGINAL_RENDER_ATLAS
ORIGINAL_LOAD_SEQUENCE_CONTEXT = hardened.ORIGINAL_LOAD_SEQUENCE_CONTEXT
ORIGINAL_SUMMARY_FROM_DECISIONS = hardened.ORIGINAL_SUMMARY_FROM_DECISIONS

PACKAGE_STATUS = "WP26_AWAITING_QA_REVIEW"
ANNOTATION_STATUS = "PM_REVIEWED_AWAITING_INDEPENDENT_QA"
EVIDENCE_BOUNDARY = (
    "REMAINING_EDGE_BATCH_E_PM_PROVISIONAL_VISUAL_REVIEW_ONLY_NOT_D02_APPROVAL_"
    "NOT_GROUP_TRUTH_NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING"
)
BATCH_ID = "M0-WP26-REMAINING-EDGE-BATCH-E"
EXPECTED_SELECTION_COUNT = 250
EXPECTED_RESIDUAL_PENDING_COUNT = 1146
EXPECTED_QUARANTINED_RESIDUAL_COUNT = 2
EXPECTED_ELIGIBLE_RESIDUAL_COUNT = 1144
EXPECTED_REMAINING_AFTER_BATCH = 896
EXPECTED_SELECTED_ENDPOINT_BOX_COUNT = 997
EXPECTED_UNIQUE_STEM_COUNT = 305
EXPECTED_UNIQUE_STEM_BOX_COUNT = 600
EXPECTED_NONEMPTY_SEQUENCE_COUNT = 55
EXPECTED_PAGE_COUNT = 50
PAIRS_PER_PAGE = 5
EXPECTED_PAGE_ROW_COUNTS = (5,) * EXPECTED_PAGE_COUNT
REVIEWED_AT = "2026-10-16T00:17:42+07:00"

# Pinned only after direct readback of all 50 pages and all 250 pair panels.
EXPECTED_REVIEW_NOTES_SHA256 = (
    "47178a56aa80d5da39e146e1319dea6015e4361161b1a1fe45b91e973dcdf64d"
)
EXPECTED_CAPTURE_COUNTS = {"NOT_RELATED": 10, "SAME_CAPTURE_CANDIDATE": 240}
EXPECTED_PHYSICAL_SIGN_COUNTS = {
    "NOT_RELATED": 11,
    "SAME_PHYSICAL_SIGN_CANDIDATE": 239,
}
EXPECTED_CONFIDENCE_COUNTS = {"HIGH": 250}
EXPECTED_CAPTURE_UNRESOLVED_IDS: set[str] = set()
EXPECTED_PHYSICAL_SIGN_UNRESOLVED_IDS: set[str] = set()
EXPECTED_CAPTURE_NOT_RELATED_IDS = {
    "edge_001508",
    "edge_001526",
    "edge_001536",
    "edge_001611",
    "edge_001621",
    "edge_001670",
    "edge_001711",
    "edge_001721",
    "edge_001749",
    "edge_001759",
}
EXPECTED_PHYSICAL_SIGN_NOT_RELATED_IDS = {
    *EXPECTED_CAPTURE_NOT_RELATED_IDS,
    "edge_001644",
}

WP25_R1_MANIFEST_SHA256 = (
    "96a19417256c312c1ec005f13c5abccf85a1718d12ab0c729cb234baebfe9fe8"
)
WP25_R1_SELECTION_SHA256 = (
    "8cb67fb593d610978dcec472f0dbd0dc53b5ae1d416468b908f92ba94320e10f"
)
WP25_R1_ANNOTATIONS_SHA256 = (
    "90e6016abcbba10df96c32625e84df3284a9c8a55daccae25771fe2159db8807"
)
WP25_R1_BUILDER_SHA256 = (
    "61ea3ae5369f393f29c3c261a74f569398baba61643c4bb7896e1eb226ffd7df"
)

MANIFEST_RELATIVE_PATH = "docs/review/generated/wp26_remaining_edge_batch_e_manifest.json"
SELECTION_RELATIVE_PATH = "docs/review/generated/wp26_remaining_edge_batch_e_selection.csv"
LINEAGE_RELATIVE_PATH = "docs/review/generated/wp26_remaining_edge_batch_e_source_lineage.csv"
LAYOUT_RELATIVE_PATH = "docs/review/generated/wp26_remaining_edge_batch_e_layout_audit.json"
REPORT_RELATIVE_PATH = "docs/review/wp26_remaining_edge_batch_e_report.md"
ANNOTATIONS_RELATIVE_PATH = "docs/review/wp26_remaining_edge_review_annotations_batch_e.json"
REVIEW_NOTES_RELATIVE_PATH = "docs/review/wp26_remaining_edge_review_notes_batch_e.csv"
ASSETS_RELATIVE_PATH = "docs/review/assets/wp26/remaining_edge_batch_e"

SEQUENCE_CONTEXT_FIELDS = hardened.SEQUENCE_CONTEXT_FIELDS


def source_contract(repo_root: Path) -> list[tuple[str, Path, str | None]]:
    inherited: list[tuple[str, Path, str | None]] = []
    for item_id, path, digest in predecessor.source_contract(repo_root):
        if item_id == "wp25_r1_builder":
            digest = WP25_R1_BUILDER_SHA256
        inherited.append((item_id, path, digest))
    generated = repo_root / "docs/review/generated"
    review = repo_root / "docs/review"
    return [
        *inherited,
        (
            "wp25_r1_manifest",
            generated / "wp25_r1_remaining_edge_batch_d_manifest.json",
            WP25_R1_MANIFEST_SHA256,
        ),
        (
            "wp25_r1_selection",
            generated / "wp25_r1_remaining_edge_batch_d_selection.csv",
            WP25_R1_SELECTION_SHA256,
        ),
        (
            "wp25_r1_annotations",
            review / "wp25_r1_remaining_edge_review_annotations_batch_d.json",
            WP25_R1_ANNOTATIONS_SHA256,
        ),
        (
            "wp26_review_notes",
            repo_root / REVIEW_NOTES_RELATIVE_PATH,
            EXPECTED_REVIEW_NOTES_SHA256,
        ),
        (
            "wp26_builder",
            repo_root / "scripts/build_wp26_remaining_edge_review_batch.py",
            None,
        ),
    ]


def load_sequence_context(repo_root: Path) -> dict[str, dict[str, str]]:
    context = ORIGINAL_LOAD_SEQUENCE_CONTEXT(repo_root)
    if len(context) != 588:
        raise ValueError("WP26 requires exact WP16-WP21 context for all 588 eligible sequences")
    return context


def derive_selection(
    repo_root: Path, raw_root: Path
) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    rows = core.load_wp5_rows(repo_root)
    inventory = core.load_inventory(repo_root)
    generated = repo_root / "docs/review/generated"
    cross_split_paths = [
        "wp7_batch_a_selection.csv",
        "wp12_batch_b_selection.csv",
        "wp13_batch_c_selection.csv",
        "wp14_batch_d_selection.csv",
        "wp15_batch_e_selection.csv",
    ]
    cross_split_rosters = [core.read_csv(generated / path) for path in cross_split_paths]
    if [len(roster) for roster in cross_split_rosters] != [100, 250, 250, 250, 176]:
        raise ValueError("WP26 predecessor cross-split edge-overlay counts differ from contract")
    cross_split_ids = [row["edge_id"] for roster in cross_split_rosters for row in roster]
    canonical_pending_cross_split = [
        row["edge_id"]
        for row in rows
        if row["review_status"] == "PENDING" and row["cross_split"] == "True"
    ]
    if (
        len(cross_split_ids) != 1026
        or len(set(cross_split_ids)) != 1026
        or cross_split_ids != canonical_pending_cross_split
    ):
        raise ValueError("WP26 requires exact coverage of all 1,026 pending cross-split edges")

    base_residual = [
        row
        for row in rows
        if row["review_status"] == "PENDING" and row["edge_id"] not in set(cross_split_ids)
    ]
    if len(base_residual) != 2146 or any(row["cross_split"] != "False" for row in base_residual):
        raise ValueError("WP26 canonical base residual must be 2,146 non-cross-split PENDING edges")
    base_quarantined = [
        row
        for row in base_residual
        if core.QUARANTINED_STEM in {row["left_stem"], row["right_stem"]}
    ]
    if [row["edge_id"] for row in base_quarantined] != ["edge_000242", "edge_000243"]:
        raise ValueError("WP26 exact quarantined residual roster changed")
    base_eligible = [row for row in base_residual if row not in base_quarantined]
    if len(base_eligible) != 2144:
        raise ValueError("WP26 base eligible residual must contain exactly 2,144 edges")

    predecessor_files = (
        "wp22_remaining_edge_batch_a_selection.csv",
        "wp23_r1_remaining_edge_batch_b_selection.csv",
        "wp24_remaining_edge_batch_c_selection.csv",
        "wp25_r1_remaining_edge_batch_d_selection.csv",
    )
    predecessor_rosters = [core.read_csv(generated / name) for name in predecessor_files]
    labels = ("WP22", "WP23-R1", "WP24", "WP25-R1")
    for index, (label, roster) in enumerate(zip(labels, predecessor_rosters, strict=True)):
        expected_ids = [
            row["edge_id"] for row in base_eligible[index * 250 : (index + 1) * 250]
        ]
        if [row["edge_id"] for row in roster] != expected_ids:
            raise ValueError(f"WP26 requires the exact canonical QA-passed {label} prefix slice")
    predecessor_remaining_ids = {
        row["edge_id"] for roster in predecessor_rosters for row in roster
    }
    if len(predecessor_remaining_ids) != 1000:
        raise ValueError("WP26 predecessor remaining-edge overlays overlap")

    predecessor_ids = set(cross_split_ids) | predecessor_remaining_ids
    residual = [
        row
        for row in rows
        if row["review_status"] == "PENDING" and row["edge_id"] not in predecessor_ids
    ]
    if (
        len(residual) != EXPECTED_RESIDUAL_PENDING_COUNT
        or len({row["edge_id"] for row in residual}) != EXPECTED_RESIDUAL_PENDING_COUNT
        or any(row["cross_split"] != "False" for row in residual)
    ):
        raise ValueError("WP26 residual must be exactly 1,146 unique non-cross-split PENDING edges")
    quarantined = [
        row
        for row in residual
        if core.QUARANTINED_STEM in {row["left_stem"], row["right_stem"]}
    ]
    if [row["edge_id"] for row in quarantined] != ["edge_000242", "edge_000243"]:
        raise ValueError("WP26 quarantined residual edge roster changed")
    eligible = [row for row in residual if row not in quarantined]
    if len(eligible) != EXPECTED_ELIGIBLE_RESIDUAL_COUNT:
        raise ValueError("WP26 review-eligible residual must contain exactly 1,144 edges")
    candidates = eligible[:EXPECTED_SELECTION_COUNT]
    if len(candidates) != EXPECTED_SELECTION_COUNT:
        raise ValueError("WP26 could not derive exactly 250 Batch-E rows")

    sequence_context = load_sequence_context(repo_root)
    selected: list[dict[str, str]] = []
    for position, edge in enumerate(candidates, start=1):
        left = inventory[edge["left_stem"]]
        right = inventory[edge["right_stem"]]
        core.verify_raw_record(left, raw_root)
        core.verify_raw_record(right, raw_root)
        for side, source in (("left", left), ("right", right)):
            if (
                edge[f"{side}_image_sha256"] != source["image_sha256"]
                or edge[f"{side}_label_sha256"] != source["label_sha256"]
            ):
                raise ValueError(f"WP5/inventory source binding drift for {edge['edge_id']}")
        page = math.ceil(position / PAIRS_PER_PAGE)
        slot = (position - 1) % PAIRS_PER_PAGE + 1
        context = sequence_context.get(edge["proxy_sequence_id"])
        context_fields = {
            "sequence_context_status": "NO_SEQUENCE_CONTEXT_AVAILABLE",
            "sequence_context_batch": "",
            "sequence_capture_context": "",
            "sequence_physical_context": "",
            "sequence_confidence_context": "",
            "sequence_context_boundary": "CONTEXT_ONLY_NOT_USED_TO_DERIVE_EDGE_DECISION",
        }
        if context is not None:
            context_fields.update(
                sequence_context_status="PROVISIONAL_SEQUENCE_CONTEXT_ONLY",
                sequence_context_batch=context["batch"],
                sequence_capture_context=context["capture"],
                sequence_physical_context=context["physical"],
                sequence_confidence_context=context["confidence"],
            )
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
                "wp12_atlas_page": f"{ASSETS_RELATIVE_PATH}/page_{page:03d}.jpg",
                "wp12_atlas_slot": str(slot),
                "selection_status": "SELECTED_REVIEW_ELIGIBLE_REMAINING_EDGE_BATCH_E",
                "evidence_boundary": EVIDENCE_BOUNDARY,
                **context_fields,
            }
        )

    unique_stems = {row[side] for row in selected for side in ("left_stem", "right_stem")}
    endpoint_box_count = sum(
        int(inventory[row[side]]["box_count"])
        for row in selected
        for side in ("left_stem", "right_stem")
    )
    unique_box_count = sum(int(inventory[stem]["box_count"]) for stem in unique_stems)
    nonempty_sequence_ids = {
        row["proxy_sequence_id"] for row in selected if row["proxy_sequence_id"]
    }
    if (
        selected[0]["edge_id"] != "edge_001505"
        or selected[0]["wp5_review_order"] != "2035"
        or selected[0]["left_stem"] != "1512"
        or selected[0]["right_stem"] != "1513"
        or selected[-1]["edge_id"] != "edge_001850"
        or selected[-1]["wp5_review_order"] != "2284"
        or selected[-1]["left_stem"] != "1867"
        or selected[-1]["right_stem"] != "1868"
        or len(unique_stems) != EXPECTED_UNIQUE_STEM_COUNT
        or endpoint_box_count != EXPECTED_SELECTED_ENDPOINT_BOX_COUNT
        or unique_box_count != EXPECTED_UNIQUE_STEM_BOX_COUNT
        or len(nonempty_sequence_ids) != EXPECTED_NONEMPTY_SEQUENCE_COUNT
        or "proxy_sequence_0050" in nonempty_sequence_ids
        or Counter(
            inventory[row[side]]["split"]
            for row in selected
            for side in ("left_stem", "right_stem")
        )
        != Counter({"train": 472, "test": 28})
        or Counter(row["proxy_status"] for row in selected)
        != Counter({"strong_candidate": 160, "uncertain": 68, "adjacency_only": 22})
        or len(eligible[EXPECTED_SELECTION_COUNT:]) + len(quarantined)
        != EXPECTED_REMAINING_AFTER_BATCH
    ):
        raise ValueError(
            "WP26 independently derived selection or quarantine boundary differs from acceptance anchors"
        )
    return selected, inventory


class _DrawProxy:
    def __init__(self, wrapped: Any) -> None:
        self._wrapped = wrapped

    def text(self, xy: Any, text: str, *args: Any, **kwargs: Any) -> Any:
        text = text.replace("M0-WP23 Remaining-Edge Batch B", "M0-WP26 Remaining-Edge Batch E")
        text = text.replace("WP23 slot", "WP26 slot")
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
    image_draw = core.ImageDraw
    original_draw = image_draw.Draw
    image_draw.Draw = lambda image: _DrawProxy(original_draw(image))
    try:
        paths, layout = ORIGINAL_RENDER_ATLAS(
            selection, inventory, raw_root, assets_dir, decisions
        )
    finally:
        image_draw.Draw = original_draw
    index_path = assets_dir / "index.html"
    index_text = index_path.read_text(encoding="utf-8")
    index_text = (
        index_text.replace("M0-WP23", "M0-WP26")
        .replace("Remaining-Edge Batch B", "Remaining-Edge Batch E")
        .replace("WP23 slot", "WP26 slot")
    )
    index_path.write_text(index_text, encoding="utf-8")
    return paths, layout


def summary_from_decisions(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    summary = ORIGINAL_SUMMARY_FROM_DECISIONS(decisions)
    summary["batch"] = BATCH_ID
    summary["status"] = PACKAGE_STATUS
    summary["pending_outside_wp7_wp12_overlays"] = EXPECTED_REMAINING_AFTER_BATCH
    summary["evidence_boundary"] = EVIDENCE_BOUNDARY
    return summary


def validate_review_decision_contract(rows: list[dict[str, Any]]) -> None:
    checks = (
        (
            dict(Counter(row["capture_hypothesis"] for row in rows)),
            EXPECTED_CAPTURE_COUNTS,
            "capture counts",
        ),
        (
            dict(Counter(row["physical_sign_hypothesis"] for row in rows)),
            EXPECTED_PHYSICAL_SIGN_COUNTS,
            "physical-sign counts",
        ),
        (
            dict(Counter(row["confidence"] for row in rows)),
            EXPECTED_CONFIDENCE_COUNTS,
            "confidence counts",
        ),
        (
            {row["edge_id"] for row in rows if row["capture_hypothesis"] == "UNRESOLVED"},
            EXPECTED_CAPTURE_UNRESOLVED_IDS,
            "capture UNRESOLVED IDs",
        ),
        (
            {
                row["edge_id"]
                for row in rows
                if row["physical_sign_hypothesis"] == "UNRESOLVED"
            },
            EXPECTED_PHYSICAL_SIGN_UNRESOLVED_IDS,
            "physical UNRESOLVED IDs",
        ),
        (
            {row["edge_id"] for row in rows if row["capture_hypothesis"] == "NOT_RELATED"},
            EXPECTED_CAPTURE_NOT_RELATED_IDS,
            "capture NOT_RELATED IDs",
        ),
        (
            {
                row["edge_id"]
                for row in rows
                if row["physical_sign_hypothesis"] == "NOT_RELATED"
            },
            EXPECTED_PHYSICAL_SIGN_NOT_RELATED_IDS,
            "physical NOT_RELATED IDs",
        ),
    )
    for actual, expected, label in checks:
        if actual != expected:
            raise ValueError(f"WP26 {label} differ from the PM visual-review contract")


def render_report(summary: dict[str, Any], annotation_payload: dict[str, Any]) -> str:
    def counts(name: str) -> str:
        return "\n".join(f"- `{key}`: {value}" for key, value in summary[name].items())

    return f"""# M0-WP26 — D02-D remaining-edge manual reconciliation, Batch E

Status: `{PACKAGE_STATUS}`  
Boundary: `{EVIDENCE_BOUNDARY}`

This append-only package records one PM/Codex provisional visual pass over the exact next 250
review-eligible canonical residual PENDING edges after the QA-passed WP22, WP23-R1, WP24 and
WP25-R1 overlays. It does not approve D-02, create final/transitive group truth or a split, or
authorize training.

## Selection and review protocol

- Exact predecessor residual: 1,146 unique non-cross-split PENDING edges after removing the
  canonical cross-split overlays, WP22, WP23-R1, WP24 and WP25-R1.
- Quarantine exclusion: `edge_000242` and `edge_000243` remain residual/PENDING but stay outside
  WP26 because they touch stem `0248`.
- Selection: first 250 of 1,144 eligible residual rows in canonical WP5 order,
  `{summary['first_edge']}` through `{summary['last_edge']}`.
- Source coverage: 500 endpoint rows, {EXPECTED_UNIQUE_STEM_COUNT} unique stems,
  {EXPECTED_SELECTED_ENDPOINT_BOX_COUNT} endpoint bbox occurrences and
  {EXPECTED_UNIQUE_STEM_BOX_COUNT} unique-stem bbox occurrences.
- Reviewer: `{annotation_payload['reviewer']}` at `{annotation_payload['reviewed_at']}`.
- All 250 pairs/500 raw frames were directly inspected in the dedicated 50-page WP26 atlas.
  Sequence evidence remained context-only and never derived an edge decision or group truth.

## Hardened verifier contract

- Exact 51-file atlas roster; extra/missing/wrong-type/symlink/path attacks fail closed.
- Index, all 50 JPEG pages and layout regenerate in isolation and byte/deep-compare.
- Trusted review-notes SHA-256 `{EXPECTED_REVIEW_NOTES_SHA256}` pins exact outcomes and
  exceptional IDs; QA-passed WP25-R1 and immutable initial WP25 audit lineage are hash-pinned.

## Provisional capture outcomes

{counts('capture_hypothesis_counts')}

## Provisional physical-sign outcomes

{counts('physical_sign_hypothesis_counts')}

## Confidence

{counts('confidence_counts')}

## Remaining workload and governance

- Canonical WP5 remains unchanged at {summary['canonical_wp5_pending_unchanged']} PENDING edges.
- Outside the reviewed edge overlays, {summary['pending_outside_wp7_wp12_overlays']} PENDING
  edges remain, including the two quarantined stem-0248 adjacency edges; zero are cross-split.
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


def _configure() -> None:
    values = {
        "PACKAGE_STATUS": PACKAGE_STATUS,
        "ANNOTATION_STATUS": ANNOTATION_STATUS,
        "EVIDENCE_BOUNDARY": EVIDENCE_BOUNDARY,
        "BATCH_ID": BATCH_ID,
        "EXPECTED_SELECTION_COUNT": EXPECTED_SELECTION_COUNT,
        "EXPECTED_RESIDUAL_PENDING_COUNT": EXPECTED_RESIDUAL_PENDING_COUNT,
        "EXPECTED_QUARANTINED_RESIDUAL_COUNT": EXPECTED_QUARANTINED_RESIDUAL_COUNT,
        "EXPECTED_ELIGIBLE_RESIDUAL_COUNT": EXPECTED_ELIGIBLE_RESIDUAL_COUNT,
        "EXPECTED_REMAINING_AFTER_BATCH": EXPECTED_REMAINING_AFTER_BATCH,
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
        "source_contract": source_contract,
        "derive_selection": derive_selection,
        "render_atlas": render_atlas,
        "summary_from_decisions": summary_from_decisions,
        "render_report": render_report,
        "validate_review_decision_contract": validate_review_decision_contract,
        "load_sequence_context": load_sequence_context,
    }
    for name, value in values.items():
        setattr(impl, name, value)
    impl.configure_previous()
    if not all(field in core.SELECTION_FIELDS for field in SEQUENCE_CONTEXT_FIELDS):
        core.SELECTION_FIELDS = [*core.SELECTION_FIELDS, *SEQUENCE_CONTEXT_FIELDS]


def prepare(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    _configure()
    result = impl.previous.prepare(repo_root, raw_root)
    result.update(
        status="WP26_PREPARED_AWAITING_PM_VISUAL_REVIEW",
        exact_residual_pending_count=EXPECTED_RESIDUAL_PENDING_COUNT,
        review_eligible_residual_count=EXPECTED_ELIGIBLE_RESIDUAL_COUNT,
        quarantined_residual_count=EXPECTED_QUARANTINED_RESIDUAL_COUNT,
    )
    return result


def build(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    _configure()
    return impl.previous.build(repo_root, raw_root)


def verify(manifest_path: Path, repo_root: Path, raw_root: Path) -> dict[str, Any]:
    _configure()
    return impl.previous.verify(manifest_path, repo_root, raw_root)


_configure()

artifact_contract = core.artifact_contract
expected_atlas_names = core.expected_atlas_names
derive_lineage = core.derive_lineage
validate_governance = core.validate_governance
sha256_file = core.sha256_file


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
    print(core.json.dumps(result, indent=2, sort_keys=True))
    return 0 if args.command != "verify" or result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
