# ruff: noqa: E501
from __future__ import annotations

import csv
import importlib.util
import json
import os
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pytest
from PIL import Image

REPO_ROOT = Path(__file__).parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/build_wp8_taxonomy_recommendation.py"
SPEC = importlib.util.spec_from_file_location("build_wp8_taxonomy_recommendation", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
wp8 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp8
SPEC.loader.exec_module(wp8)

MANIFEST_PATH = REPO_ROOT / wp8.MANIFEST_RELATIVE_PATH


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def copy_or_link(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.stat().st_size > 1024 * 1024:
        try:
            os.link(source, target)
            return
        except OSError:
            pass
    shutil.copy2(source, target)


def stage_package(tmp_path: Path) -> Path:
    manifest = read_json(MANIFEST_PATH)
    for record in manifest["sources"]:
        copy_or_link(REPO_ROOT / record["path"], tmp_path / record["path"])
    for record in manifest["artifacts"]:
        source = REPO_ROOT / record["path"]
        target = tmp_path / record["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    staged = tmp_path / wp8.MANIFEST_RELATIVE_PATH
    staged.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(MANIFEST_PATH, staged)
    return staged


def refresh_manifest_records(staged_manifest: Path) -> None:
    root = staged_manifest.parents[3]
    payload = read_json(staged_manifest)
    for collection in ("sources", "artifacts"):
        for record in payload[collection]:
            path = root / record["path"]
            if path.is_file():
                record["sha256"] = wp8.sha256_file(path)
                record["size"] = path.stat().st_size
    payload["total_artifact_bytes"] = sum(record["size"] for record in payload["artifacts"])
    wp8.write_json(staged_manifest, payload)


def verify_payload(tmp_path: Path, payload: Any, name: str) -> dict[str, Any]:
    path = tmp_path / name
    wp8.write_json(path, payload)
    return wp8.verify_manifest(path, REPO_ROOT)


def test_official_package_verifies_with_exact_rosters() -> None:
    result = wp8.verify_manifest(MANIFEST_PATH, REPO_ROOT)
    assert result == {
        "valid": True,
        "errors": [],
        "source_count": 21,
        "artifact_count": 19,
        "status": wp8.PACKAGE_STATUS,
    }
    manifest = read_json(MANIFEST_PATH)
    assert manifest["source_count"] == len(manifest["sources"]) == 21
    assert manifest["artifact_count"] == len(manifest["artifacts"]) == 19
    assert manifest["manifest_self_in_artifact_count"] is False
    assert manifest["artifact_count_semantics"] == "EXCLUDES_MANIFEST_FILE"
    assert wp8.MANIFEST_RELATIVE_PATH not in {row["path"] for row in manifest["artifacts"]}


def test_matrix_has_exact_52_unapproved_rows_and_governance_boundary() -> None:
    payload = read_json(REPO_ROOT / wp8.MATRIX_JSON_RELATIVE_PATH)
    rows = payload["rows"]
    assert [row["class_id"] for row in rows] == list(range(52))
    assert payload["class_count"] == 52
    assert payload["all_rows_unapproved"] is True
    assert payload["d03_status"] == "PENDING"
    assert payload["gate0"] == "BLOCKED"
    assert payload["training_authorized"] is False
    assert all(row["reviewer_status"] == "UNAPPROVED" for row in rows)
    assert all(row["approval_boundary"] == wp8.EVIDENCE_BOUNDARY for row in rows)


def test_closed_enum_counts_and_complete_reviewer_actions() -> None:
    rows = read_json(REPO_ROOT / wp8.MATRIX_JSON_RELATIVE_PATH)["rows"]
    assert dict(sorted(Counter(row["native_recommendation"] for row in rows).items())) == wp8.EXPECTED_NATIVE_COUNTS
    assert dict(sorted(Counter(row["gtsrb"]["disposition"] for row in rows).items())) == wp8.EXPECTED_GTSRB_COUNTS
    assert dict(sorted(Counter(row["sign_policy"] for row in rows).items())) == wp8.EXPECTED_POLICY_COUNTS
    assert dict(sorted(Counter(row["unknown_policy"] for row in rows).items())) == wp8.EXPECTED_UNKNOWN_COUNTS
    assert all(row["reviewer_action"] and row["recommendation_rationale"] for row in rows)


def test_critical_conflict_rows_match_independent_expectations() -> None:
    rows = read_json(REPO_ROOT / wp8.MATRIX_JSON_RELATIVE_PATH)["rows"]
    assert [row["class_id"] for row in rows if row["conflict_flag"]] == wp8.EXPECTED_CONFLICT_IDS
    for class_id, expected in wp8.EXPECTED_CRITICAL.items():
        row = rows[class_id]
        actual = (
            row["wp4_evidence"]["match_status"],
            row["wp4_evidence"]["official_code_candidate"],
            row["native_recommendation"],
            row["recommended_code_if_approved"],
            row["gtsrb"]["disposition"],
            row["sign_policy"],
        )
        assert actual == expected


def test_required_semantic_boundaries_are_explicit() -> None:
    rows = read_json(REPO_ROOT / wp8.MATRIX_JSON_RELATIVE_PATH)["rows"]
    assert rows[23]["recommended_code_if_approved"] == ""
    assert rows[23]["wp4_evidence"]["official_code_candidate"] == "P.111a-d"
    assert rows[23]["sign_policy"] == "VARIANT_SELECTION_REVIEW"
    assert all(rows[class_id]["sign_policy"] == "SUPPLEMENTARY_SIGN_REVIEW" for class_id in (25, 28, 30))
    assert all(rows[class_id]["recommended_code_if_approved"] == "" for class_id in (25, 28, 30))
    assert rows[34]["dataset_code"] == "B.8a"
    assert rows[34]["recommended_code_if_approved"] == "P.108a"
    assert rows[47]["dataset_code"] == "P.124b1"
    assert rows[47]["recommended_code_if_approved"] == "P.124b"
    assert rows[51]["wp4_evidence"]["match_status"] == "EXACT"
    assert rows[51]["gtsrb"]["disposition"] == "PARTIAL_ANALYSIS_ONLY"


def test_wp8_r1_qcvn_semantic_repairs_are_explicit() -> None:
    rows = read_json(REPO_ROOT / wp8.MATRIX_JSON_RELATIVE_PATH)["rows"]

    class_14 = rows[14]
    assert class_14["dataset_code"] == "P.106a*Xe tải"
    assert class_14["wp4_evidence"]["official_code_candidate"] == "P.106a"
    assert class_14["sign_policy"] == "ATOMIC_SIGN"
    assert class_14["gtsrb"]["disposition"] == "PARTIAL_ANALYSIS_ONLY"
    assert class_14["recommended_name_en_if_approved"] == "No Trucks"
    assert "P.106b" in class_14["recommendation_rationale"]
    assert "with no weight value" in class_14["recommendation_rationale"]
    assert "vehicles-over-3.5t analysis-only" in class_14["reviewer_action"]
    assert [rep["stem"] for rep in class_14["representatives"]] == ["3136", "3153", "3159"]

    expected_name_repairs = {
        6: ("W.201a", "Dangerous Curve to the Left", "Danger zone on the left"),
        42: ("R.301e", "Mandatory Left Turn", "Left Turn"),
        50: ("W.201b", "Dangerous Curve to the Right", "Danger zone on the right"),
    }
    for class_id, (code, corrected_name, previous_name) in expected_name_repairs.items():
        row = rows[class_id]
        assert row["native_recommendation"] == "CORRECT_CODE_OR_NAME_PROPOSAL"
        assert row["recommended_code_if_approved"] == code
        assert row["recommended_name_en_if_approved"] == corrected_name
        assert row["sign_policy"] == "ATOMIC_SIGN"
        assert row["gtsrb"]["disposition"] == "DIRECT_ANALYSIS_ONLY"
        assert previous_name in row["reviewer_action"]
        assert corrected_name in row["reviewer_action"]


def test_camera_not_found_scope_is_preserved_without_asserted_qcvn_code() -> None:
    row = read_json(REPO_ROOT / wp8.MATRIX_JSON_RELATIVE_PATH)["rows"][31]
    scope = row["wp4_evidence"]["negative_search_scope"]
    assert row["dataset_code"] == "Camera"
    assert row["native_recommendation"] == "OUT_OF_SCOPE_PROPOSAL"
    assert row["wp4_evidence"]["official_code_candidate"] == ""
    assert row["recommended_code_if_approved"] == ""
    assert scope["pages"] == "80-154"
    assert scope["queries"] == ["camera", "giám sát", "surveillance"]
    assert scope["query_hits"] == []


def test_each_row_has_three_hash_bound_representatives_and_bbox_refs() -> None:
    rows = read_json(REPO_ROOT / wp8.MATRIX_JSON_RELATIVE_PATH)["rows"]
    assert sum(len(row["representatives"]) for row in rows) == 156
    for row in rows:
        assert len(row["representatives"]) == 3
        assert len({rep["stem"] for rep in row["representatives"]}) == 3
        for rep in row["representatives"]:
            assert len(rep["image_sha256"]) == 64
            assert len(rep["label_sha256"]) == 64
            assert rep["label_line_number"] >= 1
            assert len(rep["source_bbox_xyxy"]) == 4


def test_rarity_is_support_only_and_never_changes_semantics() -> None:
    rows = read_json(REPO_ROOT / wp8.MATRIX_JSON_RELATIVE_PATH)["rows"]
    rare_ids = [row["class_id"] for row in rows if row["support"]["rare_flag"]]
    assert len(rare_ids) == 29
    assert rare_ids == [row["class_id"] for row in rows if row["support"]["image_count"] < 100]
    assert all("never a semantic merge rule" in row["support"]["rare_definition"] for row in rows)
    assert rows[44]["support"]["image_count"] == 3
    assert rows[44]["native_recommendation"] == "KEEP_CURRENT"


def test_atlas_has_13_deterministic_pages_and_52_complete_panels() -> None:
    layout = read_json(REPO_ROOT / wp8.LAYOUT_RELATIVE_PATH)
    assert layout["page_count"] == 13
    assert layout["class_count"] == 52
    assert layout["all_rows_unapproved"] is True
    assert layout["all_text_complete"] is True
    assert layout["all_bounds_fit"] is True
    rows = [row for page in layout["pages"] for row in page["rows"]]
    assert [row["class_id"] for row in rows] == list(range(52))
    assert all(row["all_bounds_fit"] and row["reviewer_status"] == "UNAPPROVED" for row in rows)
    for page in layout["pages"]:
        path = REPO_ROOT / page["path"]
        assert page["render_sha256"] == wp8.sha256_file(path)
        with Image.open(path) as image:
            assert image.size == (1900, 1818)
            assert image.format == "PNG"
            image.verify()


def test_report_preserves_proposal_only_gate() -> None:
    report = (REPO_ROOT / wp8.REPORT_RELATIVE_PATH).read_text(encoding="utf-8")
    assert "Every row remains `UNAPPROVED`" in report
    assert "D-03: `PENDING`" in report
    assert "Gate 0: `BLOCKED`" in report
    assert "Relabel, split, and training: not authorized" in report
    assert "S.505a means supplementary `Loại xe`" in report
    assert "P.124b1 is unsupported" in report
    assert "class 31 has no asserted QCVN code" in report
    assert "class 51 is an exact native W.246c row" in report
    assert "## WP8-R1 QA repair clarifications" in report
    assert "QCVN section B.6 assigns the fixed truck prohibition to P.106a" in report
    assert "Dangerous Curve to the Left" in report
    assert "Mandatory Left Turn" in report
    assert "Dangerous Curve to the Right" in report


def test_wp1_through_wp7_model_and_control_hashes_are_preserved() -> None:
    for item_id, path, pinned_hash in wp8.source_contract(REPO_ROOT):
        if pinned_hash is not None:
            assert wp8.sha256_file(path) == pinned_hash, item_id
    proof = read_json(
        REPO_ROOT
        / "results/data_audit/DATASET01_052bc980a7206f8d/source_preservation_proof.json"
    )
    assert proof["unchanged"] is True


def test_no_approval_relabel_split_or_training_fields_are_created() -> None:
    rows = read_json(REPO_ROOT / wp8.MATRIX_JSON_RELATIVE_PATH)["rows"]
    forbidden = {"final_class_id", "approved_code", "assigned_split", "training_target"}
    assert all(not forbidden & set(row) for row in rows)


@pytest.mark.parametrize("mutation", ["remove", "duplicate", "reorder", "extra"])
def test_manifest_rejects_artifact_roster_mutations(tmp_path: Path, mutation: str) -> None:
    payload = read_json(MANIFEST_PATH)
    if mutation == "remove":
        payload["artifacts"].pop()
    elif mutation == "duplicate":
        payload["artifacts"].append(dict(payload["artifacts"][0]))
    elif mutation == "reorder":
        payload["artifacts"][0], payload["artifacts"][1] = payload["artifacts"][1], payload["artifacts"][0]
    else:
        payload["artifacts"].append(
            {
                "id": "unexpected",
                "path": "PROJECT_MEMORY.md",
                "sha256": wp8.sha256_file(REPO_ROOT / "PROJECT_MEMORY.md"),
                "size": (REPO_ROOT / "PROJECT_MEMORY.md").stat().st_size,
            }
        )
    payload["artifact_count"] = len(payload["artifacts"])
    payload["total_artifact_bytes"] = sum(row["size"] for row in payload["artifacts"])
    result = verify_payload(tmp_path, payload, f"{mutation}.json")
    assert result["valid"] is False
    assert any("artifacts" in error for error in result["errors"])


@pytest.mark.parametrize("field", ["source_count", "artifact_count", "total_artifact_bytes"])
def test_manifest_rejects_forged_counts(tmp_path: Path, field: str) -> None:
    payload = read_json(MANIFEST_PATH)
    payload[field] += 1
    result = verify_payload(tmp_path, payload, f"forged_{field}.json")
    assert result["valid"] is False
    assert any(field in error for error in result["errors"])


@pytest.mark.parametrize(
    "attack",
    ["json_gtsrb", "csv_code", "summary_conflict", "report_gate", "layout_digest", "atlas_pixel"],
)
def test_rehashed_semantic_artifact_tamper_is_rejected(tmp_path: Path, attack: str) -> None:
    staged = stage_package(tmp_path)
    if attack == "json_gtsrb":
        path = tmp_path / wp8.MATRIX_JSON_RELATIVE_PATH
        payload = read_json(path)
        payload["rows"][51]["gtsrb"]["disposition"] = "DIRECT_ANALYSIS_ONLY"
        wp8.write_json(path, payload)
    elif attack == "csv_code":
        path = tmp_path / wp8.MATRIX_CSV_RELATIVE_PATH
        rows = read_csv(path)
        rows[34]["recommended_code_if_approved"] = "B.8a"
        wp8.write_csv(path, rows, wp8.CSV_FIELDS)
    elif attack == "summary_conflict":
        path = tmp_path / wp8.SUMMARY_RELATIVE_PATH
        payload = read_json(path)
        payload["conflict_class_ids"].remove(23)
        wp8.write_json(path, payload)
    elif attack == "report_gate":
        path = tmp_path / wp8.REPORT_RELATIVE_PATH
        path.write_text(path.read_text(encoding="utf-8").replace("D-03: `PENDING`", "D-03: `APPROVED`"), encoding="utf-8")
    elif attack == "layout_digest":
        path = tmp_path / wp8.LAYOUT_RELATIVE_PATH
        payload = read_json(path)
        payload["pages"][0]["rows"][0]["panel_text_sha256"] = "0" * 64
        wp8.write_json(path, payload)
    else:
        path = tmp_path / wp8.ASSETS_RELATIVE_PATH / "page_001.png"
        with Image.open(path) as image:
            modified = image.convert("RGB")
        modified.putpixel((1890, 1800), (255, 0, 255))
        modified.save(path, format="PNG", optimize=False)
    refresh_manifest_records(staged)
    result = wp8.verify_manifest(staged, tmp_path)
    assert result["valid"] is False
    assert any("semantic verification failed" in error for error in result["errors"])


def test_rehashed_contract_conflict_change_is_rejected_by_pinned_hash(tmp_path: Path) -> None:
    staged = stage_package(tmp_path)
    path = tmp_path / wp8.CONTRACT_RELATIVE_PATH
    payload = read_json(path)
    payload["rows"][23]["recommended_code_if_approved"] = "P.111"
    wp8.write_json(path, payload)
    refresh_manifest_records(staged)
    result = wp8.verify_manifest(staged, tmp_path)
    assert result["valid"] is False
    assert any("pinned source hash mismatch: recommendation_contract" in error for error in result["errors"])


@pytest.mark.parametrize(
    ("class_id", "field", "old_value"),
    [
        (6, "native_recommendation", "KEEP_CURRENT"),
        (14, "sign_policy", "PARAMETERIZED_SIGN_REVIEW"),
        (42, "native_recommendation", "KEEP_CURRENT"),
        (50, "native_recommendation", "KEEP_CURRENT"),
    ],
)
def test_rehashed_wp8_r1_contract_semantic_rollback_is_rejected(
    tmp_path: Path,
    class_id: int,
    field: str,
    old_value: str,
) -> None:
    staged = stage_package(tmp_path)
    path = tmp_path / wp8.CONTRACT_RELATIVE_PATH
    payload = read_json(path)
    payload["rows"][class_id][field] = old_value
    wp8.write_json(path, payload)
    refresh_manifest_records(staged)
    result = wp8.verify_manifest(staged, tmp_path)
    assert result["valid"] is False
    assert any("pinned source hash mismatch: recommendation_contract" in error for error in result["errors"])


def test_path_escape_and_symlink_escape_are_rejected(tmp_path: Path) -> None:
    payload = read_json(MANIFEST_PATH)
    payload["sources"][0]["path"] = "../outside.json"
    result = verify_payload(tmp_path, payload, "path_escape.json")
    assert result["valid"] is False
    assert any("unsafe relative path" in error for error in result["errors"])

    stage_root = tmp_path / "stage"
    staged = stage_package(stage_root)
    matrix = stage_root / wp8.MATRIX_CSV_RELATIVE_PATH
    outside = tmp_path / "outside.csv"
    shutil.copy2(matrix, outside)
    matrix.unlink()
    matrix.symlink_to(outside)
    result = wp8.verify_manifest(staged, stage_root)
    assert result["valid"] is False
    assert any("symlink path is not allowed" in error for error in result["errors"])
