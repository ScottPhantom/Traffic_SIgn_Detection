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

REPO_ROOT = Path(__file__).parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/build_wp30_remaining_edge_review_batch.py"
SPEC = importlib.util.spec_from_file_location("build_wp30_remaining_edge_review_batch", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
wp30 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp30
SPEC.loader.exec_module(wp30)
wp30._configure()
api = wp30.core

LOCAL_RAW_ROOT = REPO_ROOT / "data/raw/DATASET01/staging/052bc980a7206f8d/raw"
ICLOUD_RAW_ROOT = Path(
    "/Users/nguyentantai/Library/Mobile Documents/com~apple~CloudDocs/"
    "FALL 2026 KỲ 4/CPV301/Data/DATASET01/staging/052bc980a7206f8d/raw"
)
RAW_ROOT = LOCAL_RAW_ROOT if LOCAL_RAW_ROOT.is_dir() else ICLOUD_RAW_ROOT
MANIFEST_PATH = REPO_ROOT / wp30.MANIFEST_RELATIVE_PATH
EXCEPTIONS = {
    "edge_002977": ("SAME_CAPTURE_CANDIDATE", "NOT_RELATED", "MEDIUM"),
    "edge_003047": ("NOT_RELATED", "NOT_RELATED", "HIGH"),
    "edge_003092": ("NOT_RELATED", "NOT_RELATED", "HIGH"),
    "edge_003128": ("NOT_RELATED", "NOT_RELATED", "HIGH"),
    "edge_003153": ("NOT_RELATED", "NOT_RELATED", "HIGH"),
}


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
    staged = tmp_path / wp30.MANIFEST_RELATIVE_PATH
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
    result = wp30.verify(MANIFEST_PATH, REPO_ROOT, RAW_ROOT)
    assert result == {
        "valid": True,
        "errors": [],
        "source_count": 123,
        "artifact_count": 35,
        "status": "WP30_AWAITING_QA_REVIEW",
    }
    manifest = read_json(MANIFEST_PATH)
    assert manifest["selection_count"] == 144
    assert manifest["lineage_record_count"] == 288
    assert manifest["selected_endpoint_box_count"] == 888
    assert manifest["atlas_page_count"] == 29
    assert manifest["quarantined_stem_0248_selected"] is False
    assert manifest["gate0"] == "BLOCKED"
    assert manifest["d02_status"] == "PENDING"
    assert manifest["split_authorized"] is False
    assert manifest["training_authorized"] is False
    assert manifest["final_group_truth_created"] is False
    assert manifest["transitive_grouping_created"] is False


def test_selection_is_the_complete_final_eligible_suffix() -> None:
    residual, quarantined, eligible = wp30.derive_residual(REPO_ROOT)
    selection = read_csv(REPO_ROOT / wp30.SELECTION_RELATIVE_PATH)
    assert [row["edge_id"] for row in selection] == [row["edge_id"] for row in eligible]
    assert len(selection) == 144 and len(residual) == 146
    assert [row["edge_id"] for row in quarantined] == ["edge_000242", "edge_000243"]
    assert (selection[0]["edge_id"], selection[-1]["edge_id"]) == ("edge_002973", "edge_003176")
    assert all(row["cross_split"] == "False" for row in selection)
    stems = {row[side] for row in selection for side in ("left_stem", "right_stem")}
    assert "0248" not in stems


def test_selection_does_not_overlap_any_reviewed_overlay() -> None:
    generated = REPO_ROOT / "docs/review/generated"
    selected = {row["edge_id"] for row in read_csv(REPO_ROOT / wp30.SELECTION_RELATIVE_PATH)}
    names = [name for name, _count in wp30.CROSS_SPLIT_OVERLAYS] + [
        name for _label, name in wp30.REMAINING_EDGE_PREDECESSORS
    ]
    for name in names:
        assert not selected & {row["edge_id"] for row in read_csv(generated / name)}, name


def test_decisions_match_the_review_contract() -> None:
    payload = read_json(REPO_ROOT / wp30.ANNOTATIONS_RELATIVE_PATH)
    decisions = payload["decisions"]
    assert len(decisions) == 144
    assert Counter(row["capture_hypothesis"] for row in decisions) == Counter(
        {"SAME_CAPTURE_CANDIDATE": 140, "NOT_RELATED": 4}
    )
    assert Counter(row["confidence"] for row in decisions) == Counter({"HIGH": 143, "MEDIUM": 1})
    exceptional = {
        row["edge_id"]: (
            row["capture_hypothesis"],
            row["physical_sign_hypothesis"],
            row["confidence"],
        )
        for row in decisions
        if (row["capture_hypothesis"], row["physical_sign_hypothesis"], row["confidence"])
        != ("SAME_CAPTURE_CANDIDATE", "SAME_PHYSICAL_SIGN_CANDIDATE", "HIGH")
    }
    assert exceptional == EXCEPTIONS
    assert all(
        any("assets/wp30/remaining_edge_batch_i/" in ref for ref in row["evidence_refs"])
        for row in decisions
    )


def test_layout_has_exact_final_page_row_counts() -> None:
    layout = read_json(REPO_ROOT / wp30.LAYOUT_RELATIVE_PATH)
    wp30.validate_strict_layout(layout)
    assert [page["row_count"] for page in layout["pages"]] == [5] * 28 + [4]
    assert layout["status"] == "PASS_COMPLETE_144_PAIR_COVERAGE_TEXT_BOUNDS_AND_BBOX_CONTEXT"


def test_flipped_decision_with_rehashed_manifest_fails_closed(tmp_path: Path) -> None:
    staged = stage_package(tmp_path)
    notes_path = tmp_path / wp30.REVIEW_NOTES_RELATIVE_PATH
    rows = read_csv(notes_path)
    target = next(row for row in rows if row["edge_id"] == "edge_003092")
    target["provisional_outcome"] = target["capture_hypothesis"] = "SAME_CAPTURE_CANDIDATE"
    with notes_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    refresh_manifest_records(staged)
    result = wp30.verify(staged, tmp_path, RAW_ROOT)
    assert result["valid"] is False


@pytest.mark.parametrize("mutation", ["status_stale_250", "pair_count_float", "crlf"])
def test_layout_tampering_fails_closed(tmp_path: Path, mutation: str) -> None:
    staged = stage_package(tmp_path)
    layout_path = tmp_path / wp30.LAYOUT_RELATIVE_PATH
    layout = read_json(layout_path)
    if mutation == "status_stale_250":
        layout["status"] = "PASS_COMPLETE_250_PAIR_COVERAGE_TEXT_BOUNDS_AND_BBOX_CONTEXT"
        api.write_json(layout_path, layout)
    elif mutation == "pair_count_float":
        layout["pair_count"] = 144.0
        api.write_json(layout_path, layout)
    else:
        layout_path.write_bytes(layout_path.read_bytes().replace(b"\n", b"\r\n"))
    refresh_manifest_records(staged)
    assert wp30.verify(staged, tmp_path, RAW_ROOT)["valid"] is False


def test_report_records_governance_boundary() -> None:
    report = (REPO_ROOT / wp30.REPORT_RELATIVE_PATH).read_text(encoding="utf-8")
    assert "final Batch I" in report
    assert "no eligible edge remains after WP30" in report
    assert "D-02 remains PENDING; Gate 0 remains BLOCKED" in report
    assert "`training_authorized=false`" in report
