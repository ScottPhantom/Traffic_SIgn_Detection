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
SCRIPT_PATH = REPO_ROOT / "scripts/build_wp28_r2_remaining_edge_review_batch.py"
SPEC = importlib.util.spec_from_file_location(
    "build_wp28_r2_remaining_edge_review_batch", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
wp28_r2 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp28_r2
SPEC.loader.exec_module(wp28_r2)
wp28_r2._configure()
api = wp28_r2.core
wp28 = wp28_r2.wp28

RAW_ROOT = Path(
    "/Users/nguyentantai/Library/Mobile Documents/com~apple~CloudDocs/"
    "FALL 2026 KỲ 4/CPV301/Data/DATASET01/staging/052bc980a7206f8d/raw"
)
MANIFEST_PATH = REPO_ROOT / wp28_r2.MANIFEST_RELATIVE_PATH
INITIAL_PREFIX = "docs/review/generated/wp28_remaining_edge_batch_g"

JSON_ATTACKS = (
    "manifest_dupkey_training",
    "manifest_dupkey_benign",
    "manifest_reformat",
    "annotations_dupkey_status",
    "annotations_reformat",
    "layout_dupkey",
    "layout_reformat",
    "manifest_crlf",
    "manifest_cr",
    "annotations_crlf",
    "annotations_cr",
)
TYPE_ATTACKS = (
    "layout_pair_count_float",
    "layout_slot_bool",
    "layout_row_count_six",
    "annotation_position_float",
    "manifest_count_float",
    "manifest_flag_int",
)
INTEGRITY_ATTACKS = (
    "rollback_to_initial_decision",
    "overlay_second_row",
    "page_pixel",
    "index_text",
    "selection_symlink",
    "manifest_path_traversal",
)
WP28_R2_ATTACK_CLASSES = frozenset((*JSON_ATTACKS, *TYPE_ATTACKS, *INTEGRITY_ATTACKS))


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
    staged = tmp_path / wp28_r2.MANIFEST_RELATIVE_PATH
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


def prepend_key(text: str, key_value: str) -> str:
    assert text.startswith("{\n")
    return "{\n  " + key_value + ",\n" + text[2:]


def test_official_r1_package_verifies_with_exact_rosters() -> None:
    result = wp28_r2.verify(MANIFEST_PATH, REPO_ROOT, RAW_ROOT)
    assert result == {
        "valid": True,
        "errors": [],
        "source_count": 109,
        "artifact_count": 56,
        "status": "WP28_R2_AWAITING_QA_REVIEW",
    }
    manifest = read_json(MANIFEST_PATH)
    assert manifest["selection_count"] == 250
    assert manifest["selected_endpoint_box_count"] == 1464
    assert manifest["quarantined_stem_0248_selected"] is False
    assert manifest["gate0"] == "BLOCKED"
    assert manifest["d02_status"] == "PENDING"
    assert manifest["split_authorized"] is False
    assert manifest["training_authorized"] is False
    assert manifest["final_group_truth_created"] is False
    assert manifest["transitive_grouping_created"] is False


def test_initial_wp28_package_is_immutable_and_still_verifies() -> None:
    anchors = {
        f"{INITIAL_PREFIX}_manifest.json": wp28_r2.INITIAL_MANIFEST_SHA256,
        f"{INITIAL_PREFIX}_selection.csv": wp28_r2.INITIAL_SELECTION_SHA256,
        "docs/review/wp28_remaining_edge_review_annotations_batch_g.json": (
            wp28_r2.INITIAL_ANNOTATIONS_SHA256
        ),
        "docs/review/wp28_remaining_edge_review_notes_batch_g.csv": (
            wp28_r2.INITIAL_REVIEW_NOTES_SHA256
        ),
        "scripts/build_wp28_remaining_edge_review_batch.py": wp28_r2.INITIAL_BUILDER_SHA256,
        "tests/test_wp28_remaining_edge_review_batch.py": wp28_r2.INITIAL_TEST_SHA256,
        wp28_r2.QA_RECORD_RELATIVE_PATH: wp28_r2.QA_CORRECTION_RECORD_SHA256,
        wp28_r2.R1_QA_RECORD_RELATIVE_PATH: wp28_r2.R1_QA_RECORD_SHA256,
        "docs/review/generated/wp28_r1_remaining_edge_batch_g_manifest.json": (
            wp28_r2.R1_MANIFEST_SHA256
        ),
        "docs/review/wp28_r1_remaining_edge_review_annotations_batch_g.json": (
            wp28_r2.R1_ANNOTATIONS_SHA256
        ),
        "scripts/build_wp28_r1_remaining_edge_review_batch.py": wp28_r2.R1_BUILDER_SHA256,
        "tests/test_wp28_r1_remaining_edge_review_batch.py": wp28_r2.R1_TEST_SHA256,
        wp28_r2.REVIEW_NOTES_RELATIVE_PATH: wp28_r2.EXPECTED_REVIEW_NOTES_SHA256,
    }
    for relative, expected in anchors.items():
        assert api.sha256_file(REPO_ROOT / relative) == expected, relative
    # Use an independent builder instance: R2 patches its own chain's review-note loader.
    spec = importlib.util.spec_from_file_location(
        "wp28_r1_test_independent_initial",
        REPO_ROOT / "scripts/build_wp28_remaining_edge_review_batch.py",
    )
    assert spec is not None and spec.loader is not None
    independent = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = independent
    spec.loader.exec_module(independent)
    initial = independent.verify(REPO_ROOT / f"{INITIAL_PREFIX}_manifest.json", REPO_ROOT, RAW_ROOT)
    assert initial["valid"] is True, initial["errors"]


def test_selection_rebinds_every_row_to_the_r2_atlas_and_boundary() -> None:
    actual = read_csv(REPO_ROOT / wp28_r2.SELECTION_RELATIVE_PATH)
    initial = read_csv(REPO_ROOT / f"{INITIAL_PREFIX}_selection.csv")
    expected, _inventory = wp28_r2.derive_selection(REPO_ROOT, RAW_ROOT)
    assert actual == expected
    assert [row["edge_id"] for row in actual] == [row["edge_id"] for row in initial]
    assert (actual[0]["edge_id"], actual[-1]["edge_id"]) == ("edge_002214", "edge_002587")
    for new, old in zip(actual, initial, strict=True):
        differing = {key for key in new if new[key] != old[key]}
        # Exactly these two fields must differ on every row (R1's subset check hid a no-op).
        assert differing == {"wp12_atlas_page", "evidence_boundary"}
        assert new["wp12_atlas_page"].startswith(f"{wp28_r2.ASSETS_RELATIVE_PATH}/page_")
        assert new["evidence_boundary"] == wp28_r2.EVIDENCE_BOUNDARY
    assert all("0248" not in {row["left_stem"], row["right_stem"]} for row in actual)
    assert all(row["proxy_sequence_id"] != "proxy_sequence_0050" for row in actual)


def test_every_evidence_reference_cites_the_r2_atlas() -> None:
    annotations = read_json(REPO_ROOT / wp28_r2.ANNOTATIONS_RELATIVE_PATH)
    atlas_refs = [
        ref for row in annotations["decisions"] for ref in row["evidence_refs"] if "/assets/" in ref
    ]
    assert len(atlas_refs) == 250
    assert all(ref.startswith(f"{wp28_r2.ASSETS_RELATIVE_PATH}/page_") for ref in atlas_refs)
    corrected = next(row for row in annotations["decisions"] if row["edge_id"] == "edge_002306")
    assert corrected["evidence_refs"][-1] == (f"{wp28_r2.ASSETS_RELATIVE_PATH}/page_013.jpg#slot=5")
    r1 = read_json(REPO_ROOT / "docs/review/wp28_r1_remaining_edge_review_annotations_batch_g.json")
    fields = ("capture_hypothesis", "physical_sign_hypothesis", "confidence", "rationale")
    assert all(
        all(new[field] == old[field] for field in fields)
        for new, old in zip(annotations["decisions"], r1["decisions"], strict=True)
    )


def test_decisions_change_exactly_one_edge_from_initial_wp28() -> None:
    selection = read_csv(REPO_ROOT / wp28_r2.SELECTION_RELATIVE_PATH)
    payload = read_json(REPO_ROOT / wp28_r2.ANNOTATIONS_RELATIVE_PATH)
    decisions = payload["decisions"]
    assert [row["edge_id"] for row in decisions] == [row["edge_id"] for row in selection]
    initial = read_json(
        REPO_ROOT / "docs/review/wp28_remaining_edge_review_annotations_batch_g.json"
    )
    fields = ("capture_hypothesis", "physical_sign_hypothesis", "confidence", "rationale")
    changed = [
        new["edge_id"]
        for new, old in zip(decisions, initial["decisions"], strict=True)
        if any(new[field] != old[field] for field in fields)
    ]
    assert changed == ["edge_002306"]
    corrected = next(row for row in decisions if row["edge_id"] == "edge_002306")
    assert corrected["capture_hypothesis"] == "SAME_CAPTURE_CANDIDATE"
    assert corrected["physical_sign_hypothesis"] == "NOT_RELATED"
    assert corrected["confidence"] == "HIGH"
    assert Counter(row["capture_hypothesis"] for row in decisions) == {
        "SAME_CAPTURE_CANDIDATE": 250
    }
    assert Counter(row["physical_sign_hypothesis"] for row in decisions) == {
        "SAME_PHYSICAL_SIGN_CANDIDATE": 235,
        "NOT_RELATED": 15,
    }
    assert Counter(row["confidence"] for row in decisions) == {"HIGH": 249, "MEDIUM": 1}
    assert {row["edge_id"] for row in decisions if row["confidence"] == "MEDIUM"} == {"edge_002507"}
    assert payload["status"] == wp28_r2.ANNOTATION_STATUS
    assert all(row["evidence_boundary"] == wp28_r2.EVIDENCE_BOUNDARY for row in decisions)


def test_correction_raw_label_evidence_matches_qa_finding() -> None:
    labels = {
        stem: (RAW_ROOT / f"archive/labels/{stem}.txt").read_text(encoding="utf-8").splitlines()
        for stem in ("2331", "2332")
    }
    assert "10 0.482812 0.273148 0.028125 0.05" in labels["2331"]
    assert any(line.startswith("18 ") for line in labels["2331"])
    assert "10 0.526563 0.388889 0.019792 0.033333" in labels["2332"]
    assert not any(line.startswith("18 ") for line in labels["2332"])


@pytest.mark.parametrize("swap", ["physical_id_swap", "medium_id_swap"])
def test_same_count_decision_id_swap_fails_closed(swap: str) -> None:
    selection = read_csv(REPO_ROOT / wp28_r2.SELECTION_RELATIVE_PATH)
    notes = wp28_r2.load_review_notes(REPO_ROOT, selection)
    swapped = copy.deepcopy(notes)
    plain = next(row for row in swapped if row["edge_id"] == "edge_002214")
    if swap == "physical_id_swap":
        special = next(row for row in swapped if row["edge_id"] == "edge_002306")
        plain["physical_sign_hypothesis"], special["physical_sign_hypothesis"] = (
            special["physical_sign_hypothesis"],
            plain["physical_sign_hypothesis"],
        )
        match = "physical NOT_RELATED IDs"
    else:
        special = next(row for row in swapped if row["edge_id"] == "edge_002507")
        plain["confidence"], special["confidence"] = special["confidence"], plain["confidence"]
        match = "MEDIUM confidence IDs"
    with pytest.raises(ValueError, match=match):
        wp28_r2.validate_review_decision_contract(swapped)


def test_layout_atlas_and_text_fit_are_complete() -> None:
    layout = wp28_r2.load_canonical_json(REPO_ROOT / wp28_r2.LAYOUT_RELATIVE_PATH, "layout")
    wp28.validate_strict_layout(layout)
    assert layout["status"] == "PASS_COMPLETE_250_PAIR_COVERAGE_TEXT_BOUNDS_AND_BBOX_CONTEXT"
    atlas_dir = REPO_ROOT / wp28_r2.ASSETS_RELATIVE_PATH
    api.verify_exact_atlas_roster(atlas_dir)
    for page in layout["pages"]:
        assert page["row_count"] == len(page["rows"]) == 5
        with Image.open(REPO_ROOT / page["path"]) as image:
            rgb = image.convert("RGB")
            width, height = rgb.size
            # No rendered text may touch the right page edge (the WP25-R1 status string clipped).
            edge = [rgb.getpixel((x, y)) for y in range(height) for x in range(width - 6, width)]
            assert not any(sum(pixel) < 450 for pixel in edge), page["path"]
    index = (atlas_dir / "index.html").read_text(encoding="utf-8")
    assert "M0-WP28-R2" in index


def test_report_and_governance_boundary() -> None:
    report = (REPO_ROOT / wp28_r2.REPORT_RELATIVE_PATH).read_text(encoding="utf-8")
    assert "# M0-WP28-R2" in report
    assert "edge_002306" in report
    assert "396 PENDING" in report
    assert "D-02 remains PENDING" in report
    assert "Gate 0 remains BLOCKED" in report
    assert "training_authorized=false" in report
    assert "VGG16" not in report
    forbidden = {"group_id", "final_group_id", "assigned_split", "approved_split"}
    annotations = read_json(REPO_ROOT / wp28_r2.ANNOTATIONS_RELATIVE_PATH)
    assert all(not forbidden & set(row) for row in annotations["decisions"])


def test_wp28_r2_attack_contract_has_exactly_23_unique_classes() -> None:
    assert len(WP28_R2_ATTACK_CLASSES) == 23


@pytest.mark.parametrize("attack", sorted(WP28_R2_ATTACK_CLASSES))
def test_r1_verifier_fails_closed(tmp_path: Path, attack: str) -> None:
    if attack in {"manifest_path_traversal", "manifest_count_float", "manifest_flag_int"}:
        payload = read_json(MANIFEST_PATH)
        if attack == "manifest_path_traversal":
            payload["sources"][0]["path"] = "../outside.json"
        elif attack == "manifest_count_float":
            payload["selection_count"] = 250.0
        else:
            payload["training_authorized"] = 0
        forged = tmp_path / f"{attack}.json"
        api.write_json(forged, payload)
        result = wp28_r2.verify(forged, REPO_ROOT, RAW_ROOT)
        assert result["valid"] is False and result["errors"]
        return

    staged = stage_package(tmp_path)
    layout_path = tmp_path / wp28_r2.LAYOUT_RELATIVE_PATH
    annotations_path = tmp_path / wp28_r2.ANNOTATIONS_RELATIVE_PATH
    overlay_path = tmp_path / wp28_r2.REVIEW_NOTES_RELATIVE_PATH
    atlas_dir = tmp_path / wp28_r2.ASSETS_RELATIVE_PATH
    refresh = True
    if attack == "manifest_dupkey_training":
        text = staged.read_text(encoding="utf-8")
        staged.write_text(
            prepend_key(text, '"training_authorized": true, "d02_status": "APPROVED"'),
            encoding="utf-8",
        )
        refresh = False
    elif attack == "manifest_dupkey_benign":
        staged.write_text(
            prepend_key(staged.read_text(encoding="utf-8"), '"gate0": "BLOCKED"'), encoding="utf-8"
        )
        refresh = False
    elif attack == "manifest_reformat":
        staged.write_text(json.dumps(read_json(staged), sort_keys=True) + "\n", encoding="utf-8")
        refresh = False
    elif attack == "annotations_dupkey_status":
        annotations_path.write_text(
            prepend_key(annotations_path.read_text(encoding="utf-8"), '"status": "D02_APPROVED"'),
            encoding="utf-8",
        )
    elif attack == "annotations_reformat":
        annotations_path.write_text(
            json.dumps(read_json(annotations_path)) + "\n", encoding="utf-8"
        )
    elif attack == "layout_dupkey":
        layout_path.write_text(
            prepend_key(layout_path.read_text(encoding="utf-8"), '"pair_count": 250'),
            encoding="utf-8",
        )
    elif attack in {"manifest_crlf", "manifest_cr"}:
        newline = "\r\n" if attack == "manifest_crlf" else "\r"
        staged.write_bytes(staged.read_bytes().replace(b"\n", newline.encode()))
        refresh = False
    elif attack in {"annotations_crlf", "annotations_cr"}:
        newline = "\r\n" if attack == "annotations_crlf" else "\r"
        annotations_path.write_bytes(annotations_path.read_bytes().replace(b"\n", newline.encode()))
    elif attack == "layout_reformat":
        layout_path.write_text(json.dumps(read_json(layout_path)) + "\n", encoding="utf-8")
    elif attack in {"layout_pair_count_float", "layout_slot_bool", "layout_row_count_six"}:
        layout = read_json(layout_path)
        if attack == "layout_pair_count_float":
            layout["pair_count"] = 250.0
        elif attack == "layout_slot_bool":
            layout["pages"][0]["rows"][0]["slot"] = True
        else:
            layout["pages"][0]["row_count"] = 6
        api.write_json(layout_path, layout)
    elif attack == "annotation_position_float":
        annotations = read_json(annotations_path)
        annotations["decisions"][0]["batch_position"] = 1.0
        api.write_json(annotations_path, annotations)
    elif attack == "rollback_to_initial_decision":
        rows = read_csv(overlay_path)
        rows[0].update(
            corrected_physical_sign_hypothesis="SAME_PHYSICAL_SIGN_CANDIDATE", confidence="MEDIUM"
        )
        api.write_csv(overlay_path, rows, wp28_r2.CORRECTION_FIELDS)
    elif attack == "overlay_second_row":
        rows = read_csv(overlay_path)
        extra = dict(rows[0], edge_id="edge_002214")
        api.write_csv(overlay_path, [*rows, extra], wp28_r2.CORRECTION_FIELDS)
    elif attack == "page_pixel":
        page = atlas_dir / "page_013.jpg"
        with Image.open(page) as image:
            mutated = image.convert("RGB")
        pixel = mutated.getpixel((0, 0))
        mutated.putpixel((0, 0), tuple(255 - channel for channel in pixel))
        mutated.save(page, format="JPEG", quality=90, optimize=True, subsampling=1)
    elif attack == "index_text":
        index_path = atlas_dir / "index.html"
        index_path.write_text(
            index_path.read_text(encoding="utf-8") + "<!-- forged -->\n", encoding="utf-8"
        )
    else:
        assert attack == "selection_symlink"
        selection = tmp_path / wp28_r2.SELECTION_RELATIVE_PATH
        outside = tmp_path.parent / f"outside_{tmp_path.name}_selection.csv"
        outside.write_bytes(selection.read_bytes())
        selection.unlink()
        selection.symlink_to(outside)
        refresh = False
    if refresh:
        refresh_manifest_records(staged)
    result = wp28_r2.verify(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert result["errors"]


def test_canonical_loader_rejects_duplicate_keys_and_reformatting(tmp_path: Path) -> None:
    good = tmp_path / "good.json"
    api.write_json(good, {"a": 1, "b": [1, 2]})
    assert wp28_r2.load_canonical_json(good, "probe") == {"a": 1, "b": [1, 2]}
    dup = tmp_path / "dup.json"
    dup.write_text('{\n  "a": 1,\n  "a": 2\n}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate JSON key"):
        wp28_r2.load_canonical_json(dup, "probe")
    loose = tmp_path / "loose.json"
    loose.write_text('{"a": 1, "b": [1, 2]}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="not canonically serialized"):
        wp28_r2.load_canonical_json(loose, "probe")


def test_no_wp29_artifacts_or_authorization_are_created() -> None:
    assert not list((REPO_ROOT / "docs/review").glob("**/*wp29*"))
    assert not list((REPO_ROOT / "scripts").glob("*wp29*"))
    assert not list((REPO_ROOT / "tests").glob("*wp29*"))
    manifest = read_json(MANIFEST_PATH)
    assert manifest["d02_status"] == "PENDING"
    assert manifest["training_authorized"] is False


def test_clean_room_rebuild_is_byte_deterministic(tmp_path: Path) -> None:
    clean_root = tmp_path / "clean"
    manifest = read_json(MANIFEST_PATH)
    for record in manifest["sources"]:
        target = clean_root / record["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / record["path"], target)
    result = wp28_r2.build(clean_root, RAW_ROOT)
    assert result["manifest_sha256"] == api.sha256_file(MANIFEST_PATH)
    rebuilt = read_json(clean_root / wp28_r2.MANIFEST_RELATIVE_PATH)
    assert [(row["id"], row["sha256"], row["size"]) for row in rebuilt["artifacts"]] == [
        (row["id"], row["sha256"], row["size"]) for row in manifest["artifacts"]
    ]
