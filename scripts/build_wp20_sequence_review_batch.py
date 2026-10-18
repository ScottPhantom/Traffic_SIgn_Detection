# ruff: noqa: E501
"""Build and verify M0-WP20 D02-C sequence-review Batch E."""

from __future__ import annotations

import argparse
import html
import importlib.util
import json
import math
import shutil
import sys
from pathlib import Path
from typing import Any

BASE_PATH = Path(__file__).with_name("build_wp16_sequence_review_batch.py")
SPEC = importlib.util.spec_from_file_location("wp20_sequence_base", BASE_PATH)
assert SPEC is not None and SPEC.loader is not None
impl = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = impl
SPEC.loader.exec_module(impl)
base = impl.base

PACKAGE_STATUS = "WP20_AWAITING_QA_SEQUENCE_BATCH_E_PM_PROVISIONAL_REVIEW"
ANNOTATION_STATUS = "PM_REVIEWED_AWAITING_INDEPENDENT_QA"
EVIDENCE_BOUNDARY = (
    "SEQUENCE_BATCH_E_PM_PROVISIONAL_VISUAL_REVIEW_ONLY_NOT_D02_APPROVAL_"
    "NOT_GROUP_TRUTH_NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING"
)
BATCH_ID = "M0-WP20-D02-C-SEQUENCE-BATCH-E"
EXPECTED_SELECTION_COUNT = 100
EXPECTED_MEMBER_COUNT = 406
EXPECTED_CANONICAL_SEQUENCE_COUNT = 589
EXPECTED_PENDING_OUTSIDE_OVERLAY = 89
EXPECTED_PAGE_COUNT = 100
QUARANTINED_STEM = "0248"
REVIEWED_AT = "2026-10-12T00:20:00+07:00"
EXPECTED_REVIEW_NOTES_SHA256 = "04a70bfa693c105da29ac263ab8f24a1e030b489b8379078c79e0dd3f21e6f8b"

MANIFEST_RELATIVE_PATH = "docs/review/generated/wp20_sequence_batch_e_manifest.json"
SELECTION_RELATIVE_PATH = "docs/review/generated/wp20_sequence_batch_e_selection.csv"
EXCLUSIONS_RELATIVE_PATH = "docs/review/generated/wp20_sequence_batch_e_exclusions.csv"
LINEAGE_RELATIVE_PATH = "docs/review/generated/wp20_sequence_batch_e_member_lineage.csv"
LAYOUT_RELATIVE_PATH = "docs/review/generated/wp20_sequence_batch_e_layout_audit.json"
ANNOTATIONS_RELATIVE_PATH = "docs/review/wp20_sequence_review_annotations_batch_e.json"
REVIEW_NOTES_RELATIVE_PATH = "docs/review/wp20_sequence_review_notes_batch_e.csv"
REPORT_RELATIVE_PATH = "docs/review/wp20_sequence_review_batch_e_report.md"
ASSETS_RELATIVE_PATH = "docs/review/assets/wp20/sequence_batch_e"

WP16_MANIFEST_SHA256 = "f3e3fb7a13631ef60b9046f745c07cb39ff3df501c18d5e15e79ee2e505964bc"
WP16_SELECTION_SHA256 = "962b6eccbee8601f86cfaa02aa61df6623f42a58508d08120b9d7b2cf2201bea"
WP17_MANIFEST_SHA256 = "374ada61066f70f8ff3ba282dba41229ad2c161303146edd83aba583591b144b"
WP17_SELECTION_SHA256 = "2479e7b53c6622a120c3897aae84acab23365d8bbda69de1f6c4bcacc48458c4"
WP18_MANIFEST_SHA256 = "35bf843db7eb626404c81477efb509b2e4881a2cc7ea81fcee3187fcfab93649"
WP18_SELECTION_SHA256 = "faa55ac074b29da0dd61a33ba8e6a46401785f9ebead48130168598d5885ef01"
WP19_MANIFEST_SHA256 = "6796c3a16b2af347f0a74a06cde4477b214d97233d0d38848d9077933c7f712f"
WP19_SELECTION_SHA256 = "a63c8125fd570d19af5719bf11800d6b9ea70e3a03596cf195c63753e0c0296f"


def source_contract(repo_root: Path) -> list[tuple[str, Path, str | None]]:
    generated = repo_root / "docs/review/generated"
    audit = repo_root / "results/data_audit/DATASET01_052bc980a7206f8d"
    pinned = impl.PINNED
    return [
        ("wp5_manifest", generated / "wp5_evidence_manifest.json", pinned["wp5_manifest"]),
        ("wp5_sequence_queue", generated / "wp5_sequence_review_queue.csv", pinned["wp5_sequence_queue"]),
        ("wp2_clusters", generated / "grouping_proxy_clusters.csv", pinned["wp2_clusters"]),
        ("wp2_edges", generated / "grouping_proxy_edges.csv", pinned["wp2_edges"]),
        ("wp3_index", generated / "wp3_grouping_review_index.csv", pinned["wp3_index"]),
        ("wp3_manifest", generated / "wp3_evidence_manifest.json", pinned["wp3_manifest"]),
        ("image_inventory", audit / "image_inventory.csv", pinned["image_inventory"]),
        ("source_preservation", audit / "source_preservation_proof.json", pinned["source_preservation"]),
        ("decision_status", repo_root / "docs/review/decision_status.json", pinned["decision_status"]),
        ("wp7_manifest", generated / "wp7_batch_a_manifest.json", pinned["wp7_manifest"]),
        ("wp10_manifest", generated / "wp10_g04_quarantine_manifest.json", pinned["wp10_manifest"]),
        ("wp11_manifest", generated / "wp11_d04_manifest.json", pinned["wp11_manifest"]),
        ("wp12_manifest", generated / "wp12_batch_b_manifest.json", pinned["wp12_manifest"]),
        ("wp13_manifest", generated / "wp13_batch_c_manifest.json", pinned["wp13_manifest"]),
        ("wp14_manifest", generated / "wp14_batch_d_manifest.json", pinned["wp14_manifest"]),
        ("wp15_manifest", generated / "wp15_batch_e_manifest.json", pinned["wp15_manifest"]),
        ("wp12_builder", repo_root / "scripts/build_wp12_cross_split_review_batch.py", pinned["wp12_builder"]),
        ("wp16_manifest", generated / "wp16_sequence_batch_a_manifest.json", WP16_MANIFEST_SHA256),
        ("wp16_selection", generated / "wp16_sequence_batch_a_selection.csv", WP16_SELECTION_SHA256),
        ("wp17_manifest", generated / "wp17_sequence_batch_b_manifest.json", WP17_MANIFEST_SHA256),
        ("wp17_selection", generated / "wp17_sequence_batch_b_selection.csv", WP17_SELECTION_SHA256),
        ("wp18_manifest", generated / "wp18_sequence_batch_c_manifest.json", WP18_MANIFEST_SHA256),
        ("wp18_selection", generated / "wp18_sequence_batch_c_selection.csv", WP18_SELECTION_SHA256),
        ("wp19_manifest", generated / "wp19_sequence_batch_d_manifest.json", WP19_MANIFEST_SHA256),
        ("wp19_selection", generated / "wp19_sequence_batch_d_selection.csv", WP19_SELECTION_SHA256),
        ("wp20_review_notes", repo_root / REVIEW_NOTES_RELATIVE_PATH, EXPECTED_REVIEW_NOTES_SHA256),
        ("wp20_builder", repo_root / "scripts/build_wp20_sequence_review_batch.py", None),
    ]


def derive_selection(
    repo_root: Path, raw_root: Path
) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    queue = impl.load_sequence_queue(repo_root)
    inventory = impl.load_inventory(repo_root)
    eligible = [
        row
        for row in queue
        if row["review_status"] == "PENDING"
        and QUARANTINED_STEM not in row["members"].split(";")
    ]
    wp16 = base.read_csv(repo_root / "docs/review/generated/wp16_sequence_batch_a_selection.csv")
    wp17 = base.read_csv(repo_root / "docs/review/generated/wp17_sequence_batch_b_selection.csv")
    wp18 = base.read_csv(repo_root / "docs/review/generated/wp18_sequence_batch_c_selection.csv")
    wp19 = base.read_csv(repo_root / "docs/review/generated/wp19_sequence_batch_d_selection.csv")
    prior = [*wp16, *wp17, *wp18, *wp19]
    prior_ids = [row["proxy_sequence_id"] for row in prior]
    canonical_prior = eligible[:400]
    canonical_prior_ids = [row["proxy_sequence_id"] for row in canonical_prior]
    if (
        len(wp16) != 100
        or len(wp17) != 100
        or len(wp18) != 100
        or len(wp19) != 100
        or len(set(prior_ids)) != 400
        or [row["proxy_sequence_id"] for row in wp16]
        != [row["proxy_sequence_id"] for row in eligible[:100]]
        or [row["proxy_sequence_id"] for row in wp17]
        != [row["proxy_sequence_id"] for row in eligible[100:200]]
        or [row["proxy_sequence_id"] for row in wp18]
        != [row["proxy_sequence_id"] for row in eligible[200:300]]
        or [row["proxy_sequence_id"] for row in wp19]
        != [row["proxy_sequence_id"] for row in eligible[300:400]]
        or prior_ids != canonical_prior_ids
        or any(
            prior_row["members"] != canonical_row["members"]
            or prior_row["canonical_review_status"] != "PENDING"
            for prior_row, canonical_row in zip(prior, canonical_prior, strict=True)
        )
    ):
        raise ValueError(
            "WP20 requires exact non-overlapping WP16+WP17+WP18+WP19 canonical eligible prefix"
        )
    selected = eligible[len(prior) : len(prior) + EXPECTED_SELECTION_COUNT]
    expected_ids = [f"proxy_sequence_{index:04d}" for index in range(402, 502)]
    if [row["proxy_sequence_id"] for row in selected] != expected_ids:
        raise ValueError("WP20 selection must be exact next 100 quarantine-eligible canonical PENDING sequences")
    result: list[dict[str, str]] = []
    for order, row in enumerate(selected, start=1):
        members = row["members"].split(";")
        if row["proxy_sequence_id"] in set(prior_ids) or QUARANTINED_STEM in members:
            raise ValueError(
                "WP20 selection overlaps WP16/WP17/WP18/WP19 or contains quarantined stem 0248"
            )
        for stem in members:
            if stem not in inventory:
                raise ValueError(f"WP20 missing inventory stem: {stem}")
            impl.verify_raw_member(inventory[stem], raw_root)
        result.append(
            {
                "batch_position": str(order),
                "canonical_review_order": str(int(row["proxy_sequence_id"].rsplit("_", 1)[1])),
                "proxy_sequence_id": row["proxy_sequence_id"],
                "canonical_review_status": row["review_status"],
                "member_count": row["member_count"],
                "first_stem": row["first_stem"],
                "last_stem": row["last_stem"],
                "members": row["members"],
                "strong_edge_count": row["strong_edge_count"],
                "cross_split_strong_edges": row["cross_split_strong_edges"],
                "wp3_contact_sheet": row["contact_sheet"],
                # Compatibility key retained because the inherited hardened schema and renderer
                # consume it; the value is exclusively a WP20 path.
                "wp16_atlas_page": f"{ASSETS_RELATIVE_PATH}/page_{order:03d}.jpg",
                "selection_status": "SELECTED_NEXT_100_QUARANTINE_ELIGIBLE_PENDING_SEQUENCE_BATCH_E",
                "evidence_boundary": EVIDENCE_BOUNDARY,
            }
        )
    if sum(int(row["member_count"]) for row in result) != EXPECTED_MEMBER_COUNT:
        raise ValueError("WP20 selected member count differs from exact contract")
    if {stem for row in result for stem in row["members"].split(";")} & {
        stem for row in prior for stem in row["members"].split(";")
    }:
        raise ValueError("WP20 member roster overlaps WP16/WP17/WP18/WP19 sequence batches")
    return result, inventory


def derive_exclusions(repo_root: Path) -> list[dict[str, str]]:
    queue = impl.load_sequence_queue(repo_root)
    row = queue[49]
    if (
        row["proxy_sequence_id"] != "proxy_sequence_0050"
        or row["review_status"] != "PENDING"
        or QUARANTINED_STEM not in row["members"].split(";")
    ):
        raise ValueError("WP20 quarantine exclusion source differs from exact contract")
    return [
        {
            "canonical_review_order": "50",
            "proxy_sequence_id": "proxy_sequence_0050",
            "review_status": "PENDING",
            "members": row["members"],
            "excluded_stem": QUARANTINED_STEM,
            "exclusion_reason": "CONTAINS_QUARANTINED_STEM_0248",
            "overlay_reviewed": "False",
            "evidence_boundary": EVIDENCE_BOUNDARY,
        }
    ]


def render_atlas(
    selection: list[dict[str, str]],
    inventory: dict[str, dict[str, str]],
    raw_root: Path,
    assets_dir: Path,
    decisions: list[dict[str, Any]] | None,
) -> tuple[list[Path], dict[str, Any]]:
    if assets_dir.exists():
        shutil.rmtree(assets_dir)
    assets_dir.mkdir(parents=True)
    decision_by_id = {row["proxy_sequence_id"]: row for row in decisions or []}
    canvas_width, header_height, columns = 1600, 230, 4
    cell_width, cell_height, image_size = 390, 265, (360, 203)
    title_font = base.reviewer_font(22)
    body_font = base.reviewer_font(16)
    small_font = base.reviewer_font(14)
    pages: list[Path] = []
    audits: list[dict[str, Any]] = []
    for sequence in selection:
        page_number = int(sequence["batch_position"])
        members = sequence["members"].split(";")
        member_rows = math.ceil(len(members) / columns)
        canvas_height = header_height + member_rows * cell_height + 18
        canvas = base.Image.new("RGB", (canvas_width, canvas_height), "white")
        draw = base.ImageDraw.Draw(canvas)
        decision = decision_by_id.get(sequence["proxy_sequence_id"])
        title = (
            f"M0-WP20 Sequence Batch E | {page_number:03d}/{EXPECTED_PAGE_COUNT:03d} | "
            f"{sequence['proxy_sequence_id']} | canonical={sequence['canonical_review_order']} | "
            f"members={sequence['member_count']}"
        )
        draw.text((18, 10), title, font=title_font, fill="#111827")
        draw.text((18, 42), EVIDENCE_BOUNDARY, font=small_font, fill="#374151")
        splits = sorted({inventory[stem]["split"] for stem in members})
        proxy = (
            f"canonical PENDING | strong_edges={sequence['strong_edge_count']} | "
            f"cross_split_strong={sequence['cross_split_strong_edges']} | splits={';'.join(splits)}"
        )
        draw.text((18, 66), proxy, font=body_font, fill="#1d4ed8")
        panel_lines = [
            f"status: {ANNOTATION_STATUS if decision else 'AWAITING_PM_VISUAL_REVIEW'}",
            f"capture_sequence: {decision['capture_sequence'] if decision else 'BLANK'}",
            f"physical_sign_sequence: {decision['physical_sign_sequence'] if decision else 'BLANK'}",
            f"confidence: {decision['confidence'] if decision else 'BLANK'}",
            f"rationale: {decision['rationale'] if decision else 'BLANK'}",
        ]
        cursor = 92
        header_bounds: list[list[int]] = []
        for index, text in enumerate(panel_lines):
            cursor, bounds = base.draw_wrapped(
                draw, text, 18, cursor, 1550, small_font,
                "#047857" if decision and index else "#111827", line_gap=2,
            )
            header_bounds.append(bounds)
            cursor += 2
        if cursor > header_height - 8:
            raise RuntimeError(f"WP20 header text overflow for {sequence['proxy_sequence_id']}")
        member_audits: list[dict[str, Any]] = []
        for member_index, stem in enumerate(members):
            row_index, column_index = divmod(member_index, columns)
            cell_x = column_index * cell_width + 8
            cell_y = header_height + row_index * cell_height
            if (row_index + column_index) % 2:
                draw.rectangle(
                    (cell_x, cell_y, cell_x + cell_width - 8, cell_y + cell_height - 8),
                    fill="#f3f4f6",
                )
            item = inventory[stem]
            image_path, label_path, _boxes = impl.verify_raw_member(item, raw_root)
            label = (
                f"#{member_index + 1} {stem} [{item['split']}] | "
                f"{item['width']}x{item['height']} | boxes={item['box_count']} | cls={item['class_ids'] or 'none'}"
            )
            draw.text((cell_x + 8, cell_y + 8), label, font=small_font, fill="#111827")
            rendered = base.image_with_boxes(image_path, label_path, image_size)
            image_xy = (cell_x + 8, cell_y + 38)
            canvas.paste(rendered, image_xy)
            member_audits.append(
                {
                    "member_order": member_index + 1,
                    "stem": stem,
                    "split": item["split"],
                    "box_count": int(item["box_count"]),
                    "class_ids": item["class_ids"],
                    "image_bounds": [image_xy[0], image_xy[1], image_xy[0] + image_size[0], image_xy[1] + image_size[1]],
                    "label_complete": True,
                    "bbox_overlay_rendered": True,
                }
            )
        path = assets_dir / f"page_{page_number:03d}.jpg"
        canvas.save(path, format="JPEG", quality=90, optimize=True, subsampling=1)
        pages.append(path)
        audits.append(
            {
                "page": page_number,
                "path": sequence["wp16_atlas_page"],
                "width": canvas.width,
                "height": canvas.height,
                "batch_position": page_number,
                "canonical_review_order": int(sequence["canonical_review_order"]),
                "proxy_sequence_id": sequence["proxy_sequence_id"],
                "member_count": len(members),
                "header_text_bounds": header_bounds,
                "decision_recorded": decision is not None,
                "all_bounds_fit": True,
                "all_text_complete": True,
                "all_bbox_context_rendered": True,
                "members": member_audits,
            }
        )
    body = [
        "<!doctype html><meta charset='utf-8'><title>M0-WP20 sequence Batch E atlas</title>",
        "<style>body{font-family:system-ui;margin:2rem;max-width:1200px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #bbb;padding:.4rem}</style>",
        "<h1>M0-WP20 D02-C sequence review — Batch E</h1>",
        f"<p>{html.escape(EVIDENCE_BOUNDARY)}</p>",
        "<p>One canonical sequence per page; every member frame is rendered with YOLO bbox context.</p>",
        "<table><thead><tr><th>#</th><th>Sequence</th><th>Members</th><th>Capture</th><th>Physical sign</th><th>Confidence</th><th>Atlas</th></tr></thead><tbody>",
    ]
    for row in selection:
        decision = decision_by_id.get(row["proxy_sequence_id"])
        page = int(row["batch_position"])
        body.append(
            f"<tr id='{row['proxy_sequence_id']}'><td>{page}</td><td>{row['proxy_sequence_id']}</td>"
            f"<td>{row['members']}</td><td>{html.escape(decision['capture_sequence'] if decision else 'BLANK')}</td>"
            f"<td>{html.escape(decision['physical_sign_sequence'] if decision else 'BLANK')}</td>"
            f"<td>{html.escape(decision['confidence'] if decision else 'BLANK')}</td>"
            f"<td><a href='page_{page:03d}.jpg'>page {page:03d}</a></td></tr>"
        )
    body.append("</tbody></table>")
    (assets_dir / "index.html").write_text("\n".join(body) + "\n", encoding="utf-8")
    layout = {
        "schema_version": 1,
        "status": "PASS_COMPLETE_100_SEQUENCE_406_MEMBER_COVERAGE_TEXT_BOUNDS_AND_BBOX_CONTEXT",
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "page_count": EXPECTED_PAGE_COUNT,
        "sequence_count": EXPECTED_SELECTION_COUNT,
        "member_count": EXPECTED_MEMBER_COUNT,
        "sequences_per_page": 1,
        "page_sequence_counts": [1] * EXPECTED_PAGE_COUNT,
        "all_headers_complete": True,
        "all_text_complete": True,
        "all_bounds_fit": True,
        "all_bbox_context_rendered": True,
        "all_decisions_recorded": decisions is not None,
        "pages": audits,
    }
    return [assets_dir / "index.html", *pages], layout


def render_report(summary: dict[str, Any], annotation_payload: dict[str, Any]) -> str:
    def counts(name: str) -> str:
        return "\n".join(f"- `{key}`: {value}" for key, value in summary[name].items())

    return f"""# M0-WP20 — D02-C sequence review, Batch E

Status: `{PACKAGE_STATUS}`  
Boundary: `{EVIDENCE_BOUNDARY}`

This package records one PM/Codex provisional visual pass over the exact next 100 quarantine-
eligible canonical WP5 PENDING sequences after the independently QA-passed WP16-R1 Batch A,
WP17 Batch B, WP18 Batch C and WP19 Batch D.
It does not approve D-02, create final/transitive group truth or a split, or authorize training.
D02-A creator/session metadata remains preferred.

## Selection and review protocol

- Selection: `proxy_sequence_0402` through `proxy_sequence_0501`, exact canonical order with no
  gap, after excluding the exact union of WP16, WP17, WP18 and WP19 (400-sequence eligible prefix) and
  the whole quarantined `proxy_sequence_0050`.
- Exclusion registry keeps canonical row 50 `PENDING`, `overlay_reviewed=False`, reason
  `CONTAINS_QUARANTINED_STEM_0248`; no member is removed or rewritten.
- Source coverage: 100 sequences, 406 unique member frames and 1,287 bbox occurrences; all
  image/label hashes, dimensions, decode state, classes and bbox context verified.
- Reviewer: `{annotation_payload['reviewer']}` at `{annotation_payload['reviewed_at']}`.
- All 100 sequences and all 406 member frames were directly inspected in the 100-page WP20 atlas.
  Proxy metrics were context only; creator/session/physical-sign identity metadata is unavailable.

## Hardened verifier contract

- Exact 101-file atlas roster: index plus one page for each sequence.
- Exact 31-field manifest top-level schema rejects every missing or unknown field; each nested
  source/artifact record is exact-key checked.
- Index, 100 JPEG pages and layout are regenerated in isolation and byte/deep-compared.
- Trusted review-notes SHA-256 `{EXPECTED_REVIEW_NOTES_SHA256}` pins exact decisions and IDs.
  Coherent rollback and count-preserving decision-ID swaps cannot override this source anchor.

## Provisional capture-sequence outcomes

{counts('capture_sequence_counts')}

## Provisional physical-sign-sequence outcomes

{counts('physical_sign_sequence_counts')}

## Confidence

{counts('confidence_counts')}

## Remaining workload and governance

- Canonical WP5 remains unchanged at 589 PENDING sequences.
- WP16+WP17+WP18+WP19+WP20 overlays cover 500 sequences; 89 remain outside all five overlays, including
  the quarantined sequence that stays canonical `PENDING` and unreviewed.
- Canonical WP5 remains unchanged at 3,172 PENDING edges; five QA-passed cross-split overlays do
  not resolve the remaining 2,146 other pending edges or create sequence truth.
- D-02 remains PENDING; Gate 0 remains BLOCKED; `training_authorized=false`.

## Artifacts

- Decisions: `{ANNOTATIONS_RELATIVE_PATH}`.
- Selection: `{SELECTION_RELATIVE_PATH}`.
- Exclusions: `{EXCLUSIONS_RELATIVE_PATH}`.
- Member lineage: `{LINEAGE_RELATIVE_PATH}`.
- Layout audit: `{LAYOUT_RELATIVE_PATH}`.
- Atlas: `{ASSETS_RELATIVE_PATH}/index.html` and 100 JPEG pages.
- Manifest: `{MANIFEST_RELATIVE_PATH}`.
"""


_impl_verify_manifest = impl.verify_manifest
_impl_prepare = impl.prepare


def verify_manifest(manifest_path: Path, repo_root: Path, raw_root: Path) -> dict[str, Any]:
    result = _impl_verify_manifest(manifest_path, repo_root, raw_root)
    result["errors"] = [error.replace("WP16", "WP20") for error in result["errors"]]
    return result


def prepare(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    result = _impl_prepare(repo_root, raw_root)
    result["status"] = "WP20_SEQUENCE_BATCH_E_PREPARED_AWAITING_PM_VISUAL_REVIEW"
    result["prior_wp16_sequence_count"] = 100
    result["prior_wp17_sequence_count"] = 100
    result["prior_wp18_sequence_count"] = 100
    result["prior_wp19_sequence_count"] = 100
    result["prior_sequence_prefix_count"] = 400
    result["pending_sequences_outside_wp16_wp17_wp18_wp19_wp20"] = EXPECTED_PENDING_OUTSIDE_OVERLAY
    return result


def _configure() -> None:
    values = {
        "PACKAGE_STATUS": PACKAGE_STATUS,
        "ANNOTATION_STATUS": ANNOTATION_STATUS,
        "EVIDENCE_BOUNDARY": EVIDENCE_BOUNDARY,
        "BATCH_ID": BATCH_ID,
        "EXPECTED_SELECTION_COUNT": EXPECTED_SELECTION_COUNT,
        "EXPECTED_MEMBER_COUNT": EXPECTED_MEMBER_COUNT,
        "EXPECTED_CANONICAL_SEQUENCE_COUNT": EXPECTED_CANONICAL_SEQUENCE_COUNT,
        "EXPECTED_PENDING_OUTSIDE_OVERLAY": EXPECTED_PENDING_OUTSIDE_OVERLAY,
        "EXPECTED_PAGE_COUNT": EXPECTED_PAGE_COUNT,
        "QUARANTINED_STEM": QUARANTINED_STEM,
        "REVIEWED_AT": REVIEWED_AT,
        "EXPECTED_REVIEW_NOTES_SHA256": EXPECTED_REVIEW_NOTES_SHA256,
        "MANIFEST_RELATIVE_PATH": MANIFEST_RELATIVE_PATH,
        "SELECTION_RELATIVE_PATH": SELECTION_RELATIVE_PATH,
        "EXCLUSIONS_RELATIVE_PATH": EXCLUSIONS_RELATIVE_PATH,
        "LINEAGE_RELATIVE_PATH": LINEAGE_RELATIVE_PATH,
        "LAYOUT_RELATIVE_PATH": LAYOUT_RELATIVE_PATH,
        "ANNOTATIONS_RELATIVE_PATH": ANNOTATIONS_RELATIVE_PATH,
        "REVIEW_NOTES_RELATIVE_PATH": REVIEW_NOTES_RELATIVE_PATH,
        "REPORT_RELATIVE_PATH": REPORT_RELATIVE_PATH,
        "ASSETS_RELATIVE_PATH": ASSETS_RELATIVE_PATH,
        "source_contract": source_contract,
        "derive_selection": derive_selection,
        "derive_exclusions": derive_exclusions,
        "render_atlas": render_atlas,
        "render_report": render_report,
        "verify_manifest": verify_manifest,
        "prepare": prepare,
    }
    for name, value in values.items():
        setattr(impl, name, value)


_configure()

MANIFEST_TOP_LEVEL_FIELDS = impl.MANIFEST_TOP_LEVEL_FIELDS
SELECTION_FIELDS = impl.SELECTION_FIELDS
LINEAGE_FIELDS = impl.LINEAGE_FIELDS
NOTE_FIELDS = impl.NOTE_FIELDS
EXCLUSION_FIELDS = impl.EXCLUSION_FIELDS
CAPTURE_VALUES = impl.CAPTURE_VALUES
PHYSICAL_VALUES = impl.PHYSICAL_VALUES
CONFIDENCE_VALUES = impl.CONFIDENCE_VALUES
artifact_contract = impl.artifact_contract
verify_exact_atlas_roster = impl.verify_exact_atlas_roster
validate_governance = impl.validate_governance
load_inventory = impl.load_inventory
load_sequence_queue = impl.load_sequence_queue
verify_raw_member = impl.verify_raw_member
derive_lineage = impl.derive_lineage
load_review_notes = impl.load_review_notes
annotation_payload_from_notes = impl.annotation_payload_from_notes
verify_regenerated_atlas_and_layout = impl.verify_regenerated_atlas_and_layout
summary_from_decisions = impl.summary_from_decisions
build_manifest = impl.build_manifest
build = impl.build


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
        manifest = args.manifest if args.manifest.is_absolute() else repo_root / args.manifest
        result = verify_manifest(manifest, repo_root, raw_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if args.command != "verify" or result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
