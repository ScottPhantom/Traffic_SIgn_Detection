from __future__ import annotations

import hashlib
import importlib.util
import json
import logging
import sqlite3
import sys
import tarfile
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative: str) -> ModuleType:
    path = REPO_ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


bundle = load_module("test_m1_colab_bundle", "scripts/build_m1_colab_bundle.py")
runner = load_module("test_m1_colab_runner", "detector/colab/run_d1_colab.py")


@pytest.mark.parametrize(
    "name",
    ("../test.jpg", "/absolute.jpg", "train/../../test.jpg", "train\\test.jpg", "./x"),
)
def test_bundle_rejects_unsafe_member_names(name: str) -> None:
    with pytest.raises(RuntimeError, match="unsafe archive member"):
        bundle.safe_member_name(name)


def test_bundle_roster_is_train_val_only_and_exact() -> None:
    records, metadata = bundle.expected_records(REPO_ROOT)
    assert len(records) == 1912 + 376 + 1800 + 1800
    assert {record["source_split"] for record in records} == {"train", "val"}
    assert metadata["counts"] == {
        "raw_train_images": 1912,
        "raw_val_images": 376,
        "wp35_train_images": 1800,
        "wp35_train_labels": 1800,
    }
    raw_names = {Path(record["path"]).stem for record in records if record["kind"] == "raw_image"}
    export = bundle.load_export_builder(REPO_ROOT)
    test_stems = set(export.derive(REPO_ROOT)["lists"]["test"])
    assert raw_names.isdisjoint(test_stems)


def test_bundle_rejects_non_regular_tar_member(tmp_path: Path) -> None:
    archive = tmp_path / "bad.tar.gz"
    with tarfile.open(archive, "w:gz") as handle:
        link = tarfile.TarInfo(bundle.MANIFEST_MEMBER)
        link.type = tarfile.SYMTYPE
        link.linkname = "elsewhere"
        handle.addfile(link)
    with pytest.raises(RuntimeError, match="not a regular file"):
        bundle.read_archive_manifest(archive)


def test_manifest_policy_cannot_claim_test_or_symlink_content() -> None:
    manifest = {
        "schema_version": 1,
        "package": bundle.PACKAGE,
        "status": bundle.STATUS,
        "allowed_splits": ["train", "val"],
        "test_included": False,
        "regular_files_only": True,
        "repo_git_commit": "a" * 40,
        "export_manifest_sha256": "b" * 64,
        "detector_lock_sha256": "c" * 64,
        "class_map_sha256": "d" * 64,
        "train_stem_list_sha256": "e" * 64,
        "val_stem_list_sha256": "f" * 64,
        "sealed_test_stem_list_sha256": "0" * 64,
        "counts": {},
        "file_count": 0,
        "files": [],
    }
    bundle._validate_manifest_shape(manifest)
    manifest["test_included"] = True
    with pytest.raises(RuntimeError, match="split policy"):
        bundle._validate_manifest_shape(manifest)


def test_bundle_builder_refuses_existing_sidecar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "bundle.tar.gz"
    sidecar = tmp_path / "bundle.tar.gz.manifest.json"
    sidecar.write_text("sentinel", encoding="utf-8")
    monkeypatch.setattr(bundle, "require_clean_checkout", lambda _root: None)
    with pytest.raises(RuntimeError, match="refused to overwrite"):
        bundle.build_archive(REPO_ROOT, archive)
    assert sidecar.read_text(encoding="utf-8") == "sentinel"


def test_colab_logger_persists_reference_compatible_sqlite_schema(tmp_path: Path) -> None:
    logger, text_path, database_path = runner.configure_logging(tmp_path)
    logger.info("Training start")
    for handler in logger.handlers:
        handler.flush()
        handler.close()
    logger.handlers.clear()
    assert text_path.is_file()
    with sqlite3.connect(database_path) as connection:
        columns = [row[1] for row in connection.execute("PRAGMA table_info(logs)")]
        row = connection.execute(
            "SELECT level, logger, message FROM logs ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert columns == ["id", "timestamp", "level", "logger", "message"]
    assert row is not None
    assert row[0] == "INFO"
    assert row[1] == runner.LOGGER_NAME
    assert "Training start" in row[2]


def test_colab_notebook_is_unexecuted_and_never_exports_test() -> None:
    path = REPO_ROOT / "detector/colab/d1_train.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    assert notebook["nbformat"] == 4
    code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    assert all(cell.get("execution_count") is None for cell in code_cells)
    source = "\n".join("".join(cell["source"]) for cell in notebook["cells"])
    assert "m1_colab_train_val.tar.gz" in source
    assert "--download-approved-weight" in source
    assert "export-test" not in source
    assert "--final-eval" not in source


def test_runner_cli_requires_explicit_paths() -> None:
    with pytest.raises(SystemExit):
        runner.parser().parse_args([])
    logger = logging.getLogger(runner.LOGGER_NAME)
    logger.handlers.clear()


def test_runner_has_no_frozen_sync_bypass(tmp_path: Path) -> None:
    required = [
        "--repo-root",
        str(tmp_path),
        "--bundle",
        str(tmp_path / "bundle.tar.gz"),
        "--state-dir",
        str(tmp_path / "state"),
    ]
    with pytest.raises(SystemExit):
        runner.parser().parse_args([*required, "--skip-sync"])


def test_colab_subprocess_environment_forces_headless_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MPLBACKEND", "module://matplotlib_inline.backend_inline")
    environment = runner.colab_subprocess_environment()
    assert environment["MPLBACKEND"] == "Agg"
    assert environment["WANDB_DISABLED"] == "true"
    assert environment["DO_NOT_TRACK"] == "1"
    assert environment["ULTRALYTICS_HUB"] == "false"


def synthetic_run_contract() -> dict[str, object]:
    return {
        "model": {"path": "/repo/models/pretrained/yolo11s.pt"},
        "train_args": {
            "seed": 20261018,
            "epochs": 1,
            "imgsz": 1280,
            "batch": 8,
            "device": "0",
            "workers": 4,
            "fraction": 1.0,
            "patience": 30,
            "plots": False,
        },
        "contract": {
            "split_stem_sha256": {"train": "train-hash", "val": "val-hash"}
        },
    }


def synthetic_execution(repo_root: Path, run_dir: Path) -> dict[str, object]:
    return {
        "status": "SUCCEEDED",
        "started_at": "2026-10-19T00:00:00+00:00",
        "finished_at": "2026-10-19T00:01:00+00:00",
        "repo_root": str(repo_root),
        "bundle": "/drive/bundle.tar.gz",
        "bundle_sha256": "a" * 64,
        "seed": 20261018,
        "epochs": 1,
        "imgsz": 1280,
        "batch": 8,
        "device": "0",
        "tag": "colab_smoke",
        "sealed_test_accessed": False,
        "steps_completed": list(runner.REQUIRED_STEPS),
        "error": None,
        "split_stem_sha256": {"train": "train-hash", "val": "val-hash"},
        "train_command": [
            "uv",
            "run",
            "python",
            "-m",
            "m1.cli",
            "train",
            "--seed",
            "20261018",
            "--model",
            "/repo/models/pretrained/yolo11s.pt",
            "--epochs",
            "1",
            "--imgsz",
            "1280",
            "--batch",
            "8",
            "--device",
            "0",
            "--workers",
            "4",
            "--fraction",
            "1.0",
            "--patience",
            "30",
            "--tag",
            "colab_smoke",
        ],
        "run_dir": str(run_dir),
    }


def test_execution_validator_rejects_failed_sealed_or_unsynchronized_evidence(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    run_dir = repo_root / "results/experiments/run"
    run_dir.mkdir(parents=True)
    execution_path = tmp_path / "colab_execution.json"
    execution = synthetic_execution(repo_root, run_dir)
    for field, value in (
        ("status", "FAILED"),
        ("sealed_test_accessed", True),
        (
            "steps_completed",
            [
                step
                for step in runner.REQUIRED_STEPS
                if step != "detector_lock_synchronized"
            ],
        ),
    ):
        candidate = {**execution, field: value}
        execution_path.write_text(json.dumps(candidate), encoding="utf-8")
        with pytest.raises(RuntimeError):
            runner.validate_execution_record(
                execution_path, run_dir, synthetic_run_contract()
            )


def test_execution_validator_rejects_command_contract_mismatch(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    run_dir = repo_root / "results/experiments/run"
    run_dir.mkdir(parents=True)
    execution = synthetic_execution(repo_root, run_dir)
    command = list(execution["train_command"])
    command[command.index("--epochs") + 1] = "999"
    execution["train_command"] = command
    execution_path = tmp_path / "colab_execution.json"
    execution_path.write_text(json.dumps(execution), encoding="utf-8")
    with pytest.raises(RuntimeError, match="differs from run_contract"):
        runner.validate_execution_record(execution_path, run_dir, synthetic_run_contract())


def test_result_packager_rejects_qa_failed_evidence(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    run_dir = repo_root / "results/experiments/run"
    for relative in (
        "weights/best.pt",
        "weights/last.pt",
        "results.csv",
        "args.yaml",
        "run_contract.json",
    ):
        path = run_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(synthetic_run_contract()) if relative == "run_contract.json" else "x"
        path.write_text(payload, encoding="utf-8")
    execution_path = tmp_path / "colab_execution.json"
    execution = synthetic_execution(repo_root, run_dir)
    execution.update(status="FAILED", sealed_test_accessed=True)
    execution_path.write_text(json.dumps(execution), encoding="utf-8")
    text_log = tmp_path / "colab_train.log"
    text_log.write_text("x", encoding="utf-8")
    database = tmp_path / "DB_logger.db"
    database.write_bytes(b"not sqlite")
    with pytest.raises((RuntimeError, ValueError)):
        runner.package_run(
            run_dir,
            execution_path,
            text_log,
            database,
            tmp_path / "result.tar.gz",
        )
    assert not (tmp_path / "result.tar.gz").exists()


def test_sqlite_validator_requires_real_schema_epoch_and_terminal_events(tmp_path: Path) -> None:
    database = tmp_path / "DB_logger.db"
    database.write_bytes(b"not sqlite")
    text_log = tmp_path / "colab_train.log"
    text_log.write_text("Training start", encoding="utf-8")
    results = tmp_path / "results.csv"
    results.write_text("epoch,loss\n1,0.5\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="not a valid SQLite"):
        runner.validate_sqlite_log(database, text_log, results)


def test_result_archive_verifier_rejects_tampered_manifest(tmp_path: Path) -> None:
    archive_path = tmp_path / "result.tar.gz"
    run = "D1_fake"
    payloads = {
        f"{run}/weights/best.pt": b"best",
        f"{run}/weights/last.pt": b"last",
        f"{run}/results.csv": b"epoch,loss\n1,0.5\n",
        f"{run}/args.yaml": b"epochs: 1\n",
        f"{run}/run_contract.json": b"{}\n",
        "colab_logs/colab_execution.json": b"{}\n",
        "colab_logs/colab_train.log": b"success\n",
        "colab_logs/DB_logger.db": b"sqlite-bytes",
    }
    with tarfile.open(archive_path, "w:gz") as archive:
        for name, payload in payloads.items():
            source = tmp_path / name.replace("/", "_")
            source.write_bytes(payload)
            archive.add(source, arcname=name, recursive=False)
    manifest_path = tmp_path / "result.tar.gz.manifest.json"
    manifest = {
        "status": "D1_COLAB_RESULT_PACKAGE",
        "run": run,
        "archive_name": archive_path.name,
        "archive_sha256": runner.sha256_file(archive_path),
        "files": [
            {
                "path": name,
                "size": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
            for name, payload in payloads.items()
        ],
        "terminal_outcome": "SUCCEEDED",
        "sealed_test_accessed": False,
        "run_attestation_sha256": "b" * 64,
    }
    runner.write_json(manifest_path, manifest)
    assert runner.verify_result_archive(archive_path, manifest_path)["run"] == run
    manifest["terminal_outcome"] = "FAILED"
    runner.write_json(manifest_path, manifest)
    with pytest.raises(RuntimeError, match="identity/outcome"):
        runner.verify_result_archive(archive_path, manifest_path)
    manifest["terminal_outcome"] = "SUCCEEDED"
    manifest["archive_name"] = "unrelated.tar.gz"
    runner.write_json(manifest_path, manifest)
    with pytest.raises(RuntimeError, match="identity/outcome"):
        runner.verify_result_archive(archive_path, manifest_path)
    manifest["archive_name"] = archive_path.name
    manifest["run_attestation_sha256"] = "not-a-sha256"
    runner.write_json(manifest_path, manifest)
    with pytest.raises(RuntimeError, match="identity/outcome"):
        runner.verify_result_archive(archive_path, manifest_path)


def test_result_archive_verifier_derives_canonical_roster(tmp_path: Path) -> None:
    archive_path = tmp_path / "result.tar.gz"
    payload = b"best-only"
    source = tmp_path / "best.pt"
    source.write_bytes(payload)
    with tarfile.open(archive_path, "w:gz") as archive:
        archive.add(source, arcname="D1_fake/weights/best.pt", recursive=False)
    manifest_path = tmp_path / "result.tar.gz.manifest.json"
    manifest = {
        "status": "D1_COLAB_RESULT_PACKAGE",
        "run": "D1_fake",
        "archive_name": archive_path.name,
        "archive_sha256": runner.sha256_file(archive_path),
        "files": [
            {
                "path": "D1_fake/weights/best.pt",
                "size": len(payload),
                "sha256": runner.sha256_file(source),
            }
        ],
        "terminal_outcome": "SUCCEEDED",
        "sealed_test_accessed": False,
        "run_attestation_sha256": "a" * 64,
    }
    runner.write_json(manifest_path, manifest)
    with pytest.raises(RuntimeError, match="canonical eight-file roster"):
        runner.verify_result_archive(archive_path, manifest_path)


def test_result_archive_verifier_rejects_self_manifested_extra_member(tmp_path: Path) -> None:
    archive_path = tmp_path / "result.tar.gz"
    run = "D1_fake"
    names = (
        f"{run}/weights/best.pt",
        f"{run}/weights/last.pt",
        f"{run}/results.csv",
        f"{run}/args.yaml",
        f"{run}/run_contract.json",
        "colab_logs/colab_execution.json",
        "colab_logs/colab_train.log",
        "colab_logs/DB_logger.db",
        f"{run}/EXTRA.txt",
    )
    with tarfile.open(archive_path, "w:gz") as archive:
        for index, name in enumerate(names):
            source = tmp_path / f"source-{index}"
            source.write_bytes(name.encode())
            archive.add(source, arcname=name, recursive=False)
    manifest = {
        "status": "D1_COLAB_RESULT_PACKAGE",
        "run": run,
        "archive_name": archive_path.name,
        "archive_sha256": runner.sha256_file(archive_path),
        "files": [
            {
                "path": name,
                "size": len(name.encode()),
                "sha256": hashlib.sha256(name.encode()).hexdigest(),
            }
            for name in names
        ],
        "terminal_outcome": "SUCCEEDED",
        "sealed_test_accessed": False,
        "run_attestation_sha256": "a" * 64,
    }
    manifest_path = tmp_path / "result.tar.gz.manifest.json"
    runner.write_json(manifest_path, manifest)
    with pytest.raises(RuntimeError, match="canonical eight-file roster"):
        runner.verify_result_archive(archive_path, manifest_path)


def test_result_packager_refuses_existing_sidecar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifact = tmp_path / "artifact.bin"
    artifact.write_bytes(b"x")
    output = tmp_path / "result.tar.gz"
    sidecar = tmp_path / "result.tar.gz.manifest.json"
    sidecar.write_text("sentinel", encoding="utf-8")
    monkeypatch.setattr(
        runner,
        "validate_result_sources",
        lambda *_args: (
            [artifact],
            {"status": "SUCCEEDED", "sealed_test_accessed": False},
            {"run_attestation_sha256": "a" * 64},
        ),
    )
    with pytest.raises(RuntimeError, match="refused to overwrite"):
        runner.package_run(
            tmp_path,
            artifact,
            artifact,
            artifact,
            output,
        )
    assert sidecar.read_text(encoding="utf-8") == "sentinel"


def test_result_packager_validates_and_reverifies_success_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = tmp_path / "repo"
    run_dir = repo_root / "results/experiments/D1_fake"
    weights = run_dir / "weights"
    weights.mkdir(parents=True)
    (weights / "best.pt").write_bytes(b"best")
    (weights / "last.pt").write_bytes(b"last")
    (run_dir / "results.csv").write_text("epoch,loss\n1,0.5\n", encoding="utf-8")
    (run_dir / "args.yaml").write_text("epochs: 1\n", encoding="utf-8")
    run_contract = {
        **synthetic_run_contract(),
        "environment": {"runtime_backend": "cuda", "cuda_available": True},
    }
    (run_dir / "run_contract.json").write_text(
        json.dumps(run_contract), encoding="utf-8"
    )
    state = tmp_path / "state"
    logger, text_log, database = runner.configure_logging(state)
    logger.info("D1 Colab workflow started")
    logger.info("Training start")
    logger.info("SUBPROCESS 1/1 epoch metrics")
    logger.info("Training end")
    logger.info("Terminal outcome SUCCEEDED")
    for handler in logger.handlers:
        handler.flush()
        handler.close()
    logger.handlers.clear()
    execution_path = state / "colab_execution.json"
    execution_path.write_text(
        json.dumps(synthetic_execution(repo_root, run_dir)), encoding="utf-8"
    )

    class FakeContract:
        @staticmethod
        def inspect_run_weights(_path: str) -> dict[str, str]:
            return {"run_attestation_sha256": "c" * 64}

    monkeypatch.setattr(runner, "load_detector_contract", lambda _root: FakeContract())
    output = state / "result.tar.gz"
    result = runner.package_run(run_dir, execution_path, text_log, database, output)
    assert result["terminal_outcome"] == "SUCCEEDED"
    assert result["sealed_test_accessed"] is False
    assert runner.verify_result_archive(
        output, state / "result.tar.gz.manifest.json"
    )["run_attestation_sha256"] == "c" * 64
