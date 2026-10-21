#!/usr/bin/env python3
"""Pilot R3 recovery sidecar: retry recorded resume failures without rebinding training.

This file is intentionally executable outside the training checkout.  The governed
training repository stays pinned at the commit recorded by the existing checkpoint;
``--repo-root`` supplies that checkout and this sidecar only repairs orchestration.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

EXPECTED_TRAINING_COMMIT = "939f6bbce9f5c955b13ebcc84addd5083d242355"
EXPECTED_EPOCHS = 100
EXPECTED_PATIENCE = 0
EXPECTED_SEED = 20261018
EXPECTED_IMGSZ = 1280
EXPECTED_BATCH = 4
EXPECTED_DEVICE = "0"
EXPECTED_TAG = "pilot_100e_seed_20261018_r2"
ATTEMPT_KEYS = {
    "mode",
    "started_at",
    "finished_at",
    "status",
    "error",
    "runtime_identity",
    "run_binding_sha256",
    "checkpoint_binding_sha256",
}


@dataclass(frozen=True)
class Dependencies:
    pilot_r2: Any
    r6: Any
    r2: Any
    r1: Any


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load pinned recovery dependency: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def reject_symlink_components(path: Path) -> Path:
    lexical = path.expanduser().absolute()
    current = lexical
    while True:
        if current.is_symlink():
            raise RuntimeError(f"training checkout path contains a symlink: {current}")
        if current == current.parent:
            break
        current = current.parent
    return lexical


def load_dependencies(repo_root: Path) -> Dependencies:
    root = reject_symlink_components(repo_root)
    _training_commit(root)
    predecessor = reject_symlink_components(
        root / "detector/colab/run_d1_colab_pilot_r2.py"
    )
    if not predecessor.is_file():
        raise RuntimeError("pinned Pilot R2 predecessor is missing")
    pilot_r2 = _load(
        "d1_pilot_r3_training_commit_pilot_r2",
        predecessor,
    )
    return Dependencies(
        pilot_r2=pilot_r2,
        r6=pilot_r2.r6,
        r2=pilot_r2.r6.r2,
        r1=pilot_r2.r6.r2.r1,
    )


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _timestamp(value: Any) -> datetime:
    if not isinstance(value, str) or not value:
        raise RuntimeError("runtime attempt timestamp is missing")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise RuntimeError("runtime attempt timestamp is malformed") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RuntimeError("runtime attempt timestamp lacks a UTC offset")
    return parsed


def _validate_identity(value: Any) -> None:
    if (
        not isinstance(value, dict)
        or set(value) != {"schema", "digest"}
        or value.get("schema") != "sha256:d1-runtime-v1:tag+linux-boot-id"
        or not _is_sha256(value.get("digest"))
    ):
        raise RuntimeError("runtime identity is missing or malformed")


def _validate_terminal_attempt(record: Any) -> None:
    if not isinstance(record, dict) or set(record) != ATTEMPT_KEYS:
        raise RuntimeError("runtime attempt schema differs")
    _validate_identity(record["runtime_identity"])
    if not _is_sha256(record["run_binding_sha256"]):
        raise RuntimeError("runtime attempt run binding is malformed")
    if not _is_sha256(record["checkpoint_binding_sha256"]):
        raise RuntimeError("runtime attempt checkpoint binding is malformed")
    if record["mode"] not in {"fresh", "resume"}:
        raise RuntimeError("runtime attempt mode differs")
    started = _timestamp(record["started_at"])
    finished = _timestamp(record["finished_at"])
    if not started < finished:
        raise RuntimeError("runtime attempt chronology is invalid")
    if record["status"] == "FAILED":
        if not isinstance(record["error"], str) or not record["error"].strip():
            raise RuntimeError("failed runtime attempt lacks its error")
    elif record["error"] is not None:
        raise RuntimeError("successful runtime attempt unexpectedly records an error")


def validate_retry_attempts(attempts: Any, *, require_success: bool) -> dict[str, Any]:
    if not isinstance(attempts, list) or not attempts:
        raise RuntimeError("runtime evidence requires an attempt history")
    for record in attempts:
        _validate_terminal_attempt(record)
    fresh = attempts[0]
    if (fresh["mode"], fresh["status"]) != ("fresh", "PAUSED_FOR_RESUME"):
        raise RuntimeError("first runtime attempt is not the fresh pause leg")
    resume_records = attempts[1:]
    if require_success:
        if not resume_records or resume_records[-1]["status"] != "SUCCEEDED":
            raise RuntimeError("final runtime attempt is not the successful resume leg")
        failed_records = resume_records[:-1]
    else:
        failed_records = resume_records
    if any(
        record["mode"] != "resume" or record["status"] != "FAILED"
        for record in failed_records
    ):
        raise RuntimeError("retry prefix contains a non-failed resume attempt")
    if require_success and resume_records[-1]["mode"] != "resume":
        raise RuntimeError("final runtime attempt is not a resume")
    run_binding = fresh["run_binding_sha256"]
    checkpoint_binding = fresh["checkpoint_binding_sha256"]
    fresh_digest = fresh["runtime_identity"]["digest"]
    previous_finish = _timestamp(fresh["finished_at"])
    for record in resume_records:
        started = _timestamp(record["started_at"])
        finished = _timestamp(record["finished_at"])
        if previous_finish > started:
            raise RuntimeError("runtime attempt chronology is invalid or overlapping")
        if record["run_binding_sha256"] != run_binding:
            raise RuntimeError("runtime attempt run bindings differ")
        if record["checkpoint_binding_sha256"] != checkpoint_binding:
            raise RuntimeError("runtime attempt checkpoint bindings differ")
        if record["runtime_identity"]["digest"] == fresh_digest:
            raise RuntimeError("resume requires a distinct runtime identity")
        previous_finish = finished
    return {
        "attempt_count": len(attempts),
        "failed_resume_count": len(failed_records),
        "run_binding_sha256": run_binding,
        "checkpoint_binding_sha256": checkpoint_binding,
        "fresh_runtime_digest": fresh_digest,
    }


def validate_runtime_evidence(execution: Any, attempts: Any) -> dict[str, Any]:
    summary = validate_retry_attempts(attempts, require_success=True)
    final = attempts[-1]
    if (
        not isinstance(execution, dict)
        or type(execution.get("schema_version")) is not int
        or execution.get("schema_version") != 2
        or execution.get("status") != "SUCCEEDED"
        or execution.get("mode") != "resume"
        or execution.get("sealed_test_accessed") is not False
        or execution.get("error") is not None
        or execution.get("runtime_identity") != final["runtime_identity"]
        or execution.get("run_binding_sha256") != summary["run_binding_sha256"]
        or execution.get("checkpoint_binding_sha256")
        != summary["checkpoint_binding_sha256"]
        or execution.get("execution_attempts") != attempts
    ):
        raise RuntimeError("execution record is not bound to retry-aware runtime evidence")
    return {
        "status": "D1_RUNTIME_RETRY_EVIDENCE_VERIFIED",
        "attempt_count": summary["attempt_count"],
        "failed_resume_count": summary["failed_resume_count"],
        "distinct_runtime_digests": True,
        "run_binding_sha256": summary["run_binding_sha256"],
        "checkpoint_binding_sha256": summary["checkpoint_binding_sha256"],
        "sealed_test_accessed": False,
    }


def validate_retry_prefix(
    completed: list[dict[str, Any]],
    *,
    identity: dict[str, str],
    run_binding_sha256: str,
    checkpoint_binding_sha256: str,
) -> None:
    summary = validate_retry_attempts(completed, require_success=False)
    if identity["digest"] == summary["fresh_runtime_digest"]:
        raise RuntimeError("resume requires a distinct runtime identity")
    if run_binding_sha256 != summary["run_binding_sha256"]:
        raise RuntimeError("resume run binding differs from fresh attempt")
    if checkpoint_binding_sha256 != summary["checkpoint_binding_sha256"]:
        raise RuntimeError("resume checkpoint binding differs from fresh attempt")


def verify_result_archive(
    archive_path: Path, manifest_path: Path, dependencies: Dependencies
) -> dict[str, Any]:
    original = dependencies.r2.validate_runtime_evidence
    dependencies.r2.validate_runtime_evidence = validate_runtime_evidence
    try:
        return dependencies.r2.verify_r4_result_archive(archive_path, manifest_path)
    finally:
        dependencies.r2.validate_runtime_evidence = original


def verify_live_state(state_dir: Path, repo_root: Path) -> dict[str, Any]:
    _training_commit(reject_symlink_components(repo_root))
    dependencies = load_dependencies(repo_root)
    original = dependencies.r2.validate_runtime_evidence
    dependencies.r2.validate_runtime_evidence = validate_runtime_evidence
    try:
        return dependencies.r6.verify_live_state(state_dir)
    finally:
        dependencies.r2.validate_runtime_evidence = original


def _validate_arguments(args: Any) -> None:
    if args.mode != "resume":
        raise RuntimeError("pilot R3 is a resume-only recovery successor")
    if args.stop_after_epoch is not None:
        raise RuntimeError("pilot R3 resume forbids --stop-after-epoch")
    if (
        args.epochs != EXPECTED_EPOCHS
        or args.patience != EXPECTED_PATIENCE
        or args.seed != EXPECTED_SEED
        or args.imgsz != EXPECTED_IMGSZ
        or args.batch != EXPECTED_BATCH
        or str(args.device) != EXPECTED_DEVICE
        or args.tag != EXPECTED_TAG
    ):
        raise RuntimeError("pilot R3 configuration differs from the reviewed recovery candidate")


def _training_commit(repo_root: Path) -> str:
    root = reject_symlink_components(repo_root)
    if not root.is_dir():
        raise RuntimeError("training checkout directory is missing")
    git_dir = reject_symlink_components(root / ".git")
    if not git_dir.is_dir():
        raise RuntimeError("training checkout Git directory is missing")
    try:
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
    except (OSError, subprocess.CalledProcessError) as error:
        raise RuntimeError("training checkout is not a readable Git checkout") from error
    if head != EXPECTED_TRAINING_COMMIT:
        raise RuntimeError("training checkout commit differs from the checkpoint-bound commit")
    if dirty:
        raise RuntimeError("training checkout is not clean")
    return head


def _run_resume(argv: list[str] | None, dependencies: Dependencies) -> int:
    args = dependencies.r1.parser().parse_args(argv)
    _validate_arguments(args)
    repo_root = dependencies.r1.require_unlinked_path(args.repo_root, directory=True)
    _training_commit(repo_root)
    state_dir = args.state_dir.expanduser().absolute()
    bundle = args.bundle.expanduser().absolute()
    started_at = dependencies.r1.base.now()
    identity = None
    binding = None
    completed: list[dict[str, Any]] = []
    try:
        dependencies.r1.require_unlinked_path(state_dir, directory=True)
        safe_bundle = dependencies.r1.require_unlinked_path(bundle, directory=False)
        identity = dependencies.r2.derive_runtime_identity(
            args.tag, dependencies.r2.BOOT_ID_PATH.read_text(encoding="ascii")
        )
        binding = dependencies.r2.run_binding(
            args, dependencies.r1.base.sha256_file(safe_bundle)
        )
        completed = dependencies.r2._completed_attempts(state_dir)
        checkpoint = dependencies.r2.checkpoint_binding(state_dir)
        validate_retry_prefix(
            completed,
            identity=identity,
            run_binding_sha256=binding,
            checkpoint_binding_sha256=checkpoint,
        )
        dependencies.r6.r5.verify_current_checkpoint(state_dir, checkpoint)
    except Exception as error:
        try:
            dependencies.r6.r5.durable_preflight_failure(
                state_dir,
                args,
                started_at,
                error,
                identity=identity,
                binding=binding,
                completed=completed,
            )
        except Exception:
            pass
        print(json.dumps({"status": "FAILED", "error": f"{type(error).__name__}: {error}"}))
        return 1

    assert identity is not None and binding is not None
    base = dependencies.r1.base
    original_write_json = base.write_json
    original_strict_json = base.strict_json
    original_append_jsonl = dependencies.r1.append_jsonl
    original_verify = base.verify_result_archive

    def enriched_attempt(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            **payload,
            "runtime_identity": identity,
            "run_binding_sha256": binding,
            "checkpoint_binding_sha256": dependencies.r2.checkpoint_binding(state_dir),
        }

    def enriched_write_json(path: Path, payload: dict[str, Any]) -> None:
        if path.name != "colab_execution.json":
            original_write_json(path, payload)
            return
        enriched = dict(payload)
        enriched["schema_version"] = 2
        enriched["runtime_identity"] = identity
        enriched["run_binding_sha256"] = binding
        current = {
            "mode": args.mode,
            "started_at": enriched["started_at"],
            "finished_at": enriched.get("finished_at"),
            "status": enriched["status"],
            "error": enriched.get("error"),
            "runtime_identity": identity,
            "run_binding_sha256": binding,
            "checkpoint_binding_sha256": dependencies.r2.checkpoint_binding(state_dir),
        }
        enriched["checkpoint_binding_sha256"] = current["checkpoint_binding_sha256"]
        enriched["execution_attempts"] = [*completed, current]
        original_write_json(path, enriched)

    def enriched_append_jsonl(path: Path, payload: dict[str, Any]) -> None:
        original_append_jsonl(path, enriched_attempt(payload))

    def successor_strict_json(path: Path) -> Any:
        payload = original_strict_json(path)
        if (
            path.name == "colab_execution.json"
            and isinstance(payload, dict)
            and payload.get("schema_version") == 2
        ):
            compatible = dict(payload)
            compatible["schema_version"] = 1
            return compatible
        return payload

    base.write_json = enriched_write_json
    base.strict_json = successor_strict_json
    dependencies.r1.append_jsonl = enriched_append_jsonl
    base.verify_result_archive = lambda archive, manifest: verify_result_archive(
        archive, manifest, dependencies
    )
    try:
        return dependencies.r1.main(argv)
    finally:
        base.write_json = original_write_json
        base.strict_json = original_strict_json
        dependencies.r1.append_jsonl = original_append_jsonl
        base.verify_result_archive = original_verify


def _repo_root_from_argv(argv: list[str] | None) -> Path:
    preflight = argparse.ArgumentParser(add_help=False)
    preflight.add_argument("--repo-root", type=Path, required=True)
    known, _ = preflight.parse_known_args(argv)
    return known.repo_root


def main(argv: list[str] | None = None) -> int:
    repo_root = reject_symlink_components(_repo_root_from_argv(argv))
    _training_commit(repo_root)
    dependencies = load_dependencies(repo_root)
    args = dependencies.r1.parser().parse_args(argv)
    _validate_arguments(args)
    base = dependencies.r1.base
    original_strict_json = base.strict_json

    def guarded_strict_json(path: Path) -> Any:
        payload = original_strict_json(path)
        if path.name == "training_outcome.json":
            dependencies.pilot_r2.validate_pilot_outcome(payload, mode="resume")
        return payload

    base.strict_json = guarded_strict_json
    try:
        return _run_resume(argv, dependencies)
    finally:
        base.strict_json = original_strict_json


if __name__ == "__main__":
    raise SystemExit(main())
