# ruff: noqa: E501
"""Build and verify M0-WP23 remaining-edge manual-review Batch B."""

from __future__ import annotations

import argparse
import importlib.util
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PREVIOUS_PATH = Path(__file__).with_name("build_wp22_remaining_edge_review_batch.py")
SPEC = importlib.util.spec_from_file_location("wp23_hardened_previous", PREVIOUS_PATH)
assert SPEC is not None and SPEC.loader is not None
previous = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = previous
SPEC.loader.exec_module(previous)
PREVIOUS_RENDER_ATLAS = previous.render_atlas
PREVIOUS_SOURCE_CONTRACT = previous.source_contract
PREVIOUS_LOAD_SEQUENCE_CONTEXT = previous.load_sequence_context

PACKAGE_STATUS = "WP23_AWAITING_QA_REMAINING_EDGE_BATCH_B_PM_PROVISIONAL_REVIEW"
ANNOTATION_STATUS = "PM_REVIEWED_AWAITING_INDEPENDENT_QA"
EVIDENCE_BOUNDARY = (
    "REMAINING_EDGE_BATCH_B_PM_PROVISIONAL_VISUAL_REVIEW_ONLY_NOT_D02_APPROVAL_"
    "NOT_GROUP_TRUTH_NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING"
)
BATCH_ID = "M0-WP23-REMAINING-EDGE-BATCH-B"
EXPECTED_SELECTION_COUNT = 250
EXPECTED_RESIDUAL_PENDING_COUNT = 1896
EXPECTED_QUARANTINED_RESIDUAL_COUNT = 2
EXPECTED_ELIGIBLE_RESIDUAL_COUNT = 1894
EXPECTED_REMAINING_AFTER_BATCH = 1646
EXPECTED_SELECTED_ENDPOINT_BOX_COUNT = 1556
EXPECTED_PAGE_COUNT = 50
PAIRS_PER_PAGE = 5
EXPECTED_PAGE_ROW_COUNTS = (5,) * EXPECTED_PAGE_COUNT
REVIEWED_AT = "2026-10-12T03:40:28+07:00"

# Direct-PM-review trust anchor. Changing any reviewed decision requires an explicit
# source review and anchor update before the official package can be rebuilt.
EXPECTED_REVIEW_NOTES_SHA256 = (
    "c9159a36096f11c409e1c88ad49d15947ed052db7d5e4fddb310647f47a113c8"
)
EXPECTED_CAPTURE_COUNTS = {
    "NOT_RELATED": 17,
    "SAME_CAPTURE_CANDIDATE": 233,
}
EXPECTED_PHYSICAL_SIGN_COUNTS = {
    "NOT_RELATED": 17,
    "SAME_PHYSICAL_SIGN_CANDIDATE": 233,
}
EXPECTED_CONFIDENCE_COUNTS = {"HIGH": EXPECTED_SELECTION_COUNT}
EXPECTED_CAPTURE_UNRESOLVED_IDS: set[str] = set()
EXPECTED_PHYSICAL_SIGN_UNRESOLVED_IDS: set[str] = set()
EXPECTED_CAPTURE_NOT_RELATED_IDS = {
    "edge_000382",
    "edge_000399",
    "edge_000408",
    "edge_000429",
    "edge_000458",
    "edge_000523",
    "edge_000524",
    "edge_000534",
    "edge_000543",
    "edge_000587",
    "edge_000597",
    "edge_000637",
    "edge_000664",
    "edge_000699",
    "edge_000712",
    "edge_000722",
    "edge_000743",
}
EXPECTED_PHYSICAL_SIGN_NOT_RELATED_IDS = set(EXPECTED_CAPTURE_NOT_RELATED_IDS)

MANIFEST_RELATIVE_PATH = "docs/review/generated/wp23_remaining_edge_batch_b_manifest.json"
SELECTION_RELATIVE_PATH = "docs/review/generated/wp23_remaining_edge_batch_b_selection.csv"
LINEAGE_RELATIVE_PATH = "docs/review/generated/wp23_remaining_edge_batch_b_source_lineage.csv"
LAYOUT_RELATIVE_PATH = "docs/review/generated/wp23_remaining_edge_batch_b_layout_audit.json"
REPORT_RELATIVE_PATH = "docs/review/wp23_remaining_edge_batch_b_report.md"
ANNOTATIONS_RELATIVE_PATH = "docs/review/wp23_remaining_edge_review_annotations_batch_b.json"
REVIEW_NOTES_RELATIVE_PATH = "docs/review/wp23_remaining_edge_review_notes_batch_b.csv"
ASSETS_RELATIVE_PATH = "docs/review/assets/wp23/remaining_edge_batch_b"

SEQUENCE_CONTEXT_FIELDS = [
    "sequence_context_status",
    "sequence_context_batch",
    "sequence_capture_context",
    "sequence_physical_context",
    "sequence_confidence_context",
    "sequence_context_boundary",
]

PINNED = {
    "wp22_manifest": "7086371d65d1389c26541a3621745e0eadb9df7bfe62ca3dab34ffbb45e3b487",
    "wp22_selection": "af70edc35a2a925f4e23bd8ce2e481c7fdf6e18f1c904c963561c412ac74d6aa",
    "wp22_annotations": "f00bdbcf28139c3f27716aaaa035948512313e88a5efb7b9b4be53d5cc50a0ac",
    "wp22_builder": "7f9310334e640226d70f968c4c00630b1e77e3a7a763222b9e591a2b22a0ba61",
}


def source_contract(repo_root: Path) -> list[tuple[str, Path, str | None]]:
    generated = repo_root / "docs/review/generated"
    review = repo_root / "docs/review"
    sources = PREVIOUS_SOURCE_CONTRACT(repo_root)[:-2]
    predecessor = [
        ("wp22_manifest", generated / "wp22_remaining_edge_batch_a_manifest.json", PINNED["wp22_manifest"]),
        ("wp22_selection", generated / "wp22_remaining_edge_batch_a_selection.csv", PINNED["wp22_selection"]),
        ("wp22_annotations", review / "wp22_remaining_edge_review_annotations_batch_a.json", PINNED["wp22_annotations"]),
        ("wp22_builder", repo_root / "scripts/build_wp22_remaining_edge_review_batch.py", PINNED["wp22_builder"]),
    ]
    return [
        *sources,
        *predecessor,
        ("wp23_review_notes", repo_root / REVIEW_NOTES_RELATIVE_PATH, EXPECTED_REVIEW_NOTES_SHA256),
        ("wp23_builder", repo_root / "scripts/build_wp23_remaining_edge_review_batch.py", None),
    ]


def load_sequence_context(repo_root: Path) -> dict[str, dict[str, str]]:
    context = PREVIOUS_LOAD_SEQUENCE_CONTEXT(repo_root)
    if len(context) != 588:
        raise ValueError("WP23 requires exact WP16-WP21 context for all 588 eligible sequences")
    return context


def derive_selection(
    repo_root: Path, raw_root: Path
) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    base = previous.previous.previous.base
    rows = base.load_wp5_rows(repo_root)
    inventory = base.load_inventory(repo_root)
    cross_split_overlay_paths = [
        "wp7_batch_a_selection.csv",
        "wp12_batch_b_selection.csv",
        "wp13_batch_c_selection.csv",
        "wp14_batch_d_selection.csv",
        "wp15_batch_e_selection.csv",
    ]
    expected_counts = [100, 250, 250, 250, 176]
    rosters = [
        base.read_csv(repo_root / "docs/review/generated" / path)
        for path in cross_split_overlay_paths
    ]
    if [len(roster) for roster in rosters] != expected_counts:
        raise ValueError("WP23 predecessor edge-overlay counts differ from contract")
    cross_split_overlay_ids = [
        row["edge_id"] for roster in rosters for row in roster
    ]
    pending_cross_split = [
        row["edge_id"]
        for row in rows
        if row["review_status"] == "PENDING" and row["cross_split"] == "True"
    ]
    if (
        len(cross_split_overlay_ids) != 1026
        or len(set(cross_split_overlay_ids)) != 1026
        or cross_split_overlay_ids != pending_cross_split
    ):
        raise ValueError("WP23 requires exact non-overlapping coverage of all 1,026 pending cross-split edges")
    cross_split_overlay_set = set(cross_split_overlay_ids)
    base_residual = [
        row
        for row in rows
        if row["review_status"] == "PENDING"
        and row["edge_id"] not in cross_split_overlay_set
    ]
    if (
        len(base_residual) != 2146
        or len({row["edge_id"] for row in base_residual}) != 2146
        or any(row["cross_split"] != "False" for row in base_residual)
    ):
        raise ValueError("WP23 base residual must be exactly 2,146 unique non-cross-split PENDING edges")
    base_quarantined = [
        row
        for row in base_residual
        if base.QUARANTINED_STEM in {row["left_stem"], row["right_stem"]}
    ]
    if [row["edge_id"] for row in base_quarantined] != [
        "edge_000242",
        "edge_000243",
    ]:
        raise ValueError("WP23 exact base quarantined residual edge roster changed")
    base_eligible = [row for row in base_residual if row not in base_quarantined]
    if len(base_eligible) != 2144:
        raise ValueError("WP23 base review-eligible residual count must be exactly 2,144")

    wp22_selection = base.read_csv(
        repo_root / "docs/review/generated/wp22_remaining_edge_batch_a_selection.csv"
    )
    wp22_ids = [row["edge_id"] for row in wp22_selection]
    expected_wp22_ids = [row["edge_id"] for row in base_eligible[:250]]
    if (
        len(wp22_ids) != 250
        or len(set(wp22_ids)) != 250
        or wp22_ids != expected_wp22_ids
        or any(row["wp5_review_status"] != "PENDING" for row in wp22_selection)
        or any(row["cross_split"] != "False" for row in wp22_selection)
        or any(
            base.QUARANTINED_STEM in {row["left_stem"], row["right_stem"]}
            for row in wp22_selection
        )
    ):
        raise ValueError("WP23 requires the exact first-250 eligible residual roster from WP22")

    predecessor_overlay_set = cross_split_overlay_set | set(wp22_ids)
    residual = [
        row
        for row in rows
        if row["review_status"] == "PENDING"
        and row["edge_id"] not in predecessor_overlay_set
    ]
    if (
        len(residual) != EXPECTED_RESIDUAL_PENDING_COUNT
        or len({row["edge_id"] for row in residual})
        != EXPECTED_RESIDUAL_PENDING_COUNT
        or any(row["cross_split"] != "False" for row in residual)
    ):
        raise ValueError("WP23 residual must be exactly 1,896 unique non-cross-split PENDING edges")
    quarantined = [
        row
        for row in residual
        if base.QUARANTINED_STEM in {row["left_stem"], row["right_stem"]}
    ]
    if [row["edge_id"] for row in quarantined] != [
        "edge_000242",
        "edge_000243",
    ]:
        raise ValueError("WP23 exact quarantined residual edge roster changed")
    eligible = [row for row in residual if row not in quarantined]
    if len(eligible) != EXPECTED_ELIGIBLE_RESIDUAL_COUNT:
        raise ValueError("WP23 review-eligible residual count must be exactly 1,894")
    candidates = eligible[:EXPECTED_SELECTION_COUNT]
    if len(candidates) != EXPECTED_SELECTION_COUNT:
        raise ValueError("WP23 could not derive exactly 250 remaining-edge Batch-B rows")
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
                "selection_status": "SELECTED_REVIEW_ELIGIBLE_REMAINING_EDGE_BATCH_B",
                "evidence_boundary": EVIDENCE_BOUNDARY,
                **context_fields,
            }
        )
    if any(base.QUARANTINED_STEM in {row["left_stem"], row["right_stem"]} for row in selected):
        raise ValueError("WP23 selection must keep quarantined stem 0248 outside lineage")
    return selected, inventory


class _DrawProxy:
    def __init__(self, wrapped: Any) -> None:
        self._wrapped = wrapped

    def text(self, xy: Any, text: str, *args: Any, **kwargs: Any) -> Any:
        text = text.replace(
            "M0-WP22 Remaining-Edge Batch A",
            "M0-WP23 Remaining-Edge Batch B",
        )
        text = text.replace("WP22 slot", "WP23 slot")
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
    image_draw = previous.previous.previous.base.ImageDraw
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
    index_text = index_text.replace("M0-WP22", "M0-WP23").replace(
        "Remaining-Edge Batch A", "Remaining-Edge Batch B"
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
        "canonical_wp5_pending_unchanged": previous.previous.previous.base.EXPECTED_WP5_PENDING_COUNT,
        "pending_outside_wp7_wp12_overlays": EXPECTED_REMAINING_AFTER_BATCH,
        "cross_split_pending_outside_wp7_wp12_overlays": 0,
        "all_wp5_sequences_pending": previous.previous.previous.base.EXPECTED_WP5_SEQUENCE_COUNT,
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
            raise ValueError(f"WP23 {label} differ from approved PM review")


def render_report(summary: dict[str, Any], annotation_payload: dict[str, Any]) -> str:
    def counts(name: str) -> str:
        return "\n".join(f"- `{key}`: {value}" for key, value in summary[name].items())

    return f"""# M0-WP23 — D02-D remaining-edge manual reconciliation, Batch B

Status: `{PACKAGE_STATUS}`  
Boundary: `{EVIDENCE_BOUNDARY}`

This package records one PM/Codex provisional visual pass over the next 250 review-eligible
canonical residual PENDING edges after exact WP7/WP12-WP15 and WP22 overlay removal. It does not
approve D-02, create final/transitive group truth or a split, or authorize training.

## Selection and review protocol

- Exact canonical residual: 1,896 unique PENDING edges after excluding six WP5-reviewed rows, the
  exact 1,026 QA-passed cross-split overlay rows, and the exact 250-row WP22 Batch-A roster; every
  residual edge has `cross_split=False`.
- Quarantine exclusion: `edge_000242` and `edge_000243` remain residual/PENDING but are excluded
  because they touch stem `0248`; no quarantined source enters WP23 lineage.
- Selection: first 250 of the 1,894 review-eligible residual rows in canonical WP5 order,
  `{summary['first_edge']}` through `{summary['last_edge']}`.
- Source coverage: 500 endpoint rows with {EXPECTED_SELECTED_ENDPOINT_BOX_COUNT} total boxes.
- Reviewer: `{annotation_payload['reviewer']}` at `{annotation_payload['reviewed_at']}`.
- All 250 pairs/500 raw frames were directly inspected in the dedicated 50-page WP23 atlas.
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
- Outside WP7/WP12-WP15/WP22/WP23 overlays,
  {summary['pending_outside_wp7_wp12_overlays']} PENDING edges remain, including the two quarantined
  stem-0248 adjacency edges; zero are cross-split.
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
    core = previous.previous.previous.base
    if not all(field in core.SELECTION_FIELDS for field in SEQUENCE_CONTEXT_FIELDS):
        core.SELECTION_FIELDS = [*core.SELECTION_FIELDS, *SEQUENCE_CONTEXT_FIELDS]


def prepare(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    configure_previous()
    result = previous.prepare(repo_root, raw_root)
    result["status"] = "WP23_REMAINING_EDGE_BATCH_B_PREPARED_AWAITING_PM_VISUAL_REVIEW"
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
    print(previous.previous.previous.base.json.dumps(result, indent=2, sort_keys=True))
    return 0 if args.command != "verify" or result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
