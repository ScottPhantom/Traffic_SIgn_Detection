# ruff: noqa: E501
"""Build and verify the M0-WP11 D-04 rare-class decision-support package."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

PACKAGE_STATUS = "M0_WP11_AWAITING_QA_D04_DECISION_SUPPORT_ONLY"
EVIDENCE_BOUNDARY = "D04_DECISION_SUPPORT_ONLY_NO_OWNER_APPROVAL_NO_SEMANTIC_MERGE_NO_RAW_MUTATION_NO_SPLIT_NO_TRAINING"
RARE_POLICY = "box_count < 50"
EXPECTED_CLASS_COUNT = 52
EXPECTED_RARE_IDS = [1, 4, 9, 11, 15, 19, 21, 25, 27, 28, 29, 31, 33, 37, 42, 43, 44, 47, 48, 51]
EXTREME_CLASS_IDS = [44, 51]

CONTRACT_RELATIVE_PATH = "references/dataset01/wp11_d04_rare_class_contract.json"
MATRIX_JSON_RELATIVE_PATH = "docs/review/generated/wp11_d04_class_matrix.json"
MATRIX_CSV_RELATIVE_PATH = "docs/review/generated/wp11_d04_class_matrix.csv"
RARE_JSON_RELATIVE_PATH = "docs/review/generated/wp11_d04_rare_subset.json"
RARE_CSV_RELATIVE_PATH = "docs/review/generated/wp11_d04_rare_subset.csv"
EXTREME_CSV_RELATIVE_PATH = "docs/review/generated/wp11_d04_extreme_lineage.csv"
LAYOUT_RELATIVE_PATH = "docs/review/generated/wp11_d04_layout_audit.json"
REPORT_RELATIVE_PATH = "docs/review/wp11_d04_rare_class_report.md"
ASSET_DIR_RELATIVE_PATH = "docs/review/assets/wp11/d04_extreme_atlas"
MANIFEST_RELATIVE_PATH = "docs/review/generated/wp11_d04_manifest.json"

EXPECTED_PINNED_HASHES = {
    "contract": "c90c4caad941bdc89dd619969c4dbdc248af0bc26e0ae44c678157e29d7e50f6",
    "per_class_counts": "bdff0e3817470757f058b415ee7284d0f1b631ce4454eeb9b158bf6a6a6aa280",
    "image_inventory": "d45aa7f398a040c44cbc040f4ec005d7e5a8ef50586e905315f76c792ca29022",
    "source_preservation": "5ca3e769b9197cad19bcb75f553dd59fee6e3035e0cc86cd9693737f84a713d7",
    "wp1_manifest": "28adbf21dd2057fe5fc7999daccaa52d1201ea0459ef1bb7475a780ed85c51c6",
    "historical_decision_status": "87d81262e907bb1c479cfac6535e7b3f67a368c371e96b810aa02f2e92d0d72c",
    "wp8_manifest": "9d8fc460b8162874b4082940b0e7f3ceb174c068a92378974ebd93b55da20348",
    "wp8_matrix": "9a0e918baf61f58692ffd1dd728341fdd2a3457386144c78a54c33a996866efa",
    "wp8_summary": "b608172a6fd78fce07c515d5a4219e441da16dc58ddd5d0aa451e6080d37db53",
    "wp10_manifest": "9c9581e2026f036a79fc1c58bce5f1b87e4c4f0786ee50a49f890e94d0e529e5",
    "wp10_registry": "0b79dc0507577d9d69c6cb1ce5164c34470dd4104ac177f3efbbfafd0d2f3fe2",
    "wp10_overlay": "4e200af3daccc1d89078ee60fefa0164655a9696626effd7feb58e85c583a71e",
    "raw_image_0530": "74bd8303cbcc9c10a2b3bccecb7bddab2684a6e2e3344941396265409b44e03b",
    "raw_label_0530": "df1a009a370bd8f39728bb1463a27fa16325ee99cf7b9851636b206bf4e77ea3",
    "raw_image_0531": "5cc052cfb7f78e212864d0b619d5f5e1221fa03713989fb6f5322f2acf904dfb",
    "raw_label_0531": "d9b10e09728c4e2a3960dfb0d74f364a6bfec43a707c972f4e137798347c9026",
    "raw_image_0532": "131656e687499e61ea9ad02169a1b2b123e657e7015a68419d4e3f8cc3311254",
    "raw_label_0532": "df8565d9bcc6cabb228ff729b686e414cac0abefd2f0522681538daef3d4ea7e",
    "raw_image_0533": "b55301e7c82e5e64f7bc9ad503135dc9c9c592c7a1e085b94aa9fb713e705dca",
    "raw_label_0533": "c400b1b1ca2401362820781fe63648d060cae05300dd25d2f4bd7db78685e2a2",
    "raw_image_0534": "1691fec081ca9f40fb08f363c0850e8819d2c8824cea730cad2fab0851da935c",
    "raw_label_0534": "45c21ca4d33886f8a23f8248d83eb8c07d4bf5a9c39b1b34e71f4e205c016776",
    "raw_image_0670": "67c626badb1d182cca6f1959fda61e081e14b9e66de0ec8e8242cef0f824b095",
    "raw_label_0670": "c2c3cad0cf7b28464431c124d4a1c3f618d7a3c9fdb6fc5a880b3b05fa90c4cb",
    "raw_image_0671": "ef136cb7bf2df21d1f2fc1a451be15a65a83528da8f4709dcbc26c1213d81d8b",
    "raw_label_0671": "8d1bdcc1263e72c6c2edb83d3771d980745ce3845ca9ead3f99c9fd882cabd3c",
    "raw_image_0672": "5e25766817091316d971f59ba6a7392e618909583a0729ceeefef785760b7bfd",
    "raw_label_0672": "0becf97d025a2e6dca9f651c3e7030107a3c8437c915f1d05878274c19d14cfe",
}

EXTREME_STEMS = ["0670", "0671", "0672", "0530", "0531", "0532", "0533", "0534"]

CSV_FIELDS = [
    "class_id",
    "dataset_code",
    "name_en",
    "name_vi",
    "image_count",
    "box_count",
    "source_train_image_count",
    "source_test_image_count",
    "source_unsplit_image_count",
    "post_quarantine_eligible_image_count",
    "post_quarantine_eligible_box_count",
    "g04_excluded_stems",
    "g04_effect",
    "representative_stems",
    "representative_image_sha256s",
    "representative_label_sha256s",
    "wp8_rare_flag_image_lt_100",
    "wp8_taxonomy_status",
    "wp8_native_recommendation",
    "wp8_sign_policy",
    "wp8_conflict_flag",
    "d04_in_scope_box_lt_50",
    "d04_recommended_action",
    "d04_comparison_eligibility",
    "d04_recommendation_confidence",
    "d04_owner_status",
    "d04_rationale",
    "d02_group_identity_status",
    "effective_independent_support",
    "leakage_risk",
    "raw_split_usage",
    "gate0",
    "training_authorized",
]

EXTREME_FIELDS = [
    "class_id", "dataset_code", "stem", "source_split_descriptive_only", "image_path",
    "image_sha256", "label_path", "label_sha256", "label_line_number", "normalized_x_center",
    "normalized_y_center", "normalized_width", "normalized_height", "pixel_x_min", "pixel_y_min",
    "pixel_x_max", "pixel_y_max", "bbox_inside_image", "effective_independent_support",
    "group_identity_status", "atlas_page", "atlas_slot",
]


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


def csv_bytes(rows: list[dict[str, Any]], fields: list[str]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


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
        raise ValueError("WP2 bbox evidence has an unexpected raw image path")
    return image_path.parents[2]


def source_contract(repo_root: Path, raw_root: Path) -> list[tuple[str, str, str, Path, str]]:
    audit = repo_root / "results/data_audit/DATASET01_052bc980a7206f8d"
    generated = repo_root / "docs/review/generated"
    sources = [
        ("contract", "repo", CONTRACT_RELATIVE_PATH, repo_root / CONTRACT_RELATIVE_PATH, EXPECTED_PINNED_HASHES["contract"]),
        ("per_class_counts", "repo", "results/data_audit/DATASET01_052bc980a7206f8d/per_class_counts.csv", audit / "per_class_counts.csv", EXPECTED_PINNED_HASHES["per_class_counts"]),
        ("image_inventory", "repo", "results/data_audit/DATASET01_052bc980a7206f8d/image_inventory.csv", audit / "image_inventory.csv", EXPECTED_PINNED_HASHES["image_inventory"]),
        ("source_preservation", "repo", "results/data_audit/DATASET01_052bc980a7206f8d/source_preservation_proof.json", audit / "source_preservation_proof.json", EXPECTED_PINNED_HASHES["source_preservation"]),
        ("wp1_manifest", "repo", "results/data_audit/DATASET01_052bc980a7206f8d/wp1_artifact_manifest.json", audit / "wp1_artifact_manifest.json", EXPECTED_PINNED_HASHES["wp1_manifest"]),
        ("historical_decision_status", "repo", "docs/review/decision_status.json", repo_root / "docs/review/decision_status.json", EXPECTED_PINNED_HASHES["historical_decision_status"]),
        ("wp8_manifest", "repo", "docs/review/generated/wp8_taxonomy_manifest.json", generated / "wp8_taxonomy_manifest.json", EXPECTED_PINNED_HASHES["wp8_manifest"]),
        ("wp8_matrix", "repo", "docs/review/generated/wp8_taxonomy_recommendation.json", generated / "wp8_taxonomy_recommendation.json", EXPECTED_PINNED_HASHES["wp8_matrix"]),
        ("wp8_summary", "repo", "docs/review/generated/wp8_taxonomy_summary.json", generated / "wp8_taxonomy_summary.json", EXPECTED_PINNED_HASHES["wp8_summary"]),
        ("wp10_manifest", "repo", "docs/review/generated/wp10_g04_quarantine_manifest.json", generated / "wp10_g04_quarantine_manifest.json", EXPECTED_PINNED_HASHES["wp10_manifest"]),
        ("wp10_registry", "repo", "docs/review/generated/wp10_quarantine_registry.json", generated / "wp10_quarantine_registry.json", EXPECTED_PINNED_HASHES["wp10_registry"]),
        ("wp10_overlay", "repo", "docs/review/generated/wp10_g04_owner_decision_overlay.json", generated / "wp10_g04_owner_decision_overlay.json", EXPECTED_PINNED_HASHES["wp10_overlay"]),
    ]
    for stem in EXTREME_STEMS:
        sources.extend(
            [
                (f"raw_image_{stem}", "raw", f"archive/images/{stem}.jpg", raw_root / f"archive/images/{stem}.jpg", EXPECTED_PINNED_HASHES[f"raw_image_{stem}"]),
                (f"raw_label_{stem}", "raw", f"archive/labels/{stem}.txt", raw_root / f"archive/labels/{stem}.txt", EXPECTED_PINNED_HASHES[f"raw_label_{stem}"]),
            ]
        )
    return sources


def artifact_contract(repo_root: Path) -> list[tuple[str, str, Path]]:
    return [
        ("class_matrix_json", MATRIX_JSON_RELATIVE_PATH, repo_root / MATRIX_JSON_RELATIVE_PATH),
        ("class_matrix_csv", MATRIX_CSV_RELATIVE_PATH, repo_root / MATRIX_CSV_RELATIVE_PATH),
        ("rare_subset_json", RARE_JSON_RELATIVE_PATH, repo_root / RARE_JSON_RELATIVE_PATH),
        ("rare_subset_csv", RARE_CSV_RELATIVE_PATH, repo_root / RARE_CSV_RELATIVE_PATH),
        ("extreme_lineage_csv", EXTREME_CSV_RELATIVE_PATH, repo_root / EXTREME_CSV_RELATIVE_PATH),
        ("layout_audit", LAYOUT_RELATIVE_PATH, repo_root / LAYOUT_RELATIVE_PATH),
        ("report", REPORT_RELATIVE_PATH, repo_root / REPORT_RELATIVE_PATH),
        ("atlas_class_044", f"{ASSET_DIR_RELATIVE_PATH}/class_044.png", repo_root / ASSET_DIR_RELATIVE_PATH / "class_044.png"),
        ("atlas_class_051", f"{ASSET_DIR_RELATIVE_PATH}/class_051.png", repo_root / ASSET_DIR_RELATIVE_PATH / "class_051.png"),
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


def validate_contract(repo_root: Path) -> dict[str, Any]:
    payload = json.loads((repo_root / CONTRACT_RELATIVE_PATH).read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1 or payload.get("package") != "M0-WP11" or payload.get("status") != "D04_DECISION_SUPPORT_AWAITING_QA":
        raise ValueError("WP11 contract identity/status mismatch")
    policy = payload.get("current_d04_policy", {})
    if policy != {"field": "box_count", "operator": "<", "value": 50, "in_scope_class_ids": EXPECTED_RARE_IDS, "scope_count": 20}:
        raise ValueError("WP11 current D04 policy mismatch")
    if payload.get("recommendation_policy") != {
        "box_count_lte_20": "COLLECT_MORE",
        "box_count_21_to_49": "OWNER_REVIEW_REQUIRED",
        "outside_current_d04_scope": "KEEP_NATIVE_PENDING_D03",
        "automatic_semantic_merge_allowed": False,
        "owner_status": "PENDING",
    }:
        raise ValueError("WP11 recommendation policy mismatch")
    if [row.get("class_id") for row in payload.get("extreme_classes", [])] != EXTREME_CLASS_IDS:
        raise ValueError("WP11 extreme-class roster/order mismatch")
    if payload.get("quarantine_effect") != {
        "stem": "0248", "class_id": 49, "excluded_image_count": 1, "excluded_box_count": 2,
        "derived_clip_counted_as_training_sample": False, "class_49_taxonomy_excluded": False,
    }:
        raise ValueError("WP11 G0.4 quarantine effect mismatch")
    rules = payload.get("evidence_rules", {})
    if rules != {
        "raw_split_is_independent_evidence": False,
        "adjacent_or_proxy_sequence_is_group_truth": False,
        "effective_independent_support": "UNKNOWN_PENDING_D02",
        "wp8_taxonomy_rows_must_remain": "UNAPPROVED",
        "d03_status": "PENDING",
        "d04_status": "PENDING_OWNER_DECISION",
        "gate0": "BLOCKED",
        "split_authorized": False,
        "training_authorized": False,
    } or payload.get("evidence_boundary") != EVIDENCE_BOUNDARY:
        raise ValueError("WP11 evidence/governance boundary mismatch")
    return payload


def validate_controls(repo_root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    decision = json.loads((repo_root / "docs/review/decision_status.json").read_text(encoding="utf-8"))
    d04 = decision["decisions"]["D-04"]
    if decision.get("gate0") != "BLOCKED" or decision.get("training_authorized") is not False:
        raise ValueError("Gate 0/training boundary changed")
    if d04.get("status") != "PENDING" or d04.get("selected_option") is not None:
        raise ValueError("D-04 must remain PENDING with no aggregate selection")
    if d04.get("scope_rule") != {"field": "box_count", "operator": "<", "value": 50} or d04.get("in_scope_class_ids") != EXPECTED_RARE_IDS:
        raise ValueError("D-04 scope drift")
    class_decisions = d04.get("class_decisions", {})
    if [int(class_id) for class_id in class_decisions] != EXPECTED_RARE_IDS:
        raise ValueError("D-04 class-decision roster/order drift")
    if any(record.get("status") != "PENDING" or record.get("selected_option") is not None for record in class_decisions.values()):
        raise ValueError("D-04 class decisions must remain PENDING")
    if decision["decisions"]["D-02"].get("status") != "PENDING" or decision["decisions"]["D-03"].get("status") != "PENDING":
        raise ValueError("D-02 and D-03 must remain PENDING")

    wp8 = json.loads((repo_root / "docs/review/generated/wp8_taxonomy_recommendation.json").read_text(encoding="utf-8"))
    if wp8.get("class_count") != 52 or wp8.get("all_rows_unapproved") is not True or wp8.get("d03_status") != "PENDING" or wp8.get("gate0") != "BLOCKED" or wp8.get("training_authorized") is not False:
        raise ValueError("WP8 taxonomy/governance boundary drift")
    if [row.get("class_id") for row in wp8.get("rows", [])] != list(range(52)) or any(row.get("reviewer_status") != "UNAPPROVED" for row in wp8["rows"]):
        raise ValueError("WP8 must retain exactly 52 UNAPPROVED rows")

    registry = json.loads((repo_root / "docs/review/generated/wp10_quarantine_registry.json").read_text(encoding="utf-8"))
    if registry.get("entry_count") != 1 or registry.get("quarantined_stem_count") != 1 or len(registry.get("entries", [])) != 1:
        raise ValueError("WP10 registry must contain exactly one quarantine entry")
    entry = registry["entries"][0]
    if entry.get("stem") != "0248" or entry.get("scope_type") != "ENTIRE_IMAGE_STEM" or entry.get("label_rows") != [1, 2]:
        raise ValueError("WP10 registry quarantine scope drift")
    if not entry.get("exclude_entire_stem_from_split_generation") or not entry.get("exclude_entire_stem_from_training") or entry.get("derived_clip_usage") != "REVIEW_EVIDENCE_ONLY_NOT_TRAINING_LABEL":
        raise ValueError("WP10 enforcement boundary drift")
    if entry.get("class_49_taxonomy_excluded") is not False or registry["governance"].get("training_authorized") is not False:
        raise ValueError("WP10 class-49/training boundary drift")
    return decision, wp8, registry


def recommendation_for(box_count: int) -> tuple[str, str, str, str]:
    if box_count <= 20:
        return (
            "COLLECT_MORE",
            "QUARANTINE_FROM_MODEL_COMPARISON_PENDING_DATA",
            "HIGH_COUNT_INTEGRITY_LOW_INDEPENDENT_SUPPORT",
            "Observed support is too small for reliable class-level model comparison; collect more independent-group evidence before evaluation.",
        )
    if box_count < 50:
        return (
            "OWNER_REVIEW_REQUIRED",
            "OWNER_REVIEW_REQUIRED_BEFORE_MODEL_COMPARISON",
            "HIGH_COUNT_INTEGRITY_LOW_INDEPENDENT_SUPPORT",
            "The class is in the current D-04 scope, but effective independent support is unknown until D-02 and a group-aware split are resolved.",
        )
    return (
        "KEEP_NATIVE_PENDING_D03",
        "NOT_IN_CURRENT_D04_SCOPE",
        "HIGH_SCOPE_CLASSIFICATION_ONLY",
        "The class is outside the current box_count < 50 D-04 scope; rarity does not authorize a semantic merge and D-03 remains pending.",
    )


def derive_matrix(repo_root: Path) -> list[dict[str, Any]]:
    _decision, wp8, _registry = validate_controls(repo_root)
    per_class = read_csv(repo_root / "results/data_audit/DATASET01_052bc980a7206f8d/per_class_counts.csv")
    if [int(row["class_id"]) for row in per_class] != list(range(52)):
        raise ValueError("per_class_counts must cover classes 0..51 exactly")
    wp8_rows = {int(row["class_id"]): row for row in wp8["rows"]}
    rows: list[dict[str, Any]] = []
    for source in per_class:
        class_id = int(source["class_id"])
        wp8_row = wp8_rows[class_id]
        image_count = int(source["image_count"])
        box_count = int(source["box_count"])
        if wp8_row["support"]["image_count"] != image_count or wp8_row["support"]["box_count"] != box_count:
            raise ValueError(f"WP8/support drift for class {class_id}")
        d04_in_scope = box_count < 50
        if d04_in_scope != (class_id in EXPECTED_RARE_IDS):
            raise ValueError(f"D-04 scope derivation drift for class {class_id}")
        action, comparison, confidence, rationale = recommendation_for(box_count)
        excluded_image_count = 1 if class_id == 49 else 0
        excluded_box_count = 2 if class_id == 49 else 0
        excluded_stems = ["0248"] if class_id == 49 else []
        train_count = int(source["train_image_count"])
        representatives = wp8_row["representatives"]
        if len(representatives) != 3:
            raise ValueError(f"WP8 representative count drift for class {class_id}")
        rows.append(
            {
                "class_id": class_id,
                "dataset_code": source["sign_code"],
                "name_en": source["name_en"],
                "name_vi": source["name_vi"],
                "support": {"image_count": image_count, "box_count": box_count},
                "source_split_image_counts": {
                    "train": train_count,
                    "test": int(source["test_image_count"]),
                    "unsplit": int(source["unsplit_image_count"]),
                    "usage": "DESCRIPTIVE_ONLY_NOT_INDEPENDENT_EVIDENCE",
                },
                "post_quarantine_eligibility": {
                    "eligible_image_count": image_count - excluded_image_count,
                    "eligible_box_count": box_count - excluded_box_count,
                    "eligible_train_image_count_descriptive_only": train_count - excluded_image_count,
                    "excluded_stems": excluded_stems,
                    "derived_clip_counted_as_training_sample": False,
                },
                "representative_samples": representatives,
                "g04_effect": "EXCLUDES_ENTIRE_STEM_0248_TWO_CLASS49_BOXES" if class_id == 49 else "NO_DIRECT_COUNT_EFFECT",
                "wp8_taxonomy": {
                    "reviewer_status": wp8_row["reviewer_status"],
                    "native_recommendation": wp8_row["native_recommendation"],
                    "sign_policy": wp8_row["sign_policy"],
                    "conflict_flag": wp8_row["conflict_flag"],
                    "rare_flag_image_count_lt_100": wp8_row["support"]["rare_flag"],
                    "gtsrb_disposition": wp8_row["gtsrb"]["disposition"],
                    "approval_boundary": wp8_row["approval_boundary"],
                },
                "d04": {
                    "in_scope": d04_in_scope,
                    "policy": RARE_POLICY,
                    "recommended_action": action,
                    "comparison_eligibility": comparison,
                    "recommendation_confidence": confidence,
                    "owner_status": "PENDING",
                    "automatic_semantic_merge": False,
                    "rationale": rationale,
                },
                "group_identity": {
                    "d02_status": "PENDING",
                    "effective_independent_support": "UNKNOWN_PENDING_D02",
                    "adjacent_or_proxy_sequence_is_group_truth": False,
                    "leakage_risk": "UNKNOWN_UNTIL_D02_GROUP_TRUTH_AND_GROUP_AWARE_SPLIT",
                },
                "governance": {
                    "d03_status": "PENDING",
                    "gate0": "BLOCKED",
                    "split_authorized": False,
                    "training_authorized": False,
                },
            }
        )
    return rows


def flatten_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    for row in rows:
        reps = row["representative_samples"]
        split = row["source_split_image_counts"]
        eligible = row["post_quarantine_eligibility"]
        wp8 = row["wp8_taxonomy"]
        d04 = row["d04"]
        group = row["group_identity"]
        flattened.append(
            {
                "class_id": row["class_id"],
                "dataset_code": row["dataset_code"],
                "name_en": row["name_en"],
                "name_vi": row["name_vi"],
                "image_count": row["support"]["image_count"],
                "box_count": row["support"]["box_count"],
                "source_train_image_count": split["train"],
                "source_test_image_count": split["test"],
                "source_unsplit_image_count": split["unsplit"],
                "post_quarantine_eligible_image_count": eligible["eligible_image_count"],
                "post_quarantine_eligible_box_count": eligible["eligible_box_count"],
                "g04_excluded_stems": ";".join(eligible["excluded_stems"]),
                "g04_effect": row["g04_effect"],
                "representative_stems": ";".join(rep["stem"] for rep in reps),
                "representative_image_sha256s": ";".join(rep["image_sha256"] for rep in reps),
                "representative_label_sha256s": ";".join(rep["label_sha256"] for rep in reps),
                "wp8_rare_flag_image_lt_100": str(wp8["rare_flag_image_count_lt_100"]).lower(),
                "wp8_taxonomy_status": wp8["reviewer_status"],
                "wp8_native_recommendation": wp8["native_recommendation"],
                "wp8_sign_policy": wp8["sign_policy"],
                "wp8_conflict_flag": str(wp8["conflict_flag"]).lower(),
                "d04_in_scope_box_lt_50": str(d04["in_scope"]).lower(),
                "d04_recommended_action": d04["recommended_action"],
                "d04_comparison_eligibility": d04["comparison_eligibility"],
                "d04_recommendation_confidence": d04["recommendation_confidence"],
                "d04_owner_status": d04["owner_status"],
                "d04_rationale": d04["rationale"],
                "d02_group_identity_status": group["d02_status"],
                "effective_independent_support": group["effective_independent_support"],
                "leakage_risk": group["leakage_risk"],
                "raw_split_usage": split["usage"],
                "gate0": row["governance"]["gate0"],
                "training_authorized": str(row["governance"]["training_authorized"]).lower(),
            }
        )
    return flattened


def matrix_payload(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rare_rows = [row for row in rows if row["d04"]["in_scope"]]
    return {
        "schema_version": 1,
        "package": "M0-WP11",
        "status": PACKAGE_STATUS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "class_count": 52,
        "d04_policy": RARE_POLICY,
        "d04_scope_count": 20,
        "d04_scope_class_ids": EXPECTED_RARE_IDS,
        "recommendation_counts": dict(sorted(Counter(row["d04"]["recommended_action"] for row in rows).items())),
        "rare_recommendation_counts": dict(sorted(Counter(row["d04"]["recommended_action"] for row in rare_rows).items())),
        "all_owner_status_pending": True,
        "effective_independent_support": "UNKNOWN_PENDING_D02",
        "d02_status": "PENDING",
        "d03_status": "PENDING",
        "d04_status": "PENDING_OWNER_DECISION",
        "gate0": "BLOCKED",
        "split_authorized": False,
        "training_authorized": False,
        "rows": rows,
    }


def rare_payload(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rare_rows = [row for row in rows if row["d04"]["in_scope"]]
    return {
        "schema_version": 1,
        "package": "M0-WP11",
        "status": PACKAGE_STATUS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "policy": RARE_POLICY,
        "rare_count": len(rare_rows),
        "rare_class_ids": [row["class_id"] for row in rare_rows],
        "extreme_class_ids": EXTREME_CLASS_IDS,
        "recommendation_counts": dict(sorted(Counter(row["d04"]["recommended_action"] for row in rare_rows).items())),
        "all_owner_status_pending": True,
        "effective_independent_support": "UNKNOWN_PENDING_D02",
        "automatic_semantic_merge_allowed": False,
        "gate0": "BLOCKED",
        "training_authorized": False,
        "rows": rare_rows,
    }


def parse_label(path: Path) -> list[tuple[int, float, float, float, float]]:
    parsed: list[tuple[int, float, float, float, float]] = []
    for line in path.read_text(encoding="ascii").splitlines():
        fields = line.split()
        if len(fields) != 5:
            raise ValueError(f"invalid YOLO label row in {path}")
        parsed.append((int(fields[0]), *(float(value) for value in fields[1:])))
    return parsed


def bbox_xyxy(record: tuple[int, float, float, float, float], width: int, height: int) -> list[float]:
    _class_id, x_center, y_center, box_width, box_height = record
    return [
        (x_center - box_width / 2) * width,
        (y_center - box_height / 2) * height,
        (x_center + box_width / 2) * width,
        (y_center + box_height / 2) * height,
    ]


def derive_extreme_records(repo_root: Path, raw_root: Path, contract: dict[str, Any]) -> list[dict[str, Any]]:
    inventory = {row["stem"]: row for row in read_csv(repo_root / "results/data_audit/DATASET01_052bc980a7206f8d/image_inventory.csv")}
    records: list[dict[str, Any]] = []
    for extreme in contract["extreme_classes"]:
        class_id = extreme["class_id"]
        if len(extreme["instances"]) != extreme["expected_image_count"] or extreme["expected_image_count"] != extreme["expected_box_count"]:
            raise ValueError(f"extreme class {class_id} contract count mismatch")
        page = f"{ASSET_DIR_RELATIVE_PATH}/class_{class_id:03d}.png"
        for slot, expected in enumerate(extreme["instances"], start=1):
            stem = expected["stem"]
            source = inventory.get(stem)
            if source is None:
                raise ValueError(f"missing extreme inventory stem {stem}")
            if source["image_sha256"] != expected["image_sha256"] or source["label_sha256"] != expected["label_sha256"]:
                raise ValueError(f"extreme inventory hash drift for stem {stem}")
            image_path = raw_root / source["image_path"]
            label_path = raw_root / source["label_path"]
            if sha256_file(image_path) != expected["image_sha256"] or sha256_file(label_path) != expected["label_sha256"]:
                raise ValueError(f"extreme raw source drift for stem {stem}")
            with Image.open(image_path) as image:
                if image.size != (960, 540) or image.format != "JPEG" or image.mode != "RGB":
                    raise ValueError(f"extreme image contract mismatch for stem {stem}")
            parsed = parse_label(label_path)
            occurrences = [(index + 1, row) for index, row in enumerate(parsed) if row[0] == class_id]
            if len(occurrences) != 1 or occurrences[0][0] != expected["label_line_number"]:
                raise ValueError(f"extreme label class/line drift for stem {stem}")
            _line_number, record = occurrences[0]
            normalized = list(record[1:])
            if any(abs(actual - wanted) > 1e-9 for actual, wanted in zip(normalized, expected["normalized_xywh"], strict=True)):
                raise ValueError(f"extreme normalized bbox drift for stem {stem}")
            pixels = bbox_xyxy(record, 960, 540)
            inside = pixels[0] >= 0 and pixels[1] >= 0 and pixels[2] <= 960 and pixels[3] <= 540
            if not inside:
                raise ValueError(f"extreme bbox unexpectedly exceeds image for stem {stem}")
            records.append(
                {
                    "class_id": class_id,
                    "dataset_code": extreme["dataset_code"],
                    "stem": stem,
                    "source_split_descriptive_only": source["split"],
                    "image_path": source["image_path"],
                    "image_sha256": source["image_sha256"],
                    "label_path": source["label_path"],
                    "label_sha256": source["label_sha256"],
                    "label_line_number": expected["label_line_number"],
                    "normalized_x_center": normalized[0],
                    "normalized_y_center": normalized[1],
                    "normalized_width": normalized[2],
                    "normalized_height": normalized[3],
                    "pixel_x_min": pixels[0],
                    "pixel_y_min": pixels[1],
                    "pixel_x_max": pixels[2],
                    "pixel_y_max": pixels[3],
                    "bbox_inside_image": True,
                    "effective_independent_support": "UNKNOWN_PENDING_D02",
                    "group_identity_status": "UNKNOWN_NOT_PROXY_GROUND_TRUTH",
                    "atlas_page": page,
                    "atlas_slot": slot,
                }
            )
    if Counter(record["class_id"] for record in records) != Counter({44: 3, 51: 5}):
        raise ValueError("extreme evidence roster/count mismatch")
    return records


def reviewer_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in (
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    ):
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def fit_image(image: Image.Image, target: tuple[int, int]) -> Image.Image:
    converted = image.convert("RGB")
    converted.thumbnail(target, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", target, "#e5e7eb")
    canvas.paste(converted, ((target[0] - converted.width) // 2, (target[1] - converted.height) // 2))
    return canvas


def draw_wrapped(draw: ImageDraw.ImageDraw, value: str, x: int, y: int, width: int, font: ImageFont.FreeTypeFont | ImageFont.ImageFont, fill: str = "#111827") -> int:
    words = value.split()
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
    line_height = draw.textbbox((0, 0), "Ag", font=font)[3] + 5
    for index, line in enumerate(lines):
        draw.text((x, y + index * line_height), line, font=font, fill=fill)
    return y + len(lines) * line_height


def render_extreme_page(raw_root: Path, class_row: dict[str, Any], records: list[dict[str, Any]]) -> tuple[bytes, dict[str, Any]]:
    row_height = 300
    width = 1600
    height = 92 + row_height * len(records) + 50
    canvas = Image.new("RGB", (width, height), "#f8fafc")
    draw = ImageDraw.Draw(canvas)
    title_font = reviewer_font(25)
    small_font = reviewer_font(14)
    draw.rectangle((0, 0, width, 78), fill="#111827")
    draw.text((24, 13), f"M0-WP11 D-04 extreme evidence | class {class_row['class_id']} {class_row['dataset_code']}", font=title_font, fill="white")
    draw.text((24, 47), "ALL INSTANCES | raw split descriptive only | independent support UNKNOWN_PENDING_D02 | owner PENDING", font=small_font, fill="#fde68a")
    audits: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        top = 92 + index * row_height
        draw.rectangle((8, top, width - 8, top + row_height - 8), fill="white" if index % 2 == 0 else "#f1f5f9", outline="#cbd5e1", width=2)
        image_path = raw_root / record["image_path"]
        with Image.open(image_path) as image:
            source = image.convert("RGB")
        full = source.resize((480, 270), Image.Resampling.LANCZOS)
        scale_x, scale_y = 0.5, 0.5
        box = [record["pixel_x_min"] * scale_x, record["pixel_y_min"] * scale_y, record["pixel_x_max"] * scale_x, record["pixel_y_max"] * scale_y]
        full_draw = ImageDraw.Draw(full)
        full_draw.rectangle(box, outline="#dc2626", width=5)
        canvas.paste(full, (20, top + 12))

        pad_x = max(35.0, (record["pixel_x_max"] - record["pixel_x_min"]) * 2.5)
        pad_y = max(35.0, (record["pixel_y_max"] - record["pixel_y_min"]) * 2.5)
        crop_box = (
            max(0, int(record["pixel_x_min"] - pad_x)),
            max(0, int(record["pixel_y_min"] - pad_y)),
            min(960, int(record["pixel_x_max"] + pad_x)),
            min(540, int(record["pixel_y_max"] + pad_y)),
        )
        crop = fit_image(source.crop(crop_box), (320, 220))
        canvas.paste(crop, (530, top + 35))
        draw.rectangle((530, top + 35, 850, top + 255), outline="#64748b", width=2)
        cursor = top + 22
        for text, color in (
            (f"stem {record['stem']} | line {record['label_line_number']} | source split {record['source_split_descriptive_only']} (DESCRIPTIVE ONLY)", "#111827"),
            (f"image sha256 {record['image_sha256']}", "#334155"),
            (f"label sha256 {record['label_sha256']}", "#334155"),
            (f"YOLO ({record['normalized_x_center']}, {record['normalized_y_center']}, {record['normalized_width']}, {record['normalized_height']})", "#111827"),
            (f"bbox px ({record['pixel_x_min']:.6f}, {record['pixel_y_min']:.6f}, {record['pixel_x_max']:.6f}, {record['pixel_y_max']:.6f})", "#111827"),
            ("group identity UNKNOWN | adjacency/proxy is NOT group truth", "#92400e"),
        ):
            cursor = draw_wrapped(draw, text, 880, cursor, 690, small_font, color) + 5
        if cursor > top + row_height - 15:
            raise RuntimeError(f"WP11 atlas text overflow for stem {record['stem']}")
        audits.append(
            {
                "class_id": record["class_id"],
                "stem": record["stem"],
                "slot": index + 1,
                "full_image_bounds": [20, top + 12, 500, top + 282],
                "crop_bounds": [530, top + 35, 850, top + 255],
                "text_bounds": [880, top + 22, 1570, cursor],
                "bbox_visible": True,
                "hashes_visible": True,
                "all_bounds_fit": True,
            }
        )
    footer_y = height - 42
    draw.rectangle((0, footer_y, width, height), fill="#111827")
    draw.text((20, footer_y + 11), EVIDENCE_BOUNDARY, font=small_font, fill="#fde68a")
    buffer = io.BytesIO()
    canvas.save(buffer, format="PNG", optimize=False)
    payload = buffer.getvalue()
    return payload, {
        "class_id": class_row["class_id"],
        "dataset_code": class_row["dataset_code"],
        "path": f"{ASSET_DIR_RELATIVE_PATH}/class_{class_row['class_id']:03d}.png",
        "width": width,
        "height": height,
        "row_count": len(records),
        "expected_all_instances": class_row["support"]["image_count"],
        "all_instances_rendered": len(records) == class_row["support"]["image_count"],
        "all_bounds_fit": True,
        "render_sha256": sha256_bytes(payload),
        "rows": audits,
    }


def atlas_payloads(raw_root: Path, rows: list[dict[str, Any]], extreme_records: list[dict[str, Any]]) -> tuple[dict[str, bytes], dict[str, Any]]:
    outputs: dict[str, bytes] = {}
    pages: list[dict[str, Any]] = []
    by_class = {row["class_id"]: row for row in rows}
    for class_id in EXTREME_CLASS_IDS:
        records = [record for record in extreme_records if record["class_id"] == class_id]
        payload, audit = render_extreme_page(raw_root, by_class[class_id], records)
        outputs[audit["path"]] = payload
        pages.append(audit)
    layout = {
        "schema_version": 1,
        "status": "PASS_ALL_EXTREME_INSTANCES_RENDERED_WITH_HASH_AND_BBOX_LINEAGE",
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "page_count": 2,
        "extreme_class_ids": EXTREME_CLASS_IDS,
        "extreme_instance_count": 8,
        "all_instances_rendered": all(page["all_instances_rendered"] for page in pages),
        "all_bounds_fit": all(page["all_bounds_fit"] for page in pages),
        "raw_split_descriptive_only": True,
        "effective_independent_support": "UNKNOWN_PENDING_D02",
        "pages": pages,
    }
    return outputs, layout


def render_report(rows: list[dict[str, Any]], extreme_records: list[dict[str, Any]]) -> str:
    rare = [row for row in rows if row["d04"]["in_scope"]]
    table = "\n".join(
        f"| {row['class_id']} | {row['dataset_code']} | {row['support']['image_count']} | {row['support']['box_count']} | {row['post_quarantine_eligibility']['eligible_image_count']} | {row['post_quarantine_eligibility']['eligible_box_count']} | {row['d04']['recommended_action']} | {row['d04']['owner_status']} |"
        for row in rare
    )
    extreme_lines = "\n".join(
        f"- Class {class_id}: {sum(record['class_id'] == class_id for record in extreme_records)} complete instances rendered in `{ASSET_DIR_RELATIVE_PATH}/class_{class_id:03d}.png`."
        for class_id in EXTREME_CLASS_IDS
    )
    counts = Counter(row["d04"]["recommended_action"] for row in rows)
    return f"""# M0-WP11 D-04 rare-class decision-support report

Status: `{PACKAGE_STATUS}`  
Boundary: `{EVIDENCE_BOUNDARY}`

## Decision boundary

This package uses the current D-04 scope `box_count < 50`, which contains exactly 20 classes. It is
different from the WP8 analysis flag `image_count < 100` (29 classes). Neither rule authorizes a
semantic merge. All owner decisions remain `PENDING`; D-03 remains `PENDING`; Gate 0 remains
`BLOCKED`; `training_authorized=false`.

Raw train/test counts are descriptive source metadata only. They are not independent evaluation
evidence. Effective independent support is `UNKNOWN_PENDING_D02` because physical-sign/scene group
truth and a group-aware split do not yet exist. Adjacent or proxy sequences are not group truth.

## Recommendation rule

- `box_count <= 20`: `COLLECT_MORE` and quarantine the class from model-comparison claims pending
  independent-group data.
- `21 <= box_count < 50`: `OWNER_REVIEW_REQUIRED` before any model-comparison inclusion.
- Outside D-04 scope: `KEEP_NATIVE_PENDING_D03`.
- No automatic merge, relabel, split, training or taxonomy approval is permitted.

Across all 52 rows: {counts['COLLECT_MORE']} `COLLECT_MORE`, {counts['OWNER_REVIEW_REQUIRED']}
`OWNER_REVIEW_REQUIRED`, and {counts['KEEP_NATIVE_PENDING_D03']} `KEEP_NATIVE_PENDING_D03`.

## D-04 decision-focused subset

| Class | Code | Images | Boxes | Eligible images | Eligible boxes | Recommendation | Owner |
| ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
{table}

## Extreme-support evidence

{extreme_lines}

Class 44 (`W.233`) has exactly 3 images/3 boxes; class 51 (`W.246c`) has exactly 5 images/5 boxes.
Every available instance is hash-bound, its exact label line and pixel bbox are recorded, and every
instance was rendered in the two-page atlas. Because D-02 is unresolved, these counts do not imply
3 or 5 independent physical signs.

## G0.4 quarantine effect

The WP10 registry excludes entire stem `0248` from split/training eligibility. Class 49 changes from
120 images/221 boxes to 119 eligible images/219 eligible boxes. The WP9 derived clip is not counted
as a training sample. Class 49 and its taxonomy remain present and `UNAPPROVED`; only sample 0248 is
quarantined. No other class count changes.

## Owner action

Review the 20 D-04 rows independently. `COLLECT_MORE` and `OWNER_REVIEW_REQUIRED` are PM proposals,
not approvals. D-04 remains `PENDING_OWNER_DECISION`; WP11 must pass QA before presentation to the
owner. This package does not approve D-04, D-03, D-02, a final split, training, or experiments.
"""


def expected_artifacts(repo_root: Path, raw_root: Path) -> dict[str, bytes]:
    verify_pinned_sources(repo_root, raw_root)
    contract = validate_contract(repo_root)
    rows = derive_matrix(repo_root)
    extreme_records = derive_extreme_records(repo_root, raw_root, contract)
    matrix = matrix_payload(rows)
    rare = rare_payload(rows)
    atlas, layout = atlas_payloads(raw_root, rows, extreme_records)
    artifacts = {
        MATRIX_JSON_RELATIVE_PATH: json_bytes(matrix),
        MATRIX_CSV_RELATIVE_PATH: csv_bytes(flatten_rows(rows), CSV_FIELDS),
        RARE_JSON_RELATIVE_PATH: json_bytes(rare),
        RARE_CSV_RELATIVE_PATH: csv_bytes(flatten_rows(rare["rows"]), CSV_FIELDS),
        EXTREME_CSV_RELATIVE_PATH: csv_bytes(extreme_records, EXTREME_FIELDS),
        LAYOUT_RELATIVE_PATH: json_bytes(layout),
        REPORT_RELATIVE_PATH: render_report(rows, extreme_records).encode("utf-8"),
    }
    artifacts.update(atlas)
    return artifacts


def build_manifest(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    sources = verify_pinned_sources(repo_root, raw_root)
    artifacts = [
        {"id": item_id, "root": "repo", "path": relative, "sha256": sha256_file(path), "size": path.stat().st_size}
        for item_id, relative, path in artifact_contract(repo_root)
    ]
    return {
        "schema_version": 1,
        "package": "M0-WP11",
        "status": PACKAGE_STATUS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "d04_policy": RARE_POLICY,
        "class_count": 52,
        "rare_class_count": 20,
        "extreme_class_ids": EXTREME_CLASS_IDS,
        "extreme_instance_count": 8,
        "atlas_page_count": 2,
        "all_owner_status_pending": True,
        "effective_independent_support": "UNKNOWN_PENDING_D02",
        "automatic_semantic_merge_allowed": False,
        "wp10_g04_quarantine_applied": True,
        "d02_status": "PENDING",
        "d03_status": "PENDING",
        "d04_status": "PENDING_OWNER_DECISION",
        "gate0": "BLOCKED",
        "split_authorized": False,
        "training_authorized": False,
        "manifest_path": MANIFEST_RELATIVE_PATH,
        "manifest_self_in_artifact_count": False,
        "artifact_count_semantics": "EXCLUDES_MANIFEST_FILE",
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
    if len({record[0] for record in roster}) != len(roster):
        errors.append(f"duplicate {name} IDs")
    if len({record[1:] for record in roster}) != len(roster):
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
        "schema_version", "package", "status", "evidence_boundary", "d04_policy", "class_count",
        "rare_class_count", "extreme_class_ids", "extreme_instance_count", "atlas_page_count",
        "all_owner_status_pending", "effective_independent_support", "automatic_semantic_merge_allowed",
        "wp10_g04_quarantine_applied", "d02_status", "d03_status", "d04_status", "gate0",
        "split_authorized", "training_authorized", "manifest_path", "manifest_self_in_artifact_count",
        "artifact_count_semantics", "source_count", "artifact_count", "total_artifact_bytes", "sources", "artifacts",
    }
    if set(payload) != expected_top:
        errors.append("manifest top-level fields differ from WP11 schema")
    constants = {
        "schema_version": 1, "package": "M0-WP11", "status": PACKAGE_STATUS,
        "evidence_boundary": EVIDENCE_BOUNDARY, "d04_policy": RARE_POLICY, "class_count": 52,
        "rare_class_count": 20, "extreme_class_ids": EXTREME_CLASS_IDS, "extreme_instance_count": 8,
        "atlas_page_count": 2, "all_owner_status_pending": True,
        "effective_independent_support": "UNKNOWN_PENDING_D02",
        "automatic_semantic_merge_allowed": False, "wp10_g04_quarantine_applied": True,
        "d02_status": "PENDING", "d03_status": "PENDING", "d04_status": "PENDING_OWNER_DECISION",
        "gate0": "BLOCKED", "split_authorized": False, "training_authorized": False,
        "manifest_path": MANIFEST_RELATIVE_PATH, "manifest_self_in_artifact_count": False,
        "artifact_count_semantics": "EXCLUDES_MANIFEST_FILE",
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
            if collection == "sources" and EXPECTED_PINNED_HASHES.get(str(record.get("id"))) is not None:
                if record.get("sha256") != EXPECTED_PINNED_HASHES[str(record["id"])]:
                    errors.append(f"pinned source hash mismatch: {record['id']}")
    if not errors:
        try:
            expected_payloads = expected_artifacts(repo_root, raw_root)
            for _item_id, relative, path in artifact_contract(repo_root):
                if path.read_bytes() != expected_payloads[relative]:
                    raise ValueError(f"semantic artifact mismatch: {relative}")
            layout = json.loads((repo_root / LAYOUT_RELATIVE_PATH).read_text(encoding="utf-8"))
            if layout.get("page_count") != 2 or layout.get("extreme_instance_count") != 8 or not layout.get("all_instances_rendered"):
                raise ValueError("WP11 visual layout completeness mismatch")
            for page in layout["pages"]:
                page_path = repo_root / page["path"]
                with Image.open(page_path) as image:
                    if image.format != "PNG" or image.mode != "RGB" or image.size != (page["width"], page["height"]):
                        raise ValueError(f"WP11 atlas image contract mismatch: {page['path']}")
                    image.verify()
        except (FileNotFoundError, json.JSONDecodeError, KeyError, OSError, TypeError, ValueError) as exc:
            errors.append(f"semantic verification failed: {exc}")
    return {
        "valid": not errors,
        "errors": errors,
        "source_count": len(sources),
        "artifact_count": len(artifacts),
        "status": payload.get("status"),
        "class_count": payload.get("class_count"),
        "rare_class_count": payload.get("rare_class_count"),
        "extreme_instance_count": payload.get("extreme_instance_count"),
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
        raise RuntimeError(f"WP11 package verification failed: {result['errors']}")
    rows = json.loads((repo_root / MATRIX_JSON_RELATIVE_PATH).read_text(encoding="utf-8"))["rows"]
    return {
        "status": PACKAGE_STATUS,
        "class_count": 52,
        "rare_class_count": 20,
        "extreme_instance_count": 8,
        "atlas_page_count": 2,
        "recommendation_counts": dict(sorted(Counter(row["d04"]["recommended_action"] for row in rows).items())),
        "source_count": manifest["source_count"],
        "artifact_count": manifest["artifact_count"],
        "manifest_sha256": sha256_file(repo_root / MANIFEST_RELATIVE_PATH),
        "d04_status": "PENDING_OWNER_DECISION",
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
        exit_code = 0
    else:
        manifest = args.manifest if args.manifest.is_absolute() else repo_root / args.manifest
        result = verify_manifest(manifest, repo_root, raw_root)
        exit_code = 0 if result["valid"] else 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
