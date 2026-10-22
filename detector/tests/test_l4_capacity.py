from __future__ import annotations

import statistics
from copy import deepcopy

import pytest

from m1 import l4_capacity


def repetition(
    batch: int,
    workers: int,
    *,
    repeat: int,
    images_per_second: float,
    peak_fraction: float,
    status: str = "SUCCEEDED",
) -> dict:
    measured_images = 1000 if status == "SUCCEEDED" else 0
    measurement_seconds = (
        measured_images / images_per_second if status == "SUCCEEDED" else 0
    )
    return {
        "repeat": repeat,
        "status": status,
        "oom": status == "OOM",
        "error": (
            "CUDA out of memory"
            if status == "OOM"
            else "generic failure"
            if status == "FAILED"
            else None
        ),
        "measured_batches": 20 if status == "SUCCEEDED" else 0,
        "measured_images": measured_images,
        "measurement_seconds": measurement_seconds,
        "images_per_second": images_per_second if status == "SUCCEEDED" else 0,
        "gpu_sample_count": 10 if status == "SUCCEEDED" else 0,
        "median_gpu_utilization_percent": 88 if status == "SUCCEEDED" else 0,
        "p95_gpu_utilization_percent": 96 if status == "SUCCEEDED" else 0,
        "peak_vram_used_mib": 24000 * peak_fraction,
        "total_vram_mib": 24000,
        "peak_vram_fraction": peak_fraction,
        "median_power_watts": 60 if status == "SUCCEEDED" else 0,
        "raw_telemetry_sha256": f"{repeat}" * 64,
        "run_dir": f"profile_b{batch}_w{workers}_r{repeat}",
    }


def candidate(
    batch: int,
    workers: int,
    *,
    images_per_second: float,
    peak_fraction: float,
    status: str = "SUCCEEDED",
) -> dict:
    repetitions = [
        repetition(
            batch,
            workers,
            repeat=repeat,
            images_per_second=images_per_second + (repeat - 2) * 0.1,
            peak_fraction=peak_fraction,
            status=status,
        )
        for repeat in range(1, l4_capacity.PROFILE_REPETITIONS + 1)
    ]
    if status == "SUCCEEDED":
        aggregate = {
            "measured_batches": sum(row["measured_batches"] for row in repetitions),
            "measured_images": sum(row["measured_images"] for row in repetitions),
            "measurement_seconds": sum(row["measurement_seconds"] for row in repetitions),
            "images_per_second": statistics.median(
                row["images_per_second"] for row in repetitions
            ),
            "throughput_cv": statistics.pstdev(
                row["images_per_second"] for row in repetitions
            )
            / statistics.mean(row["images_per_second"] for row in repetitions),
            "gpu_sample_count": sum(row["gpu_sample_count"] for row in repetitions),
            "median_gpu_utilization_percent": statistics.median(
                row["median_gpu_utilization_percent"] for row in repetitions
            ),
            "p95_gpu_utilization_percent": max(
                row["p95_gpu_utilization_percent"] for row in repetitions
            ),
            "peak_vram_used_mib": max(row["peak_vram_used_mib"] for row in repetitions),
            "total_vram_mib": repetitions[0]["total_vram_mib"],
            "peak_vram_fraction": max(row["peak_vram_fraction"] for row in repetitions),
            "median_power_watts": statistics.median(
                row["median_power_watts"] for row in repetitions
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
            "peak_vram_used_mib": max(row["peak_vram_used_mib"] for row in repetitions),
            "total_vram_mib": repetitions[0]["total_vram_mib"],
            "peak_vram_fraction": max(row["peak_vram_fraction"] for row in repetitions),
            "median_power_watts": 0,
        }
    errors = [row["error"] for row in repetitions if row["error"]]
    return {
        "batch": batch,
        "workers": workers,
        "status": status,
        "oom": status == "OOM",
        "error": " | ".join(errors) if errors else None,
        **aggregate,
        "run_dir": f"profile_b{batch}_w{workers}",
        "repetitions": repetitions,
    }


def complete_grid() -> list[dict]:
    throughput = {
        (4, 4): 10.0,
        (4, 8): 10.5,
        (8, 4): 18.0,
        (8, 8): 19.0,
        (12, 4): 20.0,
        (12, 8): 20.2,
        (16, 4): 20.3,
        (16, 8): 20.4,
    }
    peak = {4: 0.28, 8: 0.48, 12: 0.70, 16: 0.88}
    return [
        candidate(
            batch,
            workers,
            images_per_second=throughput[(batch, workers)],
            peak_fraction=peak[batch],
            status="OOM" if batch == 16 else "SUCCEEDED",
        )
        for batch, workers in l4_capacity.candidate_grid()
    ]


def test_candidate_grid_is_fixed_and_ordered() -> None:
    assert l4_capacity.candidate_grid() == (
        (4, 4),
        (4, 8),
        (8, 4),
        (8, 8),
        (12, 4),
        (12, 8),
        (16, 4),
        (16, 8),
    )


def test_selection_prefers_near_best_throughput_with_more_headroom() -> None:
    selected = l4_capacity.select_candidate(complete_grid())
    assert selected["batch"] == 12
    assert selected["workers"] == 4
    assert selected["images_per_second"] == 20.0
    assert selected["headroom_fraction"] == pytest.approx(0.30)


@pytest.mark.parametrize("attack", ("missing", "duplicate", "reordered"))
def test_grid_cannot_hide_or_cherry_pick_candidates(attack: str) -> None:
    records = complete_grid()
    if attack == "missing":
        records.pop()
    elif attack == "duplicate":
        records[-1] = deepcopy(records[-2])
    else:
        records[0], records[1] = records[1], records[0]
    with pytest.raises(RuntimeError, match="grid"):
        l4_capacity.select_candidate(records)


def test_selection_rejects_all_candidates_above_headroom_limit() -> None:
    records = [
        candidate(
            record["batch"],
            record["workers"],
            images_per_second=record["images_per_second"],
            peak_fraction=0.90,
            status=record["status"],
        )
        for record in complete_grid()
    ]
    with pytest.raises(RuntimeError, match="headroom"):
        l4_capacity.select_candidate(records)


def test_selection_requires_batch_four_and_a_larger_batch() -> None:
    records = complete_grid()
    records = [
        record
        if record["batch"] == 4
        else candidate(
            record["batch"],
            record["workers"],
            images_per_second=0,
            peak_fraction=record["peak_vram_fraction"],
            status="OOM",
        )
        for record in records
    ]
    with pytest.raises(RuntimeError, match="larger batch"):
        l4_capacity.select_candidate(records)


def test_report_and_lock_are_explicitly_not_owner_approved() -> None:
    report = l4_capacity.build_report(
        records=complete_grid(),
        environment={
            "runtime_backend": "cuda",
            "gpu_name": "NVIDIA L4",
            "git_dirty_files": 0,
        },
        model={"sha256": "a" * 64},
        data_contract={
            "export_manifest_sha256": "b" * 64,
            "split_stem_sha256": {"test": "c" * 64},
        },
        git_commit="d" * 40,
    )
    assert report["sealed_test_accessed"] is False
    assert report["not_model_quality_evidence"] is True
    lock = l4_capacity.build_lock_candidate(report, report_sha256="e" * 64)
    assert lock["status"] == "PROPOSAL_NOT_OWNER_APPROVED"
    assert lock["sealed_test_accessed"] is False
    assert lock["selection"]["seeds"] == [20261018, 20261019, 20261020]


def test_report_rejects_non_l4_dirty_or_non_cuda_environment() -> None:
    base = {
        "runtime_backend": "cuda",
        "gpu_name": "NVIDIA L4",
        "git_dirty_files": 0,
    }
    for patch in (
        {"runtime_backend": "cpu"},
        {"gpu_name": "Tesla T4"},
        {"git_dirty_files": 1},
    ):
        environment = {**base, **patch}
        with pytest.raises(RuntimeError):
            l4_capacity.build_report(
                records=complete_grid(),
                environment=environment,
                model={"sha256": "a" * 64},
                data_contract={
                    "export_manifest_sha256": "b" * 64,
                    "split_stem_sha256": {"test": "c" * 64},
                },
                git_commit="d" * 40,
            )


def test_tampered_selection_cannot_create_lock() -> None:
    report = l4_capacity.build_report(
        records=complete_grid(),
        environment={
            "runtime_backend": "cuda",
            "gpu_name": "NVIDIA L4",
            "git_dirty_files": 0,
        },
        model={"sha256": "a" * 64},
        data_contract={
            "export_manifest_sha256": "b" * 64,
            "split_stem_sha256": {"test": "c" * 64},
        },
        git_commit="d" * 40,
    )
    report["selection"]["batch"] = 16
    with pytest.raises(RuntimeError, match="does not reproduce"):
        l4_capacity.build_lock_candidate(report, report_sha256="e" * 64)


def test_generic_failure_cannot_be_relabelled_as_oom() -> None:
    record = candidate(8, 4, images_per_second=0, peak_fraction=0.5, status="FAILED")
    record["status"] = "OOM"
    record["oom"] = True
    with pytest.raises(RuntimeError, match="status does not match"):
        l4_capacity.validate_candidate(record)


def test_all_three_repetitions_are_required() -> None:
    record = candidate(8, 4, images_per_second=18, peak_fraction=0.5)
    record["repetitions"].pop()
    with pytest.raises(RuntimeError, match="all fixed repetitions"):
        l4_capacity.validate_candidate(record)
