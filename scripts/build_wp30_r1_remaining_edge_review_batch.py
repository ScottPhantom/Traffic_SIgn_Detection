# ruff: noqa: E501
"""Build and verify the M0-WP30-R1 one-edge QA correction reissue of final Batch I."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

IMPL_PATH = Path(__file__).with_name("build_wp30_remaining_edge_review_batch.py")
SPEC = importlib.util.spec_from_file_location("wp30_r1_initial_package", IMPL_PATH)
assert SPEC is not None and SPEC.loader is not None
wp30 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp30
SPEC.loader.exec_module(wp30)

base_impl = wp30.impl
core = wp30.core
ORIGINAL_DERIVE_SELECTION = wp30.derive_selection
ORIGINAL_RENDER_ATLAS = wp30.render_atlas
ORIGINAL_SUMMARY_FROM_DECISIONS = wp30.ORIGINAL_SUMMARY_FROM_DECISIONS
INITIAL_EVIDENCE_BOUNDARY = wp30.EVIDENCE_BOUNDARY
INITIAL_ASSETS_RELATIVE_PATH = wp30.ASSETS_RELATIVE_PATH
EXPECTED_LAYOUT_STATUS = wp30.EXPECTED_LAYOUT_STATUS

PACKAGE_STATUS = "WP30_R1_AWAITING_QA_REVIEW"
# Short enough to fit the atlas text column.
ANNOTATION_STATUS = "PM_R1_CORRECTED_AWAITING_QA"
EVIDENCE_BOUNDARY = (
    "REMAINING_EDGE_BATCH_I_R1_ONE_EDGE_QA_CORRECTION_ONLY_NOT_D02_APPROVAL_"
    "NOT_GROUP_TRUTH_NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING"
)
BATCH_ID = "M0-WP30-R1-REMAINING-EDGE-BATCH-I-FINAL"
EXPECTED_SELECTION_COUNT = wp30.EXPECTED_SELECTION_COUNT
EXPECTED_RESIDUAL_PENDING_COUNT = wp30.EXPECTED_RESIDUAL_PENDING_COUNT
EXPECTED_QUARANTINED_RESIDUAL_COUNT = wp30.EXPECTED_QUARANTINED_RESIDUAL_COUNT
EXPECTED_ELIGIBLE_RESIDUAL_COUNT = wp30.EXPECTED_ELIGIBLE_RESIDUAL_COUNT
EXPECTED_REMAINING_AFTER_BATCH = wp30.EXPECTED_REMAINING_AFTER_BATCH
EXPECTED_SELECTED_ENDPOINT_BOX_COUNT = wp30.EXPECTED_SELECTED_ENDPOINT_BOX_COUNT
EXPECTED_PAGE_COUNT = wp30.EXPECTED_PAGE_COUNT
PAIRS_PER_PAGE = wp30.PAIRS_PER_PAGE
EXPECTED_PAGE_ROW_COUNTS = wp30.EXPECTED_PAGE_ROW_COUNTS
REVIEWED_AT = "2026-10-17T15:00:00+07:00"
CORRECTED_EDGE_ID = "edge_003047"

# Immutable QA-failed initial WP30 bytes (as reviewed in docs/review/wp30_independent_qa_record.md).
INITIAL_MANIFEST_SHA256 = "c906e22fc48678308e54ace0363735a97d7f482eb13135822e39bd67b2ad54f0"
INITIAL_SELECTION_SHA256 = "5e185c6aa55cc2b279c7e503b0b7ee80880ad15edfc31541e63b19d60edb3a93"
INITIAL_ANNOTATIONS_SHA256 = "a85a6b24e4962a76a17240815d501bddcf3795ff38955293c683565e0d2cf590"
INITIAL_REVIEW_NOTES_SHA256 = "488c69d1f5c9b59838bbde57e9861be7c1fb431749f7fc6e78608ff0fe28551c"
INITIAL_BUILDER_SHA256 = "ca35511cc932c776ec9ea49dc6c9a6fa04edd8da7c9201734a8b8ad9e58acb9a"
INITIAL_TEST_SHA256 = "74d622591656ff8aef7790987a7497fd0c56ff5330315c86e7dfc0326883c9f1"
EXPECTED_REVIEW_NOTES_SHA256 = "46e7325abede0f864006372b7fdc8962f1404c77bc10e0768834168a5264d3c3"
QA_RECORD_SHA256 = "f9147fd604dbb17c85fb07ea69faad89c1fe188e2554791a52c3eebe86a7136d"

EXPECTED_CAPTURE_COUNTS = {"NOT_RELATED": 3, "SAME_CAPTURE_CANDIDATE": 141}
EXPECTED_PHYSICAL_SIGN_COUNTS = dict(wp30.EXPECTED_PHYSICAL_SIGN_COUNTS)
EXPECTED_CONFIDENCE_COUNTS = {"HIGH": 142, "MEDIUM": 2}
EXPECTED_CAPTURE_UNRESOLVED_IDS: set[str] = set()
EXPECTED_PHYSICAL_SIGN_UNRESOLVED_IDS: set[str] = set()
EXPECTED_CAPTURE_NOT_RELATED_IDS = wp30.EXPECTED_CAPTURE_NOT_RELATED_IDS - {CORRECTED_EDGE_ID}
EXPECTED_PHYSICAL_SIGN_NOT_RELATED_IDS = set(wp30.EXPECTED_PHYSICAL_SIGN_NOT_RELATED_IDS)
EXPECTED_MEDIUM_CONFIDENCE_IDS = wp30.EXPECTED_MEDIUM_CONFIDENCE_IDS | {CORRECTED_EDGE_ID}

MANIFEST_RELATIVE_PATH = "docs/review/generated/wp30_r1_remaining_edge_batch_i_manifest.json"
SELECTION_RELATIVE_PATH = "docs/review/generated/wp30_r1_remaining_edge_batch_i_selection.csv"
LINEAGE_RELATIVE_PATH = "docs/review/generated/wp30_r1_remaining_edge_batch_i_source_lineage.csv"
LAYOUT_RELATIVE_PATH = "docs/review/generated/wp30_r1_remaining_edge_batch_i_layout_audit.json"
REPORT_RELATIVE_PATH = "docs/review/wp30_r1_remaining_edge_batch_i_report.md"
ANNOTATIONS_RELATIVE_PATH = "docs/review/wp30_r1_remaining_edge_review_annotations_batch_i.json"
REVIEW_NOTES_RELATIVE_PATH = "docs/review/wp30_r1_edge_decision_correction.csv"
QA_RECORD_RELATIVE_PATH = "docs/review/wp30_independent_qa_record.md"
ASSETS_RELATIVE_PATH = "docs/review/assets/wp30_r1/remaining_edge_batch_i"

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
    # Drop the initial package's own notes/builder entries; they are re-pinned below as the
    # immutable QA-failed lineage.
    sources = [
        entry for entry in wp30.source_contract(repo_root) if entry[0] not in {"wp30_review_notes", "wp30_builder"}
    ]
    correction_lineage = [
        ("wp30_failed_manifest", generated / "wp30_remaining_edge_batch_i_manifest.json", INITIAL_MANIFEST_SHA256),
        ("wp30_failed_selection", generated / "wp30_remaining_edge_batch_i_selection.csv", INITIAL_SELECTION_SHA256),
        ("wp30_failed_annotations", review / "wp30_remaining_edge_review_annotations_batch_i.json", INITIAL_ANNOTATIONS_SHA256),
        ("wp30_failed_review_notes", review / "wp30_remaining_edge_review_notes_batch_i.csv", INITIAL_REVIEW_NOTES_SHA256),
        ("wp30_failed_builder", repo_root / "scripts/build_wp30_remaining_edge_review_batch.py", INITIAL_BUILDER_SHA256),
        ("wp30_failed_test", repo_root / "tests/test_wp30_remaining_edge_review_batch.py", INITIAL_TEST_SHA256),
        ("wp30_qa_record", repo_root / QA_RECORD_RELATIVE_PATH, QA_RECORD_SHA256),
        ("wp30_r1_correction_overlay", repo_root / REVIEW_NOTES_RELATIVE_PATH, EXPECTED_REVIEW_NOTES_SHA256),
        ("wp30_r1_builder", repo_root / "scripts/build_wp30_r1_remaining_edge_review_batch.py", None),
    ]
    return [*sources, *correction_lineage]


def derive_selection(
    repo_root: Path, raw_root: Path
) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    selected, inventory = ORIGINAL_DERIVE_SELECTION(repo_root, raw_root)
    initial = core.read_csv(repo_root / "docs/review/generated/wp30_remaining_edge_batch_i_selection.csv")
    if selected != initial:
        raise ValueError("WP30-R1 selection or source lineage differs from immutable initial WP30")
    # The initial builder stamps its own atlas path/boundary from its module globals; bind every
    # row to the R1 atlas and boundary explicitly (the WP28-R1 lesson).
    rebound: list[dict[str, str]] = []
    for row in initial:
        bound = dict(row)
        if not bound["wp12_atlas_page"].startswith(f"{INITIAL_ASSETS_RELATIVE_PATH}/page_"):
            raise ValueError("WP30-R1 initial atlas page reference has an unexpected prefix")
        bound["wp12_atlas_page"] = bound["wp12_atlas_page"].replace(
            INITIAL_ASSETS_RELATIVE_PATH, ASSETS_RELATIVE_PATH
        )
        bound["evidence_boundary"] = EVIDENCE_BOUNDARY
        rebound.append(bound)
    if any(
        core.QUARANTINED_STEM in {row["left_stem"], row["right_stem"]}
        or row["proxy_sequence_id"] == "proxy_sequence_0050"
        for row in rebound
    ):
        raise ValueError("WP30-R1 must preserve stem-0248 and proxy_sequence_0050 quarantine")
    edge = next(row for row in rebound if row["edge_id"] == CORRECTED_EDGE_ID)
    expected = {
        "batch_position": "53",
        "wp5_review_order": "3087",
        "left_stem": "3084",
        "right_stem": "3085",
        "left_class_ids": "6",
        "right_class_ids": "48",
        "wp12_atlas_slot": "3",
        "wp12_atlas_page": f"{ASSETS_RELATIVE_PATH}/page_011.jpg",
    }
    if any(edge[field] != value for field, value in expected.items()):
        raise ValueError("WP30-R1 edge_003047 source evidence differs from the QA finding")
    return rebound, inventory


def load_review_notes(
    repo_root: Path, selection: list[dict[str, str]]
) -> list[dict[str, str]]:
    initial_path = repo_root / "docs/review/wp30_remaining_edge_review_notes_batch_i.csv"
    if core.sha256_file(initial_path) != INITIAL_REVIEW_NOTES_SHA256:
        raise ValueError("initial WP30 review notes no longer match the failed-package anchor")
    notes = core.read_csv(initial_path)
    if len(notes) != EXPECTED_SELECTION_COUNT or list(notes[0]) != core.REVIEW_NOTE_FIELDS:
        raise ValueError("initial WP30 review notes schema/count changed")
    if [row["edge_id"] for row in notes] != [row["edge_id"] for row in selection]:
        raise ValueError("initial WP30 review notes no longer align with the R1 selection")
    overlay_path = repo_root / REVIEW_NOTES_RELATIVE_PATH
    if core.sha256_file(overlay_path) != EXPECTED_REVIEW_NOTES_SHA256:
        raise ValueError("trusted WP30-R1 correction-overlay anchor mismatch")
    corrections = core.read_csv(overlay_path)
    if len(corrections) != 1 or list(corrections[0]) != CORRECTION_FIELDS:
        raise ValueError("WP30-R1 requires an exact one-row correction overlay")
    correction = corrections[0]
    if correction["edge_id"] != CORRECTED_EDGE_ID:
        raise ValueError("WP30-R1 correction overlay may change only edge_003047")
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
        "HIGH",
    )
    if previous != expected_previous or expected_previous[:3] != ("NOT_RELATED", "NOT_RELATED", "NOT_RELATED"):
        raise ValueError("WP30-R1 previous edge_003047 decision does not match the QA-failed package")
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
        text = text.replace("M0-WP30 Remaining-Edge Batch I", "M0-WP30-R1 Remaining-Edge Batch I")
        text = text.replace("WP30 slot", "WP30-R1 slot")
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
    index_text = index_text.replace("M0-WP30", "M0-WP30-R1").replace("WP30 slot", "WP30-R1 slot")
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
            raise ValueError(f"WP30-R1 {label} differ from the QA correction contract")
    corrected = next(row for row in rows if row["edge_id"] == CORRECTED_EDGE_ID)
    if (
        corrected["provisional_outcome"] != "SAME_CAPTURE_CANDIDATE"
        or corrected["capture_hypothesis"] != "SAME_CAPTURE_CANDIDATE"
        or corrected["physical_sign_hypothesis"] != "NOT_RELATED"
        or corrected["confidence"] != "MEDIUM"
        or "same ride companions" not in corrected["rationale"]
        or "raw frames checked" not in corrected["rationale"]
    ):
        raise ValueError("WP30-R1 edge_003047 correction or rationale differs from QA evidence")


def render_report(summary: dict[str, Any], annotation_payload: dict[str, Any]) -> str:
    def counts(name: str) -> str:
        return "\n".join(f"- `{key}`: {value}" for key, value in summary[name].items())

    return f"""# M0-WP30-R1 — D02-D remaining-edge manual reconciliation, final Batch I correction

Status: `{PACKAGE_STATUS}`
Boundary: `{EVIDENCE_BOUNDARY}`

This R1 reissue preserves the immutable QA-failed M0-WP30 package and changes only the reviewed
decision/rationale for `edge_003047`. It does not approve D-02, create final/transitive group
truth or a split, or authorize training.

## QA failure and R1 correction lineage

- Initial independent QA verdict: **FAIL** with one `P1` and one non-blocking `P3` (inherited
  WP12 error-message text) and zero `P0`/`P2`.
- Initial manifest SHA-256: `{INITIAL_MANIFEST_SHA256}`.
- Initial annotations SHA-256: `{INITIAL_ANNOTATIONS_SHA256}`.
- Initial review-notes SHA-256: `{INITIAL_REVIEW_NOTES_SHA256}`.
- QA record: `{QA_RECORD_RELATIVE_PATH}` (SHA-256 `{QA_RECORD_SHA256}`).
- Trusted one-row correction-overlay SHA-256: `{EXPECTED_REVIEW_NOTES_SHA256}`.
- Corrected edge: `edge_003047`, Batch position 53, WP5 order 3087, stems 3084/3085, page 011
  slot 3. The scene changes, but the same ride companions seen in stems 3000–3076 continue in
  3085, so the frames are a gapped single ride as in WP29 `edge_002967`.
- Corrected decision: `SAME_CAPTURE_CANDIDATE` / `NOT_RELATED`, confidence `MEDIUM`. The other
  143 review decisions are unchanged.
- Every selection row and evidence reference is bound to the R1 atlas and R1 boundary.

## Selection and evidence boundary

- Selection remains the exact same 144 canonical rows as initial WP30,
  `{summary['first_edge']}` through `{summary['last_edge']}`, with 288 endpoints and
  {EXPECTED_SELECTED_ENDPOINT_BOX_COUNT} bbox occurrences.
- `edge_000242` and `edge_000243` remain quarantined/PENDING and outside lineage;
  `proxy_sequence_0050` is not selected.
- All 144 pairs/288 raw frames remain represented in the deterministic 29-page R1 atlas.
- Sequence evidence remains context only and never derives an edge decision or group truth.
  Capture relation and physical-sign relation are recorded separately.

## Corrected capture outcomes

{counts('capture_hypothesis_counts')}

## Corrected physical-sign outcomes

{counts('physical_sign_hypothesis_counts')}

## Confidence

{counts('confidence_counts')}

## Remaining workload and governance

- Canonical WP5 remains unchanged at {summary['canonical_wp5_pending_unchanged']} PENDING edges.
- Outside the reviewed edge overlays, {summary['pending_outside_wp7_wp12_overlays']} PENDING
  edges remain: only the two quarantined stem-0248 adjacency edges; zero are review-eligible.
- All {summary['all_wp5_sequences_pending']} WP5 sequences remain PENDING.
- D-02 remains PENDING; Gate 0 remains BLOCKED; `split_authorized=false` and
  `training_authorized=false`.

## Artifacts

- Corrected decisions: `{ANNOTATIONS_RELATIVE_PATH}`.
- Selection reissue bound to the R1 atlas: `{SELECTION_RELATIVE_PATH}`.
- Source lineage: `{LINEAGE_RELATIVE_PATH}`.
- Layout audit: `{LAYOUT_RELATIVE_PATH}`.
- Atlas: `{ASSETS_RELATIVE_PATH}/index.html` and {EXPECTED_PAGE_COUNT} JPEG pages.
- Manifest: `{MANIFEST_RELATIVE_PATH}`.
"""


def validate_strict_package_json(repo_root: Path, raw_root: Path, manifest_path: Path) -> None:
    """Type-strict, duplicate-key-free and canonical-byte checks for layout/annotations/manifest.

    Call only after the inherited build/verify has configured the chain for WP30-R1.
    """
    layout = wp30.load_canonical_json(core.safe_child(repo_root, LAYOUT_RELATIVE_PATH), "layout")
    wp30.validate_strict_layout(layout)
    selection, _inventory = derive_selection(repo_root, raw_root)
    if [row["edge_id"] for page in layout["pages"] for row in page["rows"]] != [
        row["edge_id"] for row in selection
    ]:
        raise ValueError("WP30-R1 layout edge order differs from the canonical selection")
    annotations = wp30.load_canonical_json(core.safe_child(repo_root, ANNOTATIONS_RELATIVE_PATH), "annotations")
    expected_annotations = core.annotation_payload_from_notes(load_review_notes(repo_root, selection), selection)
    if wp30.strict_semantic_diff(expected_annotations, annotations):
        raise ValueError("WP30-R1 annotations differ type-strictly from the corrected review notes")
    for decision in annotations["decisions"]:
        refs = decision["evidence_refs"]
        if not any(ref.startswith(f"{ASSETS_RELATIVE_PATH}/page_") for ref in refs) or any(
            ref.startswith(f"{INITIAL_ASSETS_RELATIVE_PATH}/") for ref in refs
        ):
            raise ValueError(f"WP30-R1 evidence for {decision['edge_id']} is not bound to the R1 atlas")
    manifest = wp30.load_canonical_json(manifest_path, "manifest")
    if wp30.strict_semantic_diff(core.build_manifest(repo_root), manifest):
        raise ValueError("WP30-R1 manifest differs type-strictly from the canonical rebuilt manifest")


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
        "load_sequence_context": wp30.load_sequence_context,
    }
    for name, value in values.items():
        setattr(base_impl, name, value)
    base_impl.configure_previous()
    core.load_review_notes = load_review_notes
    if not all(field in core.SELECTION_FIELDS for field in wp30.SEQUENCE_CONTEXT_FIELDS):
        core.SELECTION_FIELDS = [*core.SELECTION_FIELDS, *wp30.SEQUENCE_CONTEXT_FIELDS]


def prepare(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    _configure()
    result = base_impl.previous.prepare(repo_root, raw_root)
    result["status"] = "WP30_R1_PREPARED_AWAITING_BUILD_AND_QA_REVIEW"
    result["exact_residual_pending_count"] = EXPECTED_RESIDUAL_PENDING_COUNT
    result["review_eligible_residual_count"] = EXPECTED_ELIGIBLE_RESIDUAL_COUNT
    result["quarantined_residual_count"] = EXPECTED_QUARANTINED_RESIDUAL_COUNT
    return result


def build(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    _configure()
    with wp30._exact_status_verifier():
        result = base_impl.previous.build(repo_root, raw_root)
    root = repo_root.resolve()
    validate_strict_package_json(root, raw_root.resolve(), root / MANIFEST_RELATIVE_PATH)
    return result


def verify(manifest_path: Path, repo_root: Path, raw_root: Path) -> dict[str, Any]:
    _configure()
    with wp30._exact_status_verifier():
        result = base_impl.previous.verify(manifest_path, repo_root, raw_root)
    if result.get("valid") is not True:
        return result
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
