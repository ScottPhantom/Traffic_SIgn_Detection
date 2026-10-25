from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load_runner() -> Any:
    path = ROOT / "detector/colab/run_yolo11n_n54_r1.py"
    spec = importlib.util.spec_from_file_location("test_yolo11n_n54_runner", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


runner = load_runner()


def argv(tmp_path: Path, *, mode: str, stop: int | None) -> list[str]:
    values = [
        "--repo-root",
        str(tmp_path / "repo"),
        "--bundle",
        str(tmp_path / "bundle.tar.gz"),
        "--bundle-sha256",
        "a" * 64,
        "--state-dir",
        str(tmp_path / runner.EXPECTED_STATE_SUFFIX),
        "--mode",
        mode,
        "--expected-checkout",
        "b" * 40,
        "--source-qa-record",
        str(tmp_path / "source_qa.md"),
        "--source-qa-sha256",
        "c" * 64,
        "--cos-lr",
    ]
    if stop is not None:
        values.extend(("--stop-after-epoch", str(stop)))
    return values


@pytest.mark.parametrize(
    ("mode", "stop", "leg"),
    (
        ("fresh", 1, "fresh_epoch_1"),
        ("resume", 2, "resume_epoch_2"),
        ("resume", None, "long_resume"),
    ),
)
def test_n54_three_legs_are_exact(
    tmp_path: Path, mode: str, stop: int | None, leg: str
) -> None:
    args = runner.parser().parse_args(argv(tmp_path, mode=mode, stop=stop))
    assert runner.validate_frozen(args) == leg
    assert args.epochs == 100
    assert args.batch == 4
    assert args.cos_lr is True


@pytest.mark.parametrize(("mode", "stop"), (("fresh", None), ("fresh", 2), ("resume", 1)))
def test_n54_rejects_invalid_leg(tmp_path: Path, mode: str, stop: int | None) -> None:
    args = runner.parser().parse_args(argv(tmp_path, mode=mode, stop=stop))
    with pytest.raises(RuntimeError, match="fresh-1, resume-2, or long-resume"):
        runner.validate_frozen(args)


def test_n54_state_and_binding_are_isolated(tmp_path: Path) -> None:
    args = runner.parser().parse_args(argv(tmp_path, mode="fresh", stop=1))
    state = runner.normalized_state(args.state_dir)
    assert state.as_posix().endswith(runner.EXPECTED_STATE_SUFFIX)
    first_binding = runner.run_binding(args)
    assert len(first_binding) == 64
    other = runner.parser().parse_args(argv(tmp_path / "other", mode="fresh", stop=1))
    assert runner.run_binding(other) != first_binding
    args.state_dir = tmp_path / "wrong"
    with pytest.raises(RuntimeError, match="requires Drive state suffix"):
        runner.normalized_state(args.state_dir)


def test_n54_train_commands_preserve_smoke_and_long_modes(tmp_path: Path) -> None:
    model = tmp_path / "yolo11n.pt"
    state = tmp_path / "state"
    fresh = runner.parser().parse_args(argv(tmp_path, mode="fresh", stop=1))
    resume = runner.parser().parse_args(argv(tmp_path, mode="resume", stop=2))
    long = runner.parser().parse_args(argv(tmp_path, mode="resume", stop=None))
    fresh_command = runner.build_train_command(fresh, model, state)
    resume_command = runner.build_train_command(resume, model, state)
    long_command = runner.build_train_command(long, model, state)
    assert "m1.resumable_train_n54_r1" in fresh_command
    assert fresh_command[-2:] == ["--stop-after-epoch", "1"]
    assert resume_command[-3:] == ["--resume", "--stop-after-epoch", "2"]
    assert long_command[-1] == "--resume"
    assert "--stop-after-epoch" not in long_command


def test_n54_attempt_sequence_requires_distinct_runtimes(tmp_path: Path) -> None:
    args = runner.parser().parse_args(argv(tmp_path, mode="resume", stop=None))
    binding = runner.run_binding(args)
    attempts = [
        {
            "leg": "fresh_epoch_1",
            "status": "PAUSED_FOR_RESUME",
            "completed_epoch": 1,
            "run_binding_sha256": binding,
            "runtime_digest": "1" * 64,
            "sealed_test_accessed": False,
        },
        {
            "leg": "resume_epoch_2",
            "status": "PAUSED_FOR_RESUME",
            "completed_epoch": 2,
            "run_binding_sha256": binding,
            "runtime_digest": "2" * 64,
            "sealed_test_accessed": False,
        },
    ]
    runner.validate_attempts(attempts, "long_resume", "3" * 64, binding)
    with pytest.raises(RuntimeError, match="distinct runtime"):
        runner.validate_attempts(attempts, "long_resume", "2" * 64, binding)
    attempts.append(
        {
            "leg": "long_resume",
            "status": "FAILED",
            "completed_epoch": 100,
            "run_binding_sha256": binding,
            "runtime_digest": "3" * 64,
            "sealed_test_accessed": False,
        }
    )
    runner.validate_attempts(attempts, "long_resume", "4" * 64, binding)


def test_n54_smoke_proof_is_bound_to_epoch_2_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = tmp_path / "state"
    (state / "recovery").mkdir(parents=True)
    latest = state / "recovery/latest.json"
    latest.write_text('{"generation":"epoch-0002"}\n', encoding="utf-8")
    binding = "4" * 64
    attempts = [
        {"runtime_digest": "1" * 64},
        {"runtime_digest": "2" * 64},
    ]
    payload = {
        "schema": "yolo11n-n54-r1-smoke-qa-v1",
        "package": runner.PACKAGE,
        "verdict": "PASS",
        "bundle_sha256": "a" * 64,
        "run_binding_sha256": binding,
        "state_path_sha256": hashlib.sha256(str(state).encode()).hexdigest(),
        "checkpoint_epoch": 2,
        "checkpoint_latest_sha256": hashlib.sha256(latest.read_bytes()).hexdigest(),
        "runtime_digests": ["1" * 64, "2" * 64],
        "sealed_test_accessed": False,
    }
    proof = tmp_path / "proof.json"
    proof.write_text(json.dumps(payload), encoding="utf-8")
    digest = hashlib.sha256(proof.read_bytes()).hexdigest()
    monkeypatch.setattr(
        runner,
        "verify_epoch_2_checkpoint",
        lambda _state: hashlib.sha256(latest.read_bytes()).hexdigest(),
    )
    runner.require_smoke_qa(
        proof,
        digest,
        attempts=attempts,
        binding=binding,
        bundle_sha256="a" * 64,
        state=state,
    )
    replay_state = tmp_path / "other" / "state"
    with pytest.raises(RuntimeError, match="does not bind"):
        runner.require_smoke_qa(
            proof,
            digest,
            attempts=attempts,
            binding=binding,
            bundle_sha256="a" * 64,
            state=replay_state,
        )
    payload["checkpoint_epoch"] = 1
    proof.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(RuntimeError, match="does not bind"):
        runner.require_smoke_qa(
            proof,
            hashlib.sha256(proof.read_bytes()).hexdigest(),
            attempts=attempts,
            binding=binding,
            bundle_sha256="a" * 64,
            state=state,
        )


def test_n54_failed_long_attempt_can_reuse_two_leg_smoke_proof(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = tmp_path / "state"
    (state / "recovery").mkdir(parents=True)
    latest = state / "recovery/latest.json"
    latest.write_text('{"generation":"epoch-0002"}\n', encoding="utf-8")
    args = runner.parser().parse_args(argv(tmp_path, mode="resume", stop=None))
    binding = runner.run_binding(args)
    attempts = [
        {
            "leg": "fresh_epoch_1",
            "status": "PAUSED_FOR_RESUME",
            "completed_epoch": 1,
            "run_binding_sha256": binding,
            "runtime_digest": "1" * 64,
            "sealed_test_accessed": False,
        },
        {
            "leg": "resume_epoch_2",
            "status": "PAUSED_FOR_RESUME",
            "completed_epoch": 2,
            "run_binding_sha256": binding,
            "runtime_digest": "2" * 64,
            "sealed_test_accessed": False,
        },
        {
            "leg": "long_resume",
            "status": "FAILED",
            "completed_epoch": 100,
            "run_binding_sha256": binding,
            "runtime_digest": "3" * 64,
            "sealed_test_accessed": False,
        },
    ]
    runner.validate_attempts(attempts, "long_resume", "4" * 64, binding)
    payload = {
        "schema": "yolo11n-n54-r1-smoke-qa-v1",
        "package": runner.PACKAGE,
        "verdict": "PASS",
        "bundle_sha256": "a" * 64,
        "run_binding_sha256": binding,
        "state_path_sha256": hashlib.sha256(str(state).encode()).hexdigest(),
        "checkpoint_epoch": 2,
        "checkpoint_latest_sha256": hashlib.sha256(latest.read_bytes()).hexdigest(),
        "runtime_digests": ["1" * 64, "2" * 64],
        "sealed_test_accessed": False,
    }
    proof = tmp_path / "proof-retry.json"
    proof.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(
        runner,
        "verify_epoch_2_checkpoint",
        lambda _state: hashlib.sha256(latest.read_bytes()).hexdigest(),
    )
    runner.require_smoke_qa(
        proof,
        hashlib.sha256(proof.read_bytes()).hexdigest(),
        attempts=attempts,
        binding=binding,
        bundle_sha256="a" * 64,
        state=state,
    )


def test_n54_checkpoint_pointer_must_be_epoch_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = tmp_path / "state"
    (state / "recovery").mkdir(parents=True)
    latest = state / "recovery/latest.json"
    latest.write_text(
        json.dumps({"generation": "epoch-0001", "binding_sha256": "a" * 64}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        runner.r2,
        "verify_current_checkpoint",
        lambda *_args: {"completed_epoch": 2},
    )
    with pytest.raises(RuntimeError, match="not generation epoch-0002"):
        runner.verify_epoch_2_checkpoint(state)
    latest.write_text(
        json.dumps({"generation": "epoch-0002", "binding_sha256": "a" * 64}),
        encoding="utf-8",
    )
    assert runner.verify_epoch_2_checkpoint(state) == hashlib.sha256(
        latest.read_bytes()
    ).hexdigest()


def test_n54_requires_exact_l4(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            stdout="NVIDIA L4, GPU-123, 580.82.07\n"
        ),
    )
    assert runner.require_l4()["name"] == "NVIDIA L4"
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            stdout="NVIDIA A100-SXM4-40GB, GPU-123, 580.82.07\n"
        ),
    )
    with pytest.raises(RuntimeError, match="NVIDIA L4"):
        runner.require_l4()


def test_n54_accepts_terminal_checkpoint_recovery() -> None:
    assert (
        runner.validate_outcome(
            {"status": "COMPLETED_FROM_FINAL_CHECKPOINT", "completed_epoch": 100},
            None,
        )
        == 100
    )
    with pytest.raises(RuntimeError, match="outcome differs"):
        runner.validate_outcome({"status": "COMPLETED_EARLY_STOPPED", "completed_epoch": 80}, None)


def test_n54_result_package_is_atomic_and_retryable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = tmp_path / "state"
    run = tmp_path / "run"
    (run / "weights").mkdir(parents=True)
    (run / "weights/best.pt").write_bytes(b"best")
    (run / "weights/last.pt").write_bytes(b"last")
    (run / "results.csv").write_text("epoch,loss\n1,0.1\n", encoding="utf-8")
    (run / "args.yaml").write_text("epochs: 100\n", encoding="utf-8")
    (run / "run_contract.json").write_text(
        json.dumps(
            {
                "experiment": runner.EXPERIMENT,
                "owner_decision_sha256": runner.OWNER_DECISION_SHA256,
                "model": {"sha256": runner.WEIGHT_SHA256},
                "status": "TRAINED",
                "environment": {"runtime_backend": "cuda"},
            }
        ),
        encoding="utf-8",
    )
    state.mkdir()
    execution = state / "colab_execution.json"
    text_log = state / "colab_train.log"
    database = state / "DB_logger.db"
    execution.write_text('{"status":"SUCCEEDED"}\n', encoding="utf-8")
    text_log.write_text("log\n", encoding="utf-8")
    database.write_bytes(b"sqlite")
    monkeypatch.setattr(runner.r1.base, "validate_sqlite_log", lambda *_args: None)
    first = runner.package_result(state, run, execution, text_log, database)
    assert Path(first["archive"]).is_file()
    assert Path(first["manifest"]).is_file()
    assert runner.package_result(state, run, execution, text_log, database) == first
    execution.write_text('{"status":"SUCCEEDED","retry":true}\n', encoding="utf-8")
    recovered = runner.package_result(state, run, execution, text_log, database)
    assert recovered["archive_sha256"] != first["archive_sha256"]
    assert any((state / "results/quarantine").iterdir())


def test_n54_source_has_no_sealed_test_route() -> None:
    source = (ROOT / "detector/colab/run_yolo11n_n54_r1.py").read_text(encoding="utf-8")
    assert "export-test" not in source
    assert "--final-eval" not in source
    assert "yolo11s.pt" not in source
