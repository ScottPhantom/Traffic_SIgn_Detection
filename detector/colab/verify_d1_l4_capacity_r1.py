#!/usr/bin/env python3
"""Independently replay and verify one completed D1 L4 capacity package."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
import statistics
import sys
import tarfile
from pathlib import Path
from typing import Any

COLAB_ROOT = Path(__file__).resolve().parent
DETECTOR_ROOT = COLAB_ROOT.parent
for import_root in (DETECTOR_ROOT, COLAB_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

import run_d1_l4_capacity_r1 as runner  # noqa: E402

from m1 import checkpoint_store, l4_capacity  # noqa: E402


def _close(left: float, right: float) -> bool:
    return math.isclose(float(left), float(right), rel_tol=1e-9, abs_tol=1e-9)


def _expected_roster() -> list[dict[str, Any]]:
    return [
        {
            "attempt_id": f"b{batch:02d}_w{workers:02d}_r{repeat:02d}",
            "batch": batch,
            "workers": workers,
            "repeat": repeat,
        }
        for batch, workers in l4_capacity.candidate_grid()
        for repeat in range(1, l4_capacity.PROFILE_REPETITIONS + 1)
    ]


def verify_plan(output_dir: Path) -> tuple[dict[str, Any], str]:
    plan_path = output_dir / runner.PLAN_NAME
    plan_file_sha256 = runner.sha256_file(plan_path)
    plan = runner.strict_json(plan_path)
    expected_hash = plan.pop("plan_sha256", None)
    if expected_hash != l4_capacity.canonical_sha256(plan):
        raise RuntimeError("capacity plan canonical hash differs")
    plan["plan_sha256"] = expected_hash
    if plan.get("status") != "FROZEN_BEFORE_EXECUTION":
        raise RuntimeError("capacity plan is not frozen")
    if plan.get("scope") != "TRAIN_VAL_CAPACITY_ONLY":
        raise RuntimeError("capacity plan scope differs")
    if plan.get("sealed_test_accessed") is not False:
        raise RuntimeError("capacity plan indicates sealed-test access")
    if plan.get("roster") != _expected_roster():
        raise RuntimeError("capacity plan roster differs from the fixed 24 attempts")
    profile = plan.get("profile")
    expected_profile = {
        "epochs": l4_capacity.PROFILE_EPOCHS,
        "fraction": l4_capacity.PROFILE_FRACTION,
        "imgsz": l4_capacity.PROFILE_IMGSZ,
        "seed": l4_capacity.PROFILE_SEED,
        "warmup_batches": l4_capacity.WARMUP_BATCHES,
        "repetitions": l4_capacity.PROFILE_REPETITIONS,
        "max_vram_fraction": l4_capacity.MAX_VRAM_FRACTION,
        "max_throughput_cv": l4_capacity.MAX_THROUGHPUT_CV,
        "throughput_tie_fraction": l4_capacity.THROUGHPUT_TIE_FRACTION,
    }
    if profile != expected_profile:
        raise RuntimeError("capacity plan profile differs from the reviewed policy")
    if Path(plan["output_dir"]).absolute() != output_dir:
        raise RuntimeError("capacity plan output directory differs")
    return plan, plan_file_sha256


def _verify_train_args(
    train_args: Any, *, attempt: dict[str, Any], plan: dict[str, Any]
) -> None:
    if not isinstance(train_args, dict):
        raise RuntimeError("capacity telemetry train_args must be an object")
    expected = {
        "data": plan["data_contract"]["data_yaml"],
        "epochs": l4_capacity.PROFILE_EPOCHS,
        "imgsz": l4_capacity.PROFILE_IMGSZ,
        "batch": attempt["batch"],
        "device": "0",
        "seed": l4_capacity.PROFILE_SEED,
        "deterministic": True,
        "workers": attempt["workers"],
        "fraction": l4_capacity.PROFILE_FRACTION,
        "patience": 0,
        "plots": False,
        "val": False,
        "save": False,
        "cache": False,
        "amp": True,
        "verbose": False,
        "pretrained": True,
        "fliplr": 0.0,
    }
    for key, value in expected.items():
        if train_args.get(key) != value:
            raise RuntimeError(f"capacity telemetry train_args differs: {key}")
    if Path(train_args.get("project", "")).name != attempt["attempt_id"]:
        raise RuntimeError("capacity telemetry project directory differs")
    if train_args.get("name") != "ultralytics" or train_args.get("exist_ok") is not False:
        raise RuntimeError("capacity telemetry Ultralytics output policy differs")


def verify_attempt(
    output_dir: Path,
    *,
    attempt: dict[str, Any],
    plan: dict[str, Any],
    plan_file_sha256: str,
) -> tuple[dict[str, Any], str, str]:
    attempt_dir = output_dir / "attempts" / attempt["attempt_id"]
    result_path = attempt_dir / "result.json"
    telemetry_path = attempt_dir / "raw_telemetry.json"
    result = runner.strict_json(result_path)
    expected_result_keys = {"attempt_id", "batch", "workers"} | l4_capacity.REPETITION_KEYS
    if set(result) != expected_result_keys:
        raise RuntimeError(f"capacity result schema differs: {attempt['attempt_id']}")
    for key in ("attempt_id", "batch", "workers", "repeat"):
        if result.get(key) != attempt[key]:
            raise RuntimeError(f"capacity result identity differs: {attempt['attempt_id']}")
    telemetry_sha256 = runner.sha256_file(telemetry_path)
    if result["raw_telemetry_sha256"] != telemetry_sha256:
        raise RuntimeError(f"capacity telemetry hash differs: {attempt['attempt_id']}")
    telemetry = runner.strict_json(telemetry_path)
    expected_telemetry_keys = {
        "schema_version",
        "attempt",
        "plan_sha256",
        "started_at",
        "finished_at",
        "status",
        "error",
        "train_args",
        "steps",
        "gpu_samples",
        "sealed_test_accessed",
    }
    if set(telemetry) != expected_telemetry_keys:
        raise RuntimeError(f"capacity telemetry schema differs: {attempt['attempt_id']}")
    if telemetry["attempt"] != attempt or telemetry["plan_sha256"] != plan_file_sha256:
        raise RuntimeError(f"capacity telemetry plan binding differs: {attempt['attempt_id']}")
    if telemetry["sealed_test_accessed"] is not False:
        raise RuntimeError(
            f"capacity telemetry indicates sealed-test access: {attempt['attempt_id']}"
        )
    if telemetry["status"] != result["status"] or telemetry["error"] != result["error"]:
        raise RuntimeError(f"capacity telemetry terminal state differs: {attempt['attempt_id']}")
    _verify_train_args(telemetry["train_args"], attempt=attempt, plan=plan)

    steps = telemetry["steps"]
    samples = telemetry["gpu_samples"]
    if not isinstance(steps, list) or not isinstance(samples, list) or not samples:
        raise RuntimeError(f"capacity raw telemetry is incomplete: {attempt['attempt_id']}")
    gpu_uuid = plan["environment"]["gpu_uuid"]
    total_vram = plan["environment"]["total_vram_mib"]
    for sample in samples:
        if sample.get("gpu_uuid") != gpu_uuid:
            raise RuntimeError(f"capacity GPU UUID drifted: {attempt['attempt_id']}")
        if not _close(sample.get("memory_total_mib", -1), total_vram):
            raise RuntimeError(f"capacity total VRAM drifted: {attempt['attempt_id']}")
    peak_vram = max(sample["memory_used_mib"] for sample in samples)
    if not _close(result["peak_vram_used_mib"], peak_vram):
        raise RuntimeError(f"capacity peak VRAM does not replay: {attempt['attempt_id']}")
    if not _close(result["total_vram_mib"], total_vram):
        raise RuntimeError(f"capacity total VRAM does not replay: {attempt['attempt_id']}")
    if not _close(result["peak_vram_fraction"], peak_vram / total_vram):
        raise RuntimeError(f"capacity VRAM fraction does not replay: {attempt['attempt_id']}")
    if result["status"] == "SUCCEEDED":
        images = sum(step["images"] for step in steps)
        seconds = sum(step["seconds"] for step in steps)
        replay = {
            "measured_batches": len(steps),
            "measured_images": images,
            "measurement_seconds": seconds,
            "images_per_second": images / seconds,
            "gpu_sample_count": len(samples),
            "median_gpu_utilization_percent": statistics.median(
                sample["utilization_percent"] for sample in samples
            ),
            "p95_gpu_utilization_percent": runner.percentile(
                [sample["utilization_percent"] for sample in samples], 0.95
            ),
            "median_power_watts": statistics.median(
                sample["power_watts"] for sample in samples
            ),
        }
        for key, value in replay.items():
            if not _close(result[key], value):
                raise RuntimeError(
                    f"capacity successful metric does not replay: {attempt['attempt_id']} {key}"
                )
    else:
        for key in (
            "measured_batches",
            "measured_images",
            "measurement_seconds",
            "images_per_second",
            "gpu_sample_count",
            "median_gpu_utilization_percent",
            "p95_gpu_utilization_percent",
            "median_power_watts",
        ):
            if result[key] != 0:
                raise RuntimeError(
                    f"capacity failed metric is not zero: {attempt['attempt_id']} {key}"
                )
    repetition = {
        key: value
        for key, value in result.items()
        if key not in {"attempt_id", "batch", "workers"}
    }
    l4_capacity.validate_repetition(repetition, expected_repeat=attempt["repeat"])
    return repetition, runner.sha256_file(result_path), telemetry_sha256


def verify_database(
    database_path: Path,
    *,
    plan_sha256: str,
    expected_rows: list[tuple[Any, ...]],
) -> None:
    uri = f"file:{database_path}?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        metadata = dict(connection.execute("SELECT key, value FROM metadata ORDER BY key"))
        if metadata != {
            "plan_sha256": plan_sha256,
            "sealed_test_accessed": "false",
        }:
            raise RuntimeError("capacity database metadata differs")
        rows = connection.execute(
            """
            SELECT attempt_id, batch, workers, repetition, status,
                   result_sha256, raw_telemetry_sha256
            FROM attempts ORDER BY rowid
            """
        ).fetchall()
    if rows != expected_rows:
        raise RuntimeError("capacity database attempt ledger differs")


def verify_execution(path: Path, *, plan_sha256: str, report_sha256: str) -> None:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    if len(rows) != 2 or [row.get("status") for row in rows] != ["STARTED", "SUCCEEDED"]:
        raise RuntimeError("capacity execution journal is not a clean success")
    if any(row.get("plan_sha256") != plan_sha256 for row in rows):
        raise RuntimeError("capacity execution journal plan binding differs")
    if rows[-1].get("report_sha256") != report_sha256:
        raise RuntimeError("capacity execution journal report binding differs")
    if any(row.get("sealed_test_accessed") is not False for row in rows):
        raise RuntimeError("capacity execution journal indicates sealed-test access")


def verify_package(output_dir: Path) -> dict[str, Any]:
    output_dir = checkpoint_store.require_safe_directory(output_dir)
    plan, plan_file_sha256 = verify_plan(output_dir)
    repetitions: dict[tuple[int, int], list[dict[str, Any]]] = {
        candidate: [] for candidate in l4_capacity.candidate_grid()
    }
    database_rows = []
    for attempt in plan["roster"]:
        repetition, result_sha256, telemetry_sha256 = verify_attempt(
            output_dir,
            attempt=attempt,
            plan=plan,
            plan_file_sha256=plan_file_sha256,
        )
        repetitions[(attempt["batch"], attempt["workers"])].append(repetition)
        database_rows.append(
            (
                attempt["attempt_id"],
                attempt["batch"],
                attempt["workers"],
                attempt["repeat"],
                repetition["status"],
                result_sha256,
                telemetry_sha256,
            )
        )
    verify_database(
        output_dir / runner.DATABASE_NAME,
        plan_sha256=plan_file_sha256,
        expected_rows=database_rows,
    )
    candidates = [
        l4_capacity.aggregate_candidate(
            batch=batch,
            workers=workers,
            repetitions=repetitions[(batch, workers)],
            run_dir=str(output_dir / "attempts"),
        )
        for batch, workers in l4_capacity.candidate_grid()
    ]
    report_path = output_dir / runner.REPORT_NAME
    report = runner.strict_json(report_path)
    evidence_sha256 = report.pop("evidence_sha256", None)
    if evidence_sha256 != l4_capacity.canonical_sha256(report):
        raise RuntimeError("capacity report evidence hash differs")
    report["evidence_sha256"] = evidence_sha256
    expected_report = l4_capacity.build_report(
        records=candidates,
        environment=plan["environment"],
        model=plan["model"],
        data_contract=plan["data_contract"],
        git_commit=plan["git_commit"],
    )
    if report != expected_report:
        raise RuntimeError("capacity report does not replay from raw attempts")
    report_file_sha256 = runner.sha256_file(report_path)
    proposal = runner.strict_json(output_dir / runner.LOCK_CANDIDATE_NAME)
    if proposal != l4_capacity.build_lock_candidate(
        report,
        report_sha256=report_file_sha256,
    ):
        raise RuntimeError("capacity selection proposal does not replay")
    verify_execution(
        output_dir / runner.EXECUTION_NAME,
        plan_sha256=plan_file_sha256,
        report_sha256=report_file_sha256,
    )
    log_path = output_dir / runner.TEXT_LOG_NAME
    if not log_path.is_file() or log_path.stat().st_size == 0:
        raise RuntimeError("capacity text log is missing or empty")
    verify_manifest_and_archive(output_dir, plan_sha256=plan_file_sha256)
    return {
        "status": "D1_L4_CAPACITY_R1_VERIFIED",
        "attempts": len(plan["roster"]),
        "selection": proposal["selection"],
        "sealed_test_accessed": False,
    }


def verify_manifest_and_archive(output_dir: Path, *, plan_sha256: str) -> None:
    manifest_path = output_dir / runner.MANIFEST_NAME
    archive_path = output_dir / runner.ARCHIVE_NAME
    manifest = runner.strict_json(manifest_path)
    evidence_sha256 = manifest.pop("evidence_sha256", None)
    if evidence_sha256 != l4_capacity.canonical_sha256(manifest):
        raise RuntimeError("capacity evidence manifest hash differs")
    manifest["evidence_sha256"] = evidence_sha256
    if manifest.get("plan_sha256") != plan_sha256:
        raise RuntimeError("capacity evidence manifest plan binding differs")
    if manifest.get("sealed_test_accessed") is not False:
        raise RuntimeError("capacity evidence manifest indicates sealed-test access")
    expected_files = []
    for record in manifest.get("files", []):
        path = output_dir / record["path"]
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"capacity manifest file is unsafe or missing: {path}")
        observed = {
            "path": record["path"],
            "size": path.stat().st_size,
            "sha256": runner.sha256_file(path),
        }
        if observed != record:
            raise RuntimeError(f"capacity manifest file differs: {record['path']}")
        expected_files.append(record["path"])
    actual_files = sorted(
        path.relative_to(output_dir).as_posix()
        for path in output_dir.rglob("*")
        if path.is_file() and path not in {manifest_path, archive_path}
    )
    if expected_files != actual_files:
        raise RuntimeError("capacity evidence manifest file inventory differs")
    with tarfile.open(archive_path, "r:gz") as archive:
        members = archive.getmembers()
        expected_members = [*expected_files, runner.MANIFEST_NAME]
        if [member.name for member in members] != expected_members:
            raise RuntimeError("capacity archive member inventory differs")
        for member in members:
            if not member.isfile() or member.issym() or member.islnk():
                raise RuntimeError(f"capacity archive member is unsafe: {member.name}")
            handle = archive.extractfile(member)
            if handle is None:
                raise RuntimeError(f"capacity archive member is unreadable: {member.name}")
            digest = hashlib.sha256()
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
            source = output_dir / member.name
            if digest.hexdigest() != runner.sha256_file(source):
                raise RuntimeError(f"capacity archive member differs: {member.name}")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--output-dir", type=Path, required=True)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        result = verify_package(args.output_dir.expanduser().absolute())
    except (OSError, RuntimeError, ValueError, sqlite3.DatabaseError, tarfile.TarError) as error:
        print(json.dumps({"status": "FAILED", "error": f"{type(error).__name__}: {error}"}))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
