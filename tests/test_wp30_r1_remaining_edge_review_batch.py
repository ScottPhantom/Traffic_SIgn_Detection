from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/build_wp30_r1_remaining_edge_review_batch.py"
SPEC = importlib.util.spec_from_file_location(
    "build_wp30_r1_remaining_edge_review_batch", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
wp30_r1 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp30_r1
SPEC.loader.exec_module(wp30_r1)
wp30_r1._configure()
api = wp30_r1.core

LOCAL_RAW_ROOT = REPO_ROOT / "data/raw/DATASET01/staging/052bc980a7206f8d/raw"
ICLOUD_RAW_ROOT = Path(
    "/Users/nguyentantai/Library/Mobile Documents/com~apple~CloudDocs/"
    "FALL 2026 KỲ 4/CPV301/Data/DATASET01/staging/052bc980a7206f8d/raw"
)
RAW_ROOT = LOCAL_RAW_ROOT if LOCAL_RAW_ROOT.is_dir() else ICLOUD_RAW_ROOT
MANIFEST_PATH = REPO_ROOT / wp30_r1.MANIFEST_RELATIVE_PATH
DECISION_FIELDS = (
    "provisional_outcome",
    "capture_hypothesis",
    "physical_sign_hypothesis",
    "confidence",
)


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def stage_package(tmp_path: Path) -> Path:
    manifest = read_json(MANIFEST_PATH)
    for record in [*manifest["sources"], *manifest["artifacts"]]:
        target = tmp_path / record["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / record["path"], target)
    staged = tmp_path / wp30_r1.MANIFEST_RELATIVE_PATH
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
    payload["total_artifact_bytes"] = sum(record["size"] for record in payload["artifacts"])
    api.write_json(staged_manifest, payload)


def test_official_r1_package_verifies() -> None:
    result = wp30_r1.verify(MANIFEST_PATH, REPO_ROOT, RAW_ROOT)
    assert result == {
        "valid": True,
        "errors": [],
        "source_count": 130,
        "artifact_count": 35,
        "status": "WP30_R1_AWAITING_QA_REVIEW",
    }
    manifest = read_json(MANIFEST_PATH)
    assert manifest["training_authorized"] is False
    assert manifest["final_group_truth_created"] is False


def test_initial_wp30_package_is_immutable_and_still_verifies() -> None:
    initial = wp30_r1.wp30
    assert (
        api.sha256_file(REPO_ROOT / initial.MANIFEST_RELATIVE_PATH)
        == wp30_r1.INITIAL_MANIFEST_SHA256
    )
    assert (
        api.sha256_file(REPO_ROOT / initial.SELECTION_RELATIVE_PATH)
        == wp30_r1.INITIAL_SELECTION_SHA256
    )
    assert (
        api.sha256_file(REPO_ROOT / initial.ANNOTATIONS_RELATIVE_PATH)
        == wp30_r1.INITIAL_ANNOTATIONS_SHA256
    )
    assert (
        api.sha256_file(REPO_ROOT / initial.REVIEW_NOTES_RELATIVE_PATH)
        == wp30_r1.INITIAL_REVIEW_NOTES_SHA256
    )


def test_decisions_change_exactly_one_edge_from_initial_wp30() -> None:
    initial = read_json(REPO_ROOT / wp30_r1.wp30.ANNOTATIONS_RELATIVE_PATH)["decisions"]
    corrected = read_json(REPO_ROOT / wp30_r1.ANNOTATIONS_RELATIVE_PATH)["decisions"]
    assert [row["edge_id"] for row in initial] == [row["edge_id"] for row in corrected]
    changed = [
        new["edge_id"]
        for old, new in zip(initial, corrected, strict=True)
        if any(old[field] != new[field] for field in DECISION_FIELDS)
        or old["rationale"] != new["rationale"]
    ]
    assert changed == ["edge_003047"]
    edge = next(row for row in corrected if row["edge_id"] == "edge_003047")
    assert (edge["capture_hypothesis"], edge["physical_sign_hypothesis"], edge["confidence"]) == (
        "SAME_CAPTURE_CANDIDATE",
        "NOT_RELATED",
        "MEDIUM",
    )


def test_every_row_and_reference_is_bound_to_the_r1_atlas() -> None:
    selection = read_csv(REPO_ROOT / wp30_r1.SELECTION_RELATIVE_PATH)
    initial = read_csv(REPO_ROOT / wp30_r1.wp30.SELECTION_RELATIVE_PATH)
    assert len(selection) == len(initial) == 144
    for row, old in zip(selection, initial, strict=True):
        assert row["wp12_atlas_page"] == old["wp12_atlas_page"].replace(
            wp30_r1.INITIAL_ASSETS_RELATIVE_PATH, wp30_r1.ASSETS_RELATIVE_PATH
        )
        assert row["evidence_boundary"] == wp30_r1.EVIDENCE_BOUNDARY
        stripped = {
            k: v for k, v in row.items() if k not in {"wp12_atlas_page", "evidence_boundary"}
        }
        assert stripped == {
            k: v for k, v in old.items() if k not in {"wp12_atlas_page", "evidence_boundary"}
        }
    for decision in read_json(REPO_ROOT / wp30_r1.ANNOTATIONS_RELATIVE_PATH)["decisions"]:
        refs = decision["evidence_refs"]
        assert any(ref.startswith(f"{wp30_r1.ASSETS_RELATIVE_PATH}/page_") for ref in refs)
        assert not any(ref.startswith(f"{wp30_r1.INITIAL_ASSETS_RELATIVE_PATH}/") for ref in refs)


@pytest.mark.parametrize("attack", ["second_edge", "revert_capture", "confidence_high"])
def test_tampered_correction_overlay_fails_closed(tmp_path: Path, attack: str) -> None:
    staged = stage_package(tmp_path)
    overlay = tmp_path / wp30_r1.REVIEW_NOTES_RELATIVE_PATH
    rows = read_csv(overlay)
    if attack == "second_edge":
        rows.append({**rows[0], "edge_id": "edge_003092"})
    elif attack == "revert_capture":
        rows[0]["corrected_capture_hypothesis"] = rows[0]["corrected_provisional_outcome"] = (
            "NOT_RELATED"
        )
    else:
        rows[0]["confidence"] = "HIGH"
    write_csv(overlay, rows)
    refresh_manifest_records(staged)
    assert wp30_r1.verify(staged, tmp_path, RAW_ROOT)["valid"] is False


def test_report_records_correction_and_governance() -> None:
    report = (REPO_ROOT / wp30_r1.REPORT_RELATIVE_PATH).read_text(encoding="utf-8")
    assert "edge_003047" in report and "143 review decisions are unchanged" in report
    assert "D-02 remains PENDING; Gate 0 remains BLOCKED" in report
