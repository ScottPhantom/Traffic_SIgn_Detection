#!/usr/bin/env python3
"""Verify R2 L4 capacity evidence against independent repository anchors."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sqlite3
import stat
import subprocess
import sys
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Any

COLAB_ROOT = Path(__file__).resolve().parent
DETECTOR_ROOT = COLAB_ROOT.parent
for import_root in (DETECTOR_ROOT, COLAB_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

import run_d1_l4_capacity_r1 as r1_runner  # noqa: E402
import run_d1_l4_capacity_r2 as r2_runner  # noqa: E402
import verify_d1_l4_capacity_r1 as r1_verifier  # noqa: E402

from m1 import checkpoint_store, contract  # noqa: E402

TRAIN_ARG_KEYS = {
    "data",
    "epochs",
    "imgsz",
    "batch",
    "device",
    "seed",
    "deterministic",
    "workers",
    "fraction",
    "patience",
    "plots",
    "val",
    "save",
    "cache",
    "amp",
    "verbose",
    "project",
    "name",
    "exist_ok",
    "pretrained",
    "fliplr",
}


def strict_json_line(line: str) -> dict[str, Any]:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON constant is forbidden: {value}")

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key is forbidden: {key}")
            result[key] = value
        return result

    value = json.loads(
        line,
        parse_constant=reject_constant,
        object_pairs_hook=unique_object,
    )
    if not isinstance(value, dict):
        raise RuntimeError("capacity execution row must be an object")
    return value


def parse_timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise RuntimeError(f"{label} timestamp is missing")
    try:
        observed = datetime.fromisoformat(value)
    except ValueError as error:
        raise RuntimeError(f"{label} timestamp is malformed") from error
    if observed.tzinfo is None or observed.utcoffset() is None:
        raise RuntimeError(f"{label} timestamp lacks a UTC offset")
    return observed


def verify_execution(path: Path, *, plan_sha256: str, report_sha256: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    rows = [strict_json_line(line) for line in lines]
    started_keys = {
        "schema_version",
        "status",
        "started_at",
        "plan_sha256",
        "sealed_test_accessed",
    }
    succeeded_keys = {
        "schema_version",
        "status",
        "finished_at",
        "plan_sha256",
        "report_sha256",
        "sealed_test_accessed",
    }
    if len(rows) != 2 or set(rows[0]) != started_keys or set(rows[1]) != succeeded_keys:
        raise RuntimeError("capacity execution journal schema differs")
    if [row["status"] for row in rows] != ["STARTED", "SUCCEEDED"]:
        raise RuntimeError("capacity execution journal is not a clean success")
    if any(row["schema_version"] != 1 for row in rows):
        raise RuntimeError("capacity execution schema version differs")
    if any(row["plan_sha256"] != plan_sha256 for row in rows):
        raise RuntimeError("capacity execution plan binding differs")
    if rows[1]["report_sha256"] != report_sha256:
        raise RuntimeError("capacity execution report binding differs")
    if any(row["sealed_test_accessed"] is not False for row in rows):
        raise RuntimeError("capacity execution indicates sealed-test access")
    started_at = parse_timestamp(rows[0]["started_at"], "execution start")
    finished_at = parse_timestamp(rows[1]["finished_at"], "execution finish")
    if not started_at < finished_at:
        raise RuntimeError("capacity execution chronology differs")


def _require_safe_database(path: Path) -> None:
    checkpoint_store.require_safe_directory(path.parent)
    metadata = os.lstat(path)
    if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        raise RuntimeError("capacity database must be a regular non-symlink file")
    if metadata.st_nlink != 1:
        raise RuntimeError("capacity database must have one hard link")


def verify_independent_anchors(plan: dict[str, Any]) -> None:
    repo_root = checkpoint_store.require_safe_directory(Path(plan["repo_root"]))
    if repo_root != contract.REPO_ROOT.absolute():
        raise RuntimeError("capacity repository root differs from the governed checkout")
    commit = plan.get("git_commit")
    if not isinstance(commit, str) or len(commit) != 40:
        raise RuntimeError("capacity Git commit anchor is malformed")
    subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    source_sha256 = plan.get("source_sha256")
    if not isinstance(source_sha256, dict) or set(source_sha256) != set(r2_runner.SOURCE_PATHS):
        raise RuntimeError("capacity reviewed source roster differs")
    for relative, expected_sha256 in source_sha256.items():
        current_path = repo_root / relative
        if r1_runner.sha256_file(current_path) != expected_sha256:
            raise RuntimeError(f"capacity reviewed source bytes differ: {relative}")
        committed = subprocess.run(
            ["git", "show", f"{commit}:{relative}"],
            cwd=repo_root,
            check=True,
            capture_output=True,
        ).stdout
        if hashlib.sha256(committed).hexdigest() != expected_sha256:
            raise RuntimeError(f"capacity commit source bytes differ: {relative}")
    if contract.bind_training_model(plan["model"]["path"]) != plan["model"]:
        raise RuntimeError("capacity model differs from the approved local artifact")
    if contract.check_contract() != plan["data_contract"]:
        raise RuntimeError("capacity data differs from the governed train/val contract")
    environment = plan.get("environment")
    if not isinstance(environment, dict):
        raise RuntimeError("capacity environment anchor is missing")
    if environment.get("detector_lock_sha256") != contract.DETECTOR_LOCK_SHA256:
        raise RuntimeError("capacity detector lock differs from the approved lock")
    if environment.get("runtime_backend") != "cuda" or environment.get("gpu_name") != "NVIDIA L4":
        raise RuntimeError("capacity environment is not the reviewed NVIDIA L4 CUDA target")
    if environment.get("git_commit") != commit or environment.get("git_dirty_files") != 0:
        raise RuntimeError("capacity environment Git binding differs")
    gpu_uuid = environment.get("gpu_uuid")
    if not isinstance(gpu_uuid, str) or not gpu_uuid.startswith("GPU-"):
        raise RuntimeError("capacity GPU UUID anchor is malformed")
    total_vram = environment.get("total_vram_mib")
    if type(total_vram) not in (int, float) or not math.isfinite(float(total_vram)):
        raise RuntimeError("capacity total VRAM anchor is malformed")
    if total_vram <= 0:
        raise RuntimeError("capacity total VRAM anchor is not positive")


def verify_attempt_hardening(
    output_dir: Path,
    *,
    attempt: dict[str, Any],
    plan: dict[str, Any],
) -> None:
    attempt_dir = output_dir / "attempts" / attempt["attempt_id"]
    result = r1_runner.strict_json(attempt_dir / "result.json")
    telemetry = r1_runner.strict_json(attempt_dir / "raw_telemetry.json")
    if set(telemetry.get("train_args", {})) != TRAIN_ARG_KEYS:
        raise RuntimeError(f"capacity train-argument schema differs: {attempt['attempt_id']}")
    if telemetry["train_args"]["batch"] != attempt["batch"]:
        raise RuntimeError(f"capacity requested batch differs: {attempt['attempt_id']}")
    started_at = parse_timestamp(telemetry.get("started_at"), "attempt start")
    finished_at = parse_timestamp(telemetry.get("finished_at"), "attempt finish")
    if not started_at < finished_at:
        raise RuntimeError(f"capacity attempt chronology differs: {attempt['attempt_id']}")
    if result["status"] == "SUCCEEDED":
        r2_runner.validate_effective_batch(
            telemetry,
            planned_batch=attempt["batch"],
        )
    elif result["status"] == "OOM":
        error = result.get("error")
        if not isinstance(error, str) or ":" not in error:
            raise RuntimeError(f"capacity OOM evidence is malformed: {attempt['attempt_id']}")
        exception_type = error.split(":", 1)[0]
        if not r2_runner.is_cuda_oom(exception_type=exception_type, message=error):
            raise RuntimeError(f"capacity OOM evidence does not replay: {attempt['attempt_id']}")
    elif result["status"] != "FAILED":
        raise RuntimeError(f"capacity attempt status differs: {attempt['attempt_id']}")
    for sample in telemetry.get("gpu_samples", []):
        if sample.get("gpu_uuid") != plan["environment"]["gpu_uuid"]:
            raise RuntimeError(f"capacity GPU UUID drifted: {attempt['attempt_id']}")


def verify_package(output_dir: Path) -> dict[str, Any]:
    output_dir = checkpoint_store.require_safe_directory(output_dir)
    plan, plan_sha256 = r1_verifier.verify_plan(output_dir)
    verify_independent_anchors(plan)
    _require_safe_database(output_dir / r1_runner.DATABASE_NAME)
    for attempt in plan["roster"]:
        verify_attempt_hardening(
            output_dir,
            attempt=attempt,
            plan=plan,
        )
    report_sha256 = r1_runner.sha256_file(output_dir / r1_runner.REPORT_NAME)
    verify_execution(
        output_dir / r1_runner.EXECUTION_NAME,
        plan_sha256=plan_sha256,
        report_sha256=report_sha256,
    )
    result = r1_verifier.verify_package(output_dir)
    result["status"] = "D1_L4_CAPACITY_R2_VERIFIED"
    return result


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--output-dir", type=Path, required=True)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        result = verify_package(args.output_dir.expanduser().absolute())
    except (
        OSError,
        RuntimeError,
        ValueError,
        sqlite3.DatabaseError,
        subprocess.CalledProcessError,
        tarfile.TarError,
    ) as error:
        print(json.dumps({"status": "FAILED", "error": f"{type(error).__name__}: {error}"}))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
