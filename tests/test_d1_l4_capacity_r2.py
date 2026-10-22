from __future__ import annotations

import importlib
import json
import sqlite3
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
COLAB_ROOT = REPO_ROOT / "detector/colab"
DETECTOR_ROOT = REPO_ROOT / "detector"
for import_root in (DETECTOR_ROOT, COLAB_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

r2 = importlib.import_module("run_d1_l4_capacity_r2")
verifier = importlib.import_module("verify_d1_l4_capacity_r2")


class ImageBatch:
    def __init__(self, images: int) -> None:
        self.shape = (images, 3, 8, 8)


class Trainer:
    def __init__(self, *, images: int, batch_size: int) -> None:
        self.batch = {"img": ImageBatch(images)}
        self.batch_size = batch_size
        self.loss = None


def test_timer_includes_inter_batch_loader_gap(monkeypatch: pytest.MonkeyPatch) -> None:
    clock = iter((1.0, 2.0, 5.0, 7.0))
    monkeypatch.setattr(r2.time, "perf_counter", lambda: next(clock))
    timer = r2.StepTimer(warmup_batches=0, planned_batch=8)
    trainer = Trainer(images=8, batch_size=8)
    timer.on_start(trainer)
    timer.on_end(trainer)
    timer.on_start(trainer)
    timer.on_end(trainer)
    assert timer.steps[0]["seconds"] == 1.0
    assert timer.steps[1]["compute_seconds"] == 2.0
    assert timer.steps[1]["inter_batch_gap_seconds"] == 3.0
    assert timer.steps[1]["seconds"] == 5.0


def test_timer_rejects_ultralytics_auto_batch_reduction() -> None:
    timer = r2.StepTimer(warmup_batches=0, planned_batch=16)
    with pytest.raises(RuntimeError, match="changed the effective batch"):
        timer.on_start(Trainer(images=8, batch_size=8))


def test_effective_batch_replay_requires_full_planned_batch() -> None:
    telemetry = {
        "steps": [
            {
                "batch_index": 11,
                "images": 4,
                "seconds": 1.2,
                "compute_seconds": 1.0,
                "inter_batch_gap_seconds": 0.2,
                "planned_batch": 16,
                "trainer_batch_size": 16,
            }
        ]
    }
    with pytest.raises(RuntimeError, match="no full planned batch"):
        r2.validate_effective_batch(telemetry, planned_batch=16)


@pytest.mark.parametrize(
    ("exception_type", "message", "expected"),
    (
        ("OutOfMemoryError", "allocation failed", True),
        ("RuntimeError", "CUDA out of memory", True),
        ("RuntimeError", "data loader failed", False),
        ("ValueError", "bundle hash mismatch", False),
    ),
)
def test_oom_allowlist_is_fail_closed(
    exception_type: str, message: str, expected: bool
) -> None:
    assert r2.is_cuda_oom(exception_type=exception_type, message=message) is expected


def test_sqlite_writer_rejects_file_symlink_and_hardlink(tmp_path: Path) -> None:
    governed = tmp_path / "capacity.db"
    r2.initialize_database(governed, "a" * 64)
    outside = tmp_path / "outside.db"
    governed.replace(outside)
    governed.symlink_to(outside)
    attempt = {
        "attempt_id": "b04_w04_r01",
        "batch": 4,
        "workers": 4,
        "repeat": 1,
        "status": "SUCCEEDED",
        "raw_telemetry_sha256": "b" * 64,
    }
    with pytest.raises(RuntimeError, match="non-symlink"):
        r2.record_attempt(governed, attempt, "c" * 64)
    with sqlite3.connect(outside) as connection:
        assert connection.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 0

    governed.unlink()
    governed.hardlink_to(outside)
    with pytest.raises(RuntimeError, match="one hard link"):
        r2.record_attempt(governed, attempt, "c" * 64)


def test_execution_rejects_duplicate_sealed_marker(tmp_path: Path) -> None:
    journal = tmp_path / "capacity_execution.jsonl"
    journal.write_text(
        "\n".join(
            (
                '{"schema_version":1,"status":"STARTED","started_at":"2026-10-21T01:00:00+00:00","plan_sha256":"p","sealed_test_accessed":true,"sealed_test_accessed":false}',
                '{"schema_version":1,"status":"SUCCEEDED","finished_at":"2026-10-21T01:01:00+00:00","plan_sha256":"p","report_sha256":"r","sealed_test_accessed":false}',
            )
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate JSON key"):
        verifier.verify_execution(journal, plan_sha256="p", report_sha256="r")


@pytest.mark.parametrize(
    ("started", "finished"),
    (
        ("x", "2026-10-21T01:01:00+00:00"),
        ("2026-10-21T01:00:00", "2026-10-21T01:01:00+00:00"),
        ("2026-10-21T01:02:00+00:00", "2026-10-21T01:01:00+00:00"),
    ),
)
def test_execution_rejects_bad_timestamp_or_chronology(
    tmp_path: Path, started: str, finished: str
) -> None:
    journal = tmp_path / "capacity_execution.jsonl"
    rows = (
        {
            "schema_version": 1,
            "status": "STARTED",
            "started_at": started,
            "plan_sha256": "p",
            "sealed_test_accessed": False,
        },
        {
            "schema_version": 1,
            "status": "SUCCEEDED",
            "finished_at": finished,
            "plan_sha256": "p",
            "report_sha256": "r",
            "sealed_test_accessed": False,
        },
    )
    journal.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    with pytest.raises(RuntimeError):
        verifier.verify_execution(journal, plan_sha256="p", report_sha256="r")


def test_verifier_rejects_extra_training_argument(tmp_path: Path) -> None:
    attempt = {"attempt_id": "b04_w04_r01", "batch": 4, "workers": 4, "repeat": 1}
    attempt_dir = tmp_path / "attempts" / attempt["attempt_id"]
    attempt_dir.mkdir(parents=True)
    (attempt_dir / "result.json").write_text('{"status":"SUCCEEDED"}', encoding="utf-8")
    (attempt_dir / "raw_telemetry.json").write_text(
        json.dumps({"train_args": {"forged_extra_optimizer": "SGD"}}),
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="train-argument schema"):
        verifier.verify_attempt_hardening(
            tmp_path,
            attempt=attempt,
            plan={"environment": {"gpu_uuid": "GPU-test"}},
        )


def test_verifier_rejects_nonexistent_git_anchor() -> None:
    with pytest.raises(verifier.subprocess.CalledProcessError):
        verifier.verify_independent_anchors(
            {
                "repo_root": str(REPO_ROOT),
                "git_commit": "f" * 40,
                "model": {"path": "unused"},
                "data_contract": {},
                "environment": {},
            }
        )


def test_verifier_rejects_alternate_repository_root(tmp_path: Path) -> None:
    tmp_path.mkdir(exist_ok=True)
    with pytest.raises(RuntimeError, match="repository root differs"):
        verifier.verify_independent_anchors(
            {
                "repo_root": str(tmp_path),
                "git_commit": "f" * 40,
                "model": {"path": "unused"},
                "data_contract": {},
                "environment": {},
            }
        )


def test_r2_source_has_no_sealed_test_or_pilot_route() -> None:
    source = (COLAB_ROOT / "run_d1_l4_capacity_r2.py").read_text(encoding="utf-8")
    assert "export-test" not in source
    assert "--final-eval" not in source
    assert "pilot_r3" not in source
