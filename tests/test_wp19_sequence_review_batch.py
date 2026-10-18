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
SCRIPT_PATH = REPO_ROOT / "scripts/build_wp19_sequence_review_batch.py"
SPEC = importlib.util.spec_from_file_location("build_wp19_sequence_review_batch", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
api = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = api
SPEC.loader.exec_module(api)

RAW_ROOT = Path(
    "/Users/nguyentantai/Library/Mobile Documents/com~apple~CloudDocs/"
    "FALL 2026 KỲ 4/CPV301/Data/DATASET01/staging/052bc980a7206f8d/raw"
)
MANIFEST_PATH = REPO_ROOT / api.MANIFEST_RELATIVE_PATH

ATTACK_CLASSES = (
    "manifest_unknown_benign",
    "manifest_unknown_governance",
    "manifest_missing_field",
    "nested_source_unknown",
    "nested_artifact_missing",
    "roster_duplicate",
    "roster_order",
    "manifest_path_traversal",
    "selection_path_swap",
    "selection_symlink",
    "artifact_hash",
    "source_hash",
    "predecessor_prefix",
    "selection_semantic",
    "exclusion_semantic",
    "lineage_semantic",
    "annotation_decision_id",
    "same_count_swap",
    "coherent_rollback",
    "governance_tamper",
    "layout_semantic",
    "atlas_pixel",
)


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
    staged = tmp_path / api.MANIFEST_RELATIVE_PATH
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
                record["sha256"] = api.base.sha256_file(path)
                record["size"] = path.stat().st_size
    payload["total_artifact_bytes"] = sum(
        record["size"] for record in payload["artifacts"]
    )
    api.base.write_json(staged_manifest, payload)


def rebuild_staged_from_notes(stage_root: Path, notes: list[dict[str, str]]) -> Path:
    selection, inventory = api.derive_selection(stage_root, RAW_ROOT)
    annotations = api.annotation_payload_from_notes(notes, selection)
    decisions = annotations["decisions"]
    api.base.write_json(stage_root / api.ANNOTATIONS_RELATIVE_PATH, annotations)
    _paths, layout = api.render_atlas(
        selection,
        inventory,
        RAW_ROOT,
        stage_root / api.ASSETS_RELATIVE_PATH,
        decisions,
    )
    api.base.write_json(stage_root / api.LAYOUT_RELATIVE_PATH, layout)
    summary = api.summary_from_decisions(decisions)
    (stage_root / api.REPORT_RELATIVE_PATH).write_text(
        api.render_report(summary, annotations), encoding="utf-8"
    )
    manifest_path = stage_root / api.MANIFEST_RELATIVE_PATH
    api.base.write_json(manifest_path, api.build_manifest(stage_root))
    return manifest_path


def test_official_package_verifies_with_exact_contract() -> None:
    result = api.verify_manifest(MANIFEST_PATH, REPO_ROOT, RAW_ROOT)
    assert result == {
        "valid": True,
        "errors": [],
        "source_count": 25,
        "artifact_count": 107,
        "status": api.PACKAGE_STATUS,
    }
    manifest = read_json(MANIFEST_PATH)
    assert set(manifest) == api.MANIFEST_TOP_LEVEL_FIELDS
    assert all(
        set(record) == {"id", "path", "sha256", "size"}
        for record in [*manifest["sources"], *manifest["artifacts"]]
    )
    assert manifest["selection_count"] == 100
    assert manifest["member_lineage_count"] == 422
    assert manifest["pending_sequences_outside_overlay"] == 189
    assert manifest["exclusion_count"] == 1
    assert manifest["quarantined_stem_0248_selected"] is False
    assert manifest["quarantined_sequence_reviewed"] is False
    assert manifest["atlas_page_count"] == 100
    assert manifest["atlas_file_count"] == 101
    assert manifest["source_count"] == len(manifest["sources"]) == 25
    assert manifest["artifact_count"] == len(manifest["artifacts"]) == 107
    assert manifest["total_artifact_bytes"] == sum(
        (REPO_ROOT / row["path"]).stat().st_size for row in manifest["artifacts"]
    )


def test_selection_is_exact_next_nonoverlapping_canonical_batch() -> None:
    actual = read_csv(REPO_ROOT / api.SELECTION_RELATIVE_PATH)
    expected, _inventory = api.derive_selection(REPO_ROOT, RAW_ROOT)
    prior = [
        *read_csv(REPO_ROOT / "docs/review/generated/wp16_sequence_batch_a_selection.csv"),
        *read_csv(REPO_ROOT / "docs/review/generated/wp17_sequence_batch_b_selection.csv"),
    ]
    assert actual == expected
    assert [row["proxy_sequence_id"] for row in actual] == [
        f"proxy_sequence_{index:04d}" for index in range(302, 402)
    ]
    assert sum(int(row["member_count"]) for row in actual) == 422
    assert len({stem for row in actual for stem in row["members"].split(";")}) == 422
    assert not (
        {stem for row in actual for stem in row["members"].split(";")}
        & {stem for row in prior for stem in row["members"].split(";")}
    )
    assert all("0248" not in row["members"].split(";") for row in actual)
    assert read_csv(REPO_ROOT / api.EXCLUSIONS_RELATIVE_PATH) == api.derive_exclusions(
        REPO_ROOT
    )


def test_visual_decisions_and_lineage_are_complete() -> None:
    selection = read_csv(REPO_ROOT / api.SELECTION_RELATIVE_PATH)
    notes = api.load_review_notes(REPO_ROOT, selection)
    annotations = read_json(REPO_ROOT / api.ANNOTATIONS_RELATIVE_PATH)
    decisions = annotations["decisions"]
    lineage = read_csv(REPO_ROOT / api.LINEAGE_RELATIVE_PATH)
    assert annotations == api.annotation_payload_from_notes(notes, selection)
    assert len(decisions) == 100
    assert Counter(row["capture_sequence"] for row in decisions) == {
        "CONTINUOUS_CANDIDATE": 100
    }
    assert Counter(row["physical_sign_sequence"] for row in decisions) == {
        "MULTIPLE_SIGNS": 61,
        "SAME_PHYSICAL_SIGN_CANDIDATE": 39,
    }
    assert Counter(row["confidence"] for row in decisions) == {"HIGH": 100}
    assert lineage == api.derive_lineage(selection, api.load_inventory(REPO_ROOT), RAW_ROOT)
    assert len(lineage) == len({row["stem"] for row in lineage}) == 422
    assert sum(int(row["box_count"]) for row in lineage) == 824
    assert "0248" not in {row["stem"] for row in lineage}


def test_atlas_layout_and_governance_are_exact() -> None:
    atlas = REPO_ROOT / api.ASSETS_RELATIVE_PATH
    api.verify_exact_atlas_roster(atlas)
    layout = read_json(REPO_ROOT / api.LAYOUT_RELATIVE_PATH)
    assert layout["page_count"] == layout["sequence_count"] == 100
    assert layout["member_count"] == 422
    assert layout["page_sequence_counts"] == [1] * 100
    assert layout["all_text_complete"] is True
    assert layout["all_bounds_fit"] is True
    assert layout["all_bbox_context_rendered"] is True
    assert layout["all_decisions_recorded"] is True
    assert sum(len(page["members"]) for page in layout["pages"]) == 422
    for page in layout["pages"]:
        expected_height = 230 + ((page["member_count"] + 3) // 4) * 265 + 18
        with Image.open(REPO_ROOT / page["path"]) as image:
            assert image.size == (1600, expected_height)
            image.verify()
    api.validate_governance(REPO_ROOT)
    manifest = read_json(MANIFEST_PATH)
    assert manifest["gate0"] == "BLOCKED"
    assert manifest["d02_status"] == "PENDING"
    assert manifest["training_authorized"] is False
    forbidden = {"group_id", "final_group_id", "assigned_split", "approved_split"}
    assert all(not forbidden.intersection(row) for row in annotations_rows())


def annotations_rows() -> list[dict[str, Any]]:
    selection = read_csv(REPO_ROOT / api.SELECTION_RELATIVE_PATH)
    decisions = read_json(REPO_ROOT / api.ANNOTATIONS_RELATIVE_PATH)["decisions"]
    return [*selection, *decisions]


def test_attack_contract_has_exactly_22_unique_classes() -> None:
    assert len(ATTACK_CLASSES) == len(set(ATTACK_CLASSES)) == 22


@pytest.mark.parametrize("attack", ATTACK_CLASSES)
def test_fail_closed_attack_matrix(tmp_path: Path, attack: str) -> None:
    staged = stage_package(tmp_path)
    payload = read_json(staged)
    if attack == "manifest_unknown_benign":
        payload["qa_note"] = "unknown"
        api.base.write_json(staged, payload)
    elif attack == "manifest_unknown_governance":
        payload["training_authorized_override"] = True
        api.base.write_json(staged, payload)
    elif attack == "manifest_missing_field":
        payload.pop("artifact_count_semantics")
        api.base.write_json(staged, payload)
    elif attack == "nested_source_unknown":
        payload["sources"][0]["note"] = "unknown"
        api.base.write_json(staged, payload)
    elif attack == "nested_artifact_missing":
        payload["artifacts"][0].pop("size")
        api.base.write_json(staged, payload)
    elif attack == "roster_duplicate":
        payload["artifacts"].append(dict(payload["artifacts"][0]))
        payload["artifact_count"] += 1
        api.base.write_json(staged, payload)
    elif attack == "roster_order":
        payload["artifacts"][0], payload["artifacts"][1] = (
            payload["artifacts"][1],
            payload["artifacts"][0],
        )
        api.base.write_json(staged, payload)
    elif attack == "manifest_path_traversal":
        payload["sources"][0]["path"] = "../outside"
        api.base.write_json(staged, payload)
    elif attack == "selection_path_swap":
        target = next(row for row in payload["artifacts"] if row["id"] == "selection")
        target["path"] = api.EXCLUSIONS_RELATIVE_PATH
        api.base.write_json(staged, payload)
    elif attack == "selection_symlink":
        path = tmp_path / api.SELECTION_RELATIVE_PATH
        outside = tmp_path / "outside.csv"
        outside.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(outside)
    elif attack == "artifact_hash":
        payload["artifacts"][0]["sha256"] = "0" * 64
        api.base.write_json(staged, payload)
    elif attack == "source_hash":
        payload["sources"][0]["sha256"] = "0" * 64
        api.base.write_json(staged, payload)
    elif attack == "predecessor_prefix":
        path = tmp_path / "docs/review/generated/wp18_sequence_batch_c_selection.csv"
        rows = read_csv(path)
        rows[0]["canonical_review_order"] = "999"
        api.base.write_csv(path, rows, api.SELECTION_FIELDS)
        refresh_manifest_records(staged)
    elif attack == "selection_semantic":
        path = tmp_path / api.SELECTION_RELATIVE_PATH
        rows = read_csv(path)
        rows[0]["canonical_review_order"] = "999"
        api.base.write_csv(path, rows, api.SELECTION_FIELDS)
        refresh_manifest_records(staged)
    elif attack == "exclusion_semantic":
        path = tmp_path / api.EXCLUSIONS_RELATIVE_PATH
        rows = read_csv(path)
        rows[0]["overlay_reviewed"] = "True"
        api.base.write_csv(path, rows, api.EXCLUSION_FIELDS)
        refresh_manifest_records(staged)
    elif attack == "lineage_semantic":
        path = tmp_path / api.LINEAGE_RELATIVE_PATH
        rows = read_csv(path)
        rows[0]["box_count"] = str(int(rows[0]["box_count"]) + 1)
        api.base.write_csv(path, rows, api.LINEAGE_FIELDS)
        refresh_manifest_records(staged)
    elif attack == "annotation_decision_id":
        path = tmp_path / api.ANNOTATIONS_RELATIVE_PATH
        value = read_json(path)
        value["decisions"][0]["proxy_sequence_id"] = "proxy_sequence_9999"
        api.base.write_json(path, value)
        refresh_manifest_records(staged)
    elif attack in {"same_count_swap", "coherent_rollback"}:
        notes_path = tmp_path / api.REVIEW_NOTES_RELATIVE_PATH
        notes = read_csv(notes_path)
        if attack == "same_count_swap":
            same = next(
                row
                for row in notes
                if row["physical_sign_sequence"] == "SAME_PHYSICAL_SIGN_CANDIDATE"
            )
            multiple = next(
                row for row in notes if row["physical_sign_sequence"] == "MULTIPLE_SIGNS"
            )
            same["physical_sign_sequence"], multiple["physical_sign_sequence"] = (
                multiple["physical_sign_sequence"],
                same["physical_sign_sequence"],
            )
        else:
            notes[0]["capture_sequence"] = "UNRESOLVED"
            notes[0]["physical_sign_sequence"] = "UNRESOLVED"
            notes[0]["confidence"] = "LOW"
            notes[0]["rationale"] = "Forged coherent rollback."
        api.base.write_csv(notes_path, notes, api.NOTE_FIELDS)
        staged = rebuild_staged_from_notes(tmp_path, notes)
    elif attack == "governance_tamper":
        path = tmp_path / "docs/review/decision_status.json"
        value = read_json(path)
        value["gate0"] = "PASS"
        value["training_authorized"] = True
        api.base.write_json(path, value)
        refresh_manifest_records(staged)
    elif attack == "layout_semantic":
        path = tmp_path / api.LAYOUT_RELATIVE_PATH
        value = read_json(path)
        value["pages"][0]["members"][0]["bbox_overlay_rendered"] = False
        api.base.write_json(path, value)
        refresh_manifest_records(staged)
    else:
        path = tmp_path / api.ASSETS_RELATIVE_PATH / "page_001.jpg"
        with Image.open(path) as source:
            changed = source.convert("RGB")
        pixel = changed.getpixel((0, 0))
        changed.putpixel((0, 0), tuple(255 - channel for channel in pixel))
        changed.save(path, format="JPEG", quality=90, optimize=True, subsampling=1)
        refresh_manifest_records(staged)
    result = api.verify_manifest(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False, attack
    assert result["errors"], attack


def test_raw_sources_and_historical_pins_remain_preserved() -> None:
    for item_id, path, pinned_hash in api.source_contract(REPO_ROOT):
        if item_id == "wp19_builder":
            assert pinned_hash is None
            continue
        assert pinned_hash is not None
        assert api.base.sha256_file(path) == pinned_hash
    proof = read_json(
        REPO_ROOT
        / "results/data_audit/DATASET01_052bc980a7206f8d/source_preservation_proof.json"
    )
    assert proof["unchanged"] is True


def test_clean_room_rebuild_is_byte_deterministic(tmp_path: Path) -> None:
    clean_root = tmp_path / "clean"
    manifest = read_json(MANIFEST_PATH)
    for record in manifest["sources"]:
        source = REPO_ROOT / record["path"]
        target = clean_root / record["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    result = api.build(clean_root, RAW_ROOT)
    assert result["manifest_sha256"] == api.base.sha256_file(MANIFEST_PATH)
    rebuilt = read_json(clean_root / api.MANIFEST_RELATIVE_PATH)
    assert [
        (row["id"], row["sha256"], row["size"]) for row in rebuilt["artifacts"]
    ] == [
        (row["id"], row["sha256"], row["size"]) for row in manifest["artifacts"]
    ]
