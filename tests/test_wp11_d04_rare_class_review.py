# ruff: noqa: E501
from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pytest
from PIL import Image

REPO_ROOT = Path(__file__).parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/build_wp11_d04_rare_class_review.py"
SPEC = importlib.util.spec_from_file_location("build_wp11_d04_rare_class_review", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
wp11 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp11
SPEC.loader.exec_module(wp11)

RAW_ROOT = wp11.default_raw_root(REPO_ROOT)
MANIFEST_PATH = REPO_ROOT / wp11.MANIFEST_RELATIVE_PATH


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def copy_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def stage_package(tmp_path: Path) -> tuple[Path, Path, Path]:
    stage_repo = tmp_path / "repo"
    stage_raw = tmp_path / "raw"
    manifest = read_json(MANIFEST_PATH)
    roots = {"repo": REPO_ROOT, "raw": RAW_ROOT}
    targets = {"repo": stage_repo, "raw": stage_raw}
    for record in manifest["sources"]:
        copy_file(roots[record["root"]] / record["path"], targets[record["root"]] / record["path"])
    for record in manifest["artifacts"]:
        copy_file(REPO_ROOT / record["path"], stage_repo / record["path"])
    staged_manifest = stage_repo / wp11.MANIFEST_RELATIVE_PATH
    copy_file(MANIFEST_PATH, staged_manifest)
    return stage_repo, stage_raw, staged_manifest


def refresh_manifest(staged_manifest: Path, stage_repo: Path, stage_raw: Path) -> None:
    payload = read_json(staged_manifest)
    roots = {"repo": stage_repo, "raw": stage_raw}
    for collection in ("sources", "artifacts"):
        for record in payload[collection]:
            path = roots[record["root"]] / record["path"]
            if path.is_file():
                record["sha256"] = wp11.sha256_file(path)
                record["size"] = path.stat().st_size
    payload["total_artifact_bytes"] = sum(record["size"] for record in payload["artifacts"])
    staged_manifest.write_bytes(wp11.json_bytes(payload))


def write_manifest(tmp_path: Path, payload: dict[str, Any]) -> Path:
    path = tmp_path / "manifest.json"
    path.write_bytes(wp11.json_bytes(payload))
    return path


def test_official_package_verifies_with_exact_rosters() -> None:
    result = wp11.verify_manifest(MANIFEST_PATH, REPO_ROOT, RAW_ROOT)
    assert result == {
        "valid": True,
        "errors": [],
        "source_count": 28,
        "artifact_count": 9,
        "status": wp11.PACKAGE_STATUS,
        "class_count": 52,
        "rare_class_count": 20,
        "extreme_instance_count": 8,
    }
    manifest = read_json(MANIFEST_PATH)
    assert manifest["source_count"] == len(manifest["sources"]) == 28
    assert manifest["artifact_count"] == len(manifest["artifacts"]) == 9
    assert manifest["manifest_self_in_artifact_count"] is False
    assert manifest["artifact_count_semantics"] == "EXCLUDES_MANIFEST_FILE"
    assert wp11.MANIFEST_RELATIVE_PATH not in {record["path"] for record in manifest["artifacts"]}


def test_matrix_has_exact_52_rows_and_current_d04_scope() -> None:
    matrix = read_json(REPO_ROOT / wp11.MATRIX_JSON_RELATIVE_PATH)
    assert matrix["class_count"] == 52
    assert [row["class_id"] for row in matrix["rows"]] == list(range(52))
    assert matrix["d04_policy"] == "box_count < 50"
    assert matrix["d04_scope_count"] == 20
    assert matrix["d04_scope_class_ids"] == wp11.EXPECTED_RARE_IDS
    assert [row["class_id"] for row in matrix["rows"] if row["d04"]["in_scope"]] == wp11.EXPECTED_RARE_IDS


def test_wp8_analysis_rare_flag_remains_distinct_from_d04_scope() -> None:
    rows = read_json(REPO_ROOT / wp11.MATRIX_JSON_RELATIVE_PATH)["rows"]
    wp8_rare = [row["class_id"] for row in rows if row["wp8_taxonomy"]["rare_flag_image_count_lt_100"]]
    d04_rare = [row["class_id"] for row in rows if row["d04"]["in_scope"]]
    assert len(wp8_rare) == 29
    assert len(d04_rare) == 20
    assert wp8_rare != d04_rare
    assert 14 in wp8_rare and 14 not in d04_rare


def test_recommendation_counts_and_rules_are_exact() -> None:
    matrix = read_json(REPO_ROOT / wp11.MATRIX_JSON_RELATIVE_PATH)
    rows = matrix["rows"]
    assert matrix["recommendation_counts"] == {
        "COLLECT_MORE": 5,
        "KEEP_NATIVE_PENDING_D03": 32,
        "OWNER_REVIEW_REQUIRED": 15,
    }
    assert matrix["rare_recommendation_counts"] == {"COLLECT_MORE": 5, "OWNER_REVIEW_REQUIRED": 15}
    assert [row["class_id"] for row in rows if row["d04"]["recommended_action"] == "COLLECT_MORE"] == [21, 33, 44, 47, 51]
    assert all(row["d04"]["recommended_action"] == "OWNER_REVIEW_REQUIRED" for row in rows if 20 < row["support"]["box_count"] < 50)
    assert all(row["d04"]["recommended_action"] == "KEEP_NATIVE_PENDING_D03" for row in rows if row["support"]["box_count"] >= 50)


def test_all_rows_preserve_governance_and_unknown_independent_support() -> None:
    rows = read_json(REPO_ROOT / wp11.MATRIX_JSON_RELATIVE_PATH)["rows"]
    assert all(row["d04"]["owner_status"] == "PENDING" for row in rows)
    assert all(row["d04"]["automatic_semantic_merge"] is False for row in rows)
    assert all(row["wp8_taxonomy"]["reviewer_status"] == "UNAPPROVED" for row in rows)
    assert all(row["group_identity"]["d02_status"] == "PENDING" for row in rows)
    assert all(row["group_identity"]["effective_independent_support"] == "UNKNOWN_PENDING_D02" for row in rows)
    assert all(row["group_identity"]["adjacent_or_proxy_sequence_is_group_truth"] is False for row in rows)
    assert all(row["source_split_image_counts"]["usage"] == "DESCRIPTIVE_ONLY_NOT_INDEPENDENT_EVIDENCE" for row in rows)
    assert all(row["governance"] == {"d03_status": "PENDING", "gate0": "BLOCKED", "split_authorized": False, "training_authorized": False} for row in rows)


def test_g04_effect_excludes_only_stem_0248_from_class49_eligibility() -> None:
    rows = read_json(REPO_ROOT / wp11.MATRIX_JSON_RELATIVE_PATH)["rows"]
    class_49 = rows[49]
    assert class_49["support"] == {"image_count": 120, "box_count": 221}
    assert class_49["post_quarantine_eligibility"] == {
        "derived_clip_counted_as_training_sample": False,
        "eligible_box_count": 219,
        "eligible_image_count": 119,
        "eligible_train_image_count_descriptive_only": 94,
        "excluded_stems": ["0248"],
    }
    assert class_49["g04_effect"] == "EXCLUDES_ENTIRE_STEM_0248_TWO_CLASS49_BOXES"
    assert class_49["wp8_taxonomy"]["reviewer_status"] == "UNAPPROVED"
    assert all(row["g04_effect"] == "NO_DIRECT_COUNT_EFFECT" for row in rows if row["class_id"] != 49)
    assert all(row["post_quarantine_eligibility"]["excluded_stems"] == [] for row in rows if row["class_id"] != 49)


def test_extreme_classes_have_exact_support_and_collect_more_recommendation() -> None:
    rows = read_json(REPO_ROOT / wp11.MATRIX_JSON_RELATIVE_PATH)["rows"]
    assert rows[44]["dataset_code"] == "W.233"
    assert rows[44]["support"] == {"image_count": 3, "box_count": 3}
    assert rows[44]["d04"]["recommended_action"] == "COLLECT_MORE"
    assert rows[44]["d04"]["comparison_eligibility"] == "QUARANTINE_FROM_MODEL_COMPARISON_PENDING_DATA"
    assert rows[51]["dataset_code"] == "W.246c"
    assert rows[51]["support"] == {"image_count": 5, "box_count": 5}
    assert rows[51]["d04"]["recommended_action"] == "COLLECT_MORE"
    assert rows[51]["wp8_taxonomy"]["conflict_flag"] is True


def test_extreme_lineage_covers_every_available_instance_with_exact_hash_and_bbox() -> None:
    rows = read_csv(REPO_ROOT / wp11.EXTREME_CSV_RELATIVE_PATH)
    assert len(rows) == 8
    assert [row["stem"] for row in rows] == ["0670", "0671", "0672", "0530", "0531", "0532", "0533", "0534"]
    assert Counter(int(row["class_id"]) for row in rows) == Counter({44: 3, 51: 5})
    for row in rows:
        stem = row["stem"]
        assert row["image_sha256"] == wp11.EXPECTED_PINNED_HASHES[f"raw_image_{stem}"]
        assert row["label_sha256"] == wp11.EXPECTED_PINNED_HASHES[f"raw_label_{stem}"]
        assert row["bbox_inside_image"] == "True"
        assert float(row["pixel_x_min"]) < float(row["pixel_x_max"])
        assert float(row["pixel_y_min"]) < float(row["pixel_y_max"])
        assert row["effective_independent_support"] == "UNKNOWN_PENDING_D02"
        assert row["group_identity_status"] == "UNKNOWN_NOT_PROXY_GROUND_TRUTH"


def test_atlas_has_two_complete_pages_and_eight_visible_rows() -> None:
    layout = read_json(REPO_ROOT / wp11.LAYOUT_RELATIVE_PATH)
    assert layout["status"] == "PASS_ALL_EXTREME_INSTANCES_RENDERED_WITH_HASH_AND_BBOX_LINEAGE"
    assert layout["page_count"] == 2
    assert layout["extreme_class_ids"] == [44, 51]
    assert layout["extreme_instance_count"] == 8
    assert layout["all_instances_rendered"] is True
    assert layout["all_bounds_fit"] is True
    assert [page["row_count"] for page in layout["pages"]] == [3, 5]
    assert sum(len(page["rows"]) for page in layout["pages"]) == 8
    for page in layout["pages"]:
        path = REPO_ROOT / page["path"]
        assert wp11.sha256_file(path) == page["render_sha256"]
        assert all(row["bbox_visible"] and row["hashes_visible"] and row["all_bounds_fit"] for row in page["rows"])
        with Image.open(path) as image:
            assert image.size == (page["width"], page["height"])
            assert image.mode == "RGB"
            assert image.format == "PNG"
            image.verify()


def test_json_and_csv_matrices_match() -> None:
    matrix = read_json(REPO_ROOT / wp11.MATRIX_JSON_RELATIVE_PATH)
    rare = read_json(REPO_ROOT / wp11.RARE_JSON_RELATIVE_PATH)
    assert read_csv(REPO_ROOT / wp11.MATRIX_CSV_RELATIVE_PATH) == [
        {field: str(value) for field, value in row.items()} for row in wp11.flatten_rows(matrix["rows"])
    ]
    assert read_csv(REPO_ROOT / wp11.RARE_CSV_RELATIVE_PATH) == [
        {field: str(value) for field, value in row.items()} for row in wp11.flatten_rows(rare["rows"])
    ]


def test_report_states_all_required_evidence_boundaries() -> None:
    report = (REPO_ROOT / wp11.REPORT_RELATIVE_PATH).read_text(encoding="utf-8")
    required = [
        "`box_count < 50`",
        "exactly 20 classes",
        "`image_count < 100` (29 classes)",
        "UNKNOWN_PENDING_D02",
        "Adjacent or proxy sequences are not group truth",
        "Class 44 (`W.233`) has exactly 3 images/3 boxes",
        "class 51 (`W.246c`) has exactly 5 images/5 boxes",
        "119 eligible images/219 eligible boxes",
        "D-04 remains `PENDING_OWNER_DECISION`",
        "training_authorized=false",
    ]
    assert all(value in report for value in required)


@pytest.mark.parametrize("mutation", ["remove", "duplicate", "reorder", "insert"])
def test_manifest_rejects_artifact_roster_mutations(tmp_path: Path, mutation: str) -> None:
    payload = read_json(MANIFEST_PATH)
    if mutation == "remove":
        payload["artifacts"].pop()
    elif mutation == "duplicate":
        payload["artifacts"].append(dict(payload["artifacts"][0]))
    elif mutation == "reorder":
        payload["artifacts"][0], payload["artifacts"][1] = payload["artifacts"][1], payload["artifacts"][0]
    else:
        payload["artifacts"].insert(1, {"id": "unexpected", "root": "repo", "path": "PROJECT_MEMORY.md", "sha256": wp11.sha256_file(REPO_ROOT / "PROJECT_MEMORY.md"), "size": (REPO_ROOT / "PROJECT_MEMORY.md").stat().st_size})
    payload["artifact_count"] = len(payload["artifacts"])
    payload["total_artifact_bytes"] = sum(record["size"] for record in payload["artifacts"])
    result = wp11.verify_manifest(write_manifest(tmp_path, payload), REPO_ROOT, RAW_ROOT)
    assert result["valid"] is False
    assert any("artifacts" in error for error in result["errors"])


@pytest.mark.parametrize("mutation", ["remove", "duplicate", "reorder", "insert"])
def test_manifest_rejects_source_roster_mutations(tmp_path: Path, mutation: str) -> None:
    payload = read_json(MANIFEST_PATH)
    if mutation == "remove":
        payload["sources"].pop()
    elif mutation == "duplicate":
        payload["sources"].append(dict(payload["sources"][0]))
    elif mutation == "reorder":
        payload["sources"][0], payload["sources"][1] = payload["sources"][1], payload["sources"][0]
    else:
        payload["sources"].insert(1, {"id": "unexpected", "root": "repo", "path": "PROJECT_MEMORY.md", "sha256": wp11.sha256_file(REPO_ROOT / "PROJECT_MEMORY.md"), "size": (REPO_ROOT / "PROJECT_MEMORY.md").stat().st_size})
    payload["source_count"] = len(payload["sources"])
    result = wp11.verify_manifest(write_manifest(tmp_path, payload), REPO_ROOT, RAW_ROOT)
    assert result["valid"] is False
    assert any("sources" in error for error in result["errors"])


@pytest.mark.parametrize("field", ["source_count", "artifact_count", "total_artifact_bytes"])
def test_manifest_rejects_forged_counts(tmp_path: Path, field: str) -> None:
    payload = read_json(MANIFEST_PATH)
    payload[field] += 1
    result = wp11.verify_manifest(write_manifest(tmp_path, payload), REPO_ROOT, RAW_ROOT)
    assert result["valid"] is False
    assert any(field in error for error in result["errors"])


@pytest.mark.parametrize(
    "attack",
    [
        "matrix_support_drift",
        "matrix_omit_44",
        "matrix_omit_51",
        "matrix_class49_eligible",
        "matrix_auto_merge",
        "matrix_d03_promote",
        "matrix_gate_promote",
        "matrix_training_promote",
        "matrix_owner_status_approved",
        "rare_omit_44",
        "rare_omit_51",
        "rare_action_merge",
        "layout_row_omission",
        "atlas_pixel",
    ],
)
def test_rehashed_semantic_artifact_tamper_is_rejected(tmp_path: Path, attack: str) -> None:
    stage_repo, stage_raw, staged_manifest = stage_package(tmp_path)
    if attack.startswith("matrix"):
        path = stage_repo / wp11.MATRIX_JSON_RELATIVE_PATH
        payload = read_json(path)
        if attack == "matrix_support_drift":
            payload["rows"][44]["support"]["box_count"] = 4
        elif attack == "matrix_omit_44":
            payload["rows"] = [row for row in payload["rows"] if row["class_id"] != 44]
        elif attack == "matrix_omit_51":
            payload["rows"] = [row for row in payload["rows"] if row["class_id"] != 51]
        elif attack == "matrix_class49_eligible":
            payload["rows"][49]["post_quarantine_eligibility"]["eligible_image_count"] = 120
            payload["rows"][49]["post_quarantine_eligibility"]["eligible_box_count"] = 221
        elif attack == "matrix_auto_merge":
            payload["rows"][44]["d04"]["automatic_semantic_merge"] = True
        elif attack == "matrix_d03_promote":
            payload["rows"][44]["governance"]["d03_status"] = "APPROVED"
        elif attack == "matrix_gate_promote":
            payload["gate0"] = "PASS"
        elif attack == "matrix_training_promote":
            payload["training_authorized"] = True
        else:
            payload["rows"][44]["d04"]["owner_status"] = "APPROVED"
    elif attack.startswith("rare"):
        path = stage_repo / wp11.RARE_JSON_RELATIVE_PATH
        payload = read_json(path)
        if attack == "rare_omit_44":
            payload["rows"] = [row for row in payload["rows"] if row["class_id"] != 44]
        elif attack == "rare_omit_51":
            payload["rows"] = [row for row in payload["rows"] if row["class_id"] != 51]
        else:
            payload["rows"][0]["d04"]["recommended_action"] = "MERGE_AUTOMATICALLY"
    elif attack == "layout_row_omission":
        path = stage_repo / wp11.LAYOUT_RELATIVE_PATH
        payload = read_json(path)
        payload["pages"][0]["rows"].pop()
        payload["pages"][0]["row_count"] = 2
    else:
        path = stage_repo / wp11.ASSET_DIR_RELATIVE_PATH / "class_044.png"
        with Image.open(path) as image:
            modified = image.convert("RGB")
        modified.putpixel((1580, 1000), (255, 0, 255))
        modified.save(path, format="PNG", optimize=False)
        payload = None
    if payload is not None:
        path.write_bytes(wp11.json_bytes(payload))
    refresh_manifest(staged_manifest, stage_repo, stage_raw)
    result = wp11.verify_manifest(staged_manifest, stage_repo, stage_raw)
    assert result["valid"] is False
    assert any("semantic verification failed" in error for error in result["errors"])


@pytest.mark.parametrize("source_id", ["per_class_counts", "image_inventory", "wp8_matrix", "wp10_registry", "contract", "raw_image_0670", "raw_label_0670", "raw_image_0530", "raw_label_0530"])
def test_rehashed_source_count_hash_and_bbox_drift_is_rejected(tmp_path: Path, source_id: str) -> None:
    stage_repo, stage_raw, staged_manifest = stage_package(tmp_path)
    manifest = read_json(staged_manifest)
    record = next(record for record in manifest["sources"] if record["id"] == source_id)
    root = stage_repo if record["root"] == "repo" else stage_raw
    path = root / record["path"]
    payload = bytearray(path.read_bytes())
    payload[-1] ^= 1
    path.write_bytes(bytes(payload))
    refresh_manifest(staged_manifest, stage_repo, stage_raw)
    result = wp11.verify_manifest(staged_manifest, stage_repo, stage_raw)
    assert result["valid"] is False
    assert any(f"pinned source hash mismatch: {source_id}" in error for error in result["errors"])


def test_manifest_path_escape_and_symlink_escape_are_rejected(tmp_path: Path) -> None:
    payload = read_json(MANIFEST_PATH)
    payload["sources"][0]["path"] = "../outside.json"
    result = wp11.verify_manifest(write_manifest(tmp_path, payload), REPO_ROOT, RAW_ROOT)
    assert result["valid"] is False
    assert any("unsafe relative path" in error for error in result["errors"])

    stage_repo, stage_raw, staged_manifest = stage_package(tmp_path / "symlink")
    matrix = stage_repo / wp11.MATRIX_JSON_RELATIVE_PATH
    outside = tmp_path / "outside.json"
    shutil.copy2(matrix, outside)
    matrix.unlink()
    matrix.symlink_to(outside)
    result = wp11.verify_manifest(staged_manifest, stage_repo, stage_raw)
    assert result["valid"] is False
    assert any("symlink path is not allowed" in error for error in result["errors"])


def test_rebuild_is_deterministic_and_preserves_wp10_and_raw() -> None:
    package_paths = [REPO_ROOT / relative for relative in (
        wp11.MATRIX_JSON_RELATIVE_PATH,
        wp11.MATRIX_CSV_RELATIVE_PATH,
        wp11.RARE_JSON_RELATIVE_PATH,
        wp11.RARE_CSV_RELATIVE_PATH,
        wp11.EXTREME_CSV_RELATIVE_PATH,
        wp11.LAYOUT_RELATIVE_PATH,
        wp11.REPORT_RELATIVE_PATH,
        f"{wp11.ASSET_DIR_RELATIVE_PATH}/class_044.png",
        f"{wp11.ASSET_DIR_RELATIVE_PATH}/class_051.png",
        wp11.MANIFEST_RELATIVE_PATH,
    )]
    before = {path: wp11.sha256_file(path) for path in package_paths}
    pinned_before = {
        "wp10": wp11.sha256_file(REPO_ROOT / "docs/review/generated/wp10_g04_quarantine_manifest.json"),
        "raw_0670": wp11.sha256_file(RAW_ROOT / "archive/labels/0670.txt"),
        "raw_0530": wp11.sha256_file(RAW_ROOT / "archive/labels/0530.txt"),
    }
    result = wp11.build(REPO_ROOT, RAW_ROOT)
    assert result["manifest_sha256"] == before[REPO_ROOT / wp11.MANIFEST_RELATIVE_PATH]
    assert {path: wp11.sha256_file(path) for path in package_paths} == before
    assert wp11.sha256_file(REPO_ROOT / "docs/review/generated/wp10_g04_quarantine_manifest.json") == pinned_before["wp10"]
    assert wp11.sha256_file(RAW_ROOT / "archive/labels/0670.txt") == pinned_before["raw_0670"]
    assert wp11.sha256_file(RAW_ROOT / "archive/labels/0530.txt") == pinned_before["raw_0530"]


def test_clean_room_rebuild_is_byte_identical(tmp_path: Path) -> None:
    stage_repo, stage_raw, staged_manifest = stage_package(tmp_path)
    official_paths = [record["path"] for record in read_json(MANIFEST_PATH)["artifacts"]] + [wp11.MANIFEST_RELATIVE_PATH]
    official_hashes = {relative: wp11.sha256_file(REPO_ROOT / relative) for relative in official_paths}
    for relative in official_paths[:-1]:
        (stage_repo / relative).unlink()
    staged_manifest.unlink()
    result = wp11.build(stage_repo, stage_raw)
    assert result["manifest_sha256"] == official_hashes[wp11.MANIFEST_RELATIVE_PATH]
    assert {relative: wp11.sha256_file(stage_repo / relative) for relative in official_paths} == official_hashes
