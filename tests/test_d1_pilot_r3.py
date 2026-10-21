from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = REPO_ROOT / "detector/colab/run_d1_colab_pilot_r3.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("test_d1_pilot_r3_runner", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


runner = load_runner()


def attempt(
    *,
    mode: str,
    status: str,
    start: str,
    finish: str,
    digest: str,
    error: str | None = None,
) -> dict:
    return {
        "mode": mode,
        "started_at": start,
        "finished_at": finish,
        "status": status,
        "error": error,
        "runtime_identity": {
            "schema": "sha256:d1-runtime-v1:tag+linux-boot-id",
            "digest": digest * 64,
        },
        "run_binding_sha256": "a" * 64,
        "checkpoint_binding_sha256": "b" * 64,
    }


def retry_history(*, final_success: bool) -> list[dict]:
    records = [
        attempt(
            mode="fresh",
            status="PAUSED_FOR_RESUME",
            start="2026-10-21T01:00:00+00:00",
            finish="2026-10-21T01:05:00+00:00",
            digest="1",
        ),
        attempt(
            mode="resume",
            status="FAILED",
            start="2026-10-21T02:00:00+00:00",
            finish="2026-10-21T02:05:00+00:00",
            digest="2",
            error="RuntimeError: interrupted",
        ),
        attempt(
            mode="resume",
            status="FAILED",
            start="2026-10-21T02:10:00+00:00",
            finish="2026-10-21T02:11:00+00:00",
            digest="2",
            error="RuntimeError: retry guard",
        ),
    ]
    if final_success:
        records.append(
            attempt(
                mode="resume",
                status="SUCCEEDED",
                start="2026-10-21T03:00:00+00:00",
                finish="2026-10-21T05:00:00+00:00",
                digest="3",
            )
        )
    return records


def execution(records: list[dict]) -> dict:
    final = records[-1]
    return {
        "schema_version": 2,
        "status": "SUCCEEDED",
        "mode": "resume",
        "sealed_test_accessed": False,
        "error": None,
        "runtime_identity": final["runtime_identity"],
        "run_binding_sha256": "a" * 64,
        "checkpoint_binding_sha256": "b" * 64,
        "execution_attempts": records,
    }


def test_retry_prefix_accepts_recorded_resume_failures() -> None:
    records = retry_history(final_success=False)
    runner.validate_retry_prefix(
        records,
        identity={
            "schema": "sha256:d1-runtime-v1:tag+linux-boot-id",
            "digest": "3" * 64,
        },
        run_binding_sha256="a" * 64,
        checkpoint_binding_sha256="b" * 64,
    )


def test_retry_aware_runtime_evidence_accepts_failures_then_success() -> None:
    records = retry_history(final_success=True)
    result = runner.validate_runtime_evidence(execution(records), records)
    assert result["attempt_count"] == 4
    assert result["failed_resume_count"] == 2
    assert result["sealed_test_accessed"] is False


@pytest.mark.parametrize("target", ("binding", "checkpoint", "chronology", "sealed"))
def test_retry_runtime_evidence_rejects_tampering(target: str) -> None:
    records = retry_history(final_success=True)
    payload = execution(records)
    if target == "binding":
        records[1]["run_binding_sha256"] = "c" * 64
    elif target == "checkpoint":
        records[2]["checkpoint_binding_sha256"] = "c" * 64
    elif target == "chronology":
        records[2]["started_at"] = "2026-10-21T01:01:00+00:00"
    else:
        payload["sealed_test_accessed"] = True
    with pytest.raises(RuntimeError):
        runner.validate_runtime_evidence(payload, records)


def test_retry_prefix_rejects_prior_success() -> None:
    records = retry_history(final_success=True)
    with pytest.raises(RuntimeError, match="non-failed resume"):
        runner.validate_retry_prefix(
            records,
            identity={
                "schema": "sha256:d1-runtime-v1:tag+linux-boot-id",
                "digest": "4" * 64,
            },
            run_binding_sha256="a" * 64,
            checkpoint_binding_sha256="b" * 64,
        )


def test_retry_prefix_rejects_fresh_runtime_reuse() -> None:
    records = retry_history(final_success=False)
    with pytest.raises(RuntimeError, match="distinct runtime"):
        runner.validate_retry_prefix(
            records,
            identity=deepcopy(records[0]["runtime_identity"]),
            run_binding_sha256="a" * 64,
            checkpoint_binding_sha256="b" * 64,
        )


def test_real_failed_drive_attempt_shape_is_retryable() -> None:
    fixture = REPO_ROOT / "tests/fixtures/d1_pilot_r2_failed_attempts.json"
    if not fixture.is_file():
        pytest.skip("local Drive evidence fixture is intentionally absent")
    records = json.loads(fixture.read_text(encoding="utf-8"))
    summary = runner.validate_retry_attempts(records, require_success=False)
    assert summary["failed_resume_count"] >= 1


def test_resume_delegation_preserves_full_attempt_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pilot_r2 = runner._load(
        "test_d1_pilot_r3_local_predecessor",
        REPO_ROOT / "detector/colab/run_d1_colab_pilot_r2.py",
    )
    dependencies = runner.Dependencies(
        pilot_r2=pilot_r2,
        r6=pilot_r2.r6,
        r2=pilot_r2.r6.r2,
        r1=pilot_r2.r6.r2.r1,
    )
    records = retry_history(final_success=False)
    state = tmp_path / "state"
    state.mkdir()
    attempts_path = state / "execution_attempts.jsonl"
    attempts_path.write_text(
        "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8"
    )
    bundle = tmp_path / "bundle.tar.gz"
    bundle.write_bytes(b"train-val-only")
    boot = tmp_path / "boot_id"
    boot.write_text("33333333-3333-4333-8333-333333333333", encoding="ascii")
    monkeypatch.setattr(runner, "_training_commit", lambda _repo: runner.EXPECTED_TRAINING_COMMIT)
    monkeypatch.setattr(dependencies.r2, "BOOT_ID_PATH", boot)
    monkeypatch.setattr(dependencies.r2, "run_binding", lambda *_args: "a" * 64)
    monkeypatch.setattr(dependencies.r2, "checkpoint_binding", lambda _state: "b" * 64)
    monkeypatch.setattr(
        dependencies.r6.r5, "verify_current_checkpoint", lambda *_args: {}
    )

    def inherited_main(_argv):
        payload = {
            "status": "SUCCEEDED",
            "mode": "resume",
            "started_at": "2026-10-21T03:00:00+00:00",
            "finished_at": "2026-10-21T05:00:00+00:00",
            "error": None,
            "sealed_test_accessed": False,
        }
        dependencies.r1.base.write_json(state / "colab_execution.json", payload)
        dependencies.r1.append_jsonl(
            attempts_path,
            {
                "mode": "resume",
                "started_at": payload["started_at"],
                "finished_at": payload["finished_at"],
                "status": "SUCCEEDED",
                "error": None,
            },
        )
        return 0

    monkeypatch.setattr(dependencies.r1, "main", inherited_main)
    argv = [
        "--repo-root",
        str(REPO_ROOT),
        "--bundle",
        str(bundle),
        "--state-dir",
        str(state),
        "--mode",
        "resume",
        "--seed",
        "20261018",
        "--epochs",
        "100",
        "--imgsz",
        "1280",
        "--batch",
        "4",
        "--patience",
        "0",
        "--device",
        "0",
        "--tag",
        "pilot_100e_seed_20261018_r2",
    ]
    assert runner._run_resume(argv, dependencies) == 0
    execution_payload = json.loads((state / "colab_execution.json").read_text())
    assert len(execution_payload["execution_attempts"]) == 4
    assert execution_payload["execution_attempts"][:3] == records
    assert len(attempts_path.read_text().splitlines()) == 4


@pytest.mark.parametrize("attack", ("wrong_commit", "dirty_checkout"))
def test_untrusted_checkout_cannot_execute_before_pin_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, attack: str
) -> None:
    repo = tmp_path / "training-repo"
    predecessor = repo / "detector/colab/run_d1_colab_pilot_r2.py"
    predecessor.parent.mkdir(parents=True)
    marker = tmp_path / "executed.txt"
    predecessor.write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "qa@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "QA"], cwd=repo, check=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=repo, check=True)
    observed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if attack == "dirty_checkout":
        monkeypatch.setattr(runner, "EXPECTED_TRAINING_COMMIT", observed)
        predecessor.write_text(predecessor.read_text() + "# dirty\n", encoding="utf-8")
        message = "not clean"
    else:
        message = "commit differs"
    with pytest.raises(RuntimeError, match=message):
        runner.load_dependencies(repo)
    assert not marker.exists()


def test_symlinked_checkout_cannot_execute_before_pin_guard(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    linked = tmp_path / "linked"
    linked.symlink_to(target, target_is_directory=True)
    with pytest.raises(RuntimeError, match="symlink"):
        runner.load_dependencies(linked)
