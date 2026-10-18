"""Fail-closed data, model and run contracts for the D1 cascade classifier."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import pickle
import platform
import socket
import stat
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import numpy as np

DETECTOR_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = DETECTOR_ROOT.parent
DATA_ROOT = REPO_ROOT / "data/processed/dataset01_crops"
MANIFEST_PATH = REPO_ROOT / "docs/review/generated/dataset01_crops_manifest.json"
RESULTS_DIR = REPO_ROOT / "results/experiments/d1_cascade_classifier"
LOCK_PATH = DETECTOR_ROOT / "uv.lock"

MANIFEST_SHA256 = "6526844b44670e6b933ade6b48271f0f122621f783672dbfa04a1d4119beb576"
CLASSES = 54
SEEDS = (20261018, 20261019, 20261020)
ARCHITECTURES = ("compact_cnn", "vgg16_scratch")
LATENCY_WARMUP = 50
LATENCY_ITERATIONS = 300
ARRAY_SCHEMA = {
    "features": (np.dtype(np.uint8), (None, 32, 32, 3)),
    "labels": (np.dtype(np.uint8), (None,)),
    "sizes": (np.dtype(np.uint16), (None, 2)),
    "coords": (np.dtype(np.uint16), (None, 4)),
}
DATA_FILES = {"train": "train.p", "val": "valid.p"}
INDEX_FILES = {"train": "train_index.csv", "val": "valid_index.csv"}
EXACT_DATA_ROSTER = {"train.p", "valid.p", "train_index.csv", "valid_index.csv", "signnames.csv"}
OFFLINE_ENVIRONMENT = {
    "HF_HUB_OFFLINE": "1",
    "WANDB_DISABLED": "true",
    "WANDB_MODE": "disabled",
    "COMET_MODE": "DISABLED",
    "CLEARML_OFFLINE_MODE": "1",
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_sha256(payload: Any) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    return sha256_bytes(encoded)


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


def exact_keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise RuntimeError(f"{label} schema differs: expected exactly {sorted(expected)}")
    return value


def _sha256(value: Any, label: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise RuntimeError(f"{label} must be a lowercase SHA-256")
    return value


class RestrictedUnpickler(pickle.Unpickler):
    """Load the array-only package without permitting arbitrary pickle globals."""

    ALLOWED = {
        ("numpy._core.numeric", "_frombuffer"),
        ("numpy.core.numeric", "_frombuffer"),
        ("numpy", "dtype"),
    }

    def find_class(self, module: str, name: str) -> Any:
        if (module, name) not in self.ALLOWED:
            raise pickle.UnpicklingError(f"forbidden pickle global: {module}.{name}")
        return super().find_class(module, name)


def _safe_pickle(path: Path) -> dict[str, np.ndarray]:
    try:
        value = RestrictedUnpickler(io.BytesIO(path.read_bytes())).load()
    except (
        AttributeError,
        EOFError,
        ImportError,
        pickle.PickleError,
        ValueError,
        TypeError,
    ) as error:
        raise RuntimeError(f"invalid classifier pickle: {path.name}: {error}") from error
    return exact_keys(value, set(ARRAY_SCHEMA), f"{path.name} arrays")  # type: ignore[return-value]


def _validate_manifest(manifest: Any) -> dict[str, Any]:
    result = exact_keys(
        manifest,
        {
            "classes",
            "format",
            "package",
            "pinned_sources",
            "signnames_sha256",
            "splits",
            "status",
            "test",
            "use_limits",
        },
        "crop manifest",
    )
    if result["classes"] != CLASSES or result["package"] != "DATASET01-GTSRB-STYLE":
        raise RuntimeError("crop manifest identity/classes differ")
    if result["status"] != "DATASET01_GTSRB_STYLE_CROPS":
        raise RuntimeError("crop manifest status differs")
    format_record = exact_keys(
        result["format"],
        {"border", "coords", "features", "labels", "resize", "sizes"},
        "crop manifest format",
    )
    if any(type(value) is not str or not value.strip() for value in format_record.values()):
        raise RuntimeError("crop manifest format fields must be non-empty strings")
    if not isinstance(result["pinned_sources"], dict) or not result["pinned_sources"]:
        raise RuntimeError("crop manifest pinned sources must be a non-empty object")
    for path, digest in result["pinned_sources"].items():
        if type(path) is not str or not path.strip():
            raise RuntimeError("crop manifest pinned source path is blank")
        _sha256(digest, f"crop manifest source {path}")
    _sha256(result["signnames_sha256"], "crop manifest signnames")
    if (
        type(result["test"]) is not str
        or "sealed" not in result["test"]
        or not isinstance(result["use_limits"], list)
        or not result["use_limits"]
        or any(type(item) is not str or not item.strip() for item in result["use_limits"])
    ):
        raise RuntimeError("crop manifest use limits/test policy differ")
    exact_keys(result["splits"], {"train", "val"}, "crop manifest splits")
    for split in ("train", "val"):
        row = exact_keys(
            result["splits"][split],
            {
                "classes",
                "file",
                "index_sha256",
                "per_class",
                "samples",
                "sha256",
                "signs_under_16px",
                "sources",
            },
            f"crop manifest {split}",
        )
        if (
            row["file"] != DATA_FILES[split]
            or type(row["samples"]) is not int
            or row["samples"] <= 0
            or type(row["classes"]) is not int
            or row["classes"] <= 0
            or type(row["signs_under_16px"]) is not int
            or row["signs_under_16px"] < 0
        ):
            raise RuntimeError(f"crop manifest {split} identity/count differs")
        hashes = exact_keys(
            row["sha256"], set(ARRAY_SCHEMA), f"crop manifest {split} array hashes"
        )
        for name, digest in hashes.items():
            _sha256(digest, f"crop manifest {split}.{name}")
        _sha256(row["index_sha256"], f"crop manifest {split} index")
        if not isinstance(row["per_class"], dict) or not row["per_class"]:
            raise RuntimeError(f"crop manifest {split} per_class differs")
        for class_id, count in row["per_class"].items():
            if not class_id.isdigit() or not 0 <= int(class_id) < CLASSES:
                raise RuntimeError(f"crop manifest {split} class id differs")
            if type(count) is not int or count <= 0:
                raise RuntimeError(f"crop manifest {split} class count differs")
        if sum(row["per_class"].values()) != row["samples"]:
            raise RuntimeError(f"crop manifest {split} class total differs")
        if row["classes"] != len(row["per_class"]):
            raise RuntimeError(f"crop manifest {split} represented-class count differs")
        if not isinstance(row["sources"], dict) or sum(row["sources"].values()) != row["samples"]:
            raise RuntimeError(f"crop manifest {split} source counts differ")
    return result


def _reject_forbidden_path(path: Path) -> None:
    forbidden = {"test", "test.p", "test_index.csv", "data_test.yaml"}
    if any(part.lower() in forbidden for part in path.parts):
        raise RuntimeError(f"sealed-test path is forbidden for cascade classifier: {path}")


def _validate_signnames(path: Path, expected_sha256: str) -> None:
    if sha256_file(path) != expected_sha256:
        raise RuntimeError("signnames.csv hash differs from crop manifest")
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise RuntimeError("signnames.csv is empty")
    if [int(row["ClassId"]) for row in rows] != list(range(CLASSES)):
        raise RuntimeError("signnames.csv must contain ClassId 0..53 exactly once and in order")
    if set(rows[0]) != {"ClassId", "SignName", "DerivedKey", "QCVN"}:
        raise RuntimeError("signnames.csv schema differs")


def _validate_arrays(
    split: str, arrays: dict[str, np.ndarray], manifest_split: dict[str, Any]
) -> dict[str, Any]:
    samples = manifest_split["samples"]
    hashes: dict[str, str] = {}
    for name, (dtype, shape) in ARRAY_SCHEMA.items():
        value = arrays[name]
        if not isinstance(value, np.ndarray) or value.dtype != dtype:
            raise RuntimeError(f"{split}.{name} dtype differs")
        expected_shape = (samples, *shape[1:])
        if value.shape != expected_shape or not value.flags.c_contiguous:
            raise RuntimeError(f"{split}.{name} shape/contiguity differs: {value.shape}")
        hashes[name] = sha256_bytes(value.tobytes(order="C"))
        if hashes[name] != manifest_split["sha256"][name]:
            raise RuntimeError(f"{split}.{name} hash differs from crop manifest")
    labels = arrays["labels"]
    if labels.size and (int(labels.min()) < 0 or int(labels.max()) >= CLASSES):
        raise RuntimeError(f"{split} label outside 0..{CLASSES - 1}")
    counts = {str(i): int(np.sum(labels == i)) for i in sorted(set(labels.tolist()))}
    if counts != manifest_split["per_class"]:
        raise RuntimeError(f"{split} class counts differ from crop manifest")
    return {"samples": samples, "array_sha256": hashes}


def check_data_contract(
    data_root: Path = DATA_ROOT,
    manifest_path: Path = MANIFEST_PATH,
    *,
    expected_manifest_sha256: str | None = MANIFEST_SHA256,
) -> tuple[dict[str, Any], dict[str, dict[str, np.ndarray]]]:
    data_root = Path(os.path.abspath(data_root)).resolve()
    manifest_path = Path(os.path.abspath(manifest_path)).resolve()
    _reject_forbidden_path(data_root)
    _reject_forbidden_path(manifest_path)
    if not data_root.is_dir() or not manifest_path.is_file():
        raise RuntimeError("classifier data root or crop manifest is missing")
    roster = {path.name for path in data_root.iterdir()}
    if roster != EXACT_DATA_ROSTER:
        raise RuntimeError(f"classifier data roster differs: {sorted(roster)}")
    if any(path.is_symlink() or not path.is_file() for path in data_root.iterdir()):
        raise RuntimeError("classifier data roster must contain regular non-symlink files")
    manifest_hash = sha256_file(manifest_path)
    if expected_manifest_sha256 is not None and manifest_hash != expected_manifest_sha256:
        raise RuntimeError("crop manifest hash differs from the reviewed package")
    manifest = _validate_manifest(strict_json(manifest_path))
    _validate_signnames(data_root / "signnames.csv", manifest["signnames_sha256"])
    arrays: dict[str, dict[str, np.ndarray]] = {}
    split_contract: dict[str, Any] = {}
    for split in ("train", "val"):
        pickle_path = data_root / DATA_FILES[split]
        index_path = data_root / INDEX_FILES[split]
        if sha256_file(index_path) != manifest["splits"][split]["index_sha256"]:
            raise RuntimeError(f"{split} index hash differs from crop manifest")
        arrays[split] = _safe_pickle(pickle_path)
        split_contract[split] = {
            **_validate_arrays(split, arrays[split], manifest["splits"][split]),
            "pickle_sha256": sha256_file(pickle_path),
            "index_sha256": sha256_file(index_path),
        }
    return (
        {
            "manifest_path": str(manifest_path),
            "manifest_sha256": manifest_hash,
            "signnames_sha256": manifest["signnames_sha256"],
            "splits": split_contract,
            "sealed_test_accessed": False,
        },
        arrays,
    )


def validate_architecture(name: str) -> str:
    if name not in ARCHITECTURES:
        raise RuntimeError(f"unknown architecture {name!r}; allowed: {ARCHITECTURES}")
    return name


def validate_seed(seed: int) -> int:
    if seed not in SEEDS:
        raise RuntimeError(f"seed {seed} is not approved; allowed: {SEEDS}")
    return seed


def model_config(architecture: str) -> dict[str, Any]:
    validate_architecture(architecture)
    return {
        "architecture": architecture,
        "classes": CLASSES,
        "input_shape": [3, 32, 32],
        "weights": None,
        "horizontal_flip": False,
    }


def environment() -> dict[str, Any]:
    import torch
    import torchvision

    def git(*args: str) -> str:
        try:
            return subprocess.run(
                ["git", *args], cwd=REPO_ROOT, check=True, capture_output=True, text=True
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return "UNKNOWN"

    dirty = git("status", "--porcelain")
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "torch": torch.__version__,
        "torchvision": torchvision.__version__,
        "cuda_available": torch.cuda.is_available(),
        "mps_available": bool(
            getattr(torch.backends, "mps", None) and torch.backends.mps.is_available()
        ),
        "git_commit": git("rev-parse", "HEAD"),
        "git_dirty_files": len(dirty.splitlines()) if dirty and dirty != "UNKNOWN" else 0,
        "detector_lock_sha256": sha256_file(LOCK_PATH),
        "offline_environment": OFFLINE_ENVIRONMENT,
    }


@contextmanager
def offline_mode() -> Iterator[None]:
    """Disable telemetry and fail closed on Python socket connections during model work."""
    previous = {key: os.environ.get(key) for key in OFFLINE_ENVIRONMENT}
    original_create_connection = socket.create_connection
    original_connect = socket.socket.connect

    def blocked(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("network access is disabled for the cascade classifier")

    os.environ.update(OFFLINE_ENVIRONMENT)
    socket.create_connection = blocked
    socket.socket.connect = blocked
    try:
        yield
    finally:
        socket.create_connection = original_create_connection
        socket.socket.connect = original_connect
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def absolute_lexical(path: Path | str) -> Path:
    """Return an absolute path without erasing symlink identity through resolve()."""
    return Path(os.path.abspath(Path(path).expanduser()))


def reject_symlink_components(path: Path) -> None:
    """Reject every existing symlink from the filesystem anchor through ``path``."""
    lexical = absolute_lexical(path)
    current = Path(lexical.anchor)
    for part in lexical.parts[1:]:
        current /= part
        try:
            mode = os.lstat(current).st_mode
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(mode):
            raise RuntimeError(f"path contains a symlink component: {current}")


def _inside_results(path: Path, label: str) -> Path:
    lexical = absolute_lexical(path)
    results = absolute_lexical(RESULTS_DIR)
    try:
        lexical.relative_to(results)
    except ValueError as error:
        raise RuntimeError(f"{label} must stay under {results}") from error
    reject_symlink_components(results)
    reject_symlink_components(lexical)
    return lexical


def _regular_file(path: Path, label: str) -> Path:
    lexical = _inside_results(path, label)
    try:
        mode = os.lstat(lexical).st_mode
    except FileNotFoundError as error:
        raise RuntimeError(f"{label} is missing: {lexical}") from error
    if not stat.S_ISREG(mode):
        raise RuntimeError(f"{label} must be a regular non-symlink file: {lexical}")
    return lexical


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Atomically write JSON below results without following any symlink."""
    lexical = absolute_lexical(path)
    parent = absolute_lexical(lexical.parent)
    results = absolute_lexical(RESULTS_DIR)
    try:
        parent.relative_to(results)
    except ValueError as error:
        raise RuntimeError(f"JSON output must stay under {results}") from error
    reject_symlink_components(results)
    reject_symlink_components(parent)
    parent.mkdir(parents=True, exist_ok=True)
    reject_symlink_components(parent)
    try:
        mode = os.lstat(lexical).st_mode
    except FileNotFoundError:
        pass
    else:
        if not stat.S_ISREG(mode):
            raise RuntimeError(f"JSON output must be a regular non-symlink file: {lexical}")
    encoded = (
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    ).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{lexical.name}.", dir=parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        # os.replace replaces a raced-in symlink entry itself; it never follows its target.
        os.replace(temporary, lexical)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def prepare_run_directory(run_dir: Path) -> Path:
    """Create a new run below the fixed results root without following symlink components."""
    lexical = absolute_lexical(run_dir)
    expected_parent = absolute_lexical(RESULTS_DIR)
    if lexical.parent != expected_parent:
        raise RuntimeError(f"run directory must be a direct child of {expected_parent}")
    reject_symlink_components(lexical)
    if lexical.exists():
        raise RuntimeError(f"run directory already exists: {lexical}")
    (lexical / "weights").mkdir(parents=True)
    return lexical


def load_run_weights(weights: str) -> tuple[Path, dict[str, Any]]:
    path = absolute_lexical(weights)
    _reject_forbidden_path(path)
    if path.name not in {"best.pt", "last.pt"} or path.parent.name != "weights":
        raise RuntimeError("weights must be <run>/weights/best.pt or last.pt")
    run_dir = path.parent.parent
    _inside_results(run_dir, "classifier run")
    if not run_dir.is_dir() or not path.parent.is_dir():
        raise RuntimeError("classifier run/weights directory is missing")
    path = _regular_file(path, "selected classifier checkpoint")
    contract_path = _regular_file(run_dir / "run_contract.json", "classifier run contract")
    record = exact_keys(
        strict_json(contract_path),
        {
            "artifacts",
            "bindings",
            "config",
            "data",
            "environment",
            "experiment",
            "model",
            "run",
            "seed",
            "status",
        },
        "classifier run contract",
    )
    if (
        record["experiment"] != "D1_CASCADE_CLASSIFIER"
        or record["status"] != "TRAINED"
        or record["run"] != run_dir.name
    ):
        raise RuntimeError("classifier run identity/status differs")
    validate_seed(record["seed"])
    model = exact_keys(
        record["model"],
        {"architecture", "classes", "horizontal_flip", "input_shape", "weights"},
        "model",
    )
    validate_architecture(model["architecture"])
    if model != model_config(model["architecture"]):
        raise RuntimeError("classifier model contract differs")
    config = exact_keys(
        record["config"],
        {
            "architecture",
            "batch",
            "device",
            "epochs",
            "horizontal_flip",
            "learning_rate",
            "model_config_sha256",
            "seed",
            "weights",
            "workers",
        },
        "classifier train config",
    )
    if (
        config["architecture"] != model["architecture"]
        or config["seed"] != record["seed"]
        or config["horizontal_flip"] is not False
        or config["weights"] is not None
        or config["workers"] != 0
    ):
        raise RuntimeError("classifier config contradicts model/seed invariants")
    if (
        type(config["epochs"]) is not int
        or config["epochs"] <= 0
        or type(config["batch"]) is not int
        or config["batch"] <= 0
        or type(config["learning_rate"]) not in (int, float)
        or not math.isfinite(config["learning_rate"])
        or config["learning_rate"] <= 0
        or config["device"] not in {"cpu", "mps", "cuda"}
    ):
        raise RuntimeError("classifier config contains invalid numeric/device values")
    _sha256(config["model_config_sha256"], "classifier model config")
    expected_environment = {
        "cuda_available",
        "detector_lock_sha256",
        "git_commit",
        "git_dirty_files",
        "machine",
        "mps_available",
        "offline_environment",
        "platform",
        "python",
        "torch",
        "torchvision",
    }
    exact_keys(record["environment"], expected_environment, "classifier environment")
    environment_record = record["environment"]
    for key in ("git_commit", "machine", "platform", "python", "torch", "torchvision"):
        if type(environment_record[key]) is not str or not environment_record[key].strip():
            raise RuntimeError(f"classifier environment {key} is blank")
    if (
        type(environment_record["git_dirty_files"]) is not int
        or environment_record["git_dirty_files"] < 0
        or type(environment_record["cuda_available"]) is not bool
        or type(environment_record["mps_available"]) is not bool
    ):
        raise RuntimeError("classifier environment primitive fields differ")
    if record["environment"]["detector_lock_sha256"] != sha256_file(LOCK_PATH):
        raise RuntimeError("classifier environment detector lock hash differs")
    if record["environment"]["offline_environment"] != OFFLINE_ENVIRONMENT:
        raise RuntimeError("classifier environment does not bind offline controls")
    artifacts = exact_keys(
        record["artifacts"], {"best.pt", "history.json", "last.pt"}, "classifier artifacts"
    )
    for artifact_name, artifact_record in artifacts.items():
        artifact_record = exact_keys(
            artifact_record, {"path", "sha256"}, f"classifier artifact {artifact_name}"
        )
        artifact_path = (
            run_dir / "weights" / artifact_name
            if artifact_name.endswith(".pt")
            else run_dir / artifact_name
        )
        artifact_path = _regular_file(artifact_path, f"classifier artifact {artifact_name}")
        if artifact_record["path"] != str(artifact_path):
            raise RuntimeError(f"classifier artifact path differs: {artifact_name}")
        _sha256(artifact_record["sha256"], f"classifier artifact {artifact_name}")
        if not artifact_path.is_file() or artifact_record["sha256"] != sha256_file(artifact_path):
            raise RuntimeError(f"classifier artifact hash differs: {artifact_name}")
    artifact = artifacts[path.name]
    if not isinstance(artifact, dict) or artifact.get("sha256") != sha256_file(path):
        raise RuntimeError("classifier checkpoint hash differs from run contract")
    current_data, _ = check_data_contract()
    if record["data"] != current_data:
        raise RuntimeError("classifier run data contract differs from current governed data")
    if record["config"].get("model_config_sha256") != canonical_sha256(model):
        raise RuntimeError("classifier model config hash differs")
    bindings = exact_keys(
        record["bindings"],
        {"config_sha256", "data_sha256", "environment_sha256", "model_sha256"},
        "classifier run bindings",
    )
    expected_bindings = {
        "config_sha256": canonical_sha256(record["config"]),
        "data_sha256": canonical_sha256(record["data"]),
        "environment_sha256": canonical_sha256(record["environment"]),
        "model_sha256": canonical_sha256(record["model"]),
    }
    if bindings != expected_bindings:
        raise RuntimeError("classifier run data/model/config/environment binding differs")
    return path, record
