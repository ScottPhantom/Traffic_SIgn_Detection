"""Contract checks for the N54 long-resume Colab notebook builder."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/build_yolo11n_n54_r1_long_notebook.py"
NOTEBOOK = ROOT / "detector/colab/yolo11n_n54_r1_long.ipynb"


def load_builder():
    spec = importlib.util.spec_from_file_location("n54_long_notebook_builder", BUILDER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_long_notebook_is_deterministic_and_code_compiles() -> None:
    builder = load_builder()
    expected = builder.notebook()
    assert expected == builder.notebook()
    assert expected == json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    for cell in expected["cells"]:
        if cell["cell_type"] == "code":
            compile("".join(cell["source"]), cell["id"], "exec")


def test_long_notebook_binds_qa_and_cannot_repeat_smoke() -> None:
    builder = load_builder()
    cells = {cell["id"]: "".join(cell["source"]) for cell in builder.notebook()["cells"]}
    config = cells["n54-resume-config"]
    inputs = cells["n54-resume-inputs"]
    run = cells["n54-resume-run"]
    verify = cells["n54-resume-verify"]

    assert "MODE = 'resume'" in config
    assert "STOP_AFTER = None" in config
    assert builder.SOURCE_COMMIT in config
    assert builder.SMOKE_QA_SHA256 in config
    assert builder.LATEST_SHA256 in config
    assert "SMOKE_QA = DRIVE_ROOT /" in config
    assert "file_hash(latest_path) == LATEST_SHA256" in inputs
    assert "len(set(proof['runtime_digests'])) == 2" in inputs
    assert "'--smoke-qa-proof', str(SMOKE_QA)" in run
    assert "'--smoke-qa-sha256', SMOKE_QA_SHA256" in run
    assert "--stop-after-epoch" not in run.split("assert '--stop-after-epoch' not in command")[0]
    assert "'epoch-0100'" in verify
    assert "len(expected) == 8" in verify
    assert "execution['sealed_test_accessed'] is False" in verify
    assert "export-test" not in str(cells)
    assert "--final-eval" not in str(cells)


def test_proof_and_checkout_pins_match_existing_smoke() -> None:
    builder = load_builder()
    proof_path = ROOT / "docs/review/generated/yolo11n_n54_r1_smoke_qa_proof.json"
    proof = json.loads(proof_path.read_text(encoding="utf-8"))
    assert hashlib.sha256(proof_path.read_bytes()).hexdigest() == builder.SMOKE_QA_SHA256
    assert proof["checkpoint_latest_sha256"] == builder.LATEST_SHA256
    assert proof["sealed_test_accessed"] is False
    assert builder.SOURCE_COMMIT == "45b7b1fab606032fcfb2956d0207171ae8b4c7f6"
