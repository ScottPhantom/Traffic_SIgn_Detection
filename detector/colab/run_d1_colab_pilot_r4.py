#!/usr/bin/env python3
"""Pilot R4 post-train repair: package a verified epoch-0100 retry history.

R3 correctly retained failed resume attempts in the durable SQLite/text logs, but
the pinned R1 packager rejected every non-INFO row.  That invariant conflicts
with the retry-aware attempt history: a failed runner invocation legitimately
persists an ERROR row before a later successful resume.  This sidecar keeps the
checkpoint-bound training checkout immutable and narrows the repair to log
validation during a resume from the already-complete epoch-0100 checkpoint.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

EXPECTED_TRAINING_COMMIT = "939f6bbce9f5c955b13ebcc84addd5083d242355"
EXPECTED_FINAL_GENERATION = "epoch-0100"
LOGGER_NAME = "CPV_log_record"
EXPECTED_COLUMNS = ["id", "timestamp", "level", "logger", "message"]
KNOWN_HISTORICAL_ERROR = "D1 resumable Colab workflow failed"


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load pinned Pilot R3 dependency: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _repo_root_from_argv(argv: list[str] | None) -> Path:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--repo-root", type=Path, required=True)
    known, _ = parser.parse_known_args(argv)
    return known.repo_root.expanduser().absolute()


def load_pilot_r3(repo_root: Path) -> Any:
    runner = repo_root / "detector/colab/run_d1_colab_pilot_r3.py"
    if runner.is_symlink() or not runner.is_file():
        raise RuntimeError("pinned Pilot R3 predecessor is missing or linked")
    return _load("d1_pilot_r4_training_commit_pilot_r3", runner)


def _last_index(messages: list[str], token: str) -> int:
    for index in range(len(messages) - 1, -1, -1):
        if token in messages[index]:
            return index
    raise RuntimeError(f"DB_logger.db is missing required final event: {token}")


def _parse_attempt_time(value: Any) -> datetime:
    if not isinstance(value, str):
        raise RuntimeError("failed attempt timestamp is missing")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RuntimeError("failed attempt timestamp lacks an offset")
    return parsed


def _message_time(message: str) -> datetime:
    match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})", message)
    if match is None:
        raise RuntimeError("historical SQLite ERROR row lacks a logger timestamp")
    return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S,%f").replace(tzinfo=UTC)


def _failed_attempt_windows(execution: dict[str, Any]) -> list[tuple[datetime, datetime]]:
    attempts = execution.get("execution_attempts")
    if not isinstance(attempts, list):
        raise RuntimeError("retry-aware execution history is missing")
    windows: list[tuple[datetime, datetime]] = []
    for record in attempts:
        if not isinstance(record, dict) or record.get("status") != "FAILED":
            continue
        windows.append(
            (
                _parse_attempt_time(record.get("started_at")),
                _parse_attempt_time(record.get("finished_at")),
            )
        )
    return windows


def validate_retry_aware_sqlite_log(
    database_path: Path,
    text_log: Path,
    results_csv: Path,
    *,
    execution_path: Path,
) -> None:
    """Validate the final successful lifecycle while retaining earlier failures."""
    if text_log.stat().st_size == 0 or results_csv.stat().st_size == 0:
        raise RuntimeError("Colab text log and results.csv must be non-empty")
    csv_lines = [line for line in results_csv.read_text(encoding="utf-8").splitlines() if line]
    if len(csv_lines) != 101:
        raise RuntimeError("results.csv does not contain exactly 100 completed epochs")
    execution = json.loads(execution_path.read_text(encoding="utf-8"))
    if (
        execution.get("status") != "SUCCEEDED"
        or execution.get("sealed_test_accessed") is not False
        or execution.get("error") is not None
    ):
        raise RuntimeError("execution is not a successful sealed-test-safe retry")
    failed_windows = _failed_attempt_windows(execution)
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
    if [row[1] for row in columns] != EXPECTED_COLUMNS:
        raise RuntimeError("DB_logger.db logs table schema differs")
    if not rows or any(row[2] != LOGGER_NAME for row in rows):
        raise RuntimeError("DB_logger.db contains an unexpected logger")
    messages = [str(row[3]) for row in rows]
    workflow_start = _last_index(messages, "D1 Colab workflow started")
    training_start = _last_index(messages, "Training start")
    training_end = _last_index(messages, "Training end")
    terminal = _last_index(messages, "Terminal outcome SUCCEEDED")
    if not workflow_start < training_start < training_end < terminal:
        raise RuntimeError("final DB_logger.db lifecycle is out of order")
    if any(row[1] != "INFO" for row in rows[workflow_start:]):
        raise RuntimeError("final successful SQLite lifecycle contains a non-INFO record")
    if not any("SUBPROCESS" in message for message in messages[training_start + 1 : training_end]):
        raise RuntimeError("final SQLite lifecycle contains no subprocess evidence")
    for _row_id, level, _logger, message in rows[:workflow_start]:
        if level == "INFO":
            continue
        if level != "ERROR" or KNOWN_HISTORICAL_ERROR not in message:
            raise RuntimeError("historical SQLite lifecycle contains an unexpected record")
        observed = _message_time(message)
        # Attempt records are intentionally second-precision while the logger
        # preserves milliseconds.  Compare at the coarser durable precision;
        # this admits at most the remainder of the same recorded second.
        observed_second = observed.replace(microsecond=0)
        if not any(start <= observed_second <= finish for start, finish in failed_windows):
            raise RuntimeError("historical SQLite ERROR is not bound to a failed attempt")
    text = text_log.read_text(encoding="utf-8")
    final_text = text[text.rfind("D1 Colab workflow started") :]
    if not all(
        token in final_text
        for token in ("Training start", "Training end", "Terminal outcome SUCCEEDED")
    ):
        raise RuntimeError("final text-log lifecycle is incomplete")


def require_final_checkpoint(state_dir: Path, base: Any) -> None:
    latest = base.strict_json(state_dir / "recovery/latest.json")
    if latest.get("generation") != EXPECTED_FINAL_GENERATION:
        raise RuntimeError("Pilot R4 repair requires the completed epoch-0100 checkpoint")
    manifest = state_dir / "recovery/snapshots/epoch-0100/checkpoint_manifest.json"
    if (
        not manifest.is_file()
        or manifest.is_symlink()
        or base.sha256_file(manifest) != latest.get("manifest_sha256")
    ):
        raise RuntimeError("epoch-0100 checkpoint manifest is missing, linked or mismatched")


def main(argv: list[str] | None = None) -> int:
    repo_root = _repo_root_from_argv(argv)
    pilot_r3 = load_pilot_r3(repo_root)
    if pilot_r3._training_commit(repo_root) != EXPECTED_TRAINING_COMMIT:
        raise RuntimeError("training checkout commit differs")
    dependencies = pilot_r3.load_dependencies(repo_root)
    args = dependencies.r1.parser().parse_args(argv)
    pilot_r3._validate_arguments(args)
    state_dir = args.state_dir.expanduser().absolute()
    base = dependencies.r1.base
    require_final_checkpoint(state_dir, base)
    original_validate = base.validate_sqlite_log
    original_strict_json = base.strict_json

    def repaired_validate(database: Path, text_log: Path, results_csv: Path) -> None:
        validate_retry_aware_sqlite_log(
            database,
            text_log,
            results_csv,
            execution_path=state_dir / "colab_execution.json",
        )

    def guarded_strict_json(path: Path) -> Any:
        payload = original_strict_json(path)
        if path.name == "training_outcome.json":
            dependencies.pilot_r2.validate_pilot_outcome(payload, mode="resume")
        return payload

    base.validate_sqlite_log = repaired_validate
    base.strict_json = guarded_strict_json
    try:
        return pilot_r3._run_resume(argv, dependencies)
    finally:
        base.validate_sqlite_log = original_validate
        base.strict_json = original_strict_json


if __name__ == "__main__":
    raise SystemExit(main())
