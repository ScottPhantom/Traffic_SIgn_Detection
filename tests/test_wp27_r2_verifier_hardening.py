from __future__ import annotations

import copy
import csv
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/build_wp27_r2_verifier_hardening.py"
SPEC = importlib.util.spec_from_file_location("build_wp27_r2_verifier_hardening", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
wp27_r2 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp27_r2
SPEC.loader.exec_module(wp27_r2)
r1 = wp27_r2.r1

RAW_ROOT = Path(
    "/Users/nguyentantai/Library/Mobile Documents/com~apple~CloudDocs/"
    "FALL 2026 KỲ 4/CPV301/Data/DATASET01/staging/052bc980a7206f8d/raw"
)
MANIFEST_PATH = REPO_ROOT / wp27_r2.MANIFEST_RELATIVE_PATH
R1_MANIFEST_PATH = REPO_ROOT / wp27_r2.R1_MANIFEST_RELATIVE_PATH

COHERENT_ATTACKS = (
    "rollback_initial_layout",
    "status_249",
    "noncanonical_whitespace",
    "layout_symlink",
    "r1_manifest_refresh_only",
    "r2_audit_tamper",
    "r2_report_tamper",
    "r1_builder_tamper",
)
WP27_R2_ATTACK_CLASSES = frozenset((*wp27_r2.TYPE_CONFUSION_PROBES, *COHERENT_ATTACKS))


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def copy_member(root: Path, relative: str) -> None:
    target = root / relative
    if target.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO_ROOT / relative, target)


def stage_package(tmp_path: Path) -> Path:
    """Copy (never hard-link) the full WP27 → R1 → R2 package so mutations stay isolated."""
    for manifest_path in (R1_MANIFEST_PATH, MANIFEST_PATH):
        manifest = read_json(manifest_path)
        for record in [*manifest["sources"], *manifest["artifacts"]]:
            copy_member(tmp_path, record["path"])
    copy_member(tmp_path, wp27_r2.R1_MANIFEST_RELATIVE_PATH)
    copy_member(tmp_path, wp27_r2.MANIFEST_RELATIVE_PATH)
    return tmp_path / wp27_r2.MANIFEST_RELATIVE_PATH


def apply_probe(layout: dict[str, Any], probe: str) -> None:
    page = layout["pages"][0]
    row = page["rows"][0]
    if probe == "pair_count_float":
        layout["pair_count"] = 250.0
    elif probe == "page_count_float":
        layout["page_count"] = 50.0
    elif probe == "pairs_per_page_float":
        layout["pairs_per_page"] = 5.0
    elif probe == "page_number_bool":
        page["page"] = True
    elif probe == "row_count_float":
        page["row_count"] = 5.0
    elif probe == "slot_bool":
        row["slot"] = True
    elif probe == "batch_position_bool":
        row["batch_position"] = True
    else:
        assert probe == "bounds_float"
        row["left_bounds"] = [float(value) for value in row["left_bounds"]]


def coherent_r1_refresh(root: Path, layout: dict[str, Any], layout_text: str | None = None) -> None:
    """Rewrite the R1 layout and refresh every dependent R1 artifact with the R1 helpers."""
    layout_path = root / r1.LAYOUT_RELATIVE_PATH
    if layout_text is None:
        r1.write_json(layout_path, layout)
    else:
        layout_path.write_text(layout_text, encoding="utf-8")
    initial_manifest = read_json(root / r1.INITIAL_MANIFEST_RELATIVE_PATH)
    roster = r1.expected_effective_roster(initial_manifest, r1.sha256_file(layout_path))
    r1.write_csv(root / r1.EFFECTIVE_ROSTER_RELATIVE_PATH, roster, r1.ROSTER_FIELDS)
    (root / r1.REPORT_RELATIVE_PATH).write_text(
        r1.render_report(
            initial_manifest,
            r1.sha256_file(layout_path),
            r1.sha256_file(root / r1.DELTA_RELATIVE_PATH),
            r1.sha256_file(root / r1.EFFECTIVE_ROSTER_RELATIVE_PATH),
        ),
        encoding="utf-8",
    )
    r1.write_json(root / r1.MANIFEST_RELATIVE_PATH, r1.build_manifest(root))


def refresh_r2_manifest(root: Path) -> None:
    """Simulate an attacker coherently refreshing the R2 manifest as well."""
    wp27_r2.write_json(root / wp27_r2.MANIFEST_RELATIVE_PATH, wp27_r2.build_manifest(root))


def test_official_r2_package_verifies_and_pins_r1() -> None:
    result = wp27_r2.verify(MANIFEST_PATH, REPO_ROOT, RAW_ROOT)
    assert result == {
        "valid": True,
        "errors": [],
        "source_count": 11,
        "artifact_count": 2,
        "effective_layout_sha256": wp27_r2.R1_LAYOUT_SHA256,
        "status": wp27_r2.STATUS,
    }
    manifest = read_json(MANIFEST_PATH)
    assert manifest["r1_manifest_sha256"] == wp27_r2.sha256_file(R1_MANIFEST_PATH)
    assert manifest["changed_predecessor_bytes"] == 0
    assert manifest["d02_status"] == "PENDING"
    assert manifest["gate0"] == "BLOCKED"
    assert manifest["split_authorized"] is False
    assert manifest["training_authorized"] is False
    assert manifest["final_group_truth_created"] is False
    assert manifest["transitive_grouping_created"] is False
    assert manifest["wp28_started"] is False
    assert manifest["residual_pending_edges"] == 646
    assert manifest["review_eligible_residual_edges"] == 644
    assert manifest["quarantined_residual_edges"] == 2


def test_r1_bytes_are_untouched_and_pinned() -> None:
    for _item_id, relative, digest in wp27_r2.R1_PINNED_FILES:
        assert wp27_r2.sha256_file(REPO_ROOT / relative) == digest
    anchors = (
        (r1.INITIAL_MANIFEST_RELATIVE_PATH, r1.INITIAL_MANIFEST_SHA256),
        (r1.INITIAL_LAYOUT_RELATIVE_PATH, r1.INITIAL_LAYOUT_SHA256),
        (wp27_r2.QA_RECORD_RELATIVE_PATH, wp27_r2.QA_RECORD_SHA256),
    )
    for relative, digest in anchors:
        assert wp27_r2.sha256_file(REPO_ROOT / relative) == digest


def test_effective_layout_is_canonical_and_type_strict_diff_is_exactly_status() -> None:
    initial_layout = read_json(REPO_ROOT / r1.INITIAL_LAYOUT_RELATIVE_PATH)
    effective_layout = read_json(REPO_ROOT / r1.LAYOUT_RELATIVE_PATH)
    assert (REPO_ROOT / r1.LAYOUT_RELATIVE_PATH).read_text(encoding="utf-8") == (
        wp27_r2.canonical_json_text(r1.corrected_layout(initial_layout))
    )
    assert wp27_r2.strict_semantic_diff(initial_layout, effective_layout) == [
        ("/status", r1.STALE_LAYOUT_STATUS, r1.EXPECTED_LAYOUT_STATUS)
    ]
    assert wp27_r2.leaf_type_counts(initial_layout) == wp27_r2.leaf_type_counts(effective_layout)
    audit = read_json(REPO_ROOT / wp27_r2.AUDIT_RELATIVE_PATH)
    assert audit["status"] == wp27_r2.AUDIT_STATUS
    assert audit["pair_count"] == 250 and type(audit["pair_count"]) is int
    assert audit["page_count"] == 50 and type(audit["page_count"]) is int
    assert [row["json_pointer"] for row in audit["type_strict_diff"]] == ["/status"]
    assert audit["exact_int_fields_checked"] == wp27_r2.validate_strict_layout(
        initial_layout, effective_layout
    )


def test_strict_diff_detects_type_only_changes_that_r1_diff_misses() -> None:
    initial_layout = read_json(REPO_ROOT / r1.INITIAL_LAYOUT_RELATIVE_PATH)
    for probe in wp27_r2.TYPE_CONFUSION_PROBES:
        effective_layout = r1.corrected_layout(initial_layout)
        apply_probe(effective_layout, probe)
        assert len(r1.semantic_diff(initial_layout, effective_layout)) == 1, probe
        assert len(wp27_r2.strict_semantic_diff(initial_layout, effective_layout)) > 1, probe
        with pytest.raises(ValueError):
            wp27_r2.validate_strict_layout(initial_layout, effective_layout)


def test_wp27_r2_attack_contract_has_exactly_16_unique_classes() -> None:
    assert len(wp27_r2.TYPE_CONFUSION_PROBES) == 8
    assert len(WP27_R2_ATTACK_CLASSES) == 16


@pytest.mark.parametrize("probe", wp27_r2.TYPE_CONFUSION_PROBES)
def test_r2_rejects_type_confusion_after_full_coherent_refresh(tmp_path: Path, probe: str) -> None:
    staged = stage_package(tmp_path)
    layout = read_json(tmp_path / r1.LAYOUT_RELATIVE_PATH)
    apply_probe(layout, probe)
    coherent_r1_refresh(tmp_path, layout)
    refresh_r2_manifest(tmp_path)
    result = wp27_r2.verify(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert "pinned sources hash mismatch: wp27_r1_corrected_layout_audit" in result["errors"]
    # Defense in depth: without the hash pins, canonical bytes and type-strict checks still fail.
    initial_layout = read_json(tmp_path / r1.INITIAL_LAYOUT_RELATIVE_PATH)
    with pytest.raises(ValueError, match="canonical serialization"):
        wp27_r2.validate_canonical_layout_bytes(tmp_path, initial_layout)
    with pytest.raises(ValueError, match="type-strict"):
        wp27_r2.validate_strict_layout(
            initial_layout, read_json(tmp_path / r1.LAYOUT_RELATIVE_PATH)
        )
    # The immutable R1 verifier still fails open on the same staged package (the QA finding).
    assert r1.verify(tmp_path / r1.MANIFEST_RELATIVE_PATH, tmp_path, RAW_ROOT)["valid"] is True


@pytest.mark.parametrize("attack", COHERENT_ATTACKS)
def test_r2_rejects_rollback_substitution_and_refresh_attacks(tmp_path: Path, attack: str) -> None:
    staged = stage_package(tmp_path)
    layout_path = tmp_path / r1.LAYOUT_RELATIVE_PATH
    if attack == "rollback_initial_layout":
        coherent_r1_refresh(tmp_path, read_json(tmp_path / r1.INITIAL_LAYOUT_RELATIVE_PATH))
        refresh_r2_manifest(tmp_path)
    elif attack == "status_249":
        layout = read_json(layout_path)
        layout["status"] = "PASS_COMPLETE_249_PAIR_COVERAGE_TEXT_BOUNDS_AND_BBOX_CONTEXT"
        coherent_r1_refresh(tmp_path, layout)
        refresh_r2_manifest(tmp_path)
    elif attack == "noncanonical_whitespace":
        layout = read_json(layout_path)
        coherent_r1_refresh(tmp_path, layout, json.dumps(layout, sort_keys=True) + "\n")
        refresh_r2_manifest(tmp_path)
    elif attack == "layout_symlink":
        layout_path.unlink()
        layout_path.symlink_to(REPO_ROOT / r1.LAYOUT_RELATIVE_PATH)
    elif attack == "r1_manifest_refresh_only":
        payload = read_json(tmp_path / r1.MANIFEST_RELATIVE_PATH)
        payload["status"] = "WP27_R1_QA_PASS"
        r1.write_json(tmp_path / r1.MANIFEST_RELATIVE_PATH, payload)
        refresh_r2_manifest(tmp_path)
    elif attack == "r2_audit_tamper":
        audit_path = tmp_path / wp27_r2.AUDIT_RELATIVE_PATH
        audit = read_json(audit_path)
        audit["exact_int_fields_checked"] += 1
        wp27_r2.write_json(audit_path, audit)
        refresh_r2_manifest(tmp_path)
    elif attack == "r2_report_tamper":
        report_path = tmp_path / wp27_r2.REPORT_RELATIVE_PATH
        report_path.write_text(
            report_path.read_text(encoding="utf-8").replace("BLOCKED", "PASSED"), encoding="utf-8"
        )
        refresh_r2_manifest(tmp_path)
    else:
        assert attack == "r1_builder_tamper"
        builder_path = tmp_path / r1.R1_BUILDER_RELATIVE_PATH
        tampered = builder_path.read_text(encoding="utf-8") + "\n# tamper\n"
        builder_path.write_text(tampered, encoding="utf-8")
        refresh_r2_manifest(tmp_path)
    result = wp27_r2.verify(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert result["errors"]


@pytest.mark.parametrize(
    "mutation",
    [
        "path_traversal",
        "absolute_path",
        "artifact_id_swap",
        "source_remove",
        "source_extra",
        "artifact_reorder",
        "pinned_source_rehash",
        "count_float",
        "flag_flip_training",
        "flag_flip_wp28",
        "size_bool",
    ],
)
def test_manifest_mutations_fail_closed(tmp_path: Path, mutation: str) -> None:
    payload = read_json(MANIFEST_PATH)
    if mutation == "path_traversal":
        payload["artifacts"][0]["path"] = "../outside.json"
    elif mutation == "absolute_path":
        payload["artifacts"][0]["path"] = str(REPO_ROOT / wp27_r2.AUDIT_RELATIVE_PATH)
    elif mutation == "artifact_id_swap":
        payload["artifacts"][0]["id"], payload["artifacts"][1]["id"] = (
            payload["artifacts"][1]["id"],
            payload["artifacts"][0]["id"],
        )
    elif mutation == "source_remove":
        payload["sources"].pop()
        payload["source_count"] -= 1
    elif mutation == "source_extra":
        payload["sources"].append(copy.deepcopy(payload["sources"][0]) | {"id": "extra"})
        payload["source_count"] += 1
    elif mutation == "artifact_reorder":
        payload["artifacts"].reverse()
    elif mutation == "pinned_source_rehash":
        payload["sources"][1]["sha256"] = "0" * 64
    elif mutation == "count_float":
        payload["source_count"] = float(payload["source_count"])
    elif mutation == "flag_flip_training":
        payload["training_authorized"] = True
    elif mutation == "flag_flip_wp28":
        payload["wp28_started"] = 0
    else:
        assert mutation == "size_bool"
        payload["artifacts"][0]["size"] = True
    forged = tmp_path / f"forged_{mutation}.json"
    wp27_r2.write_json(forged, payload)
    result = wp27_r2.verify(forged, REPO_ROOT, RAW_ROOT)
    assert result["valid"] is False
    assert result["errors"]


def test_clean_room_rebuild_is_byte_deterministic(tmp_path: Path) -> None:
    clean = tmp_path / "clean"
    r1_manifest = read_json(R1_MANIFEST_PATH)
    r2_manifest = read_json(MANIFEST_PATH)
    for record in [*r1_manifest["sources"], *r1_manifest["artifacts"], *r2_manifest["sources"]]:
        copy_member(clean, record["path"])
    copy_member(clean, wp27_r2.R1_MANIFEST_RELATIVE_PATH)
    assert not (clean / wp27_r2.MANIFEST_RELATIVE_PATH).exists()
    result = wp27_r2.build(clean, RAW_ROOT)
    assert result["manifest_sha256"] == wp27_r2.sha256_file(MANIFEST_PATH)
    for record in r2_manifest["artifacts"]:
        assert wp27_r2.sha256_file(clean / record["path"]) == record["sha256"]


def test_no_wp28_authorization_is_created_by_r2() -> None:
    manifest = read_json(MANIFEST_PATH)
    assert manifest["wp28_started"] is False
    assert manifest["d02_status"] == "PENDING"
    assert manifest["gate0"] == "BLOCKED"
    assert read_csv(REPO_ROOT / r1.DELTA_RELATIVE_PATH) == [
        {
            "json_pointer": "/status",
            "initial_value": r1.STALE_LAYOUT_STATUS,
            "effective_value": r1.EXPECTED_LAYOUT_STATUS,
            "change_type": "REPLACE_STALE_INHERITED_COUNT_WITH_EXACT_PAIR_COUNT",
        }
    ]
