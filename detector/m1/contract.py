"""Binding between the detector package and the governed data contract (G0.7, D-05).

The root project owns the data contract. This module loads the root M1 export builder by path
(standard library only), so the detector env never re-implements split or label logic.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
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
SPLIT_FRAMES = REPO_ROOT / "docs/review/generated/wp36_r1_split_frames.csv"
D05_RECORD = REPO_ROOT / "docs/review/d05_owner_decision_record.md"
D05_RECORD_SHA256 = "c81f37ed0236c019644914445776632dbe0fbcef0f7d5b964fb5c6d635555702"

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
    for name in ("train", "val") if split != "test" else ("test",):
        labels = sorted((EXPORT_DIR / "labels" / name).glob("*.txt"))
        stems = [p.stem for p in labels if not p.stem.startswith("wp35_")]
        if len(stems) != manifest["splits"][name]["frames"]:
            raise RuntimeError(f"exported {name} frame count differs from the manifest")
        if export.list_sha256(stems) != manifest["splits"][name]["stem_list_sha256"]:
            raise RuntimeError(f"exported {name} stems differ from the manifest")
    return {
        "export_manifest_sha256": sha256_file(REPO_ROOT / export.MANIFEST_PATH),
        "class_map_sha256": manifest["class_map_sha256"],
        "split_stem_sha256": {
            s: manifest["splits"][s]["stem_list_sha256"] for s in manifest["splits"]
        },
        "data_yaml": str(data_yaml),
    }


def class_ids() -> dict[str, int]:
    path = REPO_ROOT / "docs/review/generated/m1_yolo_classes.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["derived_key"]: int(row["yolo_id"]) for row in csv.DictReader(handle)}


def group_of() -> dict[str, str]:
    with SPLIT_FRAMES.open(newline="", encoding="utf-8") as handle:
        return {row["stem"]: row["group_id"] for row in csv.DictReader(handle)}


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

    return {
        "git_commit": git("rev-parse", "HEAD"),
        "git_dirty_files": len(git("status", "--porcelain").splitlines()),
        "detector_lock_sha256": sha256_file(DETECTOR_ROOT / "uv.lock"),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
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
