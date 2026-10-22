from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "detector/colab/run_d1_l4_capacity_r1.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("test_d1_l4_capacity_runner", RUNNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    sys.path.insert(0, str(REPO_ROOT / "detector"))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


runner = load_runner()


def test_gpu_sample_parser_requires_complete_finite_l4_telemetry() -> None:
    sample = runner.parse_gpu_sample("GPU-abc, 91, 12000, 23034, 69.5, 63")
    assert sample["gpu_uuid"] == "GPU-abc"
    assert sample["utilization_percent"] == 91
    assert sample["memory_total_mib"] == 23034
    for malformed in (
        "GPU-abc, 91, 12000, 23034, 69.5",
        "GPU-abc, N/A, 12000, 23034, 69.5, 63",
        "GPU-abc, 101, 12000, 23034, 69.5, 63",
        "not-a-uuid, 91, 12000, 23034, 69.5, 63",
    ):
        with pytest.raises(RuntimeError):
            runner.parse_gpu_sample(malformed)


def test_oom_classifier_does_not_hide_generic_failures() -> None:
    assert runner._oom_error(RuntimeError("CUDA out of memory")) is True
    assert runner._oom_error(RuntimeError("data loader failed")) is False
    assert runner._oom_error(ValueError("bundle hash mismatch")) is False


def test_plan_freezes_full_factorial_roster_before_execution(tmp_path: Path) -> None:
    plan = runner.build_plan(
        repo_root=REPO_ROOT,
        output_dir=tmp_path / "capacity",
        model={"path": "/model.pt", "sha256": "a" * 64},
        data_contract={"export_manifest_sha256": "b" * 64},
        environment={"gpu_name": "NVIDIA L4", "gpu_uuid": "GPU-abc"},
        git_commit="c" * 40,
    )
    assert len(plan["roster"]) == 24
    assert len({row["attempt_id"] for row in plan["roster"]}) == 24
    assert plan["sealed_test_accessed"] is False
    digest = plan.pop("plan_sha256")
    assert runner.l4_capacity.canonical_sha256(plan) == digest


def test_exclusive_writer_refuses_symlink_and_overwrite(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    runner.write_json_exclusive(output, {"status": "first"})
    with pytest.raises(RuntimeError, match="overwrite"):
        runner.write_json_exclusive(output, {"status": "second"})
    target = tmp_path / "outside.json"
    target.write_text("original", encoding="utf-8")
    linked = tmp_path / "linked.json"
    linked.symlink_to(target)
    with pytest.raises(RuntimeError, match="overwrite"):
        runner.write_json_exclusive(linked, {"status": "attack"})
    assert target.read_text(encoding="utf-8") == "original"


def test_strict_json_rejects_duplicate_and_non_finite_values(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"status":1,"status":2}', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        runner.strict_json(duplicate)
    non_finite = tmp_path / "nan.json"
    non_finite.write_text('{"value":NaN}', encoding="utf-8")
    with pytest.raises(ValueError, match="non-finite"):
        runner.strict_json(non_finite)


def test_step_timer_counts_actual_images_after_warmup() -> None:
    torch = pytest.importorskip("torch")
    timer = runner.StepTimer(warmup_batches=1)

    class Trainer:
        batch = {"img": torch.zeros((3, 3, 8, 8))}
        loss = torch.tensor(1.0)

    timer.on_start(Trainer())
    timer.on_end(Trainer())
    timer.on_start(Trainer())
    timer.on_end(Trainer())
    assert timer.observed_batches == 2
    assert len(timer.steps) == 1
    assert timer.steps[0]["images"] == 3
    assert timer.steps[0]["seconds"] > 0


def test_static_surface_has_no_sealed_test_or_final_eval_route() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    assert "export-test" not in text
    assert "--final-eval" not in text
    assert '"val": False' in text
    assert '"sealed_test_accessed": False' in text
    assert "d1_train_pilot_r3" not in text


def test_database_attempts_are_append_only(tmp_path: Path) -> None:
    database = tmp_path / "capacity.db"
    runner.initialize_database(database, "a" * 64)
    attempt = {
        "attempt_id": "b04_w04_r01",
        "batch": 4,
        "workers": 4,
        "repeat": 1,
        "status": "SUCCEEDED",
        "raw_telemetry_sha256": "b" * 64,
    }
    runner.record_attempt(database, attempt, "c" * 64)
    with pytest.raises(runner.sqlite3.IntegrityError):
        runner.record_attempt(database, attempt, "c" * 64)


def test_execution_journal_is_append_only_and_rejects_symlink(tmp_path: Path) -> None:
    journal = tmp_path / "capacity_execution.jsonl"
    runner.append_jsonl(journal, {"status": "STARTED"})
    runner.append_jsonl(journal, {"status": "SUCCEEDED"})
    assert [runner.json.loads(line)["status"] for line in journal.read_text().splitlines()] == [
        "STARTED",
        "SUCCEEDED",
    ]
    outside = tmp_path / "outside.jsonl"
    outside.write_text("unchanged\n", encoding="utf-8")
    linked = tmp_path / "linked.jsonl"
    linked.symlink_to(outside)
    with pytest.raises(RuntimeError, match="regular file"):
        runner.append_jsonl(linked, {"status": "FAILED"})
    assert outside.read_text(encoding="utf-8") == "unchanged\n"


def test_candidate_command_is_token_exact() -> None:
    attempt = {"attempt_id": "b08_w04_r02", "batch": 8, "workers": 4, "repeat": 2}
    command = runner._candidate_command(
        runner=Path("/runner.py"),
        plan_path=Path("/plan.json"),
        plan_sha256="a" * 64,
        attempt=attempt,
    )
    assert command[-8:] == [
        "--attempt-id",
        "b08_w04_r02",
        "--batch",
        "8",
        "--workers",
        "4",
        "--repeat",
        "2",
    ]


def test_writer_does_not_leave_partial_on_encoding_failure(tmp_path: Path) -> None:
    target = tmp_path / "bad.json"
    with pytest.raises(ValueError):
        runner.write_json_exclusive(target, {"bad": float("nan")})
    assert not target.exists()
    assert not any(path.name.endswith(".partial") for path in tmp_path.iterdir())


def test_evidence_package_hashes_files_and_excludes_archive(tmp_path: Path) -> None:
    output = tmp_path / "capacity"
    output.mkdir()
    (output / "capacity.log").write_text("complete\n", encoding="utf-8")
    nested = output / "attempts" / "b04_w04_r01"
    nested.mkdir(parents=True)
    (nested / "result.json").write_text('{"status":"SUCCEEDED"}\n', encoding="utf-8")
    manifest_path, archive_path = runner.package_evidence(
        output,
        plan_sha256="a" * 64,
    )
    manifest = runner.strict_json(manifest_path)
    assert manifest["sealed_test_accessed"] is False
    assert [row["path"] for row in manifest["files"]] == [
        "attempts/b04_w04_r01/result.json",
        "capacity.log",
    ]
    assert archive_path.is_file()
    with runner.tarfile.open(archive_path, "r:gz") as archive:
        assert sorted(archive.getnames()) == [
            "attempts/b04_w04_r01/result.json",
            "capacity.log",
            "capacity_evidence_manifest.json",
        ]
