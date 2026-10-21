from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from ast import FunctionDef, Import, ImportFrom, Module, parse
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = REPO_ROOT / "scripts/build_d1_pilot_notebook_r4.py"
NOTEBOOK = REPO_ROOT / "detector/colab/d1_train_pilot_r4.ipynb"


def load_builder():
    spec = importlib.util.spec_from_file_location("test_d1_pilot_r4_builder", BUILDER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


builder = load_builder()


def notebook() -> dict:
    return json.loads(NOTEBOOK.read_text(encoding="utf-8"))


def source() -> str:
    return "\n".join("".join(cell["source"]) for cell in notebook()["cells"])


def test_r4_notebook_is_unexecuted_l4_resume_only_and_sealed_safe() -> None:
    payload = notebook()
    code = [cell for cell in payload["cells"] if cell["cell_type"] == "code"]
    assert all(cell.get("execution_count") is None and not cell.get("outputs") for cell in code)
    assert payload["metadata"]["accelerator"] == "GPU"
    assert payload["metadata"]["colab"]["gpuType"] == "L4"
    assert payload["metadata"]["pilot_r4_status"] == "PENDING_INDEPENDENT_QA"
    assert "r4_status" not in payload["metadata"]
    text = source()
    assert 'MODE = "resume"' in text
    assert 'assert MODE == "resume"' in text
    assert "--stop-after-epoch" not in text
    assert "export-test" not in text
    assert "--final-eval" not in text


def test_r4_notebook_pins_training_r3_and_r4_independently() -> None:
    text = source()
    assert f'TRAINING_COMMIT = "{builder.TRAINING_COMMIT}"' in text
    assert f'RECOVERY_COMMIT = "{builder.R3_COMMIT}"' in text
    assert f'RECOVERY_RUNNER_SHA256 = "{builder.R3_SHA256}"' in text
    assert f'R4_COMMIT = "{builder.R4_COMMIT}"' in text
    assert f'R4_RUNNER_SHA256 = "{builder.R4_SHA256}"' in text
    assert 'RECOVERY_RUNNER = Path("/content/run_d1_colab_pilot_r3.py")' in text
    assert 'R4_RUNNER = Path("/content/run_d1_colab_pilot_r4.py")' in text
    assert "download_verified_runner(" in text
    assert "subprocess.run(command, input=verified_r4_bytes, check=True)" in text


def test_r4_notebook_requires_epoch100_and_validates_final_package() -> None:
    text = source()
    assert 'preflight_latest["generation"] == "epoch-0100"' in text
    assert 'execution["status"] == "SUCCEEDED"' in text
    assert 'execution["training_outcome"]["completed_epoch"] == 100' in text
    assert 'latest["generation"] == "epoch-0100"' in text
    assert 'STATE_DIR.glob("*_result.tar.gz")' in text
    assert "pilot_r3 = verifier.load_pilot_r3(REPO_DIR)" in text
    assert "pilot_r3.verify_live_state(STATE_DIR, REPO_DIR)" in text
    assert 'sealed_test_accessed"] is False' in text


def test_r4_builder_is_deterministic_and_pins_frozen_r3() -> None:
    assert hashlib.sha256(builder.SOURCE.read_bytes()).hexdigest() == builder.SOURCE_SHA256
    before = NOTEBOOK.read_bytes()
    builder.build()
    assert NOTEBOOK.read_bytes() == before


def helper_namespace() -> dict:
    cell = "".join(notebook()["cells"][2]["source"])
    tree = parse(cell)
    selected = [
        node
        for node in tree.body
        if isinstance(node, (Import, ImportFrom, FunctionDef))
    ]
    namespace: dict = {}
    exec(compile(Module(body=selected, type_ignores=[]), "cell-2-helpers", "exec"), namespace)
    return namespace


def test_post_download_replacement_is_rejected_before_execution(tmp_path: Path) -> None:
    namespace = helper_namespace()
    runner_path = tmp_path / "runner.py"
    trusted = b"print('trusted')\n"
    runner_path.write_bytes(trusted)
    expected = hashlib.sha256(trusted).hexdigest()
    assert namespace["verified_runner_bytes"](runner_path, expected) == trusted
    runner_path.write_text("print('tampered')\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        namespace["verified_runner_bytes"](runner_path, expected)


def test_symlinked_runner_is_rejected(tmp_path: Path) -> None:
    namespace = helper_namespace()
    target = tmp_path / "target.py"
    target.write_text("print('target')\n", encoding="utf-8")
    linked = tmp_path / "runner.py"
    linked.symlink_to(target)
    with pytest.raises(OSError):
        namespace["verified_runner_bytes"](
            linked, hashlib.sha256(target.read_bytes()).hexdigest()
        )
