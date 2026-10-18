# ruff: noqa: E501
"""Build and verify the M0-WP28-R2 evidence-binding reissue of the Batch G correction."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

IMPL_PATH = Path(__file__).with_name("build_wp28_remaining_edge_review_batch.py")
SPEC = importlib.util.spec_from_file_location("wp28_r2_initial_package", IMPL_PATH)
assert SPEC is not None and SPEC.loader is not None
wp28 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp28
SPEC.loader.exec_module(wp28)

base_impl = wp28.impl
core = wp28.core
ORIGINAL_DERIVE_SELECTION = wp28.derive_selection
ORIGINAL_RENDER_ATLAS = wp28.render_atlas
ORIGINAL_SUMMARY_FROM_DECISIONS = wp28.ORIGINAL_SUMMARY_FROM_DECISIONS
INITIAL_EVIDENCE_BOUNDARY = wp28.EVIDENCE_BOUNDARY
INITIAL_ASSETS_RELATIVE_PATH = wp28.ASSETS_RELATIVE_PATH
EXPECTED_LAYOUT_STATUS = wp28.EXPECTED_LAYOUT_STATUS

PACKAGE_STATUS = "WP28_R2_AWAITING_QA_REVIEW"
# Short enough to fit the atlas text column (the WP25-R1 string clips at the page edge).
ANNOTATION_STATUS = "PM_R2_REISSUED_AWAITING_QA"
EVIDENCE_BOUNDARY = (
    "REMAINING_EDGE_BATCH_G_R2_EVIDENCE_BINDING_REISSUE_ONLY_NOT_D02_APPROVAL_"
    "NOT_GROUP_TRUTH_NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING"
)
BATCH_ID = "M0-WP28-R2-REMAINING-EDGE-BATCH-G"
EXPECTED_SELECTION_COUNT = wp28.EXPECTED_SELECTION_COUNT
EXPECTED_RESIDUAL_PENDING_COUNT = wp28.EXPECTED_RESIDUAL_PENDING_COUNT
EXPECTED_QUARANTINED_RESIDUAL_COUNT = wp28.EXPECTED_QUARANTINED_RESIDUAL_COUNT
EXPECTED_ELIGIBLE_RESIDUAL_COUNT = wp28.EXPECTED_ELIGIBLE_RESIDUAL_COUNT
EXPECTED_REMAINING_AFTER_BATCH = wp28.EXPECTED_REMAINING_AFTER_BATCH
EXPECTED_SELECTED_ENDPOINT_BOX_COUNT = wp28.EXPECTED_SELECTED_ENDPOINT_BOX_COUNT
EXPECTED_PAGE_COUNT = wp28.EXPECTED_PAGE_COUNT
PAIRS_PER_PAGE = wp28.PAIRS_PER_PAGE
EXPECTED_PAGE_ROW_COUNTS = wp28.EXPECTED_PAGE_ROW_COUNTS
REVIEWED_AT = "2026-10-16T23:10:00+07:00"
CORRECTED_EDGE_ID = "edge_002306"

INITIAL_MANIFEST_SHA256 = "d5933d813a8788c2cb367b99b92d54eee7aa8e8ebbe171e424ce2834da6fdc0f"
INITIAL_SELECTION_SHA256 = "556de19cf71ea1d15727df2f5f2fb64bc36e732ced3ba8a791b11c129b167a6f"
INITIAL_ANNOTATIONS_SHA256 = "71be309b9a82d6f839dc875d71a74ab0072e2c1849b4d2eb60de1a677b578267"
INITIAL_REVIEW_NOTES_SHA256 = "56f02f8a70063ced5dfa9b259d41bfd8c10fc3a99b0071d4d0b42aa27c4122f9"
INITIAL_BUILDER_SHA256 = "0b9e19dba0722d77725332be0ae6db3cffe93c92fe374c426f12eb6ab0fe819c"
INITIAL_TEST_SHA256 = "cc6cdcbf92da82e8f250368a17cbd0dbae1f8eee3fbdc9b1bebdea501445c5da"
EXPECTED_REVIEW_NOTES_SHA256 = "0fdf1ed29f62919650fe121fa7d87d5905f9732fa1cd06458dde01a114b5a0a4"
R1_QA_RECORD_SHA256 = "7ead37a0ec5d9ea9429ac591587479349edc126ea9d86b4bae9854de7f00720d"
QA_CORRECTION_RECORD_SHA256 = "82fb850730071b50678f4755a9c9f2bba04eb4e290fd9ce7f1b2b649eae4cd8a"
# WP28-R1 failed QA only on evidence binding; its decision overlay is reused unchanged.
R1_MANIFEST_SHA256 = "2dc57da89791e13602a0a6be04b8464cbc64727c84199571e921d7e414aab83b"
R1_BUILDER_SHA256 = "215272e412107044281f18d6100a267bd72faf0eca2fca74bd8d5dafc4d9ed5f"
R1_TEST_SHA256 = "094dff55efe3ba86c1b3014339baf3140dd0b49ae7f7ee7242e4c8e42c1052f5"
R1_ANNOTATIONS_SHA256 = "f5a75679c84393c15bbafcef7db53946f9cb463348b08df96796bd614ef601c6"

EXPECTED_CAPTURE_COUNTS = {"SAME_CAPTURE_CANDIDATE": 250}
EXPECTED_PHYSICAL_SIGN_COUNTS = {
    "NOT_RELATED": 15,
    "SAME_PHYSICAL_SIGN_CANDIDATE": 235,
}
EXPECTED_CONFIDENCE_COUNTS = {"HIGH": 249, "MEDIUM": 1}
EXPECTED_CAPTURE_UNRESOLVED_IDS: set[str] = set()
EXPECTED_PHYSICAL_SIGN_UNRESOLVED_IDS: set[str] = set()
EXPECTED_CAPTURE_NOT_RELATED_IDS: set[str] = set()
EXPECTED_PHYSICAL_SIGN_NOT_RELATED_IDS = wp28.EXPECTED_PHYSICAL_SIGN_NOT_RELATED_IDS | {CORRECTED_EDGE_ID}
EXPECTED_MEDIUM_CONFIDENCE_IDS = wp28.EXPECTED_MEDIUM_CONFIDENCE_IDS - {CORRECTED_EDGE_ID}

MANIFEST_RELATIVE_PATH = "docs/review/generated/wp28_r2_remaining_edge_batch_g_manifest.json"
SELECTION_RELATIVE_PATH = "docs/review/generated/wp28_r2_remaining_edge_batch_g_selection.csv"
LINEAGE_RELATIVE_PATH = "docs/review/generated/wp28_r2_remaining_edge_batch_g_source_lineage.csv"
LAYOUT_RELATIVE_PATH = "docs/review/generated/wp28_r2_remaining_edge_batch_g_layout_audit.json"
REPORT_RELATIVE_PATH = "docs/review/wp28_r2_remaining_edge_batch_g_report.md"
ANNOTATIONS_RELATIVE_PATH = "docs/review/wp28_r2_remaining_edge_review_annotations_batch_g.json"
REVIEW_NOTES_RELATIVE_PATH = "docs/review/wp28_r1_edge_decision_correction.csv"
R1_QA_RECORD_RELATIVE_PATH = "docs/review/wp28_r1_qa_correction_record.md"
QA_RECORD_RELATIVE_PATH = "docs/review/wp28_r2_qa_correction_record.md"
ASSETS_RELATIVE_PATH = "docs/review/assets/wp28_r2/remaining_edge_batch_g"

CORRECTION_FIELDS = [
    "edge_id",
    "previous_provisional_outcome",
    "previous_capture_hypothesis",
    "previous_physical_sign_hypothesis",
    "corrected_provisional_outcome",
    "corrected_capture_hypothesis",
    "corrected_physical_sign_hypothesis",
    "confidence",
    "rationale",
    "qa_finding",
]


def source_contract(repo_root: Path) -> list[tuple[str, Path, str | None]]:
    generated = repo_root / "docs/review/generated"
    review = repo_root / "docs/review"
    sources = wp28.source_contract(repo_root)[:-2]
    correction_lineage = [
        ("wp28_failed_manifest", generated / "wp28_remaining_edge_batch_g_manifest.json", INITIAL_MANIFEST_SHA256),
        ("wp28_failed_selection", generated / "wp28_remaining_edge_batch_g_selection.csv", INITIAL_SELECTION_SHA256),
        ("wp28_failed_annotations", review / "wp28_remaining_edge_review_annotations_batch_g.json", INITIAL_ANNOTATIONS_SHA256),
        ("wp28_failed_review_notes", review / "wp28_remaining_edge_review_notes_batch_g.csv", INITIAL_REVIEW_NOTES_SHA256),
        ("wp28_failed_builder", repo_root / "scripts/build_wp28_remaining_edge_review_batch.py", INITIAL_BUILDER_SHA256),
        ("wp28_failed_test", repo_root / "tests/test_wp28_remaining_edge_review_batch.py", INITIAL_TEST_SHA256),
        ("wp28_r1_qa_record", repo_root / R1_QA_RECORD_RELATIVE_PATH, R1_QA_RECORD_SHA256),
        ("wp28_r1_correction_overlay", repo_root / REVIEW_NOTES_RELATIVE_PATH, EXPECTED_REVIEW_NOTES_SHA256),
        ("wp28_r1_failed_manifest", generated / "wp28_r1_remaining_edge_batch_g_manifest.json", R1_MANIFEST_SHA256),
        ("wp28_r1_failed_annotations", review / "wp28_r1_remaining_edge_review_annotations_batch_g.json", R1_ANNOTATIONS_SHA256),
        ("wp28_r1_failed_builder", repo_root / "scripts/build_wp28_r1_remaining_edge_review_batch.py", R1_BUILDER_SHA256),
        ("wp28_r1_failed_test", repo_root / "tests/test_wp28_r1_remaining_edge_review_batch.py", R1_TEST_SHA256),
        ("wp28_r2_qa_record", repo_root / QA_RECORD_RELATIVE_PATH, QA_CORRECTION_RECORD_SHA256),
        ("wp28_r2_builder", repo_root / "scripts/build_wp28_r2_remaining_edge_review_batch.py", None),
    ]
    return [*sources, *correction_lineage]


def derive_selection(
    repo_root: Path, raw_root: Path
) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    selected, inventory = ORIGINAL_DERIVE_SELECTION(repo_root, raw_root)
    initial = core.read_csv(repo_root / "docs/review/generated/wp28_remaining_edge_batch_g_selection.csv")
    normalized: list[dict[str, str]] = []
    for row in selected:
        restored = dict(row)
        restored["wp12_atlas_page"] = restored["wp12_atlas_page"].replace(
            ASSETS_RELATIVE_PATH, INITIAL_ASSETS_RELATIVE_PATH
        )
        restored["evidence_boundary"] = INITIAL_EVIDENCE_BOUNDARY
        normalized.append(restored)
    if normalized != initial:
        raise ValueError("WP28-R2 selection or source lineage differs from immutable initial WP28")
    # The initial builder stamps its own atlas path/boundary from its module globals; bind every
    # row to the R2 atlas and boundary explicitly (the WP28-R1 replacement was a no-op).
    rebound: list[dict[str, str]] = []
    for row in normalized:
        bound = dict(row)
        if not bound["wp12_atlas_page"].startswith(f"{INITIAL_ASSETS_RELATIVE_PATH}/page_"):
            raise ValueError("WP28-R2 initial atlas page reference has an unexpected prefix")
        bound["wp12_atlas_page"] = bound["wp12_atlas_page"].replace(
            INITIAL_ASSETS_RELATIVE_PATH, ASSETS_RELATIVE_PATH
        )
        bound["evidence_boundary"] = EVIDENCE_BOUNDARY
        rebound.append(bound)
    selected = rebound
    if any(
        core.QUARANTINED_STEM in {row["left_stem"], row["right_stem"]}
        or row["proxy_sequence_id"] == "proxy_sequence_0050"
        for row in selected
    ):
        raise ValueError("WP28-R2 must preserve stem-0248 and proxy_sequence_0050 quarantine")
    edge = next(row for row in selected if row["edge_id"] == CORRECTED_EDGE_ID)
    expected = {
        "batch_position": "65",
        "wp5_review_order": "2599",
        "left_stem": "2331",
        "right_stem": "2332",
        "left_class_ids": "10 18 23",
        "right_class_ids": "2 10 12",
        "proxy_status": "adjacency_only",
        "wp12_atlas_slot": "5",
    }
    if any(edge[field] != value for field, value in expected.items()):
        raise ValueError("WP28-R2 edge_002306 source evidence differs from QA finding")
    if not edge["wp12_atlas_page"].endswith("/page_013.jpg"):
        raise ValueError("WP28-R2 edge_002306 must remain on atlas page 013")
    expected_labels = {
        "left_label_path": "10 0.482812 0.273148 0.028125 0.05",
        "right_label_path": "10 0.526563 0.388889 0.019792 0.033333",
    }
    for field, cls10_line in expected_labels.items():
        lines = (raw_root / edge[field]).read_text(encoding="utf-8").splitlines()
        if cls10_line not in lines:
            raise ValueError(f"WP28-R2 {field} differs from independently reverified QA evidence")
    return selected, inventory


def load_review_notes(
    repo_root: Path, selection: list[dict[str, str]]
) -> list[dict[str, str]]:
    initial_path = repo_root / "docs/review/wp28_remaining_edge_review_notes_batch_g.csv"
    if core.sha256_file(initial_path) != INITIAL_REVIEW_NOTES_SHA256:
        raise ValueError("initial WP28 review notes no longer match the failed-package anchor")
    notes = core.read_csv(initial_path)
    if len(notes) != EXPECTED_SELECTION_COUNT or list(notes[0]) != core.REVIEW_NOTE_FIELDS:
        raise ValueError("initial WP28 review notes schema/count changed")
    if [row["edge_id"] for row in notes] != [row["edge_id"] for row in selection]:
        raise ValueError("initial WP28 review notes no longer align with the R1 selection")
    overlay_path = repo_root / REVIEW_NOTES_RELATIVE_PATH
    if core.sha256_file(overlay_path) != EXPECTED_REVIEW_NOTES_SHA256:
        raise ValueError("trusted WP28-R1 correction-overlay anchor mismatch")
    corrections = core.read_csv(overlay_path)
    if len(corrections) != 1 or list(corrections[0]) != CORRECTION_FIELDS:
        raise ValueError("WP28-R1 requires an exact one-row correction overlay")
    correction = corrections[0]
    if correction["edge_id"] != CORRECTED_EDGE_ID:
        raise ValueError("WP28-R1 correction overlay may change only edge_002306")
    target = next(row for row in notes if row["edge_id"] == CORRECTED_EDGE_ID)
    previous = (
        target["provisional_outcome"],
        target["capture_hypothesis"],
        target["physical_sign_hypothesis"],
        target["confidence"],
    )
    expected_previous = (
        correction["previous_provisional_outcome"],
        correction["previous_capture_hypothesis"],
        correction["previous_physical_sign_hypothesis"],
        "MEDIUM",
    )
    if previous != expected_previous or expected_previous[:3] != (
        "SAME_CAPTURE_CANDIDATE",
        "SAME_CAPTURE_CANDIDATE",
        "SAME_PHYSICAL_SIGN_CANDIDATE",
    ):
        raise ValueError("WP28-R1 previous edge_002306 decision does not match the QA-failed package")
    target.update(
        provisional_outcome=correction["corrected_provisional_outcome"],
        capture_hypothesis=correction["corrected_capture_hypothesis"],
        physical_sign_hypothesis=correction["corrected_physical_sign_hypothesis"],
        confidence=correction["confidence"],
        rationale=correction["rationale"],
    )
    validate_review_decision_contract(notes)
    return notes


class _R1DrawProxy:
    def __init__(self, wrapped: Any) -> None:
        self._wrapped = wrapped

    def text(self, xy: Any, text: str, *args: Any, **kwargs: Any) -> Any:
        text = text.replace("M0-WP28 Remaining-Edge Batch G", "M0-WP28-R2 Remaining-Edge Batch G")
        text = text.replace("WP28 slot", "WP28-R2 slot")
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
    image_draw.Draw = lambda image: _R1DrawProxy(original_draw(image))
    try:
        paths, layout = ORIGINAL_RENDER_ATLAS(selection, inventory, raw_root, assets_dir, decisions)
    finally:
        image_draw.Draw = original_draw
    index_path = assets_dir / "index.html"
    index_text = index_path.read_text(encoding="utf-8")
    index_text = index_text.replace("M0-WP28", "M0-WP28-R2").replace("WP28 slot", "WP28-R2 slot")
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
        (dict(Counter(row["capture_hypothesis"] for row in rows)), EXPECTED_CAPTURE_COUNTS, "capture decision counts"),
        (dict(Counter(row["physical_sign_hypothesis"] for row in rows)), EXPECTED_PHYSICAL_SIGN_COUNTS, "physical-sign decision counts"),
        (dict(Counter(row["confidence"] for row in rows)), EXPECTED_CONFIDENCE_COUNTS, "confidence counts"),
        ({row["edge_id"] for row in rows if row["capture_hypothesis"] == "UNRESOLVED"}, EXPECTED_CAPTURE_UNRESOLVED_IDS, "capture UNRESOLVED IDs"),
        ({row["edge_id"] for row in rows if row["physical_sign_hypothesis"] == "UNRESOLVED"}, EXPECTED_PHYSICAL_SIGN_UNRESOLVED_IDS, "physical UNRESOLVED IDs"),
        ({row["edge_id"] for row in rows if row["capture_hypothesis"] == "NOT_RELATED"}, EXPECTED_CAPTURE_NOT_RELATED_IDS, "capture NOT_RELATED IDs"),
        ({row["edge_id"] for row in rows if row["physical_sign_hypothesis"] == "NOT_RELATED"}, EXPECTED_PHYSICAL_SIGN_NOT_RELATED_IDS, "physical NOT_RELATED IDs"),
        ({row["edge_id"] for row in rows if row["confidence"] == "MEDIUM"}, EXPECTED_MEDIUM_CONFIDENCE_IDS, "MEDIUM confidence IDs"),
    )
    for actual, expected, label in checks:
        if actual != expected:
            raise ValueError(f"WP28-R2 {label} differ from the QA correction contract")
    corrected = next(row for row in rows if row["edge_id"] == CORRECTED_EDGE_ID)
    if (
        corrected["provisional_outcome"] != "SAME_CAPTURE_CANDIDATE"
        or corrected["capture_hypothesis"] != "SAME_CAPTURE_CANDIDATE"
        or corrected["physical_sign_hypothesis"] != "NOT_RELATED"
        or corrected["confidence"] != "HIGH"
        or "has been passed" not in corrected["rationale"]
        or "0.482812/0.273148/0.028125/0.05" not in corrected["rationale"]
        or "0.526563/0.388889/0.019792/0.033333" not in corrected["rationale"]
        or "raw crop checked" not in corrected["rationale"]
    ):
        raise ValueError("WP28-R2 edge_002306 correction or rationale differs from QA evidence")


def render_report(summary: dict[str, Any], annotation_payload: dict[str, Any]) -> str:
    def counts(name: str) -> str:
        return "\n".join(f"- `{key}`: {value}" for key, value in summary[name].items())

    return f"""# M0-WP28-R2 — D02-D remaining-edge manual reconciliation, Batch G evidence-binding reissue

Status: `{PACKAGE_STATUS}`  
Boundary: `{EVIDENCE_BOUNDARY}`

This R2 reissue preserves the immutable QA-failed M0-WP28 and M0-WP28-R1 packages. It keeps the
R1 decisions unchanged (only `edge_002306` differs from initial WP28) and binds every selection
row and evidence reference to the WP28-R2 atlas. It does not approve D-02, create
final/transitive group truth or a split, authorize training, or start WP29.

## QA failure and R2 correction lineage

- Initial WP28 QA: **FAIL** (one `P1` on `edge_002306`, one `P2`, two `P3`).
- WP28-R1 QA: **FAIL** with zero `P0`/`P1`, one `P2` and three `P3`; QA agreed with every
  decision. P2: all R1 evidence references still cited the superseded initial atlas because the
  initial builder stamps atlas paths from its own module globals.
- Initial manifest SHA-256: `{INITIAL_MANIFEST_SHA256}`.
- WP28-R1 manifest SHA-256: `{R1_MANIFEST_SHA256}`.
- QA records: `{R1_QA_RECORD_RELATIVE_PATH}` and `{QA_RECORD_RELATIVE_PATH}`.
- Trusted one-row correction overlay reused from WP28-R1, SHA-256 `{EXPECTED_REVIEW_NOTES_SHA256}`.
- Corrected edge (unchanged from R1): `edge_002306`, Batch position 65, WP5 order 2599, stems
  2331/2332, page 013 slot 5: `SAME_CAPTURE_CANDIDATE` / `NOT_RELATED`, confidence `HIGH`.
- R2 hardening: every row differs from the initial selection in exactly `wp12_atlas_page` and
  `evidence_boundary`; every atlas evidence reference cites `{ASSETS_RELATIVE_PATH}`; layout,
  annotations and manifest must match canonical JSON bytes exactly (no duplicate keys, no CRLF/CR).

## Selection and evidence boundary

- Selection remains the exact same 250 canonical rows as initial WP28,
  `{summary['first_edge']}` through `{summary['last_edge']}`, with 500 endpoints and
  {EXPECTED_SELECTED_ENDPOINT_BOX_COUNT} bbox occurrences.
- `edge_000242` and `edge_000243` remain quarantined/PENDING and outside lineage;
  `proxy_sequence_0050` is not selected.
- All 250 pairs/500 raw frames remain represented in the deterministic 50-page R2 atlas.
- Sequence evidence remains context only and never derives an edge decision or group truth.
  Capture relation and physical-sign relation are recorded separately.

## Capture outcomes

{counts('capture_hypothesis_counts')}

## Physical-sign outcomes

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
- Selection reissue: `{SELECTION_RELATIVE_PATH}`.
- Source lineage: `{LINEAGE_RELATIVE_PATH}`.
- Layout audit: `{LAYOUT_RELATIVE_PATH}`.
- Atlas: `{ASSETS_RELATIVE_PATH}/index.html` and {EXPECTED_PAGE_COUNT} JPEG pages.
- Manifest: `{MANIFEST_RELATIVE_PATH}`.
"""


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
        raise ValueError(f"WP28-R2 {label} is not canonically serialized")
    return payload


def validate_strict_package_json(repo_root: Path, raw_root: Path, manifest_path: Path) -> None:
    """Type-strict, duplicate-key-free and canonical-byte checks for layout/annotations/manifest.

    Call only after the inherited build/verify has configured the chain for WP28-R2.
    """
    layout = load_canonical_json(core.safe_child(repo_root, LAYOUT_RELATIVE_PATH), "layout")
    wp28.validate_strict_layout(layout)
    for page_number, page in enumerate(layout["pages"], start=1):
        if page["row_count"] != PAIRS_PER_PAGE or len(page["rows"]) != PAIRS_PER_PAGE:
            raise ValueError(f"WP28-R2 layout page {page_number} row_count mismatch")
    selection, _inventory = derive_selection(repo_root, raw_root)
    if [row["edge_id"] for page in layout["pages"] for row in page["rows"]] != [
        row["edge_id"] for row in selection
    ]:
        raise ValueError("WP28-R2 layout edge order differs from the canonical selection")
    annotations = load_canonical_json(core.safe_child(repo_root, ANNOTATIONS_RELATIVE_PATH), "annotations")
    expected_annotations = core.annotation_payload_from_notes(load_review_notes(repo_root, selection), selection)
    atlas_refs = [ref for row in annotations["decisions"] for ref in row["evidence_refs"] if "/assets/" in ref]
    if len(atlas_refs) != EXPECTED_SELECTION_COUNT or any(
        not ref.startswith(f"{ASSETS_RELATIVE_PATH}/page_") for ref in atlas_refs
    ):
        raise ValueError("WP28-R2 evidence references must cite the WP28-R2 atlas")
    if wp28.strict_semantic_diff(expected_annotations, annotations):
        raise ValueError("WP28-R2 annotations differ type-strictly from the corrected review notes")
    manifest = load_canonical_json(manifest_path, "manifest")
    if wp28.strict_semantic_diff(core.build_manifest(repo_root), manifest):
        raise ValueError("WP28-R2 manifest differs type-strictly from the canonical rebuilt manifest")


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
        "load_sequence_context": wp28.load_sequence_context,
    }
    for name, value in values.items():
        setattr(base_impl, name, value)
    base_impl.configure_previous()
    core.load_review_notes = load_review_notes
    if not all(field in core.SELECTION_FIELDS for field in wp28.SEQUENCE_CONTEXT_FIELDS):
        core.SELECTION_FIELDS = [*core.SELECTION_FIELDS, *wp28.SEQUENCE_CONTEXT_FIELDS]


def prepare(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    _configure()
    result = base_impl.previous.prepare(repo_root, raw_root)
    result["status"] = "WP28_R2_PREPARED_AWAITING_BUILD_AND_QA_REVIEW"
    result["exact_residual_pending_count"] = EXPECTED_RESIDUAL_PENDING_COUNT
    result["review_eligible_residual_count"] = EXPECTED_ELIGIBLE_RESIDUAL_COUNT
    result["quarantined_residual_count"] = EXPECTED_QUARANTINED_RESIDUAL_COUNT
    return result


def build(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    _configure()
    with wp28._exact_status_verifier():
        result = base_impl.previous.build(repo_root, raw_root)
    root = repo_root.resolve()
    validate_strict_package_json(root, raw_root.resolve(), root / MANIFEST_RELATIVE_PATH)
    return result


def verify(manifest_path: Path, repo_root: Path, raw_root: Path) -> dict[str, Any]:
    _configure()
    with wp28._exact_status_verifier():
        result = base_impl.previous.verify(manifest_path, repo_root, raw_root)
    if result.get("valid") is not True:
        return result
    # The inherited verifier leaves the chain configured for WP28-R2; the strict layer then closes
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
