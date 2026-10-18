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
SCRIPT_PATH = REPO_ROOT / "scripts/build_wp23_remaining_edge_review_batch.py"
SPEC = importlib.util.spec_from_file_location(
    "build_wp23_remaining_edge_review_batch", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
wp23 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp23
SPEC.loader.exec_module(wp23)
wp23.configure_previous()
wp23.previous.configure_previous()
wp23.previous.previous.configure_previous()
wp23.previous.previous.previous.configure_base()
api = wp23.previous.previous.previous.base

RAW_ROOT = Path(
    "/Users/nguyentantai/Library/Mobile Documents/com~apple~CloudDocs/"
    "FALL 2026 KỲ 4/CPV301/Data/DATASET01/staging/052bc980a7206f8d/raw"
)
MANIFEST_PATH = REPO_ROOT / wp23.MANIFEST_RELATIVE_PATH

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
WP23_ATTACK_CLASSES = frozenset(
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
    staged = tmp_path / wp23.MANIFEST_RELATIVE_PATH
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
    return wp23.verify(path, REPO_ROOT, RAW_ROOT)


def test_official_package_verifies_with_exact_rosters() -> None:
    result = wp23.verify(MANIFEST_PATH, REPO_ROOT, RAW_ROOT)
    assert result == {
        "valid": True,
        "errors": [],
        "source_count": 56,
        "artifact_count": 56,
        "status": wp23.PACKAGE_STATUS,
    }
    manifest = read_json(MANIFEST_PATH)
    assert manifest["source_count"] == len(manifest["sources"]) == 56
    assert manifest["artifact_count"] == len(manifest["artifacts"]) == 56
    assert manifest["selection_count"] == 250
    assert manifest["lineage_record_count"] == 500
    assert manifest["selected_endpoint_box_count"] == 1556
    assert manifest["atlas_page_count"] == 50
    assert manifest["quarantined_stem_0248_selected"] is False
    assert manifest["manifest_self_in_artifact_count"] is False
    assert manifest["artifact_count_semantics"] == "EXCLUDES_MANIFEST_FILE"
    assert manifest["total_artifact_bytes"] == sum(
        (REPO_ROOT / row["path"]).stat().st_size for row in manifest["artifacts"]
    )
    assert api.sha256_file(
        REPO_ROOT / wp23.REVIEW_NOTES_RELATIVE_PATH
    ) == wp23.EXPECTED_REVIEW_NOTES_SHA256


def test_selection_is_exact_first_250_review_eligible_residual_rows() -> None:
    actual = read_csv(REPO_ROOT / wp23.SELECTION_RELATIVE_PATH)
    expected, _inventory = wp23.derive_selection(REPO_ROOT, RAW_ROOT)
    assert actual == expected
    assert len(actual) == len({row["edge_id"] for row in actual}) == 250
    assert actual[0]["edge_id"] == "edge_000379"
    assert actual[-1]["edge_id"] == "edge_000760"
    assert int(actual[0]["wp5_review_order"]) == 1285
    assert int(actual[-1]["wp5_review_order"]) == 1534
    assert all(row["cross_split"] == "False" for row in actual)
    assert all(row["wp5_review_status"] == "PENDING" for row in actual)
    assert all("0248" not in {row["left_stem"], row["right_stem"]} for row in actual)
    assert all(
        row["sequence_context_boundary"]
        == "CONTEXT_ONLY_NOT_USED_TO_DERIVE_EDGE_DECISION"
        for row in actual
    )


def test_residual_derivation_and_quarantine_exclusion_are_exact() -> None:
    rows = api.load_wp5_rows(REPO_ROOT)
    overlay_paths = (
        "wp7_batch_a_selection.csv",
        "wp12_batch_b_selection.csv",
        "wp13_batch_c_selection.csv",
        "wp14_batch_d_selection.csv",
        "wp15_batch_e_selection.csv",
    )
    overlays = [
        read_csv(REPO_ROOT / "docs/review/generated" / path)
        for path in overlay_paths
    ]
    assert [len(batch) for batch in overlays] == [100, 250, 250, 250, 176]
    overlay_ids = [row["edge_id"] for batch in overlays for row in batch]
    assert len(overlay_ids) == len(set(overlay_ids)) == 1026
    base_residual = [
        row
        for row in rows
        if row["review_status"] == "PENDING" and row["edge_id"] not in set(overlay_ids)
    ]
    assert len(base_residual) == 2146
    assert all(row["cross_split"] == "False" for row in base_residual)
    base_quarantined = [
        row["edge_id"]
        for row in base_residual
        if "0248" in {row["left_stem"], row["right_stem"]}
    ]
    assert base_quarantined == ["edge_000242", "edge_000243"]
    base_eligible = [
        row
        for row in base_residual
        if "0248" not in {row["left_stem"], row["right_stem"]}
    ]
    assert len(base_eligible) == 2144

    wp22_selection = read_csv(
        REPO_ROOT
        / "docs/review/generated/wp22_remaining_edge_batch_a_selection.csv"
    )
    assert [row["edge_id"] for row in wp22_selection] == [
        row["edge_id"] for row in base_eligible[:250]
    ]
    predecessor_ids = set(overlay_ids) | {
        row["edge_id"] for row in wp22_selection
    }
    residual = [
        row
        for row in rows
        if row["review_status"] == "PENDING"
        and row["edge_id"] not in predecessor_ids
    ]
    assert len(residual) == 1896
    assert all(row["cross_split"] == "False" for row in residual)
    quarantined = [
        row["edge_id"]
        for row in residual
        if "0248" in {row["left_stem"], row["right_stem"]}
    ]
    assert quarantined == ["edge_000242", "edge_000243"]
    eligible = [
        row
        for row in residual
        if "0248" not in {row["left_stem"], row["right_stem"]}
    ]
    selection = read_csv(REPO_ROOT / wp23.SELECTION_RELATIVE_PATH)
    assert len(eligible) == 1894
    assert [row["edge_id"] for row in selection] == [
        row["edge_id"] for row in eligible[:250]
    ]
    assert len(eligible[250:]) + len(quarantined) == 1646


def test_sequence_context_is_exact_and_never_a_decision_source() -> None:
    context = wp23.load_sequence_context(REPO_ROOT)
    selection = read_csv(REPO_ROOT / wp23.SELECTION_RELATIVE_PATH)
    assert len(context) == 588
    for row in selection:
        sequence_id = row["proxy_sequence_id"]
        if sequence_id not in context:
            assert row["sequence_context_status"] == "NO_SEQUENCE_CONTEXT_AVAILABLE"
            assert all(
                row[field] == ""
                for field in (
                    "sequence_context_batch",
                    "sequence_capture_context",
                    "sequence_physical_context",
                    "sequence_confidence_context",
                )
            )
            continue
        expected = context[sequence_id]
        assert row["sequence_context_status"] == "PROVISIONAL_SEQUENCE_CONTEXT_ONLY"
        assert row["sequence_context_batch"] == expected["batch"]
        assert row["sequence_capture_context"] == expected["capture"]
        assert row["sequence_physical_context"] == expected["physical"]
        assert row["sequence_confidence_context"] == expected["confidence"]
    no_context_sequence_ids = {
        row["proxy_sequence_id"]
        for row in selection
        if row["sequence_context_status"] == "NO_SEQUENCE_CONTEXT_AVAILABLE"
        and row["proxy_sequence_id"]
    }
    assert no_context_sequence_ids == set()


def test_decisions_are_complete_pinned_and_provisional() -> None:
    selection = read_csv(REPO_ROOT / wp23.SELECTION_RELATIVE_PATH)
    payload, decisions = api.load_annotations(REPO_ROOT, selection)
    notes = api.load_review_notes(REPO_ROOT, selection)
    assert payload == api.annotation_payload_from_notes(notes, selection)
    assert len(decisions) == 250
    assert Counter(row["provisional_outcome"] for row in decisions) == {
        "SAME_CAPTURE_CANDIDATE": 233,
        "NOT_RELATED": 17,
    }
    assert Counter(row["capture_hypothesis"] for row in decisions) == {
        "SAME_CAPTURE_CANDIDATE": 233,
        "NOT_RELATED": 17,
    }
    assert Counter(row["physical_sign_hypothesis"] for row in decisions) == {
        "SAME_PHYSICAL_SIGN_CANDIDATE": 233,
        "NOT_RELATED": 17,
    }
    assert Counter(row["confidence"] for row in decisions) == {"HIGH": 250}
    not_related = {
        row["edge_id"]
        for row in decisions
        if row["capture_hypothesis"] == "NOT_RELATED"
    }
    assert not_related == wp23.EXPECTED_CAPTURE_NOT_RELATED_IDS
    assert not_related == wp23.EXPECTED_PHYSICAL_SIGN_NOT_RELATED_IDS
    assert all(row["reviewer"] == "PM/Codex provisional visual reviewer" for row in decisions)
    assert all(row["evidence_boundary"] == wp23.EVIDENCE_BOUNDARY for row in decisions)


def test_atlas_layout_and_lineage_are_complete() -> None:
    atlas_dir = REPO_ROOT / wp23.ASSETS_RELATIVE_PATH
    api.verify_exact_atlas_roster(atlas_dir)
    assert sorted(path.name for path in atlas_dir.iterdir()) == sorted(
        api.expected_atlas_names()
    )
    layout = read_json(REPO_ROOT / wp23.LAYOUT_RELATIVE_PATH)
    assert layout["page_count"] == 50
    assert layout["pair_count"] == 250
    assert layout["pairs_per_page"] == 5
    assert layout["all_headers_complete"] is True
    assert layout["all_text_complete"] is True
    assert layout["all_bounds_fit"] is True
    assert layout["all_bbox_context_rendered"] is True
    assert layout["all_decisions_recorded"] is True
    rows = [row for page in layout["pages"] for row in page["rows"]]
    assert [row["batch_position"] for row in rows] == list(range(1, 251))
    assert all(page["row_count"] == len(page["rows"]) == 5 for page in layout["pages"])
    for page in layout["pages"]:
        assert page["width"] == 1600
        assert page["height"] == 2372
        with Image.open(REPO_ROOT / page["path"]) as image:
            assert image.size == (1600, 2372)
            image.verify()

    selection = read_csv(REPO_ROOT / wp23.SELECTION_RELATIVE_PATH)
    lineage = read_csv(REPO_ROOT / wp23.LINEAGE_RELATIVE_PATH)
    inventory_path = (
        REPO_ROOT
        / "results/data_audit/DATASET01_052bc980a7206f8d/image_inventory.csv"
    )
    inventory = {row["stem"]: row for row in read_csv(inventory_path)}
    assert len(lineage) == 500
    assert lineage == api.derive_lineage(selection, inventory, RAW_ROOT)
    assert Counter(row["edge_id"] for row in lineage) == {
        row["edge_id"]: 2 for row in selection
    }
    assert sum(int(inventory[row["stem"]]["box_count"]) for row in lineage) == 1556
    assert all(row["stem"] != "0248" for row in lineage)


def test_manifest_hashes_pins_and_governance_match() -> None:
    manifest = read_json(MANIFEST_PATH)
    pinned = {
        item_id: digest
        for item_id, _path, digest in wp23.source_contract(REPO_ROOT)
    }
    for record in [*manifest["sources"], *manifest["artifacts"]]:
        path = REPO_ROOT / record["path"]
        assert record["sha256"] == api.sha256_file(path)
        assert record["size"] == path.stat().st_size
        if record["id"] in pinned and pinned[record["id"]] is not None:
            assert record["sha256"] == pinned[record["id"]]
    assert manifest["status"] == wp23.PACKAGE_STATUS
    assert manifest["gate0"] == "BLOCKED"
    assert manifest["d02_status"] == "PENDING"
    assert manifest["split_authorized"] is False
    assert manifest["training_authorized"] is False
    assert manifest["final_group_truth_created"] is False


def test_report_and_artifacts_do_not_promote_group_truth() -> None:
    report = (REPO_ROOT / wp23.REPORT_RELATIVE_PATH).read_text(encoding="utf-8")
    assert "# M0-WP23" in report
    assert wp23.EXPECTED_REVIEW_NOTES_SHA256 in report
    assert "first 250 of the 1,894 review-eligible residual rows" in report
    assert "All 250 pairs/500 raw frames were directly inspected" in report
    assert "1,646 PENDING edges" in report or "1646 PENDING edges" in report
    assert "All 589 WP5 sequences remain PENDING" in report
    assert "D-02 remains PENDING" in report
    assert "Gate 0 remains BLOCKED" in report
    assert "training_authorized=false" in report
    forbidden = {"group_id", "final_group_id", "assigned_split", "approved_split"}
    selection = read_csv(REPO_ROOT / wp23.SELECTION_RELATIVE_PATH)
    annotations = read_json(REPO_ROOT / wp23.ANNOTATIONS_RELATIVE_PATH)
    assert not forbidden & set(selection[0])
    assert all(not forbidden & set(row) for row in annotations["decisions"])
    api.validate_governance(REPO_ROOT)


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
            payload[collection][1],
            payload[collection][0],
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
    result = verify_payload(tmp_path, payload, f"{collection}_{mutation}.json")
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


def test_wp23_attack_contract_has_exactly_18_unique_classes() -> None:
    assert len(WP23_ATTACK_CLASSES) == 18


@pytest.mark.parametrize("attack", ATLAS_ATTACKS)
def test_atlas_directory_rejects_non_exact_or_non_regular_roster(
    tmp_path: Path, attack: str
) -> None:
    staged = stage_package(tmp_path)
    atlas_dir = tmp_path / wp23.ASSETS_RELATIVE_PATH
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
        page.unlink()
        page.symlink_to("page_002.jpg")
    else:
        copied = tmp_path / "copied_atlas"
        shutil.copytree(atlas_dir, copied)
        shutil.rmtree(atlas_dir)
        atlas_dir.symlink_to(copied, target_is_directory=True)
    result = wp23.verify(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert result["errors"]


@pytest.mark.parametrize("attack", LAYOUT_ATTACKS)
def test_layout_semantics_fail_after_coherent_rehash(
    tmp_path: Path, attack: str
) -> None:
    staged = stage_package(tmp_path)
    path = tmp_path / wp23.LAYOUT_RELATIVE_PATH
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
    result = wp23.verify(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert any("semantic verification failed" in error for error in result["errors"])


@pytest.mark.parametrize("attack", BYTE_ATTACKS)
def test_atlas_bytes_fail_after_coherent_rehash(tmp_path: Path, attack: str) -> None:
    staged = stage_package(tmp_path)
    if attack == "page_pixel":
        path = tmp_path / wp23.ASSETS_RELATIVE_PATH / "page_001.jpg"
        with Image.open(path) as image:
            mutated = image.convert("RGB")
        pixel = mutated.getpixel((0, 0))
        mutated.putpixel((0, 0), tuple(255 - channel for channel in pixel))
        mutated.save(path, format="JPEG", quality=90, optimize=True, subsampling=1)
    else:
        path = tmp_path / wp23.ASSETS_RELATIVE_PATH / "index.html"
        path.write_text(
            path.read_text(encoding="utf-8") + "<!-- forged -->\n",
            encoding="utf-8",
        )
    refresh_manifest_records(staged)
    result = wp23.verify(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert any(
        "atlas bytes differ from deterministic regeneration" in error
        for error in result["errors"]
    )


def test_review_note_anchor_and_exact_exception_ids_fail_closed(
    tmp_path: Path,
) -> None:
    staged = stage_package(tmp_path)
    path = tmp_path / wp23.REVIEW_NOTES_RELATIVE_PATH
    notes = read_csv(path)
    related = next(row for row in notes if row["edge_id"] == "edge_000379")
    unrelated = next(row for row in notes if row["edge_id"] == "edge_000382")
    related.update(
        provisional_outcome="NOT_RELATED",
        capture_hypothesis="NOT_RELATED",
        physical_sign_hypothesis="NOT_RELATED",
    )
    unrelated.update(
        provisional_outcome="SAME_CAPTURE_CANDIDATE",
        capture_hypothesis="SAME_CAPTURE_CANDIDATE",
        physical_sign_hypothesis="SAME_PHYSICAL_SIGN_CANDIDATE",
    )
    assert Counter(row["capture_hypothesis"] for row in notes) == {
        "SAME_CAPTURE_CANDIDATE": 233,
        "NOT_RELATED": 17,
    }
    with pytest.raises(ValueError, match="NOT_RELATED IDs"):
        wp23.validate_review_decision_contract(notes)
    api.write_csv(path, notes, api.REVIEW_NOTE_FIELDS)
    refresh_manifest_records(staged)
    result = wp23.verify(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert any("pinned source hash mismatch" in error for error in result["errors"])


@pytest.mark.parametrize("attack", PATH_ATTACKS)
def test_path_and_symlink_escape_fail_closed(tmp_path: Path, attack: str) -> None:
    if attack == "manifest_path_traversal":
        payload = read_json(MANIFEST_PATH)
        payload["sources"][0]["path"] = "../outside.json"
        result = verify_payload(tmp_path, payload, "path_escape.json")
        assert result["valid"] is False
        assert any("unsafe relative path" in error for error in result["errors"])
        return
    stage_root = tmp_path / "stage"
    staged = stage_package(stage_root)
    selection = stage_root / wp23.SELECTION_RELATIVE_PATH
    outside = tmp_path / "outside.csv"
    outside.write_bytes(selection.read_bytes())
    selection.unlink()
    selection.symlink_to(outside)
    result = wp23.verify(staged, stage_root, RAW_ROOT)
    assert result["valid"] is False
    assert result["errors"]


def test_sources_raw_and_readme_remain_preserved() -> None:
    for item_id, path, pinned_hash in wp23.source_contract(REPO_ROOT):
        if item_id == "wp23_builder":
            assert pinned_hash is None
            continue
        assert pinned_hash is not None
        assert api.sha256_file(path) == pinned_hash
    proof = read_json(
        REPO_ROOT
        / "results/data_audit/DATASET01_052bc980a7206f8d/source_preservation_proof.json"
    )
    assert proof["unchanged"] is True
    assert api.sha256_file(REPO_ROOT / "README.md") == (
        "9005addc5b9952b36fca7f744489270cc7507bfaad0c6a02f305954915de01a7"
    )


def test_clean_room_rebuild_is_byte_deterministic(tmp_path: Path) -> None:
    clean_root = tmp_path / "clean"
    manifest = read_json(MANIFEST_PATH)
    for record in manifest["sources"]:
        source = REPO_ROOT / record["path"]
        target = clean_root / record["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    result = wp23.build(clean_root, RAW_ROOT)
    assert result["manifest_sha256"] == api.sha256_file(MANIFEST_PATH)
    rebuilt = read_json(clean_root / wp23.MANIFEST_RELATIVE_PATH)
    assert [
        (row["id"], row["sha256"], row["size"]) for row in rebuilt["artifacts"]
    ] == [
        (row["id"], row["sha256"], row["size"])
        for row in manifest["artifacts"]
    ]
