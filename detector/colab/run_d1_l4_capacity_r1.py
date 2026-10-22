#!/usr/bin/env python3
"""Profile the governed D1 train path on one idle NVIDIA L4 runtime.

This append-only successor is intentionally separate from Pilot R3.  It runs the
fixed factorial capacity plan in isolated subprocesses, records every successful,
OOM, and failed repetition, and emits only a configuration proposal.  It never
evaluates model quality and never exports or reads the sealed test split.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import os
import sqlite3
import statistics
import subprocess
import sys
import tarfile
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DETECTOR_ROOT = Path(__file__).resolve().parents[1]
if str(DETECTOR_ROOT) not in sys.path:
    sys.path.insert(0, str(DETECTOR_ROOT))

from m1 import checkpoint_store, contract, l4_capacity  # noqa: E402

LOGGER_NAME = "D1_L4_CAPACITY_R1"
PLAN_NAME = "capacity_plan.json"
EXECUTION_NAME = "capacity_execution.jsonl"
REPORT_NAME = "capacity_report.json"
LOCK_CANDIDATE_NAME = "capacity_selection_proposal.json"
TEXT_LOG_NAME = "capacity.log"
DATABASE_NAME = "capacity.db"
MANIFEST_NAME = "capacity_evidence_manifest.json"
ARCHIVE_NAME = "capacity_evidence.tar.gz"
GPU_QUERY = (
    "uuid,utilization.gpu,memory.used,memory.total,power.draw,temperature.gpu"
)


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def strict_json(path: Path) -> Any:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON constant is forbidden: {value}")

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key is forbidden: {key}")
            result[key] = value
        return result

    return json.loads(
        path.read_text(encoding="utf-8"),
        parse_constant=reject_constant,
        object_pairs_hook=unique_object,
    )


def write_json_exclusive(path: Path, payload: Any) -> None:
    parent = checkpoint_store.require_safe_directory(path.parent, create=True)
    target = parent / path.name
    if os.path.lexists(target):
        raise RuntimeError(f"refused to overwrite capacity artifact: {target}")
    temporary = parent / f".{path.name}.{os.getpid()}.partial"
    if os.path.lexists(temporary):
        raise RuntimeError(f"capacity partial already exists: {temporary}")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        encoded = (
            json.dumps(
                payload,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        descriptor = -1
        os.replace(temporary, target)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if os.path.lexists(temporary):
            temporary.unlink()


def append_jsonl(path: Path, payload: Any) -> None:
    parent = checkpoint_store.require_safe_directory(path.parent, create=True)
    target = parent / path.name
    if os.path.lexists(target):
        metadata = os.lstat(target)
        if not os.path.isfile(target) or os.path.islink(target):
            raise RuntimeError(f"capacity journal is not a regular file: {target}")
        if metadata.st_nlink != 1:
            raise RuntimeError(f"capacity journal has multiple hard links: {target}")
    descriptor = os.open(
        target,
        os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW,
        0o600,
    )
    try:
        encoded = (
            json.dumps(
                payload,
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
        os.write(descriptor, encoded)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def configure_logging(output_dir: Path) -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    logger.propagate = False
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    for handler in (
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(output_dir / TEXT_LOG_NAME, encoding="utf-8"),
    ):
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def initialize_database(path: Path, plan_sha256: str) -> None:
    if os.path.lexists(path):
        raise RuntimeError(f"refused to overwrite capacity database: {path}")
    with sqlite3.connect(path) as connection:
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
        connection.execute(
            "INSERT INTO metadata(key, value) VALUES (?, ?)",
            ("plan_sha256", plan_sha256),
        )
        connection.execute(
            "INSERT INTO metadata(key, value) VALUES (?, ?)",
            ("sealed_test_accessed", "false"),
        )


def record_attempt(path: Path, attempt: dict[str, Any], result_sha256: str) -> None:
    with sqlite3.connect(path) as connection:
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
                now(),
            ),
        )


def package_evidence(output_dir: Path, *, plan_sha256: str) -> tuple[Path, Path]:
    manifest_path = output_dir / MANIFEST_NAME
    archive_path = output_dir / ARCHIVE_NAME
    if os.path.lexists(manifest_path) or os.path.lexists(archive_path):
        raise RuntimeError("capacity evidence package already exists")
    files = []
    for path in sorted(output_dir.rglob("*")):
        if path in {manifest_path, archive_path} or path.is_dir():
            continue
        if path.is_symlink() or not path.is_file() or path.stat().st_nlink != 1:
            raise RuntimeError(f"capacity evidence contains an unsafe file: {path}")
        files.append(
            {
                "path": path.relative_to(output_dir).as_posix(),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    manifest = {
        "schema_version": 1,
        "status": "EVIDENCE_PACKAGED",
        "plan_sha256": plan_sha256,
        "sealed_test_accessed": False,
        "files": files,
    }
    manifest["evidence_sha256"] = l4_capacity.canonical_sha256(manifest)
    write_json_exclusive(manifest_path, manifest)
    with tarfile.open(archive_path, "x:gz") as archive:
        for record in [*files, {"path": MANIFEST_NAME}]:
            archive.add(output_dir / record["path"], arcname=record["path"], recursive=False)
    return manifest_path, archive_path


def percentile(values: list[float], quantile: float) -> float:
    if not values:
        raise RuntimeError("cannot calculate percentile of empty telemetry")
    ordered = sorted(values)
    index = (len(ordered) - 1) * quantile
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - index) + ordered[upper] * (index - lower)


def parse_gpu_sample(line: str) -> dict[str, Any]:
    fields = [field.strip() for field in line.split(",")]
    if len(fields) != 6:
        raise RuntimeError("nvidia-smi sample field count differs")
    gpu_uuid = fields[0]
    if not gpu_uuid.startswith("GPU-"):
        raise RuntimeError("nvidia-smi GPU UUID is malformed")
    values = []
    for label, field in zip(
        ("utilization", "memory used", "memory total", "power", "temperature"),
        fields[1:],
        strict=True,
    ):
        try:
            value = float(field)
        except ValueError as error:
            raise RuntimeError(f"nvidia-smi {label} is unsupported or malformed") from error
        if not math.isfinite(value) or value < 0:
            raise RuntimeError(f"nvidia-smi {label} is invalid")
        values.append(value)
    utilization, memory_used, memory_total, power, temperature = values
    if utilization > 100 or memory_total <= 0 or memory_used > memory_total:
        raise RuntimeError("nvidia-smi sample is outside physical bounds")
    return {
        "time": now(),
        "gpu_uuid": gpu_uuid,
        "utilization_percent": utilization,
        "memory_used_mib": memory_used,
        "memory_total_mib": memory_total,
        "power_watts": power,
        "temperature_celsius": temperature,
    }


def query_gpu_sample() -> dict[str, Any]:
    output = subprocess.run(
        [
            "nvidia-smi",
            f"--query-gpu={GPU_QUERY}",
            "--format=csv,noheader,nounits",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    lines = [line for line in output.splitlines() if line.strip()]
    if len(lines) != 1:
        raise RuntimeError("capacity successor requires exactly one visible GPU")
    return parse_gpu_sample(lines[0])


def require_idle_gpu() -> None:
    output = subprocess.run(
        [
            "nvidia-smi",
            "--query-compute-apps=pid,process_name",
            "--format=csv,noheader,nounits",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if output:
        raise RuntimeError("L4 capacity study refuses a concurrent GPU compute process")


class NvidiaSampler:
    def __init__(self, interval_seconds: float = 0.5) -> None:
        self.interval_seconds = interval_seconds
        self.samples: list[dict[str, Any]] = []
        self.error: str | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self.samples.append(query_gpu_sample())
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.wait(self.interval_seconds):
            try:
                self.samples.append(query_gpu_sample())
            except Exception as error:  # recorded and made terminal below
                self.error = f"{type(error).__name__}: {error}"
                return

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)


class StepTimer:
    def __init__(self, warmup_batches: int) -> None:
        self.warmup_batches = warmup_batches
        self._started: float | None = None
        self.observed_batches = 0
        self.steps: list[dict[str, Any]] = []

    def on_start(self, _trainer: Any) -> None:
        self._started = time.perf_counter()

    def on_end(self, trainer: Any) -> None:
        if self._started is None:
            raise RuntimeError("train batch ended without a matching start")
        elapsed = time.perf_counter() - self._started
        self._started = None
        self.observed_batches += 1
        batch = getattr(trainer, "batch", None)
        if not isinstance(batch, dict) or "img" not in batch:
            raise RuntimeError("Ultralytics trainer did not expose the actual batch images")
        images = int(batch["img"].shape[0])
        if images <= 0 or elapsed <= 0:
            raise RuntimeError("measured train batch is invalid")
        loss = getattr(trainer, "loss", None)
        if loss is not None:
            finite = bool(loss.detach().isfinite().all().item())
            if not finite:
                raise RuntimeError("training loss contains NaN or infinity")
        if self.observed_batches > self.warmup_batches:
            self.steps.append(
                {
                    "batch_index": self.observed_batches,
                    "images": images,
                    "seconds": elapsed,
                }
            )


def _oom_error(error: BaseException) -> bool:
    message = f"{type(error).__name__}: {error}".lower()
    return type(error).__name__ == "OutOfMemoryError" or "cuda out of memory" in message


def _training_commit(repo_root: Path) -> str:
    root = checkpoint_store.require_safe_directory(repo_root)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if len(head) != 40 or dirty:
        raise RuntimeError("L4 capacity study requires an exact clean Git checkout")
    return head


def build_plan(
    *,
    repo_root: Path,
    output_dir: Path,
    model: dict[str, Any],
    data_contract: dict[str, Any],
    environment: dict[str, Any],
    git_commit: str,
) -> dict[str, Any]:
    roster = []
    for batch, workers in l4_capacity.candidate_grid():
        for repeat in range(1, l4_capacity.PROFILE_REPETITIONS + 1):
            roster.append(
                {
                    "attempt_id": f"b{batch:02d}_w{workers:02d}_r{repeat:02d}",
                    "batch": batch,
                    "workers": workers,
                    "repeat": repeat,
                }
            )
    plan = {
        "schema_version": 1,
        "status": "FROZEN_BEFORE_EXECUTION",
        "scope": "TRAIN_VAL_CAPACITY_ONLY",
        "repo_root": str(repo_root),
        "output_dir": str(output_dir),
        "git_commit": git_commit,
        "model": model,
        "data_contract": data_contract,
        "environment": environment,
        "profile": {
            "epochs": l4_capacity.PROFILE_EPOCHS,
            "fraction": l4_capacity.PROFILE_FRACTION,
            "imgsz": l4_capacity.PROFILE_IMGSZ,
            "seed": l4_capacity.PROFILE_SEED,
            "warmup_batches": l4_capacity.WARMUP_BATCHES,
            "repetitions": l4_capacity.PROFILE_REPETITIONS,
            "max_vram_fraction": l4_capacity.MAX_VRAM_FRACTION,
            "max_throughput_cv": l4_capacity.MAX_THROUGHPUT_CV,
            "throughput_tie_fraction": l4_capacity.THROUGHPUT_TIE_FRACTION,
        },
        "roster": roster,
        "sealed_test_accessed": False,
    }
    plan["plan_sha256"] = l4_capacity.canonical_sha256(plan)
    return plan


def _candidate_command(
    *, runner: Path, plan_path: Path, plan_sha256: str, attempt: dict[str, Any]
) -> list[str]:
    return [
        sys.executable,
        str(runner),
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


def run_candidate(args: argparse.Namespace) -> int:
    plan_path = args.plan.expanduser().absolute()
    if sha256_file(plan_path) != args.plan_sha256:
        raise RuntimeError("capacity plan file hash differs")
    plan = strict_json(plan_path)
    expected_hash = plan.pop("plan_sha256")
    if l4_capacity.canonical_sha256(plan) != expected_hash:
        raise RuntimeError("capacity plan canonical hash differs")
    plan["plan_sha256"] = expected_hash
    expected_attempt = {
        "attempt_id": args.attempt_id,
        "batch": args.batch,
        "workers": args.workers,
        "repeat": args.repeat,
    }
    if expected_attempt not in plan["roster"]:
        raise RuntimeError("capacity attempt is not in the frozen plan")
    repo_root = checkpoint_store.require_safe_directory(Path(plan["repo_root"]))
    if _training_commit(repo_root) != plan["git_commit"]:
        raise RuntimeError("capacity candidate Git commit differs from the frozen plan")
    gpu = query_gpu_sample()
    current_environment = {
        **contract.environment(),
        "gpu_uuid": gpu["gpu_uuid"],
        "total_vram_mib": gpu["memory_total_mib"],
    }
    if current_environment != plan["environment"]:
        raise RuntimeError("capacity candidate environment differs from the frozen plan")
    model_binding = contract.bind_training_model(plan["model"]["path"])
    if model_binding != plan["model"]:
        raise RuntimeError("capacity candidate model binding differs from the frozen plan")
    bound = contract.check_contract()
    if bound != plan["data_contract"]:
        raise RuntimeError("capacity candidate data contract differs from the frozen plan")

    output_dir = checkpoint_store.require_safe_directory(Path(plan["output_dir"]))
    attempt_dir = output_dir / "attempts" / args.attempt_id
    if os.path.lexists(attempt_dir):
        raise RuntimeError("capacity attempt directory already exists")
    checkpoint_store.require_safe_directory(attempt_dir, create=True)
    timer = StepTimer(l4_capacity.WARMUP_BATCHES)
    sampler = NvidiaSampler()
    contract.disable_telemetry()
    from ultralytics import YOLO

    train_args = {
        "data": bound["data_yaml"],
        "epochs": l4_capacity.PROFILE_EPOCHS,
        "imgsz": l4_capacity.PROFILE_IMGSZ,
        "batch": args.batch,
        "device": "0",
        "seed": l4_capacity.PROFILE_SEED,
        "deterministic": True,
        "workers": args.workers,
        "fraction": l4_capacity.PROFILE_FRACTION,
        "patience": 0,
        "plots": False,
        "val": False,
        "save": False,
        "cache": False,
        "amp": True,
        "verbose": False,
        "project": str(attempt_dir),
        "name": "ultralytics",
        "exist_ok": False,
        "pretrained": True,
        **contract.FORBIDDEN_OVERRIDES,
    }
    started_at = now()
    status = "SUCCEEDED"
    error_text = None
    model = YOLO(model_binding["path"])
    model.add_callback("on_train_batch_start", timer.on_start)
    model.add_callback("on_train_batch_end", timer.on_end)
    sampler.start()
    try:
        model.train(**train_args)
    except Exception as error:
        status = "OOM" if _oom_error(error) else "FAILED"
        error_text = f"{type(error).__name__}: {error}"
    finally:
        sampler.stop()
    if sampler.error and status == "SUCCEEDED":
        status = "FAILED"
        error_text = sampler.error

    telemetry = {
        "schema_version": 1,
        "attempt": expected_attempt,
        "plan_sha256": args.plan_sha256,
        "started_at": started_at,
        "finished_at": now(),
        "status": status,
        "error": error_text,
        "train_args": train_args,
        "steps": timer.steps,
        "gpu_samples": sampler.samples,
        "sealed_test_accessed": False,
    }
    telemetry_path = attempt_dir / "raw_telemetry.json"
    write_json_exclusive(telemetry_path, telemetry)
    telemetry_sha256 = sha256_file(telemetry_path)
    samples = sampler.samples
    total_vram = samples[0]["memory_total_mib"] if samples else 1.0
    peak_vram = max((sample["memory_used_mib"] for sample in samples), default=0.0)
    measured_images = sum(step["images"] for step in timer.steps)
    measurement_seconds = sum(step["seconds"] for step in timer.steps)
    successful = status == "SUCCEEDED"
    result = {
        **expected_attempt,
        "status": status,
        "oom": status == "OOM",
        "error": error_text,
        "measured_batches": len(timer.steps) if successful else 0,
        "measured_images": measured_images if successful else 0,
        "measurement_seconds": measurement_seconds if successful else 0,
        "images_per_second": (
            measured_images / measurement_seconds
            if successful and measurement_seconds > 0
            else 0
        ),
        "gpu_sample_count": len(samples) if successful else 0,
        "median_gpu_utilization_percent": (
            statistics.median(sample["utilization_percent"] for sample in samples)
            if successful and samples
            else 0
        ),
        "p95_gpu_utilization_percent": (
            percentile([sample["utilization_percent"] for sample in samples], 0.95)
            if successful and samples
            else 0
        ),
        "peak_vram_used_mib": peak_vram,
        "total_vram_mib": total_vram,
        "peak_vram_fraction": peak_vram / total_vram,
        "median_power_watts": (
            statistics.median(sample["power_watts"] for sample in samples)
            if successful and samples
            else 0
        ),
        "raw_telemetry_sha256": telemetry_sha256,
        "run_dir": str(attempt_dir),
    }
    repetition = {
        key: value
        for key, value in result.items()
        if key not in {"attempt_id", "batch", "workers"}
    }
    l4_capacity.validate_repetition(repetition, expected_repeat=args.repeat)
    result_path = attempt_dir / "result.json"
    write_json_exclusive(result_path, result)
    print(json.dumps({"status": status, "result": str(result_path)}))
    return 1 if status == "FAILED" else 0


def _read_repetition(output_dir: Path, attempt: dict[str, Any]) -> tuple[dict[str, Any], Path]:
    result_path = output_dir / "attempts" / attempt["attempt_id"] / "result.json"
    result = strict_json(result_path)
    for key in ("attempt_id", "batch", "workers", "repeat"):
        if result.get(key) != attempt[key]:
            raise RuntimeError("capacity attempt result identity differs")
    repetition = {
        key: value
        for key, value in result.items()
        if key not in {"attempt_id", "batch", "workers"}
    }
    l4_capacity.validate_repetition(repetition, expected_repeat=attempt["repeat"])
    telemetry_path = Path(repetition["run_dir"]) / "raw_telemetry.json"
    if sha256_file(telemetry_path) != repetition["raw_telemetry_sha256"]:
        raise RuntimeError("capacity raw telemetry hash differs")
    return repetition, result_path


def run_matrix(args: argparse.Namespace) -> int:
    repo_root = checkpoint_store.require_safe_directory(args.repo_root)
    git_commit = _training_commit(repo_root)
    require_idle_gpu()
    output_dir = args.output_dir.expanduser().absolute()
    if os.path.lexists(output_dir):
        raise RuntimeError("capacity output directory must not already exist")
    checkpoint_store.require_safe_directory(output_dir, create=True)
    logger = configure_logging(output_dir)
    model = contract.bind_training_model(str(args.model))
    data_contract = contract.check_contract()
    environment = contract.environment()
    if environment["runtime_backend"] != "cuda" or environment["gpu_name"] != "NVIDIA L4":
        raise RuntimeError("capacity successor requires exactly one NVIDIA L4 CUDA runtime")
    gpu = query_gpu_sample()
    environment = {
        **environment,
        "gpu_uuid": gpu["gpu_uuid"],
        "total_vram_mib": gpu["memory_total_mib"],
    }
    plan = build_plan(
        repo_root=repo_root,
        output_dir=output_dir,
        model=model,
        data_contract=data_contract,
        environment=environment,
        git_commit=git_commit,
    )
    plan_path = output_dir / PLAN_NAME
    write_json_exclusive(plan_path, plan)
    plan_sha256 = sha256_file(plan_path)
    initialize_database(output_dir / DATABASE_NAME, plan_sha256)
    execution_path = output_dir / EXECUTION_NAME
    append_jsonl(
        execution_path,
        {
            "schema_version": 1,
            "status": "STARTED",
            "started_at": now(),
            "plan_sha256": plan_sha256,
            "sealed_test_accessed": False,
        },
    )
    try:
        runner = Path(__file__).resolve()
        for attempt in plan["roster"]:
            command = _candidate_command(
                runner=runner,
                plan_path=plan_path,
                plan_sha256=plan_sha256,
                attempt=attempt,
            )
            logger.info(
                "ATTEMPT start id=%s command=%s",
                attempt["attempt_id"],
                json.dumps(command),
            )
            completed = subprocess.run(
                command,
                cwd=repo_root / "detector",
                capture_output=True,
                text=True,
            )
            logger.info(
                "ATTEMPT stdout id=%s %s",
                attempt["attempt_id"],
                completed.stdout.strip(),
            )
            if completed.stderr.strip():
                logger.info(
                    "ATTEMPT stderr id=%s %s",
                    attempt["attempt_id"],
                    completed.stderr.strip(),
                )
            repetition, result_path = _read_repetition(output_dir, attempt)
            result = strict_json(result_path)
            record_attempt(output_dir / DATABASE_NAME, result, sha256_file(result_path))
            logger.info(
                "ATTEMPT end id=%s status=%s",
                attempt["attempt_id"],
                repetition["status"],
            )
            if completed.returncode or repetition["status"] == "FAILED":
                raise RuntimeError(
                    f"capacity attempt failed generically: {attempt['attempt_id']}"
                )

        candidates = []
        for batch, workers in l4_capacity.candidate_grid():
            repetitions = []
            for attempt in plan["roster"]:
                if attempt["batch"] == batch and attempt["workers"] == workers:
                    repetition, _ = _read_repetition(output_dir, attempt)
                    repetitions.append(repetition)
            candidates.append(
                l4_capacity.aggregate_candidate(
                    batch=batch,
                    workers=workers,
                    repetitions=repetitions,
                    run_dir=str(output_dir / "attempts"),
                )
            )
        report = l4_capacity.build_report(
            records=candidates,
            environment=environment,
            model=model,
            data_contract=data_contract,
            git_commit=git_commit,
        )
        report_path = output_dir / REPORT_NAME
        write_json_exclusive(report_path, report)
        proposal = l4_capacity.build_lock_candidate(
            report,
            report_sha256=sha256_file(report_path),
        )
        write_json_exclusive(output_dir / LOCK_CANDIDATE_NAME, proposal)
        logger.info("CAPACITY completed proposal=%s", json.dumps(proposal["selection"]))
        append_jsonl(
            execution_path,
            {
                "schema_version": 1,
                "status": "SUCCEEDED",
                "finished_at": now(),
                "plan_sha256": plan_sha256,
                "report_sha256": sha256_file(report_path),
                "sealed_test_accessed": False,
            },
        )
        for handler in logger.handlers:
            handler.flush()
        manifest_path, archive_path = package_evidence(
            output_dir,
            plan_sha256=plan_sha256,
        )
        print(
            json.dumps(
                {
                    "status": "CAPACITY_PROFILE_COMPLETED",
                    "report": str(report_path),
                    "proposal": str(output_dir / LOCK_CANDIDATE_NAME),
                    "manifest": str(manifest_path),
                    "archive": str(archive_path),
                    "sealed_test_accessed": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    except Exception as error:
        append_jsonl(
            execution_path,
            {
                "schema_version": 1,
                "status": "FAILED",
                "finished_at": now(),
                "plan_sha256": plan_sha256,
                "error": f"{type(error).__name__}: {error}",
                "sealed_test_accessed": False,
            },
        )
        raise


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--repo-root", type=Path, required=True)
    run.add_argument("--model", type=Path, required=True)
    run.add_argument("--output-dir", type=Path, required=True)
    candidate = commands.add_parser("_candidate")
    candidate.add_argument("--plan", type=Path, required=True)
    candidate.add_argument("--plan-sha256", required=True)
    candidate.add_argument("--attempt-id", required=True)
    candidate.add_argument("--batch", type=int, required=True)
    candidate.add_argument("--workers", type=int, required=True)
    candidate.add_argument("--repeat", type=int, required=True)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return run_matrix(args) if args.command == "run" else run_candidate(args)
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as error:
        print(json.dumps({"status": "FAILED", "error": f"{type(error).__name__}: {error}"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
