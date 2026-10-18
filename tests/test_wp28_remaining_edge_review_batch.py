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
SCRIPT_PATH = REPO_ROOT / "scripts/build_wp28_remaining_edge_review_batch.py"
SPEC = importlib.util.spec_from_file_location("build_wp28_remaining_edge_review_batch", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
wp28 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp28
SPEC.loader.exec_module(wp28)
wp28._configure()
api = wp28.core

RAW_ROOT = Path(
    "/Users/nguyentantai/Library/Mobile Documents/com~apple~CloudDocs/"
    "FALL 2026 KỲ 4/CPV301/Data/DATASET01/staging/052bc980a7206f8d/raw"
)
MANIFEST_PATH = REPO_ROOT / wp28.MANIFEST_RELATIVE_PATH

ATLAS_ATTACKS = ("extra_page", "missing_page", "page_symlink", "atlas_root_symlink")
LAYOUT_ATTACKS = ("left_bounds", "text_bounds", "bbox_placement", "page_coverage_geometry")
TYPE_ATTACKS = (
    "status_stale_176",
    "pair_count_float",
    "page_count_float",
    "page_number_bool",
    "slot_bool",
    "batch_position_float",
    "bounds_float",
    "annotation_position_float",
    "manifest_count_float",
    "manifest_flag_int",
)
BYTE_ATTACKS = ("page_pixel", "index_text")
PATH_ATTACKS = ("manifest_path_traversal", "selection_symlink")
WP28_ATTACK_CLASSES = frozenset(
    (*ATLAS_ATTACKS, *LAYOUT_ATTACKS, *TYPE_ATTACKS, *BYTE_ATTACKS, *PATH_ATTACKS)
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
        target = tmp_path / record["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / record["path"], target)
    staged = tmp_path / wp28.MANIFEST_RELATIVE_PATH
    staged.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(MANIFEST_PATH, staged)
    return staged


def refresh_manifest_records(staged_manifest: Path) -> None:
    """Simulate an attacker coherently refreshing every manifest hash and size."""
    root = staged_manifest.parents[3]
    payload = read_json(staged_manifest)
    for collection in ("sources", "artifacts"):
        for record in payload[collection]:
            path = root / record["path"]
            if path.is_file():
                record["sha256"] = api.sha256_file(path)
                record["size"] = path.stat().st_size
    payload["total_artifact_bytes"] = sum(record["size"] for record in payload["artifacts"])
    api.write_json(staged_manifest, payload)


def test_official_package_verifies_with_exact_rosters() -> None:
    result = wp28.verify(MANIFEST_PATH, REPO_ROOT, RAW_ROOT)
    assert result == {
        "valid": True,
        "errors": [],
        "source_count": 97,
        "artifact_count": 56,
        "status": "WP28_AWAITING_QA_REVIEW",
    }
    manifest = read_json(MANIFEST_PATH)
    assert manifest["selection_count"] == 250
    assert manifest["lineage_record_count"] == 500
    assert manifest["selected_endpoint_box_count"] == 1464
    assert manifest["atlas_page_count"] == 50
    assert manifest["quarantined_stem_0248_selected"] is False
    assert manifest["gate0"] == "BLOCKED"
    assert manifest["d02_status"] == "PENDING"
    assert manifest["split_authorized"] is False
    assert manifest["training_authorized"] is False
    assert manifest["final_group_truth_created"] is False
    assert manifest["transitive_grouping_created"] is False


def test_selection_is_exact_next_250_after_qa_passed_predecessor_chain() -> None:
    actual = read_csv(REPO_ROOT / wp28.SELECTION_RELATIVE_PATH)
    expected, _inventory = wp28.derive_selection(REPO_ROOT, RAW_ROOT)
    assert actual == expected
    assert len(actual) == len({row["edge_id"] for row in actual}) == 250
    assert (actual[0]["edge_id"], actual[0]["wp5_review_order"]) == ("edge_002214", "2535")
    assert (actual[0]["left_stem"], actual[0]["right_stem"]) == ("2239", "2240")
    assert (actual[-1]["edge_id"], actual[-1]["wp5_review_order"]) == ("edge_002587", "2784")
    assert (actual[-1]["left_stem"], actual[-1]["right_stem"]) == ("2612", "2613")
    assert all(row["cross_split"] == "False" for row in actual)
    assert all(row["wp5_review_status"] == "PENDING" for row in actual)
    assert all("0248" not in {row["left_stem"], row["right_stem"]} for row in actual)
    assert all(row["proxy_sequence_id"] != "proxy_sequence_0050" for row in actual)
    assert all(
        row["sequence_context_boundary"] == "CONTEXT_ONLY_NOT_USED_TO_DERIVE_EDGE_DECISION"
        for row in actual
    )


def test_residual_derivation_is_independent_and_exact() -> None:
    """Re-derive the residual queue with plain CSV logic, without the builder helpers."""
    generated = REPO_ROOT / "docs/review/generated"
    rows = read_csv(generated / "wp5_provisional_edge_decisions.csv")
    assert len(rows) == 3178
    assert sum(row["review_status"] == "PENDING" for row in rows) == 3172
    cross_split = {
        row["edge_id"]
        for name in (
            "wp7_batch_a",
            "wp12_batch_b",
            "wp13_batch_c",
            "wp14_batch_d",
            "wp15_batch_e",
        )
        for row in read_csv(generated / f"{name}_selection.csv")
    }
    predecessors = [
        [row["edge_id"] for row in read_csv(generated / f"{name}_selection.csv")]
        for name in (
            "wp22_remaining_edge_batch_a",
            "wp23_r1_remaining_edge_batch_b",
            "wp24_remaining_edge_batch_c",
            "wp25_r1_remaining_edge_batch_d",
            "wp26_remaining_edge_batch_e",
            "wp27_remaining_edge_batch_f",
        )
    ]
    base_eligible = [
        row["edge_id"]
        for row in rows
        if row["review_status"] == "PENDING"
        and row["edge_id"] not in cross_split
        and "0248" not in {row["left_stem"], row["right_stem"]}
    ]
    for index, roster in enumerate(predecessors):
        assert roster == base_eligible[index * 250 : (index + 1) * 250]
    excluded = cross_split | {edge for roster in predecessors for edge in roster}
    residual = [
        row for row in rows if row["review_status"] == "PENDING" and row["edge_id"] not in excluded
    ]
    quarantined = [
        row["edge_id"] for row in residual if "0248" in {row["left_stem"], row["right_stem"]}
    ]
    eligible = [row["edge_id"] for row in residual if row["edge_id"] not in quarantined]
    selection = [row["edge_id"] for row in read_csv(REPO_ROOT / wp28.SELECTION_RELATIVE_PATH)]
    assert len(residual) == 646
    assert quarantined == ["edge_000242", "edge_000243"]
    assert len(eligible) == 644
    assert selection == eligible[:250]
    assert not set(selection) & excluded
    assert len(eligible[250:]) + len(quarantined) == 396


def test_selection_acceptance_tallies_are_reconstructed() -> None:
    selection = read_csv(REPO_ROOT / wp28.SELECTION_RELATIVE_PATH)
    inventory = api.load_inventory(REPO_ROOT)
    stems = {row[side] for row in selection for side in ("left_stem", "right_stem")}
    assert len(stems) == 305
    assert (
        sum(
            int(inventory[row[side]]["box_count"])
            for row in selection
            for side in ("left_stem", "right_stem")
        )
        == 1464
    )
    assert sum(int(inventory[stem]["box_count"]) for stem in stems) == 889
    assert Counter(row[side] for row in selection for side in ("left_split", "right_split")) == {
        "train": 484,
        "test": 16,
    }
    assert Counter(row["proxy_status"] for row in selection) == {
        "strong_candidate": 143,
        "uncertain": 85,
        "adjacency_only": 22,
    }
    assert len({row["proxy_sequence_id"] for row in selection if row["proxy_sequence_id"]}) == 54


def test_decisions_are_complete_pinned_provisional_and_id_exact() -> None:
    selection = read_csv(REPO_ROOT / wp28.SELECTION_RELATIVE_PATH)
    payload, decisions = api.load_annotations(REPO_ROOT, selection)
    notes = api.load_review_notes(REPO_ROOT, selection)
    assert (
        wp28.strict_semantic_diff(api.annotation_payload_from_notes(notes, selection), payload)
        == []
    )
    assert len(decisions) == 250
    assert Counter(row["capture_hypothesis"] for row in decisions) == {
        "SAME_CAPTURE_CANDIDATE": 250
    }
    assert Counter(row["physical_sign_hypothesis"] for row in decisions) == {
        "SAME_PHYSICAL_SIGN_CANDIDATE": 236,
        "NOT_RELATED": 14,
    }
    assert Counter(row["confidence"] for row in decisions) == {"HIGH": 248, "MEDIUM": 2}
    assert {
        row["edge_id"] for row in decisions if row["physical_sign_hypothesis"] == "NOT_RELATED"
    } == wp28.EXPECTED_PHYSICAL_SIGN_NOT_RELATED_IDS
    assert {
        row["edge_id"] for row in decisions if row["confidence"] == "MEDIUM"
    } == wp28.EXPECTED_MEDIUM_CONFIDENCE_IDS
    # Capture and physical-sign relations stay separate: every NOT_RELATED sign is same-capture.
    assert all(
        row["capture_hypothesis"] == "SAME_CAPTURE_CANDIDATE"
        for row in decisions
        if row["physical_sign_hypothesis"] == "NOT_RELATED"
    )
    assert all(
        "raw crop checked" in row["rationale"]
        for row in decisions
        if row["physical_sign_hypothesis"] == "NOT_RELATED"
    )
    assert all(row["reviewer"] == "PM/Codex provisional visual reviewer" for row in decisions)
    assert all(row["evidence_boundary"] == wp28.EVIDENCE_BOUNDARY for row in decisions)


@pytest.mark.parametrize("swap", ["physical_id_swap", "medium_id_swap"])
def test_same_count_decision_id_swap_fails_closed(swap: str) -> None:
    notes = read_csv(REPO_ROOT / wp28.REVIEW_NOTES_RELATIVE_PATH)
    swapped = copy.deepcopy(notes)
    plain = next(row for row in swapped if row["edge_id"] == "edge_002214")
    if swap == "physical_id_swap":
        special = next(row for row in swapped if row["edge_id"] == "edge_002227")
        plain["physical_sign_hypothesis"], special["physical_sign_hypothesis"] = (
            special["physical_sign_hypothesis"],
            plain["physical_sign_hypothesis"],
        )
        match = "physical NOT_RELATED IDs"
    else:
        special = next(row for row in swapped if row["edge_id"] == "edge_002306")
        plain["confidence"], special["confidence"] = special["confidence"], plain["confidence"]
        match = "MEDIUM confidence IDs"
    with pytest.raises(ValueError, match=match):
        wp28.validate_review_decision_contract(swapped)


def test_layout_status_is_exact_and_inherited_verifier_differs_only_by_that_constant() -> None:
    layout = read_json(REPO_ROOT / wp28.LAYOUT_RELATIVE_PATH)
    assert layout["status"] == "PASS_COMPLETE_250_PAIR_COVERAGE_TEXT_BOUNDS_AND_BBOX_CONTEXT"
    wp28.validate_strict_layout(layout)
    original = wp28.ORIGINAL_WP15_VERIFY_MANIFEST.__code__
    derived = wp28.EXACT_STATUS_VERIFY_MANIFEST.__code__
    assert derived.co_code == original.co_code
    assert derived.co_names == original.co_names
    changed = [
        (left, right)
        for left, right in zip(original.co_consts, derived.co_consts, strict=True)
        if left != right
    ]
    assert changed == [(wp28.INHERITED_STALE_LAYOUT_STATUS, wp28.EXPECTED_LAYOUT_STATUS)]
    # The scoped substitution never leaks into the immutable predecessor modules.
    assert wp28.WP15_MODULE.verify_manifest is wp28.ORIGINAL_WP15_VERIFY_MANIFEST


def test_atlas_layout_lineage_and_raw_label_binding_are_complete() -> None:
    atlas_dir = REPO_ROOT / wp28.ASSETS_RELATIVE_PATH
    api.verify_exact_atlas_roster(atlas_dir)
    assert sorted(path.name for path in atlas_dir.iterdir()) == sorted(api.expected_atlas_names())
    layout = read_json(REPO_ROOT / wp28.LAYOUT_RELATIVE_PATH)
    assert (layout["page_count"], layout["pair_count"], layout["pairs_per_page"]) == (50, 250, 5)
    layout_rows = [row for page in layout["pages"] for row in page["rows"]]
    assert [row["batch_position"] for row in layout_rows] == list(range(1, 251))
    for page in layout["pages"]:
        assert page["row_count"] == len(page["rows"]) == 5
        with Image.open(REPO_ROOT / page["path"]) as image:
            assert image.size == (page["width"], page["height"])
            image.verify()
    selection = read_csv(REPO_ROOT / wp28.SELECTION_RELATIVE_PATH)
    lineage = read_csv(REPO_ROOT / wp28.LINEAGE_RELATIVE_PATH)
    inventory = api.load_inventory(REPO_ROOT)
    assert lineage == api.derive_lineage(selection, inventory, RAW_ROOT)
    assert len(lineage) == 500
    assert Counter(row["edge_id"] for row in lineage) == {row["edge_id"]: 2 for row in selection}
    assert all(row["stem"] != "0248" for row in lineage)


def test_predecessor_chain_and_preservation_anchors_are_immutable() -> None:
    generated = "docs/review/generated"
    anchors = {
        f"{generated}/wp27_remaining_edge_batch_f_manifest.json": wp28.WP27_MANIFEST_SHA256,
        f"{generated}/wp27_remaining_edge_batch_f_selection.csv": wp28.WP27_SELECTION_SHA256,
        "docs/review/wp27_remaining_edge_review_annotations_batch_f.json": (
            wp28.WP27_ANNOTATIONS_SHA256
        ),
        "scripts/build_wp27_remaining_edge_review_batch.py": wp28.WP27_BUILDER_SHA256,
        f"{generated}/wp27_r1_layout_correction_manifest.json": wp28.WP27_R1_MANIFEST_SHA256,
        f"{generated}/wp27_r2_verifier_hardening_manifest.json": wp28.WP27_R2_MANIFEST_SHA256,
        "scripts/build_wp27_r2_verifier_hardening.py": wp28.WP27_R2_BUILDER_SHA256,
        "tests/test_wp27_r2_verifier_hardening.py": wp28.WP27_R2_TEST_SHA256,
        "README.md": "9005addc5b9952b36fca7f744489270cc7507bfaad0c6a02f305954915de01a7",
        "models/VGG16_model.h5": "745cf3f6e9f5edfe32954866d93f07d9504f6bc2d4f3667c8b8f99f1c924b565",
        "results/data_audit/DATASET01_052bc980a7206f8d/source_preservation_proof.json": (
            "5ca3e769b9197cad19bcb75f553dd59fee6e3035e0cc86cd9693737f84a713d7"
        ),
    }
    for relative, expected in anchors.items():
        assert api.sha256_file(REPO_ROOT / relative) == expected, relative
    manifest = read_json(MANIFEST_PATH)
    pinned = {item_id: digest for item_id, _path, digest in wp28.source_contract(REPO_ROOT)}
    for record in manifest["sources"]:
        if pinned.get(record["id"]) is not None:
            assert record["sha256"] == pinned[record["id"]]
    assert {"wp27_r1_manifest", "wp27_r2_manifest", "wp27_r2_builder"} <= set(pinned)


def test_report_and_artifacts_preserve_evidence_boundary() -> None:
    report = (REPO_ROOT / wp28.REPORT_RELATIVE_PATH).read_text(encoding="utf-8")
    assert "# M0-WP28" in report
    assert "All 250 pairs/500 raw frames were directly inspected" in report
    assert "646 unique non-cross-split PENDING edges" in report
    assert "396 PENDING" in report
    assert "D-02 remains PENDING" in report
    assert "Gate 0 remains BLOCKED" in report
    assert "training_authorized=false" in report
    assert "VGG16" not in report
    forbidden = {"group_id", "final_group_id", "assigned_split", "approved_split"}
    selection = read_csv(REPO_ROOT / wp28.SELECTION_RELATIVE_PATH)
    annotations = read_json(REPO_ROOT / wp28.ANNOTATIONS_RELATIVE_PATH)
    assert not forbidden & set(selection[0])
    assert all(not forbidden & set(row) for row in annotations["decisions"])


def test_wp28_attack_contract_has_exactly_22_unique_classes() -> None:
    assert len(WP28_ATTACK_CLASSES) == 22


@pytest.mark.parametrize("attack", sorted(WP28_ATTACK_CLASSES))
def test_verifier_fails_closed_for_attack_classes(tmp_path: Path, attack: str) -> None:
    if attack == "manifest_path_traversal":
        payload = read_json(MANIFEST_PATH)
        payload["sources"][0]["path"] = "../outside.json"
        forged = tmp_path / "path_escape.json"
        api.write_json(forged, payload)
        result = wp28.verify(forged, REPO_ROOT, RAW_ROOT)
        assert result["valid"] is False and result["errors"]
        return
    if attack in {"manifest_count_float", "manifest_flag_int"}:
        payload = read_json(MANIFEST_PATH)
        if attack == "manifest_count_float":
            payload["selection_count"] = 250.0
        else:
            payload["training_authorized"] = 0
        forged = tmp_path / f"{attack}.json"
        api.write_json(forged, payload)
        result = wp28.verify(forged, REPO_ROOT, RAW_ROOT)
        assert result["valid"] is False and result["errors"]
        return

    staged = stage_package(tmp_path)
    atlas_dir = tmp_path / wp28.ASSETS_RELATIVE_PATH
    page = atlas_dir / "page_001.jpg"
    layout_path = tmp_path / wp28.LAYOUT_RELATIVE_PATH
    if attack == "extra_page":
        (atlas_dir / "unexpected.txt").write_text("unexpected", encoding="utf-8")
    elif attack == "missing_page":
        page.unlink()
    elif attack == "page_symlink":
        page.unlink()
        page.symlink_to("page_002.jpg")
    elif attack == "atlas_root_symlink":
        copied = tmp_path / "copied_atlas"
        shutil.copytree(atlas_dir, copied)
        shutil.rmtree(atlas_dir)
        atlas_dir.symlink_to(copied, target_is_directory=True)
    elif attack in LAYOUT_ATTACKS or attack in TYPE_ATTACKS:
        if attack == "annotation_position_float":
            annotations_path = tmp_path / wp28.ANNOTATIONS_RELATIVE_PATH
            annotations = read_json(annotations_path)
            annotations["decisions"][0]["batch_position"] = 1.0
            api.write_json(annotations_path, annotations)
        else:
            payload = read_json(layout_path)
            row = payload["pages"][0]["rows"][0]
            if attack == "left_bounds":
                row["left_bounds"][2] += 1
            elif attack == "text_bounds":
                row["text_bounds"][3] -= 1
            elif attack == "bbox_placement":
                row["bbox_overlay_rendered"] = False
            elif attack == "page_coverage_geometry":
                payload["pages"][0]["rows"].pop()
            elif attack == "status_stale_176":
                payload["status"] = wp28.INHERITED_STALE_LAYOUT_STATUS
            elif attack == "pair_count_float":
                payload["pair_count"] = 250.0
            elif attack == "page_count_float":
                payload["page_count"] = 50.0
            elif attack == "page_number_bool":
                payload["pages"][0]["page"] = True
            elif attack == "slot_bool":
                row["slot"] = True
            elif attack == "batch_position_float":
                row["batch_position"] = 1.0
            else:
                assert attack == "bounds_float"
                row["left_bounds"] = [float(value) for value in row["left_bounds"]]
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
            index_path.read_text(encoding="utf-8") + "<!-- forged -->\n", encoding="utf-8"
        )
        refresh_manifest_records(staged)
    else:
        assert attack == "selection_symlink"
        selection = tmp_path / wp28.SELECTION_RELATIVE_PATH
        outside = tmp_path.parent / f"outside_{tmp_path.name}_selection.csv"
        outside.write_bytes(selection.read_bytes())
        selection.unlink()
        selection.symlink_to(outside)
    result = wp28.verify(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert result["errors"]


@pytest.mark.parametrize("collection", ["sources", "artifacts"])
@pytest.mark.parametrize("mutation", ["remove", "duplicate", "reorder", "extra"])
def test_manifest_rejects_roster_mutations(tmp_path: Path, collection: str, mutation: str) -> None:
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
    result = wp28.verify(forged, REPO_ROOT, RAW_ROOT)
    assert result["valid"] is False
    assert result["errors"]


def test_review_note_anchor_blocks_coherent_decision_rollback(tmp_path: Path) -> None:
    staged = stage_package(tmp_path)
    notes_path = tmp_path / wp28.REVIEW_NOTES_RELATIVE_PATH
    notes = read_csv(notes_path)
    target = next(row for row in notes if row["edge_id"] == "edge_002227")
    target.update(
        physical_sign_hypothesis="SAME_PHYSICAL_SIGN_CANDIDATE", rationale="Forged rollback."
    )
    api.write_csv(notes_path, notes, api.REVIEW_NOTE_FIELDS)
    refresh_manifest_records(staged)
    result = wp28.verify(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert any("pinned source hash mismatch" in error for error in result["errors"])


def test_no_wp29_artifacts_or_authorization_are_created() -> None:
    assert not list((REPO_ROOT / "docs/review").glob("**/*wp29*"))
    assert not list((REPO_ROOT / "scripts").glob("*wp29*"))
    assert not list((REPO_ROOT / "tests").glob("*wp29*"))
    manifest = read_json(MANIFEST_PATH)
    assert manifest["gate0"] == "BLOCKED"
    assert manifest["d02_status"] == "PENDING"
    assert manifest["split_authorized"] is False
    assert manifest["training_authorized"] is False


def test_clean_room_rebuild_is_byte_deterministic(tmp_path: Path) -> None:
    clean_root = tmp_path / "clean"
    manifest = read_json(MANIFEST_PATH)
    for record in manifest["sources"]:
        target = clean_root / record["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / record["path"], target)
    result = wp28.build(clean_root, RAW_ROOT)
    assert result["manifest_sha256"] == api.sha256_file(MANIFEST_PATH)
    rebuilt = read_json(clean_root / wp28.MANIFEST_RELATIVE_PATH)
    assert [(row["id"], row["sha256"], row["size"]) for row in rebuilt["artifacts"]] == [
        (row["id"], row["sha256"], row["size"]) for row in manifest["artifacts"]
    ]
