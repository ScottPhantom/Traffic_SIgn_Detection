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
SCRIPT_PATH = REPO_ROOT / "scripts/build_wp25_r1_remaining_edge_review_batch.py"
SPEC = importlib.util.spec_from_file_location(
    "build_wp25_r1_remaining_edge_review_batch", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
wp25_r1 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp25_r1
SPEC.loader.exec_module(wp25_r1)
wp25_r1._configure()
api = wp25_r1.core

RAW_ROOT = Path(
    "/Users/nguyentantai/Library/Mobile Documents/com~apple~CloudDocs/"
    "FALL 2026 KỲ 4/CPV301/Data/DATASET01/staging/052bc980a7206f8d/raw"
)
MANIFEST_PATH = REPO_ROOT / wp25_r1.MANIFEST_RELATIVE_PATH

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
WP25_R1_ATTACK_CLASSES = frozenset(
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
    staged = tmp_path / wp25_r1.MANIFEST_RELATIVE_PATH
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


def test_official_r1_package_verifies_with_exact_rosters() -> None:
    result = wp25_r1.verify(MANIFEST_PATH, REPO_ROOT, RAW_ROOT)
    assert result == {
        "valid": True,
        "errors": [],
        "source_count": 78,
        "artifact_count": 56,
        "status": wp25_r1.PACKAGE_STATUS,
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


def test_selection_and_lineage_are_unchanged_from_initial_wp25() -> None:
    initial = read_csv(
        REPO_ROOT / "docs/review/generated/wp25_remaining_edge_batch_d_selection.csv"
    )
    corrected = read_csv(REPO_ROOT / wp25_r1.SELECTION_RELATIVE_PATH)
    assert len(initial) == len(corrected) == 250
    for old, new in zip(initial, corrected, strict=True):
        restored = dict(new)
        restored["wp12_atlas_page"] = restored["wp12_atlas_page"].replace(
            wp25_r1.ASSETS_RELATIVE_PATH, wp25_r1.INITIAL_ASSETS_RELATIVE_PATH
        )
        restored["evidence_boundary"] = wp25_r1.INITIAL_EVIDENCE_BOUNDARY
        assert restored == old
    assert corrected[143]["edge_id"] == "edge_001358"
    assert corrected[143]["wp5_review_order"] == "1928"
    assert corrected[143]["wp12_atlas_page"].endswith("page_029.jpg")
    assert corrected[143]["wp12_atlas_slot"] == "4"
    assert api.sha256_file(REPO_ROOT / wp25_r1.SELECTION_RELATIVE_PATH) == (
        wp25_r1.INITIAL_SELECTION_SHA256
    )
    assert all(
        "0248" not in {row["left_stem"], row["right_stem"]}
        and row["proxy_sequence_id"] != "proxy_sequence_0050"
        for row in corrected
    )
    lineage = read_csv(REPO_ROOT / wp25_r1.LINEAGE_RELATIVE_PATH)
    assert len(lineage) == 500
    assert [
        (row["edge_id"], row["side"], row["stem"], row["image_sha256"], row["label_sha256"])
        for row in lineage
    ] == [
        (row["edge_id"], row["side"], row["stem"], row["image_sha256"], row["label_sha256"])
        for row in read_csv(
            REPO_ROOT
            / "docs/review/generated/wp25_remaining_edge_batch_d_source_lineage.csv"
        )
    ]


def test_only_edge_001358_semantics_changed_and_tallies_are_correct() -> None:
    old_payload = read_json(
        REPO_ROOT / "docs/review/wp25_remaining_edge_review_annotations_batch_d.json"
    )
    new_payload = read_json(REPO_ROOT / wp25_r1.ANNOTATIONS_RELATIVE_PATH)
    old_by_id = {row["edge_id"]: row for row in old_payload["decisions"]}
    new_by_id = {row["edge_id"]: row for row in new_payload["decisions"]}
    decision_fields = (
        "provisional_outcome",
        "capture_hypothesis",
        "physical_sign_hypothesis",
        "confidence",
        "rationale",
    )
    changed = {
        edge_id
        for edge_id in old_by_id
        if any(old_by_id[edge_id][field] != new_by_id[edge_id][field] for field in decision_fields)
    }
    assert changed == {"edge_001358"}
    decisions = list(new_by_id.values())
    assert Counter(row["capture_hypothesis"] for row in decisions) == {
        "SAME_CAPTURE_CANDIDATE": 241,
        "NOT_RELATED": 9,
    }
    assert Counter(row["physical_sign_hypothesis"] for row in decisions) == {
        "SAME_PHYSICAL_SIGN_CANDIDATE": 241,
        "NOT_RELATED": 9,
    }
    assert Counter(row["confidence"] for row in decisions) == {"HIGH": 250}
    corrected = new_by_id["edge_001358"]
    assert corrected["capture_hypothesis"] == "SAME_CAPTURE_CANDIDATE"
    assert corrected["physical_sign_hypothesis"] == "SAME_PHYSICAL_SIGN_CANDIDATE"
    assert "same moving camera advances within one road scene" in corrected["rationale"]
    assert "same class-5 physical sign" in corrected["rationale"]
    assert "MAE 12.005787" in corrected["rationale"]
    assert "dHash 18" in corrected["rationale"]
    assert "histogram 0.99375935" in corrected["rationale"]
    selection = read_csv(REPO_ROOT / wp25_r1.SELECTION_RELATIVE_PATH)
    source = next(row for row in selection if row["edge_id"] == "edge_001358")
    assert (RAW_ROOT / source["left_label_path"]).read_text(encoding="utf-8") == (
        "5 0.388021 0.303704 0.036458 0.055556\n"
    )
    assert (RAW_ROOT / source["right_label_path"]).read_text(encoding="utf-8") == (
        "5 0.406250 0.313889 0.037500 0.046296\n"
    )


def test_edge_001358_cannot_regress_to_not_related_or_old_rationale() -> None:
    selection = read_csv(REPO_ROOT / wp25_r1.SELECTION_RELATIVE_PATH)
    _payload, decisions = api.load_annotations(REPO_ROOT, selection)
    regressed = copy.deepcopy(decisions)
    target = next(row for row in regressed if row["edge_id"] == "edge_001358")
    target.update(
        provisional_outcome="NOT_RELATED",
        capture_hypothesis="NOT_RELATED",
        physical_sign_hypothesis="NOT_RELATED",
        rationale=(
            "Direct PM atlas review shows discontinuous scene and non-matching physical signs "
            "across stems 1365/1366; sequence evidence was context only."
        ),
    )
    with pytest.raises(ValueError, match="WP25-R1"):
        wp25_r1.validate_review_decision_contract(regressed)


def test_all_9_not_related_rows_have_explicit_scene_or_sign_change_rationale() -> None:
    payload = read_json(REPO_ROOT / wp25_r1.ANNOTATIONS_RELATIVE_PATH)
    not_related = [
        row for row in payload["decisions"] if row["capture_hypothesis"] == "NOT_RELATED"
    ]
    assert len(not_related) == 9
    assert {row["edge_id"] for row in not_related} == wp25_r1.EXPECTED_CAPTURE_NOT_RELATED_IDS
    assert all(
        "discontinuous scene and non-matching physical signs" in row["rationale"]
        for row in not_related
    )


def test_initial_failed_package_and_preservation_anchors_are_immutable() -> None:
    anchors = {
        "docs/review/generated/wp25_remaining_edge_batch_d_manifest.json": (
            wp25_r1.INITIAL_MANIFEST_SHA256
        ),
        "docs/review/generated/wp25_remaining_edge_batch_d_selection.csv": (
            wp25_r1.INITIAL_SELECTION_SHA256
        ),
        "docs/review/wp25_remaining_edge_review_annotations_batch_d.json": (
            wp25_r1.INITIAL_ANNOTATIONS_SHA256
        ),
        "docs/review/wp25_remaining_edge_review_notes_batch_d.csv": (
            wp25_r1.INITIAL_REVIEW_NOTES_SHA256
        ),
        "scripts/build_wp25_remaining_edge_review_batch.py": wp25_r1.INITIAL_BUILDER_SHA256,
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
    assert api.sha256_file(
        REPO_ROOT
        / "results/data_audit/DATASET01_052bc980a7206f8d/source_preservation_proof.json"
    ) == "5ca3e769b9197cad19bcb75f553dd59fee6e3035e0cc86cd9693737f84a713d7"


def test_hash_delta_enumerates_manifest_and_all_56_artifacts() -> None:
    rows = read_csv(
        REPO_ROOT / "docs/review/generated/wp25_r1_artifact_hash_delta.csv"
    )
    assert len(rows) == 57
    assert rows[0]["artifact_id"] == "manifest"
    assert rows[0]["initial_sha256"] == wp25_r1.INITIAL_MANIFEST_SHA256
    assert rows[0]["r1_sha256"] == api.sha256_file(MANIFEST_PATH)
    by_id = {row["artifact_id"]: row for row in rows}
    assert by_id["selection"]["changed"] == "false"
    assert sum(row["changed"] == "true" for row in rows) == 56
    manifest = read_json(MANIFEST_PATH)
    assert [row["artifact_id"] for row in rows[1:]] == [
        record["id"] for record in manifest["artifacts"]
    ]
    assert [row["r1_sha256"] for row in rows[1:]] == [
        record["sha256"] for record in manifest["artifacts"]
    ]


def test_qa_record_pins_exact_finding_and_no_wp26_boundary() -> None:
    text = (REPO_ROOT / wp25_r1.QA_RECORD_RELATIVE_PATH).read_text(encoding="utf-8")
    assert "exactly one P1 finding; P0/P2/P3 findings: zero" in text
    assert "does not authorize WP26" in text
    assert "241 same, 9 `NOT_RELATED`, 250 `HIGH`" in text


def test_wp25_r1_attack_contract_has_exactly_18_unique_classes() -> None:
    assert len(WP25_R1_ATTACK_CLASSES) == 18


@pytest.mark.parametrize("attack", sorted(WP25_R1_ATTACK_CLASSES))
def test_r1_verifier_fails_closed_for_18_attack_classes(
    tmp_path: Path, attack: str
) -> None:
    if attack == "manifest_path_traversal":
        payload = read_json(MANIFEST_PATH)
        payload["sources"][0]["path"] = "../outside.json"
        path = tmp_path / "path_escape.json"
        api.write_json(path, payload)
        result = wp25_r1.verify(path, REPO_ROOT, RAW_ROOT)
        assert result["valid"] is False
        assert result["errors"]
        return

    staged = stage_package(tmp_path)
    atlas_dir = tmp_path / wp25_r1.ASSETS_RELATIVE_PATH
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
        path = tmp_path / wp25_r1.LAYOUT_RELATIVE_PATH
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
    elif attack == "page_pixel":
        with Image.open(page) as image:
            mutated = image.convert("RGB")
        pixel = mutated.getpixel((0, 0))
        mutated.putpixel((0, 0), tuple(255 - channel for channel in pixel))
        mutated.save(page, format="JPEG", quality=90, optimize=True, subsampling=1)
        refresh_manifest_records(staged)
    elif attack == "index_text":
        path = atlas_dir / "index.html"
        path.write_text(path.read_text(encoding="utf-8") + "<!-- forged -->\n", encoding="utf-8")
        refresh_manifest_records(staged)
    else:
        selection = tmp_path / wp25_r1.SELECTION_RELATIVE_PATH
        outside = tmp_path / "outside.csv"
        outside.write_bytes(selection.read_bytes())
        selection.unlink()
        selection.symlink_to(outside)

    result = wp25_r1.verify(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert result["errors"]


def test_correction_overlay_anchor_fails_after_coherent_manifest_rehash(
    tmp_path: Path,
) -> None:
    staged = stage_package(tmp_path)
    correction = tmp_path / wp25_r1.REVIEW_NOTES_RELATIVE_PATH
    correction.write_text(
        correction.read_text(encoding="utf-8").replace(
            "SAME_CAPTURE_CANDIDATE", "NOT_RELATED", 1
        ),
        encoding="utf-8",
    )
    refresh_manifest_records(staged)
    result = wp25_r1.verify(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert any("pinned source hash mismatch" in error for error in result["errors"])


def test_clean_room_rebuild_is_56_of_56_byte_deterministic(tmp_path: Path) -> None:
    clean_root = tmp_path / "clean"
    manifest = read_json(MANIFEST_PATH)
    for record in manifest["sources"]:
        source = REPO_ROOT / record["path"]
        target = clean_root / record["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    result = wp25_r1.build(clean_root, RAW_ROOT)
    assert result["manifest_sha256"] == api.sha256_file(MANIFEST_PATH)
    rebuilt = read_json(clean_root / wp25_r1.MANIFEST_RELATIVE_PATH)
    assert len(rebuilt["artifacts"]) == 56
    assert [
        (row["id"], row["sha256"], row["size"]) for row in rebuilt["artifacts"]
    ] == [
        (row["id"], row["sha256"], row["size"])
        for row in manifest["artifacts"]
    ]
