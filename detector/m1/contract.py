"""Binding between the detector package and the governed data contract (G0.7, D-05).

The root project owns the data contract. This module loads the root M1 export builder by path
(standard library only), so the detector env never re-implements split or label logic.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Any
from zoneinfo import ZoneInfo

DETECTOR_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = DETECTOR_ROOT.parent
EXPORT_DIR = REPO_ROOT / "data/processed/m1_yolo"
RESULTS_DIR = REPO_ROOT / "results/experiments"
RUN_REGISTRY = REPO_ROOT / "docs/review/generated/d1_run_registry.json"
PRETRAINED_WEIGHTS = REPO_ROOT / "models/pretrained/yolo11s.pt"
PRETRAINED_WEIGHTS_SHA256 = "85a76fe86dd8afe384648546b56a7a78580c7cb7b404fc595f97969322d502d5"
SPLIT_FRAMES = REPO_ROOT / "docs/review/generated/wp36_r1_split_frames.csv"
WP33_BOXES = REPO_ROOT / "docs/review/generated/wp33_derived_boxes.csv"
D05_RECORD = REPO_ROOT / "docs/review/d05_owner_decision_record.md"
D05_RECORD_SHA256 = "c81f37ed0236c019644914445776632dbe0fbcef0f7d5b964fb5c6d635555702"
DETECTOR_LOCK_SHA256 = "5d56642af267bdff63f7d2a627ccf97a8f04cbf848a673a5d65988a471baaec5"

# D-05 (owner-approved 2026-10-18).
SEEDS = (20261018, 20261019, 20261020)
GATES = {
    "map50": 0.60,
    "map50_95": 0.40,
    "agnostic_recall": 0.85,
    "fp_per_image": 0.30,
    "critical_class_recall": 0.70,
    "other_class_recall": 0.50,
    "min_support_for_class_gate": 20,
    "latency_p95_ms": 100.0,
}
CRITICAL_KEYS = ("0", "2", "7", "32", "13", "22", "45", "39", "40", "41")
LATENCY_WARMUP, LATENCY_ITERATIONS = 50, 300
FORBIDDEN_OVERRIDES = {"fliplr": 0.0}  # no semantic horizontal flip (left/right signs)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(payload: Any) -> str:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(data).hexdigest()


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


def _exact_keys(value: Any, expected: set[str], label: str) -> None:
    if not isinstance(value, dict) or set(value) != expected:
        raise RuntimeError(f"{label} schema differs: expected exactly {sorted(expected)}")


def _require_git_tracked_clean(path: Path, label: str) -> None:
    try:
        relative = path.resolve().relative_to(REPO_ROOT)
    except ValueError as error:
        raise RuntimeError(f"{label} must be stored inside the repository") from error
    if not path.is_file():
        raise RuntimeError(f"{label} is missing: {path}")
    try:
        subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", str(relative)],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        for cached in (False, True):
            command = ["git", "diff", "--quiet"]
            if cached:
                command.append("--cached")
            command.extend(["--", str(relative)])
            subprocess.run(command, cwd=REPO_ROOT, check=True)
    except (OSError, subprocess.CalledProcessError) as error:
        raise RuntimeError(f"{label} must be committed and clean") from error


def load_export_module() -> ModuleType:
    path = REPO_ROOT / "scripts/build_m1_yolo_dataset.py"
    spec = importlib.util.spec_from_file_location("m1_export_contract", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def check_contract(split: str = "val") -> dict[str, Any]:
    """Fail closed unless the D-05 record, the export manifest and the exported files agree."""
    if sha256_file(D05_RECORD) != D05_RECORD_SHA256:
        raise RuntimeError("D-05 owner decision record changed; re-approve before training")
    export = load_export_module()
    result = export.verify(REPO_ROOT)
    if not result["valid"]:
        raise RuntimeError(f"M1 export manifest invalid: {result['errors']}")
    yaml_name = "data_test.yaml" if split == "test" else "data.yaml"
    data_yaml = EXPORT_DIR / yaml_name
    if not data_yaml.is_file():
        command = "export-test --final-eval" if split == "test" else "export"
        raise RuntimeError(f"{data_yaml} missing: run scripts/build_m1_yolo_dataset.py {command}")
    text = data_yaml.read_text(encoding="utf-8")
    if split != "test" and "\ntest:" in text:
        raise RuntimeError("data.yaml must not reference the sealed test split")
    manifest = json.loads((REPO_ROOT / export.MANIFEST_PATH).read_text(encoding="utf-8"))
    materialised_splits = ("train", "val") if split != "test" else ("test",)
    materialised = export.verify_materialised(
        REPO_ROOT,
        export.DEFAULT_RAW_ROOT,
        export.DEFAULT_WP35_ROOT,
        EXPORT_DIR,
        materialised_splits,
    )
    if not materialised["valid"]:
        raise RuntimeError(f"M1 materialised export invalid: {materialised['errors']}")
    return {
        "export_manifest_sha256": sha256_file(REPO_ROOT / export.MANIFEST_PATH),
        "class_map_sha256": manifest["class_map_sha256"],
        "split_stem_sha256": {
            s: manifest["splits"][s]["stem_list_sha256"] for s in manifest["splits"]
        },
        "data_yaml": str(data_yaml),
    }


def bind_training_model(model: str) -> dict[str, str]:
    """Permit only the exact Owner-approved local pretrained checkpoint."""
    path = Path(model).expanduser().resolve()
    if path != PRETRAINED_WEIGHTS.resolve():
        raise RuntimeError(
            f"training model must be the Owner-approved local weight: {PRETRAINED_WEIGHTS}"
        )
    if not path.is_file():
        raise RuntimeError(f"approved pretrained weight is missing: {path}")
    digest = sha256_file(path)
    if digest != PRETRAINED_WEIGHTS_SHA256:
        raise RuntimeError("approved pretrained weight SHA-256 mismatch")
    return {"path": str(path), "sha256": digest, "origin": "ultralytics/assets v8.4.0"}


def inspect_run_weights(weights: str) -> dict[str, Any]:
    """Validate a complete run claim before it can be added to the committed registry."""
    path = Path(weights).expanduser().resolve()
    if not path.is_file():
        raise RuntimeError(f"weights file is missing: {path}")
    if path.parent.name != "weights" or path.name not in {"best.pt", "last.pt"}:
        raise RuntimeError("weights must be <run>/weights/best.pt or last.pt")
    run_dir = path.parent.parent
    try:
        run_dir.relative_to(RESULTS_DIR.resolve())
    except ValueError as error:
        raise RuntimeError(f"run directory must be under {RESULTS_DIR}") from error
    contract_path = run_dir / "run_contract.json"
    if not contract_path.is_file():
        raise RuntimeError(f"run contract is missing: {contract_path}")
    record = strict_json(contract_path)
    _exact_keys(
        record,
        {
            "experiment",
            "run",
            "seed",
            "model",
            "train_args",
            "contract",
            "environment",
            "d05_gates",
            "status",
            "artifacts",
        },
        "run contract",
    )
    if record["experiment"] != "D1" or record["run"] != run_dir.name:
        raise RuntimeError("run contract experiment/run identity differs")
    if record.get("status") != "TRAINED":
        raise RuntimeError("run contract status is not TRAINED")
    _exact_keys(record["artifacts"], {"weights"}, "run artifacts")
    artifacts = record["artifacts"]["weights"]
    if not isinstance(artifacts, dict):
        raise RuntimeError("run weight artifacts must be an object")
    expected = artifacts.get(path.name, {}).get("sha256")
    actual = sha256_file(path)
    if not expected or actual != expected:
        raise RuntimeError(f"run weight SHA-256 is not bound by run_contract.json: {path.name}")
    seed = record.get("seed")
    if seed not in SEEDS:
        raise RuntimeError(f"run contract seed is not approved: {seed}")
    model = record["model"]
    _exact_keys(model, {"path", "sha256", "origin"}, "run model")
    if model["sha256"] != PRETRAINED_WEIGHTS_SHA256:
        raise RuntimeError("run contract does not bind the approved pretrained model")
    bound = check_contract()
    run_data = record["contract"]
    _exact_keys(
        run_data,
        {"export_manifest_sha256", "class_map_sha256", "split_stem_sha256", "data_yaml"},
        "run data contract",
    )
    for key in ("export_manifest_sha256", "class_map_sha256", "split_stem_sha256"):
        if run_data[key] != bound[key]:
            raise RuntimeError("run contract data binding differs from the governed contract")
    if record["d05_gates"] != GATES:
        raise RuntimeError("run contract D-05 gates differ")
    train_args = record["train_args"]
    required_train = {
        "data": run_data["data_yaml"],
        "seed": seed,
        "deterministic": True,
        "pretrained": True,
        "fliplr": 0.0,
    }
    if any(train_args.get(key) != value for key, value in required_train.items()):
        raise RuntimeError("run contract training invariants differ")
    _exact_keys(
        record["environment"],
        {
            "git_commit",
            "git_dirty_files",
            "detector_lock_sha256",
            "python",
            "platform",
            "machine",
            "hardware_chip",
            "torch",
            "ultralytics",
            "mps_available",
        },
        "run environment",
    )
    if record["environment"]["detector_lock_sha256"] != DETECTOR_LOCK_SHA256:
        raise RuntimeError("run contract detector lock differs")
    if set(artifacts) != {"best.pt", "last.pt"}:
        raise RuntimeError("run contract must bind exactly best.pt and last.pt")
    for name, artifact in artifacts.items():
        _exact_keys(artifact, {"path", "sha256"}, f"run weight artifact {name}")
        if Path(artifact["path"]).name != name:
            raise RuntimeError(f"run weight artifact path differs: {name}")
    claim = {
        "path": str(path),
        "sha256": actual,
        "run_dir": str(run_dir),
        "run_contract": str(contract_path),
        "run_contract_sha256": sha256_file(contract_path),
        "seed": seed,
        "run": run_dir.name,
    }
    claim["attestation"] = {
        "run": claim["run"],
        "seed": seed,
        "run_contract_sha256": claim["run_contract_sha256"],
        "approved_pretrained_sha256": PRETRAINED_WEIGHTS_SHA256,
        "export_manifest_sha256": bound["export_manifest_sha256"],
        "detector_lock_sha256": DETECTOR_LOCK_SHA256,
        "weights": {name: artifacts[name]["sha256"] for name in sorted(artifacts)},
    }
    claim["run_attestation_sha256"] = canonical_sha256(claim["attestation"])
    return claim


def bind_run_weights(weights: str) -> dict[str, Any]:
    """Bind a checkpoint to a clean committed run registry, not its self-issued contract alone."""
    claim = inspect_run_weights(weights)
    _require_git_tracked_clean(RUN_REGISTRY, "run registry")
    registry = strict_json(RUN_REGISTRY)
    _exact_keys(
        registry,
        {
            "schema_version",
            "status",
            "approved_pretrained_sha256",
            "export_manifest_sha256",
            "detector_lock_sha256",
            "entries",
        },
        "run registry",
    )
    if registry["schema_version"] != 1 or registry["status"] != "RUNS_REGISTERED":
        raise RuntimeError("run registry status/schema is invalid")
    if registry["approved_pretrained_sha256"] != PRETRAINED_WEIGHTS_SHA256:
        raise RuntimeError("run registry pretrained hash differs")
    if registry["detector_lock_sha256"] != DETECTOR_LOCK_SHA256:
        raise RuntimeError("run registry detector lock differs")
    if registry["export_manifest_sha256"] != claim["attestation"]["export_manifest_sha256"]:
        raise RuntimeError("run registry export manifest differs")
    entries = registry["entries"]
    if not isinstance(entries, list):
        raise RuntimeError("run registry entries must be a list")
    hashes = [canonical_sha256(entry) for entry in entries]
    if len(hashes) != len(set(hashes)):
        raise RuntimeError("run registry contains duplicate entries")
    if claim["run_attestation_sha256"] not in hashes:
        raise RuntimeError("run is not pinned by the committed run registry")
    claim["run_registry"] = str(RUN_REGISTRY)
    claim["run_registry_sha256"] = sha256_file(RUN_REGISTRY)
    return claim


def bind_threshold_lock(path_value: str, weight: dict[str, Any]) -> dict[str, Any]:
    """Require a clean, Git-tracked val lock and bind it to the selected run weight."""
    path = Path(path_value).expanduser().resolve()
    _require_git_tracked_clean(path, "threshold lock")
    record = strict_json(path)
    _exact_keys(
        record,
        {
            "schema_version",
            "status",
            "selection",
            "test_seal_sha256",
            "export_manifest_sha256",
            "candidates",
            "input_val_reports",
            "sealed_test_seen",
        },
        "threshold lock",
    )
    if record["schema_version"] != 1 or record["status"] != "LOCKED_ON_VAL":
        raise RuntimeError("threshold lock status is not LOCKED_ON_VAL")
    if record["sealed_test_seen"] is not False:
        raise RuntimeError("threshold lock says the sealed test was already seen")
    bound = check_contract()
    if record["test_seal_sha256"] != bound["split_stem_sha256"]["test"]:
        raise RuntimeError("threshold lock test seal differs from the governed split")
    if record["export_manifest_sha256"] != bound["export_manifest_sha256"]:
        raise RuntimeError("threshold lock export manifest differs")
    candidates = record["candidates"]
    if not isinstance(candidates, list) or len(candidates) != 3:
        raise RuntimeError("threshold lock must contain exactly the three D-05 seeds")
    candidate_keys = {
        "seed",
        "weight_path",
        "weight_sha256",
        "run_contract_sha256",
        "run_attestation_sha256",
        "conf",
        "nms_iou",
        "val_report_sha256",
    }
    for item in candidates:
        _exact_keys(item, candidate_keys, "threshold candidate")
        for name in ("conf", "nms_iou"):
            value = item[name]
            if (
                type(value) not in (int, float)
                or not math.isfinite(value)
                or not 0 <= value <= 1
            ):
                raise RuntimeError(f"threshold candidate {name} must be finite in [0,1]")
        bound_weight = bind_run_weights(item["weight_path"])
        for key in ("seed", "sha256", "run_contract_sha256", "run_attestation_sha256"):
            candidate_key = "weight_sha256" if key == "sha256" else key
            if item[candidate_key] != bound_weight[key]:
                raise RuntimeError(f"threshold candidate {candidate_key} differs from run binding")
    if {item["seed"] for item in candidates} != set(SEEDS):
        raise RuntimeError("threshold lock seed set differs")
    if len({item["weight_sha256"] for item in candidates}) != 3:
        raise RuntimeError("threshold lock must bind three distinct weights")
    report_rows = record["input_val_reports"]
    if not isinstance(report_rows, list) or len(report_rows) != 3:
        raise RuntimeError("threshold lock must bind exactly three val reports")
    for row in report_rows:
        _exact_keys(row, {"path", "sha256"}, "threshold val report")
        report_path = Path(row["path"]).expanduser().resolve()
        if not report_path.is_file() or sha256_file(report_path) != row["sha256"]:
            raise RuntimeError("threshold lock val report file/hash differs")
    if {row["sha256"] for row in report_rows} != {
        item["val_report_sha256"] for item in candidates
    }:
        raise RuntimeError("threshold lock val report hashes differ from candidates")
    candidate = next(
        (item for item in candidates if item.get("weight_sha256") == weight["sha256"]), None
    )
    if candidate is None:
        raise RuntimeError("run weight is not present in the committed threshold lock")
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "conf": float(candidate["conf"]),
        "nms_iou": float(candidate["nms_iou"]),
        "candidate": candidate,
    }


def class_ids() -> dict[str, int]:
    path = REPO_ROOT / "docs/review/generated/m1_yolo_classes.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["derived_key"]: int(row["yolo_id"]) for row in csv.DictReader(handle)}


def group_of() -> dict[str, str]:
    with SPLIT_FRAMES.open(newline="", encoding="utf-8") as handle:
        return {row["stem"]: row["group_id"] for row in csv.DictReader(handle)}


def unknown_boxes() -> dict[str, list[tuple[float, float, float, float]]]:
    """Normalized xywh boxes whose WP33 derived key is UNKNOWN."""
    result: dict[str, list[tuple[float, float, float, float]]] = {}
    with WP33_BOXES.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["derived_key"] == "UNKNOWN":
                result.setdefault(row["stem"], []).append(
                    tuple(float(row[key]) for key in ("x", "y", "w", "h"))
                )
    return result


def environment() -> dict[str, Any]:
    import torch
    import ultralytics

    def git(*args: str) -> str:
        try:
            return subprocess.run(
                ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return "UNKNOWN"

    def hardware_chip() -> str:
        try:
            output = subprocess.run(
                ["system_profiler", "SPHardwareDataType"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout
        except (OSError, subprocess.CalledProcessError):
            return "UNKNOWN"
        for line in output.splitlines():
            if "Chip:" in line:
                return line.split("Chip:", 1)[1].strip()
        return "UNKNOWN"

    return {
        "git_commit": git("rev-parse", "HEAD"),
        "git_dirty_files": len(git("status", "--porcelain").splitlines()),
        "detector_lock_sha256": sha256_file(DETECTOR_ROOT / "uv.lock"),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "hardware_chip": hardware_chip(),
        "torch": torch.__version__,
        "ultralytics": ultralytics.__version__,
        "mps_available": bool(torch.backends.mps.is_available()),
    }


def disable_telemetry() -> None:
    from ultralytics import settings

    settings.update(
        {
            "sync": False,
            "clearml": False,
            "comet": False,
            "dvc": False,
            "mlflow": False,
            "raytune": False,
            "tensorboard": False,
            "wandb": False,
        }
    )


def now() -> str:
    return datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%Y%m%dT%H%M%S")


def log_test_access(action: str, reason: str) -> None:
    export = load_export_module()
    path = REPO_ROOT / export.TEST_ACCESS_LOG
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {"time": now(), "action": action, "reason": reason}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
