# ruff: noqa: E501
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest
from PIL import Image

REPO_ROOT = Path(__file__).parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/build_wp9_bbox_0248_adjudication.py"
SPEC = importlib.util.spec_from_file_location("build_wp9_bbox_0248_adjudication", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
wp9 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp9
SPEC.loader.exec_module(wp9)

RAW_ROOT = wp9.default_raw_root(REPO_ROOT)
MANIFEST_PATH = REPO_ROOT / wp9.MANIFEST_RELATIVE_PATH


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


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
    staged_manifest = stage_repo / wp9.MANIFEST_RELATIVE_PATH
    copy_file(MANIFEST_PATH, staged_manifest)
    return stage_repo, stage_raw, staged_manifest


def refresh_manifest(staged_manifest: Path, stage_repo: Path, stage_raw: Path) -> None:
    payload = read_json(staged_manifest)
    roots = {"repo": stage_repo, "raw": stage_raw}
    for collection in ("sources", "artifacts"):
        for record in payload[collection]:
            path = roots[record["root"]] / record["path"]
            if path.is_file():
                record["sha256"] = wp9.sha256_file(path)
                record["size"] = path.stat().st_size
    payload["total_artifact_bytes"] = sum(record["size"] for record in payload["artifacts"])
    staged_manifest.write_bytes(wp9.json_bytes(payload))


def write_manifest(tmp_path: Path, payload: dict[str, Any]) -> Path:
    path = tmp_path / "manifest.json"
    path.write_bytes(wp9.json_bytes(payload))
    return path


def test_official_package_verifies_with_exact_rosters() -> None:
    result = wp9.verify_manifest(MANIFEST_PATH, REPO_ROOT, RAW_ROOT)
    assert result == {
        "valid": True,
        "errors": [],
        "source_count": 17,
        "artifact_count": 5,
        "status": wp9.PACKAGE_STATUS,
    }
    manifest = read_json(MANIFEST_PATH)
    assert manifest["source_count"] == len(manifest["sources"]) == 17
    assert manifest["artifact_count"] == len(manifest["artifacts"]) == 5
    assert manifest["manifest_self_in_artifact_count"] is False
    assert manifest["artifact_count_semantics"] == "EXCLUDES_MANIFEST_FILE"
    assert wp9.MANIFEST_RELATIVE_PATH not in {record["path"] for record in manifest["artifacts"]}


def test_raw_fact_and_visual_assessment_are_explicit() -> None:
    payload = read_json(REPO_ROOT / wp9.ADJUDICATION_RELATIVE_PATH)
    assert payload["target"]["stem"] == "0248"
    assert payload["target"]["class_id"] == 49
    assert payload["target"]["label"]["line_number"] == 1
    assert payload["target"]["label"]["line_index"] == 0
    fact = payload["verified_raw_fact"]
    assert fact["pixel_xyxy"] == wp9.EXPECTED_RAW_XYXY
    assert fact["right_overflow_px"] == pytest.approx(18.00048)
    assert fact["raw_bytes_unchanged"] is True
    assert payload["visual_assessment"]["finding"] == "IMAGE_EDGE_TRUNCATED_OBJECT_WITH_RAW_BOX_EXTENDING_BEYOND_RIGHT_BOUNDARY"
    assert payload["visual_assessment"]["confidence"] == "HIGH"


def test_clip_candidate_is_exact_and_raw_is_unchanged() -> None:
    raw_hash_before = wp9.sha256_file(RAW_ROOT / "archive/labels/0248.txt")
    derived = (REPO_ROOT / wp9.DERIVED_LABEL_RELATIVE_PATH).read_text(encoding="ascii")
    assert derived == "\n".join(wp9.EXPECTED_DERIVED_LINES) + "\n"
    assert wp9.sha256_file(RAW_ROOT / "archive/labels/0248.txt") == raw_hash_before == wp9.EXPECTED_PINNED_HASHES["raw_label_0248"]
    payload = read_json(REPO_ROOT / wp9.ADJUDICATION_RELATIVE_PATH)
    candidate = payload["derived_clip_candidate"]
    assert candidate["raw_line_1_pixel_xyxy"] == wp9.EXPECTED_RAW_XYXY
    assert candidate["derived_line_1_pixel_xyxy"] == wp9.EXPECTED_CLIPPED_XYXY
    assert candidate["right_overflow_removed_px"] == pytest.approx(18.00048)
    assert candidate["source_raw_label_overwritten"] is False


def test_recommendation_is_separate_from_owner_decision() -> None:
    payload = read_json(REPO_ROOT / wp9.ADJUDICATION_RELATIVE_PATH)
    assert payload["recommendation"]["proposed_disposition"] == wp9.RECOMMENDATION
    assert payload["recommendation"]["raw_handling"] == wp9.RAW_HANDLING
    assert payload["recommendation"]["derived_candidate_role"] == wp9.DERIVED_ROLE
    assert payload["owner_decision"] == {
        "decision_id": "G0.4-bbox-0248",
        "recommendation_is_not_owner_approval": True,
        "selected_option": None,
        "status": "PENDING",
    }
    assert payload["governance"] == {
        "gate0": "BLOCKED",
        "relabel_authorized": False,
        "split_authorized": False,
        "training_authorized": False,
    }


def test_context_is_proxy_only_and_not_group_truth() -> None:
    payload = read_json(REPO_ROOT / wp9.ADJUDICATION_RELATIVE_PATH)
    assert [record["stem"] for record in payload["context_proxy_only"]] == ["0247", "0249"]
    assert all(record["role"] == "ADJACENCY_CONTEXT_PROXY_ONLY_NOT_GROUP_GROUND_TRUTH" for record in payload["context_proxy_only"])


def test_visual_layout_and_png_contract() -> None:
    layout = read_json(REPO_ROOT / wp9.LAYOUT_RELATIVE_PATH)
    assert layout["status"] == "PASS_ALL_PANELS_AND_OVERLAYS_WITHIN_CANVAS"
    assert layout["canvas"] == {"height": 1500, "width": 1900}
    assert layout["raw_box_extends_beyond_image_boundary"] is True
    assert layout["zoom_virtual_outside_area_visible"] is True
    assert layout["context_is_proxy_only"] is True
    assert layout["all_three_options_visible"] is True
    assert layout["recommendation_visible"] is True
    assert layout["all_bounds_fit"] is True
    visual = REPO_ROOT / wp9.VISUAL_RELATIVE_PATH
    assert layout["render_sha256"] == wp9.sha256_file(visual)
    with Image.open(visual) as image:
        assert image.size == (1900, 1500)
        assert image.mode == "RGB"
        assert image.format == "PNG"
        image.verify()


def test_report_states_evidence_and_governance_boundaries() -> None:
    report = (REPO_ROOT / wp9.REPORT_RELATIVE_PATH).read_text(encoding="utf-8")
    required = [
        "Verified raw fact",
        "IMAGE_EDGE_TRUNCATED_OBJECT_WITH_RAW_BOX_EXTENDING_BEYOND_RIGHT_BOUNDARY",
        "PM recommendation — proposal, not owner approval",
        wp9.RECOMMENDATION,
        "Owner decision `G0.4-bbox-0248`: `PENDING`",
        "training_authorized=false",
        wp9.EXPECTED_PINNED_HASHES["wp8_manifest"],
    ]
    assert all(value in report for value in required)


def test_rebuild_is_deterministic_and_preserves_raw() -> None:
    paths = [REPO_ROOT / relative for relative in (
        wp9.ADJUDICATION_RELATIVE_PATH,
        wp9.DERIVED_LABEL_RELATIVE_PATH,
        wp9.LAYOUT_RELATIVE_PATH,
        wp9.REPORT_RELATIVE_PATH,
        wp9.VISUAL_RELATIVE_PATH,
        wp9.MANIFEST_RELATIVE_PATH,
    )]
    before = {path: wp9.sha256_file(path) for path in paths}
    raw_before = wp9.sha256_file(RAW_ROOT / "archive/labels/0248.txt")
    result = wp9.build(REPO_ROOT, RAW_ROOT)
    assert result["manifest_sha256"] == before[REPO_ROOT / wp9.MANIFEST_RELATIVE_PATH]
    assert {path: wp9.sha256_file(path) for path in paths} == before
    assert wp9.sha256_file(RAW_ROOT / "archive/labels/0248.txt") == raw_before


def test_clean_room_rebuild_is_byte_identical(tmp_path: Path) -> None:
    stage_repo, stage_raw, staged_manifest = stage_package(tmp_path)
    official_paths = [
        wp9.ADJUDICATION_RELATIVE_PATH,
        wp9.DERIVED_LABEL_RELATIVE_PATH,
        wp9.LAYOUT_RELATIVE_PATH,
        wp9.REPORT_RELATIVE_PATH,
        wp9.VISUAL_RELATIVE_PATH,
        wp9.MANIFEST_RELATIVE_PATH,
    ]
    official_hashes = {relative: wp9.sha256_file(REPO_ROOT / relative) for relative in official_paths}
    for relative in official_paths[:-1]:
        (stage_repo / relative).unlink()
    staged_manifest.unlink()
    result = wp9.build(stage_repo, stage_raw)
    assert result["manifest_sha256"] == official_hashes[wp9.MANIFEST_RELATIVE_PATH]
    assert {relative: wp9.sha256_file(stage_repo / relative) for relative in official_paths} == official_hashes


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
        payload["artifacts"].append({
            "id": "unexpected", "root": "repo", "path": "PROJECT_MEMORY.md",
            "sha256": wp9.sha256_file(REPO_ROOT / "PROJECT_MEMORY.md"),
            "size": (REPO_ROOT / "PROJECT_MEMORY.md").stat().st_size,
        })
    payload["artifact_count"] = len(payload["artifacts"])
    payload["total_artifact_bytes"] = sum(record["size"] for record in payload["artifacts"])
    result = wp9.verify_manifest(write_manifest(tmp_path, payload), REPO_ROOT, RAW_ROOT)
    assert result["valid"] is False
    assert any("artifacts" in error for error in result["errors"])


@pytest.mark.parametrize("field", ["source_count", "artifact_count", "total_artifact_bytes"])
def test_manifest_rejects_forged_counts(tmp_path: Path, field: str) -> None:
    payload = read_json(MANIFEST_PATH)
    payload[field] += 1
    result = wp9.verify_manifest(write_manifest(tmp_path, payload), REPO_ROOT, RAW_ROOT)
    assert result["valid"] is False
    assert any(field in error for error in result["errors"])


@pytest.mark.parametrize(
    ("field_path", "replacement"),
    [
        (("target", "stem"), "0249"),
        (("target", "class_id"), 48),
        (("target", "label_line_number"), 2),
        (("target", "label_line_index"), 1),
        (("raw_annotation", "pixel_xyxy"), [927.0, 159.0, 960.0, 214.0]),
        (("raw_annotation", "right_overflow_px"), 0.0),
    ],
)
def test_rehashed_contract_identity_geometry_and_overflow_tamper_is_rejected(tmp_path: Path, field_path: tuple[str, str], replacement: Any) -> None:
    stage_repo, stage_raw, staged_manifest = stage_package(tmp_path)
    contract_path = stage_repo / wp9.CONTRACT_RELATIVE_PATH
    contract = read_json(contract_path)
    contract[field_path[0]][field_path[1]] = replacement
    contract_path.write_bytes(wp9.json_bytes(contract))
    refresh_manifest(staged_manifest, stage_repo, stage_raw)
    result = wp9.verify_manifest(staged_manifest, stage_repo, stage_raw)
    assert result["valid"] is False
    assert any("pinned source hash mismatch: contract" in error for error in result["errors"])


@pytest.mark.parametrize("attack", ["adjudication", "derived_label", "layout", "report", "visual"])
def test_rehashed_semantic_artifact_tamper_is_rejected(tmp_path: Path, attack: str) -> None:
    stage_repo, stage_raw, staged_manifest = stage_package(tmp_path)
    if attack == "adjudication":
        path = stage_repo / wp9.ADJUDICATION_RELATIVE_PATH
        payload = read_json(path)
        payload["derived_clip_candidate"]["derived_line_1_pixel_xyxy"][2] = 959.0
        path.write_bytes(wp9.json_bytes(payload))
    elif attack == "derived_label":
        path = stage_repo / wp9.DERIVED_LABEL_RELATIVE_PATH
        path.write_text("49 0.982812750 0.345370000 0.034374500 0.100000000\n" + wp9.EXPECTED_RAW_LINES[1] + "\n", encoding="ascii")
    elif attack == "layout":
        path = stage_repo / wp9.LAYOUT_RELATIVE_PATH
        payload = read_json(path)
        payload["raw_box_extends_beyond_image_boundary"] = False
        path.write_bytes(wp9.json_bytes(payload))
    elif attack == "report":
        path = stage_repo / wp9.REPORT_RELATIVE_PATH
        path.write_text(path.read_text(encoding="utf-8").replace("`PENDING`", "`APPROVED`", 1), encoding="utf-8")
    else:
        path = stage_repo / wp9.VISUAL_RELATIVE_PATH
        with Image.open(path) as image:
            modified = image.convert("RGB")
        modified.putpixel((1880, 1420), (255, 0, 255))
        modified.save(path, format="PNG", optimize=False)
    refresh_manifest(staged_manifest, stage_repo, stage_raw)
    result = wp9.verify_manifest(staged_manifest, stage_repo, stage_raw)
    assert result["valid"] is False
    assert any("semantic verification failed" in error for error in result["errors"])


@pytest.mark.parametrize("target", ["image", "label"])
def test_rehashed_raw_source_mutation_is_rejected(tmp_path: Path, target: str) -> None:
    stage_repo, stage_raw, staged_manifest = stage_package(tmp_path)
    path = stage_raw / ("archive/images/0248.jpg" if target == "image" else "archive/labels/0248.txt")
    payload = bytearray(path.read_bytes())
    payload[-1] ^= 1
    path.write_bytes(bytes(payload))
    refresh_manifest(staged_manifest, stage_repo, stage_raw)
    result = wp9.verify_manifest(staged_manifest, stage_repo, stage_raw)
    assert result["valid"] is False
    expected_id = "raw_image_0248" if target == "image" else "raw_label_0248"
    assert any(f"pinned source hash mismatch: {expected_id}" in error for error in result["errors"])


def test_path_escape_and_symlink_escape_are_rejected(tmp_path: Path) -> None:
    payload = read_json(MANIFEST_PATH)
    payload["sources"][0]["path"] = "../outside.json"
    result = wp9.verify_manifest(write_manifest(tmp_path, payload), REPO_ROOT, RAW_ROOT)
    assert result["valid"] is False
    assert any("unsafe relative path" in error for error in result["errors"])

    stage_repo, stage_raw, staged_manifest = stage_package(tmp_path / "symlink")
    candidate = stage_repo / wp9.DERIVED_LABEL_RELATIVE_PATH
    outside = tmp_path / "outside.txt"
    shutil.copy2(candidate, outside)
    candidate.unlink()
    candidate.symlink_to(outside)
    result = wp9.verify_manifest(staged_manifest, stage_repo, stage_raw)
    assert result["valid"] is False
    assert any("symlink path is not allowed" in error for error in result["errors"])
