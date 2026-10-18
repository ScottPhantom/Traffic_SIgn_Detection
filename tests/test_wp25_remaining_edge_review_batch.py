from __future__ import annotations

import copy
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
SCRIPT_PATH = REPO_ROOT / "scripts/build_wp25_remaining_edge_review_batch.py"
SPEC = importlib.util.spec_from_file_location(
    "build_wp25_remaining_edge_review_batch", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
wp25 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp25
SPEC.loader.exec_module(wp25)
wp25._configure()
api = wp25.core

RAW_ROOT = Path(
    "/Users/nguyentantai/Library/Mobile Documents/com~apple~CloudDocs/"
    "FALL 2026 KỲ 4/CPV301/Data/DATASET01/staging/052bc980a7206f8d/raw"
)
MANIFEST_PATH = REPO_ROOT / wp25.MANIFEST_RELATIVE_PATH

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
WP25_ATTACK_CLASSES = frozenset(
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
    staged = tmp_path / wp25.MANIFEST_RELATIVE_PATH
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


def test_official_package_verifies_with_exact_rosters() -> None:
    result = wp25.verify(MANIFEST_PATH, REPO_ROOT, RAW_ROOT)
    assert result == {
        "valid": True,
        "errors": [],
        "source_count": 72,
        "artifact_count": 56,
        "status": "WP25_AWAITING_QA_REVIEW",
    }
    manifest = read_json(MANIFEST_PATH)
    assert manifest["selection_count"] == 250
    assert manifest["lineage_record_count"] == 500
    assert manifest["selected_endpoint_box_count"] == 1090
    assert manifest["atlas_page_count"] == 50
    assert manifest["gate0"] == "BLOCKED"
    assert manifest["d02_status"] == "PENDING"
    assert manifest["split_authorized"] is False
    assert manifest["training_authorized"] is False
    assert manifest["final_group_truth_created"] is False
    assert manifest["transitive_grouping_created"] is False


def test_selection_is_exact_next_250_after_wp22_wp23_r1_and_wp24() -> None:
    actual = read_csv(REPO_ROOT / wp25.SELECTION_RELATIVE_PATH)
    expected, _inventory = wp25.derive_selection(REPO_ROOT, RAW_ROOT)
    assert actual == expected
    assert len(actual) == len({row["edge_id"] for row in actual}) == 250
    assert (actual[0]["edge_id"], actual[0]["wp5_review_order"]) == (
        "edge_001155",
        "1785",
    )
    assert (actual[-1]["edge_id"], actual[-1]["wp5_review_order"]) == (
        "edge_001502",
        "2034",
    )
    assert all(row["cross_split"] == "False" for row in actual)
    assert all(row["wp5_review_status"] == "PENDING" for row in actual)
    assert all("0248" not in {row["left_stem"], row["right_stem"]} for row in actual)
    assert all(row["proxy_sequence_id"] != "proxy_sequence_0050" for row in actual)
    assert all(
        row["sequence_context_boundary"]
        == "CONTEXT_ONLY_NOT_USED_TO_DERIVE_EDGE_DECISION"
        for row in actual
    )


def test_residual_derivation_predecessor_prefix_and_quarantine_are_exact() -> None:
    rows = api.load_wp5_rows(REPO_ROOT)
    generated = REPO_ROOT / "docs/review/generated"
    overlay_names = (
        "wp7_batch_a_selection.csv",
        "wp12_batch_b_selection.csv",
        "wp13_batch_c_selection.csv",
        "wp14_batch_d_selection.csv",
        "wp15_batch_e_selection.csv",
    )
    cross_split = [row for name in overlay_names for row in read_csv(generated / name)]
    wp22 = read_csv(generated / "wp22_remaining_edge_batch_a_selection.csv")
    wp23_r1 = read_csv(generated / "wp23_r1_remaining_edge_batch_b_selection.csv")
    wp24 = read_csv(generated / "wp24_remaining_edge_batch_c_selection.csv")
    assert len(cross_split) == len({row["edge_id"] for row in cross_split}) == 1026
    base_residual = [
        row
        for row in rows
        if row["review_status"] == "PENDING"
        and row["edge_id"] not in {item["edge_id"] for item in cross_split}
    ]
    base_eligible = [
        row for row in base_residual if "0248" not in {row["left_stem"], row["right_stem"]}
    ]
    assert len(base_residual) == 2146
    assert [row["edge_id"] for row in wp22] == [row["edge_id"] for row in base_eligible[:250]]
    assert [row["edge_id"] for row in wp23_r1] == [
        row["edge_id"] for row in base_eligible[250:500]
    ]
    assert [row["edge_id"] for row in wp24] == [
        row["edge_id"] for row in base_eligible[500:750]
    ]
    excluded = {
        row["edge_id"] for row in [*cross_split, *wp22, *wp23_r1, *wp24]
    }
    residual = [
        row
        for row in rows
        if row["review_status"] == "PENDING" and row["edge_id"] not in excluded
    ]
    quarantined = [
        row for row in residual if "0248" in {row["left_stem"], row["right_stem"]}
    ]
    eligible = [row for row in residual if row not in quarantined]
    selection = read_csv(REPO_ROOT / wp25.SELECTION_RELATIVE_PATH)
    assert len(residual) == 1396
    assert [row["edge_id"] for row in quarantined] == ["edge_000242", "edge_000243"]
    assert len(eligible) == 1394
    assert [row["edge_id"] for row in selection] == [
        row["edge_id"] for row in eligible[:250]
    ]
    assert len(eligible[250:]) + len(quarantined) == 1146


def test_selection_acceptance_tallies_are_reconstructed() -> None:
    selection = read_csv(REPO_ROOT / wp25.SELECTION_RELATIVE_PATH)
    inventory = api.load_inventory(REPO_ROOT)
    stems = {row[side] for row in selection for side in ("left_stem", "right_stem")}
    assert len(stems) == 307
    assert sum(
        int(inventory[row[side]]["box_count"])
        for row in selection
        for side in ("left_stem", "right_stem")
    ) == 1090
    assert sum(int(inventory[stem]["box_count"]) for stem in stems) == 671
    assert Counter(
        row[side] for row in selection for side in ("left_split", "right_split")
    ) == {"train": 468, "test": 32}
    assert Counter(row["proxy_status"] for row in selection) == {
        "strong_candidate": 142,
        "uncertain": 79,
        "adjacency_only": 29,
    }
    assert len({row["proxy_sequence_id"] for row in selection if row["proxy_sequence_id"]}) == 58


def test_decisions_are_complete_pinned_provisional_and_id_exact() -> None:
    selection = read_csv(REPO_ROOT / wp25.SELECTION_RELATIVE_PATH)
    payload, decisions = api.load_annotations(REPO_ROOT, selection)
    notes = api.load_review_notes(REPO_ROOT, selection)
    assert payload == api.annotation_payload_from_notes(notes, selection)
    assert len(decisions) == 250
    assert Counter(row["capture_hypothesis"] for row in decisions) == {
        "SAME_CAPTURE_CANDIDATE": 240,
        "NOT_RELATED": 10,
    }
    assert Counter(row["physical_sign_hypothesis"] for row in decisions) == {
        "SAME_PHYSICAL_SIGN_CANDIDATE": 240,
        "NOT_RELATED": 10,
    }
    assert Counter(row["confidence"] for row in decisions) == {"HIGH": 250}
    assert {
        row["edge_id"] for row in decisions if row["capture_hypothesis"] == "NOT_RELATED"
    } == wp25.EXPECTED_CAPTURE_NOT_RELATED_IDS
    assert all(row["reviewer"] == "PM/Codex provisional visual reviewer" for row in decisions)
    assert all(row["evidence_boundary"] == wp25.EVIDENCE_BOUNDARY for row in decisions)


def test_same_count_decision_id_swap_fails_closed() -> None:
    notes = read_csv(REPO_ROOT / wp25.REVIEW_NOTES_RELATIVE_PATH)
    swapped = copy.deepcopy(notes)
    related = next(row for row in swapped if row["edge_id"] == "edge_001155")
    unrelated = next(row for row in swapped if row["edge_id"] == "edge_001200")
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
    assert Counter(row["capture_hypothesis"] for row in swapped) == Counter(
        row["capture_hypothesis"] for row in notes
    )
    with pytest.raises(ValueError, match="NOT_RELATED IDs"):
        wp25.validate_review_decision_contract(swapped)


def test_atlas_layout_lineage_and_raw_label_binding_are_complete() -> None:
    atlas_dir = REPO_ROOT / wp25.ASSETS_RELATIVE_PATH
    api.verify_exact_atlas_roster(atlas_dir)
    assert sorted(path.name for path in atlas_dir.iterdir()) == sorted(
        api.expected_atlas_names()
    )
    layout = read_json(REPO_ROOT / wp25.LAYOUT_RELATIVE_PATH)
    assert layout["page_count"] == 50
    assert layout["pair_count"] == 250
    assert layout["pairs_per_page"] == 5
    assert layout["all_headers_complete"] is True
    assert layout["all_text_complete"] is True
    assert layout["all_bounds_fit"] is True
    assert layout["all_bbox_context_rendered"] is True
    assert layout["all_decisions_recorded"] is True
    layout_rows = [row for page in layout["pages"] for row in page["rows"]]
    assert [row["batch_position"] for row in layout_rows] == list(range(1, 251))
    for page in layout["pages"]:
        assert page["row_count"] == len(page["rows"]) == 5
        assert (page["width"], page["height"]) == (1600, 2372)
        with Image.open(REPO_ROOT / page["path"]) as image:
            assert image.size == (1600, 2372)
            image.verify()
    selection = read_csv(REPO_ROOT / wp25.SELECTION_RELATIVE_PATH)
    lineage = read_csv(REPO_ROOT / wp25.LINEAGE_RELATIVE_PATH)
    inventory = api.load_inventory(REPO_ROOT)
    assert lineage == api.derive_lineage(selection, inventory, RAW_ROOT)
    assert len(lineage) == 500
    assert Counter(row["edge_id"] for row in lineage) == {
        row["edge_id"]: 2 for row in selection
    }
    assert all(row["stem"] != "0248" for row in lineage)
    assert sum(int(inventory[row["stem"]]["box_count"]) for row in lineage) == 1090


def test_manifest_hashes_source_pins_and_governance_match() -> None:
    manifest = read_json(MANIFEST_PATH)
    pinned = {item_id: digest for item_id, _path, digest in wp25.source_contract(REPO_ROOT)}
    assert manifest["source_count"] == len(manifest["sources"]) == 72
    assert manifest["artifact_count"] == len(manifest["artifacts"]) == 56
    for record in [*manifest["sources"], *manifest["artifacts"]]:
        path = REPO_ROOT / record["path"]
        assert record["sha256"] == api.sha256_file(path)
        assert record["size"] == path.stat().st_size
        if pinned.get(record["id"]) is not None:
            assert record["sha256"] == pinned[record["id"]]
    assert api.sha256_file(REPO_ROOT / wp25.REVIEW_NOTES_RELATIVE_PATH) == (
        wp25.EXPECTED_REVIEW_NOTES_SHA256
    )
    api.validate_governance(REPO_ROOT)


def test_report_and_artifacts_preserve_evidence_boundary() -> None:
    report = (REPO_ROOT / wp25.REPORT_RELATIVE_PATH).read_text(encoding="utf-8")
    assert "# M0-WP25" in report
    assert "All 250 pairs/500 raw frames were directly inspected" in report
    assert "1146 PENDING" in report or "1,146 PENDING" in report
    assert "D-02 remains PENDING" in report
    assert "Gate 0 remains BLOCKED" in report
    assert "training_authorized=false" in report
    forbidden = {"group_id", "final_group_id", "assigned_split", "approved_split"}
    selection = read_csv(REPO_ROOT / wp25.SELECTION_RELATIVE_PATH)
    annotations = read_json(REPO_ROOT / wp25.ANNOTATIONS_RELATIVE_PATH)
    assert not forbidden & set(selection[0])
    assert all(not forbidden & set(row) for row in annotations["decisions"])


def test_wp24_and_preservation_anchors_remain_immutable() -> None:
    anchors = {
        "docs/review/generated/wp24_remaining_edge_batch_c_manifest.json": (
            wp25.WP24_MANIFEST_SHA256
        ),
        "docs/review/generated/wp24_remaining_edge_batch_c_selection.csv": (
            wp25.WP24_SELECTION_SHA256
        ),
        "docs/review/wp24_remaining_edge_review_annotations_batch_c.json": (
            wp25.WP24_ANNOTATIONS_SHA256
        ),
        "scripts/build_wp24_remaining_edge_review_batch.py": wp25.WP24_BUILDER_SHA256,
        "README.md": "9005addc5b9952b36fca7f744489270cc7507bfaad0c6a02f305954915de01a7",
        "models/VGG16_model.h5": "745cf3f6e9f5edfe32954866d93f07d9504f6bc2d4f3667c8b8f99f1c924b565",
    }
    for relative, expected in anchors.items():
        assert api.sha256_file(REPO_ROOT / relative) == expected
    proof = read_json(
        REPO_ROOT
        / "results/data_audit/DATASET01_052bc980a7206f8d/source_preservation_proof.json"
    )
    assert proof["unchanged"] is True


def test_wp25_attack_contract_has_exactly_18_unique_classes() -> None:
    assert len(WP25_ATTACK_CLASSES) == 18


@pytest.mark.parametrize("attack", sorted(WP25_ATTACK_CLASSES))
def test_verifier_fails_closed_for_18_attack_classes(
    tmp_path: Path, attack: str
) -> None:
    if attack == "manifest_path_traversal":
        payload = read_json(MANIFEST_PATH)
        payload["sources"][0]["path"] = "../outside.json"
        forged = tmp_path / "path_escape.json"
        api.write_json(forged, payload)
        result = wp25.verify(forged, REPO_ROOT, RAW_ROOT)
        assert result["valid"] is False
        assert result["errors"]
        return

    staged = stage_package(tmp_path)
    atlas_dir = tmp_path / wp25.ASSETS_RELATIVE_PATH
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
    elif attack == "atlas_root_symlink":
        copied = tmp_path / "copied_atlas"
        shutil.copytree(atlas_dir, copied)
        shutil.rmtree(atlas_dir)
        atlas_dir.symlink_to(copied, target_is_directory=True)
    elif attack in LAYOUT_ATTACKS:
        layout_path = tmp_path / wp25.LAYOUT_RELATIVE_PATH
        payload = read_json(layout_path)
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
        api.write_json(layout_path, payload)
        refresh_manifest_records(staged)
    elif attack == "page_pixel":
        with Image.open(page) as image:
            mutated = image.convert("RGB")
        pixel = mutated.getpixel((0, 0))
        mutated.putpixel((0, 0), tuple(255 - channel for channel in pixel))
        mutated.save(page, format="JPEG", quality=90, optimize=True, subsampling=1)
        refresh_manifest_records(staged)
    elif attack == "index_text":
        index_path = atlas_dir / "index.html"
        index_path.write_text(
            index_path.read_text(encoding="utf-8") + "<!-- forged -->\n",
            encoding="utf-8",
        )
        refresh_manifest_records(staged)
    else:
        selection = tmp_path / wp25.SELECTION_RELATIVE_PATH
        outside = tmp_path.parent / "outside_wp25_selection.csv"
        outside.write_bytes(selection.read_bytes())
        selection.unlink()
        selection.symlink_to(outside)
    result = wp25.verify(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert result["errors"]


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
    payload["total_artifact_bytes"] = sum(row["size"] for row in payload["artifacts"])
    forged = tmp_path / f"{collection}_{mutation}.json"
    api.write_json(forged, payload)
    result = wp25.verify(forged, REPO_ROOT, RAW_ROOT)
    assert result["valid"] is False
    assert result["errors"]


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
    forged = tmp_path / f"forged_{field}.json"
    api.write_json(forged, payload)
    result = wp25.verify(forged, REPO_ROOT, RAW_ROOT)
    assert result["valid"] is False
    assert result["errors"]


def test_review_note_anchor_blocks_coherent_decision_rollback(tmp_path: Path) -> None:
    staged = stage_package(tmp_path)
    notes_path = tmp_path / wp25.REVIEW_NOTES_RELATIVE_PATH
    notes = read_csv(notes_path)
    target = next(row for row in notes if row["edge_id"] == "edge_001200")
    target.update(
        provisional_outcome="SAME_CAPTURE_CANDIDATE",
        capture_hypothesis="SAME_CAPTURE_CANDIDATE",
        physical_sign_hypothesis="SAME_PHYSICAL_SIGN_CANDIDATE",
        rationale="Forged rollback.",
    )
    api.write_csv(notes_path, notes, api.REVIEW_NOTE_FIELDS)
    refresh_manifest_records(staged)
    result = wp25.verify(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert any("pinned source hash mismatch" in error for error in result["errors"])


def test_clean_room_rebuild_is_byte_deterministic(tmp_path: Path) -> None:
    clean_root = tmp_path / "clean"
    manifest = read_json(MANIFEST_PATH)
    for record in manifest["sources"]:
        source = REPO_ROOT / record["path"]
        target = clean_root / record["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    result = wp25.build(clean_root, RAW_ROOT)
    assert result["manifest_sha256"] == api.sha256_file(MANIFEST_PATH)
    rebuilt = read_json(clean_root / wp25.MANIFEST_RELATIVE_PATH)
    assert [
        (row["id"], row["sha256"], row["size"]) for row in rebuilt["artifacts"]
    ] == [
        (row["id"], row["sha256"], row["size"])
        for row in manifest["artifacts"]
    ]
