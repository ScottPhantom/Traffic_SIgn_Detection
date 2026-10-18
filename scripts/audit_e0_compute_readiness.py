# ruff: noqa: E501
"""Build and verify the read-only M0-WP6 frozen-E0 compute/readiness preflight."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import pickle
import platform
import statistics
import subprocess
import sys
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from cpv301_autodrive.inference import preprocess_image
from cpv301_autodrive.labels import GTSRB_LABELS

STATUS = "WP6_AWAITING_QA_READ_ONLY_PREFLIGHT"
EVIDENCE_BOUNDARY = (
    "FROZEN_E0_LOCAL_PREFLIGHT_ONLY_NO_D05_APPROVAL_NO_CALIBRATION_NO_OOD_CLAIM_"
    "NO_VIETNAM_VALIDATION_NO_TRAINING"
)
MANIFEST_SCHEMA_VERSION = 2
MANIFEST_COUNT_SEMANTICS = "EXCLUDES_MANIFEST_FILE"
MANIFEST_RELATIVE_PATH = "docs/review/generated/wp6_e0_compute_manifest.json"
EVIDENCE_RELATIVE_PATH = "docs/review/generated/wp6_e0_compute_readiness.json"
ATTESTATION_RELATIVE_PATH = "docs/review/generated/wp6_e0_compute_attestation.json"
REPORT_RELATIVE_PATH = "docs/review/wp6_e0_compute_readiness_report.md"
ATTESTATION_STATUS = "WP6_CLEAN_BUILD_BENCHMARK_ATTESTATION"
CANDIDATE_STATUS = "WP6_UNPINNED_CANDIDATE_REQUIRES_REVIEWED_SOURCE_ANCHOR"
CANDIDATE_DIR_RELATIVE_PATH = "tmp/wp6_candidate"
CANDIDATE_EVIDENCE_FILENAME = "wp6_e0_compute_readiness_candidate.json"
CANDIDATE_ATTESTATION_FILENAME = "wp6_e0_compute_attestation_candidate.json"
TRUSTED_ATTESTATION_SHA256 = (
    "5102dc7493cd32f0f958430b3d0dd25b0e288ba10052b81ee17236b4acfb3c56"
)
BENCHMARK_SPLIT_ID = "gtsrb_test"
BENCHMARK_SEED = 20261010
WARMUP_ITERATIONS = 20
MEASURED_REPEATS = 3
ITERATIONS_PER_REPEAT = 100
MEASURED_ITERATIONS = MEASURED_REPEATS * ITERATIONS_PER_REPEAT
EXPECTED_SOURCE_COUNT = 20
EXPECTED_MEASURED_CLASS_COUNT = 41
EXPECTED_PREDICTION_TRACE_SHA256 = (
    "ecfdc3d7c76d8f8eb7208ec431b6bb1b45104e1bcd0e3e0e5e134e9d31044a1d"
)
TIMED_OPERATIONS = [
    "PIL RGB conversion/check and bilinear resize to 32x32",
    "NumPy float32 conversion and division by 255",
    "Keras model.predict with batch_size=1 and output materialization",
]
EXCLUDED_OPERATIONS = [
    "pickle file read/deserialization",
    "source hash verification",
    "model file load/deserialization",
    "PIL image object construction from the already-loaded array",
    "sample selection",
    "JSON/report serialization",
]
TIMING_METHOD = "time.perf_counter_ns around preprocess_image plus keras model.predict"
LATENCY_STATUS = "MEASURED_LOCAL_E0_DIAGNOSTIC_NOT_AN_ACCEPTANCE_GATE"
LATENCY_INTERPRETATION_BOUNDARY = (
    "Observed latency on this local host/backend only. D-05 is unapproved/inactive, so "
    "this measurement is not a pass/fail acceptance decision and cannot be generalized "
    "to another device, GPU backend, Vietnamese data or end-to-end camera latency."
)
READINESS_STATUS = (
    "TECHNICALLY_READY_FOR_LATER_DIAGNOSTIC_DESIGN_WITH_UNRESOLVED_GOVERNANCE_AND_OOD_INPUTS"
)
READINESS_AVAILABLE = [
    "Frozen hash-pinned E0 model with verified 43-class input/output contract",
    "Hash-pinned GTSRB train/valid/test arrays with exact schema and all 43 classes",
    "Existing closed-set E0 test metrics and calibration diagnostic ECE",
    "Reproducible local batch-1 latency command and measured backend contract",
]
READINESS_VALID_SPLIT = (
    "DIAGNOSTIC_ONLY_SAME_GTSRB_SOURCE_AND_USED_DURING_MODEL_DEVELOPMENT; NOT_AN_"
    "INDEPENDENT_VIETNAMESE_HOLDOUT"
)
READINESS_TEST_POLICY = (
    "FROZEN_E0_EVALUATION_REFERENCE_ALREADY_OPENED; DO_NOT_SELECT_TEMPERATURE_OR_"
    "UNKNOWN_THRESHOLD_ON_TEST"
)
READINESS_BLOCKERS = [
    "No approved D-05 bundle, latency gate, seed budget or reviewer decision",
    "No provenance-approved unknown-sign OOD set",
    "No provenance-approved non-sign/background OOD set for classifier rejection",
    "No difficult-image OOD groups for blur, night, rain, occlusion or full-scene inputs",
    "No independent Vietnamese validation/holdout with approved taxonomy and grouping",
    "No locked group-aware Vietnam train/validation/test manifests",
    "No frozen probability-export/calibration fitting protocol or threshold-selection protocol",
    "Current confidence_threshold=0.50 is a demo value and raw Softmax is not an UNKNOWN guarantee",
]
READINESS_ACTIONS_NOT_PERFORMED = [
    "No temperature fitting",
    "No UNKNOWN/OOD threshold selection",
    "No OOD performance calculation",
    "No training or fine-tuning",
    "No model promotion",
    "No split mutation",
]
EXPECTED_MODEL_LAYERS = [
    {"name": "conv2d", "class_name": "Conv2D", "parameters": 896},
    {"name": "activation", "class_name": "Activation", "parameters": 0},
    {
        "name": "batch_normalization",
        "class_name": "BatchNormalization",
        "parameters": 128,
    },
    {"name": "conv2d_1", "class_name": "Conv2D", "parameters": 9248},
    {"name": "activation_1", "class_name": "Activation", "parameters": 0},
    {
        "name": "batch_normalization_1",
        "class_name": "BatchNormalization",
        "parameters": 128,
    },
    {"name": "max_pooling2d", "class_name": "MaxPooling2D", "parameters": 0},
    {"name": "conv2d_2", "class_name": "Conv2D", "parameters": 18496},
    {"name": "activation_2", "class_name": "Activation", "parameters": 0},
    {
        "name": "batch_normalization_2",
        "class_name": "BatchNormalization",
        "parameters": 256,
    },
    {"name": "conv2d_3", "class_name": "Conv2D", "parameters": 36928},
    {"name": "activation_3", "class_name": "Activation", "parameters": 0},
    {
        "name": "batch_normalization_3",
        "class_name": "BatchNormalization",
        "parameters": 256,
    },
    {"name": "max_pooling2d_1", "class_name": "MaxPooling2D", "parameters": 0},
    {"name": "flatten", "class_name": "Flatten", "parameters": 0},
    {"name": "dense", "class_name": "Dense", "parameters": 2097664},
    {"name": "activation_4", "class_name": "Activation", "parameters": 0},
    {
        "name": "batch_normalization_4",
        "class_name": "BatchNormalization",
        "parameters": 2048,
    },
    {"name": "dense_1", "class_name": "Dense", "parameters": 22059},
    {"name": "activation_5", "class_name": "Activation", "parameters": 0},
]
EXPECTED_SPLITS = {
    "train": {"samples": 34799, "sha256": "5c319e00df7f45a18761e65dfd47341779c310798a71ea3f371659cc4a63da44"},
    "valid": {"samples": 4410, "sha256": "7d92b991f95cf3bfcc6e35b88bad506b89e562992c1eb6c1034462a9604b6948"},
    "test": {"samples": 12630, "sha256": "60b6450ffdb227042eb32f28d15fe77f98ad24dd550cc85eb445b8c0e502e470"},
}
EXPECTED_PINNED_HASHES = {
    "model": "745cf3f6e9f5edfe32954866d93f07d9504f6bc2d4f3667c8b8f99f1c924b565",
    "uv_lock": "0562d2fdda3a3a9173973df132bac3f7f88df7ac4fab589b2d2eacc9538a518e",
    "pyproject": "e0f45811a0e963d7163cd7f9c0f48a0f719b895c4c8e4c2d9b61d49b383cafe6",
    "e0_manifest": "24fd31868abb048794e1c656efc3b12dad4f0194e4c54e2b667644565c7d41d4",
    "evaluation_summary": "99884485b8762c89a48feb1194a150f062963ffa64e3444acc27026b99a6864e",
    "evaluation_per_class": "7ba35ccdadbc16416e1987ccfb71541d189608e9a5371f0a68e3370bf52341f8",
    "evaluation_confusion": "8a8daf2ca019177c8605684048c6a06bc07a407c87ed1bdc57e2043317e0d801",
    "evaluation_mistakes": "b42f3463ad2748759fe5ace869815d595afaff167974350408cbfbdbbfa4055f",
    "decision_status": "87d81262e907bb1c479cfac6535e7b3f67a368c371e96b810aa02f2e92d0d72c",
    "experiment_acceptance": "4d126725dea7464004c60da370eaf84a9ba16dc83b716c04db9d0344e086a4c8",
    "drive_inventory": "35feb56fddc3cc2f9d037643fe0fc6ff8b43b0de651952a9168e006c58577c3f",
    "model_provenance": "a13a6b895ef1e51e2fa82a7ae32c1afe4a85f6ff1de3470a2211b01ac1ea8712",
    "initial_assessment": "e9e51d90db6b844f4cf51b86bd4c4914dd2b59bb1ccdf1b22d39ca347d6088a0",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_sha256(payload: Any) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def nested_mapping_keys(payload: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(payload, dict):
        for key, value in payload.items():
            keys.add(str(key).lower())
            keys.update(nested_mapping_keys(value))
    elif isinstance(payload, list):
        for value in payload:
            keys.update(nested_mapping_keys(value))
    return keys


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def command_output(command: list[str]) -> str | None:
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    value = result.stdout.strip()
    return value or None


def int_command(command: list[str]) -> int | None:
    value = command_output(command)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def collect_hardware_inventory() -> dict[str, Any]:
    displays: list[dict[str, Any]] = []
    raw_displays = command_output(["system_profiler", "SPDisplaysDataType", "-json"])
    if raw_displays is not None:
        try:
            payload = json.loads(raw_displays)
            for display in payload.get("SPDisplaysDataType", []):
                displays.append(
                    {
                        "chipset_model": display.get("sppci_model") or display.get("_name"),
                        "type": display.get("sppci_device_type"),
                        "bus": display.get("sppci_bus"),
                        "cores": int(display["sppci_cores"])
                        if str(display.get("sppci_cores", "")).isdigit()
                        else None,
                        "metal_family": display.get("spdisplays_mtlgpufamilysupport"),
                    }
                )
        except (json.JSONDecodeError, TypeError, ValueError):
            displays = []
    sw_name = command_output(["sw_vers", "-productName"])
    sw_version = command_output(["sw_vers", "-productVersion"])
    sw_build = command_output(["sw_vers", "-buildVersion"])
    return {
        "observation_status": "OBSERVED_LOCAL_HOST",
        "os": {
            "name": sw_name or platform.system() or "UNKNOWN",
            "version": sw_version or platform.release() or "UNKNOWN",
            "build": sw_build or "UNKNOWN",
            "kernel": platform.release(),
            "machine": platform.machine(),
        },
        "cpu": {
            "brand": command_output(["sysctl", "-n", "machdep.cpu.brand_string"])
            or platform.processor()
            or "UNKNOWN",
            "physical_cores": int_command(["sysctl", "-n", "hw.physicalcpu"]),
            "logical_cores": int_command(["sysctl", "-n", "hw.logicalcpu"])
            or os.cpu_count(),
        },
        "memory_bytes": int_command(["sysctl", "-n", "hw.memsize"]),
        "graphics": displays,
        "privacy_boundary": (
            "No serial number, hardware UUID, provisioning identifier, username or display "
            "serial is collected."
        ),
    }


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def collect_runtime_inventory(repo_root: Path) -> tuple[dict[str, Any], Any]:
    import tensorflow as tf
    from tensorflow import keras

    physical = [
        {"name": device.name, "type": device.device_type}
        for device in tf.config.list_physical_devices()
    ]
    logical = [
        {"name": device.name, "type": device.device_type}
        for device in tf.config.list_logical_devices()
    ]
    gpu_visible = any(device["type"] == "GPU" for device in logical)
    executable = Path(os.path.abspath(sys.executable))
    try:
        executable_value = executable.relative_to(repo_root.absolute()).as_posix()
    except ValueError:
        executable_value = f"external-environment/{executable.name}"
    uv_version = command_output(["uv", "--version"])
    runtime = {
        "observation_status": "OBSERVED_CURRENT_UV_ENVIRONMENT",
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "python_executable": executable_value,
        "uv_version": uv_version or "UNKNOWN",
        "tensorflow_version": tf.__version__,
        "keras_version": package_version("keras") or getattr(keras, "__version__", "UNKNOWN"),
        "tensorflow_macos_version": package_version("tensorflow-macos"),
        "tensorflow_metal_version": package_version("tensorflow-metal"),
        "physical_devices": physical,
        "logical_devices": logical,
        "tensorflow_built_with_cuda": bool(tf.test.is_built_with_cuda()),
        "execution_backend": "TENSORFLOW_GPU" if gpu_visible else "TENSORFLOW_CPU_ONLY",
        "gpu_visible_to_tensorflow": gpu_visible,
    }
    return runtime, keras


def runtime_attestation_payload(runtime: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "python_version",
        "python_implementation",
        "uv_version",
        "tensorflow_version",
        "keras_version",
        "tensorflow_macos_version",
        "tensorflow_metal_version",
        "physical_devices",
        "logical_devices",
        "tensorflow_built_with_cuda",
        "execution_backend",
        "gpu_visible_to_tensorflow",
    )
    return {field: runtime[field] for field in fields}


def source_contract(repo_root: Path) -> list[tuple[str, Path, str | None]]:
    fixed = [
        ("model", repo_root / "models/VGG16_model.h5", EXPECTED_PINNED_HASHES["model"]),
        ("gtsrb_train", repo_root / "data/processed/train.p", EXPECTED_SPLITS["train"]["sha256"]),
        ("gtsrb_valid", repo_root / "data/processed/valid.p", EXPECTED_SPLITS["valid"]["sha256"]),
        ("gtsrb_test", repo_root / "data/processed/test.p", EXPECTED_SPLITS["test"]["sha256"]),
        ("uv_lock", repo_root / "uv.lock", EXPECTED_PINNED_HASHES["uv_lock"]),
        ("pyproject", repo_root / "pyproject.toml", EXPECTED_PINNED_HASHES["pyproject"]),
        ("e0_manifest", repo_root / "results/experiments/E0_GTSRB_baseline/manifest.json", EXPECTED_PINNED_HASHES["e0_manifest"]),
        ("evaluation_summary", repo_root / "results/evaluation/gtsrb_test_baseline/summary.json", EXPECTED_PINNED_HASHES["evaluation_summary"]),
        ("evaluation_per_class", repo_root / "results/evaluation/gtsrb_test_baseline/per_class_metrics.csv", EXPECTED_PINNED_HASHES["evaluation_per_class"]),
        ("evaluation_confusion", repo_root / "results/evaluation/gtsrb_test_baseline/confusion_matrix.csv", EXPECTED_PINNED_HASHES["evaluation_confusion"]),
        ("evaluation_mistakes", repo_root / "results/evaluation/gtsrb_test_baseline/high_confidence_mistakes.csv", EXPECTED_PINNED_HASHES["evaluation_mistakes"]),
        ("decision_status", repo_root / "docs/review/decision_status.json", EXPECTED_PINNED_HASHES["decision_status"]),
        ("experiment_acceptance", repo_root / "docs/review/experiment_acceptance_template.md", EXPECTED_PINNED_HASHES["experiment_acceptance"]),
        ("drive_inventory", repo_root / "docs/drive_inventory.md", EXPECTED_PINNED_HASHES["drive_inventory"]),
        ("model_provenance", repo_root / "docs/model_provenance.md", EXPECTED_PINNED_HASHES["model_provenance"]),
        ("initial_assessment", repo_root / "docs/initial_model_assessment.md", EXPECTED_PINNED_HASHES["initial_assessment"]),
    ]
    controls = [
        ("wp6_script", repo_root / "scripts/audit_e0_compute_readiness.py", None),
        ("inference_source", repo_root / "src/cpv301_autodrive/inference.py", None),
        ("evaluation_source", repo_root / "src/cpv301_autodrive/evaluation.py", None),
        ("labels_source", repo_root / "src/cpv301_autodrive/labels.py", None),
    ]
    return [*fixed, *controls]


def artifact_contract(repo_root: Path) -> list[tuple[str, Path]]:
    return [
        ("readiness_evidence", repo_root / EVIDENCE_RELATIVE_PATH),
        ("benchmark_attestation", repo_root / ATTESTATION_RELATIVE_PATH),
        ("human_report", repo_root / REPORT_RELATIVE_PATH),
    ]


def relative_record(path: Path, repo_root: Path, item_id: str) -> dict[str, Any]:
    relative = path.resolve().relative_to(repo_root.resolve()).as_posix()
    return {
        "id": item_id,
        "path": relative,
        "sha256": sha256_file(path),
        "size": path.stat().st_size,
    }


def verify_pinned_sources(repo_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item_id, path, expected_hash in source_contract(repo_root):
        if not path.is_file():
            raise FileNotFoundError(f"required WP6 source missing: {path}")
        actual_hash = sha256_file(path)
        if expected_hash is not None and actual_hash != expected_hash:
            raise ValueError(
                f"pinned source hash mismatch for {item_id}: expected {expected_hash}, got {actual_hash}"
            )
        records.append(
            {
                **relative_record(path, repo_root, item_id),
                "pinned_expected_sha256": expected_hash,
                "hash_status": "MATCH" if expected_hash is not None else "OBSERVED_CONTROL",
            }
        )
    return records


def load_trusted_split(
    path: Path, split_name: str, repo_root: Path
) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    expected = EXPECTED_SPLITS[split_name]
    actual_hash = sha256_file(path)
    if actual_hash != expected["sha256"]:
        raise ValueError(f"{split_name} split hash mismatch before pickle load")
    with path.open("rb") as stream:
        payload = pickle.load(stream)  # noqa: S301 - hash-pinned local Drive artifact
    if not isinstance(payload, dict) or set(payload) != {
        "features",
        "labels",
        "coords",
        "sizes",
    }:
        raise ValueError(f"{split_name} split must have exact features/labels/coords/sizes keys")
    arrays = {key: np.asarray(value) for key, value in payload.items()}
    features = arrays["features"]
    labels = arrays["labels"]
    coords = arrays["coords"]
    sizes = arrays["sizes"]
    sample_count = expected["samples"]
    if features.shape != (sample_count, 32, 32, 3) or features.dtype != np.uint8:
        raise ValueError(f"invalid {split_name} feature schema: {features.shape}/{features.dtype}")
    if labels.shape != (sample_count,) or not np.issubdtype(labels.dtype, np.integer):
        raise ValueError(f"invalid {split_name} label schema: {labels.shape}/{labels.dtype}")
    if coords.shape != (sample_count, 4) or sizes.shape != (sample_count, 2):
        raise ValueError(f"invalid {split_name} coords/sizes schema")
    unique_classes = np.unique(labels)
    if unique_classes.tolist() != list(range(43)):
        raise ValueError(f"{split_name} must contain all class IDs 0..42")
    if int(features.min()) < 0 or int(features.max()) > 255:
        raise ValueError(f"{split_name} pixels outside uint8 range")
    report = {
        "path": path.resolve().relative_to(repo_root.resolve()).as_posix(),
        "sha256": actual_hash,
        "samples": sample_count,
        "keys": sorted(payload),
        "features": {
            "shape": list(features.shape),
            "dtype": str(features.dtype),
            "min": int(features.min()),
            "max": int(features.max()),
        },
        "labels": {
            "shape": list(labels.shape),
            "dtype": str(labels.dtype),
            "min": int(labels.min()),
            "max": int(labels.max()),
            "observed_class_count": len(unique_classes),
            "class_ids": unique_classes.tolist(),
            "class_support": {
                str(class_id): int(count)
                for class_id, count in sorted(Counter(labels.tolist()).items())
            },
        },
        "coords": {"shape": list(coords.shape), "dtype": str(coords.dtype)},
        "sizes": {"shape": list(sizes.shape), "dtype": str(sizes.dtype)},
        "schema_status": "PASS_HASH_PINNED_GTSRB_43_CLASS_CROP",
    }
    return report, features, labels


def inspect_model(model: Any, model_path: Path, repo_root: Path) -> dict[str, Any]:
    input_shape = [value if value is not None else None for value in model.input_shape]
    output_shape = [value if value is not None else None for value in model.output_shape]
    if input_shape != [None, 32, 32, 3] or output_shape != [None, 43]:
        raise ValueError(f"unexpected E0 model contract: {input_shape} -> {output_shape}")
    layers = [
        {
            "name": layer.name,
            "class_name": layer.__class__.__name__,
            "parameters": int(layer.count_params()),
        }
        for layer in model.layers
    ]
    if int(model.count_params()) != 2188107:
        raise ValueError("unexpected frozen E0 parameter count")
    if len(GTSRB_LABELS) != 43 or len(set(GTSRB_LABELS)) != 43 or any(
        not label.strip() for label in GTSRB_LABELS
    ):
        raise ValueError("GTSRB label contract must contain 43 unique non-empty labels")
    return {
        "path": model_path.resolve().relative_to(repo_root.resolve()).as_posix(),
        "sha256": sha256_file(model_path),
        "retained_filename": model_path.name,
        "architecture_classification": (
            "SMALL_VGG_INSPIRED_SEQUENTIAL_CNN_NOT_CANONICAL_KERAS_VGG16"
        ),
        "keras_model_class": model.__class__.__name__,
        "keras_model_name": model.name,
        "input_shape": input_shape,
        "output_shape": output_shape,
        "parameter_count": int(model.count_params()),
        "layer_count": len(layers),
        "layers": layers,
        "preprocessing_contract": "RGB 32x32 float32 divided by 255",
        "output_contract": "43-way GTSRB Softmax",
        "label_count": len(GTSRB_LABELS),
        "labels_sha256": canonical_json_sha256(list(GTSRB_LABELS)),
        "frozen_control": True,
    }


def percentile(values: list[float], value: float) -> float:
    return float(np.percentile(np.asarray(values, dtype=np.float64), value))


def summarize_latencies(values: list[float]) -> dict[str, Any]:
    if len(values) != MEASURED_ITERATIONS or any(
        not math.isfinite(value) or value <= 0 for value in values
    ):
        raise ValueError("invalid latency observations")
    repeat_means = [
        statistics.fmean(values[start : start + ITERATIONS_PER_REPEAT])
        for start in range(0, MEASURED_ITERATIONS, ITERATIONS_PER_REPEAT)
    ]
    repeat_mean = statistics.fmean(repeat_means)
    return {
        "p50": percentile(values, 50),
        "p95": percentile(values, 95),
        "mean": statistics.fmean(values),
        "std_population": statistics.pstdev(values),
        "min": min(values),
        "max": max(values),
        "repeat_means": repeat_means,
        "repeat_mean_cv": (
            statistics.pstdev(repeat_means) / repeat_mean if repeat_mean > 0 else None
        ),
    }


def build_benchmark_attestation(evidence: dict[str, Any]) -> dict[str, Any]:
    latency = evidence["latency_benchmark"]
    observations = latency["latency_ms"]["raw_observations"]
    contract_fields = (
        "split",
        "batch_size",
        "warmup_iterations",
        "measured_repeats",
        "iterations_per_repeat",
        "measured_iterations",
        "timing_method",
        "timed_operations",
        "excluded_operations",
        "interpretation_boundary",
    )
    runtime_payload = runtime_attestation_payload(evidence["runtime"])
    return {
        "schema_version": 1,
        "package": "M0-WP6",
        "status": ATTESTATION_STATUS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "model_sha256": EXPECTED_PINNED_HASHES["model"],
        "test_split_sha256": EXPECTED_SPLITS["test"]["sha256"],
        "runtime_attestation": runtime_payload,
        "runtime_attestation_sha256": canonical_json_sha256(runtime_payload),
        "benchmark_contract": {field: latency[field] for field in contract_fields},
        "sample_selection": latency["sample_selection"],
        "latency_observation_count": len(observations),
        "latency_observations_sha256": canonical_json_sha256(observations),
        "latency_statistics": {
            key: value
            for key, value in latency["latency_ms"].items()
            if key != "raw_observations"
        },
        "prediction_trace_sha256": latency["prediction_trace_sha256"],
    }


def validate_benchmark_attestation(
    attestation: dict[str, Any], evidence: dict[str, Any]
) -> None:
    expected = build_benchmark_attestation(evidence)
    if attestation != expected:
        raise ValueError(
            "WP6 benchmark attestation does not match the clean-build runtime/trace evidence"
        )


def run_latency_benchmark(
    model: Any, raw_images: np.ndarray, labels: np.ndarray
) -> dict[str, Any]:
    if len(raw_images) < WARMUP_ITERATIONS + MEASURED_ITERATIONS:
        raise ValueError("benchmark split is too small for the fixed sample contract")
    rng = np.random.default_rng(BENCHMARK_SEED)
    permutation = rng.permutation(len(raw_images))
    warmup_indices = permutation[:WARMUP_ITERATIONS]
    measured_indices = permutation[
        WARMUP_ITERATIONS : WARMUP_ITERATIONS + MEASURED_ITERATIONS
    ]
    pil_images = {
        int(index): Image.fromarray(raw_images[int(index)])
        for index in np.concatenate((warmup_indices, measured_indices))
    }
    for index in warmup_indices:
        output = np.asarray(
            model.predict(preprocess_image(pil_images[int(index)]), batch_size=1, verbose=0)
        )
        if output.shape != (1, 43) or not np.isfinite(output).all():
            raise ValueError("invalid output during benchmark warm-up")
    repeat_latencies: list[list[float]] = []
    predictions: list[int] = []
    for repeat in range(MEASURED_REPEATS):
        values: list[float] = []
        start = repeat * ITERATIONS_PER_REPEAT
        stop = start + ITERATIONS_PER_REPEAT
        for index in measured_indices[start:stop]:
            before = time.perf_counter_ns()
            batch = preprocess_image(pil_images[int(index)])
            output = np.asarray(model.predict(batch, batch_size=1, verbose=0))
            after = time.perf_counter_ns()
            if output.shape != (1, 43) or not np.isfinite(output).all():
                raise ValueError("invalid output during measured benchmark")
            values.append((after - before) / 1_000_000.0)
            predictions.append(int(output.argmax(axis=1)[0]))
        repeat_latencies.append(values)
    latencies = [value for repeat in repeat_latencies for value in repeat]
    latency_summary = summarize_latencies(latencies)
    trace = {
        "indices": measured_indices.tolist(),
        "true_labels": labels[measured_indices].astype(int).tolist(),
        "predicted_labels": predictions,
    }
    return {
        "status": LATENCY_STATUS,
        "split": BENCHMARK_SPLIT_ID,
        "batch_size": 1,
        "sample_selection": {
            "method": "numpy.default_rng(seed).permutation; warm-up first, measured next",
            "seed": BENCHMARK_SEED,
            "warmup_indices_sha256": canonical_json_sha256(warmup_indices.tolist()),
            "measured_indices_sha256": canonical_json_sha256(measured_indices.tolist()),
            "measured_unique_samples": len(set(measured_indices.tolist())),
            "measured_observed_classes": len(set(labels[measured_indices].tolist())),
        },
        "warmup_iterations": WARMUP_ITERATIONS,
        "measured_repeats": MEASURED_REPEATS,
        "iterations_per_repeat": ITERATIONS_PER_REPEAT,
        "measured_iterations": MEASURED_ITERATIONS,
        "timing_method": TIMING_METHOD,
        "timed_operations": TIMED_OPERATIONS,
        "excluded_operations": EXCLUDED_OPERATIONS,
        "latency_ms": {
            **latency_summary,
            "raw_observations": latencies,
        },
        "prediction_trace_sha256": canonical_json_sha256(trace),
        "interpretation_boundary": LATENCY_INTERPRETATION_BOUNDARY,
    }


def validate_upstream_controls(repo_root: Path) -> dict[str, Any]:
    e0 = json.loads(
        (repo_root / "results/experiments/E0_GTSRB_baseline/manifest.json").read_text(
            encoding="utf-8"
        )
    )
    if e0.get("status") != "frozen_control_reference":
        raise ValueError("E0 manifest is not a frozen control")
    if e0.get("model", {}).get("sha256") != EXPECTED_PINNED_HASHES["model"]:
        raise ValueError("E0 manifest model hash mismatch")
    if e0.get("dataset", {}).get("sha256") != EXPECTED_SPLITS["test"]["sha256"]:
        raise ValueError("E0 manifest test split hash mismatch")
    if e0.get("dataset", {}).get("samples") != EXPECTED_SPLITS["test"]["samples"]:
        raise ValueError("E0 manifest test sample count mismatch")
    expected_evaluation = {
        "summary.json": EXPECTED_PINNED_HASHES["evaluation_summary"],
        "per_class_metrics.csv": EXPECTED_PINNED_HASHES["evaluation_per_class"],
        "confusion_matrix.csv": EXPECTED_PINNED_HASHES["evaluation_confusion"],
        "high_confidence_mistakes.csv": EXPECTED_PINNED_HASHES["evaluation_mistakes"],
    }
    if e0.get("evaluation", {}).get("artifacts_sha256") != expected_evaluation:
        raise ValueError("E0 evaluation artifact hashes do not reconcile")
    decision = json.loads(
        (repo_root / "docs/review/decision_status.json").read_text(encoding="utf-8")
    )
    required_pending = ["D-01", "D-02", "D-03", "D-04", "D-05", "G0.4-bbox-0248"]
    if decision.get("gate0") != "BLOCKED" or decision.get("training_authorized") is not False:
        raise ValueError("Gate 0/training boundary is not fail-closed")
    if any(
        decision.get("decisions", {}).get(item, {}).get("status") != "PENDING"
        for item in required_pending
    ):
        raise ValueError("D-01..D-05/G0.4 must remain PENDING")
    acceptance = (
        repo_root / "docs/review/experiment_acceptance_template.md"
    ).read_text(encoding="utf-8")
    if "UNAPPROVED / INACTIVE WHILE GATE 0 IS BLOCKED" not in acceptance:
        raise ValueError("experiment acceptance template is not unapproved/inactive")
    return {
        "e0_manifest_reconciled": True,
        "drive_provenance_hashes_reconciled": True,
        "evaluation_artifact_hashes_reconciled": True,
        "decision_status": {item: "PENDING" for item in required_pending},
        "gate0": "BLOCKED",
        "training_authorized": False,
        "experiment_acceptance_template": "UNAPPROVED_INACTIVE",
    }


def calibration_readiness() -> dict[str, Any]:
    return {
        "status": READINESS_STATUS,
        "available": READINESS_AVAILABLE,
        "valid_split_suitability": READINESS_VALID_SPLIT,
        "test_split_policy": READINESS_TEST_POLICY,
        "missing_or_blocking": READINESS_BLOCKERS,
        "actions_not_performed": READINESS_ACTIONS_NOT_PERFORMED,
    }


def deterministic_non_timing_payload(evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": evidence["schema_version"],
        "status": evidence["status"],
        "evidence_boundary": evidence["evidence_boundary"],
        "hardware": evidence["hardware"],
        "runtime": evidence["runtime"],
        "sources": evidence["sources"],
        "model": evidence["model"],
        "datasets": evidence["datasets"],
        "upstream_controls": evidence["upstream_controls"],
        "calibration_ood_readiness": evidence["calibration_ood_readiness"],
        "preservation": evidence["preservation"],
        "benchmark_contract": {
            key: value
            for key, value in evidence["latency_benchmark"].items()
            if key not in {"latency_ms", "prediction_trace_sha256"}
        },
    }


def render_report(evidence: dict[str, Any]) -> str:
    hardware = evidence["hardware"]
    runtime = evidence["runtime"]
    latency = evidence["latency_benchmark"]
    stats = latency["latency_ms"]
    datasets = evidence["datasets"]
    readiness = evidence["calibration_ood_readiness"]
    graphics = hardware["graphics"]
    graphics_text = ", ".join(
        f"{item['chipset_model']} ({item['cores']} cores, {item['metal_family']})"
        for item in graphics
    ) or "UNKNOWN"
    repeat_means = ", ".join(f"{value:.3f}" for value in stats["repeat_means"])
    blockers = "\n".join(f"- {item}" for item in readiness["missing_or_blocking"])
    return f"""# M0-WP6 — Frozen E0 compute/runtime and evaluation-readiness preflight

Status: `{evidence['status']}`  
Boundary: `{evidence['evidence_boundary']}`

WP6 proves only that the frozen local E0 control can be inventoried and benchmarked reproducibly on this host. It does not approve D-05, calibrate UNKNOWN/OOD, validate Vietnam, open Gate 0 or authorize training.

## Observed local host and runtime

- OS: {hardware['os']['name']} {hardware['os']['version']} ({hardware['os']['build']}), {hardware['os']['machine']}.
- CPU: {hardware['cpu']['brand']}; physical/logical cores: {hardware['cpu']['physical_cores']}/{hardware['cpu']['logical_cores']}.
- Reliably observed memory: {hardware['memory_bytes']} bytes.
- Hardware graphics/Metal: {graphics_text}.
- Python: {runtime['python_version']} at `{runtime['python_executable']}`; {runtime['uv_version']}.
- TensorFlow/Keras: {runtime['tensorflow_version']} / {runtime['keras_version']}.
- TensorFlow-visible devices: `{json.dumps(runtime['logical_devices'], sort_keys=True)}`.
- Execution backend used: `{runtime['execution_backend']}`. Hardware Metal exists, but TensorFlow exposes no GPU and `tensorflow-metal` is not installed.

No serial number, hardware UUID, provisioning identifier, username or display serial is recorded.

## Frozen E0 and local GTSRB artifacts

- Model: `{evidence['model']['path']}`, SHA-256 `{evidence['model']['sha256']}`.
- Architecture: {evidence['model']['architecture_classification']}; {evidence['model']['parameter_count']} parameters; input {evidence['model']['input_shape']}; output {evidence['model']['output_shape']}.
- Train: {datasets['train']['samples']} samples, 43 classes, SHA-256 `{datasets['train']['sha256']}`.
- Valid: {datasets['valid']['samples']} samples, 43 classes, SHA-256 `{datasets['valid']['sha256']}`.
- Test: {datasets['test']['samples']} samples, 43 classes, SHA-256 `{datasets['test']['sha256']}`.
- All three pickles have exact keys `features/labels/coords/sizes`, uint8 32x32x3 features and class IDs 0..42.
- Model/test/evaluation hashes reconcile with the frozen E0 manifest and retained Drive provenance.

`valid.p` is same-source GTSRB data used during model development. It may support a later diagnostic/calibration design, but it is not an independent Vietnamese holdout and cannot validate Vietnamese-domain performance.

## Reproducible batch-1 latency

Candidate measurement command (never updates the official package or trust anchor):

```bash
uv run python scripts/audit_e0_compute_readiness.py build --repo-root .
```

Official package verification command:

```bash
uv run python scripts/audit_e0_compute_readiness.py verify --repo-root .
```

- Split: `{latency['split']}`; deterministic seed {latency['sample_selection']['seed']}.
- Backend: `{runtime['execution_backend']}`; batch size 1.
- Warm-up: {latency['warmup_iterations']} iterations.
- Measured: {latency['measured_iterations']} iterations in {latency['measured_repeats']} repeats of {latency['iterations_per_repeat']}.
- Timing: `{latency['timing_method']}`.
- Included: preprocessing (`preprocess_image`) and `keras model.predict`; excluded: pickle/model loading, PIL construction, sample selection and serialization.
- p50: {stats['p50']:.3f} ms; p95: {stats['p95']:.3f} ms; mean: {stats['mean']:.3f} ms; population std: {stats['std_population']:.3f} ms.
- Repeat means: [{repeat_means}] ms; repeat-mean CV: {stats['repeat_mean_cv']:.6f}.
- Clean-build benchmark attestation: `{ATTESTATION_RELATIVE_PATH}`; verifier compares its runtime,
  exact observation digest, statistics and prediction trace with the evidence before accepting.
- Independent source anchor: `{TRUSTED_ATTESTATION_SHA256}`. A new measurement remains an
  unpinned candidate until a maintainer reviews it, changes this source constant and explicitly
  runs `promote-pinned`; no build command can rewrite or auto-promote the anchor.

This is an observed local diagnostic, not a D-05 pass/fail result. D-05 is still unapproved/inactive.

## Calibration/OOD readiness

Readiness classification: `{readiness['status']}`.

{blockers}

No temperature, UNKNOWN threshold or OOD metric was fitted or selected. The existing `0.50` threshold remains a demo value.

## Governance state

- D-01…D-05 and G0.4: `PENDING`.
- Gate 0: `BLOCKED`.
- `training_authorized=false`.
- Experiment acceptance template: `UNAPPROVED / INACTIVE`.
- No training, split mutation, model overwrite or model promotion occurred.
"""


def build_evidence(repo_root: Path) -> dict[str, Any]:
    before_hashes = {
        item_id: sha256_file(path)
        for item_id, path, _ in source_contract(repo_root)
        if path.is_file()
    }
    sources = verify_pinned_sources(repo_root)
    hardware = collect_hardware_inventory()
    runtime, keras = collect_runtime_inventory(repo_root)
    datasets: dict[str, Any] = {}
    raw_test: np.ndarray | None = None
    test_labels: np.ndarray | None = None
    for split_name in ("train", "valid", "test"):
        report, features, labels = load_trusted_split(
            repo_root / f"data/processed/{split_name}.p", split_name, repo_root
        )
        datasets[split_name] = report
        if split_name == "test":
            raw_test = features
            test_labels = labels
        else:
            del features, labels
    model_path = repo_root / "models/VGG16_model.h5"
    model = keras.models.load_model(model_path, compile=False)
    model_report = inspect_model(model, model_path, repo_root)
    if raw_test is None or test_labels is None:
        raise RuntimeError("test split was not loaded")
    latency = run_latency_benchmark(model, raw_test, test_labels)
    evidence: dict[str, Any] = {
        "schema_version": 1,
        "package": "M0-WP6",
        "status": STATUS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "observed_at_utc": datetime.now(UTC).isoformat(),
        "hardware": hardware,
        "runtime": runtime,
        "sources": sources,
        "model": model_report,
        "datasets": datasets,
        "upstream_controls": validate_upstream_controls(repo_root),
        "latency_benchmark": latency,
        "calibration_ood_readiness": calibration_readiness(),
        "preservation": {
            "all_source_hashes_unchanged_during_build": False,
            "source_count": len(sources),
        },
    }
    after_hashes = {
        item_id: sha256_file(path)
        for item_id, path, _ in source_contract(repo_root)
    }
    if before_hashes != after_hashes:
        raise RuntimeError("a WP6 source/control artifact changed during build")
    evidence["preservation"]["all_source_hashes_unchanged_during_build"] = True
    evidence["deterministic_non_timing_sha256"] = canonical_json_sha256(
        deterministic_non_timing_payload(evidence)
    )
    return evidence


def build_manifest(repo_root: Path) -> dict[str, Any]:
    sources = [
        relative_record(path, repo_root, item_id)
        for item_id, path, _ in source_contract(repo_root)
    ]
    artifacts = [
        relative_record(path, repo_root, item_id)
        for item_id, path in artifact_contract(repo_root)
    ]
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "package": "M0-WP6",
        "status": STATUS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "gate0": "BLOCKED",
        "training_authorized": False,
        "manifest_path": MANIFEST_RELATIVE_PATH,
        "manifest_self_in_artifact_count": False,
        "artifact_count_semantics": MANIFEST_COUNT_SEMANTICS,
        "trusted_attestation_sha256": TRUSTED_ATTESTATION_SHA256,
        "source_count": len(sources),
        "artifact_count": len(artifacts),
        "total_artifact_bytes": sum(record["size"] for record in artifacts),
        "sources": sources,
        "artifacts": artifacts,
    }


def resolve_safe_path(repo_root: Path, value: str) -> Path:
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"unsafe manifest path: {value}")
    target = (repo_root / relative).resolve()
    target.relative_to(repo_root.resolve())
    return target


def contract_pairs(
    contract: list[tuple[str, Path]] | list[tuple[str, Path, str | None]],
    repo_root: Path,
) -> list[tuple[str, str]]:
    return [
        (item[0], item[1].resolve().relative_to(repo_root.resolve()).as_posix())
        for item in contract
    ]


def verify_record_collection(
    payload: dict[str, Any],
    collection: str,
    expected: list[tuple[str, str]],
    repo_root: Path,
    errors: list[str],
) -> list[dict[str, Any]]:
    value = payload.get(collection)
    if not isinstance(value, list):
        errors.append(f"{collection} must be a list")
        return []
    records: list[dict[str, Any]] = []
    pairs: list[tuple[str, str]] = []
    for index, record in enumerate(value):
        if not isinstance(record, dict):
            errors.append(f"{collection}[{index}] must be an object")
            continue
        if set(record) != {"id", "path", "sha256", "size"}:
            errors.append(f"{collection}[{index}] has unexpected fields")
        item_id, path_value = record.get("id"), record.get("path")
        digest, size = record.get("sha256"), record.get("size")
        if not isinstance(item_id, str) or not item_id:
            errors.append(f"{collection}[{index}].id must be a non-empty string")
        if not isinstance(path_value, str) or not path_value:
            errors.append(f"{collection}[{index}].path must be a non-empty string")
        else:
            try:
                resolve_safe_path(repo_root, path_value)
            except (ValueError, OSError) as exc:
                errors.append(str(exc))
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            errors.append(f"{collection}[{index}].sha256 must be lowercase hex64")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            errors.append(f"{collection}[{index}].size must be a non-negative integer")
        if isinstance(item_id, str) and isinstance(path_value, str):
            pairs.append((item_id, path_value))
        records.append(record)
    duplicate_ids = sorted(
        item for item, count in Counter(item for item, _ in pairs).items() if count > 1
    )
    duplicate_paths = sorted(
        item for item, count in Counter(item for _, item in pairs).items() if count > 1
    )
    if duplicate_ids:
        errors.append(f"duplicate {collection} IDs: {duplicate_ids}")
    if duplicate_paths:
        errors.append(f"duplicate {collection} paths: {duplicate_paths}")
    if pairs != expected:
        expected_ids = {item_id for item_id, _ in expected}
        actual_ids = {item_id for item_id, _ in pairs}
        missing = sorted(expected_ids - actual_ids)
        extra = sorted(actual_ids - expected_ids)
        if missing:
            errors.append(f"missing canonical {collection} IDs: {missing}")
        if extra:
            errors.append(f"unexpected {collection} IDs: {extra}")
        errors.append(f"{collection} roster/order differs from canonical contract")
    return records


def validate_evidence(evidence: dict[str, Any], repo_root: Path) -> None:
    expected_top = {
        "schema_version",
        "package",
        "status",
        "evidence_boundary",
        "observed_at_utc",
        "hardware",
        "runtime",
        "sources",
        "model",
        "datasets",
        "upstream_controls",
        "latency_benchmark",
        "calibration_ood_readiness",
        "preservation",
        "deterministic_non_timing_sha256",
    }
    if not isinstance(evidence, dict) or set(evidence) != expected_top:
        raise ValueError("WP6 evidence top-level fields differ from schema v1")
    if (
        evidence.get("schema_version") != 1
        or evidence.get("package") != "M0-WP6"
        or evidence.get("status") != STATUS
    ):
        raise ValueError("invalid WP6 evidence schema/package/status")
    if evidence.get("evidence_boundary") != EVIDENCE_BOUNDARY:
        raise ValueError("invalid WP6 evidence boundary")
    try:
        observed_at = datetime.fromisoformat(evidence["observed_at_utc"])
    except (TypeError, ValueError) as exc:
        raise ValueError("WP6 observed_at_utc must be ISO 8601") from exc
    if observed_at.tzinfo is None:
        raise ValueError("WP6 observed_at_utc must include a timezone")
    if evidence.get("preservation") != {
        "all_source_hashes_unchanged_during_build": True,
        "source_count": EXPECTED_SOURCE_COUNT,
    }:
        raise ValueError("invalid WP6 preservation statement")

    expected_sources = source_contract(repo_root)
    sources = evidence.get("sources")
    if not isinstance(sources, list) or len(sources) != EXPECTED_SOURCE_COUNT:
        raise ValueError("WP6 evidence source roster count mismatch")
    for record, (item_id, path, pinned_hash) in zip(sources, expected_sources, strict=True):
        expected_path = path.resolve().relative_to(repo_root.resolve()).as_posix()
        if not isinstance(record, dict) or set(record) != {
            "id",
            "path",
            "sha256",
            "size",
            "pinned_expected_sha256",
            "hash_status",
        }:
            raise ValueError(f"WP6 evidence source record schema mismatch for {item_id}")
        if record["id"] != item_id or record["path"] != expected_path:
            raise ValueError(f"WP6 evidence source roster mismatch for {item_id}")
        if record["pinned_expected_sha256"] != pinned_hash:
            raise ValueError(f"WP6 evidence pinned hash declaration mismatch for {item_id}")
        if pinned_hash is not None:
            if record["sha256"] != pinned_hash or record["hash_status"] != "MATCH":
                raise ValueError(f"WP6 evidence pinned hash mismatch for {item_id}")
        elif record["hash_status"] != "OBSERVED_CONTROL":
            raise ValueError(f"WP6 evidence control hash status mismatch for {item_id}")
        if (
            not isinstance(record["sha256"], str)
            or len(record["sha256"]) != 64
            or any(character not in "0123456789abcdef" for character in record["sha256"])
            or isinstance(record["size"], bool)
            or not isinstance(record["size"], int)
            or record["size"] <= 0
        ):
            raise ValueError(f"WP6 evidence invalid source hash/size for {item_id}")

    model = evidence["model"]
    expected_model = {
        "path": "models/VGG16_model.h5",
        "sha256": EXPECTED_PINNED_HASHES["model"],
        "retained_filename": "VGG16_model.h5",
        "architecture_classification": (
            "SMALL_VGG_INSPIRED_SEQUENTIAL_CNN_NOT_CANONICAL_KERAS_VGG16"
        ),
        "keras_model_class": "Sequential",
        "keras_model_name": "sequential",
        "input_shape": [None, 32, 32, 3],
        "output_shape": [None, 43],
        "parameter_count": 2188107,
        "layer_count": 20,
        "layers": EXPECTED_MODEL_LAYERS,
        "preprocessing_contract": "RGB 32x32 float32 divided by 255",
        "output_contract": "43-way GTSRB Softmax",
        "label_count": 43,
        "labels_sha256": canonical_json_sha256(list(GTSRB_LABELS)),
        "frozen_control": True,
    }
    if model != expected_model:
        raise ValueError("WP6 evidence model contract mismatch")

    datasets = evidence["datasets"]
    if not isinstance(datasets, dict) or set(datasets) != set(EXPECTED_SPLITS):
        raise ValueError("WP6 evidence dataset roster mismatch")
    for split_name, expected in EXPECTED_SPLITS.items():
        split = datasets[split_name]
        expected_samples = expected["samples"]
        if (
            split["path"] != f"data/processed/{split_name}.p"
            or split["sha256"] != expected["sha256"]
            or split["samples"] != expected_samples
            or split["keys"] != ["coords", "features", "labels", "sizes"]
            or split["schema_status"] != "PASS_HASH_PINNED_GTSRB_43_CLASS_CROP"
        ):
            raise ValueError(f"WP6 evidence {split_name} identity/schema mismatch")
        if split["features"] != {
            "shape": [expected_samples, 32, 32, 3],
            "dtype": "uint8",
            "min": 0,
            "max": 255,
        }:
            raise ValueError(f"WP6 evidence {split_name} feature schema mismatch")
        labels = split["labels"]
        if (
            labels["shape"] != [expected_samples]
            or labels["dtype"] != "uint8"
            or labels["min"] != 0
            or labels["max"] != 42
            or labels["observed_class_count"] != 43
            or labels["class_ids"] != list(range(43))
            or set(labels["class_support"]) != {str(value) for value in range(43)}
            or sum(labels["class_support"].values()) != expected_samples
            or split["coords"] != {"shape": [expected_samples, 4], "dtype": "uint8"}
            or split["sizes"] != {"shape": [expected_samples, 2], "dtype": "uint8"}
        ):
            raise ValueError(f"WP6 evidence {split_name} label/metadata schema mismatch")

    hardware = evidence["hardware"]
    forbidden_hardware_fields = {
        "serial_number",
        "serialnumber",
        "hardware_uuid",
        "hardwareuuid",
        "username",
        "user_name",
    }
    if nested_mapping_keys(hardware) & forbidden_hardware_fields:
        raise ValueError("WP6 hardware evidence violates the privacy boundary")
    if hardware.get("observation_status") != "OBSERVED_LOCAL_HOST":
        raise ValueError("WP6 hardware observation status mismatch")
    runtime = evidence["runtime"]
    expected_runtime_fields = {
        "observation_status",
        "python_version",
        "python_implementation",
        "python_executable",
        "uv_version",
        "tensorflow_version",
        "keras_version",
        "tensorflow_macos_version",
        "tensorflow_metal_version",
        "physical_devices",
        "logical_devices",
        "tensorflow_built_with_cuda",
        "execution_backend",
        "gpu_visible_to_tensorflow",
    }
    if set(runtime) != expected_runtime_fields:
        raise ValueError("WP6 runtime inventory fields mismatch")
    logical = runtime.get("logical_devices")
    if not isinstance(logical, list) or not logical:
        raise ValueError("WP6 runtime must report visible logical devices")
    gpu_visible = any(device.get("type") == "GPU" for device in logical)
    expected_backend = "TENSORFLOW_GPU" if gpu_visible else "TENSORFLOW_CPU_ONLY"
    if (
        runtime.get("execution_backend") != expected_backend
        or runtime.get("gpu_visible_to_tensorflow") is not gpu_visible
        or Path(runtime.get("python_executable", "/")).is_absolute()
    ):
        raise ValueError("WP6 runtime/backend/privacy contract is invalid")

    latency = evidence["latency_benchmark"]
    if (
        latency.get("status") != LATENCY_STATUS
        or latency.get("split") != BENCHMARK_SPLIT_ID
        or latency.get("batch_size") != 1
        or latency.get("warmup_iterations") != WARMUP_ITERATIONS
        or latency.get("measured_repeats") != MEASURED_REPEATS
        or latency.get("iterations_per_repeat") != ITERATIONS_PER_REPEAT
        or latency.get("measured_iterations") != MEASURED_ITERATIONS
        or latency.get("timing_method") != TIMING_METHOD
        or latency.get("timed_operations") != TIMED_OPERATIONS
        or latency.get("excluded_operations") != EXCLUDED_OPERATIONS
        or latency.get("interpretation_boundary")
        != LATENCY_INTERPRETATION_BOUNDARY
        or latency.get("prediction_trace_sha256")
        != EXPECTED_PREDICTION_TRACE_SHA256
    ):
        raise ValueError("WP6 timing contract mismatch")
    selection = latency.get("sample_selection", {})
    permutation = np.random.default_rng(BENCHMARK_SEED).permutation(
        EXPECTED_SPLITS["test"]["samples"]
    )
    expected_warmup = permutation[:WARMUP_ITERATIONS].tolist()
    expected_measured = permutation[
        WARMUP_ITERATIONS : WARMUP_ITERATIONS + MEASURED_ITERATIONS
    ].tolist()
    if (
        selection.get("seed") != BENCHMARK_SEED
        or selection.get("method")
        != "numpy.default_rng(seed).permutation; warm-up first, measured next"
        or selection.get("warmup_indices_sha256")
        != canonical_json_sha256(expected_warmup)
        or selection.get("measured_indices_sha256")
        != canonical_json_sha256(expected_measured)
        or selection.get("measured_unique_samples") != MEASURED_ITERATIONS
        or selection.get("measured_observed_classes") != EXPECTED_MEASURED_CLASS_COUNT
    ):
        raise ValueError("WP6 deterministic sample-selection contract mismatch")
    latency_ms = latency.get("latency_ms", {})
    observations = latency_ms.get("raw_observations")
    if not isinstance(observations, list):
        raise ValueError("WP6 timing observations must be a list")
    recomputed = summarize_latencies(observations)
    if set(latency_ms) != {*recomputed, "raw_observations"}:
        raise ValueError("WP6 timing-statistic fields mismatch")
    for field, expected_value in recomputed.items():
        actual_value = latency_ms[field]
        if isinstance(expected_value, list):
            if len(actual_value) != len(expected_value) or any(
                not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12)
                for actual, expected in zip(actual_value, expected_value, strict=True)
            ):
                raise ValueError(f"WP6 timing statistic mismatch: {field}")
        elif expected_value is None:
            if actual_value is not None:
                raise ValueError(f"WP6 timing statistic mismatch: {field}")
        elif not math.isclose(
            actual_value, expected_value, rel_tol=1e-12, abs_tol=1e-12
        ):
            raise ValueError(f"WP6 timing statistic mismatch: {field}")

    controls = evidence["upstream_controls"]
    required_decisions = {"D-01", "D-02", "D-03", "D-04", "D-05", "G0.4-bbox-0248"}
    if (
        controls.get("gate0") != "BLOCKED"
        or controls.get("training_authorized") is not False
        or controls.get("experiment_acceptance_template") != "UNAPPROVED_INACTIVE"
        or set(controls.get("decision_status", {})) != required_decisions
        or set(controls.get("decision_status", {}).values()) != {"PENDING"}
    ):
        raise ValueError("WP6 governance boundary is invalid")
    readiness = evidence["calibration_ood_readiness"]
    if readiness != calibration_readiness():
        raise ValueError("WP6 readiness/governance semantics mismatch")
    expected_fingerprint = canonical_json_sha256(deterministic_non_timing_payload(evidence))
    if evidence.get("deterministic_non_timing_sha256") != expected_fingerprint:
        raise ValueError("WP6 deterministic non-timing fingerprint mismatch")


def verify_manifest(manifest_path: Path, repo_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        return {"valid": False, "errors": [f"manifest unreadable: {exc}"]}
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["manifest root must be an object"]}
    expected_top = {
        "schema_version",
        "package",
        "status",
        "evidence_boundary",
        "gate0",
        "training_authorized",
        "manifest_path",
        "manifest_self_in_artifact_count",
        "artifact_count_semantics",
        "trusted_attestation_sha256",
        "source_count",
        "artifact_count",
        "total_artifact_bytes",
        "sources",
        "artifacts",
    }
    if set(payload) != expected_top:
        errors.append("manifest top-level fields differ from WP6 schema v2")
    constants = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "package": "M0-WP6",
        "status": STATUS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "gate0": "BLOCKED",
        "training_authorized": False,
        "manifest_path": MANIFEST_RELATIVE_PATH,
        "manifest_self_in_artifact_count": False,
        "artifact_count_semantics": MANIFEST_COUNT_SEMANTICS,
        "trusted_attestation_sha256": TRUSTED_ATTESTATION_SHA256,
    }
    for field, expected in constants.items():
        if payload.get(field) != expected:
            errors.append(f"invalid manifest {field}")
    expected_sources = contract_pairs(source_contract(repo_root), repo_root)
    expected_artifacts = contract_pairs(artifact_contract(repo_root), repo_root)
    source_records = verify_record_collection(
        payload, "sources", expected_sources, repo_root, errors
    )
    artifact_records = verify_record_collection(
        payload, "artifacts", expected_artifacts, repo_root, errors
    )
    source_by_id = {
        record.get("id"): record
        for record in source_records
        if isinstance(record.get("id"), str)
    }
    for item_id, _path, pinned_hash in source_contract(repo_root):
        if pinned_hash is not None and source_by_id.get(item_id, {}).get("sha256") != pinned_hash:
            errors.append(f"pinned source digest mismatch: {item_id}")
    if payload.get("source_count") != len(source_records) or len(source_records) != len(expected_sources):
        errors.append("source_count mismatch")
    if payload.get("artifact_count") != len(artifact_records) or len(artifact_records) != len(expected_artifacts):
        errors.append("artifact_count mismatch")
    recorded_bytes = sum(
        record.get("size", -1)
        for record in artifact_records
        if isinstance(record.get("size"), int) and not isinstance(record.get("size"), bool)
    )
    if payload.get("total_artifact_bytes") != recorded_bytes:
        errors.append("total_artifact_bytes mismatch")
    for collection, records in (("sources", source_records), ("artifacts", artifact_records)):
        for record in records:
            path_value = record.get("path")
            if not isinstance(path_value, str):
                continue
            try:
                path = resolve_safe_path(repo_root, path_value)
            except (ValueError, OSError):
                continue
            if not path.is_file():
                errors.append(f"missing {collection} file: {path_value}")
            elif path.stat().st_size != record.get("size") or sha256_file(path) != record.get("sha256"):
                errors.append(f"tampered {collection} file: {path_value}")
    if errors:
        return {
            "valid": False,
            "errors": errors,
            "source_count": len(source_records),
            "artifact_count": len(artifact_records),
        }
    attestation_path = repo_root / ATTESTATION_RELATIVE_PATH
    if (
        len(TRUSTED_ATTESTATION_SHA256) != 64
        or any(
            character not in "0123456789abcdef"
            for character in TRUSTED_ATTESTATION_SHA256
        )
    ):
        errors.append("trusted attestation source anchor is not pinned")
    elif sha256_file(attestation_path) != TRUSTED_ATTESTATION_SHA256:
        errors.append("trusted attestation source anchor mismatch")
    if errors:
        return {
            "valid": False,
            "errors": errors,
            "source_count": len(source_records),
            "artifact_count": len(artifact_records),
        }
    try:
        evidence = json.loads((repo_root / EVIDENCE_RELATIVE_PATH).read_text(encoding="utf-8"))
        validate_evidence(evidence, repo_root)
        attestation = json.loads(
            (repo_root / ATTESTATION_RELATIVE_PATH).read_text(encoding="utf-8")
        )
        validate_benchmark_attestation(attestation, evidence)
        live_runtime, keras = collect_runtime_inventory(repo_root)
        if runtime_attestation_payload(evidence["runtime"]) != runtime_attestation_payload(
            live_runtime
        ):
            errors.append("recorded runtime/device inventory differs from live verification")
        live_model = keras.models.load_model(
            repo_root / "models/VGG16_model.h5", compile=False
        )
        live_model_report = inspect_model(
            live_model, repo_root / "models/VGG16_model.h5", repo_root
        )
        if evidence["model"] != live_model_report:
            errors.append("recorded model semantics differ from the hash-pinned model")
        report = (repo_root / REPORT_RELATIVE_PATH).read_text(encoding="utf-8")
        if report != render_report(evidence):
            errors.append("human report does not match the verified evidence")
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        KeyError,
        OSError,
        TypeError,
        ValueError,
    ) as exc:
        errors.append(f"evidence semantic verification failed: {exc}")
    return {
        "valid": not errors,
        "errors": errors,
        "source_count": len(source_records),
        "artifact_count": len(artifact_records),
        "status": payload.get("status"),
    }


def candidate_paths(repo_root: Path, candidate_dir: Path) -> tuple[Path, Path]:
    root = candidate_dir if candidate_dir.is_absolute() else repo_root / candidate_dir
    root = root.resolve()
    root.relative_to(repo_root.resolve())
    return root / CANDIDATE_EVIDENCE_FILENAME, root / CANDIDATE_ATTESTATION_FILENAME


def build_candidate(repo_root: Path, candidate_dir: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    evidence_path, attestation_path = candidate_paths(repo_root, candidate_dir)
    evidence = build_evidence(repo_root)
    validate_evidence(evidence, repo_root)
    attestation = build_benchmark_attestation(evidence)
    validate_benchmark_attestation(attestation, evidence)
    write_json(evidence_path, evidence)
    write_json(attestation_path, attestation)
    attestation_sha256 = sha256_file(attestation_path)
    return {
        "status": CANDIDATE_STATUS,
        "candidate_evidence": evidence_path.relative_to(repo_root).as_posix(),
        "candidate_attestation": attestation_path.relative_to(repo_root).as_posix(),
        "candidate_attestation_sha256": attestation_sha256,
        "trusted_attestation_sha256": TRUSTED_ATTESTATION_SHA256,
        "anchor_matches": attestation_sha256 == TRUSTED_ATTESTATION_SHA256,
        "official_package_modified": False,
        "promotion_rule": (
            "Code-review the candidate, manually update TRUSTED_ATTESTATION_SHA256 in the "
            "verifier source, then run promote-pinned. Build never updates the trust anchor or "
            "official package."
        ),
        "gate0": "BLOCKED",
        "training_authorized": False,
    }


def refresh_evidence_sources(
    evidence: dict[str, Any], repo_root: Path
) -> dict[str, Any]:
    evidence["sources"] = verify_pinned_sources(repo_root)
    evidence["preservation"] = {
        "all_source_hashes_unchanged_during_build": True,
        "source_count": EXPECTED_SOURCE_COUNT,
    }
    evidence["deterministic_non_timing_sha256"] = canonical_json_sha256(
        deterministic_non_timing_payload(evidence)
    )
    validate_evidence(evidence, repo_root)
    return evidence


def promote_pinned_candidate(repo_root: Path, candidate_dir: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    candidate_evidence_path, candidate_attestation_path = candidate_paths(
        repo_root, candidate_dir
    )
    if sha256_file(candidate_attestation_path) != TRUSTED_ATTESTATION_SHA256:
        raise ValueError(
            "candidate attestation does not match the reviewed source anchor; promotion refused"
        )
    evidence = json.loads(candidate_evidence_path.read_text(encoding="utf-8"))
    attestation = json.loads(candidate_attestation_path.read_text(encoding="utf-8"))
    validate_evidence(evidence, repo_root)
    validate_benchmark_attestation(attestation, evidence)
    live_runtime, keras = collect_runtime_inventory(repo_root)
    if runtime_attestation_payload(evidence["runtime"]) != runtime_attestation_payload(
        live_runtime
    ):
        raise ValueError("candidate runtime/device inventory differs from live promotion host")
    live_model = keras.models.load_model(
        repo_root / "models/VGG16_model.h5", compile=False
    )
    if evidence["model"] != inspect_model(
        live_model, repo_root / "models/VGG16_model.h5", repo_root
    ):
        raise ValueError("candidate model semantics differ from the hash-pinned model")
    evidence = refresh_evidence_sources(evidence, repo_root)
    validate_benchmark_attestation(attestation, evidence)

    evidence_path = repo_root / EVIDENCE_RELATIVE_PATH
    report_path = repo_root / REPORT_RELATIVE_PATH
    attestation_path = repo_root / ATTESTATION_RELATIVE_PATH
    manifest_path = repo_root / MANIFEST_RELATIVE_PATH
    write_json(evidence_path, evidence)
    write_json(attestation_path, attestation)
    if sha256_file(attestation_path) != TRUSTED_ATTESTATION_SHA256:
        raise RuntimeError("official attestation bytes differ from the reviewed source anchor")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(evidence), encoding="utf-8")
    manifest = build_manifest(repo_root)
    write_json(manifest_path, manifest)
    verification = verify_manifest(manifest_path, repo_root)
    if not verification["valid"]:
        raise RuntimeError(f"WP6 package verification failed: {verification['errors']}")
    return {
        "status": STATUS,
        "manifest": MANIFEST_RELATIVE_PATH,
        "manifest_sha256": sha256_file(manifest_path),
        "trusted_attestation_sha256": TRUSTED_ATTESTATION_SHA256,
        "deterministic_non_timing_sha256": evidence["deterministic_non_timing_sha256"],
        "source_count": manifest["source_count"],
        "artifact_count": manifest["artifact_count"],
        "latency_ms": {
            key: evidence["latency_benchmark"]["latency_ms"][key]
            for key in ("p50", "p95", "mean", "std_population")
        },
        "execution_backend": evidence["runtime"]["execution_backend"],
        "gate0": "BLOCKED",
        "training_authorized": False,
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("--repo-root", type=Path, required=True)
    build.add_argument(
        "--candidate-dir", type=Path, default=Path(CANDIDATE_DIR_RELATIVE_PATH)
    )
    promote = commands.add_parser("promote-pinned")
    promote.add_argument("--repo-root", type=Path, required=True)
    promote.add_argument(
        "--candidate-dir", type=Path, default=Path(CANDIDATE_DIR_RELATIVE_PATH)
    )
    verify = commands.add_parser("verify")
    verify.add_argument("--repo-root", type=Path, required=True)
    verify.add_argument(
        "--manifest",
        type=Path,
        default=Path(MANIFEST_RELATIVE_PATH),
    )
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    if args.command == "build":
        result = build_candidate(repo_root, args.candidate_dir)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.command == "promote-pinned":
        result = promote_pinned_candidate(repo_root, args.candidate_dir)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    manifest = args.manifest
    if not manifest.is_absolute():
        manifest = repo_root / manifest
    result = verify_manifest(manifest, repo_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
