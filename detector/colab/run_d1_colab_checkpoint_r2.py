#!/usr/bin/env python3
"""Append-only R4 successor with privacy-preserving two-runtime evidence."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Any

RUNTIME_SCHEMA = "sha256:d1-runtime-v1:tag+linux-boot-id"
BOOT_ID_PATH = Path("/proc/sys/kernel/random/boot_id")
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


def _load_r1() -> Any:
    path = Path(__file__).with_name("run_d1_colab_checkpoint_r1.py")
    spec = importlib.util.spec_from_file_location("d1_checkpoint_r4_pinned_r1", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load pinned checkpoint runner: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


r1 = _load_r1()
ORIGINAL_VERIFY_RESULT_ARCHIVE = r1.base.verify_result_archive


def canonical_sha256(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def strict_json_bytes(payload: bytes) -> Any:
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
        payload,
        parse_constant=reject_constant,
        object_pairs_hook=unique_object,
    )


def derive_runtime_identity(tag: str, boot_id: str) -> dict[str, str]:
    normalized = boot_id.strip().lower()
    boot_id_pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
    if re.fullmatch(boot_id_pattern, normalized) is None:
        raise RuntimeError("Linux boot_id is missing or malformed")
    if re.fullmatch(r"[A-Za-z0-9_.-]+", tag) is None:
        raise RuntimeError("runtime identity tag is unsafe")
    digest = hashlib.sha256(
        b"d1-runtime-v1\0" + tag.encode("ascii") + b"\0" + normalized.encode("ascii")
    ).hexdigest()
    return {"schema": RUNTIME_SCHEMA, "digest": digest}


def run_binding(args: Any, bundle_sha256: str) -> str:
    return canonical_sha256(
        {
            "schema": "d1-run-binding-v1",
            "bundle_sha256": bundle_sha256,
            "seed": args.seed,
            "epochs": args.epochs,
            "imgsz": args.imgsz,
            "batch": args.batch,
            "device": str(args.device),
            "workers": args.workers,
            "fraction": args.fraction,
            "patience": args.patience,
            "tag": args.tag,
        }
    )


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _validate_identity(value: Any) -> None:
    if (
        not isinstance(value, dict)
        or set(value) != {"schema", "digest"}
        or value["schema"] != RUNTIME_SCHEMA
        or not _is_sha256(value["digest"])
    ):
        raise RuntimeError("runtime identity is missing or malformed")


def _validate_attempt(record: Any) -> None:
    if not isinstance(record, dict) or set(record) != ATTEMPT_KEYS:
        raise RuntimeError("runtime attempt schema differs")
    _validate_identity(record["runtime_identity"])
    if not _is_sha256(record["run_binding_sha256"]):
        raise RuntimeError("runtime attempt run binding is malformed")
    if not _is_sha256(record["checkpoint_binding_sha256"]):
        raise RuntimeError("runtime attempt checkpoint binding is malformed")
    if (
        record["mode"] not in {"fresh", "resume"}
        or not isinstance(record["started_at"], str)
        or not record["started_at"]
        or not isinstance(record["finished_at"], str)
        or not record["finished_at"]
        or record["error"] is not None
    ):
        raise RuntimeError("runtime attempt terminal fields differ")


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise RuntimeError("runtime attempt timestamp is malformed") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RuntimeError("runtime attempt timestamp lacks a UTC offset")
    return parsed


def validate_runtime_evidence(execution: Any, attempts: Any) -> dict[str, Any]:
    if not isinstance(attempts, list) or len(attempts) != 2:
        raise RuntimeError("runtime evidence requires exactly two attempts")
    for record in attempts:
        _validate_attempt(record)
    fresh, resume = attempts
    if (fresh["mode"], fresh["status"]) != ("fresh", "PAUSED_FOR_RESUME"):
        raise RuntimeError("first runtime attempt is not the fresh pause leg")
    if (resume["mode"], resume["status"]) != ("resume", "SUCCEEDED"):
        raise RuntimeError("second runtime attempt is not the successful resume leg")
    fresh_start = _timestamp(fresh["started_at"])
    fresh_finish = _timestamp(fresh["finished_at"])
    resume_start = _timestamp(resume["started_at"])
    resume_finish = _timestamp(resume["finished_at"])
    if not fresh_start < fresh_finish <= resume_start < resume_finish:
        raise RuntimeError("runtime attempt chronology is invalid or overlapping")
    if fresh["runtime_identity"]["digest"] == resume["runtime_identity"]["digest"]:
        raise RuntimeError("fresh and resume attempts used the same runtime identity")
    if fresh["run_binding_sha256"] != resume["run_binding_sha256"]:
        raise RuntimeError("fresh and resume run bindings differ")
    if fresh["checkpoint_binding_sha256"] != resume["checkpoint_binding_sha256"]:
        raise RuntimeError("fresh and resume checkpoint bindings differ")
    if not isinstance(execution, dict):
        raise RuntimeError("execution record is not an object")
    if (
        execution.get("schema_version") != 2
        or execution.get("status") != "SUCCEEDED"
        or execution.get("mode") != "resume"
        or execution.get("sealed_test_accessed") is not False
        or execution.get("error") is not None
        or execution.get("runtime_identity") != resume["runtime_identity"]
        or execution.get("run_binding_sha256") != resume["run_binding_sha256"]
        or execution.get("checkpoint_binding_sha256")
        != resume["checkpoint_binding_sha256"]
        or execution.get("execution_attempts") != attempts
    ):
        raise RuntimeError("execution record is not bound to the two-runtime evidence")
    return {
        "status": "D1_RUNTIME_EVIDENCE_VERIFIED",
        "attempt_count": 2,
        "distinct_runtime_digests": True,
        "run_binding_sha256": resume["run_binding_sha256"],
        "checkpoint_binding_sha256": resume["checkpoint_binding_sha256"],
        "sealed_test_accessed": False,
    }


def read_attempts(path: Path) -> list[dict[str, Any]]:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError("execution_attempts.jsonl is missing or linked")
    records = []

    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON constant is forbidden: {value}")

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key is forbidden: {key}")
            result[key] = value
        return result

    for line in path.read_text(encoding="utf-8").splitlines():
        if not line:
            raise RuntimeError("execution_attempts.jsonl contains a blank record")
        records.append(
            json.loads(
                line,
                parse_constant=reject_constant,
                object_pairs_hook=unique_object,
            )
        )
    return records


def checkpoint_binding(state_dir: Path) -> str:
    latest = r1.base.strict_json(state_dir / "recovery/latest.json")
    value = latest.get("binding_sha256")
    if not _is_sha256(value):
        raise RuntimeError("latest checkpoint binding is missing or malformed")
    return value


def verify_current_checkpoint(state_dir: Path, expected_binding: str) -> dict[str, Any]:
    recovery = state_dir / "recovery"
    latest_path = recovery / "latest.json"
    if not latest_path.is_file() or latest_path.is_symlink():
        raise RuntimeError("checkpoint latest pointer is missing or linked")
    latest = strict_json_bytes(latest_path.read_bytes())
    if not isinstance(latest, dict) or set(latest) != {
        "schema_version",
        "generation",
        "manifest_sha256",
        "binding_sha256",
    }:
        raise RuntimeError("checkpoint latest pointer schema differs")
    generation = latest["generation"]
    if (
        latest["schema_version"] != 1
        or not isinstance(generation, str)
        or re.fullmatch(r"epoch-[0-9]{4}", generation) is None
        or not _is_sha256(latest["manifest_sha256"])
        or latest["binding_sha256"] != expected_binding
    ):
        raise RuntimeError("checkpoint latest pointer identity differs")
    snapshot = recovery / "snapshots" / generation
    if not snapshot.is_dir() or snapshot.is_symlink():
        raise RuntimeError("checkpoint snapshot is missing or linked")
    manifest_path = snapshot / "checkpoint_manifest.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise RuntimeError("checkpoint manifest is missing or linked")
    if r1.base.sha256_file(manifest_path) != latest["manifest_sha256"]:
        raise RuntimeError("checkpoint manifest hash differs from latest pointer")
    manifest = strict_json_bytes(manifest_path.read_bytes())
    if not isinstance(manifest, dict) or set(manifest) != {
        "schema_version",
        "status",
        "run",
        "completed_epoch",
        "binding",
        "binding_sha256",
        "files",
    }:
        raise RuntimeError("checkpoint manifest schema differs")
    if (
        manifest["schema_version"] != 1
        or manifest["status"] != "RECOVERABLE"
        or manifest["binding_sha256"] != expected_binding
        or canonical_sha256(manifest["binding"]) != expected_binding
        or generation != f"epoch-{manifest['completed_epoch']:04d}"
    ):
        raise RuntimeError("checkpoint manifest identity differs")
    records = manifest["files"]
    expected_paths = {
        "weights/last.pt",
        "weights/best.pt",
        "results.csv",
        "args.yaml",
        "run_contract.json",
    }
    if not isinstance(records, list) or len(records) != len(expected_paths):
        raise RuntimeError("checkpoint manifest file roster differs")
    by_path = {record.get("path"): record for record in records if isinstance(record, dict)}
    if set(by_path) != expected_paths:
        raise RuntimeError("checkpoint manifest file roster differs")
    for name, record in by_path.items():
        path = snapshot / name
        if (
            set(record) != {"path", "size", "sha256"}
            or type(record["size"]) is not int
            or record["size"] <= 0
            or not _is_sha256(record["sha256"])
            or not path.is_file()
            or path.is_symlink()
            or path.stat().st_size != record["size"]
            or r1.base.sha256_file(path) != record["sha256"]
        ):
            raise RuntimeError(f"checkpoint artifact differs: {name}")
    return manifest


def verify_r4_result_archive(archive_path: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = ORIGINAL_VERIFY_RESULT_ARCHIVE(archive_path, manifest_path)
    run = manifest["run"]
    execution_name = "colab_logs/colab_execution.json"
    with tarfile.open(archive_path, mode="r:gz") as archive:
        member = archive.getmember(execution_name)
        handle = archive.extractfile(member)
        if handle is None:
            raise RuntimeError("result archive execution record is unreadable")
        execution = strict_json_bytes(handle.read())
    evidence = validate_runtime_evidence(execution, execution.get("execution_attempts"))
    if not run.startswith("D1_"):
        raise RuntimeError("result archive run identity differs")
    return {
        **manifest,
        "runtime_evidence": evidence,
        "runtime_attempts": execution["execution_attempts"],
    }


def verify_live_state(state_dir: Path) -> dict[str, Any]:
    execution = r1.base.strict_json(state_dir / "colab_execution.json")
    attempts = read_attempts(state_dir / "execution_attempts.jsonl")
    evidence = validate_runtime_evidence(execution, attempts)
    verify_current_checkpoint(state_dir, evidence["checkpoint_binding_sha256"])
    archives = sorted(state_dir.glob("*_result.tar.gz"))
    if len(archives) != 1:
        raise RuntimeError("live state must contain exactly one result archive")
    manifest_path = archives[0].with_name(f"{archives[0].name}.manifest.json")
    result = verify_r4_result_archive(archives[0], manifest_path)
    if result["runtime_evidence"] != evidence or result["runtime_attempts"] != attempts:
        raise RuntimeError("archive and live runtime evidence differ")
    return {"status": "D1_R4_LIVE_STATE_VERIFIED", "runtime_evidence": evidence}


def _completed_attempts(state_dir: Path) -> list[dict[str, Any]]:
    path = state_dir / "execution_attempts.jsonl"
    if not path.exists():
        return []
    return read_attempts(path)


def record_preflight_failure(
    state_dir: Path,
    args: Any,
    started_at: str,
    error: Exception,
    *,
    identity: dict[str, str] | None,
    binding: str | None,
    completed: list[dict[str, Any]],
) -> None:
    safe_state = r1.require_unlinked_path(state_dir, directory=True)
    safe_state.mkdir(parents=True, exist_ok=True)
    for child in ("colab_execution.json", "colab_execution.json.tmp", "execution_attempts.jsonl"):
        r1.require_writable_child(safe_state, child)
    finished_at = r1.base.now()
    message = f"{type(error).__name__}: {error}"
    latest = safe_state / "recovery/latest.json"
    checkpoint = checkpoint_binding(safe_state) if latest.is_file() else None
    attempt = {
        "mode": args.mode,
        "started_at": started_at,
        "finished_at": finished_at,
        "status": "FAILED",
        "error": message,
        "runtime_identity": identity,
        "run_binding_sha256": binding,
        "checkpoint_binding_sha256": checkpoint,
    }
    execution = {
        "schema_version": 2,
        "status": "FAILED",
        "mode": args.mode,
        "started_at": started_at,
        "finished_at": finished_at,
        "sealed_test_accessed": False,
        "runtime_identity": identity,
        "run_binding_sha256": binding,
        "checkpoint_binding_sha256": checkpoint,
        "execution_attempts": [*completed, attempt],
        "error": message,
    }
    r1.base.write_json(safe_state / "colab_execution.json", execution)
    r1.append_jsonl(safe_state / "execution_attempts.jsonl", attempt)


def main(argv: list[str] | None = None) -> int:
    args = r1.parser().parse_args(argv)
    state_dir = args.state_dir.expanduser().absolute()
    bundle = args.bundle.expanduser().absolute()
    started_at = r1.base.now()
    identity = None
    binding = None
    completed: list[dict[str, Any]] = []
    try:
        r1.require_unlinked_path(state_dir, directory=True)
        safe_bundle = r1.require_unlinked_path(bundle, directory=False)
        identity = derive_runtime_identity(args.tag, BOOT_ID_PATH.read_text(encoding="ascii"))
        binding = run_binding(args, r1.base.sha256_file(safe_bundle))
        completed = _completed_attempts(state_dir)
        if args.mode == "fresh":
            if completed:
                raise RuntimeError("fresh R4 state already contains attempts")
        else:
            if len(completed) != 1:
                raise RuntimeError("resume R4 state requires exactly one fresh attempt")
            prior = completed[0]
            _validate_attempt(prior)
            if (prior["mode"], prior["status"]) != ("fresh", "PAUSED_FOR_RESUME"):
                raise RuntimeError("resume R4 state lacks the fresh pause attempt")
            if prior["runtime_identity"]["digest"] == identity["digest"]:
                raise RuntimeError("resume requires a distinct runtime identity")
            if prior["run_binding_sha256"] != binding:
                raise RuntimeError("resume run binding differs from fresh attempt")
    except Exception as error:
        try:
            record_preflight_failure(
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

    original_write_json = r1.base.write_json
    original_strict_json = r1.base.strict_json
    original_append_jsonl = r1.append_jsonl
    original_verify = r1.base.verify_result_archive

    def enriched_attempt(payload: dict[str, Any]) -> dict[str, Any]:
        latest = state_dir / "recovery/latest.json"
        return {
            **payload,
            "runtime_identity": identity,
            "run_binding_sha256": binding,
            "checkpoint_binding_sha256": (
                checkpoint_binding(state_dir) if latest.is_file() else None
            ),
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
            "checkpoint_binding_sha256": None,
        }
        latest = state_dir / "recovery/latest.json"
        if latest.is_file():
            current["checkpoint_binding_sha256"] = checkpoint_binding(state_dir)
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

    r1.base.write_json = enriched_write_json
    r1.base.strict_json = successor_strict_json
    r1.append_jsonl = enriched_append_jsonl
    r1.base.verify_result_archive = verify_r4_result_archive
    try:
        return r1.main(argv)
    finally:
        r1.base.write_json = original_write_json
        r1.base.strict_json = original_strict_json
        r1.append_jsonl = original_append_jsonl
        r1.base.verify_result_archive = original_verify


if __name__ == "__main__":
    raise SystemExit(main())
