#!/usr/bin/env python3
"""Run the train/val-only D1 cascade detector baseline on a private Colab GPU.

The outer workflow verifies and restores the exact already-approved M1 train/val bundle, builds
the QA-approved one-class successor dataset, synchronizes the frozen detector environment and
launches an internal Ultralytics training command.  The internal command re-verifies every data
and model binding before training.  Neither command has a sealed-test route.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import re
import shutil
import stat
import sys
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Any

APPROVED_SEEDS = (20261018, 20261019, 20261020)
PRETRAINED_SHA256 = "85a76fe86dd8afe384648546b56a7a78580c7cb7b404fc595f97969322d502d5"
APPROVED_BUNDLE_SHA256 = "eb5226e36cf619e271132794c97fd633f7528d72e25463356eb165f36f43e191"
APPROVED_BUNDLE_COMMIT = "1842a1b77e6448a54fec486937f4c0f0e6ff19f5"
TEST_SEAL_SHA256 = "afa03d4b6deb7567c5784b29122966d84599d4eb81fdbad37c3b20adaf7524bc"
M1_EXPORT_MANIFEST_SHA256 = "8a8df5f242829277fb86cfd55490dd4284e42a6c09f7ace6a509e42feb179d71"
CASCADE_MANIFEST_SHA256 = "d6ca36a4c21cbadb922df897625ce80dc9d6fa3d5770b3c6cb84ddff78e10fd2"
CASCADE_BUILDER_SHA256 = "d2b80eb4906570e6636d3e0651a612368181e66a007c8e424d7a8df3d560cb39"
BUNDLE_BUILDER_SHA256 = "ac0c4a9a7d15522bb4254221f252fefb640395683b4ee7b7698b61f606d47536"
DETECTOR_LOCK_SHA256 = "5d56642af267bdff63f7d2a627ccf97a8f04cbf848a673a5d65988a471baaec5"
CASCADE_MANIFEST = Path("docs/review/generated/d1_cascade_detector_manifest.json")
CASCADE_DATASET = Path("data/processed/d1_cascade_yolo")
RESULTS_DIR = Path("results/experiments")
LOGGER_NAME = "CPV_log_record"
MODEL_ORIGIN = "ultralytics/assets v8.4.0 Owner-approved"
M1_RUNNER_SHA256 = "0d04c869d0181c68a4d60a93b05967c4db5b5e31cfc44cf653bfcbd43f225786"
REQUIRED_STEPS = (
    "approved_bundle_verified_and_extracted",
    "cascade_train_val_export_regenerated",
    "detector_lock_synchronized",
    "approved_pretrained_weight_verified",
    "cascade_contract_checked",
    "training_completed",
)
EXECUTION_KEYS = {
    "status",
    "started_at",
    "finished_at",
    "repo_root",
    "bundle",
    "bundle_sha256",
    "seed",
    "epochs",
    "imgsz",
    "batch",
    "device",
    "tag",
    "sealed_test_accessed",
    "steps_completed",
    "train_command",
    "run_dir",
    "error",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def absolute_lexical(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def reject_symlink_components(path: Path) -> None:
    """Reject every existing symlink component without dereferencing the target path."""
    target = absolute_lexical(path)
    current = Path(target.anchor)
    for part in target.parts[1:]:
        current /= part
        try:
            mode = os.lstat(current).st_mode
        except FileNotFoundError:
            break
        if stat.S_ISLNK(mode):
            raise RuntimeError(f"refused symlink component: {current}")


def require_regular_file(path: Path, label: str) -> Path:
    lexical = absolute_lexical(path)
    reject_symlink_components(lexical)
    try:
        mode = os.lstat(lexical).st_mode
    except FileNotFoundError as error:
        raise RuntimeError(f"{label} is missing: {lexical}") from error
    if not stat.S_ISREG(mode):
        raise RuntimeError(f"{label} must be a regular non-symlink file: {lexical}")
    return lexical


def path_exists_lstat(path: Path) -> bool:
    try:
        os.lstat(path)
    except FileNotFoundError:
        return False
    return True


def canonical_sha256(payload: Any) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def strict_json(path: Path) -> Any:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON constant is forbidden: {value}")

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key is forbidden: {key}")
            result[key] = value
        return result

    return json.loads(
        path.read_text(encoding="utf-8"),
        parse_constant=reject_constant,
        object_pairs_hook=unique_object,
    )


def load_pinned_module(name: str, path: Path, expected_sha256: str) -> ModuleType:
    if not path.is_file() or path.is_symlink() or sha256_file(path) != expected_sha256:
        raise RuntimeError(f"pinned module differs: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load pinned module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_bundle_builder(repo_root: Path) -> ModuleType:
    return load_pinned_module(
        "d1_cascade_colab_bundle",
        repo_root / "scripts/build_m1_colab_bundle.py",
        BUNDLE_BUILDER_SHA256,
    )


def load_cascade_builder(repo_root: Path) -> ModuleType:
    return load_pinned_module(
        "d1_cascade_colab_dataset",
        repo_root / "scripts/build_d1_cascade_detector_dataset.py",
        CASCADE_BUILDER_SHA256,
    )


def load_environment_contract(repo_root: Path) -> ModuleType:
    path = repo_root / "detector/m1/contract.py"
    spec = importlib.util.spec_from_file_location("d1_cascade_environment_contract", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load detector environment contract: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def verify_shared_bundle(repo_root: Path, archive: Path) -> dict[str, Any]:
    """Verify the exact approved upload while allowing its older clean source commit."""
    if sha256_file(archive) != APPROVED_BUNDLE_SHA256:
        raise RuntimeError("bundle SHA-256 differs from the independently reviewed upload")
    builder = load_bundle_builder(repo_root)
    manifest, members = builder.read_archive_manifest(archive)
    expected, metadata = builder.expected_records(repo_root)
    if manifest["repo_git_commit"] != APPROVED_BUNDLE_COMMIT:
        raise RuntimeError("bundle source commit differs from the independently reviewed upload")
    for key in (
        "export_manifest_sha256",
        "detector_lock_sha256",
        "class_map_sha256",
        "train_stem_list_sha256",
        "val_stem_list_sha256",
        "sealed_test_stem_list_sha256",
        "counts",
    ):
        if manifest[key] != metadata[key]:
            raise RuntimeError(f"bundle governed binding differs: {key}")
    expected_by_path = {record["path"]: record for record in expected}
    actual_by_path = {record["path"]: record for record in manifest["files"]}
    if set(actual_by_path) != set(expected_by_path):
        raise RuntimeError("bundle roster differs from the current governed train/val roster")
    if set(members) != set(expected_by_path) | {builder.MANIFEST_MEMBER}:
        raise RuntimeError("bundle archive has missing or extra members")
    with tarfile.open(archive, mode="r:gz") as bundle:
        for path, expected_record in expected_by_path.items():
            actual = actual_by_path[path]
            for key in ("sha256", "source_split", "kind"):
                if actual[key] != expected_record[key]:
                    raise RuntimeError(f"bundle file binding differs: {path} {key}")
            member = members[path]
            handle = bundle.extractfile(member)
            if handle is None or member.size != actual["size"]:
                raise RuntimeError(f"bundle member size differs: {path}")
            if builder.sha256_stream(handle) != actual["sha256"]:
                raise RuntimeError(f"bundle member SHA-256 differs: {path}")
    return manifest


def extract_shared_bundle(repo_root: Path, archive: Path) -> dict[str, int]:
    manifest = verify_shared_bundle(repo_root, archive)
    builder = load_bundle_builder(repo_root)
    written = reused = 0
    with tarfile.open(archive, mode="r:gz") as bundle:
        for record in manifest["files"]:
            destination = builder._safe_destination(repo_root, record["path"])
            if destination.is_symlink():
                raise RuntimeError(f"refused bundle destination symlink: {destination}")
            if destination.exists():
                if not destination.is_file() or sha256_file(destination) != record["sha256"]:
                    raise RuntimeError(f"refused differing bundle destination: {destination}")
                reused += 1
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            handle = bundle.extractfile(record["path"])
            if handle is None:
                raise RuntimeError(f"cannot read bundle member: {record['path']}")
            with destination.open("xb") as output:
                shutil.copyfileobj(handle, output, length=1024 * 1024)
            if sha256_file(destination) != record["sha256"]:
                raise RuntimeError(f"extracted bundle file differs: {destination}")
            written += 1
    return {"written": written, "reused": reused}


def verify_cascade_contract(repo_root: Path) -> dict[str, Any]:
    manifest_path = repo_root / CASCADE_MANIFEST
    if sha256_file(manifest_path) != CASCADE_MANIFEST_SHA256:
        raise RuntimeError("cascade manifest SHA-256 differs from the QA-approved manifest")
    builder = load_cascade_builder(repo_root)
    manifest_check = builder.verify_manifest(repo_root)
    export_check = builder.verify_export(
        repo_root,
        repo_root / builder.m1.DEFAULT_RAW_ROOT,
        repo_root / builder.m1.DEFAULT_WP35_ROOT,
        repo_root / CASCADE_DATASET,
    )
    if manifest_check["valid"] is not True or export_check["valid"] is not True:
        raise RuntimeError(
            f"cascade data contract invalid: manifest={manifest_check['errors']} "
            f"export={export_check['errors']}"
        )
    manifest = strict_json(manifest_path)
    if manifest["allowed_splits"] != ["train", "val"] or manifest["test_included"] is not False:
        raise RuntimeError("cascade manifest exposes a non-train/val split")
    yaml_path = repo_root / CASCADE_DATASET / "data.yaml"
    text = yaml_path.read_text(encoding="utf-8")
    if "\ntest:" in text or manifest["classes"] != {"count": 1, "names": {"0": "traffic_sign"}}:
        raise RuntimeError("cascade dataset class/split boundary differs")
    return {
        "cascade_manifest_sha256": CASCADE_MANIFEST_SHA256,
        "m1_export_manifest_sha256": M1_EXPORT_MANIFEST_SHA256,
        "bundle_sha256": APPROVED_BUNDLE_SHA256,
        "bundle_source_commit": APPROVED_BUNDLE_COMMIT,
        "split_stem_sha256": {
            "train": manifest["source_bindings"]["train_stem_list_sha256"],
            "val": manifest["source_bindings"]["val_stem_list_sha256"],
        },
        "data_yaml": str(yaml_path.resolve()),
        "classes": {"0": "traffic_sign"},
        "test_included": False,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def internal_train(args: argparse.Namespace) -> int:
    repo_root = args.repo_root.expanduser().resolve()
    if args.seed not in APPROVED_SEEDS:
        raise RuntimeError(f"seed is not approved: {args.seed}")
    if re.fullmatch(r"[A-Za-z0-9_.-]+", args.tag) is None:
        raise RuntimeError("training tag is missing or unsafe")
    for key in ("epochs", "imgsz", "batch"):
        _validate_positive_int(getattr(args, key), f"--{key}")
    _validate_positive_int(args.workers, "--workers", allow_zero=True)
    _validate_positive_int(args.patience, "--patience", allow_zero=True)
    if not math.isfinite(args.fraction) or not 0 < args.fraction <= 1:
        raise RuntimeError("--fraction must be finite in (0,1]")
    if not isinstance(args.device, str) or not args.device.strip():
        raise RuntimeError("--device must be a non-empty string")
    model_path = (repo_root / "models/pretrained/yolo11s.pt").resolve()
    if not model_path.is_file() or sha256_file(model_path) != PRETRAINED_SHA256:
        raise RuntimeError("approved pretrained yolo11s.pt is missing or differs")
    lock_path = repo_root / "detector/uv.lock"
    if sha256_file(lock_path) != DETECTOR_LOCK_SHA256:
        raise RuntimeError("detector lock differs")
    bound = verify_cascade_contract(repo_root)
    detector_root = repo_root / "detector"
    sys.path.insert(0, str(detector_root))
    try:
        from ultralytics import YOLO

        from m1 import contract as environment_contract

        environment_contract.disable_telemetry()
        environment = environment_contract.environment()
    finally:
        sys.path.pop(0)
    if environment["runtime_backend"] != "cuda" or environment["cuda_available"] is not True:
        raise RuntimeError("cascade Colab training requires an observed CUDA runtime")
    seal = strict_json(repo_root / CASCADE_MANIFEST)["source_bindings"][
        "sealed_test_stem_list_sha256"
    ]
    run_name = f"D1C_yolo11s_oneclass_{seal[:8]}_{args.seed}_{args.tag}"
    results_root = (repo_root / RESULTS_DIR).resolve()
    run_dir = results_root / run_name
    if run_dir.exists():
        raise RuntimeError(f"run directory already exists: {run_dir}")
    train_args = {
        "data": bound["data_yaml"],
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "device": args.device,
        "seed": args.seed,
        "deterministic": True,
        "workers": args.workers,
        "fraction": args.fraction,
        "patience": args.patience,
        "plots": False,
        "project": str(results_root),
        "name": run_name,
        "exist_ok": True,  # run_dir was proven absent and is pre-created for the contract
        "pretrained": True,
        "fliplr": 0.0,
    }
    record: dict[str, Any] = {
        "schema_version": 1,
        "experiment": "D1_CASCADE_ONE_CLASS_DETECTOR",
        "run": run_name,
        "seed": args.seed,
        "model": {
            "path": str(model_path),
            "sha256": PRETRAINED_SHA256,
            "origin": MODEL_ORIGIN,
        },
        "train_args": train_args,
        "data_contract": bound,
        "environment": environment,
        "status": "STARTED",
        "sealed_test_accessed": False,
    }
    write_json(run_dir / "run_contract.json", record)
    YOLO(str(model_path)).train(**train_args)
    artifacts: dict[str, dict[str, Any]] = {}
    for name in ("best.pt", "last.pt"):
        path = run_dir / "weights" / name
        if not path.is_file() or path.is_symlink():
            raise RuntimeError(f"training did not produce regular weight: {path}")
        artifacts[name] = {"path": str(path), "sha256": sha256_file(path)}
    record["artifacts"] = {"weights": artifacts}
    record["status"] = "TRAINED"
    write_json(run_dir / "run_contract.json", record)
    print(json.dumps({"status": "TRAINED", "run": run_name, "dir": str(run_dir)}))
    return 0


def _validate_positive_int(value: Any, label: str, *, allow_zero: bool = False) -> int:
    if type(value) is not int or value < (0 if allow_zero else 1):
        qualifier = "non-negative" if allow_zero else "positive"
        raise RuntimeError(f"{label} must be a {qualifier} integer")
    return value


def _validate_timestamp(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"{label} must be a non-empty ISO-8601 timestamp")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise RuntimeError(f"{label} must be an ISO-8601 timestamp") from error
    return value


def validate_run_contract(
    run_dir: Path,
    *,
    repo_root: Path | None = None,
    execution_repo_root: Path | None = None,
) -> dict[str, Any]:
    """Validate a local or safely extracted run against live governed inputs."""
    run_dir = absolute_lexical(run_dir)
    contract_path = require_regular_file(run_dir / "run_contract.json", "run contract")
    record = strict_json(contract_path)
    required = {
        "schema_version",
        "experiment",
        "run",
        "seed",
        "model",
        "train_args",
        "data_contract",
        "environment",
        "status",
        "sealed_test_accessed",
        "artifacts",
    }
    if not isinstance(record, dict) or set(record) != required:
        raise RuntimeError("cascade run contract schema differs")
    if (
        record["schema_version"] != 1
        or record["experiment"] != "D1_CASCADE_ONE_CLASS_DETECTOR"
        or record["run"] != run_dir.name
        or record["seed"] not in APPROVED_SEEDS
        or record["status"] != "TRAINED"
        or record["sealed_test_accessed"] is not False
    ):
        raise RuntimeError("cascade run identity/outcome differs")
    if not isinstance(record["model"], dict) or set(record["model"]) != {
        "path",
        "sha256",
        "origin",
    }:
        raise RuntimeError("cascade run model schema differs")
    repo_root = absolute_lexical(repo_root or Path(__file__).resolve().parents[2])
    execution_root = absolute_lexical(execution_repo_root or repo_root)
    expected_model = execution_root / "models/pretrained/yolo11s.pt"
    if record["model"] != {
        "path": str(expected_model),
        "sha256": PRETRAINED_SHA256,
        "origin": MODEL_ORIGIN,
    }:
        raise RuntimeError("cascade run approved-model identity differs")
    live_model = require_regular_file(
        repo_root / "models/pretrained/yolo11s.pt", "approved pretrained model"
    )
    if sha256_file(live_model) != PRETRAINED_SHA256:
        raise RuntimeError("live approved pretrained model SHA-256 differs")
    contract = record["data_contract"]
    if not isinstance(contract, dict) or set(contract) != {
        "cascade_manifest_sha256",
        "m1_export_manifest_sha256",
        "bundle_sha256",
        "bundle_source_commit",
        "split_stem_sha256",
        "data_yaml",
        "classes",
        "test_included",
    }:
        raise RuntimeError("cascade run data contract schema differs")
    live_contract = verify_cascade_contract(repo_root)
    expected_contract = {
        **live_contract,
        "data_yaml": str(execution_root / CASCADE_DATASET / "data.yaml"),
    }
    if contract != expected_contract:
        raise RuntimeError("cascade run data contract differs from live governed data")
    train_args = record["train_args"]
    if not isinstance(train_args, dict) or set(train_args) != {
        "data",
        "epochs",
        "imgsz",
        "batch",
        "device",
        "seed",
        "deterministic",
        "workers",
        "fraction",
        "patience",
        "plots",
        "project",
        "name",
        "exist_ok",
        "pretrained",
        "fliplr",
    }:
        raise RuntimeError("cascade run training arguments schema differs")
    for key, value in {
        "data": contract["data_yaml"],
        "seed": record["seed"],
        "deterministic": True,
        "pretrained": True,
        "fliplr": 0.0,
        "plots": False,
        "project": str(execution_root / RESULTS_DIR),
        "name": record["run"],
        "exist_ok": True,
    }.items():
        if train_args.get(key) != value:
            raise RuntimeError(f"cascade run training invariant differs: {key}")
    for key in ("epochs", "imgsz", "batch"):
        _validate_positive_int(train_args[key], f"train_args.{key}")
    _validate_positive_int(train_args["workers"], "train_args.workers", allow_zero=True)
    _validate_positive_int(train_args["patience"], "train_args.patience", allow_zero=True)
    fraction = train_args["fraction"]
    if type(fraction) not in (int, float) or not math.isfinite(fraction) or not 0 < fraction <= 1:
        raise RuntimeError("train_args.fraction must be finite in (0,1]")
    if not isinstance(train_args["device"], str) or not train_args["device"].strip():
        raise RuntimeError("train_args.device must be a non-empty string")
    environment = record["environment"]
    environment_contract = load_environment_contract(repo_root)
    environment_contract.validate_environment_record(
        environment, "cascade run environment", require_clean=True
    )
    if environment["runtime_backend"] != "cuda" or environment["cuda_available"] is not True:
        raise RuntimeError("cascade run environment is not CUDA")
    if re.fullmatch(r"[0-9a-f]{40}", environment["git_commit"]) is None:
        raise RuntimeError("cascade run environment Git commit is invalid")
    if not isinstance(record["artifacts"], dict) or set(record["artifacts"]) != {"weights"}:
        raise RuntimeError("cascade run artifact schema differs")
    artifacts = record["artifacts"]["weights"]
    if not isinstance(artifacts, dict) or set(artifacts) != {"best.pt", "last.pt"}:
        raise RuntimeError("cascade run weight roster differs")
    for name, artifact in artifacts.items():
        path = run_dir / "weights" / name
        expected_artifact_path = execution_root / RESULTS_DIR / record["run"] / "weights" / name
        if (
            not isinstance(artifact, dict)
            or set(artifact) != {"path", "sha256"}
            or artifact["path"] != str(expected_artifact_path)
            or re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"]) is None
            or require_regular_file(path, f"cascade run weight {name}") != path
            or sha256_file(path) != artifact["sha256"]
        ):
            raise RuntimeError(f"cascade run weight binding differs: {name}")
    return record


def expected_train_command(execution_root: Path, train_args: dict[str, Any], tag: str) -> list[str]:
    return [
        "uv",
        "run",
        "python",
        str(execution_root / "detector/colab/run_d1_cascade_colab.py"),
        "_train",
        "--repo-root",
        str(execution_root),
        "--seed",
        str(train_args["seed"]),
        "--epochs",
        str(train_args["epochs"]),
        "--imgsz",
        str(train_args["imgsz"]),
        "--batch",
        str(train_args["batch"]),
        "--device",
        str(train_args["device"]),
        "--workers",
        str(train_args["workers"]),
        "--fraction",
        str(train_args["fraction"]),
        "--patience",
        str(train_args["patience"]),
        "--tag",
        tag,
    ]


def validate_execution_record(
    execution_path: Path,
    contract: dict[str, Any],
    run_dir: Path,
) -> dict[str, Any]:
    execution = strict_json(require_regular_file(execution_path, "cascade execution record"))
    if not isinstance(execution, dict) or set(execution) != EXECUTION_KEYS:
        raise RuntimeError("cascade execution record schema differs")
    execution_root_value = execution.get("repo_root")
    if (
        not isinstance(execution_root_value, str)
        or not execution_root_value
        or not Path(execution_root_value).is_absolute()
    ):
        raise RuntimeError("cascade execution repository root must be absolute")
    execution_root = absolute_lexical(Path(execution_root_value))
    tag = execution.get("tag")
    expected_run_dir = execution_root / RESULTS_DIR / contract["run"]
    if (
        execution.get("status") != "SUCCEEDED"
        or execution.get("sealed_test_accessed") is not False
        or execution.get("steps_completed") != list(REQUIRED_STEPS)
        or execution.get("run_dir") != str(expected_run_dir)
        or execution.get("bundle_sha256") != APPROVED_BUNDLE_SHA256
        or execution.get("error") is not None
        or not isinstance(execution.get("bundle"), str)
        or not Path(execution["bundle"]).is_absolute()
        or not isinstance(tag, str)
        or re.fullmatch(r"[A-Za-z0-9_.-]+", tag) is None
    ):
        raise RuntimeError("cascade execution record has no bound successful outcome")
    _validate_timestamp(execution["started_at"], "execution.started_at")
    _validate_timestamp(execution["finished_at"], "execution.finished_at")
    train_args = contract["train_args"]
    for key in ("seed", "epochs", "imgsz", "batch", "device"):
        if execution[key] != train_args[key]:
            raise RuntimeError(f"cascade execution parameter differs: {key}")
    expected_name = f"D1C_yolo11s_oneclass_{TEST_SEAL_SHA256[:8]}_{contract['seed']}_{tag}"
    if contract["run"] != expected_name:
        raise RuntimeError("cascade execution run name differs from seed/tag/seal")
    if execution["train_command"] != expected_train_command(execution_root, train_args, tag):
        raise RuntimeError("cascade execution training command differs")
    if run_dir.name != contract["run"]:
        raise RuntimeError("cascade extracted/local run directory identity differs")
    return execution


def package_result(
    run_dir: Path,
    execution_path: Path,
    text_log: Path,
    database_log: Path,
    output: Path,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    output = absolute_lexical(output)
    sidecar = output.with_name(f"{output.name}.manifest.json")
    partial = output.with_name(f".{output.name}.partial")
    manifest_partial = sidecar.with_name(f".{sidecar.name}.partial")
    reject_symlink_components(output.parent)
    output.parent.mkdir(parents=True, exist_ok=True)
    reject_symlink_components(output.parent)
    existing = [
        path
        for path in (output, sidecar, partial, manifest_partial)
        if path_exists_lstat(path)
    ]
    if existing:
        raise RuntimeError(f"refused existing cascade result output path(s): {existing}")
    execution_preview = strict_json(require_regular_file(execution_path, "execution record"))
    execution_root = absolute_lexical(Path(execution_preview.get("repo_root", "")))
    repo_root = absolute_lexical(repo_root or run_dir.parents[2])
    contract = validate_run_contract(
        run_dir, repo_root=repo_root, execution_repo_root=execution_root
    )
    validate_execution_record(execution_path, contract, run_dir)
    sources = [
        run_dir / "weights/best.pt",
        run_dir / "weights/last.pt",
        run_dir / "results.csv",
        run_dir / "args.yaml",
        run_dir / "run_contract.json",
        execution_path,
        text_log,
        database_log,
    ]
    for path in sources:
        source = require_regular_file(path, "cascade result source")
        if source.stat().st_size == 0:
            raise RuntimeError(f"cascade result source is empty: {source}")
    m1_runner = load_pinned_module(
        "d1_cascade_result_logging",
        repo_root / "detector/colab/run_d1_colab.py",
        M1_RUNNER_SHA256,
    )
    m1_runner.validate_sqlite_log(database_log, text_log, run_dir / "results.csv")
    archive_names = {
        path: (
            f"colab_logs/{path.name}"
            if path in {execution_path, text_log, database_log}
            else f"{run_dir.name}/{path.relative_to(run_dir).as_posix()}"
        )
        for path in sources
    }
    files = [
        {"path": archive_names[path], "size": path.stat().st_size, "sha256": sha256_file(path)}
        for path in sources
    ]
    attestation = {
        "run": run_dir.name,
        "seed": contract["seed"],
        "run_contract_sha256": sha256_file(run_dir / "run_contract.json"),
        "cascade_manifest_sha256": CASCADE_MANIFEST_SHA256,
        "approved_pretrained_sha256": PRETRAINED_SHA256,
        "weights": {
            name: contract["artifacts"]["weights"][name]["sha256"]
            for name in ("best.pt", "last.pt")
        },
    }
    result = {
        "status": "D1_CASCADE_COLAB_RESULT_PACKAGE",
        "run": run_dir.name,
        "archive_name": output.name,
        "archive_sha256": None,
        "files": sorted(files, key=lambda row: row["path"]),
        "terminal_outcome": "SUCCEEDED",
        "sealed_test_accessed": False,
        "run_attestation": attestation,
        "run_attestation_sha256": canonical_sha256(attestation),
    }
    archive_created = manifest_created = False
    try:
        with tarfile.open(partial, mode="x:gz", compresslevel=1) as archive:
            archive_created = True
            for path in sources:
                archive.add(path, arcname=archive_names[path], recursive=False)
        require_regular_file(partial, "cascade result archive partial")
        result["archive_sha256"] = sha256_file(partial)
        with manifest_partial.open("xb") as handle:
            manifest_created = True
            handle.write(
                (
                    json.dumps(
                        result,
                        indent=2,
                        sort_keys=True,
                        ensure_ascii=False,
                        allow_nan=False,
                    )
                    + "\n"
                ).encode("utf-8")
            )
        require_regular_file(manifest_partial, "cascade result manifest partial")
        os.replace(partial, output)
        archive_created = False
        os.replace(manifest_partial, sidecar)
        manifest_created = False
    finally:
        if archive_created and path_exists_lstat(partial):
            partial.unlink()
        if manifest_created and path_exists_lstat(manifest_partial):
            manifest_partial.unlink()
    require_regular_file(output, "cascade result archive")
    require_regular_file(sidecar, "cascade result manifest")
    verify_result_archive(output, sidecar, repo_root=repo_root)
    return {**result, "manifest": str(sidecar)}


def verify_result_archive(
    archive_path: Path,
    manifest_path: Path,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Verify archive bytes and independently replay every semantic acceptance check."""
    archive_path = require_regular_file(archive_path, "cascade result archive")
    manifest_path = require_regular_file(manifest_path, "cascade result manifest")
    repo_root = absolute_lexical(repo_root or Path(__file__).resolve().parents[2])
    manifest = strict_json(manifest_path)
    required = {
        "status",
        "run",
        "archive_name",
        "archive_sha256",
        "files",
        "terminal_outcome",
        "sealed_test_accessed",
        "run_attestation",
        "run_attestation_sha256",
    }
    if not isinstance(manifest, dict) or set(manifest) != required:
        raise RuntimeError("cascade result manifest schema differs")
    if (
        manifest["status"] != "D1_CASCADE_COLAB_RESULT_PACKAGE"
        or manifest["terminal_outcome"] != "SUCCEEDED"
        or manifest["sealed_test_accessed"] is not False
        or manifest["archive_name"] != archive_path.name
        or sha256_file(archive_path) != manifest["archive_sha256"]
    ):
        raise RuntimeError("cascade result manifest identity/outcome differs")
    run = manifest["run"]
    if not isinstance(run, str) or re.fullmatch(r"D1C_[A-Za-z0-9_.-]+", run) is None:
        raise RuntimeError("cascade result run identity is unsafe")
    records = manifest["files"]
    if not isinstance(records, list) or len(records) != 8:
        raise RuntimeError("cascade result manifest must bind exactly eight files")
    def safe_name(name: Any) -> str:
        if not isinstance(name, str):
            raise RuntimeError("cascade result path must be a string")
        path = Path(name)
        if (
            not name
            or path.is_absolute()
            or name != path.as_posix()
            or "\\" in name
            or any(part in {"", ".", ".."} for part in path.parts)
        ):
            raise RuntimeError(f"unsafe cascade result path: {name!r}")
        return name

    by_path = {safe_name(record.get("path")): record for record in records}
    if len(by_path) != 8:
        raise RuntimeError("cascade result manifest contains duplicate paths")
    expected_paths = {
        f"{run}/weights/best.pt",
        f"{run}/weights/last.pt",
        f"{run}/results.csv",
        f"{run}/args.yaml",
        f"{run}/run_contract.json",
        "colab_logs/colab_execution.json",
        "colab_logs/colab_train.log",
        "colab_logs/DB_logger.db",
    }
    if set(by_path) != expected_paths:
        raise RuntimeError("cascade result manifest file roster differs")
    for name, record in by_path.items():
        if (
            not isinstance(record, dict)
            or set(record) != {"path", "size", "sha256"}
            or type(record["size"]) is not int
            or record["size"] <= 0
            or not isinstance(record["sha256"], str)
            or re.fullmatch(r"[0-9a-f]{64}", record["sha256"]) is None
        ):
            raise RuntimeError(f"cascade result file record differs: {name}")
    with tempfile.TemporaryDirectory(
        prefix="d1-cascade-result-verify-", dir=archive_path.parent
    ) as temporary:
        extracted_root = Path(temporary)
        with tarfile.open(archive_path, mode="r:gz") as archive:
            member_list = archive.getmembers()
            members = {safe_name(member.name): member for member in member_list}
            if len(members) != len(member_list):
                raise RuntimeError("cascade result archive contains duplicate members")
            if set(members) != set(by_path) or any(
                not member.isreg() for member in members.values()
            ):
                raise RuntimeError("cascade result archive roster/type differs")
            for name, record in by_path.items():
                member = members[name]
                handle = archive.extractfile(member)
                if handle is None or member.size != record["size"]:
                    raise RuntimeError(f"cascade result member size differs: {name}")
                destination = extracted_root / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                with destination.open("xb") as output:
                    shutil.copyfileobj(handle, output, length=1024 * 1024)
                if sha256_file(destination) != record["sha256"]:
                    raise RuntimeError(f"cascade result member SHA-256 differs: {name}")

        extracted_run = extracted_root / run
        execution_path = extracted_root / "colab_logs/colab_execution.json"
        execution_preview = strict_json(
            require_regular_file(execution_path, "archived cascade execution record")
        )
        if not isinstance(execution_preview, dict):
            raise RuntimeError("archived cascade execution record must be an object")
        execution_root = absolute_lexical(Path(execution_preview.get("repo_root", "")))
        contract = validate_run_contract(
            extracted_run,
            repo_root=repo_root,
            execution_repo_root=execution_root,
        )
        execution = validate_execution_record(execution_path, contract, extracted_run)
        m1_runner = load_pinned_module(
            "d1_cascade_archive_logging",
            repo_root / "detector/colab/run_d1_colab.py",
            M1_RUNNER_SHA256,
        )
        m1_runner.validate_sqlite_log(
            extracted_root / "colab_logs/DB_logger.db",
            extracted_root / "colab_logs/colab_train.log",
            extracted_run / "results.csv",
        )
        require_regular_file(extracted_run / "args.yaml", "archived args.yaml")
        if (extracted_run / "args.yaml").stat().st_size == 0:
            raise RuntimeError("archived args.yaml is empty")
        expected_attestation = {
            "run": run,
            "seed": contract["seed"],
            "run_contract_sha256": sha256_file(extracted_run / "run_contract.json"),
            "cascade_manifest_sha256": CASCADE_MANIFEST_SHA256,
            "approved_pretrained_sha256": PRETRAINED_SHA256,
            "weights": {
                name: contract["artifacts"]["weights"][name]["sha256"]
                for name in ("best.pt", "last.pt")
            },
        }
        if (
            manifest["run_attestation"] != expected_attestation
            or manifest["run_attestation_sha256"] != canonical_sha256(expected_attestation)
            or execution["status"] != manifest["terminal_outcome"]
            or execution["sealed_test_accessed"] != manifest["sealed_test_accessed"]
        ):
            raise RuntimeError("cascade result attestation differs from archived evidence")
    return manifest


def run_workflow(args: argparse.Namespace) -> int:
    repo_root = args.repo_root.expanduser().resolve()
    bundle = args.bundle.expanduser().resolve()
    state_dir = absolute_lexical(args.state_dir.expanduser())
    reject_symlink_components(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    reject_symlink_components(state_dir)
    if any(state_dir.iterdir()):
        raise RuntimeError(f"state directory must be empty: {state_dir}")
    m1_runner = load_pinned_module(
        "d1_cascade_colab_logging",
        repo_root / "detector/colab/run_d1_colab.py",
        "0d04c869d0181c68a4d60a93b05967c4db5b5e31cfc44cf653bfcbd43f225786",
    )
    logger, text_log, database_log = m1_runner.configure_logging(state_dir)
    execution_path = state_dir / "colab_execution.json"
    execution: dict[str, Any] = {
        "status": "STARTED",
        "started_at": m1_runner.now(),
        "finished_at": None,
        "repo_root": str(repo_root),
        "bundle": str(bundle),
        "bundle_sha256": sha256_file(bundle) if bundle.is_file() else None,
        "seed": args.seed,
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "device": args.device,
        "tag": args.tag,
        "sealed_test_accessed": False,
        "steps_completed": [],
        "train_command": None,
        "run_dir": None,
        "error": None,
    }
    write_json(execution_path, execution)
    logger.info(
        "D1 Colab workflow started baseline=cascade seed=%d epochs=%d",
        args.seed,
        args.epochs,
    )
    try:
        extract_shared_bundle(repo_root, bundle)
        execution["steps_completed"].append("approved_bundle_verified_and_extracted")
        m1_runner.run_command(
            logger,
            [
                sys.executable,
                "scripts/build_d1_cascade_detector_dataset.py",
                "export",
                "--repo-root",
                str(repo_root),
            ],
            cwd=repo_root,
        )
        execution["steps_completed"].append("cascade_train_val_export_regenerated")
        detector_root = repo_root / "detector"
        m1_runner.run_command(logger, ["uv", "sync", "--frozen"], cwd=detector_root)
        execution["steps_completed"].append("detector_lock_synchronized")
        model = repo_root / "models/pretrained/yolo11s.pt"
        if args.download_approved_weight:
            m1_runner.download_approved_weight(logger, model)
        elif not model.is_file() or sha256_file(model) != PRETRAINED_SHA256:
            raise RuntimeError(
                "approved pretrained weight is absent; use --download-approved-weight only "
                "under the recorded Owner authorization"
            )
        execution["steps_completed"].append("approved_pretrained_weight_verified")
        verify_cascade_contract(repo_root)
        execution["steps_completed"].append("cascade_contract_checked")
        process_env = os.environ.copy()
        process_env.update(
            {"WANDB_DISABLED": "true", "DO_NOT_TRACK": "1", "ULTRALYTICS_HUB": "false"}
        )
        script = repo_root / "detector/colab/run_d1_cascade_colab.py"
        train_command = [
            "uv",
            "run",
            "python",
            str(script),
            "_train",
            "--repo-root",
            str(repo_root),
            "--seed",
            str(args.seed),
            "--epochs",
            str(args.epochs),
            "--imgsz",
            str(args.imgsz),
            "--batch",
            str(args.batch),
            "--device",
            str(args.device),
            "--workers",
            str(args.workers),
            "--fraction",
            str(args.fraction),
            "--patience",
            str(args.patience),
            "--tag",
            args.tag,
        ]
        execution["train_command"] = train_command
        write_json(execution_path, execution)
        before = {path.resolve() for path in (repo_root / RESULTS_DIR).glob("D1C_*")}
        logger.info("Training start")
        m1_runner.run_command(logger, train_command, cwd=detector_root, env=process_env)
        logger.info("Training end")
        after = {path.resolve() for path in (repo_root / RESULTS_DIR).glob("D1C_*")}
        new_runs = sorted(after - before)
        if len(new_runs) != 1:
            raise RuntimeError(f"expected exactly one new cascade run, found {new_runs}")
        run_dir = new_runs[0]
        execution["steps_completed"].append("training_completed")
        execution["run_dir"] = str(run_dir)
        execution["status"] = "SUCCEEDED"
        execution["finished_at"] = m1_runner.now()
        write_json(execution_path, execution)
        logger.info("Terminal outcome SUCCEEDED")
        output = state_dir / f"{run_dir.name}_result.tar.gz"
        result = package_result(run_dir, execution_path, text_log, database_log, output)
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    except Exception as error:
        execution["status"] = "FAILED"
        execution["finished_at"] = m1_runner.now()
        execution["error"] = f"{type(error).__name__}: {error}"
        write_json(execution_path, execution)
        logger.exception("D1 cascade Colab workflow failed")
        return 1


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--repo-root", type=Path, required=True)
    run.add_argument("--bundle", type=Path, required=True)
    run.add_argument("--state-dir", type=Path, required=True)
    run.add_argument("--download-approved-weight", action="store_true")
    train = commands.add_parser("_train", help=argparse.SUPPRESS)
    train.add_argument("--repo-root", type=Path, required=True)
    for command in (run, train):
        command.add_argument("--seed", type=int, choices=APPROVED_SEEDS, default=APPROVED_SEEDS[0])
        command.add_argument("--epochs", type=int, default=100)
        command.add_argument("--imgsz", type=int, default=1280)
        command.add_argument("--batch", type=int, default=8)
        command.add_argument("--device", default="0")
        command.add_argument("--workers", type=int, default=4)
        command.add_argument("--fraction", type=float, default=1.0)
        command.add_argument("--patience", type=int, default=30)
        command.add_argument("--tag", default="colab")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "_train":
            return internal_train(args)
        return run_workflow(args)
    except (OSError, RuntimeError, ValueError, tarfile.TarError) as error:
        print(json.dumps({"status": "FAILED", "error": str(error)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
