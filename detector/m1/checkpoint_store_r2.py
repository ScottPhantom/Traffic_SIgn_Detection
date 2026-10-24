"""Bounded-I/O checkpoint successor for future Colab training runs.

The legacy store is intentionally left unchanged because completed and active
runs bind its bytes.  This successor keeps the same crash-safe snapshot format
but fixes retention at two verified generations and records small chained I/O
telemetry.  Consequently the amount of historical model data re-hashed by one
save is bounded instead of growing with the epoch number.
"""

from __future__ import annotations

import json
import math
import os
import stat
import time
from pathlib import Path
from typing import Any

from m1 import checkpoint_store as legacy

SCHEMA_VERSION = 2
RETENTION = 2
TELEMETRY_NAME = "checkpoint_io.jsonl"
TELEMETRY_KEYS = {
    "schema_version",
    "epoch",
    "generation",
    "manifest_sha256",
    "binding_sha256",
    "retention",
    "snapshot_count_after_prune",
    "checkpoint_io_seconds",
    "sealed_test_accessed",
    "previous_event_sha256",
    "event_sha256",
}


def _event_hash(event: dict[str, Any]) -> str:
    payload = {key: value for key, value in event.items() if key != "event_sha256"}
    return legacy.canonical_sha256(payload)


def _read_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists() and not path.is_symlink():
        return []
    legacy._assert_regular_file(path, "checkpoint I/O telemetry")
    if path.stat().st_nlink != 1:
        raise RuntimeError("checkpoint I/O telemetry must have exactly one link")
    events: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.endswith("\n"):
                raise RuntimeError("checkpoint I/O telemetry has a partial final line")
            try:
                event = json.loads(line)
            except json.JSONDecodeError as error:
                raise RuntimeError(
                    f"checkpoint I/O telemetry line {line_number} is invalid JSON"
                ) from error
            if not isinstance(event, dict) or set(event) != TELEMETRY_KEYS:
                raise RuntimeError("checkpoint I/O telemetry schema differs")
            events.append(event)
    return events


def _validate_events(
    events: list[dict[str, Any]], *, binding_sha256: str
) -> list[dict[str, Any]]:
    previous_hash: str | None = None
    previous_epoch: int | None = None
    for event in events:
        if type(event["schema_version"]) is not int or event["schema_version"] != SCHEMA_VERSION:
            raise RuntimeError("checkpoint I/O telemetry version differs")
        if type(event["epoch"]) is not int or event["epoch"] < 1:
            raise RuntimeError("checkpoint I/O telemetry epoch is invalid")
        if previous_epoch is not None and event["epoch"] != previous_epoch + 1:
            raise RuntimeError("checkpoint I/O telemetry epochs are not contiguous")
        if event["generation"] != f"epoch-{event['epoch']:04d}":
            raise RuntimeError("checkpoint I/O telemetry generation differs")
        for key in ("manifest_sha256", "binding_sha256", "event_sha256"):
            value = event[key]
            if (
                not isinstance(value, str)
                or len(value) != 64
                or any(character not in "0123456789abcdef" for character in value)
            ):
                raise RuntimeError(f"checkpoint I/O telemetry {key} is malformed")
        if event["binding_sha256"] != binding_sha256:
            raise RuntimeError("checkpoint I/O telemetry binding differs")
        if type(event["retention"]) is not int or event["retention"] != RETENTION:
            raise RuntimeError("checkpoint I/O telemetry retention differs")
        count = event["snapshot_count_after_prune"]
        if type(count) is not int or count < 1 or count > RETENTION:
            raise RuntimeError("checkpoint I/O telemetry snapshot count differs")
        seconds = event["checkpoint_io_seconds"]
        if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 0:
            raise RuntimeError("checkpoint I/O telemetry duration is invalid")
        if type(event["sealed_test_accessed"]) is not bool:
            raise RuntimeError("checkpoint I/O telemetry seal marker must be boolean")
        if event["sealed_test_accessed"] is not False:
            raise RuntimeError("checkpoint I/O telemetry indicates sealed-test access")
        if event["previous_event_sha256"] != previous_hash:
            raise RuntimeError("checkpoint I/O telemetry hash chain differs")
        if event["event_sha256"] != _event_hash(event):
            raise RuntimeError("checkpoint I/O telemetry event hash differs")
        previous_hash = event["event_sha256"]
        previous_epoch = event["epoch"]
    return events


def _append_event(path: Path, event: dict[str, Any]) -> None:
    legacy.require_safe_directory(path.parent, create=True)
    before: os.stat_result | None = None
    if path.exists() or path.is_symlink():
        legacy._assert_regular_file(path, "checkpoint I/O telemetry")
        before = path.lstat()
        if before.st_nlink != 1:
            raise RuntimeError("checkpoint I/O telemetry must have exactly one link")
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
            raise RuntimeError("checkpoint I/O telemetry descriptor is unsafe")
        if before is not None and (opened.st_dev, opened.st_ino) != (
            before.st_dev,
            before.st_ino,
        ):
            raise RuntimeError("checkpoint I/O telemetry changed before append")
        payload = (
            json.dumps(event, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
        ).encode("utf-8")
        remaining = memoryview(payload)
        while remaining:
            written = os.write(descriptor, remaining)
            if written <= 0:
                raise RuntimeError("checkpoint I/O telemetry append was incomplete")
            remaining = remaining[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


class EfficientCheckpointStore(legacy.CheckpointStore):
    """Legacy-compatible store with constant-size recovery history."""

    def __init__(self, root: Path) -> None:
        super().__init__(root, retention=RETENTION)
        self.telemetry_path = self.root / TELEMETRY_NAME

    def save(self, run_dir: Path, *, epoch: int, binding: dict[str, Any]) -> dict[str, Any]:
        if binding.get("sealed_test_accessed") is not False:
            raise RuntimeError("future-run binding must keep sealed_test_accessed=false")
        binding_hash = legacy.canonical_sha256(binding)
        prior = _validate_events(_read_events(self.telemetry_path), binding_sha256=binding_hash)
        if prior and epoch <= prior[-1]["epoch"]:
            raise RuntimeError("checkpoint I/O telemetry refuses a repeated or older epoch")
        if prior and epoch != prior[-1]["epoch"] + 1:
            raise RuntimeError("checkpoint I/O telemetry refuses an epoch gap")
        started = time.monotonic()
        manifest = super().save(run_dir, epoch=epoch, binding=binding)
        duration = time.monotonic() - started
        pointer = json.loads((self.root / legacy.LATEST).read_text(encoding="utf-8"))
        snapshot_count = sum(
            1
            for path in self.snapshots.iterdir()
            if (
                path.is_dir()
                and not path.is_symlink()
                and legacy.SNAPSHOT_PATTERN.fullmatch(path.name)
            )
        )
        event = {
            "schema_version": SCHEMA_VERSION,
            "epoch": epoch,
            "generation": pointer["generation"],
            "manifest_sha256": pointer["manifest_sha256"],
            "binding_sha256": binding_hash,
            "retention": RETENTION,
            "snapshot_count_after_prune": snapshot_count,
            "checkpoint_io_seconds": duration,
            "sealed_test_accessed": False,
            "previous_event_sha256": prior[-1]["event_sha256"] if prior else None,
            "event_sha256": "",
        }
        event["event_sha256"] = _event_hash(event)
        _append_event(self.telemetry_path, event)
        return manifest

    def verify_telemetry(self, binding: dict[str, Any]) -> list[dict[str, Any]]:
        """Verify the complete small history and bind its tail to ``latest.json``."""
        binding_hash = legacy.canonical_sha256(binding)
        events = _validate_events(_read_events(self.telemetry_path), binding_sha256=binding_hash)
        if not events:
            raise RuntimeError("checkpoint I/O telemetry is empty")
        pointer = json.loads((self.root / legacy.LATEST).read_text(encoding="utf-8"))
        tail = events[-1]
        if (
            tail["generation"] != pointer["generation"]
            or tail["manifest_sha256"] != pointer["manifest_sha256"]
            or tail["binding_sha256"] != pointer["binding_sha256"]
        ):
            raise RuntimeError("checkpoint I/O telemetry tail differs from latest pointer")
        self.load_latest(binding)
        return events

    def restore_latest(
        self, destination_root: Path, binding: dict[str, Any]
    ) -> Path:
        """Refuse restore before copying bytes when the chained I/O ledger is invalid."""
        self.verify_telemetry(binding)
        return super().restore_latest(destination_root, binding)


def make_ultralytics_callback(
    store: EfficientCheckpointStore, binding: dict[str, Any]
):
    """Return the future-run callback without changing the active legacy runner."""

    def mirror(trainer: Any) -> None:
        store.save(Path(trainer.save_dir), epoch=int(trainer.epoch) + 1, binding=binding)

    return mirror
