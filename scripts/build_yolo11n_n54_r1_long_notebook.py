#!/usr/bin/env python3
"""Build the append-only YOLO11n N54 long-resume Colab notebook."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE_BUILDER = ROOT / "scripts/build_yolo11n_dual_track_r1_notebooks.py"
OUTPUT = ROOT / "detector/colab/yolo11n_n54_r1_long.ipynb"

# The training checkout must remain identical to the two smoke legs because it
# participates in the run binding. The new proof is stored on the private Drive.
SOURCE_COMMIT = "45b7b1fab606032fcfb2956d0207171ae8b4c7f6"
SMOKE_QA_SHA256 = "9189b52043157a5b536365fa714df8152bb05519b8bff723596f024a189bcd1e"
SMOKE_QA_PATH = "M1_D1_Colab/yolo11n_n54_r1_smoke_qa_proof.json"
LATEST_SHA256 = "3e223f7cb010c83da168e239e1b1d9016129e44bffb2a36261b6234f9acc68a3"


def _load_base() -> Any:
    spec = importlib.util.spec_from_file_location("yolo11n_n54_notebook_base", BASE_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load notebook base: {BASE_BUILDER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def notebook() -> dict[str, Any]:
    if not (
        len(SOURCE_COMMIT) == 40
        and len(SMOKE_QA_SHA256) == 64
        and len(LATEST_SHA256) == 64
    ):
        raise RuntimeError("long notebook requires committed smoke QA and epoch-2 pins")

    base = _load_base()
    result = copy.deepcopy(base.n54_notebook("resume", 2))
    cells = result["cells"]
    cells[0]["source"] = (
        "# YOLO11n N54 R1 — resume to epoch 100\n\n"
        "Same QA-passed train/validation run, resumed from epoch 2 on a third NVIDIA L4. "
        "The sealed test stays closed.\n"
    ).splitlines(keepends=True)

    config = "".join(cells[2]["source"])
    config = config.replace("STOP_AFTER = 2", "STOP_AFTER = None")
    config = config.replace(
        "assert (MODE, STOP_AFTER) in {('fresh', 1), ('resume', 2)}",
        "assert MODE == 'resume' and STOP_AFTER is None",
    )
    config = config.replace(
        f"SOURCE_COMMIT = {base.SOURCE_COMMIT!r}",
        f"SOURCE_COMMIT = {SOURCE_COMMIT!r}",
    )
    config += (
        f"\nSMOKE_QA = DRIVE_ROOT / {SMOKE_QA_PATH!r}\n"
        f"SMOKE_QA_SHA256 = {SMOKE_QA_SHA256!r}\n"
        f"LATEST_SHA256 = {LATEST_SHA256!r}\n"
    )
    cells[2]["source"] = config.splitlines(keepends=True)

    inputs = "".join(cells[4]["source"])
    inputs += """
assert SMOKE_QA.is_file() and not SMOKE_QA.is_symlink()
assert file_hash(SMOKE_QA) == SMOKE_QA_SHA256
latest_path = STATE / 'recovery/latest.json'
assert latest_path.is_file() and not latest_path.is_symlink()
assert file_hash(latest_path) == LATEST_SHA256
latest = json.loads(latest_path.read_text())
assert latest['generation'] == 'epoch-0002'
execution = json.loads((STATE / 'colab_execution.json').read_text())
assert execution['status'] == 'PAUSED_FOR_RESUME'
assert execution['sealed_test_accessed'] is False
assert [attempt['completed_epoch'] for attempt in execution['execution_attempts']] == [1, 2]
proof = json.loads(SMOKE_QA.read_text())
assert proof['verdict'] == 'PASS'
assert proof['checkpoint_latest_sha256'] == LATEST_SHA256
assert proof['sealed_test_accessed'] is False
assert proof['runtime_digests'] == [
    attempt['runtime_digest'] for attempt in execution['execution_attempts']
]
assert len(set(proof['runtime_digests'])) == 2
subprocess.run(['uv', 'sync', '--frozen'], cwd=REPO / 'detector', check=True)
print({'resume_from': 'epoch-0002', 'smoke_qa_sha256': SMOKE_QA_SHA256})
"""
    cells[4]["source"] = inputs.splitlines(keepends=True)

    run = """command = [
    sys.executable, str(REPO / 'detector/colab/run_yolo11n_n54_r1.py'),
    '--repo-root', str(REPO),
    '--bundle', str(BUNDLE), '--bundle-sha256', BUNDLE_SHA256,
    '--state-dir', str(STATE), '--mode', MODE,
    '--expected-checkout', SOURCE_COMMIT,
    '--source-qa-record', str(SOURCE_QA), '--source-qa-sha256', SOURCE_QA_SHA256,
    '--smoke-qa-proof', str(SMOKE_QA), '--smoke-qa-sha256', SMOKE_QA_SHA256,
    '--seed', '20261018', '--epochs', '100', '--imgsz', '1280',
    '--batch', '4', '--workers', '4', '--fraction', '1.0',
    '--patience', '30', '--device', '0', '--tag', 'n54_r1', '--cos-lr',
]
assert '--stop-after-epoch' not in command
print('Running:', ' '.join(command))
subprocess.run(command, check=True)
"""
    cells[5]["source"] = run.splitlines(keepends=True)

    verify = """import sqlite3
import tarfile

execution = json.loads((STATE / 'colab_execution.json').read_text())
assert execution['status'] == 'SUCCEEDED'
assert execution['sealed_test_accessed'] is False
attempts = execution['execution_attempts']
assert len(attempts) == 3
assert [item['leg'] for item in attempts] == [
    'fresh_epoch_1', 'resume_epoch_2', 'long_resume',
]
assert len({item['runtime_digest'] for item in attempts}) == 3
assert all(item['sealed_test_accessed'] is False for item in attempts)
assert attempts[-1]['completed_epoch'] == 100

latest = json.loads((STATE / 'recovery/latest.json').read_text())
assert latest['generation'] == 'epoch-0100'
snapshot = STATE / 'recovery/snapshots/epoch-0100'
checkpoint_manifest_path = snapshot / 'checkpoint_manifest.json'
assert file_hash(checkpoint_manifest_path) == latest['manifest_sha256']
checkpoint_manifest = json.loads(checkpoint_manifest_path.read_text())
assert checkpoint_manifest['completed_epoch'] == 100

result_dir = STATE / 'results'
archive_path = result_dir / 'result.tar.gz'
manifest_path = result_dir / 'result_manifest.json'
assert archive_path.is_file() and not archive_path.is_symlink()
assert manifest_path.is_file() and not manifest_path.is_symlink()
result = json.loads(manifest_path.read_text())
assert result['package'] == 'YOLO11N-N54-R1'
assert result['completed_epoch'] == 100
assert result['sealed_test_accessed'] is False
assert file_hash(archive_path) == result['archive_sha256']
expected = result['members']
assert len(expected) == 8
with tarfile.open(archive_path, 'r:gz') as reader:
    members = reader.getmembers()
    assert len(members) == 8 and {member.name for member in members} == set(expected)
    for member in members:
        assert member.isfile()
        content = reader.extractfile(member).read()
        assert len(content) == expected[member.name]['bytes']
        assert hashlib.sha256(content).hexdigest() == expected[member.name]['sha256']

database = STATE / 'DB_logger.db'
text_log = STATE / 'colab_train.log'
assert database.is_file() and text_log.is_file()
with sqlite3.connect(f'file:{database}?mode=ro', uri=True) as db:
    assert db.execute('PRAGMA integrity_check').fetchone() == ('ok',)
    assert db.execute('SELECT COUNT(*) FROM logs').fetchone()[0] > 0
assert 'Training end' in text_log.read_text()
print({
    'status': 'SUCCEEDED', 'epoch': 100,
    'archive_sha256': result['archive_sha256'], 'seal': False,
})
"""
    cells[6]["source"] = verify.splitlines(keepends=True)
    result["metadata"]["yolo11n_dual_track_r1_status"] = "QA_GATED_LONG_RESUME"
    return result


def main() -> int:
    payload = notebook()
    rendered = json.dumps(payload, ensure_ascii=False, indent=1) + "\n"
    OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"{OUTPUT}: {hashlib.sha256(rendered.encode()).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
