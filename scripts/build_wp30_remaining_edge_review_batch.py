# ruff: noqa: E501
"""Build and verify M0-WP30 final remaining-edge manual-review Batch I."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import types
from collections import Counter
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

PREVIOUS_PATH = Path(__file__).with_name("build_wp29_remaining_edge_review_batch.py")
PREVIOUS_SPEC = importlib.util.spec_from_file_location("wp30_qa_passed_predecessor", PREVIOUS_PATH)
assert PREVIOUS_SPEC is not None and PREVIOUS_SPEC.loader is not None
previous = importlib.util.module_from_spec(PREVIOUS_SPEC)
sys.modules[PREVIOUS_SPEC.name] = previous
PREVIOUS_SPEC.loader.exec_module(previous)

impl = previous.impl
core = previous.core
ORIGINAL_LOAD_SEQUENCE_CONTEXT = previous.ORIGINAL_LOAD_SEQUENCE_CONTEXT
ORIGINAL_SUMMARY_FROM_DECISIONS = previous.ORIGINAL_SUMMARY_FROM_DECISIONS
WP29_RENDER_ATLAS = previous.render_atlas
WP15_MODULE = previous.WP15_MODULE
ORIGINAL_WP15_VERIFY_MANIFEST = previous.ORIGINAL_WP15_VERIFY_MANIFEST
strict_semantic_diff = previous.strict_semantic_diff
_strict_types = previous._strict_types
TOP_LEVEL_LAYOUT_TYPES = previous.TOP_LEVEL_LAYOUT_TYPES
PAGE_LAYOUT_TYPES = previous.PAGE_LAYOUT_TYPES
ROW_LAYOUT_TYPES = previous.ROW_LAYOUT_TYPES

PACKAGE_STATUS = "WP30_AWAITING_QA_REVIEW"
ANNOTATION_STATUS = "PM_REVIEWED_AWAITING_INDEPENDENT_QA"
EVIDENCE_BOUNDARY = (
    "REMAINING_EDGE_BATCH_I_FINAL_PM_PROVISIONAL_VISUAL_REVIEW_ONLY_NOT_D02_APPROVAL_"
    "NOT_GROUP_TRUTH_NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING"
)
BATCH_ID = "M0-WP30-REMAINING-EDGE-BATCH-I-FINAL"
EXPECTED_SELECTION_COUNT = 144
EXPECTED_RESIDUAL_PENDING_COUNT = 146
EXPECTED_QUARANTINED_RESIDUAL_COUNT = 2
EXPECTED_ELIGIBLE_RESIDUAL_COUNT = 144
EXPECTED_REMAINING_AFTER_BATCH = 2
EXPECTED_SELECTED_ENDPOINT_BOX_COUNT = 888
EXPECTED_UNIQUE_STEM_COUNT = 172
EXPECTED_UNIQUE_STEM_BOX_COUNT = 537
EXPECTED_NONEMPTY_SEQUENCE_COUNT = 31
EXPECTED_PAGE_COUNT = 29
PAIRS_PER_PAGE = 5
EXPECTED_PAGE_ROW_COUNTS = (5,) * 28 + (4,)
EXPECTED_LAYOUT_STATUS = "PASS_COMPLETE_144_PAIR_COVERAGE_TEXT_BOUNDS_AND_BBOX_CONTEXT"
INHERITED_STALE_LAYOUT_STATUS = previous.INHERITED_STALE_LAYOUT_STATUS
REVIEWED_AT = "2026-10-17T10:30:00+07:00"

# Replaced only after direct readback of all 29 pages and all 144 pair panels.
EXPECTED_REVIEW_NOTES_SHA256 = "488c69d1f5c9b59838bbde57e9861be7c1fb431749f7fc6e78608ff0fe28551c"
EXPECTED_CAPTURE_COUNTS = {"NOT_RELATED": 4, "SAME_CAPTURE_CANDIDATE": 140}
EXPECTED_PHYSICAL_SIGN_COUNTS = {
    "NOT_RELATED": 5,
    "SAME_PHYSICAL_SIGN_CANDIDATE": 139,
}
EXPECTED_CONFIDENCE_COUNTS = {"HIGH": 143, "MEDIUM": 1}
EXPECTED_CAPTURE_UNRESOLVED_IDS: set[str] = set()
EXPECTED_PHYSICAL_SIGN_UNRESOLVED_IDS: set[str] = set()
# Discontinuous scenes (location, riders and signs all change).
EXPECTED_CAPTURE_NOT_RELATED_IDS = {"edge_003047", "edge_003092", "edge_003128", "edge_003153"}
# edge_002977 is same-capture (out-of-order frames, as WP29 edge_002967) but different signs.
EXPECTED_PHYSICAL_SIGN_NOT_RELATED_IDS = {
    "edge_002977",
    "edge_003047",
    "edge_003092",
    "edge_003128",
    "edge_003153",
}
EXPECTED_MEDIUM_CONFIDENCE_IDS = {"edge_002977"}

WP29_BUILDER_SHA256 = "352cec7944313354502c9adecfb2105243d17754ee6f330db3b0bec6b1089719"
WP29_TEST_SHA256 = "34a3b9d95014fd27d970069999c3b96430db127051fd076bc22cb47d9a5ceb15"
WP29_MANIFEST_SHA256 = "e7b56820d4dca24e54dc7f58f3e94d929f3d626b9ddb753d0e176c9de5b59a63"
WP29_SELECTION_SHA256 = "e880898c6699d89512834f1b7a4839dad216570c0cca5de0353073fa86e4357b"
WP29_ANNOTATIONS_SHA256 = "c4ade02295ca6a09f22930a6a413564c0a50822884215ef8b56d679b77fc7490"
WP28_R2_WP29_QA_RECORD_SHA256 = "d2c0123bfa46d06f38bfd8a74d4ed94de7f274d515d9171f9a6a9af671308e37"

MANIFEST_RELATIVE_PATH = "docs/review/generated/wp30_remaining_edge_batch_i_manifest.json"
SELECTION_RELATIVE_PATH = "docs/review/generated/wp30_remaining_edge_batch_i_selection.csv"
LINEAGE_RELATIVE_PATH = "docs/review/generated/wp30_remaining_edge_batch_i_source_lineage.csv"
LAYOUT_RELATIVE_PATH = "docs/review/generated/wp30_remaining_edge_batch_i_layout_audit.json"
REPORT_RELATIVE_PATH = "docs/review/wp30_remaining_edge_batch_i_report.md"
ANNOTATIONS_RELATIVE_PATH = "docs/review/wp30_remaining_edge_review_annotations_batch_i.json"
REVIEW_NOTES_RELATIVE_PATH = "docs/review/wp30_remaining_edge_review_notes_batch_i.csv"
ASSETS_RELATIVE_PATH = "docs/review/assets/wp30/remaining_edge_batch_i"

SEQUENCE_CONTEXT_FIELDS = previous.SEQUENCE_CONTEXT_FIELDS
CROSS_SPLIT_OVERLAYS = (
    ("wp7_batch_a_selection.csv", 100),
    ("wp12_batch_b_selection.csv", 250),
    ("wp13_batch_c_selection.csv", 250),
    ("wp14_batch_d_selection.csv", 250),
    ("wp15_batch_e_selection.csv", 176),
)
REMAINING_EDGE_PREDECESSORS = (
    ("WP22", "wp22_remaining_edge_batch_a_selection.csv"),
    ("WP23-R1", "wp23_r1_remaining_edge_batch_b_selection.csv"),
    ("WP24", "wp24_remaining_edge_batch_c_selection.csv"),
    ("WP25-R1", "wp25_r1_remaining_edge_batch_d_selection.csv"),
    ("WP26", "wp26_remaining_edge_batch_e_selection.csv"),
    ("WP27-R2", "wp27_remaining_edge_batch_f_selection.csv"),
    ("WP28-R2", "wp28_r2_remaining_edge_batch_g_selection.csv"),
    ("WP29", "wp29_remaining_edge_batch_h_selection.csv"),
)



def _derive_exact_status_verify_manifest() -> Callable[..., dict[str, Any]]:
    """Return the QA-passed WP15 verifier with only its stale 176-pair status constant replaced."""
    code = ORIGINAL_WP15_VERIFY_MANIFEST.__code__
    if code.co_consts.count(INHERITED_STALE_LAYOUT_STATUS) != 1:
        raise ValueError("inherited WP15 verifier no longer has exactly one stale status constant")
    if EXPECTED_LAYOUT_STATUS in code.co_consts:
        raise ValueError("inherited WP15 verifier unexpectedly already contains the exact status")
    consts = tuple(
        EXPECTED_LAYOUT_STATUS if value == INHERITED_STALE_LAYOUT_STATUS else value
        for value in code.co_consts
    )
    return types.FunctionType(
        code.replace(co_consts=consts),
        ORIGINAL_WP15_VERIFY_MANIFEST.__globals__,
        ORIGINAL_WP15_VERIFY_MANIFEST.__name__,
        ORIGINAL_WP15_VERIFY_MANIFEST.__defaults__,
        ORIGINAL_WP15_VERIFY_MANIFEST.__closure__,
    )


EXACT_STATUS_VERIFY_MANIFEST = _derive_exact_status_verify_manifest()


@contextmanager
def _exact_status_verifier() -> Iterator[None]:
    WP15_MODULE.verify_manifest = EXACT_STATUS_VERIFY_MANIFEST
    try:
        yield
    finally:
        WP15_MODULE.verify_manifest = ORIGINAL_WP15_VERIFY_MANIFEST


def source_contract(repo_root: Path) -> list[tuple[str, Path, str | None]]:
    inherited: list[tuple[str, Path, str | None]] = []
    for item_id, path, digest in previous.source_contract(repo_root):
        if item_id == "wp29_builder":
            continue
        inherited.append((item_id, path, digest))
    generated = repo_root / "docs/review/generated"
    review = repo_root / "docs/review"
    return [
        *inherited,
        ("wp29_builder", repo_root / "scripts/build_wp29_remaining_edge_review_batch.py", WP29_BUILDER_SHA256),
        ("wp29_test", repo_root / "tests/test_wp29_remaining_edge_review_batch.py", WP29_TEST_SHA256),
        ("wp29_manifest", generated / "wp29_remaining_edge_batch_h_manifest.json", WP29_MANIFEST_SHA256),
        ("wp29_selection", generated / "wp29_remaining_edge_batch_h_selection.csv", WP29_SELECTION_SHA256),
        ("wp29_annotations", review / "wp29_remaining_edge_review_annotations_batch_h.json", WP29_ANNOTATIONS_SHA256),
        ("wp28_r2_wp29_qa_record", review / "wp28_r2_wp29_independent_qa_record.md", WP28_R2_WP29_QA_RECORD_SHA256),
        ("wp30_review_notes", repo_root / REVIEW_NOTES_RELATIVE_PATH, EXPECTED_REVIEW_NOTES_SHA256),
        ("wp30_builder", repo_root / "scripts/build_wp30_remaining_edge_review_batch.py", None),
    ]


def load_sequence_context(repo_root: Path) -> dict[str, dict[str, str]]:
    context = ORIGINAL_LOAD_SEQUENCE_CONTEXT(repo_root)
    if len(context) != 588:
        raise ValueError("WP30 requires exact WP16-WP21 context for all 588 eligible sequences")
    return context


def derive_residual(repo_root: Path) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    """Return (residual, quarantined, eligible) after the exact QA-passed predecessor chain."""
    rows = core.load_wp5_rows(repo_root)
    generated = repo_root / "docs/review/generated"
    cross_split_rosters = [core.read_csv(generated / name) for name, _count in CROSS_SPLIT_OVERLAYS]
    if [len(roster) for roster in cross_split_rosters] != [count for _name, count in CROSS_SPLIT_OVERLAYS]:
        raise ValueError("WP30 predecessor cross-split edge-overlay counts differ from contract")
    cross_split_ids = [row["edge_id"] for roster in cross_split_rosters for row in roster]
    canonical_pending_cross_split = [
        row["edge_id"]
        for row in rows
        if row["review_status"] == "PENDING" and row["cross_split"] == "True"
    ]
    if len(set(cross_split_ids)) != 1026 or cross_split_ids != canonical_pending_cross_split:
        raise ValueError("WP30 requires exact coverage of all 1,026 pending cross-split edges")
    cross_split_set = set(cross_split_ids)
    base_residual = [
        row for row in rows if row["review_status"] == "PENDING" and row["edge_id"] not in cross_split_set
    ]
    if len(base_residual) != 2146 or any(row["cross_split"] != "False" for row in base_residual):
        raise ValueError("WP30 canonical base residual must be 2,146 non-cross-split PENDING edges")
    base_eligible = [
        row for row in base_residual if core.QUARANTINED_STEM not in {row["left_stem"], row["right_stem"]}
    ]
    if len(base_eligible) != 2144:
        raise ValueError("WP30 base eligible residual must contain exactly 2,144 edges")
    predecessor_ids: set[str] = set()
    for index, (label, name) in enumerate(REMAINING_EDGE_PREDECESSORS):
        roster = core.read_csv(generated / name)
        expected_ids = [row["edge_id"] for row in base_eligible[index * 250 : (index + 1) * 250]]
        if [row["edge_id"] for row in roster] != expected_ids:
            raise ValueError(f"WP30 requires the exact canonical QA-passed {label} prefix slice")
        predecessor_ids.update(expected_ids)
    if len(predecessor_ids) != 2000:
        raise ValueError("WP30 predecessor remaining-edge overlays overlap")
    excluded = cross_split_set | predecessor_ids
    residual = [row for row in rows if row["review_status"] == "PENDING" and row["edge_id"] not in excluded]
    if (
        len(residual) != EXPECTED_RESIDUAL_PENDING_COUNT
        or len({row["edge_id"] for row in residual}) != EXPECTED_RESIDUAL_PENDING_COUNT
        or any(row["cross_split"] != "False" for row in residual)
    ):
        raise ValueError("WP30 residual must be exactly 146 unique non-cross-split PENDING edges")
    quarantined = [row for row in residual if core.QUARANTINED_STEM in {row["left_stem"], row["right_stem"]}]
    if [row["edge_id"] for row in quarantined] != ["edge_000242", "edge_000243"]:
        raise ValueError("WP30 quarantined residual edge roster changed")
    eligible = [row for row in residual if row not in quarantined]
    if len(eligible) != EXPECTED_ELIGIBLE_RESIDUAL_COUNT or eligible != base_eligible[2000:]:
        raise ValueError("WP30 review-eligible residual must be exactly base_eligible[2000:] (144 edges)")
    return residual, quarantined, eligible


def derive_selection(
    repo_root: Path, raw_root: Path
) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    inventory = core.load_inventory(repo_root)
    _residual, quarantined, eligible = derive_residual(repo_root)
    candidates = eligible[:EXPECTED_SELECTION_COUNT]
    if len(candidates) != EXPECTED_SELECTION_COUNT or eligible[EXPECTED_SELECTION_COUNT:]:
        raise ValueError("WP30 must select the complete residual eligible suffix (exactly 144 rows)")
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
                "selection_status": "SELECTED_REVIEW_ELIGIBLE_FINAL_REMAINING_EDGE_BATCH_I",
                "evidence_boundary": EVIDENCE_BOUNDARY,
                **context_fields,
            }
        )

    unique_stems = {row[side] for row in selected for side in ("left_stem", "right_stem")}
    endpoint_box_count = sum(
        int(inventory[row[side]]["box_count"]) for row in selected for side in ("left_stem", "right_stem")
    )
    unique_box_count = sum(int(inventory[stem]["box_count"]) for stem in unique_stems)
    nonempty_sequence_ids = {row["proxy_sequence_id"] for row in selected if row["proxy_sequence_id"]}
    if (
        selected[0]["edge_id"] != "edge_002973"
        or selected[0]["wp5_review_order"] != "3035"
        or selected[0]["left_stem"] != "3010"
        or selected[0]["right_stem"] != "3011"
        or selected[-1]["edge_id"] != "edge_003176"
        or selected[-1]["wp5_review_order"] != "3178"
        or selected[-1]["left_stem"] != "3213"
        or selected[-1]["right_stem"] != "3214"
        or core.QUARANTINED_STEM in unique_stems
        or len(unique_stems) != EXPECTED_UNIQUE_STEM_COUNT
        or endpoint_box_count != EXPECTED_SELECTED_ENDPOINT_BOX_COUNT
        or unique_box_count != EXPECTED_UNIQUE_STEM_BOX_COUNT
        or len(nonempty_sequence_ids) != EXPECTED_NONEMPTY_SEQUENCE_COUNT
        or "proxy_sequence_0050" in nonempty_sequence_ids
        or Counter(inventory[row[side]]["split"] for row in selected for side in ("left_stem", "right_stem"))
        != Counter({"train": 280, "test": 8})
        or Counter(row["proxy_status"] for row in selected)
        != Counter({"strong_candidate": 79, "uncertain": 49, "adjacency_only": 16})
        or len(eligible[EXPECTED_SELECTION_COUNT:]) + len(quarantined) != EXPECTED_REMAINING_AFTER_BATCH
    ):
        raise ValueError("WP30 independently derived selection or quarantine boundary differs from acceptance anchors")
    return selected, inventory


class _DrawProxy:
    def __init__(self, wrapped: Any) -> None:
        self._wrapped = wrapped

    def text(self, xy: Any, text: str, *args: Any, **kwargs: Any) -> Any:
        text = text.replace("M0-WP29 Remaining-Edge Batch H", "M0-WP30 Remaining-Edge Batch I")
        text = text.replace("WP29 slot", "WP30 slot")
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
        paths, layout = WP29_RENDER_ATLAS(selection, inventory, raw_root, assets_dir, decisions)
    finally:
        image_draw.Draw = original_draw
    # WP28 stamps the exact pair count into the layout status; the index heading is relabeled.
    index_path = assets_dir / "index.html"
    index_text = index_path.read_text(encoding="utf-8")
    index_text = (
        index_text.replace("M0-WP29", "M0-WP30")
        .replace("Remaining-Edge Batch H", "Remaining-Edge Batch I")
        .replace("WP29 slot", "WP30 slot")
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
        (dict(Counter(row["capture_hypothesis"] for row in rows)), EXPECTED_CAPTURE_COUNTS, "capture counts"),
        (dict(Counter(row["physical_sign_hypothesis"] for row in rows)), EXPECTED_PHYSICAL_SIGN_COUNTS, "physical-sign counts"),
        (dict(Counter(row["confidence"] for row in rows)), EXPECTED_CONFIDENCE_COUNTS, "confidence counts"),
        ({row["edge_id"] for row in rows if row["capture_hypothesis"] == "UNRESOLVED"}, EXPECTED_CAPTURE_UNRESOLVED_IDS, "capture UNRESOLVED IDs"),
        ({row["edge_id"] for row in rows if row["physical_sign_hypothesis"] == "UNRESOLVED"}, EXPECTED_PHYSICAL_SIGN_UNRESOLVED_IDS, "physical UNRESOLVED IDs"),
        ({row["edge_id"] for row in rows if row["capture_hypothesis"] == "NOT_RELATED"}, EXPECTED_CAPTURE_NOT_RELATED_IDS, "capture NOT_RELATED IDs"),
        ({row["edge_id"] for row in rows if row["physical_sign_hypothesis"] == "NOT_RELATED"}, EXPECTED_PHYSICAL_SIGN_NOT_RELATED_IDS, "physical NOT_RELATED IDs"),
        ({row["edge_id"] for row in rows if row["confidence"] == "MEDIUM"}, EXPECTED_MEDIUM_CONFIDENCE_IDS, "MEDIUM confidence IDs"),
    )
    for actual, expected, label in checks:
        if actual != expected:
            raise ValueError(f"WP30 {label} differ from the PM visual-review contract")


def render_report(summary: dict[str, Any], annotation_payload: dict[str, Any]) -> str:
    def counts(name: str) -> str:
        return "\n".join(f"- `{key}`: {value}" for key, value in summary[name].items())

    return f"""# M0-WP30 — D02-D remaining-edge manual reconciliation, final Batch I

Status: `{PACKAGE_STATUS}`
Boundary: `{EVIDENCE_BOUNDARY}`

This append-only package records one PM provisional visual pass over the complete final suffix of
review-eligible canonical residual PENDING edges after the QA-passed WP22, WP23-R1, WP24, WP25-R1,
WP26, WP27-R2, WP28-R2 and WP29 overlays. It does not approve D-02, create final/transitive group
truth or a split, or authorize training.

## Selection and review protocol

- Exact predecessor residual: 146 unique non-cross-split PENDING edges after removing the
  canonical cross-split overlays and the eight QA-passed remaining-edge prefixes.
- Quarantine exclusion: `edge_000242` and `edge_000243` remain residual/PENDING but stay outside
  WP30 because they touch stem `0248`; `proxy_sequence_0050` is not selected.
- Selection: all 144 remaining eligible residual rows in canonical WP5 order,
  `{summary['first_edge']}` through `{summary['last_edge']}`; no eligible edge remains after WP30.
- Source coverage: 288 endpoint rows, {EXPECTED_UNIQUE_STEM_COUNT} unique stems,
  {EXPECTED_SELECTED_ENDPOINT_BOX_COUNT} endpoint bbox occurrences and
  {EXPECTED_UNIQUE_STEM_BOX_COUNT} unique-stem bbox occurrences.
- Reviewer: `{annotation_payload['reviewer']}` at `{annotation_payload['reviewed_at']}`.
- All 144 pairs/288 raw frames were directly inspected in the dedicated 29-page WP30 atlas
  (28 pages of five pairs and one final page of four). Sequence evidence remained context-only
  and never derived an edge decision or group truth. Capture relation and physical-sign relation
  are recorded separately.

## Hardened verifier contract

- Layout status is the exact `{EXPECTED_LAYOUT_STATUS}`; the inherited QA-passed WP15 verifier is
  reused with only its stale 176-pair status constant replaced. Layout, annotations and manifest
  must be canonical JSON bytes with no duplicate keys and pass type-strict comparison, including
  the exact 5×28 + 4 page row counts.
- Exact 30-file atlas roster; extra/missing/wrong-type/symlink/path attacks fail closed.
- Index, all 29 JPEG pages and layout regenerate in isolation and byte/deep-compare.
- Trusted review-notes SHA-256 `{EXPECTED_REVIEW_NOTES_SHA256}` pins exact outcomes and
  exceptional IDs; WP29, the WP28-R2/WP29 independent QA record and the full immutable
  predecessor lineage are hash-pinned.

## Provisional capture outcomes

{counts('capture_hypothesis_counts')}

## Provisional physical-sign outcomes

{counts('physical_sign_hypothesis_counts')}

## Confidence

{counts('confidence_counts')}

## Remaining workload and governance

- Canonical WP5 remains unchanged at {summary['canonical_wp5_pending_unchanged']} PENDING edges.
- Outside the reviewed edge overlays, {summary['pending_outside_wp7_wp12_overlays']} PENDING
  edges remain: only the two quarantined stem-0248 adjacency edges; zero are review-eligible and
  zero are cross-split.
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


def validate_strict_layout(layout: Any) -> None:
    if not isinstance(layout, dict):
        raise ValueError("WP30 layout root must be an object")
    _strict_types(layout, TOP_LEVEL_LAYOUT_TYPES, "layout")
    if (
        layout["status"] != EXPECTED_LAYOUT_STATUS
        or layout["pair_count"] != EXPECTED_SELECTION_COUNT
        or layout["page_count"] != EXPECTED_PAGE_COUNT
        or layout["pairs_per_page"] != PAIRS_PER_PAGE
        or len(layout["pages"]) != EXPECTED_PAGE_COUNT
    ):
        raise ValueError("WP30 exact 144-pair layout status/count contract mismatch")
    position = 0
    for page_number, page in enumerate(layout["pages"], start=1):
        if not isinstance(page, dict):
            raise ValueError("WP30 layout page must be an object")
        _strict_types(page, PAGE_LAYOUT_TYPES, f"layout page {page_number}")
        if (
            page["page"] != page_number
            or page["row_count"] != EXPECTED_PAGE_ROW_COUNTS[page_number - 1]
            or len(page["rows"]) != EXPECTED_PAGE_ROW_COUNTS[page_number - 1]
        ):
            raise ValueError(f"WP30 layout page {page_number} identity mismatch")
        for slot, row in enumerate(page["rows"], start=1):
            position += 1
            if not isinstance(row, dict):
                raise ValueError("WP30 layout row must be an object")
            _strict_types(row, ROW_LAYOUT_TYPES, f"layout page {page_number} slot {slot}")
            if row["slot"] != slot or row["batch_position"] != position:
                raise ValueError(f"WP30 layout page {page_number} slot {slot} position mismatch")
            for field in ("left_bounds", "right_bounds", "text_bounds"):
                if len(row[field]) != 4 or any(type(value) is not int for value in row[field]):
                    raise ValueError(f"WP30 layout bounds must be four JSON integers: {field}")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, value in pairs:
        if key in payload:
            raise ValueError(f"duplicate JSON key is forbidden: {key}")
        payload[key] = value
    return payload


def load_canonical_json(path: Path, label: str) -> Any:
    # Compare raw bytes: universal-newline text reads would hide CRLF/CR variants.
    raw = path.read_bytes()
    payload = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
    if raw != (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8"):
        raise ValueError(f"WP30 {label} is not canonically serialized")
    return payload


def validate_strict_package_json(repo_root: Path, raw_root: Path, manifest_path: Path) -> None:
    """Type-strict, duplicate-key-free and canonical-byte checks for layout/annotations/manifest.

    Call only after the inherited build/verify has configured the chain for WP30.
    """
    layout = load_canonical_json(core.safe_child(repo_root, LAYOUT_RELATIVE_PATH), "layout")
    validate_strict_layout(layout)
    selection, _inventory = derive_selection(repo_root, raw_root)
    if [row["edge_id"] for page in layout["pages"] for row in page["rows"]] != [
        row["edge_id"] for row in selection
    ]:
        raise ValueError("WP30 layout edge order differs from the canonical selection")
    annotations = load_canonical_json(core.safe_child(repo_root, ANNOTATIONS_RELATIVE_PATH), "annotations")
    expected_annotations = core.annotation_payload_from_notes(core.load_review_notes(repo_root, selection), selection)
    if strict_semantic_diff(expected_annotations, annotations):
        raise ValueError("WP30 annotations differ type-strictly from the pinned review notes")
    manifest = load_canonical_json(manifest_path, "manifest")
    if strict_semantic_diff(core.build_manifest(repo_root), manifest):
        raise ValueError("WP30 manifest differs type-strictly from the canonical rebuilt manifest")


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
        status="WP30_PREPARED_AWAITING_PM_VISUAL_REVIEW",
        exact_residual_pending_count=EXPECTED_RESIDUAL_PENDING_COUNT,
        review_eligible_residual_count=EXPECTED_ELIGIBLE_RESIDUAL_COUNT,
        quarantined_residual_count=EXPECTED_QUARANTINED_RESIDUAL_COUNT,
    )
    return result


def build(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    _configure()
    with _exact_status_verifier():
        result = impl.previous.build(repo_root, raw_root)
    root = repo_root.resolve()
    validate_strict_package_json(root, raw_root.resolve(), root / MANIFEST_RELATIVE_PATH)
    return result


def verify(manifest_path: Path, repo_root: Path, raw_root: Path) -> dict[str, Any]:
    _configure()
    with _exact_status_verifier():
        result = impl.previous.verify(manifest_path, repo_root, raw_root)
    if result.get("valid") is not True:
        return result
    # The inherited verifier leaves the chain configured for WP30; the strict layer then closes
    # the `==` type-confusion, duplicate-key and non-canonical-byte gaps.
    try:
        validate_strict_package_json(repo_root.resolve(), raw_root.resolve(), manifest_path)
    except (FileNotFoundError, json.JSONDecodeError, KeyError, OSError, TypeError, ValueError) as exc:
        return {**result, "valid": False, "errors": [f"strict verification failed: {exc}"]}
    return result


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
