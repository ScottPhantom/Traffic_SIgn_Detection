#!/usr/bin/env python3
"""Generate the proof-bound VGG16-54 R1 epoch-2 resume launcher."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "detector/colab/vgg16_54_r1_resume_r4.ipynb"
R3_BUILDER = ROOT / "scripts/build_vgg16_54_r1_launch_r3_notebook.py"
FRESH_SMOKE_QA_SHA256 = "97b9dbbba6ebb99e30df733949684e9aef2e486f7e8357cee4b90968e42da580"


def _load_r3() -> Any:
    spec = importlib.util.spec_from_file_location("vgg16_54_r1_launch_r3_pinned", R3_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load pinned R3 builder: {R3_BUILDER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def notebook() -> dict[str, object]:
    payload = json.loads(json.dumps(_load_r3().notebook()))
    payload["cells"][0]["source"] = (
        "# VGG16-54 R1 R4 — proof-bound resume through epoch 2\n\n"
        "Train/validation only. Run on a genuinely new NVIDIA L4 after the independent fresh "
        "artifact QA proof has been uploaded. This notebook rehashes the complete epoch-1 state "
        "before resume and stops exactly at epoch 2. Never open the sealed test.\n"
    ).splitlines(keepends=True)

    config = "".join(payload["cells"][2]["source"])
    config = config.replace(
        "SMOKE_QA = None\nSMOKE_QA_SHA256 = None\nMODE = 'fresh'\nSTOP_AFTER = 1\n",
        "FRESH_SMOKE_QA = DRIVE / 'vgg16_54_r1_r3_fresh_smoke_qa_proof.json'\n"
        f"FRESH_SMOKE_QA_SHA256 = '{FRESH_SMOKE_QA_SHA256}'\n"
        "SMOKE_QA = None\nSMOKE_QA_SHA256 = None\nMODE = 'resume'\nSTOP_AFTER = 2\n",
    )
    payload["cells"][2]["source"] = config.splitlines(keepends=True)

    preflight = "".join(payload["cells"][3]["source"])
    preflight = preflight.replace(
        "import hashlib\n", "import hashlib\nimport json\nimport os\nimport stat\n"
    )
    preflight = preflight.replace(
        "    (RUNTIME_SOURCE_QA, RUNTIME_SOURCE_QA_SHA256),\n",
        "    (RUNTIME_SOURCE_QA, RUNTIME_SOURCE_QA_SHA256),\n"
        "    (FRESH_SMOKE_QA, FRESH_SMOKE_QA_SHA256),\n",
    )
    preflight += (
        "\ndef reject_constant(value):\n"
        "    raise ValueError(f'non-finite JSON constant: {value}')\n\n"
        "def unique_object(pairs):\n"
        "    result = {}\n"
        "    for key, value in pairs:\n"
        "        assert key not in result, f'duplicate JSON key: {key}'\n"
        "        result[key] = value\n"
        "    return result\n\n"
        "def strict_json(path):\n"
        "    return json.loads(\n"
        "        path.read_text(), parse_constant=reject_constant,\n"
        "        object_pairs_hook=unique_object,\n"
        "    )\n\n"
        "def safe_file(path):\n"
        "    info = path.lstat()\n"
        "    assert stat.S_ISREG(info.st_mode) and info.st_nlink == 1\n"
        "    return info\n\n"
        "proof = strict_json(FRESH_SMOKE_QA)\n"
        "assert set(proof) == {\n"
        "    'schema_version', 'verdict', 'package', 'state_suffix', 'source_commit',\n"
        "    'launcher_commit', 'launch_notebook_sha256', 'launch_qa_record_sha256',\n"
        "    'config_sha256', 'bundle_manifest_sha256', 'status', 'event', 'epoch',\n"
        "    'attempt_count', 'fresh_attempt', 'runtime_identity', 'gpu',\n"
        "    'run_binding_sha256', 'checkpoint_binding_sha256', 'checkpoint_generation',\n"
        "    'checkpoint_manifest_sha256', 'snapshot_files', 'state_artifacts',\n"
        "    'sealed_test_accessed', 'authorization',\n"
        "}\n"
        "assert proof['schema_version'] == 1 and proof['verdict'] == 'PASS'\n"
        "assert proof['package'] == 'VGG16-54-R1-R3-FRESH-SMOKE'\n"
        "assert proof['state_suffix'] == 'M1_D1_Colab/runs/vgg16_54_seed_20261018_r2'\n"
        "assert proof['source_commit'] == CHECKOUT_COMMIT\n"
        "assert proof['config_sha256'] == "
        "'b5275ca6635859f3eb2ae5d98e480da18f748667a96f92a36d1e2145b197c15a'\n"
        "assert proof['bundle_manifest_sha256'] == MANIFEST_SHA256\n"
        "assert (proof['status'], proof['event'], proof['epoch']) == "
        "('SMOKE_STOP', 'SMOKE_STOP', 1)\n"
        "assert proof['attempt_count'] == 1\n"
        "assert proof['fresh_attempt'] == {'mode': 'fresh', 'completed_epoch': 0}\n"
        "assert proof['runtime_identity'] == {\n"
        "    'schema': 'sha256:d1-runtime-v1:tag+linux-boot-id',\n"
        "    'digest': '15f95cca74680341a2e90aeee1e6679050ddf3974ab525e6ad7366eb1000453f',\n"
        "}\n"
        "assert proof['gpu']['device_name'] == 'NVIDIA L4'\n"
        "assert proof['run_binding_sha256'] == proof['checkpoint_binding_sha256']\n"
        "assert proof['run_binding_sha256'] == "
        "'fe334b1877454adb608628bde0c1a3287a31b861f5bb7b16635e96a8a1953bbe'\n"
        "assert proof['checkpoint_generation'] == 'epoch-0001'\n"
        "assert proof['sealed_test_accessed'] is False\n"
        "assert proof['authorization'] == 'RESUME_EPOCH_2_ON_GENUINELY_NEW_L4_ONLY'\n"
        "expected_state = {\n"
        "    'colab_execution.json', 'DB_logger.db', 'train.log',\n"
        "    'recovery/checkpoint_io.jsonl', 'recovery/latest.json',\n"
        "}\n"
        "assert set(proof['state_artifacts']) == expected_state\n"
        "for relative, record in proof['state_artifacts'].items():\n"
        "    assert set(record) == {'size', 'sha256'}\n"
        "    artifact = STATE / relative\n"
        "    assert safe_file(artifact).st_size == record['size']\n"
        "    assert sha256(artifact) == record['sha256']\n"
        "snapshot = STATE / 'recovery/snapshots' / proof['checkpoint_generation']\n"
        "rows = {row['path']: row for row in proof['snapshot_files']}\n"
        "assert set(rows) == {\n"
        "    'weights/last.pt', 'weights/best.pt', 'results.csv', 'args.yaml',\n"
        "    'run_contract.json',\n"
        "}\n"
        "for relative, record in rows.items():\n"
        "    assert set(record) == {'path', 'size', 'sha256'}\n"
        "    artifact = snapshot / relative\n"
        "    assert safe_file(artifact).st_size == record['size']\n"
        "    assert sha256(artifact) == record['sha256']\n"
        "manifest_path = snapshot / 'checkpoint_manifest.json'\n"
        "safe_file(manifest_path)\n"
        "assert sha256(manifest_path) == proof['checkpoint_manifest_sha256']\n"
        "roster = {str(path.relative_to(STATE)) for path in STATE.rglob('*') if path.is_file()}\n"
        "expected_roster = expected_state | {\n"
        "    f'recovery/snapshots/{proof[\"checkpoint_generation\"]}/{relative}'\n"
        "    for relative in rows\n"
        "} | {f'recovery/snapshots/{proof[\"checkpoint_generation\"]}/checkpoint_manifest.json'}\n"
        "assert roster == expected_roster\n"
        "execution = strict_json(STATE / 'colab_execution.json')\n"
        "assert execution['execution_attempts'][0]['runtime_identity'] == "
        "proof['runtime_identity']\n"
        "assert execution['execution_attempts'][0]['gpu'] == proof['gpu']\n"
        "assert execution['sealed_test_accessed'] is False\n"
    )
    payload["cells"][3]["source"] = preflight.splitlines(keepends=True)

    verification = (
        "import json\n"
        "import sqlite3\n\n"
        "execution = json.loads((STATE / 'colab_execution.json').read_text())\n"
        "print(json.dumps(execution, indent=2, ensure_ascii=False))\n"
        "with sqlite3.connect(STATE / 'DB_logger.db') as database:\n"
        "    rows = list(database.execute(\n"
        "        'SELECT time, stage, event, payload FROM logs ORDER BY rowid DESC LIMIT 20'\n"
        "    ))\n"
        "for row in rows:\n"
        "    print(row)\n"
        "attempts = execution['execution_attempts']\n"
        "assert execution['status'] == 'SMOKE_STOP' and execution['epoch'] == 2\n"
        "assert execution['sealed_test_accessed'] is False\n"
        "assert len(attempts) == 2\n"
        "assert attempts[0]['mode'] == 'fresh' and attempts[0]['completed_epoch'] == 0\n"
        "assert attempts[1]['mode'] == 'resume' and attempts[1]['completed_epoch'] == 1\n"
        "assert attempts[1]['gpu']['device_name'] == 'NVIDIA L4'\n"
        "assert attempts[0]['runtime_identity']['digest'] != "
        "attempts[1]['runtime_identity']['digest']\n"
        "assert attempts[1]['run_binding_sha256'] == attempts[1]['checkpoint_binding_sha256']\n"
    )
    payload["cells"][7]["source"] = verification.splitlines(keepends=True)
    payload["cells"][8]["source"] = (
        "## Gate after this notebook\n\n"
        "Stop after epoch 2. Independent two-runtime artifact QA must verify both runtime "
        "digests, the epoch-2 checkpoint, all three logs and `sealed_test_accessed=false`. Long "
        "training remains forbidden until that QA produces a separately pinned proof.\n"
    ).splitlines(keepends=True)
    return payload


def main() -> None:
    OUTPUT.write_text(json.dumps(notebook(), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
