from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def load_runner():
    path = REPO_ROOT / "detector/colab/run_d1_colab_checkpoint_r3.py"
    spec = importlib.util.spec_from_file_location("test_d1_runtime_evidence_r4_r3", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


runner = load_runner()


def build_checkpoint(state: Path, *, run: object = "D1_fixture") -> str:
    snapshot = state / "recovery/snapshots/epoch-0002"
    binding_object = {"seed": 20261018, "epochs": 2}
    binding = runner.r2.canonical_sha256(binding_object)
    records = []
    for index, name in enumerate(runner.checkpoint_store.REQUIRED_ARTIFACTS, start=1):
        path = snapshot / name
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = f"artifact-{index}".encode()
        path.write_bytes(payload)
        records.append(
            {
                "path": name,
                "size": len(payload),
                "sha256": runner.r2.hashlib.sha256(payload).hexdigest(),
            }
        )
    manifest = {
        "schema_version": 1,
        "status": "RECOVERABLE",
        "run": run,
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
        "manifest_sha256": runner.r2.r1.base.sha256_file(manifest_path),
        "binding_sha256": binding,
    }
    (state / "recovery/latest.json").write_text(json.dumps(latest), encoding="utf-8")
    return binding


def test_valid_checkpoint_passes_pinned_store_verification(tmp_path: Path) -> None:
    state = tmp_path / "state"
    binding = build_checkpoint(state)
    assert runner.verify_current_checkpoint(state, binding)["completed_epoch"] == 2


def test_recovery_symlink_ancestor_fails_closed(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    binding = build_checkpoint(outside)
    state = tmp_path / "state"
    state.mkdir()
    (state / "recovery").symlink_to(outside / "recovery", target_is_directory=True)
    with pytest.raises(RuntimeError, match="contains a symlink"):
        runner.verify_current_checkpoint(state, binding)


def test_snapshot_weights_symlink_ancestor_fails_closed(tmp_path: Path) -> None:
    state = tmp_path / "state"
    binding = build_checkpoint(state)
    weights = state / "recovery/snapshots/epoch-0002/weights"
    outside = tmp_path / "outside-weights"
    os.replace(weights, outside)
    weights.symlink_to(outside, target_is_directory=True)
    with pytest.raises(RuntimeError, match="contains a symlink"):
        runner.verify_current_checkpoint(state, binding)


def test_non_string_checkpoint_run_fails_closed(tmp_path: Path) -> None:
    state = tmp_path / "state"
    binding = build_checkpoint(state, run={"not": "a run name"})
    with pytest.raises(RuntimeError, match="run identity"):
        runner.verify_current_checkpoint(state, binding)


def base_argv(bundle: Path, state: Path, mode: str) -> list[str]:
    return [
        "--repo-root",
        str(REPO_ROOT),
        "--bundle",
        str(bundle),
        "--state-dir",
        str(state),
        "--mode",
        mode,
        "--epochs",
        "2",
        "--batch",
        "4",
        "--tag",
        "checkpoint_smoke_r4_r3",
    ]


@pytest.mark.parametrize("boot_text", ("", "not-a-boot-id"))
def test_bad_or_missing_boot_id_is_durably_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, boot_text: str
) -> None:
    bundle = tmp_path / "bundle.tar.gz"
    bundle.write_bytes(b"train-val-only")
    state = tmp_path / "state"
    boot = tmp_path / "boot_id"
    if boot_text:
        boot.write_text(boot_text, encoding="ascii")
    monkeypatch.setattr(runner.r2, "BOOT_ID_PATH", boot)
    assert runner.main(base_argv(bundle, state, "fresh")) == 1
    execution = json.loads((state / "colab_execution.json").read_text())
    assert execution["status"] == "FAILED"
    assert execution["sealed_test_accessed"] is False
    assert len((state / "execution_attempts.jsonl").read_text().splitlines()) == 1


def test_malformed_prior_jsonl_is_durably_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = tmp_path / "bundle.tar.gz"
    bundle.write_bytes(b"train-val-only")
    state = tmp_path / "state"
    (state / "recovery").mkdir(parents=True)
    (state / "recovery/latest.json").write_text(
        json.dumps({"binding_sha256": "b" * 64}), encoding="utf-8"
    )
    (state / "execution_attempts.jsonl").write_text("{malformed}\n", encoding="utf-8")
    boot = tmp_path / "boot_id"
    boot.write_text("22222222-2222-4222-8222-222222222222", encoding="ascii")
    monkeypatch.setattr(runner.r2, "BOOT_ID_PATH", boot)
    assert runner.main(base_argv(bundle, state, "resume")) == 1
    execution = json.loads((state / "colab_execution.json").read_text())
    assert execution["status"] == "FAILED"
    assert "JSONDecodeError" in execution["error"]
    assert len((state / "execution_attempts.jsonl").read_text().splitlines()) == 2


def test_run_binding_mismatch_is_durably_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = tmp_path / "bundle.tar.gz"
    bundle.write_bytes(b"train-val-only")
    state = tmp_path / "state"
    (state / "recovery").mkdir(parents=True)
    (state / "recovery/latest.json").write_text(
        json.dumps({"binding_sha256": "b" * 64}), encoding="utf-8"
    )
    prior = {
        "mode": "fresh",
        "started_at": "2026-10-21T01:00:00+00:00",
        "finished_at": "2026-10-21T01:05:00+00:00",
        "status": "PAUSED_FOR_RESUME",
        "error": None,
        "runtime_identity": runner.r2.derive_runtime_identity(
            "checkpoint_smoke_r4_r3", "11111111-1111-4111-8111-111111111111"
        ),
        "run_binding_sha256": "c" * 64,
        "checkpoint_binding_sha256": "b" * 64,
    }
    (state / "execution_attempts.jsonl").write_text(json.dumps(prior) + "\n", encoding="utf-8")
    boot = tmp_path / "boot_id"
    boot.write_text("22222222-2222-4222-8222-222222222222", encoding="ascii")
    monkeypatch.setattr(runner.r2, "BOOT_ID_PATH", boot)
    assert runner.main(base_argv(bundle, state, "resume")) == 1
    execution = json.loads((state / "colab_execution.json").read_text())
    assert execution["status"] == "FAILED"
    assert "run binding differs" in execution["error"]
    assert len((state / "execution_attempts.jsonl").read_text().splitlines()) == 2


def test_r3_notebook_is_unexecuted_and_fail_closed() -> None:
    notebook = json.loads(
        (REPO_ROOT / "detector/colab/d1_train_checkpoint_r3.ipynb").read_text()
    )
    code = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    assert all(cell.get("execution_count") is None and not cell.get("outputs") for cell in code)
    source = "\n".join("".join(cell["source"]) for cell in notebook["cells"])
    assert 'CODE_COMMIT = "PENDING_AFTER_QA"' in source
    assert "run_d1_colab_checkpoint_r3.py" in source
    assert "checkpoint_smoke_seed_20261018_r4_r3" in source
    assert "export-test" not in source and "--final-eval" not in source
