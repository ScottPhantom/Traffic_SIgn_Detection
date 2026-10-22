"""Non-destructive-staging successor for the QA-failed corrected-validation evaluator R4.

R3 is validation-only.  It copies every consumer input from a verified open descriptor into an
exclusive private snapshot, makes Ultralytics consume only that snapshot, and stages reports
outside the run directory before macOS' atomic exclusive rename publishes them.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import importlib.util
import json
import os
import stat
import sys
import tempfile
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
PREDECESSOR = Path("detector/m1/corrected_val_r4.py")
PREDECESSOR_TEST = Path("detector/tests/test_corrected_val_r4.py")
PREDECESSOR_QA = Path("docs/review/d1_corrected_val_r4_independent_qa_record.md")
REPORT_NAME = "eval_val_wp38_r1_r4_r5.json"
PINNED = {
    PREDECESSOR: "5d3f69b8fa6e150acfc9fbf7d9ca1b9aa8e0af1c43538c175125e3dbe3a88e18",
    PREDECESSOR_TEST: "50614fe194e4218f537f096ed1ad69dad530e143cf94ab107f044c5974c99e4a",
    PREDECESSOR_QA: "ff6b3bc258500198b7b782beb21755b8cba6799c140c27a1c50fa0c1ea368021",
}
CORRECTED_STEMS = {f"{number:04d}" for number in range(1319, 1358)}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_predecessor() -> ModuleType:
    return _load(REPO_ROOT / PREDECESSOR, "m1_corrected_val_r5_predecessor")


def verify_pins() -> None:
    for relative, expected in PINNED.items():
        path = REPO_ROOT / relative
        if not path.is_file() or path.is_symlink() or sha256_file(path) != expected:
            raise RuntimeError(f"pinned corrected-validation R4 evidence differs: {relative}")


def _same_inode(left: os.stat_result, right: os.stat_result) -> bool:
    return (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino)


def _hash_fd(fd: int) -> str:
    os.lseek(fd, 0, os.SEEK_SET)
    digest = hashlib.sha256()
    while chunk := os.read(fd, 1024 * 1024):
        digest.update(chunk)
    os.lseek(fd, 0, os.SEEK_SET)
    return digest.hexdigest()


def _write_all(fd: int, data: bytes) -> None:
    offset = 0
    while offset < len(data):
        written = os.write(fd, data[offset:])
        if written <= 0:
            raise OSError("short write")
        offset += written


def _copy_open_fd(source_fd: int, destination: Path, expected_hash: str) -> dict[str, Any]:
    flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    destination_fd: int | None = None
    created: os.stat_result | None = None
    try:
        destination_fd = os.open(destination, flags, 0o400)
        created = os.fstat(destination_fd)
        if not stat.S_ISREG(created.st_mode) or created.st_nlink != 1:
            raise RuntimeError("private snapshot destination is unsafe")
        os.lseek(source_fd, 0, os.SEEK_SET)
        digest = hashlib.sha256()
        size = 0
        while chunk := os.read(source_fd, 1024 * 1024):
            digest.update(chunk)
            _write_all(destination_fd, chunk)
            size += len(chunk)
        os.fsync(destination_fd)
        source_hash = digest.hexdigest()
        if source_hash != expected_hash:
            raise RuntimeError(f"snapshot source hash differs: {destination.name}")
        if _hash_fd(destination_fd) != expected_hash:
            raise RuntimeError(f"snapshot destination hash differs: {destination.name}")
        return {"sha256": expected_hash, "size": size}
    except Exception:
        if created is not None:
            try:
                current = destination.lstat()
                if _same_inode(current, created):
                    destination.unlink()
            except FileNotFoundError:
                pass
        raise
    finally:
        if destination_fd is not None:
            os.close(destination_fd)


def _open_source(path: Path, *, follow_symlink: bool) -> tuple[int, os.stat_result]:
    before = path.lstat()
    if follow_symlink:
        if not stat.S_ISLNK(before.st_mode):
            raise RuntimeError(f"expected governed image symlink differs: {path.name}")
        flags = os.O_RDONLY
    else:
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise RuntimeError(f"expected single-link regular source differs: {path.name}")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    opened = os.fstat(fd)
    if not stat.S_ISREG(opened.st_mode):
        os.close(fd)
        raise RuntimeError(f"snapshot source is not regular: {path.name}")
    if not follow_symlink and not _same_inode(before, opened):
        os.close(fd)
        raise RuntimeError(f"snapshot source changed while opening: {path.name}")
    return fd, opened


def _expected_val_inputs(predecessor: ModuleType) -> tuple[dict[str, Any], dict[str, Any]]:
    integration = predecessor.load_integration()
    data = integration.derive(REPO_ROOT, integration.DEFAULT_WP38_ROOT)
    image_authority = integration
    while not hasattr(image_authority, "image_record"):
        if not hasattr(image_authority, "load_predecessor"):
            raise RuntimeError("cannot locate governed validation image authority")
        image_authority = image_authority.load_predecessor(REPO_ROOT)
    images: dict[str, Any] = {}
    labels: dict[str, Any] = {}
    for stem, text in sorted(data["labels"]["val"].items()):
        _source, expected_hash, extension = image_authority.image_record(
            REPO_ROOT,
            integration.DEFAULT_RAW_ROOT,
            "val",
            stem,
            data["correction"]["records"],
            data["inventory"],
        )
        images[stem] = {"sha256": expected_hash, "extension": extension}
        labels[stem] = text.encode()
    if len(images) != 376 or len(labels) != 376:
        raise RuntimeError("corrected-validation expected roster differs")
    return {"images": images, "labels": labels}, data


def _snapshot_yaml(root: Path, classes: list[dict[str, Any]]) -> bytes:
    lines = [
        f"path: {json.dumps(str(root))}",
        "train: images/val",
        "val: images/val",
        "names:",
    ]
    for row in sorted(classes, key=lambda item: int(item["yolo_id"])):
        lines.append(f"  {int(row['yolo_id'])}: {json.dumps(row['name'], ensure_ascii=False)}")
    return ("\n".join(lines) + "\n").encode()


def _write_private_file(path: Path, payload: bytes) -> dict[str, Any]:
    expected = hashlib.sha256(payload).hexdigest()
    with tempfile.TemporaryFile() as handle:
        handle.write(payload)
        handle.flush()
        handle.seek(0)
        return _copy_open_fd(handle.fileno(), path, expected)


def _build_private_snapshot(
    root: Path,
    weight_fd: int,
    weight_hash: str,
    predecessor: ModuleType,
) -> dict[str, Any]:
    root.chmod(0o700)
    image_dir = root / "images/val"
    label_dir = root / "labels/val"
    image_dir.mkdir(parents=True, mode=0o700)
    label_dir.mkdir(parents=True, mode=0o700)
    expected, data = _expected_val_inputs(predecessor)
    export_dir = predecessor.load_predecessor().EXPORT_DIR
    records: list[dict[str, Any]] = []
    for stem, binding in expected["images"].items():
        source = export_dir / "images/val" / f"{stem}{binding['extension']}"
        source_fd: int | None = None
        try:
            source_fd, _opened = _open_source(source, follow_symlink=True)
            copied = _copy_open_fd(
                source_fd,
                image_dir / source.name,
                binding["sha256"],
            )
        finally:
            if source_fd is not None:
                os.close(source_fd)
        records.append({"path": f"images/val/{source.name}", **copied})
    for stem, expected_bytes in expected["labels"].items():
        source = export_dir / "labels/val" / f"{stem}.txt"
        source_fd = None
        try:
            source_fd, _opened = _open_source(source, follow_symlink=False)
            copied = _copy_open_fd(
                source_fd,
                label_dir / source.name,
                hashlib.sha256(expected_bytes).hexdigest(),
            )
        finally:
            if source_fd is not None:
                os.close(source_fd)
        records.append({"path": f"labels/val/{source.name}", **copied})
    weight = root / "best.pt"
    copied_weight = _copy_open_fd(weight_fd, weight, weight_hash)
    records.append({"path": "best.pt", **copied_weight})
    yaml_path = root / "data.yaml"
    copied_yaml = _write_private_file(yaml_path, _snapshot_yaml(root, data["classes"]))
    records.append({"path": "data.yaml", **copied_yaml})
    records.sort(key=lambda row: row["path"])
    roster_hash = hashlib.sha256(
        json.dumps(records, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "root": str(root),
        "weight": str(weight),
        "data_yaml": str(yaml_path),
        "records": records,
        "roster_sha256": roster_hash,
        "val_frames": 376,
        "test_included": False,
        "sealed_test_accessed": False,
    }


def _load_snapshot_frames(
    snapshot: dict[str, Any],
    *,
    imgsz: int,
    device: str,
    nms_iou: float,
    groups: dict[str, str],
    unknown: dict[str, list[tuple[float, float, float, float]]],
    predecessor: ModuleType,
) -> list[Frame]:
    from ultralytics import YOLO

    root = Path(snapshot["root"])
    images = sorted(
        path
        for path in (root / "images/val").iterdir()
        if path.suffix.lower() in cli.IMAGE_SUFFIXES
    )
    if len(images) != 376:
        raise RuntimeError("private snapshot image roster differs")
    model = YOLO(snapshot["weight"])
    frames: list[Frame] = []
    for path, result in cli.iter_image_predictions(
        model, images, imgsz=imgsz, device=device, nms_iou=nms_iou
    ):
        with Image.open(path) as image:
            width, height = image.size
        rows = [
            line.split()
            for line in (root / "labels/val" / f"{path.stem}.txt").read_text().splitlines()
            if line.strip()
        ]
        gt = np.asarray([[float(value) for value in row[1:]] for row in rows]).reshape(-1, 4)
        unknown_xywh = np.asarray(unknown.get(path.stem, []), dtype=float).reshape(-1, 4)
        if path.stem in CORRECTED_STEMS:
            unknown_xywh = predecessor.rotate_ccw_xywh(unknown_xywh)
        boxes = result.boxes
        frames.append(
            Frame(
                stem=path.stem,
                group_id=groups[path.stem],
                gt_boxes=predecessor.xywh_to_xyxy(gt, width, height),
                gt_classes=np.asarray([int(row[0]) for row in rows], dtype=int),
                pred_boxes=boxes.xyxy.cpu().numpy(),
                pred_classes=boxes.cls.cpu().numpy().astype(int),
                pred_scores=boxes.conf.cpu().numpy(),
                image_width=width,
                image_height=height,
                unknown_boxes=predecessor.xywh_to_xyxy(
                    unknown_xywh, width, height
                ),
            )
        )
    return frames


def _rename_exclusive(
    source_dir_fd: int,
    source: str,
    destination_dir_fd: int,
    destination: str,
) -> None:
    """Atomically rename without replacing an existing destination on macOS."""
    libc = ctypes.CDLL(None, use_errno=True)
    try:
        rename = libc.renameatx_np
    except AttributeError as error:
        raise RuntimeError("atomic exclusive report publication is unavailable") from error
    rename.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    rename.restype = ctypes.c_int
    rename_excl = 0x00000004
    result = rename(
        source_dir_fd,
        os.fsencode(source),
        destination_dir_fd,
        os.fsencode(destination),
        rename_excl,
    )
    if result != 0:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code), destination)


def _report_integration() -> ModuleType:
    module = load_predecessor()
    while not hasattr(module, "load_integration"):
        if not hasattr(module, "load_predecessor"):
            raise RuntimeError("cannot locate report directory authority")
        module = module.load_predecessor()
    return module.load_integration()


def _safe_write_report(run_dir: Path, payload: dict[str, Any]) -> Path:
    integration = _report_integration()
    root_fd, retained_fds, relations = integration._open_directory_chain(run_dir)
    staging_dir = Path(tempfile.mkdtemp(prefix="cpv301-corrected-report-r5-"))
    staging_dir.chmod(0o700)
    staging_fd: int | None = None
    temp_fd: int | None = None
    temporary = "report.partial"
    final_published = False
    primary_error: BaseException | None = None
    flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        staging_fd = os.open(
            staging_dir,
            os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0),
        )
        if os.fstat(staging_fd).st_dev != os.fstat(root_fd).st_dev:
            raise RuntimeError("private report staging is not on the run filesystem")
        temp_fd = os.open(temporary, flags, 0o600, dir_fd=staging_fd)
        owned = os.fstat(temp_fd)
        if not stat.S_ISREG(owned.st_mode) or owned.st_nlink != 1:
            raise RuntimeError("corrected-validation report partial is unsafe")
        data = (
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
            + "\n"
        ).encode()
        _write_all(temp_fd, data)
        os.fsync(temp_fd)
        if _hash_fd(temp_fd) != hashlib.sha256(data).hexdigest():
            raise RuntimeError("corrected-validation report partial hash differs")
        if not _same_inode(os.fstat(temp_fd), owned):
            raise RuntimeError("corrected-validation report partial binding differs")
        integration._validate_relations(relations)
        _rename_exclusive(
            staging_fd,
            temporary,
            root_fd,
            REPORT_NAME,
        )
        final_published = True
        return run_dir / REPORT_NAME
    except BaseException as error:
        primary_error = error
        raise
    finally:
        close_errors: list[BaseException] = []
        if temp_fd is not None:
            try:
                os.close(temp_fd)
            except OSError as error:
                close_errors.append(error)
        if staging_fd is not None:
            try:
                os.close(staging_fd)
            except OSError as error:
                close_errors.append(error)
        for fd in reversed(retained_fds):
            try:
                os.close(fd)
            except OSError as error:
                close_errors.append(error)
        if close_errors and primary_error is None and not final_published:
            raise RuntimeError("corrected-validation descriptor close failed") from close_errors[0]


def verify_corrected_data() -> dict[str, Any]:
    verify_pins()
    return load_predecessor().verify_corrected_data()


def evaluate(
    weights: str,
    *,
    imgsz: int = 1280,
    device: str = "mps",
    nms_iou: float = 0.70,
    bootstrap: bool = True,
) -> dict[str, Any]:
    cli._unit_interval("--nms-iou", nms_iou)
    verify_pins()
    predecessor_r4 = load_predecessor()
    predecessor_r3 = predecessor_r4.load_predecessor()
    predecessor_r2 = predecessor_r3.load_predecessor()
    predecessor = predecessor_r2.load_predecessor()
    data_binding = predecessor.verify_corrected_data()
    weight_binding = contract.bind_run_weights(weights)
    report_path = Path(weight_binding["run_dir"]) / REPORT_NAME
    if report_path.exists() or report_path.is_symlink():
        raise RuntimeError(f"refused to overwrite corrected-validation report: {report_path}")

    weight_fd: int | None = None
    try:
        weight_fd, _weight_stat = predecessor_r2._open_weight_guard(
            Path(weight_binding["path"]), weight_binding["sha256"]
        )
        groups = dict(contract.group_of())
        unknown = {key: list(value) for key, value in contract.unknown_boxes().items()}
        ids = dict(contract.class_ids())
        with tempfile.TemporaryDirectory(prefix="cpv301-corrected-val-r3-") as directory:
            snapshot = _build_private_snapshot(
                Path(directory),
                weight_fd,
                weight_binding["sha256"],
                predecessor_r2,
            )
            contract.disable_telemetry()
            from ultralytics import YOLO

            private_project = Path(directory) / "ultralytics"
            validation = YOLO(snapshot["weight"]).val(
                data=snapshot["data_yaml"],
                split="val",
                imgsz=imgsz,
                device=device,
                conf=0.001,
                iou=nms_iou,
                plots=False,
                verbose=False,
                project=private_project,
                name="validation",
                exist_ok=False,
            )
            frames = _load_snapshot_frames(
                snapshot,
                imgsz=imgsz,
                device=device,
                nms_iou=nms_iou,
                groups=groups,
                unknown=unknown,
                predecessor=predecessor,
            )
            point = select_threshold(frames, contract.GATES["agnostic_recall"])
            names = {value: key for key, value in ids.items()}
            snapshot_binding = {
                key: value
                for key, value in snapshot.items()
                if key not in {"root", "weight", "data_yaml"}
            }
            report = {
                "schema_version": 3,
                "status": "CORRECTED_VALIDATION_COMPLETE",
                "split": "val",
                "seed": weight_binding["seed"],
                "weights": weight_binding,
                "data_binding": data_binding,
                "private_snapshot": snapshot_binding,
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
                "use_time_binding": {
                    "consumer": "exclusive_private_snapshot",
                    "source_hashes_verified_before_consumer": True,
                    "snapshot_destroyed_after_evaluation": True,
                    "snapshot_roster_sha256": snapshot["roster_sha256"],
                },
                "test_included": False,
                "sealed_test_accessed": False,
                "note": (
                    "Validation-only re-evaluation after governed WP38-R1 orientation correction; "
                    "not a D-05 final verdict and not training authorization."
                ),
            }
        output = _safe_write_report(Path(weight_binding["run_dir"]), report)
        return {
            "status": report["status"],
            "report": str(output),
            "map50": report["map50"],
            "map50_95": report["map50_95"],
            "operating_point": report["operating_point"],
            "single_seed_checks_passed": report["gates"]["single_seed_checks_passed"],
            "use_time_binding_verified": True,
            "sealed_test_accessed": False,
        }
    finally:
        if weight_fd is not None:
            os.close(weight_fd)


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
