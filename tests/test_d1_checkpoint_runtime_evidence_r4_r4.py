from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def load_runner():
    path = REPO_ROOT / "detector/colab/run_d1_colab_checkpoint_r4.py"
    spec = importlib.util.spec_from_file_location("test_d1_runtime_evidence_r4_r4", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


runner = load_runner()


def build_checkpoint(state: Path) -> tuple[str, Path, Path]:
    snapshot = state / "recovery/snapshots/epoch-0002"
    binding_object = {"seed": 20261018, "epochs": 2}
    binding = runner.r2.canonical_sha256(binding_object)
    records = []
    for index, name in enumerate(runner.r3.checkpoint_store.REQUIRED_ARTIFACTS, start=1):
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
        "manifest_sha256": runner.r2.r1.base.sha256_file(manifest_path),
        "binding_sha256": binding,
    }
    latest_path = state / "recovery/latest.json"
    latest_path.write_text(json.dumps(latest), encoding="utf-8")
    return binding, latest_path, manifest_path


@pytest.mark.parametrize("target", ("latest", "manifest", "size"))
def test_boolean_integer_type_confusion_fails_closed(tmp_path: Path, target: str) -> None:
    state = tmp_path / "state"
    binding, latest_path, manifest_path = build_checkpoint(state)
    if target == "latest":
        payload = json.loads(latest_path.read_text())
        payload["schema_version"] = True
        latest_path.write_text(json.dumps(payload), encoding="utf-8")
    else:
        payload = json.loads(manifest_path.read_text())
        if target == "manifest":
            payload["schema_version"] = True
        else:
            artifact = state / "recovery/snapshots/epoch-0002/results.csv"
            artifact.write_bytes(b"x")
            record = next(row for row in payload["files"] if row["path"] == "results.csv")
            record["size"] = True
            record["sha256"] = runner.r2.hashlib.sha256(b"x").hexdigest()
        manifest_path.write_text(json.dumps(payload), encoding="utf-8")
        latest = json.loads(latest_path.read_text())
        latest["manifest_sha256"] = runner.r2.r1.base.sha256_file(manifest_path)
        latest_path.write_text(json.dumps(latest), encoding="utf-8")
    with pytest.raises(RuntimeError, match="types differ"):
        runner.verify_current_checkpoint(state, binding)


def test_corrupt_latest_preflight_failure_is_durable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = tmp_path / "bundle.tar.gz"
    bundle.write_bytes(b"train-val-only")
    state = tmp_path / "state"
    (state / "recovery").mkdir(parents=True)
    (state / "recovery/latest.json").write_text("{corrupt", encoding="utf-8")
    (state / "execution_attempts.jsonl").write_text("{malformed}\n", encoding="utf-8")
    boot = tmp_path / "boot_id"
    boot.write_text("22222222-2222-4222-8222-222222222222", encoding="ascii")
    monkeypatch.setattr(runner.r2, "BOOT_ID_PATH", boot)
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
        "--tag",
        "checkpoint_smoke_r4_r4",
    ]
    assert runner.main(argv) == 1
    execution = json.loads((state / "colab_execution.json").read_text())
    assert execution["status"] == "FAILED"
    assert execution["checkpoint_binding_sha256"] is None
    assert execution["sealed_test_accessed"] is False
    assert len((state / "execution_attempts.jsonl").read_text().splitlines()) == 2


def test_r4_notebook_is_unexecuted_and_fail_closed() -> None:
    notebook = json.loads(
        (REPO_ROOT / "detector/colab/d1_train_checkpoint_r4.ipynb").read_text()
    )
    code = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    assert all(cell.get("execution_count") is None and not cell.get("outputs") for cell in code)
    source = "\n".join("".join(cell["source"]) for cell in notebook["cells"])
    assert 'CODE_COMMIT = "PENDING_AFTER_QA"' in source
    assert "run_d1_colab_checkpoint_r4.py" in source
    assert "checkpoint_smoke_seed_20261018_r4_r4" in source
    assert "export-test" not in source and "--final-eval" not in source
