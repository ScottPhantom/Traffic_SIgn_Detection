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
SCRIPT_PATH = REPO_ROOT / "scripts/build_wp12_cross_split_review_batch.py"
SPEC = importlib.util.spec_from_file_location(
    "build_wp12_cross_split_review_batch", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
wp12 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp12
SPEC.loader.exec_module(wp12)

RAW_ROOT = Path(
    "/Users/nguyentantai/Library/Mobile Documents/com~apple~CloudDocs/"
    "FALL 2026 KỲ 4/CPV301/Data/DATASET01/staging/052bc980a7206f8d/raw"
)
MANIFEST_PATH = REPO_ROOT / wp12.MANIFEST_RELATIVE_PATH


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
    staged = tmp_path / wp12.MANIFEST_RELATIVE_PATH
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
                record["sha256"] = wp12.sha256_file(path)
                record["size"] = path.stat().st_size
    payload["total_artifact_bytes"] = sum(
        record["size"] for record in payload["artifacts"]
    )
    wp12.write_json(staged_manifest, payload)


def verify_payload(tmp_path: Path, payload: Any, name: str) -> dict[str, Any]:
    path = tmp_path / name
    wp12.write_json(path, payload)
    return wp12.verify_manifest(path, REPO_ROOT, RAW_ROOT)


def test_official_package_verifies_with_exact_rosters() -> None:
    result = wp12.verify_manifest(MANIFEST_PATH, REPO_ROOT, RAW_ROOT)
    assert result == {
        "valid": True,
        "errors": [],
        "source_count": 12,
        "artifact_count": 56,
        "status": wp12.PACKAGE_STATUS,
    }
    manifest = read_json(MANIFEST_PATH)
    assert manifest["source_count"] == len(manifest["sources"]) == 12
    assert manifest["artifact_count"] == len(manifest["artifacts"]) == 56
    assert manifest["selection_count"] == 250
    assert manifest["lineage_record_count"] == 500
    assert manifest["selected_endpoint_box_count"] == 1553
    assert manifest["quarantined_stem_0248_selected"] is False
    assert manifest["atlas_page_count"] == 50
    assert manifest["manifest_self_in_artifact_count"] is False
    assert manifest["artifact_count_semantics"] == "EXCLUDES_MANIFEST_FILE"
    assert wp12.MANIFEST_RELATIVE_PATH not in {
        row["path"] for row in manifest["artifacts"]
    }
    assert manifest["total_artifact_bytes"] == sum(
        (REPO_ROOT / row["path"]).stat().st_size for row in manifest["artifacts"]
    )
    assert manifest["package"] == wp12.BATCH_ID
    assert wp12.sha256_file(
        REPO_ROOT / wp12.REVIEW_NOTES_RELATIVE_PATH
    ) == wp12.EXPECTED_REVIEW_NOTES_SHA256


def test_selection_is_exact_next_250_pending_cross_split_rows() -> None:
    actual = read_csv(REPO_ROOT / wp12.SELECTION_RELATIVE_PATH)
    expected, _inventory = wp12.derive_selection(REPO_ROOT, RAW_ROOT)
    assert actual == expected
    assert len(actual) == len({row["edge_id"] for row in actual}) == 250
    assert actual[0]["edge_id"] == "edge_000315"
    assert actual[-1]["edge_id"] == "edge_001033"
    assert all(row["cross_split"] == "True" for row in actual)
    assert all(row["wp5_review_status"] == "PENDING" for row in actual)
    assert not wp12.EXPECTED_WP5_REVIEWED_IDS & {row["edge_id"] for row in actual}
    assert all(
        "0248" not in {row["left_stem"], row["right_stem"]} for row in actual
    )
    batch_a_ids = {
        row["edge_id"]
        for row in read_csv(REPO_ROOT / "docs/review/generated/wp7_batch_a_selection.csv")
    }
    assert len(batch_a_ids) == 100
    assert not batch_a_ids & {row["edge_id"] for row in actual}


def test_decisions_are_complete_bounded_and_image_referenced() -> None:
    selection = read_csv(REPO_ROOT / wp12.SELECTION_RELATIVE_PATH)
    payload, decisions = wp12.load_annotations(REPO_ROOT, selection)
    notes = wp12.load_review_notes(REPO_ROOT, selection)
    assert payload == wp12.annotation_payload_from_notes(notes, selection)
    assert len(decisions) == 250
    assert set(Counter(row["provisional_outcome"] for row in decisions)) <= set(
        wp12.ALLOWED_OUTCOMES
    )
    assert set(Counter(row["confidence"] for row in decisions)) <= set(
        wp12.CONFIDENCE_VALUES
    )
    assert all(row["evidence_refs"] == wp12.expected_evidence_refs(selected)
               for row, selected in zip(decisions, selection, strict=True))
    assert all(row["metadata_boundary"] == wp12.METADATA_BOUNDARY for row in decisions)
    assert all(row["evidence_boundary"] == wp12.EVIDENCE_BOUNDARY for row in decisions)
    assert Counter(row["capture_hypothesis"] for row in decisions) == {
        "SAME_CAPTURE_CANDIDATE": 240,
        "NOT_RELATED": 8,
        "UNRESOLVED": 2,
    }
    assert Counter(row["physical_sign_hypothesis"] for row in decisions) == {
        "SAME_PHYSICAL_SIGN_CANDIDATE": 235,
        "NOT_RELATED": 14,
        "UNRESOLVED": 1,
    }
    assert Counter(row["confidence"] for row in decisions) == {"HIGH": 243, "MEDIUM": 7}
    assert {
        row["edge_id"]
        for row in decisions
        if row["capture_hypothesis"] == "UNRESOLVED"
    } == {"edge_000535", "edge_000539"}
    assert {
        row["edge_id"]
        for row in decisions
        if row["physical_sign_hypothesis"] == "UNRESOLVED"
    } == {"edge_000539"}


def test_atlas_has_50_decision_complete_pages_and_250_slots() -> None:
    atlas_dir = REPO_ROOT / wp12.ASSETS_RELATIVE_PATH
    wp12.verify_exact_atlas_roster(atlas_dir)
    assert sorted(path.name for path in atlas_dir.iterdir()) == sorted(
        wp12.expected_atlas_names()
    )
    layout = read_json(REPO_ROOT / wp12.LAYOUT_RELATIVE_PATH)
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
    selection = read_csv(REPO_ROOT / wp12.SELECTION_RELATIVE_PATH)
    lineage = read_csv(REPO_ROOT / wp12.LINEAGE_RELATIVE_PATH)
    inventory_path = (
        REPO_ROOT
        / "results/data_audit/DATASET01_052bc980a7206f8d/image_inventory.csv"
    )
    assert len(lineage) == 500
    assert lineage == wp12.derive_lineage(
        selection,
        {row["stem"]: row for row in read_csv(inventory_path)},
        RAW_ROOT,
    )
    assert Counter(row["edge_id"] for row in lineage) == {
        row["edge_id"]: 2 for row in selection
    }
    assert all(row["side"] in {"LEFT", "RIGHT"} for row in lineage)
    inventory = {row["stem"]: row for row in read_csv(inventory_path)}
    assert sum(int(inventory[row["stem"]]["box_count"]) for row in lineage) == 1553
    assert all(row["stem"] != "0248" for row in lineage)


def test_manifest_hashes_sizes_and_pinned_sources_match() -> None:
    manifest = read_json(MANIFEST_PATH)
    pinned = {item_id: digest for item_id, _path, digest in wp12.source_contract(REPO_ROOT)}
    for record in [*manifest["sources"], *manifest["artifacts"]]:
        path = REPO_ROOT / record["path"]
        assert record["sha256"] == wp12.sha256_file(path)
        assert record["size"] == path.stat().st_size
        if record["id"] in pinned and pinned[record["id"]] is not None:
            assert record["sha256"] == pinned[record["id"]]


def test_report_keeps_wp5_and_gate0_fail_closed() -> None:
    report = (REPO_ROOT / wp12.REPORT_RELATIVE_PATH).read_text(encoding="utf-8")
    assert "# M0-WP12-R1" in report
    assert wp12.PRE_REPAIR_MANIFEST_SHA256 in report
    assert wp12.EXPECTED_REVIEW_NOTES_SHA256 in report
    assert "Status remains awaiting independent QA" in report
    assert "0 blind capture-decision disagreements" in report
    assert "visually accepted 50/50 pages" in report
    assert "Canonical WP5 remains unchanged at 3172 PENDING edges" in report
    assert "2822 canonical" in report
    assert "676" in report
    assert "All 589 WP5 sequences remain PENDING" in report
    assert "D-02 remains PENDING" in report
    assert "Gate 0 remains BLOCKED" in report
    assert "training_authorized=false" in report
    wp12.validate_governance(REPO_ROOT)


def test_no_final_group_or_split_fields_are_created() -> None:
    forbidden = {"group_id", "final_group_id", "assigned_split", "approved_split"}
    selection = read_csv(REPO_ROOT / wp12.SELECTION_RELATIVE_PATH)
    annotations = read_json(REPO_ROOT / wp12.ANNOTATIONS_RELATIVE_PATH)
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
                "sha256": wp12.sha256_file(REPO_ROOT / "PROJECT_MEMORY.md"),
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


@pytest.mark.parametrize("attack", ["extra", "missing", "directory", "symlink"])
def test_atlas_directory_rejects_non_exact_or_non_regular_roster(
    tmp_path: Path, attack: str
) -> None:
    staged = stage_package(tmp_path)
    atlas_dir = tmp_path / wp12.ASSETS_RELATIVE_PATH
    page = atlas_dir / "page_001.jpg"
    if attack == "extra":
        (atlas_dir / "unexpected.txt").write_text("unexpected", encoding="utf-8")
    elif attack == "missing":
        page.unlink()
    elif attack == "directory":
        page.unlink()
        page.mkdir()
    else:
        target = atlas_dir / "page_002.jpg"
        page.unlink()
        page.symlink_to(target.name)
    result = wp12.verify_manifest(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert result["errors"]


@pytest.mark.parametrize(
    "attack",
    [
        "left_bounds",
        "right_bounds",
        "text_bounds",
        "page_width",
        "page_height",
        "bbox_placement",
        "text_context",
    ],
)
def test_layout_semantics_fail_after_coherent_rehash(
    tmp_path: Path, attack: str
) -> None:
    staged = stage_package(tmp_path)
    path = tmp_path / wp12.LAYOUT_RELATIVE_PATH
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
    else:
        row["left_stem"] = "forged-context"
    wp12.write_json(path, payload)
    refresh_manifest_records(staged)
    result = wp12.verify_manifest(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert any("semantic verification failed" in error for error in result["errors"])


@pytest.mark.parametrize("attack", ["page_pixel", "index_text"])
def test_atlas_bytes_fail_after_coherent_rehash(tmp_path: Path, attack: str) -> None:
    staged = stage_package(tmp_path)
    if attack == "page_pixel":
        path = tmp_path / wp12.ASSETS_RELATIVE_PATH / "page_001.jpg"
        with Image.open(path) as image:
            mutated = image.convert("RGB")
        pixel = mutated.getpixel((0, 0))
        mutated.putpixel((0, 0), tuple(255 - channel for channel in pixel))
        mutated.save(path, format="JPEG", quality=90, optimize=True, subsampling=1)
    else:
        path = tmp_path / wp12.ASSETS_RELATIVE_PATH / "index.html"
        path.write_text(
            path.read_text(encoding="utf-8") + "<!-- forged -->\n",
            encoding="utf-8",
        )
    refresh_manifest_records(staged)
    result = wp12.verify_manifest(staged, tmp_path, RAW_ROOT)
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
        path = tmp_path / wp12.SELECTION_RELATIVE_PATH
        rows = read_csv(path)
        rows[0], rows[1] = rows[1], rows[0]
        wp12.write_csv(path, rows, wp12.SELECTION_FIELDS)
    elif attack == "selection_duplicate":
        path = tmp_path / wp12.SELECTION_RELATIVE_PATH
        rows = read_csv(path)
        rows[1] = dict(rows[0])
        wp12.write_csv(path, rows, wp12.SELECTION_FIELDS)
    elif attack == "annotation_change":
        path = tmp_path / wp12.ANNOTATIONS_RELATIVE_PATH
        payload = read_json(path)
        payload["decisions"][0]["confidence"] = "LOW"
        wp12.write_json(path, payload)
    elif attack == "annotation_promotion":
        path = tmp_path / wp12.ANNOTATIONS_RELATIVE_PATH
        payload = read_json(path)
        payload["decisions"][0]["final_group_id"] = "forbidden"
        wp12.write_json(path, payload)
    elif attack == "annotation_evidence":
        path = tmp_path / wp12.ANNOTATIONS_RELATIVE_PATH
        payload = read_json(path)
        payload["decisions"][0]["evidence_refs"][0] = "forged"
        wp12.write_json(path, payload)
    elif attack == "annotation_reviewer":
        path = tmp_path / wp12.ANNOTATIONS_RELATIVE_PATH
        payload = read_json(path)
        payload["reviewer"] = "forged"
        wp12.write_json(path, payload)
    elif attack == "annotation_timestamp":
        path = tmp_path / wp12.ANNOTATIONS_RELATIVE_PATH
        payload = read_json(path)
        payload["reviewed_at"] = "2026-10-11T18:00:00"
        wp12.write_json(path, payload)
    elif attack == "lineage_hash":
        path = tmp_path / wp12.LINEAGE_RELATIVE_PATH
        rows = read_csv(path)
        rows[0]["image_sha256"] = "0" * 64
        wp12.write_csv(path, rows, wp12.LINEAGE_FIELDS)
    elif attack == "lineage_reorder":
        path = tmp_path / wp12.LINEAGE_RELATIVE_PATH
        rows = read_csv(path)
        rows[0], rows[1] = rows[1], rows[0]
        wp12.write_csv(path, rows, wp12.LINEAGE_FIELDS)
    elif attack == "manifest_governance":
        payload = read_json(staged)
        payload["training_authorized"] = True
        wp12.write_json(staged, payload)
    else:
        path = tmp_path / wp12.LAYOUT_RELATIVE_PATH
        payload = read_json(path)
        payload["pages"][0]["rows"][0]["slot"] = 2
        wp12.write_json(path, payload)
    if attack != "manifest_governance":
        refresh_manifest_records(staged)
    result = wp12.verify_manifest(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    if attack == "manifest_governance":
        assert any("training_authorized" in error for error in result["errors"])
    else:
        assert any("semantic verification failed" in error for error in result["errors"])


def test_review_note_tamper_fails_even_after_source_rehash(tmp_path: Path) -> None:
    staged = stage_package(tmp_path)
    path = tmp_path / wp12.REVIEW_NOTES_RELATIVE_PATH
    rows = read_csv(path)
    rows[0]["edge_id"] = rows[1]["edge_id"]
    wp12.write_csv(path, rows, wp12.REVIEW_NOTE_FIELDS)
    refresh_manifest_records(staged)
    result = wp12.verify_manifest(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert any("pinned source hash mismatch" in error for error in result["errors"])


def test_coherent_edge_000539_review_rollback_is_rejected_by_source_anchor(
    tmp_path: Path,
) -> None:
    staged = stage_package(tmp_path)
    notes_path = tmp_path / wp12.REVIEW_NOTES_RELATIVE_PATH
    notes = read_csv(notes_path)
    target = next(row for row in notes if row["edge_id"] == "edge_000539")
    target["provisional_outcome"] = "SAME_CAPTURE_CANDIDATE"
    target["capture_hypothesis"] = "SAME_CAPTURE_CANDIDATE"
    target["physical_sign_hypothesis"] = "SAME_PHYSICAL_SIGN_CANDIDATE"
    wp12.write_csv(notes_path, notes, wp12.REVIEW_NOTE_FIELDS)

    selection, inventory = wp12.derive_selection(tmp_path, RAW_ROOT)
    annotation_payload = wp12.annotation_payload_from_notes(notes, selection)
    decisions = annotation_payload["decisions"]
    wp12.write_json(tmp_path / wp12.ANNOTATIONS_RELATIVE_PATH, annotation_payload)
    wp12.write_csv(
        tmp_path / wp12.SELECTION_RELATIVE_PATH,
        selection,
        wp12.SELECTION_FIELDS,
    )
    wp12.write_csv(
        tmp_path / wp12.LINEAGE_RELATIVE_PATH,
        wp12.derive_lineage(selection, inventory, RAW_ROOT),
        wp12.LINEAGE_FIELDS,
    )
    _paths, layout = wp12.render_atlas(
        selection,
        inventory,
        RAW_ROOT,
        tmp_path / wp12.ASSETS_RELATIVE_PATH,
        decisions,
    )
    wp12.write_json(tmp_path / wp12.LAYOUT_RELATIVE_PATH, layout)
    summary = wp12.summary_from_decisions(decisions)
    (tmp_path / wp12.REPORT_RELATIVE_PATH).write_text(
        wp12.render_report(summary, annotation_payload), encoding="utf-8"
    )
    wp12.write_json(staged, wp12.build_manifest(tmp_path))

    result = wp12.verify_manifest(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert any(
        "pinned source hash mismatch: wp12_review_notes" in error
        for error in result["errors"]
    )


@pytest.mark.parametrize("source_id", ["wp5_manifest", "wp7_selection", "wp7_annotations"])
def test_pinned_source_tamper_fails_even_after_manifest_rehash(
    tmp_path: Path, source_id: str
) -> None:
    staged = stage_package(tmp_path)
    payload = read_json(staged)
    record = next(row for row in payload["sources"] if row["id"] == source_id)
    path = tmp_path / record["path"]
    path.write_bytes(path.read_bytes() + b"\n")
    refresh_manifest_records(staged)
    result = wp12.verify_manifest(staged, tmp_path, RAW_ROOT)
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
    selection = stage_root / wp12.SELECTION_RELATIVE_PATH
    outside = tmp_path / "outside.csv"
    outside.write_bytes(selection.read_bytes())
    selection.unlink()
    selection.symlink_to(outside)
    result = wp12.verify_manifest(staged, stage_root, RAW_ROOT)
    assert result["valid"] is False
    assert result["errors"]


def test_wp5_sources_and_raw_inventory_remain_preserved() -> None:
    for _item_id, path, pinned_hash in wp12.source_contract(REPO_ROOT)[:10]:
        assert pinned_hash is not None
        assert wp12.sha256_file(path) == pinned_hash
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
    result = wp12.build(clean_root, RAW_ROOT)
    assert result["manifest_sha256"] == wp12.sha256_file(MANIFEST_PATH)
    rebuilt = read_json(clean_root / wp12.MANIFEST_RELATIVE_PATH)
    assert [(row["id"], row["sha256"], row["size"]) for row in rebuilt["artifacts"]] == [
        (row["id"], row["sha256"], row["size"]) for row in manifest["artifacts"]
    ]
