from __future__ import annotations

import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def load_runner():
    path = REPO_ROOT / "detector/colab/run_d1_colab_checkpoint_r2.py"
    spec = importlib.util.spec_from_file_location("test_d1_runtime_evidence_r4", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


runner = load_runner()


def identity(boot_id: str) -> dict[str, str]:
    return runner.derive_runtime_identity("checkpoint_smoke_r4", boot_id)


def evidence() -> tuple[dict, list[dict]]:
    binding = "a" * 64
    checkpoint = "b" * 64
    attempts = [
        {
            "mode": "fresh",
            "started_at": "2026-10-21T01:00:00+00:00",
            "finished_at": "2026-10-21T01:05:00+00:00",
            "status": "PAUSED_FOR_RESUME",
            "error": None,
            "runtime_identity": identity("11111111-1111-4111-8111-111111111111"),
            "run_binding_sha256": binding,
            "checkpoint_binding_sha256": checkpoint,
        },
        {
            "mode": "resume",
            "started_at": "2026-10-21T02:00:00+00:00",
            "finished_at": "2026-10-21T02:05:00+00:00",
            "status": "SUCCEEDED",
            "error": None,
            "runtime_identity": identity("22222222-2222-4222-8222-222222222222"),
            "run_binding_sha256": binding,
            "checkpoint_binding_sha256": checkpoint,
        },
    ]
    execution = {
        "schema_version": 2,
        "status": "SUCCEEDED",
        "mode": "resume",
        "sealed_test_accessed": False,
        "error": None,
        "runtime_identity": attempts[1]["runtime_identity"],
        "run_binding_sha256": binding,
        "checkpoint_binding_sha256": checkpoint,
        "execution_attempts": attempts,
    }
    return execution, attempts


def test_runtime_digest_is_private_deterministic_and_boot_scoped() -> None:
    boot_a = "11111111-1111-4111-8111-111111111111"
    boot_b = "22222222-2222-4222-8222-222222222222"
    first = identity(boot_a)
    assert first == identity(boot_a)
    assert first != identity(boot_b)
    assert set(first) == {"schema", "digest"}
    assert boot_a not in json.dumps(first)
    assert len(first["digest"]) == 64


def test_two_runtime_evidence_passes() -> None:
    execution, attempts = evidence()
    result = runner.validate_runtime_evidence(execution, attempts)
    assert result["status"] == "D1_RUNTIME_EVIDENCE_VERIFIED"
    assert result["distinct_runtime_digests"] is True
    assert result["sealed_test_accessed"] is False


def test_equal_runtime_digests_fail_closed() -> None:
    execution, attempts = evidence()
    attempts[1]["runtime_identity"] = deepcopy(attempts[0]["runtime_identity"])
    execution["runtime_identity"] = attempts[1]["runtime_identity"]
    with pytest.raises(RuntimeError, match="same runtime identity"):
        runner.validate_runtime_evidence(execution, attempts)


@pytest.mark.parametrize("target", ("execution", "attempt"))
def test_missing_runtime_digest_fails_closed(target: str) -> None:
    execution, attempts = evidence()
    if target == "execution":
        del execution["runtime_identity"]
    else:
        del attempts[0]["runtime_identity"]
    with pytest.raises(RuntimeError):
        runner.validate_runtime_evidence(execution, attempts)


def test_malformed_runtime_digest_fails_closed() -> None:
    execution, attempts = evidence()
    attempts[0]["runtime_identity"]["digest"] = "not-a-sha256"
    with pytest.raises(RuntimeError, match="missing or malformed"):
        runner.validate_runtime_evidence(execution, attempts)


def test_reordered_attempts_fail_closed() -> None:
    execution, attempts = evidence()
    reversed_attempts = list(reversed(attempts))
    execution["execution_attempts"] = reversed_attempts
    with pytest.raises(RuntimeError, match="first runtime attempt"):
        runner.validate_runtime_evidence(execution, reversed_attempts)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("started_at", "not-a-timestamp"),
        ("finished_at", "2026-10-21T01:00:00"),
    ),
)
def test_malformed_or_naive_timestamp_fails_closed(field: str, value: str) -> None:
    execution, attempts = evidence()
    attempts[0][field] = value
    with pytest.raises(RuntimeError, match="timestamp"):
        runner.validate_runtime_evidence(execution, attempts)


def test_overlapping_or_reversed_chronology_fails_closed() -> None:
    execution, attempts = evidence()
    attempts[0]["finished_at"] = "2026-10-21T03:00:00+00:00"
    with pytest.raises(RuntimeError, match="chronology"):
        runner.validate_runtime_evidence(execution, attempts)


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    (
        ("run_binding_sha256", "c" * 64, "run bindings differ"),
        ("checkpoint_binding_sha256", "d" * 64, "checkpoint bindings differ"),
    ),
)
def test_tampered_binding_fails_closed(field: str, replacement: str, message: str) -> None:
    execution, attempts = evidence()
    attempts[1][field] = replacement
    execution[field] = replacement
    with pytest.raises(RuntimeError, match=message):
        runner.validate_runtime_evidence(execution, attempts)


def test_external_attempts_must_match_packaged_execution() -> None:
    execution, attempts = evidence()
    tampered = deepcopy(attempts)
    tampered[1]["runtime_identity"] = identity("33333333-3333-4333-8333-333333333333")
    with pytest.raises(RuntimeError, match="not bound"):
        runner.validate_runtime_evidence(execution, tampered)


def test_live_verifier_rejects_different_archived_digest_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    execution, attempts = evidence()
    state = tmp_path / "state"
    (state / "recovery").mkdir(parents=True)
    (state / "recovery/latest.json").write_text(
        json.dumps({"binding_sha256": "b" * 64}), encoding="utf-8"
    )
    (state / "colab_execution.json").write_text("{}", encoding="utf-8")
    (state / "execution_attempts.jsonl").write_text("{}\n", encoding="utf-8")
    archive = state / "D1_fixture_result.tar.gz"
    archive.write_bytes(b"fixture")
    archived_attempts = deepcopy(attempts)
    archived_attempts[0]["runtime_identity"] = identity(
        "33333333-3333-4333-8333-333333333333"
    )
    archived_attempts[1]["runtime_identity"] = identity(
        "44444444-4444-4444-8444-444444444444"
    )
    summary = runner.validate_runtime_evidence(execution, attempts)
    monkeypatch.setattr(
        runner.r1.base,
        "strict_json",
        lambda path: (
            execution
            if path.name == "colab_execution.json"
            else {"binding_sha256": "b" * 64}
        ),
    )
    monkeypatch.setattr(runner, "read_attempts", lambda _path: attempts)
    monkeypatch.setattr(runner, "verify_current_checkpoint", lambda *_args: {})
    monkeypatch.setattr(
        runner,
        "verify_r4_result_archive",
        lambda _archive, _manifest: {
            "runtime_evidence": summary,
            "runtime_attempts": archived_attempts,
        },
    )
    with pytest.raises(RuntimeError, match="archive and live"):
        runner.verify_live_state(state)


def test_strict_archived_json_rejects_duplicate_and_nonfinite_values() -> None:
    with pytest.raises(ValueError, match="duplicate JSON key"):
        runner.strict_json_bytes(b'{"status":"ok","status":"bad"}')
    with pytest.raises(ValueError, match="non-finite"):
        runner.strict_json_bytes(b'{"value":NaN}')


def test_live_verifier_rejects_recovery_pointer_binding_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    execution, attempts = evidence()
    state = tmp_path / "state"
    (state / "recovery").mkdir(parents=True)
    (state / "recovery/latest.json").write_text(
        json.dumps({"binding_sha256": "c" * 64}), encoding="utf-8"
    )
    (state / "colab_execution.json").write_text("{}", encoding="utf-8")
    (state / "execution_attempts.jsonl").write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(runner.r1.base, "strict_json", lambda _path: execution)
    monkeypatch.setattr(runner, "read_attempts", lambda _path: attempts)
    monkeypatch.setattr(
        runner,
        "verify_current_checkpoint",
        lambda *_args: (_ for _ in ()).throw(
            RuntimeError("live runtime evidence differs from recovery/latest.json")
        ),
    )
    with pytest.raises(RuntimeError, match="recovery/latest"):
        runner.verify_live_state(state)


def test_current_checkpoint_rehashes_pointer_manifest_and_all_files(tmp_path: Path) -> None:
    state = tmp_path / "state"
    snapshot = state / "recovery/snapshots/epoch-0002"
    binding_object = {"seed": 20261018, "epochs": 2}
    binding = runner.canonical_sha256(binding_object)
    paths = (
        "weights/last.pt",
        "weights/best.pt",
        "results.csv",
        "args.yaml",
        "run_contract.json",
    )
    records = []
    for index, name in enumerate(paths, start=1):
        path = snapshot / name
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = f"artifact-{index}".encode()
        path.write_bytes(payload)
        records.append(
            {
                "path": name,
                "size": len(payload),
                "sha256": runner.hashlib.sha256(payload).hexdigest(),
            }
        )
    manifest = {
        "schema_version": 1,
        "status": "RECOVERABLE",
        "run": "D1_fixture",
        "completed_epoch": 2,
        "binding": binding_object,
        "binding_sha256": binding,
        "files": records,
    }
    manifest_path = snapshot / "checkpoint_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    latest = {
        "schema_version": 1,
        "generation": "epoch-0002",
        "manifest_sha256": runner.r1.base.sha256_file(manifest_path),
        "binding_sha256": binding,
    }
    (state / "recovery/latest.json").write_text(json.dumps(latest), encoding="utf-8")
    assert runner.verify_current_checkpoint(state, binding)["completed_epoch"] == 2
    (snapshot / "weights/last.pt").write_bytes(b"tampered")
    with pytest.raises(RuntimeError, match="checkpoint artifact differs"):
        runner.verify_current_checkpoint(state, binding)


def test_successor_is_append_only_and_sealed_test_free() -> None:
    source = (REPO_ROOT / "detector/colab/run_d1_colab_checkpoint_r2.py").read_text()
    assert "run_d1_colab_checkpoint_r1.py" in source
    assert "BOOT_ID_PATH" in source
    assert "sealed_test_accessed" in source
    assert "export-test" not in source
    assert "--final-eval" not in source


def test_r4_notebook_is_unexecuted_fail_closed_and_runtime_evidence_aware() -> None:
    path = REPO_ROOT / "detector/colab/d1_train_checkpoint_r2.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    assert all(cell.get("execution_count") is None for cell in code_cells)
    assert all(not cell.get("outputs") for cell in code_cells)
    source = "\n".join("".join(cell["source"]) for cell in notebook["cells"])
    assert 'CODE_COMMIT = "PENDING_AFTER_QA"' in source
    assert 'MODE = "fresh"' in source
    assert 'MODE in {"fresh", "resume"}' in source
    assert "checkpoint_smoke_seed_20261018_r4" in source
    assert "run_d1_colab_checkpoint_r2.py" in source
    assert "verify_live_state" in source
    assert "distinct_runtime_digests" in source
    assert "sealed_test_accessed" in source
    assert "export-test" not in source
    assert "--final-eval" not in source


def test_main_persists_distinct_attempts_and_execution_binding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = tmp_path / "bundle.tar.gz"
    bundle.write_bytes(b"train-val-only")
    state = tmp_path / "state"
    boot = tmp_path / "boot_id"
    monkeypatch.setattr(runner, "BOOT_ID_PATH", boot)

    def fake_r1_main(argv):
        args = runner.r1.parser().parse_args(argv)
        (state / "recovery").mkdir(parents=True, exist_ok=True)
        (state / "recovery/latest.json").write_text(
            json.dumps({"binding_sha256": "b" * 64}), encoding="utf-8"
        )
        terminal = "PAUSED_FOR_RESUME" if args.mode == "fresh" else "SUCCEEDED"
        execution = {
            "schema_version": 1,
            "status": terminal,
            "mode": args.mode,
            "started_at": "2026-10-21T01:00:00+00:00"
            if args.mode == "fresh"
            else "2026-10-21T02:00:00+00:00",
            "finished_at": "2026-10-21T01:05:00+00:00"
            if args.mode == "fresh"
            else "2026-10-21T02:05:00+00:00",
            "sealed_test_accessed": False,
            "error": None,
        }
        runner.r1.base.write_json(state / "colab_execution.json", execution)
        runner.r1.append_jsonl(
            state / "execution_attempts.jsonl",
            {
                "mode": args.mode,
                "started_at": execution["started_at"],
                "finished_at": execution["finished_at"],
                "status": terminal,
                "error": None,
            },
        )
        return 0

    monkeypatch.setattr(runner.r1, "main", fake_r1_main)
    common = [
        "--repo-root",
        str(REPO_ROOT),
        "--bundle",
        str(bundle),
        "--state-dir",
        str(state),
        "--seed",
        "20261018",
        "--epochs",
        "2",
        "--imgsz",
        "1280",
        "--batch",
        "4",
        "--tag",
        "checkpoint_smoke_r4",
    ]

    boot.write_text("11111111-1111-4111-8111-111111111111", encoding="ascii")
    assert runner.main([*common, "--mode", "fresh", "--stop-after-epoch", "1"]) == 0
    boot.write_text("22222222-2222-4222-8222-222222222222", encoding="ascii")
    assert runner.main([*common, "--mode", "resume"]) == 0

    attempts = runner.read_attempts(state / "execution_attempts.jsonl")
    execution = json.loads((state / "colab_execution.json").read_text())
    verified = runner.validate_runtime_evidence(execution, attempts)
    assert verified["distinct_runtime_digests"] is True
    assert attempts[0]["run_binding_sha256"] == attempts[1]["run_binding_sha256"]
    assert attempts[0]["checkpoint_binding_sha256"] == attempts[1][
        "checkpoint_binding_sha256"
    ]


def test_same_runtime_resume_preflight_is_durably_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = tmp_path / "bundle.tar.gz"
    bundle.write_bytes(b"train-val-only")
    state = tmp_path / "state"
    (state / "recovery").mkdir(parents=True)
    (state / "recovery/latest.json").write_text(
        json.dumps({"binding_sha256": "b" * 64}), encoding="utf-8"
    )
    boot = tmp_path / "boot_id"
    boot.write_text("11111111-1111-4111-8111-111111111111", encoding="ascii")
    monkeypatch.setattr(runner, "BOOT_ID_PATH", boot)
    argv = [
        "--repo-root",
        str(REPO_ROOT),
        "--bundle",
        str(bundle),
        "--state-dir",
        str(state),
        "--mode",
        "resume",
        "--epochs",
        "2",
        "--batch",
        "4",
        "--tag",
        "checkpoint_smoke_r4",
    ]
    args = runner.r1.parser().parse_args(argv)
    prior = {
        "mode": "fresh",
        "started_at": "2026-10-21T01:00:00+00:00",
        "finished_at": "2026-10-21T01:05:00+00:00",
        "status": "PAUSED_FOR_RESUME",
        "error": None,
        "runtime_identity": identity("11111111-1111-4111-8111-111111111111"),
        "run_binding_sha256": runner.run_binding(args, runner.r1.base.sha256_file(bundle)),
        "checkpoint_binding_sha256": "b" * 64,
    }
    (state / "execution_attempts.jsonl").write_text(
        json.dumps(prior) + "\n", encoding="utf-8"
    )
    assert runner.main(argv) == 1
    execution = json.loads((state / "colab_execution.json").read_text())
    assert execution["status"] == "FAILED"
    assert "distinct runtime" in execution["error"]
    assert len((state / "execution_attempts.jsonl").read_text().splitlines()) == 2
