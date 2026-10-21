from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = REPO_ROOT / "detector/colab/run_d1_colab_pilot_r5.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("test_d1_pilot_r5_runner", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


runner = load_runner()


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def make_checkout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init")
    git(root, "config", "user.email", "qa@example.invalid")
    git(root, "config", "user.name", "QA")
    (root / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    experiments = root / "results" / "experiments"
    experiments.mkdir(parents=True)
    (experiments / ".gitkeep").write_text("", encoding="utf-8")
    git(root, "add", "tracked.txt", "results/experiments/.gitkeep")
    git(root, "commit", "-m", "fixture")
    monkeypatch.setattr(runner, "EXPECTED_TRAINING_COMMIT", git(root, "rev-parse", "HEAD"))
    return root


def write_execution(state: Path, root: Path) -> None:
    state.mkdir(parents=True)
    run_dir = root / "results" / "experiments" / runner.EXPECTED_RUN
    (state / "colab_execution.json").write_text(
        json.dumps(
            {
                "status": "SUCCEEDED",
                "sealed_test_accessed": False,
                "run_dir": str(run_dir),
                "training_outcome": {
                    "status": "COMPLETED_FROM_FINAL_CHECKPOINT",
                    "completed_epoch": 100,
                    "run": runner.EXPECTED_RUN,
                },
            }
        ),
        encoding="utf-8",
    )


def test_clean_exact_ephemeral_run_removes_only_reviewed_untracked_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = make_checkout(tmp_path, monkeypatch)
    state = tmp_path / "state"
    write_execution(state, root)
    run_dir = root / "results" / "experiments" / runner.EXPECTED_RUN
    run_dir.mkdir(parents=True)
    (run_dir / "weights.pt").write_bytes(b"ephemeral")

    result = runner.clean_exact_ephemeral_run(root, state)

    assert result == {
        "status": "EXACT_EPHEMERAL_RUN_REMOVED",
        "removed": f"results/experiments/{runner.EXPECTED_RUN}",
    }
    assert not run_dir.exists()
    assert git(root, "status", "--porcelain=v1") == ""


def test_clean_exact_ephemeral_run_is_noop_for_clean_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = make_checkout(tmp_path, monkeypatch)
    state = tmp_path / "state"
    write_execution(state, root)
    payload = json.loads((state / "colab_execution.json").read_text())
    payload["run_dir"] = "/content/Traffic_Sign_Detector/results/experiments/elsewhere"
    (state / "colab_execution.json").write_text(json.dumps(payload), encoding="utf-8")

    assert runner.clean_exact_ephemeral_run(root, state) == {
        "status": "CHECKOUT_ALREADY_CLEAN",
        "removed": None,
    }


def test_clean_exact_ephemeral_run_rejects_any_additional_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = make_checkout(tmp_path, monkeypatch)
    state = tmp_path / "state"
    write_execution(state, root)
    run_dir = root / "results" / "experiments" / runner.EXPECTED_RUN
    run_dir.mkdir(parents=True)
    (run_dir / "weights.pt").write_bytes(b"ephemeral")
    (root / "unexpected.txt").write_text("unexpected\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="outside the exact ephemeral run"):
        runner.clean_exact_ephemeral_run(root, state)
    assert run_dir.exists()
    assert (root / "unexpected.txt").exists()


def test_clean_exact_ephemeral_run_rejects_symlink_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = make_checkout(tmp_path, monkeypatch)
    state = tmp_path / "state"
    write_execution(state, root)
    outside = tmp_path / "outside"
    outside.mkdir()
    target = root / "results" / "experiments" / runner.EXPECTED_RUN
    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(outside, target_is_directory=True)

    with pytest.raises(RuntimeError, match="linked or not a directory"):
        runner.clean_exact_ephemeral_run(root, state)
    assert outside.is_dir()


def test_load_pilot_r4_rejects_tampered_sibling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    r5 = tmp_path / "run_d1_colab_pilot_r5.py"
    r5.write_text("# R5\n", encoding="utf-8")
    (tmp_path / "run_d1_colab_pilot_r4.py").write_text("# tampered\n", encoding="utf-8")
    monkeypatch.setattr(runner, "__file__", str(r5))

    with pytest.raises(RuntimeError, match="hash differs"):
        runner.load_pilot_r4()


def test_require_exact_regular_file_rejects_symlink_and_tamper(tmp_path: Path) -> None:
    outside = tmp_path / "outside.log"
    outside.write_bytes(b"reviewed")
    linked = tmp_path / "linked.log"
    linked.symlink_to(outside)

    with pytest.raises(RuntimeError, match="symlink"):
        runner.require_exact_regular_file(
            linked,
            expected_size=len(b"reviewed"),
            expected_sha256=runner.sha256_file(outside),
        )

    regular = tmp_path / "regular.log"
    regular.write_bytes(b"reviewed")
    expected = runner.sha256_file(regular)
    regular.write_bytes(b"tampered")
    with pytest.raises(RuntimeError, match="SHA-256 differs"):
        runner.require_exact_regular_file(
            regular,
            expected_size=len(b"tampered"),
            expected_sha256=expected,
        )


def test_verify_authenticates_drive_state_before_ephemeral_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cleanup_called = False

    def forbidden_cleanup(*_args):
        nonlocal cleanup_called
        cleanup_called = True
        raise AssertionError("cleanup must not run for unauthenticated Drive state")

    def reject_artifact(*_args, **_kwargs):
        raise RuntimeError("required artifact SHA-256 differs")

    monkeypatch.setattr(runner, "clean_exact_ephemeral_run", forbidden_cleanup)
    monkeypatch.setattr(runner, "require_exact_regular_file", reject_artifact)
    with pytest.raises(RuntimeError, match="SHA-256 differs"):
        runner.verify_packaged_state(tmp_path / "repo", tmp_path / "state")
    assert cleanup_called is False


def test_verify_authenticates_archive_before_ephemeral_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = tmp_path / "state"
    state.mkdir()
    archive = state / "run_result.tar.gz"
    archive.write_bytes(b"corrupt archive")
    cleanup_called = False

    def forbidden_cleanup(*_args):
        nonlocal cleanup_called
        cleanup_called = True
        raise AssertionError("cleanup must not run for unauthenticated archive")

    def accept_live_reject_archive(path: Path, **_kwargs):
        if path == archive:
            raise RuntimeError("required artifact SHA-256 differs")
        return path

    monkeypatch.setattr(runner, "clean_exact_ephemeral_run", forbidden_cleanup)
    monkeypatch.setattr(
        runner, "require_exact_regular_file", accept_live_reject_archive
    )
    with pytest.raises(RuntimeError, match="SHA-256 differs"):
        runner.verify_packaged_state(tmp_path / "repo", state)
    assert cleanup_called is False


def test_verify_cleans_exact_dirty_run_before_predecessor_clean_git_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = make_checkout(tmp_path, monkeypatch)
    state = tmp_path / "state"
    write_execution(state, root)
    run_dir = root / "results" / "experiments" / runner.EXPECTED_RUN
    run_dir.mkdir(parents=True)
    (run_dir / "reconstructed.txt").write_text("ephemeral\n", encoding="utf-8")
    archive = state / "run_result.tar.gz"
    archive.write_bytes(b"archive")
    manifest = state / "run_result.tar.gz.manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "files": [
                    {
                        "path": f"colab_logs/{name}",
                        "size": runner.EXPECTED_LIVE_ARTIFACTS[name][0],
                        "sha256": runner.EXPECTED_LIVE_ARTIFACTS[name][1],
                    }
                    for name in ("colab_execution.json", "DB_logger.db")
                ]
            }
        ),
        encoding="utf-8",
    )
    r3_path = tmp_path / "run_d1_colab_pilot_r3.py"
    r3_path.write_text("# pinned R3\n", encoding="utf-8")

    class ReachedCleanGuard(RuntimeError):
        pass

    def clean_guard(_root: Path):
        assert git(root, "status", "--porcelain=v1") == ""
        raise ReachedCleanGuard("predecessor received clean checkout")

    pilot_r3 = SimpleNamespace(__file__=str(r3_path), load_dependencies=clean_guard)
    pilot_r4 = SimpleNamespace(load_pilot_r3=lambda _root: pilot_r3)
    monkeypatch.setattr(runner, "PILOT_R3_SHA256", runner.sha256_file(r3_path))
    monkeypatch.setattr(runner, "load_pilot_r4", lambda: pilot_r4)
    monkeypatch.setattr(
        runner, "require_exact_regular_file", lambda path, **_kwargs: path
    )

    with pytest.raises(ReachedCleanGuard, match="clean checkout"):
        runner.verify_packaged_state(root, state)
    assert not run_dir.exists()


def test_verify_packaged_state_patches_r6_wrapper_validator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    state = tmp_path / "state"
    snapshot = state / "recovery/snapshots/epoch-0100"
    snapshot.mkdir(parents=True)
    for name in ("DB_logger.db", "colab_train.log", "execution_attempts.jsonl"):
        (state / name).write_bytes(b"x")
    (state / "colab_execution.json").write_text("{}", encoding="utf-8")
    (state / "recovery/latest.json").write_text(
        json.dumps({"generation": "epoch-0100"}), encoding="utf-8"
    )
    (snapshot / "results.csv").write_text("epoch\n", encoding="utf-8")
    archive = state / "run_result.tar.gz"
    manifest = state / "run_result.tar.gz.manifest.json"
    archive.write_bytes(b"archive")
    manifest.write_bytes(b"manifest")
    expected_evidence = {
        "status": "D1_RUNTIME_RETRY_EVIDENCE_VERIFIED",
        "attempt_count": 6,
        "failed_resume_count": 4,
        "distinct_runtime_digests": True,
        "sealed_test_accessed": False,
    }
    calls: list[object] = []

    def old_validator(*_args):
        raise AssertionError("old two-attempt validator must not be called")

    def retry_validator(execution, attempts):
        calls.append((execution, attempts))
        return expected_evidence

    class R6:
        validate_runtime_evidence = staticmethod(old_validator)

        @staticmethod
        def verify_live_state(_state):
            assert R6.validate_runtime_evidence is retry_validator
            return {"runtime_evidence": retry_validator("execution", "attempts")}

    base = SimpleNamespace(
        strict_json=lambda path: json.loads(path.read_text(encoding="utf-8"))
    )
    dependencies = SimpleNamespace(
        r1=SimpleNamespace(base=base),
        r2=SimpleNamespace(read_attempts=lambda _path: ["attempt"]),
        r6=R6,
    )
    pilot_r3 = SimpleNamespace(
        __file__=str(tmp_path / "run_d1_colab_pilot_r3.py"),
        load_dependencies=lambda _root: (calls.append("load_dependencies"), dependencies)[1],
        validate_runtime_evidence=retry_validator,
    )
    Path(pilot_r3.__file__).write_bytes(b"R3")
    pilot_r4 = SimpleNamespace(
        load_pilot_r3=lambda _root: pilot_r3,
        validate_retry_aware_sqlite_log=lambda *_args, **_kwargs: calls.append("sqlite"),
    )
    monkeypatch.setattr(runner, "PILOT_R3_SHA256", runner.sha256_file(Path(pilot_r3.__file__)))
    monkeypatch.setattr(
        runner,
        "clean_exact_ephemeral_run",
        lambda *_args: (calls.append("cleanup"), {"status": "clean"})[1],
    )
    monkeypatch.setattr(runner, "load_pilot_r4", lambda: pilot_r4)
    monkeypatch.setattr(runner, "require_exact_regular_file", lambda path, **_kwargs: path)
    monkeypatch.setattr(
        runner,
        "strict_json",
        lambda _path: {
            "files": [
                {
                    "path": f"colab_logs/{name}",
                    "size": runner.EXPECTED_LIVE_ARTIFACTS[name][0],
                    "sha256": runner.EXPECTED_LIVE_ARTIFACTS[name][1],
                }
                for name in ("colab_execution.json", "DB_logger.db")
            ]
        },
    )

    result = runner.verify_packaged_state(root, state)

    assert result["status"] == "D1_PILOT_R5_PACKAGED_STATE_VERIFIED"
    assert result["runtime_evidence"] == expected_evidence
    assert "sqlite" in calls
    assert calls.index("cleanup") < calls.index("load_dependencies")


@pytest.mark.parametrize(
    ("attempt_count", "failed_resume_count"),
    [(2, 0), (5, 3), (7, 5), (True, 4), (6, False)],
)
def test_require_exact_runtime_evidence_rejects_non_live_retry_counts(
    attempt_count: object, failed_resume_count: object
) -> None:
    evidence = {
        "status": "D1_RUNTIME_RETRY_EVIDENCE_VERIFIED",
        "attempt_count": attempt_count,
        "failed_resume_count": failed_resume_count,
        "distinct_runtime_digests": True,
        "sealed_test_accessed": False,
    }
    with pytest.raises(RuntimeError, match="exact live history"):
        runner.require_exact_runtime_evidence(evidence)


def test_require_exact_runtime_evidence_accepts_six_attempts_four_failures() -> None:
    evidence = {
        "status": "D1_RUNTIME_RETRY_EVIDENCE_VERIFIED",
        "attempt_count": 6,
        "failed_resume_count": 4,
        "distinct_runtime_digests": True,
        "sealed_test_accessed": False,
    }
    assert runner.require_exact_runtime_evidence(evidence) is evidence


def test_source_contains_no_training_or_sealed_test_route() -> None:
    text = RUNNER_PATH.read_text(encoding="utf-8")
    assert "model.train(" not in text
    assert "export-test" not in text
    assert "--final-eval" not in text
    assert "sealed_test_accessed" in text
