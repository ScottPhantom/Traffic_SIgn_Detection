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
SCRIPT_PATH = REPO_ROOT / "scripts/build_wp16_sequence_review_batch.py"
SPEC = importlib.util.spec_from_file_location("build_wp16_sequence_review_batch", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
api = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = api
SPEC.loader.exec_module(api)

RAW_ROOT = Path(
    "/Users/nguyentantai/Library/Mobile Documents/com~apple~CloudDocs/"
    "FALL 2026 KỲ 4/CPV301/Data/DATASET01/staging/052bc980a7206f8d/raw"
)
MANIFEST_PATH = REPO_ROOT / api.MANIFEST_RELATIVE_PATH

ATLAS_ATTACKS = (
    "atlas_extra_member",
    "atlas_missing_member",
    "atlas_wrong_member",
    "atlas_directory_member",
    "atlas_member_symlink",
    "atlas_root_symlink",
)
BYTE_ATTACKS = ("atlas_pixel_rehash", "atlas_index_same_size_rehash")
LAYOUT_ATTACKS = (
    "layout_bounds",
    "layout_width",
    "layout_height",
    "layout_member_removed",
    "layout_bbox_flag",
    "layout_forged_context",
)
PATH_ATTACKS = ("selection_wrong_path", "manifest_path_traversal", "selection_symlink")
ROSTER_ATTACKS = ("manifest_roster_count",)
TOP_LEVEL_SCHEMA_ATTACKS = (
    "manifest_unknown_benign_top_level",
    "manifest_unknown_governance_top_level",
    "manifest_missing_top_level",
)
WP16_ATTACK_CLASSES = frozenset(
    (
        *ATLAS_ATTACKS,
        *BYTE_ATTACKS,
        *LAYOUT_ATTACKS,
        *PATH_ATTACKS,
        *ROSTER_ATTACKS,
        *TOP_LEVEL_SCHEMA_ATTACKS,
    )
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
        api.render_report(summary, annotations),
        encoding="utf-8",
    )
    manifest_path = stage_root / api.MANIFEST_RELATIVE_PATH
    api.base.write_json(manifest_path, api.build_manifest(stage_root))
    return manifest_path


def test_official_package_verifies_with_exact_contract() -> None:
    result = api.verify_manifest(MANIFEST_PATH, REPO_ROOT, RAW_ROOT)
    assert result == {
        "valid": True,
        "errors": [],
        "source_count": 19,
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
    assert manifest["member_lineage_count"] == 339
    assert manifest["canonical_sequence_count"] == 589
    assert manifest["canonical_sequence_pending_count"] == 589
    assert manifest["pending_sequences_outside_overlay"] == 489
    assert manifest["exclusion_count"] == 1
    assert manifest["quarantined_stem_0248_selected"] is False
    assert manifest["quarantined_sequence_reviewed"] is False
    assert manifest["excluded_quarantined_sequence_id"] == "proxy_sequence_0050"
    assert manifest["atlas_page_count"] == 100
    assert manifest["atlas_file_count"] == 101
    assert manifest["source_count"] == len(manifest["sources"]) == 19
    assert manifest["artifact_count"] == len(manifest["artifacts"]) == 107
    assert manifest["manifest_self_in_artifact_count"] is False
    assert manifest["artifact_count_semantics"] == "EXCLUDES_MANIFEST_FILE"
    assert api.MANIFEST_RELATIVE_PATH not in {
        row["path"] for row in manifest["artifacts"]
    }
    assert manifest["total_artifact_bytes"] == sum(
        (REPO_ROOT / row["path"]).stat().st_size for row in manifest["artifacts"]
    )


def test_selection_and_quarantine_exclusion_are_exact() -> None:
    actual = read_csv(REPO_ROOT / api.SELECTION_RELATIVE_PATH)
    expected, _inventory = api.derive_selection(REPO_ROOT, RAW_ROOT)
    expected_ids = [
        f"proxy_sequence_{index:04d}" for index in range(1, 102) if index != 50
    ]
    assert actual == expected
    assert [row["proxy_sequence_id"] for row in actual] == expected_ids
    assert [int(row["batch_position"]) for row in actual] == list(range(1, 101))
    assert [int(row["canonical_review_order"]) for row in actual] == [
        index for index in range(1, 102) if index != 50
    ]
    assert sum(int(row["member_count"]) for row in actual) == 339
    assert all(row["canonical_review_status"] == "PENDING" for row in actual)
    assert all("0248" not in row["members"].split(";") for row in actual)
    exclusions = read_csv(REPO_ROOT / api.EXCLUSIONS_RELATIVE_PATH)
    assert exclusions == api.derive_exclusions(REPO_ROOT)
    assert exclusions == [
        {
            "canonical_review_order": "50",
            "proxy_sequence_id": "proxy_sequence_0050",
            "review_status": "PENDING",
            "members": "0246;0247;0248;0249;0250;0251",
            "excluded_stem": "0248",
            "exclusion_reason": "CONTAINS_QUARANTINED_STEM_0248",
            "overlay_reviewed": "False",
            "evidence_boundary": api.EVIDENCE_BOUNDARY,
        }
    ]


def test_decisions_are_complete_conservative_and_exactly_bound() -> None:
    selection = read_csv(REPO_ROOT / api.SELECTION_RELATIVE_PATH)
    notes = api.load_review_notes(REPO_ROOT, selection)
    annotations = read_json(REPO_ROOT / api.ANNOTATIONS_RELATIVE_PATH)
    assert annotations == api.annotation_payload_from_notes(notes, selection)
    decisions = annotations["decisions"]
    assert len(decisions) == 100
    assert Counter(row["capture_sequence"] for row in decisions) == {
        "CONTINUOUS_CANDIDATE": 100
    }
    assert Counter(row["physical_sign_sequence"] for row in decisions) == {
        "MULTIPLE_SIGNS": 60,
        "SAME_PHYSICAL_SIGN_CANDIDATE": 40,
    }
    assert Counter(row["confidence"] for row in decisions) == {"HIGH": 100}
    assert [row["proxy_sequence_id"] for row in decisions] == [
        row["proxy_sequence_id"] for row in selection
    ]
    assert all(row["evidence_boundary"] == api.EVIDENCE_BOUNDARY for row in decisions)
    assert all(
        row["evidence_refs"] == [selected["wp16_atlas_page"], selected["wp3_contact_sheet"]]
        for row, selected in zip(decisions, selection, strict=True)
    )


def test_lineage_is_exact_hash_pinned_339_member_derivation() -> None:
    selection = read_csv(REPO_ROOT / api.SELECTION_RELATIVE_PATH)
    inventory = api.load_inventory(REPO_ROOT)
    lineage = read_csv(REPO_ROOT / api.LINEAGE_RELATIVE_PATH)
    assert lineage == api.derive_lineage(selection, inventory, RAW_ROOT)
    assert len(lineage) == len({row["stem"] for row in lineage}) == 339
    assert sum(int(row["box_count"]) for row in lineage) == 574
    assert "0248" not in {row["stem"] for row in lineage}
    assert all(row["decode_verified"] == "True" for row in lineage)
    assert Counter(row["proxy_sequence_id"] for row in lineage) == {
        row["proxy_sequence_id"]: int(row["member_count"]) for row in selection
    }


def test_atlas_and_layout_cover_every_sequence_and_member() -> None:
    atlas_dir = REPO_ROOT / api.ASSETS_RELATIVE_PATH
    api.verify_exact_atlas_roster(atlas_dir)
    assert len(list(atlas_dir.iterdir())) == 101
    layout = read_json(REPO_ROOT / api.LAYOUT_RELATIVE_PATH)
    assert layout["page_count"] == layout["sequence_count"] == 100
    assert layout["member_count"] == 339
    assert layout["page_sequence_counts"] == [1] * 100
    assert layout["all_headers_complete"] is True
    assert layout["all_text_complete"] is True
    assert layout["all_bounds_fit"] is True
    assert layout["all_bbox_context_rendered"] is True
    assert layout["all_decisions_recorded"] is True
    assert [page["page"] for page in layout["pages"]] == list(range(1, 101))
    assert sum(len(page["members"]) for page in layout["pages"]) == 339
    for page in layout["pages"]:
        expected_height = 230 + ((page["member_count"] + 3) // 4) * 265 + 18
        assert page["width"] == 1600
        assert page["height"] == expected_height
        assert page["decision_recorded"] is True
        assert all(member["bbox_overlay_rendered"] for member in page["members"])
        with Image.open(REPO_ROOT / page["path"]) as image:
            assert image.size == (1600, expected_height)
            image.verify()


def test_manifest_hashes_pins_report_and_governance() -> None:
    manifest = read_json(MANIFEST_PATH)
    pinned = {
        item_id: digest for item_id, _path, digest in api.source_contract(REPO_ROOT)
    }
    for record in [*manifest["sources"], *manifest["artifacts"]]:
        path = REPO_ROOT / record["path"]
        assert record["sha256"] == api.base.sha256_file(path)
        assert record["size"] == path.stat().st_size
        if record["id"] in pinned and pinned[record["id"]] is not None:
            assert record["sha256"] == pinned[record["id"]]
    report = (REPO_ROOT / api.REPORT_RELATIVE_PATH).read_text(encoding="utf-8")
    assert api.EXPECTED_REVIEW_NOTES_SHA256 in report
    assert "All 100 sequences and all 339 member frames were directly inspected" in report
    assert "Canonical WP5 remains unchanged at 589 PENDING sequences" in report
    assert "489 remain outside the overlay" in report
    assert "D-02 remains PENDING" in report
    assert "Gate 0 remains BLOCKED" in report
    assert "training_authorized=false" in report
    api.validate_governance(REPO_ROOT)
    forbidden = {"group_id", "final_group_id", "assigned_split", "approved_split"}
    selection = read_csv(REPO_ROOT / api.SELECTION_RELATIVE_PATH)
    annotations = read_json(REPO_ROOT / api.ANNOTATIONS_RELATIVE_PATH)
    assert all(not forbidden.intersection(row) for row in selection)
    assert all(not forbidden.intersection(row) for row in annotations["decisions"])


def test_attack_contract_has_exactly_21_unique_classes() -> None:
    assert len(WP16_ATTACK_CLASSES) == 21


@pytest.mark.parametrize("attack", ATLAS_ATTACKS)
def test_atlas_roster_attacks_fail(tmp_path: Path, attack: str) -> None:
    staged = stage_package(tmp_path)
    atlas_dir = tmp_path / api.ASSETS_RELATIVE_PATH
    page = atlas_dir / "page_001.jpg"
    if attack == "atlas_extra_member":
        (atlas_dir / "unexpected.txt").write_text("unexpected", encoding="utf-8")
    elif attack == "atlas_missing_member":
        page.unlink()
    elif attack == "atlas_wrong_member":
        page.rename(atlas_dir / "page_000.jpg")
    elif attack == "atlas_directory_member":
        page.unlink()
        page.mkdir()
    elif attack == "atlas_member_symlink":
        page.unlink()
        page.symlink_to("page_002.jpg")
    else:
        copied = tmp_path / "copied_atlas"
        shutil.copytree(atlas_dir, copied)
        shutil.rmtree(atlas_dir)
        atlas_dir.symlink_to(copied, target_is_directory=True)
    result = api.verify_manifest(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert result["errors"]


@pytest.mark.parametrize("attack", BYTE_ATTACKS)
def test_atlas_byte_attacks_fail_after_rehash(tmp_path: Path, attack: str) -> None:
    staged = stage_package(tmp_path)
    if attack == "atlas_pixel_rehash":
        path = tmp_path / api.ASSETS_RELATIVE_PATH / "page_001.jpg"
        with Image.open(path) as source:
            changed = source.convert("RGB")
        pixel = changed.getpixel((0, 0))
        changed.putpixel((0, 0), tuple(255 - channel for channel in pixel))
        changed.save(path, format="JPEG", quality=90, optimize=True, subsampling=1)
    else:
        path = tmp_path / api.ASSETS_RELATIVE_PATH / "index.html"
        content = path.read_text(encoding="utf-8")
        assert "<h1>" in content
        path.write_text(content.replace("<h1>", "<h2>", 1), encoding="utf-8")
        assert path.stat().st_size == (
            REPO_ROOT / api.ASSETS_RELATIVE_PATH / "index.html"
        ).stat().st_size
    refresh_manifest_records(staged)
    result = api.verify_manifest(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert any("atlas bytes differ from regeneration" in error for error in result["errors"])


@pytest.mark.parametrize("attack", LAYOUT_ATTACKS)
def test_layout_attacks_fail_after_rehash(tmp_path: Path, attack: str) -> None:
    staged = stage_package(tmp_path)
    path = tmp_path / api.LAYOUT_RELATIVE_PATH
    payload = read_json(path)
    page = payload["pages"][0]
    if attack == "layout_bounds":
        page["header_text_bounds"][0][2] += 1
    elif attack == "layout_width":
        page["width"] += 1
    elif attack == "layout_height":
        page["height"] -= 1
    elif attack == "layout_member_removed":
        page["members"].pop()
    elif attack == "layout_bbox_flag":
        page["members"][0]["bbox_overlay_rendered"] = False
    else:
        page["members"][0]["stem"] = "forged"
    api.base.write_json(path, payload)
    refresh_manifest_records(staged)
    result = api.verify_manifest(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert any("semantic verification failed" in error for error in result["errors"])


@pytest.mark.parametrize("attack", PATH_ATTACKS)
def test_path_attacks_fail(tmp_path: Path, attack: str) -> None:
    if attack == "manifest_path_traversal":
        payload = read_json(MANIFEST_PATH)
        payload["sources"][0]["path"] = "../outside.json"
        path = tmp_path / "traversal.json"
        api.base.write_json(path, payload)
        result = api.verify_manifest(path, REPO_ROOT, RAW_ROOT)
    else:
        staged = stage_package(tmp_path)
        if attack == "selection_wrong_path":
            payload = read_json(staged)
            target = next(row for row in payload["artifacts"] if row["id"] == "selection")
            target["path"] = api.EXCLUSIONS_RELATIVE_PATH
            api.base.write_json(staged, payload)
        else:
            selection = tmp_path / api.SELECTION_RELATIVE_PATH
            outside = tmp_path / "outside_selection.csv"
            outside.write_bytes(selection.read_bytes())
            selection.unlink()
            selection.symlink_to(outside)
        result = api.verify_manifest(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert result["errors"]


def test_manifest_roster_count_attack_fails(tmp_path: Path) -> None:
    staged = stage_package(tmp_path)
    payload = read_json(staged)
    payload["artifacts"].append(dict(payload["artifacts"][0]))
    payload["artifact_count"] += 1
    api.base.write_json(staged, payload)
    result = api.verify_manifest(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert any("artifact" in error for error in result["errors"])


@pytest.mark.parametrize("attack", TOP_LEVEL_SCHEMA_ATTACKS)
def test_manifest_top_level_schema_attacks_fail(tmp_path: Path, attack: str) -> None:
    staged = stage_package(tmp_path)
    payload = read_json(staged)
    if attack == "manifest_unknown_benign_top_level":
        payload["qa_note"] = "benign unknown field"
    elif attack == "manifest_unknown_governance_top_level":
        payload["training_authorized_override"] = True
    else:
        payload.pop("artifact_count_semantics")
    api.base.write_json(staged, payload)
    result = api.verify_manifest(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert any(
        "manifest top-level fields differ from WP16 exact schema" in error
        for error in result["errors"]
    )


def test_coherent_review_rollback_is_rejected_by_pinned_note_source(tmp_path: Path) -> None:
    stage_package(tmp_path)
    notes_path = tmp_path / api.REVIEW_NOTES_RELATIVE_PATH
    notes = read_csv(notes_path)
    notes[0]["capture_sequence"] = "UNRESOLVED"
    notes[0]["physical_sign_sequence"] = "UNRESOLVED"
    notes[0]["confidence"] = "LOW"
    notes[0]["rationale"] = "Forged coherent rollback."
    api.base.write_csv(notes_path, notes, api.NOTE_FIELDS)
    staged = rebuild_staged_from_notes(tmp_path, notes)
    result = api.verify_manifest(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert any(
        "pinned WP16 source mismatch: wp16_review_notes" in error
        for error in result["errors"]
    )


def test_count_preserving_decision_id_swap_is_rejected(tmp_path: Path) -> None:
    stage_package(tmp_path)
    notes_path = tmp_path / api.REVIEW_NOTES_RELATIVE_PATH
    notes = read_csv(notes_path)
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
    assert Counter(row["physical_sign_sequence"] for row in notes) == {
        "MULTIPLE_SIGNS": 60,
        "SAME_PHYSICAL_SIGN_CANDIDATE": 40,
    }
    api.base.write_csv(notes_path, notes, api.NOTE_FIELDS)
    staged = rebuild_staged_from_notes(tmp_path, notes)
    result = api.verify_manifest(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert any(
        "pinned WP16 source mismatch: wp16_review_notes" in error
        for error in result["errors"]
    )


def test_raw_sources_and_historical_pins_remain_preserved() -> None:
    for item_id, path, pinned_hash in api.source_contract(REPO_ROOT):
        if item_id == "wp16_builder":
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
