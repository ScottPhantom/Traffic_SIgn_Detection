from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/build_yolo11n_n1_r1_r3_long_notebook.py"
NOTEBOOK = ROOT / "detector/colab/yolo11n_n1_r1_r3_long.ipynb"


def load_builder():
    spec = importlib.util.spec_from_file_location("yolo11n_n1_r1_r3_long_builder", BUILDER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def notebook_text() -> str:
    payload = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    return "\n".join("".join(cell.get("source", [])) for cell in payload["cells"])


def test_long_notebook_is_reproducible_and_hash_pinned() -> None:
    builder = load_builder()
    first = builder.build()
    second = builder.build()
    assert first == second
    assert first["sealed_test_accessed"] is False
    assert first["source_commit"] == builder.SOURCE_COMMIT
    assert first["source_qa_sha256"] == builder.SOURCE_QA_SHA256
    assert first["smoke_qa_sha256"] == builder.SMOKE_QA_SHA256
    assert first["notebook"]["cells"] == 7
    text = notebook_text()
    for value in (
        builder.SOURCE_COMMIT,
        builder.SOURCE_QA_SHA256,
        builder.SMOKE_QA_SHA256,
        builder.SMOKE_QA_PATH,
        builder.STATE,
        builder.RUNNER,
        builder.LATEST_SHA256,
    ):
        assert value in text


def test_long_command_is_resume_without_smoke_stop_or_test_route() -> None:
    load_builder().build()
    text = notebook_text()
    assert "MODE = 'resume'" in text
    assert "STOP_AFTER = None" in text
    assert "--smoke-qa-proof" in text
    assert "assert '--stop-after' not in command" in text
    assert "'--stop-after'," not in text
    assert "export-test" not in text
    assert "final-eval" not in text
    assert "'--split'" not in text
    assert "latest['generation'] == 'epoch-0002'" in text
    assert "latest['generation'] == 'epoch-0100'" in text
    assert "execution_record['status'] == terminal_status" in text
    assert "execution, 'SUCCEEDED', 'SUCCEEDED'" in text
    assert "result.tar.gz" in text and "result_manifest.json" in text


def test_long_notebook_fails_closed_on_bindings_and_seal() -> None:
    load_builder().build()
    text = notebook_text()
    assert "gpu_name == 'NVIDIA L4'" in text
    assert "file_hash(SOURCE_QA) == SOURCE_QA_SHA256" in text
    assert "file_hash(SMOKE_QA) == SMOKE_QA_SHA256" in text
    assert "file_hash(latest_path) == LATEST_SHA256" in text
    assert "manifest['test_included'] is False" in text
    assert "manifest['sealed_test_accessed'] is False" in text
    assert "proof['sealed_test_accessed'] is False" in text
    assert "execution['sealed_test_accessed'] is False" in text
    assert "result_manifest['sealed_test_accessed'] is False" in text


def test_long_notebook_verifies_logs_archive_members_and_replay_limit() -> None:
    load_builder().build()
    text = notebook_text()
    assert "(text_log_path, 'live text log')" in text
    assert "(database_path, 'live SQLite log')" in text
    assert "require_regular(path, label)" in text
    assert "PRAGMA integrity_check" in text
    assert "SQLite and train.log events differ" in text
    assert "changed while being read" in text
    assert "execution_record['execution_attempts'] == attempts" in text
    assert "worker_rng_exact_replay') is False" in text
    assert "set(result_manifest['members']) == expected_members" in text
    assert "tarfile.open(archive, 'r:gz')" in text
    assert "result_manifest['members'][entry.name]" in text
    assert "archived_database.write_bytes(embedded['DB_logger.db'])" in text
    assert "'FINALIZING'" in text and "'TRAINING_COMPLETE'" in text
    assert "'SUCCEEDED'" in text


def test_long_notebook_binds_result_to_epoch_100_checkpoint_store() -> None:
    load_builder().build()
    text = notebook_text()
    assert "snapshot = STATE / 'detector/recovery/snapshots/epoch-0100'" in text
    assert "set(latest) ==" in text
    assert "latest['binding_sha256'] == binding_sha256" in text
    assert "hash_regular(checkpoint_manifest_path" in text
    assert "== latest['manifest_sha256']" in text
    assert "checkpoint_manifest['completed_epoch'] == 100" in text
    assert "checkpoint_manifest['binding'] == binding" in text
    assert "snapshot_files == model_members | {'checkpoint_manifest.json'}" in text
    assert "checkpoint_files[record['path']] = record" in text
    assert "result_manifest['members'][name] ==" in text
