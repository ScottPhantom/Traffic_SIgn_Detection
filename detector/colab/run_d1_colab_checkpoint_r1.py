#!/usr/bin/env python3
"""Successor D1 Colab workflow with Drive checkpointing and contract-bound resume."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import logging
import os
import re
import sys
import tarfile
from pathlib import Path
from typing import Any


def _load_base() -> Any:
    path = Path(__file__).with_name("run_d1_colab.py")
    spec = importlib.util.spec_from_file_location("d1_colab_checkpoint_r1_base", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load pinned base runner: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


base = _load_base()
RECOVERY_STEPS = (
    "bundle_verified_and_extracted",
    "train_val_export_regenerated",
    "detector_lock_synchronized",
    "approved_pretrained_weight_verified",
    "m1_cli_check_passed",
    "training_completed",
    "checkpoint_verified",
)


def require_unlinked_path(path: Path, *, directory: bool) -> Path:
    lexical = path.expanduser().absolute()
    current = lexical
    while True:
        if current.is_symlink():
            raise RuntimeError(f"path contains a symlink: {current}")
        if current == current.parent:
            break
        current = current.parent
    if directory and lexical.exists() and not lexical.is_dir():
        raise RuntimeError(f"path is not a directory: {lexical}")
    if not directory and (not lexical.is_file() or lexical.is_symlink()):
        raise RuntimeError(f"path is not a regular file: {lexical}")
    return lexical


def require_writable_child(root: Path, name: str) -> Path:
    if Path(name).name != name or name in {"", ".", ".."}:
        raise RuntimeError(f"unsafe writable child name: {name!r}")
    path = root / name
    if path.is_symlink():
        raise RuntimeError(f"writable state child is a symlink: {path}")
    if path.exists() and not path.is_file():
        raise RuntimeError(f"writable state child is not a regular file: {path}")
    return path


def configure_safe_logging(log_dir: Path) -> tuple[logging.Logger, Path, Path]:
    text_path = require_writable_child(log_dir, "colab_train.log")
    database_path = require_writable_child(log_dir, "DB_logger.db")
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    text_fd = os.open(text_path, os.O_APPEND | os.O_CREAT | os.O_WRONLY | nofollow, 0o600)
    database_fd = os.open(database_path, os.O_APPEND | os.O_CREAT | os.O_RDWR | nofollow, 0o600)
    os.close(database_fd)
    logger = logging.getLogger(base.LOGGER_NAME)
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    logger.propagate = False
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    stream = os.fdopen(text_fd, "a", encoding="utf-8")
    handlers = (
        logging.StreamHandler(sys.stdout),
        logging.StreamHandler(stream),
        base.SQLiteHandler(database_path),
    )
    for handler in handlers:
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger, text_path, database_path


def load_bundle_builder(repo_root: Path) -> Any:
    path = repo_root / "scripts/build_m1_colab_bundle.py"
    spec = importlib.util.spec_from_file_location("d1_checkpoint_bundle_builder", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load bundle builder: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def extract_historical_bundle(repo_root: Path, archive_path: Path) -> dict[str, Any]:
    """Verify an immutable data bundle while allowing a reviewed successor code commit."""
    builder = load_bundle_builder(repo_root)
    manifest, members = builder.read_archive_manifest(archive_path)
    expected, metadata = builder.expected_records(repo_root)
    for key, value in metadata.items():
        if key != "repo_git_commit" and manifest[key] != value:
            raise RuntimeError(f"successor bundle binding differs: {key}")
    expected_by_path = {record["path"]: record for record in expected}
    manifest_by_path = {record["path"]: record for record in manifest["files"]}
    if set(expected_by_path) != set(manifest_by_path):
        raise RuntimeError("successor bundle roster differs from the governed train/val roster")
    if set(members) != set(expected_by_path) | {builder.MANIFEST_MEMBER}:
        raise RuntimeError("successor bundle archive member roster differs")
    with tarfile.open(archive_path, mode="r:gz") as archive:
        for name, expected_record in expected_by_path.items():
            record = manifest_by_path[name]
            record_keys = ("sha256", "source_split", "kind")
            if any(record[key] != expected_record[key] for key in record_keys):
                raise RuntimeError(f"successor bundle record differs: {name}")
            member = members[name]
            handle = archive.extractfile(member)
            if handle is None:
                raise RuntimeError(f"cannot read successor bundle member: {name}")
            digest = hashlib.sha256()
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
            if member.size != record["size"] or digest.hexdigest() != record["sha256"]:
                raise RuntimeError(f"successor bundle member differs: {name}")
            destination = builder._safe_destination(repo_root, name)
            if destination.is_symlink():
                raise RuntimeError(f"successor bundle destination is linked: {destination}")
            if destination.exists():
                destination_differs = (
                    not destination.is_file()
                    or builder.sha256_file(destination) != record["sha256"]
                )
                if destination_differs:
                    raise RuntimeError(f"refused to overwrite successor bundle destination: {name}")
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            handle = archive.extractfile(member)
            if handle is None:
                raise RuntimeError(f"cannot extract successor bundle member: {name}")
            with destination.open("xb") as output:
                while chunk := handle.read(1024 * 1024):
                    output.write(chunk)
            if builder.sha256_file(destination) != record["sha256"]:
                raise RuntimeError(f"extracted successor bundle member differs: {name}")
    return {
        "status": "EXTRACTED_FOR_SUCCESSOR",
        "source_repo_git_commit": manifest["repo_git_commit"],
        "code_repo_git_commit": metadata["repo_git_commit"],
        "file_count": manifest["file_count"],
        "test_included": False,
    }


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    guarded = require_writable_child(path.parent, path.name)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(
        guarded, os.O_APPEND | os.O_CREAT | os.O_WRONLY | nofollow, 0o600
    )
    with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--repo-root", type=Path, required=True)
    root.add_argument("--bundle", type=Path, required=True)
    root.add_argument("--state-dir", type=Path, required=True)
    root.add_argument("--mode", choices=("fresh", "resume"), required=True)
    root.add_argument("--seed", type=int, default=20261018)
    root.add_argument("--epochs", type=int, default=100)
    root.add_argument("--imgsz", type=int, default=1280)
    root.add_argument("--batch", type=int, default=8)
    root.add_argument("--device", default="0")
    root.add_argument("--workers", type=int, default=4)
    root.add_argument("--fraction", type=float, default=1.0)
    root.add_argument("--patience", type=int, default=30)
    root.add_argument("--tag", default="colab_checkpoint_r1")
    root.add_argument("--stop-after-epoch", type=int)
    root.add_argument("--download-approved-weight", action="store_true")
    return root


def build_train_command(args: argparse.Namespace, model: Path, state_dir: Path) -> list[str]:
    command = [
        "uv",
        "run",
        "python",
        "-m",
        "m1.resumable_train",
        "--model",
        str(model),
        "--checkpoint-dir",
        str(state_dir / "recovery"),
        "--seed",
        str(args.seed),
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
    if args.mode == "resume":
        command.append("--resume")
    if args.stop_after_epoch is not None:
        command.extend(("--stop-after-epoch", str(args.stop_after_epoch)))
    return command


def _package_successor(
    *,
    repo_root: Path,
    run_dir: Path,
    execution_path: Path,
    text_log: Path,
    database_log: Path,
    output: Path,
) -> dict[str, Any]:
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
    invalid = [
        path
        for path in required
        if not path.is_file() or path.is_symlink() or path.stat().st_size == 0
    ]
    if invalid:
        raise RuntimeError("successor result roster contains a missing, linked or empty artifact")
    execution = base.strict_json(execution_path)
    if (
        execution.get("schema_version") != 1
        or execution.get("status") != "SUCCEEDED"
        or execution.get("sealed_test_accessed") is not False
        or execution.get("steps_completed") != list(RECOVERY_STEPS)
        or execution.get("error") is not None
        or execution.get("run_dir") != str(run_dir)
        or execution.get("mode") not in {"fresh", "resume"}
    ):
        raise RuntimeError("successor execution record has no bound successful outcome")
    contract_module = base.load_detector_contract(repo_root)
    claim = contract_module.inspect_run_weights(str(run_dir / "weights/best.pt"))
    run_contract = base.strict_json(run_dir / "run_contract.json")
    if run_contract["environment"]["runtime_backend"] != "cuda":
        raise RuntimeError("successor result package requires CUDA training evidence")
    base.validate_sqlite_log(database_log, text_log, run_dir / "results.csv")

    output.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = output.with_name(f"{output.name}.manifest.json")
    partial = output.with_name(f".{output.name}.partial")
    manifest_partial = manifest_path.with_name(f".{manifest_path.name}.partial")
    if any(
        path.exists() or path.is_symlink()
        for path in (output, manifest_path, partial, manifest_partial)
    ):
        raise RuntimeError("refused to overwrite an existing successor result package")
    log_paths = {execution_path, text_log, database_log}
    with tarfile.open(partial, mode="x:gz", compresslevel=1) as archive:
        for path in required:
            archive.add(
                path,
                arcname=base.result_arcname(path, run_dir, log_paths),
                recursive=False,
            )
    entries = [
        {
            "path": base.result_arcname(path, run_dir, log_paths),
            "size": path.stat().st_size,
            "sha256": base.sha256_file(path),
        }
        for path in required
    ]
    manifest = {
        "status": "D1_COLAB_RESULT_PACKAGE",
        "run": run_dir.name,
        "archive_name": output.name,
        "archive_sha256": base.sha256_file(partial),
        "files": entries,
        "terminal_outcome": "SUCCEEDED",
        "sealed_test_accessed": False,
        "run_attestation_sha256": claim["run_attestation_sha256"],
    }
    with manifest_partial.open("xb") as handle:
        handle.write(
            (json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()
        )
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(partial, output)
    os.replace(manifest_partial, manifest_path)
    return {**base.verify_result_archive(output, manifest_path), "manifest": str(manifest_path)}


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if re.fullmatch(r"[A-Za-z0-9_.-]+", args.tag) is None:
        print(json.dumps({"status": "FAILED", "error": "--tag is unsafe"}), file=sys.stderr)
        return 1
    if args.mode == "resume" and args.stop_after_epoch is not None:
        print(
            json.dumps({"status": "FAILED", "error": "resume forbids --stop-after-epoch"}),
            file=sys.stderr,
        )
        return 1
    repo_root = require_unlinked_path(args.repo_root, directory=True)
    bundle = require_unlinked_path(args.bundle, directory=False)
    state_dir = require_unlinked_path(args.state_dir, directory=True)
    if args.mode == "fresh":
        state_dir.mkdir(parents=True, exist_ok=True)
        if any(state_dir.iterdir()):
            print(json.dumps({"status": "FAILED", "error": "fresh state must be empty"}))
            return 1
    elif not (state_dir / "recovery/latest.json").is_file():
        print(json.dumps({"status": "FAILED", "error": "resume checkpoint is missing"}))
        return 1
    for child in (
        "colab_train.log",
        "DB_logger.db",
        "colab_execution.json",
        "colab_execution.json.tmp",
        "execution_attempts.jsonl",
    ):
        require_writable_child(state_dir, child)
    logger, text_log, database_log = configure_safe_logging(state_dir)
    execution_path = state_dir / "colab_execution.json"
    attempt = {
        "mode": args.mode,
        "started_at": base.now(),
        "finished_at": None,
        "status": "STARTED",
        "error": None,
    }
    execution: dict[str, Any] = {
        "schema_version": 1,
        "status": "STARTED",
        "mode": args.mode,
        "started_at": attempt["started_at"],
        "finished_at": None,
        "repo_root": str(repo_root),
        "bundle": str(bundle),
        "bundle_sha256": base.sha256_file(bundle) if bundle.is_file() else None,
        "seed": args.seed,
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "device": args.device,
        "tag": args.tag,
        "sealed_test_accessed": False,
        "steps_completed": [],
        "train_command": None,
        "training_outcome": None,
        "run_dir": None,
        "error": None,
    }
    base.write_json(execution_path, execution)
    logger.info(
        "D1 Colab workflow started mode=%s seed=%d epochs=%d imgsz=%d batch=%d",
        args.mode,
        args.seed,
        args.epochs,
        args.imgsz,
        args.batch,
    )
    try:
        bundle_result = extract_historical_bundle(repo_root, bundle)
        logger.info("Successor bundle verification %s", json.dumps(bundle_result, sort_keys=True))
        execution["bundle_binding"] = bundle_result
        execution["steps_completed"].append("bundle_verified_and_extracted")
        execution["split_stem_sha256"] = base.verify_split_bindings(repo_root, bundle)
        base.run_command(
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
        base.run_command(logger, ["uv", "sync", "--frozen"], cwd=detector_root)
        execution["steps_completed"].append("detector_lock_synchronized")
        model = repo_root / "models/pretrained/yolo11s.pt"
        if args.download_approved_weight:
            base.download_approved_weight(logger, model)
        elif not model.is_file() or base.sha256_file(model) != base.PRETRAINED_SHA256:
            raise RuntimeError("approved pretrained weight is absent or differs")
        execution["steps_completed"].append("approved_pretrained_weight_verified")
        environment = base.colab_subprocess_environment()
        base.run_command(
            logger,
            ["uv", "run", "python", "-m", "m1.cli", "check"],
            cwd=detector_root,
            env=environment,
        )
        execution["steps_completed"].append("m1_cli_check_passed")
        command = build_train_command(args, model, state_dir)
        execution["train_command"] = command
        base.write_json(execution_path, execution)
        logger.info("Training start")
        base.run_command(logger, command, cwd=detector_root, env=environment)
        logger.info("Training end")
        outcome = base.strict_json(state_dir / "recovery/training_outcome.json")
        execution["training_outcome"] = outcome
        execution["run_dir"] = outcome["run_dir"]
        execution["steps_completed"].append("training_completed")
        execution["steps_completed"].append("checkpoint_verified")
        if outcome["status"] == "PAUSED_FOR_RESUME":
            execution["status"] = "PAUSED_FOR_RESUME"
            execution["finished_at"] = base.now()
            base.write_json(execution_path, execution)
            logger.info("Terminal outcome PAUSED_FOR_RESUME")
            attempt.update(status="PAUSED_FOR_RESUME", finished_at=execution["finished_at"])
            append_jsonl(state_dir / "execution_attempts.jsonl", attempt)
            print(json.dumps(execution, indent=2, sort_keys=True))
            return 0
        terminal_statuses = {
            "COMPLETED",
            "COMPLETED_EARLY_STOPPED",
            "COMPLETED_FROM_FINAL_CHECKPOINT",
        }
        if outcome["status"] not in terminal_statuses:
            raise RuntimeError(f"unexpected resumable training outcome: {outcome}")
        run_dir = Path(outcome["run_dir"])
        execution["status"] = "SUCCEEDED"
        execution["finished_at"] = base.now()
        base.write_json(execution_path, execution)
        logger.info("Terminal outcome SUCCEEDED; validated result packaging begins")
        result = _package_successor(
            repo_root=repo_root,
            run_dir=run_dir,
            execution_path=execution_path,
            text_log=text_log,
            database_log=database_log,
            output=state_dir / f"{run_dir.name}_result.tar.gz",
        )
        attempt.update(status="SUCCEEDED", finished_at=execution["finished_at"])
        append_jsonl(state_dir / "execution_attempts.jsonl", attempt)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except Exception as error:
        execution["status"] = "FAILED"
        execution["finished_at"] = base.now()
        execution["error"] = f"{type(error).__name__}: {error}"
        base.write_json(execution_path, execution)
        attempt.update(
            status="FAILED",
            finished_at=execution["finished_at"],
            error=execution["error"],
        )
        append_jsonl(state_dir / "execution_attempts.jsonl", attempt)
        logger.exception("D1 resumable Colab workflow failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
