from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def load_runner():
    path = REPO_ROOT / "detector/colab/run_d1_colab_checkpoint_r6.py"
    spec = importlib.util.spec_from_file_location("test_d1_runtime_evidence_r4_r6", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


runner = load_runner()


def evidence(schema_version: object = 2) -> tuple[dict, list[dict]]:
    identity_a = runner.r2.derive_runtime_identity(
        "checkpoint_smoke_r4_r6", "11111111-1111-4111-8111-111111111111"
    )
    identity_b = runner.r2.derive_runtime_identity(
        "checkpoint_smoke_r4_r6", "22222222-2222-4222-8222-222222222222"
    )
    attempts = [
        {
            "mode": "fresh",
            "started_at": "2026-10-21T01:00:00+00:00",
            "finished_at": "2026-10-21T01:05:00+00:00",
            "status": "PAUSED_FOR_RESUME",
            "error": None,
            "runtime_identity": identity_a,
            "run_binding_sha256": "a" * 64,
            "checkpoint_binding_sha256": "b" * 64,
        },
        {
            "mode": "resume",
            "started_at": "2026-10-21T02:00:00+00:00",
            "finished_at": "2026-10-21T02:05:00+00:00",
            "status": "SUCCEEDED",
            "error": None,
            "runtime_identity": identity_b,
            "run_binding_sha256": "a" * 64,
            "checkpoint_binding_sha256": "b" * 64,
        },
    ]
    execution = {
        "schema_version": schema_version,
        "status": "SUCCEEDED",
        "mode": "resume",
        "sealed_test_accessed": False,
        "error": None,
        "runtime_identity": identity_b,
        "run_binding_sha256": "a" * 64,
        "checkpoint_binding_sha256": "b" * 64,
        "execution_attempts": attempts,
    }
    return execution, attempts


@pytest.mark.parametrize("invalid", (2.0, True, "2", None))
def test_execution_schema_version_requires_exact_integer(invalid: object) -> None:
    execution, attempts = evidence(invalid)
    with pytest.raises(RuntimeError, match="schema version type"):
        runner.validate_runtime_evidence(execution, attempts)


def test_exact_integer_execution_schema_passes() -> None:
    execution, attempts = evidence(2)
    assert runner.validate_runtime_evidence(execution, attempts)[
        "distinct_runtime_digests"
    ] is True


@pytest.mark.parametrize("surface", ("archive", "live"))
def test_strict_schema_is_installed_on_archive_and_live_paths(
    monkeypatch: pytest.MonkeyPatch, surface: str
) -> None:
    execution, attempts = evidence(2.0)

    def inherited_path(*_args):
        return runner.r2.validate_runtime_evidence(execution, attempts)

    if surface == "archive":
        monkeypatch.setattr(runner.r2, "verify_r4_result_archive", inherited_path)
        with pytest.raises(RuntimeError, match="schema version type"):
            runner.verify_r4_result_archive(Path("a"), Path("b"))
    else:
        monkeypatch.setattr(runner.r5, "verify_live_state", inherited_path)
        with pytest.raises(RuntimeError, match="schema version type"):
            runner.verify_live_state(Path("state"))


def test_r6_notebook_is_unexecuted_and_fail_closed() -> None:
    notebook = json.loads(
        (REPO_ROOT / "detector/colab/d1_train_checkpoint_r6.ipynb").read_text()
    )
    code = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    assert all(cell.get("execution_count") is None and not cell.get("outputs") for cell in code)
    source = "\n".join("".join(cell["source"]) for cell in notebook["cells"])
    assert 'CODE_COMMIT = "PENDING_AFTER_QA"' in source
    assert "run_d1_colab_checkpoint_r6.py" in source
    assert "checkpoint_smoke_seed_20261018_r4_r6" in source
    assert "export-test" not in source and "--final-eval" not in source
