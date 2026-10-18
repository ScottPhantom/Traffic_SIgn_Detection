from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from jsonschema import Draft202012Validator
from PIL import Image

SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "build_wp2_review_packet.py"
SPEC = importlib.util.spec_from_file_location("build_wp2_review_packet", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
wp2 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp2
SPEC.loader.exec_module(wp2)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_similarity_classification_is_fail_closed_at_thresholds() -> None:
    strong = {
        "same_dimensions": True,
        "thumbnail_mae": 12.0,
        "dhash_distance": 8,
        "rgb_histogram_cosine": 0.98,
    }
    uncertain = {
        "same_dimensions": True,
        "thumbnail_mae": 12.01,
        "dhash_distance": 9,
        "rgb_histogram_cosine": 0.97,
    }
    dimension_mismatch = {**strong, "same_dimensions": False}

    assert wp2.classify_similarity(strong) == "strong_candidate"
    assert wp2.classify_similarity(uncertain) == "uncertain"
    assert wp2.classify_similarity(dimension_mismatch) == "adjacency_only"


def test_candidate_clusters_only_join_strong_edges() -> None:
    edges = [
        {
            "left_stem": "0001",
            "right_stem": "0002",
            "proxy_status": "strong_candidate",
            "cross_split": "True",
        },
        {
            "left_stem": "0002",
            "right_stem": "0003",
            "proxy_status": "uncertain",
            "cross_split": "False",
        },
        {
            "left_stem": "0010",
            "right_stem": "0011",
            "proxy_status": "strong_candidate",
            "cross_split": "False",
        },
    ]

    clusters, by_stem = wp2.build_candidate_clusters(edges)

    assert [row["member_count"] for row in clusters] == [2, 2]
    assert by_stem["0001"] == by_stem["0002"]
    assert "0003" not in by_stem
    assert by_stem["0010"] == by_stem["0011"]
    assert clusters[0]["evidence_status"] == "PROXY_ONLY_NOT_GROUP_TRUTH"


def test_bbox_geometry_reports_overflow_without_clamping() -> None:
    geometry = wp2.bbox_pixel_geometry(0.95, 0.5, 0.2, 0.4, 100, 50)

    assert geometry["x_min"] == 85.0
    assert geometry["x_max"] == 105.0
    assert geometry["overflow_right_px"] == 5.0
    assert geometry["y_min"] == 15.0
    assert geometry["y_max"] == 35.0


def test_render_bbox_review_preserves_source_bytes(tmp_path: Path) -> None:
    image_path = tmp_path / "0248.jpg"
    label_path = tmp_path / "0248.txt"
    output_image = tmp_path / "review" / "bbox.png"
    output_json = tmp_path / "review" / "bbox.json"
    Image.new("RGB", (100, 50), "white").save(image_path)
    label_path.write_text("49 0.95 0.5 0.2 0.4\n", encoding="utf-8")
    image_before = image_path.read_bytes()
    label_before = label_path.read_bytes()

    payload = wp2.render_bbox_review(image_path, label_path, output_image, output_json)

    assert output_image.is_file()
    assert json.loads(output_json.read_text(encoding="utf-8"))["decision_status"] == "PENDING"
    assert payload["boxes"][0]["pixels"]["overflow_right_px"] == 5.0
    assert image_path.read_bytes() == image_before
    assert label_path.read_bytes() == label_before


def test_grouping_builder_produces_proxy_only_outputs(tmp_path: Path) -> None:
    audit_dir = tmp_path / "audit"
    images_dir = tmp_path / "images"
    output_dir = tmp_path / "output"
    images_dir.mkdir()
    base = np.zeros((60, 100, 3), dtype=np.uint8)
    base[:, :, 1] = 90
    Image.fromarray(base).save(images_dir / "0001.jpg")
    Image.fromarray(base).save(images_dir / "0002.jpg")
    Image.new("RGB", (80, 40), "red").save(images_dir / "0003.jpg")
    rows = [
        {
            "left_stem": "0001",
            "left_split": "train",
            "right_stem": "0002",
            "right_split": "test",
            "cross_split": "True",
            "evidence_status": "proxy_only_not_group_ground_truth",
        },
        {
            "left_stem": "0002",
            "left_split": "test",
            "right_stem": "0003",
            "right_split": "test",
            "cross_split": "False",
            "evidence_status": "proxy_only_not_group_ground_truth",
        },
    ]
    write_csv(audit_dir / "adjacent_pair_leakage.csv", list(rows[0]), rows)

    summary = wp2.build_grouping_evidence(audit_dir, images_dir, output_dir)

    assert summary["status"] == "PROXY_ONLY_NOT_APPROVED_FOR_SPLITTING"
    assert summary["counts"]["strong_candidate_edges"] == 1
    assert summary["counts"]["candidate_sequences"] == 1
    assert summary["counts"]["images_in_candidate_sequences"] == 2
    assert "not video" in summary["evidence_boundary"]
    edges = read_rows(output_dir / "grouping_proxy_edges.csv")
    assert edges[0]["proxy_sequence_id"].startswith("proxy_sequence_")
    assert edges[1]["proxy_sequence_id"] == ""


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def support_row(class_id: int, *, box_count: int = 60) -> dict[str, str]:
    return {
        "class_id": str(class_id),
        "sign_code": f"C.{class_id}",
        "name_en": f"English {class_id}",
        "name_vi": f"Vietnamese {class_id}",
        "image_count": str(box_count),
        "box_count": str(box_count),
        "train_image_count": str(max(0, box_count - 1)),
        "test_image_count": "1" if box_count else "0",
        "unsplit_image_count": "0",
    }


def write_support_table(audit_dir: Path, class_ids: list[int]) -> None:
    rows = [support_row(class_id) for class_id in class_ids]
    write_csv(audit_dir / "per_class_counts.csv", list(rows[0]), rows)


def write_taxonomy_table(path: Path, class_ids: list[int]) -> None:
    lines = [
        (
            f"| {class_id} | C.{class_id} | Vietnamese {class_id} / English {class_id} | "
            "family | — | None | H | 60 / 60 | UNAPPROVED |"
        )
        for class_id in class_ids
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_rare_rows() -> list[dict[str, str]]:
    rows = []
    for class_id in range(52):
        box_count = {44: 3, 51: 5}.get(class_id, 60)
        row = support_row(class_id, box_count=box_count)
        row.update(
            {
                "risk_band": wp2.rare_risk_band(box_count),
                "decision_status": "PENDING",
                "allowed_options": "|".join(wp2.D04_ALLOWED_OPTIONS),
                "risk_note": "fixture",
            }
        )
        rows.append(row)
    return rows


def previous_d04_snapshot(record: dict[str, object]) -> dict[str, object]:
    return {
        "status": record["status"],
        "selected_option": record["selected_option"],
        "reviewer": record["reviewer"],
        "decided_at": record["decided_at"],
        "rationale": record["rationale"],
        "evidence_links": copy.deepcopy(record["evidence_links"]),
    }


def make_resolved_d04_payload() -> tuple[dict[str, object], list[dict[str, str]]]:
    rare_rows = make_rare_rows()
    payload = wp2.build_d04_decision_template(rare_rows)
    choices = {"44": "collect_more", "51": "out_of_scope"}
    for offset, (class_id, record) in enumerate(payload["class_decisions"].items()):
        previous = previous_d04_snapshot(record)
        record.update(
            {
                "status": "RESOLVED",
                "selected_option": choices[class_id],
                "reviewer": "domain-reviewer",
                "decided_at": f"2026-10-10T15:0{offset + 1}:00+07:00",
                "rationale": f"Reviewed class {class_id}",
                "evidence_links": [f"evidence://class/{class_id}"],
                "history": [
                    {
                        "changed_at": f"2026-10-10T15:0{offset}:00+07:00",
                        "changed_by": "domain-reviewer",
                        "previous": previous,
                    }
                ],
            }
        )
    payload["status"] = "RESOLVED"
    return payload, rare_rows


def d04_schema_validator(rare_rows: list[dict[str, str]]) -> Draft202012Validator:
    template = wp2.build_d04_decision_template(rare_rows)
    schema = wp2.build_decision_status_schema(template)
    return Draft202012Validator(
        schema,
        format_checker=Draft202012Validator.FORMAT_CHECKER,
    )


def wrap_d04_for_schema(payload: dict[str, object]) -> dict[str, object]:
    return {
        "gate0": "BLOCKED",
        "training_authorized": False,
        "decisions": {"D-04": payload},
    }


@pytest.mark.parametrize(
    ("class_ids", "expected_fragment"),
    [
        (list(range(51)), "missing=[51]"),
        (list(range(51)) + [50], "duplicates=[50]"),
    ],
)
def test_rare_builder_rejects_incomplete_or_duplicate_class_ids(
    tmp_path: Path,
    class_ids: list[int],
    expected_fragment: str,
) -> None:
    audit_dir = tmp_path / "audit"
    output_dir = tmp_path / "output"
    write_support_table(audit_dir, class_ids)

    with pytest.raises(ValueError, match=r"each class_id 0\.\.51 exactly once") as error:
        wp2.build_rare_class_table(audit_dir, output_dir)

    assert expected_fragment in str(error.value)
    assert not (output_dir / "rare_class_risk.csv").exists()


def test_taxonomy_builder_rejects_duplicate_id_and_missing_id(tmp_path: Path) -> None:
    audit_dir = tmp_path / "audit"
    output_dir = tmp_path / "output"
    taxonomy_doc = tmp_path / "taxonomy.md"
    write_support_table(audit_dir, list(range(52)))
    write_taxonomy_table(taxonomy_doc, list(range(51)) + [50])

    with pytest.raises(ValueError, match=r"duplicates=\[50\].*missing=\[51\]"):
        wp2.build_taxonomy_review_table(taxonomy_doc, audit_dir, output_dir)

    assert not (output_dir / "taxonomy_review.csv").exists()


def test_taxonomy_builder_rejects_incomplete_support_source(tmp_path: Path) -> None:
    audit_dir = tmp_path / "audit"
    output_dir = tmp_path / "output"
    taxonomy_doc = tmp_path / "taxonomy.md"
    write_support_table(audit_dir, list(range(51)))
    write_taxonomy_table(taxonomy_doc, list(range(52)))

    with pytest.raises(ValueError, match=r"missing=\[51\]"):
        wp2.build_taxonomy_review_table(taxonomy_doc, audit_dir, output_dir)

    assert not (output_dir / "taxonomy_review.csv").exists()


def test_d04_template_has_complete_class_keyed_pending_records() -> None:
    template = wp2.build_d04_decision_template(make_rare_rows())

    assert template["status"] == "PENDING"
    assert template["in_scope_class_ids"] == [44, 51]
    assert set(template["allowed_options"]) == set(wp2.D04_ALLOWED_OPTIONS)
    assert set(template["class_decisions"]) == {"44", "51"}
    for record in template["class_decisions"].values():
        assert wp2.D04_CLASS_REQUIRED_FIELDS <= record.keys()
        assert record["status"] == "PENDING"
        assert record["selected_option"] is None
        assert record["history"] == []
    assert wp2.validate_d04_decision_payload(template, make_rare_rows()) == "PENDING"


def test_d04_rejects_missing_record_field_and_invalid_option() -> None:
    rare_rows = make_rare_rows()
    missing_field = wp2.build_d04_decision_template(rare_rows)
    missing_field["class_decisions"]["44"].pop("history")
    with pytest.raises(ValueError, match="record is missing"):
        wp2.validate_d04_decision_payload(missing_field, rare_rows)

    invalid_option = wp2.build_d04_decision_template(rare_rows)
    invalid_option["class_decisions"]["44"]["selected_option"] = "silent_drop"
    with pytest.raises(ValueError, match="invalid selected_option"):
        wp2.validate_d04_decision_payload(invalid_option, rare_rows)

    missing_history = wp2.build_d04_decision_template(rare_rows)
    missing_history["class_decisions"]["44"].update(
        {
            "status": "RESOLVED",
            "selected_option": "collect_more",
            "reviewer": "domain-reviewer",
            "decided_at": "2026-10-10T15:00:00+07:00",
            "rationale": "Collect additional independent groups",
            "evidence_links": ["evidence://class/44"],
        }
    )
    with pytest.raises(ValueError, match="history"):
        wp2.validate_d04_decision_payload(missing_history, rare_rows)


def test_d04_refuses_aggregate_resolution_while_any_class_is_pending() -> None:
    rare_rows = make_rare_rows()
    payload = wp2.build_d04_decision_template(rare_rows)
    payload["status"] = "RESOLVED"

    with pytest.raises(ValueError, match="any in-scope class remains unresolved"):
        wp2.validate_d04_decision_payload(payload, rare_rows)


def test_d04_supports_different_per_class_choices_and_audit_history() -> None:
    payload, rare_rows = make_resolved_d04_payload()
    validator = d04_schema_validator(rare_rows)

    assert wp2.validate_d04_decision_payload(payload, rare_rows) == "RESOLVED"
    assert validator.is_valid(wrap_d04_for_schema(payload))
    assert payload["class_decisions"]["44"]["selected_option"] == "collect_more"
    assert payload["class_decisions"]["51"]["selected_option"] == "out_of_scope"
    assert payload["class_decisions"]["44"]["history"][0]["previous"]["status"] == "PENDING"


def test_d04_rejects_exact_qa_malformed_resolved_payload_in_runtime_and_schema() -> None:
    payload, rare_rows = make_resolved_d04_payload()
    for record in payload["class_decisions"].values():
        record.update(
            {
                "reviewer": " ",
                "decided_at": "not-a-time",
                "rationale": " ",
                "evidence_links": [""],
                "history": [{}],
            }
        )

    with pytest.raises(ValueError):
        wp2.validate_d04_decision_payload(payload, rare_rows)
    assert not d04_schema_validator(rare_rows).is_valid(wrap_d04_for_schema(payload))


@pytest.mark.parametrize(
    ("field", "value", "expected_fragment"),
    [
        ("reviewer", " ", "trimmed and non-empty"),
        ("rationale", " rationale-with-leading-space", "trimmed and non-empty"),
        ("decided_at", "not-a-time", "RFC 3339 timestamp with timezone"),
        ("decided_at", "2026-10-10T15:01:00", "RFC 3339 timestamp with timezone"),
        ("evidence_links", [], "at least one reference"),
        ("evidence_links", [""], "trimmed and non-empty"),
        ("evidence_links", [42], "must be a string"),
        ("evidence_links", "evidence://class/44", "must be a list"),
        ("reviewer", 42, "must be a string"),
        ("history", [{}], "must contain exactly"),
    ],
)
def test_d04_rejects_malformed_resolved_field_variants_in_runtime_and_schema(
    field: str,
    value: object,
    expected_fragment: str,
) -> None:
    payload, rare_rows = make_resolved_d04_payload()
    payload["class_decisions"]["44"][field] = value

    with pytest.raises(ValueError, match=expected_fragment):
        wp2.validate_d04_decision_payload(payload, rare_rows)
    assert not d04_schema_validator(rare_rows).is_valid(wrap_d04_for_schema(payload))


@pytest.mark.parametrize(
    ("mutation", "expected_fragment"),
    [
        ({"changed_at": "not-a-time"}, "RFC 3339 timestamp with timezone"),
        ({"changed_by": " "}, "trimmed and non-empty"),
        ({"previous": {"status": "PENDING"}}, "must contain exactly"),
    ],
)
def test_d04_rejects_malformed_history_variants_in_runtime_and_schema(
    mutation: dict[str, object],
    expected_fragment: str,
) -> None:
    payload, rare_rows = make_resolved_d04_payload()
    history_item = payload["class_decisions"]["44"]["history"][0]
    history_item.update(mutation)

    with pytest.raises(ValueError, match=expected_fragment):
        wp2.validate_d04_decision_payload(payload, rare_rows)
    assert not d04_schema_validator(rare_rows).is_valid(wrap_d04_for_schema(payload))


def test_d04_runtime_enforces_append_order_that_json_schema_cannot_express() -> None:
    payload, rare_rows = make_resolved_d04_payload()
    history = payload["class_decisions"]["44"]["history"]
    history.append(
        {
            "changed_at": history[0]["changed_at"],
            "changed_by": "domain-reviewer",
            "previous": copy.deepcopy(history[0]["previous"]),
        }
    )

    with pytest.raises(ValueError, match="strictly append-ordered"):
        wp2.validate_d04_decision_payload(payload, rare_rows)
    assert d04_schema_validator(rare_rows).is_valid(wrap_d04_for_schema(payload))


def test_manifest_records_generated_artifact_hashes(tmp_path: Path) -> None:
    generated = tmp_path / "review" / "generated"
    generated.mkdir(parents=True)
    artifact = generated / "sample.json"
    artifact.write_text('{"status":"PENDING"}\n', encoding="utf-8")

    manifest = wp2.build_manifest(generated)

    assert manifest["status"] == "REVIEW_EVIDENCE_ONLY_NO_TRAINING_AUTHORIZATION"
    assert manifest["artifacts"] == [
        {
            "path": "generated/sample.json",
            "size": artifact.stat().st_size,
            "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        }
    ]
