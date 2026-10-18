from __future__ import annotations

import copy
import importlib.util
import json
import math
import os
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/audit_e0_compute_readiness.py"
SPEC = importlib.util.spec_from_file_location("audit_e0_compute_readiness", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
wp6 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp6
SPEC.loader.exec_module(wp6)

EVIDENCE_PATH = REPO_ROOT / wp6.EVIDENCE_RELATIVE_PATH
REPORT_PATH = REPO_ROOT / wp6.REPORT_RELATIVE_PATH
MANIFEST_PATH = REPO_ROOT / wp6.MANIFEST_RELATIVE_PATH
ATTESTATION_PATH = REPO_ROOT / wp6.ATTESTATION_RELATIVE_PATH


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def verify_payload(tmp_path: Path, payload: Any, name: str) -> dict[str, Any]:
    path = tmp_path / name
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return wp6.verify_manifest(path, REPO_ROOT)


def stage_package(tmp_path: Path) -> Path:
    manifest = read_json(MANIFEST_PATH)
    for record in manifest["sources"]:
        source = REPO_ROOT / record["path"]
        target = tmp_path / record["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        os.link(source, target)
    for record in manifest["artifacts"]:
        source = REPO_ROOT / record["path"]
        target = tmp_path / record["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    staged_manifest = tmp_path / wp6.MANIFEST_RELATIVE_PATH
    staged_manifest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(MANIFEST_PATH, staged_manifest)
    return staged_manifest


def refresh_staged_artifacts(staged_manifest: Path) -> None:
    root = staged_manifest.parents[3]
    payload = read_json(staged_manifest)
    for record in payload["artifacts"]:
        path = root / record["path"]
        record["sha256"] = wp6.sha256_file(path)
        record["size"] = path.stat().st_size
    payload["total_artifact_bytes"] = sum(
        record["size"] for record in payload["artifacts"]
    )
    staged_manifest.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_package_verifies_with_exact_rosters_and_excludes_manifest() -> None:
    result = wp6.verify_manifest(MANIFEST_PATH, REPO_ROOT)
    assert result == {
        "valid": True,
        "errors": [],
        "source_count": wp6.EXPECTED_SOURCE_COUNT,
        "artifact_count": 3,
        "status": wp6.STATUS,
    }
    manifest = read_json(MANIFEST_PATH)
    assert manifest["schema_version"] == wp6.MANIFEST_SCHEMA_VERSION == 2
    assert manifest["source_count"] == len(manifest["sources"]) == 20
    assert manifest["artifact_count"] == len(manifest["artifacts"]) == 3
    assert manifest["manifest_self_in_artifact_count"] is False
    assert manifest["artifact_count_semantics"] == "EXCLUDES_MANIFEST_FILE"
    assert manifest["trusted_attestation_sha256"] == wp6.TRUSTED_ATTESTATION_SHA256
    assert {row["path"] for row in manifest["artifacts"]} == {
        wp6.EVIDENCE_RELATIVE_PATH,
        wp6.ATTESTATION_RELATIVE_PATH,
        wp6.REPORT_RELATIVE_PATH,
    }
    assert wp6.MANIFEST_RELATIVE_PATH not in {
        row["path"] for row in manifest["artifacts"]
    }
    assert manifest["total_artifact_bytes"] == sum(
        (REPO_ROOT / row["path"]).stat().st_size for row in manifest["artifacts"]
    )


def test_all_source_hashes_and_pinned_hashes_match_current_files() -> None:
    manifest = read_json(MANIFEST_PATH)
    records = {row["id"]: row for row in manifest["sources"]}
    assert len(records) == wp6.EXPECTED_SOURCE_COUNT
    for item_id, path, pinned_hash in wp6.source_contract(REPO_ROOT):
        record = records[item_id]
        assert record["path"] == path.relative_to(REPO_ROOT).as_posix()
        assert record["sha256"] == wp6.sha256_file(path)
        assert record["size"] == path.stat().st_size
        if pinned_hash is not None:
            assert record["sha256"] == pinned_hash


def test_evidence_model_and_gtsrb_schemas_are_exact() -> None:
    evidence = read_json(EVIDENCE_PATH)
    wp6.validate_evidence(evidence, REPO_ROOT)
    model = evidence["model"]
    assert model["architecture_classification"].startswith("SMALL_VGG_INSPIRED")
    assert model["input_shape"] == [None, 32, 32, 3]
    assert model["output_shape"] == [None, 43]
    assert model["parameter_count"] == 2_188_107
    assert model["label_count"] == 43
    for split_name, expected in wp6.EXPECTED_SPLITS.items():
        split = evidence["datasets"][split_name]
        assert split["samples"] == expected["samples"]
        assert split["sha256"] == expected["sha256"]
        assert split["features"]["shape"] == [expected["samples"], 32, 32, 3]
        assert split["features"]["dtype"] == "uint8"
        assert split["labels"]["class_ids"] == list(range(43))
        assert sum(split["labels"]["class_support"].values()) == expected["samples"]


def test_runtime_inventory_matches_live_tensorflow_device_contract() -> None:
    evidence = read_json(EVIDENCE_PATH)
    packaged = evidence["runtime"]
    live, _keras = wp6.collect_runtime_inventory(REPO_ROOT)
    for key in (
        "python_version",
        "tensorflow_version",
        "keras_version",
        "physical_devices",
        "logical_devices",
        "gpu_visible_to_tensorflow",
        "execution_backend",
    ):
        assert packaged[key] == live[key]
    assert not Path(packaged["python_executable"]).is_absolute()
    assert packaged["execution_backend"] == "TENSORFLOW_CPU_ONLY"
    assert packaged["gpu_visible_to_tensorflow"] is False
    assert packaged["logical_devices"] == [{"name": "/device:CPU:0", "type": "CPU"}]
    forbidden_keys = {
        "serial_number",
        "serialnumber",
        "hardware_uuid",
        "hardwareuuid",
        "username",
        "user_name",
    }
    assert not wp6.nested_mapping_keys(evidence["hardware"]) & forbidden_keys


def test_latency_contract_and_statistics_recompute_from_300_observations() -> None:
    evidence = read_json(EVIDENCE_PATH)
    latency = evidence["latency_benchmark"]
    assert latency["batch_size"] == 1
    assert latency["warmup_iterations"] == 20
    assert latency["measured_repeats"] == 3
    assert latency["iterations_per_repeat"] == 100
    assert latency["measured_iterations"] == 300
    assert latency["timed_operations"] == wp6.TIMED_OPERATIONS
    assert latency["excluded_operations"] == wp6.EXCLUDED_OPERATIONS
    assert latency["prediction_trace_sha256"] == wp6.EXPECTED_PREDICTION_TRACE_SHA256
    observations = latency["latency_ms"]["raw_observations"]
    assert len(observations) == 300
    assert all(math.isfinite(value) and value > 0 for value in observations)
    recomputed = wp6.summarize_latencies(observations)
    for key, expected in recomputed.items():
        actual = latency["latency_ms"][key]
        if isinstance(expected, list):
            assert actual == pytest.approx(expected, rel=1e-12, abs=1e-12)
        else:
            assert actual == pytest.approx(expected, rel=1e-12, abs=1e-12)


def test_clean_build_attestation_binds_runtime_trace_and_statistics() -> None:
    evidence = read_json(EVIDENCE_PATH)
    attestation = read_json(ATTESTATION_PATH)
    wp6.validate_benchmark_attestation(attestation, evidence)
    assert wp6.sha256_file(ATTESTATION_PATH) == wp6.TRUSTED_ATTESTATION_SHA256
    observations = evidence["latency_benchmark"]["latency_ms"]["raw_observations"]
    assert attestation["status"] == wp6.ATTESTATION_STATUS
    assert attestation["latency_observation_count"] == 300
    assert attestation["latency_observations_sha256"] == wp6.canonical_json_sha256(
        observations
    )
    assert attestation["runtime_attestation"] == wp6.runtime_attestation_payload(
        evidence["runtime"]
    )
    assert attestation["prediction_trace_sha256"] == wp6.EXPECTED_PREDICTION_TRACE_SHA256


def test_governance_and_calibration_boundaries_remain_fail_closed() -> None:
    evidence = read_json(EVIDENCE_PATH)
    controls = evidence["upstream_controls"]
    assert controls["decision_status"] == {
        "D-01": "PENDING",
        "D-02": "PENDING",
        "D-03": "PENDING",
        "D-04": "PENDING",
        "D-05": "PENDING",
        "G0.4-bbox-0248": "PENDING",
    }
    assert controls["gate0"] == "BLOCKED"
    assert controls["training_authorized"] is False
    assert controls["experiment_acceptance_template"] == "UNAPPROVED_INACTIVE"
    readiness = evidence["calibration_ood_readiness"]
    assert readiness["valid_split_suitability"].startswith("DIAGNOSTIC_ONLY")
    assert "DO_NOT_SELECT" in readiness["test_split_policy"]
    assert set(readiness["actions_not_performed"]) == {
        "No temperature fitting",
        "No UNKNOWN/OOD threshold selection",
        "No OOD performance calculation",
        "No training or fine-tuning",
        "No model promotion",
        "No split mutation",
    }


def test_non_timing_fingerprint_excludes_clock_and_timing_noise() -> None:
    evidence = read_json(EVIDENCE_PATH)
    original = wp6.canonical_json_sha256(wp6.deterministic_non_timing_payload(evidence))
    assert original == evidence["deterministic_non_timing_sha256"]
    changed = copy.deepcopy(evidence)
    changed["observed_at_utc"] = "2099-01-01T00:00:00+00:00"
    changed["latency_benchmark"]["latency_ms"]["raw_observations"] = [1.0] * 300
    changed["latency_benchmark"]["latency_ms"]["p50"] = 1.0
    changed["latency_benchmark"]["prediction_trace_sha256"] = "0" * 64
    assert (
        wp6.canonical_json_sha256(wp6.deterministic_non_timing_payload(changed))
        == original
    )


def test_evidence_semantic_tampering_is_rejected_even_after_refingerprinting() -> None:
    evidence = read_json(EVIDENCE_PATH)
    mutations: list[tuple[str, Any]] = []

    wrong_source = copy.deepcopy(evidence)
    wrong_source["sources"][0]["sha256"] = "0" * 64
    wrong_source["deterministic_non_timing_sha256"] = wp6.canonical_json_sha256(
        wp6.deterministic_non_timing_payload(wrong_source)
    )
    mutations.append(("pinned source", wrong_source))

    wrong_backend = copy.deepcopy(evidence)
    wrong_backend["runtime"]["execution_backend"] = "TENSORFLOW_GPU"
    wrong_backend["deterministic_non_timing_sha256"] = wp6.canonical_json_sha256(
        wp6.deterministic_non_timing_payload(wrong_backend)
    )
    mutations.append(("backend", wrong_backend))

    wrong_stat = copy.deepcopy(evidence)
    wrong_stat["latency_benchmark"]["latency_ms"]["p95"] += 1.0
    mutations.append(("latency statistic", wrong_stat))

    wrong_decision = copy.deepcopy(evidence)
    wrong_decision["upstream_controls"]["decision_status"]["D-05"] = "RESOLVED"
    wrong_decision["deterministic_non_timing_sha256"] = wp6.canonical_json_sha256(
        wp6.deterministic_non_timing_payload(wrong_decision)
    )
    mutations.append(("decision", wrong_decision))

    for _name, payload in mutations:
        with pytest.raises(ValueError, match="WP6"):
            wp6.validate_evidence(payload, REPO_ROOT)


@pytest.mark.parametrize(
    "forgery",
    [
        "canonical_vgg16",
        "vietnamese_holdout",
        "d05_gpu_vietnam_claim",
        "coherent_false_gpu",
        "coherent_999ms_latency",
    ],
)
def test_verifier_rejects_coherently_rehashed_qa_semantic_forgeries(
    tmp_path: Path, forgery: str
) -> None:
    staged_manifest = stage_package(tmp_path)
    evidence_path = tmp_path / wp6.EVIDENCE_RELATIVE_PATH
    report_path = tmp_path / wp6.REPORT_RELATIVE_PATH
    evidence = read_json(evidence_path)

    if forgery == "canonical_vgg16":
        evidence["model"]["architecture_classification"] = "CANONICAL_KERAS_VGG16"
    elif forgery == "vietnamese_holdout":
        evidence["calibration_ood_readiness"]["valid_split_suitability"] = (
            "INDEPENDENT_VIETNAMESE_HOLDOUT_VALIDATED"
        )
    elif forgery == "d05_gpu_vietnam_claim":
        evidence["latency_benchmark"]["interpretation_boundary"] = (
            "D05_PASSED_METAL_GPU_VIETNAM_VALIDATED"
        )
    elif forgery == "coherent_false_gpu":
        evidence["runtime"]["physical_devices"] = [
            {"name": "/physical_device:GPU:0", "type": "GPU"}
        ]
        evidence["runtime"]["logical_devices"] = [
            {"name": "/device:GPU:0", "type": "GPU"}
        ]
        evidence["runtime"]["gpu_visible_to_tensorflow"] = True
        evidence["runtime"]["execution_backend"] = "TENSORFLOW_GPU"
        evidence["runtime"]["tensorflow_metal_version"] = "1.2.0-forged"
    elif forgery == "coherent_999ms_latency":
        values = [999.0] * wp6.MEASURED_ITERATIONS
        summary = wp6.summarize_latencies(values)
        evidence["latency_benchmark"]["latency_ms"] = {
            **summary,
            "raw_observations": values,
        }

    evidence["deterministic_non_timing_sha256"] = wp6.canonical_json_sha256(
        wp6.deterministic_non_timing_payload(evidence)
    )
    if forgery == "coherent_999ms_latency":
        wp6.write_json(
            tmp_path / wp6.ATTESTATION_RELATIVE_PATH,
            wp6.build_benchmark_attestation(evidence),
        )
    evidence_path.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(wp6.render_report(evidence), encoding="utf-8")
    refresh_staged_artifacts(staged_manifest)

    result = wp6.verify_manifest(staged_manifest, tmp_path)
    assert result["valid"] is False
    assert result["errors"], forgery
    if forgery == "coherent_999ms_latency":
        assert "trusted attestation source anchor mismatch" in result["errors"]


@pytest.mark.parametrize("attack", ["deleted", "substituted", "old_attestation"])
def test_source_anchor_rejects_deleted_substituted_and_old_attestations(
    tmp_path: Path, attack: str
) -> None:
    staged_manifest = stage_package(tmp_path)
    attestation_path = tmp_path / wp6.ATTESTATION_RELATIVE_PATH
    if attack == "deleted":
        attestation_path.unlink()
    elif attack == "substituted":
        wp6.write_json(attestation_path, {"status": "FORGED_ATTESTATION"})
        refresh_staged_artifacts(staged_manifest)
    else:
        old = read_json(attestation_path)
        old["status"] = "WP6_OLD_UNTRUSTED_ATTESTATION"
        wp6.write_json(attestation_path, old)
        refresh_staged_artifacts(staged_manifest)
    result = wp6.verify_manifest(staged_manifest, tmp_path)
    assert result["valid"] is False
    assert result["errors"]
    if attack != "deleted":
        assert "trusted attestation source anchor mismatch" in result["errors"]


def test_unpinned_candidate_cannot_modify_or_promote_official_package(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    forged = read_json(EVIDENCE_PATH)
    values = [777.0] * wp6.MEASURED_ITERATIONS
    forged["latency_benchmark"]["latency_ms"] = {
        **wp6.summarize_latencies(values),
        "raw_observations": values,
    }
    forged["deterministic_non_timing_sha256"] = wp6.canonical_json_sha256(
        wp6.deterministic_non_timing_payload(forged)
    )
    monkeypatch.setattr(wp6, "build_evidence", lambda _repo_root: copy.deepcopy(forged))

    result = wp6.build_candidate(tmp_path, Path("candidate"))
    assert result["status"] == wp6.CANDIDATE_STATUS
    assert result["anchor_matches"] is False
    assert result["official_package_modified"] is False
    assert not (tmp_path / wp6.EVIDENCE_RELATIVE_PATH).exists()
    assert not (tmp_path / wp6.ATTESTATION_RELATIVE_PATH).exists()
    assert not (tmp_path / wp6.MANIFEST_RELATIVE_PATH).exists()
    with pytest.raises(ValueError, match="reviewed source anchor"):
        wp6.promote_pinned_candidate(tmp_path, Path("candidate"))


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_source",
        "duplicate_source",
        "extra_artifact",
        "forged_source_count",
        "forged_artifact_bytes",
        "path_escape",
        "wrong_record_type",
        "source_hash",
        "artifact_hash",
    ],
)
def test_manifest_rejects_roster_path_count_type_and_hash_tampering(
    tmp_path: Path, mutation: str
) -> None:
    payload: Any = read_json(MANIFEST_PATH)
    if mutation == "missing_source":
        payload["sources"].pop()
    elif mutation == "duplicate_source":
        payload["sources"].append(copy.deepcopy(payload["sources"][0]))
    elif mutation == "extra_artifact":
        payload["artifacts"].append(copy.deepcopy(payload["artifacts"][0]))
    elif mutation == "forged_source_count":
        payload["source_count"] += 1
    elif mutation == "forged_artifact_bytes":
        payload["total_artifact_bytes"] += 1
    elif mutation == "path_escape":
        payload["sources"][0]["path"] = "../VGG16_model.h5"
    elif mutation == "wrong_record_type":
        payload["artifacts"][0] = "not-an-object"
    elif mutation == "source_hash":
        payload["sources"][0]["sha256"] = "0" * 64
    elif mutation == "artifact_hash":
        payload["artifacts"][0]["sha256"] = "0" * 64
    result = verify_payload(tmp_path, payload, f"{mutation}.json")
    assert result["valid"] is False
    assert result["errors"]


def test_manifest_rejects_non_object_root(tmp_path: Path) -> None:
    result = verify_payload(tmp_path, [], "list.json")
    assert result == {"valid": False, "errors": ["manifest root must be an object"]}


def test_human_report_is_derived_from_verified_evidence() -> None:
    evidence = read_json(EVIDENCE_PATH)
    assert REPORT_PATH.read_text(encoding="utf-8") == wp6.render_report(evidence)
    report = REPORT_PATH.read_text(encoding="utf-8")
    assert "D-05 is still unapproved/inactive" in report
    assert "`training_authorized=false`" in report
    assert "No temperature, UNKNOWN threshold or OOD metric was fitted or selected" in report
