from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/build_wp5_provisional_grouping_review.py"
SPEC = importlib.util.spec_from_file_location(
    "build_wp5_provisional_grouping_review", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
wp5 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp5
SPEC.loader.exec_module(wp5)

GENERATED = REPO_ROOT / "docs/review/generated"
AUDIT_DIR = REPO_ROOT / "results/data_audit/DATASET01_052bc980a7206f8d"
RAW_ROOT = Path(
    "/Users/nguyentantai/Library/Mobile Documents/com~apple~CloudDocs/"
    "FALL 2026 KỲ 4/CPV301/Data/DATASET01/staging/052bc980a7206f8d/raw"
)
MANIFEST = GENERATED / "wp5_evidence_manifest.json"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_payload(
    tmp_path: Path, payload: dict[str, Any], name: str
) -> dict[str, Any]:
    manifest_path = tmp_path / name
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8"
    )
    return wp5.verify_manifest(manifest_path, REPO_ROOT, RAW_ROOT)


def typed_decisions() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = read_csv(
        GENERATED / "wp5_provisional_edge_decisions.csv"
    )
    for row in rows:
        row["review_order"] = int(row["review_order"])
        row["atlas_slot"] = int(row["atlas_slot"])
    return rows


def test_exact_edge_sequence_and_cross_split_coverage() -> None:
    rows = typed_decisions()
    assert len(rows) == wp5.EXPECTED_EDGE_COUNT == 3178
    assert len({row["edge_id"] for row in rows}) == 3178
    assert Counter(row["proxy_status"] for row in rows) == wp5.EXPECTED_PROXY_COUNTS
    cross_split = [row for row in rows if row["cross_split"] == "True"]
    assert len(cross_split) == wp5.EXPECTED_CROSS_SPLIT_COUNT == 1031
    assert all(row["cross_split"] == "True" for row in rows[:1031])
    assert all(row["cross_split"] == "False" for row in rows[1031:])
    sequences = read_csv(GENERATED / "wp5_sequence_review_queue.csv")
    assert len(sequences) == wp5.EXPECTED_SEQUENCE_COUNT == 589
    assert len({row["proxy_sequence_id"] for row in sequences}) == 589
    assert all(row["review_status"] == "PENDING" for row in sequences)
    assert all((REPO_ROOT / row["contact_sheet"]).is_file() for row in sequences)


def test_reviewed_records_are_evidence_bounded_and_pending_rows_fail_closed() -> None:
    rows = typed_decisions()
    schema = json.loads(
        (GENERATED / "wp5_provisional_decision.schema.json").read_text(
            encoding="utf-8"
        )
    )
    validator = Draft202012Validator(schema)
    assert not [error for row in rows for error in validator.iter_errors(row)]
    reviewed = [row for row in rows if row["review_status"] == "REVIEWED"]
    pending = [row for row in rows if row["review_status"] == "PENDING"]
    assert {row["edge_id"] for row in reviewed} == {
        "edge_000001",
        "edge_000003",
        "edge_000100",
        "edge_000109",
        "edge_000527",
        "edge_000663",
    }
    assert Counter(row["provisional_outcome"] for row in reviewed) == {
        "SAME_CAPTURE_CANDIDATE": 4,
        "NOT_RELATED": 2,
    }
    assert all(row["confidence"] == "HIGH" for row in reviewed)
    assert all(row["reviewer"].strip() and row["reviewed_at"].strip() for row in reviewed)
    assert all(row["rationale"].strip() and row["evidence_ref"].strip() for row in reviewed)
    fail_closed_fields = {
        "provisional_outcome",
        "capture_hypothesis",
        "physical_sign_hypothesis",
        "confidence",
        "reviewer",
        "reviewed_at",
        "rationale",
    }
    assert len(pending) == 3172
    assert all(not row[field] for row in pending for field in fail_closed_fields)


def test_provisional_components_keep_capture_and_physical_hypotheses_separate() -> None:
    rows = read_csv(GENERATED / "wp5_provisional_components.csv")
    assert len(rows) == 6
    assert Counter(row["hypothesis"] for row in rows) == {
        "capture": 4,
        "physical_sign": 2,
    }
    assert all(row["component_label"] == wp5.COMPONENT_LABEL for row in rows)
    assert all(row["confidence"] == "HIGH" for row in rows)
    assert all(row["cross_split"] == "True" for row in rows)
    assert all(int(row["member_count"]) == 2 for row in rows)
    assert read_csv(GENERATED / "wp5_component_conflicts.csv") == []


def test_no_final_group_or_split_assignment_fields_exist() -> None:
    forbidden = {
        "group_id",
        "final_group_id",
        "assigned_split",
        "approved_split",
    }
    for path in (
        GENERATED / "wp5_provisional_edge_decisions.csv",
        GENERATED / "wp5_sequence_review_queue.csv",
        GENERATED / "wp5_provisional_components.csv",
        GENERATED / "wp5_component_conflicts.csv",
    ):
        with path.open(newline="", encoding="utf-8") as handle:
            header = set(next(csv.reader(handle)))
        assert not forbidden & header
    status = json.loads(
        (REPO_ROOT / "docs/review/decision_status.json").read_text(encoding="utf-8")
    )
    assert status["gate0"] == "BLOCKED"
    assert status["training_authorized"] is False
    assert status["decisions"]["D-02"]["status"] == "PENDING"


def test_layout_covers_every_edge_with_complete_visible_content() -> None:
    decisions = typed_decisions()
    layout = json.loads(
        (GENERATED / "wp5_pair_layout_audit.json").read_text(encoding="utf-8")
    )
    assert layout["status"] == "PASS_COMPLETE_PAIR_COVERAGE_TEXT_AND_BOUNDS"
    assert layout["page_count"] == 128
    assert layout["pair_count"] == 3178
    assert layout["all_headers_complete"] is True
    assert layout["all_text_complete"] is True
    assert layout["all_bounds_fit"] is True
    visible_rows = [row for page in layout["pages"] for row in page["rows"]]
    assert [row["edge_id"] for row in visible_rows] == [
        row["edge_id"] for row in decisions
    ]
    assert all(row["text_complete"] and row["all_bounds_fit"] for row in visible_rows)
    assert all(
        (REPO_ROOT / page["path"]).is_file() for page in layout["pages"]
    )


def test_report_reconciles_all_source_hashes_and_workload() -> None:
    report = json.loads(
        (GENERATED / "wp5_leakage_report.json").read_text(encoding="utf-8")
    )
    assert report["status"] == wp5.PACKAGE_STATUS
    assert report["source_reconciliation"] == {
        "all_image_hashes_match_inventory": True,
        "all_label_hashes_match_inventory": True,
        "edge_endpoint_occurrences_reconciled": 6356,
        "source_tree_unchanged": True,
        "unique_inventory_sources_verified": 3216,
    }
    assert report["review_progress"]["reviewed_edge_count"] == 6
    assert report["unresolved_workload"] == {
        "complete_visual_adjudication_achieved": False,
        "pending_cross_split_edges": 1026,
        "pending_edges": 3172,
        "pending_sequences": 589,
    }
    assert report["d02_recommendation"]["preferred"] == "D02-A"
    assert report["d02_recommendation"]["manual_fallback"] == "D02-B"
    assert report["d02_recommendation"]["current_decision_status"] == "PENDING"
    assert report["manifest_contract"] == {
        "atlas_page_count": 128,
        "count_semantics": "EXCLUDES_MANIFEST_FILE",
        "non_manifest_artifact_count": 137,
        "schema_version": 2,
        "source_count": 11,
    }


def test_decision_generation_and_sample_atlas_are_deterministic(tmp_path: Path) -> None:
    edges = read_csv(GENERATED / "grouping_proxy_edges.csv")
    inventory_rows = read_csv(AUDIT_DIR / "image_inventory.csv")
    inventory = {row["stem"]: row for row in inventory_rows}
    edges_by_id = {
        f"edge_{index:06d}": row for index, row in enumerate(edges, start=1)
    }
    annotations = wp5.load_annotations(
        REPO_ROOT / "docs/review/wp5_visual_review_annotations.json", edges_by_id
    )
    first = wp5.build_decision_rows(edges, inventory, annotations)
    second = wp5.build_decision_rows(edges, inventory, annotations)
    assert first == second
    sample = first[:3]
    first_paths, first_layout = wp5.render_pair_atlas(
        sample, inventory, RAW_ROOT, tmp_path / "first"
    )
    second_paths, second_layout = wp5.render_pair_atlas(
        sample, inventory, RAW_ROOT, tmp_path / "second"
    )
    assert first_layout == second_layout | {
        "pages": [
            page | {"path": page["path"].replace("second", "first")}
            for page in second_layout["pages"]
        ]
    }
    assert [sha256_file(path) for path in first_paths] == [
        sha256_file(path) for path in second_paths
    ]


def test_manifest_verifies_and_rejects_source_or_artifact_tamper(tmp_path: Path) -> None:
    result = wp5.verify_manifest(MANIFEST, REPO_ROOT, RAW_ROOT)
    assert result["valid"] is True
    assert result["errors"] == []
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    payload["sources"][0]["sha256"] = "0" * 64
    result = verify_payload(tmp_path, payload, "bad_source_manifest.json")
    assert result["valid"] is False
    assert any("tampered sources file" in error for error in result["errors"])
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    payload["artifacts"][0]["sha256"] = "f" * 64
    result = verify_payload(tmp_path, payload, "bad_artifact_manifest.json")
    assert result["valid"] is False
    assert any("tampered artifacts file" in error for error in result["errors"])


def test_manifest_schema_v2_has_exact_canonical_rosters_and_count_semantics() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert payload["schema_version"] == wp5.MANIFEST_SCHEMA_VERSION == 2
    assert payload["manifest_path"] == wp5.MANIFEST_RELATIVE_PATH
    assert payload["manifest_self_in_artifact_count"] is False
    assert payload["artifact_count_semantics"] == "EXCLUDES_MANIFEST_FILE"
    assert payload["source_count"] == len(payload["sources"]) == 11
    assert payload["artifact_count"] == len(payload["artifacts"]) == 137
    assert payload["total_artifact_bytes"] == sum(
        record["size"] for record in payload["artifacts"]
    )
    assert [(record["id"], record["path"]) for record in payload["sources"]] == (
        wp5.contract_signature(wp5.canonical_source_contract(REPO_ROOT), REPO_ROOT)
    )
    assert [(record["id"], record["path"]) for record in payload["artifacts"]] == (
        wp5.contract_signature(wp5.canonical_artifact_contract(REPO_ROOT), REPO_ROOT)
    )
    assert payload["edge_count"] == 3178
    assert payload["cross_split_edge_count"] == 1031
    assert payload["sequence_count"] == 589
    assert payload["atlas_page_count"] == 128


@pytest.mark.parametrize(
    ("collection", "expected_count"),
    [("artifacts", 136), ("sources", 10)],
)
def test_manifest_rejects_roster_entry_removal(
    tmp_path: Path, collection: str, expected_count: int
) -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    removed = payload[collection].pop(0)
    payload[f"{collection[:-1]}_count"] = len(payload[collection])
    if collection == "artifacts":
        payload["total_artifact_bytes"] = sum(
            record["size"] for record in payload["artifacts"]
        )
    assert len(payload[collection]) == expected_count
    result = verify_payload(tmp_path, payload, f"missing_{collection}.json")
    assert result["valid"] is False
    assert any(
        f"missing canonical {collection} IDs" in error and removed["id"] in error
        for error in result["errors"]
    )


@pytest.mark.parametrize("collection", ["artifacts", "sources"])
def test_manifest_rejects_duplicate_records(
    tmp_path: Path, collection: str
) -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    payload[collection].append(dict(payload[collection][0]))
    payload[f"{collection[:-1]}_count"] = len(payload[collection])
    if collection == "artifacts":
        payload["total_artifact_bytes"] = sum(
            record["size"] for record in payload["artifacts"]
        )
    result = verify_payload(tmp_path, payload, f"duplicate_{collection}.json")
    assert result["valid"] is False
    assert any(f"duplicate {collection}" in error for error in result["errors"])


def test_manifest_rejects_extra_valid_existing_file(tmp_path: Path) -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    extra_path = REPO_ROOT / "PROJECT_MEMORY.md"
    payload["artifacts"].append(
        {
            "id": "unexpected_valid_file",
            "path": "PROJECT_MEMORY.md",
            "sha256": sha256_file(extra_path),
            "size": extra_path.stat().st_size,
        }
    )
    payload["artifact_count"] = len(payload["artifacts"])
    payload["total_artifact_bytes"] = sum(
        record["size"] for record in payload["artifacts"]
    )
    result = verify_payload(tmp_path, payload, "extra_valid_file.json")
    assert result["valid"] is False
    assert any("unexpected artifacts IDs" in error for error in result["errors"])


@pytest.mark.parametrize("field", ["artifact_count", "source_count"])
def test_manifest_rejects_forged_declared_counts(
    tmp_path: Path, field: str
) -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    payload[field] = 999
    result = verify_payload(tmp_path, payload, f"forged_{field}.json")
    assert result["valid"] is False
    assert any(field in error for error in result["errors"])


def test_manifest_rejects_forged_total_bytes(tmp_path: Path) -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    payload["total_artifact_bytes"] += 1
    result = verify_payload(tmp_path, payload, "forged_total_bytes.json")
    assert result["valid"] is False
    assert any("total_artifact_bytes" in error for error in result["errors"])


@pytest.mark.parametrize("page_number", [1, 64, 128])
def test_manifest_rejects_missing_first_middle_or_last_atlas_page(
    tmp_path: Path, page_number: int
) -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    page_id = f"pair_atlas_{page_number:03d}"
    payload["artifacts"] = [
        record for record in payload["artifacts"] if record["id"] != page_id
    ]
    payload["artifact_count"] = len(payload["artifacts"])
    payload["total_artifact_bytes"] = sum(
        record["size"] for record in payload["artifacts"]
    )
    result = verify_payload(tmp_path, payload, f"missing_page_{page_number:03d}.json")
    assert result["valid"] is False
    assert any(page_id in error for error in result["errors"])


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    [
        ("path_escape", "unsafe manifest path"),
        ("directory_for_file", "unexpected artifacts path"),
        ("wrong_collection_type", "sources must be a list"),
        ("wrong_record_type", "size must be a non-negative integer"),
        ("unexpected_top_level", "top-level fields differ"),
    ],
)
def test_manifest_rejects_path_root_and_type_contract_violations(
    tmp_path: Path, mutation: str, expected_error: str
) -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if mutation == "path_escape":
        payload["sources"][0]["path"] = "../outside.csv"
    elif mutation == "directory_for_file":
        payload["artifacts"][0]["path"] = "docs/review"
    elif mutation == "wrong_collection_type":
        payload["sources"] = {"not": "a list"}
    elif mutation == "wrong_record_type":
        payload["artifacts"][0]["size"] = "1750136"
    else:
        payload["unexpected"] = True
    result = verify_payload(tmp_path, payload, f"invalid_{mutation}.json")
    assert result["valid"] is False
    assert any(expected_error in error for error in result["errors"])


def test_source_hash_check_rejects_inventory_tamper() -> None:
    row = read_csv(AUDIT_DIR / "image_inventory.csv")[0]
    tampered = dict(row)
    tampered["image_sha256"] = "0" * 64
    try:
        wp5.verify_inventory_sources({tampered["stem"]: tampered}, RAW_ROOT)
    except ValueError as error:
        assert "source hash mismatch" in str(error)
    else:
        raise AssertionError("tampered source hash was accepted")
