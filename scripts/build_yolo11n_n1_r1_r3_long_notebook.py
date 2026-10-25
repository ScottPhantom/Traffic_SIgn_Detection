#!/usr/bin/env python3
"""Build the append-only YOLO11n N1 R1-R3 long-resume Colab notebook."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE_BUILDER = ROOT / "scripts/build_yolo11n_dual_track_r1_notebooks.py"
OUTPUT = ROOT / "detector/colab/yolo11n_n1_r1_r3_long.ipynb"
SOURCE_COMMIT = "d8471ed0cfeca71ae823fc9ecf50625500e1b4be"
SOURCE_QA_SHA256 = "5fd51deea1679263b224fc45531f30a3d0a5aac86b3d044d262446e77a48b92a"
SOURCE_QA_PATH = "docs/review/yolo11n_n1_r1_r2_source_independent_qa_record.md"
SMOKE_QA_PATH = "docs/review/generated/yolo11n_n1_r1_r2_smoke_qa_proof.json"
SMOKE_QA_SHA256 = "84f98827da16884a6c95162e73d00bc6ae3ff1fa80c5f4aff67431d765f4f421"
STATE = "yolo11n_n1_seed_20261018_r1_r1"
RUNNER = "run_yolo11n_n1_r1_r1.py"
ARCHIVE_SHA256 = "5798ad93f552e1f7c36b46a3470fc9f8f85c5125df753786d63e228822299d05"
MANIFEST_SHA256 = "8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da"
WEIGHT_SHA256 = "0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1"
LATEST_SHA256 = "ed42322f480030cd05a5f1bffb30731dad9a75eba5e158883535e078c6debb6a"


def _load_base() -> Any:
    spec = importlib.util.spec_from_file_location("yolo11n_notebook_base", BASE_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load notebook base: {BASE_BUILDER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BASE = _load_base()


def _sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def notebook() -> dict[str, Any]:
    setup = f'''from pathlib import Path

TRACK = 'n1'
MODE = 'resume'
STOP_AFTER = None
REPO_URL = {BASE.REPO_URL!r}
SOURCE_COMMIT = {SOURCE_COMMIT!r}
SOURCE_QA_SHA256 = {SOURCE_QA_SHA256!r}
SMOKE_QA_SHA256 = {SMOKE_QA_SHA256!r}
WEIGHT_SHA256 = {WEIGHT_SHA256!r}
DRIVE_ROOT = Path('/content/drive/MyDrive/CPV301/Traffic_Sign_Detector')
STATE = DRIVE_ROOT / 'M1_D1_Colab/runs/{STATE}'
REPO = Path('/content/Traffic_Sign_Detector')
assert MODE == 'resume' and STOP_AFTER is None

ARCHIVE = DRIVE_ROOT / 'M1_D1_Colab/yolo11n_n1_r1.tar.gz'
ARCHIVE_SHA256 = {ARCHIVE_SHA256!r}
MANIFEST_SHA256 = {MANIFEST_SHA256!r}
LATEST_SHA256 = {LATEST_SHA256!r}
INPUT_ROOT = Path('/content/yolo11n_n1_input')
SOURCE_QA = REPO / {SOURCE_QA_PATH!r}
SMOKE_QA = REPO / {SMOKE_QA_PATH!r}
'''
    preflight = BASE.PREFLIGHT.replace(
        "assert len(WEIGHT_SHA256) == 64",
        "assert len(WEIGHT_SHA256) == 64\nassert len(SMOKE_QA_SHA256) == 64",
    )
    inputs = '''assert ARCHIVE.is_file() and not ARCHIVE.is_symlink()
assert file_hash(ARCHIVE) == ARCHIVE_SHA256
if INPUT_ROOT.exists():
    shutil.rmtree(INPUT_ROOT)
subprocess.run([
    sys.executable, str(REPO / 'detector/colab/extract_cascade_b0_r1.py'),
    str(ARCHIVE), str(INPUT_ROOT),
    '--archive-sha256', ARCHIVE_SHA256,
    '--manifest-sha256', MANIFEST_SHA256,
], check=True)
assert SOURCE_QA.is_file() and not SOURCE_QA.is_symlink()
assert file_hash(SOURCE_QA) == SOURCE_QA_SHA256
assert SMOKE_QA.is_file() and not SMOKE_QA.is_symlink()
assert file_hash(SMOKE_QA) == SMOKE_QA_SHA256
manifest = json.loads((INPUT_ROOT / 'manifest.json').read_text())
proof = json.loads(SMOKE_QA.read_text())
assert manifest['package'] == 'YOLO11N-N1-R1'
assert manifest['test_included'] is False
assert manifest['sealed_test_accessed'] is False
assert manifest['pretrained_weight_sha256'] == WEIGHT_SHA256
assert proof['verdict'] == 'PASS' and proof['stage'] == 'detector'
assert proof['manifest_sha256'] == MANIFEST_SHA256
assert proof['sealed_test_accessed'] is False
latest_path = STATE / 'detector/recovery/latest.json'
assert latest_path.is_file() and not latest_path.is_symlink()
assert file_hash(latest_path) == LATEST_SHA256
latest = json.loads(latest_path.read_text())
assert latest['generation'] == 'epoch-0002'
execution = json.loads((STATE / 'colab_execution.json').read_text())
attempts = execution['execution_attempts']
assert execution['status'] == 'SMOKE_STOP'
assert execution['sealed_test_accessed'] is False
assert [item['mode'] for item in attempts] == ['fresh', 'resume']
assert [item['runtime_digest'] for item in attempts] == proof['runtime_digests']
assert len(set(proof['runtime_digests'])) == 2
subprocess.run(['uv', 'sync', '--frozen'], cwd=REPO / 'detector', check=True)
print({
    'archive_sha256': ARCHIVE_SHA256,
    'manifest_sha256': MANIFEST_SHA256,
    'smoke_qa_sha256': SMOKE_QA_SHA256,
    'resume_from': latest['generation'],
})
'''
    run = f'''command = [
    'uv', 'run', 'python', str(REPO / 'detector/colab/{RUNNER}'),
    'detector', '--root', str(INPUT_ROOT), '--state', str(STATE),
    '--manifest-sha256', MANIFEST_SHA256,
    '--source-qa-record', str(SOURCE_QA), '--source-qa-sha256', SOURCE_QA_SHA256,
    '--mode', MODE,
    '--smoke-qa-proof', str(SMOKE_QA), '--smoke-qa-sha256', SMOKE_QA_SHA256,
]
assert '--stop-after' not in command
environment = dict(os.environ)
environment['PYTHONPATH'] = str(REPO / 'detector')
print('Running:', ' '.join(command))
subprocess.run(command, cwd=REPO / 'detector', env=environment, check=True)
'''
    verify = '''import hashlib
import json
import sqlite3
import stat
import tarfile
import tempfile
from pathlib import Path, PurePosixPath
from urllib.parse import quote


def require_regular(path, label):
    info = path.lstat()
    assert stat.S_ISREG(info.st_mode), f'{label} is not regular'
    assert not path.is_symlink() and info.st_nlink == 1, f'{label} is linked'
    assert info.st_size > 0, f'{label} is empty'
    return info


def hash_regular(path, label):
    before = require_regular(path, label)
    digest = hashlib.sha256()
    with path.open('rb') as reader:
        for chunk in iter(lambda: reader.read(1024 * 1024), b''):
            digest.update(chunk)
    after = path.lstat()
    assert (
        before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns
    ) == (
        after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns
    ), f'{label} changed while being read'
    return digest.hexdigest()


def canonical_sha256(value):
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,
        allow_nan=False,
    ).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def require_safe_directory(path, label):
    assert path.is_absolute(), f'{label} is not absolute'
    current = path
    existing = []
    while True:
        if current.exists() or current.is_symlink():
            existing.append(current)
        if current == current.parent:
            break
        current = current.parent
    for entry in reversed(existing):
        assert not entry.is_symlink(), f'{label} has a symlink component'
        assert entry.is_dir(), f'{label} has a non-directory component'
    assert path.is_dir(), f'{label} is missing'


def validate_log_pair(text, database_path, execution_record, terminal_status, terminal_event):
    lines = text.splitlines()
    assert lines and all(lines), 'train.log is empty or has blank records'
    events = [json.loads(line) for line in lines]
    for event in events:
        assert isinstance(event, dict)
        assert {'time', 'stage', 'event', 'sealed_test_accessed'} <= set(event)
        assert type(event['time']) in {int, float}
        assert event['stage'] == 'detector'
        assert isinstance(event['event'], str)
        assert event['sealed_test_accessed'] is False
    uri = f"file:{quote(str(database_path))}?mode=ro&immutable=1"
    with sqlite3.connect(uri, uri=True) as database:
        assert database.execute('PRAGMA integrity_check').fetchone() == ('ok',)
        schema = database.execute(
            "SELECT type,name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' "
            "ORDER BY type,name"
        ).fetchall()
        assert schema == [(
            'table',
            'logs',
            'CREATE TABLE logs(time REAL, stage TEXT, event TEXT, payload TEXT)',
        )]
        rows = database.execute(
            'SELECT time,stage,event,payload FROM logs ORDER BY rowid'
        ).fetchall()
    expected_rows = [
        (float(event['time']), event['stage'], event['event'], line)
        for event, line in zip(events, lines, strict=True)
    ]
    assert rows == expected_rows, 'SQLite and train.log events differ'
    attempts = [event for event in events if event['event'] == 'ATTEMPT']
    assert execution_record['execution_attempts'] == attempts
    assert execution_record['status'] == terminal_status
    terminal = events[-1]
    assert terminal['event'] == terminal_event
    for key in ('time', 'stage', 'event', 'sealed_test_accessed'):
        assert execution_record[key] == terminal[key]
    assert execution_record['sealed_test_accessed'] is False
    recoveries = [event for event in events if event['event'] == 'RECOVERY_RESTORED']
    assert recoveries
    assert all(event.get('worker_rng_exact_replay') is False for event in recoveries)
    return events


execution_path = STATE / 'colab_execution.json'
text_log_path = STATE / 'train.log'
database_path = STATE / 'DB_logger.db'
latest_path = STATE / 'detector/recovery/latest.json'
for path, label in (
    (execution_path, 'live execution record'),
    (text_log_path, 'live text log'),
    (database_path, 'live SQLite log'),
    (latest_path, 'final checkpoint pointer'),
):
    require_regular(path, label)
execution = json.loads(execution_path.read_text())
latest = json.loads(latest_path.read_text())
live_events = validate_log_pair(
    text_log_path.read_text(), database_path, execution, 'SUCCEEDED', 'SUCCEEDED'
)
assert live_events[-2]['event'] == 'TRAINING_COMPLETE'
assert live_events[-2]['epoch'] == live_events[-1]['epoch'] == 100
assert latest['generation'] == 'epoch-0100'

binding = {
    'manifest': MANIFEST_SHA256,
    'config': proof['config'],
    'stage': 'detector',
}
binding_sha256 = canonical_sha256(binding)
assert set(latest) == {
    'schema_version', 'generation', 'manifest_sha256', 'binding_sha256'
}
assert latest['schema_version'] == 1
assert latest['binding_sha256'] == binding_sha256
assert len(latest['manifest_sha256']) == 64
assert all(character in '0123456789abcdef' for character in latest['manifest_sha256'])
snapshot = STATE / 'detector/recovery/snapshots/epoch-0100'
require_safe_directory(snapshot, 'epoch-0100 snapshot')
require_safe_directory(snapshot / 'weights', 'epoch-0100 weights directory')
checkpoint_manifest_path = snapshot / 'checkpoint_manifest.json'
assert (
    hash_regular(checkpoint_manifest_path, 'epoch-0100 checkpoint manifest')
    == latest['manifest_sha256']
)
checkpoint_manifest = json.loads(checkpoint_manifest_path.read_text())
assert set(checkpoint_manifest) == {
    'schema_version',
    'status',
    'run',
    'completed_epoch',
    'binding',
    'binding_sha256',
    'files',
}
assert checkpoint_manifest['schema_version'] == 1
assert checkpoint_manifest['status'] == 'RECOVERABLE'
assert checkpoint_manifest['run'] == 'D1_yolo11n_n1_detector'
assert checkpoint_manifest['completed_epoch'] == 100
assert checkpoint_manifest['binding'] == binding
assert checkpoint_manifest['binding_sha256'] == binding_sha256
model_members = {
    'weights/last.pt',
    'weights/best.pt',
    'results.csv',
    'args.yaml',
    'run_contract.json',
}
assert isinstance(checkpoint_manifest['files'], list)
assert len(checkpoint_manifest['files']) == len(model_members)
checkpoint_files = {}
for record in checkpoint_manifest['files']:
    assert set(record) == {'path', 'size', 'sha256'}
    assert record['path'] in model_members and record['path'] not in checkpoint_files
    assert type(record['size']) is int and record['size'] > 0
    assert len(record['sha256']) == 64
    assert all(character in '0123456789abcdef' for character in record['sha256'])
    artifact = snapshot / record['path']
    info = require_regular(artifact, f"checkpoint artifact {record['path']}")
    assert info.st_size == record['size']
    assert hash_regular(artifact, f"checkpoint artifact {record['path']}") == record['sha256']
    checkpoint_files[record['path']] = record
assert set(checkpoint_files) == model_members
snapshot_files = set()
for entry in snapshot.rglob('*'):
    assert not entry.is_symlink(), 'checkpoint snapshot contains a symlink'
    if entry.is_file():
        require_regular(entry, 'checkpoint snapshot file')
        snapshot_files.add(entry.relative_to(snapshot).as_posix())
    else:
        assert entry.is_dir(), 'checkpoint snapshot contains a non-file/non-directory'
assert snapshot_files == model_members | {'checkpoint_manifest.json'}

results = STATE / 'detector/results'
archive = results / 'result.tar.gz'
result_manifest_path = results / 'result_manifest.json'
require_regular(archive, 'result archive')
require_regular(result_manifest_path, 'result manifest')
result_manifest = json.loads(result_manifest_path.read_text())
assert result_manifest['stage'] == 'detector'
assert result_manifest['binding'] == binding
assert result_manifest['completed_epoch'] == 100
assert result_manifest['sealed_test_accessed'] is False
assert hash_regular(archive, 'result archive') == result_manifest['archive_sha256']
expected_members = {
    'weights/last.pt',
    'weights/best.pt',
    'results.csv',
    'args.yaml',
    'run_contract.json',
    'train.log',
    'DB_logger.db',
    'colab_execution.json',
}
assert set(result_manifest['members']) == expected_members
for name in model_members:
    checkpoint_record = checkpoint_files[name]
    assert result_manifest['members'][name] == {
        'sha256': checkpoint_record['sha256'],
        'bytes': checkpoint_record['size'],
    }
embedded = {}
with tarfile.open(archive, 'r:gz') as handle:
    entries = handle.getmembers()
    assert len(entries) == len(expected_members)
    assert {entry.name for entry in entries} == expected_members
    for entry in entries:
        member_path = PurePosixPath(entry.name)
        assert entry.isfile()
        assert not member_path.is_absolute()
        assert not any(part in {'', '.', '..'} for part in member_path.parts)
        assert not any(part.casefold() in {'test', 'tests'} for part in member_path.parts)
        reader = handle.extractfile(entry)
        assert reader is not None
        digest = hashlib.sha256()
        payload = bytearray() if entry.name in {
            'train.log', 'DB_logger.db', 'colab_execution.json'
        } else None
        for chunk in iter(lambda: reader.read(1024 * 1024), b''):
            digest.update(chunk)
            if payload is not None:
                payload.extend(chunk)
        assert result_manifest['members'][entry.name] == {
            'sha256': digest.hexdigest(),
            'bytes': entry.size,
        }
        if payload is not None:
            embedded[entry.name] = bytes(payload)

with tempfile.TemporaryDirectory() as temporary:
    archived_database = Path(temporary) / 'DB_logger.db'
    archived_database.write_bytes(embedded['DB_logger.db'])
    archived_execution = json.loads(embedded['colab_execution.json'].decode('utf-8'))
    archived_events = validate_log_pair(
        embedded['train.log'].decode('utf-8'),
        archived_database,
        archived_execution,
        'FINALIZING',
        'TRAINING_COMPLETE',
    )
assert archived_events[-1]['epoch'] == 100
print({
    'status': 'LONG_RUN_PASS',
    'track': TRACK,
    'epoch': 100,
    'archive_sha256': result_manifest['archive_sha256'],
    'archive_members_verified': len(expected_members),
    'live_log_events': len(live_events),
    'worker_rng_exact_replay': False,
    'seal': False,
})
'''
    cells = [
        BASE.markdown(
            "# YOLO11n N1 R1-R3 — long resume from epoch 2 to epoch 100\n\n"
            "Train/validation only. Reuses existing classifiers. Never opens the sealed test.\n",
            "n1-long-title",
        ),
        BASE.code(
            "from google.colab import drive\n\ndrive.mount('/content/drive')\n",
            "n1-long-mount",
        ),
        BASE.code(setup, "n1-long-config"),
        BASE.code(preflight, "n1-long-preflight"),
        BASE.code(inputs, "n1-long-inputs"),
        BASE.code(run, "n1-long-run"),
        BASE.code(verify, "n1-long-verify"),
    ]
    payload = BASE.common_notebook(cells, status="PENDING_R1_R3_LONG_SOURCE_QA")
    serialized = json.dumps(payload, sort_keys=True)
    required = (
        SOURCE_COMMIT,
        SOURCE_QA_SHA256,
        SMOKE_QA_SHA256,
        SMOKE_QA_PATH,
        STATE,
        RUNNER,
        "epoch-0002",
        "epoch-0100",
        "--smoke-qa-proof",
    )
    if any(value not in serialized for value in required):
        raise RuntimeError("R1-R3 notebook is missing an immutable long-resume binding")
    for forbidden in ("export-test", "final-eval", "--split", "--stop-after',"):
        if forbidden in serialized:
            raise RuntimeError(f"R1-R3 notebook contains forbidden route: {forbidden}")
    return payload


def build() -> dict[str, Any]:
    payload = notebook()
    OUTPUT.write_text(
        json.dumps(payload, indent=1, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "schema": 1,
        "package": "YOLO11N-N1-R1-R3-LONG-NOTEBOOK",
        "source_commit": SOURCE_COMMIT,
        "source_qa_sha256": SOURCE_QA_SHA256,
        "smoke_qa_sha256": SMOKE_QA_SHA256,
        "state": STATE,
        "sealed_test_accessed": False,
        "notebook": {
            "path": OUTPUT.relative_to(ROOT).as_posix(),
            "sha256": _sha256(OUTPUT),
            "cells": len(payload["cells"]),
        },
    }


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
