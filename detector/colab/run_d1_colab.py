#!/usr/bin/env python3
"""Run the governed D1 YOLO training workflow on a private Colab runtime.

This standard-library launcher persists console/file/SQLite logs, safely restores the train/val
bundle, verifies the governed stem hashes, synchronizes the exact detector lock, trains through
``m1.cli``, and packages the required run artifacts. It never exports or reads the sealed test.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import logging
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PRETRAINED_URL = (
    "https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo11s.pt"
)
PRETRAINED_SHA256 = "85a76fe86dd8afe384648546b56a7a78580c7cb7b404fc595f97969322d502d5"
LOGGER_NAME = "CPV_log_record"
REQUIRED_STEPS = (
    "bundle_verified_and_extracted",
    "train_val_export_regenerated",
    "detector_lock_synchronized",
    "approved_pretrained_weight_verified",
    "m1_cli_check_passed",
    "training_completed",
)
EXECUTION_KEYS = {
    "status",
    "started_at",
    "finished_at",
    "repo_root",
    "bundle",
    "bundle_sha256",
    "seed",
    "epochs",
    "imgsz",
    "batch",
    "device",
    "sealed_test_accessed",
    "steps_completed",
    "error",
    "split_stem_sha256",
    "train_command",
    "run_dir",
    "tag",
}


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


class SQLiteHandler(logging.Handler):
    """SQLite logger compatible with the retained VGG16 notebook's ``logs`` table."""

    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    level TEXT,
                    logger TEXT,
                    message TEXT
                )
                """
            )

    def emit(self, record: logging.LogRecord) -> None:
        try:
            with sqlite3.connect(self.path) as connection:
                connection.execute(
                    "INSERT INTO logs(level, logger, message) VALUES (?, ?, ?)",
                    (record.levelname, record.name, self.format(record)),
                )
        except Exception:
            self.handleError(record)


def configure_logging(log_dir: Path) -> tuple[logging.Logger, Path, Path]:
    log_dir.mkdir(parents=True, exist_ok=True)
    text_path = log_dir / "colab_train.log"
    database_path = log_dir / "DB_logger.db"
    logger = logging.getLogger(LOGGER_NAME)
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    logger.propagate = False
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    for handler in (
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(text_path, encoding="utf-8"),
        SQLiteHandler(database_path),
    ):
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger, text_path, database_path


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def run_command(
    logger: logging.Logger,
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> None:
    logger.info("COMMAND start cwd=%s argv=%s", cwd, json.dumps(command))
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert process.stdout is not None
    for line in process.stdout:
        logger.info("SUBPROCESS %s", line.rstrip())
    return_code = process.wait()
    logger.info("COMMAND end return_code=%d", return_code)
    if return_code:
        raise RuntimeError(f"command failed with exit code {return_code}: {command}")


def colab_subprocess_environment() -> dict[str, str]:
    """Return a deterministic headless environment for detector subprocesses.

    Colab's notebook kernel can export the inline Matplotlib backend. That backend is not
    available in the separately locked detector environment and makes Ultralytics fail while
    checking the dataset before the first epoch.
    """
    environment = os.environ.copy()
    environment.update(
        {
            "WANDB_DISABLED": "true",
            "DO_NOT_TRACK": "1",
            "ULTRALYTICS_HUB": "false",
            "MPLBACKEND": "Agg",
        }
    )
    return environment


def download_approved_weight(logger: logging.Logger, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file():
        actual = sha256_file(destination)
        if actual != PRETRAINED_SHA256:
            raise RuntimeError("existing yolo11s.pt differs from the Owner-approved SHA-256")
        logger.info("Approved pretrained weight already present sha256=%s", actual)
        return
    partial = destination.with_suffix(".pt.partial")
    if partial.exists():
        raise RuntimeError(f"refused to overwrite partial pretrained download: {partial}")
    logger.info("Downloading Owner-approved official pretrained weight url=%s", PRETRAINED_URL)
    try:
        with urllib.request.urlopen(PRETRAINED_URL, timeout=120) as response:  # noqa: S310
            with partial.open("xb") as output:
                shutil.copyfileobj(response, output, length=1024 * 1024)
        actual = sha256_file(partial)
        if actual != PRETRAINED_SHA256:
            raise RuntimeError(f"downloaded yolo11s.pt SHA-256 differs: {actual}")
        os.replace(partial, destination)
    finally:
        partial.unlink(missing_ok=True)
    logger.info("Approved pretrained weight ready sha256=%s", PRETRAINED_SHA256)


def verify_split_bindings(repo_root: Path, archive: Path) -> dict[str, str]:
    sys.path.insert(0, str(repo_root / "scripts"))
    try:
        import build_m1_colab_bundle as bundle_builder
    finally:
        sys.path.pop(0)
    bundle_manifest, _members = bundle_builder.read_archive_manifest(archive)
    export_manifest = json.loads(
        (repo_root / "docs/review/generated/m1_yolo_export_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    bindings = {
        "train": export_manifest["splits"]["train"]["stem_list_sha256"],
        "val": export_manifest["splits"]["val"]["stem_list_sha256"],
    }
    if (
        bundle_manifest["train_stem_list_sha256"] != bindings["train"]
        or bundle_manifest["val_stem_list_sha256"] != bindings["val"]
    ):
        raise RuntimeError(
            "uploaded bundle train/val stem hashes differ from the M1 export manifest"
        )
    return bindings


def load_detector_contract(repo_root: Path) -> Any:
    path = repo_root / "detector/m1/contract.py"
    spec = importlib.util.spec_from_file_location("m1_colab_result_contract", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load detector contract: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def validate_execution_record(
    execution_path: Path,
    run_dir: Path,
    run_contract: dict[str, Any],
) -> dict[str, Any]:
    execution = strict_json(execution_path)
    if not isinstance(execution, dict) or set(execution) != EXECUTION_KEYS:
        raise RuntimeError("Colab execution record schema differs")
    if (
        execution["status"] != "SUCCEEDED"
        or execution["error"] is not None
        or execution["sealed_test_accessed"] is not False
        or not isinstance(execution["started_at"], str)
        or not execution["started_at"]
        or not isinstance(execution["finished_at"], str)
        or not execution["finished_at"]
    ):
        raise RuntimeError("Colab execution record has no valid successful terminal outcome")
    if execution["steps_completed"] != list(REQUIRED_STEPS):
        raise RuntimeError("Colab execution record is missing or reorders a required step")
    if Path(execution["repo_root"]).resolve() != run_dir.parents[2].resolve():
        raise RuntimeError("Colab execution repository binding differs")
    if Path(execution["run_dir"]).resolve() != run_dir.resolve():
        raise RuntimeError("Colab execution run-directory binding differs")
    bundle_sha = execution["bundle_sha256"]
    if (
        not isinstance(bundle_sha, str)
        or len(bundle_sha) != 64
        or any(character not in "0123456789abcdef" for character in bundle_sha)
    ):
        raise RuntimeError("Colab execution bundle SHA-256 is invalid")
    train_args = run_contract["train_args"]
    scalar_bindings = {
        "seed": train_args["seed"],
        "epochs": train_args["epochs"],
        "imgsz": train_args["imgsz"],
        "batch": train_args["batch"],
        "device": train_args["device"],
    }
    if any(execution[key] != value for key, value in scalar_bindings.items()):
        raise RuntimeError("Colab execution parameters differ from run_contract.json")
    split_hashes = run_contract["contract"]["split_stem_sha256"]
    if execution["split_stem_sha256"] != {
        "train": split_hashes["train"],
        "val": split_hashes["val"],
    }:
        raise RuntimeError("Colab execution train/val stem bindings differ")
    tag = execution["tag"]
    if not isinstance(tag, str) or re.fullmatch(r"[A-Za-z0-9_.-]+", tag) is None:
        raise RuntimeError("Colab execution tag is missing or unsafe")
    expected_command = [
        "uv",
        "run",
        "python",
        "-m",
        "m1.cli",
        "train",
        "--seed",
        str(train_args["seed"]),
        "--model",
        run_contract["model"]["path"],
        "--epochs",
        str(train_args["epochs"]),
        "--imgsz",
        str(train_args["imgsz"]),
        "--batch",
        str(train_args["batch"]),
        "--device",
        str(train_args["device"]),
        "--workers",
        str(train_args["workers"]),
        "--fraction",
        str(train_args["fraction"]),
        "--patience",
        str(train_args["patience"]),
        "--tag",
        tag,
    ]
    if execution["train_command"] != expected_command or train_args.get("plots") is not False:
        raise RuntimeError("Colab execution train command differs from run_contract.json")
    return execution


def validate_sqlite_log(database_path: Path, text_log: Path, results_csv: Path) -> None:
    if text_log.stat().st_size == 0 or results_csv.stat().st_size == 0:
        raise RuntimeError("Colab text log and results.csv must be non-empty")
    csv_lines = [line for line in results_csv.read_text(encoding="utf-8").splitlines() if line]
    if len(csv_lines) < 2:
        raise RuntimeError("results.csv contains no completed training epoch")
    try:
        with sqlite3.connect(f"file:{database_path}?mode=ro", uri=True) as connection:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()
            columns = connection.execute("PRAGMA table_info(logs)").fetchall()
            rows = connection.execute(
                "SELECT id, level, logger, message FROM logs ORDER BY id"
            ).fetchall()
    except sqlite3.DatabaseError as error:
        raise RuntimeError("DB_logger.db is not a valid SQLite log database") from error
    if integrity != ("ok",):
        raise RuntimeError("DB_logger.db integrity check failed")
    expected_columns = ["id", "timestamp", "level", "logger", "message"]
    if [row[1] for row in columns] != expected_columns:
        raise RuntimeError("DB_logger.db logs table schema differs")
    if not rows or any(row[1] != "INFO" or row[2] != LOGGER_NAME for row in rows):
        raise RuntimeError("DB_logger.db contains missing or unexpected logger records")
    messages = [row[3] for row in rows]

    def first_index(token: str) -> int:
        try:
            return next(index for index, message in enumerate(messages) if token in message)
        except StopIteration as error:
            raise RuntimeError(f"DB_logger.db is missing required event: {token}") from error

    workflow_start = first_index("D1 Colab workflow started")
    training_start = first_index("Training start")
    training_end = first_index("Training end")
    terminal = first_index("Terminal outcome SUCCEEDED")
    if not workflow_start < training_start < training_end < terminal:
        raise RuntimeError("DB_logger.db required events are not in lifecycle order")
    if not any("SUBPROCESS" in message for message in messages[training_start + 1 : training_end]):
        raise RuntimeError("DB_logger.db contains no persisted training subprocess/epoch output")
    text = text_log.read_text(encoding="utf-8")
    if not all(
        token in text
        for token in ("D1 Colab workflow started", "Training start", "Training end", "SUCCEEDED")
    ):
        raise RuntimeError("colab_train.log is missing required lifecycle events")


def validate_result_sources(
    run_dir: Path,
    execution_path: Path,
    text_log: Path,
    database_log: Path,
) -> tuple[list[Path], dict[str, Any], dict[str, Any]]:
    required = [
        run_dir / "weights/best.pt",
        run_dir / "weights/last.pt",
        run_dir / "results.csv",
        run_dir / "args.yaml",
        run_dir / "run_contract.json",
        execution_path,
        text_log,
        database_log,
    ]
    missing = [str(path) for path in required if not path.is_file() or path.is_symlink()]
    if missing:
        raise RuntimeError(f"required Colab result artifacts are missing or linked: {missing}")
    if any(path.stat().st_size == 0 for path in required):
        raise RuntimeError("required Colab result artifacts must all be non-empty")
    repo_root = run_dir.parents[2].resolve()
    run_contract = strict_json(run_dir / "run_contract.json")
    if not isinstance(run_contract, dict):
        raise RuntimeError("run_contract.json must contain an object")
    execution = validate_execution_record(execution_path, run_dir, run_contract)
    detector_contract = load_detector_contract(repo_root)
    claim = detector_contract.inspect_run_weights(str(run_dir / "weights/best.pt"))
    environment = run_contract["environment"]
    if environment["runtime_backend"] != "cuda" or environment["cuda_available"] is not True:
        raise RuntimeError("Colab result package requires a validated CUDA training environment")
    validate_sqlite_log(database_log, text_log, run_dir / "results.csv")
    return required, execution, claim


def result_arcname(path: Path, run_dir: Path, log_paths: set[Path]) -> str:
    if path in log_paths:
        return (Path("colab_logs") / path.name).as_posix()
    return (Path(run_dir.name) / path.relative_to(run_dir)).as_posix()


def safe_result_member(name: str) -> str:
    path = Path(name)
    if (
        path.is_absolute()
        or name != path.as_posix()
        or "\\" in name
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise RuntimeError(f"unsafe result archive member: {name!r}")
    return name


def verify_result_archive(archive_path: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = strict_json(manifest_path)
    required_keys = {
        "status",
        "run",
        "archive_name",
        "archive_sha256",
        "files",
        "terminal_outcome",
        "sealed_test_accessed",
        "run_attestation_sha256",
    }
    if not isinstance(manifest, dict) or set(manifest) != required_keys:
        raise RuntimeError("D1 Colab result manifest schema differs")
    run = manifest["run"]
    if (
        not isinstance(run, str)
        or re.fullmatch(r"D1_[A-Za-z0-9_.-]+", run) is None
        or Path(run).name != run
    ):
        raise RuntimeError("D1 Colab result run identity is invalid")
    expected_paths = {
        f"{run}/weights/best.pt",
        f"{run}/weights/last.pt",
        f"{run}/results.csv",
        f"{run}/args.yaml",
        f"{run}/run_contract.json",
        "colab_logs/colab_execution.json",
        "colab_logs/colab_train.log",
        "colab_logs/DB_logger.db",
    }
    attestation = manifest["run_attestation_sha256"]
    if (
        manifest["status"] != "D1_COLAB_RESULT_PACKAGE"
        or manifest["terminal_outcome"] != "SUCCEEDED"
        or manifest["sealed_test_accessed"] is not False
        or manifest["archive_name"] != archive_path.name
        or sha256_file(archive_path) != manifest["archive_sha256"]
        or not isinstance(attestation, str)
        or len(attestation) != 64
        or any(character not in "0123456789abcdef" for character in attestation)
    ):
        raise RuntimeError("D1 Colab result manifest identity/outcome differs")
    records = manifest["files"]
    if not isinstance(records, list) or not records:
        raise RuntimeError("D1 Colab result manifest has no files")
    by_path: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict) or set(record) != {"path", "size", "sha256"}:
            raise RuntimeError("D1 Colab result file-record schema differs")
        name = safe_result_member(record["path"])
        if name in by_path:
            raise RuntimeError(f"duplicate D1 Colab result path: {name}")
        if (
            type(record["size"]) is not int
            or record["size"] < 0
            or not isinstance(record["sha256"], str)
            or len(record["sha256"]) != 64
            or any(character not in "0123456789abcdef" for character in record["sha256"])
        ):
            raise RuntimeError(f"invalid D1 Colab result file record: {name}")
        by_path[name] = record
    if set(by_path) != expected_paths:
        raise RuntimeError("D1 Colab result manifest differs from the canonical eight-file roster")
    with tarfile.open(archive_path, mode="r:gz") as archive:
        members: dict[str, tarfile.TarInfo] = {}
        for member in archive.getmembers():
            name = safe_result_member(member.name)
            if name in members or not member.isreg():
                raise RuntimeError(f"duplicate or non-regular result member: {name}")
            members[name] = member
        if set(members) != set(by_path):
            raise RuntimeError("D1 Colab result archive roster differs from manifest")
        for name, record in by_path.items():
            member = members[name]
            extracted = archive.extractfile(member)
            if extracted is None:
                raise RuntimeError(f"cannot read D1 Colab result member: {name}")
            digest = hashlib.sha256(extracted.read()).hexdigest()
            if member.size != record["size"] or digest != record["sha256"]:
                raise RuntimeError(f"D1 Colab result member differs: {name}")
    return manifest


def package_run(
    run_dir: Path,
    execution_path: Path,
    text_log: Path,
    database_log: Path,
    output: Path,
) -> dict[str, Any]:
    required, execution, claim = validate_result_sources(
        run_dir, execution_path, text_log, database_log
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = output.with_name(f"{output.name}.manifest.json")
    partial = output.with_name(f".{output.name}.partial")
    manifest_partial = manifest_path.with_name(f".{manifest_path.name}.partial")
    existing = [
        path
        for path in (output, manifest_path, partial, manifest_partial)
        if path.exists()
    ]
    if existing:
        raise RuntimeError(f"refused to overwrite existing result output path(s): {existing}")
    log_paths = {execution_path, text_log, database_log}
    with tarfile.open(partial, mode="x:gz", compresslevel=1) as archive:
        for path in required:
            archive.add(path, arcname=result_arcname(path, run_dir, log_paths), recursive=False)
    entries = [
        {
            "path": result_arcname(path, run_dir, log_paths),
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in required
    ]
    manifest = {
        "status": "D1_COLAB_RESULT_PACKAGE",
        "run": run_dir.name,
        "archive_name": output.name,
        "archive_sha256": sha256_file(partial),
        "files": entries,
        "terminal_outcome": execution["status"],
        "sealed_test_accessed": execution["sealed_test_accessed"],
        "run_attestation_sha256": claim["run_attestation_sha256"],
    }
    with manifest_partial.open("xb") as handle:
        handle.write(
            (
                json.dumps(
                    manifest,
                    indent=2,
                    sort_keys=True,
                    ensure_ascii=False,
                    allow_nan=False,
                )
                + "\n"
            ).encode("utf-8")
        )
    os.replace(partial, output)
    os.replace(manifest_partial, manifest_path)
    verified = verify_result_archive(output, manifest_path)
    return {**verified, "manifest": str(manifest_path)}


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--repo-root", type=Path, required=True)
    root.add_argument("--bundle", type=Path, required=True)
    root.add_argument("--state-dir", type=Path, required=True)
    root.add_argument("--seed", type=int, default=20261018)
    root.add_argument("--epochs", type=int, default=100)
    root.add_argument("--imgsz", type=int, default=1280)
    root.add_argument("--batch", type=int, default=8)
    root.add_argument("--device", default="0")
    root.add_argument("--workers", type=int, default=4)
    root.add_argument("--fraction", type=float, default=1.0)
    root.add_argument("--patience", type=int, default=30)
    root.add_argument("--tag", default="colab")
    root.add_argument("--download-approved-weight", action="store_true")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if re.fullmatch(r"[A-Za-z0-9_.-]+", args.tag) is None:
        print(
            json.dumps({"status": "FAILED", "error": "--tag is missing or unsafe"}),
            file=sys.stderr,
        )
        return 1
    repo_root = args.repo_root.expanduser().resolve()
    bundle = args.bundle.expanduser().resolve()
    state_dir = args.state_dir.expanduser().resolve()
    state_dir.mkdir(parents=True, exist_ok=True)
    if any(state_dir.iterdir()):
        print(
            json.dumps(
                {"status": "FAILED", "error": f"state directory must be empty: {state_dir}"}
            ),
            file=sys.stderr,
        )
        return 1
    logger, text_log, database_log = configure_logging(state_dir)
    execution_path = state_dir / "colab_execution.json"
    execution: dict[str, Any] = {
        "status": "STARTED",
        "started_at": now(),
        "finished_at": None,
        "repo_root": str(repo_root),
        "bundle": str(bundle),
        "bundle_sha256": sha256_file(bundle) if bundle.is_file() else None,
        "seed": args.seed,
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "device": args.device,
        "tag": args.tag,
        "sealed_test_accessed": False,
        "steps_completed": [],
        "error": None,
    }
    write_json(execution_path, execution)
    logger.info(
        "D1 Colab workflow started seed=%d epochs=%d imgsz=%d batch=%d",
        args.seed,
        args.epochs,
        args.imgsz,
        args.batch,
    )
    try:
        run_command(
            logger,
            [
                sys.executable,
                "scripts/build_m1_colab_bundle.py",
                "extract",
                "--repo-root",
                str(repo_root),
                "--archive",
                str(bundle),
            ],
            cwd=repo_root,
        )
        execution["steps_completed"].append("bundle_verified_and_extracted")
        split_bindings = verify_split_bindings(repo_root, bundle)
        execution["split_stem_sha256"] = split_bindings
        run_command(
            logger,
            [
                sys.executable,
                "scripts/build_m1_yolo_dataset.py",
                "export",
                "--repo-root",
                str(repo_root),
            ],
            cwd=repo_root,
        )
        execution["steps_completed"].append("train_val_export_regenerated")
        detector_root = repo_root / "detector"
        run_command(logger, ["uv", "sync", "--frozen"], cwd=detector_root)
        execution["steps_completed"].append("detector_lock_synchronized")
        model = repo_root / "models/pretrained/yolo11s.pt"
        if args.download_approved_weight:
            download_approved_weight(logger, model)
        elif not model.is_file() or sha256_file(model) != PRETRAINED_SHA256:
            raise RuntimeError(
                "approved pretrained weight is absent; pass --download-approved-weight only "
                "with Owner approval"
            )
        execution["steps_completed"].append("approved_pretrained_weight_verified")
        process_env = colab_subprocess_environment()
        run_command(
            logger,
            ["uv", "run", "python", "-m", "m1.cli", "check"],
            cwd=detector_root,
            env=process_env,
        )
        execution["steps_completed"].append("m1_cli_check_passed")
        before = {path.resolve() for path in (repo_root / "results/experiments").glob("D1_*")}
        train_command = [
            "uv",
            "run",
            "python",
            "-m",
            "m1.cli",
            "train",
            "--seed",
            str(args.seed),
            "--model",
            str(model),
            "--epochs",
            str(args.epochs),
            "--imgsz",
            str(args.imgsz),
            "--batch",
            str(args.batch),
            "--device",
            str(args.device),
            "--workers",
            str(args.workers),
            "--fraction",
            str(args.fraction),
            "--patience",
            str(args.patience),
            "--tag",
            args.tag,
        ]
        execution["train_command"] = train_command
        write_json(execution_path, execution)
        logger.info("Training start")
        run_command(logger, train_command, cwd=detector_root, env=process_env)
        logger.info("Training end")
        after = {path.resolve() for path in (repo_root / "results/experiments").glob("D1_*")}
        new_runs = sorted(after - before)
        if len(new_runs) != 1:
            raise RuntimeError(f"expected exactly one new D1 run directory, found {new_runs}")
        run_dir = new_runs[0]
        execution["steps_completed"].append("training_completed")
        execution["run_dir"] = str(run_dir)
        execution["status"] = "SUCCEEDED"
        execution["finished_at"] = now()
        write_json(execution_path, execution)
        logger.info("Terminal outcome SUCCEEDED; validated result packaging begins")
        logger.info("Packaging required run artifacts run=%s", run_dir.name)
        result_archive = state_dir / f"{run_dir.name}_result.tar.gz"
        result = package_run(
            run_dir, execution_path, text_log, database_log, result_archive
        )
        logger.info(
            "D1 Colab workflow succeeded archive=%s sha256=%s",
            result_archive,
            result["archive_sha256"],
        )
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    except Exception as error:
        execution["status"] = "FAILED"
        execution["finished_at"] = now()
        execution["error"] = f"{type(error).__name__}: {error}"
        write_json(execution_path, execution)
        logger.exception("D1 Colab workflow failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
