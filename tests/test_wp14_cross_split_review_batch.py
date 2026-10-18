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
SCRIPT_PATH = REPO_ROOT / "scripts/build_wp14_cross_split_review_batch.py"
SPEC = importlib.util.spec_from_file_location(
    "build_wp14_cross_split_review_batch", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
wp14 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp14
SPEC.loader.exec_module(wp14)
wp14.configure_base()
api = wp14.base

RAW_ROOT = Path(
    "/Users/nguyentantai/Library/Mobile Documents/com~apple~CloudDocs/"
    "FALL 2026 KỲ 4/CPV301/Data/DATASET01/staging/052bc980a7206f8d/raw"
)
MANIFEST_PATH = REPO_ROOT / api.MANIFEST_RELATIVE_PATH

ATLAS_ATTACKS = (
    "extra_page",
    "missing_page",
    "renamed_page",
    "directory_member",
    "page_symlink",
    "atlas_root_symlink",
)
LAYOUT_ATTACKS = (
    "left_bounds",
    "right_bounds",
    "text_bounds",
    "page_width",
    "page_height",
    "bbox_placement",
    "text_context",
    "page_coverage_geometry",
)
BYTE_ATTACKS = ("page_pixel", "index_text")
PATH_ATTACKS = ("manifest_path_traversal", "selection_symlink")
WP14_ATTACK_CLASSES = frozenset(
    (*ATLAS_ATTACKS, *LAYOUT_ATTACKS, *BYTE_ATTACKS, *PATH_ATTACKS)
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
                record["sha256"] = api.sha256_file(path)
                record["size"] = path.stat().st_size
    payload["total_artifact_bytes"] = sum(
        record["size"] for record in payload["artifacts"]
    )
    api.write_json(staged_manifest, payload)


def verify_payload(tmp_path: Path, payload: Any, name: str) -> dict[str, Any]:
    path = tmp_path / name
    api.write_json(path, payload)
    return api.verify_manifest(path, REPO_ROOT, RAW_ROOT)


def test_official_package_verifies_with_exact_rosters() -> None:
    result = api.verify_manifest(MANIFEST_PATH, REPO_ROOT, RAW_ROOT)
    assert result == {
        "valid": True,
        "errors": [],
        "source_count": 20,
        "artifact_count": 56,
        "status": api.PACKAGE_STATUS,
    }
    manifest = read_json(MANIFEST_PATH)
    assert manifest["source_count"] == len(manifest["sources"]) == 20
    assert manifest["artifact_count"] == len(manifest["artifacts"]) == 56
    assert manifest["selection_count"] == 250
    assert manifest["lineage_record_count"] == 500
    assert manifest["selected_endpoint_box_count"] == 1413
    assert manifest["quarantined_stem_0248_selected"] is False
    assert manifest["atlas_page_count"] == 50
    assert manifest["manifest_self_in_artifact_count"] is False
    assert manifest["artifact_count_semantics"] == "EXCLUDES_MANIFEST_FILE"
    assert api.MANIFEST_RELATIVE_PATH not in {
        row["path"] for row in manifest["artifacts"]
    }
    assert manifest["total_artifact_bytes"] == sum(
        (REPO_ROOT / row["path"]).stat().st_size for row in manifest["artifacts"]
    )
    assert manifest["package"] == api.BATCH_ID
    assert api.sha256_file(
        REPO_ROOT / api.REVIEW_NOTES_RELATIVE_PATH
    ) == api.EXPECTED_REVIEW_NOTES_SHA256


def test_selection_is_exact_next_250_pending_cross_split_rows() -> None:
    actual = read_csv(REPO_ROOT / api.SELECTION_RELATIVE_PATH)
    expected, _inventory = api.derive_selection(REPO_ROOT, RAW_ROOT)
    assert actual == expected
    assert len(actual) == len({row["edge_id"] for row in actual}) == 250
    assert actual[0]["edge_id"] == "edge_001894"
    assert actual[-1]["edge_id"] == "edge_002664"
    assert [int(row["wp5_review_order"]) for row in actual] == list(range(606, 856))
    assert all(row["cross_split"] == "True" for row in actual)
    assert all(row["wp5_review_status"] == "PENDING" for row in actual)
    assert not api.EXPECTED_WP5_REVIEWED_IDS & {row["edge_id"] for row in actual}
    assert all(
        "0248" not in {row["left_stem"], row["right_stem"]} for row in actual
    )
    batch_a_ids = {
        row["edge_id"]
        for row in read_csv(REPO_ROOT / "docs/review/generated/wp7_batch_a_selection.csv")
    }
    assert len(batch_a_ids) == 100
    assert not batch_a_ids & {row["edge_id"] for row in actual}
    batch_b_ids = {
        row["edge_id"]
        for row in read_csv(REPO_ROOT / "docs/review/generated/wp12_batch_b_selection.csv")
    }
    assert len(batch_b_ids) == 250
    assert not batch_b_ids & {row["edge_id"] for row in actual}
    batch_c_ids = {
        row["edge_id"]
        for row in read_csv(REPO_ROOT / "docs/review/generated/wp13_batch_c_selection.csv")
    }
    assert len(batch_c_ids) == 250
    actual_ids = {row["edge_id"] for row in actual}
    assert not batch_c_ids & actual_ids
    assert not batch_a_ids & batch_b_ids
    assert not batch_a_ids & batch_c_ids
    assert not batch_b_ids & batch_c_ids


def test_decisions_are_complete_bounded_and_image_referenced() -> None:
    selection = read_csv(REPO_ROOT / api.SELECTION_RELATIVE_PATH)
    payload, decisions = api.load_annotations(REPO_ROOT, selection)
    notes = api.load_review_notes(REPO_ROOT, selection)
    assert payload == api.annotation_payload_from_notes(notes, selection)
    assert len(decisions) == 250
    assert set(Counter(row["provisional_outcome"] for row in decisions)) <= set(
        api.ALLOWED_OUTCOMES
    )
    assert set(Counter(row["confidence"] for row in decisions)) <= set(
        api.CONFIDENCE_VALUES
    )
    assert all(row["evidence_refs"] == api.expected_evidence_refs(selected)
               for row, selected in zip(decisions, selection, strict=True))
    assert all(row["metadata_boundary"] == api.METADATA_BOUNDARY for row in decisions)
    assert all(row["evidence_boundary"] == api.EVIDENCE_BOUNDARY for row in decisions)
    assert Counter(row["capture_hypothesis"] for row in decisions) == {
        "SAME_CAPTURE_CANDIDATE": 246,
        "NOT_RELATED": 4,
    }
    assert Counter(row["physical_sign_hypothesis"] for row in decisions) == {
        "SAME_PHYSICAL_SIGN_CANDIDATE": 238,
        "NOT_RELATED": 12,
    }
    assert Counter(row["confidence"] for row in decisions) == {"HIGH": 250}
    assert {
        row["edge_id"]
        for row in decisions
        if row["capture_hypothesis"] == "NOT_RELATED"
    } == wp14.EXPECTED_CAPTURE_NOT_RELATED_IDS
    assert {
        row["edge_id"]
        for row in decisions
        if row["physical_sign_hypothesis"] == "NOT_RELATED"
    } == wp14.EXPECTED_PHYSICAL_SIGN_NOT_RELATED_IDS
    assert {
        row["edge_id"]
        for row in decisions
        if row["capture_hypothesis"] == "UNRESOLVED"
    } == set()
    assert {
        row["edge_id"]
        for row in decisions
        if row["physical_sign_hypothesis"] == "UNRESOLVED"
    } == set()
    edge_002262 = next(row for row in decisions if row["edge_id"] == "edge_002262")
    assert edge_002262["capture_hypothesis"] == "SAME_CAPTURE_CANDIDATE"
    assert edge_002262["physical_sign_hypothesis"] == "NOT_RELATED"


def test_atlas_has_50_decision_complete_pages_and_250_slots() -> None:
    atlas_dir = REPO_ROOT / api.ASSETS_RELATIVE_PATH
    api.verify_exact_atlas_roster(atlas_dir)
    assert sorted(path.name for path in atlas_dir.iterdir()) == sorted(
        api.expected_atlas_names()
    )
    layout = read_json(REPO_ROOT / api.LAYOUT_RELATIVE_PATH)
    assert layout["page_count"] == 50
    assert layout["pair_count"] == 250
    assert layout["pairs_per_page"] == 5
    assert layout["all_headers_complete"] is True
    assert layout["all_text_complete"] is True
    assert layout["all_bounds_fit"] is True
    assert layout["all_bbox_context_rendered"] is True
    assert layout["all_decisions_recorded"] is True
    rows = [row for page in layout["pages"] for row in page["rows"]]
    assert len(rows) == 250
    assert [row["batch_position"] for row in rows] == list(range(1, 251))
    assert all(row["decision_recorded"] and row["all_bounds_fit"] for row in rows)
    for page in layout["pages"]:
        assert page["width"] == 1600
        assert page["height"] == 2372
        assert page["row_count"] == 5
        for row in page["rows"]:
            assert row["left_bounds"][0] == 18
            assert row["left_bounds"][2] - row["left_bounds"][0] == 600
            assert row["left_bounds"][3] - row["left_bounds"][1] == 337
            assert row["right_bounds"][0] == 628
            assert row["right_bounds"][2] - row["right_bounds"][0] == 600
            assert row["right_bounds"][3] - row["right_bounds"][1] == 337
            assert row["text_bounds"][0] == 1245
            assert row["text_bounds"][2] == 1580
            assert row["bbox_overlay_rendered"] is True
            assert row["text_complete"] is True
        with Image.open(REPO_ROOT / page["path"]) as image:
            assert image.size == (1600, 2372)
            image.verify()


def test_lineage_has_exactly_two_hash_pinned_endpoints_per_pair() -> None:
    selection = read_csv(REPO_ROOT / api.SELECTION_RELATIVE_PATH)
    lineage = read_csv(REPO_ROOT / api.LINEAGE_RELATIVE_PATH)
    inventory_path = (
        REPO_ROOT
        / "results/data_audit/DATASET01_052bc980a7206f8d/image_inventory.csv"
    )
    assert len(lineage) == 500
    assert lineage == api.derive_lineage(
        selection,
        {row["stem"]: row for row in read_csv(inventory_path)},
        RAW_ROOT,
    )
    assert Counter(row["edge_id"] for row in lineage) == {
        row["edge_id"]: 2 for row in selection
    }
    assert all(row["side"] in {"LEFT", "RIGHT"} for row in lineage)
    inventory = {row["stem"]: row for row in read_csv(inventory_path)}
    assert sum(int(inventory[row["stem"]]["box_count"]) for row in lineage) == 1413
    assert all(row["stem"] != "0248" for row in lineage)


def test_manifest_hashes_sizes_and_pinned_sources_match() -> None:
    manifest = read_json(MANIFEST_PATH)
    pinned = {item_id: digest for item_id, _path, digest in api.source_contract(REPO_ROOT)}
    for record in [*manifest["sources"], *manifest["artifacts"]]:
        path = REPO_ROOT / record["path"]
        assert record["sha256"] == api.sha256_file(path)
        assert record["size"] == path.stat().st_size
        if record["id"] in pinned and pinned[record["id"]] is not None:
            assert record["sha256"] == pinned[record["id"]]


def test_report_keeps_wp5_and_gate0_fail_closed() -> None:
    report = (REPO_ROOT / api.REPORT_RELATIVE_PATH).read_text(encoding="utf-8")
    assert "# M0-WP14" in report
    assert api.EXPECTED_REVIEW_NOTES_SHA256 in report
    assert "AWAITING_QA" in report
    assert "directly inspected in the dedicated 50-page WP14 atlas" in report
    assert "Canonical WP5 remains unchanged at 3172 PENDING edges" in report
    assert "2322 pending edges" in report
    assert "176 cross-split edges" in report
    assert "All 589 WP5 sequences remain PENDING" in report
    assert "D-02 remains PENDING" in report
    assert "Gate 0 remains BLOCKED" in report
    assert "training_authorized=false" in report
    api.validate_governance(REPO_ROOT)


def test_no_final_group_or_split_fields_are_created() -> None:
    forbidden = {"group_id", "final_group_id", "assigned_split", "approved_split"}
    selection = read_csv(REPO_ROOT / api.SELECTION_RELATIVE_PATH)
    annotations = read_json(REPO_ROOT / api.ANNOTATIONS_RELATIVE_PATH)
    assert not forbidden & set(selection[0])
    assert all(not forbidden & set(row) for row in annotations["decisions"])


@pytest.mark.parametrize("collection", ["sources", "artifacts"])
@pytest.mark.parametrize("mutation", ["remove", "duplicate", "reorder", "extra"])
def test_manifest_rejects_roster_mutations(
    tmp_path: Path, collection: str, mutation: str
) -> None:
    payload = read_json(MANIFEST_PATH)
    if mutation == "remove":
        payload[collection].pop()
    elif mutation == "duplicate":
        payload[collection].append(dict(payload[collection][0]))
    elif mutation == "reorder":
        payload[collection][0], payload[collection][1] = (
            payload[collection][1], payload[collection][0]
        )
    else:
        payload[collection].append(
            {
                "id": "unexpected",
                "path": "PROJECT_MEMORY.md",
                "sha256": api.sha256_file(REPO_ROOT / "PROJECT_MEMORY.md"),
                "size": (REPO_ROOT / "PROJECT_MEMORY.md").stat().st_size,
            }
        )
    payload[f"{collection[:-1]}_count"] = len(payload[collection])
    payload["total_artifact_bytes"] = sum(
        row["size"] for row in payload["artifacts"]
    )
    result = verify_payload(tmp_path, payload, f"{mutation}.json")
    assert result["valid"] is False
    assert any(collection in error for error in result["errors"])


@pytest.mark.parametrize(
    "field",
    [
        "selection_count",
        "lineage_record_count",
        "selected_endpoint_box_count",
        "atlas_page_count",
        "source_count",
        "artifact_count",
        "total_artifact_bytes",
    ],
)
def test_manifest_rejects_forged_counts(tmp_path: Path, field: str) -> None:
    payload = read_json(MANIFEST_PATH)
    payload[field] += 1
    result = verify_payload(tmp_path, payload, f"forged_{field}.json")
    assert result["valid"] is False
    assert any(field in error for error in result["errors"])


def test_wp12_attack_contract_has_exactly_18_unique_classes() -> None:
    assert len(WP14_ATTACK_CLASSES) == 18


@pytest.mark.parametrize("attack", ATLAS_ATTACKS)
def test_atlas_directory_rejects_non_exact_or_non_regular_roster(
    tmp_path: Path, attack: str
) -> None:
    staged = stage_package(tmp_path)
    atlas_dir = tmp_path / api.ASSETS_RELATIVE_PATH
    page = atlas_dir / "page_001.jpg"
    if attack == "extra_page":
        (atlas_dir / "unexpected.txt").write_text("unexpected", encoding="utf-8")
    elif attack == "missing_page":
        page.unlink()
    elif attack == "renamed_page":
        page.rename(atlas_dir / "renamed_page_001.jpg")
    elif attack == "directory_member":
        page.unlink()
        page.mkdir()
    elif attack == "page_symlink":
        target = atlas_dir / "page_002.jpg"
        page.unlink()
        page.symlink_to(target.name)
    else:
        copied = tmp_path / "copied_atlas"
        shutil.copytree(atlas_dir, copied)
        shutil.rmtree(atlas_dir)
        atlas_dir.symlink_to(copied, target_is_directory=True)
    result = api.verify_manifest(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert result["errors"]


@pytest.mark.parametrize("attack", LAYOUT_ATTACKS)
def test_layout_semantics_fail_after_coherent_rehash(
    tmp_path: Path, attack: str
) -> None:
    staged = stage_package(tmp_path)
    path = tmp_path / api.LAYOUT_RELATIVE_PATH
    payload = read_json(path)
    row = payload["pages"][0]["rows"][0]
    if attack == "left_bounds":
        row["left_bounds"][2] += 1
    elif attack == "right_bounds":
        row["right_bounds"][0] += 1
    elif attack == "text_bounds":
        row["text_bounds"][3] -= 1
    elif attack == "page_width":
        payload["pages"][0]["width"] += 1
    elif attack == "page_height":
        payload["pages"][0]["height"] -= 1
    elif attack == "bbox_placement":
        row["bbox_overlay_rendered"] = False
    elif attack == "text_context":
        row["left_stem"] = "forged-context"
    else:
        payload["pages"][0]["rows"].pop()
    api.write_json(path, payload)
    refresh_manifest_records(staged)
    result = api.verify_manifest(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert any("semantic verification failed" in error for error in result["errors"])


@pytest.mark.parametrize("attack", BYTE_ATTACKS)
def test_atlas_bytes_fail_after_coherent_rehash(tmp_path: Path, attack: str) -> None:
    staged = stage_package(tmp_path)
    if attack == "page_pixel":
        path = tmp_path / api.ASSETS_RELATIVE_PATH / "page_001.jpg"
        with Image.open(path) as image:
            mutated = image.convert("RGB")
        pixel = mutated.getpixel((0, 0))
        mutated.putpixel((0, 0), tuple(255 - channel for channel in pixel))
        mutated.save(path, format="JPEG", quality=90, optimize=True, subsampling=1)
    else:
        path = tmp_path / api.ASSETS_RELATIVE_PATH / "index.html"
        path.write_text(
            path.read_text(encoding="utf-8") + "<!-- forged -->\n",
            encoding="utf-8",
        )
    refresh_manifest_records(staged)
    result = api.verify_manifest(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert any(
        "atlas bytes differ from deterministic regeneration" in error
        for error in result["errors"]
    )


@pytest.mark.parametrize(
    "attack",
    [
        "selection_reorder",
        "selection_duplicate",
        "annotation_change",
        "annotation_promotion",
        "annotation_evidence",
        "annotation_reviewer",
        "annotation_timestamp",
        "lineage_hash",
        "lineage_reorder",
        "layout_slot",
        "manifest_governance",
    ],
)
def test_semantic_artifact_tamper_fails_after_rehash(
    tmp_path: Path, attack: str
) -> None:
    staged = stage_package(tmp_path)
    if attack == "selection_reorder":
        path = tmp_path / api.SELECTION_RELATIVE_PATH
        rows = read_csv(path)
        rows[0], rows[1] = rows[1], rows[0]
        api.write_csv(path, rows, api.SELECTION_FIELDS)
    elif attack == "selection_duplicate":
        path = tmp_path / api.SELECTION_RELATIVE_PATH
        rows = read_csv(path)
        rows[1] = dict(rows[0])
        api.write_csv(path, rows, api.SELECTION_FIELDS)
    elif attack == "annotation_change":
        path = tmp_path / api.ANNOTATIONS_RELATIVE_PATH
        payload = read_json(path)
        payload["decisions"][0]["confidence"] = "LOW"
        api.write_json(path, payload)
    elif attack == "annotation_promotion":
        path = tmp_path / api.ANNOTATIONS_RELATIVE_PATH
        payload = read_json(path)
        payload["decisions"][0]["final_group_id"] = "forbidden"
        api.write_json(path, payload)
    elif attack == "annotation_evidence":
        path = tmp_path / api.ANNOTATIONS_RELATIVE_PATH
        payload = read_json(path)
        payload["decisions"][0]["evidence_refs"][0] = "forged"
        api.write_json(path, payload)
    elif attack == "annotation_reviewer":
        path = tmp_path / api.ANNOTATIONS_RELATIVE_PATH
        payload = read_json(path)
        payload["reviewer"] = "forged"
        api.write_json(path, payload)
    elif attack == "annotation_timestamp":
        path = tmp_path / api.ANNOTATIONS_RELATIVE_PATH
        payload = read_json(path)
        payload["reviewed_at"] = "2026-10-11T18:00:00"
        api.write_json(path, payload)
    elif attack == "lineage_hash":
        path = tmp_path / api.LINEAGE_RELATIVE_PATH
        rows = read_csv(path)
        rows[0]["image_sha256"] = "0" * 64
        api.write_csv(path, rows, api.LINEAGE_FIELDS)
    elif attack == "lineage_reorder":
        path = tmp_path / api.LINEAGE_RELATIVE_PATH
        rows = read_csv(path)
        rows[0], rows[1] = rows[1], rows[0]
        api.write_csv(path, rows, api.LINEAGE_FIELDS)
    elif attack == "manifest_governance":
        payload = read_json(staged)
        payload["training_authorized"] = True
        api.write_json(staged, payload)
    else:
        path = tmp_path / api.LAYOUT_RELATIVE_PATH
        payload = read_json(path)
        payload["pages"][0]["rows"][0]["slot"] = 2
        api.write_json(path, payload)
    if attack != "manifest_governance":
        refresh_manifest_records(staged)
    result = api.verify_manifest(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    if attack == "manifest_governance":
        assert any("training_authorized" in error for error in result["errors"])
    else:
        assert any("semantic verification failed" in error for error in result["errors"])


def test_review_note_tamper_fails_even_after_source_rehash(tmp_path: Path) -> None:
    staged = stage_package(tmp_path)
    path = tmp_path / api.REVIEW_NOTES_RELATIVE_PATH
    rows = read_csv(path)
    rows[0]["edge_id"] = rows[1]["edge_id"]
    api.write_csv(path, rows, api.REVIEW_NOTE_FIELDS)
    refresh_manifest_records(staged)
    result = api.verify_manifest(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert any("pinned source hash mismatch" in error for error in result["errors"])


def test_coherent_edge_002262_review_rollback_is_rejected_by_source_anchor(
    tmp_path: Path,
) -> None:
    staged = stage_package(tmp_path)
    notes_path = tmp_path / api.REVIEW_NOTES_RELATIVE_PATH
    notes = read_csv(notes_path)
    target = next(row for row in notes if row["edge_id"] == "edge_002262")
    target["provisional_outcome"] = "SAME_CAPTURE_CANDIDATE"
    target["capture_hypothesis"] = "SAME_CAPTURE_CANDIDATE"
    target["physical_sign_hypothesis"] = "SAME_PHYSICAL_SIGN_CANDIDATE"
    api.write_csv(notes_path, notes, api.REVIEW_NOTE_FIELDS)

    selection, inventory = api.derive_selection(tmp_path, RAW_ROOT)
    annotation_payload = api.annotation_payload_from_notes(notes, selection)
    decisions = annotation_payload["decisions"]
    api.write_json(tmp_path / api.ANNOTATIONS_RELATIVE_PATH, annotation_payload)
    api.write_csv(
        tmp_path / api.SELECTION_RELATIVE_PATH,
        selection,
        api.SELECTION_FIELDS,
    )
    api.write_csv(
        tmp_path / api.LINEAGE_RELATIVE_PATH,
        api.derive_lineage(selection, inventory, RAW_ROOT),
        api.LINEAGE_FIELDS,
    )
    _paths, layout = api.render_atlas(
        selection,
        inventory,
        RAW_ROOT,
        tmp_path / api.ASSETS_RELATIVE_PATH,
        decisions,
    )
    api.write_json(tmp_path / api.LAYOUT_RELATIVE_PATH, layout)
    summary = api.summary_from_decisions(decisions)
    (tmp_path / api.REPORT_RELATIVE_PATH).write_text(
        api.render_report(summary, annotation_payload), encoding="utf-8"
    )
    api.write_json(staged, api.build_manifest(tmp_path))

    result = api.verify_manifest(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert any(
        "pinned source hash mismatch: wp14_review_notes" in error
        for error in result["errors"]
    )


def test_count_preserving_exception_swap_is_rejected_by_exact_id_contract(
    tmp_path: Path,
) -> None:
    staged = stage_package(tmp_path)
    notes_path = tmp_path / api.REVIEW_NOTES_RELATIVE_PATH
    notes = read_csv(notes_path)
    original_not_related = next(
        row for row in notes if row["edge_id"] == "edge_002453"
    )
    original_same = next(
        row for row in notes if row["edge_id"] == "edge_002454"
    )
    original_not_related["provisional_outcome"] = "SAME_CAPTURE_CANDIDATE"
    original_not_related["capture_hypothesis"] = "SAME_CAPTURE_CANDIDATE"
    original_not_related["physical_sign_hypothesis"] = (
        "SAME_PHYSICAL_SIGN_CANDIDATE"
    )
    original_same["provisional_outcome"] = "NOT_RELATED"
    original_same["capture_hypothesis"] = "NOT_RELATED"
    original_same["physical_sign_hypothesis"] = "NOT_RELATED"
    api.write_csv(notes_path, notes, api.REVIEW_NOTE_FIELDS)

    selection, inventory = api.derive_selection(tmp_path, RAW_ROOT)
    annotation_payload = api.annotation_payload_from_notes(notes, selection)
    decisions = annotation_payload["decisions"]
    assert Counter(row["capture_hypothesis"] for row in decisions) == {
        "SAME_CAPTURE_CANDIDATE": 246,
        "NOT_RELATED": 4,
    }
    assert Counter(row["physical_sign_hypothesis"] for row in decisions) == {
        "SAME_PHYSICAL_SIGN_CANDIDATE": 238,
        "NOT_RELATED": 12,
    }
    with pytest.raises(ValueError, match="capture NOT_RELATED edge IDs"):
        api.validate_review_decision_contract(decisions)

    api.write_json(tmp_path / api.ANNOTATIONS_RELATIVE_PATH, annotation_payload)
    api.write_csv(
        tmp_path / api.SELECTION_RELATIVE_PATH,
        selection,
        api.SELECTION_FIELDS,
    )
    api.write_csv(
        tmp_path / api.LINEAGE_RELATIVE_PATH,
        api.derive_lineage(selection, inventory, RAW_ROOT),
        api.LINEAGE_FIELDS,
    )
    _paths, layout = api.render_atlas(
        selection,
        inventory,
        RAW_ROOT,
        tmp_path / api.ASSETS_RELATIVE_PATH,
        decisions,
    )
    api.write_json(tmp_path / api.LAYOUT_RELATIVE_PATH, layout)
    summary = api.summary_from_decisions(decisions)
    (tmp_path / api.REPORT_RELATIVE_PATH).write_text(
        api.render_report(summary, annotation_payload), encoding="utf-8"
    )
    api.write_json(staged, api.build_manifest(tmp_path))
    result = api.verify_manifest(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert any(
        "pinned source hash mismatch: wp14_review_notes" in error
        for error in result["errors"]
    )


@pytest.mark.parametrize(
    "source_id",
    [
        "wp5_manifest",
        "wp7_selection",
        "wp12_manifest",
        "wp12_annotations",
        "wp13_manifest",
        "wp13_selection",
        "wp13_annotations",
        "wp13_builder",
    ],
)
def test_pinned_source_tamper_fails_even_after_manifest_rehash(
    tmp_path: Path, source_id: str
) -> None:
    staged = stage_package(tmp_path)
    payload = read_json(staged)
    record = next(row for row in payload["sources"] if row["id"] == source_id)
    path = tmp_path / record["path"]
    path.write_bytes(path.read_bytes() + b"\n")
    refresh_manifest_records(staged)
    result = api.verify_manifest(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert any("pinned source hash mismatch" in error for error in result["errors"])


def test_path_escape_and_symlink_escape_are_rejected(tmp_path: Path) -> None:
    payload = read_json(MANIFEST_PATH)
    payload["sources"][0]["path"] = "../outside.json"
    result = verify_payload(tmp_path, payload, "path_escape.json")
    assert result["valid"] is False
    assert any("unsafe relative path" in error for error in result["errors"])

    stage_root = tmp_path / "stage"
    staged = stage_package(stage_root)
    selection = stage_root / api.SELECTION_RELATIVE_PATH
    outside = tmp_path / "outside.csv"
    outside.write_bytes(selection.read_bytes())
    selection.unlink()
    selection.symlink_to(outside)
    result = api.verify_manifest(staged, stage_root, RAW_ROOT)
    assert result["valid"] is False
    assert result["errors"]


def test_wp5_sources_and_raw_inventory_remain_preserved() -> None:
    for item_id, path, pinned_hash in api.source_contract(REPO_ROOT):
        if item_id == "wp14_builder":
            assert pinned_hash is None
            continue
        assert pinned_hash is not None
        assert api.sha256_file(path) == pinned_hash
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
    assert result["manifest_sha256"] == api.sha256_file(MANIFEST_PATH)
    rebuilt = read_json(clean_root / api.MANIFEST_RELATIVE_PATH)
    assert [(row["id"], row["sha256"], row["size"]) for row in rebuilt["artifacts"]] == [
        (row["id"], row["sha256"], row["size"]) for row in manifest["artifacts"]
    ]
