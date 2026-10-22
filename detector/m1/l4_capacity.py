"""Governed selection policy for the D1 NVIDIA L4 capacity successor.

The capacity study is operational evidence only.  It uses the governed train/val
package to choose a compute configuration before the three final seeds; it never
evaluates model quality and must never access the sealed test split.
"""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from typing import Any

SCHEMA_VERSION = 1
CANDIDATE_BATCHES = (4, 8, 12, 16)
CANDIDATE_WORKERS = (4, 8)
PROFILE_EPOCHS = 1
PROFILE_FRACTION = 0.25
PROFILE_IMGSZ = 1280
PROFILE_SEED = 20261018
WARMUP_BATCHES = 10
PROFILE_REPETITIONS = 3
MAX_VRAM_FRACTION = 0.80
MIN_MEASURED_BATCHES = 10
MIN_GPU_SAMPLES = 3
THROUGHPUT_TIE_FRACTION = 0.95
MAX_THROUGHPUT_CV = 0.05

CANDIDATE_KEYS = {
    "batch",
    "workers",
    "status",
    "oom",
    "error",
    "measured_batches",
    "measured_images",
    "measurement_seconds",
    "images_per_second",
    "throughput_cv",
    "gpu_sample_count",
    "median_gpu_utilization_percent",
    "p95_gpu_utilization_percent",
    "peak_vram_used_mib",
    "total_vram_mib",
    "peak_vram_fraction",
    "median_power_watts",
    "run_dir",
    "repetitions",
}

REPETITION_KEYS = {
    "repeat",
    "status",
    "oom",
    "error",
    "measured_batches",
    "measured_images",
    "measurement_seconds",
    "images_per_second",
    "gpu_sample_count",
    "median_gpu_utilization_percent",
    "p95_gpu_utilization_percent",
    "peak_vram_used_mib",
    "total_vram_mib",
    "peak_vram_fraction",
    "median_power_watts",
    "raw_telemetry_sha256",
    "run_dir",
}


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _finite_number(value: Any, label: str, *, minimum: float | None = None) -> float:
    if type(value) not in (int, float) or not math.isfinite(float(value)):
        raise RuntimeError(f"{label} must be a finite number")
    observed = float(value)
    if minimum is not None and observed < minimum:
        raise RuntimeError(f"{label} must be at least {minimum}")
    return observed


def _positive_int(value: Any, label: str) -> int:
    if type(value) is not int or value <= 0:
        raise RuntimeError(f"{label} must be a positive integer")
    return value


def candidate_grid() -> tuple[tuple[int, int], ...]:
    return tuple(
        (batch, workers)
        for batch in CANDIDATE_BATCHES
        for workers in CANDIDATE_WORKERS
    )


def validate_repetition(record: Any, *, expected_repeat: int) -> dict[str, Any]:
    if not isinstance(record, dict) or set(record) != REPETITION_KEYS:
        raise RuntimeError("capacity repetition schema differs")
    if record["repeat"] != expected_repeat:
        raise RuntimeError("capacity repetition order differs")
    if record["status"] not in {"SUCCEEDED", "OOM", "FAILED"}:
        raise RuntimeError("capacity repetition terminal status differs")
    if type(record["oom"]) is not bool:
        raise RuntimeError("capacity repetition oom flag must be boolean")
    if record["status"] == "OOM":
        if record["oom"] is not True:
            raise RuntimeError("OOM repetition does not set oom=true")
        if not isinstance(record["error"], str) or not record["error"].strip():
            raise RuntimeError("OOM repetition lacks an error")
    elif record["status"] == "FAILED":
        if record["oom"] is not False:
            raise RuntimeError("generic failure cannot be relabelled as OOM")
        if not isinstance(record["error"], str) or not record["error"].strip():
            raise RuntimeError("failed repetition lacks an error")
    else:
        if record["oom"] is not False or record["error"] is not None:
            raise RuntimeError("successful repetition records an error")
    if not isinstance(record["run_dir"], str) or not record["run_dir"].strip():
        raise RuntimeError("capacity repetition run_dir is missing")
    if (
        not isinstance(record["raw_telemetry_sha256"], str)
        or len(record["raw_telemetry_sha256"]) != 64
    ):
        raise RuntimeError("capacity repetition telemetry hash is malformed")

    numeric = {
        "measured_batches": _finite_number(
            record["measured_batches"], "measured_batches", minimum=0
        ),
        "measured_images": _finite_number(
            record["measured_images"], "measured_images", minimum=0
        ),
        "measurement_seconds": _finite_number(
            record["measurement_seconds"], "measurement_seconds", minimum=0
        ),
        "images_per_second": _finite_number(
            record["images_per_second"], "images_per_second", minimum=0
        ),
        "gpu_sample_count": _finite_number(
            record["gpu_sample_count"], "gpu_sample_count", minimum=0
        ),
        "median_gpu_utilization_percent": _finite_number(
            record["median_gpu_utilization_percent"],
            "median_gpu_utilization_percent",
            minimum=0,
        ),
        "p95_gpu_utilization_percent": _finite_number(
            record["p95_gpu_utilization_percent"],
            "p95_gpu_utilization_percent",
            minimum=0,
        ),
        "peak_vram_used_mib": _finite_number(
            record["peak_vram_used_mib"], "peak_vram_used_mib", minimum=0
        ),
        "total_vram_mib": _finite_number(
            record["total_vram_mib"], "total_vram_mib", minimum=1
        ),
        "peak_vram_fraction": _finite_number(
            record["peak_vram_fraction"], "peak_vram_fraction", minimum=0
        ),
        "median_power_watts": _finite_number(
            record["median_power_watts"], "median_power_watts", minimum=0
        ),
    }
    if numeric["median_gpu_utilization_percent"] > 100:
        raise RuntimeError("median GPU utilization exceeds 100 percent")
    if numeric["p95_gpu_utilization_percent"] > 100:
        raise RuntimeError("p95 GPU utilization exceeds 100 percent")
    if numeric["peak_vram_fraction"] > 1:
        raise RuntimeError("peak VRAM fraction exceeds 1")
    expected_fraction = numeric["peak_vram_used_mib"] / numeric["total_vram_mib"]
    if abs(expected_fraction - numeric["peak_vram_fraction"]) > 1e-9:
        raise RuntimeError("peak VRAM fraction does not match used/total memory")
    if record["status"] == "SUCCEEDED":
        if numeric["measured_batches"] < MIN_MEASURED_BATCHES:
            raise RuntimeError("successful candidate has too few measured batches")
        if numeric["measured_images"] <= 0 or numeric["measurement_seconds"] <= 0:
            raise RuntimeError("successful candidate lacks a positive measurement window")
        expected_throughput = numeric["measured_images"] / numeric["measurement_seconds"]
        if not math.isclose(
            expected_throughput,
            numeric["images_per_second"],
            rel_tol=1e-9,
            abs_tol=1e-9,
        ):
            raise RuntimeError("candidate throughput does not match images/time")
        if numeric["gpu_sample_count"] < MIN_GPU_SAMPLES:
            raise RuntimeError("successful candidate has too few GPU samples")
    return record


def validate_candidate(record: Any) -> dict[str, Any]:
    if not isinstance(record, dict) or set(record) != CANDIDATE_KEYS:
        raise RuntimeError("capacity candidate schema differs")
    batch = _positive_int(record["batch"], "candidate batch")
    workers = _positive_int(record["workers"], "candidate workers")
    if batch not in CANDIDATE_BATCHES or workers not in CANDIDATE_WORKERS:
        raise RuntimeError("capacity candidate is outside the reviewed grid")
    repetitions = record["repetitions"]
    if not isinstance(repetitions, list) or len(repetitions) != PROFILE_REPETITIONS:
        raise RuntimeError("capacity candidate must preserve all fixed repetitions")
    repetitions = [
        validate_repetition(repetition, expected_repeat=index)
        for index, repetition in enumerate(repetitions, start=1)
    ]
    statuses = [repetition["status"] for repetition in repetitions]
    base_status = (
        "FAILED"
        if "FAILED" in statuses
        else "OOM"
        if "OOM" in statuses
        else "SUCCEEDED"
    )
    successful = [row for row in repetitions if row["status"] == "SUCCEEDED"]
    throughput_cv = (
        statistics.pstdev(row["images_per_second"] for row in successful)
        / statistics.mean(row["images_per_second"] for row in successful)
        if base_status == "SUCCEEDED"
        else 0.0
    )
    expected_status = (
        "UNSTABLE"
        if base_status == "SUCCEEDED" and throughput_cv > MAX_THROUGHPUT_CV
        else base_status
    )
    if record["status"] != expected_status:
        raise RuntimeError("capacity candidate status does not match repetitions")
    if record["oom"] is not (expected_status == "OOM"):
        raise RuntimeError("capacity candidate OOM flag does not match repetitions")
    errors = [repetition["error"] for repetition in repetitions if repetition["error"]]
    expected_error = (
        "throughput_cv_exceeds_0.05"
        if expected_status == "UNSTABLE"
        else " | ".join(errors)
        if errors
        else None
    )
    if record["error"] != expected_error:
        raise RuntimeError("capacity candidate error does not match repetitions")
    if not isinstance(record["run_dir"], str) or not record["run_dir"].strip():
        raise RuntimeError("capacity candidate run_dir is missing")

    if base_status == "SUCCEEDED":
        aggregate = {
            "measured_batches": sum(row["measured_batches"] for row in successful),
            "measured_images": sum(row["measured_images"] for row in successful),
            "measurement_seconds": sum(row["measurement_seconds"] for row in successful),
            "images_per_second": statistics.median(
                row["images_per_second"] for row in successful
            ),
            "throughput_cv": throughput_cv,
            "gpu_sample_count": sum(row["gpu_sample_count"] for row in successful),
            "median_gpu_utilization_percent": statistics.median(
                row["median_gpu_utilization_percent"] for row in successful
            ),
            "p95_gpu_utilization_percent": max(
                row["p95_gpu_utilization_percent"] for row in successful
            ),
            "peak_vram_used_mib": max(row["peak_vram_used_mib"] for row in successful),
            "total_vram_mib": successful[0]["total_vram_mib"],
            "peak_vram_fraction": max(row["peak_vram_fraction"] for row in successful),
            "median_power_watts": statistics.median(
                row["median_power_watts"] for row in successful
            ),
        }
        if any(row["total_vram_mib"] != aggregate["total_vram_mib"] for row in successful):
            raise RuntimeError("capacity repetitions report different total VRAM")
    else:
        aggregate = {
            "measured_batches": 0,
            "measured_images": 0,
            "measurement_seconds": 0,
            "images_per_second": 0,
            "throughput_cv": 0,
            "gpu_sample_count": 0,
            "median_gpu_utilization_percent": 0,
            "p95_gpu_utilization_percent": 0,
            "peak_vram_used_mib": max(row["peak_vram_used_mib"] for row in repetitions),
            "total_vram_mib": repetitions[0]["total_vram_mib"],
            "peak_vram_fraction": max(row["peak_vram_fraction"] for row in repetitions),
            "median_power_watts": 0,
        }
    for key, expected in aggregate.items():
        observed = record[key]
        if type(expected) in (int, float) and type(observed) in (int, float):
            if not math.isclose(float(observed), float(expected), rel_tol=1e-9, abs_tol=1e-9):
                raise RuntimeError(f"capacity candidate aggregate differs: {key}")
        elif observed != expected:
            raise RuntimeError(f"capacity candidate aggregate differs: {key}")
    return record


def aggregate_candidate(
    *, batch: int, workers: int, repetitions: list[dict[str, Any]], run_dir: str
) -> dict[str, Any]:
    if len(repetitions) != PROFILE_REPETITIONS:
        raise RuntimeError("capacity candidate must preserve all fixed repetitions")
    validated = [
        validate_repetition(repetition, expected_repeat=index)
        for index, repetition in enumerate(repetitions, start=1)
    ]
    statuses = [row["status"] for row in validated]
    base_status = (
        "FAILED" if "FAILED" in statuses else "OOM" if "OOM" in statuses else "SUCCEEDED"
    )
    successful = [row for row in validated if row["status"] == "SUCCEEDED"]
    throughput_cv = (
        statistics.pstdev(row["images_per_second"] for row in successful)
        / statistics.mean(row["images_per_second"] for row in successful)
        if base_status == "SUCCEEDED"
        else 0.0
    )
    status = (
        "UNSTABLE"
        if base_status == "SUCCEEDED" and throughput_cv > MAX_THROUGHPUT_CV
        else base_status
    )
    errors = [row["error"] for row in validated if row["error"]]
    error = (
        "throughput_cv_exceeds_0.05"
        if status == "UNSTABLE"
        else " | ".join(errors)
        if errors
        else None
    )
    if base_status == "SUCCEEDED":
        aggregate = {
            "measured_batches": sum(row["measured_batches"] for row in successful),
            "measured_images": sum(row["measured_images"] for row in successful),
            "measurement_seconds": sum(row["measurement_seconds"] for row in successful),
            "images_per_second": statistics.median(
                row["images_per_second"] for row in successful
            ),
            "throughput_cv": throughput_cv,
            "gpu_sample_count": sum(row["gpu_sample_count"] for row in successful),
            "median_gpu_utilization_percent": statistics.median(
                row["median_gpu_utilization_percent"] for row in successful
            ),
            "p95_gpu_utilization_percent": max(
                row["p95_gpu_utilization_percent"] for row in successful
            ),
            "peak_vram_used_mib": max(row["peak_vram_used_mib"] for row in successful),
            "total_vram_mib": successful[0]["total_vram_mib"],
            "peak_vram_fraction": max(row["peak_vram_fraction"] for row in successful),
            "median_power_watts": statistics.median(
                row["median_power_watts"] for row in successful
            ),
        }
    else:
        aggregate = {
            "measured_batches": 0,
            "measured_images": 0,
            "measurement_seconds": 0,
            "images_per_second": 0,
            "throughput_cv": 0,
            "gpu_sample_count": 0,
            "median_gpu_utilization_percent": 0,
            "p95_gpu_utilization_percent": 0,
            "peak_vram_used_mib": max(row["peak_vram_used_mib"] for row in validated),
            "total_vram_mib": validated[0]["total_vram_mib"],
            "peak_vram_fraction": max(row["peak_vram_fraction"] for row in validated),
            "median_power_watts": 0,
        }
    record = {
        "batch": batch,
        "workers": workers,
        "status": status,
        "oom": status == "OOM",
        "error": error,
        **aggregate,
        "run_dir": run_dir,
        "repetitions": validated,
    }
    return validate_candidate(record)


def validate_complete_grid(records: Any) -> list[dict[str, Any]]:
    if not isinstance(records, list):
        raise RuntimeError("capacity candidates must be a list")
    validated = [validate_candidate(record) for record in records]
    observed = [(record["batch"], record["workers"]) for record in validated]
    expected = list(candidate_grid())
    if observed != expected:
        raise RuntimeError("capacity candidate grid is incomplete, duplicated, or reordered")
    return validated


def select_candidate(records: Any) -> dict[str, Any]:
    validated = validate_complete_grid(records)
    eligible = [
        record
        for record in validated
        if record["status"] == "SUCCEEDED"
        and record["peak_vram_fraction"] <= MAX_VRAM_FRACTION
    ]
    if not eligible:
        raise RuntimeError("no successful L4 candidate preserves the required VRAM headroom")
    successful_batches = {record["batch"] for record in eligible}
    if 4 not in successful_batches or len(successful_batches) < 2:
        raise RuntimeError("capacity evidence needs batch 4 and at least one larger batch")
    best_throughput = max(record["images_per_second"] for record in eligible)
    near_best = [
        record
        for record in eligible
        if record["images_per_second"] >= best_throughput * THROUGHPUT_TIE_FRACTION
    ]
    selected = min(
        near_best,
        key=lambda record: (
            record["batch"],
            record["workers"],
            record["peak_vram_fraction"],
        ),
    )
    return {
        "batch": selected["batch"],
        "workers": selected["workers"],
        "images_per_second": selected["images_per_second"],
        "median_gpu_utilization_percent": selected["median_gpu_utilization_percent"],
        "p95_gpu_utilization_percent": selected["p95_gpu_utilization_percent"],
        "peak_vram_fraction": selected["peak_vram_fraction"],
        "headroom_fraction": 1.0 - selected["peak_vram_fraction"],
        "selection_policy": (
            "within_95_percent_of_best_median_throughput_then_batch_then_workers_then_vram"
        ),
    }


def build_report(
    *,
    records: Any,
    environment: dict[str, Any],
    model: dict[str, Any],
    data_contract: dict[str, Any],
    git_commit: str,
) -> dict[str, Any]:
    if environment.get("runtime_backend") != "cuda":
        raise RuntimeError("L4 capacity study requires CUDA")
    if environment.get("gpu_name") != "NVIDIA L4":
        raise RuntimeError("L4 capacity study requires exactly NVIDIA L4")
    if environment.get("git_dirty_files") != 0:
        raise RuntimeError("L4 capacity study requires a clean training checkout")
    if not isinstance(git_commit, str) or len(git_commit) != 40:
        raise RuntimeError("capacity study Git commit is malformed")
    validated = validate_complete_grid(records)
    selection = select_candidate(validated)
    report = {
        "schema_version": SCHEMA_VERSION,
        "status": "CAPACITY_PROFILE_COMPLETED",
        "scope": "TRAIN_VAL_CAPACITY_ONLY",
        "not_model_quality_evidence": True,
        "sealed_test_accessed": False,
        "profile": {
            "epochs": PROFILE_EPOCHS,
            "fraction": PROFILE_FRACTION,
            "imgsz": PROFILE_IMGSZ,
            "seed": PROFILE_SEED,
            "warmup_batches": WARMUP_BATCHES,
            "repetitions": PROFILE_REPETITIONS,
            "candidate_batches": list(CANDIDATE_BATCHES),
            "candidate_workers": list(CANDIDATE_WORKERS),
            "max_vram_fraction": MAX_VRAM_FRACTION,
            "max_throughput_cv": MAX_THROUGHPUT_CV,
        },
        "git_commit": git_commit,
        "environment": environment,
        "model": model,
        "data_contract": data_contract,
        "candidates": validated,
        "selection": selection,
    }
    report["evidence_sha256"] = canonical_sha256(report)
    return report


def build_lock_candidate(report: Any, *, report_sha256: str) -> dict[str, Any]:
    if not isinstance(report, dict) or report.get("status") != "CAPACITY_PROFILE_COMPLETED":
        raise RuntimeError("capacity report is not complete")
    if report.get("sealed_test_accessed") is not False:
        raise RuntimeError("capacity report indicates sealed-test access")
    if not isinstance(report_sha256, str) or len(report_sha256) != 64:
        raise RuntimeError("capacity report file hash is malformed")
    selection = report.get("selection")
    if selection != select_candidate(report.get("candidates")):
        raise RuntimeError("capacity report selection does not reproduce")
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "PROPOSAL_NOT_OWNER_APPROVED",
        "scope": "D1_FINAL_TRAIN_CONFIGURATION",
        "source_report_sha256": report_sha256,
        "source_evidence_sha256": report["evidence_sha256"],
        "git_commit": report["git_commit"],
        "model_sha256": report["model"]["sha256"],
        "export_manifest_sha256": report["data_contract"]["export_manifest_sha256"],
        "test_seal_sha256": report["data_contract"]["split_stem_sha256"]["test"],
        "selection": {
            "batch": selection["batch"],
            "workers": selection["workers"],
            "imgsz": PROFILE_IMGSZ,
            "epochs": 100,
            "fraction": 1.0,
            "patience": 0,
            "seeds": [20261018, 20261019, 20261020],
            "deterministic": True,
            "pretrained": True,
            "fliplr": 0.0,
        },
        "sealed_test_accessed": False,
    }
