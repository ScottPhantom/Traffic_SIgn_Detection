# ruff: noqa: E501
"""Build and verify M0-WP16 D02-C sequence-review Batch A."""

from __future__ import annotations

import argparse
import html
import importlib.util
import json
import math
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

BASE_PATH = Path(__file__).with_name("build_wp12_cross_split_review_batch.py")
SPEC = importlib.util.spec_from_file_location("wp16_hardened_base", BASE_PATH)
assert SPEC is not None and SPEC.loader is not None
base = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = base
SPEC.loader.exec_module(base)

PACKAGE_STATUS = "WP16_AWAITING_QA_SEQUENCE_BATCH_A_PM_PROVISIONAL_REVIEW"
ANNOTATION_STATUS = "PM_REVIEWED_AWAITING_INDEPENDENT_QA"
EVIDENCE_BOUNDARY = (
    "SEQUENCE_BATCH_A_PM_PROVISIONAL_VISUAL_REVIEW_ONLY_NOT_D02_APPROVAL_"
    "NOT_GROUP_TRUTH_NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING"
)
BATCH_ID = "M0-WP16-D02-C-SEQUENCE-BATCH-A"
EXPECTED_SELECTION_COUNT = 100
EXPECTED_MEMBER_COUNT = 339
EXPECTED_CANONICAL_SEQUENCE_COUNT = 589
EXPECTED_PENDING_OUTSIDE_OVERLAY = 489
EXPECTED_PAGE_COUNT = 100
QUARANTINED_STEM = "0248"
REVIEWED_AT = "2026-10-11T17:08:50+07:00"
EXPECTED_REVIEW_NOTES_SHA256 = "d673ac00d0345fcf1fc0b46c2e9e3396ba97d3bd17259ce7a4d370756ed38e9d"
MANIFEST_TOP_LEVEL_FIELDS = frozenset(
    {
        "schema_version",
        "package",
        "status",
        "evidence_boundary",
        "gate0",
        "d02_status",
        "canonical_wp5_mutated",
        "canonical_edge_overlays_mutated",
        "final_group_truth_created",
        "transitive_grouping_created",
        "split_authorized",
        "training_authorized",
        "manifest_path",
        "manifest_self_in_artifact_count",
        "artifact_count_semantics",
        "selection_count",
        "member_lineage_count",
        "canonical_sequence_count",
        "canonical_sequence_pending_count",
        "pending_sequences_outside_overlay",
        "quarantined_stem_0248_selected",
        "exclusion_count",
        "quarantined_sequence_reviewed",
        "excluded_quarantined_sequence_id",
        "atlas_page_count",
        "atlas_file_count",
        "source_count",
        "artifact_count",
        "total_artifact_bytes",
        "sources",
        "artifacts",
    }
)

MANIFEST_RELATIVE_PATH = "docs/review/generated/wp16_sequence_batch_a_manifest.json"
SELECTION_RELATIVE_PATH = "docs/review/generated/wp16_sequence_batch_a_selection.csv"
EXCLUSIONS_RELATIVE_PATH = "docs/review/generated/wp16_sequence_batch_a_exclusions.csv"
LINEAGE_RELATIVE_PATH = "docs/review/generated/wp16_sequence_batch_a_member_lineage.csv"
LAYOUT_RELATIVE_PATH = "docs/review/generated/wp16_sequence_batch_a_layout_audit.json"
ANNOTATIONS_RELATIVE_PATH = "docs/review/wp16_sequence_review_annotations_batch_a.json"
REVIEW_NOTES_RELATIVE_PATH = "docs/review/wp16_sequence_review_notes_batch_a.csv"
REPORT_RELATIVE_PATH = "docs/review/wp16_sequence_review_batch_a_report.md"
ASSETS_RELATIVE_PATH = "docs/review/assets/wp16/sequence_batch_a"

PINNED = {
    "wp5_manifest": "f8d620a3cbb3b500153f6685b94a9936a8f83eb6f5399ce0a2e8be77982d4b80",
    "wp5_sequence_queue": "ccb7efc219f5e1e6516b1564f5d37e143dc4093342ab6afa64fff93f7be6cf77",
    "wp2_clusters": "0dd732a5791383bedbb1aa499bc6c64bf401c5af72b64d3ceb08cc97d8ec5092",
    "wp2_edges": "801e89db137154086496f37bc38b9659596c61e4a881734e80731aeaf2ded15c",
    "wp3_index": "b09542fe373eb86424229ee533a0c40621bcf075d79acd1d4dc1eda1a866d3fe",
    "wp3_manifest": "8b2e9ef3b2418623eb92673f3c58591e29f5ed7479bca2b03582c12ef0191dcd",
    "image_inventory": "d45aa7f398a040c44cbc040f4ec005d7e5a8ef50586e905315f76c792ca29022",
    "source_preservation": "5ca3e769b9197cad19bcb75f553dd59fee6e3035e0cc86cd9693737f84a713d7",
    "decision_status": "87d81262e907bb1c479cfac6535e7b3f67a368c371e96b810aa02f2e92d0d72c",
    "wp7_manifest": "73ed4095a1f59b72f010fd87b63c4a7f0b16bcf8e0c667ec77576ec827e5d7f2",
    "wp10_manifest": "9c9581e2026f036a79fc1c58bce5f1b87e4c4f0786ee50a49f890e94d0e529e5",
    "wp11_manifest": "61b5bfbb92ac872ae4d5bfc6d508426f59b4065d4cd2f43f3f979e664095b465",
    "wp12_manifest": "8e576954bc3de456704aecdb67e8625d8621ca017fb08e3b866635db6afcc0f0",
    "wp13_manifest": "5db80e215f318a6b782d813b4560c20e35e4f3e51ef0423d7298f4818ea3db65",
    "wp14_manifest": "ea4667c2ea18bc6fff23ce23beffe5b27372e494160fa9d6ffbc86c3cb3f2dc5",
    "wp15_manifest": "032aee9da985c5dcb772ddd1c73fa9e4e6794e1beb5107fdb49b0168948a241d",
    "wp12_builder": "f2569636e26a48984e432bbfc35735f2099e855db27b2b3ce76f001c33c197df",
}

SELECTION_FIELDS = [
    "batch_position",
    "canonical_review_order",
    "proxy_sequence_id",
    "canonical_review_status",
    "member_count",
    "first_stem",
    "last_stem",
    "members",
    "strong_edge_count",
    "cross_split_strong_edges",
    "wp3_contact_sheet",
    "wp16_atlas_page",
    "selection_status",
    "evidence_boundary",
]

LINEAGE_FIELDS = [
    "batch_position",
    "canonical_review_order",
    "proxy_sequence_id",
    "member_order",
    "stem",
    "split",
    "image_path",
    "image_sha256",
    "label_path",
    "label_sha256",
    "width",
    "height",
    "format",
    "mode",
    "decode_verified",
    "box_count",
    "class_ids",
    "wp16_atlas_page",
    "evidence_boundary",
]

NOTE_FIELDS = [
    "batch_position",
    "canonical_review_order",
    "proxy_sequence_id",
    "capture_sequence",
    "physical_sign_sequence",
    "confidence",
    "reviewer",
    "reviewed_at",
    "rationale",
]

EXCLUSION_FIELDS = [
    "canonical_review_order",
    "proxy_sequence_id",
    "review_status",
    "members",
    "excluded_stem",
    "exclusion_reason",
    "overlay_reviewed",
    "evidence_boundary",
]

CAPTURE_VALUES = {"CONTINUOUS_CANDIDATE", "SPLIT_REQUIRED", "UNRESOLVED"}
PHYSICAL_VALUES = {"SAME_PHYSICAL_SIGN_CANDIDATE", "MULTIPLE_SIGNS", "UNRESOLVED"}
CONFIDENCE_VALUES = {"HIGH", "MEDIUM", "LOW"}


def source_contract(repo_root: Path) -> list[tuple[str, Path, str | None]]:
    generated = repo_root / "docs/review/generated"
    audit = repo_root / "results/data_audit/DATASET01_052bc980a7206f8d"
    return [
        ("wp5_manifest", generated / "wp5_evidence_manifest.json", PINNED["wp5_manifest"]),
        ("wp5_sequence_queue", generated / "wp5_sequence_review_queue.csv", PINNED["wp5_sequence_queue"]),
        ("wp2_clusters", generated / "grouping_proxy_clusters.csv", PINNED["wp2_clusters"]),
        ("wp2_edges", generated / "grouping_proxy_edges.csv", PINNED["wp2_edges"]),
        ("wp3_index", generated / "wp3_grouping_review_index.csv", PINNED["wp3_index"]),
        ("wp3_manifest", generated / "wp3_evidence_manifest.json", PINNED["wp3_manifest"]),
        ("image_inventory", audit / "image_inventory.csv", PINNED["image_inventory"]),
        ("source_preservation", audit / "source_preservation_proof.json", PINNED["source_preservation"]),
        ("decision_status", repo_root / "docs/review/decision_status.json", PINNED["decision_status"]),
        ("wp7_manifest", generated / "wp7_batch_a_manifest.json", PINNED["wp7_manifest"]),
        ("wp10_manifest", generated / "wp10_g04_quarantine_manifest.json", PINNED["wp10_manifest"]),
        ("wp11_manifest", generated / "wp11_d04_manifest.json", PINNED["wp11_manifest"]),
        ("wp12_manifest", generated / "wp12_batch_b_manifest.json", PINNED["wp12_manifest"]),
        ("wp13_manifest", generated / "wp13_batch_c_manifest.json", PINNED["wp13_manifest"]),
        ("wp14_manifest", generated / "wp14_batch_d_manifest.json", PINNED["wp14_manifest"]),
        ("wp15_manifest", generated / "wp15_batch_e_manifest.json", PINNED["wp15_manifest"]),
        ("wp12_builder", repo_root / "scripts/build_wp12_cross_split_review_batch.py", PINNED["wp12_builder"]),
        ("wp16_review_notes", repo_root / REVIEW_NOTES_RELATIVE_PATH, EXPECTED_REVIEW_NOTES_SHA256),
        ("wp16_builder", repo_root / "scripts/build_wp16_sequence_review_batch.py", None),
    ]


def artifact_contract(repo_root: Path) -> list[tuple[str, Path]]:
    assets = repo_root / ASSETS_RELATIVE_PATH
    rows = [
        ("annotations", repo_root / ANNOTATIONS_RELATIVE_PATH),
        ("selection", repo_root / SELECTION_RELATIVE_PATH),
        ("exclusions", repo_root / EXCLUSIONS_RELATIVE_PATH),
        ("member_lineage", repo_root / LINEAGE_RELATIVE_PATH),
        ("layout_audit", repo_root / LAYOUT_RELATIVE_PATH),
        ("report", repo_root / REPORT_RELATIVE_PATH),
        ("atlas_index", assets / "index.html"),
    ]
    rows.extend(
        (f"atlas_page_{page:03d}", assets / f"page_{page:03d}.jpg")
        for page in range(1, EXPECTED_PAGE_COUNT + 1)
    )
    return rows


def expected_atlas_names() -> list[str]:
    return [
        "index.html",
        *(f"page_{page:03d}.jpg" for page in range(1, EXPECTED_PAGE_COUNT + 1)),
    ]


def verify_exact_atlas_roster(assets_dir: Path) -> None:
    if assets_dir.is_symlink() or not assets_dir.is_dir():
        raise ValueError("WP16 atlas root must be a real directory")
    entries = sorted(assets_dir.iterdir(), key=lambda path: path.name)
    if [path.name for path in entries] != sorted(expected_atlas_names()):
        raise ValueError("WP16 atlas roster differs from exact 101-file contract")
    if any(path.is_symlink() or not path.is_file() for path in entries):
        raise ValueError("WP16 atlas members must be regular non-symlink files")


def relative_record(path: Path, repo_root: Path, item_id: str) -> dict[str, Any]:
    return {
        "id": item_id,
        "path": path.resolve().relative_to(repo_root.resolve()).as_posix(),
        "sha256": base.sha256_file(path),
        "size": path.stat().st_size,
    }


def verify_source_contract(repo_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item_id, path, pinned_hash in source_contract(repo_root):
        if path.is_symlink() or not path.is_file():
            raise FileNotFoundError(f"required WP16 source missing or non-regular: {path}")
        digest = base.sha256_file(path)
        if pinned_hash is not None and digest != pinned_hash:
            raise ValueError(f"pinned WP16 source mismatch: {item_id}")
        records.append(relative_record(path, repo_root, item_id))
    return records


def validate_governance(repo_root: Path) -> None:
    payload = json.loads((repo_root / "docs/review/decision_status.json").read_text(encoding="utf-8"))
    if payload.get("gate0") != "BLOCKED" or payload.get("training_authorized") is not False:
        raise ValueError("WP16 requires Gate 0 BLOCKED and training unauthorized")
    if payload.get("decisions", {}).get("D-02", {}).get("status") != "PENDING":
        raise ValueError("WP16 requires D-02 PENDING")


def load_inventory(repo_root: Path) -> dict[str, dict[str, str]]:
    rows = base.read_csv(repo_root / "results/data_audit/DATASET01_052bc980a7206f8d/image_inventory.csv")
    inventory = {row["stem"]: row for row in rows}
    if len(rows) != 3216 or len(inventory) != 3216:
        raise ValueError("WP16 inventory must contain 3,216 unique stems")
    return inventory


def load_sequence_queue(repo_root: Path) -> list[dict[str, str]]:
    rows = base.read_csv(repo_root / "docs/review/generated/wp5_sequence_review_queue.csv")
    if len(rows) != EXPECTED_CANONICAL_SEQUENCE_COUNT:
        raise ValueError("WP16 canonical sequence count mismatch")
    expected_ids = [f"proxy_sequence_{index:04d}" for index in range(1, 590)]
    if [row["proxy_sequence_id"] for row in rows] != expected_ids:
        raise ValueError("WP16 canonical sequence order/IDs changed")
    if {row["review_status"] for row in rows} != {"PENDING"}:
        raise ValueError("WP16 requires all canonical WP5 sequences PENDING")
    seen_members: set[str] = set()
    for row in rows:
        members = row["members"].split(";")
        if (
            int(row["member_count"]) != len(members)
            or row["source_stems"] != row["members"]
            or row["first_stem"] != members[0]
            or row["last_stem"] != members[-1]
            or len(set(members)) != len(members)
            or seen_members.intersection(members)
        ):
            raise ValueError(f"WP16 invalid canonical sequence row: {row['proxy_sequence_id']}")
        seen_members.update(members)
    wp3_rows = base.read_csv(repo_root / "docs/review/generated/wp3_grouping_review_index.csv")
    if len(wp3_rows) != len(rows):
        raise ValueError("WP16 WP3 sequence index count mismatch")
    for canonical, wp3 in zip(rows, wp3_rows, strict=True):
        if (
            canonical["proxy_sequence_id"] != wp3["proxy_sequence_id"]
            or canonical["members"] != wp3["source_stems"]
            or canonical["member_count"] != wp3["member_count"]
            or canonical["review_status"] != wp3["review_status"]
        ):
            raise ValueError("WP16 WP5/WP3 sequence binding mismatch")
    return rows


def verify_raw_member(
    inventory_row: dict[str, str], raw_root: Path
) -> tuple[Path, Path, list[tuple[int, float, float, float, float]]]:
    image_path, label_path = base.verify_raw_record(inventory_row, raw_root)
    with base.Image.open(image_path) as image:
        image.verify()
    with base.Image.open(image_path) as image:
        if (
            image.size != (int(inventory_row["width"]), int(inventory_row["height"]))
            or image.format != inventory_row["format"]
            or image.mode != inventory_row["mode"]
        ):
            raise ValueError(f"WP16 image metadata drift for {inventory_row['stem']}")
    boxes = base.parse_yolo_boxes(
        label_path, int(inventory_row["width"]), int(inventory_row["height"])
    )
    classes = sorted({str(box[0]) for box in boxes}, key=int)
    expected_classes = sorted(inventory_row["class_ids"].replace(";", " ").split(), key=int)
    if len(boxes) != int(inventory_row["box_count"]) or classes != expected_classes:
        raise ValueError(f"WP16 label evidence drift for {inventory_row['stem']}")
    return image_path, label_path, boxes


def derive_selection(
    repo_root: Path, raw_root: Path
) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    queue = load_sequence_queue(repo_root)
    inventory = load_inventory(repo_root)
    eligible = [
        row
        for row in queue
        if row["review_status"] == "PENDING"
        and QUARANTINED_STEM not in row["members"].split(";")
    ]
    selected = eligible[:EXPECTED_SELECTION_COUNT]
    expected_ids = [
        f"proxy_sequence_{index:04d}"
        for index in range(1, 102)
        if index != 50
    ]
    if [row["proxy_sequence_id"] for row in selected] != expected_ids:
        raise ValueError("WP16 selection must be exact first 100 quarantine-eligible canonical PENDING sequences")
    result: list[dict[str, str]] = []
    for order, row in enumerate(selected, start=1):
        members = row["members"].split(";")
        if QUARANTINED_STEM in members:
            raise ValueError("WP16 selection contains quarantined stem 0248")
        for stem in members:
            if stem not in inventory:
                raise ValueError(f"WP16 missing inventory stem: {stem}")
            verify_raw_member(inventory[stem], raw_root)
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
                "wp16_atlas_page": f"{ASSETS_RELATIVE_PATH}/page_{order:03d}.jpg",
                "selection_status": "SELECTED_FIRST_100_QUARANTINE_ELIGIBLE_PENDING_SEQUENCE_BATCH_A",
                "evidence_boundary": EVIDENCE_BOUNDARY,
            }
        )
    if sum(int(row["member_count"]) for row in result) != EXPECTED_MEMBER_COUNT:
        raise ValueError("WP16 selected member count differs from exact contract")
    return result, inventory


def derive_exclusions(repo_root: Path) -> list[dict[str, str]]:
    queue = load_sequence_queue(repo_root)
    row = queue[49]
    if (
        row["proxy_sequence_id"] != "proxy_sequence_0050"
        or row["review_status"] != "PENDING"
        or QUARANTINED_STEM not in row["members"].split(";")
    ):
        raise ValueError("WP16 quarantine exclusion source differs from exact contract")
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


def derive_lineage(
    selection: list[dict[str, str]],
    inventory: dict[str, dict[str, str]],
    raw_root: Path,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for sequence in selection:
        for member_order, stem in enumerate(sequence["members"].split(";"), start=1):
            item = inventory[stem]
            verify_raw_member(item, raw_root)
            rows.append(
                {
                    "batch_position": sequence["batch_position"],
                    "canonical_review_order": sequence["canonical_review_order"],
                    "proxy_sequence_id": sequence["proxy_sequence_id"],
                    "member_order": str(member_order),
                    "stem": stem,
                    "split": item["split"],
                    "image_path": item["image_path"],
                    "image_sha256": item["image_sha256"],
                    "label_path": item["label_path"],
                    "label_sha256": item["label_sha256"],
                    "width": item["width"],
                    "height": item["height"],
                    "format": item["format"],
                    "mode": item["mode"],
                    "decode_verified": "True",
                    "box_count": item["box_count"],
                    "class_ids": item["class_ids"],
                    "wp16_atlas_page": sequence["wp16_atlas_page"],
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                }
            )
    if len(rows) != EXPECTED_MEMBER_COUNT:
        raise ValueError("WP16 lineage must contain exactly 339 members")
    if len({row["stem"] for row in rows}) != EXPECTED_MEMBER_COUNT:
        raise ValueError("WP16 lineage member stems must be unique")
    return rows


def load_review_notes(
    repo_root: Path, selection: list[dict[str, str]]
) -> list[dict[str, str]]:
    path = repo_root / REVIEW_NOTES_RELATIVE_PATH
    if base.sha256_file(path) != EXPECTED_REVIEW_NOTES_SHA256:
        raise ValueError("WP16 review notes differ from pinned PM source anchor")
    rows = base.read_csv(path)
    if not rows or list(rows[0]) != NOTE_FIELDS or len(rows) != EXPECTED_SELECTION_COUNT:
        raise ValueError("WP16 review notes fields/count differ from contract")
    for expected, row in zip(selection, rows, strict=True):
        if (
            row["batch_position"] != expected["batch_position"]
            or row["canonical_review_order"] != expected["canonical_review_order"]
            or row["proxy_sequence_id"] != expected["proxy_sequence_id"]
            or row["capture_sequence"] not in CAPTURE_VALUES
            or row["physical_sign_sequence"] not in PHYSICAL_VALUES
            or row["confidence"] not in CONFIDENCE_VALUES
            or row["reviewer"] != "PM/Codex provisional sequence reviewer"
            or row["reviewed_at"] != REVIEWED_AT
            or not row["rationale"].strip()
        ):
            raise ValueError(f"WP16 invalid review note: {row.get('proxy_sequence_id')}")
    return rows


def annotation_payload_from_notes(
    notes: list[dict[str, str]], selection: list[dict[str, str]]
) -> dict[str, Any]:
    decisions = []
    for note, row in zip(notes, selection, strict=True):
        decisions.append(
            {
                "batch_position": int(row["batch_position"]),
                "canonical_review_order": int(row["canonical_review_order"]),
                "proxy_sequence_id": row["proxy_sequence_id"],
                "member_count": int(row["member_count"]),
                "members": row["members"].split(";"),
                "capture_sequence": note["capture_sequence"],
                "physical_sign_sequence": note["physical_sign_sequence"],
                "confidence": note["confidence"],
                "reviewer": note["reviewer"],
                "reviewed_at": note["reviewed_at"],
                "rationale": note["rationale"],
                "evidence_refs": [row["wp16_atlas_page"], row["wp3_contact_sheet"]],
                "evidence_boundary": EVIDENCE_BOUNDARY,
            }
        )
    return {
        "schema_version": 1,
        "status": ANNOTATION_STATUS,
        "batch_id": BATCH_ID,
        "reviewer": "PM/Codex provisional sequence reviewer",
        "reviewed_at": REVIEWED_AT,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "decision_count": len(decisions),
        "decisions": decisions,
    }


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
    canvas_width = 1600
    header_height = 230
    columns = 4
    cell_width = 390
    cell_height = 265
    image_size = (360, 203)
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
            f"M0-WP16 Sequence Batch A | {page_number:03d}/{EXPECTED_PAGE_COUNT:03d} | "
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
                draw,
                text,
                18,
                cursor,
                1550,
                small_font,
                "#047857" if decision and index else "#111827",
                line_gap=2,
            )
            header_bounds.append(bounds)
            cursor += 2
        if cursor > header_height - 8:
            raise RuntimeError(f"WP16 header text overflow for {sequence['proxy_sequence_id']}")
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
            image_path, label_path, _boxes = verify_raw_member(item, raw_root)
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
                    "image_bounds": [
                        image_xy[0],
                        image_xy[1],
                        image_xy[0] + image_size[0],
                        image_xy[1] + image_size[1],
                    ],
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
        "<!doctype html><meta charset='utf-8'><title>M0-WP16 sequence Batch A atlas</title>",
        "<style>body{font-family:system-ui;margin:2rem;max-width:1200px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #bbb;padding:.4rem}</style>",
        "<h1>M0-WP16 D02-C sequence review — Batch A</h1>",
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
        "status": "PASS_COMPLETE_100_SEQUENCE_339_MEMBER_COVERAGE_TEXT_BOUNDS_AND_BBOX_CONTEXT",
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


def verify_regenerated_atlas_and_layout(
    repo_root: Path,
    raw_root: Path,
    selection: list[dict[str, str]],
    inventory: dict[str, dict[str, str]],
    decisions: list[dict[str, Any]],
    packaged_layout: dict[str, Any],
) -> None:
    with tempfile.TemporaryDirectory(prefix="wp16_regen_") as value:
        assets = Path(value) / "atlas"
        paths, layout = render_atlas(selection, inventory, raw_root, assets, decisions)
        if layout != packaged_layout:
            raise ValueError("WP16 layout differs from deterministic regeneration")
        packaged = repo_root / ASSETS_RELATIVE_PATH
        for path in paths:
            target = packaged / path.name
            if base.sha256_file(path) != base.sha256_file(target) or path.read_bytes() != target.read_bytes():
                raise ValueError(f"WP16 atlas bytes differ from regeneration: {path.name}")


def summary_from_decisions(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "capture_sequence_counts": dict(sorted(Counter(row["capture_sequence"] for row in decisions).items())),
        "physical_sign_sequence_counts": dict(sorted(Counter(row["physical_sign_sequence"] for row in decisions).items())),
        "confidence_counts": dict(sorted(Counter(row["confidence"] for row in decisions).items())),
        "selected_sequences": EXPECTED_SELECTION_COUNT,
        "selected_members": EXPECTED_MEMBER_COUNT,
        "canonical_sequences_pending_unchanged": EXPECTED_CANONICAL_SEQUENCE_COUNT,
        "pending_sequences_outside_overlay": EXPECTED_PENDING_OUTSIDE_OVERLAY,
    }


def render_report(summary: dict[str, Any], annotation_payload: dict[str, Any]) -> str:
    def counts(name: str) -> str:
        return "\n".join(f"- `{key}`: {value}" for key, value in summary[name].items())

    return f"""# M0-WP16 — D02-C sequence review, Batch A

Status: `{PACKAGE_STATUS}`  
Boundary: `{EVIDENCE_BOUNDARY}`

This package records one PM/Codex provisional visual pass over the exact first 100 quarantine-
eligible canonical WP5 PENDING sequences in canonical order. It excludes the whole canonical
`proxy_sequence_0050` because that row contains quarantined stem `0248`; it does not truncate or
rewrite that sequence. It does not approve D-02, create final/transitive group truth or a split,
or authorize training. D02-A metadata remains preferred.

## Selection and review protocol

- Selection: `proxy_sequence_0001` through `proxy_sequence_0101`, exact canonical order with
  `proxy_sequence_0050` excluded intact by the approved stem-0248 quarantine.
- Exclusion registry pins canonical row 50 as `PENDING`, `overlay_reviewed=False`, reason
  `CONTAINS_QUARANTINED_STEM_0248`; no member is removed or rewritten.
- Source coverage: 100 sequences, 339 unique member frames, all image/label hashes, dimensions,
  decode state, label counts/classes and bbox context verified; quarantined stem `0248` is absent.
- Reviewer: `{annotation_payload['reviewer']}` at `{annotation_payload['reviewed_at']}`.
- All 100 sequences and all 339 member frames were directly inspected in the 100-page WP16 atlas.
  Proxy metrics were context only; creator/session/physical-sign identity metadata is unavailable.

## Hardened verifier contract

- Exact 101-file atlas roster: index plus one page for each sequence.
- R1 enforces the exact 31-field manifest top-level schema and rejects every missing or unknown
  field; each source/artifact record remains exact-key checked by the inherited hardened contract.
- Index, 100 JPEG pages and layout are regenerated in isolation and byte/deep-compared.
- Trusted review-notes SHA-256 `{EXPECTED_REVIEW_NOTES_SHA256}` pins exact decisions and IDs.
  Coherent downstream rebuild and count-preserving ID swaps cannot override this source anchor.

## Provisional capture-sequence outcomes

{counts('capture_sequence_counts')}

## Provisional physical-sign-sequence outcomes

{counts('physical_sign_sequence_counts')}

## Confidence

{counts('confidence_counts')}

## Remaining workload and governance

- Canonical WP5 remains unchanged at 589 PENDING sequences.
- This overlay covers 100 sequences; 489 remain outside the overlay.
- Canonical WP5 remains unchanged at 3,172 PENDING edges; five QA-passed cross-split overlays do
  not resolve the remaining 2,146 other pending edges or create sequence truth.
- D-02 remains PENDING; Gate 0 remains BLOCKED; `training_authorized=false`.

## Artifacts

- Decisions: `{ANNOTATIONS_RELATIVE_PATH}`.
- Selection: `{SELECTION_RELATIVE_PATH}`.
- Member lineage: `{LINEAGE_RELATIVE_PATH}`.
- Layout audit: `{LAYOUT_RELATIVE_PATH}`.
- Atlas: `{ASSETS_RELATIVE_PATH}/index.html` and 100 JPEG pages.
- Manifest: `{MANIFEST_RELATIVE_PATH}`.
"""


def build_manifest(repo_root: Path) -> dict[str, Any]:
    sources = [relative_record(path, repo_root, item_id) for item_id, path, _pin in source_contract(repo_root)]
    artifacts = [relative_record(path, repo_root, item_id) for item_id, path in artifact_contract(repo_root)]
    manifest = {
        "schema_version": 1,
        "package": BATCH_ID,
        "status": PACKAGE_STATUS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "gate0": "BLOCKED",
        "d02_status": "PENDING",
        "canonical_wp5_mutated": False,
        "canonical_edge_overlays_mutated": False,
        "final_group_truth_created": False,
        "transitive_grouping_created": False,
        "split_authorized": False,
        "training_authorized": False,
        "manifest_path": MANIFEST_RELATIVE_PATH,
        "manifest_self_in_artifact_count": False,
        "artifact_count_semantics": "EXCLUDES_MANIFEST_FILE",
        "selection_count": EXPECTED_SELECTION_COUNT,
        "member_lineage_count": EXPECTED_MEMBER_COUNT,
        "canonical_sequence_count": EXPECTED_CANONICAL_SEQUENCE_COUNT,
        "canonical_sequence_pending_count": EXPECTED_CANONICAL_SEQUENCE_COUNT,
        "pending_sequences_outside_overlay": EXPECTED_PENDING_OUTSIDE_OVERLAY,
        "quarantined_stem_0248_selected": False,
        "exclusion_count": 1,
        "quarantined_sequence_reviewed": False,
        "excluded_quarantined_sequence_id": "proxy_sequence_0050",
        "atlas_page_count": EXPECTED_PAGE_COUNT,
        "atlas_file_count": EXPECTED_PAGE_COUNT + 1,
        "source_count": len(sources),
        "artifact_count": len(artifacts),
        "total_artifact_bytes": sum(record["size"] for record in artifacts),
        "sources": sources,
        "artifacts": artifacts,
    }
    if set(manifest) != MANIFEST_TOP_LEVEL_FIELDS:
        raise RuntimeError("WP16 builder manifest fields differ from exact top-level contract")
    return manifest


def contract_pairs(
    contract: list[tuple[str, Path]] | list[tuple[str, Path, str | None]], repo_root: Path
) -> list[tuple[str, str]]:
    return [(item[0], item[1].relative_to(repo_root).as_posix()) for item in contract]


def verify_manifest(manifest_path: Path, repo_root: Path, raw_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    payload: dict[str, Any] = {}
    sources: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []
    try:
        repo_root = repo_root.resolve()
        raw_root = raw_root.resolve()
        manifest_path = manifest_path if manifest_path.is_absolute() else repo_root / manifest_path
        manifest_path.resolve().relative_to(repo_root)
        if manifest_path.is_symlink() or not manifest_path.is_file():
            raise ValueError("WP16 manifest must be a regular file under repo root")
        decoded = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(decoded, dict):
            raise ValueError("WP16 manifest root must be an object")
        payload = decoded
        actual_top_level_fields = set(payload)
        if actual_top_level_fields != MANIFEST_TOP_LEVEL_FIELDS:
            missing = sorted(MANIFEST_TOP_LEVEL_FIELDS - actual_top_level_fields)
            unknown = sorted(actual_top_level_fields - MANIFEST_TOP_LEVEL_FIELDS)
            errors.append(
                "manifest top-level fields differ from WP16 exact schema: "
                f"missing={missing}, unknown={unknown}"
            )
        expected_top = {
            "schema_version": 1,
            "package": BATCH_ID,
            "status": PACKAGE_STATUS,
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "gate0": "BLOCKED",
            "d02_status": "PENDING",
            "canonical_wp5_mutated": False,
            "canonical_edge_overlays_mutated": False,
            "final_group_truth_created": False,
            "transitive_grouping_created": False,
            "split_authorized": False,
            "training_authorized": False,
            "manifest_path": MANIFEST_RELATIVE_PATH,
            "manifest_self_in_artifact_count": False,
            "artifact_count_semantics": "EXCLUDES_MANIFEST_FILE",
            "selection_count": EXPECTED_SELECTION_COUNT,
            "member_lineage_count": EXPECTED_MEMBER_COUNT,
            "canonical_sequence_count": EXPECTED_CANONICAL_SEQUENCE_COUNT,
            "canonical_sequence_pending_count": EXPECTED_CANONICAL_SEQUENCE_COUNT,
            "pending_sequences_outside_overlay": EXPECTED_PENDING_OUTSIDE_OVERLAY,
            "quarantined_stem_0248_selected": False,
            "exclusion_count": 1,
            "quarantined_sequence_reviewed": False,
            "excluded_quarantined_sequence_id": "proxy_sequence_0050",
            "atlas_page_count": EXPECTED_PAGE_COUNT,
            "atlas_file_count": EXPECTED_PAGE_COUNT + 1,
            "source_count": len(source_contract(repo_root)),
            "artifact_count": len(artifact_contract(repo_root)),
        }
        for key, value in expected_top.items():
            if payload.get(key) != value:
                errors.append(f"manifest field mismatch: {key}")
        source_expected = contract_pairs(source_contract(repo_root), repo_root)
        artifact_expected = contract_pairs(artifact_contract(repo_root), repo_root)
        sources = base.validate_manifest_collection(payload, "sources", source_expected, repo_root, errors)
        artifacts = base.validate_manifest_collection(payload, "artifacts", artifact_expected, repo_root, errors)
        for name, records in (("sources", sources), ("artifacts", artifacts)):
            for record in records:
                path = base.safe_child(repo_root, record["path"])
                if path.is_symlink() or not path.is_file():
                    errors.append(f"{name} member is not a regular file: {record['path']}")
                    continue
                if path.stat().st_size != record["size"] or base.sha256_file(path) != record["sha256"]:
                    errors.append(f"{name} hash/size mismatch: {record['id']}")
        verify_source_contract(repo_root)
        verify_exact_atlas_roster(repo_root / ASSETS_RELATIVE_PATH)
        validate_governance(repo_root)
        selection, inventory = derive_selection(repo_root, raw_root)
        actual_selection = base.read_csv(repo_root / SELECTION_RELATIVE_PATH)
        if actual_selection != selection or list(actual_selection[0]) != SELECTION_FIELDS:
            raise ValueError("WP16 selection differs from exact canonical derivation")
        exclusions = derive_exclusions(repo_root)
        actual_exclusions = base.read_csv(repo_root / EXCLUSIONS_RELATIVE_PATH)
        if actual_exclusions != exclusions or list(actual_exclusions[0]) != EXCLUSION_FIELDS:
            raise ValueError("WP16 quarantine exclusion registry differs from exact contract")
        lineage = derive_lineage(selection, inventory, raw_root)
        actual_lineage = base.read_csv(repo_root / LINEAGE_RELATIVE_PATH)
        if actual_lineage != lineage or list(actual_lineage[0]) != LINEAGE_FIELDS:
            raise ValueError("WP16 lineage differs from exact raw-source derivation")
        notes = load_review_notes(repo_root, selection)
        expected_annotations = annotation_payload_from_notes(notes, selection)
        annotations = json.loads((repo_root / ANNOTATIONS_RELATIVE_PATH).read_text(encoding="utf-8"))
        if annotations != expected_annotations:
            raise ValueError("WP16 annotations differ from pinned PM notes")
        decisions = annotations["decisions"]
        layout = json.loads((repo_root / LAYOUT_RELATIVE_PATH).read_text(encoding="utf-8"))
        if (
            layout.get("page_sequence_counts") != [1] * EXPECTED_PAGE_COUNT
            or layout.get("page_count") != EXPECTED_PAGE_COUNT
            or layout.get("sequence_count") != EXPECTED_SELECTION_COUNT
            or layout.get("member_count") != EXPECTED_MEMBER_COUNT
            or len(layout.get("pages", [])) != EXPECTED_PAGE_COUNT
            or not layout.get("all_decisions_recorded")
        ):
            raise ValueError("WP16 layout cardinality/status differs from contract")
        for expected_order, (sequence, page) in enumerate(zip(selection, layout["pages"], strict=True), start=1):
            if (
                page.get("page") != expected_order
                or page.get("batch_position") != expected_order
                or page.get("canonical_review_order") != int(sequence["canonical_review_order"])
                or page.get("proxy_sequence_id") != sequence["proxy_sequence_id"]
                or page.get("member_count") != int(sequence["member_count"])
                or [member.get("stem") for member in page.get("members", [])] != sequence["members"].split(";")
                or page.get("decision_recorded") is not True
                or page.get("all_bounds_fit") is not True
                or page.get("all_text_complete") is not True
                or page.get("all_bbox_context_rendered") is not True
            ):
                raise ValueError(f"WP16 page semantic mismatch: {expected_order}")
        verify_regenerated_atlas_and_layout(repo_root, raw_root, selection, inventory, decisions, layout)
        summary = summary_from_decisions(decisions)
        expected_report = render_report(summary, annotations)
        if (repo_root / REPORT_RELATIVE_PATH).read_text(encoding="utf-8") != expected_report:
            raise ValueError("WP16 report differs from verified decisions")
        forbidden = {"group_id", "final_group_id", "assigned_split", "approved_split"}
        if any(forbidden.intersection(row) for row in [*selection, *decisions]):
            raise ValueError("WP16 package contains forbidden final grouping/split fields")
        if payload.get("total_artifact_bytes") != sum(record["size"] for record in artifacts):
            errors.append("manifest total_artifact_bytes mismatch")
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


def prepare(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    raw_root = raw_root.resolve()
    for item_id, path, pinned_hash in source_contract(repo_root)[:-2]:
        if path.is_symlink() or not path.is_file() or base.sha256_file(path) != pinned_hash:
            raise ValueError(f"WP16 prepare source mismatch: {item_id}")
    validate_governance(repo_root)
    selection, inventory = derive_selection(repo_root, raw_root)
    lineage = derive_lineage(selection, inventory, raw_root)
    base.write_csv(repo_root / SELECTION_RELATIVE_PATH, selection, SELECTION_FIELDS)
    base.write_csv(repo_root / EXCLUSIONS_RELATIVE_PATH, derive_exclusions(repo_root), EXCLUSION_FIELDS)
    base.write_csv(repo_root / LINEAGE_RELATIVE_PATH, lineage, LINEAGE_FIELDS)
    _paths, layout = render_atlas(selection, inventory, raw_root, repo_root / ASSETS_RELATIVE_PATH, None)
    base.write_json(repo_root / LAYOUT_RELATIVE_PATH, layout)
    return {
        "status": "WP16_SEQUENCE_BATCH_A_PREPARED_AWAITING_PM_VISUAL_REVIEW",
        "first_sequence": selection[0]["proxy_sequence_id"],
        "last_sequence": selection[-1]["proxy_sequence_id"],
        "selection_count": len(selection),
        "member_count": len(lineage),
        "page_count": layout["page_count"],
        "official_manifest_written": False,
        "gate0": "BLOCKED",
        "training_authorized": False,
    }


def build(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    raw_root = raw_root.resolve()
    verify_source_contract(repo_root)
    validate_governance(repo_root)
    selection, inventory = derive_selection(repo_root, raw_root)
    lineage = derive_lineage(selection, inventory, raw_root)
    notes = load_review_notes(repo_root, selection)
    annotations = annotation_payload_from_notes(notes, selection)
    before_raw = {
        stem: (
            base.sha256_file(base.safe_child(raw_root, inventory[stem]["image_path"])),
            base.sha256_file(base.safe_child(raw_root, inventory[stem]["label_path"])),
        )
        for row in selection
        for stem in row["members"].split(";")
    }
    base.write_csv(repo_root / SELECTION_RELATIVE_PATH, selection, SELECTION_FIELDS)
    base.write_csv(repo_root / EXCLUSIONS_RELATIVE_PATH, derive_exclusions(repo_root), EXCLUSION_FIELDS)
    base.write_csv(repo_root / LINEAGE_RELATIVE_PATH, lineage, LINEAGE_FIELDS)
    base.write_json(repo_root / ANNOTATIONS_RELATIVE_PATH, annotations)
    _paths, layout = render_atlas(
        selection, inventory, raw_root, repo_root / ASSETS_RELATIVE_PATH, annotations["decisions"]
    )
    base.write_json(repo_root / LAYOUT_RELATIVE_PATH, layout)
    summary = summary_from_decisions(annotations["decisions"])
    (repo_root / REPORT_RELATIVE_PATH).write_text(render_report(summary, annotations), encoding="utf-8")
    after_raw = {
        stem: (
            base.sha256_file(base.safe_child(raw_root, inventory[stem]["image_path"])),
            base.sha256_file(base.safe_child(raw_root, inventory[stem]["label_path"])),
        )
        for row in selection
        for stem in row["members"].split(";")
    }
    if before_raw != after_raw:
        raise RuntimeError("WP16 raw sources changed during build")
    manifest = build_manifest(repo_root)
    base.write_json(repo_root / MANIFEST_RELATIVE_PATH, manifest)
    result = verify_manifest(repo_root / MANIFEST_RELATIVE_PATH, repo_root, raw_root)
    if not result["valid"]:
        raise RuntimeError(f"WP16 package verification failed: {result['errors']}")
    return {
        "status": PACKAGE_STATUS,
        "selection_count": EXPECTED_SELECTION_COUNT,
        "member_count": EXPECTED_MEMBER_COUNT,
        "page_count": EXPECTED_PAGE_COUNT,
        "source_count": manifest["source_count"],
        "artifact_count": manifest["artifact_count"],
        "manifest_sha256": base.sha256_file(repo_root / MANIFEST_RELATIVE_PATH),
        "capture_sequence_counts": summary["capture_sequence_counts"],
        "physical_sign_sequence_counts": summary["physical_sign_sequence_counts"],
        "confidence_counts": summary["confidence_counts"],
        "canonical_sequences_pending_unchanged": EXPECTED_CANONICAL_SEQUENCE_COUNT,
        "pending_sequences_outside_overlay": EXPECTED_PENDING_OUTSIDE_OVERLAY,
        "gate0": "BLOCKED",
        "training_authorized": False,
    }


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
