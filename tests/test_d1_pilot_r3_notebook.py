from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from ast import FunctionDef, Import, ImportFrom, Module, parse
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = REPO_ROOT / "scripts/build_d1_pilot_notebook_r3.py"
NOTEBOOK = REPO_ROOT / "detector/colab/d1_train_pilot_r3.ipynb"


def load_builder():
    spec = importlib.util.spec_from_file_location("test_d1_pilot_r3_builder", BUILDER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


builder = load_builder()


def source() -> str:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    return "\n".join("".join(cell["source"]) for cell in notebook["cells"])


def test_r3_notebook_is_unexecuted_and_resume_only() -> None:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    code = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    assert all(cell.get("execution_count") is None and not cell.get("outputs") for cell in code)
    text = source()
    assert 'MODE = "resume"' in text
    assert 'assert MODE == "resume"' in text
    assert "--stop-after-epoch" not in text
    assert "epoch-0014" in text


def test_r3_notebook_separates_training_and_recovery_commits() -> None:
    text = source()
    assert f'TRAINING_COMMIT = "{builder.TRAINING_COMMIT}"' in text
    assert f'RECOVERY_COMMIT = "{builder.RECOVERY_COMMIT}"' in text
    assert f'RECOVERY_RUNNER_SHA256 = "{builder.RECOVERY_RUNNER_SHA256}"' in text
    assert 'RECOVERY_RUNNER = Path("/content/run_d1_colab_pilot_r3.py")' in text
    assert "raw.githubusercontent.com/ScottPhantom/Traffic_SIgn_Detection" in text
    assert "hashlib.sha256(runner_bytes).hexdigest() == RECOVERY_RUNNER_SHA256" in text
    assert 'verified_runner_bytes = verified_recovery_runner_bytes()' in text
    assert 'subprocess.run(command, input=verified_runner_bytes, check=True)' in text
    assert 'compile(verified_runner_bytes, str(RECOVERY_RUNNER), "exec")' in text


def test_r3_notebook_keeps_training_checkout_clean_and_bound() -> None:
    text = source()
    assert 'git", "checkout", CODE_COMMIT' in text
    assert "assert observed == TRAINING_COMMIT" in text
    assert 'git", "status", "--porcelain"' in text
    assert "checkout_clean" in text


def test_r3_notebook_requires_final_epoch_archive_logs_and_retry_verifier() -> None:
    text = source()
    assert 'execution["status"] == "SUCCEEDED"' in text
    assert 'execution["training_outcome"]["completed_epoch"] == 100' in text
    assert 'latest["generation"] == "epoch-0100"' in text
    assert 'STATE_DIR.glob("*_result.tar.gz")' in text
    assert "verifier.verify_live_state(STATE_DIR, REPO_DIR)" in text
    assert 'sealed_test_accessed"] is False' in text
    assert "export-test" not in text and "--final-eval" not in text


def test_r3_builder_is_deterministic_and_pins_frozen_r2() -> None:
    assert hashlib.sha256(builder.SOURCE.read_bytes()).hexdigest() == builder.SOURCE_SHA256
    before = NOTEBOOK.read_bytes()
    builder.build()
    assert NOTEBOOK.read_bytes() == before


def helper_namespace() -> dict:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cell = "".join(notebook["cells"][2]["source"])
    tree = parse(cell)
    selected = [
        node
        for node in tree.body
        if isinstance(node, (Import, ImportFrom, FunctionDef))
    ]
    namespace: dict = {}
    exec(compile(Module(body=selected, type_ignores=[]), "cell-2-helpers", "exec"), namespace)
    return namespace


def test_post_download_replacement_is_rejected_before_execution(
    tmp_path: Path,
) -> None:
    namespace = helper_namespace()
    runner_path = tmp_path / "runner.py"
    trusted = b"print('trusted')\n"
    runner_path.write_bytes(trusted)
    namespace["RECOVERY_RUNNER"] = runner_path
    namespace["RECOVERY_RUNNER_SHA256"] = hashlib.sha256(trusted).hexdigest()
    verified = namespace["verified_recovery_runner_bytes"]()
    assert verified == trusted
    marker = tmp_path / "INJECTED_EXECUTED"
    runner_path.write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('bad')\n",
        encoding="utf-8",
    )
    with pytest.raises(AssertionError):
        namespace["verified_recovery_runner_bytes"]()
    assert not marker.exists()


def test_symlinked_recovery_runner_is_rejected(tmp_path: Path) -> None:
    namespace = helper_namespace()
    target = tmp_path / "target.py"
    target.write_text("print('target')\n", encoding="utf-8")
    linked = tmp_path / "runner.py"
    linked.symlink_to(target)
    namespace["RECOVERY_RUNNER"] = linked
    namespace["RECOVERY_RUNNER_SHA256"] = hashlib.sha256(target.read_bytes()).hexdigest()
    with pytest.raises(OSError):
        namespace["verified_recovery_runner_bytes"]()
