# ruff: noqa: E501
"""Build and verify the M0-WP25-R1 one-edge QA correction reissue."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from collections import Counter
from pathlib import Path
from typing import Any

IMPL_PATH = Path(__file__).with_name("build_wp25_remaining_edge_review_batch.py")
SPEC = importlib.util.spec_from_file_location("wp25_r1_initial_package", IMPL_PATH)
assert SPEC is not None and SPEC.loader is not None
impl = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = impl
SPEC.loader.exec_module(impl)

base_impl = impl.impl
core = impl.core
ORIGINAL_DERIVE_SELECTION = impl.derive_selection
ORIGINAL_RENDER_ATLAS = impl.render_atlas
INITIAL_EVIDENCE_BOUNDARY = impl.EVIDENCE_BOUNDARY
INITIAL_ASSETS_RELATIVE_PATH = impl.ASSETS_RELATIVE_PATH

PACKAGE_STATUS = "WP25_R1_AWAITING_QA_REVIEW"
ANNOTATION_STATUS = "PM_REVIEWED_R1_CORRECTION_AWAITING_INDEPENDENT_QA"
EVIDENCE_BOUNDARY = (
    "REMAINING_EDGE_BATCH_D_R1_ONE_EDGE_QA_CORRECTION_ONLY_NOT_D02_APPROVAL_"
    "NOT_GROUP_TRUTH_NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING"
)
BATCH_ID = "M0-WP25-R1-REMAINING-EDGE-BATCH-D"
EXPECTED_SELECTION_COUNT = 250
EXPECTED_RESIDUAL_PENDING_COUNT = 1396
EXPECTED_QUARANTINED_RESIDUAL_COUNT = 2
EXPECTED_ELIGIBLE_RESIDUAL_COUNT = 1394
EXPECTED_REMAINING_AFTER_BATCH = 1146
EXPECTED_SELECTED_ENDPOINT_BOX_COUNT = 1090
EXPECTED_PAGE_COUNT = 50
EXPECTED_PAGE_ROW_COUNTS = (5,) * EXPECTED_PAGE_COUNT
REVIEWED_AT = "2026-10-14T05:23:50+07:00"

INITIAL_MANIFEST_SHA256 = "1d7b04d6432424297f2e14178dd59936526dec7d6293872fbda0010bb460e5e9"
INITIAL_SELECTION_SHA256 = "8cb67fb593d610978dcec472f0dbd0dc53b5ae1d416468b908f92ba94320e10f"
INITIAL_ANNOTATIONS_SHA256 = "990d314a462a2279d9600f2b6b5e2b12c1da73dd7425e7ec07a388d883487cc5"
INITIAL_REVIEW_NOTES_SHA256 = "b3b97a12577351ef7019f2793a0b7b988f8e7ffddb5929ae7c255a0d7e69a6b8"
INITIAL_BUILDER_SHA256 = "a1807e834a7f212907efe17f14670e31a3d8d35d90e50ec9b170f58a374b930f"
EXPECTED_REVIEW_NOTES_SHA256 = "a1385c5a295b927887ffe73c29987d1c3487812d7d25b1a3aa9688c25f39ecd9"
QA_CORRECTION_RECORD_SHA256 = "e1e641ee6b36abd257d284d3231c6672934b6ed906964536352b5a8de706439d"

EXPECTED_CAPTURE_COUNTS = {
    "NOT_RELATED": 9,
    "SAME_CAPTURE_CANDIDATE": 241,
}
EXPECTED_PHYSICAL_SIGN_COUNTS = {
    "NOT_RELATED": 9,
    "SAME_PHYSICAL_SIGN_CANDIDATE": 241,
}
EXPECTED_CONFIDENCE_COUNTS = {"HIGH": EXPECTED_SELECTION_COUNT}
EXPECTED_CAPTURE_UNRESOLVED_IDS: set[str] = set()
EXPECTED_PHYSICAL_SIGN_UNRESOLVED_IDS: set[str] = set()
EXPECTED_CAPTURE_NOT_RELATED_IDS = impl.EXPECTED_CAPTURE_NOT_RELATED_IDS - {"edge_001358"}
EXPECTED_PHYSICAL_SIGN_NOT_RELATED_IDS = set(EXPECTED_CAPTURE_NOT_RELATED_IDS)

MANIFEST_RELATIVE_PATH = "docs/review/generated/wp25_r1_remaining_edge_batch_d_manifest.json"
SELECTION_RELATIVE_PATH = "docs/review/generated/wp25_r1_remaining_edge_batch_d_selection.csv"
LINEAGE_RELATIVE_PATH = "docs/review/generated/wp25_r1_remaining_edge_batch_d_source_lineage.csv"
LAYOUT_RELATIVE_PATH = "docs/review/generated/wp25_r1_remaining_edge_batch_d_layout_audit.json"
REPORT_RELATIVE_PATH = "docs/review/wp25_r1_remaining_edge_batch_d_report.md"
ANNOTATIONS_RELATIVE_PATH = "docs/review/wp25_r1_remaining_edge_review_annotations_batch_d.json"
REVIEW_NOTES_RELATIVE_PATH = "docs/review/wp25_r1_edge_decision_correction.csv"
QA_RECORD_RELATIVE_PATH = "docs/review/wp25_r1_qa_correction_record.md"
ASSETS_RELATIVE_PATH = "docs/review/assets/wp25_r1/remaining_edge_batch_d"

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
    sources = impl.source_contract(repo_root)[:-2]
    correction_lineage = [
        ("wp25_failed_manifest", generated / "wp25_remaining_edge_batch_d_manifest.json", INITIAL_MANIFEST_SHA256),
        ("wp25_failed_selection", generated / "wp25_remaining_edge_batch_d_selection.csv", INITIAL_SELECTION_SHA256),
        ("wp25_failed_annotations", review / "wp25_remaining_edge_review_annotations_batch_d.json", INITIAL_ANNOTATIONS_SHA256),
        ("wp25_failed_review_notes", review / "wp25_remaining_edge_review_notes_batch_d.csv", INITIAL_REVIEW_NOTES_SHA256),
        ("wp25_failed_builder", repo_root / "scripts/build_wp25_remaining_edge_review_batch.py", INITIAL_BUILDER_SHA256),
        ("wp25_r1_qa_record", repo_root / QA_RECORD_RELATIVE_PATH, QA_CORRECTION_RECORD_SHA256),
        ("wp25_r1_correction_overlay", repo_root / REVIEW_NOTES_RELATIVE_PATH, EXPECTED_REVIEW_NOTES_SHA256),
        ("wp25_r1_builder", repo_root / "scripts/build_wp25_r1_remaining_edge_review_batch.py", None),
    ]
    return [*sources, *correction_lineage]


def derive_selection(
    repo_root: Path, raw_root: Path
) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    selected, inventory = ORIGINAL_DERIVE_SELECTION(repo_root, raw_root)
    initial = core.read_csv(
        repo_root / "docs/review/generated/wp25_remaining_edge_batch_d_selection.csv"
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
        raise ValueError("WP25-R1 selection or source lineage differs from immutable initial WP25")
    if any(
        "0248" in {row["left_stem"], row["right_stem"]}
        or row["proxy_sequence_id"] == "proxy_sequence_0050"
        for row in selected
    ):
        raise ValueError("WP25-R1 must preserve stem-0248 and proxy_sequence_0050 quarantine")
    edge = next(row for row in selected if row["edge_id"] == "edge_001358")
    expected = {
        "batch_position": "144",
        "wp5_review_order": "1928",
        "left_stem": "1365",
        "right_stem": "1366",
        "left_split": "train",
        "right_split": "train",
        "cross_split": "False",
        "same_dimensions": "True",
        "left_class_ids": "5",
        "right_class_ids": "5",
        "proxy_status": "uncertain",
        "proxy_sequence_id": "",
        "thumbnail_mae": "12.005787",
        "dhash_distance": "18",
        "rgb_histogram_cosine": "0.99375935",
        "wp12_atlas_slot": "4",
    }
    if any(edge[field] != value for field, value in expected.items()):
        raise ValueError("WP25-R1 edge_001358 source evidence differs from QA finding")
    if not edge["wp12_atlas_page"].endswith("/page_029.jpg"):
        raise ValueError("WP25-R1 edge_001358 must remain on atlas page 029")
    expected_labels = {
        "left_label_path": "5 0.388021 0.303704 0.036458 0.055556\n",
        "right_label_path": "5 0.406250 0.313889 0.037500 0.046296\n",
    }
    for field, expected_text in expected_labels.items():
        label_text = (raw_root / edge[field]).read_text(encoding="utf-8")
        if label_text != expected_text:
            raise ValueError(f"WP25-R1 {field} differs from independently reverified QA evidence")
    return selected, inventory


def load_review_notes(
    repo_root: Path, selection: list[dict[str, str]]
) -> list[dict[str, str]]:
    initial_path = repo_root / "docs/review/wp25_remaining_edge_review_notes_batch_d.csv"
    if core.sha256_file(initial_path) != INITIAL_REVIEW_NOTES_SHA256:
        raise ValueError("initial WP25 review notes no longer match the failed-package anchor")
    notes = core.read_csv(initial_path)
    if len(notes) != EXPECTED_SELECTION_COUNT or list(notes[0]) != core.REVIEW_NOTE_FIELDS:
        raise ValueError("initial WP25 review notes schema/count changed")
    if [row["edge_id"] for row in notes] != [row["edge_id"] for row in selection]:
        raise ValueError("initial WP25 review notes no longer align with the R1 selection")
    corrections = core.read_csv(repo_root / REVIEW_NOTES_RELATIVE_PATH)
    if len(corrections) != 1 or list(corrections[0]) != CORRECTION_FIELDS:
        raise ValueError("WP25-R1 requires an exact one-row correction overlay")
    correction = corrections[0]
    if correction["edge_id"] != "edge_001358":
        raise ValueError("WP25-R1 correction overlay may change only edge_001358")
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
        raise ValueError("WP25-R1 previous edge_001358 decision does not match the QA-failed package")
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
        text = text.replace("M0-WP25 Remaining-Edge Batch D", "M0-WP25-R1 Remaining-Edge Batch D")
        text = text.replace("WP25 slot", "WP25-R1 slot")
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
    index_text = index_text.replace("M0-WP25", "M0-WP25-R1").replace(
        "WP25 slot", "WP25-R1 slot"
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
            raise ValueError(f"WP25-R1 {label} differ from the QA correction contract")
    corrected = next(row for row in rows if row["edge_id"] == "edge_001358")
    if (
        corrected["provisional_outcome"] != "SAME_CAPTURE_CANDIDATE"
        or corrected["capture_hypothesis"] != "SAME_CAPTURE_CANDIDATE"
        or corrected["physical_sign_hypothesis"] != "SAME_PHYSICAL_SIGN_CANDIDATE"
        or corrected["confidence"] != "HIGH"
        or "same moving camera advances within one road scene" not in corrected["rationale"]
        or "same class-5 physical sign" not in corrected["rationale"]
        or "0.388021/0.303704/0.036458/0.055556" not in corrected["rationale"]
        or "0.406250/0.313889/0.037500/0.046296" not in corrected["rationale"]
        or "MAE 12.005787" not in corrected["rationale"]
        or "dHash 18" not in corrected["rationale"]
        or "histogram 0.99375935" not in corrected["rationale"]
    ):
        raise ValueError("WP25-R1 edge_001358 correction or rationale differs from QA evidence")
    not_related = [row for row in rows if row["capture_hypothesis"] == "NOT_RELATED"]
    if len(not_related) != 9 or any(
        "discontinuous scene and non-matching physical signs" not in row["rationale"]
        for row in not_related
    ):
        raise ValueError("WP25-R1 requires explicit scene/sign-change rationale for all 9 NOT_RELATED rows")


def render_report(summary: dict[str, Any], annotation_payload: dict[str, Any]) -> str:
    def counts(name: str) -> str:
        return "\n".join(f"- `{key}`: {value}" for key, value in summary[name].items())

    return f"""# M0-WP25-R1 — D02-D remaining-edge manual reconciliation, Batch D correction

Status: `{PACKAGE_STATUS}`  
Boundary: `{EVIDENCE_BOUNDARY}`

This R1 reissue preserves the immutable QA-failed M0-WP25 package and changes only the reviewed
decision/rationale for `edge_001358`. It does not approve D-02, create final/transitive group truth
or a split, authorize training, or start WP26.

## QA failure and R1 correction lineage

- Initial independent QA verdict: **FAIL**, exactly one `P1` finding and zero
  `P0`/`P2`/`P3` findings; technical/integrity checks remained PASS.
- Initial manifest SHA-256: `{INITIAL_MANIFEST_SHA256}`.
- Initial annotations SHA-256: `{INITIAL_ANNOTATIONS_SHA256}`.
- Initial review-notes SHA-256: `{INITIAL_REVIEW_NOTES_SHA256}`.
- QA record: `{QA_RECORD_RELATIVE_PATH}`.
- Trusted one-row correction-overlay SHA-256: `{EXPECTED_REVIEW_NOTES_SHA256}`.
- Corrected edge: `edge_001358`, Batch position 144, WP5 order 1928, stems 1365/1366,
  page 029 slot 4.
- QA evidence: same moving camera advances within one road scene and the same class-5 physical
  sign remains visible; class-5 bbox center/size changes from
  `(0.388021, 0.303704)/(0.036458, 0.055556)` to
  `(0.406250, 0.313889)/(0.037500, 0.046296)`; same dimensions, `uncertain` proxy,
  MAE `12.005787`, dHash `18`, histogram `0.99375935`.
- Corrected decision: `SAME_CAPTURE_CANDIDATE` / `SAME_PHYSICAL_SIGN_CANDIDATE`, confidence
  `HIGH`. The other 249 review decisions are unchanged.

## Selection and evidence boundary

- Selection remains the exact same 250 canonical rows as initial WP25,
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
- Outside WP7/WP12-WP15/WP22/WP25-R1 overlays, {summary['pending_outside_wp7_wp12_overlays']}
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
        setattr(base_impl, name, value)
    base_impl.configure_previous()
    core.load_review_notes = load_review_notes


def prepare(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    _configure()
    result = base_impl.previous.prepare(repo_root, raw_root)
    result["status"] = "WP25_R1_PREPARED_AWAITING_BUILD_AND_QA_REVIEW"
    result["exact_residual_pending_count"] = EXPECTED_RESIDUAL_PENDING_COUNT
    result["review_eligible_residual_count"] = EXPECTED_ELIGIBLE_RESIDUAL_COUNT
    result["quarantined_residual_count"] = EXPECTED_QUARANTINED_RESIDUAL_COUNT
    return result


def build(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    _configure()
    return base_impl.previous.build(repo_root, raw_root)


def verify(manifest_path: Path, repo_root: Path, raw_root: Path) -> dict[str, Any]:
    _configure()
    return base_impl.previous.verify(manifest_path, repo_root, raw_root)


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
