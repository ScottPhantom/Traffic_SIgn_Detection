from __future__ import annotations

import copy
import importlib.util
import io
import json
import os
import sys
import tarfile
import types
from argparse import Namespace
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
EXECUTION_ROOT = Path("/content/Traffic_Sign_Detector")
RUN_NAME = "D1C_yolo11s_oneclass_afa03d4b_20261018_smoke"


def load_runner() -> types.ModuleType:
    path = REPO_ROOT / "detector/colab/run_d1_cascade_colab.py"
    spec = importlib.util.spec_from_file_location("test_d1_cascade_colab_runner", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


runner = load_runner()


@lru_cache
def governed_data(execution_root: Path = EXECUTION_ROOT) -> dict[str, object]:
    live = runner.verify_cascade_contract(REPO_ROOT)
    return {
        **live,
        "data_yaml": str(execution_root / runner.CASCADE_DATASET / "data.yaml"),
    }


def cuda_environment() -> dict[str, object]:
    return {
        "git_commit": "1" * 40,
        "git_dirty_files": 0,
        "detector_lock_sha256": runner.DETECTOR_LOCK_SHA256,
        "python": "3.12.12",
        "platform": "Linux-6.6-x86_64",
        "machine": "x86_64",
        "hardware_chip": "Google Colab",
        "torch": "2.14.1+cu130",
        "ultralytics": "8.4.172",
        "mps_available": False,
        "cuda_available": True,
        "cuda_version": "13.0",
        "gpu_name": "NVIDIA L4",
        "nvidia_driver": "580.82.07",
        "runtime_backend": "cuda",
    }


def run_contract(run_dir: Path, execution_root: Path = EXECUTION_ROOT) -> dict[str, Any]:
    data = copy.deepcopy(governed_data(execution_root))
    train_args = {
        "data": data["data_yaml"],
        "epochs": 1,
        "imgsz": 1280,
        "batch": 8,
        "device": "0",
        "seed": 20261018,
        "deterministic": True,
        "workers": 4,
        "fraction": 1.0,
        "patience": 30,
        "plots": False,
        "project": str(execution_root / runner.RESULTS_DIR),
        "name": run_dir.name,
        "exist_ok": True,
        "pretrained": True,
        "fliplr": 0.0,
    }
    return {
        "schema_version": 1,
        "experiment": "D1_CASCADE_ONE_CLASS_DETECTOR",
        "run": run_dir.name,
        "seed": 20261018,
        "model": {
            "path": str(execution_root / "models/pretrained/yolo11s.pt"),
            "sha256": runner.PRETRAINED_SHA256,
            "origin": runner.MODEL_ORIGIN,
        },
        "train_args": train_args,
        "data_contract": data,
        "environment": cuda_environment(),
        "status": "TRAINED",
        "sealed_test_accessed": False,
        "artifacts": {"weights": {}},
    }


def materialize_run(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    run_dir = tmp_path / RUN_NAME
    weights = run_dir / "weights"
    weights.mkdir(parents=True)
    artifacts: dict[str, dict[str, str]] = {}
    for name, payload in (("best.pt", b"best"), ("last.pt", b"last")):
        path = weights / name
        path.write_bytes(payload)
        artifacts[name] = {
            "path": str(EXECUTION_ROOT / runner.RESULTS_DIR / RUN_NAME / "weights" / name),
            "sha256": runner.sha256_file(path),
        }
    (run_dir / "results.csv").write_text("epoch,loss\n1,0.5\n", encoding="utf-8")
    (run_dir / "args.yaml").write_text("epochs: 1\n", encoding="utf-8")
    record = run_contract(run_dir)
    record["artifacts"] = {"weights": artifacts}
    runner.write_json(run_dir / "run_contract.json", record)
    return run_dir, record


def execution_record(run_dir: Path) -> dict[str, object]:
    record = run_contract(run_dir)
    train = record["train_args"]
    tag = "smoke"
    return {
        "status": "SUCCEEDED",
        "started_at": "2026-10-19T00:00:00+00:00",
        "finished_at": "2026-10-19T00:10:00+00:00",
        "repo_root": str(EXECUTION_ROOT),
        "bundle": "/content/drive/MyDrive/CPV391/M1_D1_Colab/m1_colab_train_val.tar.gz",
        "bundle_sha256": runner.APPROVED_BUNDLE_SHA256,
        "seed": train["seed"],
        "epochs": train["epochs"],
        "imgsz": train["imgsz"],
        "batch": train["batch"],
        "device": train["device"],
        "tag": tag,
        "sealed_test_accessed": False,
        "steps_completed": list(runner.REQUIRED_STEPS),
        "train_command": runner.expected_train_command(EXECUTION_ROOT, train, tag),
        "run_dir": str(EXECUTION_ROOT / runner.RESULTS_DIR / run_dir.name),
        "error": None,
    }


def lifecycle_logs(state: Path, results_csv: Path) -> tuple[Path, Path]:
    module = runner.load_pinned_module(
        f"test_d1_logging_{state.parent.name}_{state.name}",
        REPO_ROOT / "detector/colab/run_d1_colab.py",
        runner.M1_RUNNER_SHA256,
    )
    logger, text_log, database = module.configure_logging(state)
    for message in (
        "D1 Colab workflow started baseline=cascade",
        "Training start",
        "SUBPROCESS 1/1 epoch metrics",
        "Training end",
        "Terminal outcome SUCCEEDED",
    ):
        logger.info(message)
    for handler in logger.handlers:
        handler.flush()
        handler.close()
    logger.handlers.clear()
    module.validate_sqlite_log(database, text_log, results_csv)
    return text_log, database


def package_valid_result(tmp_path: Path) -> tuple[Path, Path, Path]:
    run_dir, _record = materialize_run(tmp_path / "run")
    state = tmp_path / "state"
    state.mkdir()
    text_log, database = lifecycle_logs(state, run_dir / "results.csv")
    execution_path = state / "colab_execution.json"
    runner.write_json(execution_path, execution_record(run_dir))
    output = state / "result.tar.gz"
    runner.package_result(
        run_dir,
        execution_path,
        text_log,
        database,
        output,
        repo_root=REPO_ROOT,
    )
    return output, output.with_name(f"{output.name}.manifest.json"), run_dir


def rewrite_archive_member(
    archive_path: Path,
    sidecar_path: Path,
    output: Path,
    member_name: str,
    payload: bytes,
) -> Path:
    manifest = json.loads(sidecar_path.read_text(encoding="utf-8"))
    members: dict[str, bytes] = {}
    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive.getmembers():
            handle = archive.extractfile(member)
            assert handle is not None
            members[member.name] = handle.read()
    members[member_name] = payload
    with tarfile.open(output, "w:gz") as archive:
        for name, content in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            archive.addfile(info, io.BytesIO(content))
    manifest["archive_name"] = output.name
    manifest["archive_sha256"] = runner.sha256_file(output)
    for row in manifest["files"]:
        content = members[row["path"]]
        row["size"] = len(content)
        row["sha256"] = runner.hashlib.sha256(content).hexdigest()
    rewritten_sidecar = output.with_name(f"{output.name}.manifest.json")
    runner.write_json(rewritten_sidecar, manifest)
    return rewritten_sidecar


def test_real_cascade_contract_is_train_val_only_and_one_class() -> None:
    result = runner.verify_cascade_contract(REPO_ROOT)
    assert result["classes"] == {"0": "traffic_sign"}
    assert result["test_included"] is False
    assert set(result["split_stem_sha256"]) == {"train", "val"}


def test_public_parser_has_no_test_or_evaluation_route() -> None:
    source = (REPO_ROOT / "detector/colab/run_d1_cascade_colab.py").read_text()
    assert all(token not in source for token in ("export-test", "--final-eval", "--split"))
    args = runner.parser().parse_args(
        [
            "run",
            "--repo-root",
            str(REPO_ROOT),
            "--bundle",
            "bundle.tar.gz",
            "--state-dir",
            "state",
        ]
    )
    assert args.seed == 20261018
    with pytest.raises(SystemExit):
        runner.parser().parse_args(
            [
                "run",
                "--repo-root",
                str(REPO_ROOT),
                "--bundle",
                "bundle.tar.gz",
                "--state-dir",
                "state",
                "--seed",
                "1",
            ]
        )


def test_notebook_is_clean_train_val_launcher() -> None:
    path = REPO_ROOT / "detector/colab/d1_cascade_train.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    assert notebook["metadata"]["colab"]["gpuType"] == "L4"
    code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    assert all(cell.get("outputs", []) == [] for cell in code_cells)
    assert all(cell.get("execution_count") is None for cell in code_cells)
    code = "\n".join("".join(cell["source"]) for cell in code_cells)
    assert "run_d1_cascade_colab.py" in code and "--download-approved-weight" in code
    assert "export-test" not in code and "--final-eval" not in code


def test_cascade_subprocess_environment_forces_headless_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MPLBACKEND", "module://matplotlib_inline.backend_inline")
    environment = runner.colab_subprocess_environment()
    assert environment["MPLBACKEND"] == "Agg"
    assert environment["WANDB_DISABLED"] == "true"
    assert environment["DO_NOT_TRACK"] == "1"
    assert environment["ULTRALYTICS_HUB"] == "false"


def test_cascade_uses_the_single_current_primary_runner_pin() -> None:
    primary = REPO_ROOT / "detector/colab/run_d1_colab.py"
    assert runner.sha256_file(primary) == runner.M1_RUNNER_SHA256
    source = (REPO_ROOT / "detector/colab/run_d1_cascade_colab.py").read_text()
    assert "0d04c869d0181c68a4d60a93b05967c4db5b5e31cfc44cf653bfcbd43f225786" not in source
    assert source.count("M1_RUNNER_SHA256") >= 4


def test_bundle_rejects_unapproved_archive(tmp_path: Path) -> None:
    fake = tmp_path / "bundle.tar.gz"
    fake.write_bytes(b"not approved")
    with pytest.raises(RuntimeError, match="independently reviewed upload"):
        runner.verify_shared_bundle(REPO_ROOT, fake)


def test_internal_training_enforces_invariants(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    (repo / "models/pretrained").mkdir(parents=True)
    (repo / "models/pretrained/yolo11s.pt").write_bytes(b"model")
    (repo / "detector").mkdir()
    (repo / "detector/uv.lock").write_bytes(b"lock")
    (repo / runner.CASCADE_MANIFEST).parent.mkdir(parents=True)
    (repo / runner.CASCADE_MANIFEST).write_text(
        json.dumps({"source_bindings": {"sealed_test_stem_list_sha256": "c" * 64}}),
        encoding="utf-8",
    )
    real_sha = runner.sha256_file

    def fake_sha(path: Path) -> str:
        if path.name == "yolo11s.pt":
            return runner.PRETRAINED_SHA256
        if path.name == "uv.lock":
            return runner.DETECTOR_LOCK_SHA256
        return real_sha(path)

    synthetic_data = {
        **governed_data(repo),
        "data_yaml": str(repo / runner.CASCADE_DATASET / "data.yaml"),
    }
    monkeypatch.setattr(runner, "sha256_file", fake_sha)
    monkeypatch.setattr(runner, "verify_cascade_contract", lambda _root: synthetic_data)
    observed: dict[str, object] = {}

    class FakeYOLO:
        def __init__(self, model: str) -> None:
            observed["model"] = model

        def train(self, **kwargs: object) -> None:
            observed["train"] = kwargs
            out = Path(str(kwargs["project"])) / str(kwargs["name"])
            (out / "weights").mkdir(parents=True, exist_ok=True)
            (out / "weights/best.pt").write_bytes(b"best")
            (out / "weights/last.pt").write_bytes(b"last")

    fake_contract = types.ModuleType("m1.contract")
    fake_contract.disable_telemetry = lambda: observed.update(telemetry_disabled=True)
    fake_contract.environment = cuda_environment
    fake_m1 = types.ModuleType("m1")
    fake_m1.contract = fake_contract
    fake_ultralytics = types.ModuleType("ultralytics")
    fake_ultralytics.YOLO = FakeYOLO
    monkeypatch.setitem(sys.modules, "m1", fake_m1)
    monkeypatch.setitem(sys.modules, "ultralytics", fake_ultralytics)
    args = Namespace(
        repo_root=repo,
        seed=20261018,
        epochs=1,
        imgsz=1280,
        batch=8,
        device="0",
        workers=4,
        fraction=1.0,
        patience=30,
        tag="smoke",
    )
    assert runner.internal_train(args) == 0
    train = observed["train"]
    assert train["fliplr"] == 0.0 and train["deterministic"] is True
    assert train["pretrained"] is True and train["plots"] is False
    assert observed["telemetry_disabled"] is True


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("epochs", 0, "positive integer"),
        ("imgsz", -1, "positive integer"),
        ("batch", 0, "positive integer"),
        ("workers", -1, "non-negative integer"),
        ("fraction", 0.0, "finite in"),
        ("patience", -1, "non-negative integer"),
    ],
)
def test_run_contract_rejects_invalid_numeric_values(
    tmp_path: Path, field: str, value: object, message: str
) -> None:
    run_dir, record = materialize_run(tmp_path)
    record["train_args"][field] = value
    runner.write_json(run_dir / "run_contract.json", record)
    with pytest.raises(RuntimeError, match=message):
        runner.validate_run_contract(
            run_dir, repo_root=REPO_ROOT, execution_repo_root=EXECUTION_ROOT
        )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: r["data_contract"]["split_stem_sha256"].update(train="forged"),
        lambda r: r["data_contract"].update(classes={"999": "not_traffic_sign"}),
        lambda r: r["train_args"].update(data="/tmp/test.yaml"),
        lambda r: r["train_args"].update(project="/tmp/results"),
        lambda r: r["train_args"].update(name="forged"),
        lambda r: r["model"].update(path="/tmp/model.pt"),
        lambda r: r["model"].update(origin="forged"),
    ],
)
def test_run_contract_rejects_qa_contradictions(
    tmp_path: Path, mutation: Callable[[dict[str, Any]], None]
) -> None:
    run_dir, record = materialize_run(tmp_path)
    mutation(record)
    runner.write_json(run_dir / "run_contract.json", record)
    with pytest.raises(RuntimeError):
        runner.validate_run_contract(
            run_dir, repo_root=REPO_ROOT, execution_repo_root=EXECUTION_ROOT
        )


def test_run_contract_rejects_incomplete_cuda_identity(tmp_path: Path) -> None:
    run_dir, record = materialize_run(tmp_path)
    record["environment"] = {
        "runtime_backend": "cuda",
        "cuda_available": True,
        "git_dirty_files": 0,
        "detector_lock_sha256": runner.DETECTOR_LOCK_SHA256,
    }
    runner.write_json(run_dir / "run_contract.json", record)
    with pytest.raises(RuntimeError, match="schema differs"):
        runner.validate_run_contract(
            run_dir, repo_root=REPO_ROOT, execution_repo_root=EXECUTION_ROOT
        )


def test_result_package_and_standalone_semantic_verifier_pass(tmp_path: Path) -> None:
    output, sidecar, _run = package_valid_result(tmp_path)
    result = runner.verify_result_archive(output, sidecar, repo_root=REPO_ROOT)
    assert result["terminal_outcome"] == "SUCCEEDED"
    assert result["sealed_test_accessed"] is False
    assert len(result["files"]) == 8


def test_standalone_verifier_rejects_qa_forged_lifecycle_package(tmp_path: Path) -> None:
    output, sidecar, _run = package_valid_result(tmp_path)
    manifest = json.loads(sidecar.read_text(encoding="utf-8"))
    members: dict[str, bytes] = {}
    with tarfile.open(output, "r:gz") as archive:
        for member in archive.getmembers():
            handle = archive.extractfile(member)
            assert handle is not None
            members[member.name] = handle.read()
    members[f"{RUN_NAME}/run_contract.json"] = b"not-json"
    members["colab_logs/colab_execution.json"] = b"not-json"
    members["colab_logs/DB_logger.db"] = b"forged"
    forged = tmp_path / "forged.tar.gz"
    with tarfile.open(forged, "w:gz") as archive:
        for name, payload in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))
    manifest["archive_name"] = forged.name
    manifest["archive_sha256"] = runner.sha256_file(forged)
    for row in manifest["files"]:
        payload = members[row["path"]]
        row["size"] = len(payload)
        row["sha256"] = runner.hashlib.sha256(payload).hexdigest()
    forged_sidecar = tmp_path / "forged.tar.gz.manifest.json"
    runner.write_json(forged_sidecar, manifest)
    with pytest.raises((RuntimeError, json.JSONDecodeError)):
        runner.verify_result_archive(forged, forged_sidecar, repo_root=REPO_ROOT)


def test_standalone_verifier_rejects_self_consistent_fake_sqlite(tmp_path: Path) -> None:
    output, sidecar, _run = package_valid_result(tmp_path / "valid")
    forged = tmp_path / "fake-sqlite.tar.gz"
    forged_sidecar = rewrite_archive_member(
        output,
        sidecar,
        forged,
        "colab_logs/DB_logger.db",
        b"forged",
    )
    with pytest.raises(RuntimeError, match="SQLite"):
        runner.verify_result_archive(forged, forged_sidecar, repo_root=REPO_ROOT)


def test_standalone_verifier_rejects_self_consistent_bad_lifecycle(tmp_path: Path) -> None:
    output, sidecar, _run = package_valid_result(tmp_path / "valid")
    with tarfile.open(output, "r:gz") as archive:
        handle = archive.extractfile("colab_logs/colab_execution.json")
        assert handle is not None
        execution = json.loads(handle.read())
    execution["steps_completed"] = list(runner.REQUIRED_STEPS[:-1])
    forged = tmp_path / "bad-lifecycle.tar.gz"
    forged_sidecar = rewrite_archive_member(
        output,
        sidecar,
        forged,
        "colab_logs/colab_execution.json",
        (json.dumps(execution) + "\n").encode(),
    )
    with pytest.raises(RuntimeError, match="successful outcome"):
        runner.verify_result_archive(forged, forged_sidecar, repo_root=REPO_ROOT)


def test_execution_rejects_forged_command_prefix(tmp_path: Path) -> None:
    run_dir, record = materialize_run(tmp_path)
    execution = execution_record(run_dir)
    execution["train_command"][0:4] = ["python", "/tmp/forged.py", "noop", "noop"]
    path = tmp_path / "execution.json"
    runner.write_json(path, execution)
    with pytest.raises(RuntimeError, match="training command differs"):
        runner.validate_execution_record(path, record, run_dir)


@pytest.mark.parametrize("target", ["archive", "sidecar", "archive_partial", "sidecar_partial"])
def test_packager_rejects_symlinks_without_touching_external_target(
    tmp_path: Path, target: str
) -> None:
    run_dir, _record = materialize_run(tmp_path / "run")
    state = tmp_path / "state"
    state.mkdir()
    text_log, database = lifecycle_logs(state, run_dir / "results.csv")
    execution_path = state / "colab_execution.json"
    runner.write_json(execution_path, execution_record(run_dir))
    output = state / "result.tar.gz"
    sidecar = output.with_name(f"{output.name}.manifest.json")
    paths = {
        "archive": output,
        "sidecar": sidecar,
        "archive_partial": output.with_name(f".{output.name}.partial"),
        "sidecar_partial": sidecar.with_name(f".{sidecar.name}.partial"),
    }
    victim = tmp_path / "external-victim"
    victim.write_bytes(b"sentinel")
    os.symlink(victim, paths[target])
    with pytest.raises(RuntimeError, match="existing cascade result output"):
        runner.package_result(
            run_dir,
            execution_path,
            text_log,
            database,
            output,
            repo_root=REPO_ROOT,
        )
    assert victim.read_bytes() == b"sentinel" and paths[target].is_symlink()


def test_packager_rejects_symlinked_output_parent(tmp_path: Path) -> None:
    run_dir, _record = materialize_run(tmp_path / "run")
    real_state = tmp_path / "external-state"
    real_state.mkdir()
    state_link = tmp_path / "state-link"
    os.symlink(real_state, state_link)
    text_log, database = lifecycle_logs(real_state, run_dir / "results.csv")
    execution_path = real_state / "colab_execution.json"
    runner.write_json(execution_path, execution_record(run_dir))
    with pytest.raises(RuntimeError, match="symlink component"):
        runner.package_result(
            run_dir,
            execution_path,
            text_log,
            database,
            state_link / "result.tar.gz",
            repo_root=REPO_ROOT,
        )
    assert {path.name for path in real_state.iterdir()} == {
        "DB_logger.db",
        "colab_execution.json",
        "colab_train.log",
    }


def test_standalone_verifier_rejects_archive_and_manifest_symlinks(tmp_path: Path) -> None:
    output, sidecar, _run = package_valid_result(tmp_path / "valid")
    archive_link = tmp_path / "archive-link.tar.gz"
    manifest_link = tmp_path / "manifest-link.json"
    os.symlink(output, archive_link)
    os.symlink(sidecar, manifest_link)
    with pytest.raises(RuntimeError, match="symlink component"):
        runner.verify_result_archive(archive_link, sidecar, repo_root=REPO_ROOT)
    with pytest.raises(RuntimeError, match="symlink component"):
        runner.verify_result_archive(output, manifest_link, repo_root=REPO_ROOT)


def test_result_archive_rejects_unsafe_member_name(tmp_path: Path) -> None:
    archive = tmp_path / "result.tar.gz"
    payload = tmp_path / "payload"
    payload.write_bytes(b"x")
    with tarfile.open(archive, "w:gz") as bundle:
        bundle.add(payload, arcname="../escape")
    expected_names = (
        f"{RUN_NAME}/weights/best.pt",
        f"{RUN_NAME}/weights/last.pt",
        f"{RUN_NAME}/results.csv",
        f"{RUN_NAME}/args.yaml",
        f"{RUN_NAME}/run_contract.json",
        "colab_logs/colab_execution.json",
        "colab_logs/colab_train.log",
        "colab_logs/DB_logger.db",
    )
    manifest = {
        "status": "D1_CASCADE_COLAB_RESULT_PACKAGE",
        "run": RUN_NAME,
        "archive_name": archive.name,
        "archive_sha256": runner.sha256_file(archive),
        "files": [
            {"path": name, "size": 1, "sha256": "0" * 64} for name in expected_names
        ],
        "terminal_outcome": "SUCCEEDED",
        "sealed_test_accessed": False,
        "run_attestation": {},
        "run_attestation_sha256": "0" * 64,
    }
    sidecar = tmp_path / "manifest.json"
    runner.write_json(sidecar, manifest)
    with pytest.raises(RuntimeError, match="unsafe cascade result path"):
        runner.verify_result_archive(archive, sidecar, repo_root=REPO_ROOT)
