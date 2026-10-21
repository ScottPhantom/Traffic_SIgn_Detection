from __future__ import annotations

import hashlib
import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = REPO_ROOT / "detector/colab/run_d1_colab_pilot_r4.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("test_d1_pilot_r4_runner", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


runner = load_runner()


def test_load_pilot_r3_uses_hash_pinned_sibling_not_training_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sidecar_dir = tmp_path / "sidecars"
    sidecar_dir.mkdir()
    r4_path = sidecar_dir / "run_d1_colab_pilot_r4.py"
    r4_path.write_text("# test R4 sidecar\n", encoding="utf-8")
    r3_path = sidecar_dir / "run_d1_colab_pilot_r3.py"
    r3_bytes = b"# hash-pinned R3 sidecar\n"
    r3_path.write_bytes(r3_bytes)
    empty_training_checkout = tmp_path / "training-checkout"
    empty_training_checkout.mkdir()
    captured: dict[str, object] = {}

    def fake_load(name: str, path: Path) -> object:
        captured.update(name=name, path=path)
        return "pilot-r3"

    monkeypatch.setattr(runner, "__file__", str(r4_path))
    monkeypatch.setattr(runner, "PILOT_R3_SHA256", hashlib.sha256(r3_bytes).hexdigest())
    monkeypatch.setattr(runner, "_load", fake_load)

    assert runner.load_pilot_r3(empty_training_checkout) == "pilot-r3"
    assert captured == {"name": "d1_pilot_r4_sidecar_pilot_r3", "path": r3_path}


def test_load_pilot_r3_rejects_unpinned_sibling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    r4_path = tmp_path / "run_d1_colab_pilot_r4.py"
    r4_path.write_text("# test R4 sidecar\n", encoding="utf-8")
    (tmp_path / "run_d1_colab_pilot_r3.py").write_text(
        "# tampered R3 sidecar\n", encoding="utf-8"
    )
    monkeypatch.setattr(runner, "__file__", str(r4_path))

    with pytest.raises(RuntimeError, match="hash differs"):
        runner.load_pilot_r3(tmp_path / "training-checkout")


def write_log_db(path: Path, rows: list[tuple[str, str]]) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE logs (id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, level TEXT, logger TEXT, message TEXT)"
        )
        connection.executemany(
            "INSERT INTO logs(level, logger, message) VALUES (?, ?, ?)",
            [(level, runner.LOGGER_NAME, message) for level, message in rows],
        )


def execution(path: Path, *, include_packaging_failure: bool = False) -> None:
    attempts = [
        {
            "status": "FAILED",
            "started_at": "2026-10-21T07:00:00+00:00",
            "finished_at": "2026-10-21T07:13:10+00:00",
        }
    ]
    if include_packaging_failure:
        attempts.append(
            {
                "status": "FAILED",
                "started_at": "2026-10-21T08:05:38+00:00",
                "finished_at": "2026-10-21T12:15:48+00:00",
            }
        )
    attempts.append(
        {
            "status": "SUCCEEDED",
            "started_at": "2026-10-21T12:30:00+00:00",
            "finished_at": "2026-10-21T12:31:00+00:00",
        }
    )
    path.write_text(
        json.dumps(
            {
                "status": "SUCCEEDED",
                "sealed_test_accessed": False,
                "error": None,
                "execution_attempts": attempts,
            }
        ),
        encoding="utf-8",
    )


def valid_rows() -> list[tuple[str, str]]:
    return [
        (
            "ERROR",
            "2026-10-21 07:13:10,627 - ERROR - D1 resumable Colab workflow failed",
        ),
        ("INFO", "2026-10-21 12:15:00,000 - INFO - D1 Colab workflow started"),
        ("INFO", "2026-10-21 12:15:01,000 - INFO - Training start"),
        ("INFO", "2026-10-21 12:15:02,000 - INFO - SUBPROCESS completed_epoch=100"),
        ("INFO", "2026-10-21 12:15:03,000 - INFO - Training end"),
        (
            "INFO",
            "2026-10-21 12:15:04,000 - INFO - Terminal outcome SUCCEEDED; "
            "validated result packaging begins",
        ),
    ]


def artifacts(tmp_path: Path, rows: list[tuple[str, str]] | None = None):
    database = tmp_path / "DB_logger.db"
    text = tmp_path / "colab_train.log"
    results = tmp_path / "results.csv"
    execution_path = tmp_path / "colab_execution.json"
    selected = valid_rows() if rows is None else rows
    write_log_db(database, selected)
    text.write_text("\n".join(message for _, message in selected), encoding="utf-8")
    results.write_text("epoch,metric\n" + "\n".join(f"{i},0.5" for i in range(100)) + "\n")
    execution(execution_path)
    return database, text, results, execution_path


def test_retry_log_accepts_bound_historical_failure_and_final_success(tmp_path: Path) -> None:
    database, text, results, execution_path = artifacts(tmp_path)
    runner.validate_retry_aware_sqlite_log(
        database, text, results, execution_path=execution_path
    )


def test_real_drive_millisecond_error_boundaries_are_normalized_to_attempt_seconds(
    tmp_path: Path,
) -> None:
    rows = [
        (
            "ERROR",
            "2026-10-21 07:13:10,627 - ERROR - D1 resumable Colab workflow failed",
        ),
        (
            "ERROR",
            "2026-10-21 12:15:48,448 - ERROR - D1 resumable Colab workflow failed",
        ),
        *valid_rows()[1:],
    ]
    database, text, results, execution_path = artifacts(tmp_path, rows)
    execution(execution_path, include_packaging_failure=True)
    runner.validate_retry_aware_sqlite_log(
        database, text, results, execution_path=execution_path
    )


@pytest.mark.parametrize(
    "mutation,match",
    [
        ("late_error", "final successful"),
        ("unbound_error", "not bound"),
        ("warning", "unexpected record"),
        ("missing_subprocess", "no subprocess"),
    ],
)
def test_retry_log_rejects_unbound_or_current_lifecycle_errors(
    tmp_path: Path, mutation: str, match: str
) -> None:
    rows = valid_rows()
    if mutation == "late_error":
        rows.insert(-1, ("ERROR", "2026-10-21 12:15:03,500 - ERROR - current failure"))
    elif mutation == "unbound_error":
        rows[0] = (
            "ERROR",
            "2026-10-21 06:13:10,627 - ERROR - D1 resumable Colab workflow failed",
        )
    elif mutation == "warning":
        rows[0] = ("WARNING", "2026-10-21 07:13:10,627 - WARNING - drift")
    else:
        rows = [row for row in rows if "SUBPROCESS" not in row[1]]
    database, text, results, execution_path = artifacts(tmp_path, rows)
    with pytest.raises(RuntimeError, match=match):
        runner.validate_retry_aware_sqlite_log(
            database, text, results, execution_path=execution_path
        )


def test_final_checkpoint_requires_bound_epoch_0100_manifest(tmp_path: Path) -> None:
    state = tmp_path / "state"
    snapshot = state / "recovery/snapshots/epoch-0100"
    snapshot.mkdir(parents=True)
    manifest = snapshot / "checkpoint_manifest.json"
    manifest.write_text("{}", encoding="utf-8")
    latest = state / "recovery/latest.json"
    latest.write_text(
        json.dumps({"generation": "epoch-0100", "manifest_sha256": "good"}),
        encoding="utf-8",
    )

    class Base:
        strict_json = staticmethod(lambda path: json.loads(path.read_text()))
        sha256_file = staticmethod(lambda _path: "good")

    runner.require_final_checkpoint(state, Base)
    latest.write_text(
        json.dumps({"generation": "epoch-0099", "manifest_sha256": "good"}),
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="epoch-0100"):
        runner.require_final_checkpoint(state, Base)
