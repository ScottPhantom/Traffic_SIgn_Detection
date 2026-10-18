# ruff: noqa: E501
"""Build and verify the M0-WP8 provisional 52-class taxonomy recommendation package."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

PACKAGE_STATUS = "M0_WP8_AWAITING_QA_PROPOSAL_ONLY"
EVIDENCE_BOUNDARY = (
    "NATIVE_52_CLASS_TAXONOMY_RECOMMENDATION_ONLY_NO_D03_APPROVAL_"
    "NO_RELABEL_NO_SPLIT_NO_TRAINING"
)
EXPECTED_CLASS_COUNT = 52
EXPECTED_REPRESENTATIVE_COUNT = 156
EXPECTED_ATLAS_PAGE_COUNT = 13
CLASSES_PER_PAGE = 4
RARE_IMAGE_THRESHOLD = 100

CONTRACT_RELATIVE_PATH = "references/qcvn41_2024/wp8_recommendation_contract.json"
MANIFEST_RELATIVE_PATH = "docs/review/generated/wp8_taxonomy_manifest.json"
MATRIX_CSV_RELATIVE_PATH = "docs/review/generated/wp8_taxonomy_recommendation.csv"
MATRIX_JSON_RELATIVE_PATH = "docs/review/generated/wp8_taxonomy_recommendation.json"
SUMMARY_RELATIVE_PATH = "docs/review/generated/wp8_taxonomy_summary.json"
LAYOUT_RELATIVE_PATH = "docs/review/generated/wp8_taxonomy_layout_audit.json"
REPORT_RELATIVE_PATH = "docs/review/wp8_taxonomy_recommendation_report.md"
ASSETS_RELATIVE_PATH = "docs/review/assets/wp8/taxonomy_decision_atlas"
WP4_ASSETS_RELATIVE_PATH = "docs/review/assets/wp4/qcvn_taxonomy_atlas"

EXPECTED_PINNED_HASHES: dict[str, str] = {
    "wp1_manifest": "28adbf21dd2057fe5fc7999daccaa52d1201ea0459ef1bb7475a780ed85c51c6",
    "wp2_manifest": "506ec141bef032282f90b3d35741ece49a43fed617c3dea93863d4c32330a505",
    "wp3_manifest": "8b2e9ef3b2418623eb92673f3c58591e29f5ed7479bca2b03582c12ef0191dcd",
    "wp4_manifest": "c60c09018900071cc66d8bc01db32300f4efc6a4316bda9f506819026400db1c",
    "wp5_manifest": "f8d620a3cbb3b500153f6685b94a9936a8f83eb6f5399ce0a2e8be77982d4b80",
    "wp6_manifest": "656afe56bf342a0d4d0110dcd6b1d601f9f35633d03c65c98d54d3d454760bb0",
    "wp7_manifest": "73ed4095a1f59b72f010fd87b63c4a7f0b16bcf8e0c667ec77576ec827e5d7f2",
    "model": "745cf3f6e9f5edfe32954866d93f07d9504f6bc2d4f3667c8b8f99f1c924b565",
    "decision_status": "87d81262e907bb1c479cfac6535e7b3f67a368c371e96b810aa02f2e92d0d72c",
    "qcvn_pdf": "b6b99d0a0aeb13fe79072831857ece15bb254d8fb7817e80e4a2739a0d2145ce",
    "circular_pdf": "dc822815eb51c6674a40ce91127b636f11a7479c76f24d9a00445dcf248b6689",
    "source_provenance": "43b18ee597fb960656527e37c1927574a0ec19d9a171ccaaca9e8484566c425d",
    "evidence_index": "62233e56a47c9c7116805d2b9d38846f2a20696b952507752810a83192abd7aa",
    "wp4_worksheet": "03bf19c3756c77bb28193b6d8014d265913d582eaeacbdd31d31d858fccc89ff",
    "wp4_lineage": "c9e90b01ef3be78797b58405d9c7a7fb9f7f8384498b876af23a25b22e0a8d19",
    "taxonomy_review": "4d27209e9f381a6991cd21f7ee6521553495eb6771422a5889536ae12003bad1",
    "rare_class_risk": "5e410d855d9b15803dc1adcc0f57fd79cf9e9f392690732aeaac2e3f4bea14b7",
    "image_inventory": "d45aa7f398a040c44cbc040f4ec005d7e5a8ef50586e905315f76c792ca29022",
    "source_preservation": "5ca3e769b9197cad19bcb75f553dd59fee6e3035e0cc86cd9693737f84a713d7",
    "recommendation_contract": "9682957cf157d25ab522d794241a779584ad10c1df9154fa38ad84111d14fce6",
}

EXPECTED_NATIVE_COUNTS = {
    "CORRECT_CODE_OR_NAME_PROPOSAL": 19,
    "KEEP_CURRENT": 23,
    "OUT_OF_SCOPE_PROPOSAL": 1,
    "SEMANTIC_REVIEW_REQUIRED": 9,
}
EXPECTED_GTSRB_COUNTS = {
    "DIRECT_ANALYSIS_ONLY": 11,
    "NONE": 27,
    "PARTIAL_ANALYSIS_ONLY": 13,
    "REVIEW_REQUIRED": 1,
}
EXPECTED_POLICY_COUNTS = {
    "ATOMIC_SIGN": 36,
    "COMPOSITE_SIGN_REVIEW": 5,
    "PARAMETERIZED_SIGN_REVIEW": 7,
    "SUPPLEMENTARY_SIGN_REVIEW": 3,
    "VARIANT_SELECTION_REVIEW": 1,
}
EXPECTED_UNKNOWN_COUNTS = {
    "KEEP_NATIVE_NO_UNKNOWN": 11,
    "REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY": 31,
    "REVIEW_NATIVE_OR_UNKNOWN": 10,
}
EXPECTED_CONFLICT_IDS = [3, 22, 23, 25, 28, 30, 31, 34, 47, 51]
EXPECTED_CRITICAL: dict[int, tuple[str, str, str, str, str, str]] = {
    3: ("PARTIAL", "R.302a", "CORRECT_CODE_OR_NAME_PROPOSAL", "R.302a", "PARTIAL_ANALYSIS_ONLY", "ATOMIC_SIGN"),
    22: ("PARTIAL", "W.221b", "CORRECT_CODE_OR_NAME_PROPOSAL", "W.221b", "PARTIAL_ANALYSIS_ONLY", "ATOMIC_SIGN"),
    23: ("MISMATCH", "P.111a-d", "SEMANTIC_REVIEW_REQUIRED", "", "NONE", "VARIANT_SELECTION_REVIEW"),
    25: ("MISMATCH", "S.505a", "SEMANTIC_REVIEW_REQUIRED", "", "NONE", "SUPPLEMENTARY_SIGN_REVIEW"),
    28: ("MISMATCH", "S.505a", "SEMANTIC_REVIEW_REQUIRED", "", "NONE", "SUPPLEMENTARY_SIGN_REVIEW"),
    30: ("MISMATCH", "S.505a", "SEMANTIC_REVIEW_REQUIRED", "", "NONE", "SUPPLEMENTARY_SIGN_REVIEW"),
    31: ("NOT_FOUND", "", "OUT_OF_SCOPE_PROPOSAL", "", "NONE", "ATOMIC_SIGN"),
    34: ("MISMATCH", "P.108a", "CORRECT_CODE_OR_NAME_PROPOSAL", "P.108a", "NONE", "ATOMIC_SIGN"),
    47: ("MISMATCH", "P.124b", "CORRECT_CODE_OR_NAME_PROPOSAL", "P.124b", "NONE", "ATOMIC_SIGN"),
    51: ("EXACT", "W.246c", "KEEP_CURRENT", "W.246c", "PARTIAL_ANALYSIS_ONLY", "ATOMIC_SIGN"),
}
EXPECTED_QA_REPAIR_ROWS: dict[int, tuple[str, str, str, str, str]] = {
    6: (
        "CORRECT_CODE_OR_NAME_PROPOSAL",
        "W.201a",
        "Dangerous Curve to the Left",
        "ATOMIC_SIGN",
        "DIRECT_ANALYSIS_ONLY",
    ),
    14: (
        "CORRECT_CODE_OR_NAME_PROPOSAL",
        "P.106a",
        "No Trucks",
        "ATOMIC_SIGN",
        "PARTIAL_ANALYSIS_ONLY",
    ),
    42: (
        "CORRECT_CODE_OR_NAME_PROPOSAL",
        "R.301e",
        "Mandatory Left Turn",
        "ATOMIC_SIGN",
        "DIRECT_ANALYSIS_ONLY",
    ),
    50: (
        "CORRECT_CODE_OR_NAME_PROPOSAL",
        "W.201b",
        "Dangerous Curve to the Right",
        "ATOMIC_SIGN",
        "DIRECT_ANALYSIS_ONLY",
    ),
}

CSV_FIELDS = [
    "class_id",
    "dataset_code",
    "dataset_name_vi_en",
    "image_count",
    "box_count",
    "risk_band",
    "rare_flag",
    "wp4_match_status",
    "official_code_candidate",
    "official_name_vi",
    "official_pdf_page",
    "official_section",
    "official_figure",
    "wp4_reason",
    "evidence_confidence",
    "evidence_method",
    "negative_search_scope",
    "representative_source_stems",
    "representative_image_sha256s",
    "representative_label_sha256s",
    "representative_bbox_refs",
    "native_recommendation",
    "recommended_code_if_approved",
    "recommended_name_vi_if_approved",
    "recommended_name_en_if_approved",
    "sign_policy",
    "gtsrb_mapping_proposal",
    "gtsrb_source_relation",
    "gtsrb_disposition",
    "unknown_policy",
    "reviewer_action",
    "recommendation_rationale",
    "conflict_flag",
    "reviewer_status",
    "approval_boundary",
    "wp4_atlas_page",
    "wp8_atlas_page",
]


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


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
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def safe_child(root: Path, relative_value: str) -> Path:
    relative = Path(relative_value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"unsafe relative path: {relative_value}")
    resolved_root = root.resolve()
    target = resolved_root / relative
    if target.is_symlink():
        raise ValueError(f"symlink path is not allowed: {relative_value}")
    resolved = target.resolve()
    resolved.relative_to(resolved_root)
    return resolved


def source_contract(repo_root: Path) -> list[tuple[str, Path, str | None]]:
    generated = repo_root / "docs/review/generated"
    audit = repo_root / "results/data_audit/DATASET01_052bc980a7206f8d"
    references = repo_root / "references/qcvn41_2024"
    return [
        ("wp1_manifest", audit / "wp1_artifact_manifest.json", EXPECTED_PINNED_HASHES["wp1_manifest"]),
        ("wp2_manifest", generated / "wp2_generated_manifest.json", EXPECTED_PINNED_HASHES["wp2_manifest"]),
        ("wp3_manifest", generated / "wp3_evidence_manifest.json", EXPECTED_PINNED_HASHES["wp3_manifest"]),
        ("wp4_manifest", generated / "wp4_qcvn_manifest.json", EXPECTED_PINNED_HASHES["wp4_manifest"]),
        ("wp5_manifest", generated / "wp5_evidence_manifest.json", EXPECTED_PINNED_HASHES["wp5_manifest"]),
        ("wp6_manifest", generated / "wp6_e0_compute_manifest.json", EXPECTED_PINNED_HASHES["wp6_manifest"]),
        ("wp7_manifest", generated / "wp7_batch_a_manifest.json", EXPECTED_PINNED_HASHES["wp7_manifest"]),
        ("model", repo_root / "models/VGG16_model.h5", EXPECTED_PINNED_HASHES["model"]),
        ("decision_status", repo_root / "docs/review/decision_status.json", EXPECTED_PINNED_HASHES["decision_status"]),
        ("qcvn_pdf", references / "qcvn-41-2024-bgtvt.pdf", EXPECTED_PINNED_HASHES["qcvn_pdf"]),
        ("circular_pdf", references / "51-2024-tt-bgtvt.pdf", EXPECTED_PINNED_HASHES["circular_pdf"]),
        ("source_provenance", references / "source_provenance.json", EXPECTED_PINNED_HASHES["source_provenance"]),
        ("evidence_index", references / "qcvn_taxonomy_evidence_index.json", EXPECTED_PINNED_HASHES["evidence_index"]),
        ("wp4_worksheet", generated / "wp4_qcvn_taxonomy_worksheet.csv", EXPECTED_PINNED_HASHES["wp4_worksheet"]),
        ("wp4_lineage", generated / "wp4_qcvn_source_lineage.csv", EXPECTED_PINNED_HASHES["wp4_lineage"]),
        ("taxonomy_review", generated / "taxonomy_review.csv", EXPECTED_PINNED_HASHES["taxonomy_review"]),
        ("rare_class_risk", generated / "rare_class_risk.csv", EXPECTED_PINNED_HASHES["rare_class_risk"]),
        ("image_inventory", audit / "image_inventory.csv", EXPECTED_PINNED_HASHES["image_inventory"]),
        ("source_preservation", audit / "source_preservation_proof.json", EXPECTED_PINNED_HASHES["source_preservation"]),
        ("recommendation_contract", repo_root / CONTRACT_RELATIVE_PATH, EXPECTED_PINNED_HASHES["recommendation_contract"]),
        ("wp8_builder", repo_root / "scripts/build_wp8_taxonomy_recommendation.py", None),
    ]


def artifact_contract(repo_root: Path) -> list[tuple[str, Path]]:
    assets = repo_root / ASSETS_RELATIVE_PATH
    rows: list[tuple[str, Path]] = [
        ("recommendation_csv", repo_root / MATRIX_CSV_RELATIVE_PATH),
        ("recommendation_json", repo_root / MATRIX_JSON_RELATIVE_PATH),
        ("summary", repo_root / SUMMARY_RELATIVE_PATH),
        ("layout_audit", repo_root / LAYOUT_RELATIVE_PATH),
        ("report", repo_root / REPORT_RELATIVE_PATH),
        ("atlas_index", assets / "index.html"),
    ]
    rows.extend(
        (f"atlas_page_{page:03d}", assets / f"page_{page:03d}.png")
        for page in range(1, EXPECTED_ATLAS_PAGE_COUNT + 1)
    )
    return rows


def relative_record(path: Path, repo_root: Path, item_id: str) -> dict[str, Any]:
    return {
        "id": item_id,
        "path": path.resolve().relative_to(repo_root.resolve()).as_posix(),
        "sha256": sha256_file(path),
        "size": path.stat().st_size,
    }


def verify_pinned_sources(repo_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item_id, path, pinned_hash in source_contract(repo_root):
        if not path.is_file():
            raise FileNotFoundError(f"required WP8 source missing: {path}")
        digest = sha256_file(path)
        if pinned_hash is not None and digest != pinned_hash:
            raise ValueError(f"pinned WP8 source mismatch: {item_id}")
        records.append(relative_record(path, repo_root, item_id))
    return records


def validate_governance(repo_root: Path) -> None:
    payload = json.loads((repo_root / "docs/review/decision_status.json").read_text(encoding="utf-8"))
    decisions = payload.get("decisions", {})
    if (
        payload.get("gate0") != "BLOCKED"
        or payload.get("training_authorized") is not False
        or decisions.get("D-03", {}).get("status") != "PENDING"
        or decisions.get("D-03", {}).get("selected_option") is not None
    ):
        raise ValueError("WP8 requires D-03 PENDING, Gate 0 BLOCKED, and training unauthorized")


def validate_wp4_manifest(repo_root: Path) -> None:
    path = repo_root / "docs/review/generated/wp4_qcvn_manifest.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("status") != "READY_FOR_RE_REVIEW_EVIDENCE_ONLY_NO_APPROVAL":
        raise ValueError("WP4 status changed")
    for collection in ("sources", "artifacts"):
        records = payload.get(collection)
        if not isinstance(records, list) or not records:
            raise ValueError(f"WP4 {collection} roster missing")
        seen: set[str] = set()
        for record in records:
            path_value = record.get("path")
            if not isinstance(path_value, str) or path_value in seen:
                raise ValueError(f"WP4 {collection} path roster invalid")
            seen.add(path_value)
            source = safe_child(repo_root, path_value)
            if (
                not source.is_file()
                or source.stat().st_size != record.get("size")
                or sha256_file(source) != record.get("sha256")
            ):
                raise ValueError(f"WP4 {collection} artifact changed: {path_value}")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def expected_disposition(relation: str) -> str:
    if relation == "Direct?/Partial?":
        return "REVIEW_REQUIRED"
    if relation.startswith("Direct?"):
        return "DIRECT_ANALYSIS_ONLY"
    if relation.startswith("Partial?"):
        return "PARTIAL_ANALYSIS_ONLY"
    if relation.startswith("None"):
        return "NONE"
    raise ValueError(f"unknown WP4 GTSRB relation: {relation}")


def validate_contract(payload: dict[str, Any]) -> list[dict[str, Any]]:
    required_top = {
        "schema_version",
        "package",
        "status",
        "decision_boundary",
        "native_recommendation_enum",
        "gtsrb_disposition_enum",
        "sign_policy_enum",
        "unknown_policy_enum",
        "unknown_policy_boundary",
        "required_conflict_class_ids",
        "rows",
    }
    if set(payload) != required_top:
        raise ValueError("WP8 contract top-level fields differ from schema")
    if (
        payload["schema_version"] != 1
        or payload["package"] != "M0-WP8"
        or payload["status"] != "PROPOSAL_ONLY_AWAITING_QA"
        or payload["decision_boundary"] != EVIDENCE_BOUNDARY
        or payload["required_conflict_class_ids"] != EXPECTED_CONFLICT_IDS
    ):
        raise ValueError("WP8 contract identity/boundary changed")
    rows = payload["rows"]
    if not isinstance(rows, list) or [row.get("class_id") for row in rows] != list(range(52)):
        raise ValueError("WP8 contract must contain exactly class IDs 0..51 in order")
    fields = {
        "class_id",
        "native_recommendation",
        "recommended_code_if_approved",
        "recommended_name_vi_if_approved",
        "recommended_name_en_if_approved",
        "sign_policy",
        "gtsrb_disposition",
        "unknown_policy",
        "reviewer_action",
        "rationale",
        "conflict_flag",
    }
    for row in rows:
        if set(row) != fields:
            raise ValueError(f"WP8 contract row fields changed for class {row.get('class_id')}")
        if row["native_recommendation"] not in payload["native_recommendation_enum"]:
            raise ValueError("invalid native recommendation enum")
        if row["gtsrb_disposition"] not in payload["gtsrb_disposition_enum"]:
            raise ValueError("invalid GTSRB disposition enum")
        if row["sign_policy"] not in payload["sign_policy_enum"]:
            raise ValueError("invalid sign policy enum")
        if row["unknown_policy"] not in payload["unknown_policy_enum"]:
            raise ValueError("invalid UNKNOWN policy enum")
        if not isinstance(row["conflict_flag"], bool) or not row["reviewer_action"] or not row["rationale"]:
            raise ValueError("incomplete WP8 contract row")
    if dict(sorted(Counter(row["native_recommendation"] for row in rows).items())) != EXPECTED_NATIVE_COUNTS:
        raise ValueError("WP8 native recommendation counts changed")
    if dict(sorted(Counter(row["gtsrb_disposition"] for row in rows).items())) != EXPECTED_GTSRB_COUNTS:
        raise ValueError("WP8 GTSRB disposition counts changed")
    if dict(sorted(Counter(row["sign_policy"] for row in rows).items())) != EXPECTED_POLICY_COUNTS:
        raise ValueError("WP8 sign-policy counts changed")
    if dict(sorted(Counter(row["unknown_policy"] for row in rows).items())) != EXPECTED_UNKNOWN_COUNTS:
        raise ValueError("WP8 UNKNOWN-policy counts changed")
    conflicts = [row["class_id"] for row in rows if row["conflict_flag"]]
    if conflicts != EXPECTED_CONFLICT_IDS:
        raise ValueError("WP8 conflict set changed")
    return rows


def representative_record(row: dict[str, str]) -> dict[str, Any]:
    return {
        "stem": row["stem"],
        "split": row["split"],
        "image_path": row["image_path"],
        "image_sha256": row["image_sha256"],
        "label_path": row["label_path"],
        "label_sha256": row["label_sha256"],
        "label_line_number": int(row["label_line_number"]),
        "source_bbox_xyxy": [
            float(row["source_bbox_x_min"]),
            float(row["source_bbox_y_min"]),
            float(row["source_bbox_x_max"]),
            float(row["source_bbox_y_max"]),
        ],
        "wp4_atlas_page": row["atlas_page"],
        "wp4_atlas_slot": int(row["slot_index"]),
    }


def build_rows(repo_root: Path) -> list[dict[str, Any]]:
    validate_governance(repo_root)
    validate_wp4_manifest(repo_root)
    proof = json.loads(
        (repo_root / "results/data_audit/DATASET01_052bc980a7206f8d/source_preservation_proof.json").read_text(encoding="utf-8")
    )
    if proof.get("unchanged") is not True:
        raise ValueError("source preservation proof is not unchanged=true")

    generated = repo_root / "docs/review/generated"
    worksheet = read_csv(generated / "wp4_qcvn_taxonomy_worksheet.csv")
    taxonomy = read_csv(generated / "taxonomy_review.csv")
    risks = read_csv(generated / "rare_class_risk.csv")
    lineage = read_csv(generated / "wp4_qcvn_source_lineage.csv")
    inventory = read_csv(repo_root / "results/data_audit/DATASET01_052bc980a7206f8d/image_inventory.csv")
    evidence_payload = json.loads(
        (repo_root / "references/qcvn41_2024/qcvn_taxonomy_evidence_index.json").read_text(encoding="utf-8")
    )
    contract_payload = json.loads((repo_root / CONTRACT_RELATIVE_PATH).read_text(encoding="utf-8"))
    contract = validate_contract(contract_payload)

    for name, rows in (("worksheet", worksheet), ("taxonomy", taxonomy), ("risks", risks)):
        if len(rows) != EXPECTED_CLASS_COUNT or [int(row["class_id"]) for row in rows] != list(range(52)):
            raise ValueError(f"WP8 {name} must contain exactly class IDs 0..51")
    if any(row["reviewer_status"] != "UNAPPROVED" for row in worksheet):
        raise ValueError("WP4 worksheet rows must remain UNAPPROVED")
    if any(row["review_status"] != "UNAPPROVED" for row in taxonomy):
        raise ValueError("taxonomy review rows must remain UNAPPROVED")
    if len(lineage) != EXPECTED_REPRESENTATIVE_COUNT:
        raise ValueError("WP4 lineage must contain exactly 156 representatives")
    if len(inventory) != 3216 or len({row["stem"] for row in inventory}) != 3216:
        raise ValueError("image inventory must contain 3,216 unique stems")
    evidence_rows = evidence_payload.get("rows")
    if not isinstance(evidence_rows, list) or [row.get("class_id") for row in evidence_rows] != list(range(52)):
        raise ValueError("QCVN evidence index must contain class IDs 0..51")

    risk_by_id = {int(row["class_id"]): row for row in risks}
    taxonomy_by_id = {int(row["class_id"]): row for row in taxonomy}
    evidence_by_id = {int(row["class_id"]): row for row in evidence_rows}
    contract_by_id = {int(row["class_id"]): row for row in contract}
    inventory_by_stem = {row["stem"]: row for row in inventory}
    lineage_by_id: defaultdict[int, list[dict[str, str]]] = defaultdict(list)
    for row in lineage:
        lineage_by_id[int(row["class_id"])].append(row)

    result: list[dict[str, Any]] = []
    for class_id, worksheet_row in enumerate(worksheet):
        taxonomy_row = taxonomy_by_id[class_id]
        risk_row = risk_by_id[class_id]
        evidence = evidence_by_id[class_id]
        recommendation = contract_by_id[class_id]
        expected_fields = (
            "official_code_candidate",
            "official_name_vi",
            "official_pdf_page",
            "official_section",
            "official_figure",
            "match_status",
            "reason",
            "composite_or_parameterized",
            "evidence_confidence",
            "evidence_method",
        )
        if any(str(evidence.get(field, "")) != worksheet_row[field] for field in expected_fields):
            raise ValueError(f"WP4 worksheet/evidence-index mismatch for class {class_id}")
        if (
            taxonomy_row["dataset_code"] != worksheet_row["dataset_code"]
            or taxonomy_row["dataset_name_vi_en"] != worksheet_row["dataset_name_vi_en"]
            or risk_row["sign_code"] != worksheet_row["dataset_code"]
            or risk_row["image_count"] != worksheet_row["image_count"]
            or risk_row["box_count"] != worksheet_row["box_count"]
        ):
            raise ValueError(f"WP8 source identity/support mismatch for class {class_id}")
        if expected_disposition(worksheet_row["gtsrb_relation_proposal"]) != recommendation["gtsrb_disposition"]:
            raise ValueError(f"GTSRB disposition does not follow WP4 relation for class {class_id}")
        if evidence["match_status"] == "MISMATCH" and recommendation["native_recommendation"] == "KEEP_CURRENT":
            raise ValueError(f"MISMATCH cannot be KEEP_CURRENT for class {class_id}")
        if evidence["match_status"] == "NOT_FOUND" and recommendation["native_recommendation"] != "OUT_OF_SCOPE_PROPOSAL":
            raise ValueError("NOT_FOUND class must remain out-of-scope proposal")

        reps = lineage_by_id[class_id]
        expected_stems = worksheet_row["representative_source_stems"].split(";")
        if len(reps) != 3 or [row["stem"] for row in reps] != expected_stems:
            raise ValueError(f"representative roster/order mismatch for class {class_id}")
        for rep in reps:
            inv = inventory_by_stem.get(rep["stem"])
            if inv is None or any(
                rep[field] != inv[field]
                for field in ("image_path", "image_sha256", "label_path", "label_sha256", "split")
            ):
                raise ValueError(f"representative lineage hash/path mismatch for class {class_id}")
        rep_records = [representative_record(rep) for rep in reps]
        negative_scope = evidence.get("negative_search_scope")
        row = {
            "class_id": class_id,
            "dataset_code": worksheet_row["dataset_code"],
            "dataset_name_vi_en": worksheet_row["dataset_name_vi_en"],
            "support": {
                "image_count": int(worksheet_row["image_count"]),
                "box_count": int(worksheet_row["box_count"]),
                "risk_band": risk_row["risk_band"],
                "rare_flag": int(worksheet_row["image_count"]) < RARE_IMAGE_THRESHOLD,
                "rare_definition": f"image_count < {RARE_IMAGE_THRESHOLD}; never a semantic merge rule",
            },
            "wp4_evidence": {
                "match_status": evidence["match_status"],
                "official_code_candidate": evidence["official_code_candidate"],
                "official_name_vi": evidence["official_name_vi"],
                "official_pdf_page": evidence["official_pdf_page"],
                "official_section": evidence["official_section"],
                "official_figure": evidence["official_figure"],
                "reason": evidence["reason"],
                "composite_or_parameterized": evidence["composite_or_parameterized"],
                "evidence_confidence": evidence["evidence_confidence"],
                "evidence_method": evidence["evidence_method"],
                "evidence_tokens": evidence.get("evidence_tokens", []),
                "fingerprint_pages": evidence.get("fingerprint_pages", []),
                "negative_search_scope": negative_scope,
            },
            "representatives": rep_records,
            "native_recommendation": recommendation["native_recommendation"],
            "recommended_code_if_approved": recommendation["recommended_code_if_approved"],
            "recommended_name_vi_if_approved": recommendation["recommended_name_vi_if_approved"],
            "recommended_name_en_if_approved": recommendation["recommended_name_en_if_approved"],
            "sign_policy": recommendation["sign_policy"],
            "gtsrb": {
                "mapping_proposal": worksheet_row["gtsrb_mapping_proposal"],
                "source_relation": worksheet_row["gtsrb_relation_proposal"],
                "disposition": recommendation["gtsrb_disposition"],
                "boundary": "ANALYSIS_ONLY_NOT_A_NATIVE_TAXONOMY_MERGE_OR_TRAINING_TARGET",
            },
            "unknown_policy": recommendation["unknown_policy"],
            "unknown_policy_boundary": contract_payload["unknown_policy_boundary"],
            "reviewer_action": recommendation["reviewer_action"],
            "recommendation_rationale": recommendation["rationale"],
            "conflict_flag": recommendation["conflict_flag"],
            "reviewer_status": "UNAPPROVED",
            "approval_boundary": EVIDENCE_BOUNDARY,
            "wp4_atlas_page": worksheet_row["atlas_page"],
            "wp8_atlas_page": f"{ASSETS_RELATIVE_PATH}/page_{class_id // CLASSES_PER_PAGE + 1:03d}.png",
        }
        result.append(row)

    for class_id, expected in EXPECTED_CRITICAL.items():
        row = result[class_id]
        actual = (
            row["wp4_evidence"]["match_status"],
            row["wp4_evidence"]["official_code_candidate"],
            row["native_recommendation"],
            row["recommended_code_if_approved"],
            row["gtsrb"]["disposition"],
            row["sign_policy"],
        )
        if actual != expected:
            raise ValueError(f"critical class {class_id} differs from independent WP8 expectation")
    for class_id, expected in EXPECTED_QA_REPAIR_ROWS.items():
        row = result[class_id]
        actual = (
            row["native_recommendation"],
            row["recommended_code_if_approved"],
            row["recommended_name_en_if_approved"],
            row["sign_policy"],
            row["gtsrb"]["disposition"],
        )
        if actual != expected:
            raise ValueError(f"QA repair class {class_id} differs from independent WP8-R1 expectation")
    return result


def flatten_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    for row in rows:
        reps = row["representatives"]
        evidence = row["wp4_evidence"]
        support = row["support"]
        flattened.append(
            {
                "class_id": row["class_id"],
                "dataset_code": row["dataset_code"],
                "dataset_name_vi_en": row["dataset_name_vi_en"],
                "image_count": support["image_count"],
                "box_count": support["box_count"],
                "risk_band": support["risk_band"],
                "rare_flag": str(support["rare_flag"]).lower(),
                "wp4_match_status": evidence["match_status"],
                "official_code_candidate": evidence["official_code_candidate"],
                "official_name_vi": evidence["official_name_vi"],
                "official_pdf_page": evidence["official_pdf_page"],
                "official_section": evidence["official_section"],
                "official_figure": evidence["official_figure"],
                "wp4_reason": evidence["reason"],
                "evidence_confidence": evidence["evidence_confidence"],
                "evidence_method": evidence["evidence_method"],
                "negative_search_scope": canonical_json(evidence["negative_search_scope"]) if evidence["negative_search_scope"] else "",
                "representative_source_stems": ";".join(rep["stem"] for rep in reps),
                "representative_image_sha256s": ";".join(rep["image_sha256"] for rep in reps),
                "representative_label_sha256s": ";".join(rep["label_sha256"] for rep in reps),
                "representative_bbox_refs": ";".join(
                    f"{rep['stem']}:line={rep['label_line_number']}:xyxy={','.join(str(value) for value in rep['source_bbox_xyxy'])}"
                    for rep in reps
                ),
                "native_recommendation": row["native_recommendation"],
                "recommended_code_if_approved": row["recommended_code_if_approved"],
                "recommended_name_vi_if_approved": row["recommended_name_vi_if_approved"],
                "recommended_name_en_if_approved": row["recommended_name_en_if_approved"],
                "sign_policy": row["sign_policy"],
                "gtsrb_mapping_proposal": row["gtsrb"]["mapping_proposal"],
                "gtsrb_source_relation": row["gtsrb"]["source_relation"],
                "gtsrb_disposition": row["gtsrb"]["disposition"],
                "unknown_policy": row["unknown_policy"],
                "reviewer_action": row["reviewer_action"],
                "recommendation_rationale": row["recommendation_rationale"],
                "conflict_flag": str(row["conflict_flag"]).lower(),
                "reviewer_status": row["reviewer_status"],
                "approval_boundary": row["approval_boundary"],
                "wp4_atlas_page": row["wp4_atlas_page"],
                "wp8_atlas_page": row["wp8_atlas_page"],
            }
        )
    return flattened


def recommendation_payload(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "package": "M0-WP8",
        "status": PACKAGE_STATUS,
        "decision_boundary": EVIDENCE_BOUNDARY,
        "class_count": len(rows),
        "all_rows_unapproved": all(row["reviewer_status"] == "UNAPPROVED" for row in rows),
        "d03_status": "PENDING",
        "gate0": "BLOCKED",
        "training_authorized": False,
        "rows": rows,
    }


def summary_payload(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "package": "M0-WP8",
        "status": PACKAGE_STATUS,
        "decision_boundary": EVIDENCE_BOUNDARY,
        "class_count": len(rows),
        "representative_count": sum(len(row["representatives"]) for row in rows),
        "atlas_page_count": EXPECTED_ATLAS_PAGE_COUNT,
        "native_recommendation_counts": dict(sorted(Counter(row["native_recommendation"] for row in rows).items())),
        "gtsrb_disposition_counts": dict(sorted(Counter(row["gtsrb"]["disposition"] for row in rows).items())),
        "sign_policy_counts": dict(sorted(Counter(row["sign_policy"] for row in rows).items())),
        "unknown_policy_counts": dict(sorted(Counter(row["unknown_policy"] for row in rows).items())),
        "wp4_match_status_counts": dict(sorted(Counter(row["wp4_evidence"]["match_status"] for row in rows).items())),
        "conflict_class_ids": [row["class_id"] for row in rows if row["conflict_flag"]],
        "rare_class_ids": [row["class_id"] for row in rows if row["support"]["rare_flag"]],
        "rare_definition": f"image_count < {RARE_IMAGE_THRESHOLD}; support never changes semantics",
        "package_recommendation": "VERSION_NATIVE_52_CLASS_TAXONOMY_FIRST_GTSRB_ANALYSIS_ONLY",
        "d03_status": "PENDING",
        "all_rows_unapproved": True,
        "relabel_authorized": False,
        "split_authorized": False,
        "training_authorized": False,
        "gate0": "BLOCKED",
    }


def reviewer_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    )
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    value: str,
    x: int,
    y: int,
    width: int,
    text_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: str,
) -> int:
    words = value.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and draw.textlength(candidate, font=text_font) > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current or not lines:
        lines.append(current)
    line_height = draw.textbbox((0, 0), "Ag", font=text_font)[3] + 4
    for index, line in enumerate(lines):
        draw.text((x, y + index * line_height), line, font=text_font, fill=fill)
    return y + len(lines) * line_height


def panel_digest(row: dict[str, Any]) -> str:
    payload = {
        "class_id": row["class_id"],
        "dataset_code": row["dataset_code"],
        "match_status": row["wp4_evidence"]["match_status"],
        "native_recommendation": row["native_recommendation"],
        "recommended_code_if_approved": row["recommended_code_if_approved"],
        "recommended_name_vi_if_approved": row["recommended_name_vi_if_approved"],
        "sign_policy": row["sign_policy"],
        "gtsrb_disposition": row["gtsrb"]["disposition"],
        "unknown_policy": row["unknown_policy"],
        "reviewer_action": row["reviewer_action"],
        "rationale": row["recommendation_rationale"],
    }
    return sha256_bytes(canonical_json(payload).encode("utf-8"))


def render_atlas_page(
    repo_root: Path, rows: list[dict[str, Any]], page_number: int
) -> tuple[bytes, dict[str, Any]]:
    source_path = repo_root / WP4_ASSETS_RELATIVE_PATH / f"page_{page_number:03d}.jpg"
    with Image.open(source_path) as source_image:
        source = source_image.convert("RGB")
    if source.size != (1200, 1818):
        raise ValueError(f"unexpected WP4 atlas dimensions on page {page_number}")
    canvas = Image.new("RGB", (1900, 1818), "white")
    canvas.paste(source, (0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.line((1200, 0, 1200, 1818), fill="#111827", width=3)
    title_font = reviewer_font(22)
    body_font = reviewer_font(15)
    small_font = reviewer_font(13)
    draw.rectangle((1203, 0, 1900, 60), fill="#111827")
    draw.text((1220, 8), f"M0-WP8 decision overlay {page_number:03d}/013", font=title_font, fill="white")
    draw.text((1220, 36), "PROPOSAL ONLY | all rows UNAPPROVED | D03 PENDING", font=small_font, fill="#fde68a")
    page_rows = rows[(page_number - 1) * CLASSES_PER_PAGE : page_number * CLASSES_PER_PAGE]
    audits: list[dict[str, Any]] = []
    block_height = 439
    colors = {
        "KEEP_CURRENT": "#065f46",
        "CORRECT_CODE_OR_NAME_PROPOSAL": "#92400e",
        "SEMANTIC_REVIEW_REQUIRED": "#991b1b",
        "OUT_OF_SCOPE_PROPOSAL": "#6b21a8",
    }
    for index, row in enumerate(page_rows):
        top = 60 + index * block_height
        bottom = 1818 if index == len(page_rows) - 1 else top + block_height
        draw.rectangle((1203, top, 1899, bottom), fill="#f9fafb" if index % 2 == 0 else "#eef2ff", outline="#9ca3af", width=1)
        cursor = top + 8
        lines = [
            (f"Class {row['class_id']} | current {row['dataset_code']} | WP4 {row['wp4_evidence']['match_status']}", "#111827"),
            (f"Native: {row['native_recommendation']}", colors[row["native_recommendation"]]),
            (f"If approved: {row['recommended_code_if_approved'] or 'UNRESOLVED'} | {row['recommended_name_vi_if_approved'] or 'UNRESOLVED'}", "#1d4ed8"),
            (f"Policy: {row['sign_policy']}", "#111827"),
            (f"GTSRB: {row['gtsrb']['mapping_proposal']} | {row['gtsrb']['disposition']}", "#111827"),
            (f"UNKNOWN: {row['unknown_policy']}", "#111827"),
            (f"Support: {row['support']['image_count']} images / {row['support']['box_count']} boxes | risk {row['support']['risk_band']} | rare {str(row['support']['rare_flag']).lower()}", "#111827"),
            (f"Action: {row['reviewer_action']}", "#374151"),
            (f"Why: {row['recommendation_rationale']}", "#374151"),
        ]
        for text_value, fill in lines:
            cursor = draw_wrapped(draw, text_value, 1220, cursor, 650, body_font, fill) + 3
        if cursor > bottom - 5:
            raise RuntimeError(f"WP8 atlas text overflow for class {row['class_id']}")
        audits.append(
            {
                "class_id": row["class_id"],
                "slot": index + 1,
                "text_bounds": [1220, top + 8, 1870, cursor],
                "all_bounds_fit": True,
                "source_wp4_page": row["wp4_atlas_page"],
                "panel_text_sha256": panel_digest(row),
                "reviewer_status": "UNAPPROVED",
            }
        )
    buffer = io.BytesIO()
    canvas.save(buffer, format="PNG", optimize=False)
    payload = buffer.getvalue()
    audit = {
        "page": page_number,
        "path": f"{ASSETS_RELATIVE_PATH}/page_{page_number:03d}.png",
        "source_wp4_path": f"{WP4_ASSETS_RELATIVE_PATH}/page_{page_number:03d}.jpg",
        "source_wp4_sha256": sha256_file(source_path),
        "render_sha256": sha256_bytes(payload),
        "width": 1900,
        "height": 1818,
        "row_count": len(page_rows),
        "rows": audits,
    }
    return payload, audit


def atlas_payloads(repo_root: Path, rows: list[dict[str, Any]]) -> tuple[list[bytes], dict[str, Any]]:
    pages: list[bytes] = []
    audits: list[dict[str, Any]] = []
    for page_number in range(1, EXPECTED_ATLAS_PAGE_COUNT + 1):
        payload, audit = render_atlas_page(repo_root, rows, page_number)
        pages.append(payload)
        audits.append(audit)
    layout = {
        "schema_version": 1,
        "status": "PASS_52_ROWS_13_PAGES_COMPLETE_TEXT_BOUNDS_AND_PINNED_WP4_BACKGROUND",
        "decision_boundary": EVIDENCE_BOUNDARY,
        "page_count": EXPECTED_ATLAS_PAGE_COUNT,
        "class_count": EXPECTED_CLASS_COUNT,
        "classes_per_page": CLASSES_PER_PAGE,
        "all_rows_unapproved": True,
        "all_text_complete": True,
        "all_bounds_fit": True,
        "all_wp4_backgrounds_pinned": True,
        "pages": audits,
    }
    return pages, layout


def render_index(rows: list[dict[str, Any]]) -> str:
    body = [
        "<!doctype html><meta charset='utf-8'><title>M0-WP8 taxonomy decision atlas</title>",
        "<style>body{font-family:system-ui;margin:2rem;max-width:1400px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #bbb;padding:.4rem;vertical-align:top}code{font-size:.85rem}</style>",
        "<h1>M0-WP8 provisional 52-class taxonomy recommendation</h1>",
        f"<p>{html.escape(EVIDENCE_BOUNDARY)}</p>",
        "<p>Each PNG preserves the pinned WP4 visual evidence at left and adds the provisional WP8 decision panel at right.</p>",
        "<table><thead><tr><th>ID</th><th>Current</th><th>WP4</th><th>Native recommendation</th><th>GTSRB</th><th>Policy</th><th>Atlas</th></tr></thead><tbody>",
    ]
    for row in rows:
        page = row["class_id"] // CLASSES_PER_PAGE + 1
        body.append(
            f"<tr><td>{row['class_id']}</td><td>{html.escape(row['dataset_code'])}</td>"
            f"<td>{row['wp4_evidence']['match_status']}</td><td>{row['native_recommendation']}</td>"
            f"<td>{row['gtsrb']['disposition']}</td><td>{row['sign_policy']}</td>"
            f"<td><a href='page_{page:03d}.png'>page {page:03d}</a></td></tr>"
        )
    body.append("</tbody></table>")
    return "\n".join(body) + "\n"


def render_report(rows: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    native_counts = "\n".join(f"- `{key}`: {value}" for key, value in summary["native_recommendation_counts"].items())
    gtsrb_counts = "\n".join(f"- `{key}`: {value}" for key, value in summary["gtsrb_disposition_counts"].items())
    conflicts = [
        "| ID | Current | WP4 | Candidate | Native recommendation | GTSRB | Required reviewer action |",
        "|---:|---|---|---|---|---|---|",
    ]
    for class_id in EXPECTED_CONFLICT_IDS:
        row = rows[class_id]
        candidate = row["recommended_code_if_approved"] or "UNRESOLVED"
        conflicts.append(
            f"| {class_id} | `{row['dataset_code']}` | {row['wp4_evidence']['match_status']} | `{candidate}` | `{row['native_recommendation']}` | `{row['gtsrb']['disposition']}` | {row['reviewer_action']} |"
        )
    qa_repairs = [
        "| ID | Current dataset label | Proposed QCVN-aligned code/name | Native recommendation | Sign policy | Required reviewer action |",
        "|---:|---|---|---|---|---|",
    ]
    for class_id in EXPECTED_QA_REPAIR_ROWS:
        row = rows[class_id]
        qa_repairs.append(
            f"| {class_id} | {row['dataset_name_vi_en']} | `{row['recommended_code_if_approved']}` / {row['recommended_name_en_if_approved']} | `{row['native_recommendation']}` | `{row['sign_policy']}` | {row['reviewer_action']} |"
        )
    matrix = [
        "| ID | Current | WP4 | Native recommendation | Sign policy | GTSRB disposition | UNKNOWN route | Rare |",
        "|---:|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        matrix.append(
            f"| {row['class_id']} | `{row['dataset_code']}` | {row['wp4_evidence']['match_status']} | `{row['native_recommendation']}` | `{row['sign_policy']}` | `{row['gtsrb']['disposition']}` | `{row['unknown_policy']}` | {str(row['support']['rare_flag']).lower()} |"
        )
    return f"""# M0-WP8 - Provisional 52-class taxonomy recommendation

Status: `{PACKAGE_STATUS}`  
Boundary: `{EVIDENCE_BOUNDARY}`

This is a PM recommendation package for independent QA and domain review. It does not decide D-03, relabel data, create a split, authorize training, or convert a GTSRB relation into Vietnamese taxonomy truth. Every row remains `UNAPPROVED`.

## Package-level recommendation

1. Version the native DATASET01 52-class taxonomy first.
2. Keep every GTSRB relation analysis-only; never use it as an automatic merge or training target.
3. Apply code/name corrections only after per-row approval.
4. Route unresolved variant, composite, supplementary, or out-of-scope cases to explicit review and, if needed, a future UNKNOWN policy.
5. Treat support and rarity as data-risk metadata only. `rare_flag=true` means fewer than {RARE_IMAGE_THRESHOLD} images and never authorizes semantic merging.

## Recommendation counts

{native_counts}

## GTSRB dispositions

{gtsrb_counts}

## Required conflict register

{chr(10).join(conflicts)}

The register deliberately preserves these boundaries: S.505a means supplementary `Loại xe`; B.8a is a section/figure while P.108a is the sign code; P.124b1 is unsupported and P.124b is only a candidate; class 31 has no asserted QCVN code; class 51 is an exact native W.246c row but only a partial GTSRB analysis relation; class 23 requires P.111a-d variant review rather than a generic P.111 assignment.

## WP8-R1 QA repair clarifications

{chr(10).join(qa_repairs)}

For class 14, all three pinned representatives depict ordinary P.106a without a numeric weight value. QCVN section B.6 assigns the fixed truck prohibition to P.106a and the numeric weight parameter to P.106b. The other three rows retain their QCVN codes but require explicit English-name correction proposals. These remain reviewer proposals, not approved relabels.

## Complete reviewer matrix

{chr(10).join(matrix)}

## Evidence and audit trail

- Machine-readable matrix: `{MATRIX_CSV_RELATIVE_PATH}` and `{MATRIX_JSON_RELATIVE_PATH}`.
- Each row carries exact WP4 evidence, QCVN page/section/figure or scoped NOT_FOUND evidence, support/risk, three representative stems, image and label SHA-256 values, and source bbox line/coordinates.
- Decision atlas: `{ASSETS_RELATIVE_PATH}/index.html` plus {EXPECTED_ATLAS_PAGE_COUNT} PNG pages, derived from the pinned WP4 atlas without rebuilding WP4.
- Layout audit: `{LAYOUT_RELATIVE_PATH}`.
- Manifest and verifier: `{MANIFEST_RELATIVE_PATH}` and `scripts/build_wp8_taxonomy_recommendation.py verify`.

## Governance

- All 52 rows: `UNAPPROVED`.
- D-03: `PENDING`.
- Gate 0: `BLOCKED`.
- Relabel, split, and training: not authorized.
"""


def build_manifest(repo_root: Path) -> dict[str, Any]:
    sources = [relative_record(path, repo_root, item_id) for item_id, path, _pinned in source_contract(repo_root)]
    artifacts = [relative_record(path, repo_root, item_id) for item_id, path in artifact_contract(repo_root)]
    return {
        "schema_version": 1,
        "package": "M0-WP8",
        "status": PACKAGE_STATUS,
        "decision_boundary": EVIDENCE_BOUNDARY,
        "manifest_path": MANIFEST_RELATIVE_PATH,
        "manifest_self_in_artifact_count": False,
        "artifact_count_semantics": "EXCLUDES_MANIFEST_FILE",
        "class_count": EXPECTED_CLASS_COUNT,
        "representative_count": EXPECTED_REPRESENTATIVE_COUNT,
        "atlas_page_count": EXPECTED_ATLAS_PAGE_COUNT,
        "all_rows_unapproved": True,
        "d03_status": "PENDING",
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


def contract_pairs(
    contract: list[tuple[str, Path]] | list[tuple[str, Path, str | None]], repo_root: Path
) -> list[tuple[str, str]]:
    return [(item[0], item[1].relative_to(repo_root).as_posix()) for item in contract]


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
        if isinstance(item_id, str) and isinstance(path_value, str):
            pairs.append((item_id, path_value))
        if not isinstance(path_value, str):
            errors.append(f"{name}[{index}].path invalid")
        else:
            try:
                safe_child(repo_root, path_value)
            except (ValueError, OSError) as exc:
                errors.append(str(exc))
        digest = record.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            errors.append(f"{name}[{index}].sha256 invalid")
        size = record.get("size")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            errors.append(f"{name}[{index}].size invalid")
        records.append(record)
    if len(set(item_id for item_id, _path in pairs)) != len(pairs):
        errors.append(f"duplicate {name} IDs")
    if len(set(path for _item_id, path in pairs)) != len(pairs):
        errors.append(f"duplicate {name} paths")
    if pairs != expected:
        errors.append(f"{name} roster/order differs from canonical contract")
    return records


def verify_manifest(manifest_path: Path, repo_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        return {"valid": False, "errors": [f"manifest unreadable: {exc}"]}
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["manifest root must be an object"]}
    expected_top = {
        "schema_version", "package", "status", "decision_boundary", "manifest_path",
        "manifest_self_in_artifact_count", "artifact_count_semantics", "class_count",
        "representative_count", "atlas_page_count", "all_rows_unapproved", "d03_status",
        "gate0", "relabel_authorized", "split_authorized", "training_authorized",
        "source_count", "artifact_count", "total_artifact_bytes", "sources", "artifacts",
    }
    if set(payload) != expected_top:
        errors.append("manifest top-level fields differ from WP8 schema")
    constants = {
        "schema_version": 1,
        "package": "M0-WP8",
        "status": PACKAGE_STATUS,
        "decision_boundary": EVIDENCE_BOUNDARY,
        "manifest_path": MANIFEST_RELATIVE_PATH,
        "manifest_self_in_artifact_count": False,
        "artifact_count_semantics": "EXCLUDES_MANIFEST_FILE",
        "class_count": EXPECTED_CLASS_COUNT,
        "representative_count": EXPECTED_REPRESENTATIVE_COUNT,
        "atlas_page_count": EXPECTED_ATLAS_PAGE_COUNT,
        "all_rows_unapproved": True,
        "d03_status": "PENDING",
        "gate0": "BLOCKED",
        "relabel_authorized": False,
        "split_authorized": False,
        "training_authorized": False,
    }
    for field, expected in constants.items():
        if payload.get(field) != expected:
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

    if not errors:
        try:
            verify_pinned_sources(repo_root)
            rows = build_rows(repo_root)
            expected_matrix = recommendation_payload(rows)
            actual_matrix = json.loads((repo_root / MATRIX_JSON_RELATIVE_PATH).read_text(encoding="utf-8"))
            if actual_matrix != expected_matrix:
                raise ValueError("WP8 JSON matrix differs from pinned source contract/evidence")
            if read_csv(repo_root / MATRIX_CSV_RELATIVE_PATH) != [
                {field: str(value) for field, value in row.items()}
                for row in flatten_rows(rows)
            ]:
                raise ValueError("WP8 CSV matrix differs from pinned source contract/evidence")
            summary = summary_payload(rows)
            if json.loads((repo_root / SUMMARY_RELATIVE_PATH).read_text(encoding="utf-8")) != summary:
                raise ValueError("WP8 summary differs from independently derived rows")
            if (repo_root / REPORT_RELATIVE_PATH).read_text(encoding="utf-8") != render_report(rows, summary):
                raise ValueError("WP8 report differs from independently derived rows")
            if (repo_root / ASSETS_RELATIVE_PATH / "index.html").read_text(encoding="utf-8") != render_index(rows):
                raise ValueError("WP8 atlas index differs from independently derived rows")
            expected_pages, expected_layout = atlas_payloads(repo_root, rows)
            actual_layout = json.loads((repo_root / LAYOUT_RELATIVE_PATH).read_text(encoding="utf-8"))
            if actual_layout != expected_layout:
                raise ValueError("WP8 layout audit differs from deterministic atlas layout")
            for page_number, expected_page in enumerate(expected_pages, start=1):
                page_path = repo_root / ASSETS_RELATIVE_PATH / f"page_{page_number:03d}.png"
                if page_path.read_bytes() != expected_page:
                    raise ValueError(f"WP8 atlas page {page_number} differs from deterministic pinned-source render")
                with Image.open(page_path) as image:
                    if image.size != (1900, 1818) or image.format != "PNG":
                        raise ValueError(f"WP8 atlas page {page_number} image contract mismatch")
                    image.verify()
            forbidden = {"final_class_id", "approved_code", "assigned_split", "training_target"}
            if any(forbidden & set(row) for row in rows):
                raise ValueError("WP8 rows contain approval/training fields")
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


def build(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    verify_pinned_sources(repo_root)
    rows = build_rows(repo_root)
    matrix = recommendation_payload(rows)
    summary = summary_payload(rows)
    write_json(repo_root / MATRIX_JSON_RELATIVE_PATH, matrix)
    write_csv(repo_root / MATRIX_CSV_RELATIVE_PATH, flatten_rows(rows), CSV_FIELDS)
    write_json(repo_root / SUMMARY_RELATIVE_PATH, summary)

    pages, layout = atlas_payloads(repo_root, rows)
    assets = repo_root / ASSETS_RELATIVE_PATH
    assets.mkdir(parents=True, exist_ok=True)
    expected_names = {"index.html", *(f"page_{page:03d}.png" for page in range(1, 14))}
    for existing in assets.iterdir():
        if existing.is_file() and existing.name not in expected_names:
            raise ValueError(f"unexpected pre-existing WP8 atlas file: {existing.name}")
    for page_number, payload in enumerate(pages, start=1):
        (assets / f"page_{page_number:03d}.png").write_bytes(payload)
    (assets / "index.html").write_text(render_index(rows), encoding="utf-8")
    write_json(repo_root / LAYOUT_RELATIVE_PATH, layout)
    (repo_root / REPORT_RELATIVE_PATH).write_text(render_report(rows, summary), encoding="utf-8")

    manifest = build_manifest(repo_root)
    write_json(repo_root / MANIFEST_RELATIVE_PATH, manifest)
    result = verify_manifest(repo_root / MANIFEST_RELATIVE_PATH, repo_root)
    if not result["valid"]:
        raise RuntimeError(f"WP8 package verification failed: {result['errors']}")
    return {
        "status": PACKAGE_STATUS,
        "class_count": EXPECTED_CLASS_COUNT,
        "representative_count": EXPECTED_REPRESENTATIVE_COUNT,
        "atlas_page_count": EXPECTED_ATLAS_PAGE_COUNT,
        "source_count": manifest["source_count"],
        "artifact_count": manifest["artifact_count"],
        "manifest_sha256": sha256_file(repo_root / MANIFEST_RELATIVE_PATH),
        "native_recommendation_counts": summary["native_recommendation_counts"],
        "gtsrb_disposition_counts": summary["gtsrb_disposition_counts"],
        "conflict_class_ids": summary["conflict_class_ids"],
        "rare_class_count": len(summary["rare_class_ids"]),
        "all_rows_unapproved": True,
        "d03_status": "PENDING",
        "gate0": "BLOCKED",
        "training_authorized": False,
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("build", "verify"):
        command = commands.add_parser(name)
        command.add_argument("--repo-root", type=Path, required=True)
    commands.choices["verify"].add_argument("--manifest", type=Path, default=Path(MANIFEST_RELATIVE_PATH))
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    if args.command == "build":
        result = build(repo_root)
    else:
        manifest = args.manifest
        if not manifest.is_absolute():
            manifest = repo_root / manifest
        result = verify_manifest(manifest, repo_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if args.command != "verify" or result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
