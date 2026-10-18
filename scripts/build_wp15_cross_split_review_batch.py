# ruff: noqa: E501
"""Build and verify the M0-WP15 cross-split visual-review Batch-E package."""

from __future__ import annotations

import argparse
import importlib.util
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PREVIOUS_PATH = Path(__file__).with_name("build_wp14_cross_split_review_batch.py")
SPEC = importlib.util.spec_from_file_location("wp15_hardened_previous", PREVIOUS_PATH)
assert SPEC is not None and SPEC.loader is not None
previous = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = previous
SPEC.loader.exec_module(previous)
PREVIOUS_RENDER_ATLAS = previous.render_atlas
PREVIOUS_SOURCE_CONTRACT = previous.source_contract

PACKAGE_STATUS = "WP15_AWAITING_QA_BATCH_E_PM_PROVISIONAL_REVIEW"
ANNOTATION_STATUS = "PM_REVIEWED_AWAITING_INDEPENDENT_QA"
EVIDENCE_BOUNDARY = (
    "BATCH_E_PM_PROVISIONAL_VISUAL_REVIEW_ONLY_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_"
    "NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING"
)
BATCH_ID = "M0-WP15-BATCH-E"
EXPECTED_SELECTION_COUNT = 176
EXPECTED_BATCH_A_COUNT = 100
EXPECTED_BATCH_B_COUNT = 250
EXPECTED_BATCH_C_COUNT = 250
EXPECTED_BATCH_D_COUNT = 250
EXPECTED_SELECTED_ENDPOINT_BOX_COUNT = 992
EXPECTED_PAGE_COUNT = 36
PAIRS_PER_PAGE = previous.base.PAIRS_PER_PAGE
EXPECTED_PAGE_ROW_COUNTS = (5,) * 35 + (1,)
REVIEWED_AT = "2026-10-11T15:52:58+07:00"

# Pinned only after the PM directly inspected all 176 prepared pairs.
EXPECTED_REVIEW_NOTES_SHA256 = (
    "740fe42e79ec6e2a8c921ac254c31172188c5860898b81f205a494843f6e0bd7"
)
EXPECTED_CAPTURE_COUNTS = {"SAME_CAPTURE_CANDIDATE": 176}
EXPECTED_PHYSICAL_SIGN_COUNTS = {
    "SAME_PHYSICAL_SIGN_CANDIDATE": 173,
    "NOT_RELATED": 3,
}
EXPECTED_CONFIDENCE_COUNTS = {"HIGH": 176}
EXPECTED_CAPTURE_UNRESOLVED_IDS: set[str] = set()
EXPECTED_PHYSICAL_SIGN_UNRESOLVED_IDS: set[str] = set()
EXPECTED_CAPTURE_NOT_RELATED_IDS: set[str] = set()
EXPECTED_PHYSICAL_SIGN_NOT_RELATED_IDS = {
    "edge_002798",
    "edge_002847",
    "edge_002901",
}

MANIFEST_RELATIVE_PATH = "docs/review/generated/wp15_batch_e_manifest.json"
SELECTION_RELATIVE_PATH = "docs/review/generated/wp15_batch_e_selection.csv"
LINEAGE_RELATIVE_PATH = "docs/review/generated/wp15_batch_e_source_lineage.csv"
LAYOUT_RELATIVE_PATH = "docs/review/generated/wp15_batch_e_layout_audit.json"
REPORT_RELATIVE_PATH = "docs/review/wp15_cross_split_review_batch_e_report.md"
ANNOTATIONS_RELATIVE_PATH = "docs/review/wp15_visual_review_annotations_batch_e.json"
REVIEW_NOTES_RELATIVE_PATH = "docs/review/wp15_visual_review_notes_batch_e.csv"
ASSETS_RELATIVE_PATH = "docs/review/assets/wp15/batch_e"

PINNED = {
    **previous.PINNED,
    "wp14_manifest": "ea4667c2ea18bc6fff23ce23beffe5b27372e494160fa9d6ffbc86c3cb3f2dc5",
    "wp14_selection": "2fa132127980d9546869d628a1610c21184ebdf1c6d988772dae421a4df16a1a",
    "wp14_annotations": "2fd5a2e8d9336fb42b07250f06bdbfcf5392d1db9788a69a7d42da6dbd56e0cb",
    "wp14_builder": "4df862458d00428f0d9c286b028988f04856d04c75451a785f9a0890cd182bb5",
}


def source_contract(repo_root: Path) -> list[tuple[str, Path, str | None]]:
    generated = repo_root / "docs/review/generated"
    sources = PREVIOUS_SOURCE_CONTRACT(repo_root)[:-2]
    return [
        *sources,
        ("wp14_manifest", generated / "wp14_batch_d_manifest.json", PINNED["wp14_manifest"]),
        ("wp14_selection", generated / "wp14_batch_d_selection.csv", PINNED["wp14_selection"]),
        ("wp14_annotations", repo_root / "docs/review/wp14_visual_review_annotations_batch_d.json", PINNED["wp14_annotations"]),
        (
            "wp14_builder",
            repo_root / "scripts/build_wp14_cross_split_review_batch.py",
            PINNED["wp14_builder"],
        ),
        ("wp15_review_notes", repo_root / REVIEW_NOTES_RELATIVE_PATH, EXPECTED_REVIEW_NOTES_SHA256),
        ("wp15_builder", repo_root / "scripts/build_wp15_cross_split_review_batch.py", None),
    ]


def derive_selection(
    repo_root: Path, raw_root: Path
) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    base = previous.base
    rows = base.load_wp5_rows(repo_root)
    inventory = base.load_inventory(repo_root)
    pending = [
        row
        for row in rows
        if row["cross_split"] == "True" and row["review_status"] == "PENDING"
    ]
    rosters = [
        base.read_csv(repo_root / "docs/review/generated/wp7_batch_a_selection.csv"),
        base.read_csv(repo_root / "docs/review/generated/wp12_batch_b_selection.csv"),
        base.read_csv(repo_root / "docs/review/generated/wp13_batch_c_selection.csv"),
        base.read_csv(repo_root / "docs/review/generated/wp14_batch_d_selection.csv"),
    ]
    expected_counts = [
        EXPECTED_BATCH_A_COUNT,
        EXPECTED_BATCH_B_COUNT,
        EXPECTED_BATCH_C_COUNT,
        EXPECTED_BATCH_D_COUNT,
    ]
    pending_ids = [row["edge_id"] for row in pending]
    offset = 0
    excluded_ids: list[str] = []
    for label, roster, expected_count in zip(
        ("WP7 Batch-A", "WP12 Batch-B", "WP13 Batch-C", "WP14 Batch-D"),
        rosters,
        expected_counts,
        strict=True,
    ):
        roster_ids = [row["edge_id"] for row in roster]
        if len(roster_ids) != expected_count:
            raise ValueError(f"{label} exclusion roster count differs from contract")
        if roster_ids != pending_ids[offset : offset + expected_count]:
            raise ValueError(f"{label} exclusion roster/order differs from canonical prefix")
        excluded_ids.extend(roster_ids)
        offset += expected_count
    if len(set(excluded_ids)) != offset:
        raise ValueError("WP7/WP12/WP13/WP14 exclusion rosters overlap or contain duplicates")
    candidates = pending[offset:]
    if len(candidates) != EXPECTED_SELECTION_COUNT:
        raise ValueError("Batch-E must be the exact final 176 pending cross-split edges")
    excluded = set(excluded_ids)
    selected: list[dict[str, str]] = []
    for position, edge in enumerate(candidates, start=1):
        if edge["edge_id"] in base.EXPECTED_WP5_REVIEWED_IDS or edge["edge_id"] in excluded:
            raise ValueError("WP15 selection contains an ineligible prior-review edge")
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
                # Compatibility names are retained for the hardened WP12 renderer/verifier.
                "wp12_atlas_page": f"{ASSETS_RELATIVE_PATH}/page_{page:03d}.jpg",
                "wp12_atlas_slot": str(slot),
                "selection_status": "SELECTED_PENDING_CROSS_SPLIT_BATCH_E",
                "evidence_boundary": EVIDENCE_BOUNDARY,
            }
        )
    if any(base.QUARANTINED_STEM in {row["left_stem"], row["right_stem"]} for row in selected):
        raise ValueError("WP15 selection must exclude quarantined stem 0248")
    return selected, inventory


class _DrawProxy:
    def __init__(self, wrapped: Any) -> None:
        self._wrapped = wrapped

    def text(self, xy: Any, text: str, *args: Any, **kwargs: Any) -> Any:
        text = text.replace("M0-WP14 Batch D", "M0-WP15 Batch E")
        text = text.replace("WP14 slot", "WP15 slot")
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
    image_draw = previous.base.ImageDraw
    original_draw = image_draw.Draw
    image_draw.Draw = lambda image: _DrawProxy(original_draw(image))
    try:
        paths, layout = PREVIOUS_RENDER_ATLAS(
            selection, inventory, raw_root, assets_dir, decisions
        )
    finally:
        image_draw.Draw = original_draw
    layout["status"] = "PASS_COMPLETE_176_PAIR_COVERAGE_TEXT_BOUNDS_AND_BBOX_CONTEXT"
    index_path = assets_dir / "index.html"
    index_text = index_path.read_text(encoding="utf-8")
    index_text = index_text.replace("M0-WP14", "M0-WP15").replace(
        "Batch D", "Batch E"
    )
    index_path.write_text(index_text, encoding="utf-8")
    return paths, layout


def summary_from_decisions(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    reviewed_count = sum(
        (
            EXPECTED_BATCH_A_COUNT,
            EXPECTED_BATCH_B_COUNT,
            EXPECTED_BATCH_C_COUNT,
            EXPECTED_BATCH_D_COUNT,
            EXPECTED_SELECTION_COUNT,
        )
    )
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
        "canonical_wp5_pending_unchanged": previous.base.EXPECTED_WP5_PENDING_COUNT,
        "pending_outside_wp7_wp12_overlays": previous.base.EXPECTED_WP5_PENDING_COUNT - reviewed_count,
        "cross_split_pending_outside_wp7_wp12_overlays": previous.base.EXPECTED_WP5_CROSS_SPLIT_COUNT - 5 - reviewed_count,
        "all_wp5_sequences_pending": previous.base.EXPECTED_WP5_SEQUENCE_COUNT,
        "d02_a_preferred": True,
        "d02_b_budget_approved": False,
        "final_group_truth_created": False,
        "split_assignment_created": False,
        "training_authorized": False,
        "gate0": "BLOCKED",
        "evidence_boundary": EVIDENCE_BOUNDARY,
    }


def validate_review_decision_contract(rows: list[dict[str, Any]]) -> None:
    capture_counts = Counter(row["capture_hypothesis"] for row in rows)
    physical_counts = Counter(row["physical_sign_hypothesis"] for row in rows)
    confidence_counts = Counter(row["confidence"] for row in rows)
    capture_unresolved = {row["edge_id"] for row in rows if row["capture_hypothesis"] == "UNRESOLVED"}
    physical_unresolved = {row["edge_id"] for row in rows if row["physical_sign_hypothesis"] == "UNRESOLVED"}
    capture_not_related = {row["edge_id"] for row in rows if row["capture_hypothesis"] == "NOT_RELATED"}
    physical_not_related = {row["edge_id"] for row in rows if row["physical_sign_hypothesis"] == "NOT_RELATED"}
    checks = (
        (dict(capture_counts), EXPECTED_CAPTURE_COUNTS, "capture decision counts"),
        (dict(physical_counts), EXPECTED_PHYSICAL_SIGN_COUNTS, "physical-sign decision counts"),
        (dict(confidence_counts), EXPECTED_CONFIDENCE_COUNTS, "confidence counts"),
        (capture_unresolved, EXPECTED_CAPTURE_UNRESOLVED_IDS, "capture UNRESOLVED edge IDs"),
        (physical_unresolved, EXPECTED_PHYSICAL_SIGN_UNRESOLVED_IDS, "physical-sign UNRESOLVED edge IDs"),
        (capture_not_related, EXPECTED_CAPTURE_NOT_RELATED_IDS, "capture NOT_RELATED edge IDs"),
        (physical_not_related, EXPECTED_PHYSICAL_SIGN_NOT_RELATED_IDS, "physical-sign NOT_RELATED edge IDs"),
    )
    for actual, expected, label in checks:
        if actual != expected:
            raise ValueError(f"WP15 {label} differ from approved PM review")


def render_report(summary: dict[str, Any], annotation_payload: dict[str, Any]) -> str:
    def counts(name: str) -> str:
        return "\n".join(f"- `{key}`: {value}" for key, value in summary[name].items())

    return f"""# M0-WP15 — D02-B cross-split manual review, Batch E

Status: `{PACKAGE_STATUS}`  
Boundary: `{EVIDENCE_BOUNDARY}`

This package records one PM/Codex provisional visual pass over the exact final 176 canonical WP5
pending cross-split pairs after the WP7/WP12/WP13/WP14 prefix. It does not approve D-02, create
final/transitive group truth or a split, or authorize training. D02-A metadata remains preferred.

## Selection and review protocol

- Selection: all remaining 176 unique canonical WP5 rows with `cross_split=True` and
  `review_status=PENDING`, preserving WP5 order and excluding exact prior-batch rosters.
- Selected edge range: `{summary['first_edge']}` through `{summary['last_edge']}`.
- Source coverage: 352 endpoint rows with {EXPECTED_SELECTED_ENDPOINT_BOX_COUNT} total boxes;
  quarantined stem `0248` is absent.
- Reviewer: `{annotation_payload['reviewer']}` at `{annotation_payload['reviewed_at']}`.
- All 176 pairs/352 raw frames were directly inspected in the dedicated 36-page WP15 atlas.
  Proxy fields were context only; identity metadata is unavailable.

## Hardened verifier contract

- Exact 37-file atlas roster; extra/missing/wrong-type/symlink/path attacks fail closed.
- Index, 36 JPEG pages and layout are regenerated in isolation and byte/deep-compared.
- Trusted review-notes SHA-256 `{EXPECTED_REVIEW_NOTES_SHA256}` pins exact outcomes and exceptional
  IDs. Coherent downstream rebuild cannot override the source anchor.

## Provisional capture outcomes

{counts('capture_hypothesis_counts')}

## Provisional physical-sign outcomes

{counts('physical_sign_hypothesis_counts')}

## Confidence

{counts('confidence_counts')}

## Remaining workload and governance

- Canonical WP5 remains unchanged at {summary['canonical_wp5_pending_unchanged']} PENDING edges.
- Outside the five overlays, {summary['pending_outside_wp7_wp12_overlays']} pending edges remain;
  {summary['cross_split_pending_outside_wp7_wp12_overlays']} are cross-split.
- All {summary['all_wp5_sequences_pending']} WP5 sequences remain PENDING; zero remaining cross-split
  rows does not resolve D-02 or replace reconciliation.
- D-02 remains PENDING; Gate 0 remains BLOCKED; `training_authorized=false`.

## Artifacts

- Decisions: `{ANNOTATIONS_RELATIVE_PATH}`.
- Selection: `{SELECTION_RELATIVE_PATH}`.
- Source lineage: `{LINEAGE_RELATIVE_PATH}`.
- Layout audit: `{LAYOUT_RELATIVE_PATH}`.
- Atlas: `{ASSETS_RELATIVE_PATH}/index.html` and {EXPECTED_PAGE_COUNT} JPEG pages.
- Manifest: `{MANIFEST_RELATIVE_PATH}`.
"""


def verify_manifest(manifest_path: Path, repo_root: Path, raw_root: Path) -> dict[str, Any]:
    base = previous.base
    Image = base.Image
    annotation_payload_from_notes = base.annotation_payload_from_notes
    artifact_contract = base.artifact_contract
    contract_pairs = base.contract_pairs
    derive_lineage = base.derive_lineage
    json = base.json
    load_annotations = base.load_annotations
    load_review_notes = base.load_review_notes
    read_csv = base.read_csv
    safe_child = base.safe_child
    sha256_file = base.sha256_file
    validate_governance = base.validate_governance
    validate_manifest_collection = base.validate_manifest_collection
    verify_raw_record = base.verify_raw_record
    verify_regenerated_atlas_and_layout = base.verify_regenerated_atlas_and_layout
    errors: list[str] = []
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        return {"valid": False, "errors": [f"manifest unreadable: {exc}"]}
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["manifest root must be an object"]}
    expected_top = {
        "schema_version", "package", "status", "evidence_boundary", "gate0",
        "canonical_wp5_mutated", "canonical_wp7_mutated", "final_group_truth_created",
        "transitive_grouping_created", "split_authorized", "training_authorized",
        "d02_status", "d02_a_preferred", "d02_b_budget_approved",
        "manifest_path", "manifest_self_in_artifact_count", "artifact_count_semantics",
        "selection_count", "lineage_record_count", "selected_endpoint_box_count",
        "quarantined_stem_0248_selected", "atlas_page_count", "source_count", "artifact_count",
        "total_artifact_bytes", "sources", "artifacts",
    }
    if set(payload) != expected_top:
        errors.append("manifest top-level fields differ from WP15 schema")
    constants = {
        "schema_version": 1,
        "package": BATCH_ID,
        "status": PACKAGE_STATUS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "gate0": "BLOCKED",
        "canonical_wp5_mutated": False,
        "canonical_wp7_mutated": False,
        "final_group_truth_created": False,
        "transitive_grouping_created": False,
        "split_authorized": False,
        "training_authorized": False,
        "d02_status": "PENDING",
        "d02_a_preferred": True,
        "d02_b_budget_approved": False,
        "manifest_path": MANIFEST_RELATIVE_PATH,
        "manifest_self_in_artifact_count": False,
        "artifact_count_semantics": "EXCLUDES_MANIFEST_FILE",
        "selection_count": EXPECTED_SELECTION_COUNT,
        "lineage_record_count": EXPECTED_SELECTION_COUNT * 2,
        "selected_endpoint_box_count": EXPECTED_SELECTED_ENDPOINT_BOX_COUNT,
        "quarantined_stem_0248_selected": False,
        "atlas_page_count": EXPECTED_PAGE_COUNT,
    }
    for field, expected_value in constants.items():
        if payload.get(field) != expected_value:
            errors.append(f"invalid manifest {field}")
    expected_sources = contract_pairs(source_contract(repo_root), repo_root)
    expected_artifacts = contract_pairs(artifact_contract(repo_root), repo_root)
    sources = validate_manifest_collection(payload, "sources", expected_sources, repo_root, errors)
    artifacts = validate_manifest_collection(payload, "artifacts", expected_artifacts, repo_root, errors)
    if payload.get("source_count") != len(expected_sources) or len(sources) != len(expected_sources):
        errors.append("source_count mismatch")
    if payload.get("artifact_count") != len(expected_artifacts) or len(artifacts) != len(expected_artifacts):
        errors.append("artifact_count mismatch")
    recorded_bytes = sum(
        record.get("size", -1)
        for record in artifacts
        if isinstance(record.get("size"), int) and not isinstance(record.get("size"), bool)
    )
    if payload.get("total_artifact_bytes") != recorded_bytes:
        errors.append("total_artifact_bytes mismatch")
    pinned = {item_id: digest for item_id, _path, digest in source_contract(repo_root)}
    for collection, records in (("sources", sources), ("artifacts", artifacts)):
        for record in records:
            path_value = record.get("path")
            if not isinstance(path_value, str):
                continue
            try:
                path = safe_child(repo_root, path_value)
            except (ValueError, OSError):
                continue
            if not path.is_file():
                errors.append(f"missing {collection} file: {path_value}")
            elif path.stat().st_size != record.get("size") or sha256_file(path) != record.get("sha256"):
                errors.append(f"tampered {collection} file: {path_value}")
            if collection == "sources" and pinned.get(record.get("id")) is not None:
                if record.get("sha256") != pinned[record["id"]]:
                    errors.append(f"pinned source hash mismatch: {record['id']}")
    if errors:
        return {"valid": False, "errors": errors, "source_count": len(sources), "artifact_count": len(artifacts)}
    try:
        validate_governance(repo_root)
        proof = json.loads(
            (repo_root / "results/data_audit/DATASET01_052bc980a7206f8d/source_preservation_proof.json").read_text(encoding="utf-8")
        )
        if proof.get("unchanged") is not True:
            raise ValueError("source preservation proof is not unchanged=true")
        expected_selection, inventory = derive_selection(repo_root, raw_root)
        actual_selection = read_csv(repo_root / SELECTION_RELATIVE_PATH)
        if actual_selection != expected_selection:
            raise ValueError("WP15 selection differs from independently derived canonical final 176")
        expected_lineage = derive_lineage(expected_selection, inventory, raw_root)
        actual_lineage = read_csv(repo_root / LINEAGE_RELATIVE_PATH)
        if actual_lineage != expected_lineage:
            raise ValueError("WP15 source lineage differs from the canonical 352 endpoints")
        annotation_payload, decisions = load_annotations(repo_root, expected_selection)
        layout = json.loads((repo_root / LAYOUT_RELATIVE_PATH).read_text(encoding="utf-8"))
        if (
            layout.get("schema_version") != 1
            or layout.get("status") != "PASS_COMPLETE_176_PAIR_COVERAGE_TEXT_BOUNDS_AND_BBOX_CONTEXT"
            or layout.get("evidence_boundary") != EVIDENCE_BOUNDARY
            or layout.get("page_count") != EXPECTED_PAGE_COUNT
            or layout.get("pair_count") != EXPECTED_SELECTION_COUNT
            or layout.get("pairs_per_page") != PAIRS_PER_PAGE
            or layout.get("all_headers_complete") is not True
            or layout.get("all_text_complete") is not True
            or layout.get("all_bounds_fit") is not True
            or layout.get("all_bbox_context_rendered") is not True
            or layout.get("all_decisions_recorded") is not True
            or not isinstance(layout.get("pages"), list)
            or len(layout["pages"]) != EXPECTED_PAGE_COUNT
        ):
            raise ValueError("WP15 layout audit contract mismatch")
        layout_ids: list[str] = []
        for page_number, page in enumerate(layout["pages"], start=1):
            expected_row_count = EXPECTED_PAGE_ROW_COUNTS[page_number - 1]
            if (
                page.get("page") != page_number
                or page.get("path") != f"{ASSETS_RELATIVE_PATH}/page_{page_number:03d}.jpg"
                or page.get("row_count") != expected_row_count
                or len(page.get("rows", [])) != expected_row_count
            ):
                raise ValueError(f"WP15 atlas page {page_number} identity/coverage mismatch")
            for slot, row in enumerate(page["rows"], start=1):
                expected = expected_selection[(page_number - 1) * PAIRS_PER_PAGE + slot - 1]
                if (
                    row.get("edge_id") != expected["edge_id"]
                    or row.get("batch_position") != int(expected["batch_position"])
                    or row.get("slot") != slot
                    or row.get("left_stem") != expected["left_stem"]
                    or row.get("right_stem") != expected["right_stem"]
                    or row.get("decision_recorded") is not True
                    or row.get("all_bounds_fit") is not True
                    or row.get("text_complete") is not True
                    or row.get("bbox_overlay_rendered") is not True
                ):
                    raise ValueError(f"WP15 atlas page/slot mismatch for {expected['edge_id']}")
                layout_ids.append(row["edge_id"])
        if layout_ids != [row["edge_id"] for row in expected_selection]:
            raise ValueError("WP15 layout order differs from canonical selection")
        regenerated_annotations = annotation_payload_from_notes(
            load_review_notes(repo_root, expected_selection), expected_selection
        )
        if annotation_payload != regenerated_annotations:
            raise ValueError("WP15 annotations differ from the bound PM visual-review notes")
        verify_regenerated_atlas_and_layout(
            repo_root,
            raw_root,
            expected_selection,
            inventory,
            decisions,
            layout,
        )
        for _item_id, page_path in artifact_contract(repo_root)[6:]:
            with Image.open(page_path) as image:
                image.verify()
        summary = summary_from_decisions(decisions)
        expected_report = render_report(summary, annotation_payload)
        if (repo_root / REPORT_RELATIVE_PATH).read_text(encoding="utf-8") != expected_report:
            raise ValueError("WP15 report differs from verified decisions/summary")
        forbidden = {"group_id", "final_group_id", "assigned_split", "approved_split"}
        if forbidden & set(actual_selection[0]):
            raise ValueError("WP15 selection contains final grouping/split fields")
        if any(forbidden & set(decision) for decision in decisions):
            raise ValueError("WP15 decisions contain final grouping/split fields")
        for row in expected_selection:
            verify_raw_record(inventory[row["left_stem"]], raw_root)
            verify_raw_record(inventory[row["right_stem"]], raw_root)
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        KeyError,
        OSError,
        TypeError,
        ValueError,
    ) as exc:
        errors.append(f"semantic verification failed: {exc}")
    return {
        "valid": not errors,
        "errors": errors,
        "source_count": len(sources),
        "artifact_count": len(artifacts),
        "status": payload.get("status"),
    }


def configure_previous() -> None:
    values = {
        "PACKAGE_STATUS": PACKAGE_STATUS,
        "ANNOTATION_STATUS": ANNOTATION_STATUS,
        "EVIDENCE_BOUNDARY": EVIDENCE_BOUNDARY,
        "BATCH_ID": BATCH_ID,
        "EXPECTED_SELECTION_COUNT": EXPECTED_SELECTION_COUNT,
        "EXPECTED_BATCH_A_COUNT": EXPECTED_BATCH_A_COUNT,
        "EXPECTED_BATCH_B_COUNT": EXPECTED_BATCH_B_COUNT,
        "EXPECTED_BATCH_C_COUNT": EXPECTED_BATCH_C_COUNT,
        "EXPECTED_BATCH_D_COUNT": EXPECTED_BATCH_D_COUNT,
        "EXPECTED_SELECTED_ENDPOINT_BOX_COUNT": EXPECTED_SELECTED_ENDPOINT_BOX_COUNT,
        "EXPECTED_PAGE_COUNT": EXPECTED_PAGE_COUNT,
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
    previous.base.verify_manifest = verify_manifest


def prepare(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    configure_previous()
    result = previous.prepare(repo_root, raw_root)
    result["status"] = "WP15_BATCH_E_PREPARED_AWAITING_PM_VISUAL_REVIEW"
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
    print(previous.base.json.dumps(result, indent=2, sort_keys=True))
    return 0 if args.command != "verify" or result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
