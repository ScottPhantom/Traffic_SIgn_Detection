from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from ast import FunctionDef, Import, ImportFrom, Module, parse
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = REPO_ROOT / "scripts/build_d1_pilot_notebook_r5.py"
NOTEBOOK = REPO_ROOT / "detector/colab/d1_train_pilot_r5.ipynb"


def load_builder():
    spec = importlib.util.spec_from_file_location("test_d1_pilot_r5_builder", BUILDER_PATH)
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


def test_r5_notebook_is_unexecuted_verification_only_and_sealed_safe() -> None:
    payload = notebook()
    code = [cell for cell in payload["cells"] if cell["cell_type"] == "code"]
    assert all(cell["execution_count"] is None and not cell["outputs"] for cell in code)
    assert payload["metadata"]["accelerator"] == "GPU"
    assert payload["metadata"]["colab"]["gpuType"] == "L4"
    assert payload["metadata"]["pilot_r5_status"] == "PENDING_INDEPENDENT_QA"
    text = source()
    assert "model.train(" not in text
    assert "--mode" not in text
    assert "--bundle" not in text
    assert "export-test" not in text
    assert "--final-eval" not in text
    assert "sealed_test_accessed" in text


def test_r5_notebook_pins_training_and_all_sidecars() -> None:
    text = source()
    for name in (
        "TRAINING_COMMIT",
        "R3_COMMIT",
        "R3_SHA256",
        "R4_COMMIT",
        "R4_SHA256",
        "R5_COMMIT",
        "R5_SHA256",
    ):
        assert f'{name} = "{getattr(builder, name)}"' in text
    assert 'R3_RUNNER = Path("/content/run_d1_colab_pilot_r3.py")' in text
    assert 'R4_RUNNER = Path("/content/run_d1_colab_pilot_r4.py")' in text
    assert 'R5_RUNNER = Path("/content/run_d1_colab_pilot_r5.py")' in text


def test_r5_notebook_requires_exact_terminal_evidence() -> None:
    text = source()
    assert 'latest["generation"] == "epoch-0100"' in text
    assert 'execution["status"] == "SUCCEEDED"' in text
    assert 'result["runtime_evidence"]["attempt_count"] == 6' in text
    assert 'result["runtime_evidence"]["failed_resume_count"] == 4' in text
    assert 'result["runtime_evidence"]["distinct_runtime_digests"] is True' in text
    assert 'result["status"] == "D1_PILOT_R5_PACKAGED_STATE_VERIFIED"' in text


def test_r5_builder_is_deterministic() -> None:
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


def test_runner_read_rejects_symlink_and_tamper(tmp_path: Path) -> None:
    namespace = helper_namespace()
    target = tmp_path / "target.py"
    target.write_bytes(b"reviewed")
    expected = hashlib.sha256(target.read_bytes()).hexdigest()
    assert namespace["verified_bytes"](target, expected) == b"reviewed"
    linked = tmp_path / "linked.py"
    linked.symlink_to(target)
    with pytest.raises(OSError):
        namespace["verified_bytes"](linked, expected)
    target.write_bytes(b"tampered")
    with pytest.raises(AssertionError):
        namespace["verified_bytes"](target, expected)
