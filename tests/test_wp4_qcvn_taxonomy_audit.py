from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import shutil
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from PIL import Image, ImageDraw

REPO_ROOT = Path(__file__).parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "build_wp4_qcvn_taxonomy_audit.py"
SPEC = importlib.util.spec_from_file_location("build_wp4_qcvn_taxonomy_audit", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
wp4 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp4
SPEC.loader.exec_module(wp4)

GENERATED = REPO_ROOT / "docs" / "review" / "generated"
WORKSHEET = GENERATED / "wp4_qcvn_taxonomy_worksheet.csv"
SUMMARY = GENERATED / "wp4_qcvn_summary.json"
MANIFEST = GENERATED / "wp4_qcvn_manifest.json"
EVIDENCE_INDEX = REPO_ROOT / wp4.EVIDENCE_INDEX_RELATIVE_PATH
RAW_ROOT = Path(
    "/Users/nguyentantai/Library/Mobile Documents/com~apple~CloudDocs/"
    "FALL 2026 KỲ 4/CPV301/Data/DATASET01/staging/052bc980a7206f8d/raw"
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def stage_package(tmp_path: Path) -> Path:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for record in [*payload["sources"], *payload["artifacts"]]:
        relative = Path(record["path"])
        assert not relative.is_absolute()
        source = REPO_ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    staged_manifest = tmp_path / "docs/review/generated/wp4_qcvn_manifest.json"
    staged_manifest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(MANIFEST, staged_manifest)
    return staged_manifest


def refresh_manifest_record(
    staged_manifest: Path, collection: str, relative: Path
) -> None:
    payload = json.loads(staged_manifest.read_text(encoding="utf-8"))
    matches = [
        record for record in payload[collection] if record["path"] == relative.as_posix()
    ]
    assert len(matches) == 1
    target = staged_manifest.parents[3] / relative
    matches[0]["sha256"] = sha256_file(target)
    matches[0]["size"] = target.stat().st_size
    staged_manifest.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def verify_args(tmp_path: Path, staged_manifest: Path) -> Any:
    return wp4.parser().parse_args(
        [
            "verify",
            "--repo-root",
            str(tmp_path),
            "--manifest",
            str(staged_manifest),
            "--worksheet",
            str(tmp_path / "docs/review/generated/wp4_qcvn_taxonomy_worksheet.csv"),
            "--summary",
            str(tmp_path / "docs/review/generated/wp4_qcvn_summary.json"),
            "--qcvn-pdf",
            str(tmp_path / "references/qcvn41_2024/qcvn-41-2024-bgtvt.pdf"),
            "--circular-pdf",
            str(tmp_path / "references/qcvn41_2024/51-2024-tt-bgtvt.pdf"),
            "--source-provenance",
            str(tmp_path / "references/qcvn41_2024/source_provenance.json"),
            "--evidence-index",
            str(tmp_path / wp4.EVIDENCE_INDEX_RELATIVE_PATH),
            "--lineage",
            str(tmp_path / "docs/review/generated/wp4_qcvn_source_lineage.csv"),
            "--layout-audit",
            str(tmp_path / "docs/review/generated/wp4_qcvn_layout_audit.json"),
            "--inventory-csv",
            str(
                tmp_path
                / "results/data_audit/DATASET01_052bc980a7206f8d/image_inventory.csv"
            ),
            "--raw-root",
            str(RAW_ROOT),
            "--decision-status",
            str(tmp_path / "docs/review/decision_status.json"),
        ]
    )


def repin_mutated_index(
    tmp_path: Path,
    staged_manifest: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutate: Callable[[dict[str, Any]], None],
) -> None:
    index_path = tmp_path / wp4.EVIDENCE_INDEX_RELATIVE_PATH
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    mutate(payload)
    index_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    new_hash = sha256_file(index_path)
    monkeypatch.setattr(wp4, "EXPECTED_EVIDENCE_INDEX_SHA256", new_hash)
    provenance_path = tmp_path / "references/qcvn41_2024/source_provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    provenance["evidence_controls"][0]["sha256"] = new_hash
    provenance_path.write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    refresh_manifest_record(
        staged_manifest, "sources", wp4.EVIDENCE_INDEX_RELATIVE_PATH
    )
    refresh_manifest_record(
        staged_manifest,
        "sources",
        Path("references/qcvn41_2024/source_provenance.json"),
    )


def test_worksheet_exact_ids_schema_statuses_and_known_conflicts() -> None:
    rows = read_csv(WORKSHEET)
    assert list(rows[0]) == wp4.WORKSHEET_FIELDS
    assert len(rows) == 52
    assert [int(row["class_id"]) for row in rows] == list(range(52))
    assert all(row["reviewer_status"] == "UNAPPROVED" for row in rows)
    by_id = {int(row["class_id"]): row for row in rows}
    for class_id, expected in wp4.KNOWN_CONFLICT_EXPECTATIONS.items():
        assert by_id[class_id]["match_status"] == expected
    assert by_id[31]["official_code_candidate"] == ""
    assert by_id[31]["official_pdf_page"] == ""
    assert by_id[34]["official_code_candidate"] == "P.108a"
    assert by_id[47]["official_code_candidate"] == "P.124b"


def test_evidence_index_is_pinned_and_recomputed_from_pdf() -> None:
    qcvn = REPO_ROOT / "references/qcvn41_2024/qcvn-41-2024-bgtvt.pdf"
    rows, audit = wp4.load_and_verify_evidence_index(
        EVIDENCE_INDEX, qcvn, REPO_ROOT
    )
    assert len(rows) == 52
    assert audit["index_sha256"] == wp4.EXPECTED_EVIDENCE_INDEX_SHA256
    assert audit["fingerprinted_page_count"] == 39
    assert rows[31]["negative_search_scope"]["pages"] == "80-154"
    assert rows[31]["negative_search_scope"]["query_hits"] == []


def test_official_pdf_hash_page_count_and_control_provenance() -> None:
    root = REPO_ROOT / "references/qcvn41_2024"
    result = wp4.verify_pdf_sources(
        root / "qcvn-41-2024-bgtvt.pdf",
        root / "51-2024-tt-bgtvt.pdf",
        root / "source_provenance.json",
    )
    assert result["qcvn"]["page_count"] == 403
    assert result["qcvn"]["sha256"] == wp4.QCVN_SHA256
    assert result["circular"]["page_count"] == 1
    assert result["evidence_index_control"]["sha256"] == (
        wp4.EXPECTED_EVIDENCE_INDEX_SHA256
    )


def test_layout_and_lineage_cover_all_156_visible_overlays() -> None:
    layout = json.loads(
        (GENERATED / "wp4_qcvn_layout_audit.json").read_text(encoding="utf-8")
    )
    assert layout["schema_version"] == 2
    assert layout["page_count"] == 13
    assert layout["row_count"] == 52
    assert layout["overlay_count"] == 156
    assert layout["all_overlays_within_canvas"] is True
    assert layout["all_overlays_visible"] is True
    lineage = read_csv(GENERATED / "wp4_qcvn_source_lineage.csv")
    assert list(lineage[0]) == wp4.LINEAGE_FIELDS
    assert len(lineage) == 156
    result = wp4.verify_overlay_lineage(
        GENERATED / "wp4_qcvn_source_lineage.csv",
        GENERATED / "wp4_qcvn_layout_audit.json",
        REPO_ROOT
        / "results/data_audit/DATASET01_052bc980a7206f8d/image_inventory.csv",
        RAW_ROOT,
        REPO_ROOT,
        read_csv(WORKSHEET),
    )
    assert result["visible_overlay_count"] == 156
    assert result["geometry_reconciled_count"] == 156
    assert result["raw_source_hashes_unchanged"] is True
    assert any(row["source_bbox_within_image"] == "False" for row in lineage)


def test_class49_sampling_reserves_0248_then_preserves_wp3_order() -> None:
    assert wp4.representative_stems_for_class(49, "0119;0411;0352") == (
        "0248;0119;0411"
    )
    assert wp4.representative_stems_for_class(48, "3111;3110;3097") == (
        "3111;3110;3097"
    )


def test_required_boundary_case_0248_exact_geometry_hashes_and_pixels() -> None:
    worksheet = read_csv(WORKSHEET)
    class49 = next(row for row in worksheet if int(row["class_id"]) == 49)
    assert class49["representative_source_stems"].split(";") == [
        "0248",
        "0119",
        "0411",
    ]
    lineage = read_csv(GENERATED / "wp4_qcvn_source_lineage.csv")
    matches = [
        row
        for row in lineage
        if int(row["class_id"]) == 49 and int(row["slot_index"]) == 1
    ]
    assert len(matches) == 1
    row = matches[0]
    assert row["stem"] == "0248"
    assert row["image_sha256"] == (
        "07eab2035dc10b7b08be71d76c3c32ffdb960722839414f1e474da20c3ad0cbd"
    )
    assert row["label_sha256"] == (
        "f4ec410f7bff3ee03f6110308e8e95f57c92bcc7ebf45ff3affcfd885b419c77"
    )
    assert (int(row["source_width"]), int(row["source_height"])) == (960, 540)
    assert (int(row["label_line_number"]), int(row["label_index"])) == (1, 0)
    assert row["source_bbox_within_image"] == "False"
    for field, expected in zip(
        (
            "source_bbox_x_min",
            "source_bbox_y_min",
            "source_bbox_x_max",
            "source_bbox_y_max",
        ),
        (927.00048, 158.99976, 978.00048, 213.99984),
        strict=True,
    ):
        assert float(row[field]) == pytest.approx(expected, abs=1e-6)
    assert float(row["source_bbox_overflow_right"]) == pytest.approx(
        18.00048, abs=1e-6
    )
    assert float(row["sample_bbox_x_max"]) > float(row["sample_source_frame_x_max"])
    image_path = RAW_ROOT / row["image_path"]
    label_path = RAW_ROOT / row["label_path"]
    before = (sha256_file(image_path), sha256_file(label_path))
    atlas_path = REPO_ROOT / "docs/review" / row["atlas_page"]
    with Image.open(atlas_path) as opened:
        atlas = opened.convert("RGB")
    overlay_bounds = [
        float(row["atlas_bbox_x_min"]),
        float(row["atlas_bbox_y_min"]),
        float(row["atlas_bbox_x_max"]),
        float(row["atlas_bbox_y_max"]),
    ]
    source_frame = [
        float(row["atlas_source_frame_x_min"]),
        float(row["atlas_source_frame_y_min"]),
        float(row["atlas_source_frame_x_max"]),
        float(row["atlas_source_frame_y_max"]),
    ]
    assert wp4.overlay_pixels_present(atlas, overlay_bounds)
    assert wp4.source_boundary_pixels_present(atlas, source_frame)
    assert (sha256_file(image_path), sha256_file(label_path)) == before


def test_rebuild_is_deterministic_and_does_not_mutate_inputs(tmp_path: Path) -> None:
    audit_dir = REPO_ROOT / "results/data_audit/DATASET01_052bc980a7206f8d"
    index_target = tmp_path / wp4.EVIDENCE_INDEX_RELATIVE_PATH
    index_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(EVIDENCE_INDEX, index_target)
    source_paths = [
        REPO_ROOT / record["path"]
        for record in json.loads(MANIFEST.read_text(encoding="utf-8"))["sources"]
    ]
    before = {path: sha256_file(path) for path in source_paths}
    args = wp4.parser().parse_args(
        [
            "build",
            "--repo-root",
            str(tmp_path),
            "--qcvn-pdf",
            str(REPO_ROOT / "references/qcvn41_2024/qcvn-41-2024-bgtvt.pdf"),
            "--circular-pdf",
            str(REPO_ROOT / "references/qcvn41_2024/51-2024-tt-bgtvt.pdf"),
            "--source-provenance",
            str(REPO_ROOT / "references/qcvn41_2024/source_provenance.json"),
            "--evidence-index",
            str(index_target),
            "--taxonomy-csv",
            str(GENERATED / "taxonomy_review.csv"),
            "--wp3-atlas-csv",
            str(GENERATED / "wp3_taxonomy_reviewer_atlas.csv"),
            "--wp3-manifest",
            str(GENERATED / "wp3_evidence_manifest.json"),
            "--wp2-manifest",
            str(GENERATED / "wp2_generated_manifest.json"),
            "--wp1-manifest",
            str(audit_dir / "wp1_artifact_manifest.json"),
            "--source-preservation",
            str(audit_dir / "source_preservation_proof.json"),
            "--inventory-csv",
            str(audit_dir / "image_inventory.csv"),
            "--decision-status",
            str(REPO_ROOT / "docs/review/decision_status.json"),
            "--canonical-taxonomy",
            str(REPO_ROOT / "docs/vietnam_taxonomy_mapping.md"),
            "--raw-root",
            str(RAW_ROOT),
            "--output-dir",
            str(tmp_path / "docs/review/generated"),
            "--assets-dir",
            str(tmp_path / "docs/review/assets/wp4/qcvn_taxonomy_atlas"),
            "--report-path",
            str(tmp_path / "docs/review/m0_wp4_qcvn_taxonomy_report.md"),
            "--proposal-path",
            str(tmp_path / "docs/review/wp4_taxonomy_vnext_proposal.md"),
        ]
    )
    wp4.build(args)
    canonical = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rebuilt = json.loads(
        (tmp_path / "docs/review/generated/wp4_qcvn_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert {record["path"]: record["sha256"] for record in rebuilt["artifacts"]} == {
        record["path"]: record["sha256"] for record in canonical["artifacts"]
    }
    assert {path: sha256_file(path) for path in source_paths} == before


def test_clean_staged_verifier_passes(tmp_path: Path) -> None:
    staged_manifest = stage_package(tmp_path)
    result = wp4.verify(verify_args(tmp_path, staged_manifest))
    assert result["status"] == "PASS"
    assert result["overlay_slot_count"] == 156
    assert result["visible_overlay_count"] == 156


def test_manifest_verifier_detects_unrefreshed_artifact_tamper(tmp_path: Path) -> None:
    staged_manifest = stage_package(tmp_path)
    worksheet = tmp_path / "docs/review/generated/wp4_qcvn_taxonomy_worksheet.csv"
    worksheet.write_text(worksheet.read_text(encoding="utf-8") + "tamper\n", encoding="utf-8")
    with pytest.raises(ValueError, match="artifact hash/size mismatch"):
        wp4.verify(verify_args(tmp_path, staged_manifest))


def test_manifest_verifier_detects_unrefreshed_index_tamper(tmp_path: Path) -> None:
    staged_manifest = stage_package(tmp_path)
    index_path = tmp_path / wp4.EVIDENCE_INDEX_RELATIVE_PATH
    index_path.write_text(index_path.read_text(encoding="utf-8") + " ", encoding="utf-8")
    with pytest.raises(ValueError, match="source hash/size mismatch: evidence_index"):
        wp4.verify(verify_args(tmp_path, staged_manifest))


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("official_pdf_page", "106"),
        ("official_code_candidate", "P.999"),
        ("official_name_vi", "Tên sai nhưng có hash mới"),
        ("official_section", "B.999"),
        ("official_figure", "B.999"),
    ],
)
def test_refreshed_wrong_worksheet_semantics_are_rejected(
    tmp_path: Path, field: str, replacement: str
) -> None:
    staged_manifest = stage_package(tmp_path)
    relative = Path("docs/review/generated/wp4_qcvn_taxonomy_worksheet.csv")
    worksheet = tmp_path / relative
    rows = read_csv(worksheet)
    rows[0][field] = replacement
    write_csv(worksheet, rows)
    refresh_manifest_record(staged_manifest, "artifacts", relative)
    with pytest.raises(ValueError, match="worksheet/index semantic mismatch"):
        wp4.verify(verify_args(tmp_path, staged_manifest))


def test_refreshed_wrong_index_page_binding_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    staged_manifest = stage_package(tmp_path)
    repin_mutated_index(
        tmp_path,
        staged_manifest,
        monkeypatch,
        lambda payload: payload["rows"][0].__setitem__("official_pdf_page", "106"),
    )
    with pytest.raises(ValueError, match="official_pdf_page mismatch"):
        wp4.verify(verify_args(tmp_path, staged_manifest))


def test_refreshed_wrong_index_token_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    staged_manifest = stage_package(tmp_path)
    repin_mutated_index(
        tmp_path,
        staged_manifest,
        monkeypatch,
        lambda payload: payload["rows"][0].__setitem__("evidence_tokens", ["w.999"]),
    )
    with pytest.raises(ValueError, match="token mismatch"):
        wp4.verify(verify_args(tmp_path, staged_manifest))


def test_refreshed_wrong_page_fingerprint_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    staged_manifest = stage_package(tmp_path)

    def mutate(payload: dict[str, Any]) -> None:
        payload["page_fingerprints"]["107"]["render_pixel_sha256"] = "0" * 64

    repin_mutated_index(tmp_path, staged_manifest, monkeypatch, mutate)
    with pytest.raises(ValueError, match="page text/render fingerprint mismatch"):
        wp4.verify(verify_args(tmp_path, staged_manifest))


def test_refreshed_class31_negative_scope_tamper_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    staged_manifest = stage_package(tmp_path)

    def mutate(payload: dict[str, Any]) -> None:
        payload["rows"][31]["negative_search_scope"]["pages"] = "81-154"

    repin_mutated_index(tmp_path, staged_manifest, monkeypatch, mutate)
    with pytest.raises(ValueError, match="negative-search scope mismatch"):
        wp4.verify(verify_args(tmp_path, staged_manifest))


def test_missing_index_is_rejected(tmp_path: Path) -> None:
    staged_manifest = stage_package(tmp_path)
    (tmp_path / wp4.EVIDENCE_INDEX_RELATIVE_PATH).unlink()
    with pytest.raises(ValueError, match="required source is missing"):
        wp4.verify(verify_args(tmp_path, staged_manifest))


def test_manifest_source_path_escape_is_rejected(tmp_path: Path) -> None:
    staged_manifest = stage_package(tmp_path)
    payload = json.loads(staged_manifest.read_text(encoding="utf-8"))
    record = next(item for item in payload["sources"] if item["name"] == "evidence_index")
    record["path"] = "../qcvn_taxonomy_evidence_index.json"
    staged_manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="source path escape rejected"):
        wp4.verify(verify_args(tmp_path, staged_manifest))


def test_refreshed_lineage_geometry_tamper_is_rejected(tmp_path: Path) -> None:
    staged_manifest = stage_package(tmp_path)
    relative = Path("docs/review/generated/wp4_qcvn_source_lineage.csv")
    lineage_path = tmp_path / relative
    rows = read_csv(lineage_path)
    rows[0]["sample_bbox_x_min"] = str(float(rows[0]["sample_bbox_x_min"]) + 1.0)
    write_csv(lineage_path, rows)
    refresh_manifest_record(staged_manifest, "artifacts", relative)
    with pytest.raises(ValueError, match="overlay geometry mismatch"):
        wp4.verify(verify_args(tmp_path, staged_manifest))


def test_refreshed_lineage_code_binding_tamper_is_rejected(tmp_path: Path) -> None:
    staged_manifest = stage_package(tmp_path)
    relative = Path("docs/review/generated/wp4_qcvn_source_lineage.csv")
    lineage_path = tmp_path / relative
    rows = read_csv(lineage_path)
    rows[0]["dataset_code"] = "WRONG-CODE"
    write_csv(lineage_path, rows)
    refresh_manifest_record(staged_manifest, "artifacts", relative)
    with pytest.raises(ValueError, match="class/code/stem/page binding mismatch"):
        wp4.verify(verify_args(tmp_path, staged_manifest))


def test_other_out_of_frame_stem_cannot_replace_required_0248(tmp_path: Path) -> None:
    staged_manifest = stage_package(tmp_path)
    relative = Path("docs/review/generated/wp4_qcvn_taxonomy_worksheet.csv")
    worksheet_path = tmp_path / relative
    rows = read_csv(worksheet_path)
    class49 = next(row for row in rows if int(row["class_id"]) == 49)
    class49["representative_source_stems"] = "0809;0119;0411"
    write_csv(worksheet_path, rows)
    refresh_manifest_record(staged_manifest, "artifacts", relative)
    with pytest.raises(ValueError, match="class/code/stem/page binding mismatch"):
        wp4.verify(verify_args(tmp_path, staged_manifest))


def test_refreshed_atlas_pixel_overlay_tamper_is_rejected(tmp_path: Path) -> None:
    staged_manifest = stage_package(tmp_path)
    row = read_csv(tmp_path / "docs/review/generated/wp4_qcvn_source_lineage.csv")[0]
    relative = Path("docs/review") / row["atlas_page"]
    atlas_path = tmp_path / relative
    with Image.open(atlas_path) as opened:
        image = opened.convert("RGB")
    bbox = [
        round(float(row["atlas_bbox_x_min"])),
        round(float(row["atlas_bbox_y_min"])),
        round(float(row["atlas_bbox_x_max"])),
        round(float(row["atlas_bbox_y_max"])),
    ]
    ImageDraw.Draw(image).rectangle(
        (bbox[0] - 9, bbox[1] - 9, bbox[2] + 9, bbox[3] + 9), fill="white"
    )
    image.save(atlas_path, format="JPEG", quality=88, optimize=True, progressive=False)
    refresh_manifest_record(staged_manifest, "artifacts", relative)
    with pytest.raises(ValueError, match="visible red overlay missing"):
        wp4.verify(verify_args(tmp_path, staged_manifest))


def test_gate_boundary_remains_blocked_and_unapproved() -> None:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    assert summary["status"] == wp4.PACKAGE_STATUS
    assert summary["decision_boundary"] == {
        "D-03": "PENDING",
        "gate0": "BLOCKED",
        "training_authorized": False,
    }
    assert summary["reviewer_status_counts"] == {"UNAPPROVED": 52}
    assert summary["mutation_count"] == 0
