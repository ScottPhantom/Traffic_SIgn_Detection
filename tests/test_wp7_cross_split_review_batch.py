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
SCRIPT_PATH = REPO_ROOT / "scripts/build_wp7_cross_split_review_batch.py"
SPEC = importlib.util.spec_from_file_location(
    "build_wp7_cross_split_review_batch", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
wp7 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp7
SPEC.loader.exec_module(wp7)

RAW_ROOT = Path(
    "/Users/nguyentantai/Library/Mobile Documents/com~apple~CloudDocs/"
    "FALL 2026 KỲ 4/CPV301/Data/DATASET01/staging/052bc980a7206f8d/raw"
)
MANIFEST_PATH = REPO_ROOT / wp7.MANIFEST_RELATIVE_PATH


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def stage_package(tmp_path: Path) -> Path:
    manifest = read_json(MANIFEST_PATH)
    for record in [*manifest["sources"], *manifest["artifacts"]]:
        source = REPO_ROOT / record["path"]
        target = tmp_path / record["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    staged = tmp_path / wp7.MANIFEST_RELATIVE_PATH
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
                record["sha256"] = wp7.sha256_file(path)
                record["size"] = path.stat().st_size
    payload["total_artifact_bytes"] = sum(
        record["size"] for record in payload["artifacts"]
    )
    wp7.write_json(staged_manifest, payload)


def verify_payload(tmp_path: Path, payload: Any, name: str) -> dict[str, Any]:
    path = tmp_path / name
    wp7.write_json(path, payload)
    return wp7.verify_manifest(path, REPO_ROOT, RAW_ROOT)


def test_official_package_verifies_with_exact_rosters() -> None:
    result = wp7.verify_manifest(MANIFEST_PATH, REPO_ROOT, RAW_ROOT)
    assert result == {
        "valid": True,
        "errors": [],
        "source_count": 9,
        "artifact_count": 25,
        "status": wp7.PACKAGE_STATUS,
    }
    manifest = read_json(MANIFEST_PATH)
    assert manifest["source_count"] == len(manifest["sources"]) == 9
    assert manifest["artifact_count"] == len(manifest["artifacts"]) == 25
    assert manifest["manifest_self_in_artifact_count"] is False
    assert manifest["artifact_count_semantics"] == "EXCLUDES_MANIFEST_FILE"
    assert wp7.MANIFEST_RELATIVE_PATH not in {
        row["path"] for row in manifest["artifacts"]
    }
    assert manifest["total_artifact_bytes"] == sum(
        (REPO_ROOT / row["path"]).stat().st_size for row in manifest["artifacts"]
    )


def test_selection_is_exact_first_100_pending_cross_split_rows() -> None:
    actual = read_csv(REPO_ROOT / wp7.SELECTION_RELATIVE_PATH)
    expected, _inventory = wp7.derive_selection(REPO_ROOT, RAW_ROOT)
    assert actual == expected
    assert len(actual) == len({row["edge_id"] for row in actual}) == 100
    assert actual[0]["edge_id"] == "edge_000006"
    assert actual[-1]["edge_id"] == "edge_000307"
    assert all(row["cross_split"] == "True" for row in actual)
    assert all(row["wp5_review_status"] == "PENDING" for row in actual)
    assert not wp7.EXPECTED_WP5_REVIEWED_IDS & {row["edge_id"] for row in actual}


def test_decisions_are_complete_bounded_and_image_referenced() -> None:
    selection = read_csv(REPO_ROOT / wp7.SELECTION_RELATIVE_PATH)
    payload, decisions = wp7.load_annotations(REPO_ROOT, selection)
    notes = wp7.load_review_notes(REPO_ROOT, selection)
    assert payload == wp7.annotation_payload_from_notes(notes, selection)
    assert len(decisions) == 100
    assert set(Counter(row["provisional_outcome"] for row in decisions)) <= set(
        wp7.ALLOWED_OUTCOMES
    )
    assert set(Counter(row["confidence"] for row in decisions)) <= set(
        wp7.CONFIDENCE_VALUES
    )
    assert all(row["evidence_refs"] == wp7.expected_evidence_refs(selected)
               for row, selected in zip(decisions, selection, strict=True))
    assert all(row["metadata_boundary"] == wp7.METADATA_BOUNDARY for row in decisions)
    assert all(row["evidence_boundary"] == wp7.EVIDENCE_BOUNDARY for row in decisions)


def test_atlas_has_20_decision_complete_pages_and_100_slots() -> None:
    layout = read_json(REPO_ROOT / wp7.LAYOUT_RELATIVE_PATH)
    assert layout["page_count"] == 20
    assert layout["pair_count"] == 100
    assert layout["all_headers_complete"] is True
    assert layout["all_text_complete"] is True
    assert layout["all_bounds_fit"] is True
    assert layout["all_bbox_context_rendered"] is True
    assert layout["all_decisions_recorded"] is True
    rows = [row for page in layout["pages"] for row in page["rows"]]
    assert len(rows) == 100
    assert [row["batch_position"] for row in rows] == list(range(1, 101))
    assert all(row["decision_recorded"] and row["all_bounds_fit"] for row in rows)
    for page in layout["pages"]:
        with Image.open(REPO_ROOT / page["path"]) as image:
            assert image.size == (1600, 2372)
            image.verify()


def test_manifest_hashes_sizes_and_pinned_sources_match() -> None:
    manifest = read_json(MANIFEST_PATH)
    pinned = {item_id: digest for item_id, _path, digest in wp7.source_contract(REPO_ROOT)}
    for record in [*manifest["sources"], *manifest["artifacts"]]:
        path = REPO_ROOT / record["path"]
        assert record["sha256"] == wp7.sha256_file(path)
        assert record["size"] == path.stat().st_size
        if record["id"] in pinned and pinned[record["id"]] is not None:
            assert record["sha256"] == pinned[record["id"]]


def test_report_keeps_wp5_and_gate0_fail_closed() -> None:
    report = (REPO_ROOT / wp7.REPORT_RELATIVE_PATH).read_text(encoding="utf-8")
    assert "Canonical WP5 remains unchanged at 3172 PENDING edges" in report
    assert "3072 edges remain unreviewed" in report
    assert "All 589 WP5 sequences remain PENDING" in report
    assert "D-02 remains PENDING" in report
    assert "Gate 0 remains BLOCKED" in report
    assert "training_authorized=false" in report
    wp7.validate_governance(REPO_ROOT)


def test_no_final_group_or_split_fields_are_created() -> None:
    forbidden = {"group_id", "final_group_id", "assigned_split", "approved_split"}
    selection = read_csv(REPO_ROOT / wp7.SELECTION_RELATIVE_PATH)
    annotations = read_json(REPO_ROOT / wp7.ANNOTATIONS_RELATIVE_PATH)
    assert not forbidden & set(selection[0])
    assert all(not forbidden & set(row) for row in annotations["decisions"])


@pytest.mark.parametrize("mutation", ["remove", "duplicate", "reorder", "extra"])
def test_manifest_rejects_artifact_roster_mutations(
    tmp_path: Path, mutation: str
) -> None:
    payload = read_json(MANIFEST_PATH)
    if mutation == "remove":
        payload["artifacts"].pop()
    elif mutation == "duplicate":
        payload["artifacts"].append(dict(payload["artifacts"][0]))
    elif mutation == "reorder":
        payload["artifacts"][0], payload["artifacts"][1] = (
            payload["artifacts"][1], payload["artifacts"][0]
        )
    else:
        payload["artifacts"].append(
            {
                "id": "unexpected",
                "path": "PROJECT_MEMORY.md",
                "sha256": wp7.sha256_file(REPO_ROOT / "PROJECT_MEMORY.md"),
                "size": (REPO_ROOT / "PROJECT_MEMORY.md").stat().st_size,
            }
        )
    payload["artifact_count"] = len(payload["artifacts"])
    payload["total_artifact_bytes"] = sum(
        row["size"] for row in payload["artifacts"]
    )
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


@pytest.mark.parametrize("attack", ["selection_reorder", "annotation_change", "layout_slot"])
def test_semantic_artifact_tamper_fails_after_rehash(
    tmp_path: Path, attack: str
) -> None:
    staged = stage_package(tmp_path)
    if attack == "selection_reorder":
        path = tmp_path / wp7.SELECTION_RELATIVE_PATH
        rows = read_csv(path)
        rows[0], rows[1] = rows[1], rows[0]
        wp7.write_csv(path, rows, wp7.SELECTION_FIELDS)
    elif attack == "annotation_change":
        path = tmp_path / wp7.ANNOTATIONS_RELATIVE_PATH
        payload = read_json(path)
        payload["decisions"][0]["confidence"] = "LOW"
        wp7.write_json(path, payload)
    else:
        path = tmp_path / wp7.LAYOUT_RELATIVE_PATH
        payload = read_json(path)
        payload["pages"][0]["rows"][0]["slot"] = 2
        wp7.write_json(path, payload)
    refresh_manifest_records(staged)
    result = wp7.verify_manifest(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert any("semantic verification failed" in error for error in result["errors"])


def test_review_note_tamper_fails_even_after_source_rehash(tmp_path: Path) -> None:
    staged = stage_package(tmp_path)
    path = tmp_path / wp7.REVIEW_NOTES_RELATIVE_PATH
    rows = read_csv(path)
    rows[0]["edge_id"] = rows[1]["edge_id"]
    wp7.write_csv(path, rows, wp7.REVIEW_NOTE_FIELDS)
    refresh_manifest_records(staged)
    result = wp7.verify_manifest(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert any("review-note identity/order mismatch" in error for error in result["errors"])


def test_path_escape_and_symlink_escape_are_rejected(tmp_path: Path) -> None:
    payload = read_json(MANIFEST_PATH)
    payload["sources"][0]["path"] = "../outside.json"
    result = verify_payload(tmp_path, payload, "path_escape.json")
    assert result["valid"] is False
    assert any("unsafe relative path" in error for error in result["errors"])

    stage_root = tmp_path / "stage"
    staged = stage_package(stage_root)
    selection = stage_root / wp7.SELECTION_RELATIVE_PATH
    outside = tmp_path / "outside.csv"
    outside.write_bytes(selection.read_bytes())
    selection.unlink()
    selection.symlink_to(outside)
    result = wp7.verify_manifest(staged, stage_root, RAW_ROOT)
    assert result["valid"] is False
    assert result["errors"]


def test_wp5_sources_and_raw_inventory_remain_preserved() -> None:
    for _item_id, path, pinned_hash in wp7.source_contract(REPO_ROOT)[:7]:
        assert pinned_hash is not None
        assert wp7.sha256_file(path) == pinned_hash
    proof = read_json(
        REPO_ROOT
        / "results/data_audit/DATASET01_052bc980a7206f8d/source_preservation_proof.json"
    )
    assert proof["unchanged"] is True
