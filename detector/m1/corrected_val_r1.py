"""Validation-only evaluator for the QA-passed WP38-R1 corrected M1 export.

This module cannot address the sealed test and cannot train.  It binds an already registered D1
checkpoint to the append-only R4 data authority, rotates the governed unknown-box diagnostics for
the 39 corrected frames, and writes a distinct non-overwriting validation report.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
from PIL import Image

from m1 import cli, contract
from m1.metrics import (
    Frame,
    ap_small,
    confusion_matrix,
    error_samples,
    group_bootstrap,
    resolution_breakdown,
    select_threshold,
    unknown_false_recognition,
)

REPO_ROOT = contract.REPO_ROOT
EXPORTER = REPO_ROOT / "scripts/build_m1_yolo_dataset_wp38_r1_integration_r4.py"
MANIFEST = REPO_ROOT / "docs/review/generated/m1_yolo_wp38_r1_integration_r4_manifest.json"
QA_RECORD = REPO_ROOT / "docs/review/m1_wp38_r1_integration_r4_independent_qa_record.md"
EXPORT_DIR = REPO_ROOT / "data/processed/m1_yolo_wp38_r1_integration_r4"
REPORT_NAME = "eval_val_wp38_r1_r4.json"
CORRECTED_STEMS = {f"{number:04d}" for number in range(1319, 1358)}
PINNED = {
    EXPORTER: "0ef217775c7dcab70fddda8d5a4f89a5ab260d63a2407b85544f387774844426",
    MANIFEST: "6982a76f06f7486dd5d14015b7858ea74088f6ab3fcad6d54c576772b3c7e602",
    QA_RECORD: "27425608b177b2a29fb92a84e8ba32471cf43964766acaed6a5a3d6137f74591",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_exporter() -> ModuleType:
    spec = importlib.util.spec_from_file_location("m1_corrected_val_r4_exporter", EXPORTER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load R4 integration exporter")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def verify_corrected_data() -> dict[str, Any]:
    for path, expected in PINNED.items():
        if not path.is_file() or path.is_symlink() or sha256_file(path) != expected:
            raise RuntimeError(f"corrected-validation authority differs: {path}")
    exporter = load_exporter()
    authority = exporter.verify(REPO_ROOT)
    if authority.get("valid") is not True:
        raise RuntimeError(f"R4 integration authority differs: {authority.get('errors')}")
    materialised = exporter.verify_materialised(
        REPO_ROOT,
        exporter.DEFAULT_RAW_ROOT,
        exporter.DEFAULT_WP35_ROOT,
        exporter.DEFAULT_WP38_ROOT,
        EXPORT_DIR,
    )
    if materialised.get("valid") is not True:
        raise RuntimeError(f"R4 materialised export differs: {materialised.get('errors')}")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    yaml_path = EXPORT_DIR / "data.yaml"
    yaml_text = yaml_path.read_text(encoding="utf-8")
    if "\ntest:" in yaml_text or manifest.get("test_included") is not False:
        raise RuntimeError("corrected-validation package references the sealed test")
    if (
        manifest.get("sealed_test_accessed") is not False
        or manifest.get("training_authorized") is not False
        or manifest["splits"]["val"]["frames"] != 376
        or manifest["orientation_correction"]
        != {
            "boxes": 29,
            "frames": 39,
            "group_id": "D02-C0034",
            "raw_mutated": False,
            "rotation": "CCW_90",
            "split": "val",
        }
    ):
        raise RuntimeError("corrected-validation policy differs")
    return {
        "export_dir": str(EXPORT_DIR),
        "data_yaml": str(yaml_path),
        "integration_exporter_sha256": PINNED[EXPORTER],
        "integration_manifest_sha256": PINNED[MANIFEST],
        "integration_qa_record_sha256": PINNED[QA_RECORD],
        "val_frames": 376,
        "corrected_frames": 39,
        "test_included": False,
        "sealed_test_accessed": False,
    }


def rotate_ccw_xywh(rows: np.ndarray) -> np.ndarray:
    values = np.asarray(rows, dtype=float).reshape(-1, 4)
    if not len(values):
        return np.zeros((0, 4), dtype=float)
    rotated = np.column_stack(
        [values[:, 1], 1.0 - values[:, 0], values[:, 3], values[:, 2]]
    )
    if not np.all(np.isfinite(rotated)) or np.any(rotated < 0.0) or np.any(rotated > 1.0):
        raise RuntimeError("rotated unknown box is outside normalized bounds")
    return rotated


def xywh_to_xyxy(rows: np.ndarray, width: int, height: int) -> np.ndarray:
    values = np.asarray(rows, dtype=float).reshape(-1, 4)
    if not len(values):
        return np.zeros((0, 4), dtype=float)
    return np.column_stack(
        [
            (values[:, 0] - values[:, 2] / 2) * width,
            (values[:, 1] - values[:, 3] / 2) * height,
            (values[:, 0] + values[:, 2] / 2) * width,
            (values[:, 1] + values[:, 3] / 2) * height,
        ]
    )


def load_corrected_frames(
    weights: str, imgsz: int, device: str, nms_iou: float
) -> list[Frame]:
    from ultralytics import YOLO

    image_dir = EXPORT_DIR / "images/val"
    label_dir = EXPORT_DIR / "labels/val"
    images = sorted(
        path for path in image_dir.iterdir() if path.suffix.lower() in cli.IMAGE_SUFFIXES
    )
    if len(images) != 376:
        raise RuntimeError("corrected-validation image roster differs")
    groups = contract.group_of()
    unknown = contract.unknown_boxes()
    model = YOLO(weights)
    frames: list[Frame] = []
    for path, result in cli.iter_image_predictions(
        model, images, imgsz=imgsz, device=device, nms_iou=nms_iou
    ):
        with Image.open(path) as image:
            width, height = image.size
        rows = [
            line.split()
            for line in (label_dir / f"{path.stem}.txt").read_text().splitlines()
            if line.strip()
        ]
        gt = np.asarray([[float(value) for value in row[1:]] for row in rows]).reshape(-1, 4)
        unknown_xywh = np.asarray(unknown.get(path.stem, []), dtype=float).reshape(-1, 4)
        if path.stem in CORRECTED_STEMS:
            unknown_xywh = rotate_ccw_xywh(unknown_xywh)
        boxes = result.boxes
        frames.append(
            Frame(
                stem=path.stem,
                group_id=groups[path.stem],
                gt_boxes=xywh_to_xyxy(gt, width, height),
                gt_classes=np.asarray([int(row[0]) for row in rows], dtype=int),
                pred_boxes=boxes.xyxy.cpu().numpy(),
                pred_classes=boxes.cls.cpu().numpy().astype(int),
                pred_scores=boxes.conf.cpu().numpy(),
                image_width=width,
                image_height=height,
                unknown_boxes=xywh_to_xyxy(unknown_xywh, width, height),
            )
        )
    return frames


def evaluate(
    weights: str,
    *,
    imgsz: int = 1280,
    device: str = "mps",
    nms_iou: float = 0.70,
    bootstrap: bool = True,
) -> dict[str, Any]:
    cli._unit_interval("--nms-iou", nms_iou)
    data_binding = verify_corrected_data()
    weight_binding = contract.bind_run_weights(weights)
    out = Path(weight_binding["run_dir"]) / REPORT_NAME
    if out.exists() or out.is_symlink():
        raise RuntimeError(f"refused to overwrite corrected-validation report: {out}")
    contract.disable_telemetry()
    from ultralytics import YOLO

    validation = YOLO(weight_binding["path"]).val(
        data=data_binding["data_yaml"],
        split="val",
        imgsz=imgsz,
        device=device,
        conf=0.001,
        iou=nms_iou,
        plots=False,
        verbose=False,
        project=weight_binding["run_dir"],
        name="ultralytics_val_wp38_r1_r4",
        exist_ok=False,
    )
    frames = load_corrected_frames(weight_binding["path"], imgsz, device, nms_iou)
    point = select_threshold(frames, contract.GATES["agnostic_recall"])
    ids = contract.class_ids()
    names = {value: key for key, value in ids.items()}
    report = {
        "schema_version": 1,
        "status": "CORRECTED_VALIDATION_COMPLETE",
        "split": "val",
        "seed": weight_binding["seed"],
        "weights": weight_binding,
        "data_binding": data_binding,
        "imgsz": imgsz,
        "device": device,
        "nms_iou": nms_iou,
        "map50": float(validation.box.map50),
        "map50_95": float(validation.box.map),
        "ap_small": ap_small(frames),
        "per_class_ap50": {
            names[int(cls)]: float(validation.box.ap50[index])
            for index, cls in enumerate(validation.box.ap_class_index.tolist())
        },
        "operating_point": {
            "conf": point.conf,
            "precision": point.precision,
            "agnostic_recall": point.agnostic_recall,
            "fp_per_image": point.fp_per_image,
            "images": point.images,
            "ground_truth": point.ground_truth,
            "true_positives": point.true_positives,
            "false_positives": point.false_positives,
        },
        "resolution_breakdown": resolution_breakdown(frames, point.conf),
        "unknown_false_recognition": unknown_false_recognition(frames, point.conf),
        "confusion_matrix": {
            "labels": [names[index] for index in range(len(names))] + ["BACKGROUND"],
            "rows_gt_cols_pred": confusion_matrix(frames, point.conf, len(names)),
        },
        "error_samples": error_samples(frames, point.conf),
        "ci95_group_bootstrap": group_bootstrap(frames, point.conf) if bootstrap else None,
        "gates": cli.gate_report(
            float(validation.box.map50), float(validation.box.map), point, ids
        ),
        "test_included": False,
        "sealed_test_accessed": False,
        "note": (
            "Validation-only re-evaluation after governed WP38-R1 orientation correction; "
            "not a D-05 final verdict and not training authorization."
        ),
    }
    cli.write_json(out, report)
    return {
        "status": report["status"],
        "report": str(out),
        "map50": report["map50"],
        "map50_95": report["map50_95"],
        "operating_point": report["operating_point"],
        "single_seed_checks_passed": report["gates"]["single_seed_checks_passed"],
        "sealed_test_accessed": False,
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("check")
    run = commands.add_parser("evaluate")
    run.add_argument("--weights", required=True)
    run.add_argument("--imgsz", type=int, default=1280)
    run.add_argument("--device", default="mps")
    run.add_argument("--nms-iou", type=float, default=0.70)
    run.add_argument("--no-bootstrap", action="store_true")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        result = (
            verify_corrected_data()
            if args.command == "check"
            else evaluate(
                args.weights,
                imgsz=args.imgsz,
                device=args.device,
                nms_iou=args.nms_iou,
                bootstrap=not args.no_bootstrap,
            )
        )
    except (KeyError, OSError, RuntimeError, ValueError) as error:
        print(json.dumps({"status": "FAILED", "error": str(error)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
