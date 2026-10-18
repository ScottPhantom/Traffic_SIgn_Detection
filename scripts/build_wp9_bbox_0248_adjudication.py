# ruff: noqa: E501
"""Build and verify the M0-WP9 bbox-0248 decision-support package."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

PACKAGE_STATUS = "M0_WP9_AWAITING_QA_DECISION_SUPPORT_ONLY"
EVIDENCE_BOUNDARY = "DECISION_SUPPORT_ONLY_NO_RAW_OVERWRITE_NO_RELABEL_NO_SPLIT_NO_TRAINING"
RECOMMENDATION = "QUARANTINE_FROM_TRAINING_PENDING_OWNER_DECISION"
RAW_HANDLING = "KEEP_RAW_IMMUTABLE_FOR_PROVENANCE"
DERIVED_ROLE = "REVIEW_ONLY_NOT_APPROVED_TRAINING_LABEL"

CONTRACT_RELATIVE_PATH = "references/dataset01/wp9_bbox_0248_adjudication_contract.json"
MANIFEST_RELATIVE_PATH = "docs/review/generated/wp9_bbox_0248_manifest.json"
ADJUDICATION_RELATIVE_PATH = "docs/review/generated/wp9_bbox_0248_adjudication.json"
DERIVED_LABEL_RELATIVE_PATH = "docs/review/generated/wp9_bbox_0248_derived_candidate.txt"
LAYOUT_RELATIVE_PATH = "docs/review/generated/wp9_bbox_0248_layout_audit.json"
REPORT_RELATIVE_PATH = "docs/review/wp9_bbox_0248_adjudication_report.md"
VISUAL_RELATIVE_PATH = "docs/review/assets/wp9/bbox_0248_review.png"

EXPECTED_RAW_LINES = [
    "49 0.992188 0.345370 0.053125 0.101852",
    "49 0.333854 0.342593 0.046875 0.088889",
]
EXPECTED_DERIVED_LINES = [
    "49 0.982812750 0.345370000 0.034374500 0.101852000",
    EXPECTED_RAW_LINES[1],
]
EXPECTED_RAW_XYXY = [927.00048, 158.99976, 978.00048, 213.99984]
EXPECTED_CLIPPED_XYXY = [927.00048, 158.99976, 960.0, 213.99984]
EXPECTED_OVERFLOW = 18.00048

EXPECTED_PINNED_HASHES = {
    "contract": "0b0a87e1b1b8f4c1c2cac739eb87aa6441ec1cbfbdbad264a0f391231c002da5",
    "raw_image_0247": "c439730e326465b2a05f8279312581c0890ab8c10a2279289c9daa1e1aa502cc",
    "raw_image_0248": "07eab2035dc10b7b08be71d76c3c32ffdb960722839414f1e474da20c3ad0cbd",
    "raw_label_0248": "f4ec410f7bff3ee03f6110308e8e95f57c92bcc7ebf45ff3affcfd885b419c77",
    "raw_image_0249": "7225644c63178646ba5a19a8ff1248ba08b65f792e147613d38deeb0346f230b",
    "wp1_manifest": "28adbf21dd2057fe5fc7999daccaa52d1201ea0459ef1bb7475a780ed85c51c6",
    "image_inventory": "d45aa7f398a040c44cbc040f4ec005d7e5a8ef50586e905315f76c792ca29022",
    "source_preservation": "5ca3e769b9197cad19bcb75f553dd59fee6e3035e0cc86cd9693737f84a713d7",
    "wp2_manifest": "506ec141bef032282f90b3d35741ece49a43fed617c3dea93863d4c32330a505",
    "wp2_bbox_review": "e1b8cc2c3a6d16e8dbff847b43e33450272e4dda21f46e6708e3aff5b1dba25f",
    "wp2_bbox_visual": "3c3e3b872e7afa189d0307e2b9e3e637e275f6295ad1e793c0d797fd4325f598",
    "wp4_manifest": "c60c09018900071cc66d8bc01db32300f4efc6a4316bda9f506819026400db1c",
    "wp4_lineage": "c9e90b01ef3be78797b58405d9c7a7fb9f7f8384498b876af23a25b22e0a8d19",
    "wp4_atlas_page_013": "55d38ab22415a4de5b70048a4e70fb0ec11a3ab6fa789ea957c0f2418f3e4ac4",
    "grouping_proxy_edges": "801e89db137154086496f37bc38b9659596c61e4a881734e80731aeaf2ded15c",
    "decision_status": "87d81262e907bb1c479cfac6535e7b3f67a368c371e96b810aa02f2e92d0d72c",
    "wp8_manifest": "9d8fc460b8162874b4082940b0e7f3ceb174c068a92378974ebd93b55da20348",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def safe_child(root: Path, relative_value: str) -> Path:
    relative = Path(relative_value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"unsafe relative path: {relative_value}")
    resolved_root = root.resolve()
    candidate = resolved_root
    for part in relative.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ValueError(f"symlink path is not allowed: {relative_value}")
    resolved = candidate.resolve()
    resolved.relative_to(resolved_root)
    return resolved


def default_raw_root(repo_root: Path) -> Path:
    review = json.loads((repo_root / "docs/review/generated/bbox_0248_review.json").read_text(encoding="utf-8"))
    image_path = Path(review["source"]["image_path"])
    if image_path.name != "0248.jpg" or image_path.parent.name != "images" or image_path.parent.parent.name != "archive":
        raise ValueError("WP2 bbox review contains an unexpected raw image path")
    return image_path.parents[2]


def source_contract(repo_root: Path, raw_root: Path) -> list[tuple[str, str, str, Path, str]]:
    generated = repo_root / "docs/review/generated"
    audit = repo_root / "results/data_audit/DATASET01_052bc980a7206f8d"
    return [
        ("contract", "repo", CONTRACT_RELATIVE_PATH, repo_root / CONTRACT_RELATIVE_PATH, EXPECTED_PINNED_HASHES["contract"]),
        ("raw_image_0247", "raw", "archive/images/0247.jpg", raw_root / "archive/images/0247.jpg", EXPECTED_PINNED_HASHES["raw_image_0247"]),
        ("raw_image_0248", "raw", "archive/images/0248.jpg", raw_root / "archive/images/0248.jpg", EXPECTED_PINNED_HASHES["raw_image_0248"]),
        ("raw_label_0248", "raw", "archive/labels/0248.txt", raw_root / "archive/labels/0248.txt", EXPECTED_PINNED_HASHES["raw_label_0248"]),
        ("raw_image_0249", "raw", "archive/images/0249.jpg", raw_root / "archive/images/0249.jpg", EXPECTED_PINNED_HASHES["raw_image_0249"]),
        ("wp1_manifest", "repo", "results/data_audit/DATASET01_052bc980a7206f8d/wp1_artifact_manifest.json", audit / "wp1_artifact_manifest.json", EXPECTED_PINNED_HASHES["wp1_manifest"]),
        ("image_inventory", "repo", "results/data_audit/DATASET01_052bc980a7206f8d/image_inventory.csv", audit / "image_inventory.csv", EXPECTED_PINNED_HASHES["image_inventory"]),
        ("source_preservation", "repo", "results/data_audit/DATASET01_052bc980a7206f8d/source_preservation_proof.json", audit / "source_preservation_proof.json", EXPECTED_PINNED_HASHES["source_preservation"]),
        ("wp2_manifest", "repo", "docs/review/generated/wp2_generated_manifest.json", generated / "wp2_generated_manifest.json", EXPECTED_PINNED_HASHES["wp2_manifest"]),
        ("wp2_bbox_review", "repo", "docs/review/generated/bbox_0248_review.json", generated / "bbox_0248_review.json", EXPECTED_PINNED_HASHES["wp2_bbox_review"]),
        ("wp2_bbox_visual", "repo", "docs/review/assets/bbox_0248_review.png", repo_root / "docs/review/assets/bbox_0248_review.png", EXPECTED_PINNED_HASHES["wp2_bbox_visual"]),
        ("wp4_manifest", "repo", "docs/review/generated/wp4_qcvn_manifest.json", generated / "wp4_qcvn_manifest.json", EXPECTED_PINNED_HASHES["wp4_manifest"]),
        ("wp4_lineage", "repo", "docs/review/generated/wp4_qcvn_source_lineage.csv", generated / "wp4_qcvn_source_lineage.csv", EXPECTED_PINNED_HASHES["wp4_lineage"]),
        ("wp4_atlas_page_013", "repo", "docs/review/assets/wp4/qcvn_taxonomy_atlas/page_013.jpg", repo_root / "docs/review/assets/wp4/qcvn_taxonomy_atlas/page_013.jpg", EXPECTED_PINNED_HASHES["wp4_atlas_page_013"]),
        ("grouping_proxy_edges", "repo", "docs/review/generated/grouping_proxy_edges.csv", generated / "grouping_proxy_edges.csv", EXPECTED_PINNED_HASHES["grouping_proxy_edges"]),
        ("decision_status", "repo", "docs/review/decision_status.json", repo_root / "docs/review/decision_status.json", EXPECTED_PINNED_HASHES["decision_status"]),
        ("wp8_manifest", "repo", "docs/review/generated/wp8_taxonomy_manifest.json", generated / "wp8_taxonomy_manifest.json", EXPECTED_PINNED_HASHES["wp8_manifest"]),
    ]


def artifact_contract(repo_root: Path) -> list[tuple[str, str, Path]]:
    return [
        ("adjudication", ADJUDICATION_RELATIVE_PATH, repo_root / ADJUDICATION_RELATIVE_PATH),
        ("derived_label_candidate", DERIVED_LABEL_RELATIVE_PATH, repo_root / DERIVED_LABEL_RELATIVE_PATH),
        ("layout_audit", LAYOUT_RELATIVE_PATH, repo_root / LAYOUT_RELATIVE_PATH),
        ("report", REPORT_RELATIVE_PATH, repo_root / REPORT_RELATIVE_PATH),
        ("review_visual", VISUAL_RELATIVE_PATH, repo_root / VISUAL_RELATIVE_PATH),
    ]


def verify_pinned_sources(repo_root: Path, raw_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item_id, root_id, relative, path, expected_hash in source_contract(repo_root, raw_root):
        if not path.is_file():
            raise FileNotFoundError(path)
        actual = sha256_file(path)
        if actual != expected_hash:
            raise ValueError(f"pinned source hash mismatch: {item_id}")
        records.append({"id": item_id, "root": root_id, "path": relative, "sha256": actual, "size": path.stat().st_size})
    return records


def almost_equal(actual: float, expected: float, tolerance: float = 1e-9) -> bool:
    return abs(actual - expected) <= tolerance


def parse_raw_label(path: Path) -> list[tuple[int, float, float, float, float]]:
    raw = path.read_bytes()
    if raw != ("\r\n".join(EXPECTED_RAW_LINES) + "\r\n").encode("ascii"):
        raise ValueError("raw label bytes, line order, class, or geometry differ from the pinned contract")
    rows: list[tuple[int, float, float, float, float]] = []
    for line in raw.decode("ascii").splitlines():
        fields = line.split()
        if len(fields) != 5:
            raise ValueError("raw label must contain five fields per line")
        rows.append((int(fields[0]), *(float(value) for value in fields[1:])))
    return rows


def xyxy(row: tuple[int, float, float, float, float], width: int, height: int) -> list[float]:
    _class_id, x_center, y_center, box_width, box_height = row
    return [
        (x_center - box_width / 2) * width,
        (y_center - box_height / 2) * height,
        (x_center + box_width / 2) * width,
        (y_center + box_height / 2) * height,
    ]


def validate_governance(repo_root: Path) -> None:
    status = json.loads((repo_root / "docs/review/decision_status.json").read_text(encoding="utf-8"))
    decision = status["decisions"]["G0.4-bbox-0248"]
    if status.get("gate0") != "BLOCKED" or status.get("training_authorized") is not False:
        raise ValueError("Gate 0 governance changed")
    if decision.get("status") != "PENDING" or decision.get("selected_option") is not None:
        raise ValueError("G0.4 owner decision must remain PENDING with no selected option")
    if decision.get("allowed_options") != [
        "keep_raw_as_warning",
        "create_separate_clipped_derived_annotation",
        "quarantine_image_from_approved_dataset",
    ]:
        raise ValueError("G0.4 allowed options differ from the decision contract")


def validate_contract(repo_root: Path) -> dict[str, Any]:
    payload = json.loads((repo_root / CONTRACT_RELATIVE_PATH).read_text(encoding="utf-8"))
    if payload.get("package") != "M0-WP9" or payload.get("status") != "PROPOSAL_ONLY_AWAITING_QA":
        raise ValueError("WP9 contract identity/status mismatch")
    target = payload.get("target", {})
    if target != {
        "stem": "0248", "split": "train", "class_id": 49, "dataset_code": "P.124c",
        "image_width": 960, "image_height": 540, "label_line_number": 1, "label_line_index": 0,
    }:
        raise ValueError("WP9 contract target differs from canonical stem/class/line/index")
    raw = payload.get("raw_annotation", {})
    if raw.get("yolo") != [0.992188, 0.34537, 0.053125, 0.101852]:
        raise ValueError("WP9 contract raw YOLO geometry mismatch")
    if raw.get("pixel_xyxy") != EXPECTED_RAW_XYXY or raw.get("right_overflow_px") != EXPECTED_OVERFLOW:
        raise ValueError("WP9 contract raw pixel geometry/overflow mismatch")
    finding = payload.get("visual_finding", {})
    if finding.get("finding") != "IMAGE_EDGE_TRUNCATED_OBJECT_WITH_RAW_BOX_EXTENDING_BEYOND_RIGHT_BOUNDARY" or finding.get("confidence") != "HIGH":
        raise ValueError("WP9 visual finding/confidence mismatch")
    recommendation = payload.get("recommendation", {})
    if recommendation.get("proposed_disposition") != RECOMMENDATION or recommendation.get("raw_handling") != RAW_HANDLING or recommendation.get("derived_candidate_role") != DERIVED_ROLE:
        raise ValueError("WP9 recommendation boundary mismatch")
    candidate = payload.get("derived_clip_candidate", {})
    if candidate.get("operation") != "CLIP_X_MAX_TO_IMAGE_WIDTH_ONLY" or candidate.get("line_1") != EXPECTED_DERIVED_LINES[0] or candidate.get("line_2") != EXPECTED_DERIVED_LINES[1] or candidate.get("line_1_pixel_xyxy") != EXPECTED_CLIPPED_XYXY or candidate.get("source_raw_label_must_remain_unchanged") is not True:
        raise ValueError("WP9 derived candidate contract mismatch")
    governance = payload.get("governance", {})
    expected_governance = {
        "decision_id": "G0.4-bbox-0248", "decision_status": "PENDING", "selected_option": None,
        "gate0": "BLOCKED", "relabel_authorized": False, "split_authorized": False,
        "training_authorized": False,
    }
    if governance != expected_governance or payload.get("evidence_boundary") != EVIDENCE_BOUNDARY:
        raise ValueError("WP9 governance/evidence boundary mismatch")
    return payload


def derive_facts(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    verify_pinned_sources(repo_root, raw_root)
    validate_governance(repo_root)
    contract = validate_contract(repo_root)
    rows = parse_raw_label(raw_root / "archive/labels/0248.txt")
    if len(rows) != 2 or rows[0][0] != 49 or rows[1][0] != 49:
        raise ValueError("raw label class/count mismatch")
    with Image.open(raw_root / "archive/images/0248.jpg") as image:
        if image.size != (960, 540) or image.format != "JPEG" or image.mode != "RGB":
            raise ValueError("raw 0248 image contract mismatch")
    raw_pixels = xyxy(rows[0], 960, 540)
    if not all(almost_equal(actual, expected) for actual, expected in zip(raw_pixels, EXPECTED_RAW_XYXY, strict=True)):
        raise ValueError("raw label does not derive the expected pixel geometry")
    overflow = max(0.0, raw_pixels[2] - 960)
    if not almost_equal(overflow, EXPECTED_OVERFLOW):
        raise ValueError("raw label right overflow differs from the expected 18.00048 px")

    review = json.loads((repo_root / "docs/review/generated/bbox_0248_review.json").read_text(encoding="utf-8"))
    first = review["boxes"][0]
    if first.get("class_id") != 49 or first.get("line") != 1 or first.get("review_status") != "PENDING":
        raise ValueError("WP2 bbox row identity/status mismatch")
    review_pixels = [first["pixels"][key] for key in ("x_min", "y_min", "x_max", "y_max")]
    if not all(almost_equal(actual, expected) for actual, expected in zip(review_pixels, EXPECTED_RAW_XYXY, strict=True)):
        raise ValueError("WP2 bbox pixel geometry mismatch")
    if not almost_equal(first["pixels"]["overflow_right_px"], EXPECTED_OVERFLOW):
        raise ValueError("WP2 bbox overflow mismatch")

    inventory = read_csv(repo_root / "results/data_audit/DATASET01_052bc980a7206f8d/image_inventory.csv")
    inventory_rows = {row["stem"]: row for row in inventory if row["stem"] in {"0247", "0248", "0249"}}
    if set(inventory_rows) != {"0247", "0248", "0249"}:
        raise ValueError("inventory context roster mismatch")
    row_0248 = inventory_rows["0248"]
    if (row_0248["image_sha256"], row_0248["label_sha256"], row_0248["width"], row_0248["height"], row_0248["box_count"], row_0248["class_ids"], row_0248["split"]) != (
        EXPECTED_PINNED_HASHES["raw_image_0248"], EXPECTED_PINNED_HASHES["raw_label_0248"], "960", "540", "2", "49", "train",
    ):
        raise ValueError("inventory 0248 row mismatch")

    lineage = read_csv(repo_root / "docs/review/generated/wp4_qcvn_source_lineage.csv")
    matches = [row for row in lineage if row["stem"] == "0248" and row["class_id"] == "49"]
    if len(matches) != 1:
        raise ValueError("WP4 lineage must contain one class-49 representative for stem 0248")
    lineage_row = matches[0]
    if lineage_row["label_line_number"] != "1" or lineage_row["slot_index"] != "1" or lineage_row["source_bbox_within_image"] != "False" or not almost_equal(float(lineage_row["source_bbox_overflow_right"]), EXPECTED_OVERFLOW):
        raise ValueError("WP4 lineage line/slot/overflow mismatch")

    edges = read_csv(repo_root / "docs/review/generated/grouping_proxy_edges.csv")
    context_edges = [row for row in edges if (row["left_stem"], row["right_stem"]) in {("0247", "0248"), ("0248", "0249")}]
    if [(row["left_stem"], row["right_stem"]) for row in context_edges] != [("0247", "0248"), ("0248", "0249")]:
        raise ValueError("0247/0249 context edge roster/order mismatch")
    if any(row["proxy_sequence_id"] != "proxy_sequence_0050" for row in context_edges):
        raise ValueError("0247/0249 context is not the expected proxy sequence")

    proof = json.loads((repo_root / "results/data_audit/DATASET01_052bc980a7206f8d/source_preservation_proof.json").read_text(encoding="utf-8"))
    if proof.get("unchanged") is not True:
        raise ValueError("source preservation proof is not unchanged=true")

    return {
        "contract": contract,
        "raw_rows": rows,
        "raw_pixels": raw_pixels,
        "overflow": overflow,
        "inventory": inventory_rows,
        "context_edges": context_edges,
    }


def adjudication_payload(repo_root: Path, raw_root: Path, facts: dict[str, Any]) -> dict[str, Any]:
    inventory = facts["inventory"]
    return {
        "schema_version": 1,
        "package": "M0-WP9",
        "status": PACKAGE_STATUS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "target": {
            "stem": "0248", "split": "train", "class_id": 49, "dataset_code": "P.124c",
            "image": {"path": "archive/images/0248.jpg", "sha256": EXPECTED_PINNED_HASHES["raw_image_0248"], "width": 960, "height": 540},
            "label": {"path": "archive/labels/0248.txt", "sha256": EXPECTED_PINNED_HASHES["raw_label_0248"], "line_number": 1, "line_index": 0, "raw_line": EXPECTED_RAW_LINES[0]},
        },
        "verified_raw_fact": {
            "normalized_xywh": [0.992188, 0.34537, 0.053125, 0.101852],
            "pixel_xyxy": EXPECTED_RAW_XYXY,
            "right_overflow_px": EXPECTED_OVERFLOW,
            "line_2_inside_image": True,
            "raw_bytes_unchanged": True,
        },
        "visual_assessment": {
            "finding": "IMAGE_EDGE_TRUNCATED_OBJECT_WITH_RAW_BOX_EXTENDING_BEYOND_RIGHT_BOUNDARY",
            "confidence": "HIGH",
            "basis": [
                "The full raw frame shows the rightmost P.124c sign cut by the image boundary.",
                "The boundary zoom shows the visible sign continuing into the cropped edge while the raw box extends 18.00048 px beyond x=960.",
                "Adjacent frames 0247 and 0249 support continuity only as proxy context, never as group ground truth.",
            ],
        },
        "context_proxy_only": [
            {"stem": stem, "image_sha256": inventory[stem]["image_sha256"], "role": "ADJACENCY_CONTEXT_PROXY_ONLY_NOT_GROUP_GROUND_TRUTH"}
            for stem in ("0247", "0249")
        ],
        "decision_options": facts["contract"]["options"],
        "recommendation": facts["contract"]["recommendation"],
        "derived_clip_candidate": {
            "status": DERIVED_ROLE,
            "transform": "x_max := min(raw_x_max, image_width); y_min/y_max/x_min unchanged; recompute YOLO x_center and width",
            "raw_line_1_pixel_xyxy": EXPECTED_RAW_XYXY,
            "derived_line_1_pixel_xyxy": EXPECTED_CLIPPED_XYXY,
            "right_overflow_removed_px": EXPECTED_OVERFLOW,
            "lines": EXPECTED_DERIVED_LINES,
            "source_raw_label_overwritten": False,
        },
        "owner_decision": {
            "decision_id": "G0.4-bbox-0248", "status": "PENDING", "selected_option": None,
            "recommendation_is_not_owner_approval": True,
        },
        "governance": {
            "gate0": "BLOCKED", "relabel_authorized": False, "split_authorized": False,
            "training_authorized": False,
        },
        "source_binding": {
            "wp1_manifest_sha256": EXPECTED_PINNED_HASHES["wp1_manifest"],
            "wp2_manifest_sha256": EXPECTED_PINNED_HASHES["wp2_manifest"],
            "wp4_manifest_sha256": EXPECTED_PINNED_HASHES["wp4_manifest"],
            "wp8_manifest_sha256": EXPECTED_PINNED_HASHES["wp8_manifest"],
            "contract_sha256": EXPECTED_PINNED_HASHES["contract"],
        },
    }


def reviewer_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in (
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    ):
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def draw_wrapped(draw: ImageDraw.ImageDraw, value: str, box: tuple[int, int, int, int], font: ImageFont.FreeTypeFont | ImageFont.ImageFont, fill: str, spacing: int = 5) -> int:
    left, top, right, bottom = box
    words = value.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and draw.textlength(candidate, font=font) > right - left:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current or not lines:
        lines.append(current)
    line_height = draw.textbbox((0, 0), "Ag", font=font)[3] + spacing
    cursor = top
    for line in lines:
        if cursor + line_height > bottom:
            raise RuntimeError(f"review visual text overflow: {value}")
        draw.text((left, cursor), line, font=font, fill=fill)
        cursor += line_height
    return cursor


def render_visual(raw_root: Path, adjudication: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    with Image.open(raw_root / "archive/images/0248.jpg") as image:
        source = image.convert("RGB")
    with Image.open(raw_root / "archive/images/0247.jpg") as image:
        previous = image.convert("RGB")
    with Image.open(raw_root / "archive/images/0249.jpg") as image:
        following = image.convert("RGB")

    canvas = Image.new("RGB", (1900, 1500), "#f8fafc")
    draw = ImageDraw.Draw(canvas)
    title_font = reviewer_font(30)
    heading_font = reviewer_font(22)
    body_font = reviewer_font(18)
    small_font = reviewer_font(15)
    draw.rectangle((0, 0, 1900, 82), fill="#111827")
    draw.text((45, 18), "M0-WP9 | bbox 0248 decision-support sheet", font=title_font, fill="white")
    draw.text((1110, 25), "G0.4 PENDING | Gate 0 BLOCKED | no training", font=heading_font, fill="#fde68a")

    full_origin = (60, 120)
    canvas.paste(source, full_origin)
    image_bounds = [60, 120, 1020, 660]
    draw.rectangle(image_bounds, outline="#0891b2", width=4)
    raw_box = [full_origin[0] + value for value in (EXPECTED_RAW_XYXY[0], EXPECTED_RAW_XYXY[2])]
    raw_full_box = [raw_box[0], full_origin[1] + EXPECTED_RAW_XYXY[1], raw_box[1], full_origin[1] + EXPECTED_RAW_XYXY[3]]
    clipped_full_box = [full_origin[0] + EXPECTED_CLIPPED_XYXY[0], full_origin[1] + EXPECTED_CLIPPED_XYXY[1], full_origin[0] + EXPECTED_CLIPPED_XYXY[2], full_origin[1] + EXPECTED_CLIPPED_XYXY[3]]
    draw.rectangle(raw_full_box, outline="#dc2626", width=5)
    draw.rectangle(clipped_full_box, outline="#16a34a", width=3)
    second_pixels = xyxy((49, 0.333854, 0.342593, 0.046875, 0.088889), 960, 540)
    draw.rectangle([full_origin[0] + second_pixels[0], full_origin[1] + second_pixels[1], full_origin[0] + second_pixels[2], full_origin[1] + second_pixels[3]], outline="#16a34a", width=4)
    draw.line((1020, 112, 1020, 668), fill="#0891b2", width=5)
    draw.text((60, 90), "Raw full frame 0248 (cyan = image edge, red = raw line 1, green = clipped candidate / valid line 2)", font=body_font, fill="#111827")
    draw.text((925, 670), "x=960", font=small_font, fill="#0e7490")
    draw.text((945, 205), "+18.00048 px", font=small_font, fill="#b91c1c")

    panel_x = 1090
    draw.rounded_rectangle((panel_x, 110, 1850, 670), radius=14, fill="white", outline="#cbd5e1", width=2)
    cursor = 135
    draw.text((panel_x + 24, cursor), "Verified observation", font=heading_font, fill="#111827")
    cursor += 38
    for text, color in (
        ("RAW FACT: line 1 / index 0 / class 49", "#111827"),
        ("YOLO: 0.992188 0.345370 0.053125 0.101852", "#111827"),
        ("Pixels: (927.00048, 158.99976, 978.00048, 213.99984)", "#111827"),
        ("Right overflow: 18.00048 px", "#b91c1c"),
        ("VISUAL: the target sign itself is cut by the right frame edge.", "#7c2d12"),
        ("Assessment: IMAGE_EDGE_TRUNCATED_OBJECT; confidence HIGH.", "#7c2d12"),
        ("This is not merely an oversized box around a fully visible object.", "#7c2d12"),
    ):
        cursor = draw_wrapped(draw, text, (panel_x + 24, cursor, 1825, 645), body_font, color) + 10

    crop = source.crop((840, 100, 960, 280)).resize((360, 540), Image.Resampling.LANCZOS)
    zoom_origin = (60, 760)
    draw.rectangle((50, 725, 520, 1345), fill="white", outline="#cbd5e1", width=2)
    canvas.paste(crop, zoom_origin)
    draw.rectangle((420, 760, 500, 1300), fill="#e2e8f0")
    boundary_x = 420
    raw_zoom = [60 + (EXPECTED_RAW_XYXY[0] - 840) * 3, 760 + (EXPECTED_RAW_XYXY[1] - 100) * 3, 60 + (EXPECTED_RAW_XYXY[2] - 840) * 3, 760 + (EXPECTED_RAW_XYXY[3] - 100) * 3]
    clipped_zoom = [60 + (EXPECTED_CLIPPED_XYXY[0] - 840) * 3, 760 + (EXPECTED_CLIPPED_XYXY[1] - 100) * 3, boundary_x, 760 + (EXPECTED_CLIPPED_XYXY[3] - 100) * 3]
    draw.rectangle(raw_zoom, outline="#dc2626", width=6)
    draw.rectangle(clipped_zoom, outline="#16a34a", width=4)
    draw.line((boundary_x, 750, boundary_x, 1310), fill="#0891b2", width=6)
    draw.text((60, 735), "Boundary zoom (3x) + virtual outside-frame area", font=body_font, fill="#111827")
    draw.text((430, 1160), "outside", font=small_font, fill="#475569")
    draw.text((430, 1183), "frame", font=small_font, fill="#475569")
    draw.text((60, 1310), "Red raw box extends beyond cyan edge; green candidate clips at x=960.", font=small_font, fill="#111827")

    thumb_size = (470, 264)
    previous.thumbnail(thumb_size, Image.Resampling.LANCZOS)
    following.thumbnail(thumb_size, Image.Resampling.LANCZOS)
    draw.rectangle((550, 725, 1050, 1345), fill="white", outline="#cbd5e1", width=2)
    canvas.paste(previous, (565, 765))
    canvas.paste(following, (565, 1050))
    draw.text((565, 735), "0247 | adjacency context proxy only", font=body_font, fill="#111827")
    draw.text((565, 1020), "0249 | adjacency context proxy only", font=body_font, fill="#111827")
    draw.text((565, 1320), "Not group ground truth; used only to support visual continuity.", font=small_font, fill="#7c2d12")

    draw.rounded_rectangle((1090, 710, 1850, 1405), radius=14, fill="white", outline="#cbd5e1", width=2)
    cursor = 735
    draw.text((1115, cursor), "Decision options", font=heading_font, fill="#111827")
    cursor += 42
    option_texts = [
        "1. KEEP RAW AS WARNING — preserve raw provenance; does not approve training.",
        "2. CREATE SEPARATE CLIPPED DERIVED ANNOTATION — review/tooling only; never overwrite raw.",
        "3. QUARANTINE — exclude stem 0248 from approved training until owner decision.",
    ]
    for value in option_texts:
        cursor = draw_wrapped(draw, value, (1115, cursor, 1825, 1375), body_font, "#334155") + 14
    draw.line((1115, cursor, 1825, cursor), fill="#cbd5e1", width=2)
    cursor += 22
    draw.text((1115, cursor), "PM recommendation (not owner approval)", font=heading_font, fill="#991b1b")
    cursor += 40
    cursor = draw_wrapped(draw, "QUARANTINE_FROM_TRAINING_PENDING_OWNER_DECISION", (1115, cursor, 1825, 1375), heading_font, "#991b1b") + 12
    cursor = draw_wrapped(draw, "Keep raw immutable. Provide the clipped label only as a review candidate. Clipping fixes coordinates but cannot restore the missing part of the sign.", (1115, cursor, 1825, 1375), body_font, "#111827") + 16
    cursor = draw_wrapped(draw, "Owner decision: PENDING | Gate 0: BLOCKED | training_authorized: false", (1115, cursor, 1825, 1375), body_font, "#92400e")
    if cursor > 1375:
        raise RuntimeError("recommendation panel overflow")

    draw.rectangle((0, 1440, 1900, 1500), fill="#111827")
    draw.text((45, 1457), EVIDENCE_BOUNDARY, font=body_font, fill="#fde68a")
    buffer = io.BytesIO()
    canvas.save(buffer, format="PNG", optimize=False)
    payload = buffer.getvalue()
    audit = {
        "schema_version": 1,
        "status": "PASS_ALL_PANELS_AND_OVERLAYS_WITHIN_CANVAS",
        "canvas": {"width": 1900, "height": 1500},
        "source_image_bounds": image_bounds,
        "raw_box_full_canvas_xyxy": raw_full_box,
        "clipped_box_full_canvas_xyxy": clipped_full_box,
        "image_right_boundary_canvas_x": 1020,
        "raw_box_extends_beyond_image_boundary": raw_full_box[2] > 1020,
        "raw_box_stays_within_canvas": raw_full_box[2] < 1900,
        "zoom_raw_box_canvas_xyxy": raw_zoom,
        "zoom_clipped_box_canvas_xyxy": clipped_zoom,
        "zoom_virtual_outside_area_visible": True,
        "full_frame_visible": True,
        "boundary_zoom_visible": True,
        "context_0247_visible": True,
        "context_0249_visible": True,
        "context_is_proxy_only": True,
        "all_three_options_visible": True,
        "recommendation_visible": True,
        "governance_boundary_visible": True,
        "all_bounds_fit": True,
        "render_sha256": sha256_bytes(payload),
        "semantic_digest": sha256_bytes(json.dumps(adjudication, sort_keys=True, separators=(",", ":")).encode("utf-8")),
    }
    return payload, audit


def render_report(adjudication: dict[str, Any]) -> str:
    return f"""# M0-WP9 bbox 0248 adjudication report

Status: `{PACKAGE_STATUS}`  
Boundary: `{EVIDENCE_BOUNDARY}`

## Verified raw fact

- Target: stem `0248`, split `train`, class `49` (`P.124c`), label line `1` / zero-based index `0`.
- Image: `960x540`, SHA-256 `{EXPECTED_PINNED_HASHES['raw_image_0248']}`.
- Raw label SHA-256: `{EXPECTED_PINNED_HASHES['raw_label_0248']}`; source bytes remain unchanged.
- Raw YOLO: `0.992188 0.345370 0.053125 0.101852`.
- Raw pixel box: `(927.00048, 158.99976, 978.00048, 213.99984)`.
- Right overflow: `18.00048 px` beyond image boundary `x=960`.
- Line 2 remains inside the image and is not changed by the derived candidate.

## Visual assessment

The full raw frame and boundary zoom show that the rightmost target sign is itself cut by the
right image edge. The case is therefore classified as
`IMAGE_EDGE_TRUNCATED_OBJECT_WITH_RAW_BOX_EXTENDING_BEYOND_RIGHT_BOUNDARY`, with `HIGH`
confidence. It is not merely annotation overshoot around a fully visible object.

Frames `0247` and `0249` support continuity as adjacency context only. Their relationship is
`ADJACENCY_CONTEXT_PROXY_ONLY_NOT_GROUP_GROUND_TRUTH`; they do not establish a final group.

## Options presented to the owner

1. `keep_raw_as_warning`: preserve the immutable raw label and warning; no training approval.
2. `create_separate_clipped_derived_annotation`: create a separate image-valid candidate for
   review/tooling; never overwrite raw and do not treat it as training-approved.
3. `quarantine_image_from_approved_dataset`: exclude stem `0248` from approved training until an
   owner decision is recorded.

## PM recommendation — proposal, not owner approval

Recommend `{RECOMMENDATION}` while keeping raw handling as `{RAW_HANDLING}`. A clipped candidate
is supplied only as `{DERIVED_ROLE}`. Clipping fixes coordinate validity but cannot reconstruct
the missing portion of the sign, so it is not sufficient evidence to authorize training.

Derived line 1:

```text
{EXPECTED_DERIVED_LINES[0]}
```

The transform is limited to `x_max := min(978.00048, 960.0)`; `x_min`, `y_min`, and `y_max` stay
unchanged, then YOLO `x_center` and `width` are recomputed. Line 2 is copied unchanged.

## Governance state

- Owner decision `G0.4-bbox-0248`: `PENDING`; selected option: `null`.
- Gate 0: `BLOCKED`.
- `relabel_authorized=false`, `split_authorized=false`, `training_authorized=false`.
- This package does not mutate raw data, approve a relabel, create a split, or authorize training.

## Evidence binding

- WP1 manifest: `{EXPECTED_PINNED_HASHES['wp1_manifest']}`.
- WP2 manifest: `{EXPECTED_PINNED_HASHES['wp2_manifest']}`.
- WP4 manifest: `{EXPECTED_PINNED_HASHES['wp4_manifest']}`.
- WP8 manifest (must remain unchanged): `{EXPECTED_PINNED_HASHES['wp8_manifest']}`.
- WP9 adjudication contract: `{EXPECTED_PINNED_HASHES['contract']}`.
"""


def expected_artifacts(repo_root: Path, raw_root: Path) -> dict[str, bytes]:
    facts = derive_facts(repo_root, raw_root)
    adjudication = adjudication_payload(repo_root, raw_root, facts)
    visual, layout = render_visual(raw_root, adjudication)
    return {
        ADJUDICATION_RELATIVE_PATH: json_bytes(adjudication),
        DERIVED_LABEL_RELATIVE_PATH: ("\n".join(EXPECTED_DERIVED_LINES) + "\n").encode("ascii"),
        LAYOUT_RELATIVE_PATH: json_bytes(layout),
        REPORT_RELATIVE_PATH: render_report(adjudication).encode("utf-8"),
        VISUAL_RELATIVE_PATH: visual,
    }


def build_manifest(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    sources = verify_pinned_sources(repo_root, raw_root)
    artifacts = [
        {"id": item_id, "root": "repo", "path": relative, "sha256": sha256_file(path), "size": path.stat().st_size}
        for item_id, relative, path in artifact_contract(repo_root)
    ]
    return {
        "schema_version": 1,
        "package": "M0-WP9",
        "status": PACKAGE_STATUS,
        "decision_id": "G0.4-bbox-0248",
        "decision_status": "PENDING",
        "selected_option": None,
        "recommendation": RECOMMENDATION,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "manifest_path": MANIFEST_RELATIVE_PATH,
        "manifest_self_in_artifact_count": False,
        "artifact_count_semantics": "EXCLUDES_MANIFEST_FILE",
        "raw_source_unchanged": True,
        "derived_candidate_training_approved": False,
        "gate0": "BLOCKED",
        "relabel_authorized": False,
        "split_authorized": False,
        "training_authorized": False,
        "source_count": len(sources),
        "artifact_count": len(artifacts),
        "total_artifact_bytes": sum(record["size"] for record in artifacts),
        "sources": sources,
        "artifacts": artifacts,
    }


def validate_collection(payload: dict[str, Any], name: str, expected: list[tuple[str, str, str]], roots: dict[str, Path], errors: list[str]) -> list[dict[str, Any]]:
    value = payload.get(name)
    if not isinstance(value, list):
        errors.append(f"{name} must be a list")
        return []
    records: list[dict[str, Any]] = []
    roster: list[tuple[str, str, str]] = []
    for index, record in enumerate(value):
        if not isinstance(record, dict):
            errors.append(f"{name}[{index}] must be an object")
            continue
        if set(record) != {"id", "root", "path", "sha256", "size"}:
            errors.append(f"{name}[{index}] fields differ from contract")
        item_id, root_id, path_value = record.get("id"), record.get("root"), record.get("path")
        if isinstance(item_id, str) and isinstance(root_id, str) and isinstance(path_value, str):
            roster.append((item_id, root_id, path_value))
            if root_id not in roots:
                errors.append(f"{name}[{index}].root invalid")
            else:
                try:
                    safe_child(roots[root_id], path_value)
                except (ValueError, OSError) as exc:
                    errors.append(str(exc))
        else:
            errors.append(f"{name}[{index}] identity/path invalid")
        digest = record.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            errors.append(f"{name}[{index}].sha256 invalid")
        size = record.get("size")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            errors.append(f"{name}[{index}].size invalid")
        records.append(record)
    if len({item_id for item_id, _root, _path in roster}) != len(roster):
        errors.append(f"duplicate {name} IDs")
    if len({(root, path) for _item_id, root, path in roster}) != len(roster):
        errors.append(f"duplicate {name} paths")
    if roster != expected:
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
        "schema_version", "package", "status", "decision_id", "decision_status", "selected_option",
        "recommendation", "evidence_boundary", "manifest_path", "manifest_self_in_artifact_count",
        "artifact_count_semantics", "raw_source_unchanged", "derived_candidate_training_approved",
        "gate0", "relabel_authorized", "split_authorized", "training_authorized", "source_count",
        "artifact_count", "total_artifact_bytes", "sources", "artifacts",
    }
    if set(payload) != expected_top:
        errors.append("manifest top-level fields differ from WP9 schema")
    constants = {
        "schema_version": 1, "package": "M0-WP9", "status": PACKAGE_STATUS,
        "decision_id": "G0.4-bbox-0248", "decision_status": "PENDING", "selected_option": None,
        "recommendation": RECOMMENDATION, "evidence_boundary": EVIDENCE_BOUNDARY,
        "manifest_path": MANIFEST_RELATIVE_PATH, "manifest_self_in_artifact_count": False,
        "artifact_count_semantics": "EXCLUDES_MANIFEST_FILE", "raw_source_unchanged": True,
        "derived_candidate_training_approved": False, "gate0": "BLOCKED",
        "relabel_authorized": False, "split_authorized": False, "training_authorized": False,
    }
    for field, expected in constants.items():
        if payload.get(field) != expected:
            errors.append(f"invalid manifest {field}")

    roots = {"repo": repo_root, "raw": raw_root}
    expected_sources = [(item_id, root_id, relative) for item_id, root_id, relative, _path, _digest in source_contract(repo_root, raw_root)]
    expected_artifact_roster = [(item_id, "repo", relative) for item_id, relative, _path in artifact_contract(repo_root)]
    sources = validate_collection(payload, "sources", expected_sources, roots, errors)
    artifacts = validate_collection(payload, "artifacts", expected_artifact_roster, roots, errors)
    if payload.get("source_count") != len(expected_sources) or len(sources) != len(expected_sources):
        errors.append("source_count mismatch")
    if payload.get("artifact_count") != len(expected_artifact_roster) or len(artifacts) != len(expected_artifact_roster):
        errors.append("artifact_count mismatch")
    recorded_bytes = sum(record.get("size", -1) for record in artifacts if isinstance(record.get("size"), int) and not isinstance(record.get("size"), bool))
    if payload.get("total_artifact_bytes") != recorded_bytes:
        errors.append("total_artifact_bytes mismatch")

    pinned = EXPECTED_PINNED_HASHES
    for collection, records in (("sources", sources), ("artifacts", artifacts)):
        for record in records:
            root_id, path_value = record.get("root"), record.get("path")
            if root_id not in roots or not isinstance(path_value, str):
                continue
            try:
                path = safe_child(roots[root_id], path_value)
            except (ValueError, OSError):
                continue
            if not path.is_file():
                errors.append(f"missing {collection} file: {path_value}")
            elif path.stat().st_size != record.get("size") or sha256_file(path) != record.get("sha256"):
                errors.append(f"tampered {collection} file: {path_value}")
            if collection == "sources" and pinned.get(str(record.get("id"))) is not None and record.get("sha256") != pinned[str(record["id"])]:
                errors.append(f"pinned source hash mismatch: {record['id']}")

    if not errors:
        try:
            expected_payloads = expected_artifacts(repo_root, raw_root)
            for _item_id, relative, path in artifact_contract(repo_root):
                if path.read_bytes() != expected_payloads[relative]:
                    raise ValueError(f"semantic artifact mismatch: {relative}")
            with Image.open(repo_root / VISUAL_RELATIVE_PATH) as image:
                if image.size != (1900, 1500) or image.format != "PNG" or image.mode != "RGB":
                    raise ValueError("WP9 review visual image contract mismatch")
                image.verify()
            derived = (repo_root / DERIVED_LABEL_RELATIVE_PATH).read_text(encoding="ascii")
            if derived != "\n".join(EXPECTED_DERIVED_LINES) + "\n":
                raise ValueError("derived label differs from the exact clip transform")
            if sha256_file(raw_root / "archive/labels/0248.txt") != EXPECTED_PINNED_HASHES["raw_label_0248"]:
                raise ValueError("raw source label changed")
        except (FileNotFoundError, json.JSONDecodeError, KeyError, OSError, TypeError, ValueError) as exc:
            errors.append(f"semantic verification failed: {exc}")
    return {
        "valid": not errors,
        "errors": errors,
        "source_count": len(sources),
        "artifact_count": len(artifacts),
        "status": payload.get("status"),
    }


def build(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    repo_root, raw_root = repo_root.resolve(), raw_root.resolve()
    payloads = expected_artifacts(repo_root, raw_root)
    for relative, payload in payloads.items():
        write_bytes(repo_root / relative, payload)
    manifest = build_manifest(repo_root, raw_root)
    write_bytes(repo_root / MANIFEST_RELATIVE_PATH, json_bytes(manifest))
    result = verify_manifest(repo_root / MANIFEST_RELATIVE_PATH, repo_root, raw_root)
    if not result["valid"]:
        raise RuntimeError(f"WP9 package verification failed: {result['errors']}")
    return {
        "status": PACKAGE_STATUS,
        "recommendation": RECOMMENDATION,
        "owner_decision": "PENDING",
        "raw_source_unchanged": True,
        "source_count": manifest["source_count"],
        "artifact_count": manifest["artifact_count"],
        "manifest_sha256": sha256_file(repo_root / MANIFEST_RELATIVE_PATH),
        "gate0": "BLOCKED",
        "training_authorized": False,
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("build", "verify"):
        command = commands.add_parser(name)
        command.add_argument("--repo-root", type=Path, required=True)
        command.add_argument("--raw-root", type=Path)
    commands.choices["verify"].add_argument("--manifest", type=Path, default=Path(MANIFEST_RELATIVE_PATH))
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    raw_root = args.raw_root.resolve() if args.raw_root else default_raw_root(repo_root)
    if args.command == "build":
        result = build(repo_root, raw_root)
    else:
        manifest = args.manifest if args.manifest.is_absolute() else repo_root / args.manifest
        result = verify_manifest(manifest, repo_root, raw_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if args.command != "verify" or result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
