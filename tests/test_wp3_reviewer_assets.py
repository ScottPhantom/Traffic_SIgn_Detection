from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest
from PIL import Image

SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "build_wp3_reviewer_assets.py"
SPEC = importlib.util.spec_from_file_location("build_wp3_reviewer_assets", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
wp3 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp3
SPEC.loader.exec_module(wp3)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def make_fixture(root: Path) -> tuple[Path, Path, Path, Path]:
    audit_dir = root / "results" / "data_audit" / "fixture"
    staging_root = root / "staging" / "fixture"
    raw_root = staging_root / "raw"
    images_dir = raw_root / "archive" / "images"
    labels_dir = raw_root / "archive" / "labels"
    review_dir = root / "docs" / "review"
    generated_dir = review_dir / "generated"
    images_dir.mkdir(parents=True)
    labels_dir.mkdir(parents=True)
    audit_dir.mkdir(parents=True)
    generated_dir.mkdir(parents=True)

    inventory_rows: list[dict[str, object]] = []
    taxonomy_rows: list[dict[str, object]] = []
    for class_id in range(52):
        stem = f"{class_id:04d}"
        image_path = images_dir / f"{stem}.jpg"
        label_path = labels_dir / f"{stem}.txt"
        Image.new("RGB", (48, 32), (class_id * 3 % 256, 60, 120)).save(image_path)
        label_path.write_text(f"{class_id} 0.5 0.5 0.5 0.5\n", encoding="utf-8")
        inventory_rows.append(
            {
                "stem": stem,
                "image_path": f"archive/images/{stem}.jpg",
                "image_sha256": sha256_file(image_path),
                "label_path": f"archive/labels/{stem}.txt",
                "label_sha256": sha256_file(label_path),
                "width": 48,
                "height": 32,
                "format": "JPEG",
                "mode": "RGB",
                "has_exif": "False",
                "has_gps": "False",
                "box_count": 1,
                "class_ids": class_id,
                "split": "train" if class_id % 2 == 0 else "test",
            }
        )
        taxonomy_rows.append(
            {
                "class_id": class_id,
                "dataset_code": f"C.{class_id}",
                "dataset_name_vi_en": f"Lop {class_id} / Class {class_id}",
                "semantic_family_proposal": "fixture-family",
                "gtsrb_mapping_proposal": "None",
                "gtsrb_relation_proposal": "Needs review",
                "criticality_proposal": "H",
                "image_count": 1,
                "box_count": 1,
                "conflict_flags": (
                    "domain_reviewer_not_approved;"
                    "cross_jurisdiction_gtsrb_semantics_unapproved;"
                    "vi_en_vehicle_scope_requires_full_domain_review;"
                    "rare_support_requires_independent_adjudication"
                    if class_id in {28, 51}
                    else "domain_reviewer_not_approved"
                ),
                "authoritative_review_target": "fixture",
                "review_status": wp3.UNAPPROVED_STATUS,
                "reviewer": "",
                "review_date": "",
                "decision_notes": "",
            }
        )
    write_csv(audit_dir / "image_inventory.csv", inventory_rows)
    write_csv(generated_dir / "taxonomy_review.csv", taxonomy_rows)

    cluster_rows: list[dict[str, object]] = []
    edge_rows: list[dict[str, object]] = []
    for sequence_index in range(52):
        left_stem = f"{sequence_index:04d}"
        right_stem = f"{(sequence_index + 1) % 52:04d}"
        sequence_id = f"proxy_sequence_{sequence_index + 1:04d}"
        cluster_rows.append(
            {
                "proxy_sequence_id": sequence_id,
                "evidence_status": wp3.PROXY_ONLY_STATUS,
                "member_count": 2,
                "members": f"{left_stem};{right_stem}",
                "strong_edge_count": 1,
                "cross_split_strong_edges": 1,
            }
        )
        edge_rows.append(
            {
                "proxy_sequence_id": sequence_id,
                "left_stem": left_stem,
                "right_stem": right_stem,
                "thumbnail_mae": f"{1.25 + sequence_index / 100:.6f}",
                "dhash_distance": str(sequence_index % 9),
                "rgb_histogram_cosine": f"{0.99 + sequence_index / 100000:.8f}",
            }
        )
    write_csv(generated_dir / "grouping_proxy_clusters.csv", cluster_rows)
    write_csv(generated_dir / "grouping_proxy_edges.csv", edge_rows)

    source_proof = {
        "unchanged": True,
        "source_tree_manifest_sha256": "a" * 64,
    }
    (audit_dir / "source_preservation_proof.json").write_text(
        json.dumps(source_proof), encoding="utf-8"
    )
    (audit_dir / "wp1_artifact_manifest.json").write_text("{}\n", encoding="utf-8")
    (audit_dir / "provenance_evidence.json").write_text(
        json.dumps(
            {
                "status": "CANDIDATE",
                "archive_sha256": "b" * 64,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (generated_dir / "wp2_generated_manifest.json").write_text("{}\n", encoding="utf-8")
    decision_path = review_dir / "decision_status.json"
    decision_path.write_text(
        json.dumps({"gate0": "BLOCKED", "training_authorized": False}) + "\n",
        encoding="utf-8",
    )
    (review_dir / "dataset_owner_outreach_draft.md").write_text(
        "# DRAFT — NOT SENT\n", encoding="utf-8"
    )
    (review_dir / "wp3_provenance_and_fallback_report.md").write_text(
        "# WP3 fixture\n", encoding="utf-8"
    )
    (generated_dir / "wp3_provenance_escalation.json").write_text(
        "{}\n", encoding="utf-8"
    )
    write_csv(
        generated_dir / "wp3_fallback_dataset_candidates.csv",
        [{"candidate_status": "CANDIDATE", "name": "fixture"}],
    )
    return audit_dir, staging_root, generated_dir, review_dir


def build_fixture(root: Path) -> tuple[Path, Path, Path, Path]:
    audit_dir, staging_root, generated_dir, review_dir = make_fixture(root)
    wp3.build_reviewer_assets(
        audit_dir=audit_dir,
        staging_root=staging_root,
        wp2_generated_dir=generated_dir,
        review_dir=review_dir,
    )
    return audit_dir, staging_root, generated_dir, review_dir


def assert_text_layout(layout: dict[str, object], canvas_size: list[int]) -> None:
    assert layout["complete"] is True
    assert layout["all_bounds_fit"] is True
    assert "".join(layout["lines"]) == layout["full_text"]
    width, height = canvas_size
    for left, top, right, bottom in layout["bounds"]:
        assert 0 <= left <= right <= width
        assert 0 <= top <= bottom <= height


def assert_render_layout_audit(generated_dir: Path) -> None:
    payload = json.loads(
        (generated_dir / "wp3_render_layout_audit.json").read_text(encoding="utf-8")
    )
    assert payload["status"] == "PASS_COMPLETE_TEXT_AND_BOUNDS"
    assert payload["checks"]["all_text_complete"] is True
    assert payload["checks"]["all_text_bounds_fit"] is True
    grouping_rows = read_csv(generated_dir / "wp3_grouping_review_index.csv")
    taxonomy_rows = read_csv(generated_dir / "wp3_taxonomy_reviewer_atlas.csv")
    grouping_csv = {row["proxy_sequence_id"]: row for row in grouping_rows}
    taxonomy_csv = {int(row["class_id"]): row for row in taxonomy_rows}
    audited_grouping: set[str] = set()
    audited_taxonomy: set[int] = set()

    for page in payload["grouping_pages"]:
        canvas_size = page["canvas_size"]
        assert_text_layout(page["title"], canvas_size)
        for row in page["rows"]:
            sequence_id = row["proxy_sequence_id"]
            audited_grouping.add(sequence_id)
            assert_text_layout(row["summary"], canvas_size)
            csv_row = grouping_csv[sequence_id]
            assert row["summary"]["full_text"] == wp3.grouping_summary(csv_row)
            for label in row["thumbnail_labels"]:
                assert_text_layout(label, canvas_size)

    for page in payload["taxonomy_pages"]:
        canvas_size = page["canvas_size"]
        assert_text_layout(page["title"], canvas_size)
        for row in page["rows"]:
            class_id = int(row["class_id"])
            audited_taxonomy.add(class_id)
            assert_text_layout(row["header"], canvas_size)
            assert_text_layout(row["conflict_flags"], canvas_size)
            assert row["conflict_flags"]["full_text"] == (
                f"conflicts: {taxonomy_csv[class_id]['conflict_flags']}"
            )
            for label in row["sample_labels"]:
                assert_text_layout(label, canvas_size)

    assert audited_grouping == set(grouping_csv)
    assert audited_taxonomy == set(taxonomy_csv)


def test_deterministic_sample_is_order_independent() -> None:
    first = wp3.deterministic_sample(["c", "a", "b", "a"], 2, salt="review")
    second = wp3.deterministic_sample(["b", "c", "a"], 2, salt="review")

    assert first == second
    assert len(first) == 2


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("4 7", {4, 7}),
        ("4;7", {4, 7}),
        ("4, 7", {4, 7}),
        (" 4 ", {4}),
    ],
)
def test_parse_class_ids_accepts_inventory_delimiters(raw: str, expected: set[int]) -> None:
    assert wp3.parse_class_ids(raw) == expected


def test_taxonomy_validation_rejects_missing_or_duplicate_classes() -> None:
    valid = [{"class_id": str(class_id)} for class_id in range(52)]
    wp3.validate_exact_class_coverage(valid)

    with pytest.raises(ValueError, match="exactly once"):
        wp3.validate_exact_class_coverage(valid[:-1])
    with pytest.raises(ValueError, match="duplicates"):
        wp3.validate_exact_class_coverage(valid + [{"class_id": "0"}])


def test_grouping_validation_is_fail_closed_for_non_proxy_status() -> None:
    with pytest.raises(ValueError, match="PROXY_ONLY"):
        wp3.validate_grouping_rows(
            [{"proxy_sequence_id": "sequence-1", "evidence_status": "APPROVED"}]
        )


def test_full_build_is_deterministic_and_preserves_source_and_decisions(tmp_path: Path) -> None:
    audit_dir, staging_root, generated_dir, review_dir = make_fixture(tmp_path)
    decision_path = review_dir / "decision_status.json"
    source_image = staging_root / "raw" / "archive" / "images" / "0000.jpg"
    decision_before = decision_path.read_bytes()
    source_before = source_image.read_bytes()

    first = wp3.build_reviewer_assets(
        audit_dir=audit_dir,
        staging_root=staging_root,
        wp2_generated_dir=generated_dir,
        review_dir=review_dir,
    )
    first_manifest = (generated_dir / "wp3_evidence_manifest.json").read_bytes()
    second = wp3.build_reviewer_assets(
        audit_dir=audit_dir,
        staging_root=staging_root,
        wp2_generated_dir=generated_dir,
        review_dir=review_dir,
    )

    assert first == second
    assert first["status"] == wp3.WP3_STATUS
    assert first["grouping_sequences"] == 52
    assert first["grouping_contact_sheets"] == 3
    assert first["taxonomy_classes"] == 52
    assert first["taxonomy_pages"] == 13
    assert first["verified_source_files"] == 52
    assert first_manifest == (generated_dir / "wp3_evidence_manifest.json").read_bytes()
    assert decision_path.read_bytes() == decision_before
    assert source_image.read_bytes() == source_before

    grouping_rows = read_csv(generated_dir / "wp3_grouping_review_index.csv")
    taxonomy_rows = read_csv(generated_dir / "wp3_taxonomy_reviewer_atlas.csv")
    lineage_rows = read_csv(generated_dir / "wp3_source_lineage.csv")
    assert {row["evidence_status"] for row in grouping_rows} == {wp3.PROXY_ONLY_STATUS}
    assert {row["review_status"] for row in taxonomy_rows} == {wp3.UNAPPROVED_STATUS}
    assert [int(row["class_id"]) for row in taxonomy_rows] == list(range(52))
    assert len(lineage_rows) == 52
    assert all(row["image_sha256"] and row["label_sha256"] for row in lineage_rows)
    assert_render_layout_audit(generated_dir)

    manifest_path = generated_dir / "wp3_evidence_manifest.json"
    verification = wp3.verify_wp3_manifest(manifest_path, review_dir)
    assert verification["valid"] is True
    assert verification["mismatches"] == []
    assert verification["source_input_count"] == 9
    assert verification["control_count"] == 5


def test_manifest_is_byte_identical_across_distinct_output_roots(tmp_path: Path) -> None:
    _, _, generated_a, _ = build_fixture(tmp_path / "root-a")
    _, _, generated_b, _ = build_fixture(tmp_path / "root-b")

    manifest_a = (generated_a / "wp3_evidence_manifest.json").read_bytes()
    manifest_b = (generated_b / "wp3_evidence_manifest.json").read_bytes()

    assert manifest_a == manifest_b
    assert sha256_file(generated_a / "wp3_evidence_manifest.json") == sha256_file(
        generated_b / "wp3_evidence_manifest.json"
    )
    assert b"root-a" not in manifest_a
    assert b"root-b" not in manifest_a


def test_manifest_verification_detects_tampering(tmp_path: Path) -> None:
    _, _, generated_dir, review_dir = build_fixture(tmp_path)
    index_path = review_dir / "assets" / "wp3" / "grouping" / "index.html"
    index_path.write_text(index_path.read_text(encoding="utf-8") + "tampered", encoding="utf-8")

    verification = wp3.verify_wp3_manifest(
        generated_dir / "wp3_evidence_manifest.json", review_dir
    )

    assert verification["valid"] is False
    assert any(
        mismatch["collection"] == "artifacts"
        and mismatch["reason"] == "size_or_sha256_mismatch"
        for mismatch in verification["mismatches"]
    )


def test_manifest_verification_detects_decision_status_tampering(tmp_path: Path) -> None:
    _, _, generated_dir, review_dir = build_fixture(tmp_path)
    decision_path = review_dir / "decision_status.json"
    decision_path.write_text(
        json.dumps({"gate0": "PASS", "training_authorized": True}) + "\n",
        encoding="utf-8",
    )

    verification = wp3.verify_wp3_manifest(
        generated_dir / "wp3_evidence_manifest.json", review_dir
    )

    assert verification["valid"] is False
    assert any(
        mismatch.get("id") == "decision_status"
        and mismatch["reason"] in {"size_or_sha256_mismatch", "required_control_missing_or_invalid"}
        for mismatch in verification["mismatches"]
    )


@pytest.mark.parametrize(
    ("relative_path", "input_id"),
    [
        ("results/data_audit/fixture/image_inventory.csv", "image_inventory"),
        (
            "results/data_audit/fixture/source_preservation_proof.json",
            "source_preservation_proof",
        ),
        ("results/data_audit/fixture/wp1_artifact_manifest.json", "wp1_artifact_manifest"),
        ("results/data_audit/fixture/provenance_evidence.json", "provenance_evidence"),
    ],
)
def test_manifest_verification_detects_each_audit_source_category_tampering(
    tmp_path: Path, relative_path: str, input_id: str
) -> None:
    _, _, generated_dir, review_dir = build_fixture(tmp_path)
    source_path = tmp_path / relative_path
    source_path.write_bytes(source_path.read_bytes() + b"tampered")

    verification = wp3.verify_wp3_manifest(
        generated_dir / "wp3_evidence_manifest.json", review_dir
    )

    assert verification["valid"] is False
    assert any(
        mismatch["collection"] == "source_inputs"
        and mismatch.get("id") == input_id
        and mismatch["reason"] == "size_or_sha256_mismatch"
        for mismatch in verification["mismatches"]
    )


@pytest.mark.parametrize(
    ("filename", "input_id"),
    [
        ("grouping_proxy_clusters.csv", "wp2_grouping_clusters"),
        ("grouping_proxy_edges.csv", "wp2_grouping_edges"),
        ("taxonomy_review.csv", "wp2_taxonomy_review"),
        ("wp2_generated_manifest.json", "wp2_generated_manifest"),
    ],
)
def test_manifest_verification_detects_each_wp2_source_category_tampering(
    tmp_path: Path, filename: str, input_id: str
) -> None:
    _, _, generated_dir, review_dir = build_fixture(tmp_path)
    source_path = generated_dir / filename
    source_path.write_bytes(source_path.read_bytes() + b"tampered")

    verification = wp3.verify_wp3_manifest(
        generated_dir / "wp3_evidence_manifest.json", review_dir
    )

    assert verification["valid"] is False
    assert any(
        mismatch["collection"] == "source_inputs"
        and mismatch.get("id") == input_id
        and mismatch["reason"] == "size_or_sha256_mismatch"
        for mismatch in verification["mismatches"]
    )


def test_manifest_verification_detects_missing_source(tmp_path: Path) -> None:
    audit_dir, _, generated_dir, review_dir = build_fixture(tmp_path)
    (audit_dir / "image_inventory.csv").unlink()

    verification = wp3.verify_wp3_manifest(
        generated_dir / "wp3_evidence_manifest.json", review_dir
    )

    assert verification["valid"] is False
    assert any(
        mismatch["collection"] == "source_inputs"
        and mismatch.get("id") == "image_inventory"
        and mismatch["reason"] == "missing"
        for mismatch in verification["mismatches"]
    )


def test_manifest_verification_detects_source_wrong_type(tmp_path: Path) -> None:
    _, _, generated_dir, review_dir = build_fixture(tmp_path)
    source_path = generated_dir / "taxonomy_review.csv"
    source_path.unlink()
    source_path.mkdir()

    verification = wp3.verify_wp3_manifest(
        generated_dir / "wp3_evidence_manifest.json", review_dir
    )

    assert verification["valid"] is False
    assert any(
        mismatch["collection"] == "source_inputs"
        and mismatch.get("id") == "wp2_taxonomy_review"
        and mismatch["reason"] == "wrong_type"
        for mismatch in verification["mismatches"]
    )


def test_manifest_verification_rejects_traversal_path(tmp_path: Path) -> None:
    _, _, generated_dir, review_dir = build_fixture(tmp_path)
    manifest_path = generated_dir / "wp3_evidence_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source_inputs"][0]["path"] = "../outside.csv"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    verification = wp3.verify_wp3_manifest(manifest_path, review_dir)

    assert verification["valid"] is False
    assert any(
        mismatch["collection"] == "source_inputs"
        and mismatch["reason"] == "path_escape"
        for mismatch in verification["mismatches"]
    )


@pytest.mark.parametrize(
    ("field", "replacement", "expected_reason"),
    [
        ("decision_status_sha256", "0" * 64, "control_hash_mismatch"),
        ("source_tree_manifest_sha256", "0" * 64, "source_tree_hash_mismatch"),
    ],
)
def test_manifest_verification_rejects_explicit_control_hash_tampering(
    tmp_path: Path, field: str, replacement: str, expected_reason: str
) -> None:
    _, _, generated_dir, review_dir = build_fixture(tmp_path)
    manifest_path = generated_dir / "wp3_evidence_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest[field] = replacement
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    verification = wp3.verify_wp3_manifest(manifest_path, review_dir)

    assert verification["valid"] is False
    assert any(
        mismatch["reason"] == expected_reason
        for mismatch in verification["mismatches"]
    )
