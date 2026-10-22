#!/usr/bin/env python3
"""Hardened append-only successor for the D1 NVIDIA L4 capacity study."""

from __future__ import annotations

import argparse
import json
import math
import os
import sqlite3
import stat
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

COLAB_ROOT = Path(__file__).resolve().parent
DETECTOR_ROOT = COLAB_ROOT.parent
for import_root in (DETECTOR_ROOT, COLAB_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

import run_d1_l4_capacity_r1 as r1  # noqa: E402

from m1 import checkpoint_store, l4_capacity  # noqa: E402

OOM_MARKERS = (
    "cuda out of memory",
    "cudnn_status_alloc_failed",
    "cublas_status_alloc_failed",
)
STEP_KEYS = {
    "batch_index",
    "images",
    "seconds",
    "compute_seconds",
    "inter_batch_gap_seconds",
    "planned_batch",
    "trainer_batch_size",
}
R1_BUILD_PLAN = r1.build_plan
SOURCE_PATHS = (
    "detector/m1/l4_capacity.py",
    "detector/colab/run_d1_l4_capacity_r1.py",
    "detector/colab/verify_d1_l4_capacity_r1.py",
    "detector/colab/run_d1_l4_capacity_r2.py",
    "detector/colab/verify_d1_l4_capacity_r2.py",
)


def is_cuda_oom(*, exception_type: str, message: str) -> bool:
    if not isinstance(exception_type, str) or not isinstance(message, str):
        return False
    if exception_type == "OutOfMemoryError":
        return True
    normalized = message.casefold()
    return any(marker in normalized for marker in OOM_MARKERS)


def _oom_error(error: BaseException) -> bool:
    return is_cuda_oom(exception_type=type(error).__name__, message=str(error))


class StepTimer:
    """Measure steady-state batch-to-batch time, including loader/iterator wait."""

    def __init__(self, warmup_batches: int, planned_batch: int) -> None:
        self.warmup_batches = warmup_batches
        self.planned_batch = planned_batch
        self._started: float | None = None
        self._previous_end: float | None = None
        self._current_gap = 0.0
        self._current_images = 0
        self._trainer_batch_size = 0
        self.observed_batches = 0
        self.steps: list[dict[str, Any]] = []

    def on_start(self, trainer: Any) -> None:
        started = time.perf_counter()
        self._current_gap = (
            started - self._previous_end if self._previous_end is not None else 0.0
        )
        batch = getattr(trainer, "batch", None)
        if not isinstance(batch, dict) or "img" not in batch:
            raise RuntimeError("Ultralytics trainer did not expose the actual batch images")
        self._current_images = int(batch["img"].shape[0])
        self._trainer_batch_size = int(getattr(trainer, "batch_size", 0))
        if self._current_images <= 0 or self._trainer_batch_size <= 0:
            raise RuntimeError("observed effective batch is invalid")
        if self._trainer_batch_size != self.planned_batch:
            raise RuntimeError(
                "Ultralytics changed the effective batch from the frozen capacity plan"
            )
        if self._current_images > self.planned_batch:
            raise RuntimeError("observed images exceed the frozen capacity batch")
        self._started = started

    def on_end(self, trainer: Any) -> None:
        if self._started is None:
            raise RuntimeError("train batch ended without a matching start")
        ended = time.perf_counter()
        compute_seconds = ended - self._started
        self._started = None
        self._previous_end = ended
        self.observed_batches += 1
        loss = getattr(trainer, "loss", None)
        if loss is not None and not bool(loss.detach().isfinite().all().item()):
            raise RuntimeError("training loss contains NaN or infinity")
        if compute_seconds <= 0 or self._current_gap < 0:
            raise RuntimeError("measured train batch timing is invalid")
        if self.observed_batches > self.warmup_batches:
            self.steps.append(
                {
                    "batch_index": self.observed_batches,
                    "images": self._current_images,
                    "seconds": compute_seconds + self._current_gap,
                    "compute_seconds": compute_seconds,
                    "inter_batch_gap_seconds": self._current_gap,
                    "planned_batch": self.planned_batch,
                    "trainer_batch_size": self._trainer_batch_size,
                }
            )


def validate_effective_batch(
    telemetry: dict[str, Any], *, planned_batch: int
) -> dict[str, Any]:
    steps = telemetry.get("steps")
    if not isinstance(steps, list) or not steps:
        raise RuntimeError("successful capacity attempt has no measured steps")
    full_batches = 0
    for step in steps:
        if not isinstance(step, dict) or set(step) != STEP_KEYS:
            raise RuntimeError("capacity timing step schema differs")
        if step["planned_batch"] != planned_batch:
            raise RuntimeError("capacity timing planned batch differs")
        if step["trainer_batch_size"] != planned_batch:
            raise RuntimeError("capacity timing effective trainer batch differs")
        images = step["images"]
        if type(images) is not int or images <= 0 or images > planned_batch:
            raise RuntimeError("capacity timing actual image count differs")
        if images == planned_batch:
            full_batches += 1
        for key in ("seconds", "compute_seconds", "inter_batch_gap_seconds"):
            value = step[key]
            if type(value) not in (int, float) or not math.isfinite(float(value)):
                raise RuntimeError(f"capacity timing {key} is not finite")
        if step["compute_seconds"] <= 0 or step["inter_batch_gap_seconds"] < 0:
            raise RuntimeError("capacity timing components are invalid")
        if not math.isclose(
            step["seconds"],
            step["compute_seconds"] + step["inter_batch_gap_seconds"],
            rel_tol=1e-9,
            abs_tol=1e-9,
        ):
            raise RuntimeError("capacity timing does not include loader/iterator gap")
    if full_batches == 0:
        raise RuntimeError("capacity attempt observed no full planned batch")
    return {"effective_batch": planned_batch, "full_batch_count": full_batches}


def _safe_database(path: Path) -> os.stat_result:
    parent = checkpoint_store.require_safe_directory(path.parent)
    target = parent / path.name
    metadata = os.lstat(target)
    if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        raise RuntimeError(f"capacity database must be a regular non-symlink file: {target}")
    if metadata.st_nlink != 1:
        raise RuntimeError(f"capacity database must have one hard link: {target}")
    return metadata


def _database_connection(path: Path) -> sqlite3.Connection:
    before = _safe_database(path)
    uri = f"file:{quote(str(path))}?mode=rw"
    connection = sqlite3.connect(uri, uri=True)
    after = _safe_database(path)
    if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
        connection.close()
        raise RuntimeError("capacity database identity changed while opening")
    return connection


def initialize_database(path: Path, plan_sha256: str) -> None:
    parent = checkpoint_store.require_safe_directory(path.parent, create=True)
    target = parent / path.name
    descriptor = os.open(
        target,
        os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600,
    )
    os.close(descriptor)
    try:
        with _database_connection(target) as connection:
            connection.executescript(
                """
                CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE attempts(
                    attempt_id TEXT PRIMARY KEY,
                    batch INTEGER NOT NULL,
                    workers INTEGER NOT NULL,
                    repetition INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    result_sha256 TEXT NOT NULL,
                    raw_telemetry_sha256 TEXT NOT NULL,
                    recorded_at TEXT NOT NULL
                );
                """
            )
            connection.executemany(
                "INSERT INTO metadata(key, value) VALUES (?, ?)",
                (("plan_sha256", plan_sha256), ("sealed_test_accessed", "false")),
            )
    except Exception:
        target.unlink(missing_ok=True)
        raise


def record_attempt(path: Path, attempt: dict[str, Any], result_sha256: str) -> None:
    with _database_connection(path) as connection:
        connection.execute(
            """
            INSERT INTO attempts(
                attempt_id, batch, workers, repetition, status,
                result_sha256, raw_telemetry_sha256, recorded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                attempt["attempt_id"],
                attempt["batch"],
                attempt["workers"],
                attempt["repeat"],
                attempt["status"],
                result_sha256,
                attempt["raw_telemetry_sha256"],
                r1.now(),
            ),
        )


def _candidate_command(
    *, runner: Path, plan_path: Path, plan_sha256: str, attempt: dict[str, Any]
) -> list[str]:
    del runner
    return [
        sys.executable,
        str(Path(__file__).resolve()),
        "_candidate",
        "--plan",
        str(plan_path),
        "--plan-sha256",
        plan_sha256,
        "--attempt-id",
        attempt["attempt_id"],
        "--batch",
        str(attempt["batch"]),
        "--workers",
        str(attempt["workers"]),
        "--repeat",
        str(attempt["repeat"]),
    ]


def build_plan(**kwargs: Any) -> dict[str, Any]:
    plan = R1_BUILD_PLAN(**kwargs)
    plan.pop("plan_sha256")
    repo_root = Path(plan["repo_root"])
    plan["source_sha256"] = {
        relative: r1.sha256_file(repo_root / relative) for relative in SOURCE_PATHS
    }
    plan["plan_sha256"] = l4_capacity.canonical_sha256(plan)
    return plan


def run_candidate(args: argparse.Namespace) -> int:
    original_timer = r1.StepTimer
    r1.StepTimer = lambda warmup: StepTimer(warmup, args.batch)
    try:
        return_code = r1.run_candidate(args)
    finally:
        r1.StepTimer = original_timer
    plan = r1.strict_json(args.plan.expanduser().absolute())
    attempt_dir = Path(plan["output_dir"]) / "attempts" / args.attempt_id
    result = r1.strict_json(attempt_dir / "result.json")
    telemetry = r1.strict_json(attempt_dir / "raw_telemetry.json")
    if result["status"] == "SUCCEEDED":
        try:
            validate_effective_batch(telemetry, planned_batch=args.batch)
        except RuntimeError as error:
            print(json.dumps({"status": "FAILED", "error": str(error)}))
            return 1
    if result["status"] == "OOM" and not is_cuda_oom(
        exception_type=result["error"].split(":", 1)[0],
        message=result["error"],
    ):
        print(json.dumps({"status": "FAILED", "error": "unverified OOM evidence"}))
        return 1
    return return_code


def _install_hardening() -> None:
    r1.StepTimer = StepTimer
    r1._oom_error = _oom_error
    r1.initialize_database = initialize_database
    r1.record_attempt = record_attempt
    r1._candidate_command = _candidate_command
    r1.build_plan = build_plan
    r1.l4_capacity = l4_capacity


def parser() -> argparse.ArgumentParser:
    return r1.parser()


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    _install_hardening()
    try:
        return r1.run_matrix(args) if args.command == "run" else run_candidate(args)
    except (
        OSError,
        RuntimeError,
        ValueError,
        sqlite3.DatabaseError,
        subprocess.CalledProcessError,
    ) as error:
        print(json.dumps({"status": "FAILED", "error": f"{type(error).__name__}: {error}"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
