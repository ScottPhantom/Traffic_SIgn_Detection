"""Crash-safe, contract-bound checkpoint mirroring for long Colab training.

The training run remains on Colab's fast ephemeral disk.  After Ultralytics has
finished writing an epoch checkpoint, this module copies a complete recovery
snapshot to mounted Drive, verifies every byte, and only then atomically moves
``latest.json`` to the new generation.  A partially copied generation is never
considered resumable.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import uuid
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
LATEST = "latest.json"
SNAPSHOT_PATTERN = re.compile(r"epoch-(\d{4})$")
RUN_PATTERN = re.compile(r"D1_[A-Za-z0-9_.-]+$")
REQUIRED_ARTIFACTS = (
    "weights/last.pt",
    "weights/best.pt",
    "results.csv",
    "args.yaml",
    "run_contract.json",
)


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json_atomic(path: Path, payload: Any) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    data = (
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    ).encode("utf-8")
    try:
        with temporary.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def write_json_atomic(path: Path, payload: Any) -> None:
    """Public atomic JSON writer used by the recovery CLI."""
    _write_json_atomic(path, payload)


def _copy_verified_atomic(source: Path, destination: Path) -> dict[str, Any]:
    source_hash = sha256_file(source)
    temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with source.open("rb") as input_handle, temporary.open("xb") as output_handle:
            shutil.copyfileobj(input_handle, output_handle, length=1024 * 1024)
            output_handle.flush()
            os.fsync(output_handle.fileno())
        copied_hash = sha256_file(temporary)
        if copied_hash != source_hash:
            raise RuntimeError(f"checkpoint copy hash mismatch: {source}")
        size = temporary.stat().st_size
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return {"path": destination.name, "size": size, "sha256": source_hash}


def _assert_regular_file(path: Path, label: str) -> None:
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError as error:
        raise RuntimeError(f"{label} is missing: {path}") from error
    if not stat.S_ISREG(mode) or path.is_symlink():
        raise RuntimeError(f"{label} must be a regular non-symlink file: {path}")


def _assert_safe_directory(path: Path) -> None:
    if not path.is_absolute():
        raise RuntimeError("checkpoint directory must be absolute")
    current = path
    existing: list[Path] = []
    while True:
        if current.exists() or current.is_symlink():
            existing.append(current)
        if current == current.parent:
            break
        current = current.parent
    for candidate in reversed(existing):
        if candidate.is_symlink():
            raise RuntimeError(f"checkpoint path contains a symlink: {candidate}")
        if not candidate.is_dir():
            raise RuntimeError(f"checkpoint path component is not a directory: {candidate}")


def require_safe_directory(path: Path, *, create: bool = False) -> Path:
    """Return an absolute lexical directory after component-wise no-symlink checks."""
    lexical = path.expanduser().absolute()
    _assert_safe_directory(lexical)
    if create:
        lexical.mkdir(parents=True, exist_ok=True)
        _assert_safe_directory(lexical)
    return lexical


class CheckpointStore:
    """Persist and verify two crash-safe recovery generations."""

    def __init__(self, root: Path, *, retention: int = 2) -> None:
        self.root = root.expanduser().absolute()
        if retention < 2:
            raise ValueError("checkpoint retention must be at least two generations")
        self.retention = retention
        require_safe_directory(self.root, create=True)
        self.snapshots = self.root / "snapshots"
        self.snapshots.mkdir(exist_ok=True)

    def save(self, run_dir: Path, *, epoch: int, binding: dict[str, Any]) -> dict[str, Any]:
        """Copy one complete epoch and advance ``latest.json`` only after verification."""
        if epoch < 1 or epoch > 9999:
            raise ValueError("epoch must be in [1, 9999]")
        run_dir = run_dir.absolute()
        _assert_safe_directory(run_dir)
        generation = f"epoch-{epoch:04d}"
        destination = self.snapshots / generation
        staging = self.snapshots / f".{generation}.{uuid.uuid4().hex}.partial"
        staging.mkdir()
        files: list[dict[str, Any]] = []
        try:
            for relative in REQUIRED_ARTIFACTS:
                source = run_dir / relative
                _assert_regular_file(source, f"checkpoint source {relative}")
                record = _copy_verified_atomic(source, staging / relative)
                record["path"] = relative
                files.append(record)
            manifest = {
                "schema_version": SCHEMA_VERSION,
                "status": "RECOVERABLE",
                "run": run_dir.name,
                "completed_epoch": epoch,
                "binding": binding,
                "binding_sha256": canonical_sha256(binding),
                "files": files,
            }
            manifest_path = staging / "checkpoint_manifest.json"
            _write_json_atomic(manifest_path, manifest)
            verified = self._verify_generation(
                staging, binding, expected_generation=generation
            )
            if destination.exists() or destination.is_symlink():
                try:
                    self._verify_generation(destination, binding)
                except (OSError, RuntimeError, TypeError, ValueError):
                    quarantine = self.root / "quarantine"
                    quarantine.mkdir(exist_ok=True)
                    _assert_safe_directory(quarantine)
                    quarantined = quarantine / f"{generation}.{uuid.uuid4().hex}.incomplete"
                    os.replace(destination, quarantined)
                else:
                    raise RuntimeError(f"checkpoint generation already verified: {destination}")
            os.replace(staging, destination)
            manifest_path = destination / "checkpoint_manifest.json"
            verified = self._verify_generation(destination, binding)
            pointer = {
                "schema_version": SCHEMA_VERSION,
                "generation": generation,
                "manifest_sha256": sha256_file(manifest_path),
                "binding_sha256": canonical_sha256(binding),
            }
            _write_json_atomic(self.root / LATEST, pointer)
            self._prune_verified_generations(binding)
            return verified
        except Exception:
            # An incomplete attempt has a unique hidden name and can never collide with resume.
            raise

    def load_latest(self, binding: dict[str, Any]) -> dict[str, Any]:
        pointer_path = self.root / LATEST
        _assert_regular_file(pointer_path, "checkpoint latest pointer")
        pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
        expected_keys = {
            "schema_version",
            "generation",
            "manifest_sha256",
            "binding_sha256",
        }
        if not isinstance(pointer, dict) or set(pointer) != expected_keys:
            raise RuntimeError("checkpoint latest pointer schema differs")
        if pointer["schema_version"] != SCHEMA_VERSION:
            raise RuntimeError("checkpoint latest pointer version differs")
        if pointer["binding_sha256"] != canonical_sha256(binding):
            raise RuntimeError("checkpoint binding differs from requested training configuration")
        generation = pointer["generation"]
        if not isinstance(generation, str) or SNAPSHOT_PATTERN.fullmatch(generation) is None:
            raise RuntimeError("checkpoint generation name is unsafe")
        snapshot = self.snapshots / generation
        manifest_path = snapshot / "checkpoint_manifest.json"
        _assert_regular_file(manifest_path, "checkpoint manifest")
        if sha256_file(manifest_path) != pointer["manifest_sha256"]:
            raise RuntimeError("checkpoint manifest hash differs from latest pointer")
        return self._verify_generation(snapshot, binding)

    def restore_latest(self, destination_root: Path, binding: dict[str, Any]) -> Path:
        """Restore the latest verified run and return its local ``last.pt`` path."""
        manifest = self.load_latest(binding)
        destination_root = destination_root.absolute()
        _assert_safe_directory(destination_root)
        destination_root.mkdir(parents=True, exist_ok=True)
        _assert_safe_directory(destination_root)
        run_dir = destination_root / manifest["run"]
        if run_dir.exists():
            raise RuntimeError(f"resume destination already exists: {run_dir}")
        run_dir.mkdir()
        snapshot = self.snapshots / f"epoch-{manifest['completed_epoch']:04d}"
        for record in manifest["files"]:
            source = snapshot / record["path"]
            restored = _copy_verified_atomic(source, run_dir / record["path"])
            if restored["sha256"] != record["sha256"] or restored["size"] != record["size"]:
                raise RuntimeError(f"restored checkpoint differs: {record['path']}")
        return run_dir / "weights/last.pt"

    def _verify_generation(
        self,
        snapshot: Path,
        expected_binding: dict[str, Any],
        *,
        expected_generation: str | None = None,
    ) -> dict[str, Any]:
        if snapshot.is_symlink() or not snapshot.is_dir():
            raise RuntimeError(f"checkpoint snapshot must be a non-symlink directory: {snapshot}")
        _assert_safe_directory(snapshot / "weights")
        manifest_path = snapshot / "checkpoint_manifest.json"
        _assert_regular_file(manifest_path, "checkpoint manifest")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected_keys = {
            "schema_version",
            "status",
            "run",
            "completed_epoch",
            "binding",
            "binding_sha256",
            "files",
        }
        if not isinstance(manifest, dict) or set(manifest) != expected_keys:
            raise RuntimeError("checkpoint manifest schema differs")
        if manifest["schema_version"] != SCHEMA_VERSION or manifest["status"] != "RECOVERABLE":
            raise RuntimeError("checkpoint manifest identity differs")
        binding_hash = canonical_sha256(expected_binding)
        if manifest["binding"] != expected_binding or manifest["binding_sha256"] != binding_hash:
            raise RuntimeError("checkpoint manifest binding differs")
        if not isinstance(manifest["run"], str) or RUN_PATTERN.fullmatch(manifest["run"]) is None:
            raise RuntimeError("checkpoint run identity differs")
        if (
            type(manifest["completed_epoch"]) is not int
            or manifest["completed_epoch"] < 1
            or manifest["completed_epoch"] > 9999
        ):
            raise RuntimeError("checkpoint completed epoch differs")
        canonical_generation = f"epoch-{manifest['completed_epoch']:04d}"
        generation_differs = (
            canonical_generation != expected_generation
            if expected_generation is not None
            else snapshot.name != canonical_generation
        )
        if generation_differs:
            raise RuntimeError("checkpoint epoch and generation differ")
        if not isinstance(manifest["files"], list):
            raise RuntimeError("checkpoint file roster is not a list")
        roster = {record.get("path") for record in manifest["files"] if isinstance(record, dict)}
        if roster != set(REQUIRED_ARTIFACTS) or len(manifest["files"]) != len(REQUIRED_ARTIFACTS):
            raise RuntimeError("checkpoint file roster differs")
        for record in manifest["files"]:
            if set(record) != {"path", "size", "sha256"}:
                raise RuntimeError("checkpoint file record schema differs")
            path = snapshot / record["path"]
            _assert_regular_file(path, f"checkpoint artifact {record['path']}")
            if path.stat().st_size != record["size"] or sha256_file(path) != record["sha256"]:
                raise RuntimeError(f"checkpoint artifact hash/size differs: {record['path']}")
        return manifest

    def _prune_verified_generations(self, binding: dict[str, Any]) -> None:
        candidates = []
        for path in sorted(self.snapshots.iterdir()):
            if (
                not path.is_dir()
                or path.is_symlink()
                or SNAPSHOT_PATTERN.fullmatch(path.name) is None
            ):
                continue
            try:
                self._verify_generation(path, binding)
            except (OSError, RuntimeError, TypeError, ValueError):
                continue
            candidates.append(path)
        for obsolete in candidates[: -self.retention]:
            shutil.rmtree(obsolete)


def make_ultralytics_callback(
    store: CheckpointStore, binding: dict[str, Any]
):
    """Return an ``on_model_save`` callback that mirrors each completed epoch."""

    def mirror(trainer: Any) -> None:
        store.save(Path(trainer.save_dir), epoch=int(trainer.epoch) + 1, binding=binding)

    return mirror
