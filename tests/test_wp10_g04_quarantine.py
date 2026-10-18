# ruff: noqa: E501
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/build_wp10_g04_quarantine.py"
SPEC = importlib.util.spec_from_file_location("build_wp10_g04_quarantine", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
wp10 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp10
SPEC.loader.exec_module(wp10)

RAW_ROOT = wp10.default_raw_root(REPO_ROOT)
MANIFEST_PATH = REPO_ROOT / wp10.MANIFEST_RELATIVE_PATH


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
    staged_manifest = stage_repo / wp10.MANIFEST_RELATIVE_PATH
    copy_file(MANIFEST_PATH, staged_manifest)
    return stage_repo, stage_raw, staged_manifest


def refresh_manifest(staged_manifest: Path, stage_repo: Path, stage_raw: Path) -> None:
    payload = read_json(staged_manifest)
    roots = {"repo": stage_repo, "raw": stage_raw}
    for collection in ("sources", "artifacts"):
        for record in payload[collection]:
            path = roots[record["root"]] / record["path"]
            if path.is_file():
                record["sha256"] = wp10.sha256_file(path)
                record["size"] = path.stat().st_size
    payload["total_artifact_bytes"] = sum(record["size"] for record in payload["artifacts"])
    staged_manifest.write_bytes(wp10.json_bytes(payload))


def write_manifest(tmp_path: Path, payload: dict[str, Any]) -> Path:
    path = tmp_path / "manifest.json"
    path.write_bytes(wp10.json_bytes(payload))
    return path


def test_official_package_verifies_with_exact_rosters() -> None:
    result = wp10.verify_manifest(MANIFEST_PATH, REPO_ROOT, RAW_ROOT)
    assert result == {
        "valid": True,
        "errors": [],
        "source_count": 10,
        "artifact_count": 3,
        "status": wp10.PACKAGE_STATUS,
        "decision_status": "OWNER_APPROVED",
        "selected_option": "APPROVED_QUARANTINE",
    }
    manifest = read_json(MANIFEST_PATH)
    assert manifest["source_count"] == len(manifest["sources"]) == 10
    assert manifest["artifact_count"] == len(manifest["artifacts"]) == 3
    assert manifest["manifest_self_in_artifact_count"] is False
    assert manifest["artifact_count_semantics"] == "EXCLUDES_MANIFEST_FILE"
    assert wp10.MANIFEST_RELATIVE_PATH not in {record["path"] for record in manifest["artifacts"]}


def test_owner_overlay_is_append_only_and_exact() -> None:
    overlay = read_json(REPO_ROOT / wp10.OVERLAY_RELATIVE_PATH)
    assert overlay["overlay_type"] == "APPEND_ONLY_OWNER_DECISION_RESOLUTION"
    assert overlay["historical_decision_file_mutated"] is False
    assert overlay["decision"] == {
        "authority": "DIRECT_OWNER_APPROVAL_ROUTED_QA_PM",
        "decision_date": "2026-10-11",
        "decision_id": "G0.4-bbox-0248",
        "decision_timezone": "Asia/Saigon",
        "selected_option": "APPROVED_QUARANTINE",
        "status": "OWNER_APPROVED",
    }
    assert overlay["scope"]["scope_type"] == "ENTIRE_IMAGE_STEM"
    assert overlay["scope"]["stem"] == "0248"
    assert overlay["scope"]["label_rows"] == [1, 2]
    assert overlay["scope"]["class_ids_present"] == [49]
    assert overlay["scope"]["class_49_taxonomy_excluded"] is False
    assert overlay["scope"]["only_sample_0248_quarantined"] is True


def test_registry_enforces_entire_stem_and_preserves_taxonomy() -> None:
    registry = read_json(REPO_ROOT / wp10.REGISTRY_RELATIVE_PATH)
    assert registry["entry_count"] == registry["quarantined_stem_count"] == 1
    assert registry["default_policy"] == "FAIL_CLOSED_IF_OWNER_OVERLAY_OR_REGISTRY_IS_MISSING_INVALID_OR_UNVERIFIED"
    entry = registry["entries"][0]
    assert entry["stem"] == "0248"
    assert entry["scope_type"] == "ENTIRE_IMAGE_STEM"
    assert entry["label_row_count"] == 2
    assert entry["label_rows"] == [1, 2]
    assert entry["exclude_entire_stem_from_split_generation"] is True
    assert entry["exclude_entire_stem_from_training"] is True
    assert entry["raw_immutable"] is True
    assert entry["derived_clip_usage"] == wp10.DERIVED_CLIP_USAGE
    assert entry["class_49_taxonomy_excluded"] is False
    assert registry["governance"]["training_authorized"] is False


def test_historical_decision_and_raw_are_unchanged() -> None:
    historical = read_json(REPO_ROOT / "docs/review/decision_status.json")
    assert historical["decisions"][wp10.DECISION_ID]["status"] == "PENDING"
    assert historical["decisions"][wp10.DECISION_ID]["selected_option"] is None
    assert wp10.sha256_file(REPO_ROOT / "docs/review/decision_status.json") == wp10.EXPECTED_PINNED_HASHES["historical_decision_status"]
    assert wp10.sha256_file(RAW_ROOT / "archive/images/0248.jpg") == wp10.EXPECTED_PINNED_HASHES["raw_image_0248"]
    assert wp10.sha256_file(RAW_ROOT / "archive/labels/0248.txt") == wp10.EXPECTED_PINNED_HASHES["raw_label_0248"]
    assert wp10.sha256_file(REPO_ROOT / "docs/review/generated/wp9_bbox_0248_derived_candidate.txt") == wp10.EXPECTED_PINNED_HASHES["wp9_derived_candidate"]


def test_report_states_exact_enforcement_and_remaining_governance() -> None:
    report = (REPO_ROOT / wp10.REPORT_RELATIVE_PATH).read_text(encoding="utf-8")
    required = [
        "entire image/stem `0248`",
        "both raw",
        "label rows",
        wp10.DERIVED_CLIP_USAGE,
        "Class `49` and its taxonomy remain in scope",
        "G0.4 becomes formally closed only after WP10 QA PASS",
        "D-01 through D-05 remain",
        "training_authorized=false",
    ]
    assert all(value in report for value in required)


def test_candidate_with_quarantined_stem_is_rejected() -> None:
    result = wp10.verify_candidate_stems(["0247", "0248", "0249"], MANIFEST_PATH, REPO_ROOT, RAW_ROOT)
    assert result["allowed"] is False
    assert result["candidate_passes_quarantine_check"] is False
    assert result["status"] == "REJECTED_QUARANTINED_STEM"
    assert result["violations"] == [{
        "stem": "0248",
        "decision_id": "G0.4-bbox-0248",
        "selected_option": "APPROVED_QUARANTINE",
        "scope": "ENTIRE_IMAGE_STEM_ALL_LABEL_ROWS",
        "reason": "owner-approved quarantine excludes stem 0248 from split generation and training",
    }]
    assert result["training_authorized"] is False


def test_candidate_without_quarantined_stem_passes_only_this_check() -> None:
    result = wp10.verify_candidate_stems(["0247", "0249"], MANIFEST_PATH, REPO_ROOT, RAW_ROOT)
    assert result["allowed"] is True
    assert result["candidate_passes_quarantine_check"] is True
    assert result["status"] == "ACCEPTED_NO_QUARANTINED_STEMS"
    assert result["violations"] == []
    assert result["training_authorized"] is False


@pytest.mark.parametrize(
    ("name", "payload", "expected_allowed"),
    [
        ("list.json", ["0247", "0248"], False),
        ("stems.json", {"stems": ["0247", "0249"]}, True),
        ("splits.json", {"splits": {"train": ["0247"], "validation": ["0248"]}}, False),
        ("stems.txt", "0247\n0249\n", True),
    ],
)
def test_supported_candidate_formats(tmp_path: Path, name: str, payload: Any, expected_allowed: bool) -> None:
    path = tmp_path / name
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        path.write_text(json.dumps(payload), encoding="utf-8")
    result = wp10.verify_candidate_path(path, MANIFEST_PATH, REPO_ROOT, RAW_ROOT)
    assert result["allowed"] is expected_allowed
    assert result["training_authorized"] is False


@pytest.mark.parametrize(
    "payload",
    [
        [],
        ["0247", "0247"],
        ["../0248"],
        ["archive/images/0248"],
        [" 0248"],
        [248],
    ],
)
def test_invalid_candidate_stem_lists_fail_closed(payload: Any) -> None:
    result = wp10.verify_candidate_stems(payload, MANIFEST_PATH, REPO_ROOT, RAW_ROOT)
    assert result["allowed"] is False
    assert result["status"] == "REJECTED_CANDIDATE_INVALID_FAIL_CLOSED"
    assert result["training_authorized"] is False


def test_candidate_symlink_fails_closed(tmp_path: Path) -> None:
    actual = tmp_path / "actual.txt"
    actual.write_text("0247\n", encoding="utf-8")
    link = tmp_path / "candidate.txt"
    link.symlink_to(actual)
    result = wp10.verify_candidate_path(link, MANIFEST_PATH, REPO_ROOT, RAW_ROOT)
    assert result["allowed"] is False
    assert result["status"] == "REJECTED_CANDIDATE_INVALID_FAIL_CLOSED"
    assert any("symlink" in error for error in result["errors"])


@pytest.mark.parametrize("missing", ["manifest", "overlay", "registry"])
def test_missing_package_controls_reject_candidate_fail_closed(tmp_path: Path, missing: str) -> None:
    stage_repo, stage_raw, staged_manifest = stage_package(tmp_path)
    if missing == "manifest":
        staged_manifest.unlink()
    elif missing == "overlay":
        (stage_repo / wp10.OVERLAY_RELATIVE_PATH).unlink()
    else:
        (stage_repo / wp10.REGISTRY_RELATIVE_PATH).unlink()
    result = wp10.verify_candidate_stems(["0247"], staged_manifest, stage_repo, stage_raw)
    assert result["allowed"] is False
    assert result["status"] == "REJECTED_PACKAGE_INVALID_FAIL_CLOSED"
    assert result["training_authorized"] is False


@pytest.mark.parametrize(
    "attack",
    [
        "overlay_pending",
        "overlay_wrong_option",
        "overlay_training_clip",
        "registry_remove_entry",
        "registry_scope_line_only",
        "registry_allow_split",
        "registry_allow_training",
        "registry_training_clip",
    ],
)
def test_rehashed_semantic_overlay_and_registry_tamper_is_rejected(tmp_path: Path, attack: str) -> None:
    stage_repo, stage_raw, staged_manifest = stage_package(tmp_path)
    if attack.startswith("overlay"):
        path = stage_repo / wp10.OVERLAY_RELATIVE_PATH
        payload = read_json(path)
        if attack == "overlay_pending":
            payload["decision"]["status"] = "PENDING"
        elif attack == "overlay_wrong_option":
            payload["decision"]["selected_option"] = "keep_raw_as_warning"
        else:
            payload["enforcement"]["derived_clip_usage"] = "TRAINING_AUTHORIZED"
    else:
        path = stage_repo / wp10.REGISTRY_RELATIVE_PATH
        payload = read_json(path)
        if attack == "registry_remove_entry":
            payload["entries"] = []
            payload["entry_count"] = 0
            payload["quarantined_stem_count"] = 0
        elif attack == "registry_scope_line_only":
            payload["entries"][0]["scope_type"] = "LABEL_LINE_1_ONLY"
            payload["entries"][0]["label_rows"] = [1]
            payload["entries"][0]["label_row_count"] = 1
        elif attack == "registry_allow_split":
            payload["entries"][0]["exclude_entire_stem_from_split_generation"] = False
        elif attack == "registry_allow_training":
            payload["entries"][0]["exclude_entire_stem_from_training"] = False
        else:
            payload["entries"][0]["derived_clip_usage"] = "TRAINING_AUTHORIZED"
    path.write_bytes(wp10.json_bytes(payload))
    refresh_manifest(staged_manifest, stage_repo, stage_raw)
    result = wp10.verify_manifest(staged_manifest, stage_repo, stage_raw)
    assert result["valid"] is False
    assert any("semantic verification failed" in error for error in result["errors"])
    candidate = wp10.verify_candidate_stems(["0247"], staged_manifest, stage_repo, stage_raw)
    assert candidate["allowed"] is False
    assert candidate["status"] == "REJECTED_PACKAGE_INVALID_FAIL_CLOSED"


@pytest.mark.parametrize("source_id", ["raw_image_0248", "raw_label_0248", "wp9_manifest", "wp9_derived_candidate", "contract"])
def test_rehashed_source_drift_is_rejected(tmp_path: Path, source_id: str) -> None:
    stage_repo, stage_raw, staged_manifest = stage_package(tmp_path)
    manifest = read_json(staged_manifest)
    record = next(record for record in manifest["sources"] if record["id"] == source_id)
    root = stage_repo if record["root"] == "repo" else stage_raw
    path = root / record["path"]
    payload = bytearray(path.read_bytes())
    payload[-1] ^= 1
    path.write_bytes(bytes(payload))
    refresh_manifest(staged_manifest, stage_repo, stage_raw)
    result = wp10.verify_manifest(staged_manifest, stage_repo, stage_raw)
    assert result["valid"] is False
    assert any(f"pinned source hash mismatch: {source_id}" in error for error in result["errors"])


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
        payload["artifacts"].insert(1, {
            "id": "unexpected", "root": "repo", "path": "PROJECT_MEMORY.md",
            "sha256": wp10.sha256_file(REPO_ROOT / "PROJECT_MEMORY.md"),
            "size": (REPO_ROOT / "PROJECT_MEMORY.md").stat().st_size,
        })
    payload["artifact_count"] = len(payload["artifacts"])
    payload["total_artifact_bytes"] = sum(record["size"] for record in payload["artifacts"])
    result = wp10.verify_manifest(write_manifest(tmp_path, payload), REPO_ROOT, RAW_ROOT)
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
        payload["sources"].insert(1, {
            "id": "unexpected", "root": "repo", "path": "PROJECT_MEMORY.md",
            "sha256": wp10.sha256_file(REPO_ROOT / "PROJECT_MEMORY.md"),
            "size": (REPO_ROOT / "PROJECT_MEMORY.md").stat().st_size,
        })
    payload["source_count"] = len(payload["sources"])
    result = wp10.verify_manifest(write_manifest(tmp_path, payload), REPO_ROOT, RAW_ROOT)
    assert result["valid"] is False
    assert any("sources" in error for error in result["errors"])


@pytest.mark.parametrize("field", ["source_count", "artifact_count", "total_artifact_bytes"])
def test_manifest_rejects_forged_counts(tmp_path: Path, field: str) -> None:
    payload = read_json(MANIFEST_PATH)
    payload[field] += 1
    result = wp10.verify_manifest(write_manifest(tmp_path, payload), REPO_ROOT, RAW_ROOT)
    assert result["valid"] is False
    assert any(field in error for error in result["errors"])


def test_manifest_path_escape_and_symlink_escape_are_rejected(tmp_path: Path) -> None:
    payload = read_json(MANIFEST_PATH)
    payload["sources"][0]["path"] = "../outside.json"
    result = wp10.verify_manifest(write_manifest(tmp_path, payload), REPO_ROOT, RAW_ROOT)
    assert result["valid"] is False
    assert any("unsafe relative path" in error for error in result["errors"])

    stage_repo, stage_raw, staged_manifest = stage_package(tmp_path / "symlink")
    registry = stage_repo / wp10.REGISTRY_RELATIVE_PATH
    outside = tmp_path / "outside.json"
    shutil.copy2(registry, outside)
    registry.unlink()
    registry.symlink_to(outside)
    result = wp10.verify_manifest(staged_manifest, stage_repo, stage_raw)
    assert result["valid"] is False
    assert any("symlink path is not allowed" in error for error in result["errors"])


def test_rebuild_is_deterministic_and_preserves_all_pinned_inputs() -> None:
    package_paths = [REPO_ROOT / relative for relative in (
        wp10.OVERLAY_RELATIVE_PATH,
        wp10.REGISTRY_RELATIVE_PATH,
        wp10.REPORT_RELATIVE_PATH,
        wp10.MANIFEST_RELATIVE_PATH,
    )]
    before = {path: wp10.sha256_file(path) for path in package_paths}
    pinned_before = {
        "raw_label": wp10.sha256_file(RAW_ROOT / "archive/labels/0248.txt"),
        "wp8": wp10.sha256_file(REPO_ROOT / "docs/review/generated/wp8_taxonomy_manifest.json"),
        "wp9": wp10.sha256_file(REPO_ROOT / "docs/review/generated/wp9_bbox_0248_manifest.json"),
        "derived": wp10.sha256_file(REPO_ROOT / "docs/review/generated/wp9_bbox_0248_derived_candidate.txt"),
    }
    result = wp10.build(REPO_ROOT, RAW_ROOT)
    assert result["manifest_sha256"] == before[REPO_ROOT / wp10.MANIFEST_RELATIVE_PATH]
    assert {path: wp10.sha256_file(path) for path in package_paths} == before
    assert wp10.sha256_file(RAW_ROOT / "archive/labels/0248.txt") == pinned_before["raw_label"]
    assert wp10.sha256_file(REPO_ROOT / "docs/review/generated/wp8_taxonomy_manifest.json") == pinned_before["wp8"]
    assert wp10.sha256_file(REPO_ROOT / "docs/review/generated/wp9_bbox_0248_manifest.json") == pinned_before["wp9"]
    assert wp10.sha256_file(REPO_ROOT / "docs/review/generated/wp9_bbox_0248_derived_candidate.txt") == pinned_before["derived"]


def test_clean_room_rebuild_is_byte_identical(tmp_path: Path) -> None:
    stage_repo, stage_raw, staged_manifest = stage_package(tmp_path)
    official_paths = [
        wp10.OVERLAY_RELATIVE_PATH,
        wp10.REGISTRY_RELATIVE_PATH,
        wp10.REPORT_RELATIVE_PATH,
        wp10.MANIFEST_RELATIVE_PATH,
    ]
    official_hashes = {relative: wp10.sha256_file(REPO_ROOT / relative) for relative in official_paths}
    for relative in official_paths[:-1]:
        (stage_repo / relative).unlink()
    staged_manifest.unlink()
    result = wp10.build(stage_repo, stage_raw)
    assert result["manifest_sha256"] == official_hashes[wp10.MANIFEST_RELATIVE_PATH]
    assert {relative: wp10.sha256_file(stage_repo / relative) for relative in official_paths} == official_hashes
