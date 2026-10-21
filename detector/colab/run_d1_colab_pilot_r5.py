#!/usr/bin/env python3
"""Pilot R5 finalizer for the packaged epoch-0100 Pilot R2 run.

R4 repaired retry-aware SQLite validation and successfully produced the final
archive, but its notebook's last readback exposed two orchestration defects:

* a reconstructed run directory may remain as the checkout's sole untracked
  path after packaging; and
* the inherited R6 verifier temporarily reinstalls its original two-attempt
  validator, shadowing Pilot R3's retry-aware validator.

This append-only sidecar performs no training and no packaging.  It may remove
only the exact untracked, reconstructed run directory after a fail-closed Git
dry-run, then installs the retry-aware validator at the R6 wrapper boundary and
verifies the live Drive state, archive, checkpoint and durable logs.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

EXPECTED_TRAINING_COMMIT = "939f6bbce9f5c955b13ebcc84addd5083d242355"
EXPECTED_RUN = (
    "D1_yolo11s_wp33_afa03d4b_20261018_20261021T111233_"
    "pilot_100e_seed_20261018_r2"
)
PILOT_R3_SHA256 = "8c9b23472091f6c677d635a54e4f4e8b896e1fcf204d627ba56eb208db00c49c"
PILOT_R4_SHA256 = "ffcc88e2339b349775ca34e5e30531a102d0bcab1d45fa0dff9b1ea8bead25ad"
EXPECTED_FINAL_GENERATION = "epoch-0100"
EXPECTED_ATTEMPT_COUNT = 6
EXPECTED_FAILED_RESUME_COUNT = 4
EXPECTED_LIVE_ARTIFACTS = {
    "colab_execution.json": (
        6848,
        "0f3f6bb9d96d4b852a97966f37048b659ffaa424868af05834e482c9ae01ccbc",
    ),
    "execution_attempts.jsonl": (
        3584,
        "eeedb9a8954ad4445b1ee65484d2b69cf30d106fa486f93c815b9241e7882b84",
    ),
    "DB_logger.db": (
        32940032,
        "57e93f1c78365b4396600136ab16887d9bc6731a3343fe65787fd7390abd9bb8",
    ),
    "colab_train.log": (
        16324955,
        "a3bdec9a5eb31b33126c75f20bdb9d9376b5e6ecc22ba422f54ecdb70107defe",
    ),
    "recovery/latest.json": (
        233,
        "252b889a7b4136cba12609b11766e29e217f5ef1c93a2073d0e7dc9d2991eaf5",
    ),
}
EXPECTED_ARCHIVE_SIZE = 144369956
EXPECTED_ARCHIVE_SHA256 = "6ae2e6a29e1712ff5372764d5cc1eb6bb7ae9c9d06d7a08de8aab3e3c2f6778f"
EXPECTED_MANIFEST_SIZE = 2140
EXPECTED_MANIFEST_SHA256 = "0ecac47986d946ed83dfbac1e203f60b4e6055e5054ed9c52476db128b7f7796"


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load pinned Pilot dependency: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_exact_regular_file(
    path: Path, *, expected_size: int, expected_sha256: str
) -> Path:
    """Require one exact, regular, unlinked artifact and hash it without following links."""
    safe = reject_symlink_components(path)
    try:
        metadata = safe.lstat()
    except FileNotFoundError as error:
        raise RuntimeError(f"required artifact is missing: {safe}") from error
    if not stat.S_ISREG(metadata.st_mode):
        raise RuntimeError(f"required artifact is not a regular file: {safe}")
    if metadata.st_size != expected_size:
        raise RuntimeError(f"required artifact size differs: {safe}")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(safe, flags)
    except OSError as error:
        raise RuntimeError(f"required artifact cannot be opened safely: {safe}") from error
    digest = hashlib.sha256()
    with os.fdopen(descriptor, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != expected_sha256:
        raise RuntimeError(f"required artifact SHA-256 differs: {safe}")
    return safe


def reject_symlink_components(path: Path) -> Path:
    lexical = path.expanduser().absolute()
    current = lexical
    while True:
        if current.is_symlink():
            raise RuntimeError(f"path contains a symlink: {current}")
        if current == current.parent:
            break
        current = current.parent
    return lexical


def strict_json(path: Path) -> Any:
    safe = reject_symlink_components(path)
    if not safe.is_file():
        raise RuntimeError(f"JSON input is missing: {safe}")

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
        safe.read_text(encoding="utf-8"),
        parse_constant=reject_constant,
        object_pairs_hook=unique_object,
    )


def load_pilot_r4() -> Any:
    sidecar = Path(__file__).absolute().with_name("run_d1_colab_pilot_r4.py")
    if sidecar.is_symlink() or not sidecar.is_file():
        raise RuntimeError("pinned Pilot R4 predecessor is missing or linked")
    if sha256_file(sidecar) != PILOT_R4_SHA256:
        raise RuntimeError("pinned Pilot R4 predecessor hash differs")
    return _load("d1_pilot_r5_sidecar_pilot_r4", sidecar)


def _git(repo_root: Path, *args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as error:
        raise RuntimeError(f"Git command failed: {' '.join(args)}") from error


def clean_exact_ephemeral_run(repo_root: Path, state_dir: Path) -> dict[str, Any]:
    """Remove only the exact untracked reconstructed run directory, if present."""
    root = reject_symlink_components(repo_root)
    state = reject_symlink_components(state_dir)
    if not (root / ".git").is_dir():
        raise RuntimeError("training checkout Git directory is missing")
    if _git(root, "rev-parse", "HEAD").strip() != EXPECTED_TRAINING_COMMIT:
        raise RuntimeError("training checkout commit differs")

    execution = strict_json(state / "colab_execution.json")
    outcome = execution.get("training_outcome")
    if (
        not isinstance(outcome, dict)
        or outcome.get("run") != EXPECTED_RUN
        or outcome.get("completed_epoch") != 100
        or outcome.get("status") != "COMPLETED_FROM_FINAL_CHECKPOINT"
        or execution.get("status") != "SUCCEEDED"
        or execution.get("sealed_test_accessed") is not False
    ):
        raise RuntimeError("terminal execution is not the reviewed packaged pilot")

    status = _git(root, "status", "--porcelain=v1", "--untracked-files=normal")
    if not status:
        return {"status": "CHECKOUT_ALREADY_CLEAN", "removed": None}
    expected = root / "results" / "experiments" / EXPECTED_RUN
    recorded = Path(str(execution.get("run_dir", ""))).expanduser().absolute()
    if recorded != expected:
        raise RuntimeError("recorded run directory differs from the exact ephemeral target")
    relative = expected.relative_to(root).as_posix()
    if expected.is_symlink() or not expected.is_dir():
        raise RuntimeError("ephemeral run target is missing, linked or not a directory")
    expected_status = f"?? {relative}/\n"
    if status != expected_status:
        raise RuntimeError("checkout contains changes outside the exact ephemeral run")

    dry_run = _git(root, "clean", "-nd", "--", relative)
    if dry_run != f"Would remove {relative}/\n":
        raise RuntimeError("Git clean dry-run differs from the exact ephemeral target")
    removed = _git(root, "clean", "-fd", "--", relative)
    if removed != f"Removing {relative}/\n":
        raise RuntimeError("Git clean removed an unexpected target")
    if _git(root, "status", "--porcelain=v1"):
        raise RuntimeError("training checkout remains dirty after exact cleanup")
    return {"status": "EXACT_EPHEMERAL_RUN_REMOVED", "removed": relative}


def require_exact_runtime_evidence(evidence: Any) -> dict[str, Any]:
    if (
        not isinstance(evidence, dict)
        or evidence.get("status") != "D1_RUNTIME_RETRY_EVIDENCE_VERIFIED"
        or type(evidence.get("attempt_count")) is not int
        or evidence["attempt_count"] != EXPECTED_ATTEMPT_COUNT
        or type(evidence.get("failed_resume_count")) is not int
        or evidence["failed_resume_count"] != EXPECTED_FAILED_RESUME_COUNT
        or evidence.get("distinct_runtime_digests") is not True
        or evidence.get("sealed_test_accessed") is not False
    ):
        raise RuntimeError("retry-aware runtime evidence differs from the exact live history")
    return evidence


def verify_packaged_state(repo_root: Path, state_dir: Path) -> dict[str, Any]:
    root = reject_symlink_components(repo_root)
    state = reject_symlink_components(state_dir)
    for relative, (expected_size, expected_sha256) in EXPECTED_LIVE_ARTIFACTS.items():
        require_exact_regular_file(
            state / relative,
            expected_size=expected_size,
            expected_sha256=expected_sha256,
        )
    archives = sorted(state.glob("*_result.tar.gz"))
    if len(archives) != 1:
        raise RuntimeError("live state does not contain exactly one result archive")
    archive = require_exact_regular_file(
        archives[0],
        expected_size=EXPECTED_ARCHIVE_SIZE,
        expected_sha256=EXPECTED_ARCHIVE_SHA256,
    )
    manifest = require_exact_regular_file(
        archive.with_name(f"{archive.name}.manifest.json"),
        expected_size=EXPECTED_MANIFEST_SIZE,
        expected_sha256=EXPECTED_MANIFEST_SHA256,
    )
    manifest_payload = strict_json(manifest)
    manifest_files = manifest_payload.get("files") if isinstance(manifest_payload, dict) else None
    if not isinstance(manifest_files, list):
        raise RuntimeError("result archive manifest file roster is missing")
    archive_records = {
        record.get("path"): record
        for record in manifest_files
        if isinstance(record, dict)
    }
    for live_name in ("colab_execution.json", "DB_logger.db"):
        record = archive_records.get(f"colab_logs/{live_name}")
        expected_size, expected_sha256 = EXPECTED_LIVE_ARTIFACTS[live_name]
        if record != {
            "path": f"colab_logs/{live_name}",
            "size": expected_size,
            "sha256": expected_sha256,
        }:
            raise RuntimeError(f"archive manifest does not bind live artifact: {live_name}")
    pilot_r4 = load_pilot_r4()
    pilot_r3 = pilot_r4.load_pilot_r3(root)
    if sha256_file(Path(pilot_r3.__file__)) != PILOT_R3_SHA256:
        raise RuntimeError("loaded Pilot R3 predecessor hash differs")
    # The predecessor dependency loader deliberately rejects a dirty checkout.
    # Authenticate every immutable Drive/sidecar byte first, then clean only the
    # exact reviewed ephemeral directory before invoking that guard.
    cleanup = clean_exact_ephemeral_run(root, state)
    dependencies = pilot_r3.load_dependencies(root)

    execution = dependencies.r1.base.strict_json(state / "colab_execution.json")
    attempts = dependencies.r2.read_attempts(state / "execution_attempts.jsonl")
    expected_evidence = require_exact_runtime_evidence(
        pilot_r3.validate_runtime_evidence(execution, attempts)
    )

    original_r6_validator = dependencies.r6.validate_runtime_evidence
    dependencies.r6.validate_runtime_evidence = pilot_r3.validate_runtime_evidence
    try:
        verified = dependencies.r6.verify_live_state(state)
    finally:
        dependencies.r6.validate_runtime_evidence = original_r6_validator
    if verified.get("runtime_evidence") != expected_evidence:
        raise RuntimeError("R6 live verification and retry-aware evidence differ")

    latest = dependencies.r1.base.strict_json(state / "recovery/latest.json")
    if latest.get("generation") != EXPECTED_FINAL_GENERATION:
        raise RuntimeError("final checkpoint generation differs")
    snapshot = state / "recovery" / "snapshots" / EXPECTED_FINAL_GENERATION
    pilot_r4.validate_retry_aware_sqlite_log(
        state / "DB_logger.db",
        state / "colab_train.log",
        snapshot / "results.csv",
        execution_path=state / "colab_execution.json",
    )
    return {
        "status": "D1_PILOT_R5_PACKAGED_STATE_VERIFIED",
        "cleanup": cleanup,
        "archive": str(archive),
        "archive_sha256": EXPECTED_ARCHIVE_SHA256,
        "manifest": str(manifest),
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "latest_generation": latest["generation"],
        "runtime_evidence": expected_evidence,
        "sealed_test_accessed": False,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--repo-root", type=Path, required=True)
    result.add_argument("--state-dir", type=Path, required=True)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    result = verify_packaged_state(args.repo_root, args.state_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
