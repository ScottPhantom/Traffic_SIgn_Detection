# ruff: noqa: E501
"""Build and verify the M0-WP23-R1 one-edge QA correction reissue."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from collections import Counter
from pathlib import Path
from typing import Any

IMPL_PATH = Path(__file__).with_name("build_wp23_remaining_edge_review_batch.py")
SPEC = importlib.util.spec_from_file_location("wp23_r1_initial_package", IMPL_PATH)
assert SPEC is not None and SPEC.loader is not None
impl = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = impl
SPEC.loader.exec_module(impl)

core = impl.previous.previous.previous.base
ORIGINAL_DERIVE_SELECTION = impl.derive_selection
ORIGINAL_RENDER_ATLAS = impl.render_atlas
INITIAL_EVIDENCE_BOUNDARY = impl.EVIDENCE_BOUNDARY
INITIAL_ASSETS_RELATIVE_PATH = impl.ASSETS_RELATIVE_PATH

PACKAGE_STATUS = "WP23_R1_AWAITING_QA_REVIEW"
ANNOTATION_STATUS = "PM_REVIEWED_R1_CORRECTION_AWAITING_INDEPENDENT_QA"
EVIDENCE_BOUNDARY = (
    "REMAINING_EDGE_BATCH_B_R1_ONE_EDGE_QA_CORRECTION_ONLY_NOT_D02_APPROVAL_"
    "NOT_GROUP_TRUTH_NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING"
)
BATCH_ID = "M0-WP23-R1-REMAINING-EDGE-BATCH-B"
EXPECTED_SELECTION_COUNT = 250
EXPECTED_RESIDUAL_PENDING_COUNT = 1896
EXPECTED_QUARANTINED_RESIDUAL_COUNT = 2
EXPECTED_ELIGIBLE_RESIDUAL_COUNT = 1894
EXPECTED_REMAINING_AFTER_BATCH = 1646
EXPECTED_SELECTED_ENDPOINT_BOX_COUNT = 1556
EXPECTED_PAGE_COUNT = 50
EXPECTED_PAGE_ROW_COUNTS = (5,) * EXPECTED_PAGE_COUNT
REVIEWED_AT = "2026-10-12T05:43:08+07:00"

INITIAL_MANIFEST_SHA256 = "dec19a75bb2def4d29afabe36963f7cdfd474b5c2bdd556e8c40ec198a8f09dd"
INITIAL_SELECTION_SHA256 = "e6913b2eeba22c990cef393490f8d8cb2caaa6745b2045e6edf64c3a6f9973a6"
INITIAL_ANNOTATIONS_SHA256 = "2720ac892a9f0ebe46dc027a722702031a8519aaa856965d560da99d85e2c7be"
INITIAL_REVIEW_NOTES_SHA256 = "c9159a36096f11c409e1c88ad49d15947ed052db7d5e4fddb310647f47a113c8"
INITIAL_BUILDER_SHA256 = "f71b2d239fa35288f8c82a0648329f4e9609f1ad79409576e077554f43c8050e"
EXPECTED_REVIEW_NOTES_SHA256 = "f12ce41c8290bab9808522b24fa96e460f53ff81ba0b466240c21635b77994b8"
QA_CORRECTION_RECORD_SHA256 = "de28a2b8cd272a359c7886037756421e416618485c36de35e77b77d1a6e88326"

EXPECTED_CAPTURE_COUNTS = {
    "NOT_RELATED": 16,
    "SAME_CAPTURE_CANDIDATE": 234,
}
EXPECTED_PHYSICAL_SIGN_COUNTS = {
    "NOT_RELATED": 16,
    "SAME_PHYSICAL_SIGN_CANDIDATE": 234,
}
EXPECTED_CONFIDENCE_COUNTS = {"HIGH": EXPECTED_SELECTION_COUNT}
EXPECTED_CAPTURE_UNRESOLVED_IDS: set[str] = set()
EXPECTED_PHYSICAL_SIGN_UNRESOLVED_IDS: set[str] = set()
EXPECTED_CAPTURE_NOT_RELATED_IDS = impl.EXPECTED_CAPTURE_NOT_RELATED_IDS - {"edge_000664"}
EXPECTED_PHYSICAL_SIGN_NOT_RELATED_IDS = set(EXPECTED_CAPTURE_NOT_RELATED_IDS)

MANIFEST_RELATIVE_PATH = "docs/review/generated/wp23_r1_remaining_edge_batch_b_manifest.json"
SELECTION_RELATIVE_PATH = "docs/review/generated/wp23_r1_remaining_edge_batch_b_selection.csv"
LINEAGE_RELATIVE_PATH = "docs/review/generated/wp23_r1_remaining_edge_batch_b_source_lineage.csv"
LAYOUT_RELATIVE_PATH = "docs/review/generated/wp23_r1_remaining_edge_batch_b_layout_audit.json"
REPORT_RELATIVE_PATH = "docs/review/wp23_r1_remaining_edge_batch_b_report.md"
ANNOTATIONS_RELATIVE_PATH = "docs/review/wp23_r1_remaining_edge_review_annotations_batch_b.json"
REVIEW_NOTES_RELATIVE_PATH = "docs/review/wp23_r1_edge_decision_correction.csv"
QA_RECORD_RELATIVE_PATH = "docs/review/wp23_r1_qa_correction_record.md"
ASSETS_RELATIVE_PATH = "docs/review/assets/wp23_r1/remaining_edge_batch_b"

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
    sources = impl.PREVIOUS_SOURCE_CONTRACT(repo_root)[:-2]
    predecessor = [
        ("wp22_manifest", generated / "wp22_remaining_edge_batch_a_manifest.json", impl.PINNED["wp22_manifest"]),
        ("wp22_selection", generated / "wp22_remaining_edge_batch_a_selection.csv", impl.PINNED["wp22_selection"]),
        ("wp22_annotations", review / "wp22_remaining_edge_review_annotations_batch_a.json", impl.PINNED["wp22_annotations"]),
        ("wp22_builder", repo_root / "scripts/build_wp22_remaining_edge_review_batch.py", impl.PINNED["wp22_builder"]),
    ]
    correction_lineage = [
        ("wp23_failed_manifest", generated / "wp23_remaining_edge_batch_b_manifest.json", INITIAL_MANIFEST_SHA256),
        ("wp23_failed_selection", generated / "wp23_remaining_edge_batch_b_selection.csv", INITIAL_SELECTION_SHA256),
        ("wp23_failed_annotations", review / "wp23_remaining_edge_review_annotations_batch_b.json", INITIAL_ANNOTATIONS_SHA256),
        ("wp23_failed_review_notes", review / "wp23_remaining_edge_review_notes_batch_b.csv", INITIAL_REVIEW_NOTES_SHA256),
        ("wp23_failed_builder", repo_root / "scripts/build_wp23_remaining_edge_review_batch.py", INITIAL_BUILDER_SHA256),
        ("wp23_r1_qa_record", repo_root / QA_RECORD_RELATIVE_PATH, QA_CORRECTION_RECORD_SHA256),
        ("wp23_r1_correction_overlay", repo_root / REVIEW_NOTES_RELATIVE_PATH, EXPECTED_REVIEW_NOTES_SHA256),
        ("wp23_r1_builder", repo_root / "scripts/build_wp23_r1_remaining_edge_review_batch.py", None),
    ]
    return [*sources, *predecessor, *correction_lineage]


def derive_selection(
    repo_root: Path, raw_root: Path
) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    selected, inventory = ORIGINAL_DERIVE_SELECTION(repo_root, raw_root)
    initial = core.read_csv(
        repo_root / "docs/review/generated/wp23_remaining_edge_batch_b_selection.csv"
    )
    normalized: list[dict[str, str]] = []
    for row in selected:
        restored = dict(row)
        restored["wp12_atlas_page"] = restored["wp12_atlas_page"].replace(
            ASSETS_RELATIVE_PATH, INITIAL_ASSETS_RELATIVE_PATH
        )
        restored["evidence_boundary"] = INITIAL_EVIDENCE_BOUNDARY
        normalized.append(restored)
    if normalized != initial:
        raise ValueError("WP23-R1 selection or source lineage differs from immutable initial WP23")
    edge = next(row for row in selected if row["edge_id"] == "edge_000664")
    expected = {
        "batch_position": "192",
        "wp5_review_order": "1476",
        "left_stem": "0671",
        "right_stem": "0672",
        "left_split": "train",
        "right_split": "train",
        "cross_split": "False",
        "left_class_ids": "7 10 17 19 44",
        "right_class_ids": "7 10 17 19 44",
        "proxy_status": "strong_candidate",
        "thumbnail_mae": "6.303241",
        "dhash_distance": "6",
        "rgb_histogram_cosine": "0.99600903",
        "wp12_atlas_slot": "2",
    }
    if any(edge[field] != value for field, value in expected.items()):
        raise ValueError("WP23-R1 edge_000664 source evidence differs from QA finding")
    if not edge["wp12_atlas_page"].endswith("/page_039.jpg"):
        raise ValueError("WP23-R1 edge_000664 must remain on atlas page 039")
    return selected, inventory


def load_review_notes(
    repo_root: Path, selection: list[dict[str, str]]
) -> list[dict[str, str]]:
    initial_path = repo_root / "docs/review/wp23_remaining_edge_review_notes_batch_b.csv"
    if core.sha256_file(initial_path) != INITIAL_REVIEW_NOTES_SHA256:
        raise ValueError("initial WP23 review notes no longer match the failed-package anchor")
    notes = core.read_csv(initial_path)
    if len(notes) != EXPECTED_SELECTION_COUNT or list(notes[0]) != core.REVIEW_NOTE_FIELDS:
        raise ValueError("initial WP23 review notes schema/count changed")
    if [row["edge_id"] for row in notes] != [row["edge_id"] for row in selection]:
        raise ValueError("initial WP23 review notes no longer align with the R1 selection")
    corrections = core.read_csv(repo_root / REVIEW_NOTES_RELATIVE_PATH)
    if len(corrections) != 1 or list(corrections[0]) != CORRECTION_FIELDS:
        raise ValueError("WP23-R1 requires an exact one-row correction overlay")
    correction = corrections[0]
    if correction["edge_id"] != "edge_000664":
        raise ValueError("WP23-R1 correction overlay may change only edge_000664")
    target = next(row for row in notes if row["edge_id"] == correction["edge_id"])
    previous = (
        target["provisional_outcome"],
        target["capture_hypothesis"],
        target["physical_sign_hypothesis"],
    )
    expected_previous = (
        correction["previous_provisional_outcome"],
        correction["previous_capture_hypothesis"],
        correction["previous_physical_sign_hypothesis"],
    )
    if previous != expected_previous or expected_previous != ("NOT_RELATED",) * 3:
        raise ValueError("WP23-R1 previous edge_000664 decision does not match the QA-failed package")
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
        text = text.replace("M0-WP23 Remaining-Edge Batch B", "M0-WP23-R1 Remaining-Edge Batch B")
        text = text.replace("WP23 slot", "WP23-R1 slot")
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
        paths, layout = ORIGINAL_RENDER_ATLAS(
            selection, inventory, raw_root, assets_dir, decisions
        )
    finally:
        image_draw.Draw = original_draw
    index_path = assets_dir / "index.html"
    index_text = index_path.read_text(encoding="utf-8")
    index_text = index_text.replace("M0-WP23", "M0-WP23-R1").replace(
        "WP23 slot", "WP23-R1 slot"
    )
    index_path.write_text(index_text, encoding="utf-8")
    return paths, layout


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
            raise ValueError(f"WP23-R1 {label} differ from the QA correction contract")
    corrected = next(row for row in rows if row["edge_id"] == "edge_000664")
    if (
        corrected["provisional_outcome"] != "SAME_CAPTURE_CANDIDATE"
        or corrected["capture_hypothesis"] != "SAME_CAPTURE_CANDIDATE"
        or corrected["physical_sign_hypothesis"] != "SAME_PHYSICAL_SIGN_CANDIDATE"
        or corrected["confidence"] != "HIGH"
        or "same camera advances slightly within one scene" not in corrected["rationale"]
        or "7, 10, 17, 19, and 44" not in corrected["rationale"]
        or "MAE 6.303241" not in corrected["rationale"]
        or "dHash 6" not in corrected["rationale"]
        or "histogram 0.99600903" not in corrected["rationale"]
    ):
        raise ValueError("WP23-R1 edge_000664 correction or rationale differs from QA evidence")
    not_related = [row for row in rows if row["capture_hypothesis"] == "NOT_RELATED"]
    if len(not_related) != 16 or any(
        "discontinuous scene or non-matching physical signs" not in row["rationale"]
        for row in not_related
    ):
        raise ValueError("WP23-R1 requires explicit scene/sign-change rationale for all 16 NOT_RELATED rows")


def render_report(summary: dict[str, Any], annotation_payload: dict[str, Any]) -> str:
    def counts(name: str) -> str:
        return "\n".join(f"- `{key}`: {value}" for key, value in summary[name].items())

    return f"""# M0-WP23-R1 — D02-D remaining-edge manual reconciliation, Batch B correction

Status: `{PACKAGE_STATUS}`  
Boundary: `{EVIDENCE_BOUNDARY}`

This R1 reissue preserves the immutable QA-failed M0-WP23 package and changes only the reviewed
decision/rationale for `edge_000664`. It does not approve D-02, create final/transitive group truth
or a split, authorize training, or start WP24.

## QA failure and R1 correction lineage

- Initial independent QA verdict: **FAIL**, exactly one High finding and zero
  Critical/Medium/Low findings; technical/integrity checks remained PASS.
- Initial manifest SHA-256: `{INITIAL_MANIFEST_SHA256}`.
- Initial annotations SHA-256: `{INITIAL_ANNOTATIONS_SHA256}`.
- Initial review-notes SHA-256: `{INITIAL_REVIEW_NOTES_SHA256}`.
- QA record: `{QA_RECORD_RELATIVE_PATH}`.
- Trusted one-row correction-overlay SHA-256: `{EXPECTED_REVIEW_NOTES_SHA256}`.
- Corrected edge: `edge_000664`, WP5 order 1476, stems 0671/0672, page 039 slot 2.
- QA evidence: same camera advances slightly in one scene; identical annotated class sets
  `7 10 17 19 44`; `strong_candidate`, MAE `6.303241`, dHash `6`, histogram `0.99600903`.
- Corrected decision: `SAME_CAPTURE_CANDIDATE` / `SAME_PHYSICAL_SIGN_CANDIDATE`, confidence
  `HIGH`. The other 249 review decisions are unchanged.

## Selection and evidence boundary

- Selection remains the exact same 250 canonical rows as initial WP23,
  `{summary['first_edge']}` through `{summary['last_edge']}`, with 500 endpoints and
  {EXPECTED_SELECTED_ENDPOINT_BOX_COUNT} bbox occurrences.
- `edge_000242` and `edge_000243` remain quarantined/PENDING and outside lineage.
- All 250 pairs/500 raw frames remain represented in the deterministic 50-page R1 atlas.
- Sequence evidence remains context only and never derives an edge decision or group truth.

## Corrected capture outcomes

{counts('capture_hypothesis_counts')}

## Corrected physical-sign outcomes

{counts('physical_sign_hypothesis_counts')}

## Confidence

{counts('confidence_counts')}

## Remaining workload and governance

- Canonical WP5 remains unchanged at {summary['canonical_wp5_pending_unchanged']} PENDING edges.
- Outside WP7/WP12-WP15/WP22/WP23-R1 overlays, {summary['pending_outside_wp7_wp12_overlays']}
  PENDING edges remain, including the two quarantined stem-0248 adjacency edges; zero are
  cross-split.
- All {summary['all_wp5_sequences_pending']} WP5 sequences remain PENDING.
- D-02 remains PENDING; Gate 0 remains BLOCKED; `split_authorized=false` and
  `training_authorized=false`.

## Artifacts

- Corrected decisions: `{ANNOTATIONS_RELATIVE_PATH}`.
- Immutable selection reissue: `{SELECTION_RELATIVE_PATH}`.
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
        "render_report": render_report,
        "validate_review_decision_contract": validate_review_decision_contract,
    }
    for name, value in values.items():
        setattr(impl, name, value)
    impl.configure_previous()
    core.load_review_notes = load_review_notes


def prepare(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    _configure()
    result = impl.previous.prepare(repo_root, raw_root)
    result["status"] = "WP23_R1_PREPARED_AWAITING_BUILD_AND_QA_REVIEW"
    result["exact_residual_pending_count"] = EXPECTED_RESIDUAL_PENDING_COUNT
    result["review_eligible_residual_count"] = EXPECTED_ELIGIBLE_RESIDUAL_COUNT
    result["quarantined_residual_count"] = EXPECTED_QUARANTINED_RESIDUAL_COUNT
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
