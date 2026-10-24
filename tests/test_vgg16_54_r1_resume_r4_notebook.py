from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).parents[1]
BUILDER = REPO_ROOT / "scripts/build_vgg16_54_r1_resume_r4_notebook.py"
NOTEBOOK = REPO_ROOT / "detector/colab/vgg16_54_r1_resume_r4.ipynb"


def load_builder() -> Any:
    spec = importlib.util.spec_from_file_location("vgg16_r4_resume_builder", BUILDER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def notebook() -> dict[str, Any]:
    return json.loads(NOTEBOOK.read_text(encoding="utf-8"))


def source(index: int) -> str:
    return "".join(notebook()["cells"][index]["source"])


def test_resume_notebook_is_deterministic_and_clean(tmp_path: Path) -> None:
    builder = load_builder()
    expected = json.dumps(builder.notebook(), indent=1, ensure_ascii=False) + "\n"
    assert expected.encode() == NOTEBOOK.read_bytes()
    generated = tmp_path / "generated.ipynb"
    builder.OUTPUT = generated
    builder.main()
    assert generated.read_bytes() == NOTEBOOK.read_bytes()
    for cell in notebook()["cells"]:
        if cell["cell_type"] == "code":
            assert cell["execution_count"] is None
            assert cell["outputs"] == []
            compile("".join(cell["source"]), "notebook-cell", "exec")


def test_resume_notebook_pins_fresh_proof_and_exact_boundary() -> None:
    serialized = json.dumps(notebook())
    assert "97b9dbbba6ebb99e30df733949684e9aef2e486f7e8357cee4b90968e42da580" in serialized
    assert "vgg16_54_r1_r3_fresh_smoke_qa_proof.json" in serialized
    assert "MODE = 'resume'" in serialized
    assert "STOP_AFTER = 2" in serialized
    assert "runs/vgg16_54_seed_20261018_r2" in serialized
    assert "'python', '-m', 'colab.run_vgg16_54_r1_r1'" in serialized


def test_resume_preflight_rehashes_closed_proof_and_full_state() -> None:
    preflight = source(3)
    assert "assert set(proof) ==" in preflight
    assert "RESUME_EPOCH_2_ON_GENUINELY_NEW_L4_ONLY" in preflight
    assert "assert roster == expected_roster" in preflight
    assert "assert sha256(artifact) == record['sha256']" in preflight
    assert "checkpoint_manifest_sha256" in preflight
    assert "runtime_identity'] == proof['runtime_identity']" in preflight


def test_resume_postflight_requires_two_distinct_l4_attempts() -> None:
    verification = source(7)
    assert "execution['epoch'] == 2" in verification
    assert "len(attempts) == 2" in verification
    assert "attempts[0]['runtime_identity']['digest'] !=" in verification
    assert "attempts[1]['gpu']['device_name'] == 'NVIDIA L4'" in verification


def test_resume_notebook_has_no_long_or_sealed_route() -> None:
    lowered = json.dumps(notebook()).lower()
    assert "stop_after = none" not in lowered
    assert "export-test" not in lowered
    assert "--final-eval" not in lowered
    assert "split test" not in lowered
    assert "long training remains forbidden" in lowered
