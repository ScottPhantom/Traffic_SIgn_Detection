from __future__ import annotations

import copy
import csv
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/build_wp27_r1_layout_correction.py"
SPEC = importlib.util.spec_from_file_location("build_wp27_r1_layout_correction", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
wp27_r1 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp27_r1
SPEC.loader.exec_module(wp27_r1)

RAW_ROOT = Path(
    "/Users/nguyentantai/Library/Mobile Documents/com~apple~CloudDocs/"
    "FALL 2026 KỲ 4/CPV301/Data/DATASET01/staging/052bc980a7206f8d/raw"
)
MANIFEST_PATH = REPO_ROOT / wp27_r1.MANIFEST_RELATIVE_PATH

LAYOUT_STATUS_ATTACKS = (
    "inherited_176",
    "status_249",
    "status_251",
    "status_missing",
    "status_bool",
    "status_integer",
)
LAYOUT_COUNT_ATTACKS = (
    "pair_count_249",
    "pair_count_251",
    "pair_count_missing",
    "pair_count_string",
    "page_count_49",
    "page_count_51",
    "page_count_missing",
    "page_count_bool",
)
COHERENT_ATTACKS = (
    "rollback_initial_layout",
    "layout_substitution",
    "layout_id_swap",
    "layout_symlink",
    "manifest_path_traversal",
    "artifact_id_swap",
    "coherent_rehash_stale",
)
WP27_R1_ATTACK_CLASSES = frozenset(
    (*LAYOUT_STATUS_ATTACKS, *LAYOUT_COUNT_ATTACKS, *COHERENT_ATTACKS)
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
    seen: set[str] = set()
    for record in [*manifest["sources"], *manifest["artifacts"]]:
        if record["path"] in seen:
            continue
        seen.add(record["path"])
        source = REPO_ROOT / record["path"]
        target = tmp_path / record["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        os.link(source, target)
    staged = tmp_path / wp27_r1.MANIFEST_RELATIVE_PATH
    staged.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(MANIFEST_PATH, staged)
    return staged


def detach(path: Path) -> None:
    payload = path.read_bytes()
    path.unlink()
    path.write_bytes(payload)


def refresh_manifest_artifacts(staged_manifest: Path) -> None:
    root = staged_manifest.parents[3]
    payload = read_json(staged_manifest)
    for record in payload["artifacts"]:
        path = root / record["path"]
        if path.is_file():
            record["sha256"] = wp27_r1.sha256_file(path)
            record["size"] = path.stat().st_size
    payload["total_artifact_bytes"] = sum(record["size"] for record in payload["artifacts"])
    wp27_r1.write_json(staged_manifest, payload)


def test_official_r1_package_verifies_with_exact_rosters() -> None:
    result = wp27_r1.verify(MANIFEST_PATH, REPO_ROOT, RAW_ROOT)
    assert result == {
        "valid": True,
        "errors": [],
        "source_count": 151,
        "artifact_count": 4,
        "effective_artifact_count": 56,
        "changed_artifact_count": 1,
        "status": wp27_r1.STATUS,
    }
    manifest = read_json(MANIFEST_PATH)
    assert manifest["initial_source_count"] == 88
    assert manifest["initial_artifact_count"] == 56
    assert manifest["effective_artifact_count"] == 56
    assert manifest["changed_artifact_count"] == 1
    assert manifest["canonical_wp5_pending_unchanged"] == 3172
    assert manifest["all_wp5_sequences_pending"] == 589
    assert manifest["residual_pending_edges"] == 646
    assert manifest["review_eligible_residual_edges"] == 644
    assert manifest["quarantined_residual_edges"] == 2
    assert manifest["d02_status"] == "PENDING"
    assert manifest["gate0"] == "BLOCKED"
    assert manifest["split_authorized"] is False
    assert manifest["training_authorized"] is False
    assert manifest["final_group_truth_created"] is False
    assert manifest["transitive_grouping_created"] is False
    assert manifest["wp28_started"] is False


def test_historical_verifier_accepts_stale_176_but_r1_requires_exact_250() -> None:
    historical = wp27_r1.initial.verify(
        REPO_ROOT / wp27_r1.INITIAL_MANIFEST_RELATIVE_PATH, REPO_ROOT, RAW_ROOT
    )
    assert historical["valid"] is True
    assert historical["errors"] == []
    initial_layout = read_json(REPO_ROOT / wp27_r1.INITIAL_LAYOUT_RELATIVE_PATH)
    effective_layout = read_json(REPO_ROOT / wp27_r1.LAYOUT_RELATIVE_PATH)
    assert initial_layout["status"] == wp27_r1.STALE_LAYOUT_STATUS
    assert initial_layout["pair_count"] == 250
    assert effective_layout["status"] == wp27_r1.EXPECTED_LAYOUT_STATUS
    assert effective_layout["pair_count"] == 250
    with pytest.raises(ValueError, match="exact 250-pair"):
        wp27_r1.validate_effective_layout(initial_layout)


def test_layout_semantic_delta_is_exactly_one_field() -> None:
    initial_layout = read_json(REPO_ROOT / wp27_r1.INITIAL_LAYOUT_RELATIVE_PATH)
    effective_layout = read_json(REPO_ROOT / wp27_r1.LAYOUT_RELATIVE_PATH)
    assert wp27_r1.semantic_diff(initial_layout, effective_layout) == [
        (
            "/status",
            wp27_r1.STALE_LAYOUT_STATUS,
            wp27_r1.EXPECTED_LAYOUT_STATUS,
        )
    ]
    assert read_csv(REPO_ROOT / wp27_r1.DELTA_RELATIVE_PATH) == [
        {
            "json_pointer": "/status",
            "initial_value": wp27_r1.STALE_LAYOUT_STATUS,
            "effective_value": wp27_r1.EXPECTED_LAYOUT_STATUS,
            "change_type": "REPLACE_STALE_INHERITED_COUNT_WITH_EXACT_PAIR_COUNT",
        }
    ]


def test_effective_roster_preserves_all_unaffected_bytes_and_exact_ids() -> None:
    initial_manifest = read_json(REPO_ROOT / wp27_r1.INITIAL_MANIFEST_RELATIVE_PATH)
    roster = read_csv(REPO_ROOT / wp27_r1.EFFECTIVE_ROSTER_RELATIVE_PATH)
    assert len(roster) == len(initial_manifest["artifacts"]) == 56
    assert [row["artifact_id"] for row in roster] == [
        record["id"] for record in initial_manifest["artifacts"]
    ]
    changed = [row for row in roster if row["relationship"] == "CORRECTED_STATUS_FIELD_ONLY"]
    unchanged = [
        row
        for row in roster
        if row["relationship"] == "BYTE_IDENTICAL_IMMUTABLE_INITIAL_ARTIFACT"
    ]
    assert [row["artifact_id"] for row in changed] == ["layout_audit"]
    assert len(unchanged) == 55
    assert all(row["initial_path"] == row["effective_path"] for row in unchanged)
    assert all(row["initial_sha256"] == row["effective_sha256"] for row in unchanged)
    assert {row["artifact_id"] for row in unchanged} >= {
        "annotations",
        "selection",
        "source_lineage",
        "atlas_index",
        *(f"atlas_page_{page:03d}" for page in range(1, 51)),
    }
    for row in roster:
        assert wp27_r1.sha256_file(REPO_ROOT / row["initial_path"]) == row["initial_sha256"]
        assert wp27_r1.sha256_file(REPO_ROOT / row["effective_path"]) == row["effective_sha256"]


def test_initial_wp27_and_preservation_anchors_are_immutable() -> None:
    anchors = {
        wp27_r1.INITIAL_MANIFEST_RELATIVE_PATH: wp27_r1.INITIAL_MANIFEST_SHA256,
        wp27_r1.INITIAL_LAYOUT_RELATIVE_PATH: wp27_r1.INITIAL_LAYOUT_SHA256,
        wp27_r1.INITIAL_BUILDER_RELATIVE_PATH: wp27_r1.INITIAL_BUILDER_SHA256,
        wp27_r1.INITIAL_TEST_RELATIVE_PATH: wp27_r1.INITIAL_TEST_SHA256,
        "README.md": wp27_r1.README_SHA256,
        "models/VGG16_model.h5": wp27_r1.MODEL_SHA256,
        "results/data_audit/DATASET01_052bc980a7206f8d/source_preservation_proof.json": (
            wp27_r1.PRESERVATION_SHA256
        ),
    }
    for relative, digest in anchors.items():
        assert wp27_r1.sha256_file(REPO_ROOT / relative) == digest
    proof = read_json(
        REPO_ROOT
        / "results/data_audit/DATASET01_052bc980a7206f8d/source_preservation_proof.json"
    )
    assert proof["unchanged"] is True


def test_manifest_source_contract_pins_initial_and_effective_rosters() -> None:
    manifest = read_json(MANIFEST_PATH)
    expected_sources = wp27_r1.source_contract(REPO_ROOT)
    expected_artifacts = wp27_r1.artifact_contract(REPO_ROOT)
    assert len(expected_sources) == len(manifest["sources"]) == 151
    assert len(expected_artifacts) == len(manifest["artifacts"]) == 4
    assert [row["id"] for row in manifest["sources"]] == [row[0] for row in expected_sources]
    assert [row["id"] for row in manifest["artifacts"]] == [row[0] for row in expected_artifacts]
    assert len({row["path"] for row in manifest["sources"]}) == 151
    assert len({row["path"] for row in manifest["artifacts"]}) == 4


def test_wp27_r1_attack_contract_has_exactly_21_unique_classes() -> None:
    assert len(WP27_R1_ATTACK_CLASSES) == 21


@pytest.mark.parametrize("attack", sorted(WP27_R1_ATTACK_CLASSES))
def test_r1_verifier_rejects_status_count_rollback_substitution_and_manifest_attacks(
    tmp_path: Path, attack: str
) -> None:
    if attack == "manifest_path_traversal":
        payload = read_json(MANIFEST_PATH)
        payload["artifacts"][0]["path"] = "../outside.json"
        forged = tmp_path / "path_escape.json"
        wp27_r1.write_json(forged, payload)
        result = wp27_r1.verify(forged, REPO_ROOT, RAW_ROOT)
        assert result["valid"] is False
        assert result["errors"]
        return
    if attack == "artifact_id_swap":
        payload = read_json(MANIFEST_PATH)
        payload["artifacts"][0]["id"], payload["artifacts"][1]["id"] = (
            payload["artifacts"][1]["id"],
            payload["artifacts"][0]["id"],
        )
        forged = tmp_path / "id_swap.json"
        wp27_r1.write_json(forged, payload)
        result = wp27_r1.verify(forged, REPO_ROOT, RAW_ROOT)
        assert result["valid"] is False
        assert result["errors"]
        return

    staged = stage_package(tmp_path)
    layout_path = tmp_path / wp27_r1.LAYOUT_RELATIVE_PATH
    if attack == "layout_symlink":
        layout_path.unlink()
        layout_path.symlink_to(tmp_path / wp27_r1.INITIAL_LAYOUT_RELATIVE_PATH)
        result = wp27_r1.verify(staged, tmp_path, RAW_ROOT)
        assert result["valid"] is False
        assert result["errors"]
        return

    detach(layout_path)
    layout = read_json(layout_path)
    if attack in {"inherited_176", "rollback_initial_layout", "layout_substitution"}:
        layout = read_json(tmp_path / wp27_r1.INITIAL_LAYOUT_RELATIVE_PATH)
    elif attack == "status_249":
        layout["status"] = "PASS_COMPLETE_249_PAIR_COVERAGE_TEXT_BOUNDS_AND_BBOX_CONTEXT"
    elif attack == "status_251":
        layout["status"] = "PASS_COMPLETE_251_PAIR_COVERAGE_TEXT_BOUNDS_AND_BBOX_CONTEXT"
    elif attack == "status_missing":
        layout.pop("status")
    elif attack == "status_bool":
        layout["status"] = True
    elif attack == "status_integer":
        layout["status"] = 250
    elif attack == "pair_count_249":
        layout["pair_count"] = 249
    elif attack == "pair_count_251":
        layout["pair_count"] = 251
    elif attack == "pair_count_missing":
        layout.pop("pair_count")
    elif attack == "pair_count_string":
        layout["pair_count"] = "250"
    elif attack == "page_count_49":
        layout["page_count"] = 49
    elif attack == "page_count_51":
        layout["page_count"] = 51
    elif attack == "page_count_missing":
        layout.pop("page_count")
    elif attack == "page_count_bool":
        layout["page_count"] = True
    elif attack == "layout_id_swap":
        layout["pages"][0]["rows"][0]["edge_id"], layout["pages"][0]["rows"][1]["edge_id"] = (
            layout["pages"][0]["rows"][1]["edge_id"],
            layout["pages"][0]["rows"][0]["edge_id"],
        )
    else:
        assert attack == "coherent_rehash_stale"
        layout["status"] = wp27_r1.STALE_LAYOUT_STATUS
        # Simulate an attacker refreshing every directly dependent R1 artifact and manifest hash.
        delta_path = tmp_path / wp27_r1.DELTA_RELATIVE_PATH
        roster_path = tmp_path / wp27_r1.EFFECTIVE_ROSTER_RELATIVE_PATH
        report_path = tmp_path / wp27_r1.REPORT_RELATIVE_PATH
        for path in (delta_path, roster_path, report_path):
            detach(path)
        wp27_r1.write_csv(
            delta_path,
            [
                {
                    "json_pointer": "/status",
                    "initial_value": wp27_r1.STALE_LAYOUT_STATUS,
                    "effective_value": wp27_r1.STALE_LAYOUT_STATUS,
                    "change_type": "FORGED_COHERENT_ROLLBACK",
                }
            ],
            wp27_r1.DELTA_FIELDS,
        )
        forged_roster = read_csv(roster_path)
        target = next(row for row in forged_roster if row["artifact_id"] == "layout_audit")
        target["effective_sha256"] = wp27_r1.sha256_file(
            tmp_path / wp27_r1.INITIAL_LAYOUT_RELATIVE_PATH
        )
        wp27_r1.write_csv(roster_path, forged_roster, wp27_r1.ROSTER_FIELDS)
        report_path.write_text("forged coherent rollback\n", encoding="utf-8")
    wp27_r1.write_json(layout_path, layout)
    refresh_manifest_artifacts(staged)
    result = wp27_r1.verify(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False
    assert result["errors"]


@pytest.mark.parametrize("collection", ["sources", "artifacts"])
@pytest.mark.parametrize("mutation", ["remove", "duplicate", "reorder", "extra"])
def test_manifest_rejects_exact_roster_mutations(
    tmp_path: Path, collection: str, mutation: str
) -> None:
    payload = read_json(MANIFEST_PATH)
    if mutation == "remove":
        payload[collection].pop()
    elif mutation == "duplicate":
        payload[collection].append(copy.deepcopy(payload[collection][0]))
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
                "sha256": wp27_r1.sha256_file(REPO_ROOT / "PROJECT_MEMORY.md"),
                "size": (REPO_ROOT / "PROJECT_MEMORY.md").stat().st_size,
            }
        )
    payload[f"{collection[:-1]}_count"] = len(payload[collection])
    payload["total_artifact_bytes"] = sum(row["size"] for row in payload["artifacts"])
    forged = tmp_path / f"{collection}_{mutation}.json"
    wp27_r1.write_json(forged, payload)
    result = wp27_r1.verify(forged, REPO_ROOT, RAW_ROOT)
    assert result["valid"] is False
    assert result["errors"]


@pytest.mark.parametrize(
    "field",
    [
        "initial_source_count",
        "initial_artifact_count",
        "effective_artifact_count",
        "changed_artifact_count",
        "source_count",
        "artifact_count",
        "total_artifact_bytes",
        "residual_pending_edges",
        "review_eligible_residual_edges",
    ],
)
def test_manifest_rejects_forged_counts(tmp_path: Path, field: str) -> None:
    payload = read_json(MANIFEST_PATH)
    payload[field] += 1
    forged = tmp_path / f"forged_{field}.json"
    wp27_r1.write_json(forged, payload)
    result = wp27_r1.verify(forged, REPO_ROOT, RAW_ROOT)
    assert result["valid"] is False
    assert result["errors"]


def test_clean_room_rebuild_is_four_of_four_byte_deterministic(tmp_path: Path) -> None:
    clean = tmp_path / "clean"
    manifest = read_json(MANIFEST_PATH)
    for record in manifest["sources"]:
        source = REPO_ROOT / record["path"]
        target = clean / record["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        os.link(source, target)
    result = wp27_r1.build(clean, RAW_ROOT)
    assert result["manifest_sha256"] == wp27_r1.sha256_file(MANIFEST_PATH)
    rebuilt = read_json(clean / wp27_r1.MANIFEST_RELATIVE_PATH)
    assert [
        (row["id"], row["sha256"], row["size"]) for row in rebuilt["artifacts"]
    ] == [
        (row["id"], row["sha256"], row["size"]) for row in manifest["artifacts"]
    ]


def test_no_wp28_artifact_or_authorization_is_created() -> None:
    assert not list((REPO_ROOT / "docs/review").glob("**/*wp28*"))
    assert not list((REPO_ROOT / "scripts").glob("*wp28*"))
    assert not list((REPO_ROOT / "tests").glob("*wp28*"))
    manifest = read_json(MANIFEST_PATH)
    assert manifest["wp28_started"] is False
    assert manifest["d02_status"] == "PENDING"
    assert manifest["gate0"] == "BLOCKED"
    assert manifest["split_authorized"] is False
    assert manifest["training_authorized"] is False
