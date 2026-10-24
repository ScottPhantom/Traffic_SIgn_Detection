#!/usr/bin/env python3
"""Generate the fail-closed GitHub/Colab launch template for VGG16-54 R1."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "detector/colab/vgg16_54_r1.ipynb"


def markdown(source: str) -> dict[str, object]:
    return {"cell_type": "markdown", "metadata": {}, "source": source.splitlines(keepends=True)}


def code(source: str) -> dict[str, object]:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


def notebook() -> dict[str, object]:
    return {
        "cells": [
            markdown(
                "# VGG16-54 R1 — preparation template\n\n"
                "Train/validation only. This template intentionally fails until the Owner "
                "configuration decision, independent source QA, immutable Git commit and "
                "Drive hashes are filled. Do not run alongside another job on the same L4. "
                "Never upload or open the sealed test.\n"
            ),
            code(
                "from google.colab import drive\n\n"
                "drive.mount('/content/drive')\n"
            ),
            code(
                "from pathlib import Path\n\n"
                "DRIVE = Path('/content/drive/MyDrive/CPV301/Traffic_Sign_Detector/M1_D1_Colab')\n"
                "ARCHIVE = DRIVE / 'cascade_b0_r1.tar.gz'\n"
                "ARCHIVE_SHA256 = "
                "'5a5a9afbf06b9bc2f55546f5a49738ed9ca9ac6f96a78931f78669e71dab4806'\n"
                "MANIFEST_SHA256 = "
                "'bae147b6f7c6f80ac973923df4b60fd31b6587221fe75eaa2d9ed4b93ee6a51b'\n"
                "REPO_URL = 'https://github.com/ScottPhantom/Traffic_SIgn_Detection.git'\n"
                "CHECKOUT_COMMIT = 'PENDING_PUSHED_IMMUTABLE_COMMIT'\n"
                "OWNER_APPROVAL = DRIVE / 'vgg16_54_r1_owner_approval.json'\n"
                "OWNER_APPROVAL_SHA256 = 'PENDING_OWNER_APPROVAL'\n"
                "SOURCE_QA = DRIVE / 'vgg16_54_r1_source_qa_proof.json'\n"
                "SOURCE_QA_SHA256 = 'PENDING_INDEPENDENT_QA'\n"
                "SMOKE_QA = None\n"
                "SMOKE_QA_SHA256 = None\n"
                "MODE = 'fresh'\n"
                "STOP_AFTER = 1\n"
                "STATE = DRIVE / 'runs/vgg16_54_seed_20261018_r1'\n"
                "ROOT = Path('/content/vgg16_54_input')\n"
                "REPO = Path('/content/Traffic_Sign_Detector')\n"
            ),
            code(
                "import hashlib\n"
                "import subprocess\n\n"
                "def sha256(path):\n"
                "    value = hashlib.sha256()\n"
                "    with path.open('rb') as handle:\n"
                "        for chunk in iter(lambda: handle.read(1024 * 1024), b''):\n"
                "            value.update(chunk)\n"
                "    return value.hexdigest()\n\n"
                "assert len(CHECKOUT_COMMIT) == 40 and all(\n"
                "    c in '0123456789abcdef' for c in CHECKOUT_COMMIT\n"
                ")\n"
                "for value in (OWNER_APPROVAL_SHA256, SOURCE_QA_SHA256):\n"
                "    assert len(value) == 64 and all(c in '0123456789abcdef' for c in value)\n"
                "assert sha256(ARCHIVE) == ARCHIVE_SHA256\n"
                "subprocess.run(['nvidia-smi'], check=True)\n"
            ),
            code(
                "import shutil\n"
                "import subprocess\n\n"
                "assert not REPO.exists(), 'Use a fresh runtime checkout'\n"
                "subprocess.run(\n"
                "    ['git', 'clone', '--filter=blob:none', REPO_URL, str(REPO)], check=True\n"
                ")\n"
                "subprocess.run(\n"
                "    ['git', 'checkout', '--detach', CHECKOUT_COMMIT], cwd=REPO, check=True\n"
                ")\n"
                "observed = subprocess.check_output(\n"
                "    ['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True\n"
                ").strip()\n"
                "assert observed == CHECKOUT_COMMIT\n"
                "subprocess.run(['pip', 'install', '-q', 'uv==0.11.14'], check=True)\n"
                "subprocess.run(['uv', 'sync', '--frozen'], cwd=REPO / 'detector', check=True)\n"
            ),
            code(
                "import subprocess\n"
                "import sys\n\n"
                "assert not ROOT.exists(), 'Use a fresh extraction destination'\n"
                "subprocess.run([\n"
                "    sys.executable, str(REPO / 'detector/colab/extract_cascade_b0_r1.py'),\n"
                "    str(ARCHIVE), str(ROOT), '--archive-sha256', ARCHIVE_SHA256,\n"
                "    '--manifest-sha256', MANIFEST_SHA256,\n"
                "], check=True)\n"
            ),
            code(
                "import subprocess\n\n"
                "command = [\n"
                "    'uv', 'run', 'python', 'colab/run_vgg16_54_r1.py',\n"
                "    '--root', str(ROOT), '--state', str(STATE),\n"
                "    '--bundle-manifest-sha256', MANIFEST_SHA256,\n"
                "    '--owner-approval', str(OWNER_APPROVAL),\n"
                "    '--owner-approval-sha256', OWNER_APPROVAL_SHA256,\n"
                "    '--source-qa', str(SOURCE_QA), '--source-qa-sha256', SOURCE_QA_SHA256,\n"
                "    '--mode', MODE,\n"
                "]\n"
                "if STOP_AFTER is not None:\n"
                "    command += ['--stop-after', str(STOP_AFTER)]\n"
                "else:\n"
                "    command += [\n"
                "        '--smoke-qa', str(SMOKE_QA),\n"
                "        '--smoke-qa-sha256', SMOKE_QA_SHA256,\n"
                "    ]\n"
                "subprocess.run(command, cwd=REPO / 'detector', check=True)\n"
            ),
            code(
                "import json\n"
                "import sqlite3\n\n"
                "execution = json.loads((STATE / 'colab_execution.json').read_text())\n"
                "print(json.dumps(execution, indent=2, ensure_ascii=False))\n"
                "with sqlite3.connect(STATE / 'DB_logger.db') as database:\n"
                "    query = (\n"
                "        'SELECT time, stage, event, payload FROM logs '\n"
                "        'ORDER BY rowid DESC LIMIT 20'\n"
                "    )\n"
                "    for row in database.execute(query):\n"
                "        print(row)\n"
                "assert execution['sealed_test_accessed'] is False\n"
            ),
            markdown(
                "## Resume protocol\n\n"
                "After independent QA of epoch 1, disconnect this runtime. On a genuinely new "
                "L4 runtime set `MODE='resume'`, `STOP_AFTER=2`, rerun all cells, then obtain "
                "independent smoke artifact QA. Only after that QA PASS set `STOP_AFTER=None` "
                "and fill the two smoke-proof anchors.\n"
            ),
        ],
        "metadata": {
            "accelerator": "GPU",
            "colab": {"gpuType": "L4", "provenance": []},
            "kernelspec": {"display_name": "Python 3", "name": "python3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> None:
    payload = json.dumps(notebook(), indent=1, ensure_ascii=False) + "\n"
    OUTPUT.write_text(payload, encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
