#!/usr/bin/env python3
"""Build immutable-commit Colab smoke notebooks for YOLO11n N54 and N1 R1."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "detector/colab"
REPO_URL = "https://github.com/ScottPhantom/Traffic_SIgn_Detection.git"
SOURCE_COMMIT = "45b7b1fab606032fcfb2956d0207171ae8b4c7f6"
SOURCE_QA_SHA256 = "bcf7470d931d23445785c1103e3c919aca4c696b22738079756572892ce4f632"
WEIGHT_URL = "https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo11n.pt"
WEIGHT_SHA256 = "0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1"
N54_BUNDLE_SHA256 = "7ea344cb1e2c166786d0552f215993969efec9b5f06a9bf49310d4390243d641"
N54_BUNDLE_BYTES = 766_226_800
N54_SIDECAR_SHA256 = "7e0dc5b0144faa5f0be407224eaf8070dd51199fa8a1d2f164b248fd6a06d5b2"
N54_SIDECAR_BYTES = 1_499_866
N54_PARTS = (
    (
        "m1_colab_train_val_backend_r1.tar.gz.part-00",
        99_614_720,
        "53f30f08406fbef5b8451610b2fd44a1f2be42ca6d50f612b68e5ace285e66ff",
    ),
    (
        "m1_colab_train_val_backend_r1.tar.gz.part-01",
        99_614_720,
        "8451fe932760179d4b2e1a9cbdd21fd58744bc6b8f3d2a90e431cece7f546544",
    ),
    (
        "m1_colab_train_val_backend_r1.tar.gz.part-02",
        99_614_720,
        "867c935bf152ddfc3e7919547dccf3682291326b60b956a8100fc1a59b60e98d",
    ),
    (
        "m1_colab_train_val_backend_r1.tar.gz.part-03",
        99_614_720,
        "046fc8ae5d4e0a91196ccd6a6afa422fb1254baea7ae30bc3cab39602b534907",
    ),
    (
        "m1_colab_train_val_backend_r1.tar.gz.part-04",
        99_614_720,
        "6d3751d858232fada5d57e8e892f3e272cd5b9e34efb184971b3f4786842665d",
    ),
    (
        "m1_colab_train_val_backend_r1.tar.gz.part-05",
        99_614_720,
        "938106e4d34743e9b79109feb98d573f317afad44289f792f070f22e3924159b",
    ),
    (
        "m1_colab_train_val_backend_r1.tar.gz.part-06",
        99_614_720,
        "3497c1a10314c74d4b81ba9a5a49653b16ba2e2d52b424fd7655623547cb6408",
    ),
    (
        "m1_colab_train_val_backend_r1.tar.gz.part-07",
        68_923_760,
        "5f5ca85bc392310b2b5693ad9d0723f046eca9fd7980b45c944f22a3b3bc0eea",
    ),
)
N1_BUNDLE_SHA256 = "5798ad93f552e1f7c36b46a3470fc9f8f85c5125df753786d63e228822299d05"
N1_MANIFEST_SHA256 = "8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da"


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def markdown(source: str, identifier: str) -> dict[str, Any]:
    return {
        "cell_type": "markdown",
        "id": identifier,
        "metadata": {},
        "source": source.splitlines(keepends=True),
    }


def code(source: str, identifier: str) -> dict[str, Any]:
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": identifier,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


def common_notebook(cells: list[dict[str, Any]], *, status: str) -> dict[str, Any]:
    return {
        "cells": cells,
        "metadata": {
            "accelerator": "GPU",
            "colab": {"gpuType": "L4", "provenance": []},
            "kernelspec": {"display_name": "Python 3", "name": "python3"},
            "language_info": {"name": "python"},
            "yolo11n_dual_track_r1_status": status,
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def common_setup(track: str, mode: str, stop_after: int) -> str:
    state_suffix = (
        "yolo11n_n54_seed_20261018_r1"
        if track == "n54"
        else "yolo11n_n1_seed_20261018_r1"
    )
    return f'''from pathlib import Path

TRACK = {track!r}
MODE = {mode!r}
STOP_AFTER = {stop_after}
REPO_URL = {REPO_URL!r}
SOURCE_COMMIT = {SOURCE_COMMIT!r}
SOURCE_QA_SHA256 = {SOURCE_QA_SHA256!r}
WEIGHT_URL = {WEIGHT_URL!r}
WEIGHT_SHA256 = {WEIGHT_SHA256!r}
DRIVE_ROOT = Path('/content/drive/MyDrive/CPV301/Traffic_Sign_Detector')
STATE = DRIVE_ROOT / 'M1_D1_Colab/runs/{state_suffix}'
REPO = Path('/content/Traffic_Sign_Detector')
assert MODE in {{'fresh', 'resume'}}
assert (MODE, STOP_AFTER) in {{('fresh', 1), ('resume', 2)}}
'''


PREFLIGHT = '''import hashlib
import json
import os
import shutil
import subprocess
import sys

def file_hash(path):
    value = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()

gpu_name = subprocess.run(
    ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
    check=True, capture_output=True, text=True,
).stdout.strip()
assert gpu_name == 'NVIDIA L4', gpu_name
assert len(SOURCE_COMMIT) == 40
assert len(SOURCE_QA_SHA256) == 64
assert len(WEIGHT_SHA256) == 64
if REPO.exists():
    shutil.rmtree(REPO)
subprocess.run(['git', 'clone', '--filter=blob:none', REPO_URL, str(REPO)], check=True)
subprocess.run(['git', 'checkout', '--detach', SOURCE_COMMIT], cwd=REPO, check=True)
observed = subprocess.run(
    ['git', 'rev-parse', 'HEAD'], cwd=REPO, check=True,
    capture_output=True, text=True,
).stdout.strip()
assert observed == SOURCE_COMMIT
assert not subprocess.run(
    ['git', 'status', '--porcelain'], cwd=REPO, check=True,
    capture_output=True, text=True,
).stdout.strip()
if shutil.which('uv') is None:
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'uv==0.11.14'], check=True)
print({'gpu': gpu_name, 'checkout': observed, 'track': TRACK, 'mode': MODE})
'''


def n54_notebook(mode: str, stop_after: int) -> dict[str, Any]:
    setup = common_setup("n54", mode, stop_after) + f'''
N54_ROOT = DRIVE_ROOT / 'M1_D1_Colab'
DRIVE_BUNDLE = N54_ROOT / 'm1_colab_train_val_backend_r1.tar.gz'
SIDECAR = N54_ROOT / 'm1_colab_train_val_backend_r1.tar.gz.manifest.json'
BUNDLE_SHA256 = {N54_BUNDLE_SHA256!r}
BUNDLE_BYTES = {N54_BUNDLE_BYTES}
SIDECAR_SHA256 = {N54_SIDECAR_SHA256!r}
SIDECAR_BYTES = {N54_SIDECAR_BYTES}
PART_SPECS = {N54_PARTS!r}
SOURCE_QA = REPO / 'docs/review/yolo11n_dual_track_r1_source_independent_qa_record.md'
'''
    inputs = '''import os
import urllib.request

assert SIDECAR.is_file() and not SIDECAR.is_symlink()
assert SIDECAR.stat().st_size == SIDECAR_BYTES
assert file_hash(SIDECAR) == SIDECAR_SHA256
if DRIVE_BUNDLE.is_file():
    assert not DRIVE_BUNDLE.is_symlink()
    BUNDLE = DRIVE_BUNDLE
    bundle_source = 'single_archive'
else:
    parts = []
    for name, expected_bytes, expected_hash in PART_SPECS:
        part = N54_ROOT / name
        assert part.is_file() and not part.is_symlink()
        assert part.stat().st_size == expected_bytes
        assert file_hash(part) == expected_hash
        parts.append(part)
    BUNDLE = Path('/content/m1_colab_train_val_backend_r1.tar.gz')
    if BUNDLE.exists():
        assert BUNDLE.is_file() and not BUNDLE.is_symlink()
    else:
        with BUNDLE.open('xb') as destination:
            for part in parts:
                with part.open('rb') as source:
                    for chunk in iter(lambda: source.read(1024 * 1024), b''):
                        destination.write(chunk)
    bundle_source = 'verified_drive_parts'
assert BUNDLE.stat().st_size == BUNDLE_BYTES
assert file_hash(BUNDLE) == BUNDLE_SHA256
assert SOURCE_QA.is_file() and file_hash(SOURCE_QA) == SOURCE_QA_SHA256
if MODE == 'fresh':
    assert not STATE.exists(), STATE
else:
    assert (STATE / 'recovery/latest.json').is_file()
weight = REPO / 'models/pretrained/yolo11n.pt'
weight.parent.mkdir(parents=True, exist_ok=True)
if weight.exists():
    assert weight.is_file() and not weight.is_symlink()
    assert file_hash(weight) == WEIGHT_SHA256
else:
    partial = weight.with_suffix('.partial')
    assert not partial.exists()
    urllib.request.urlretrieve(WEIGHT_URL, partial)
    assert file_hash(partial) == WEIGHT_SHA256
    os.replace(partial, weight)
assert file_hash(weight) == WEIGHT_SHA256
print({
    'bundle_source': bundle_source,
    'bundle_sha256': BUNDLE_SHA256,
    'weight_sha256': WEIGHT_SHA256,
})
'''
    run = '''command = [
    sys.executable, str(REPO / 'detector/colab/run_yolo11n_n54_r1.py'),
    '--repo-root', str(REPO),
    '--bundle', str(BUNDLE),
    '--bundle-sha256', BUNDLE_SHA256,
    '--state-dir', str(STATE),
    '--mode', MODE,
    '--expected-checkout', SOURCE_COMMIT,
    '--source-qa-record', str(SOURCE_QA),
    '--source-qa-sha256', SOURCE_QA_SHA256,
    '--stop-after-epoch', str(STOP_AFTER),
    '--seed', '20261018', '--epochs', '100', '--imgsz', '1280',
    '--batch', '4', '--workers', '4', '--fraction', '1.0',
    '--patience', '30', '--device', '0', '--tag', 'n54_r1', '--cos-lr',
]
print('Running:', ' '.join(command))
subprocess.run(command, check=True)
'''
    verify = '''execution = json.loads((STATE / 'colab_execution.json').read_text())
latest = json.loads((STATE / 'recovery/latest.json').read_text())
attempts_path = STATE / 'n54_execution_attempts.jsonl'
attempts = [json.loads(line) for line in attempts_path.read_text().splitlines()]
assert execution['status'] == 'PAUSED_FOR_RESUME'
assert execution['sealed_test_accessed'] is False
assert latest['generation'] == f'epoch-{STOP_AFTER:04d}'
assert attempts[-1]['completed_epoch'] == STOP_AFTER
assert attempts[-1]['sealed_test_accessed'] is False
if MODE == 'fresh':
    assert len(attempts) == 1 and attempts[0]['leg'] == 'fresh_epoch_1'
else:
    assert len(attempts) == 2 and attempts[1]['leg'] == 'resume_epoch_2'
    assert attempts[0]['runtime_digest'] != attempts[1]['runtime_digest']
print({'status': 'SMOKE_PASS', 'track': TRACK, 'epoch': STOP_AFTER, 'seal': False})
'''
    title = f"# YOLO11n N54 R1 — {mode} smoke to epoch {stop_after}\n\n"
    title += "Train/validation only. Requires NVIDIA L4. Never opens the sealed test.\n"
    return common_notebook(
        [
            markdown(title, f"n54-{mode}-title"),
            code(
                "from google.colab import drive\n\ndrive.mount('/content/drive')\n",
                f"n54-{mode}-mount",
            ),
            code(setup, f"n54-{mode}-config"),
            code(PREFLIGHT, f"n54-{mode}-preflight"),
            code(inputs, f"n54-{mode}-inputs"),
            code(run, f"n54-{mode}-run"),
            code(verify, f"n54-{mode}-verify"),
        ],
        status="PENDING_LIVE_SMOKE",
    )


def n1_notebook(mode: str, stop_after: int) -> dict[str, Any]:
    setup = common_setup("n1", mode, stop_after) + f'''
ARCHIVE = DRIVE_ROOT / 'M1_D1_Colab/yolo11n_n1_r1.tar.gz'
ARCHIVE_SHA256 = {N1_BUNDLE_SHA256!r}
MANIFEST_SHA256 = {N1_MANIFEST_SHA256!r}
INPUT_ROOT = Path('/content/yolo11n_n1_input')
SOURCE_QA = REPO / 'docs/review/yolo11n_dual_track_r1_source_independent_qa_record.md'
'''
    inputs = '''import socket

assert ARCHIVE.is_file() and not ARCHIVE.is_symlink()
assert file_hash(ARCHIVE) == ARCHIVE_SHA256
if INPUT_ROOT.exists():
    shutil.rmtree(INPUT_ROOT)
subprocess.run([
    sys.executable, str(REPO / 'detector/colab/extract_cascade_b0_r1.py'),
    str(ARCHIVE), str(INPUT_ROOT),
    '--archive-sha256', ARCHIVE_SHA256,
    '--manifest-sha256', MANIFEST_SHA256,
], check=True)
assert SOURCE_QA.is_file() and file_hash(SOURCE_QA) == SOURCE_QA_SHA256
manifest = json.loads((INPUT_ROOT / 'manifest.json').read_text())
assert manifest['package'] == 'YOLO11N-N1-R1'
assert manifest['test_included'] is False
assert manifest['sealed_test_accessed'] is False
assert manifest['pretrained_weight_sha256'] == WEIGHT_SHA256
if MODE == 'fresh':
    assert not STATE.exists(), STATE
else:
    assert (STATE / 'detector/recovery/latest.json').is_file()
    prior_execution = json.loads((STATE / 'colab_execution.json').read_text())
    prior_attempts = prior_execution['execution_attempts']
    assert len(prior_attempts) == 1 and prior_attempts[0]['mode'] == 'fresh'
    boot_id = Path('/proc/sys/kernel/random/boot_id').read_text()
    current_runtime = hashlib.sha256((socket.gethostname() + boot_id).encode()).hexdigest()
    assert current_runtime != prior_attempts[0]['runtime_digest'], 'A new L4 runtime is required'
subprocess.run(['uv', 'sync', '--frozen'], cwd=REPO / 'detector', check=True)
print({'archive_sha256': ARCHIVE_SHA256, 'manifest_sha256': MANIFEST_SHA256})
'''
    run = '''command = [
    'uv', 'run', 'python', str(REPO / 'detector/colab/run_yolo11n_n1_r1.py'),
    'detector', '--root', str(INPUT_ROOT), '--state', str(STATE),
    '--manifest-sha256', MANIFEST_SHA256,
    '--source-qa-record', str(SOURCE_QA), '--source-qa-sha256', SOURCE_QA_SHA256,
    '--mode', MODE, '--stop-after', str(STOP_AFTER),
]
environment = dict(os.environ)
environment['PYTHONPATH'] = str(REPO / 'detector')
print('Running:', ' '.join(command))
subprocess.run(command, cwd=REPO / 'detector', env=environment, check=True)
'''
    verify = '''execution = json.loads((STATE / 'colab_execution.json').read_text())
latest = json.loads((STATE / 'detector/recovery/latest.json').read_text())
assert execution['sealed_test_accessed'] is False
assert execution['status'] == 'SMOKE_STOP'
assert latest['generation'] == f'epoch-{STOP_AFTER:04d}'
attempts = execution['execution_attempts']
assert attempts[-1]['mode'] == MODE
if MODE == 'fresh':
    assert len(attempts) == 1
else:
    assert len(attempts) == 2
    assert attempts[0]['runtime_digest'] != attempts[1]['runtime_digest']
print({'status': 'SMOKE_PASS', 'track': TRACK, 'epoch': STOP_AFTER, 'seal': False})
'''
    title = f"# YOLO11n N1 R1 — {mode} smoke to epoch {stop_after}\n\n"
    title += "Train/validation only. Classifiers are not retrained. Never opens the sealed test.\n"
    return common_notebook(
        [
            markdown(title, f"n1-{mode}-title"),
            code(
                "from google.colab import drive\n\ndrive.mount('/content/drive')\n",
                f"n1-{mode}-mount",
            ),
            code(setup, f"n1-{mode}-config"),
            code(PREFLIGHT, f"n1-{mode}-preflight"),
            code(inputs, f"n1-{mode}-inputs"),
            code(run, f"n1-{mode}-run"),
            code(verify, f"n1-{mode}-verify"),
        ],
        status="PENDING_LIVE_SMOKE",
    )


def build() -> dict[str, Any]:
    outputs = {
        "yolo11n_n54_r1_fresh.ipynb": n54_notebook("fresh", 1),
        "yolo11n_n54_r1_resume.ipynb": n54_notebook("resume", 2),
        "yolo11n_n1_r1_fresh.ipynb": n1_notebook("fresh", 1),
        "yolo11n_n1_r1_resume.ipynb": n1_notebook("resume", 2),
    }
    result: dict[str, Any] = {
        "schema": 1,
        "source_commit": SOURCE_COMMIT,
        "source_qa_sha256": SOURCE_QA_SHA256,
        "notebooks": {},
        "sealed_test_accessed": False,
    }
    for name, payload in outputs.items():
        path = OUTPUT_DIR / name
        path.write_text(
            json.dumps(payload, indent=1, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        result["notebooks"][name] = {"sha256": sha256(path), "cells": len(payload["cells"])}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(build(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
