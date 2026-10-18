# ruff: noqa: E501
"""Build and verify the M0-WP12 cross-split visual-review Batch-B package."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import shutil
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

PACKAGE_STATUS = "WP12_R1_AWAITING_QA_BATCH_B_PM_PROVISIONAL_REVIEW"
ANNOTATION_STATUS = "PM_REVIEWED_AWAITING_INDEPENDENT_QA"
EVIDENCE_BOUNDARY = (
    "BATCH_B_PM_PROVISIONAL_VISUAL_REVIEW_ONLY_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_"
    "NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING"
)
METADATA_BOUNDARY = "NO_CREATOR_SESSION_OR_PHYSICAL_SIGN_IDENTITY_METADATA_AVAILABLE"
REVIEWER = "PM/Codex provisional visual reviewer"
BATCH_ID = "M0-WP12-R1-BATCH-B"
EXPECTED_SELECTION_COUNT = 250
EXPECTED_BATCH_A_COUNT = 100
EXPECTED_WP5_EDGE_COUNT = 3178
EXPECTED_WP5_REVIEWED_COUNT = 6
EXPECTED_WP5_PENDING_COUNT = 3172
EXPECTED_WP5_SEQUENCE_COUNT = 589
EXPECTED_WP5_CROSS_SPLIT_COUNT = 1031
EXPECTED_SELECTED_ENDPOINT_BOX_COUNT = 1553
QUARANTINED_STEM = "0248"
EXPECTED_WP5_REVIEWED_IDS = {
    "edge_000001",
    "edge_000003",
    "edge_000100",
    "edge_000109",
    "edge_000527",
    "edge_000663",
}
PAIRS_PER_PAGE = 5
EXPECTED_PAGE_COUNT = math.ceil(EXPECTED_SELECTION_COUNT / PAIRS_PER_PAGE)
MANIFEST_SCHEMA_VERSION = 1
PRE_REPAIR_MANIFEST_SHA256 = (
    "0b5c90de79326bc7cccb18830078c5aef5ec46bd8559ca1f909e3a5878456347"
)
EXPECTED_REVIEW_NOTES_SHA256 = (
    "27adbf366cfbfd2c03c1025e82bd6cef26e1b353e1e50340ddc6d7a5f9ed75b4"
)
EXPECTED_CAPTURE_COUNTS = {
    "SAME_CAPTURE_CANDIDATE": 240,
    "NOT_RELATED": 8,
    "UNRESOLVED": 2,
}
EXPECTED_PHYSICAL_SIGN_COUNTS = {
    "SAME_PHYSICAL_SIGN_CANDIDATE": 235,
    "NOT_RELATED": 14,
    "UNRESOLVED": 1,
}
EXPECTED_CONFIDENCE_COUNTS = {"HIGH": 243, "MEDIUM": 7}
EXPECTED_CAPTURE_UNRESOLVED_IDS = {"edge_000535", "edge_000539"}
EXPECTED_PHYSICAL_SIGN_UNRESOLVED_IDS = {"edge_000539"}
MANIFEST_RELATIVE_PATH = "docs/review/generated/wp12_batch_b_manifest.json"
SELECTION_RELATIVE_PATH = "docs/review/generated/wp12_batch_b_selection.csv"
LINEAGE_RELATIVE_PATH = "docs/review/generated/wp12_batch_b_source_lineage.csv"
LAYOUT_RELATIVE_PATH = "docs/review/generated/wp12_batch_b_layout_audit.json"
REPORT_RELATIVE_PATH = "docs/review/wp12_cross_split_review_batch_b_report.md"
ANNOTATIONS_RELATIVE_PATH = "docs/review/wp12_visual_review_annotations_batch_b.json"
REVIEW_NOTES_RELATIVE_PATH = "docs/review/wp12_visual_review_notes_batch_b.csv"
ASSETS_RELATIVE_PATH = "docs/review/assets/wp12/batch_b"
REVIEWED_AT = "2026-10-11T18:00:00+07:00"
EXPECTED_PINNED_HASHES = {
    "wp5_manifest": "f8d620a3cbb3b500153f6685b94a9936a8f83eb6f5399ce0a2e8be77982d4b80",
    "wp5_decisions": "3f4cda85d10ea3dbcb9d9c83bbe2d5651991c00fb98b5e0fffbf28716e34fa1a",
    "wp5_layout": "8e9da4db09b1a175fd258b1704dbb6d70c66190864a1ec91b7f3e9bc8ad070a9",
    "image_inventory": "d45aa7f398a040c44cbc040f4ec005d7e5a8ef50586e905315f76c792ca29022",
    "source_preservation": "5ca3e769b9197cad19bcb75f553dd59fee6e3035e0cc86cd9693737f84a713d7",
    "decision_status": "87d81262e907bb1c479cfac6535e7b3f67a368c371e96b810aa02f2e92d0d72c",
    "wp6_manifest": "656afe56bf342a0d4d0110dcd6b1d601f9f35633d03c65c98d54d3d454760bb0",
    "wp7_manifest": "73ed4095a1f59b72f010fd87b63c4a7f0b16bcf8e0c667ec77576ec827e5d7f2",
    "wp7_selection": "1779ac973fad5f1de54c019cdb87dc77cd7228b9d3b15be923d9d6b4d243fdcf",
    "wp7_annotations": "f38e63e8c60ca043de97fb1d82ace4fe8acefb5be260f6500cf1c57f898b2d4d",
}
ALLOWED_OUTCOMES = (
    "SAME_CAPTURE_CANDIDATE",
    "NOT_RELATED",
    "UNRESOLVED",
)
CAPTURE_HYPOTHESES = (
    "SAME_CAPTURE_CANDIDATE",
    "NOT_RELATED",
    "UNRESOLVED",
)
PHYSICAL_SIGN_HYPOTHESES = (
    "SAME_PHYSICAL_SIGN_CANDIDATE",
    "NOT_RELATED",
    "UNRESOLVED",
)
CONFIDENCE_VALUES = ("HIGH", "MEDIUM", "LOW")
SELECTION_FIELDS = [
    "batch_position",
    "edge_id",
    "wp5_review_order",
    "wp5_review_status",
    "left_stem",
    "left_split",
    "right_stem",
    "right_split",
    "cross_split",
    "same_dimensions",
    "thumbnail_mae",
    "dhash_distance",
    "rgb_histogram_cosine",
    "proxy_status",
    "proxy_sequence_id",
    "left_class_ids",
    "right_class_ids",
    "left_image_path",
    "right_image_path",
    "left_label_path",
    "right_label_path",
    "left_image_sha256",
    "right_image_sha256",
    "left_label_sha256",
    "right_label_sha256",
    "wp5_atlas_page",
    "wp5_atlas_slot",
    "wp12_atlas_page",
    "wp12_atlas_slot",
    "selection_status",
    "evidence_boundary",
]
REVIEW_NOTE_FIELDS = [
    "batch_position",
    "edge_id",
    "provisional_outcome",
    "capture_hypothesis",
    "physical_sign_hypothesis",
    "confidence",
    "rationale",
]
LINEAGE_FIELDS = [
    "batch_position",
    "edge_id",
    "side",
    "stem",
    "split",
    "class_ids",
    "image_path",
    "label_path",
    "image_sha256",
    "label_sha256",
    "image_width",
    "image_height",
    "wp5_atlas_page",
    "wp5_atlas_slot",
    "wp12_atlas_page",
    "wp12_atlas_slot",
    "evidence_boundary",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json_bytes(payload))


def json_bytes(payload: Any) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def reviewer_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    )
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def safe_child(root: Path, relative_value: str) -> Path:
    relative = Path(relative_value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"unsafe relative path: {relative_value}")
    resolved_root = root.resolve()
    lexical_target = resolved_root / relative
    current = resolved_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"symlink path is forbidden: {relative_value}")
    target = lexical_target.resolve()
    target.relative_to(resolved_root)
    return target


def source_contract(repo_root: Path) -> list[tuple[str, Path, str | None]]:
    generated = repo_root / "docs/review/generated"
    audit = repo_root / "results/data_audit/DATASET01_052bc980a7206f8d"
    return [
        ("wp5_manifest", generated / "wp5_evidence_manifest.json", EXPECTED_PINNED_HASHES["wp5_manifest"]),
        ("wp5_decisions", generated / "wp5_provisional_edge_decisions.csv", EXPECTED_PINNED_HASHES["wp5_decisions"]),
        ("wp5_layout", generated / "wp5_pair_layout_audit.json", EXPECTED_PINNED_HASHES["wp5_layout"]),
        ("image_inventory", audit / "image_inventory.csv", EXPECTED_PINNED_HASHES["image_inventory"]),
        ("source_preservation", audit / "source_preservation_proof.json", EXPECTED_PINNED_HASHES["source_preservation"]),
        ("decision_status", repo_root / "docs/review/decision_status.json", EXPECTED_PINNED_HASHES["decision_status"]),
        ("wp6_manifest", generated / "wp6_e0_compute_manifest.json", EXPECTED_PINNED_HASHES["wp6_manifest"]),
        ("wp7_manifest", generated / "wp7_batch_a_manifest.json", EXPECTED_PINNED_HASHES["wp7_manifest"]),
        ("wp7_selection", generated / "wp7_batch_a_selection.csv", EXPECTED_PINNED_HASHES["wp7_selection"]),
        ("wp7_annotations", repo_root / "docs/review/wp7_visual_review_annotations_batch_a.json", EXPECTED_PINNED_HASHES["wp7_annotations"]),
        (
            "wp12_review_notes",
            repo_root / REVIEW_NOTES_RELATIVE_PATH,
            EXPECTED_REVIEW_NOTES_SHA256,
        ),
        ("wp12_builder", repo_root / "scripts/build_wp12_cross_split_review_batch.py", None),
    ]


def artifact_contract(repo_root: Path) -> list[tuple[str, Path]]:
    assets = repo_root / ASSETS_RELATIVE_PATH
    rows: list[tuple[str, Path]] = [
        ("annotations", repo_root / ANNOTATIONS_RELATIVE_PATH),
        ("selection", repo_root / SELECTION_RELATIVE_PATH),
        ("source_lineage", repo_root / LINEAGE_RELATIVE_PATH),
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
        raise ValueError("WP12 atlas root must be a real directory")
    expected = sorted(expected_atlas_names())
    entries = sorted(assets_dir.iterdir(), key=lambda path: path.name)
    actual = [path.name for path in entries]
    if actual != expected:
        raise ValueError("WP12 atlas directory roster differs from exact 51-file contract")
    for path in entries:
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"WP12 atlas entry must be a regular non-symlink file: {path.name}")


def relative_record(path: Path, repo_root: Path, item_id: str) -> dict[str, Any]:
    return {
        "id": item_id,
        "path": path.resolve().relative_to(repo_root.resolve()).as_posix(),
        "sha256": sha256_file(path),
        "size": path.stat().st_size,
    }


def verify_source_contract(repo_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item_id, path, pinned_hash in source_contract(repo_root):
        if not path.is_file():
            raise FileNotFoundError(f"required WP12 source missing: {path}")
        digest = sha256_file(path)
        if pinned_hash is not None and digest != pinned_hash:
            raise ValueError(f"pinned WP12 source mismatch: {item_id}")
        records.append(relative_record(path, repo_root, item_id))
    return records


def validate_governance(repo_root: Path) -> None:
    payload = json.loads((repo_root / "docs/review/decision_status.json").read_text(encoding="utf-8"))
    required = {"D-01", "D-02", "D-03", "D-04", "D-05", "G0.4-bbox-0248"}
    decisions = payload.get("decisions", {})
    if (
        payload.get("gate0") != "BLOCKED"
        or payload.get("training_authorized") is not False
        or set(decisions) != required
        or {decisions[item].get("status") for item in required} != {"PENDING"}
    ):
        raise ValueError("WP12 requires every Gate-0 decision PENDING and training unauthorized")


def load_inventory(repo_root: Path) -> dict[str, dict[str, str]]:
    rows = read_csv(
        repo_root / "results/data_audit/DATASET01_052bc980a7206f8d/image_inventory.csv"
    )
    inventory = {row["stem"]: row for row in rows}
    if len(rows) != 3216 or len(inventory) != 3216:
        raise ValueError("WP12 inventory must contain 3,216 unique stems")
    return inventory


def load_wp5_rows(repo_root: Path) -> list[dict[str, str]]:
    rows = read_csv(repo_root / "docs/review/generated/wp5_provisional_edge_decisions.csv")
    if len(rows) != EXPECTED_WP5_EDGE_COUNT:
        raise ValueError("WP5 edge count mismatch")
    if [int(row["review_order"]) for row in rows] != list(
        range(1, EXPECTED_WP5_EDGE_COUNT + 1)
    ):
        raise ValueError("WP5 review order is not canonical/contiguous")
    if len({row["edge_id"] for row in rows}) != EXPECTED_WP5_EDGE_COUNT:
        raise ValueError("WP5 edge IDs are not unique")
    cross_prefix = [row["cross_split"] for row in rows[:EXPECTED_WP5_CROSS_SPLIT_COUNT]]
    if set(cross_prefix) != {"True"} or any(
        row["cross_split"] != "False" for row in rows[EXPECTED_WP5_CROSS_SPLIT_COUNT:]
    ):
        raise ValueError("WP5 cross-split priority/order changed")
    reviewed = {row["edge_id"] for row in rows if row["review_status"] == "REVIEWED"}
    if reviewed != EXPECTED_WP5_REVIEWED_IDS:
        raise ValueError("WP5 reviewed edge set changed")
    if sum(row["review_status"] == "PENDING" for row in rows) != EXPECTED_WP5_PENDING_COUNT:
        raise ValueError("WP5 pending count changed")
    return rows


def verify_raw_record(
    inventory_row: dict[str, str], raw_root: Path
) -> tuple[Path, Path]:
    image_path = safe_child(raw_root, inventory_row["image_path"])
    label_path = safe_child(raw_root, inventory_row["label_path"])
    if not image_path.is_file() or not label_path.is_file():
        raise FileNotFoundError(f"raw source missing for stem {inventory_row['stem']}")
    if sha256_file(image_path) != inventory_row["image_sha256"]:
        raise ValueError(f"raw image hash drift for stem {inventory_row['stem']}")
    if sha256_file(label_path) != inventory_row["label_sha256"]:
        raise ValueError(f"raw label hash drift for stem {inventory_row['stem']}")
    return image_path, label_path


def derive_selection(
    repo_root: Path, raw_root: Path
) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    rows = load_wp5_rows(repo_root)
    inventory = load_inventory(repo_root)
    pending_cross_split = [
        row
        for row in rows
        if row["cross_split"] == "True" and row["review_status"] == "PENDING"
    ]
    batch_a_rows = read_csv(repo_root / "docs/review/generated/wp7_batch_a_selection.csv")
    batch_a_ids = [row["edge_id"] for row in batch_a_rows]
    if (
        len(batch_a_ids) != EXPECTED_BATCH_A_COUNT
        or len(set(batch_a_ids)) != EXPECTED_BATCH_A_COUNT
        or batch_a_ids != [row["edge_id"] for row in pending_cross_split[:EXPECTED_BATCH_A_COUNT]]
    ):
        raise ValueError("WP7 Batch-A exclusion roster/order differs from canonical WP5 prefix")
    batch_a_set = set(batch_a_ids)
    candidates = [row for row in pending_cross_split if row["edge_id"] not in batch_a_set][
        :EXPECTED_SELECTION_COUNT
    ]
    if len(candidates) != EXPECTED_SELECTION_COUNT:
        raise ValueError("could not derive exactly 250 next pending cross-split WP5 edges")
    selected: list[dict[str, str]] = []
    for position, edge in enumerate(candidates, start=1):
        if edge["edge_id"] in EXPECTED_WP5_REVIEWED_IDS or edge["edge_id"] in batch_a_set:
            raise ValueError("WP12 selection contains an ineligible WP5/WP7 edge")
        left = inventory[edge["left_stem"]]
        right = inventory[edge["right_stem"]]
        verify_raw_record(left, raw_root)
        verify_raw_record(right, raw_root)
        if (
            edge["left_image_sha256"] != left["image_sha256"]
            or edge["right_image_sha256"] != right["image_sha256"]
            or edge["left_label_sha256"] != left["label_sha256"]
            or edge["right_label_sha256"] != right["label_sha256"]
        ):
            raise ValueError(f"WP5/inventory source binding drift for {edge['edge_id']}")
        wp12_page = math.ceil(position / PAIRS_PER_PAGE)
        wp12_slot = (position - 1) % PAIRS_PER_PAGE + 1
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
                "wp12_atlas_page": f"{ASSETS_RELATIVE_PATH}/page_{wp12_page:03d}.jpg",
                "wp12_atlas_slot": str(wp12_slot),
                "selection_status": "SELECTED_PENDING_CROSS_SPLIT_BATCH_B",
                "evidence_boundary": EVIDENCE_BOUNDARY,
            }
        )
    if any(
        QUARANTINED_STEM in {row["left_stem"], row["right_stem"]}
        for row in selected
    ):
        raise ValueError("WP12 selection must exclude quarantined stem 0248")
    return selected, inventory


def derive_lineage(
    selection: list[dict[str, str]],
    inventory: dict[str, dict[str, str]],
    raw_root: Path,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for selected in selection:
        for side in ("left", "right"):
            stem = selected[f"{side}_stem"]
            source = inventory[stem]
            image_path, _label_path = verify_raw_record(source, raw_root)
            with Image.open(image_path) as image:
                width, height = image.size
            rows.append(
                {
                    "batch_position": selected["batch_position"],
                    "edge_id": selected["edge_id"],
                    "side": side.upper(),
                    "stem": stem,
                    "split": selected[f"{side}_split"],
                    "class_ids": selected[f"{side}_class_ids"],
                    "image_path": selected[f"{side}_image_path"],
                    "label_path": selected[f"{side}_label_path"],
                    "image_sha256": selected[f"{side}_image_sha256"],
                    "label_sha256": selected[f"{side}_label_sha256"],
                    "image_width": str(width),
                    "image_height": str(height),
                    "wp5_atlas_page": selected["wp5_atlas_page"],
                    "wp5_atlas_slot": selected["wp5_atlas_slot"],
                    "wp12_atlas_page": selected["wp12_atlas_page"],
                    "wp12_atlas_slot": selected["wp12_atlas_slot"],
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                }
            )
    if len(rows) != EXPECTED_SELECTION_COUNT * 2:
        raise ValueError("WP12 source lineage must contain exactly 500 endpoint rows")
    endpoint_box_count = sum(int(inventory[row["stem"]]["box_count"]) for row in rows)
    if endpoint_box_count != EXPECTED_SELECTED_ENDPOINT_BOX_COUNT:
        raise ValueError("WP12 selected endpoint box count differs from 1,553")
    return rows


def expected_evidence_refs(row: dict[str, str]) -> list[str]:
    return [
        f"{row['left_image_path']}#sha256={row['left_image_sha256']}",
        f"{row['right_image_path']}#sha256={row['right_image_sha256']}",
        f"{row['wp12_atlas_page']}#slot={row['wp12_atlas_slot']}",
    ]


def validate_review_decision_contract(rows: list[dict[str, Any]]) -> None:
    capture_counts = Counter(row["capture_hypothesis"] for row in rows)
    physical_counts = Counter(row["physical_sign_hypothesis"] for row in rows)
    confidence_counts = Counter(row["confidence"] for row in rows)
    capture_unresolved = {
        row["edge_id"]
        for row in rows
        if row["capture_hypothesis"] == "UNRESOLVED"
    }
    physical_unresolved = {
        row["edge_id"]
        for row in rows
        if row["physical_sign_hypothesis"] == "UNRESOLVED"
    }
    if dict(capture_counts) != EXPECTED_CAPTURE_COUNTS:
        raise ValueError("WP12 capture decision counts differ from approved PM review")
    if dict(physical_counts) != EXPECTED_PHYSICAL_SIGN_COUNTS:
        raise ValueError("WP12 physical-sign decision counts differ from approved PM review")
    if dict(confidence_counts) != EXPECTED_CONFIDENCE_COUNTS:
        raise ValueError("WP12 confidence counts differ from approved PM review")
    if capture_unresolved != EXPECTED_CAPTURE_UNRESOLVED_IDS:
        raise ValueError("WP12 capture UNRESOLVED edge IDs differ from approved PM review")
    if physical_unresolved != EXPECTED_PHYSICAL_SIGN_UNRESOLVED_IDS:
        raise ValueError(
            "WP12 physical-sign UNRESOLVED edge IDs differ from approved PM review"
        )


def load_review_notes(
    repo_root: Path, selection: list[dict[str, str]]
) -> list[dict[str, str]]:
    notes_path = repo_root / REVIEW_NOTES_RELATIVE_PATH
    if sha256_file(notes_path) != EXPECTED_REVIEW_NOTES_SHA256:
        raise ValueError("trusted WP12 review-notes source anchor mismatch")
    notes = read_csv(notes_path)
    if len(notes) != EXPECTED_SELECTION_COUNT:
        raise ValueError("WP12 review notes must contain exactly 250 decisions")
    if not notes or list(notes[0]) != REVIEW_NOTE_FIELDS:
        raise ValueError("WP12 review-note columns differ from contract")
    for expected, note in zip(selection, notes, strict=True):
        if (
            note["batch_position"] != expected["batch_position"]
            or note["edge_id"] != expected["edge_id"]
        ):
            raise ValueError(f"WP12 review-note identity/order mismatch at {expected['edge_id']}")
        if note["provisional_outcome"] not in ALLOWED_OUTCOMES:
            raise ValueError(f"invalid WP12 review-note outcome for {expected['edge_id']}")
        if note["capture_hypothesis"] not in CAPTURE_HYPOTHESES:
            raise ValueError(f"invalid WP12 review-note capture hypothesis for {expected['edge_id']}")
        if note["provisional_outcome"] != note["capture_hypothesis"]:
            raise ValueError(
                f"WP12 review-note outcome/capture mismatch for {expected['edge_id']}"
            )
        if note["physical_sign_hypothesis"] not in PHYSICAL_SIGN_HYPOTHESES:
            raise ValueError(f"invalid WP12 review-note physical hypothesis for {expected['edge_id']}")
        if note["confidence"] not in CONFIDENCE_VALUES:
            raise ValueError(f"invalid WP12 review-note confidence for {expected['edge_id']}")
        if not note["rationale"].strip():
            raise ValueError(f"missing WP12 review-note rationale for {expected['edge_id']}")
    validate_review_decision_contract(notes)
    return notes


def annotation_payload_from_notes(
    notes: list[dict[str, str]], selection: list[dict[str, str]]
) -> dict[str, Any]:
    decisions: list[dict[str, Any]] = []
    for note, selected in zip(notes, selection, strict=True):
        decisions.append(
            {
                "batch_position": int(selected["batch_position"]),
                "edge_id": selected["edge_id"],
                "left_stem": selected["left_stem"],
                "right_stem": selected["right_stem"],
                "provisional_outcome": note["provisional_outcome"],
                "capture_hypothesis": note["capture_hypothesis"],
                "physical_sign_hypothesis": note["physical_sign_hypothesis"],
                "confidence": note["confidence"],
                "rationale": note["rationale"],
                "evidence_refs": expected_evidence_refs(selected),
                "reviewer": REVIEWER,
                "reviewed_at": REVIEWED_AT,
                "metadata_boundary": METADATA_BOUNDARY,
                "evidence_boundary": EVIDENCE_BOUNDARY,
            }
        )
    return {
        "schema_version": 1,
        "batch": BATCH_ID,
        "status": ANNOTATION_STATUS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "metadata_boundary": METADATA_BOUNDARY,
        "reviewer": REVIEWER,
        "reviewed_at": REVIEWED_AT,
        "decisions": decisions,
    }


def validate_annotations(
    payload: dict[str, Any], selection: list[dict[str, str]]
) -> list[dict[str, Any]]:
    expected_top = {
        "schema_version",
        "batch",
        "status",
        "evidence_boundary",
        "metadata_boundary",
        "reviewer",
        "reviewed_at",
        "decisions",
    }
    if not isinstance(payload, dict) or set(payload) != expected_top:
        raise ValueError("WP12 annotation top-level schema mismatch")
    if (
        payload["schema_version"] != 1
        or payload["batch"] != BATCH_ID
        or payload["status"] != ANNOTATION_STATUS
        or payload["evidence_boundary"] != EVIDENCE_BOUNDARY
        or payload["metadata_boundary"] != METADATA_BOUNDARY
        or payload["reviewer"] != REVIEWER
    ):
        raise ValueError("WP12 annotation status/boundary/reviewer mismatch")
    try:
        timestamp = datetime.fromisoformat(payload["reviewed_at"])
    except (TypeError, ValueError) as exc:
        raise ValueError("WP12 reviewed_at must be ISO 8601") from exc
    if timestamp.tzinfo is None:
        raise ValueError("WP12 reviewed_at must include timezone")
    decisions = payload["decisions"]
    if not isinstance(decisions, list) or len(decisions) != EXPECTED_SELECTION_COUNT:
        raise ValueError("WP12 annotations must contain exactly 250 decisions")
    expected_fields = {
        "batch_position",
        "edge_id",
        "left_stem",
        "right_stem",
        "provisional_outcome",
        "capture_hypothesis",
        "physical_sign_hypothesis",
        "confidence",
        "rationale",
        "evidence_refs",
        "reviewer",
        "reviewed_at",
        "metadata_boundary",
        "evidence_boundary",
    }
    for expected, decision in zip(selection, decisions, strict=True):
        if not isinstance(decision, dict) or set(decision) != expected_fields:
            raise ValueError(f"WP12 decision schema mismatch at {expected['edge_id']}")
        if (
            decision["batch_position"] != int(expected["batch_position"])
            or decision["edge_id"] != expected["edge_id"]
            or decision["left_stem"] != expected["left_stem"]
            or decision["right_stem"] != expected["right_stem"]
        ):
            raise ValueError(f"WP12 decision identity/order mismatch at {expected['edge_id']}")
        if decision["provisional_outcome"] not in ALLOWED_OUTCOMES:
            raise ValueError(f"invalid WP12 outcome for {expected['edge_id']}")
        if decision["capture_hypothesis"] not in CAPTURE_HYPOTHESES:
            raise ValueError(f"invalid WP12 capture hypothesis for {expected['edge_id']}")
        if decision["physical_sign_hypothesis"] not in PHYSICAL_SIGN_HYPOTHESES:
            raise ValueError(f"invalid WP12 physical-sign hypothesis for {expected['edge_id']}")
        if decision["provisional_outcome"] != decision["capture_hypothesis"]:
            raise ValueError(f"WP12 provisional outcome must equal capture hypothesis at {expected['edge_id']}")
        if decision["confidence"] not in CONFIDENCE_VALUES:
            raise ValueError(f"invalid WP12 confidence for {expected['edge_id']}")
        if not isinstance(decision["rationale"], str) or not decision["rationale"].strip():
            raise ValueError(f"missing WP12 rationale for {expected['edge_id']}")
        if decision["evidence_refs"] != expected_evidence_refs(expected):
            raise ValueError(f"WP12 evidence refs mismatch for {expected['edge_id']}")
        if (
            decision["reviewer"] != REVIEWER
            or decision["reviewed_at"] != REVIEWED_AT
            or
            decision["metadata_boundary"] != METADATA_BOUNDARY
            or decision["evidence_boundary"] != EVIDENCE_BOUNDARY
        ):
            raise ValueError(f"WP12 decision boundary mismatch for {expected['edge_id']}")
    validate_review_decision_contract(decisions)
    return decisions


def load_annotations(
    repo_root: Path, selection: list[dict[str, str]]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = json.loads((repo_root / ANNOTATIONS_RELATIVE_PATH).read_text(encoding="utf-8"))
    return payload, validate_annotations(payload, selection)


def parse_yolo_boxes(label_path: Path, width: int, height: int) -> list[tuple[int, float, float, float, float]]:
    boxes: list[tuple[int, float, float, float, float]] = []
    for line in label_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 5:
            raise ValueError(f"invalid YOLO line in {label_path}")
        class_id = int(parts[0])
        cx, cy, bw, bh = map(float, parts[1:])
        boxes.append(
            (
                class_id,
                (cx - bw / 2) * width,
                (cy - bh / 2) * height,
                (cx + bw / 2) * width,
                (cy + bh / 2) * height,
            )
        )
    return boxes


def image_with_boxes(image_path: Path, label_path: Path, size: tuple[int, int]) -> Image.Image:
    with Image.open(image_path) as source:
        image = source.convert("RGB")
    draw = ImageDraw.Draw(image)
    line_width = max(3, image.width // 240)
    label_font = reviewer_font(max(18, image.width // 45))
    for class_id, x1, y1, x2, y2 in parse_yolo_boxes(label_path, image.width, image.height):
        draw.rectangle((x1, y1, x2, y2), outline="#ff1744", width=line_width)
        draw.rectangle((x1, max(0, y1 - 26), x1 + 70, y1), fill="#ff1744")
        draw.text((x1 + 3, max(0, y1 - 25)), f"cls {class_id}", fill="white", font=label_font)
    image.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, "#111827")
    canvas.paste(image, ((size[0] - image.width) // 2, (size[1] - image.height) // 2))
    return canvas


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    width: int,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: str,
    line_gap: int = 4,
) -> tuple[int, list[int]]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and draw.textlength(candidate, font=font) > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current or not lines:
        lines.append(current)
    line_height = draw.textbbox((0, 0), "Ag", font=font)[3] + line_gap
    for index, line in enumerate(lines):
        draw.text((x, y + index * line_height), line, font=font, fill=fill)
    bottom = y + len(lines) * line_height
    return bottom, [x, y, x + width, bottom]


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
    decision_by_id = {row["edge_id"]: row for row in decisions or []}
    canvas_width = 1600
    header_height = 72
    row_height = 460
    image_size = (600, 337)
    title_font = reviewer_font(22)
    body_font = reviewer_font(16)
    small_font = reviewer_font(14)
    page_paths: list[Path] = []
    page_audits: list[dict[str, Any]] = []
    for page_number in range(1, EXPECTED_PAGE_COUNT + 1):
        rows = selection[(page_number - 1) * PAIRS_PER_PAGE : page_number * PAIRS_PER_PAGE]
        canvas = Image.new(
            "RGB", (canvas_width, header_height + row_height * len(rows)), "white"
        )
        draw = ImageDraw.Draw(canvas)
        draw.text(
            (18, 8),
            f"M0-WP12-R1 Batch B visual review | page {page_number:03d}/{EXPECTED_PAGE_COUNT:03d}",
            font=title_font,
            fill="#111827",
        )
        draw.text((18, 40), EVIDENCE_BOUNDARY, font=small_font, fill="#374151")
        audit_rows: list[dict[str, Any]] = []
        for row_index, row in enumerate(rows):
            top = header_height + row_index * row_height
            if row_index % 2:
                draw.rectangle((0, top, canvas_width, top + row_height), fill="#f3f4f6")
            decision = decision_by_id.get(row["edge_id"])
            left_image, left_label = verify_raw_record(inventory[row["left_stem"]], raw_root)
            right_image, right_label = verify_raw_record(inventory[row["right_stem"]], raw_root)
            left_render = image_with_boxes(left_image, left_label, image_size)
            right_render = image_with_boxes(right_image, right_label, image_size)
            left_xy = (18, top + 52)
            right_xy = (628, top + 52)
            canvas.paste(left_render, left_xy)
            canvas.paste(right_render, right_xy)
            header = (
                f"#{row['batch_position']} {row['edge_id']} | WP5 order {row['wp5_review_order']} | "
                f"WP12 slot {row['wp12_atlas_slot']} | {row['left_split']} → {row['right_split']}"
            )
            draw.text((18, top + 10), header, font=body_font, fill="#111827")
            draw.text(
                (18, top + 32),
                f"LEFT {row['left_stem']} | classes {row['left_class_ids']} | {row['left_image_path']}",
                font=small_font,
                fill="#1d4ed8",
            )
            draw.text(
                (628, top + 32),
                f"RIGHT {row['right_stem']} | classes {row['right_class_ids']} | {row['right_image_path']}",
                font=small_font,
                fill="#1d4ed8",
            )
            panel_x = 1245
            cursor = top + 12
            panel_width = 335
            panel_lines = [
                f"proxy context only: {row['proxy_status']}; MAE {row['thumbnail_mae']}; dHash {row['dhash_distance']}; hist {row['rgb_histogram_cosine']}",
                f"status: {ANNOTATION_STATUS if decision else 'AWAITING_PM_VISUAL_REVIEW'}",
                f"outcome: {decision['provisional_outcome'] if decision else 'BLANK'}",
                f"capture: {decision['capture_hypothesis'] if decision else 'BLANK'}",
                f"physical sign: {decision['physical_sign_hypothesis'] if decision else 'BLANK'}",
                f"confidence: {decision['confidence'] if decision else 'BLANK'}",
                f"rationale: {decision['rationale'] if decision else 'BLANK'}",
                "metadata: none for creator/session/physical-sign identity",
            ]
            text_bounds: list[list[int]] = []
            for index, text in enumerate(panel_lines):
                cursor, bounds = draw_wrapped(
                    draw,
                    text,
                    panel_x,
                    cursor,
                    panel_width,
                    small_font,
                    "#047857" if decision and index >= 1 else "#111827",
                )
                cursor += 4
            text_bounds.append(bounds)
            if cursor > top + row_height - 6:
                raise RuntimeError(f"WP12 atlas text overflow for {row['edge_id']}")
            audit_rows.append(
                {
                    "batch_position": int(row["batch_position"]),
                    "edge_id": row["edge_id"],
                    "slot": int(row["wp12_atlas_slot"]),
                    "left_stem": row["left_stem"],
                    "right_stem": row["right_stem"],
                    "left_bounds": [*left_xy, left_xy[0] + image_size[0], left_xy[1] + image_size[1]],
                    "right_bounds": [*right_xy, right_xy[0] + image_size[0], right_xy[1] + image_size[1]],
                    "text_bounds": [panel_x, top + 12, panel_x + panel_width, cursor],
                    "decision_recorded": decision is not None,
                    "all_bounds_fit": cursor <= top + row_height - 6,
                    "text_complete": True,
                    "bbox_overlay_rendered": True,
                }
            )
        page_path = assets_dir / f"page_{page_number:03d}.jpg"
        canvas.save(page_path, format="JPEG", quality=90, optimize=True, subsampling=1)
        page_paths.append(page_path)
        page_audits.append(
            {
                "page": page_number,
                "path": f"{ASSETS_RELATIVE_PATH}/page_{page_number:03d}.jpg",
                "width": canvas.width,
                "height": canvas.height,
                "row_count": len(rows),
                "rows": audit_rows,
            }
        )
    body = [
        "<!doctype html><meta charset='utf-8'><title>M0-WP12-R1 Batch B atlas</title>",
        "<style>body{font-family:system-ui;margin:2rem;max-width:1200px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #bbb;padding:.4rem}img{max-width:100%}</style>",
        "<h1>M0-WP12-R1 cross-split manual review — Batch B</h1>",
        f"<p>{html.escape(EVIDENCE_BOUNDARY)}</p>",
        "<p>Every pair must be judged from both displayed source images. Proxy fields are context only.</p>",
        "<table><thead><tr><th>#</th><th>Edge</th><th>WP5 order</th><th>Stems/splits</th><th>Atlas</th><th>Outcome</th><th>Confidence</th></tr></thead><tbody>",
    ]
    for row in selection:
        decision = decision_by_id.get(row["edge_id"])
        page = math.ceil(int(row["batch_position"]) / PAIRS_PER_PAGE)
        body.append(
            f"<tr id='{row['edge_id']}'><td>{row['batch_position']}</td><td>{row['edge_id']}</td>"
            f"<td>{row['wp5_review_order']}</td><td>{row['left_stem']} [{row['left_split']}] / {row['right_stem']} [{row['right_split']}]</td>"
            f"<td><a href='page_{page:03d}.jpg'>page {page:03d}, slot {row['wp12_atlas_slot']}</a></td>"
            f"<td>{html.escape(decision['provisional_outcome'] if decision else 'BLANK')}</td>"
            f"<td>{html.escape(decision['confidence'] if decision else 'BLANK')}</td></tr>"
        )
    body.append("</tbody></table>")
    (assets_dir / "index.html").write_text("\n".join(body) + "\n", encoding="utf-8")
    layout = {
        "schema_version": 1,
        "status": "PASS_COMPLETE_250_PAIR_COVERAGE_TEXT_BOUNDS_AND_BBOX_CONTEXT",
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "page_count": EXPECTED_PAGE_COUNT,
        "pair_count": EXPECTED_SELECTION_COUNT,
        "pairs_per_page": PAIRS_PER_PAGE,
        "all_headers_complete": True,
        "all_text_complete": True,
        "all_bounds_fit": True,
        "all_bbox_context_rendered": True,
        "all_decisions_recorded": decisions is not None,
        "pages": page_audits,
    }
    return [assets_dir / "index.html", *page_paths], layout


def verify_regenerated_atlas_and_layout(
    repo_root: Path,
    raw_root: Path,
    selection: list[dict[str, str]],
    inventory: dict[str, dict[str, str]],
    decisions: list[dict[str, Any]],
    packaged_layout: dict[str, Any],
) -> None:
    packaged_assets = repo_root / ASSETS_RELATIVE_PATH
    verify_exact_atlas_roster(packaged_assets)
    with tempfile.TemporaryDirectory(prefix="wp12-r1-verify-") as temporary:
        temporary_root = Path(temporary)
        regenerated_assets = temporary_root / "batch_b"
        _paths, regenerated_layout = render_atlas(
            selection,
            inventory,
            raw_root,
            regenerated_assets,
            decisions,
        )
        verify_exact_atlas_roster(regenerated_assets)
        for name in expected_atlas_names():
            if (packaged_assets / name).read_bytes() != (
                regenerated_assets / name
            ).read_bytes():
                raise ValueError(
                    f"WP12 atlas bytes differ from deterministic regeneration: {name}"
                )
        regenerated_layout_path = temporary_root / "layout_audit.json"
        write_json(regenerated_layout_path, regenerated_layout)
        if packaged_layout != regenerated_layout:
            raise ValueError("WP12 layout differs from deterministic regeneration")
        if (repo_root / LAYOUT_RELATIVE_PATH).read_bytes() != (
            regenerated_layout_path.read_bytes()
        ):
            raise ValueError(
                "WP12 layout bytes differ from deterministic regeneration"
            )


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
        "canonical_wp5_pending_unchanged": EXPECTED_WP5_PENDING_COUNT,
        "pending_outside_wp7_wp12_overlays": EXPECTED_WP5_PENDING_COUNT
        - EXPECTED_BATCH_A_COUNT
        - EXPECTED_SELECTION_COUNT,
        "cross_split_pending_outside_wp7_wp12_overlays": EXPECTED_WP5_CROSS_SPLIT_COUNT
        - 5
        - EXPECTED_BATCH_A_COUNT
        - EXPECTED_SELECTION_COUNT,
        "all_wp5_sequences_pending": EXPECTED_WP5_SEQUENCE_COUNT,
        "d02_a_preferred": True,
        "d02_b_budget_approved": False,
        "final_group_truth_created": False,
        "split_assignment_created": False,
        "training_authorized": False,
        "gate0": "BLOCKED",
        "evidence_boundary": EVIDENCE_BOUNDARY,
    }


def render_report(summary: dict[str, Any], annotation_payload: dict[str, Any]) -> str:
    outcomes = "\n".join(
        f"- `{name}`: {count}" for name, count in summary["outcome_counts"].items()
    )
    confidence = "\n".join(
        f"- `{name}`: {count}" for name, count in summary["confidence_counts"].items()
    )
    captures = "\n".join(
        f"- `{name}`: {count}" for name, count in summary["capture_hypothesis_counts"].items()
    )
    physical = "\n".join(
        f"- `{name}`: {count}"
        for name, count in summary["physical_sign_hypothesis_counts"].items()
    )
    return f"""# M0-WP12-R1 — D02-B cross-split manual review, Batch B

Status: `{PACKAGE_STATUS}`  
Boundary: `{EVIDENCE_BOUNDARY}`

This package records one PM/Codex provisional visual pass over exactly 250 canonical WP5 pending
cross-split pairs. It does not approve D-02, does not create final/transitive group truth or a split,
and does not authorize training. D02-A creator/session metadata remains preferred.

## Selection and review protocol

- Selection: exact next 250 unique canonical WP5 rows with `cross_split=True` and
  `review_status=PENDING`, preserving WP5 review order and excluding the exact 100-edge WP7 Batch-A
  roster. Canonical WP5 reviewed rows are ineligible by construction.
- Selected edge range: `{summary['first_edge']}` through `{summary['last_edge']}` in Batch-B order.
- Source coverage: 500 endpoint rows with {EXPECTED_SELECTED_ENDPOINT_BOX_COUNT} total boxes;
  quarantined stem `{QUARANTINED_STEM}` is absent.
- Reviewer: `{annotation_payload['reviewer']}` at `{annotation_payload['reviewed_at']}`.
- All 250 pairs/500 raw frames were directly inspected in the dedicated 50-page WP12 atlas before
  annotation. Proxy fields were context only.
- Creator/session/physical-sign identity metadata: unavailable for every record.

## R1 repair lineage

- Independent QA rejected the pre-repair manifest `{PRE_REPAIR_MANIFEST_SHA256}` because the
  verifier did not semantically bind atlas bytes/layout to deterministic regeneration and did not
  pin the approved PM review-notes source.
- R1 requires the exact 51-file atlas roster, regenerates the index/50 JPEG pages and layout audit
  in an isolated temporary directory for byte/deep comparison, and pins review-notes SHA-256
  `{EXPECTED_REVIEW_NOTES_SHA256}` plus the approved decision counts and unresolved edge IDs.
- Status remains awaiting independent QA. This repair does not change any PM visual decision.
- Independent QA found 0 blind capture-decision disagreements and visually accepted 50/50 pages;
  its package verdict remained FAIL solely because of the three verifier blockers repaired here.

## Provisional capture outcomes

{outcomes}

Capture-hypothesis count cross-check:

{captures}

## Provisional physical-sign outcomes

{physical}

## Confidence

{confidence}

## Remaining workload and governance

- Canonical WP5 remains unchanged at {summary['canonical_wp5_pending_unchanged']} PENDING edges until this separate package receives QA review.
- Outside the WP7 and WP12 overlays, {summary['pending_outside_wp7_wp12_overlays']} canonical
  PENDING edges remain without either overlay; {summary['cross_split_pending_outside_wp7_wp12_overlays']}
  of those are cross-split.
- All {summary['all_wp5_sequences_pending']} WP5 sequences remain PENDING.
- Any future PM/QA disagreement remains unresolved/uncertain and cannot form a positive component.
- D-02 remains PENDING; Gate 0 remains BLOCKED; `training_authorized=false`.

## Artifacts

- Decisions: `{ANNOTATIONS_RELATIVE_PATH}`.
- Selection: `{SELECTION_RELATIVE_PATH}`.
- Source lineage: `{LINEAGE_RELATIVE_PATH}`.
- Layout audit: `{LAYOUT_RELATIVE_PATH}`.
- Atlas: `{ASSETS_RELATIVE_PATH}/index.html` and {EXPECTED_PAGE_COUNT} JPEG pages.
- Manifest: `{MANIFEST_RELATIVE_PATH}`.
"""


def build_manifest(repo_root: Path) -> dict[str, Any]:
    sources = [
        relative_record(path, repo_root, item_id)
        for item_id, path, _pinned in source_contract(repo_root)
    ]
    artifacts = [
        relative_record(path, repo_root, item_id)
        for item_id, path in artifact_contract(repo_root)
    ]
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
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
        "source_count": len(sources),
        "artifact_count": len(artifacts),
        "total_artifact_bytes": sum(record["size"] for record in artifacts),
        "sources": sources,
        "artifacts": artifacts,
    }


def contract_pairs(
    contract: list[tuple[str, Path]] | list[tuple[str, Path, str | None]],
    repo_root: Path,
) -> list[tuple[str, str]]:
    return [
        (item[0], item[1].relative_to(repo_root).as_posix())
        for item in contract
    ]


def validate_manifest_collection(
    payload: dict[str, Any],
    name: str,
    expected: list[tuple[str, str]],
    repo_root: Path,
    errors: list[str],
) -> list[dict[str, Any]]:
    value = payload.get(name)
    if not isinstance(value, list):
        errors.append(f"{name} must be a list")
        return []
    records: list[dict[str, Any]] = []
    pairs: list[tuple[str, str]] = []
    for index, record in enumerate(value):
        if not isinstance(record, dict):
            errors.append(f"{name}[{index}] must be an object")
            continue
        if set(record) != {"id", "path", "sha256", "size"}:
            errors.append(f"{name}[{index}] fields differ from contract")
        item_id = record.get("id")
        path_value = record.get("path")
        digest = record.get("sha256")
        size = record.get("size")
        if isinstance(item_id, str) and isinstance(path_value, str):
            pairs.append((item_id, path_value))
        if not isinstance(path_value, str):
            errors.append(f"{name}[{index}].path invalid")
        else:
            try:
                safe_child(repo_root, path_value)
            except (ValueError, OSError) as exc:
                errors.append(str(exc))
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            errors.append(f"{name}[{index}].sha256 invalid")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            errors.append(f"{name}[{index}].size invalid")
        records.append(record)
    if len(set(item for item, _path in pairs)) != len(pairs):
        errors.append(f"duplicate {name} IDs")
    if len(set(path for _item, path in pairs)) != len(pairs):
        errors.append(f"duplicate {name} paths")
    if pairs != expected:
        errors.append(f"{name} roster/order differs from canonical contract")
    return records


def verify_manifest(manifest_path: Path, repo_root: Path, raw_root: Path) -> dict[str, Any]:
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
        errors.append("manifest top-level fields differ from WP12 schema")
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
            raise ValueError("WP12 selection differs from independently derived canonical next 250")
        expected_lineage = derive_lineage(expected_selection, inventory, raw_root)
        actual_lineage = read_csv(repo_root / LINEAGE_RELATIVE_PATH)
        if actual_lineage != expected_lineage:
            raise ValueError("WP12 source lineage differs from the canonical 500 endpoints")
        annotation_payload, decisions = load_annotations(repo_root, expected_selection)
        layout = json.loads((repo_root / LAYOUT_RELATIVE_PATH).read_text(encoding="utf-8"))
        if (
            layout.get("schema_version") != 1
            or layout.get("status") != "PASS_COMPLETE_250_PAIR_COVERAGE_TEXT_BOUNDS_AND_BBOX_CONTEXT"
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
            raise ValueError("WP12 layout audit contract mismatch")
        layout_ids: list[str] = []
        for page_number, page in enumerate(layout["pages"], start=1):
            if (
                page.get("page") != page_number
                or page.get("path") != f"{ASSETS_RELATIVE_PATH}/page_{page_number:03d}.jpg"
                or page.get("row_count") != PAIRS_PER_PAGE
                or len(page.get("rows", [])) != PAIRS_PER_PAGE
            ):
                raise ValueError(f"WP12 atlas page {page_number} identity/coverage mismatch")
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
                    raise ValueError(f"WP12 atlas page/slot mismatch for {expected['edge_id']}")
                layout_ids.append(row["edge_id"])
        if layout_ids != [row["edge_id"] for row in expected_selection]:
            raise ValueError("WP12 layout order differs from canonical selection")
        regenerated_annotations = annotation_payload_from_notes(
            load_review_notes(repo_root, expected_selection), expected_selection
        )
        if annotation_payload != regenerated_annotations:
            raise ValueError("WP12 annotations differ from the bound PM visual-review notes")
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
            raise ValueError("WP12 report differs from verified decisions/summary")
        forbidden = {"group_id", "final_group_id", "assigned_split", "approved_split"}
        if forbidden & set(actual_selection[0]):
            raise ValueError("WP12 selection contains final grouping/split fields")
        if any(forbidden & set(decision) for decision in decisions):
            raise ValueError("WP12 decisions contain final grouping/split fields")
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


def prepare(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    raw_root = raw_root.resolve()
    for item_id, path, pinned_hash in source_contract(repo_root)[:-2]:
        if not path.is_file() or (pinned_hash is not None and sha256_file(path) != pinned_hash):
            raise ValueError(f"WP12 prepare source mismatch: {item_id}")
    validate_governance(repo_root)
    selection, inventory = derive_selection(repo_root, raw_root)
    write_csv(repo_root / SELECTION_RELATIVE_PATH, selection, SELECTION_FIELDS)
    write_csv(
        repo_root / LINEAGE_RELATIVE_PATH,
        derive_lineage(selection, inventory, raw_root),
        LINEAGE_FIELDS,
    )
    _paths, layout = render_atlas(
        selection, inventory, raw_root, repo_root / ASSETS_RELATIVE_PATH, None
    )
    write_json(repo_root / LAYOUT_RELATIVE_PATH, layout)
    return {
        "status": "WP12_BATCH_B_PREPARED_AWAITING_PM_VISUAL_REVIEW",
        "selection_count": len(selection),
        "page_count": layout["page_count"],
        "first_edge": selection[0]["edge_id"],
        "last_edge": selection[-1]["edge_id"],
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
    notes = load_review_notes(repo_root, selection)
    write_json(
        repo_root / ANNOTATIONS_RELATIVE_PATH,
        annotation_payload_from_notes(notes, selection),
    )
    annotation_payload, decisions = load_annotations(repo_root, selection)
    before_raw = {
        (row[side], side): sha256_file(safe_child(raw_root, row[side]))
        for row in selection
        for side in ("left_image_path", "right_image_path", "left_label_path", "right_label_path")
    }
    write_csv(repo_root / SELECTION_RELATIVE_PATH, selection, SELECTION_FIELDS)
    write_csv(
        repo_root / LINEAGE_RELATIVE_PATH,
        derive_lineage(selection, inventory, raw_root),
        LINEAGE_FIELDS,
    )
    _paths, layout = render_atlas(
        selection, inventory, raw_root, repo_root / ASSETS_RELATIVE_PATH, decisions
    )
    write_json(repo_root / LAYOUT_RELATIVE_PATH, layout)
    summary = summary_from_decisions(decisions)
    (repo_root / REPORT_RELATIVE_PATH).write_text(
        render_report(summary, annotation_payload), encoding="utf-8"
    )
    after_raw = {
        (row[side], side): sha256_file(safe_child(raw_root, row[side]))
        for row in selection
        for side in ("left_image_path", "right_image_path", "left_label_path", "right_label_path")
    }
    if before_raw != after_raw:
        raise RuntimeError("WP12 raw sources changed during build")
    manifest = build_manifest(repo_root)
    write_json(repo_root / MANIFEST_RELATIVE_PATH, manifest)
    result = verify_manifest(repo_root / MANIFEST_RELATIVE_PATH, repo_root, raw_root)
    if not result["valid"]:
        raise RuntimeError(f"WP12 package verification failed: {result['errors']}")
    return {
        "status": PACKAGE_STATUS,
        "selection_count": EXPECTED_SELECTION_COUNT,
        "selected_endpoint_box_count": EXPECTED_SELECTED_ENDPOINT_BOX_COUNT,
        "quarantined_stem_0248_selected": False,
        "page_count": EXPECTED_PAGE_COUNT,
        "source_count": manifest["source_count"],
        "artifact_count": manifest["artifact_count"],
        "manifest_sha256": sha256_file(repo_root / MANIFEST_RELATIVE_PATH),
        "outcome_counts": summary["outcome_counts"],
        "confidence_counts": summary["confidence_counts"],
        "canonical_wp5_pending_unchanged": EXPECTED_WP5_PENDING_COUNT,
        "pending_outside_wp7_wp12_overlays": summary["pending_outside_wp7_wp12_overlays"],
        "cross_split_pending_outside_wp7_wp12_overlays": summary[
            "cross_split_pending_outside_wp7_wp12_overlays"
        ],
        "all_wp5_sequences_pending": EXPECTED_WP5_SEQUENCE_COUNT,
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
        manifest = args.manifest
        if not manifest.is_absolute():
            manifest = repo_root / manifest
        result = verify_manifest(manifest, repo_root, raw_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if args.command != "verify" or result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
